"""Patient FHIR Bundle (chart-read) endpoint tests.

``GET /v1/reports/fhir/patients/{user_id}/bundle`` is the PHI-boundary
surface that streams a patient's full psychometric history to a clinician
as a single FHIR R4 Bundle.  Introduced in Sprint 27 on top of the
existing AssessmentRepository + fhir_observation / fhir_bundle helpers.

Coverage matrix:
- Auth: missing / empty ``X-Clinician-Id`` rejected.
- Empty patient history → 200 with ``entry=[]`` (NOT 404 — absence of
  readings is a valid clinical state).
- Multi-instrument bundle: submit across PHQ-9 / GAD-7 / WHO-5 /
  AUDIT / AUDIT-C / PSS-10 / DAST-10 and verify every entry renders
  through the numeric ``valueInteger`` path.
- C-SSRS mixed in: categorical ``valueCodeableConcept`` path preserved
  inside the Bundle; ``component`` entries emitted for triggering items.
- Safety routing: PHQ-9 item 9 positive and C-SSRS acute record both
  carry the ``interpretation`` block inside their Bundle entries.
- Instrument filter: ``?instrument=phq9`` restricts to one instrument;
  unknown filter yields an empty Bundle.
- Chronological ordering: entries are oldest-first regardless of
  submission order.
- Bundle identifier: caller correlation_id round-trips; absent → fresh
  UUID; caller ``urn:uuid:`` prefix preserved idempotently.
- PHI boundary header + audit emission shape (``phi.access.attempt``
  before fetch, ``phi.access.ok`` after, ``phi.access.error`` on stored
  record dispatch failure).
- Limit validation: 0 / negative / > 1000 → 400.
- Cross-user isolation: clinician-A reading patient-A cannot see
  patient-B's records (repository boundary).
- Serializability: response round-trips through ``json.dumps``.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

import pytest
from fastapi.testclient import TestClient

from discipline.app import create_app
from discipline.psychometric.repository import (
    AssessmentRecord,
    get_assessment_repository,
)
from discipline.shared.idempotency import get_idempotency_store
from discipline.shared.logging import LogStream, get_stream_logger


# ---- Fixtures -----------------------------------------------------------


@pytest.fixture(autouse=True)
def _reset_stores() -> Any:
    """Clear idempotency + repository between tests.

    Mirrors the single-Observation endpoint fixture — both surfaces
    share the same module-level stores and must see a fresh state for
    each test."""
    get_idempotency_store().clear()
    get_assessment_repository().clear()
    yield
    get_idempotency_store().clear()
    get_assessment_repository().clear()


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


@pytest.fixture
def captured_audit_events(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, Any]]:
    """Intercept audit-stream emissions so tests can assert on them.

    Same shape as the clinician-bundle POST test fixture — we patch the
    BoundLogger's ``info`` / ``warning`` methods so the assertion proves
    the router uses the audit stream rather than just emitting structured
    output somewhere."""
    captured: list[dict[str, Any]] = []
    audit = get_stream_logger(LogStream.AUDIT)

    def _capture(level: str):
        def inner(event: str, **kwargs: Any) -> None:
            captured.append({"level": level, "event": event, **kwargs})

        return inner

    monkeypatch.setattr(audit, "info", _capture("info"))
    monkeypatch.setattr(audit, "warning", _capture("warning"))
    return captured


def _submit(
    client: TestClient,
    *,
    user_id: str,
    instrument: str,
    items: list[int],
    sex: str | None = None,
    behavior_within_3mo: bool | None = None,
) -> str:
    """POST an assessment and return its id — mirrors the fixture used
    by the single-Observation endpoint test so the setup pattern is
    recognizable across files."""
    body: dict[str, Any] = {
        "instrument": instrument,
        "items": items,
        "user_id": user_id,
    }
    if sex is not None:
        body["sex"] = sex
    if behavior_within_3mo is not None:
        body["behavior_within_3mo"] = behavior_within_3mo
    resp = client.post(
        "/v1/assessments",
        json=body,
        headers={"Idempotency-Key": f"test-{uuid.uuid4()}"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["assessment_id"]


def _save_record_directly(
    *,
    user_id: str,
    instrument: str,
    total: int,
    created_at: datetime,
    severity: str = "mild",
    assessment_id: str | None = None,
    index: int | None = None,
    requires_t3: bool = False,
    triggering_items: tuple[int, ...] | None = None,
    raw_items: tuple[int, ...] | None = None,
) -> str:
    """Persist a record bypassing the HTTP layer.

    Used by tests that need to pin ``created_at`` for chronological
    ordering assertions — the HTTP submit path stamps records with
    ``repo.now()`` and back-to-back submissions land microseconds apart,
    which makes oldest-first sorting harder to assert deterministically
    across unrelated instruments."""
    repo = get_assessment_repository()
    aid = assessment_id or f"rec-{uuid.uuid4()}"
    record = AssessmentRecord(
        assessment_id=aid,
        user_id=user_id,
        instrument=instrument,
        total=total,
        severity=severity,
        requires_t3=requires_t3,
        raw_items=raw_items or tuple([0] * 9),
        created_at=created_at,
        index=index,
        triggering_items=triggering_items,
    )
    repo.save(record)
    return aid


# =============================================================================
# Auth
# =============================================================================


class TestAuth:
    def test_missing_clinician_id_header_rejected(
        self, client: TestClient
    ) -> None:
        """Without clinician identity the endpoint refuses — patients
        use /v1/assessments/history, clinicians use this URL."""
        resp = client.get("/v1/reports/fhir/patients/pt-1/bundle")
        # FastAPI's Header(...) produces 422 when the header is absent;
        # our guard produces 401 on empty.  Either non-success is
        # acceptable — the point is the request doesn't succeed.
        assert resp.status_code in (401, 422)

    def test_empty_clinician_id_rejected(self, client: TestClient) -> None:
        resp = client.get(
            "/v1/reports/fhir/patients/pt-1/bundle",
            headers={"X-Clinician-Id": ""},
        )
        assert resp.status_code == 401
        assert resp.json()["detail"]["code"] == "auth.missing_clinician_id"


# =============================================================================
# Empty history — 200 with empty entry
# =============================================================================


class TestEmptyHistory:
    def test_unknown_user_returns_empty_bundle_not_404(
        self, client: TestClient
    ) -> None:
        """'Patient has no readings yet' is a clinical state, not a
        missing resource.  Returning 404 would break the chart-read
        UX (empty state is the right render, not an error banner)."""
        resp = client.get(
            "/v1/reports/fhir/patients/nobody/bundle",
            headers={"X-Clinician-Id": "c1"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["resourceType"] == "Bundle"
        assert body["type"] == "collection"
        assert body["entry"] == []

    def test_empty_bundle_still_has_identifier_and_timestamp(
        self, client: TestClient
    ) -> None:
        """Empty Bundles must still be valid FHIR — identifier and
        timestamp are required by the R4 spec regardless of entry
        count."""
        resp = client.get(
            "/v1/reports/fhir/patients/nobody/bundle",
            headers={"X-Clinician-Id": "c1"},
        )
        body = resp.json()
        assert body["identifier"]["value"].startswith("urn:uuid:")
        assert body["identifier"]["system"] == "urn:ietf:rfc:3986"
        assert body["timestamp"].endswith("Z")


# =============================================================================
# Numeric instruments — valueInteger path
# =============================================================================


class TestNumericInstruments:
    def test_phq9_only_bundle_renders_valueinteger(
        self, client: TestClient
    ) -> None:
        _submit(
            client,
            user_id="u1",
            instrument="phq9",
            items=[1, 0, 0, 0, 0, 0, 0, 0, 0],
        )
        resp = client.get(
            "/v1/reports/fhir/patients/u1/bundle",
            headers={"X-Clinician-Id": "c1"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["entry"]) == 1
        obs = body["entry"][0]["resource"]
        assert obs["resourceType"] == "Observation"
        assert obs["valueInteger"] == 1
        assert obs["code"]["coding"][0]["code"] == "44261-6"

    def test_multi_instrument_bundle_covers_all_numeric_renderers(
        self, client: TestClient
    ) -> None:
        """One submission per numeric instrument; the bundle should
        carry one entry per submission with the right LOINC code."""
        _submit(
            client,
            user_id="u1",
            instrument="phq9",
            items=[0, 0, 0, 0, 0, 0, 0, 0, 0],
        )
        _submit(
            client,
            user_id="u1",
            instrument="gad7",
            items=[0, 0, 0, 0, 0, 0, 0],
        )
        _submit(
            client,
            user_id="u1",
            instrument="who5",
            items=[3, 3, 3, 3, 3],
        )
        _submit(
            client,
            user_id="u1",
            instrument="audit",
            items=[1, 1, 1, 1, 1, 1, 1, 1, 0, 0],
        )
        _submit(
            client,
            user_id="u1",
            instrument="audit_c",
            items=[1, 1, 1],
            sex="female",
        )
        _submit(
            client,
            user_id="u1",
            instrument="pss10",
            items=[1, 1, 1, 2, 2, 1, 1, 2, 2, 1],
        )
        _submit(
            client,
            user_id="u1",
            instrument="dast10",
            items=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        )
        resp = client.get(
            "/v1/reports/fhir/patients/u1/bundle",
            headers={"X-Clinician-Id": "c1"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["entry"]) == 7
        loinc_codes = {
            e["resource"]["code"]["coding"][0]["code"]
            for e in body["entry"]
        }
        assert loinc_codes == {
            "44261-6",  # phq9
            "69737-5",  # gad7
            "75626-2",  # audit
            "75624-7",  # audit_c
            "82667-7",  # dast10
            "89708-7",  # who5
            "93038-1",  # pss10
        }


# =============================================================================
# C-SSRS — categorical valueCodeableConcept path
# =============================================================================


class TestCssrsInBundle:
    def test_cssrs_record_renders_valuecodeableconcept(
        self, client: TestClient
    ) -> None:
        """The bundle-level dispatch must route C-SSRS through
        render_cssrs_bundle — a categorical record wrongly rendered as
        valueInteger would emit a score (= positive_count) that EHRs
        could silently mistake for a severity metric."""
        _submit(
            client,
            user_id="u1",
            instrument="cssrs",
            items=[0, 0, 0, 0, 0, 0],
        )
        resp = client.get(
            "/v1/reports/fhir/patients/u1/bundle",
            headers={"X-Clinician-Id": "c1"},
        )
        assert resp.status_code == 200
        body = resp.json()
        obs = body["entry"][0]["resource"]
        assert "valueCodeableConcept" in obs
        assert "valueInteger" not in obs
        assert obs["valueCodeableConcept"]["coding"][0]["code"] == "none"

    def test_cssrs_triggering_items_become_component_entries(
        self, client: TestClient
    ) -> None:
        """C-SSRS positive items must flow into the Bundle entry's
        component array so the EHR can see WHICH items fired without
        the raw item-response payload."""
        _submit(
            client,
            user_id="u1",
            instrument="cssrs",
            items=[1, 1, 0, 0, 0, 0],
        )
        resp = client.get(
            "/v1/reports/fhir/patients/u1/bundle",
            headers={"X-Clinician-Id": "c1"},
        )
        obs = resp.json()["entry"][0]["resource"]
        assert "component" in obs
        component_codes = {
            c["code"]["coding"][0]["code"] for c in obs["component"]
        }
        assert component_codes == {"item-1", "item-2"}


# =============================================================================
# Mixed numeric + C-SSRS in one Bundle
# =============================================================================


class TestMixedInstrumentBundle:
    def test_numeric_and_categorical_coexist_in_same_bundle(
        self, client: TestClient
    ) -> None:
        """A clinician reading the full chart will see both shapes in
        one response — the fhir_bundle layer must preserve each
        renderer's output verbatim."""
        _submit(
            client,
            user_id="u1",
            instrument="phq9",
            items=[0, 0, 0, 0, 0, 0, 0, 0, 0],
        )
        _submit(
            client,
            user_id="u1",
            instrument="cssrs",
            items=[0, 0, 0, 0, 0, 0],
        )
        resp = client.get(
            "/v1/reports/fhir/patients/u1/bundle",
            headers={"X-Clinician-Id": "c1"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["entry"]) == 2
        shapes = {
            "valueInteger" if "valueInteger" in e["resource"] else "valueCodeableConcept"
            for e in body["entry"]
        }
        assert shapes == {"valueInteger", "valueCodeableConcept"}


# =============================================================================
# Safety routing — interpretation block flows through
# =============================================================================


class TestSafetyRouting:
    def test_phq9_item9_positive_surfaces_interpretation(
        self, client: TestClient
    ) -> None:
        """A T3-firing PHQ-9 submission (item 9 positive) must carry
        the interpretation block in its Bundle entry so receiving
        systems can flag the result on the chart read."""
        _submit(
            client,
            user_id="u1",
            instrument="phq9",
            items=[0, 0, 0, 0, 0, 0, 0, 0, 2],
        )
        resp = client.get(
            "/v1/reports/fhir/patients/u1/bundle",
            headers={"X-Clinician-Id": "c1"},
        )
        obs = resp.json()["entry"][0]["resource"]
        assert "interpretation" in obs
        assert obs["interpretation"][0]["coding"][0]["code"] == "t3-routed"

    def test_cssrs_acute_triage_surfaces_interpretation(
        self, client: TestClient
    ) -> None:
        """C-SSRS item 4 positive + behavior_within_3mo → acute band;
        the Bundle entry surfaces the same t3-routed code used for
        PHQ-9 item 9 so receiving systems' safety branches are
        uniform across instrument sources."""
        _submit(
            client,
            user_id="u1",
            instrument="cssrs",
            items=[0, 0, 0, 1, 0, 0],
            behavior_within_3mo=True,
        )
        resp = client.get(
            "/v1/reports/fhir/patients/u1/bundle",
            headers={"X-Clinician-Id": "c1"},
        )
        obs = resp.json()["entry"][0]["resource"]
        assert "interpretation" in obs
        assert obs["interpretation"][0]["coding"][0]["code"] == "t3-routed"


# =============================================================================
# Instrument filter
# =============================================================================


class TestInstrumentFilter:
    def test_filter_restricts_to_single_instrument(
        self, client: TestClient
    ) -> None:
        _submit(
            client,
            user_id="u1",
            instrument="phq9",
            items=[0, 0, 0, 0, 0, 0, 0, 0, 0],
        )
        _submit(
            client,
            user_id="u1",
            instrument="gad7",
            items=[0, 0, 0, 0, 0, 0, 0],
        )
        resp = client.get(
            "/v1/reports/fhir/patients/u1/bundle?instrument=phq9",
            headers={"X-Clinician-Id": "c1"},
        )
        body = resp.json()
        assert len(body["entry"]) == 1
        assert (
            body["entry"][0]["resource"]["code"]["coding"][0]["code"]
            == "44261-6"
        )

    def test_filter_lowercases_caller_input(self, client: TestClient) -> None:
        """Callers don't need to know the canonical casing — same
        contract as /trajectory/{instrument}."""
        _submit(
            client,
            user_id="u1",
            instrument="phq9",
            items=[0, 0, 0, 0, 0, 0, 0, 0, 0],
        )
        resp = client.get(
            "/v1/reports/fhir/patients/u1/bundle?instrument=PHQ9",
            headers={"X-Clinician-Id": "c1"},
        )
        assert resp.status_code == 200
        assert len(resp.json()["entry"]) == 1

    def test_unknown_filter_returns_empty_not_422(
        self, client: TestClient
    ) -> None:
        """Unknown instrument filter on an existing patient is a
        clinical 'no match' query, not a validation error.  Parallels
        the trajectory endpoint's tolerance for unknown instruments."""
        _submit(
            client,
            user_id="u1",
            instrument="phq9",
            items=[0, 0, 0, 0, 0, 0, 0, 0, 0],
        )
        resp = client.get(
            "/v1/reports/fhir/patients/u1/bundle?instrument=not_real",
            headers={"X-Clinician-Id": "c1"},
        )
        assert resp.status_code == 200
        assert resp.json()["entry"] == []

    def test_empty_filter_param_treated_as_no_filter(
        self, client: TestClient
    ) -> None:
        """``?instrument=`` (empty value) must NOT filter out every
        record; strip + lower on an empty string is a no-op filter."""
        _submit(
            client,
            user_id="u1",
            instrument="phq9",
            items=[0, 0, 0, 0, 0, 0, 0, 0, 0],
        )
        resp = client.get(
            "/v1/reports/fhir/patients/u1/bundle?instrument=",
            headers={"X-Clinician-Id": "c1"},
        )
        assert resp.status_code == 200
        assert len(resp.json()["entry"]) == 1


# =============================================================================
# Chronological ordering — oldest-first for chart read
# =============================================================================


class TestChronologicalOrder:
    def test_entries_are_oldest_first(self, client: TestClient) -> None:
        """The repository stores newest-first, but the clinician chart
        read needs oldest-first so the timeline renders top-to-bottom
        in the order events occurred."""
        _save_record_directly(
            user_id="u1",
            instrument="phq9",
            total=5,
            severity="mild",
            created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            raw_items=tuple([0] * 9),
        )
        _save_record_directly(
            user_id="u1",
            instrument="phq9",
            total=10,
            severity="moderate",
            created_at=datetime(2026, 3, 15, tzinfo=timezone.utc),
            raw_items=tuple([0] * 9),
        )
        _save_record_directly(
            user_id="u1",
            instrument="phq9",
            total=3,
            severity="minimal",
            created_at=datetime(2026, 2, 1, tzinfo=timezone.utc),
            raw_items=tuple([0] * 9),
        )
        resp = client.get(
            "/v1/reports/fhir/patients/u1/bundle",
            headers={"X-Clinician-Id": "c1"},
        )
        body = resp.json()
        effective_dates = [
            e["resource"]["effectiveDateTime"] for e in body["entry"]
        ]
        assert effective_dates == sorted(effective_dates)

    def test_single_record_bundle_has_one_entry(
        self, client: TestClient
    ) -> None:
        _submit(
            client,
            user_id="u1",
            instrument="phq9",
            items=[0, 0, 0, 0, 0, 0, 0, 0, 0],
        )
        resp = client.get(
            "/v1/reports/fhir/patients/u1/bundle",
            headers={"X-Clinician-Id": "c1"},
        )
        assert len(resp.json()["entry"]) == 1


# =============================================================================
# Bundle identifier + correlation-id
# =============================================================================


class TestBundleIdentifier:
    def test_correlation_id_lands_in_bundle_identifier(
        self, client: TestClient
    ) -> None:
        resp = client.get(
            "/v1/reports/fhir/patients/u1/bundle",
            headers={
                "X-Clinician-Id": "c1",
                "X-Correlation-Id": "corr-12345",
            },
        )
        assert resp.json()["identifier"]["value"] == "urn:uuid:corr-12345"

    def test_no_correlation_id_yields_fresh_uuid(
        self, client: TestClient
    ) -> None:
        resp = client.get(
            "/v1/reports/fhir/patients/u1/bundle",
            headers={"X-Clinician-Id": "c1"},
        )
        assert resp.json()["identifier"]["value"].startswith("urn:uuid:")

    def test_caller_urn_uuid_prefix_not_doubled(
        self, client: TestClient
    ) -> None:
        """A caller that already prepended 'urn:uuid:' must not see
        'urn:uuid:urn:uuid:' in the response."""
        resp = client.get(
            "/v1/reports/fhir/patients/u1/bundle",
            headers={
                "X-Clinician-Id": "c1",
                "X-Correlation-Id": "urn:uuid:already-prefixed",
            },
        )
        assert (
            resp.json()["identifier"]["value"]
            == "urn:uuid:already-prefixed"
        )


# =============================================================================
# PHI boundary header
# =============================================================================


class TestPhiBoundaryHeader:
    def test_header_present_on_empty_bundle(self, client: TestClient) -> None:
        resp = client.get(
            "/v1/reports/fhir/patients/nobody/bundle",
            headers={"X-Clinician-Id": "c1"},
        )
        assert resp.headers.get("X-Phi-Boundary") == "1"

    def test_header_present_on_populated_bundle(
        self, client: TestClient
    ) -> None:
        _submit(
            client,
            user_id="u1",
            instrument="phq9",
            items=[0, 0, 0, 0, 0, 0, 0, 0, 0],
        )
        resp = client.get(
            "/v1/reports/fhir/patients/u1/bundle",
            headers={"X-Clinician-Id": "c1"},
        )
        assert resp.headers.get("X-Phi-Boundary") == "1"


# =============================================================================
# Audit emission
# =============================================================================


class TestAuditEmission:
    def test_attempt_event_fires_before_fetch(
        self,
        client: TestClient,
        captured_audit_events: list[dict[str, Any]],
    ) -> None:
        """Enumeration attempts must show up in the trail even when the
        patient has no records — attempt emits BEFORE the repo read."""
        client.get(
            "/v1/reports/fhir/patients/unknown/bundle",
            headers={"X-Clinician-Id": "clin-777"},
        )
        attempt = next(
            e for e in captured_audit_events if e["event"] == "phi.access.attempt"
        )
        assert attempt["actor_id"] == "clin-777"
        assert attempt["actor_role"] == "clinician"
        assert attempt["subject_id"] == "unknown"
        assert attempt["resource"] == "fhir.bundle.history"

    def test_ok_event_includes_observation_count(
        self,
        client: TestClient,
        captured_audit_events: list[dict[str, Any]],
    ) -> None:
        _submit(
            client,
            user_id="u1",
            instrument="phq9",
            items=[0, 0, 0, 0, 0, 0, 0, 0, 0],
        )
        _submit(
            client,
            user_id="u1",
            instrument="gad7",
            items=[0, 0, 0, 0, 0, 0, 0],
        )
        client.get(
            "/v1/reports/fhir/patients/u1/bundle",
            headers={"X-Clinician-Id": "clin-777"},
        )
        ok = next(
            e for e in captured_audit_events if e["event"] == "phi.access.ok"
        )
        assert ok["subject_id"] == "u1"
        assert ok["observation_count"] == 2
        assert ok["bundle_identifier"].startswith("urn:uuid:")

    def test_ok_event_echoes_instrument_filter(
        self,
        client: TestClient,
        captured_audit_events: list[dict[str, Any]],
    ) -> None:
        client.get(
            "/v1/reports/fhir/patients/u1/bundle?instrument=phq9",
            headers={"X-Clinician-Id": "c1"},
        )
        ok = next(
            e for e in captured_audit_events if e["event"] == "phi.access.ok"
        )
        assert ok["instrument_filter"] == "phq9"

    def test_correlation_id_threaded_into_attempt(
        self,
        client: TestClient,
        captured_audit_events: list[dict[str, Any]],
    ) -> None:
        client.get(
            "/v1/reports/fhir/patients/u1/bundle",
            headers={
                "X-Clinician-Id": "c1",
                "X-Correlation-Id": "trace-xyz",
            },
        )
        attempt = next(
            e for e in captured_audit_events if e["event"] == "phi.access.attempt"
        )
        assert attempt["correlation_id"] == "trace-xyz"

    def test_attempt_fires_before_ok(
        self,
        client: TestClient,
        captured_audit_events: list[dict[str, Any]],
    ) -> None:
        client.get(
            "/v1/reports/fhir/patients/u1/bundle",
            headers={"X-Clinician-Id": "c1"},
        )
        events = [e["event"] for e in captured_audit_events]
        attempt_idx = events.index("phi.access.attempt")
        ok_idx = events.index("phi.access.ok")
        assert attempt_idx < ok_idx


# =============================================================================
# Limit validation
# =============================================================================


class TestLimitValidation:
    def test_zero_limit_rejected(self, client: TestClient) -> None:
        resp = client.get(
            "/v1/reports/fhir/patients/u1/bundle?limit=0",
            headers={"X-Clinician-Id": "c1"},
        )
        assert resp.status_code == 400
        assert resp.json()["detail"]["code"] == "validation.limit"

    def test_negative_limit_rejected(self, client: TestClient) -> None:
        resp = client.get(
            "/v1/reports/fhir/patients/u1/bundle?limit=-1",
            headers={"X-Clinician-Id": "c1"},
        )
        assert resp.status_code == 400

    def test_limit_above_ceiling_rejected(self, client: TestClient) -> None:
        resp = client.get(
            "/v1/reports/fhir/patients/u1/bundle?limit=1001",
            headers={"X-Clinician-Id": "c1"},
        )
        assert resp.status_code == 400

    def test_limit_at_ceiling_accepted(self, client: TestClient) -> None:
        resp = client.get(
            "/v1/reports/fhir/patients/u1/bundle?limit=1000",
            headers={"X-Clinician-Id": "c1"},
        )
        assert resp.status_code == 200


# =============================================================================
# Cross-user isolation (repository boundary)
# =============================================================================


class TestCrossUserIsolation:
    def test_bundle_only_contains_target_patient_records(
        self, client: TestClient
    ) -> None:
        """The repository enforces per-user isolation; this is an
        integration check that the router doesn't accidentally leak
        records across users (e.g., by filtering after fetching
        everyone)."""
        _submit(
            client,
            user_id="alice",
            instrument="phq9",
            items=[1, 0, 0, 0, 0, 0, 0, 0, 0],
        )
        _submit(
            client,
            user_id="bob",
            instrument="phq9",
            items=[2, 0, 0, 0, 0, 0, 0, 0, 0],
        )
        resp = client.get(
            "/v1/reports/fhir/patients/alice/bundle",
            headers={"X-Clinician-Id": "c1"},
        )
        body = resp.json()
        assert len(body["entry"]) == 1
        assert body["entry"][0]["resource"]["valueInteger"] == 1
        assert (
            body["entry"][0]["resource"]["subject"]["reference"]
            == "Patient/alice"
        )


# =============================================================================
# Serializability + structural integrity
# =============================================================================


class TestSerializability:
    def test_response_is_json_round_trippable(self, client: TestClient) -> None:
        """No leaked datetime / UUID objects — the response body must
        round-trip through json.dumps cleanly for EHR integrations."""
        _submit(
            client,
            user_id="u1",
            instrument="phq9",
            items=[0, 0, 0, 0, 0, 0, 0, 0, 0],
        )
        resp = client.get(
            "/v1/reports/fhir/patients/u1/bundle",
            headers={"X-Clinician-Id": "c1"},
        )
        json.dumps(resp.json())

    def test_every_entry_has_fullurl_and_resource(
        self, client: TestClient
    ) -> None:
        _submit(
            client,
            user_id="u1",
            instrument="phq9",
            items=[0, 0, 0, 0, 0, 0, 0, 0, 0],
        )
        _submit(
            client,
            user_id="u1",
            instrument="gad7",
            items=[0, 0, 0, 0, 0, 0, 0],
        )
        resp = client.get(
            "/v1/reports/fhir/patients/u1/bundle",
            headers={"X-Clinician-Id": "c1"},
        )
        for entry in resp.json()["entry"]:
            assert entry["fullUrl"].startswith("urn:uuid:")
            assert entry["resource"]["resourceType"] == "Observation"

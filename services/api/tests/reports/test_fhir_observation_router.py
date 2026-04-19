"""Single-Observation FHIR GET endpoint tests.

``GET /v1/reports/fhir/observations/{assessment_id}`` is the PHI-boundary
surface for fetching one stored assessment as a FHIR R4 Observation.
Introduced in Sprint 24 alongside the AssessmentRepository wiring.

Coverage matrix:
- Auth: missing / empty ``X-Clinician-Id`` rejected.
- 404: unknown assessment_id → 404, and the miss is audited.
- Happy path per instrument: PHQ-9 / GAD-7 / AUDIT-C / WHO-5 / PSS-10
  / DAST-10 → ``valueInteger`` shape via ``render_bundle``.
- C-SSRS: categorical ``valueCodeableConcept`` shape via
  ``render_cssrs_bundle``, with ``component`` entries per triggering
  item.
- Safety routing: T3-firing records surface the ``interpretation``
  block (PHQ-9 item 9 + C-SSRS acute triage).
- PHI boundary header present on every successful response.
- Audit emission shape: attempt + ok on success, attempt + error on
  404, correlation_id passthrough.
"""

from __future__ import annotations

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

    Mirrors the psychometric-router test fixture — both surfaces
    share the same module-level stores and must see a fresh state
    for each test."""
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
    """Intercept audit-stream emissions.

    Same pattern as ``test_clinician_bundle_router.py`` — we patch
    the BoundLogger so the assertion proves the router is using the
    audit stream, not merely emitting structured output somewhere.
    """
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
    """POST an assessment, return the assessment_id.

    Uses a fresh Idempotency-Key per call so tests don't collide on
    the cache."""
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


# ---- Auth ---------------------------------------------------------------


class TestAuth:
    def test_missing_clinician_id_header_rejected(
        self, client: TestClient
    ) -> None:
        """Without clinician identity the endpoint refuses — there is
        no patient-portal read path on this URL (patients use
        /v1/assessments/history instead)."""
        # Seed a record so a missing header is never confused with 404.
        aid = _submit(
            client,
            user_id="u1",
            instrument="phq9",
            items=[0, 0, 0, 0, 0, 0, 0, 0, 0],
        )
        resp = client.get(f"/v1/reports/fhir/observations/{aid}")
        # FastAPI's Header(...) with alias produces 422 from pydantic
        # validation when the header is entirely absent; either 401
        # (our guard) or 422 (pydantic) is acceptable, the point is the
        # request does NOT succeed.
        assert resp.status_code in (401, 422)

    def test_empty_clinician_id_rejected(self, client: TestClient) -> None:
        aid = _submit(
            client,
            user_id="u1",
            instrument="phq9",
            items=[0, 0, 0, 0, 0, 0, 0, 0, 0],
        )
        resp = client.get(
            f"/v1/reports/fhir/observations/{aid}",
            headers={"X-Clinician-Id": ""},
        )
        assert resp.status_code == 401


# ---- 404 ----------------------------------------------------------------


class TestNotFound:
    def test_unknown_assessment_returns_404(self, client: TestClient) -> None:
        resp = client.get(
            "/v1/reports/fhir/observations/never-existed",
            headers={"X-Clinician-Id": "c1"},
        )
        assert resp.status_code == 404
        assert resp.json()["detail"]["code"] == "not_found"

    def test_404_emits_audit_attempt_and_error(
        self,
        client: TestClient,
        captured_audit_events: list[dict[str, Any]],
    ) -> None:
        """A probing enumeration of assessment ids must be auditable —
        the miss emits an ``attempt`` followed by an ``error`` event
        with the clinician id, not silent."""
        client.get(
            "/v1/reports/fhir/observations/never-existed",
            headers={"X-Clinician-Id": "c1"},
        )
        events = [e["event"] for e in captured_audit_events]
        assert "phi.access.attempt" in events
        assert "phi.access.error" in events
        error_event = next(
            e for e in captured_audit_events if e["event"] == "phi.access.error"
        )
        assert error_event["error"] == "not_found"
        assert error_event["actor_id"] == "c1"


# ---- Numeric-scored instruments (valueInteger path) ---------------------


class TestNumericInstruments:
    @pytest.mark.parametrize(
        ("instrument", "items", "expected_loinc", "extra"),
        [
            (
                "phq9",
                [0, 0, 0, 0, 0, 0, 0, 0, 0],
                "44261-6",
                {},
            ),
            (
                "gad7",
                [1, 1, 1, 1, 1, 1, 1],
                "69737-5",
                {},
            ),
            (
                "who5",
                [5, 5, 5, 5, 5],
                "89708-7",
                {},
            ),
            (
                "audit_c",
                [4, 4, 4],
                "75624-7",
                {"sex": "male"},
            ),
            (
                "pss10",
                [2, 2, 2, 2, 2, 2, 2, 2, 2, 2],
                "93038-1",
                {},
            ),
            (
                "dast10",
                [1, 0, 1, 0, 0, 0, 0, 0, 0, 0],
                "82667-7",
                {},
            ),
        ],
    )
    def test_numeric_instrument_renders_observation(
        self,
        client: TestClient,
        instrument: str,
        items: list[int],
        expected_loinc: str,
        extra: dict[str, Any],
    ) -> None:
        aid = _submit(
            client, user_id="u-num", instrument=instrument, items=items, **extra
        )
        resp = client.get(
            f"/v1/reports/fhir/observations/{aid}",
            headers={"X-Clinician-Id": "c-num"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["resourceType"] == "Observation"
        assert body["status"] == "final"
        # The LOINC code is the interop anchor — a silently mis-coded
        # observation is a compliance defect per fhir_observation docstring.
        assert body["code"]["coding"][0]["code"] == expected_loinc
        assert body["subject"]["reference"] == "Patient/u-num"
        assert "valueInteger" in body
        # effectiveDateTime is ISO8601 with Z suffix.
        assert body["effectiveDateTime"].endswith("Z")

    def test_phi_boundary_header_on_success(self, client: TestClient) -> None:
        aid = _submit(
            client,
            user_id="u-phi",
            instrument="phq9",
            items=[0, 0, 0, 0, 0, 0, 0, 0, 0],
        )
        resp = client.get(
            f"/v1/reports/fhir/observations/{aid}",
            headers={"X-Clinician-Id": "c-phi"},
        )
        assert resp.status_code == 200
        assert resp.headers.get("X-Phi-Boundary") == "1"


# ---- C-SSRS (valueCodeableConcept path) ---------------------------------


class TestCssrs:
    def test_cssrs_renders_categorical_observation(
        self, client: TestClient
    ) -> None:
        """C-SSRS produces ``valueCodeableConcept`` (categorical
        risk band), not ``valueInteger`` — this test pins the wire
        shape change relative to the numeric instruments."""
        aid = _submit(
            client,
            user_id="u-cssrs",
            instrument="cssrs",
            # Item 4 positive → acute T3 per Posner 2011.
            items=[0, 0, 0, 1, 0, 0],
        )
        resp = client.get(
            f"/v1/reports/fhir/observations/{aid}",
            headers={"X-Clinician-Id": "c-cssrs"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["resourceType"] == "Observation"
        # Categorical path: no valueInteger, yes valueCodeableConcept.
        assert "valueInteger" not in body
        assert "valueCodeableConcept" in body
        # Risk band string flows through.
        coding = body["valueCodeableConcept"]["coding"][0]
        assert coding["code"] == "acute"

    def test_cssrs_triggering_items_become_components(
        self, client: TestClient
    ) -> None:
        """Each triggering item becomes a FHIR ``component`` entry so
        receiving EHRs see which items fired without needing the raw
        item responses."""
        aid = _submit(
            client,
            user_id="u-cssrs",
            instrument="cssrs",
            items=[0, 0, 0, 1, 1, 0],  # items 4 + 5 fire → acute
        )
        resp = client.get(
            f"/v1/reports/fhir/observations/{aid}",
            headers={"X-Clinician-Id": "c-cssrs"},
        )
        components = resp.json()["component"]
        assert len(components) == 2
        codes = [c["code"]["coding"][0]["code"] for c in components]
        assert codes == ["item-4", "item-5"]

    def test_cssrs_acute_emits_interpretation(
        self, client: TestClient
    ) -> None:
        """Acute C-SSRS (T3) surfaces the safety-routing interpretation
        block — receiving EHRs key off this across PHQ-9 and C-SSRS
        uniformly."""
        aid = _submit(
            client,
            user_id="u-cssrs",
            instrument="cssrs",
            items=[0, 0, 0, 1, 0, 0],
        )
        resp = client.get(
            f"/v1/reports/fhir/observations/{aid}",
            headers={"X-Clinician-Id": "c-cssrs"},
        )
        body = resp.json()
        assert "interpretation" in body
        assert (
            body["interpretation"][0]["coding"][0]["code"] == "t3-routed"
        )

    def test_cssrs_none_risk_has_no_interpretation(
        self, client: TestClient
    ) -> None:
        """No T3 → no interpretation block — the absence is the signal
        to receiving systems that no safety routing fired."""
        aid = _submit(
            client,
            user_id="u-cssrs",
            instrument="cssrs",
            items=[0, 0, 0, 0, 0, 0],
        )
        resp = client.get(
            f"/v1/reports/fhir/observations/{aid}",
            headers={"X-Clinician-Id": "c-cssrs"},
        )
        body = resp.json()
        assert body["valueCodeableConcept"]["coding"][0]["code"] == "none"
        assert "interpretation" not in body


# ---- Safety routing on numeric instruments ------------------------------


class TestSafetyRouting:
    def test_phq9_item9_positive_emits_interpretation(
        self, client: TestClient
    ) -> None:
        """PHQ-9 with item 9 positive routes T3 — the rendered
        observation must carry the interpretation block that receiving
        EHRs branch on."""
        aid = _submit(
            client,
            user_id="u-phq",
            instrument="phq9",
            items=[0, 0, 0, 0, 0, 0, 0, 0, 1],
        )
        resp = client.get(
            f"/v1/reports/fhir/observations/{aid}",
            headers={"X-Clinician-Id": "c-phq"},
        )
        body = resp.json()
        assert "interpretation" in body
        assert body["interpretation"][0]["coding"][0]["code"] == "t3-routed"

    def test_phq9_safe_response_has_no_interpretation(
        self, client: TestClient
    ) -> None:
        aid = _submit(
            client,
            user_id="u-phq",
            instrument="phq9",
            items=[0, 0, 0, 0, 0, 0, 0, 0, 0],
        )
        resp = client.get(
            f"/v1/reports/fhir/observations/{aid}",
            headers={"X-Clinician-Id": "c-phq"},
        )
        assert "interpretation" not in resp.json()


# ---- Audit emission ------------------------------------------------------


class TestAuditEmission:
    def test_success_emits_attempt_and_ok(
        self,
        client: TestClient,
        captured_audit_events: list[dict[str, Any]],
    ) -> None:
        aid = _submit(
            client,
            user_id="u-audit",
            instrument="phq9",
            items=[0, 0, 0, 0, 0, 0, 0, 0, 0],
        )
        captured_audit_events.clear()  # drop POST-path audit noise

        resp = client.get(
            f"/v1/reports/fhir/observations/{aid}",
            headers={"X-Clinician-Id": "c-audit"},
        )
        assert resp.status_code == 200
        events = [e["event"] for e in captured_audit_events]
        assert "phi.access.attempt" in events
        assert "phi.access.ok" in events
        ok_event = next(
            e for e in captured_audit_events if e["event"] == "phi.access.ok"
        )
        assert ok_event["actor_id"] == "c-audit"
        assert ok_event["actor_role"] == "clinician"
        assert ok_event["subject_id"] == "u-audit"
        assert ok_event["resource"] == "fhir.observation"
        assert ok_event["resource_id"] == aid
        assert ok_event["instrument"] == "phq9"

    def test_correlation_id_passes_through(
        self,
        client: TestClient,
        captured_audit_events: list[dict[str, Any]],
    ) -> None:
        """``X-Correlation-Id`` is echoed into the audit record so an
        operator tracing a patient-initiated support ticket can
        correlate the clinician's PHI read back to the originating
        request."""
        aid = _submit(
            client,
            user_id="u-corr",
            instrument="phq9",
            items=[0, 0, 0, 0, 0, 0, 0, 0, 0],
        )
        captured_audit_events.clear()

        client.get(
            f"/v1/reports/fhir/observations/{aid}",
            headers={
                "X-Clinician-Id": "c-corr",
                "X-Correlation-Id": "corr-abc-123",
            },
        )
        attempt = next(
            e
            for e in captured_audit_events
            if e["event"] == "phi.access.attempt"
        )
        assert attempt["correlation_id"] == "corr-abc-123"


# ---- Cross-user clinician access ----------------------------------------


class TestCrossUserAccess:
    def test_clinician_can_read_any_patients_observation(
        self, client: TestClient
    ) -> None:
        """Clinician access is cross-patient by role — the endpoint
        does NOT filter by actor_id == subject_id.  That's the
        clinician-portal shape; patient-portal access goes through
        /v1/assessments/history which IS user-scoped.

        When real Clerk role-gating lands, the clinician role claim
        is what makes this defensible; today the header-based stub
        simulates that authorization contract.
        """
        aid = _submit(
            client,
            user_id="patient-A",
            instrument="phq9",
            items=[0, 0, 0, 0, 0, 0, 0, 0, 0],
        )
        resp = client.get(
            f"/v1/reports/fhir/observations/{aid}",
            headers={"X-Clinician-Id": "c-cross"},
        )
        assert resp.status_code == 200
        # Subject reference ties the rendered observation to the
        # original patient, not the requesting clinician.
        assert resp.json()["subject"]["reference"] == "Patient/patient-A"


# ---- Unsupported-instrument defense-in-depth -----------------------------


class TestUnsupportedInstrument:
    def test_record_with_unknown_instrument_returns_422(
        self, client: TestClient
    ) -> None:
        """A record stored under an instrument string that LOINC_CODES
        doesn't map (e.g. a future scorer not yet registered with
        ``fhir_observation``) must surface as 422 at this surface, not
        a 500.  We save directly to the repository because the router
        would reject an unknown instrument at the POST layer."""
        repo = get_assessment_repository()
        record = AssessmentRecord(
            assessment_id="odd-instrument-1",
            user_id="u-x",
            instrument="future_instrument",
            total=5,
            severity="unknown",
            requires_t3=False,
            raw_items=(1, 2, 3),
            created_at=datetime(2026, 4, 18, tzinfo=timezone.utc),
        )
        repo.save(record)
        resp = client.get(
            "/v1/reports/fhir/observations/odd-instrument-1",
            headers={"X-Clinician-Id": "c-x"},
        )
        assert resp.status_code == 422
        assert (
            resp.json()["detail"]["code"] == "validation.unsupported_instrument"
        )

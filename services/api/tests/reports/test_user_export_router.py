"""User Right-of-Access HTTP endpoint tests.

This route is a PHI surface (CLAUDE.md Rule #11) and an audited surface
(Rule #6).  The tests enforce both contracts directly — a regression
in either is an HIPAA-adjacent defect.

Self-access-only discipline: ``actor_id`` must equal ``user_id``.  A
clinician exporting a patient's data must use the clinician-bundle
endpoint, which runs a different audit tag.  The 403 path is tested
explicitly because silently routing cross-user access through would be
a privacy incident.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

import pytest
from fastapi.testclient import TestClient

from discipline.app import create_app
from discipline.shared.http.phi_boundary import (
    PHI_BOUNDARY_HEADER,
    PHI_BOUNDARY_VALUE,
)
from discipline.shared.logging import LogStream, get_stream_logger


# ---- Fixtures --------------------------------------------------------------


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


@pytest.fixture
def captured_audit_events(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, Any]]:
    """Intercept audit-stream emissions.

    See test_clinician_bundle_router.py for the rationale behind
    monkeypatching the BoundLogger directly instead of capturing stdout."""
    captured: list[dict[str, Any]] = []
    audit = get_stream_logger(LogStream.AUDIT)

    def _capture(level: str):
        def inner(event: str, **kwargs: Any) -> None:
            captured.append({"level": level, "event": event, **kwargs})

        return inner

    monkeypatch.setattr(audit, "info", _capture("info"))
    monkeypatch.setattr(audit, "warning", _capture("warning"))
    return captured


def _request_payload(
    *,
    actor_id: str = "user-001",
    user_id: str = "user-001",
    locale: str = "en",
    profile: dict[str, Any] | None = None,
    psychometric_scores: list[dict[str, Any]] | None = None,
    intervention_events: list[dict[str, Any]] | None = None,
    resilience_streak: dict[str, Any] | None = None,
    safety_events: list[dict[str, Any]] | None = None,
    consents: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Minimal valid payload — actor == user (self-access) + one record."""
    return {
        "actor_id": actor_id,
        "user_id": user_id,
        "locale": locale,
        "profile": profile if profile is not None else {"display_name": "Alex"},
        "psychometric_scores": (
            psychometric_scores
            if psychometric_scores is not None
            else [
                {
                    "instrument": "phq9",
                    "score": 8,
                    "effective": "2026-04-10T12:00:00Z",
                }
            ]
        ),
        "intervention_events": intervention_events or [],
        "resilience_streak": resilience_streak or {},
        "safety_events": safety_events or [],
        "consents": consents or [],
    }


# =============================================================================
# Happy path
# =============================================================================


class TestHappyPath:
    def test_returns_200(self, client: TestClient) -> None:
        resp = client.post("/v1/reports/user/export", json=_request_payload())
        assert resp.status_code == 200

    def test_response_carries_manifest_and_archive(self, client: TestClient) -> None:
        """Body shape: ``{user_id, manifest_sha256, archive_json,
        pdf_summary_available}``.  Clients re-encode ``archive_json`` to
        bytes and re-hash it to verify the manifest."""
        resp = client.post("/v1/reports/user/export", json=_request_payload())
        body = resp.json()
        assert body["user_id"] == "user-001"
        assert isinstance(body["manifest_sha256"], str)
        assert len(body["manifest_sha256"]) == 64
        assert isinstance(body["archive_json"], str)
        assert body["pdf_summary_available"] is False

    def test_manifest_verifiable_by_client(self, client: TestClient) -> None:
        """Client-side verification round-trip.  A user who receives
        their archive and wants to verify it wasn't tampered with
        re-encodes the JSON and recomputes the sha256 — must match."""
        resp = client.post("/v1/reports/user/export", json=_request_payload())
        body = resp.json()
        recomputed = hashlib.sha256(
            body["archive_json"].encode("utf-8")
        ).hexdigest()
        assert recomputed == body["manifest_sha256"]

    def test_archive_json_is_valid_json(self, client: TestClient) -> None:
        resp = client.post("/v1/reports/user/export", json=_request_payload())
        parsed = json.loads(resp.json()["archive_json"])
        assert parsed["user_id"] == "user-001"
        assert parsed["locale"] == "en"
        assert "sections" in parsed


# =============================================================================
# PHI boundary — Rule #11
# =============================================================================


class TestPhiBoundary:
    def test_successful_response_carries_phi_header(
        self, client: TestClient
    ) -> None:
        resp = client.post("/v1/reports/user/export", json=_request_payload())
        assert resp.status_code == 200
        assert resp.headers.get(PHI_BOUNDARY_HEADER) == PHI_BOUNDARY_VALUE

    def test_403_response_still_carries_phi_header(self, client: TestClient) -> None:
        """Even on denial, the request entered the PHI boundary — the
        header must reflect that so the log correlator can detect
        cross-user access attempts."""
        resp = client.post(
            "/v1/reports/user/export",
            json=_request_payload(actor_id="other-user"),
        )
        assert resp.status_code == 403
        assert resp.headers.get(PHI_BOUNDARY_HEADER) == PHI_BOUNDARY_VALUE

    def test_422_response_still_carries_phi_header(self, client: TestClient) -> None:
        """Empty-payload 422s also entered the PHI boundary before
        refusing."""
        payload = _request_payload()
        payload["profile"] = {}
        payload["psychometric_scores"] = []
        payload["intervention_events"] = []
        payload["resilience_streak"] = {}
        payload["safety_events"] = []
        payload["consents"] = []
        resp = client.post("/v1/reports/user/export", json=payload)
        assert resp.status_code == 422
        assert resp.headers.get(PHI_BOUNDARY_HEADER) == PHI_BOUNDARY_VALUE


# =============================================================================
# Self-access discipline — actor_id == user_id
# =============================================================================


class TestSelfAccessOnly:
    def test_cross_user_returns_403(self, client: TestClient) -> None:
        """A clinician exporting a patient must use the clinician-bundle
        endpoint.  This route is self-access only — the guard prevents
        someone from accidentally chaining the audit tags and losing
        the distinction between 'user exported own data' and 'clinician
        exported patient data' in the audit retention pool."""
        resp = client.post(
            "/v1/reports/user/export",
            json=_request_payload(actor_id="clin-042", user_id="user-001"),
        )
        assert resp.status_code == 403
        assert resp.json()["detail"]["code"] == "auth.self_access_only"

    def test_cross_user_attempt_is_audited(
        self,
        client: TestClient,
        captured_audit_events: list[dict[str, Any]],
    ) -> None:
        """The audit trail MUST show the failed attempt — silent denial
        without audit would hide a cross-user access attempt from
        compliance review."""
        client.post(
            "/v1/reports/user/export",
            json=_request_payload(actor_id="clin-042", user_id="user-001"),
        )
        mismatch_events = [
            e
            for e in captured_audit_events
            if e.get("event") == "user.export.error"
            and e.get("error") == "actor_subject_mismatch"
        ]
        assert len(mismatch_events) == 1
        event = mismatch_events[0]
        assert event["actor_id"] == "clin-042"
        assert event["subject_id"] == "user-001"

    def test_self_access_permitted(self, client: TestClient) -> None:
        resp = client.post(
            "/v1/reports/user/export",
            json=_request_payload(actor_id="user-001", user_id="user-001"),
        )
        assert resp.status_code == 200


# =============================================================================
# Audit emission pattern — Rule #6 dual-event
# =============================================================================


class TestAuditEmission:
    def test_happy_path_emits_attempt_and_ok(
        self,
        client: TestClient,
        captured_audit_events: list[dict[str, Any]],
    ) -> None:
        """Mirror of the clinician-bundle pattern: ``attempt`` before
        build, ``ok`` after success.  Both must appear, in that order."""
        client.post("/v1/reports/user/export", json=_request_payload())
        events = [e["event"] for e in captured_audit_events]
        assert "user.export.attempt" in events
        assert "user.export.ok" in events
        assert events.index("user.export.attempt") < events.index(
            "user.export.ok"
        )

    def test_ok_event_carries_manifest_sha256(
        self,
        client: TestClient,
        captured_audit_events: list[dict[str, Any]],
    ) -> None:
        """The manifest sha256 in the audit stream is the tamper-evidence
        anchor — a user disputing an archive compares the audited
        manifest to the archive they received.  If this kwarg is missing,
        the audit becomes unverifiable."""
        resp = client.post("/v1/reports/user/export", json=_request_payload())
        ok = next(
            e
            for e in captured_audit_events
            if e.get("event") == "user.export.ok"
        )
        assert ok["manifest_sha256"] == resp.json()["manifest_sha256"]
        assert ok["subject_id"] == "user-001"
        assert ok["actor_id"] == "user-001"
        assert ok["actor_role"] == "user"
        assert "archive_size_bytes" in ok

    def test_empty_export_emits_error_audit(
        self,
        client: TestClient,
        captured_audit_events: list[dict[str, Any]],
    ) -> None:
        """A user with zero records on every section — the attempt is
        audited (they tried), then the error is audited.  Both rows
        land in the 6-year retention pool."""
        payload = _request_payload()
        payload["profile"] = {}
        payload["psychometric_scores"] = []
        payload["intervention_events"] = []
        payload["resilience_streak"] = {}
        payload["safety_events"] = []
        payload["consents"] = []
        client.post("/v1/reports/user/export", json=payload)

        attempt = [
            e
            for e in captured_audit_events
            if e.get("event") == "user.export.attempt"
        ]
        errors = [
            e
            for e in captured_audit_events
            if e.get("event") == "user.export.error"
        ]
        assert len(attempt) == 1
        assert len(errors) == 1
        assert errors[0]["error"] == "empty_export"

    def test_no_ok_event_on_empty_export(
        self,
        client: TestClient,
        captured_audit_events: list[dict[str, Any]],
    ) -> None:
        """Negative assertion: a failed export must NOT emit ``ok`` —
        otherwise a misconfigured audit query counting 'ok' events
        would overcount."""
        payload = _request_payload()
        payload["profile"] = {}
        payload["psychometric_scores"] = []
        payload["intervention_events"] = []
        payload["resilience_streak"] = {}
        payload["safety_events"] = []
        payload["consents"] = []
        client.post("/v1/reports/user/export", json=payload)

        ok_events = [
            e
            for e in captured_audit_events
            if e.get("event") == "user.export.ok"
        ]
        assert len(ok_events) == 0


# =============================================================================
# Validation
# =============================================================================


class TestValidation:
    def test_missing_actor_id_rejected(self, client: TestClient) -> None:
        payload = _request_payload()
        del payload["actor_id"]
        resp = client.post("/v1/reports/user/export", json=payload)
        assert resp.status_code == 422

    def test_missing_user_id_rejected(self, client: TestClient) -> None:
        payload = _request_payload()
        del payload["user_id"]
        resp = client.post("/v1/reports/user/export", json=payload)
        assert resp.status_code == 422

    def test_empty_locale_rejected(self, client: TestClient) -> None:
        """Locale must be at least 2 chars (ISO 639-1).  An empty locale
        would propagate into the archive as ``"locale": ""`` which would
        break client-side rendering of locale-dependent fields."""
        resp = client.post(
            "/v1/reports/user/export",
            json=_request_payload(locale=""),
        )
        assert resp.status_code == 422

    def test_all_empty_sections_returns_422(self, client: TestClient) -> None:
        """Same behavior as the builder's ``EmptyExportError`` — the
        error surface is a 422 with a stable error code, not 500."""
        payload = _request_payload()
        payload["profile"] = {}
        payload["psychometric_scores"] = []
        payload["intervention_events"] = []
        payload["resilience_streak"] = {}
        payload["safety_events"] = []
        payload["consents"] = []
        resp = client.post("/v1/reports/user/export", json=payload)
        assert resp.status_code == 422
        assert resp.json()["detail"]["code"] == "validation.empty_export"


# =============================================================================
# Wire format / archive integrity
# =============================================================================


class TestArchiveIntegrity:
    def test_archive_contains_supplied_sections(self, client: TestClient) -> None:
        """End-to-end: what goes into the request body appears in the
        archive's sections block.  If a future refactor drops a section
        silently, this catches it."""
        resp = client.post(
            "/v1/reports/user/export",
            json=_request_payload(
                profile={"display_name": "Farida"},
                psychometric_scores=[
                    {"instrument": "gad7", "score": 12, "effective": "2026-04-05Z"}
                ],
                intervention_events=[{"event": "urge.recorded", "intensity": 6}],
                safety_events=[{"event": "cssrs.item1", "at": "2026-04-02Z"}],
                consents=[{"kind": "research", "accepted_at": "2026-01-01Z"}],
            ),
        )
        parsed = json.loads(resp.json()["archive_json"])
        sections = parsed["sections"]
        assert sections["profile"] == {"display_name": "Farida"}
        assert len(sections["psychometric_scores"]) == 1
        assert len(sections["intervention_events"]) == 1
        assert len(sections["safety_events"]) == 1
        assert len(sections["consents"]) == 1

    def test_non_latin_display_name_preserved_through_wire(
        self, client: TestClient
    ) -> None:
        """End-to-end Unicode — the profile name survives Pydantic +
        JSON serialize + HTTP + client-side decode + json.loads round-
        trip without getting ``\\uXXXX``-escaped or mangled."""
        resp = client.post(
            "/v1/reports/user/export",
            json=_request_payload(profile={"display_name": "علي"}),
        )
        parsed = json.loads(resp.json()["archive_json"])
        assert parsed["sections"]["profile"]["display_name"] == "علي"

    def test_pdf_summary_marked_unavailable(self, client: TestClient) -> None:
        """PDF is deferred — the flag ``pdf_summary_available`` must be
        ``False`` so clients don't try to render a download link for
        something that isn't there yet."""
        resp = client.post("/v1/reports/user/export", json=_request_payload())
        assert resp.json()["pdf_summary_available"] is False

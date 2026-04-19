"""Clinician FHIR bundle endpoint tests.

This is the live PHI surface (CLAUDE.md Rule #11): every test here is an
interop or compliance contract.

Coverage matrix:
- Happy path: bundle assembled, X-Phi-Boundary header set, audit events
  emitted before + after assembly.
- Validation: empty observation list rejected, unknown instrument rejected
  with 422 + audit error event.
- Safety routing: a safety-positive Observation flows through and the
  resulting Bundle includes the interpretation array.
- Audit emission shape: actor_id, subject_id, bundle_identifier present.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

import pytest
from fastapi.testclient import TestClient

from discipline.app import create_app
from discipline.shared.logging import LogStream, get_stream_logger


# ---- Fixtures --------------------------------------------------------------


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


@pytest.fixture
def captured_audit_events(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, Any]]:
    """Intercept audit-stream emissions so tests can assert on them.

    We monkeypatch the stream's BoundLogger ``info`` / ``warning`` methods
    rather than capturing stdout because structlog's renderer writes
    one-JSON-per-line which is brittle to parse, and the BoundLogger is
    the canonical entry point — a test that intercepts there proves the
    router is using the right surface."""
    captured: list[dict[str, Any]] = []
    audit = get_stream_logger(LogStream.AUDIT)

    def _capture(level: str):
        def inner(event: str, **kwargs: Any) -> None:
            captured.append({"level": level, "event": event, **kwargs})
        return inner

    monkeypatch.setattr(audit, "info", _capture("info"))
    monkeypatch.setattr(audit, "warning", _capture("warning"))
    return captured


def _spec_payload(
    *,
    instrument: str = "phq9",
    score: int = 8,
    safety_positive: bool = False,
    patient_reference: str = "Patient/test-001",
) -> dict[str, Any]:
    return {
        "patient_reference": patient_reference,
        "instrument": instrument,
        "score": score,
        "effective": "2026-04-18T12:00:00+00:00",
        "safety_item_positive": safety_positive,
        "status": "final",
    }


def _request_payload(
    *,
    clinician_id: str = "clin-001",
    patient_id: str = "pt-001",
    observations: list[dict[str, Any]] | None = None,
    correlation_id: str | None = None,
    bundle_type: str = "collection",
) -> dict[str, Any]:
    return {
        "clinician_id": clinician_id,
        "patient_id": patient_id,
        # Explicit None-check: an empty list is a valid (albeit invalid)
        # caller intent that we want to forward to the validator.
        "observations": [_spec_payload()] if observations is None else observations,
        "bundle_type": bundle_type,
        "correlation_id": correlation_id,
    }


# =============================================================================
# Happy path
# =============================================================================


class TestHappyPath:
    def test_returns_200_with_bundle_resource(self, client: TestClient) -> None:
        resp = client.post(
            "/v1/reports/fhir/clinician-bundle",
            json=_request_payload(),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["resourceType"] == "Bundle"
        assert body["type"] == "collection"
        assert len(body["entry"]) == 1

    def test_phi_boundary_header_set(self, client: TestClient) -> None:
        """Rule #11: every PHI response carries this header so the log
        correlator can cross-reference audit + app streams."""
        resp = client.post(
            "/v1/reports/fhir/clinician-bundle",
            json=_request_payload(),
        )
        assert resp.headers.get("X-Phi-Boundary") == "1"

    def test_response_is_json_serializable(self, client: TestClient) -> None:
        """The returned dict must be json.dumps-safe — no leaked datetimes
        or UUID objects from the assembler."""
        resp = client.post(
            "/v1/reports/fhir/clinician-bundle",
            json=_request_payload(),
        )
        # If the response is JSON, this round-trips cleanly.
        json.dumps(resp.json())

    def test_multi_observation_bundle(self, client: TestClient) -> None:
        observations = [
            _spec_payload(instrument="phq9", score=8),
            _spec_payload(instrument="gad7", score=5),
            _spec_payload(instrument="who5", score=64),
        ]
        resp = client.post(
            "/v1/reports/fhir/clinician-bundle",
            json=_request_payload(observations=observations),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["entry"]) == 3
        # Ordering preserved
        scores = [e["resource"]["valueInteger"] for e in body["entry"]]
        assert scores == [8, 5, 64]


# =============================================================================
# Audit emission
# =============================================================================


class TestAuditEmission:
    def test_attempt_event_fires_before_assembly(
        self,
        client: TestClient,
        captured_audit_events: list[dict[str, Any]],
    ) -> None:
        client.post(
            "/v1/reports/fhir/clinician-bundle",
            json=_request_payload(clinician_id="clin-007", patient_id="pt-042"),
        )
        attempt = next(
            e for e in captured_audit_events if e["event"] == "phi.access.attempt"
        )
        assert attempt["actor_id"] == "clin-007"
        assert attempt["actor_role"] == "clinician"
        assert attempt["subject_id"] == "pt-042"
        assert attempt["resource"] == "fhir.bundle"
        assert attempt["resource_count"] == 1

    def test_ok_event_fires_after_successful_assembly(
        self,
        client: TestClient,
        captured_audit_events: list[dict[str, Any]],
    ) -> None:
        client.post(
            "/v1/reports/fhir/clinician-bundle",
            json=_request_payload(clinician_id="clin-007", patient_id="pt-042"),
        )
        ok = next(e for e in captured_audit_events if e["event"] == "phi.access.ok")
        assert ok["actor_id"] == "clin-007"
        assert ok["subject_id"] == "pt-042"
        assert ok["bundle_identifier"] is not None
        assert ok["bundle_identifier"].startswith("urn:uuid:")
        assert ok["observation_count"] == 1

    def test_attempt_and_ok_both_fire_in_order(
        self,
        client: TestClient,
        captured_audit_events: list[dict[str, Any]],
    ) -> None:
        client.post(
            "/v1/reports/fhir/clinician-bundle",
            json=_request_payload(),
        )
        events = [e["event"] for e in captured_audit_events]
        attempt_idx = events.index("phi.access.attempt")
        ok_idx = events.index("phi.access.ok")
        assert attempt_idx < ok_idx

    def test_correlation_id_threaded_into_attempt_event(
        self,
        client: TestClient,
        captured_audit_events: list[dict[str, Any]],
    ) -> None:
        """A caller-supplied correlation_id must round-trip into the audit
        record so external systems can stitch their trace to ours."""
        client.post(
            "/v1/reports/fhir/clinician-bundle",
            json=_request_payload(correlation_id="external-trace-123"),
        )
        attempt = next(
            e for e in captured_audit_events if e["event"] == "phi.access.attempt"
        )
        assert attempt["correlation_id"] == "external-trace-123"


# =============================================================================
# Validation + error paths
# =============================================================================


class TestValidationErrors:
    def test_empty_observations_rejected_at_pydantic_layer(
        self, client: TestClient
    ) -> None:
        """Pydantic min_length=1 catches this before it hits the assembler."""
        resp = client.post(
            "/v1/reports/fhir/clinician-bundle",
            json=_request_payload(observations=[]),
        )
        assert resp.status_code == 422

    def test_unknown_instrument_returns_422_with_supported_list(
        self,
        client: TestClient,
    ) -> None:
        """The error response surfaces the supported instrument list so the
        client can self-correct without trial-and-error."""
        resp = client.post(
            "/v1/reports/fhir/clinician-bundle",
            json=_request_payload(
                observations=[_spec_payload(instrument="not_an_instrument")],
            ),
        )
        assert resp.status_code == 422
        detail = resp.json()["detail"]
        assert detail["code"] == "validation.unsupported_instrument"
        assert "phq9" in detail["supported_instruments"]
        assert "gad7" in detail["supported_instruments"]

    def test_unknown_instrument_emits_audit_error_event(
        self,
        client: TestClient,
        captured_audit_events: list[dict[str, Any]],
    ) -> None:
        """A failed PHI access is itself auditable — clinician X tried to
        read patient Y's data; we must record that even if it errored."""
        client.post(
            "/v1/reports/fhir/clinician-bundle",
            json=_request_payload(
                observations=[_spec_payload(instrument="not_an_instrument")],
            ),
        )
        # Both events fire: attempt before assembly, error after.
        events = [e["event"] for e in captured_audit_events]
        assert "phi.access.attempt" in events
        assert "phi.access.error" in events
        error_evt = next(
            e for e in captured_audit_events if e["event"] == "phi.access.error"
        )
        assert error_evt["error"] == "unsupported_instrument"

    def test_negative_score_rejected_at_pydantic_layer(
        self, client: TestClient
    ) -> None:
        resp = client.post(
            "/v1/reports/fhir/clinician-bundle",
            json=_request_payload(observations=[_spec_payload(score=-1)]),
        )
        assert resp.status_code == 422

    def test_missing_clinician_id_rejected(self, client: TestClient) -> None:
        payload = _request_payload()
        del payload["clinician_id"]
        resp = client.post("/v1/reports/fhir/clinician-bundle", json=payload)
        assert resp.status_code == 422


# =============================================================================
# Safety-positive routing
# =============================================================================


class TestSafetyPositiveBundle:
    def test_safety_positive_observation_carries_interpretation(
        self,
        client: TestClient,
    ) -> None:
        """A safety-positive Observation must surface the interpretation
        array in the Bundle so receiving systems can flag the result."""
        resp = client.post(
            "/v1/reports/fhir/clinician-bundle",
            json=_request_payload(
                observations=[_spec_payload(safety_positive=True)],
            ),
        )
        assert resp.status_code == 200
        observation = resp.json()["entry"][0]["resource"]
        assert "interpretation" in observation
        assert (
            observation["interpretation"][0]["coding"][0]["code"]
            == "t3-routed"
        )


# =============================================================================
# Bundle type override
# =============================================================================


class TestBundleTypeOverride:
    def test_default_is_collection(self, client: TestClient) -> None:
        resp = client.post(
            "/v1/reports/fhir/clinician-bundle",
            json=_request_payload(),
        )
        assert resp.json()["type"] == "collection"

    def test_document_type_passes_through(self, client: TestClient) -> None:
        resp = client.post(
            "/v1/reports/fhir/clinician-bundle",
            json=_request_payload(bundle_type="document"),
        )
        assert resp.json()["type"] == "document"


# =============================================================================
# Correlation-id-as-bundle-identifier
# =============================================================================


class TestCorrelationIdAsBundleIdentifier:
    def test_caller_correlation_id_lands_in_bundle_identifier(
        self,
        client: TestClient,
    ) -> None:
        """When the caller passes a correlation_id, it becomes the Bundle
        identifier — connecting the FHIR payload back to the caller's
        own trace ID."""
        resp = client.post(
            "/v1/reports/fhir/clinician-bundle",
            json=_request_payload(correlation_id="corr-9999"),
        )
        assert resp.json()["identifier"]["value"] == "urn:uuid:corr-9999"

    def test_no_correlation_id_yields_fresh_uuid(self, client: TestClient) -> None:
        resp = client.post(
            "/v1/reports/fhir/clinician-bundle",
            json=_request_payload(correlation_id=None),
        )
        assert resp.json()["identifier"]["value"].startswith("urn:uuid:")

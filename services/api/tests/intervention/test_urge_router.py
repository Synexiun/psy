"""Urge creation router tests.

``POST /v1/urges`` is the entry point for the 60–180 second intervention
window.  These tests verify the request contract and response shape; the
stub implementation will be replaced by UrgeService.open + BanditService.select.

``POST /v1/sos`` is tested in tests/test_sos_is_deterministic.py — this file
covers only the non-SOS urge endpoint.
"""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from discipline.app import create_app


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


_URL = "/v1/urges"
_IK_HEADER = {"Idempotency-Key": "test-urge-key"}


def _valid_payload(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "started_at": "2026-04-19T10:00:00Z",
        "intensity_start": 6,
        "trigger_tags": [],
    }
    base.update(overrides)
    return base


# =============================================================================
# TestUrgeHappyPath
# =============================================================================


class TestUrgeHappyPath:
    def test_happy_path_returns_201(self, client: TestClient) -> None:
        response = client.post(_URL, json=_valid_payload(), headers=_IK_HEADER)
        assert response.status_code == 201

    def test_response_has_urge_id(self, client: TestClient) -> None:
        body = client.post(_URL, json=_valid_payload(), headers=_IK_HEADER).json()
        urge_id = body["urge_id"]
        assert isinstance(urge_id, str)
        uuid.UUID(urge_id)

    def test_urge_id_is_unique_across_calls(self, client: TestClient) -> None:
        id1 = client.post(_URL, json=_valid_payload(), headers=_IK_HEADER).json()["urge_id"]
        id2 = client.post(_URL, json=_valid_payload(), headers={"Idempotency-Key": "key2"}).json()["urge_id"]
        assert id1 != id2

    def test_response_has_recommended_tool(self, client: TestClient) -> None:
        body = client.post(_URL, json=_valid_payload(), headers=_IK_HEADER).json()
        assert "recommended_tool" in body
        assert isinstance(body["recommended_tool"], dict)

    def test_recommended_tool_has_tool_variant(self, client: TestClient) -> None:
        body = client.post(_URL, json=_valid_payload(), headers=_IK_HEADER).json()
        assert "tool_variant" in body["recommended_tool"]

    def test_trigger_tags_defaults_to_empty_list(self, client: TestClient) -> None:
        """trigger_tags is optional; omitting it must still produce 201."""
        payload = {"started_at": "2026-04-19T10:00:00Z", "intensity_start": 4}
        response = client.post(_URL, json=payload, headers=_IK_HEADER)
        assert response.status_code == 201

    def test_trigger_tags_accepted_when_provided(self, client: TestClient) -> None:
        payload = _valid_payload(trigger_tags=["boredom", "social_event"])
        response = client.post(_URL, json=payload, headers=_IK_HEADER)
        assert response.status_code == 201

    def test_location_context_optional(self, client: TestClient) -> None:
        payload = _valid_payload(location_context="home")
        response = client.post(_URL, json=payload, headers=_IK_HEADER)
        assert response.status_code == 201

    def test_origin_defaults_to_self_reported(self, client: TestClient) -> None:
        """origin defaults to 'self_reported'; no need to supply it explicitly."""
        payload = {"started_at": "2026-04-19T10:00:00Z", "intensity_start": 5}
        response = client.post(_URL, json=payload, headers=_IK_HEADER)
        assert response.status_code == 201


# =============================================================================
# TestUrgeValidation
# =============================================================================


class TestUrgeValidation:
    def test_missing_idempotency_key_returns_422(self, client: TestClient) -> None:
        response = client.post(_URL, json=_valid_payload())
        assert response.status_code == 422

    def test_intensity_below_zero_rejected(self, client: TestClient) -> None:
        response = client.post(_URL, json=_valid_payload(intensity_start=-1), headers=_IK_HEADER)
        assert response.status_code == 422

    def test_intensity_above_ten_rejected(self, client: TestClient) -> None:
        response = client.post(_URL, json=_valid_payload(intensity_start=11), headers=_IK_HEADER)
        assert response.status_code == 422

    def test_intensity_at_minimum_boundary_accepted(self, client: TestClient) -> None:
        response = client.post(_URL, json=_valid_payload(intensity_start=0), headers=_IK_HEADER)
        assert response.status_code == 201

    def test_intensity_at_maximum_boundary_accepted(self, client: TestClient) -> None:
        response = client.post(_URL, json=_valid_payload(intensity_start=10), headers=_IK_HEADER)
        assert response.status_code == 201

    def test_missing_started_at_rejected(self, client: TestClient) -> None:
        payload = {"intensity_start": 5}
        response = client.post(_URL, json=payload, headers=_IK_HEADER)
        assert response.status_code == 422

    def test_missing_intensity_start_rejected(self, client: TestClient) -> None:
        payload = {"started_at": "2026-04-19T10:00:00Z"}
        response = client.post(_URL, json=payload, headers=_IK_HEADER)
        assert response.status_code == 422

    def test_empty_body_rejected(self, client: TestClient) -> None:
        response = client.post(_URL, json={}, headers=_IK_HEADER)
        assert response.status_code == 422

    def test_intensity_as_string_rejected(self, client: TestClient) -> None:
        response = client.post(
            _URL,
            json=_valid_payload(intensity_start="high"),
            headers=_IK_HEADER,
        )
        assert response.status_code == 422

    def test_all_intensity_values_in_range_accepted(self, client: TestClient) -> None:
        """Boundary sweep: every valid intensity value (0–10) produces 201."""
        for intensity in range(0, 11):
            response = client.post(
                _URL,
                json=_valid_payload(intensity_start=intensity),
                headers={"Idempotency-Key": f"key-{intensity}"},
            )
            assert response.status_code == 201, f"intensity_start={intensity} should be accepted"

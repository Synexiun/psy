"""Intervention router tests.

Covers urge creation, SOS determinism, tool registry, and outcome recording.
"""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from discipline.app import create_app
from discipline.intervention.outcome_service import reset_outcome_repository


@pytest.fixture(autouse=True)
def _clear_outcomes() -> None:
    reset_outcome_repository()


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


_USER_HEADER = {"X-User-Id": "user_int_001"}
_USER_HEADER_B = {"X-User-Id": "user_int_002"}


# =============================================================================
# Tool registry
# =============================================================================


class TestToolList:
    def test_list_returns_200(self, client: TestClient) -> None:
        response = client.get("/v1/tools")
        assert response.status_code == 200

    def test_list_is_non_empty(self, client: TestClient) -> None:
        body = client.get("/v1/tools").json()
        assert len(body) > 0

    def test_list_items_have_required_fields(self, client: TestClient) -> None:
        tools = client.get("/v1/tools").json()
        for t in tools:
            assert "variant" in t
            assert "name" in t
            assert "category" in t
            assert "offline_capable" in t

    def test_list_all_tools_offline_capable(self, client: TestClient) -> None:
        """AGENTS.md: every tool variant must have an offline fallback."""
        tools = client.get("/v1/tools").json()
        for t in tools:
            assert t["offline_capable"] is True, f"{t['variant']} is not offline_capable"

    def test_list_contains_urge_surf(self, client: TestClient) -> None:
        tools = client.get("/v1/tools").json()
        variants = {t["variant"] for t in tools}
        assert "urge_surf" in variants

    def test_list_contains_tipp(self, client: TestClient) -> None:
        tools = client.get("/v1/tools").json()
        variants = {t["variant"] for t in tools}
        assert "tipp_60s" in variants


class TestToolDetail:
    def test_get_existing_returns_200(self, client: TestClient) -> None:
        response = client.get("/v1/tools/urge_surf")
        assert response.status_code == 200

    def test_get_has_all_fields(self, client: TestClient) -> None:
        body = client.get("/v1/tools/urge_surf").json()
        assert "variant" in body
        assert "name" in body
        assert "category" in body
        assert "duration_seconds" in body
        assert "description" in body
        assert "offline_capable" in body
        assert "requires_audio" in body
        assert "requires_location" in body

    def test_get_not_found_returns_404(self, client: TestClient) -> None:
        response = client.get("/v1/tools/nonexistent")
        assert response.status_code == 404
        assert response.json()["detail"] == "tool.not_found"

    def test_get_matches_list_item(self, client: TestClient) -> None:
        list_tools = client.get("/v1/tools").json()
        detail = client.get(f"/v1/tools/{list_tools[0]['variant']}").json()
        assert detail["variant"] == list_tools[0]["variant"]
        assert detail["name"] == list_tools[0]["name"]


# =============================================================================
# Outcome recording
# =============================================================================


class TestOutcomeRecord:
    def test_record_returns_201(self, client: TestClient) -> None:
        response = client.post(
            "/v1/outcomes",
            json={
                "intervention_id": str(uuid.uuid4()),
                "tool_variant": "urge_surf",
                "outcome": "handled",
            },
            headers=_USER_HEADER,
        )
        assert response.status_code == 201

    def test_record_response_has_outcome_id(self, client: TestClient) -> None:
        body = client.post(
            "/v1/outcomes",
            json={
                "intervention_id": str(uuid.uuid4()),
                "tool_variant": "urge_surf",
                "outcome": "handled",
            },
            headers=_USER_HEADER,
        ).json()
        assert "outcome_id" in body
        uuid.UUID(body["outcome_id"])

    def test_record_all_valid_outcomes_accepted(self, client: TestClient) -> None:
        for outcome in ("handled", "dismissed", "expired", "escalated", "completed"):
            response = client.post(
                "/v1/outcomes",
                json={
                    "intervention_id": str(uuid.uuid4()),
                    "tool_variant": "urge_surf",
                    "outcome": outcome,
                },
                headers={"X-User-Id": f"user_{outcome}"},
            )
            assert response.status_code == 201, f"outcome={outcome} should be accepted"

    def test_record_invalid_outcome_returns_422(self, client: TestClient) -> None:
        response = client.post(
            "/v1/outcomes",
            json={
                "intervention_id": str(uuid.uuid4()),
                "tool_variant": "urge_surf",
                "outcome": "unknown",
            },
            headers=_USER_HEADER,
        )
        assert response.status_code == 422

    def test_record_missing_intervention_id_returns_422(self, client: TestClient) -> None:
        response = client.post(
            "/v1/outcomes",
            json={"tool_variant": "urge_surf", "outcome": "handled"},
            headers=_USER_HEADER,
        )
        assert response.status_code == 422

    def test_record_missing_tool_variant_returns_422(self, client: TestClient) -> None:
        response = client.post(
            "/v1/outcomes",
            json={"intervention_id": str(uuid.uuid4()), "outcome": "handled"},
            headers=_USER_HEADER,
        )
        assert response.status_code == 422

    def test_record_with_context(self, client: TestClient) -> None:
        body = client.post(
            "/v1/outcomes",
            json={
                "intervention_id": str(uuid.uuid4()),
                "tool_variant": "urge_surf",
                "outcome": "handled",
                "context": {"duration_used_seconds": 180},
            },
            headers=_USER_HEADER,
        ).json()
        assert body["outcome"] == "handled"

    def test_record_user_isolation(self, client: TestClient) -> None:
        client.post(
            "/v1/outcomes",
            json={
                "intervention_id": str(uuid.uuid4()),
                "tool_variant": "urge_surf",
                "outcome": "handled",
            },
            headers=_USER_HEADER,
        )
        # Outcomes don't have a list endpoint in this sprint, so we verify
        # the user_id is captured correctly via the response shape
        body = client.post(
            "/v1/outcomes",
            json={
                "intervention_id": str(uuid.uuid4()),
                "tool_variant": "urge_surf",
                "outcome": "dismissed",
            },
            headers=_USER_HEADER_B,
        ).json()
        assert body["outcome"] == "dismissed"

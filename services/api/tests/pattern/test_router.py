"""Pattern router tests — insight detection, listing, and dismissal.

Covers the four detector types (temporal, contextual, physiological,
compound), user isolation, and the dismiss lifecycle.
"""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from discipline.app import create_app
from discipline.pattern.repository import reset_pattern_repository
from discipline.pattern.service import reset_pattern_service


@pytest.fixture(autouse=True)
def _clear_pattern() -> None:
    reset_pattern_repository()
    reset_pattern_service()


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


_USER_HEADER = {"X-User-Id": "user_pat_001"}
_USER_HEADER_B = {"X-User-Id": "user_pat_002"}

_URL_LIST = "/v1/patterns"
_URL_MINE = "/v1/patterns/mine"


# =============================================================================
# Pattern mining
# =============================================================================


class TestPatternMine:
    def test_mine_returns_201(self, client: TestClient) -> None:
        response = client.post(_URL_MINE, headers=_USER_HEADER)
        assert response.status_code == 201

    def test_mine_creates_four_patterns(self, client: TestClient) -> None:
        body = client.post(_URL_MINE, headers=_USER_HEADER).json()
        assert body["mined_count"] == 4
        assert len(body["patterns"]) == 4

    def test_mine_pattern_types_are_valid(self, client: TestClient) -> None:
        body = client.post(_URL_MINE, headers=_USER_HEADER).json()
        types = {p["pattern_type"] for p in body["patterns"]}
        assert types == {"temporal", "contextual", "physiological", "compound"}

    def test_mine_each_pattern_has_required_fields(self, client: TestClient) -> None:
        body = client.post(_URL_MINE, headers=_USER_HEADER).json()
        for p in body["patterns"]:
            assert "pattern_id" in p
            uuid.UUID(p["pattern_id"])
            assert "detector" in p and isinstance(p["detector"], str)
            assert "confidence" in p
            assert "description" in p and isinstance(p["description"], str)
            assert "metadata" in p and isinstance(p["metadata"], dict)
            assert "status" in p
            assert "created_at" in p
            assert "updated_at" in p

    def test_mine_confidence_in_range(self, client: TestClient) -> None:
        body = client.post(_URL_MINE, headers=_USER_HEADER).json()
        for p in body["patterns"]:
            assert 0.0 <= p["confidence"] <= 1.0

    def test_mine_patterns_are_active_by_default(self, client: TestClient) -> None:
        body = client.post(_URL_MINE, headers=_USER_HEADER).json()
        for p in body["patterns"]:
            assert p["status"] == "active"
            assert p["dismissed_at"] is None
            assert p["dismiss_reason"] is None

    def test_mine_is_user_isolated(self, client: TestClient) -> None:
        body_a = client.post(_URL_MINE, headers=_USER_HEADER).json()
        body_b = client.post(_URL_MINE, headers=_USER_HEADER_B).json()
        ids_a = {p["pattern_id"] for p in body_a["patterns"]}
        ids_b = {p["pattern_id"] for p in body_b["patterns"]}
        assert ids_a.isdisjoint(ids_b)

    def test_mine_twice_creates_new_patterns(self, client: TestClient) -> None:
        """Mining is not idempotent — each run creates fresh records."""
        body1 = client.post(_URL_MINE, headers=_USER_HEADER).json()
        body2 = client.post(_URL_MINE, headers=_USER_HEADER).json()
        ids1 = {p["pattern_id"] for p in body1["patterns"]}
        ids2 = {p["pattern_id"] for p in body2["patterns"]}
        assert ids1.isdisjoint(ids2)


# =============================================================================
# Pattern listing
# =============================================================================


class TestPatternList:
    def test_list_empty_returns_200(self, client: TestClient) -> None:
        response = client.get(_URL_LIST, headers=_USER_HEADER)
        assert response.status_code == 200
        assert response.json() == []

    def test_list_returns_active_patterns(self, client: TestClient) -> None:
        client.post(_URL_MINE, headers=_USER_HEADER)
        response = client.get(_URL_LIST, headers=_USER_HEADER)
        assert response.status_code == 200
        body = response.json()
        assert len(body) == 4
        for p in body:
            assert p["status"] == "active"

    def test_list_excludes_dismissed_patterns(self, client: TestClient) -> None:
        mined = client.post(_URL_MINE, headers=_USER_HEADER).json()
        pattern_id = mined["patterns"][0]["pattern_id"]
        client.post(f"/v1/patterns/{pattern_id}/dismiss", json={}, headers=_USER_HEADER)
        listed = client.get(_URL_LIST, headers=_USER_HEADER).json()
        listed_ids = {p["pattern_id"] for p in listed}
        assert pattern_id not in listed_ids
        assert len(listed) == 3

    def test_list_respects_limit(self, client: TestClient) -> None:
        client.post(_URL_MINE, headers=_USER_HEADER)
        client.post(_URL_MINE, headers=_USER_HEADER)
        body = client.get(_URL_LIST, headers=_USER_HEADER, params={"limit": 3}).json()
        assert len(body) == 3

    def test_list_user_isolation(self, client: TestClient) -> None:
        client.post(_URL_MINE, headers=_USER_HEADER)
        body_b = client.get(_URL_LIST, headers=_USER_HEADER_B).json()
        assert body_b == []

    def test_list_orders_newest_first(self, client: TestClient) -> None:
        client.post(_URL_MINE, headers=_USER_HEADER)
        client.post(_URL_MINE, headers=_USER_HEADER)
        body = client.get(_URL_LIST, headers=_USER_HEADER).json()
        for i in range(len(body) - 1):
            assert body[i]["created_at"] >= body[i + 1]["created_at"]


# =============================================================================
# Pattern dismissal
# =============================================================================


class TestPatternDismiss:
    def test_dismiss_returns_200(self, client: TestClient) -> None:
        mined = client.post(_URL_MINE, headers=_USER_HEADER).json()
        pattern_id = mined["patterns"][0]["pattern_id"]
        response = client.post(
            f"/v1/patterns/{pattern_id}/dismiss",
            json={"reason": "not relevant"},
            headers=_USER_HEADER,
        )
        assert response.status_code == 200

    def test_dismiss_sets_status_to_dismissed(self, client: TestClient) -> None:
        mined = client.post(_URL_MINE, headers=_USER_HEADER).json()
        pattern_id = mined["patterns"][0]["pattern_id"]
        body = client.post(
            f"/v1/patterns/{pattern_id}/dismiss",
            json={},
            headers=_USER_HEADER,
        ).json()
        assert body["status"] == "dismissed"

    def test_dismiss_sets_dismissed_at(self, client: TestClient) -> None:
        mined = client.post(_URL_MINE, headers=_USER_HEADER).json()
        pattern_id = mined["patterns"][0]["pattern_id"]
        body = client.post(
            f"/v1/patterns/{pattern_id}/dismiss",
            json={},
            headers=_USER_HEADER,
        ).json()
        assert body["dismissed_at"] is not None
        assert isinstance(body["dismissed_at"], str)

    def test_dismiss_preserves_reason(self, client: TestClient) -> None:
        mined = client.post(_URL_MINE, headers=_USER_HEADER).json()
        pattern_id = mined["patterns"][0]["pattern_id"]
        body = client.post(
            f"/v1/patterns/{pattern_id}/dismiss",
            json={"reason": "already aware of this"},
            headers=_USER_HEADER,
        ).json()
        assert body["dismiss_reason"] == "already aware of this"

    def test_dismiss_unknown_returns_404(self, client: TestClient) -> None:
        response = client.post(
            "/v1/patterns/00000000-0000-0000-0000-000000000000/dismiss",
            json={},
            headers=_USER_HEADER,
        )
        assert response.status_code == 404

    def test_dismiss_cross_user_is_blocked(self, client: TestClient) -> None:
        mined = client.post(_URL_MINE, headers=_USER_HEADER).json()
        pattern_id = mined["patterns"][0]["pattern_id"]
        response = client.post(
            f"/v1/patterns/{pattern_id}/dismiss",
            json={},
            headers=_USER_HEADER_B,
        )
        assert response.status_code == 404

    def test_dismiss_without_reason_is_allowed(self, client: TestClient) -> None:
        mined = client.post(_URL_MINE, headers=_USER_HEADER).json()
        pattern_id = mined["patterns"][0]["pattern_id"]
        body = client.post(
            f"/v1/patterns/{pattern_id}/dismiss",
            json={},
            headers=_USER_HEADER,
        ).json()
        assert body["status"] == "dismissed"
        assert body["dismiss_reason"] is None

    def test_dismiss_updates_updated_at(self, client: TestClient) -> None:
        mined = client.post(_URL_MINE, headers=_USER_HEADER).json()
        pattern = mined["patterns"][0]
        dismissed = client.post(
            f"/v1/patterns/{pattern['pattern_id']}/dismiss",
            json={},
            headers=_USER_HEADER,
        ).json()
        assert dismissed["updated_at"] > pattern["updated_at"]

"""Notifications router tests.

Covers nudge scheduling, listing, dispatch, and push token registration.
"""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from discipline.app import create_app
from discipline.notifications.repository import reset_notification_repositories


@pytest.fixture(autouse=True)
def _clear_notifications() -> None:
    reset_notification_repositories()


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


_USER_HEADER = {"X-User-Id": "user_notif_001"}
_USER_HEADER_B = {"X-User-Id": "user_notif_002"}


# =============================================================================
# Nudge scheduling
# =============================================================================


class TestNudgeSchedule:
    def test_schedule_returns_201(self, client: TestClient) -> None:
        response = client.post(
            "/v1/nudges",
            json={
                "nudge_type": "check_in",
                "scheduled_at": "2026-04-23T10:00:00Z",
            },
            headers=_USER_HEADER,
        )
        assert response.status_code == 201

    def test_schedule_response_has_nudge_id(self, client: TestClient) -> None:
        body = client.post(
            "/v1/nudges",
            json={
                "nudge_type": "check_in",
                "scheduled_at": "2026-04-23T10:00:00Z",
            },
            headers=_USER_HEADER,
        ).json()
        assert "nudge_id" in body
        uuid.UUID(body["nudge_id"])

    def test_schedule_status_is_scheduled(self, client: TestClient) -> None:
        body = client.post(
            "/v1/nudges",
            json={
                "nudge_type": "check_in",
                "scheduled_at": "2026-04-23T10:00:00Z",
            },
            headers=_USER_HEADER,
        ).json()
        assert body["status"] == "scheduled"

    def test_schedule_all_valid_types_accepted(self, client: TestClient) -> None:
        for ntype in ("check_in", "tool_suggestion", "crisis_follow_up", "weekly_reflection"):
            response = client.post(
                "/v1/nudges",
                json={
                    "nudge_type": ntype,
                    "scheduled_at": "2026-04-23T10:00:00Z",
                },
                headers={"X-User-Id": f"user_{ntype}"},
            )
            assert response.status_code == 201, f"nudge_type={ntype} should be accepted"

    def test_schedule_invalid_type_returns_422(self, client: TestClient) -> None:
        response = client.post(
            "/v1/nudges",
            json={
                "nudge_type": "invalid",
                "scheduled_at": "2026-04-23T10:00:00Z",
            },
            headers=_USER_HEADER,
        )
        assert response.status_code == 422

    def test_schedule_with_tool_variant(self, client: TestClient) -> None:
        body = client.post(
            "/v1/nudges",
            json={
                "nudge_type": "tool_suggestion",
                "scheduled_at": "2026-04-23T10:00:00Z",
                "tool_variant": "urge_surf",
            },
            headers=_USER_HEADER,
        ).json()
        assert body["tool_variant"] == "urge_surf"

    def test_schedule_missing_scheduled_at_returns_422(self, client: TestClient) -> None:
        response = client.post(
            "/v1/nudges",
            json={"nudge_type": "check_in"},
            headers=_USER_HEADER,
        )
        assert response.status_code == 422


# =============================================================================
# Nudge listing
# =============================================================================


class TestNudgeList:
    def test_list_empty_returns_empty(self, client: TestClient) -> None:
        body = client.get("/v1/nudges", headers=_USER_HEADER).json()
        assert body == []

    def test_list_returns_scheduled_nudges(self, client: TestClient) -> None:
        client.post(
            "/v1/nudges",
            json={"nudge_type": "check_in", "scheduled_at": "2026-04-23T10:00:00Z"},
            headers=_USER_HEADER,
        )
        body = client.get("/v1/nudges", headers=_USER_HEADER).json()
        assert len(body) == 1

    def test_list_respects_user_isolation(self, client: TestClient) -> None:
        client.post(
            "/v1/nudges",
            json={"nudge_type": "check_in", "scheduled_at": "2026-04-23T10:00:00Z"},
            headers=_USER_HEADER,
        )
        body = client.get("/v1/nudges", headers=_USER_HEADER_B).json()
        assert body == []

    def test_list_respects_limit(self, client: TestClient) -> None:
        for i in range(5):
            client.post(
                "/v1/nudges",
                json={"nudge_type": "check_in", "scheduled_at": f"2026-04-23T1{i}:00:00Z"},
                headers=_USER_HEADER,
            )
        body = client.get("/v1/nudges?limit=2", headers=_USER_HEADER).json()
        assert len(body) == 2


# =============================================================================
# Nudge send
# =============================================================================


class TestNudgeSend:
    def test_send_returns_200(self, client: TestClient) -> None:
        nudge = client.post(
            "/v1/nudges",
            json={"nudge_type": "check_in", "scheduled_at": "2026-04-23T10:00:00Z"},
            headers=_USER_HEADER,
        ).json()
        response = client.post(f"/v1/nudges/{nudge['nudge_id']}/send", headers=_USER_HEADER)
        assert response.status_code == 200

    def test_send_updates_status(self, client: TestClient) -> None:
        nudge = client.post(
            "/v1/nudges",
            json={"nudge_type": "check_in", "scheduled_at": "2026-04-23T10:00:00Z"},
            headers=_USER_HEADER,
        ).json()
        body = client.post(f"/v1/nudges/{nudge['nudge_id']}/send", headers=_USER_HEADER).json()
        assert body["status"] == "sent"

    def test_send_sets_sent_at(self, client: TestClient) -> None:
        nudge = client.post(
            "/v1/nudges",
            json={"nudge_type": "check_in", "scheduled_at": "2026-04-23T10:00:00Z"},
            headers=_USER_HEADER,
        ).json()
        body = client.post(f"/v1/nudges/{nudge['nudge_id']}/send", headers=_USER_HEADER).json()
        assert body["sent_at"] is not None
        assert isinstance(body["sent_at"], str)

    def test_send_not_found_returns_404(self, client: TestClient) -> None:
        response = client.post(f"/v1/nudges/{uuid.uuid4()}/send", headers=_USER_HEADER)
        assert response.status_code == 404

    def test_send_cross_user_isolation(self, client: TestClient) -> None:
        nudge = client.post(
            "/v1/nudges",
            json={"nudge_type": "check_in", "scheduled_at": "2026-04-23T10:00:00Z"},
            headers=_USER_HEADER,
        ).json()
        response = client.post(f"/v1/nudges/{nudge['nudge_id']}/send", headers=_USER_HEADER_B)
        assert response.status_code == 404


# =============================================================================
# Push token registration
# =============================================================================


class TestPushTokenRegister:
    def test_register_returns_201(self, client: TestClient) -> None:
        response = client.post(
            "/v1/push-tokens",
            json={"platform": "ios", "token": "some_push_token_123"},
            headers=_USER_HEADER,
        )
        assert response.status_code == 201

    def test_register_response_has_token_id(self, client: TestClient) -> None:
        body = client.post(
            "/v1/push-tokens",
            json={"platform": "ios", "token": "some_push_token_123"},
            headers=_USER_HEADER,
        ).json()
        assert "token_id" in body
        uuid.UUID(body["token_id"])

    def test_register_all_platforms_accepted(self, client: TestClient) -> None:
        for platform in ("ios", "android", "web"):
            response = client.post(
                "/v1/push-tokens",
                json={"platform": platform, "token": f"token_{platform}"},
                headers={"X-User-Id": f"user_{platform}"},
            )
            assert response.status_code == 201, f"platform={platform} should be accepted"

    def test_register_invalid_platform_returns_422(self, client: TestClient) -> None:
        response = client.post(
            "/v1/push-tokens",
            json={"platform": "desktop", "token": "token"},
            headers=_USER_HEADER,
        )
        assert response.status_code == 422

    def test_register_missing_token_returns_422(self, client: TestClient) -> None:
        response = client.post(
            "/v1/push-tokens",
            json={"platform": "ios"},
            headers=_USER_HEADER,
        )
        assert response.status_code == 422


# =============================================================================
# Push token listing
# =============================================================================


class TestPushTokenList:
    def test_list_empty_returns_empty(self, client: TestClient) -> None:
        body = client.get("/v1/push-tokens", headers=_USER_HEADER).json()
        assert body == []

    def test_list_returns_registered_tokens(self, client: TestClient) -> None:
        client.post(
            "/v1/push-tokens",
            json={"platform": "ios", "token": "token1"},
            headers=_USER_HEADER,
        )
        body = client.get("/v1/push-tokens", headers=_USER_HEADER).json()
        assert len(body) == 1
        assert body[0]["platform"] == "ios"

    def test_list_respects_user_isolation(self, client: TestClient) -> None:
        client.post(
            "/v1/push-tokens",
            json={"platform": "ios", "token": "token1"},
            headers=_USER_HEADER,
        )
        body = client.get("/v1/push-tokens", headers=_USER_HEADER_B).json()
        assert body == []

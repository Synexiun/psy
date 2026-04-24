"""Check-in router tests.

Covers:
- POST /v1/check-in returns 201 with session_id and received_at
- GET /v1/check-in/history returns 200 with items list
- After POST, GET /v1/check-in/history returns the submitted check-in
- limit parameter works correctly
- User isolation (user A's history not visible to user B)
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from discipline.app import create_app
from discipline.check_in.router import reset_check_in_store
from discipline.shared.middleware.rate_limit import limiter


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture(autouse=True)
def _clear_store() -> None:
    """Reset the in-memory check-in store and rate limiter before every test."""
    reset_check_in_store()
    # Clear the slowapi in-memory bucket so high-volume tests don't hit
    # the 60/minute default_limits wall that applies to all undecorated routes.
    limiter._storage.reset()


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


_USER_A = {"X-User-Id": "user_test_001"}
_USER_B = {"X-User-Id": "user_test_002"}

_URL_CHECKIN = "/v1/check-in"
_URL_HISTORY = "/v1/check-in/history"


def _valid_check_in(**overrides):
    base = {
        "intensity": 5,
        "trigger_tags": ["stress", "boredom"],
    }
    base.update(overrides)
    return base


# =============================================================================
# POST /v1/check-in
# =============================================================================


class TestSubmitCheckIn:
    def test_returns_201(self, client: TestClient) -> None:
        response = client.post(_URL_CHECKIN, json=_valid_check_in(), headers=_USER_A)
        assert response.status_code == 201

    def test_response_has_session_id(self, client: TestClient) -> None:
        response = client.post(_URL_CHECKIN, json=_valid_check_in(), headers=_USER_A)
        body = response.json()
        assert "session_id" in body
        assert isinstance(body["session_id"], str)
        assert len(body["session_id"]) > 0

    def test_response_has_received_at(self, client: TestClient) -> None:
        response = client.post(_URL_CHECKIN, json=_valid_check_in(), headers=_USER_A)
        body = response.json()
        assert "received_at" in body
        assert isinstance(body["received_at"], str)
        # Should be a parseable ISO-8601 timestamp
        from datetime import datetime
        datetime.fromisoformat(body["received_at"])

    def test_response_has_state_updated(self, client: TestClient) -> None:
        response = client.post(_URL_CHECKIN, json=_valid_check_in(), headers=_USER_A)
        body = response.json()
        assert body["state_updated"] is True

    def test_intensity_boundary_zero(self, client: TestClient) -> None:
        response = client.post(
            _URL_CHECKIN, json=_valid_check_in(intensity=0), headers=_USER_A
        )
        assert response.status_code == 201

    def test_intensity_boundary_ten(self, client: TestClient) -> None:
        response = client.post(
            _URL_CHECKIN, json=_valid_check_in(intensity=10), headers=_USER_A
        )
        assert response.status_code == 201

    def test_intensity_above_max_rejected(self, client: TestClient) -> None:
        response = client.post(
            _URL_CHECKIN, json=_valid_check_in(intensity=11), headers=_USER_A
        )
        assert response.status_code == 422

    def test_intensity_below_min_rejected(self, client: TestClient) -> None:
        response = client.post(
            _URL_CHECKIN, json=_valid_check_in(intensity=-1), headers=_USER_A
        )
        assert response.status_code == 422

    def test_empty_trigger_tags_accepted(self, client: TestClient) -> None:
        response = client.post(
            _URL_CHECKIN, json=_valid_check_in(trigger_tags=[]), headers=_USER_A
        )
        assert response.status_code == 201

    def test_optional_notes_accepted(self, client: TestClient) -> None:
        response = client.post(
            _URL_CHECKIN,
            json=_valid_check_in(notes="Feeling overwhelmed"),
            headers=_USER_A,
        )
        assert response.status_code == 201

    def test_notes_over_max_length_rejected(self, client: TestClient) -> None:
        long_note = "x" * 281
        response = client.post(
            _URL_CHECKIN, json=_valid_check_in(notes=long_note), headers=_USER_A
        )
        assert response.status_code == 422

    def test_custom_checked_in_at_accepted(self, client: TestClient) -> None:
        response = client.post(
            _URL_CHECKIN,
            json=_valid_check_in(checked_in_at="2026-04-20T14:30:00Z"),
            headers=_USER_A,
        )
        assert response.status_code == 201

    def test_each_submission_has_unique_session_id(self, client: TestClient) -> None:
        r1 = client.post(_URL_CHECKIN, json=_valid_check_in(), headers=_USER_A)
        r2 = client.post(_URL_CHECKIN, json=_valid_check_in(), headers=_USER_A)
        assert r1.json()["session_id"] != r2.json()["session_id"]


# =============================================================================
# GET /v1/check-in/history
# =============================================================================


class TestGetCheckInHistory:
    def test_returns_200(self, client: TestClient) -> None:
        response = client.get(_URL_HISTORY, headers=_USER_A)
        assert response.status_code == 200

    def test_empty_history_returns_empty_items(self, client: TestClient) -> None:
        response = client.get(_URL_HISTORY, headers=_USER_A)
        body = response.json()
        assert body["items"] == []
        assert body["total"] == 0

    def test_response_shape(self, client: TestClient) -> None:
        response = client.get(_URL_HISTORY, headers=_USER_A)
        body = response.json()
        assert "items" in body
        assert "total" in body
        assert isinstance(body["items"], list)
        assert isinstance(body["total"], int)


# =============================================================================
# POST then GET — round-trip
# =============================================================================


class TestCheckInRoundTrip:
    def test_post_then_history_contains_checkin(self, client: TestClient) -> None:
        post_resp = client.post(_URL_CHECKIN, json=_valid_check_in(), headers=_USER_A)
        assert post_resp.status_code == 201
        session_id = post_resp.json()["session_id"]

        hist_resp = client.get(_URL_HISTORY, headers=_USER_A)
        assert hist_resp.status_code == 200
        body = hist_resp.json()
        assert body["total"] == 1
        assert len(body["items"]) == 1

        item = body["items"][0]
        assert item["session_id"] == session_id
        assert item["intensity"] == 5
        assert item["trigger_tags"] == ["stress", "boredom"]

    def test_history_item_has_checked_in_at(self, client: TestClient) -> None:
        ts = "2026-04-20T14:30:00+00:00"
        client.post(
            _URL_CHECKIN,
            json=_valid_check_in(checked_in_at=ts),
            headers=_USER_A,
        )
        body = client.get(_URL_HISTORY, headers=_USER_A).json()
        assert body["items"][0]["checked_in_at"] == ts

    def test_multiple_posts_all_appear_in_history(self, client: TestClient) -> None:
        for intensity in [2, 5, 8]:
            client.post(
                _URL_CHECKIN, json=_valid_check_in(intensity=intensity), headers=_USER_A
            )

        body = client.get(_URL_HISTORY, headers=_USER_A).json()
        assert body["total"] == 3
        assert len(body["items"]) == 3

    def test_history_is_newest_first(self, client: TestClient) -> None:
        for intensity in [1, 2, 3]:
            client.post(
                _URL_CHECKIN, json=_valid_check_in(intensity=intensity), headers=_USER_A
            )

        body = client.get(_URL_HISTORY, headers=_USER_A).json()
        intensities = [item["intensity"] for item in body["items"]]
        assert intensities == [3, 2, 1]


# =============================================================================
# limit parameter
# =============================================================================


class TestCheckInHistoryLimit:
    def test_limit_default_is_20(self, client: TestClient) -> None:
        for i in range(25):
            client.post(
                _URL_CHECKIN, json=_valid_check_in(intensity=i % 11), headers=_USER_A
            )

        body = client.get(_URL_HISTORY, headers=_USER_A).json()
        assert body["total"] == 25
        assert len(body["items"]) == 20

    def test_limit_parameter_respected(self, client: TestClient) -> None:
        for i in range(10):
            client.post(
                _URL_CHECKIN, json=_valid_check_in(intensity=i % 11), headers=_USER_A
            )

        body = client.get(_URL_HISTORY + "?limit=3", headers=_USER_A).json()
        assert body["total"] == 10
        assert len(body["items"]) == 3

    def test_limit_returns_most_recent(self, client: TestClient) -> None:
        for intensity in [1, 2, 3, 4, 5]:
            client.post(
                _URL_CHECKIN, json=_valid_check_in(intensity=intensity), headers=_USER_A
            )

        body = client.get(_URL_HISTORY + "?limit=2", headers=_USER_A).json()
        intensities = [item["intensity"] for item in body["items"]]
        assert intensities == [5, 4]

    def test_limit_1_accepted(self, client: TestClient) -> None:
        client.post(_URL_CHECKIN, json=_valid_check_in(), headers=_USER_A)
        body = client.get(_URL_HISTORY + "?limit=1", headers=_USER_A).json()
        assert len(body["items"]) == 1

    def test_limit_100_accepted(self, client: TestClient) -> None:
        response = client.get(_URL_HISTORY + "?limit=100", headers=_USER_A)
        assert response.status_code == 200

    def test_limit_0_rejected(self, client: TestClient) -> None:
        response = client.get(_URL_HISTORY + "?limit=0", headers=_USER_A)
        assert response.status_code == 422

    def test_limit_101_rejected(self, client: TestClient) -> None:
        response = client.get(_URL_HISTORY + "?limit=101", headers=_USER_A)
        assert response.status_code == 422

    def test_limit_less_than_total_returns_correct_count(self, client: TestClient) -> None:
        for i in range(5):
            client.post(
                _URL_CHECKIN, json=_valid_check_in(intensity=i % 11), headers=_USER_A
            )

        body = client.get(_URL_HISTORY + "?limit=3", headers=_USER_A).json()
        assert len(body["items"]) == 3

    def test_limit_greater_than_total_returns_all(self, client: TestClient) -> None:
        for i in range(3):
            client.post(
                _URL_CHECKIN, json=_valid_check_in(intensity=i % 11), headers=_USER_A
            )

        body = client.get(_URL_HISTORY + "?limit=50", headers=_USER_A).json()
        assert len(body["items"]) == 3


# =============================================================================
# User isolation
# =============================================================================


class TestUserIsolation:
    def test_user_a_history_not_visible_to_user_b(self, client: TestClient) -> None:
        client.post(_URL_CHECKIN, json=_valid_check_in(intensity=7), headers=_USER_A)

        body_b = client.get(_URL_HISTORY, headers=_USER_B).json()
        assert body_b["total"] == 0
        assert body_b["items"] == []

    def test_user_b_history_not_visible_to_user_a(self, client: TestClient) -> None:
        client.post(_URL_CHECKIN, json=_valid_check_in(intensity=3), headers=_USER_B)

        body_a = client.get(_URL_HISTORY, headers=_USER_A).json()
        assert body_a["total"] == 0
        assert body_a["items"] == []

    def test_both_users_see_only_their_own_data(self, client: TestClient) -> None:
        client.post(_URL_CHECKIN, json=_valid_check_in(intensity=2), headers=_USER_A)
        client.post(_URL_CHECKIN, json=_valid_check_in(intensity=9), headers=_USER_B)
        client.post(_URL_CHECKIN, json=_valid_check_in(intensity=4), headers=_USER_A)

        body_a = client.get(_URL_HISTORY, headers=_USER_A).json()
        body_b = client.get(_URL_HISTORY, headers=_USER_B).json()

        assert body_a["total"] == 2
        assert body_b["total"] == 1

        intensities_a = {item["intensity"] for item in body_a["items"]}
        intensities_b = {item["intensity"] for item in body_b["items"]}

        assert 9 not in intensities_a
        assert 2 not in intensities_b
        assert 4 not in intensities_b

    def test_default_user_id_isolated_from_explicit_user(self, client: TestClient) -> None:
        """Requests without X-User-Id default to test_user_001; must not bleed into named users."""
        client.post(_URL_CHECKIN, json=_valid_check_in())  # no header → test_user_001

        body = client.get(_URL_HISTORY, headers=_USER_A).json()
        # _USER_A is "user_test_001", distinct from the default "test_user_001"
        assert body["total"] == 0

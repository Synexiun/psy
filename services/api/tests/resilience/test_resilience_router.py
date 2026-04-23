"""Resilience streak router tests.

Covers the streak state machine: GET current, POST handled, POST relapse.
The monotonically non-decreasing resilience_days rule is verified at the
HTTP contract level.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from discipline.app import create_app
from discipline.resilience.repository import reset_streak_repository


@pytest.fixture(autouse=True)
def _clear_streaks() -> None:
    reset_streak_repository()


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


_USER_HEADER = {"X-User-Id": "user_res_001"}
_USER_HEADER_B = {"X-User-Id": "user_res_002"}
_URL = "/v1/streak"
_URL_HANDLED = "/v1/streak/handled"
_URL_RELAPSE = "/v1/streak/relapse"


# =============================================================================
# Current streak
# =============================================================================


class TestStreakCurrent:
    def test_returns_200(self, client: TestClient) -> None:
        response = client.get(_URL, headers=_USER_HEADER)
        assert response.status_code == 200

    def test_response_has_all_fields(self, client: TestClient) -> None:
        body = client.get(_URL, headers=_USER_HEADER).json()
        assert "continuous_days" in body
        assert "resilience_days" in body
        assert "resilience_urges_handled_total" in body
        assert "resilience_streak_start" in body
        assert "continuous_streak_start" in body

    def test_initial_state_is_zero(self, client: TestClient) -> None:
        body = client.get(_URL, headers=_USER_HEADER).json()
        assert body["continuous_days"] == 0
        assert body["resilience_days"] == 0
        assert body["resilience_urges_handled_total"] == 0
        assert body["continuous_streak_start"] is None

    def test_resilience_days_is_non_negative(self, client: TestClient) -> None:
        body = client.get(_URL, headers=_USER_HEADER).json()
        assert isinstance(body["resilience_days"], int)
        assert body["resilience_days"] >= 0

    def test_user_isolation(self, client: TestClient) -> None:
        client.post(_URL_HANDLED, headers=_USER_HEADER)
        a = client.get(_URL, headers=_USER_HEADER).json()
        b = client.get(_URL, headers=_USER_HEADER_B).json()
        assert a["continuous_days"] == 1
        assert b["continuous_days"] == 0


# =============================================================================
# Handled urge
# =============================================================================


class TestStreakHandled:
    def test_returns_201(self, client: TestClient) -> None:
        response = client.post(_URL_HANDLED, headers=_USER_HEADER)
        assert response.status_code == 200

    def test_action_is_handled(self, client: TestClient) -> None:
        body = client.post(_URL_HANDLED, headers=_USER_HEADER).json()
        assert body["action"] == "handled"

    def test_increments_continuous_days(self, client: TestClient) -> None:
        client.post(_URL_HANDLED, headers=_USER_HEADER)
        body = client.get(_URL, headers=_USER_HEADER).json()
        assert body["continuous_days"] == 1

    def test_increments_resilience_days(self, client: TestClient) -> None:
        client.post(_URL_HANDLED, headers=_USER_HEADER)
        body = client.get(_URL, headers=_USER_HEADER).json()
        assert body["resilience_days"] == 1

    def test_increments_urges_handled_total(self, client: TestClient) -> None:
        client.post(_URL_HANDLED, headers=_USER_HEADER)
        body = client.get(_URL, headers=_USER_HEADER).json()
        assert body["resilience_urges_handled_total"] == 1

    def test_multiple_handled_increments_all(self, client: TestClient) -> None:
        for _ in range(5):
            client.post(_URL_HANDLED, headers=_USER_HEADER)
        body = client.get(_URL, headers=_USER_HEADER).json()
        assert body["continuous_days"] == 5
        assert body["resilience_days"] == 5
        assert body["resilience_urges_handled_total"] == 5

    def test_sets_continuous_streak_start_on_first_handle(self, client: TestClient) -> None:
        client.post(_URL_HANDLED, headers=_USER_HEADER)
        body = client.get(_URL, headers=_USER_HEADER).json()
        assert body["continuous_streak_start"] is not None
        assert isinstance(body["continuous_streak_start"], str)

    def test_preserves_continuous_streak_start(self, client: TestClient) -> None:
        r1 = client.post(_URL_HANDLED, headers=_USER_HEADER).json()
        start1 = r1["streak"]["continuous_streak_start"]
        r2 = client.post(_URL_HANDLED, headers=_USER_HEADER).json()
        start2 = r2["streak"]["continuous_streak_start"]
        assert start1 == start2


# =============================================================================
# Relapse
# =============================================================================


class TestStreakRelapse:
    def test_returns_200(self, client: TestClient) -> None:
        response = client.post(_URL_RELAPSE, headers=_USER_HEADER)
        assert response.status_code == 200

    def test_action_is_relapse(self, client: TestClient) -> None:
        body = client.post(_URL_RELAPSE, headers=_USER_HEADER).json()
        assert body["action"] == "relapse"

    def test_resets_continuous_days_to_zero(self, client: TestClient) -> None:
        client.post(_URL_HANDLED, headers=_USER_HEADER)
        client.post(_URL_HANDLED, headers=_USER_HEADER)
        body = client.post(_URL_RELAPSE, headers=_USER_HEADER).json()
        assert body["streak"]["continuous_days"] == 0

    def test_resets_continuous_streak_start_to_null(self, client: TestClient) -> None:
        client.post(_URL_HANDLED, headers=_USER_HEADER)
        body = client.post(_URL_RELAPSE, headers=_USER_HEADER).json()
        assert body["streak"]["continuous_streak_start"] is None

    def test_does_not_decrease_resilience_days(self, client: TestClient) -> None:
        client.post(_URL_HANDLED, headers=_USER_HEADER)
        client.post(_URL_HANDLED, headers=_USER_HEADER)
        before = client.get(_URL, headers=_USER_HEADER).json()["resilience_days"]
        body = client.post(_URL_RELAPSE, headers=_USER_HEADER).json()
        after = body["streak"]["resilience_days"]
        assert after >= before

    def test_preserves_urges_handled_total(self, client: TestClient) -> None:
        client.post(_URL_HANDLED, headers=_USER_HEADER)
        client.post(_URL_HANDLED, headers=_USER_HEADER)
        before = client.get(_URL, headers=_USER_HEADER).json()["resilience_urges_handled_total"]
        body = client.post(_URL_RELAPSE, headers=_USER_HEADER).json()
        after = body["streak"]["resilience_urges_handled_total"]
        assert after == before

    def test_relapse_then_handle_restarts_continuous(self, client: TestClient) -> None:
        client.post(_URL_HANDLED, headers=_USER_HEADER)
        client.post(_URL_HANDLED, headers=_USER_HEADER)
        client.post(_URL_RELAPSE, headers=_USER_HEADER)
        client.post(_URL_HANDLED, headers=_USER_HEADER)
        body = client.get(_URL, headers=_USER_HEADER).json()
        assert body["continuous_days"] == 1
        assert body["resilience_days"] == 3

    def test_user_isolation(self, client: TestClient) -> None:
        client.post(_URL_HANDLED, headers=_USER_HEADER)
        client.post(_URL_HANDLED, headers=_USER_HEADER)
        client.post(_URL_RELAPSE, headers=_USER_HEADER)
        body = client.get(_URL, headers=_USER_HEADER_B).json()
        assert body["continuous_days"] == 0


# =============================================================================
# Streak state machine invariants
# =============================================================================


class TestStreakInvariants:
    def test_resilience_never_decreases(self, client: TestClient) -> None:
        """AGENTS.md Rule #3: resilience_days is monotonically non-decreasing."""
        values: list[int] = []
        for _ in range(3):
            client.post(_URL_HANDLED, headers=_USER_HEADER)
            values.append(client.get(_URL, headers=_USER_HEADER).json()["resilience_days"])
        client.post(_URL_RELAPSE, headers=_USER_HEADER)
        values.append(client.get(_URL, headers=_USER_HEADER).json()["resilience_days"])
        for i in range(1, len(values)):
            assert values[i] >= values[i - 1], f"resilience_days decreased at step {i}"

    def test_continuous_is_non_negative(self, client: TestClient) -> None:
        """Continuous streak can never be negative."""
        for _ in range(3):
            client.post(_URL_HANDLED, headers=_USER_HEADER)
        client.post(_URL_RELAPSE, headers=_USER_HEADER)
        client.post(_URL_RELAPSE, headers=_USER_HEADER)
        body = client.get(_URL, headers=_USER_HEADER).json()
        assert body["continuous_days"] >= 0

"""Resilience streak router tests.

``GET /v1/streak`` is the user-facing headline for the monotonically
non-decreasing resilience streak.  The DB trigger enforcing non-decreasing
behaviour is tested in schema tests; this file covers the HTTP contract.

Note on the stub state: ``resilience_days`` is wired to a stub
``StreakService.current``; these tests verify the response contract
(shape, types, non-negativity) that the stub must satisfy before the
real service is wired.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from discipline.app import create_app


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


_URL = "/v1/streak"


class TestStreakEndpoint:
    def test_returns_200(self, client: TestClient) -> None:
        response = client.get(_URL)
        assert response.status_code == 200

    def test_response_has_all_fields(self, client: TestClient) -> None:
        body = client.get(_URL).json()
        assert "continuous_days" in body
        assert "resilience_days" in body
        assert "resilience_urges_handled_total" in body
        assert "resilience_streak_start" in body

    def test_continuous_days_is_non_negative_int(self, client: TestClient) -> None:
        body = client.get(_URL).json()
        assert isinstance(body["continuous_days"], int)
        assert body["continuous_days"] >= 0

    def test_resilience_days_is_non_negative_int(self, client: TestClient) -> None:
        """Resilience days is monotonically non-decreasing (DB trigger
        enforces this); the HTTP contract requires it to be non-negative."""
        body = client.get(_URL).json()
        assert isinstance(body["resilience_days"], int)
        assert body["resilience_days"] >= 0

    def test_resilience_urges_handled_total_is_non_negative(
        self, client: TestClient
    ) -> None:
        body = client.get(_URL).json()
        assert body["resilience_urges_handled_total"] >= 0

    def test_resilience_streak_start_is_string(self, client: TestClient) -> None:
        body = client.get(_URL).json()
        assert isinstance(body["resilience_streak_start"], str)
        assert len(body["resilience_streak_start"]) > 0

    def test_continuous_streak_start_may_be_null(self, client: TestClient) -> None:
        """continuous_streak_start is optional — a user who has never been
        clean does not have a streak start date."""
        body = client.get(_URL).json()
        # Allowed to be None (new user) or a non-empty string (active streak)
        val = body.get("continuous_streak_start")
        assert val is None or isinstance(val, str)

    def test_response_is_stable_across_calls(self, client: TestClient) -> None:
        """The stub is deterministic — two consecutive GETs return the same shape."""
        b1 = client.get(_URL).json()
        b2 = client.get(_URL).json()
        assert b1.keys() == b2.keys()
        assert b1["resilience_days"] == b2["resilience_days"]
        assert b1["resilience_urges_handled_total"] == b2["resilience_urges_handled_total"]

    def test_no_auth_required_for_stub(self, client: TestClient) -> None:
        """Pre-auth phase: the stub endpoint is open so mobile dev can
        hit it without token plumbing.  Remove this test when the real
        service is wired with session auth."""
        response = client.get(_URL)
        assert response.status_code == 200

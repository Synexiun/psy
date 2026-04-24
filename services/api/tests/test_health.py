"""Tests for the liveness probe (``/health``).

The ``/health`` endpoint is the ECS ALB liveness probe.  It must always
return 200 if the process is alive — it does NOT check dependencies.
Dependency checks live on ``/ready`` (readiness probe); see
``tests/shared/test_health.py`` for the full readiness test suite.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from discipline.app import create_app


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


class TestHealth:
    def test_returns_200(self, client: TestClient) -> None:
        # Liveness probe must always return 200 regardless of dependency state.
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_response_has_status(self, client: TestClient) -> None:
        body = client.get("/health").json()
        assert "status" in body

    def test_response_status_is_ok(self, client: TestClient) -> None:
        body = client.get("/health").json()
        assert body["status"] == "ok"

    def test_response_has_version(self, client: TestClient) -> None:
        body = client.get("/health").json()
        assert "version" in body
        assert body["version"] == "0.0.0"

    def test_response_has_uptime_seconds(self, client: TestClient) -> None:
        body = client.get("/health").json()
        assert "uptime_seconds" in body
        assert isinstance(body["uptime_seconds"], int | float)

    def test_liveness_unaffected_by_redis_failure(
        self, client: TestClient
    ) -> None:
        """Liveness must be 200 even when Redis is unreachable.

        The ALB must not restart a task just because Redis is temporarily
        down — that is the readiness probe's job on ``/ready``.
        """
        with patch("discipline.app.get_redis_client") as mock_get_redis:
            mock_client: Any = MagicMock()
            mock_client.ping.side_effect = RuntimeError("redis down")
            mock_get_redis.return_value = mock_client
            resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

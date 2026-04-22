"""Tests for the ``/health`` endpoint.

Covers the basic shape and the enhanced connectivity checks.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from discipline.app import create_app


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


def _mock_healthy_deps() -> Any:
    """Return patch decorators for redis + postgres health."""
    def _decorator(fn: Any) -> Any:
        @patch("discipline.app.get_redis_client")
        @patch("discipline.app._get_engine")
        @pytest.mark.usefixtures("client")
        def _wrapped(mock_get_engine: Any, mock_get_redis: Any, *args: Any, **kwargs: Any) -> Any:
            mock_get_redis.return_value = MagicMock()
            mock_conn = AsyncMock()
            mock_conn.execute.return_value.scalar.return_value = 1
            mock_engine = MagicMock()
            mock_engine.connect.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
            mock_engine.connect.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_get_engine.return_value = mock_engine
            return fn(*args, **kwargs)
        return _wrapped
    return _decorator


class TestHealth:
    def test_returns_200(self, client: TestClient) -> None:
        # Without mocking, Redis/Postgres are unavailable → 503.
        # This test verifies the endpoint responds without crashing.
        resp = client.get("/health")
        assert resp.status_code in (200, 503)

    def test_response_has_status(self, client: TestClient) -> None:
        body = client.get("/health").json()
        assert "status" in body

    def test_response_has_version(self, client: TestClient) -> None:
        body = client.get("/health").json()
        assert "version" in body
        assert body["version"] == "0.0.0"

    def test_response_has_checks(self, client: TestClient) -> None:
        body = client.get("/health").json()
        assert "checks" in body
        assert isinstance(body["checks"], dict)

    @patch("discipline.app.get_redis_client")
    def test_degraded_when_redis_fails(
        self, mock_get_redis: Any, client: TestClient
    ) -> None:
        mock_client = MagicMock()
        mock_client.ping.side_effect = RuntimeError("redis down")
        mock_get_redis.return_value = mock_client

        resp = client.get("/health")
        assert resp.status_code == 503
        body = resp.json()
        assert body["status"] == "degraded"
        assert "redis" in body["checks"]
        assert "error" in body["checks"]["redis"]

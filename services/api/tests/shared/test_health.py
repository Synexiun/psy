"""Tests for the liveness (``/health``) and readiness (``/ready``) probes.

``/health`` — liveness: always 200 if the process is running.
``/ready``  — readiness: 200 when DB + Redis are reachable, 503 otherwise.

These two endpoints are polled by the ECS ALB target group and the rolling-
deploy gate respectively.  A regression here is operationally critical, so
we pin both the happy path and the degraded path with explicit mocks.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from discipline.app import create_app


# ---------------------------------------------------------------------------
# Shared fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


# ---------------------------------------------------------------------------
# /health — liveness probe
# ---------------------------------------------------------------------------


class TestLivenessProbe:
    """``/health`` must always respond 200 regardless of dependency state."""

    _URL = "/health"

    def test_returns_200(self, client: TestClient) -> None:
        resp = client.get(self._URL)
        assert resp.status_code == 200

    def test_body_has_status_ok(self, client: TestClient) -> None:
        body = client.get(self._URL).json()
        assert body["status"] == "ok"

    def test_body_has_version(self, client: TestClient) -> None:
        body = client.get(self._URL).json()
        assert "version" in body
        assert isinstance(body["version"], str)
        assert len(body["version"]) > 0

    def test_body_has_uptime_seconds(self, client: TestClient) -> None:
        body = client.get(self._URL).json()
        assert "uptime_seconds" in body
        assert isinstance(body["uptime_seconds"], int | float)
        assert body["uptime_seconds"] >= 0

    def test_liveness_does_not_check_dependencies(self, client: TestClient) -> None:
        """Liveness must return 200 even if Redis/DB are unavailable.

        This is the liveness contract: the probe only tests that the process
        is alive.  A broken Redis must not cause an ECS task restart (which
        would be counterproductive).  Only the readiness probe (/ready) gates
        on dependency health.
        """
        with (
            patch("discipline.app.get_redis_client") as mock_redis,
            patch("discipline.app._get_engine") as mock_engine,
        ):
            mock_redis.side_effect = RuntimeError("redis down")
            mock_engine.side_effect = RuntimeError("db down")
            resp = client.get(self._URL)
        # Still 200 — liveness doesn't call these
        assert resp.status_code == 200

    def test_version_matches_package(self, client: TestClient) -> None:
        from discipline import __version__

        body = client.get(self._URL).json()
        assert body["version"] == __version__


# ---------------------------------------------------------------------------
# /ready — readiness probe
# ---------------------------------------------------------------------------


def _make_healthy_engine_mock() -> Any:
    """Return a mock SQLAlchemy async engine whose connect() returns SELECT 1."""
    mock_conn = AsyncMock()
    mock_conn.execute.return_value.scalar.return_value = 1
    mock_engine = MagicMock()
    mock_engine.connect.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_engine.connect.return_value.__aexit__ = AsyncMock(return_value=False)
    return mock_engine


class TestReadinessProbe:
    """``/ready`` gates on Redis + PostgreSQL connectivity."""

    _URL = "/ready"

    # ------------------------------------------------------------------
    # Happy path (both deps healthy)
    # ------------------------------------------------------------------

    def test_returns_200_when_all_healthy(self, client: TestClient) -> None:
        with (
            patch("discipline.app.get_redis_client") as mock_redis,
            patch("discipline.app._get_engine") as mock_engine,
        ):
            mock_redis.return_value = MagicMock()  # ping() succeeds by default
            mock_engine.return_value = _make_healthy_engine_mock()
            resp = client.get(self._URL)
        assert resp.status_code == 200

    def test_body_status_ready_when_healthy(self, client: TestClient) -> None:
        with (
            patch("discipline.app.get_redis_client") as mock_redis,
            patch("discipline.app._get_engine") as mock_engine,
        ):
            mock_redis.return_value = MagicMock()
            mock_engine.return_value = _make_healthy_engine_mock()
            body = client.get(self._URL).json()
        assert body["status"] == "ready"

    def test_checks_dict_all_ok_when_healthy(self, client: TestClient) -> None:
        with (
            patch("discipline.app.get_redis_client") as mock_redis,
            patch("discipline.app._get_engine") as mock_engine,
        ):
            mock_redis.return_value = MagicMock()
            mock_engine.return_value = _make_healthy_engine_mock()
            body = client.get(self._URL).json()
        assert body["checks"]["redis"] == "ok"
        assert body["checks"]["postgres"] == "ok"

    def test_body_has_version(self, client: TestClient) -> None:
        with (
            patch("discipline.app.get_redis_client") as mock_redis,
            patch("discipline.app._get_engine") as mock_engine,
        ):
            mock_redis.return_value = MagicMock()
            mock_engine.return_value = _make_healthy_engine_mock()
            body = client.get(self._URL).json()
        assert "version" in body

    # ------------------------------------------------------------------
    # Redis failure
    # ------------------------------------------------------------------

    def test_returns_503_when_redis_fails(self, client: TestClient) -> None:
        with (
            patch("discipline.app.get_redis_client") as mock_redis,
            patch("discipline.app._get_engine") as mock_engine,
        ):
            failing_redis = MagicMock()
            failing_redis.ping.side_effect = RuntimeError("connection refused")
            mock_redis.return_value = failing_redis
            mock_engine.return_value = _make_healthy_engine_mock()
            resp = client.get(self._URL)
        assert resp.status_code == 503

    def test_status_degraded_when_redis_fails(self, client: TestClient) -> None:
        with (
            patch("discipline.app.get_redis_client") as mock_redis,
            patch("discipline.app._get_engine") as mock_engine,
        ):
            failing_redis = MagicMock()
            failing_redis.ping.side_effect = RuntimeError("connection refused")
            mock_redis.return_value = failing_redis
            mock_engine.return_value = _make_healthy_engine_mock()
            body = client.get(self._URL).json()
        assert body["status"] == "degraded"

    def test_redis_check_shows_error_detail(self, client: TestClient) -> None:
        with (
            patch("discipline.app.get_redis_client") as mock_redis,
            patch("discipline.app._get_engine") as mock_engine,
        ):
            failing_redis = MagicMock()
            failing_redis.ping.side_effect = RuntimeError("connection refused")
            mock_redis.return_value = failing_redis
            mock_engine.return_value = _make_healthy_engine_mock()
            body = client.get(self._URL).json()
        assert "error" in body["checks"]["redis"]

    # ------------------------------------------------------------------
    # PostgreSQL failure
    # ------------------------------------------------------------------

    def test_returns_503_when_postgres_fails(self, client: TestClient) -> None:
        with (
            patch("discipline.app.get_redis_client") as mock_redis,
            patch("discipline.app._get_engine") as mock_engine,
        ):
            mock_redis.return_value = MagicMock()
            mock_engine.side_effect = RuntimeError("db unavailable")
            resp = client.get(self._URL)
        assert resp.status_code == 503

    def test_postgres_check_shows_error_detail(self, client: TestClient) -> None:
        with (
            patch("discipline.app.get_redis_client") as mock_redis,
            patch("discipline.app._get_engine") as mock_engine,
        ):
            mock_redis.return_value = MagicMock()
            mock_engine.side_effect = RuntimeError("db unavailable")
            body = client.get(self._URL).json()
        assert "error" in body["checks"]["postgres"]

    # ------------------------------------------------------------------
    # Both dependencies down
    # ------------------------------------------------------------------

    def test_returns_503_when_both_fail(self, client: TestClient) -> None:
        with (
            patch("discipline.app.get_redis_client") as mock_redis,
            patch("discipline.app._get_engine") as mock_engine,
        ):
            failing_redis = MagicMock()
            failing_redis.ping.side_effect = RuntimeError("redis down")
            mock_redis.return_value = failing_redis
            mock_engine.side_effect = RuntimeError("db down")
            resp = client.get(self._URL)
        assert resp.status_code == 503

    def test_both_checks_show_errors_when_both_fail(self, client: TestClient) -> None:
        with (
            patch("discipline.app.get_redis_client") as mock_redis,
            patch("discipline.app._get_engine") as mock_engine,
        ):
            failing_redis = MagicMock()
            failing_redis.ping.side_effect = RuntimeError("redis down")
            mock_redis.return_value = failing_redis
            mock_engine.side_effect = RuntimeError("db down")
            body = client.get(self._URL).json()
        assert "error" in body["checks"]["redis"]
        assert "error" in body["checks"]["postgres"]

    # ------------------------------------------------------------------
    # Response shape invariants (regardless of health state)
    # ------------------------------------------------------------------

    def test_checks_key_always_present(self, client: TestClient) -> None:
        resp = client.get(self._URL)
        body = resp.json()
        assert "checks" in body
        assert isinstance(body["checks"], dict)

    def test_status_key_always_present(self, client: TestClient) -> None:
        resp = client.get(self._URL)
        assert "status" in resp.json()

    def test_status_value_is_one_of_valid_states(self, client: TestClient) -> None:
        body = client.get(self._URL).json()
        assert body["status"] in {"ready", "degraded"}


# ---------------------------------------------------------------------------
# Liveness / readiness contract: they are independent endpoints
# ---------------------------------------------------------------------------


class TestProbeEndpointsAreDistinct:
    """The two probes must be separate routes — ECS ALB and deploy gates
    call different paths for different semantics."""

    def test_health_url_is_slash_health(self, client: TestClient) -> None:
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_ready_url_is_slash_ready(self, client: TestClient) -> None:
        resp = client.get("/ready")
        # 200 (if deps reachable) or 503 (if not) — either is acceptable;
        # we only care that the route exists and returns a parseable JSON body.
        assert resp.status_code in {200, 503}
        assert "status" in resp.json()

    def test_health_does_not_have_checks_key(self, client: TestClient) -> None:
        """Liveness probe is intentionally minimal — no dependency checks."""
        body = client.get("/health").json()
        assert "checks" not in body

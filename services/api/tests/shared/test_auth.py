"""``require_admin`` dependency tests.

The admin gate is a scaffold — production replaces it with a Clerk
session + admin role claim — but the contract (403 on missing / mismatched
token, passes through on match) is stable and must not regress.

Uses ``hmac.compare_digest`` semantics: the tests submit a range of
near-miss and full-miss token values and assert consistent 403 response
shape.  Timing-channel resistance is a property of the ``hmac`` module
itself and is not re-tested here.
"""

from __future__ import annotations

import os

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from discipline.shared.auth import require_admin


@pytest.fixture
def app_with_admin_route() -> FastAPI:
    """Minimal FastAPI app with one admin-gated route for isolated testing.

    Isolated from :func:`discipline.app.create_app` so a regression in
    an unrelated router can't mask a regression in ``require_admin``.
    """
    app = FastAPI()

    @app.get("/admin-only", dependencies=[Depends(require_admin)])
    async def _admin_only() -> dict[str, str]:
        return {"status": "ok"}

    return app


@pytest.fixture
def client(app_with_admin_route: FastAPI) -> TestClient:
    return TestClient(app_with_admin_route)


# ---- Missing / malformed token --------------------------------------------


class TestMissingToken:
    def test_no_header_returns_403(self, client: TestClient) -> None:
        resp = client.get("/admin-only")
        assert resp.status_code == 403
        detail = resp.json()["detail"]
        assert detail["code"] == "auth.admin_required"

    def test_empty_header_returns_403(self, client: TestClient) -> None:
        """An empty-string token must not pass — ``hmac.compare_digest``
        would treat it as a length mismatch, but the explicit ``is None``
        check in the dep catches this before the compare runs."""
        resp = client.get("/admin-only", headers={"X-Admin-Token": ""})
        assert resp.status_code == 403

    def test_wrong_token_returns_403_with_forbidden_code(
        self, client: TestClient
    ) -> None:
        resp = client.get(
            "/admin-only", headers={"X-Admin-Token": "not-the-token"}
        )
        assert resp.status_code == 403
        detail = resp.json()["detail"]
        assert detail["code"] == "auth.admin_forbidden"

    def test_near_miss_token_returns_403(self, client: TestClient) -> None:
        """A token one character off must still 403 — not leak 'close'
        via different status codes or different response bodies."""
        token = os.environ.get("ADMIN_API_TOKEN", "dev-admin-token")
        resp = client.get(
            "/admin-only", headers={"X-Admin-Token": token + "x"}
        )
        assert resp.status_code == 403
        assert resp.json()["detail"]["code"] == "auth.admin_forbidden"


# ---- Correct token --------------------------------------------------------


class TestCorrectToken:
    def test_correct_token_passes(self, client: TestClient) -> None:
        token = os.environ.get("ADMIN_API_TOKEN", "dev-admin-token")
        resp = client.get("/admin-only", headers={"X-Admin-Token": token})
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


# ---- Env-configured token --------------------------------------------------


class TestEnvConfiguredToken:
    def test_token_read_from_env_at_call_time(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The dep reads ``ADMIN_API_TOKEN`` at call time (not import time),
        so a deploy rotating the env var takes effect for the next request.
        This test pins that behavior — a refactor that caches the token
        at module import would break rotation and silently drift."""
        monkeypatch.setenv("ADMIN_API_TOKEN", "rotated-value-42")
        resp = client.get(
            "/admin-only", headers={"X-Admin-Token": "rotated-value-42"}
        )
        assert resp.status_code == 200
        # Old token now rejected.
        resp_old = client.get(
            "/admin-only", headers={"X-Admin-Token": "dev-admin-token"}
        )
        assert resp_old.status_code == 403

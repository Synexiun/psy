"""Identity router tests.

Covers the user identity stub and the auth exchange endpoint.
"""

from __future__ import annotations

import time
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from jose import jwt as jose_jwt

from discipline.app import create_app
from discipline.identity.repository import reset_user_repository
from discipline.identity.session_store import SessionStore


@pytest.fixture(autouse=True)
def _clear_users() -> None:
    reset_user_repository()


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


@pytest.fixture
def clerk_token() -> str:
    import os

    secret = os.environ.get(
        "SERVER_SESSION_SECRET", "dev-only-session-secret-do-not-use-in-prod"
    )
    now = int(time.time())
    raw = jose_jwt.encode(
        {
            "sub": "clerk_user_test",
            "email_address": "test@example.com",
            "locale": "en",
            "iat": now,
            "exp": now + 3600,
        },
        secret,
        algorithm="HS256",
    )
    return "test_clerk_" + raw


_URL_ME = "/v1/me"
_URL_EXCHANGE = "/v1/me/auth/exchange"
_URL_REFRESH = "/v1/me/auth/refresh"
_URL_LOGOUT = "/v1/me/auth/logout"


class TestIdentityEndpoint:
    def test_returns_200(self, client: TestClient) -> None:
        response = client.get(_URL_ME)
        assert response.status_code == 200

    def test_response_has_status_field(self, client: TestClient) -> None:
        body = client.get(_URL_ME).json()
        assert "status" in body

    def test_status_is_not_implemented(self, client: TestClient) -> None:
        body = client.get(_URL_ME).json()
        assert body["status"] == "not_implemented"

    def test_status_is_string(self, client: TestClient) -> None:
        body = client.get(_URL_ME).json()
        assert isinstance(body["status"], str)

    def test_response_is_stable_across_calls(self, client: TestClient) -> None:
        b1 = client.get(_URL_ME).json()
        b2 = client.get(_URL_ME).json()
        assert b1 == b2

    def test_no_auth_required_for_stub(self, client: TestClient) -> None:
        response = client.get(_URL_ME)
        assert response.status_code == 200


class TestAuthExchange:
    def test_exchange_valid_token(self, client: TestClient, clerk_token: str) -> None:
        resp = client.post(_URL_EXCHANGE, json={"clerk_token": clerk_token})
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert "refresh_token" in body
        assert body["expires_in"] == 900
        assert body["token_type"] == "bearer"

    def test_exchange_missing_token(self, client: TestClient) -> None:
        resp = client.post(_URL_EXCHANGE, json={})
        assert resp.status_code == 400
        assert resp.json()["detail"]["code"] == "auth.missing_clerk_token"

    def test_exchange_invalid_token(self, client: TestClient) -> None:
        resp = client.post(_URL_EXCHANGE, json={"clerk_token": "invalid"})
        assert resp.status_code == 401
        assert resp.json()["detail"]["code"] == "auth.exchange_invalid"

    def test_exchange_response_has_jwt_shape(
        self, client: TestClient, clerk_token: str
    ) -> None:
        resp = client.post(_URL_EXCHANGE, json={"clerk_token": clerk_token})
        body = resp.json()
        assert isinstance(body["access_token"], str)
        assert len(body["access_token"]) > 20
        assert isinstance(body["refresh_token"], str)
        assert isinstance(body["expires_in"], int)


def _make_mock_store(
    *,
    consume_result: tuple[str, str, str] | None = None,
    is_active: bool = True,
) -> SessionStore:
    store = MagicMock(spec=SessionStore)
    store.consume_refresh.return_value = consume_result
    store.is_active.return_value = is_active
    return store


class TestAuthRefresh:
    def test_refresh_missing_token(self, client: TestClient) -> None:
        resp = client.post(_URL_REFRESH, json={})
        assert resp.status_code == 400
        assert resp.json()["detail"]["code"] == "auth.missing_refresh_token"

    def test_refresh_invalid_token(self, client: TestClient) -> None:
        mock_store = _make_mock_store(consume_result=None)
        with patch("discipline.identity.router.get_session_store", return_value=mock_store):
            resp = client.post(_URL_REFRESH, json={"refresh_token": "bad_token"})
        assert resp.status_code == 401
        assert resp.json()["detail"]["code"] == "auth.refresh_invalid"

    def test_refresh_revoked_session_kills_family(self, client: TestClient) -> None:
        mock_store = _make_mock_store(
            consume_result=("sess_01", "fam_compromised", "user_clerk_user_test"),
            is_active=False,
        )
        with patch("discipline.identity.router.get_session_store", return_value=mock_store):
            resp = client.post(_URL_REFRESH, json={"refresh_token": "rt_01"})
        assert resp.status_code == 401
        assert resp.json()["detail"]["code"] == "auth.session_revoked"
        mock_store.kill_family.assert_called_once_with("fam_compromised")

    def test_refresh_user_not_found(self, client: TestClient) -> None:
        mock_store = _make_mock_store(
            consume_result=("sess_01", "fam_01", "unknown_user_id"),
            is_active=True,
        )
        with patch("discipline.identity.router.get_session_store", return_value=mock_store):
            resp = client.post(_URL_REFRESH, json={"refresh_token": "rt_01"})
        assert resp.status_code == 401
        assert resp.json()["detail"]["code"] == "auth.user_not_found"

    def test_refresh_full_roundtrip(
        self, client: TestClient, clerk_token: str
    ) -> None:
        # First exchange to get a user in the in-memory repo.
        exchange_resp = client.post(_URL_EXCHANGE, json={"clerk_token": clerk_token})
        assert exchange_resp.status_code == 200

        # The exchange creates user_id = "user_clerk_user_test" in the in-memory repo.
        user_id = "user_clerk_user_test"
        mock_store = _make_mock_store(
            consume_result=("sess_01", "fam_01", user_id),
            is_active=True,
        )
        # Also mock activate/store_refresh so issue_session inside doesn't hit Redis.
        mock_store.activate.return_value = None
        mock_store.store_refresh.return_value = None

        with patch("discipline.identity.router.get_session_store", return_value=mock_store):
            with patch("discipline.identity.session.get_session_store", return_value=mock_store):
                resp = client.post(_URL_REFRESH, json={"refresh_token": "rt_valid"})

        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert "refresh_token" in body
        assert body["expires_in"] == 900
        assert body["token_type"] == "bearer"


class TestAuthLogout:
    def test_logout_missing_session_id(self, client: TestClient) -> None:
        resp = client.post(_URL_LOGOUT, json={})
        assert resp.status_code == 400
        assert resp.json()["detail"]["code"] == "auth.missing_session_id"

    def test_logout_with_session_id(self, client: TestClient) -> None:
        mock_store = _make_mock_store()
        with patch("discipline.identity.router.get_session_store", return_value=mock_store):
            resp = client.post(_URL_LOGOUT, json={"session_id": "sess_test_123"})
        assert resp.status_code == 200
        assert resp.json()["status"] == "logged_out"
        mock_store.revoke.assert_called_once_with("sess_test_123")

    def test_logout_redis_unavailable_still_200(self, client: TestClient) -> None:
        failing_store = MagicMock(spec=SessionStore)
        failing_store.revoke.side_effect = ConnectionError("Redis down")
        with patch("discipline.identity.router.get_session_store", return_value=failing_store):
            resp = client.post(_URL_LOGOUT, json={"session_id": "sess_down"})
        assert resp.status_code == 200
        assert resp.json()["status"] == "logged_out"

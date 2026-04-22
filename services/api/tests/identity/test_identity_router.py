"""Identity router tests.

Covers the user identity stub and the auth exchange endpoint.
"""

from __future__ import annotations

import time

import pytest
from fastapi.testclient import TestClient
from jose import jwt as jose_jwt

from discipline.app import create_app
from discipline.identity.repository import reset_user_repository


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

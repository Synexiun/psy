"""Identity router tests.

``GET /v1/me`` is the user identity stub wired to ``UserService.get_current``
once real auth lands.  These tests verify the pre-auth stub contract:
shape, types, and determinism.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from discipline.app import create_app


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


_URL = "/v1/me"


class TestIdentityEndpoint:
    def test_returns_200(self, client: TestClient) -> None:
        response = client.get(_URL)
        assert response.status_code == 200

    def test_response_has_status_field(self, client: TestClient) -> None:
        body = client.get(_URL).json()
        assert "status" in body

    def test_status_is_not_implemented(self, client: TestClient) -> None:
        """Stub contract: status == 'not_implemented' until UserService is wired."""
        body = client.get(_URL).json()
        assert body["status"] == "not_implemented"

    def test_status_is_string(self, client: TestClient) -> None:
        body = client.get(_URL).json()
        assert isinstance(body["status"], str)

    def test_response_is_stable_across_calls(self, client: TestClient) -> None:
        """Stub is deterministic — identical shape on consecutive GETs."""
        b1 = client.get(_URL).json()
        b2 = client.get(_URL).json()
        assert b1 == b2

    def test_no_auth_required_for_stub(self, client: TestClient) -> None:
        """Pre-auth phase: identity stub is open so mobile dev can probe
        without token plumbing.  Remove when UserService is wired with
        Clerk session auth."""
        response = client.get(_URL)
        assert response.status_code == 200

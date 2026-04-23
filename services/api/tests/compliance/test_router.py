"""Compliance router tests.

Covers consent grant/retrieve and quick-erase lifecycle.
"""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from discipline.app import create_app
from discipline.compliance.repository import reset_compliance_repositories


@pytest.fixture(autouse=True)
def _clear_compliance() -> None:
    reset_compliance_repositories()


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


_USER_HEADER = {"X-User-Id": "user_comp_001"}
_USER_HEADER_B = {"X-User-Id": "user_comp_002"}


# =============================================================================
# Consent grant
# =============================================================================


class TestConsentGrant:
    def test_grant_returns_201(self, client: TestClient) -> None:
        response = client.post(
            "/v1/compliance/consent",
            json={"consent_type": "privacy_policy", "version": "1.0.0"},
            headers=_USER_HEADER,
        )
        assert response.status_code == 201

    def test_grant_response_has_consent_id(self, client: TestClient) -> None:
        body = client.post(
            "/v1/compliance/consent",
            json={"consent_type": "terms_of_service", "version": "1.0.0"},
            headers=_USER_HEADER,
        ).json()
        assert "consent_id" in body
        uuid.UUID(body["consent_id"])

    def test_grant_all_valid_types_accepted(self, client: TestClient) -> None:
        for ctype in ("terms_of_service", "privacy_policy", "clinical_data", "marketing"):
            response = client.post(
                "/v1/compliance/consent",
                json={"consent_type": ctype, "version": "1.0.0"},
                headers={"X-User-Id": f"user_{ctype}"},
            )
            assert response.status_code == 201, f"consent_type={ctype} should be accepted"

    def test_grant_invalid_type_returns_422(self, client: TestClient) -> None:
        response = client.post(
            "/v1/compliance/consent",
            json={"consent_type": "invalid_type", "version": "1.0.0"},
            headers=_USER_HEADER,
        )
        assert response.status_code == 422

    def test_grant_missing_version_returns_422(self, client: TestClient) -> None:
        response = client.post(
            "/v1/compliance/consent",
            json={"consent_type": "privacy_policy"},
            headers=_USER_HEADER,
        )
        assert response.status_code == 422

    def test_grant_overwrites_previous_same_type(self, client: TestClient) -> None:
        client.post(
            "/v1/compliance/consent",
            json={"consent_type": "privacy_policy", "version": "1.0.0"},
            headers=_USER_HEADER,
        )
        body = client.post(
            "/v1/compliance/consent",
            json={"consent_type": "privacy_policy", "version": "2.0.0"},
            headers=_USER_HEADER,
        ).json()
        assert body["version"] == "2.0.0"

    def test_grant_preserves_different_types(self, client: TestClient) -> None:
        client.post(
            "/v1/compliance/consent",
            json={"consent_type": "privacy_policy", "version": "1.0.0"},
            headers=_USER_HEADER,
        )
        body = client.post(
            "/v1/compliance/consent",
            json={"consent_type": "clinical_data", "version": "1.0.0"},
            headers=_USER_HEADER,
        ).json()
        assert body["consent_type"] == "clinical_data"

    def test_grant_with_ip_address(self, client: TestClient) -> None:
        body = client.post(
            "/v1/compliance/consent",
            json={
                "consent_type": "privacy_policy",
                "version": "1.0.0",
                "ip_address": "192.168.1.1",
            },
            headers=_USER_HEADER,
        ).json()
        assert "consent_id" in body


# =============================================================================
# Consent retrieval
# =============================================================================


class TestConsentGet:
    def test_get_existing_returns_200(self, client: TestClient) -> None:
        client.post(
            "/v1/compliance/consent",
            json={"consent_type": "privacy_policy", "version": "1.0.0"},
            headers=_USER_HEADER,
        )
        response = client.get(
            "/v1/compliance/consent/privacy_policy",
            headers=_USER_HEADER,
        )
        assert response.status_code == 200

    def test_get_returns_correct_version(self, client: TestClient) -> None:
        client.post(
            "/v1/compliance/consent",
            json={"consent_type": "privacy_policy", "version": "2.1.0"},
            headers=_USER_HEADER,
        )
        body = client.get(
            "/v1/compliance/consent/privacy_policy",
            headers=_USER_HEADER,
        ).json()
        assert body["version"] == "2.1.0"

    def test_get_not_found_returns_404(self, client: TestClient) -> None:
        response = client.get(
            "/v1/compliance/consent/privacy_policy",
            headers=_USER_HEADER,
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "consent.not_found"

    def test_get_user_isolation(self, client: TestClient) -> None:
        client.post(
            "/v1/compliance/consent",
            json={"consent_type": "privacy_policy", "version": "1.0.0"},
            headers=_USER_HEADER,
        )
        response = client.get(
            "/v1/compliance/consent/privacy_policy",
            headers=_USER_HEADER_B,
        )
        assert response.status_code == 404


# =============================================================================
# Quick-erase request
# =============================================================================


class TestQuickEraseRequest:
    def test_request_returns_201(self, client: TestClient) -> None:
        response = client.post(
            "/v1/compliance/quick-erase",
            headers=_USER_HEADER,
        )
        assert response.status_code == 201

    def test_request_response_has_request_id(self, client: TestClient) -> None:
        body = client.post("/v1/compliance/quick-erase", headers=_USER_HEADER).json()
        assert "request_id" in body
        uuid.UUID(body["request_id"])

    def test_request_status_is_pending(self, client: TestClient) -> None:
        body = client.post("/v1/compliance/quick-erase", headers=_USER_HEADER).json()
        assert body["status"] == "pending"

    def test_request_has_requested_at(self, client: TestClient) -> None:
        body = client.post("/v1/compliance/quick-erase", headers=_USER_HEADER).json()
        assert "requested_at" in body
        assert isinstance(body["requested_at"], str)

    def test_request_completed_at_is_null(self, client: TestClient) -> None:
        body = client.post("/v1/compliance/quick-erase", headers=_USER_HEADER).json()
        assert body["completed_at"] is None


# =============================================================================
# Quick-erase status
# =============================================================================


class TestQuickEraseStatus:
    def test_get_latest_returns_200(self, client: TestClient) -> None:
        client.post("/v1/compliance/quick-erase", headers=_USER_HEADER)
        response = client.get("/v1/compliance/quick-erase/status", headers=_USER_HEADER)
        assert response.status_code == 200

    def test_get_latest_returns_most_recent(self, client: TestClient) -> None:
        r1 = client.post("/v1/compliance/quick-erase", headers=_USER_HEADER).json()
        client.post("/v1/compliance/quick-erase", headers=_USER_HEADER)
        body = client.get("/v1/compliance/quick-erase/status", headers=_USER_HEADER).json()
        assert body["request_id"] != r1["request_id"]
        assert body["status"] == "pending"

    def test_get_not_found_returns_404(self, client: TestClient) -> None:
        response = client.get("/v1/compliance/quick-erase/status", headers=_USER_HEADER)
        assert response.status_code == 404
        assert response.json()["detail"] == "quick_erase.not_found"

    def test_get_user_isolation(self, client: TestClient) -> None:
        client.post("/v1/compliance/quick-erase", headers=_USER_HEADER)
        response = client.get("/v1/compliance/quick-erase/status", headers=_USER_HEADER_B)
        assert response.status_code == 404

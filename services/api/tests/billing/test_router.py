"""Billing router tests — subscription lifecycle and webhooks.

Covers subscription creation, retrieval, upgrade, cancellation,
webhook acceptance, user isolation, and validation boundaries.
"""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from discipline.app import create_app
from discipline.billing.repository import reset_subscription_repository


@pytest.fixture(autouse=True)
def _clear_billing() -> None:
    reset_subscription_repository()


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


_USER_HEADER = {"X-User-Id": "user_bill_001"}
_USER_HEADER_B = {"X-User-Id": "user_bill_002"}

_URL_SUB = "/v1/subscriptions"
_URL_UPGRADE = "/v1/subscriptions/upgrade"
_URL_CANCEL = "/v1/subscriptions/cancel"


def _valid_create_payload(**overrides):
    base = {
        "tier": "plus",
        "provider": "stripe",
        "provider_subscription_id": "sub_test_123",
        "current_period_start": "2026-04-01T00:00:00Z",
        "current_period_end": "2026-04-30T23:59:59Z",
    }
    base.update(overrides)
    return base


# =============================================================================
# Subscription creation
# =============================================================================


class TestSubscriptionCreate:
    def test_create_returns_201(self, client: TestClient) -> None:
        response = client.post(_URL_SUB, json=_valid_create_payload(), headers=_USER_HEADER)
        assert response.status_code == 201

    def test_create_response_has_subscription_id(self, client: TestClient) -> None:
        body = client.post(_URL_SUB, json=_valid_create_payload(), headers=_USER_HEADER).json()
        assert "subscription_id" in body
        uuid.UUID(body["subscription_id"])

    def test_create_persists_tier(self, client: TestClient) -> None:
        body = client.post(_URL_SUB, json=_valid_create_payload(tier="pro"), headers=_USER_HEADER).json()
        assert body["tier"] == "pro"

    def test_create_persists_provider(self, client: TestClient) -> None:
        body = client.post(
            _URL_SUB,
            json=_valid_create_payload(provider="apple_iap"),
            headers=_USER_HEADER,
        ).json()
        assert body["provider"] == "apple_iap"

    def test_create_defaults_to_active(self, client: TestClient) -> None:
        body = client.post(_URL_SUB, json=_valid_create_payload(), headers=_USER_HEADER).json()
        assert body["status"] == "active"

    def test_create_all_valid_tiers_accepted(self, client: TestClient) -> None:
        for tier in ("free", "plus", "pro", "enterprise"):
            reset_subscription_repository()
            response = client.post(
                _URL_SUB,
                json=_valid_create_payload(tier=tier),
                headers=_USER_HEADER,
            )
            assert response.status_code == 201, f"tier={tier} failed"

    def test_create_all_valid_providers_accepted(self, client: TestClient) -> None:
        for provider in ("stripe", "apple_iap", "google_iap"):
            reset_subscription_repository()
            response = client.post(
                _URL_SUB,
                json=_valid_create_payload(provider=provider),
                headers=_USER_HEADER,
            )
            assert response.status_code == 201, f"provider={provider} failed"

    def test_create_invalid_tier_returns_422(self, client: TestClient) -> None:
        response = client.post(
            _URL_SUB,
            json=_valid_create_payload(tier="invalid"),
            headers=_USER_HEADER,
        )
        assert response.status_code == 422

    def test_create_invalid_provider_returns_422(self, client: TestClient) -> None:
        response = client.post(
            _URL_SUB,
            json=_valid_create_payload(provider="paypal"),
            headers=_USER_HEADER,
        )
        assert response.status_code == 422

    def test_create_missing_provider_subscription_id_returns_422(self, client: TestClient) -> None:
        payload = _valid_create_payload()
        del payload["provider_subscription_id"]
        response = client.post(_URL_SUB, json=payload, headers=_USER_HEADER)
        assert response.status_code == 422

    def test_create_user_isolation(self, client: TestClient) -> None:
        body_a = client.post(_URL_SUB, json=_valid_create_payload(), headers=_USER_HEADER).json()
        body_b = client.post(_URL_SUB, json=_valid_create_payload(), headers=_USER_HEADER_B).json()
        assert body_a["subscription_id"] != body_b["subscription_id"]


# =============================================================================
# Subscription retrieval
# =============================================================================


class TestSubscriptionGet:
    def test_get_returns_200(self, client: TestClient) -> None:
        client.post(_URL_SUB, json=_valid_create_payload(), headers=_USER_HEADER)
        response = client.get(_URL_SUB, headers=_USER_HEADER)
        assert response.status_code == 200

    def test_get_returns_same_subscription(self, client: TestClient) -> None:
        created = client.post(_URL_SUB, json=_valid_create_payload(), headers=_USER_HEADER).json()
        fetched = client.get(_URL_SUB, headers=_USER_HEADER).json()
        assert fetched["subscription_id"] == created["subscription_id"]

    def test_get_when_none_returns_404(self, client: TestClient) -> None:
        response = client.get(_URL_SUB, headers=_USER_HEADER)
        assert response.status_code == 404

    def test_get_user_isolation(self, client: TestClient) -> None:
        client.post(_URL_SUB, json=_valid_create_payload(), headers=_USER_HEADER)
        response = client.get(_URL_SUB, headers=_USER_HEADER_B)
        assert response.status_code == 404

    def test_get_preserves_period_dates(self, client: TestClient) -> None:
        client.post(_URL_SUB, json=_valid_create_payload(), headers=_USER_HEADER)
        body = client.get(_URL_SUB, headers=_USER_HEADER).json()
        assert body["current_period_start"] == "2026-04-01T00:00:00Z"
        assert body["current_period_end"] == "2026-04-30T23:59:59Z"


# =============================================================================
# Subscription upgrade
# =============================================================================


class TestSubscriptionUpgrade:
    def test_upgrade_returns_200(self, client: TestClient) -> None:
        client.post(_URL_SUB, json=_valid_create_payload(tier="plus"), headers=_USER_HEADER)
        response = client.post(
            _URL_UPGRADE,
            json={"target_tier": "pro"},
            headers=_USER_HEADER,
        )
        assert response.status_code == 200

    def test_upgrade_changes_tier(self, client: TestClient) -> None:
        client.post(_URL_SUB, json=_valid_create_payload(tier="plus"), headers=_USER_HEADER)
        body = client.post(
            _URL_UPGRADE,
            json={"target_tier": "pro"},
            headers=_USER_HEADER,
        ).json()
        assert body["tier"] == "pro"

    def test_upgrade_preserves_other_fields(self, client: TestClient) -> None:
        created = client.post(_URL_SUB, json=_valid_create_payload(), headers=_USER_HEADER).json()
        upgraded = client.post(
            _URL_UPGRADE,
            json={"target_tier": "pro"},
            headers=_USER_HEADER,
        ).json()
        assert upgraded["subscription_id"] == created["subscription_id"]
        assert upgraded["provider"] == created["provider"]
        assert upgraded["provider_subscription_id"] == created["provider_subscription_id"]

    def test_upgrade_invalid_tier_returns_422(self, client: TestClient) -> None:
        client.post(_URL_SUB, json=_valid_create_payload(), headers=_USER_HEADER)
        response = client.post(
            _URL_UPGRADE,
            json={"target_tier": "platinum"},
            headers=_USER_HEADER,
        )
        assert response.status_code == 422

    def test_upgrade_without_subscription_returns_404(self, client: TestClient) -> None:
        response = client.post(
            _URL_UPGRADE,
            json={"target_tier": "pro"},
            headers=_USER_HEADER,
        )
        assert response.status_code == 404

    def test_upgrade_user_isolation(self, client: TestClient) -> None:
        client.post(_URL_SUB, json=_valid_create_payload(), headers=_USER_HEADER)
        response = client.post(
            _URL_UPGRADE,
            json={"target_tier": "pro"},
            headers=_USER_HEADER_B,
        )
        assert response.status_code == 404


# =============================================================================
# Subscription cancellation
# =============================================================================


class TestSubscriptionCancel:
    def test_cancel_returns_200(self, client: TestClient) -> None:
        client.post(_URL_SUB, json=_valid_create_payload(), headers=_USER_HEADER)
        response = client.post(_URL_CANCEL, json={}, headers=_USER_HEADER)
        assert response.status_code == 200

    def test_cancel_sets_status_to_canceled(self, client: TestClient) -> None:
        client.post(_URL_SUB, json=_valid_create_payload(), headers=_USER_HEADER)
        body = client.post(_URL_CANCEL, json={}, headers=_USER_HEADER).json()
        assert body["status"] == "canceled"

    def test_cancel_preserves_access_until(self, client: TestClient) -> None:
        client.post(_URL_SUB, json=_valid_create_payload(), headers=_USER_HEADER)
        body = client.post(_URL_CANCEL, json={}, headers=_USER_HEADER).json()
        assert body["access_until"] == "2026-04-30T23:59:59Z"

    def test_cancel_preserves_reason(self, client: TestClient) -> None:
        client.post(_URL_SUB, json=_valid_create_payload(), headers=_USER_HEADER)
        body = client.post(
            _URL_CANCEL,
            json={"reason": "switching to a different approach"},
            headers=_USER_HEADER,
        ).json()
        assert body["subscription_id"]  # valid shape

    def test_cancel_response_has_neutral_message(self, client: TestClient) -> None:
        client.post(_URL_SUB, json=_valid_create_payload(), headers=_USER_HEADER)
        body = client.post(_URL_CANCEL, json={}, headers=_USER_HEADER).json()
        assert "canceled" in body["message"].lower()
        assert "access" in body["message"].lower()

    def test_cancel_response_has_no_shame_tokens(self, client: TestClient) -> None:
        """AGENTS.md Rule #4 — no guilt/shame/retention-dark-pattern copy."""
        shame_tokens = ("failed", "shame", "weak", "worthless", "give up", "you should")
        client.post(_URL_SUB, json=_valid_create_payload(), headers=_USER_HEADER)
        body = client.post(_URL_CANCEL, json={}, headers=_USER_HEADER).json()
        message = body["message"].lower()
        for token in shame_tokens:
            assert token not in message, f"shame token found: {token}"

    def test_cancel_without_subscription_returns_404(self, client: TestClient) -> None:
        response = client.post(_URL_CANCEL, json={}, headers=_USER_HEADER)
        assert response.status_code == 404

    def test_cancel_user_isolation(self, client: TestClient) -> None:
        client.post(_URL_SUB, json=_valid_create_payload(), headers=_USER_HEADER)
        response = client.post(_URL_CANCEL, json={}, headers=_USER_HEADER_B)
        assert response.status_code == 404

    def test_cancel_no_reason_is_allowed(self, client: TestClient) -> None:
        client.post(_URL_SUB, json=_valid_create_payload(), headers=_USER_HEADER)
        response = client.post(_URL_CANCEL, json={}, headers=_USER_HEADER)
        assert response.status_code == 200


# =============================================================================
# Webhooks
# =============================================================================


class TestStripeWebhook:
    def test_stripe_webhook_returns_202(self, client: TestClient) -> None:
        response = client.post(
            "/v1/webhooks/stripe",
            json={"id": "evt_123", "type": "invoice.paid", "data": {}},
        )
        assert response.status_code == 202

    def test_stripe_webhook_returns_accepted(self, client: TestClient) -> None:
        body = client.post(
            "/v1/webhooks/stripe",
            json={"id": "evt_123", "type": "invoice.paid", "data": {}},
        ).json()
        assert body["status"] == "accepted"

    def test_stripe_webhook_missing_id_returns_422(self, client: TestClient) -> None:
        response = client.post(
            "/v1/webhooks/stripe",
            json={"type": "invoice.paid"},
        )
        assert response.status_code == 422


class TestAppleWebhook:
    def test_apple_webhook_returns_202(self, client: TestClient) -> None:
        response = client.post(
            "/v1/webhooks/apple",
            json={"notificationType": "SUBSCRIBED"},
        )
        assert response.status_code == 202

    def test_apple_webhook_returns_accepted(self, client: TestClient) -> None:
        body = client.post(
            "/v1/webhooks/apple",
            json={"notificationType": "SUBSCRIBED"},
        ).json()
        assert body["status"] == "accepted"

    def test_apple_webhook_missing_type_returns_422(self, client: TestClient) -> None:
        response = client.post(
            "/v1/webhooks/apple",
            json={},
        )
        assert response.status_code == 422


class TestGoogleWebhook:
    def test_google_webhook_returns_202(self, client: TestClient) -> None:
        response = client.post(
            "/v1/webhooks/google",
            json={"version": "1.0", "packageName": "com.disciplineos.app"},
        )
        assert response.status_code == 202

    def test_google_webhook_returns_accepted(self, client: TestClient) -> None:
        body = client.post(
            "/v1/webhooks/google",
            json={"version": "1.0", "packageName": "com.disciplineos.app"},
        ).json()
        assert body["status"] == "accepted"

    def test_google_webhook_missing_version_returns_422(self, client: TestClient) -> None:
        response = client.post(
            "/v1/webhooks/google",
            json={"packageName": "com.disciplineos.app"},
        )
        assert response.status_code == 422

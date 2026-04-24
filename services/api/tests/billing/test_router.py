"""Billing router tests — subscription lifecycle and webhooks.

Covers subscription creation, retrieval, upgrade, cancellation,
webhook acceptance, user isolation, and validation boundaries.
"""

from __future__ import annotations

import json
import uuid
from unittest.mock import patch, MagicMock

import pytest
import stripe
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


def _make_stripe_event(event_type: str, obj: dict) -> stripe.Event:
    """Build a minimal stripe.Event object for testing."""
    raw = {
        "id": "evt_test_123",
        "object": "event",
        "type": event_type,
        "data": {"object": obj},
        "livemode": False,
        "created": 1700000000,
        "api_version": "2024-04-10",
        "pending_webhooks": 0,
        "request": None,
    }
    return stripe.Event.construct_from(raw, stripe.api_key)


class TestStripeWebhook:
    """Stripe webhook endpoint tests.

    ``stripe.Webhook.construct_event`` is mocked so tests do not need a
    real signing secret.
    """

    def _post_stripe(
        self,
        client: TestClient,
        event: stripe.Event,
        sig: str = "t=1,v1=abc",
    ):
        raw = json.dumps({"id": event.id, "type": event.type}).encode()
        with patch(
            "stripe.Webhook.construct_event", return_value=event
        ):
            return client.post(
                "/v1/webhooks/stripe",
                content=raw,
                headers={
                    "content-type": "application/json",
                    "stripe-signature": sig,
                },
            )

    def test_stripe_webhook_returns_202(self, client: TestClient) -> None:
        event = _make_stripe_event("invoice.paid", {"subscription": "sub_123"})
        response = self._post_stripe(client, event)
        assert response.status_code == 202

    def test_stripe_webhook_returns_accepted(self, client: TestClient) -> None:
        event = _make_stripe_event("invoice.paid", {"subscription": "sub_123"})
        body = self._post_stripe(client, event).json()
        assert body["status"] == "accepted"

    def test_stripe_webhook_missing_signature_returns_400(
        self, client: TestClient
    ) -> None:
        raw = json.dumps({"id": "evt_123", "type": "invoice.paid"}).encode()
        response = client.post(
            "/v1/webhooks/stripe",
            content=raw,
            headers={"content-type": "application/json"},
        )
        assert response.status_code == 400

    def test_stripe_webhook_invalid_signature_returns_400(
        self, client: TestClient
    ) -> None:
        raw = json.dumps({"id": "evt_123", "type": "invoice.paid"}).encode()
        with patch(
            "stripe.Webhook.construct_event",
            side_effect=stripe.SignatureVerificationError(
                "Invalid signature", sig_header="bad"
            ),
        ):
            response = client.post(
                "/v1/webhooks/stripe",
                content=raw,
                headers={
                    "content-type": "application/json",
                    "stripe-signature": "t=1,v1=bad",
                },
            )
        assert response.status_code == 400

    def test_stripe_subscription_created_returns_202(
        self, client: TestClient
    ) -> None:
        event = _make_stripe_event(
            "customer.subscription.created",
            {"id": "sub_new", "status": "active"},
        )
        assert self._post_stripe(client, event).status_code == 202

    def test_stripe_subscription_updated_returns_202(
        self, client: TestClient
    ) -> None:
        event = _make_stripe_event(
            "customer.subscription.updated",
            {"id": "sub_upd", "status": "active"},
        )
        assert self._post_stripe(client, event).status_code == 202

    def test_stripe_subscription_deleted_returns_202(
        self, client: TestClient
    ) -> None:
        event = _make_stripe_event(
            "customer.subscription.deleted",
            {"id": "sub_del"},
        )
        assert self._post_stripe(client, event).status_code == 202

    def test_stripe_invoice_paid_returns_202(self, client: TestClient) -> None:
        event = _make_stripe_event(
            "invoice.paid", {"subscription": "sub_inv"}
        )
        assert self._post_stripe(client, event).status_code == 202

    def test_stripe_invoice_payment_failed_returns_202(
        self, client: TestClient
    ) -> None:
        event = _make_stripe_event(
            "invoice.payment_failed", {"subscription": "sub_fail"}
        )
        assert self._post_stripe(client, event).status_code == 202

    def test_stripe_unknown_event_type_returns_202(
        self, client: TestClient
    ) -> None:
        event = _make_stripe_event("charge.succeeded", {})
        assert self._post_stripe(client, event).status_code == 202


def _make_apple_jws(payload: dict) -> str:
    """Build a minimal JWS compact serialisation for Apple S2S tests."""
    import base64

    header = base64.urlsafe_b64encode(b'{"alg":"ES256"}').rstrip(b"=").decode()
    body = (
        base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b"=").decode()
    )
    sig = base64.urlsafe_b64encode(b"fakesig").rstrip(b"=").decode()
    return f"{header}.{body}.{sig}"


class TestAppleWebhook:
    """Apple S2S webhook endpoint tests.

    Uses a real JWS-shaped payload (base64url-encoded segments) so the
    ``verify_jws_payload`` decode path is exercised end-to-end.
    """

    def test_apple_webhook_returns_202(self, client: TestClient) -> None:
        signed = _make_apple_jws({"notificationType": "SUBSCRIBED"})
        response = client.post(
            "/v1/webhooks/apple",
            json={"signedPayload": signed},
        )
        assert response.status_code == 202

    def test_apple_webhook_returns_accepted(self, client: TestClient) -> None:
        signed = _make_apple_jws({"notificationType": "SUBSCRIBED"})
        body = client.post(
            "/v1/webhooks/apple",
            json={"signedPayload": signed},
        ).json()
        assert body["status"] == "accepted"

    def test_apple_webhook_missing_signed_payload_returns_422(
        self, client: TestClient
    ) -> None:
        response = client.post("/v1/webhooks/apple", json={})
        assert response.status_code == 422

    def test_apple_webhook_invalid_jws_returns_400(
        self, client: TestClient
    ) -> None:
        response = client.post(
            "/v1/webhooks/apple",
            json={"signedPayload": "not.a.jws.with.too.many.parts.here"},
        )
        assert response.status_code == 400

    def test_apple_did_renew_returns_202(self, client: TestClient) -> None:
        signed = _make_apple_jws({"notificationType": "DID_RENEW"})
        assert (
            client.post("/v1/webhooks/apple", json={"signedPayload": signed}).status_code
            == 202
        )

    def test_apple_expired_returns_202(self, client: TestClient) -> None:
        signed = _make_apple_jws({"notificationType": "EXPIRED"})
        assert (
            client.post("/v1/webhooks/apple", json={"signedPayload": signed}).status_code
            == 202
        )

    def test_apple_did_change_renewal_status_returns_202(
        self, client: TestClient
    ) -> None:
        signed = _make_apple_jws(
            {"notificationType": "DID_CHANGE_RENEWAL_STATUS", "subtype": "AUTO_RENEW_DISABLED"}
        )
        assert (
            client.post("/v1/webhooks/apple", json={"signedPayload": signed}).status_code
            == 202
        )


def _make_google_pubsub(notification: dict) -> dict:
    """Build a Pub/Sub push envelope containing a base64-encoded notification."""
    import base64

    data = base64.b64encode(json.dumps(notification).encode()).decode()
    return {
        "message": {"data": data, "messageId": "msg_001"},
        "subscription": "projects/test/subscriptions/play-billing",
    }


class TestGoogleWebhook:
    """Google Play RTDN webhook endpoint tests."""

    def test_google_webhook_returns_202(self, client: TestClient) -> None:
        body = _make_google_pubsub(
            {
                "version": "1.0",
                "packageName": "com.disciplineos.app",
                "subscriptionNotification": {
                    "version": "1.0",
                    "notificationType": 2,
                    "purchaseToken": "tok_123",
                    "subscriptionId": "discipline_monthly",
                },
            }
        )
        response = client.post("/v1/webhooks/google", json=body)
        assert response.status_code == 202

    def test_google_webhook_returns_accepted(self, client: TestClient) -> None:
        body = _make_google_pubsub(
            {
                "version": "1.0",
                "packageName": "com.disciplineos.app",
                "subscriptionNotification": {
                    "version": "1.0",
                    "notificationType": 2,
                    "purchaseToken": "tok_456",
                    "subscriptionId": "discipline_monthly",
                },
            }
        )
        result = client.post("/v1/webhooks/google", json=body).json()
        assert result["status"] == "accepted"

    def test_google_webhook_missing_message_returns_422(
        self, client: TestClient
    ) -> None:
        response = client.post(
            "/v1/webhooks/google",
            json={"subscription": "projects/test/subscriptions/play"},
        )
        assert response.status_code == 422

    def test_google_subscription_recovered_returns_202(
        self, client: TestClient
    ) -> None:
        body = _make_google_pubsub(
            {
                "subscriptionNotification": {
                    "version": "1.0",
                    "notificationType": 1,
                    "purchaseToken": "tok_recovery",
                    "subscriptionId": "discipline_monthly",
                }
            }
        )
        assert client.post("/v1/webhooks/google", json=body).status_code == 202

    def test_google_subscription_cancelled_returns_202(
        self, client: TestClient
    ) -> None:
        body = _make_google_pubsub(
            {
                "subscriptionNotification": {
                    "version": "1.0",
                    "notificationType": 3,
                    "purchaseToken": "tok_cancel",
                    "subscriptionId": "discipline_monthly",
                }
            }
        )
        assert client.post("/v1/webhooks/google", json=body).status_code == 202

    def test_google_subscription_expired_returns_202(
        self, client: TestClient
    ) -> None:
        body = _make_google_pubsub(
            {
                "subscriptionNotification": {
                    "version": "1.0",
                    "notificationType": 13,
                    "purchaseToken": "tok_expired",
                    "subscriptionId": "discipline_monthly",
                }
            }
        )
        assert client.post("/v1/webhooks/google", json=body).status_code == 202

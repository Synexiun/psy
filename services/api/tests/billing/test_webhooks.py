"""Unit tests for billing webhook handlers.

Covers:
- StripeWebhookHandler: signature verification, event routing, state transitions
- AppleS2SWebhookHandler: JWS payload decode, notification routing
- GooglePlayWebhookHandler: base64 decode, RTDN notification routing

``stripe.Webhook.construct_event`` is always mocked so tests do not
require a real Stripe signing secret or network access.
"""

from __future__ import annotations

import base64
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import stripe

from discipline.billing.repository import (
    InMemorySubscriptionRepository,
    reset_subscription_repository,
)
from discipline.billing.webhooks import (
    AppleS2SWebhookHandler,
    GooglePlayWebhookHandler,
    StripeWebhookHandler,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_stripe_event(event_type: str, obj: dict) -> stripe.Event:
    """Construct a minimal stripe.Event for testing."""
    raw = {
        "id": "evt_test_001",
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


def _make_apple_jws(payload: dict) -> str:
    """Build a minimal JWS compact serialisation for tests."""
    header = base64.urlsafe_b64encode(b'{"alg":"ES256"}').rstrip(b"=").decode()
    body = (
        base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b"=").decode()
    )
    sig = base64.urlsafe_b64encode(b"fakesig").rstrip(b"=").decode()
    return f"{header}.{body}.{sig}"


def _make_google_notification(notification_type: int, purchase_token: str) -> dict:
    return {
        "version": "1.0",
        "packageName": "com.disciplineos.app",
        "subscriptionNotification": {
            "version": "1.0",
            "notificationType": notification_type,
            "purchaseToken": purchase_token,
            "subscriptionId": "discipline_monthly",
        },
    }


def _b64_encode_notification(notification: dict) -> str:
    return base64.b64encode(json.dumps(notification).encode()).decode()


@pytest.fixture(autouse=True)
def _reset_repo():
    reset_subscription_repository()


# ---------------------------------------------------------------------------
# StripeWebhookHandler — construct_event
# ---------------------------------------------------------------------------


class TestStripeConstructEvent:
    """Tests for signature verification in StripeWebhookHandler."""

    def test_valid_signature_returns_event(self) -> None:
        handler = StripeWebhookHandler(webhook_secret="whsec_test")
        raw = b'{"id": "evt_1", "type": "invoice.paid"}'
        expected_event = _make_stripe_event("invoice.paid", {"subscription": "sub_x"})

        with patch("stripe.Webhook.construct_event", return_value=expected_event) as mock:
            event = handler.construct_event(raw, "t=1,v1=abc")

        mock.assert_called_once_with(raw, "t=1,v1=abc", "whsec_test")
        assert event.type == "invoice.paid"  # type: ignore[attr-defined]

    def test_invalid_signature_raises_verification_error(self) -> None:
        handler = StripeWebhookHandler(webhook_secret="whsec_test")
        raw = b'{"id": "evt_1"}'

        with patch(
            "stripe.Webhook.construct_event",
            side_effect=stripe.SignatureVerificationError(
                "No signatures found", sig_header="bad"
            ),
        ):
            with pytest.raises(stripe.error.SignatureVerificationError):
                handler.construct_event(raw, "t=1,v1=bad")

    def test_reads_secret_from_env_when_not_provided(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_from_env")
        handler = StripeWebhookHandler()
        assert handler._webhook_secret == "whsec_from_env"

    def test_explicit_secret_overrides_env(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_from_env")
        handler = StripeWebhookHandler(webhook_secret="whsec_explicit")
        assert handler._webhook_secret == "whsec_explicit"

    def test_empty_string_used_when_env_not_set(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("STRIPE_WEBHOOK_SECRET", raising=False)
        handler = StripeWebhookHandler()
        assert handler._webhook_secret == ""


# ---------------------------------------------------------------------------
# StripeWebhookHandler — handle / event routing
# ---------------------------------------------------------------------------


class TestStripeHandle:
    """Event routing tests — all tested with mocked repo."""

    @pytest.fixture
    def handler(self) -> StripeWebhookHandler:
        return StripeWebhookHandler(webhook_secret="whsec_test")

    @pytest.fixture
    def mock_repo(self):
        repo = AsyncMock(spec=InMemorySubscriptionRepository)
        repo.update_status_by_provider_subscription_id = AsyncMock(return_value=None)
        repo.cancel_by_provider_subscription_id = AsyncMock(return_value=None)
        return repo

    async def test_subscription_created_accepted(
        self, handler: StripeWebhookHandler, mock_repo: AsyncMock
    ) -> None:
        event = _make_stripe_event(
            "customer.subscription.created",
            {"id": "sub_new", "status": "active"},
        )
        with patch(
            "discipline.billing.webhooks.get_subscription_repository",
            return_value=mock_repo,
        ):
            result = await handler.handle(event)
        assert result is True
        mock_repo.update_status_by_provider_subscription_id.assert_called_once()
        call_kwargs = mock_repo.update_status_by_provider_subscription_id.call_args
        assert call_kwargs.args[0] == "sub_new"
        assert call_kwargs.kwargs["status"] == "active"

    async def test_subscription_updated_accepted(
        self, handler: StripeWebhookHandler, mock_repo: AsyncMock
    ) -> None:
        event = _make_stripe_event(
            "customer.subscription.updated",
            {"id": "sub_upd", "status": "past_due"},
        )
        with patch(
            "discipline.billing.webhooks.get_subscription_repository",
            return_value=mock_repo,
        ):
            result = await handler.handle(event)
        assert result is True
        call_kwargs = mock_repo.update_status_by_provider_subscription_id.call_args
        assert call_kwargs.kwargs["status"] == "past_due"

    async def test_subscription_deleted_calls_cancel(
        self, handler: StripeWebhookHandler, mock_repo: AsyncMock
    ) -> None:
        event = _make_stripe_event(
            "customer.subscription.deleted",
            {"id": "sub_del"},
        )
        with patch(
            "discipline.billing.webhooks.get_subscription_repository",
            return_value=mock_repo,
        ):
            result = await handler.handle(event)
        assert result is True
        mock_repo.cancel_by_provider_subscription_id.assert_called_once_with(
            "sub_del", reason="stripe_subscription_deleted"
        )

    async def test_invoice_paid_marks_active(
        self, handler: StripeWebhookHandler, mock_repo: AsyncMock
    ) -> None:
        event = _make_stripe_event(
            "invoice.paid", {"subscription": "sub_inv_paid"}
        )
        with patch(
            "discipline.billing.webhooks.get_subscription_repository",
            return_value=mock_repo,
        ):
            result = await handler.handle(event)
        assert result is True
        call_kwargs = mock_repo.update_status_by_provider_subscription_id.call_args
        assert call_kwargs.args[0] == "sub_inv_paid"
        assert call_kwargs.kwargs["status"] == "active"

    async def test_invoice_payment_failed_marks_past_due(
        self, handler: StripeWebhookHandler, mock_repo: AsyncMock
    ) -> None:
        event = _make_stripe_event(
            "invoice.payment_failed", {"subscription": "sub_inv_fail"}
        )
        with patch(
            "discipline.billing.webhooks.get_subscription_repository",
            return_value=mock_repo,
        ):
            result = await handler.handle(event)
        assert result is True
        call_kwargs = mock_repo.update_status_by_provider_subscription_id.call_args
        assert call_kwargs.args[0] == "sub_inv_fail"
        assert call_kwargs.kwargs["status"] == "past_due"

    async def test_unknown_event_type_accepted(
        self, handler: StripeWebhookHandler, mock_repo: AsyncMock
    ) -> None:
        event = _make_stripe_event("charge.succeeded", {"amount": 1000})
        with patch(
            "discipline.billing.webhooks.get_subscription_repository",
            return_value=mock_repo,
        ):
            result = await handler.handle(event)
        assert result is True
        mock_repo.update_status_by_provider_subscription_id.assert_not_called()
        mock_repo.cancel_by_provider_subscription_id.assert_not_called()

    async def test_invoice_paid_missing_subscription_id_still_returns_true(
        self, handler: StripeWebhookHandler, mock_repo: AsyncMock
    ) -> None:
        event = _make_stripe_event("invoice.paid", {})  # no 'subscription' key
        with patch(
            "discipline.billing.webhooks.get_subscription_repository",
            return_value=mock_repo,
        ):
            result = await handler.handle(event)
        assert result is True
        mock_repo.update_status_by_provider_subscription_id.assert_not_called()


# ---------------------------------------------------------------------------
# AppleS2SWebhookHandler — verify_jws_payload
# ---------------------------------------------------------------------------


class TestAppleVerifyJwsPayload:
    """JWS decode tests for AppleS2SWebhookHandler.verify_jws_payload."""

    def test_valid_jws_returns_payload(self) -> None:
        handler = AppleS2SWebhookHandler()
        payload = {"notificationType": "SUBSCRIBED", "subtype": None}
        jws = _make_apple_jws(payload)
        result = handler.verify_jws_payload(jws)
        assert result["notificationType"] == "SUBSCRIBED"

    def test_jws_with_two_parts_raises(self) -> None:
        handler = AppleS2SWebhookHandler()
        with pytest.raises(ValueError, match="Invalid JWS"):
            handler.verify_jws_payload("header.body")

    def test_jws_with_one_part_raises(self) -> None:
        handler = AppleS2SWebhookHandler()
        with pytest.raises(ValueError):
            handler.verify_jws_payload("onlyonepart")

    def test_roundtrip_preserves_all_fields(self) -> None:
        handler = AppleS2SWebhookHandler()
        original = {
            "notificationType": "DID_RENEW",
            "subtype": None,
            "notificationUUID": "uuid-abc-123",
        }
        jws = _make_apple_jws(original)
        result = handler.verify_jws_payload(jws)
        assert result == original

    def test_payload_with_padding_variance(self) -> None:
        """Payloads whose base64url length is not divisible by 4 are handled."""
        handler = AppleS2SWebhookHandler()
        # "x" encodes to 1-byte base64 needing padding
        payload = {"t": "x"}
        jws = _make_apple_jws(payload)
        result = handler.verify_jws_payload(jws)
        assert result["t"] == "x"


# ---------------------------------------------------------------------------
# AppleS2SWebhookHandler — handle / notification routing
# ---------------------------------------------------------------------------


class TestAppleHandle:
    @pytest.fixture
    def handler(self) -> AppleS2SWebhookHandler:
        return AppleS2SWebhookHandler()

    @pytest.fixture
    def mock_repo(self):
        repo = AsyncMock(spec=InMemorySubscriptionRepository)
        repo.update_status_by_provider_subscription_id = AsyncMock(return_value=None)
        repo.cancel_by_provider_subscription_id = AsyncMock(return_value=None)
        return repo

    async def test_subscribed_marks_active(
        self, handler: AppleS2SWebhookHandler, mock_repo: AsyncMock
    ) -> None:
        payload = {
            "notificationType": "SUBSCRIBED",
            "data": {"originalTransactionId": "orig_txn_001"},
        }
        with patch(
            "discipline.billing.webhooks.get_subscription_repository",
            return_value=mock_repo,
        ):
            result = await handler.handle(payload)
        assert result is True
        call_kwargs = mock_repo.update_status_by_provider_subscription_id.call_args
        assert call_kwargs.args[0] == "orig_txn_001"
        assert call_kwargs.kwargs["status"] == "active"

    async def test_did_renew_marks_active(
        self, handler: AppleS2SWebhookHandler, mock_repo: AsyncMock
    ) -> None:
        payload = {
            "notificationType": "DID_RENEW",
            "data": {"originalTransactionId": "orig_txn_002"},
        }
        with patch(
            "discipline.billing.webhooks.get_subscription_repository",
            return_value=mock_repo,
        ):
            result = await handler.handle(payload)
        assert result is True
        call_kwargs = mock_repo.update_status_by_provider_subscription_id.call_args
        assert call_kwargs.kwargs["status"] == "active"

    async def test_expired_cancels_subscription(
        self, handler: AppleS2SWebhookHandler, mock_repo: AsyncMock
    ) -> None:
        payload = {
            "notificationType": "EXPIRED",
            "data": {"originalTransactionId": "orig_txn_003"},
        }
        with patch(
            "discipline.billing.webhooks.get_subscription_repository",
            return_value=mock_repo,
        ):
            result = await handler.handle(payload)
        assert result is True
        mock_repo.cancel_by_provider_subscription_id.assert_called_once_with(
            "orig_txn_003", reason="apple_expired"
        )

    async def test_revoke_cancels_subscription(
        self, handler: AppleS2SWebhookHandler, mock_repo: AsyncMock
    ) -> None:
        payload = {
            "notificationType": "REVOKE",
            "data": {"originalTransactionId": "orig_txn_004"},
        }
        with patch(
            "discipline.billing.webhooks.get_subscription_repository",
            return_value=mock_repo,
        ):
            result = await handler.handle(payload)
        assert result is True
        call_kwargs = mock_repo.cancel_by_provider_subscription_id.call_args
        assert call_kwargs.args[0] == "orig_txn_004"
        assert "revoke" in call_kwargs.kwargs["reason"].lower()

    async def test_did_change_renewal_status_disabled(
        self, handler: AppleS2SWebhookHandler, mock_repo: AsyncMock
    ) -> None:
        payload = {
            "notificationType": "DID_CHANGE_RENEWAL_STATUS",
            "subtype": "AUTO_RENEW_DISABLED",
            "data": {"originalTransactionId": "orig_txn_005"},
        }
        with patch(
            "discipline.billing.webhooks.get_subscription_repository",
            return_value=mock_repo,
        ):
            result = await handler.handle(payload)
        assert result is True
        call_kwargs = mock_repo.update_status_by_provider_subscription_id.call_args
        assert call_kwargs.kwargs["status"] == "pending_cancellation"

    async def test_did_change_renewal_status_enabled(
        self, handler: AppleS2SWebhookHandler, mock_repo: AsyncMock
    ) -> None:
        payload = {
            "notificationType": "DID_CHANGE_RENEWAL_STATUS",
            "subtype": "AUTO_RENEW_ENABLED",
            "data": {"originalTransactionId": "orig_txn_006"},
        }
        with patch(
            "discipline.billing.webhooks.get_subscription_repository",
            return_value=mock_repo,
        ):
            result = await handler.handle(payload)
        assert result is True
        call_kwargs = mock_repo.update_status_by_provider_subscription_id.call_args
        assert call_kwargs.kwargs["status"] == "active"

    async def test_unknown_notification_type_accepted(
        self, handler: AppleS2SWebhookHandler, mock_repo: AsyncMock
    ) -> None:
        payload = {"notificationType": "TEST_NOTIFICATION"}
        with patch(
            "discipline.billing.webhooks.get_subscription_repository",
            return_value=mock_repo,
        ):
            result = await handler.handle(payload)
        assert result is True
        mock_repo.update_status_by_provider_subscription_id.assert_not_called()
        mock_repo.cancel_by_provider_subscription_id.assert_not_called()


# ---------------------------------------------------------------------------
# GooglePlayWebhookHandler — decode_notification
# ---------------------------------------------------------------------------


class TestGoogleDecodeNotification:
    """Base64-decode tests for GooglePlayWebhookHandler.decode_notification."""

    def test_valid_base64_returns_dict(self) -> None:
        handler = GooglePlayWebhookHandler()
        notification = {"version": "1.0", "packageName": "com.test"}
        encoded = base64.b64encode(json.dumps(notification).encode()).decode()
        result = handler.decode_notification(encoded)
        assert result == notification

    def test_roundtrip_preserves_nested_fields(self) -> None:
        handler = GooglePlayWebhookHandler()
        notification = _make_google_notification(2, "tok_roundtrip")
        encoded = _b64_encode_notification(notification)
        result = handler.decode_notification(encoded)
        assert result["subscriptionNotification"]["purchaseToken"] == "tok_roundtrip"

    def test_padding_added_automatically(self) -> None:
        """Standard base64 padding is optional from sender; handler adds it."""
        handler = GooglePlayWebhookHandler()
        notification = {"t": "a"}
        # Strip padding manually
        encoded = base64.b64encode(json.dumps(notification).encode()).decode().rstrip("=")
        result = handler.decode_notification(encoded)
        assert result["t"] == "a"

    def test_invalid_base64_raises(self) -> None:
        handler = GooglePlayWebhookHandler()
        with pytest.raises(Exception):
            handler.decode_notification("!!!not_base64!!!")


# ---------------------------------------------------------------------------
# GooglePlayWebhookHandler — handle / notification routing
# ---------------------------------------------------------------------------


class TestGoogleHandle:
    @pytest.fixture
    def handler(self) -> GooglePlayWebhookHandler:
        return GooglePlayWebhookHandler()

    @pytest.fixture
    def mock_repo(self):
        repo = AsyncMock(spec=InMemorySubscriptionRepository)
        repo.update_status_by_provider_subscription_id = AsyncMock(return_value=None)
        repo.cancel_by_provider_subscription_id = AsyncMock(return_value=None)
        return repo

    async def test_subscription_recovered_marks_active(
        self, handler: GooglePlayWebhookHandler, mock_repo: AsyncMock
    ) -> None:
        notification = _make_google_notification(1, "tok_recovered")
        with patch(
            "discipline.billing.webhooks.get_subscription_repository",
            return_value=mock_repo,
        ):
            result = await handler.handle(notification)
        assert result is True
        call_kwargs = mock_repo.update_status_by_provider_subscription_id.call_args
        assert call_kwargs.args[0] == "tok_recovered"
        assert call_kwargs.kwargs["status"] == "active"

    async def test_subscription_renewed_marks_active(
        self, handler: GooglePlayWebhookHandler, mock_repo: AsyncMock
    ) -> None:
        notification = _make_google_notification(2, "tok_renewed")
        with patch(
            "discipline.billing.webhooks.get_subscription_repository",
            return_value=mock_repo,
        ):
            result = await handler.handle(notification)
        assert result is True
        call_kwargs = mock_repo.update_status_by_provider_subscription_id.call_args
        assert call_kwargs.kwargs["status"] == "active"

    async def test_subscription_cancelled_calls_cancel(
        self, handler: GooglePlayWebhookHandler, mock_repo: AsyncMock
    ) -> None:
        notification = _make_google_notification(3, "tok_cancelled")
        with patch(
            "discipline.billing.webhooks.get_subscription_repository",
            return_value=mock_repo,
        ):
            result = await handler.handle(notification)
        assert result is True
        mock_repo.cancel_by_provider_subscription_id.assert_called_once_with(
            "tok_cancelled", reason="google_play_cancellation"
        )

    async def test_subscription_expired_calls_cancel(
        self, handler: GooglePlayWebhookHandler, mock_repo: AsyncMock
    ) -> None:
        notification = _make_google_notification(13, "tok_expired")
        with patch(
            "discipline.billing.webhooks.get_subscription_repository",
            return_value=mock_repo,
        ):
            result = await handler.handle(notification)
        assert result is True
        mock_repo.cancel_by_provider_subscription_id.assert_called_once_with(
            "tok_expired", reason="google_play_expired"
        )

    async def test_non_subscription_notification_accepted(
        self, handler: GooglePlayWebhookHandler, mock_repo: AsyncMock
    ) -> None:
        """testNotification / oneTimeProductNotification have no subscriptionNotification."""
        notification = {
            "version": "1.0",
            "packageName": "com.disciplineos.app",
            "testNotification": {"version": "1.0"},
        }
        with patch(
            "discipline.billing.webhooks.get_subscription_repository",
            return_value=mock_repo,
        ):
            result = await handler.handle(notification)
        assert result is True
        mock_repo.update_status_by_provider_subscription_id.assert_not_called()
        mock_repo.cancel_by_provider_subscription_id.assert_not_called()

    async def test_unknown_notification_type_accepted(
        self, handler: GooglePlayWebhookHandler, mock_repo: AsyncMock
    ) -> None:
        notification = _make_google_notification(99, "tok_unknown")
        with patch(
            "discipline.billing.webhooks.get_subscription_repository",
            return_value=mock_repo,
        ):
            result = await handler.handle(notification)
        assert result is True
        mock_repo.update_status_by_provider_subscription_id.assert_not_called()
        mock_repo.cancel_by_provider_subscription_id.assert_not_called()

    async def test_subscription_purchased_marks_active(
        self, handler: GooglePlayWebhookHandler, mock_repo: AsyncMock
    ) -> None:
        """notificationType 4 = SUBSCRIPTION_PURCHASED → active."""
        notification = _make_google_notification(4, "tok_purchased")
        with patch(
            "discipline.billing.webhooks.get_subscription_repository",
            return_value=mock_repo,
        ):
            result = await handler.handle(notification)
        assert result is True
        call_kwargs = mock_repo.update_status_by_provider_subscription_id.call_args
        assert call_kwargs.kwargs["status"] == "active"


# ---------------------------------------------------------------------------
# Repository integration — update_status_by_provider_subscription_id
# ---------------------------------------------------------------------------


class TestRepositoryWebhookMethods:
    """Light integration tests for the new repo methods used by webhook handlers."""

    async def test_update_status_by_provider_id(self) -> None:
        from discipline.billing.repository import InMemorySubscriptionRepository

        repo = InMemorySubscriptionRepository()
        await repo.create(
            user_id="user_wh_001",
            tier="plus",
            provider="stripe",
            provider_subscription_id="sub_wh_abc",
            current_period_start="2026-04-01T00:00:00+00:00",
            current_period_end="2026-04-30T23:59:59+00:00",
        )
        updated = await repo.update_status_by_provider_subscription_id(
            "sub_wh_abc", status="past_due"
        )
        assert updated is not None
        assert updated.status == "past_due"

    async def test_cancel_by_provider_id(self) -> None:
        from discipline.billing.repository import InMemorySubscriptionRepository

        repo = InMemorySubscriptionRepository()
        await repo.create(
            user_id="user_wh_002",
            tier="pro",
            provider="stripe",
            provider_subscription_id="sub_wh_def",
            current_period_start="2026-04-01T00:00:00+00:00",
            current_period_end="2026-04-30T23:59:59+00:00",
        )
        cancelled = await repo.cancel_by_provider_subscription_id(
            "sub_wh_def", reason="test_cancel"
        )
        assert cancelled is not None
        assert cancelled.status == "canceled"
        assert cancelled.cancel_reason == "test_cancel"

    async def test_update_status_for_nonexistent_returns_none(self) -> None:
        from discipline.billing.repository import InMemorySubscriptionRepository

        repo = InMemorySubscriptionRepository()
        result = await repo.update_status_by_provider_subscription_id(
            "nonexistent_sub", status="active"
        )
        assert result is None

    async def test_cancel_for_nonexistent_returns_none(self) -> None:
        from discipline.billing.repository import InMemorySubscriptionRepository

        repo = InMemorySubscriptionRepository()
        result = await repo.cancel_by_provider_subscription_id(
            "nonexistent_sub", reason=None
        )
        assert result is None

    async def test_get_by_provider_subscription_id(self) -> None:
        from discipline.billing.repository import InMemorySubscriptionRepository

        repo = InMemorySubscriptionRepository()
        created = await repo.create(
            user_id="user_wh_003",
            tier="free",
            provider="apple_iap",
            provider_subscription_id="orig_txn_999",
            current_period_start="2026-04-01T00:00:00+00:00",
            current_period_end="2026-04-30T23:59:59+00:00",
        )
        fetched = await repo.get_by_provider_subscription_id("orig_txn_999")
        assert fetched is not None
        assert fetched.subscription_id == created.subscription_id

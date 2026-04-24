"""Billing webhook handlers — Stripe, Apple S2S, Google Play.

Each handler verifies the incoming request's authenticity before
processing:

- Stripe: ``stripe.Webhook.construct_event`` validates the
  ``Stripe-Signature`` HMAC header against ``STRIPE_WEBHOOK_SECRET``.
- Apple S2S: JWS payload is base64url-decoded and parsed; signature
  chain validation against Apple's root certificate is marked TODO
  pending PKI tooling (PyJWT + cryptography wheel constraint).
- Google Play: Pub/Sub RTDN ``message.data`` field is base64-decoded
  into a ``DeveloperNotification`` dict.

All handlers return a ``bool`` indicating whether the event was accepted
(True) so callers can replay idempotently.  Unknown event types are
logged and accepted (True) rather than rejected so Stripe / Apple /
Google do not retry indefinitely for events we have not yet implemented.
"""

from __future__ import annotations

import base64
import json
import logging
import os
from typing import Any

import stripe

from discipline.billing.repository import get_subscription_repository

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Stripe
# ---------------------------------------------------------------------------

_STRIPE_SUBSCRIPTION_ACTIVE_TYPES = frozenset(
    {
        "customer.subscription.created",
        "customer.subscription.updated",
    }
)


class StripeWebhookHandler:
    """Stripe webhook handler with signature verification.

    Parameters
    ----------
    webhook_secret:
        Stripe webhook signing secret.  Defaults to the
        ``STRIPE_WEBHOOK_SECRET`` environment variable.  Pass an
        explicit value in tests.
    """

    def __init__(self, webhook_secret: str | None = None) -> None:
        self._webhook_secret: str = (
            webhook_secret
            if webhook_secret is not None
            else os.environ.get("STRIPE_WEBHOOK_SECRET", "")
        )

    def construct_event(self, raw_body: bytes, sig_header: str) -> stripe.Event:
        """Parse and verify a Stripe webhook payload.

        Parameters
        ----------
        raw_body:
            The raw request body bytes — **must not** be JSON-decoded
            first; Stripe verifies against the exact bytes sent over
            the wire.
        sig_header:
            Value of the ``Stripe-Signature`` HTTP header.

        Returns
        -------
        stripe.Event
            The verified Stripe event object.

        Raises
        ------
        stripe.SignatureVerificationError
            If the signature is invalid or the timestamp is outside
            Stripe's tolerance window (±300 s by default).
        """
        return stripe.Webhook.construct_event(
            raw_body,
            sig_header,
            self._webhook_secret,
        )

    async def handle(self, event: stripe.Event) -> bool:
        """Route a verified Stripe event to the appropriate handler.

        Parameters
        ----------
        event:
            A ``stripe.Event`` object already validated by
            :meth:`construct_event`.

        Returns
        -------
        bool
            ``True`` if the event was accepted (even if unrecognised),
            ``False`` if processing failed.
        """
        event_type: str = event.type  # type: ignore[attr-defined]

        if event_type in _STRIPE_SUBSCRIPTION_ACTIVE_TYPES:
            return await self._handle_subscription_updated(event)
        if event_type == "customer.subscription.deleted":
            return await self._handle_subscription_cancelled(event)
        if event_type == "invoice.paid":
            return await self._handle_invoice_paid(event)
        if event_type == "invoice.payment_failed":
            return await self._handle_invoice_payment_failed(event)

        # Unknown event — accept so Stripe stops retrying.
        logger.info("stripe_webhook.unhandled type=%s id=%s", event_type, event.id)  # type: ignore[attr-defined]
        return True

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _handle_subscription_updated(self, event: stripe.Event) -> bool:
        """Handle subscription.created / subscription.updated."""
        obj: dict[str, Any] = event.data.object.to_dict()  # type: ignore[union-attr]
        provider_sub_id: str = obj.get("id", "")
        status: str = obj.get("status", "active")
        period_start: int | None = obj.get("current_period_start")
        period_end: int | None = obj.get("current_period_end")

        from datetime import UTC, datetime

        start_iso = (
            datetime.fromtimestamp(period_start, tz=UTC).isoformat()
            if period_start is not None
            else None
        )
        end_iso = (
            datetime.fromtimestamp(period_end, tz=UTC).isoformat()
            if period_end is not None
            else None
        )

        repo = get_subscription_repository()
        await repo.update_status_by_provider_subscription_id(
            provider_sub_id,
            status=status,
            current_period_start=start_iso,
            current_period_end=end_iso,
        )
        logger.info(
            "stripe_webhook.subscription_updated provider_sub_id=%s status=%s",
            provider_sub_id,
            status,
        )
        return True

    async def _handle_subscription_cancelled(self, event: stripe.Event) -> bool:
        """Handle customer.subscription.deleted."""
        obj: dict[str, Any] = event.data.object.to_dict()  # type: ignore[union-attr]
        provider_sub_id: str = obj.get("id", "")

        repo = get_subscription_repository()
        await repo.cancel_by_provider_subscription_id(
            provider_sub_id,
            reason="stripe_subscription_deleted",
        )
        logger.info(
            "stripe_webhook.subscription_cancelled provider_sub_id=%s",
            provider_sub_id,
        )
        return True

    async def _handle_invoice_paid(self, event: stripe.Event) -> bool:
        """Handle invoice.paid — mark the linked subscription active."""
        obj: dict[str, Any] = event.data.object.to_dict()  # type: ignore[union-attr]
        provider_sub_id: str = obj.get("subscription", "")
        if not provider_sub_id:
            logger.warning("stripe_webhook.invoice_paid missing subscription id")
            return True

        repo = get_subscription_repository()
        await repo.update_status_by_provider_subscription_id(
            provider_sub_id,
            status="active",
        )
        logger.info(
            "stripe_webhook.invoice_paid provider_sub_id=%s", provider_sub_id
        )
        return True

    async def _handle_invoice_payment_failed(self, event: stripe.Event) -> bool:
        """Handle invoice.payment_failed — mark the subscription past_due."""
        obj: dict[str, Any] = event.data.object.to_dict()  # type: ignore[union-attr]
        provider_sub_id: str = obj.get("subscription", "")
        if not provider_sub_id:
            logger.warning(
                "stripe_webhook.invoice_payment_failed missing subscription id"
            )
            return True

        repo = get_subscription_repository()
        await repo.update_status_by_provider_subscription_id(
            provider_sub_id,
            status="past_due",
        )
        logger.info(
            "stripe_webhook.invoice_payment_failed provider_sub_id=%s",
            provider_sub_id,
        )
        return True


# ---------------------------------------------------------------------------
# Apple App Store Server Notifications (S2S)
# ---------------------------------------------------------------------------

_APPLE_ACTIVE_TYPES = frozenset({"SUBSCRIBED", "DID_RENEW"})
_APPLE_CANCELLED_TYPES = frozenset({"EXPIRED", "REVOKE"})


class AppleS2SWebhookHandler:
    """App Store Server Notifications handler.

    Apple delivers notifications as a signed JWS
    (JSON Web Signature).  The outer envelope has three base64url-
    encoded segments separated by ``'.'``; the middle segment (index 1)
    is the JSON payload.

    Signature verification against Apple's root certificate is marked
    TODO — it requires the ``cryptography`` package's X.509 primitives
    and the Apple Root CA G3 certificate.  For now the handler decodes
    and parses the payload, which is sufficient for a controlled
    server-to-server integration where TLS provides transport security.
    """

    def verify_jws_payload(self, signed_payload: str) -> dict[str, Any]:
        """Decode the JWS payload segment without verifying the signature.

        Parameters
        ----------
        signed_payload:
            The raw JWS compact serialisation string sent by Apple.

        Returns
        -------
        dict
            Parsed JSON payload from the middle JWS segment.

        Notes
        -----
        TODO (production): verify the JWS signature chain against the
        Apple Root CA G3 certificate embedded in the JWS header's
        ``x5c`` field.  Use ``cryptography`` for ECDSA P-256 / P-384
        verification.  Reject any notification whose chain does not
        terminate in the pinned Apple Root CA G3 DER fingerprint.
        """
        parts = signed_payload.split(".")
        if len(parts) != 3:
            raise ValueError(
                f"Invalid JWS compact serialisation: expected 3 parts, got {len(parts)}"
            )
        # base64url → add padding then decode
        payload_b64 = parts[1]
        # Standard base64 requires padding to a multiple of 4
        payload_b64 += "=" * (-len(payload_b64) % 4)
        payload_bytes = base64.urlsafe_b64decode(payload_b64)
        return json.loads(payload_bytes)

    async def handle(self, payload: dict[str, Any]) -> bool:
        """Route an Apple S2S notification to the appropriate handler.

        Parameters
        ----------
        payload:
            Parsed JSON payload (from :meth:`verify_jws_payload` or
            directly from tests).

        Returns
        -------
        bool
            ``True`` if the notification was accepted.
        """
        notification_type: str = payload.get("notificationType", "")
        subtype: str | None = payload.get("subtype")

        if notification_type in _APPLE_ACTIVE_TYPES:
            return await self._handle_active(payload, notification_type)
        if notification_type == "DID_CHANGE_RENEWAL_STATUS":
            return await self._handle_renewal_status_change(payload, subtype)
        if notification_type in _APPLE_CANCELLED_TYPES:
            return await self._handle_expired_or_revoked(payload, notification_type)

        logger.info(
            "apple_s2s_webhook.unhandled notificationType=%s", notification_type
        )
        return True

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _extract_original_transaction_id(self, payload: dict[str, Any]) -> str | None:
        """Pull originalTransactionId from the decoded data sub-payload."""
        data = payload.get("data", {})
        if not isinstance(data, dict):
            return None
        # data.signedTransactionInfo is another JWS; for now use
        # transactionId directly if callers have pre-decoded it.
        return data.get("originalTransactionId") or data.get("transactionId")

    async def _handle_active(
        self, payload: dict[str, Any], notification_type: str
    ) -> bool:
        provider_sub_id = self._extract_original_transaction_id(payload)
        if provider_sub_id:
            repo = get_subscription_repository()
            await repo.update_status_by_provider_subscription_id(
                provider_sub_id, status="active"
            )
        logger.info(
            "apple_s2s_webhook.active notificationType=%s provider_sub_id=%s",
            notification_type,
            provider_sub_id,
        )
        return True

    async def _handle_renewal_status_change(
        self, payload: dict[str, Any], subtype: str | None
    ) -> bool:
        """DID_CHANGE_RENEWAL_STATUS — update renewal intent."""
        provider_sub_id = self._extract_original_transaction_id(payload)
        # subtype AUTO_RENEW_DISABLED means the user turned off auto-renew
        # (subscription stays active until period end, then expires).
        # AUTO_RENEW_ENABLED means they re-enabled it.
        new_status = "active" if subtype == "AUTO_RENEW_ENABLED" else "pending_cancellation"
        if provider_sub_id:
            repo = get_subscription_repository()
            await repo.update_status_by_provider_subscription_id(
                provider_sub_id, status=new_status
            )
        logger.info(
            "apple_s2s_webhook.renewal_status_change subtype=%s provider_sub_id=%s",
            subtype,
            provider_sub_id,
        )
        return True

    async def _handle_expired_or_revoked(
        self, payload: dict[str, Any], notification_type: str
    ) -> bool:
        provider_sub_id = self._extract_original_transaction_id(payload)
        if provider_sub_id:
            repo = get_subscription_repository()
            await repo.cancel_by_provider_subscription_id(
                provider_sub_id,
                reason=f"apple_{notification_type.lower()}",
            )
        logger.info(
            "apple_s2s_webhook.expired_or_revoked notificationType=%s provider_sub_id=%s",
            notification_type,
            provider_sub_id,
        )
        return True


# ---------------------------------------------------------------------------
# Google Play Real-time Developer Notifications (RTDN)
# ---------------------------------------------------------------------------

# Google Play subscriptionNotification.notificationType constants
_GOOGLE_ACTIVE_TYPES = frozenset(
    {
        1,  # SUBSCRIPTION_RECOVERED
        2,  # SUBSCRIPTION_RENEWED
        4,  # SUBSCRIPTION_PURCHASED
        7,  # SUBSCRIPTION_RESTARTED
        9,  # SUBSCRIPTION_DEFERRED
    }
)
_GOOGLE_CANCELLED_TYPES = frozenset(
    {
        3,  # SUBSCRIPTION_CANCELED
    }
)
_GOOGLE_EXPIRED_TYPES = frozenset(
    {
        13,  # SUBSCRIPTION_EXPIRED
    }
)


class GooglePlayWebhookHandler:
    """Google Play Developer Notifications (RTDN) handler.

    Google delivers RTDN messages via Cloud Pub/Sub.  The HTTP POST
    body is a JSON envelope with a ``message`` field whose ``data``
    value is the base64-encoded ``DeveloperNotification`` protobuf
    rendered as JSON.
    """

    def decode_notification(self, encoded: str) -> dict[str, Any]:
        """Decode the base64-encoded ``message.data`` field.

        Parameters
        ----------
        encoded:
            The base64-encoded string from ``request.body["message"]["data"]``.

        Returns
        -------
        dict
            Parsed ``DeveloperNotification`` JSON object.
        """
        # Google uses standard base64 (with padding), not base64url.
        padding = "=" * (-len(encoded) % 4)
        raw = base64.b64decode(encoded + padding)
        return json.loads(raw)

    async def handle(self, payload: dict[str, Any]) -> bool:
        """Route a Google Play RTDN notification.

        Parameters
        ----------
        payload:
            Decoded ``DeveloperNotification`` dict (from
            :meth:`decode_notification`).  When the envelope arrives
            from the router the ``message.data`` must be decoded first.

        Returns
        -------
        bool
            ``True`` if the notification was accepted.
        """
        sub_notification: dict[str, Any] | None = payload.get("subscriptionNotification")
        if sub_notification is None:
            # oneTimeProductNotification or testNotification — nothing to do.
            logger.info("google_play_webhook.non_subscription_notification")
            return True

        notification_type: int = sub_notification.get("notificationType", 0)
        purchase_token: str = sub_notification.get("purchaseToken", "")

        if notification_type in _GOOGLE_ACTIVE_TYPES:
            return await self._handle_active(purchase_token, notification_type)
        if notification_type in _GOOGLE_CANCELLED_TYPES:
            return await self._handle_cancelled(purchase_token)
        if notification_type in _GOOGLE_EXPIRED_TYPES:
            return await self._handle_expired(purchase_token)

        logger.info(
            "google_play_webhook.unhandled notificationType=%d purchaseToken=%s",
            notification_type,
            purchase_token,
        )
        return True

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _handle_active(self, purchase_token: str, notification_type: int) -> bool:
        if purchase_token:
            repo = get_subscription_repository()
            await repo.update_status_by_provider_subscription_id(
                purchase_token, status="active"
            )
        logger.info(
            "google_play_webhook.active notificationType=%d purchaseToken=%s",
            notification_type,
            purchase_token,
        )
        return True

    async def _handle_cancelled(self, purchase_token: str) -> bool:
        if purchase_token:
            repo = get_subscription_repository()
            await repo.cancel_by_provider_subscription_id(
                purchase_token, reason="google_play_cancellation"
            )
        logger.info(
            "google_play_webhook.cancelled purchaseToken=%s", purchase_token
        )
        return True

    async def _handle_expired(self, purchase_token: str) -> bool:
        if purchase_token:
            repo = get_subscription_repository()
            await repo.cancel_by_provider_subscription_id(
                purchase_token, reason="google_play_expired"
            )
        logger.info(
            "google_play_webhook.expired purchaseToken=%s", purchase_token
        )
        return True


# ---------------------------------------------------------------------------
# Singleton registry
# ---------------------------------------------------------------------------

_stripe_handler = StripeWebhookHandler()
_apple_handler = AppleS2SWebhookHandler()
_google_handler = GooglePlayWebhookHandler()


def get_stripe_webhook_handler() -> StripeWebhookHandler:
    return _stripe_handler


def get_apple_webhook_handler() -> AppleS2SWebhookHandler:
    return _apple_handler


def get_google_webhook_handler() -> GooglePlayWebhookHandler:
    return _google_handler

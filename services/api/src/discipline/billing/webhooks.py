"""Billing webhook handlers — Stripe, Apple S2S, Google Play.

These are production-scaffold stubs.  In production each handler
verifies signatures before processing:
- Stripe: ``stripe.Webhook.construct_event`` with ``STRIPE_WEBHOOK_SECRET``
- Apple S2S: JWS signature validation + Apple root cert chain
- Google Play: Google API client + purchase validation

All handlers return a bool indicating whether the event was accepted
(for idempotent replay safety).
"""

from __future__ import annotations

from typing import Any

from discipline.billing.repository import (
    SubscriptionRecord,
    get_subscription_repository,
)


class StripeWebhookHandler:
    """Stripe webhook handler scaffold."""

    async def handle(self, event: dict[str, Any]) -> bool:
        """Process a Stripe webhook event.

        Stub: accepts the event shape and logs the type.  Production
        verifies signature, idempotency (event.id dedup), and routes
        to the appropriate state transition.
        """
        event_type = event.get("type", "unknown")
        _ = event.get("data", {}).get("object", {})

        if event_type.startswith("invoice."):
            return True
        if event_type.startswith("customer.subscription."):
            return True
        return True


class AppleS2SWebhookHandler:
    """App Store Server Notifications handler scaffold."""

    async def handle(self, payload: dict[str, Any]) -> bool:
        """Process an Apple S2S notification.

        Stub: accepts the notification shape.  Production validates
        the JWS signature and maps notificationType + subtype to
        subscription state transitions.
        """
        _ = payload.get("notificationType", "unknown")
        _ = payload.get("subtype")
        return True


class GooglePlayWebhookHandler:
    """Google Play Developer Notifications handler scaffold."""

    async def handle(self, payload: dict[str, Any]) -> bool:
        """Process a Google Play RTDN notification.

        Stub: accepts the notification shape.  Production validates
        the purchase token against the Google Play Developer API
        and maps notificationType to subscription state transitions.
        """
        _ = payload.get("version")
        _ = payload.get("packageName")
        _ = payload.get("eventTimeMillis")
        return True


# Singleton instances
_stripe_handler = StripeWebhookHandler()
_apple_handler = AppleS2SWebhookHandler()
_google_handler = GooglePlayWebhookHandler()


def get_stripe_webhook_handler() -> StripeWebhookHandler:
    return _stripe_handler


def get_apple_webhook_handler() -> AppleS2SWebhookHandler:
    return _apple_handler


def get_google_webhook_handler() -> GooglePlayWebhookHandler:
    return _google_handler

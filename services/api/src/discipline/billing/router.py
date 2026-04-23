"""Billing HTTP surface — subscriptions and webhooks.

Endpoints:
- ``GET /v1/subscriptions`` — current subscription for caller
- ``POST /v1/subscriptions`` — create a subscription
- ``POST /v1/subscriptions/upgrade`` — upgrade tier
- ``POST /v1/subscriptions/cancel`` — cancel subscription
- ``POST /v1/webhooks/stripe`` — Stripe webhook
- ``POST /v1/webhooks/apple`` — Apple S2S notification
- ``POST /v1/webhooks/google`` — Google Play RTDN

Auth:
- Subscription endpoints: authenticated (Clerk session → server JWT)
- Webhook endpoints: unauthenticated (signature-verified in handler)
"""

from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from discipline.billing.service import SubscriptionService
from discipline.billing.webhooks import (
    get_apple_webhook_handler,
    get_google_webhook_handler,
    get_stripe_webhook_handler,
)

router = APIRouter(tags=["billing"])


# =============================================================================
# Subscription schemas
# =============================================================================


class SubscriptionCreate(BaseModel):
    """Request body for creating a subscription."""

    tier: str = Field(
        ...,
        pattern=r"^(free|plus|pro|enterprise)$",
    )
    provider: str = Field(
        ...,
        pattern=r"^(stripe|apple_iap|google_iap)$",
    )
    provider_subscription_id: str = Field(..., min_length=1, max_length=255)
    current_period_start: str = Field(..., min_length=1)
    current_period_end: str = Field(..., min_length=1)


class SubscriptionItem(BaseModel):
    """Subscription record response."""

    subscription_id: str
    status: str
    tier: str
    provider: str
    provider_subscription_id: str
    current_period_start: str
    current_period_end: str
    canceled_at: str | None
    cancel_reason: str | None
    created_at: str
    updated_at: str


class SubscriptionUpgradeRequest(BaseModel):
    """Request body for upgrading a subscription."""

    target_tier: str = Field(
        ...,
        pattern=r"^(free|plus|pro|enterprise)$",
    )


class SubscriptionCancelRequest(BaseModel):
    """Request body for canceling a subscription."""

    reason: str | None = Field(
        default=None,
        max_length=255,
        description="Optional cancellation reason for product improvement",
    )


class SubscriptionCancelResponse(BaseModel):
    """Response after cancellation.

    Copy is intentionally neutral — no guilt, no shame, no retention
    dark patterns (AGENTS.md Rule #4 compassion-first stance applied
    to billing interactions).
    """

    subscription_id: str
    status: str
    tier: str
    access_until: str
    message: str


# =============================================================================
# Webhook schemas
# =============================================================================


class StripeWebhookBody(BaseModel):
    """Stripe event envelope."""

    model_config = {"extra": "allow"}

    id: str = Field(..., min_length=1)
    type: str = Field(..., min_length=1)
    data: dict[str, object] = Field(default_factory=dict)


class AppleS2SBody(BaseModel):
    """App Store Server Notification envelope."""

    model_config = {"extra": "allow"}

    notificationType: str = Field(..., min_length=1)


class GooglePlayBody(BaseModel):
    """Google Play Developer Notification envelope."""

    model_config = {"extra": "allow"}

    version: str = Field(..., min_length=1)
    packageName: str = Field(..., min_length=1)


# =============================================================================
# Helpers
# =============================================================================


def _derive_user_id(x_user_id: str | None) -> str:
    """Stub: in production this resolves the server JWT session."""
    return x_user_id or "test_user_001"


def _record_to_item(record: object) -> SubscriptionItem:
    from discipline.billing.repository import SubscriptionRecord

    r = record if isinstance(record, SubscriptionRecord) else record
    return SubscriptionItem(
        subscription_id=r.subscription_id,
        status=r.status,
        tier=r.tier,
        provider=r.provider,
        provider_subscription_id=r.provider_subscription_id,
        current_period_start=r.current_period_start,
        current_period_end=r.current_period_end,
        canceled_at=r.canceled_at,
        cancel_reason=r.cancel_reason,
        created_at=r.created_at,
        updated_at=r.updated_at,
    )


# =============================================================================
# Subscription endpoints
# =============================================================================


@router.get("/subscriptions", response_model=SubscriptionItem)
async def get_subscription(
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
) -> SubscriptionItem:
    """Return the current subscription for the caller."""
    user_id = _derive_user_id(x_user_id)
    service = SubscriptionService()
    record = await service.get_current(user_id)
    if record is None:
        raise HTTPException(status_code=404, detail="subscription.not_found")
    return _record_to_item(record)


@router.post("/subscriptions", response_model=SubscriptionItem, status_code=201)
async def create_subscription(
    payload: SubscriptionCreate,
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
) -> SubscriptionItem:
    """Create a new subscription for the caller."""
    user_id = _derive_user_id(x_user_id)
    service = SubscriptionService()
    record = await service.create_subscription(
        user_id=user_id,
        tier=payload.tier,
        provider=payload.provider,
        provider_subscription_id=payload.provider_subscription_id,
        current_period_start=payload.current_period_start,
        current_period_end=payload.current_period_end,
    )
    return _record_to_item(record)


@router.post("/subscriptions/upgrade", response_model=SubscriptionItem)
async def upgrade_subscription(
    payload: SubscriptionUpgradeRequest,
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
) -> SubscriptionItem:
    """Upgrade the caller's subscription to a higher tier."""
    user_id = _derive_user_id(x_user_id)
    service = SubscriptionService()
    record = await service.upgrade(user_id, payload.target_tier)
    if record is None:
        raise HTTPException(status_code=404, detail="subscription.not_found")
    return _record_to_item(record)


@router.post("/subscriptions/cancel", response_model=SubscriptionCancelResponse)
async def cancel_subscription(
    payload: SubscriptionCancelRequest,
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
) -> SubscriptionCancelResponse:
    """Cancel the caller's subscription.

    Access is retained until the end of the current billing period.
    The response uses neutral copy — no guilt, shame, or retention
    dark patterns.
    """
    user_id = _derive_user_id(x_user_id)
    service = SubscriptionService()
    record = await service.cancel(user_id, reason=payload.reason)
    if record is None:
        raise HTTPException(status_code=404, detail="subscription.not_found")
    return SubscriptionCancelResponse(
        subscription_id=record.subscription_id,
        status=record.status,
        tier=record.tier,
        access_until=record.current_period_end,
        message="Your subscription has been canceled. You'll keep access until the end of your current billing period.",
    )


# =============================================================================
# Webhook endpoints
# =============================================================================


@router.post("/webhooks/stripe", status_code=202)
async def stripe_webhook(payload: StripeWebhookBody) -> dict[str, str]:
    """Receive Stripe webhook events.

    Stub: accepts the event shape.  Production verifies the Stripe
    signature before processing.
    """
    handler = get_stripe_webhook_handler()
    await handler.handle(payload.model_dump())
    return {"status": "accepted"}


@router.post("/webhooks/apple", status_code=202)
async def apple_webhook(payload: AppleS2SBody) -> dict[str, str]:
    """Receive Apple App Store Server Notifications.

    Stub: accepts the notification shape.  Production validates
    the JWS signature before processing.
    """
    handler = get_apple_webhook_handler()
    await handler.handle(payload.model_dump())
    return {"status": "accepted"}


@router.post("/webhooks/google", status_code=202)
async def google_webhook(payload: GooglePlayBody) -> dict[str, str]:
    """Receive Google Play Developer Notifications.

    Stub: accepts the notification shape.  Production validates
    the purchase token against the Google Play Developer API.
    """
    handler = get_google_webhook_handler()
    await handler.handle(payload.model_dump())
    return {"status": "accepted"}

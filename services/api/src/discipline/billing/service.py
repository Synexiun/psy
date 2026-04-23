"""Billing service — subscription lifecycle.

Encodes the subscription state machine:
- ``create_subscription`` — new subscription from Stripe or IAP receipt.
- ``upgrade`` — move to a higher tier (immediate).
- ``cancel`` — mark canceled; access retained until period_end.

No dark patterns: cancellation is immediate, reason is optional,
response copy is neutral and free of guilt/shame language.
"""

from __future__ import annotations

from discipline.billing.repository import (
    SubscriptionRecord,
    get_subscription_repository,
)


class SubscriptionService:
    """User subscription lifecycle manager."""

    def __init__(self, repository: object | None = None) -> None:
        self._repo = repository or get_subscription_repository()

    async def create_subscription(
        self,
        *,
        user_id: str,
        tier: str,
        provider: str,
        provider_subscription_id: str,
        current_period_start: str,
        current_period_end: str,
    ) -> SubscriptionRecord:
        """Create a new subscription for a user."""
        return await self._repo.create(
            user_id=user_id,
            tier=tier,
            provider=provider,
            provider_subscription_id=provider_subscription_id,
            current_period_start=current_period_start,
            current_period_end=current_period_end,
        )

    async def get_current(self, user_id: str) -> SubscriptionRecord | None:
        """Return the current subscription for a user."""
        return await self._repo.get_by_user(user_id)

    async def upgrade(self, user_id: str, target_tier: str) -> SubscriptionRecord | None:
        """Upgrade a user's subscription to a higher tier.

        Returns None if the user has no active subscription.
        """
        record = await self._repo.get_by_user(user_id)
        if record is None:
            return None
        updated = SubscriptionRecord(
            subscription_id=record.subscription_id,
            user_id=record.user_id,
            status=record.status,
            tier=target_tier,
            provider=record.provider,
            provider_subscription_id=record.provider_subscription_id,
            current_period_start=record.current_period_start,
            current_period_end=record.current_period_end,
            canceled_at=record.canceled_at,
            cancel_reason=record.cancel_reason,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )
        return await self._repo.update(updated)

    async def cancel(
        self,
        user_id: str,
        *,
        reason: str | None,
    ) -> SubscriptionRecord | None:
        """Cancel a user's subscription.

        The subscription status changes to ``canceled`` but the user
        retains access until ``current_period_end``.  No guilt or
        retention-dark-pattern copy is returned.
        """
        return await self._repo.cancel(user_id, reason=reason)

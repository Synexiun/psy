"""Billing repository — subscription storage and lifecycle.

Provides both an in-memory stub (for tests and pre-DB dev) and an
async SQLAlchemy implementation (for production).  The interface is
stable so callers don't change when the backend swaps.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from discipline.billing.models import Subscription


@dataclass(frozen=True, slots=True)
class SubscriptionRecord:
    """Plain data object returned by the repository."""

    subscription_id: str
    user_id: str
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


class SubscriptionRepository(Protocol):
    """Protocol for subscription storage backends."""

    async def create(
        self,
        *,
        user_id: str,
        tier: str,
        provider: str,
        provider_subscription_id: str,
        current_period_start: str,
        current_period_end: str,
    ) -> SubscriptionRecord:
        ...

    async def get_by_user(self, user_id: str) -> SubscriptionRecord | None:
        ...

    async def get_by_provider_subscription_id(
        self, provider_subscription_id: str
    ) -> SubscriptionRecord | None:
        ...

    async def update(self, record: SubscriptionRecord) -> SubscriptionRecord:
        ...

    async def update_status_by_provider_subscription_id(
        self,
        provider_subscription_id: str,
        *,
        status: str,
        current_period_start: str | None = None,
        current_period_end: str | None = None,
    ) -> SubscriptionRecord | None:
        ...

    async def cancel_by_provider_subscription_id(
        self,
        provider_subscription_id: str,
        *,
        reason: str | None,
    ) -> SubscriptionRecord | None:
        ...

    async def cancel(
        self,
        user_id: str,
        *,
        reason: str | None,
    ) -> SubscriptionRecord | None:
        ...


# ---------------------------------------------------------------------------
# In-memory stub
# ---------------------------------------------------------------------------


class InMemorySubscriptionRepository:
    """Thread-safe in-memory store for tests and local dev."""

    def __init__(self) -> None:
        self._subscriptions: dict[str, SubscriptionRecord] = {}

    async def create(
        self,
        *,
        user_id: str,
        tier: str,
        provider: str,
        provider_subscription_id: str,
        current_period_start: str,
        current_period_end: str,
    ) -> SubscriptionRecord:
        from uuid import uuid4

        now = datetime.now(UTC).isoformat()
        record = SubscriptionRecord(
            subscription_id=str(uuid4()),
            user_id=user_id,
            status="active",
            tier=tier,
            provider=provider,
            provider_subscription_id=provider_subscription_id,
            current_period_start=current_period_start,
            current_period_end=current_period_end,
            canceled_at=None,
            cancel_reason=None,
            created_at=now,
            updated_at=now,
        )
        self._subscriptions[record.user_id] = record
        return record

    async def get_by_user(self, user_id: str) -> SubscriptionRecord | None:
        return self._subscriptions.get(user_id)

    def _find_by_provider_id(self, provider_subscription_id: str) -> SubscriptionRecord | None:
        for record in self._subscriptions.values():
            if record.provider_subscription_id == provider_subscription_id:
                return record
        return None

    async def get_by_provider_subscription_id(
        self, provider_subscription_id: str
    ) -> SubscriptionRecord | None:
        return self._find_by_provider_id(provider_subscription_id)

    async def update(self, record: SubscriptionRecord) -> SubscriptionRecord:
        self._subscriptions[record.user_id] = record
        return record

    async def update_status_by_provider_subscription_id(
        self,
        provider_subscription_id: str,
        *,
        status: str,
        current_period_start: str | None = None,
        current_period_end: str | None = None,
    ) -> SubscriptionRecord | None:
        record = self._find_by_provider_id(provider_subscription_id)
        if record is None:
            return None
        now = datetime.now(UTC).isoformat()
        updated = SubscriptionRecord(
            subscription_id=record.subscription_id,
            user_id=record.user_id,
            status=status,
            tier=record.tier,
            provider=record.provider,
            provider_subscription_id=record.provider_subscription_id,
            current_period_start=current_period_start or record.current_period_start,
            current_period_end=current_period_end or record.current_period_end,
            canceled_at=record.canceled_at,
            cancel_reason=record.cancel_reason,
            created_at=record.created_at,
            updated_at=now,
        )
        self._subscriptions[record.user_id] = updated
        return updated

    async def cancel_by_provider_subscription_id(
        self,
        provider_subscription_id: str,
        *,
        reason: str | None,
    ) -> SubscriptionRecord | None:
        record = self._find_by_provider_id(provider_subscription_id)
        if record is None:
            return None
        return await self.cancel(record.user_id, reason=reason)

    async def cancel(
        self,
        user_id: str,
        *,
        reason: str | None,
    ) -> SubscriptionRecord | None:
        record = self._subscriptions.get(user_id)
        if record is None:
            return None
        now = datetime.now(UTC).isoformat()
        updated = SubscriptionRecord(
            subscription_id=record.subscription_id,
            user_id=record.user_id,
            status="canceled",
            tier=record.tier,
            provider=record.provider,
            provider_subscription_id=record.provider_subscription_id,
            current_period_start=record.current_period_start,
            current_period_end=record.current_period_end,
            canceled_at=now,
            cancel_reason=reason,
            created_at=record.created_at,
            updated_at=now,
        )
        self._subscriptions[user_id] = updated
        return updated


# ---------------------------------------------------------------------------
# SQLAlchemy implementation
# ---------------------------------------------------------------------------


class SQLAlchemySubscriptionRepository:
    """Production subscription storage backed by PostgreSQL."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        user_id: str,
        tier: str,
        provider: str,
        provider_subscription_id: str,
        current_period_start: str,
        current_period_end: str,
    ) -> SubscriptionRecord:
        from uuid import UUID

        sub = Subscription(
            user_id=UUID(user_id),
            tier=tier,
            provider=provider,
            provider_subscription_id=provider_subscription_id,
            current_period_start=datetime.fromisoformat(current_period_start),
            current_period_end=datetime.fromisoformat(current_period_end),
            status="active",
        )
        self._session.add(sub)
        await self._session.flush()
        return _subscription_to_record(sub)

    async def get_by_user(self, user_id: str) -> SubscriptionRecord | None:
        from uuid import UUID

        result = await self._session.execute(
            select(Subscription).where(Subscription.user_id == UUID(user_id))
        )
        sub = result.scalar_one_or_none()
        return _subscription_to_record(sub) if sub else None

    async def get_by_provider_subscription_id(
        self, provider_subscription_id: str
    ) -> SubscriptionRecord | None:
        result = await self._session.execute(
            select(Subscription).where(
                Subscription.provider_subscription_id == provider_subscription_id
            )
        )
        sub = result.scalar_one_or_none()
        return _subscription_to_record(sub) if sub else None

    async def update_status_by_provider_subscription_id(
        self,
        provider_subscription_id: str,
        *,
        status: str,
        current_period_start: str | None = None,
        current_period_end: str | None = None,
    ) -> SubscriptionRecord | None:
        result = await self._session.execute(
            select(Subscription).where(
                Subscription.provider_subscription_id == provider_subscription_id
            )
        )
        sub = result.scalar_one_or_none()
        if sub is None:
            return None
        sub.status = status
        if current_period_start is not None:
            sub.current_period_start = datetime.fromisoformat(current_period_start)
        if current_period_end is not None:
            sub.current_period_end = datetime.fromisoformat(current_period_end)
        await self._session.flush()
        return _subscription_to_record(sub)

    async def cancel_by_provider_subscription_id(
        self,
        provider_subscription_id: str,
        *,
        reason: str | None,
    ) -> SubscriptionRecord | None:
        result = await self._session.execute(
            select(Subscription).where(
                Subscription.provider_subscription_id == provider_subscription_id
            )
        )
        sub = result.scalar_one_or_none()
        if sub is None:
            return None
        sub.status = "canceled"
        sub.canceled_at = datetime.now(UTC)
        sub.cancel_reason = reason
        await self._session.flush()
        return _subscription_to_record(sub)

    async def update(self, record: SubscriptionRecord) -> SubscriptionRecord:
        from uuid import UUID

        result = await self._session.execute(
            select(Subscription).where(Subscription.user_id == UUID(record.user_id))
        )
        sub = result.scalar_one()
        sub.status = record.status
        sub.tier = record.tier
        sub.provider_subscription_id = record.provider_subscription_id
        sub.current_period_start = datetime.fromisoformat(record.current_period_start)
        sub.current_period_end = datetime.fromisoformat(record.current_period_end)
        sub.canceled_at = datetime.fromisoformat(record.canceled_at) if record.canceled_at else None
        sub.cancel_reason = record.cancel_reason
        await self._session.flush()
        return _subscription_to_record(sub)

    async def cancel(
        self,
        user_id: str,
        *,
        reason: str | None,
    ) -> SubscriptionRecord | None:
        from uuid import UUID

        result = await self._session.execute(
            select(Subscription).where(Subscription.user_id == UUID(user_id))
        )
        sub = result.scalar_one_or_none()
        if sub is None:
            return None
        sub.status = "canceled"
        sub.canceled_at = datetime.now(UTC)
        sub.cancel_reason = reason
        await self._session.flush()
        return _subscription_to_record(sub)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _subscription_to_record(sub: Subscription) -> SubscriptionRecord:
    return SubscriptionRecord(
        subscription_id=str(sub.id),
        user_id=str(sub.user_id),
        status=sub.status,
        tier=sub.tier,
        provider=sub.provider,
        provider_subscription_id=sub.provider_subscription_id,
        current_period_start=sub.current_period_start.isoformat(),
        current_period_end=sub.current_period_end.isoformat(),
        canceled_at=sub.canceled_at.isoformat() if sub.canceled_at else None,
        cancel_reason=sub.cancel_reason,
        created_at=sub.created_at.isoformat(),
        updated_at=sub.updated_at.isoformat(),
    )


# ---------------------------------------------------------------------------
# Singleton registry (dev/test in-memory; prod binds to SQLAlchemy)
# ---------------------------------------------------------------------------

_subscription_repo: SubscriptionRepository = InMemorySubscriptionRepository()


def get_subscription_repository() -> SubscriptionRepository:
    return _subscription_repo


def reset_subscription_repository() -> None:
    global _subscription_repo
    _subscription_repo = InMemorySubscriptionRepository()

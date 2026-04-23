"""Notifications repository — nudge and push token storage.

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

from discipline.notifications.models import Nudge, PushToken


@dataclass(frozen=True, slots=True)
class NudgeRecord:
    """Plain data object returned by the repository."""

    nudge_id: str
    user_id: str
    nudge_type: str
    status: str
    scheduled_at: str
    sent_at: str | None
    tool_variant: str | None
    message_copy: str | None
    created_at: str


@dataclass(frozen=True, slots=True)
class PushTokenRecord:
    """Plain data object returned by the repository."""

    token_id: str
    user_id: str
    platform: str
    token_hash: str
    created_at: str
    last_valid_at: str | None


class NudgeRepository(Protocol):
    """Protocol for nudge storage backends."""

    async def create(
        self,
        *,
        user_id: str,
        nudge_type: str,
        scheduled_at: str,
        tool_variant: str | None,
        message_copy: str | None,
    ) -> NudgeRecord:
        ...

    async def list_by_user(
        self, user_id: str, *, limit: int = 50
    ) -> list[NudgeRecord]:
        ...

    async def mark_sent(self, nudge_id: str, user_id: str) -> NudgeRecord | None:
        ...


class PushTokenRepository(Protocol):
    """Protocol for push token storage backends."""

    async def create(
        self,
        *,
        user_id: str,
        platform: str,
        token_hash: str,
        token_encrypted: str,
    ) -> PushTokenRecord:
        ...

    async def list_by_user(self, user_id: str) -> list[PushTokenRecord]:
        ...


# ---------------------------------------------------------------------------
# In-memory stubs
# ---------------------------------------------------------------------------


class InMemoryNudgeRepository:
    """Thread-safe in-memory store for tests and local dev."""

    def __init__(self) -> None:
        self._nudges: dict[str, NudgeRecord] = {}

    async def create(
        self,
        *,
        user_id: str,
        nudge_type: str,
        scheduled_at: str,
        tool_variant: str | None,
        message_copy: str | None,
    ) -> NudgeRecord:
        from uuid import uuid4

        now = datetime.now(UTC).isoformat()
        record = NudgeRecord(
            nudge_id=str(uuid4()),
            user_id=user_id,
            nudge_type=nudge_type,
            status="scheduled",
            scheduled_at=scheduled_at,
            sent_at=None,
            tool_variant=tool_variant,
            message_copy=message_copy,
            created_at=now,
        )
        self._nudges[record.nudge_id] = record
        return record

    async def list_by_user(
        self, user_id: str, *, limit: int = 50
    ) -> list[NudgeRecord]:
        results = [r for r in self._nudges.values() if r.user_id == user_id]
        results.sort(key=lambda r: r.scheduled_at, reverse=True)
        return results[:limit]

    async def mark_sent(self, nudge_id: str, user_id: str) -> NudgeRecord | None:
        record = self._nudges.get(nudge_id)
        if record is None or record.user_id != user_id:
            return None
        updated = NudgeRecord(
            nudge_id=record.nudge_id,
            user_id=record.user_id,
            nudge_type=record.nudge_type,
            status="sent",
            scheduled_at=record.scheduled_at,
            sent_at=datetime.now(UTC).isoformat(),
            tool_variant=record.tool_variant,
            message_copy=record.message_copy,
            created_at=record.created_at,
        )
        self._nudges[nudge_id] = updated
        return updated


class InMemoryPushTokenRepository:
    """Thread-safe in-memory store for tests and local dev."""

    def __init__(self) -> None:
        self._tokens: dict[str, PushTokenRecord] = {}

    async def create(
        self,
        *,
        user_id: str,
        platform: str,
        token_hash: str,
        token_encrypted: str,
    ) -> PushTokenRecord:
        from uuid import uuid4

        now = datetime.now(UTC).isoformat()
        record = PushTokenRecord(
            token_id=str(uuid4()),
            user_id=user_id,
            platform=platform,
            token_hash=token_hash,
            created_at=now,
            last_valid_at=now,
        )
        self._tokens[record.token_id] = record
        return record

    async def list_by_user(self, user_id: str) -> list[PushTokenRecord]:
        return [r for r in self._tokens.values() if r.user_id == user_id]


# ---------------------------------------------------------------------------
# SQLAlchemy implementations
# ---------------------------------------------------------------------------


class SQLAlchemyNudgeRepository:
    """Production nudge storage backed by PostgreSQL."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        user_id: str,
        nudge_type: str,
        scheduled_at: str,
        tool_variant: str | None,
        message_copy: str | None,
    ) -> NudgeRecord:
        from uuid import UUID

        nudge = Nudge(
            user_id=UUID(user_id),
            nudge_type=nudge_type,
            scheduled_at=datetime.fromisoformat(scheduled_at),
            tool_variant=tool_variant,
            message_copy=message_copy,
        )
        self._session.add(nudge)
        await self._session.flush()
        return _nudge_to_record(nudge)

    async def list_by_user(
        self, user_id: str, *, limit: int = 50
    ) -> list[NudgeRecord]:
        from uuid import UUID

        result = await self._session.execute(
            select(Nudge)
            .where(Nudge.user_id == UUID(user_id))
            .order_by(Nudge.scheduled_at.desc())
            .limit(limit)
        )
        return [_nudge_to_record(n) for n in result.scalars().all()]

    async def mark_sent(self, nudge_id: str, user_id: str) -> NudgeRecord | None:
        from uuid import UUID

        result = await self._session.execute(
            select(Nudge).where(
                Nudge.id == UUID(nudge_id),
                Nudge.user_id == UUID(user_id),
            )
        )
        nudge = result.scalar_one_or_none()
        if nudge is None:
            return None
        nudge.status = "sent"
        nudge.sent_at = datetime.now(UTC)
        await self._session.flush()
        return _nudge_to_record(nudge)


class SQLAlchemyPushTokenRepository:
    """Production push token storage backed by PostgreSQL."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        user_id: str,
        platform: str,
        token_hash: str,
        token_encrypted: str,
    ) -> PushTokenRecord:
        from uuid import UUID

        token = PushToken(
            user_id=UUID(user_id),
            platform=platform,
            token_hash=token_hash,
            token_encrypted=token_encrypted,
            last_valid_at=datetime.now(UTC),
        )
        self._session.add(token)
        await self._session.flush()
        return _token_to_record(token)

    async def list_by_user(self, user_id: str) -> list[PushTokenRecord]:
        from uuid import UUID

        result = await self._session.execute(
            select(PushToken).where(PushToken.user_id == UUID(user_id))
        )
        return [_token_to_record(t) for t in result.scalars().all()]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _nudge_to_record(nudge: Nudge) -> NudgeRecord:
    return NudgeRecord(
        nudge_id=str(nudge.id),
        user_id=str(nudge.user_id),
        nudge_type=nudge.nudge_type,
        status=nudge.status,
        scheduled_at=nudge.scheduled_at.isoformat(),
        sent_at=nudge.sent_at.isoformat() if nudge.sent_at else None,
        tool_variant=nudge.tool_variant,
        message_copy=nudge.message_copy,
        created_at=nudge.created_at.isoformat(),
    )


def _token_to_record(token: PushToken) -> PushTokenRecord:
    return PushTokenRecord(
        token_id=str(token.id),
        user_id=str(token.user_id),
        platform=token.platform,
        token_hash=token.token_hash,
        created_at=token.created_at.isoformat(),
        last_valid_at=token.last_valid_at.isoformat() if token.last_valid_at else None,
    )


# ---------------------------------------------------------------------------
# Singleton registry (dev/test in-memory; prod binds to SQLAlchemy)
# ---------------------------------------------------------------------------

_nudge_repo: NudgeRepository = InMemoryNudgeRepository()
_token_repo: PushTokenRepository = InMemoryPushTokenRepository()


def get_nudge_repository() -> NudgeRepository:
    return _nudge_repo


def get_push_token_repository() -> PushTokenRepository:
    return _token_repo


def reset_notification_repositories() -> None:
    global _nudge_repo, _token_repo
    _nudge_repo = InMemoryNudgeRepository()
    _token_repo = InMemoryPushTokenRepository()

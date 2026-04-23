"""Clinical repository — relapse event storage.

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

from discipline.clinical.models import RelapseEvent


@dataclass(frozen=True, slots=True)
class RelapseRecord:
    """Plain data object returned by the repository."""

    relapse_id: str
    user_id: str
    occurred_at: str
    behavior: str
    severity: int
    context_tags: list[str]
    compassion_message: str
    reviewed: bool
    reviewed_at: str | None
    reviewed_by: str | None
    created_at: str


class RelapseRepository(Protocol):
    """Protocol for relapse storage backends."""

    async def create(
        self,
        *,
        user_id: str,
        occurred_at: str,
        behavior: str,
        severity: int,
        context_tags: list[str],
        compassion_message: str,
    ) -> RelapseRecord:
        ...

    async def get_by_id(self, relapse_id: str, user_id: str) -> RelapseRecord | None:
        ...

    async def mark_reviewed(
        self,
        relapse_id: str,
        user_id: str,
        *,
        reviewed_by: str,
    ) -> RelapseRecord | None:
        ...


# ---------------------------------------------------------------------------
# In-memory stub
# ---------------------------------------------------------------------------


class InMemoryRelapseRepository:
    """Thread-safe in-memory store for tests and local dev."""

    def __init__(self) -> None:
        self._relapses: dict[str, RelapseRecord] = {}

    async def create(
        self,
        *,
        user_id: str,
        occurred_at: str,
        behavior: str,
        severity: int,
        context_tags: list[str],
        compassion_message: str,
    ) -> RelapseRecord:
        from uuid import uuid4

        now = datetime.now(UTC).isoformat()
        record = RelapseRecord(
            relapse_id=str(uuid4()),
            user_id=user_id,
            occurred_at=occurred_at,
            behavior=behavior,
            severity=severity,
            context_tags=list(context_tags),
            compassion_message=compassion_message,
            reviewed=False,
            reviewed_at=None,
            reviewed_by=None,
            created_at=now,
        )
        self._relapses[record.relapse_id] = record
        return record

    async def get_by_id(self, relapse_id: str, user_id: str) -> RelapseRecord | None:
        record = self._relapses.get(relapse_id)
        if record is None or record.user_id != user_id:
            return None
        return record

    async def mark_reviewed(
        self,
        relapse_id: str,
        user_id: str,
        *,
        reviewed_by: str,
    ) -> RelapseRecord | None:
        record = self._relapses.get(relapse_id)
        if record is None or record.user_id != user_id:
            return None
        now = datetime.now(UTC).isoformat()
        updated = RelapseRecord(
            relapse_id=record.relapse_id,
            user_id=record.user_id,
            occurred_at=record.occurred_at,
            behavior=record.behavior,
            severity=record.severity,
            context_tags=record.context_tags,
            compassion_message=record.compassion_message,
            reviewed=True,
            reviewed_at=now,
            reviewed_by=reviewed_by,
            created_at=record.created_at,
        )
        self._relapses[relapse_id] = updated
        return updated


# ---------------------------------------------------------------------------
# SQLAlchemy implementation
# ---------------------------------------------------------------------------


class SQLAlchemyRelapseRepository:
    """Production relapse storage backed by PostgreSQL."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        user_id: str,
        occurred_at: str,
        behavior: str,
        severity: int,
        context_tags: list[str],
        compassion_message: str,
    ) -> RelapseRecord:
        from uuid import UUID

        event = RelapseEvent(
            user_id=UUID(user_id),
            occurred_at=datetime.fromisoformat(occurred_at),
            behavior=behavior,
            severity=severity,
            context_tags=list(context_tags),
            compassion_message=compassion_message,
        )
        self._session.add(event)
        await self._session.flush()
        return _relapse_to_record(event)

    async def get_by_id(self, relapse_id: str, user_id: str) -> RelapseRecord | None:
        from uuid import UUID

        result = await self._session.execute(
            select(RelapseEvent).where(
                RelapseEvent.id == UUID(relapse_id),
                RelapseEvent.user_id == UUID(user_id),
            )
        )
        event = result.scalar_one_or_none()
        return _relapse_to_record(event) if event else None

    async def mark_reviewed(
        self,
        relapse_id: str,
        user_id: str,
        *,
        reviewed_by: str,
    ) -> RelapseRecord | None:
        from uuid import UUID

        result = await self._session.execute(
            select(RelapseEvent).where(
                RelapseEvent.id == UUID(relapse_id),
                RelapseEvent.user_id == UUID(user_id),
            )
        )
        event = result.scalar_one_or_none()
        if event is None:
            return None
        event.reviewed = True
        event.reviewed_at = datetime.now(UTC)
        event.reviewed_by = reviewed_by
        await self._session.flush()
        return _relapse_to_record(event)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _relapse_to_record(event: RelapseEvent) -> RelapseRecord:
    return RelapseRecord(
        relapse_id=str(event.id),
        user_id=str(event.user_id),
        occurred_at=event.occurred_at.isoformat(),
        behavior=event.behavior,
        severity=event.severity,
        context_tags=list(event.context_tags),
        compassion_message=event.compassion_message,
        reviewed=event.reviewed,
        reviewed_at=event.reviewed_at.isoformat() if event.reviewed_at else None,
        reviewed_by=event.reviewed_by,
        created_at=event.created_at.isoformat(),
    )


# ---------------------------------------------------------------------------
# Singleton registry (dev/test in-memory; prod binds to SQLAlchemy)
# ---------------------------------------------------------------------------

_relapse_repo: RelapseRepository = InMemoryRelapseRepository()


def get_relapse_repository() -> RelapseRepository:
    return _relapse_repo


def reset_relapse_repository() -> None:
    global _relapse_repo
    _relapse_repo = InMemoryRelapseRepository()

"""Resilience repository — streak state storage.

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

from discipline.resilience.models import StreakStateModel


@dataclass(frozen=True, slots=True)
class StreakStateRecord:
    """Plain data object returned by the repository."""

    user_id: str
    continuous_days: int
    continuous_streak_start: str | None
    resilience_days: int
    resilience_urges_handled_total: int
    resilience_streak_start: str
    updated_at: str


class StreakStateRepository(Protocol):
    """Protocol for streak state storage backends."""

    async def get_or_create(self, user_id: str) -> StreakStateRecord:
        ...

    async def update(self, record: StreakStateRecord) -> StreakStateRecord:
        ...


# ---------------------------------------------------------------------------
# In-memory stub
# ---------------------------------------------------------------------------


class InMemoryStreakStateRepository:
    """Thread-safe in-memory store for tests and local dev."""

    def __init__(self) -> None:
        self._states: dict[str, StreakStateRecord] = {}

    async def get_or_create(self, user_id: str) -> StreakStateRecord:
        if user_id in self._states:
            return self._states[user_id]
        now = datetime.now(UTC).isoformat()
        record = StreakStateRecord(
            user_id=user_id,
            continuous_days=0,
            continuous_streak_start=None,
            resilience_days=0,
            resilience_urges_handled_total=0,
            resilience_streak_start=now,
            updated_at=now,
        )
        self._states[user_id] = record
        return record

    async def update(self, record: StreakStateRecord) -> StreakStateRecord:
        self._states[record.user_id] = record
        return record


# ---------------------------------------------------------------------------
# SQLAlchemy implementation
# ---------------------------------------------------------------------------


class SQLAlchemyStreakStateRepository:
    """Production streak state storage backed by PostgreSQL."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_or_create(self, user_id: str) -> StreakStateRecord:
        from uuid import UUID

        result = await self._session.execute(
            select(StreakStateModel).where(StreakStateModel.user_id == UUID(user_id))
        )
        state = result.scalar_one_or_none()
        if state is None:
            state = StreakStateModel(user_id=UUID(user_id))
            self._session.add(state)
            await self._session.flush()
        return _state_to_record(state)

    async def update(self, record: StreakStateRecord) -> StreakStateRecord:
        from uuid import UUID

        result = await self._session.execute(
            select(StreakStateModel).where(StreakStateModel.user_id == UUID(record.user_id))
        )
        state = result.scalar_one()
        state.continuous_days = record.continuous_days
        state.continuous_streak_start = (
            datetime.fromisoformat(record.continuous_streak_start)
            if record.continuous_streak_start
            else None
        )
        state.resilience_days = record.resilience_days
        state.resilience_urges_handled_total = record.resilience_urges_handled_total
        state.resilience_streak_start = datetime.fromisoformat(record.resilience_streak_start)
        state.updated_at = datetime.now(UTC)
        await self._session.flush()
        return _state_to_record(state)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _state_to_record(state: StreakStateModel) -> StreakStateRecord:
    return StreakStateRecord(
        user_id=str(state.user_id),
        continuous_days=state.continuous_days,
        continuous_streak_start=state.continuous_streak_start.isoformat() if state.continuous_streak_start else None,
        resilience_days=state.resilience_days,
        resilience_urges_handled_total=state.resilience_urges_handled_total,
        resilience_streak_start=state.resilience_streak_start.isoformat(),
        updated_at=state.updated_at.isoformat(),
    )


# ---------------------------------------------------------------------------
# Singleton registry (dev/test in-memory; prod binds to SQLAlchemy)
# ---------------------------------------------------------------------------

_streak_repo: StreakStateRepository = InMemoryStreakStateRepository()


def get_streak_state_repository() -> StreakStateRepository:
    return _streak_repo


def reset_streak_repository() -> None:
    global _streak_repo
    _streak_repo = InMemoryStreakStateRepository()

"""Pattern repository — pattern storage and lifecycle.

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

from discipline.pattern.models import Pattern


@dataclass(frozen=True, slots=True)
class PatternRecord:
    """Plain data object returned by the repository."""

    pattern_id: str
    user_id: str
    pattern_type: str
    detector: str
    confidence: float
    description: str
    metadata_json: dict[str, object]
    status: str
    dismissed_at: str | None
    dismiss_reason: str | None
    created_at: str
    updated_at: str


class PatternRepository(Protocol):
    """Protocol for pattern storage backends."""

    async def create(
        self,
        *,
        user_id: str,
        pattern_type: str,
        detector: str,
        confidence: float,
        description: str,
        metadata_json: dict[str, object],
    ) -> PatternRecord:
        ...

    async def list_by_user(
        self,
        user_id: str,
        *,
        limit: int = 50,
        status_filter: str | None = None,
    ) -> list[PatternRecord]:
        ...

    async def get_by_id(self, pattern_id: str, user_id: str) -> PatternRecord | None:
        ...

    async def dismiss(
        self,
        pattern_id: str,
        user_id: str,
        *,
        reason: str | None,
    ) -> PatternRecord | None:
        ...


# ---------------------------------------------------------------------------
# In-memory stub
# ---------------------------------------------------------------------------


class InMemoryPatternRepository:
    """Thread-safe in-memory store for tests and local dev."""

    def __init__(self) -> None:
        self._patterns: dict[str, PatternRecord] = {}

    async def create(
        self,
        *,
        user_id: str,
        pattern_type: str,
        detector: str,
        confidence: float,
        description: str,
        metadata_json: dict[str, object],
    ) -> PatternRecord:
        from uuid import uuid4

        now = datetime.now(UTC).isoformat()
        record = PatternRecord(
            pattern_id=str(uuid4()),
            user_id=user_id,
            pattern_type=pattern_type,
            detector=detector,
            confidence=confidence,
            description=description,
            metadata_json=metadata_json,
            status="active",
            dismissed_at=None,
            dismiss_reason=None,
            created_at=now,
            updated_at=now,
        )
        self._patterns[record.pattern_id] = record
        return record

    async def list_by_user(
        self,
        user_id: str,
        *,
        limit: int = 50,
        status_filter: str | None = None,
    ) -> list[PatternRecord]:
        results = [
            r for r in self._patterns.values()
            if r.user_id == user_id
            and (status_filter is None or r.status == status_filter)
        ]
        results.sort(key=lambda r: r.created_at, reverse=True)
        return results[:limit]

    async def get_by_id(self, pattern_id: str, user_id: str) -> PatternRecord | None:
        record = self._patterns.get(pattern_id)
        if record is None or record.user_id != user_id:
            return None
        return record

    async def dismiss(
        self,
        pattern_id: str,
        user_id: str,
        *,
        reason: str | None,
    ) -> PatternRecord | None:
        record = self._patterns.get(pattern_id)
        if record is None or record.user_id != user_id:
            return None
        now = datetime.now(UTC).isoformat()
        updated = PatternRecord(
            pattern_id=record.pattern_id,
            user_id=record.user_id,
            pattern_type=record.pattern_type,
            detector=record.detector,
            confidence=record.confidence,
            description=record.description,
            metadata_json=record.metadata_json,
            status="dismissed",
            dismissed_at=now,
            dismiss_reason=reason,
            created_at=record.created_at,
            updated_at=now,
        )
        self._patterns[pattern_id] = updated
        return updated


# ---------------------------------------------------------------------------
# SQLAlchemy implementation
# ---------------------------------------------------------------------------


class SQLAlchemyPatternRepository:
    """Production pattern storage backed by PostgreSQL."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        user_id: str,
        pattern_type: str,
        detector: str,
        confidence: float,
        description: str,
        metadata_json: dict[str, object],
    ) -> PatternRecord:
        from uuid import UUID

        pattern = Pattern(
            user_id=UUID(user_id),
            pattern_type=pattern_type,
            detector=detector,
            confidence=confidence,
            description=description,
            metadata_json=metadata_json,
            status="active",
        )
        self._session.add(pattern)
        await self._session.flush()
        return _pattern_to_record(pattern)

    async def list_by_user(
        self,
        user_id: str,
        *,
        limit: int = 50,
        status_filter: str | None = None,
    ) -> list[PatternRecord]:
        from uuid import UUID

        stmt = (
            select(Pattern)
            .where(Pattern.user_id == UUID(user_id))
            .order_by(Pattern.created_at.desc())
            .limit(limit)
        )
        if status_filter is not None:
            stmt = stmt.where(Pattern.status == status_filter)
        result = await self._session.execute(stmt)
        return [_pattern_to_record(p) for p in result.scalars().all()]

    async def get_by_id(self, pattern_id: str, user_id: str) -> PatternRecord | None:
        from uuid import UUID

        result = await self._session.execute(
            select(Pattern).where(
                Pattern.id == UUID(pattern_id),
                Pattern.user_id == UUID(user_id),
            )
        )
        pattern = result.scalar_one_or_none()
        return _pattern_to_record(pattern) if pattern else None

    async def dismiss(
        self,
        pattern_id: str,
        user_id: str,
        *,
        reason: str | None,
    ) -> PatternRecord | None:
        from uuid import UUID

        result = await self._session.execute(
            select(Pattern).where(
                Pattern.id == UUID(pattern_id),
                Pattern.user_id == UUID(user_id),
            )
        )
        pattern = result.scalar_one_or_none()
        if pattern is None:
            return None
        pattern.status = "dismissed"
        pattern.dismissed_at = datetime.now(UTC)
        pattern.dismiss_reason = reason
        await self._session.flush()
        return _pattern_to_record(pattern)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _pattern_to_record(pattern: Pattern) -> PatternRecord:
    return PatternRecord(
        pattern_id=str(pattern.id),
        user_id=str(pattern.user_id),
        pattern_type=pattern.pattern_type,
        detector=pattern.detector,
        confidence=pattern.confidence,
        description=pattern.description,
        metadata_json=dict(pattern.metadata_json),
        status=pattern.status,
        dismissed_at=pattern.dismissed_at.isoformat() if pattern.dismissed_at else None,
        dismiss_reason=pattern.dismiss_reason,
        created_at=pattern.created_at.isoformat(),
        updated_at=pattern.updated_at.isoformat(),
    )


# ---------------------------------------------------------------------------
# Singleton registry (dev/test in-memory; prod binds to SQLAlchemy)
# ---------------------------------------------------------------------------

_pattern_repo: PatternRepository = InMemoryPatternRepository()


def get_pattern_repository() -> PatternRepository:
    return _pattern_repo


def reset_pattern_repository() -> None:
    global _pattern_repo
    _pattern_repo = InMemoryPatternRepository()

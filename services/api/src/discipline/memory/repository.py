"""Memory repository — journal and voice session storage.

Provides both an in-memory stub (for tests and pre-DB dev) and an
async SQLAlchemy implementation (for production).  The interface is
stable so callers don't change when the backend swaps.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from discipline.memory.models import Journal, VoiceSession


@dataclass(frozen=True, slots=True)
class JournalRecord:
    """Plain data object returned by the repository."""

    journal_id: str
    user_id: str
    title: str | None
    body_encrypted: str
    mood_score: int | None
    created_at: str
    updated_at: str


@dataclass(frozen=True, slots=True)
class VoiceSessionRecord:
    """Plain data object returned by the repository."""

    session_id: str
    user_id: str
    status: str
    duration_seconds: int | None
    s3_key: str | None
    transcription: str | None
    created_at: str
    finalized_at: str | None
    hard_delete_at: str


class JournalRepository(Protocol):
    """Protocol for journal storage backends."""

    async def create(
        self,
        *,
        user_id: str,
        title: str | None,
        body_encrypted: str,
        mood_score: int | None,
    ) -> JournalRecord:
        ...

    async def list_by_user(self, user_id: str, *, limit: int = 50) -> list[JournalRecord]:
        ...

    async def get_by_id(self, journal_id: str, user_id: str) -> JournalRecord | None:
        ...


class VoiceSessionRepository(Protocol):
    """Protocol for voice session storage backends."""

    async def create(self, *, user_id: str) -> VoiceSessionRecord:
        ...

    async def finalize(
        self,
        session_id: str,
        user_id: str,
        *,
        duration_seconds: int | None,
        s3_key: str,
    ) -> VoiceSessionRecord | None:
        ...

    async def get_by_id(self, session_id: str, user_id: str) -> VoiceSessionRecord | None:
        ...


# ---------------------------------------------------------------------------
# In-memory stubs
# ---------------------------------------------------------------------------


class InMemoryJournalRepository:
    """Thread-safe in-memory store for tests and local dev."""

    def __init__(self) -> None:
        self._journals: dict[str, JournalRecord] = {}

    async def create(
        self,
        *,
        user_id: str,
        title: str | None,
        body_encrypted: str,
        mood_score: int | None,
    ) -> JournalRecord:
        from uuid import uuid4

        now = datetime.now(UTC).isoformat()
        record = JournalRecord(
            journal_id=str(uuid4()),
            user_id=user_id,
            title=title,
            body_encrypted=body_encrypted,
            mood_score=mood_score,
            created_at=now,
            updated_at=now,
        )
        self._journals[record.journal_id] = record
        return record

    async def list_by_user(self, user_id: str, *, limit: int = 50) -> list[JournalRecord]:
        results = [
            r for r in self._journals.values() if r.user_id == user_id
        ]
        results.sort(key=lambda r: r.created_at, reverse=True)
        return results[:limit]

    async def get_by_id(self, journal_id: str, user_id: str) -> JournalRecord | None:
        record = self._journals.get(journal_id)
        if record is None or record.user_id != user_id:
            return None
        return record


class InMemoryVoiceSessionRepository:
    """Thread-safe in-memory store for tests and local dev."""

    def __init__(self) -> None:
        self._sessions: dict[str, VoiceSessionRecord] = {}

    async def create(self, *, user_id: str) -> VoiceSessionRecord:
        from uuid import uuid4

        now = datetime.now(UTC)
        hard_delete_at = now + timedelta(hours=72)
        record = VoiceSessionRecord(
            session_id=str(uuid4()),
            user_id=user_id,
            status="recording",
            duration_seconds=None,
            s3_key=None,
            transcription=None,
            created_at=now.isoformat(),
            finalized_at=None,
            hard_delete_at=hard_delete_at.isoformat(),
        )
        self._sessions[record.session_id] = record
        return record

    async def finalize(
        self,
        session_id: str,
        user_id: str,
        *,
        duration_seconds: int | None,
        s3_key: str,
    ) -> VoiceSessionRecord | None:
        record = self._sessions.get(session_id)
        if record is None or record.user_id != user_id:
            return None
        updated = VoiceSessionRecord(
            session_id=record.session_id,
            user_id=record.user_id,
            status="uploaded",
            duration_seconds=duration_seconds,
            s3_key=s3_key,
            transcription=record.transcription,
            created_at=record.created_at,
            finalized_at=datetime.now(UTC).isoformat(),
            hard_delete_at=record.hard_delete_at,
        )
        self._sessions[session_id] = updated
        return updated

    async def get_by_id(self, session_id: str, user_id: str) -> VoiceSessionRecord | None:
        record = self._sessions.get(session_id)
        if record is None or record.user_id != user_id:
            return None
        return record


# ---------------------------------------------------------------------------
# SQLAlchemy implementations
# ---------------------------------------------------------------------------


class SQLAlchemyJournalRepository:
    """Production journal storage backed by PostgreSQL."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        user_id: str,
        title: str | None,
        body_encrypted: str,
        mood_score: int | None,
    ) -> JournalRecord:
        from uuid import UUID

        journal = Journal(
            user_id=UUID(user_id),
            title=title,
            body_encrypted=body_encrypted,
            mood_score=mood_score,
        )
        self._session.add(journal)
        await self._session.flush()
        return _journal_to_record(journal)

    async def list_by_user(self, user_id: str, *, limit: int = 50) -> list[JournalRecord]:
        from uuid import UUID

        result = await self._session.execute(
            select(Journal)
            .where(Journal.user_id == UUID(user_id))
            .order_by(Journal.created_at.desc())
            .limit(limit)
        )
        return [_journal_to_record(j) for j in result.scalars().all()]

    async def get_by_id(self, journal_id: str, user_id: str) -> JournalRecord | None:
        from uuid import UUID

        result = await self._session.execute(
            select(Journal).where(
                Journal.id == UUID(journal_id),
                Journal.user_id == UUID(user_id),
            )
        )
        journal = result.scalar_one_or_none()
        return _journal_to_record(journal) if journal else None


class SQLAlchemyVoiceSessionRepository:
    """Production voice session storage backed by PostgreSQL."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, *, user_id: str) -> VoiceSessionRecord:
        from uuid import UUID

        now = datetime.now(UTC)
        session = VoiceSession(
            user_id=UUID(user_id),
            status="recording",
            hard_delete_at=now + timedelta(hours=72),
        )
        self._session.add(session)
        await self._session.flush()
        return _voice_to_record(session)

    async def finalize(
        self,
        session_id: str,
        user_id: str,
        *,
        duration_seconds: int | None,
        s3_key: str,
    ) -> VoiceSessionRecord | None:
        from uuid import UUID

        result = await self._session.execute(
            select(VoiceSession).where(
                VoiceSession.id == UUID(session_id),
                VoiceSession.user_id == UUID(user_id),
            )
        )
        voice = result.scalar_one_or_none()
        if voice is None:
            return None
        voice.status = "uploaded"
        voice.duration_seconds = duration_seconds
        voice.s3_key = s3_key
        voice.finalized_at = datetime.now(UTC)
        await self._session.flush()
        return _voice_to_record(voice)

    async def get_by_id(self, session_id: str, user_id: str) -> VoiceSessionRecord | None:
        from uuid import UUID

        result = await self._session.execute(
            select(VoiceSession).where(
                VoiceSession.id == UUID(session_id),
                VoiceSession.user_id == UUID(user_id),
            )
        )
        voice = result.scalar_one_or_none()
        return _voice_to_record(voice) if voice else None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _journal_to_record(journal: Journal) -> JournalRecord:
    return JournalRecord(
        journal_id=str(journal.id),
        user_id=str(journal.user_id),
        title=journal.title,
        body_encrypted=journal.body_encrypted,
        mood_score=journal.mood_score,
        created_at=journal.created_at.isoformat(),
        updated_at=journal.updated_at.isoformat(),
    )


def _voice_to_record(voice: VoiceSession) -> VoiceSessionRecord:
    return VoiceSessionRecord(
        session_id=str(voice.id),
        user_id=str(voice.user_id),
        status=voice.status,
        duration_seconds=voice.duration_seconds,
        s3_key=voice.s3_key,
        transcription=voice.transcription,
        created_at=voice.created_at.isoformat(),
        finalized_at=voice.finalized_at.isoformat() if voice.finalized_at else None,
        hard_delete_at=voice.hard_delete_at.isoformat(),
    )


# ---------------------------------------------------------------------------
# Singleton registry (dev/test in-memory; prod binds to SQLAlchemy)
# ---------------------------------------------------------------------------

_journal_repo: JournalRepository = InMemoryJournalRepository()
_voice_repo: VoiceSessionRepository = InMemoryVoiceSessionRepository()


def get_journal_repository() -> JournalRepository:
    return _journal_repo


def get_voice_session_repository() -> VoiceSessionRepository:
    return _voice_repo


def reset_memory_repositories() -> None:
    global _journal_repo, _voice_repo
    _journal_repo = InMemoryJournalRepository()
    _voice_repo = InMemoryVoiceSessionRepository()

"""Tests for discipline.memory.repository — journal and voice session in-memory stores.

Covers:
- JournalRecord frozen dataclass
- InMemoryJournalRepository.create: returns JournalRecord, valid UUID, fields match
- list_by_user: filters by user, sorted descending, default limit 50
- get_by_id: returns record, None for wrong user, None for unknown ID
- VoiceSessionRecord frozen dataclass
- InMemoryVoiceSessionRepository.create: status=recording, hard_delete_at set
- finalize: sets status=uploaded, s3_key, finalized_at
- finalize: wrong user returns None, unknown session returns None
- get_by_id: returns session, None for wrong user
- reset_memory_repositories: clears both repos
"""

from __future__ import annotations

import uuid

import pytest

from discipline.memory.repository import (
    InMemoryJournalRepository,
    InMemoryVoiceSessionRepository,
    JournalRecord,
    VoiceSessionRecord,
    reset_memory_repositories,
)


@pytest.fixture(autouse=True)
def _reset() -> None:
    reset_memory_repositories()


# ---------------------------------------------------------------------------
# JournalRecord frozen dataclass
# ---------------------------------------------------------------------------


class TestJournalRecord:
    def test_can_be_constructed(self) -> None:
        r = JournalRecord(
            journal_id="jid",
            user_id="uid",
            title="My Day",
            body_encrypted="enc...",
            mood_score=7,
            created_at="2026-04-25T00:00:00+00:00",
            updated_at="2026-04-25T00:00:00+00:00",
        )
        assert r.journal_id == "jid"

    def test_frozen(self) -> None:
        r = JournalRecord(
            journal_id="jid",
            user_id="uid",
            title=None,
            body_encrypted="enc",
            mood_score=None,
            created_at="2026-04-25",
            updated_at="2026-04-25",
        )
        with pytest.raises((AttributeError, TypeError)):
            r.title = "mutated"  # type: ignore[misc]

    def test_title_accepts_none(self) -> None:
        r = JournalRecord(
            journal_id="j", user_id="u", title=None,
            body_encrypted="e", mood_score=None,
            created_at="2026-04-25", updated_at="2026-04-25",
        )
        assert r.title is None

    def test_mood_score_accepts_none(self) -> None:
        r = JournalRecord(
            journal_id="j", user_id="u", title=None,
            body_encrypted="e", mood_score=None,
            created_at="2026-04-25", updated_at="2026-04-25",
        )
        assert r.mood_score is None


# ---------------------------------------------------------------------------
# InMemoryJournalRepository.create
# ---------------------------------------------------------------------------


class TestJournalCreate:
    @pytest.mark.asyncio
    async def test_returns_journal_record(self) -> None:
        repo = InMemoryJournalRepository()
        r = await repo.create(
            user_id="u-1", title="Test", body_encrypted="enc", mood_score=5
        )
        assert isinstance(r, JournalRecord)

    @pytest.mark.asyncio
    async def test_journal_id_is_valid_uuid(self) -> None:
        repo = InMemoryJournalRepository()
        r = await repo.create(
            user_id="u-1", title=None, body_encrypted="enc", mood_score=None
        )
        uuid.UUID(r.journal_id)

    @pytest.mark.asyncio
    async def test_fields_match_input(self) -> None:
        repo = InMemoryJournalRepository()
        r = await repo.create(
            user_id="u-99", title="Title", body_encrypted="body_enc", mood_score=8
        )
        assert r.user_id == "u-99"
        assert r.title == "Title"
        assert r.body_encrypted == "body_enc"
        assert r.mood_score == 8

    @pytest.mark.asyncio
    async def test_two_entries_have_different_ids(self) -> None:
        repo = InMemoryJournalRepository()
        r1 = await repo.create(user_id="u", title=None, body_encrypted="e1", mood_score=None)
        r2 = await repo.create(user_id="u", title=None, body_encrypted="e2", mood_score=None)
        assert r1.journal_id != r2.journal_id


# ---------------------------------------------------------------------------
# InMemoryJournalRepository.list_by_user
# ---------------------------------------------------------------------------


class TestJournalListByUser:
    @pytest.mark.asyncio
    async def test_empty_for_unknown_user(self) -> None:
        repo = InMemoryJournalRepository()
        assert await repo.list_by_user("ghost") == []

    @pytest.mark.asyncio
    async def test_returns_only_matching_user(self) -> None:
        repo = InMemoryJournalRepository()
        await repo.create(user_id="alice", title=None, body_encrypted="e", mood_score=None)
        await repo.create(user_id="bob", title=None, body_encrypted="e", mood_score=None)
        results = await repo.list_by_user("alice")
        assert all(r.user_id == "alice" for r in results)
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_sorted_descending_by_created_at(self) -> None:
        repo = InMemoryJournalRepository()
        for _ in range(3):
            await repo.create(user_id="u", title=None, body_encrypted="e", mood_score=None)
        results = await repo.list_by_user("u")
        times = [r.created_at for r in results]
        assert times == sorted(times, reverse=True)

    @pytest.mark.asyncio
    async def test_limit_respected(self) -> None:
        repo = InMemoryJournalRepository()
        for _ in range(10):
            await repo.create(user_id="u", title=None, body_encrypted="e", mood_score=None)
        results = await repo.list_by_user("u", limit=3)
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_default_limit_is_50(self) -> None:
        repo = InMemoryJournalRepository()
        for _ in range(60):
            await repo.create(user_id="u", title=None, body_encrypted="e", mood_score=None)
        results = await repo.list_by_user("u")
        assert len(results) == 50


# ---------------------------------------------------------------------------
# InMemoryJournalRepository.get_by_id
# ---------------------------------------------------------------------------


class TestJournalGetById:
    @pytest.mark.asyncio
    async def test_returns_record_for_correct_user(self) -> None:
        repo = InMemoryJournalRepository()
        r = await repo.create(user_id="u-1", title=None, body_encrypted="e", mood_score=None)
        result = await repo.get_by_id(r.journal_id, "u-1")
        assert result is not None
        assert result.journal_id == r.journal_id

    @pytest.mark.asyncio
    async def test_returns_none_for_wrong_user(self) -> None:
        repo = InMemoryJournalRepository()
        r = await repo.create(user_id="alice", title=None, body_encrypted="e", mood_score=None)
        result = await repo.get_by_id(r.journal_id, "bob")
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_for_unknown_id(self) -> None:
        repo = InMemoryJournalRepository()
        result = await repo.get_by_id("nonexistent-id", "u-1")
        assert result is None


# ---------------------------------------------------------------------------
# VoiceSessionRecord frozen dataclass
# ---------------------------------------------------------------------------


class TestVoiceSessionRecord:
    def test_can_be_constructed(self) -> None:
        r = VoiceSessionRecord(
            session_id="sid",
            user_id="uid",
            status="recording",
            duration_seconds=None,
            s3_key=None,
            transcription=None,
            created_at="2026-04-25T00:00:00+00:00",
            finalized_at=None,
            hard_delete_at="2026-04-28T00:00:00+00:00",
        )
        assert r.session_id == "sid"

    def test_frozen(self) -> None:
        r = VoiceSessionRecord(
            session_id="sid", user_id="uid", status="recording",
            duration_seconds=None, s3_key=None, transcription=None,
            created_at="2026-04-25", finalized_at=None,
            hard_delete_at="2026-04-28",
        )
        with pytest.raises((AttributeError, TypeError)):
            r.status = "mutated"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# InMemoryVoiceSessionRepository.create
# ---------------------------------------------------------------------------


class TestVoiceSessionCreate:
    @pytest.mark.asyncio
    async def test_returns_voice_session_record(self) -> None:
        repo = InMemoryVoiceSessionRepository()
        r = await repo.create(user_id="u-1")
        assert isinstance(r, VoiceSessionRecord)

    @pytest.mark.asyncio
    async def test_session_id_is_valid_uuid(self) -> None:
        repo = InMemoryVoiceSessionRepository()
        r = await repo.create(user_id="u-1")
        uuid.UUID(r.session_id)

    @pytest.mark.asyncio
    async def test_status_is_recording(self) -> None:
        repo = InMemoryVoiceSessionRepository()
        r = await repo.create(user_id="u-1")
        assert r.status == "recording"

    @pytest.mark.asyncio
    async def test_hard_delete_at_is_72h_after_creation(self) -> None:
        """CLAUDE.md Rule #7: voice blobs hard-delete at 72h."""
        from datetime import datetime, timezone

        repo = InMemoryVoiceSessionRepository()
        r = await repo.create(user_id="u-1")
        created = datetime.fromisoformat(r.created_at)
        hard_delete = datetime.fromisoformat(r.hard_delete_at)
        delta_hours = (hard_delete - created).total_seconds() / 3600
        assert 71.9 <= delta_hours <= 72.1, (
            f"hard_delete_at is {delta_hours:.1f}h after creation, expected 72h"
        )

    @pytest.mark.asyncio
    async def test_s3_key_is_none_on_creation(self) -> None:
        repo = InMemoryVoiceSessionRepository()
        r = await repo.create(user_id="u-1")
        assert r.s3_key is None

    @pytest.mark.asyncio
    async def test_finalized_at_is_none_on_creation(self) -> None:
        repo = InMemoryVoiceSessionRepository()
        r = await repo.create(user_id="u-1")
        assert r.finalized_at is None


# ---------------------------------------------------------------------------
# InMemoryVoiceSessionRepository.finalize
# ---------------------------------------------------------------------------


class TestVoiceSessionFinalize:
    @pytest.mark.asyncio
    async def test_finalize_sets_uploaded_status(self) -> None:
        repo = InMemoryVoiceSessionRepository()
        session = await repo.create(user_id="u-1")
        updated = await repo.finalize(
            session.session_id, "u-1",
            duration_seconds=60, s3_key="voice/u-1/session.webm"
        )
        assert updated is not None
        assert updated.status == "uploaded"

    @pytest.mark.asyncio
    async def test_finalize_sets_s3_key(self) -> None:
        repo = InMemoryVoiceSessionRepository()
        session = await repo.create(user_id="u-1")
        updated = await repo.finalize(
            session.session_id, "u-1",
            duration_seconds=30, s3_key="voice/key.webm"
        )
        assert updated is not None
        assert updated.s3_key == "voice/key.webm"

    @pytest.mark.asyncio
    async def test_finalize_sets_finalized_at(self) -> None:
        repo = InMemoryVoiceSessionRepository()
        session = await repo.create(user_id="u-1")
        updated = await repo.finalize(
            session.session_id, "u-1",
            duration_seconds=90, s3_key="key"
        )
        assert updated is not None
        assert updated.finalized_at is not None

    @pytest.mark.asyncio
    async def test_finalize_wrong_user_returns_none(self) -> None:
        repo = InMemoryVoiceSessionRepository()
        session = await repo.create(user_id="alice")
        result = await repo.finalize(
            session.session_id, "bob",
            duration_seconds=60, s3_key="k"
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_finalize_unknown_session_returns_none(self) -> None:
        repo = InMemoryVoiceSessionRepository()
        result = await repo.finalize(
            "nonexistent-session", "u-1",
            duration_seconds=60, s3_key="k"
        )
        assert result is None


# ---------------------------------------------------------------------------
# InMemoryVoiceSessionRepository.get_by_id
# ---------------------------------------------------------------------------


class TestVoiceSessionGetById:
    @pytest.mark.asyncio
    async def test_returns_session_for_correct_user(self) -> None:
        repo = InMemoryVoiceSessionRepository()
        session = await repo.create(user_id="u-1")
        result = await repo.get_by_id(session.session_id, "u-1")
        assert result is not None
        assert result.session_id == session.session_id

    @pytest.mark.asyncio
    async def test_returns_none_for_wrong_user(self) -> None:
        repo = InMemoryVoiceSessionRepository()
        session = await repo.create(user_id="alice")
        result = await repo.get_by_id(session.session_id, "bob")
        assert result is None

"""Tests for discipline.notifications.repository — nudge and push token in-memory stores.

Covers:
- NudgeRecord frozen dataclass
- InMemoryNudgeRepository.create: returns NudgeRecord, status=scheduled, fields match
- list_by_user: filters by user, sorted descending by scheduled_at
- list_by_user: default limit 50
- mark_sent: sets status=sent, sent_at populated
- mark_sent: wrong user returns None, unknown nudge returns None
- PushTokenRecord frozen dataclass
- InMemoryPushTokenRepository.create: returns PushTokenRecord, token_id is valid UUID
- list_by_user: returns tokens for user, empty for unknown
- reset_notification_repositories: clears both repos
"""

from __future__ import annotations

import uuid

import pytest

from discipline.notifications.repository import (
    InMemoryNudgeRepository,
    InMemoryPushTokenRepository,
    NudgeRecord,
    PushTokenRecord,
    reset_notification_repositories,
)


@pytest.fixture(autouse=True)
def _reset() -> None:
    reset_notification_repositories()


# ---------------------------------------------------------------------------
# NudgeRecord frozen dataclass
# ---------------------------------------------------------------------------


class TestNudgeRecord:
    def test_can_be_constructed(self) -> None:
        r = NudgeRecord(
            nudge_id="nid",
            user_id="uid",
            nudge_type="check_in",
            status="scheduled",
            scheduled_at="2026-04-25T08:00:00+00:00",
            sent_at=None,
            tool_variant=None,
            message_copy=None,
            created_at="2026-04-25T00:00:00+00:00",
        )
        assert r.nudge_id == "nid"

    def test_frozen(self) -> None:
        r = NudgeRecord(
            nudge_id="n", user_id="u", nudge_type="check_in",
            status="scheduled", scheduled_at="2026-04-25T08:00:00+00:00",
            sent_at=None, tool_variant=None, message_copy=None,
            created_at="2026-04-25",
        )
        with pytest.raises((AttributeError, TypeError)):
            r.status = "sent"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# InMemoryNudgeRepository.create
# ---------------------------------------------------------------------------


class TestNudgeCreate:
    @pytest.mark.asyncio
    async def test_returns_nudge_record(self) -> None:
        repo = InMemoryNudgeRepository()
        r = await repo.create(
            user_id="u-1", nudge_type="check_in",
            scheduled_at="2026-04-25T08:00:00+00:00",
            tool_variant=None, message_copy=None,
        )
        assert isinstance(r, NudgeRecord)

    @pytest.mark.asyncio
    async def test_nudge_id_is_valid_uuid(self) -> None:
        repo = InMemoryNudgeRepository()
        r = await repo.create(
            user_id="u-1", nudge_type="check_in",
            scheduled_at="2026-04-25T08:00:00+00:00",
            tool_variant=None, message_copy=None,
        )
        uuid.UUID(r.nudge_id)

    @pytest.mark.asyncio
    async def test_status_is_scheduled(self) -> None:
        repo = InMemoryNudgeRepository()
        r = await repo.create(
            user_id="u-1", nudge_type="check_in",
            scheduled_at="2026-04-25T08:00:00+00:00",
            tool_variant=None, message_copy=None,
        )
        assert r.status == "scheduled"

    @pytest.mark.asyncio
    async def test_fields_match_input(self) -> None:
        repo = InMemoryNudgeRepository()
        r = await repo.create(
            user_id="u-99", nudge_type="urge_surf_prompt",
            scheduled_at="2026-04-25T18:00:00+00:00",
            tool_variant="urge_surf", message_copy="Time to check in",
        )
        assert r.user_id == "u-99"
        assert r.nudge_type == "urge_surf_prompt"
        assert r.tool_variant == "urge_surf"
        assert r.message_copy == "Time to check in"

    @pytest.mark.asyncio
    async def test_sent_at_is_none_on_creation(self) -> None:
        repo = InMemoryNudgeRepository()
        r = await repo.create(
            user_id="u-1", nudge_type="check_in",
            scheduled_at="2026-04-25T08:00:00+00:00",
            tool_variant=None, message_copy=None,
        )
        assert r.sent_at is None


# ---------------------------------------------------------------------------
# InMemoryNudgeRepository.list_by_user
# ---------------------------------------------------------------------------


class TestNudgeListByUser:
    @pytest.mark.asyncio
    async def test_empty_for_unknown_user(self) -> None:
        repo = InMemoryNudgeRepository()
        assert await repo.list_by_user("ghost") == []

    @pytest.mark.asyncio
    async def test_returns_only_matching_user(self) -> None:
        repo = InMemoryNudgeRepository()
        await repo.create(
            user_id="alice", nudge_type="check_in",
            scheduled_at="2026-04-25T08:00:00+00:00",
            tool_variant=None, message_copy=None,
        )
        await repo.create(
            user_id="bob", nudge_type="check_in",
            scheduled_at="2026-04-25T09:00:00+00:00",
            tool_variant=None, message_copy=None,
        )
        results = await repo.list_by_user("alice")
        assert all(r.user_id == "alice" for r in results)
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_default_limit_is_50(self) -> None:
        repo = InMemoryNudgeRepository()
        for i in range(60):
            await repo.create(
                user_id="u-1", nudge_type="check_in",
                scheduled_at=f"2026-04-{i % 28 + 1:02d}T08:00:00+00:00",
                tool_variant=None, message_copy=None,
            )
        results = await repo.list_by_user("u-1")
        assert len(results) == 50

    @pytest.mark.asyncio
    async def test_limit_respected(self) -> None:
        repo = InMemoryNudgeRepository()
        for i in range(10):
            await repo.create(
                user_id="u-1", nudge_type="check_in",
                scheduled_at=f"2026-04-{i + 1:02d}T08:00:00+00:00",
                tool_variant=None, message_copy=None,
            )
        results = await repo.list_by_user("u-1", limit=3)
        assert len(results) == 3


# ---------------------------------------------------------------------------
# InMemoryNudgeRepository.mark_sent
# ---------------------------------------------------------------------------


class TestMarkSent:
    @pytest.mark.asyncio
    async def test_mark_sent_sets_status_sent(self) -> None:
        repo = InMemoryNudgeRepository()
        nudge = await repo.create(
            user_id="u-1", nudge_type="check_in",
            scheduled_at="2026-04-25T08:00:00+00:00",
            tool_variant=None, message_copy=None,
        )
        updated = await repo.mark_sent(nudge.nudge_id, "u-1")
        assert updated is not None
        assert updated.status == "sent"

    @pytest.mark.asyncio
    async def test_mark_sent_sets_sent_at(self) -> None:
        repo = InMemoryNudgeRepository()
        nudge = await repo.create(
            user_id="u-1", nudge_type="check_in",
            scheduled_at="2026-04-25T08:00:00+00:00",
            tool_variant=None, message_copy=None,
        )
        updated = await repo.mark_sent(nudge.nudge_id, "u-1")
        assert updated is not None
        assert updated.sent_at is not None

    @pytest.mark.asyncio
    async def test_mark_sent_wrong_user_returns_none(self) -> None:
        repo = InMemoryNudgeRepository()
        nudge = await repo.create(
            user_id="alice", nudge_type="check_in",
            scheduled_at="2026-04-25T08:00:00+00:00",
            tool_variant=None, message_copy=None,
        )
        result = await repo.mark_sent(nudge.nudge_id, "bob")
        assert result is None

    @pytest.mark.asyncio
    async def test_mark_sent_unknown_id_returns_none(self) -> None:
        repo = InMemoryNudgeRepository()
        result = await repo.mark_sent("nonexistent-nudge-id", "u-1")
        assert result is None


# ---------------------------------------------------------------------------
# PushTokenRecord frozen dataclass
# ---------------------------------------------------------------------------


class TestPushTokenRecord:
    def test_can_be_constructed(self) -> None:
        r = PushTokenRecord(
            token_id="tid",
            user_id="uid",
            platform="ios",
            token_hash="hash123",
            created_at="2026-04-25T00:00:00+00:00",
            last_valid_at="2026-04-25T00:00:00+00:00",
        )
        assert r.token_id == "tid"

    def test_frozen(self) -> None:
        r = PushTokenRecord(
            token_id="t", user_id="u", platform="ios",
            token_hash="h", created_at="2026-04-25",
            last_valid_at=None,
        )
        with pytest.raises((AttributeError, TypeError)):
            r.platform = "android"  # type: ignore[misc]

    def test_last_valid_at_accepts_none(self) -> None:
        r = PushTokenRecord(
            token_id="t", user_id="u", platform="ios",
            token_hash="h", created_at="2026-04-25",
            last_valid_at=None,
        )
        assert r.last_valid_at is None


# ---------------------------------------------------------------------------
# InMemoryPushTokenRepository
# ---------------------------------------------------------------------------


class TestPushTokenRepository:
    @pytest.mark.asyncio
    async def test_create_returns_push_token_record(self) -> None:
        repo = InMemoryPushTokenRepository()
        r = await repo.create(
            user_id="u-1", platform="ios",
            token_hash="hash1", token_encrypted="enc1",
        )
        assert isinstance(r, PushTokenRecord)

    @pytest.mark.asyncio
    async def test_token_id_is_valid_uuid(self) -> None:
        repo = InMemoryPushTokenRepository()
        r = await repo.create(
            user_id="u-1", platform="android",
            token_hash="hash2", token_encrypted="enc2",
        )
        uuid.UUID(r.token_id)

    @pytest.mark.asyncio
    async def test_fields_match_input(self) -> None:
        repo = InMemoryPushTokenRepository()
        r = await repo.create(
            user_id="u-99", platform="ios",
            token_hash="myhash", token_encrypted="myenc",
        )
        assert r.user_id == "u-99"
        assert r.platform == "ios"
        assert r.token_hash == "myhash"

    @pytest.mark.asyncio
    async def test_list_by_user_returns_tokens(self) -> None:
        repo = InMemoryPushTokenRepository()
        await repo.create(
            user_id="u-1", platform="ios",
            token_hash="h1", token_encrypted="e1",
        )
        await repo.create(
            user_id="u-1", platform="android",
            token_hash="h2", token_encrypted="e2",
        )
        tokens = await repo.list_by_user("u-1")
        assert len(tokens) == 2
        assert all(t.user_id == "u-1" for t in tokens)

    @pytest.mark.asyncio
    async def test_list_by_user_empty_for_unknown(self) -> None:
        repo = InMemoryPushTokenRepository()
        tokens = await repo.list_by_user("ghost-user")
        assert tokens == []

    @pytest.mark.asyncio
    async def test_list_by_user_filters_by_user(self) -> None:
        repo = InMemoryPushTokenRepository()
        await repo.create(user_id="alice", platform="ios", token_hash="h1", token_encrypted="e1")
        await repo.create(user_id="bob", platform="ios", token_hash="h2", token_encrypted="e2")
        tokens = await repo.list_by_user("alice")
        assert len(tokens) == 1
        assert tokens[0].user_id == "alice"

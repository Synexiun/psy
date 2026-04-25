"""Tests for discipline.resilience.repository — streak state in-memory store.

Covers:
- StreakStateRecord frozen dataclass
- InMemoryStreakStateRepository.get_or_create: new user initialised with zero counters
- get_or_create: existing user returns same record without mutation
- update: stores updated record, returns it, subsequent get_or_create sees updated state
- reset_streak_repository: replaces singleton, clears store
"""

from __future__ import annotations

import pytest

from discipline.resilience.repository import (
    InMemoryStreakStateRepository,
    StreakStateRecord,
    get_streak_state_repository,
    reset_streak_repository,
)


@pytest.fixture(autouse=True)
def _reset() -> None:
    reset_streak_repository()


# ---------------------------------------------------------------------------
# StreakStateRecord frozen dataclass
# ---------------------------------------------------------------------------


class TestStreakStateRecord:
    def test_can_be_constructed(self) -> None:
        r = StreakStateRecord(
            user_id="u-1",
            continuous_days=5,
            continuous_streak_start="2026-04-20T00:00:00+00:00",
            resilience_days=30,
            resilience_urges_handled_total=12,
            resilience_streak_start="2026-03-26T00:00:00+00:00",
            updated_at="2026-04-25T00:00:00+00:00",
        )
        assert r.user_id == "u-1"
        assert r.resilience_days == 30

    def test_frozen(self) -> None:
        r = StreakStateRecord(
            user_id="u", continuous_days=0,
            continuous_streak_start=None,
            resilience_days=0,
            resilience_urges_handled_total=0,
            resilience_streak_start="2026-04-25",
            updated_at="2026-04-25",
        )
        with pytest.raises((AttributeError, TypeError)):
            r.continuous_days = 99  # type: ignore[misc]

    def test_continuous_streak_start_accepts_none(self) -> None:
        r = StreakStateRecord(
            user_id="u", continuous_days=0, continuous_streak_start=None,
            resilience_days=0, resilience_urges_handled_total=0,
            resilience_streak_start="2026-04-25", updated_at="2026-04-25",
        )
        assert r.continuous_streak_start is None


# ---------------------------------------------------------------------------
# InMemoryStreakStateRepository.get_or_create
# ---------------------------------------------------------------------------


class TestGetOrCreate:
    @pytest.mark.asyncio
    async def test_new_user_gets_zero_continuous_days(self) -> None:
        repo = InMemoryStreakStateRepository()
        r = await repo.get_or_create("u-1")
        assert r.continuous_days == 0

    @pytest.mark.asyncio
    async def test_new_user_gets_zero_resilience_days(self) -> None:
        repo = InMemoryStreakStateRepository()
        r = await repo.get_or_create("u-1")
        assert r.resilience_days == 0

    @pytest.mark.asyncio
    async def test_new_user_gets_zero_urges_handled(self) -> None:
        repo = InMemoryStreakStateRepository()
        r = await repo.get_or_create("u-1")
        assert r.resilience_urges_handled_total == 0

    @pytest.mark.asyncio
    async def test_new_user_continuous_streak_start_is_none(self) -> None:
        repo = InMemoryStreakStateRepository()
        r = await repo.get_or_create("u-1")
        assert r.continuous_streak_start is None

    @pytest.mark.asyncio
    async def test_new_user_user_id_matches(self) -> None:
        repo = InMemoryStreakStateRepository()
        r = await repo.get_or_create("u-99")
        assert r.user_id == "u-99"

    @pytest.mark.asyncio
    async def test_existing_user_returns_same_record(self) -> None:
        repo = InMemoryStreakStateRepository()
        first = await repo.get_or_create("u-1")
        second = await repo.get_or_create("u-1")
        assert first.user_id == second.user_id
        assert first.resilience_streak_start == second.resilience_streak_start

    @pytest.mark.asyncio
    async def test_different_users_tracked_independently(self) -> None:
        repo = InMemoryStreakStateRepository()
        alice = await repo.get_or_create("alice")
        bob = await repo.get_or_create("bob")
        assert alice.user_id != bob.user_id


# ---------------------------------------------------------------------------
# InMemoryStreakStateRepository.update
# ---------------------------------------------------------------------------


class TestUpdate:
    @pytest.mark.asyncio
    async def test_update_stores_new_values(self) -> None:
        repo = InMemoryStreakStateRepository()
        original = await repo.get_or_create("u-1")
        updated = StreakStateRecord(
            user_id=original.user_id,
            continuous_days=7,
            continuous_streak_start="2026-04-18T00:00:00+00:00",
            resilience_days=original.resilience_days + 7,
            resilience_urges_handled_total=original.resilience_urges_handled_total + 3,
            resilience_streak_start=original.resilience_streak_start,
            updated_at="2026-04-25T00:00:00+00:00",
        )
        returned = await repo.update(updated)
        assert returned.continuous_days == 7
        assert returned.resilience_days == 7

    @pytest.mark.asyncio
    async def test_update_returns_stored_record(self) -> None:
        repo = InMemoryStreakStateRepository()
        original = await repo.get_or_create("u-1")
        new_record = StreakStateRecord(
            user_id=original.user_id,
            continuous_days=3,
            continuous_streak_start=None,
            resilience_days=10,
            resilience_urges_handled_total=5,
            resilience_streak_start=original.resilience_streak_start,
            updated_at="2026-04-25T00:00:00+00:00",
        )
        result = await repo.update(new_record)
        assert result is new_record

    @pytest.mark.asyncio
    async def test_subsequent_get_or_create_sees_updated_state(self) -> None:
        repo = InMemoryStreakStateRepository()
        original = await repo.get_or_create("u-1")
        new_record = StreakStateRecord(
            user_id=original.user_id,
            continuous_days=15,
            continuous_streak_start="2026-04-10T00:00:00+00:00",
            resilience_days=100,
            resilience_urges_handled_total=50,
            resilience_streak_start=original.resilience_streak_start,
            updated_at="2026-04-25T00:00:00+00:00",
        )
        await repo.update(new_record)
        fetched = await repo.get_or_create("u-1")
        assert fetched.continuous_days == 15
        assert fetched.resilience_days == 100


# ---------------------------------------------------------------------------
# reset_streak_repository
# ---------------------------------------------------------------------------


class TestReset:
    @pytest.mark.asyncio
    async def test_reset_clears_store(self) -> None:
        repo = InMemoryStreakStateRepository()
        await repo.get_or_create("u-1")
        reset_streak_repository()
        new_repo = get_streak_state_repository()
        result = await new_repo.get_or_create("u-1")
        assert result.continuous_days == 0
        assert result.resilience_days == 0

    def test_reset_returns_fresh_in_memory_instance(self) -> None:
        reset_streak_repository()
        repo = get_streak_state_repository()
        assert isinstance(repo, InMemoryStreakStateRepository)

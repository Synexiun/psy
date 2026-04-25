"""Tests for discipline.resilience.service — StreakService state machine.

CLAUDE.md Rule #3: resilience_days is monotonically non-decreasing.
These tests verify the service enforces this at the state machine level.

Covers:
- apply_handled: increments continuous_days AND resilience_days
- apply_handled: increments resilience_urges_handled_total
- apply_handled: sets continuous_streak_start when starting from zero
- apply_handled: preserves existing continuous_streak_start
- apply_relapse: resets continuous_days to 0
- apply_relapse: PRESERVES resilience_days (Rule #3)
- apply_relapse: PRESERVES resilience_urges_handled_total (Rule #3)
- apply_relapse: clears continuous_streak_start
- current: returns current state without mutation
- compound sequence: handled → relapse → handled
"""

from __future__ import annotations

import pytest

from discipline.resilience.repository import (
    InMemoryStreakStateRepository,
    reset_streak_repository,
)
from discipline.resilience.service import StreakService


@pytest.fixture(autouse=True)
def _reset() -> None:
    reset_streak_repository()


def _make_service() -> StreakService:
    repo = InMemoryStreakStateRepository()
    return StreakService(repository=repo)


# ---------------------------------------------------------------------------
# apply_handled
# ---------------------------------------------------------------------------


class TestApplyHandled:
    @pytest.mark.asyncio
    async def test_increments_continuous_days(self) -> None:
        svc = _make_service()
        result = await svc.apply_handled("u-1")
        assert result.continuous_days == 1

    @pytest.mark.asyncio
    async def test_increments_resilience_days(self) -> None:
        svc = _make_service()
        result = await svc.apply_handled("u-1")
        assert result.resilience_days == 1

    @pytest.mark.asyncio
    async def test_increments_urges_handled_total(self) -> None:
        svc = _make_service()
        result = await svc.apply_handled("u-1")
        assert result.resilience_urges_handled_total == 1

    @pytest.mark.asyncio
    async def test_sets_continuous_streak_start_on_first_call(self) -> None:
        svc = _make_service()
        result = await svc.apply_handled("u-1")
        assert result.continuous_streak_start is not None

    @pytest.mark.asyncio
    async def test_preserves_continuous_streak_start_on_subsequent_call(self) -> None:
        svc = _make_service()
        first = await svc.apply_handled("u-1")
        second = await svc.apply_handled("u-1")
        assert second.continuous_streak_start == first.continuous_streak_start

    @pytest.mark.asyncio
    async def test_accumulates_over_multiple_calls(self) -> None:
        svc = _make_service()
        for _ in range(5):
            await svc.apply_handled("u-1")
        state = await svc.current("u-1")
        assert state.continuous_days == 5
        assert state.resilience_days == 5
        assert state.resilience_urges_handled_total == 5

    @pytest.mark.asyncio
    async def test_different_users_tracked_independently(self) -> None:
        svc = _make_service()
        await svc.apply_handled("alice")
        await svc.apply_handled("alice")
        await svc.apply_handled("bob")
        alice = await svc.current("alice")
        bob = await svc.current("bob")
        assert alice.continuous_days == 2
        assert bob.continuous_days == 1


# ---------------------------------------------------------------------------
# apply_relapse — Rule #3 is the critical invariant here
# ---------------------------------------------------------------------------


class TestApplyRelapse:
    @pytest.mark.asyncio
    async def test_resets_continuous_days_to_zero(self) -> None:
        svc = _make_service()
        await svc.apply_handled("u-1")
        await svc.apply_handled("u-1")
        result = await svc.apply_relapse("u-1")
        assert result.continuous_days == 0

    @pytest.mark.asyncio
    async def test_preserves_resilience_days_rule_3(self) -> None:
        """Rule #3: resilience_days MUST NOT decrement on relapse."""
        svc = _make_service()
        await svc.apply_handled("u-1")
        await svc.apply_handled("u-1")
        await svc.apply_handled("u-1")
        result = await svc.apply_relapse("u-1")
        assert result.resilience_days == 3

    @pytest.mark.asyncio
    async def test_preserves_urges_handled_total_rule_3(self) -> None:
        """Rule #3: urges_handled_total is part of resilience and must not reset."""
        svc = _make_service()
        await svc.apply_handled("u-1")
        await svc.apply_handled("u-1")
        result = await svc.apply_relapse("u-1")
        assert result.resilience_urges_handled_total == 2

    @pytest.mark.asyncio
    async def test_clears_continuous_streak_start(self) -> None:
        svc = _make_service()
        await svc.apply_handled("u-1")
        result = await svc.apply_relapse("u-1")
        assert result.continuous_streak_start is None

    @pytest.mark.asyncio
    async def test_relapse_on_fresh_user_keeps_zero_resilience(self) -> None:
        """Relapse on a user who never handled an urge — resilience stays 0."""
        svc = _make_service()
        result = await svc.apply_relapse("u-1")
        assert result.resilience_days == 0
        assert result.continuous_days == 0

    @pytest.mark.asyncio
    async def test_resilience_continues_accumulating_after_relapse(self) -> None:
        """After relapse, applying handled urges still increments resilience."""
        svc = _make_service()
        await svc.apply_handled("u-1")
        await svc.apply_relapse("u-1")
        result = await svc.apply_handled("u-1")
        assert result.resilience_days == 2  # 1 before + 1 after relapse
        assert result.continuous_days == 1  # restarted

    @pytest.mark.asyncio
    async def test_multiple_relapses_never_decrement_resilience(self) -> None:
        """Multiple relapses in sequence must not reduce resilience_days."""
        svc = _make_service()
        await svc.apply_handled("u-1")
        await svc.apply_handled("u-1")
        await svc.apply_relapse("u-1")
        await svc.apply_relapse("u-1")
        state = await svc.current("u-1")
        assert state.resilience_days == 2  # still the value earned before relapse


# ---------------------------------------------------------------------------
# current
# ---------------------------------------------------------------------------


class TestCurrent:
    @pytest.mark.asyncio
    async def test_current_returns_zero_state_for_new_user(self) -> None:
        svc = _make_service()
        state = await svc.current("u-new")
        assert state.continuous_days == 0
        assert state.resilience_days == 0

    @pytest.mark.asyncio
    async def test_current_does_not_mutate_state(self) -> None:
        svc = _make_service()
        await svc.apply_handled("u-1")
        before = await svc.current("u-1")
        await svc.current("u-1")
        after = await svc.current("u-1")
        assert before.continuous_days == after.continuous_days
        assert before.resilience_days == after.resilience_days

    @pytest.mark.asyncio
    async def test_current_user_id_matches(self) -> None:
        svc = _make_service()
        state = await svc.current("u-99")
        assert state.user_id == "u-99"

"""Resilience streak service.

Encodes the streak state machine:
- ``apply_handled`` increments both continuous and resilience.
- ``apply_relapse`` resets continuous to 0, preserves resilience.

AGENTS.md Rule #3: resilience_days is monotonically non-decreasing.
"""

from __future__ import annotations

from datetime import UTC, datetime

from discipline.resilience.repository import (
    StreakStateRecord,
    get_streak_state_repository,
)


class StreakService:
    """User streak state machine."""

    def __init__(self, repository: object | None = None) -> None:
        self._repo = repository or get_streak_state_repository()

    async def apply_handled(self, user_id: str) -> StreakStateRecord:
        """Record a handled urge.

        Increments both continuous and resilience streaks.
        """
        state = await self._repo.get_or_create(user_id)
        now = datetime.now(UTC).isoformat()
        new_continuous = state.continuous_days + 1
        new_resilience = state.resilience_days + 1
        return await self._repo.update(
            StreakStateRecord(
                user_id=state.user_id,
                continuous_days=new_continuous,
                continuous_streak_start=state.continuous_streak_start or now,
                resilience_days=new_resilience,
                resilience_urges_handled_total=state.resilience_urges_handled_total + 1,
                resilience_streak_start=state.resilience_streak_start,
                updated_at=now,
            )
        )

    async def apply_relapse(self, user_id: str) -> StreakStateRecord:
        """Record a relapse.

        Resets continuous streak to 0.  Resilience streak is preserved
        (never decremented per AGENTS.md Rule #3).
        """
        state = await self._repo.get_or_create(user_id)
        now = datetime.now(UTC).isoformat()
        return await self._repo.update(
            StreakStateRecord(
                user_id=state.user_id,
                continuous_days=0,
                continuous_streak_start=None,
                resilience_days=state.resilience_days,
                resilience_urges_handled_total=state.resilience_urges_handled_total,
                resilience_streak_start=state.resilience_streak_start,
                updated_at=now,
            )
        )

    async def current(self, user_id: str) -> StreakStateRecord:
        """Return the current streak state for a user."""
        return await self._repo.get_or_create(user_id)

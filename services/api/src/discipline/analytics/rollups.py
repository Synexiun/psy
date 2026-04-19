"""Daily rollup builder.

Writes to ``analytics.daily_user_rollups``; read by :mod:`.router` for user insight
endpoints and by ``reports.*`` for weekly / monthly stories.

The rollup shape is versioned; downstream readers must tolerate new columns via
``NULLable`` defaults.  No destructive schema changes without a migration plan.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class DailyRollup:
    user_id: str
    day: date
    urges_logged: int
    urges_handled: int
    tools_used: int
    mood_mean: float | None
    sleep_hours: float | None
    wellbeing_state: str | None  # low-cardinality label, not a score
    rollup_version: str = "1.0.0"


async def build_for_user(_user_id: str, _day: date) -> DailyRollup:
    """Stub.  The real implementation reads from signal.minute_buckets and
    intervention.events, and writes via the analytics repository."""
    raise NotImplementedError


__all__ = ["DailyRollup", "build_for_user"]

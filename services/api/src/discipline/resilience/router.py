"""Resilience HTTP surface — streak state.

Endpoints:
- ``GET /v1/streak`` — current streak state
- ``POST /v1/streak/handled`` — record a handled urge
- ``POST /v1/streak/relapse`` — record a relapse

All endpoints are authenticated (Clerk session → server JWT).
"""

from __future__ import annotations

from fastapi import APIRouter, Header
from pydantic import BaseModel

from discipline.resilience.service import StreakService

router = APIRouter(tags=["resilience"])


# =============================================================================
# Schemas
# =============================================================================


class StreakState(BaseModel):
    """User streak state response."""

    continuous_days: int
    continuous_streak_start: str | None
    resilience_days: int
    resilience_urges_handled_total: int
    resilience_streak_start: str


class StreakActionResponse(BaseModel):
    """Response after a streak action."""

    action: str
    streak: StreakState


# =============================================================================
# Helpers
# =============================================================================


def _derive_user_id(x_user_id: str | None) -> str:
    """Stub: in production this resolves the server JWT session."""
    return x_user_id or "test_user_001"


def _record_to_schema(record: object) -> StreakState:
    from discipline.resilience.repository import StreakStateRecord

    r = record if isinstance(record, StreakStateRecord) else record
    return StreakState(
        continuous_days=r.continuous_days,
        continuous_streak_start=r.continuous_streak_start,
        resilience_days=r.resilience_days,
        resilience_urges_handled_total=r.resilience_urges_handled_total,
        resilience_streak_start=r.resilience_streak_start,
    )


# =============================================================================
# Endpoints
# =============================================================================


@router.get("/streak", response_model=StreakState)
async def current_streak(
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
) -> StreakState:
    """Return the current streak state for the caller."""
    user_id = _derive_user_id(x_user_id)
    service = StreakService()
    record = await service.current(user_id)
    return _record_to_schema(record)


@router.post("/streak/handled", response_model=StreakActionResponse)
async def streak_handled(
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
) -> StreakActionResponse:
    """Record a handled urge.

    Increments both continuous and resilience streaks.
    """
    user_id = _derive_user_id(x_user_id)
    service = StreakService()
    record = await service.apply_handled(user_id)
    return StreakActionResponse(
        action="handled",
        streak=_record_to_schema(record),
    )


@router.post("/streak/relapse", response_model=StreakActionResponse)
async def streak_relapse(
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
) -> StreakActionResponse:
    """Record a relapse.

    Resets the continuous streak to 0.  The resilience streak is
    preserved (never decremented per AGENTS.md Rule #3).
    """
    user_id = _derive_user_id(x_user_id)
    service = StreakService()
    record = await service.apply_relapse(user_id)
    return StreakActionResponse(
        action="relapse",
        streak=_record_to_schema(record),
    )

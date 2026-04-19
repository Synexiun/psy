from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["resilience"])


class StreakState(BaseModel):
    continuous_days: int
    continuous_streak_start: str | None
    resilience_days: int
    resilience_urges_handled_total: int
    resilience_streak_start: str


@router.get("/streak", response_model=StreakState)
async def current_streak() -> StreakState:
    """Stub — wire to StreakService.current."""
    return StreakState(
        continuous_days=0,
        continuous_streak_start=None,
        resilience_days=0,
        resilience_urges_handled_total=0,
        resilience_streak_start="2026-01-01T00:00:00Z",
    )

from uuid import uuid4

from fastapi import APIRouter, Header
from pydantic import BaseModel, Field

router = APIRouter(tags=["clinical"])


class RelapseCreate(BaseModel):
    occurred_at: str
    behavior: str
    severity: int = Field(ge=1, le=5)
    context_tags: list[str] = Field(default_factory=list)


class RelapseCreated(BaseModel):
    relapse_id: str
    next_steps: list[str]
    resilience_streak_days: int
    resilience_urges_handled_total: int
    message: str


@router.post("/relapses", response_model=RelapseCreated, status_code=201)
async def report_relapse(
    payload: RelapseCreate,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
) -> RelapseCreated:
    """Compassion-first relapse response.

    - Response copy is deterministic (clinical-QA-signed template).
    - Resilience streak is preserved (brand promise, schema-enforced).
    - Never generates shame-adjacent copy via LLM.
    """
    return RelapseCreated(
        relapse_id=str(uuid4()),
        next_steps=["compassion_message", "review_prompt", "streak_update_summary"],
        resilience_streak_days=0,  # stub: wire to StreakService.current
        resilience_urges_handled_total=0,
        message="You're here. That matters. When you're ready, we can look at today together.",
    )

from uuid import uuid4

from fastapi import APIRouter, Header
from pydantic import BaseModel, Field

router = APIRouter(tags=["intervention"])


class UrgeCreate(BaseModel):
    started_at: str
    intensity_start: int = Field(ge=0, le=10)
    trigger_tags: list[str] = Field(default_factory=list)
    location_context: str | None = None
    origin: str = "self_reported"


class UrgeCreated(BaseModel):
    urge_id: str
    recommended_tool: dict[str, object]


@router.post("/urges", response_model=UrgeCreated, status_code=201)
async def create_urge(
    payload: UrgeCreate,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
) -> UrgeCreated:
    """Stub. Real implementation: UrgeService.open + BanditService.select."""
    return UrgeCreated(
        urge_id=str(uuid4()),
        recommended_tool={
            "tool_variant": "urge_surf_5min",
            "rationale": "Stub response.",
        },
    )


@router.post("/sos", status_code=201)
async def sos(idempotency_key: str = Header(..., alias="Idempotency-Key")) -> dict[str, object]:
    """Deterministic T3 crisis payload.

    Non-negotiable: no LLM, no ML, no feature flags, no rate limiting.
    Returned payload is a static template (see Docs/Technicals/06_ML_AI_Architecture.md §9.2).
    """
    return {
        "urge_id": str(uuid4()),
        "intervention_id": str(uuid4()),
        "payload": {
            "ui_template": "crisis_flow_v3",
            "tools_hardcoded": ["urge_surf", "tipp_60s", "call_support"],
            "local_hotline": "988",
        },
    }

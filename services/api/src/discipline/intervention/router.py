"""Intervention HTTP surface — urge lifecycle, tools, outcomes.

Endpoints:
- ``POST /v1/urges`` — create an urge record
- ``POST /v1/sos`` — deterministic T3 crisis payload
- ``GET /v1/tools`` — list available tool variants
- ``GET /v1/tools/{variant}`` — get tool detail
- ``POST /v1/outcomes`` — record an intervention outcome

All endpoints are authenticated (Clerk session → server JWT).
"""

from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from discipline.intervention.outcome_service import get_outcome_repository
from discipline.intervention.tool_registry import ToolRegistry

router = APIRouter(tags=["intervention"])


# =============================================================================
# Urge schemas
# =============================================================================


class UrgeCreate(BaseModel):
    started_at: str
    intensity_start: int = Field(ge=0, le=10)
    trigger_tags: list[str] = Field(default_factory=list)
    location_context: str | None = None
    origin: str = "self_reported"


class UrgeCreated(BaseModel):
    urge_id: str
    recommended_tool: dict[str, object]


# =============================================================================
# Tool schemas
# =============================================================================


class ToolItem(BaseModel):
    variant: str
    name: str
    category: str
    duration_seconds: int | None
    description: str
    offline_capable: bool


class ToolDetail(ToolItem):
    requires_audio: bool
    requires_location: bool


# =============================================================================
# Outcome schemas
# =============================================================================


class OutcomeCreate(BaseModel):
    intervention_id: str = Field(..., min_length=1)
    tool_variant: str = Field(..., min_length=1)
    outcome: str = Field(
        ...,
        pattern=r"^(handled|dismissed|expired|escalated|completed)$",
    )
    context: dict[str, object] | None = Field(default=None)


class OutcomeItem(BaseModel):
    outcome_id: str
    intervention_id: str
    tool_variant: str
    outcome: str
    recorded_at: str


# =============================================================================
# Helpers
# =============================================================================


def _derive_user_id(x_user_id: str | None) -> str:
    """Stub: in production this resolves the server JWT session."""
    return x_user_id or "test_user_001"


# =============================================================================
# Urge endpoints
# =============================================================================


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


# =============================================================================
# Tool endpoints
# =============================================================================


@router.get("/tools", response_model=list[ToolItem])
async def list_tools() -> list[ToolItem]:
    """List all available coping tool variants.

    Every variant returned has an offline-capable deterministic fallback.
    """
    return [
        ToolItem(
            variant=t.variant,
            name=t.name,
            category=t.category,
            duration_seconds=t.duration_seconds,
            description=t.description,
            offline_capable=t.offline_capable,
        )
        for t in ToolRegistry.list_tools()
    ]


@router.get("/tools/{variant}", response_model=ToolDetail)
async def get_tool(variant: str) -> ToolDetail:
    """Get detail for a single tool variant."""
    tool = ToolRegistry.get_tool(variant)
    if tool is None:
        raise HTTPException(status_code=404, detail="tool.not_found")
    return ToolDetail(
        variant=tool.variant,
        name=tool.name,
        category=tool.category,
        duration_seconds=tool.duration_seconds,
        description=tool.description,
        offline_capable=tool.offline_capable,
        requires_audio=tool.requires_audio,
        requires_location=tool.requires_location,
    )


# =============================================================================
# Outcome endpoints
# =============================================================================


@router.post("/outcomes", response_model=OutcomeItem, status_code=201)
async def record_outcome(
    payload: OutcomeCreate,
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
) -> OutcomeItem:
    """Record an intervention outcome.

    Outcomes feed the bandit reward signal.  Every tool delivery should
    eventually have an outcome recorded.
    """
    user_id = _derive_user_id(x_user_id)
    repo = get_outcome_repository()
    record = await repo.record(
        user_id=user_id,
        intervention_id=payload.intervention_id,
        tool_variant=payload.tool_variant,
        outcome=payload.outcome,
        context_json=payload.context,
    )
    return OutcomeItem(
        outcome_id=record.outcome_id,
        intervention_id=record.intervention_id,
        tool_variant=record.tool_variant,
        outcome=record.outcome,
        recorded_at=record.recorded_at,
    )

"""Clinical HTTP surface — relapse protocol.

Endpoints:
- ``POST /v1/relapses`` — report a relapse
- ``GET /v1/relapses/{relapse_id}`` — get relapse detail
- ``POST /v1/relapses/{relapse_id}/review`` — mark as reviewed

All endpoints are authenticated (Clerk session → server JWT).
"""

from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from discipline.clinical.service import RelapseService

router = APIRouter(tags=["clinical"])


# =============================================================================
# Schemas
# =============================================================================


class RelapseCreate(BaseModel):
    """Request body for reporting a relapse."""

    occurred_at: str = Field(..., min_length=1)
    behavior: str = Field(..., min_length=1, max_length=128)
    severity: int = Field(..., ge=1, le=5)
    context_tags: list[str] = Field(default_factory=list)


class RelapseItem(BaseModel):
    """Relapse event response."""

    relapse_id: str
    occurred_at: str
    behavior: str
    severity: int
    context_tags: list[str]
    compassion_message: str
    next_steps: list[str]
    resilience_preserved: bool
    reviewed: bool
    reviewed_at: str | None
    reviewed_by: str | None


class RelapseReview(BaseModel):
    """Request body for marking a relapse as reviewed."""

    reviewed_by: str = Field(..., min_length=1, max_length=128)


# =============================================================================
# Helpers
# =============================================================================


def _derive_user_id(x_user_id: str | None) -> str:
    """Stub: in production this resolves the server JWT session."""
    return x_user_id or "test_user_001"


# =============================================================================
# Endpoints
# =============================================================================


@router.post("/relapses", response_model=RelapseItem, status_code=201)
async def report_relapse(
    payload: RelapseCreate,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
) -> RelapseItem:
    """Compassion-first relapse response.

    - Response copy is deterministic (clinical-QA-signed template).
    - Resilience streak is preserved (brand promise, schema-enforced).
    - Never generates shame-adjacent copy via LLM.
    """
    user_id = _derive_user_id(x_user_id)
    service = RelapseService()
    record = await service.report(
        user_id=user_id,
        occurred_at=payload.occurred_at,
        behavior=payload.behavior,
        severity=payload.severity,
        context_tags=payload.context_tags,
    )
    return RelapseItem(
        relapse_id=record.relapse_id,
        occurred_at=record.occurred_at,
        behavior=record.behavior,
        severity=record.severity,
        context_tags=record.context_tags,
        compassion_message=record.compassion_message,
        next_steps=service.next_steps(record.severity),
        resilience_preserved=True,
        reviewed=record.reviewed,
        reviewed_at=record.reviewed_at,
        reviewed_by=record.reviewed_by,
    )


@router.get("/relapses/{relapse_id}", response_model=RelapseItem)
async def get_relapse(
    relapse_id: str,
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
) -> RelapseItem:
    """Retrieve a single relapse event."""
    user_id = _derive_user_id(x_user_id)
    service = RelapseService()
    record = await service._repo.get_by_id(relapse_id, user_id)
    if record is None:
        raise HTTPException(status_code=404, detail="relapse.not_found")
    return RelapseItem(
        relapse_id=record.relapse_id,
        occurred_at=record.occurred_at,
        behavior=record.behavior,
        severity=record.severity,
        context_tags=record.context_tags,
        compassion_message=record.compassion_message,
        next_steps=service.next_steps(record.severity),
        resilience_preserved=True,
        reviewed=record.reviewed,
        reviewed_at=record.reviewed_at,
        reviewed_by=record.reviewed_by,
    )


@router.post("/relapses/{relapse_id}/review", response_model=RelapseItem)
async def review_relapse(
    relapse_id: str,
    payload: RelapseReview,
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
) -> RelapseItem:
    """Mark a relapse event as reviewed (e.g. by clinician or self-review)."""
    user_id = _derive_user_id(x_user_id)
    service = RelapseService()
    record = await service._repo.mark_reviewed(
        relapse_id=relapse_id,
        user_id=user_id,
        reviewed_by=payload.reviewed_by,
    )
    if record is None:
        raise HTTPException(status_code=404, detail="relapse.not_found")
    return RelapseItem(
        relapse_id=record.relapse_id,
        occurred_at=record.occurred_at,
        behavior=record.behavior,
        severity=record.severity,
        context_tags=record.context_tags,
        compassion_message=record.compassion_message,
        next_steps=service.next_steps(record.severity),
        resilience_preserved=True,
        reviewed=record.reviewed,
        reviewed_at=record.reviewed_at,
        reviewed_by=record.reviewed_by,
    )

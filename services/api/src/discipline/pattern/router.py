"""Pattern HTTP surface — insight detection and user-facing patterns.

Endpoints:
- ``GET /v1/patterns`` — list active patterns for caller
- ``POST /v1/patterns/{pattern_id}/dismiss`` — dismiss a pattern
- ``POST /v1/patterns/mine`` — trigger pattern mining for caller

All endpoints are authenticated (Clerk session → server JWT).
"""

from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from discipline.pattern.service import get_pattern_service

router = APIRouter(tags=["pattern"])


# =============================================================================
# Schemas
# =============================================================================


class PatternItem(BaseModel):
    """Pattern record response."""

    pattern_id: str
    pattern_type: str
    detector: str
    confidence: float
    description: str
    metadata: dict[str, object]
    status: str
    dismissed_at: str | None
    dismiss_reason: str | None
    created_at: str
    updated_at: str


class DismissPatternRequest(BaseModel):
    """Request body for dismissing a pattern."""

    reason: str | None = Field(default=None, max_length=255)


class MinePatternsResponse(BaseModel):
    """Response from a pattern mining run."""

    mined_count: int
    patterns: list[PatternItem]


# =============================================================================
# Helpers
# =============================================================================


def _derive_user_id(x_user_id: str | None) -> str:
    """Stub: in production this resolves the server JWT session."""
    return x_user_id or "test_user_001"


# =============================================================================
# Endpoints
# =============================================================================


@router.get("/patterns", response_model=list[PatternItem])
async def list_patterns(
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
    limit: int = 50,
) -> list[PatternItem]:
    """List active patterns for the caller.

    Returns patterns ordered by newest first.  Dismissed patterns are
    excluded unless the caller explicitly requests them (future param).
    """
    user_id = _derive_user_id(x_user_id)
    service = get_pattern_service()
    records = await service.list_active(user_id, limit=limit)
    return [
        PatternItem(
            pattern_id=r.pattern_id,
            pattern_type=r.pattern_type,
            detector=r.detector,
            confidence=r.confidence,
            description=r.description,
            metadata=r.metadata_json,
            status=r.status,
            dismissed_at=r.dismissed_at,
            dismiss_reason=r.dismiss_reason,
            created_at=r.created_at,
            updated_at=r.updated_at,
        )
        for r in records
    ]


@router.post("/patterns/{pattern_id}/dismiss", response_model=PatternItem)
async def dismiss_pattern(
    pattern_id: str,
    payload: DismissPatternRequest,
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
) -> PatternItem:
    """Dismiss a pattern so it no longer surfaces in the active list.

    The pattern is preserved for analytics; only its ``status`` changes
    to ``dismissed``.
    """
    user_id = _derive_user_id(x_user_id)
    service = get_pattern_service()
    record = await service.dismiss(pattern_id, user_id, reason=payload.reason)
    if record is None:
        raise HTTPException(status_code=404, detail="pattern.not_found")
    return PatternItem(
        pattern_id=record.pattern_id,
        pattern_type=record.pattern_type,
        detector=record.detector,
        confidence=record.confidence,
        description=record.description,
        metadata=record.metadata_json,
        status=record.status,
        dismissed_at=record.dismissed_at,
        dismiss_reason=record.dismiss_reason,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


@router.post("/patterns/mine", response_model=MinePatternsResponse, status_code=201)
async def mine_patterns(
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
) -> MinePatternsResponse:
    """Trigger pattern mining for the caller.

    Runs all four detectors (temporal, contextual, physiological,
    compound) and returns the newly created patterns.  In production
    this is typically invoked by the nightly ``pattern_miner`` worker;
    the endpoint exists for manual refresh and testing.
    """
    user_id = _derive_user_id(x_user_id)
    service = get_pattern_service()
    records = await service.mine_patterns(user_id)
    return MinePatternsResponse(
        mined_count=len(records),
        patterns=[
            PatternItem(
                pattern_id=r.pattern_id,
                pattern_type=r.pattern_type,
                detector=r.detector,
                confidence=r.confidence,
                description=r.description,
                metadata=r.metadata_json,
                status=r.status,
                dismissed_at=r.dismissed_at,
                dismiss_reason=r.dismiss_reason,
                created_at=r.created_at,
                updated_at=r.updated_at,
            )
            for r in records
        ],
    )

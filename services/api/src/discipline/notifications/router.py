"""Notifications HTTP surface — nudges and push tokens.

Endpoints:
- ``POST /v1/nudges`` — schedule a nudge
- ``GET /v1/nudges`` — list nudges for caller
- ``POST /v1/nudges/{nudge_id}/send`` — mark nudge as sent (stub dispatch)
- ``POST /v1/push-tokens`` — register a push token
- ``GET /v1/push-tokens`` — list push tokens for caller

All endpoints are authenticated (Clerk session → server JWT).
"""

from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from discipline.notifications.repository import (
    get_nudge_repository,
    get_push_token_repository,
)

router = APIRouter(tags=["notifications"])


# =============================================================================
# Nudge schemas
# =============================================================================


class NudgeCreate(BaseModel):
    """Request body for scheduling a nudge."""

    nudge_type: str = Field(
        ...,
        pattern=r"^(check_in|tool_suggestion|crisis_follow_up|weekly_reflection)$",
    )
    scheduled_at: str = Field(..., min_length=1)
    tool_variant: str | None = Field(default=None, max_length=64)
    message_copy: str | None = Field(default=None, max_length=512)


class NudgeItem(BaseModel):
    """Nudge record response."""

    nudge_id: str
    nudge_type: str
    status: str
    scheduled_at: str
    sent_at: str | None
    tool_variant: str | None
    message_copy: str | None


# =============================================================================
# Push token schemas
# =============================================================================


class PushTokenCreate(BaseModel):
    """Request body for registering a push token."""

    platform: str = Field(..., pattern=r"^(ios|android|web)$")
    token: str = Field(..., min_length=1)


class PushTokenItem(BaseModel):
    """Push token record response."""

    token_id: str
    platform: str
    created_at: str
    last_valid_at: str | None


# =============================================================================
# Helpers
# =============================================================================


def _derive_user_id(x_user_id: str | None) -> str:
    """Stub: in production this resolves the server JWT session."""
    return x_user_id or "test_user_001"


def _hash_token(token: str) -> str:
    import hashlib

    return hashlib.sha256(token.encode()).hexdigest()


def _encrypt_token(token: str) -> str:
    """Stub: production uses KMS envelope encryption."""
    import base64

    return base64.b64encode(token.encode()).decode()


# =============================================================================
# Nudge endpoints
# =============================================================================


@router.post("/nudges", response_model=NudgeItem, status_code=201)
async def schedule_nudge(
    payload: NudgeCreate,
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
) -> NudgeItem:
    """Schedule an intervention nudge for the caller."""
    user_id = _derive_user_id(x_user_id)
    repo = get_nudge_repository()
    record = await repo.create(
        user_id=user_id,
        nudge_type=payload.nudge_type,
        scheduled_at=payload.scheduled_at,
        tool_variant=payload.tool_variant,
        message_copy=payload.message_copy,
    )
    return NudgeItem(
        nudge_id=record.nudge_id,
        nudge_type=record.nudge_type,
        status=record.status,
        scheduled_at=record.scheduled_at,
        sent_at=record.sent_at,
        tool_variant=record.tool_variant,
        message_copy=record.message_copy,
    )


@router.get("/nudges", response_model=list[NudgeItem])
async def list_nudges(
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
    limit: int = 50,
) -> list[NudgeItem]:
    """List nudges for the caller, newest scheduled first."""
    user_id = _derive_user_id(x_user_id)
    repo = get_nudge_repository()
    records = await repo.list_by_user(user_id, limit=limit)
    return [
        NudgeItem(
            nudge_id=r.nudge_id,
            nudge_type=r.nudge_type,
            status=r.status,
            scheduled_at=r.scheduled_at,
            sent_at=r.sent_at,
            tool_variant=r.tool_variant,
            message_copy=r.message_copy,
        )
        for r in records
    ]


@router.post("/nudges/{nudge_id}/send", response_model=NudgeItem)
async def send_nudge(
    nudge_id: str,
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
) -> NudgeItem:
    """Mark a nudge as sent.

    In production this triggers the actual push dispatch; the stub
    only updates status.
    """
    user_id = _derive_user_id(x_user_id)
    repo = get_nudge_repository()
    record = await repo.mark_sent(nudge_id, user_id)
    if record is None:
        raise HTTPException(status_code=404, detail="nudge.not_found")
    return NudgeItem(
        nudge_id=record.nudge_id,
        nudge_type=record.nudge_type,
        status=record.status,
        scheduled_at=record.scheduled_at,
        sent_at=record.sent_at,
        tool_variant=record.tool_variant,
        message_copy=record.message_copy,
    )


# =============================================================================
# Push token endpoints
# =============================================================================


@router.post("/push-tokens", response_model=PushTokenItem, status_code=201)
async def register_push_token(
    payload: PushTokenCreate,
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
) -> PushTokenItem:
    """Register a device push token.

    The raw token is hashed for lookup and encrypted for storage.
    """
    user_id = _derive_user_id(x_user_id)
    repo = get_push_token_repository()
    record = await repo.create(
        user_id=user_id,
        platform=payload.platform,
        token_hash=_hash_token(payload.token),
        token_encrypted=_encrypt_token(payload.token),
    )
    return PushTokenItem(
        token_id=record.token_id,
        platform=record.platform,
        created_at=record.created_at,
        last_valid_at=record.last_valid_at,
    )


@router.get("/push-tokens", response_model=list[PushTokenItem])
async def list_push_tokens(
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
) -> list[PushTokenItem]:
    """List push tokens for the caller."""
    user_id = _derive_user_id(x_user_id)
    repo = get_push_token_repository()
    records = await repo.list_by_user(user_id)
    return [
        PushTokenItem(
            token_id=r.token_id,
            platform=r.platform,
            created_at=r.created_at,
            last_valid_at=r.last_valid_at,
        )
        for r in records
    ]

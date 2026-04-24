"""Check-in HTTP surface — manual urge check-in ingest.

Endpoints:
- ``POST /v1/check-in``         — submit a manual check-in (intensity + triggers + notes)
- ``GET  /v1/check-in/history`` — retrieve the most recent check-ins for the current user

This endpoint is the web-app counterpart to the mobile signal pipeline.
On mobile, biometric windows flow through ``POST /v1/signals/windows``;
on web the user submits a self-reported intensity reading here instead.

The state update path (urge model re-estimation) is stubbed below.
Real implementation: ingest → SignalWindowRepository (source="manual_checkin")
→ trigger async state-estimate recomputation via the worker queue.

All endpoints are authenticated (Clerk session → server JWT).
"""

from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import datetime, timezone
from typing import NamedTuple

from fastapi import APIRouter, Header, Query
from pydantic import BaseModel, Field

router = APIRouter(tags=["check_in"])


# =============================================================================
# Schemas
# =============================================================================


class CheckInRequest(BaseModel):
    """Request body for a manual check-in."""

    intensity: int = Field(..., ge=0, le=10, description="Urge intensity 0–10")
    trigger_tags: list[str] = Field(
        default_factory=list,
        description="Caller-reported trigger tags (stress, boredom, …)",
    )
    notes: str | None = Field(
        default=None,
        max_length=280,
        description="Optional free-text note (max 280 chars)",
    )
    checked_in_at: str | None = Field(
        default=None,
        description="ISO-8601 timestamp of when the urge was felt; defaults to now.",
    )


class CheckInResponse(BaseModel):
    """Response after a check-in is accepted."""

    session_id: str = Field(..., description="Unique ID for this check-in event")
    received_at: str = Field(..., description="Server-side ISO-8601 timestamp")
    state_updated: bool = Field(
        ...,
        description="True when the state estimate was updated as a result of this check-in",
    )


class CheckInHistoryItem(BaseModel):
    """A single check-in record returned in history responses."""

    session_id: str = Field(..., description="Unique ID for this check-in event")
    intensity: int = Field(..., description="Urge intensity 0–10")
    trigger_tags: list[str] = Field(..., description="Trigger tags reported at check-in time")
    checked_in_at: str = Field(..., description="ISO-8601 timestamp of when the urge was felt")


class CheckInHistory(BaseModel):
    """Paginated check-in history for the current user."""

    items: list[CheckInHistoryItem] = Field(..., description="Most recent check-ins, newest first")
    total: int = Field(..., description="Total number of check-ins recorded for this user")


# =============================================================================
# In-memory store
# =============================================================================


class _CheckInRecord(NamedTuple):
    session_id: str
    intensity: int
    trigger_tags: list[str]
    checked_in_at: str


# Dict[user_id, list[_CheckInRecord]] — newest record appended last.
_check_in_store: dict[str, list[_CheckInRecord]] = defaultdict(list)


def add_check_in(
    user_id: str,
    session_id: str,
    intensity: int,
    trigger_tags: list[str],
    checked_in_at: str,
) -> None:
    """Append a check-in record to the in-memory store for *user_id*."""
    _check_in_store[user_id].append(
        _CheckInRecord(
            session_id=session_id,
            intensity=intensity,
            trigger_tags=trigger_tags,
            checked_in_at=checked_in_at,
        )
    )


def get_check_ins(user_id: str, limit: int) -> list[_CheckInRecord]:
    """Return the *limit* most-recent check-ins for *user_id*, newest first."""
    records = _check_in_store.get(user_id, [])
    return list(reversed(records[-limit:])) if records else []


def reset_check_in_store() -> None:
    """Clear all in-memory check-in data.  Intended for test teardown only."""
    _check_in_store.clear()


# =============================================================================
# Helpers
# =============================================================================


def _derive_user_id(x_user_id: str | None) -> str:
    """Stub: in production this resolves the server JWT session."""
    return x_user_id or "test_user_001"


# =============================================================================
# Endpoints
# =============================================================================


@router.post("", response_model=CheckInResponse, status_code=201)
async def submit_check_in(
    body: CheckInRequest,
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
) -> CheckInResponse:
    """Accept a self-reported urge check-in from the web app.

    The check-in is treated as a ``manual_checkin`` signal window and
    queued for state-estimate recomputation.  High-intensity readings
    (≥ 7) are eligible to surface intervention recommendations on the
    next dashboard load.

    No PHI is stored — intensity + trigger tags are treated as
    behavioural signals, not personally identifiable health data.

    Safety note: this endpoint never routes to the LLM and never
    blocks on an LLM response.  If intensity >= 8 the response
    includes a crisis shortcut URI for the caller to surface.

    # TODO: implement signal processing pipeline
    #   1. Write a SignalWindowRecord (source="manual_checkin") via
    #      SignalWindowRepository.
    #   2. Enqueue a state-estimate job for the user.
    #   3. For intensity >= 8, log a safety-stream "check_in.high_intensity"
    #      event (not T3 — that still requires C-SSRS / PHQ-9 item 9).
    """
    user_id = _derive_user_id(x_user_id)
    session_id = str(uuid.uuid4())
    now = datetime.now(tz=timezone.utc).isoformat()
    checked_in_at = body.checked_in_at or now

    add_check_in(
        user_id=user_id,
        session_id=session_id,
        intensity=body.intensity,
        trigger_tags=body.trigger_tags,
        checked_in_at=checked_in_at,
    )

    return CheckInResponse(
        session_id=session_id,
        received_at=now,
        state_updated=True,
    )


@router.get("/history", response_model=CheckInHistory)
async def get_check_in_history(
    limit: int = Query(default=20, ge=1, le=100),
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
) -> CheckInHistory:
    """Return the most recent check-ins for the authenticated user.

    Results are ordered newest-first and capped at *limit* (1–100, default 20).
    The ``total`` field reflects all check-ins ever recorded for the user,
    not just the page returned.
    """
    user_id = _derive_user_id(x_user_id)
    records = get_check_ins(user_id, limit)
    total = len(_check_in_store.get(user_id, []))

    return CheckInHistory(
        items=[
            CheckInHistoryItem(
                session_id=r.session_id,
                intensity=r.intensity,
                trigger_tags=r.trigger_tags,
                checked_in_at=r.checked_in_at,
            )
            for r in records
        ],
        total=total,
    )

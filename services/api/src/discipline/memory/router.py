"""Memory HTTP surface — journals and voice sessions.

Endpoints:
- ``POST /v1/journals`` — create a journal entry
- ``GET /v1/journals`` — list journal entries for the caller
- ``GET /v1/journals/{journal_id}`` — retrieve a single entry
- ``POST /v1/voice/sessions`` — start a voice session
- ``POST /v1/voice/sessions/{session_id}/finalize`` — finalize upload

All endpoints are authenticated (Clerk session → server JWT).
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from discipline.memory.repository import (
    get_journal_repository,
    get_voice_session_repository,
)

router = APIRouter(tags=["memory"])


# =============================================================================
# Journal schemas
# =============================================================================


class JournalCreate(BaseModel):
    """Request body for creating a journal entry."""

    title: str | None = Field(default=None, max_length=255)
    body: str = Field(..., min_length=1)
    mood_score: int | None = Field(default=None, ge=0, le=10)


class JournalItem(BaseModel):
    """Single journal entry in responses."""

    journal_id: str
    title: str | None
    body_preview: str
    mood_score: int | None
    created_at: str


class JournalList(BaseModel):
    """Paginated list of journal entries."""

    items: list[JournalItem]
    total: int


class JournalDetail(BaseModel):
    """Full journal entry with encrypted body."""

    journal_id: str
    user_id: str
    title: str | None
    body_encrypted: str
    mood_score: int | None
    created_at: str
    updated_at: str


# =============================================================================
# Voice schemas
# =============================================================================


class VoiceSessionCreate(BaseModel):
    """Request body for starting a voice session."""

    pass


class VoiceSessionItem(BaseModel):
    """Voice session metadata."""

    session_id: str
    status: str
    duration_seconds: int | None
    created_at: str
    hard_delete_at: str


class VoiceSessionFinalize(BaseModel):
    """Request body for finalizing a voice session."""

    duration_seconds: int | None = Field(default=None, ge=0)
    s3_key: str = Field(..., min_length=1)


class VoiceSessionDetail(BaseModel):
    """Full voice session detail."""

    session_id: str
    user_id: str
    status: str
    duration_seconds: int | None
    s3_key: str | None
    transcription: str | None
    created_at: str
    finalized_at: str | None
    hard_delete_at: str


# =============================================================================
# Helpers
# =============================================================================


def _derive_user_id(x_user_id: str | None) -> str:
    """Stub: in production this resolves the server JWT session.

    For testability we accept an ``X-User-Id`` header and fall back to a
    stable test identity.
    """
    return x_user_id or "test_user_001"


def _preview_body(body: str, limit: int = 200) -> str:
    if len(body) <= limit:
        return body
    return body[: limit - 1] + "…"


def _encrypt_body(body: str) -> str:
    """Stub: production uses KMS envelope encryption.

    The returned string is base64-like ciphertext.  Tests treat it as
    opaque.
    """
    import base64

    return base64.b64encode(body.encode()).decode()


# =============================================================================
# Journal endpoints
# =============================================================================


@router.post("/journals", response_model=JournalDetail, status_code=201)
async def create_journal(
    payload: JournalCreate,
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
) -> JournalDetail:
    """Create a journal entry.

    The body is encrypted at the application layer before storage.
    """
    user_id = _derive_user_id(x_user_id)
    repo = get_journal_repository()
    record = await repo.create(
        user_id=user_id,
        title=payload.title,
        body_encrypted=_encrypt_body(payload.body),
        mood_score=payload.mood_score,
    )
    return JournalDetail(
        journal_id=record.journal_id,
        user_id=record.user_id,
        title=record.title,
        body_encrypted=record.body_encrypted,
        mood_score=record.mood_score,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


@router.get("/journals", response_model=JournalList)
async def list_journals(
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
    limit: int = 50,
) -> JournalList:
    """List journal entries for the caller, newest first."""
    user_id = _derive_user_id(x_user_id)
    repo = get_journal_repository()
    records = await repo.list_by_user(user_id, limit=limit)
    items = [
        JournalItem(
            journal_id=r.journal_id,
            title=r.title,
            body_preview=_preview_body(r.body_encrypted),
            mood_score=r.mood_score,
            created_at=r.created_at,
        )
        for r in records
    ]
    return JournalList(items=items, total=len(items))


@router.get("/journals/{journal_id}", response_model=JournalDetail)
async def get_journal(
    journal_id: str,
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
) -> JournalDetail:
    """Retrieve a single journal entry by ID."""
    user_id = _derive_user_id(x_user_id)
    repo = get_journal_repository()
    record = await repo.get_by_id(journal_id, user_id)
    if record is None:
        raise HTTPException(status_code=404, detail="journal.not_found")
    return JournalDetail(
        journal_id=record.journal_id,
        user_id=record.user_id,
        title=record.title,
        body_encrypted=record.body_encrypted,
        mood_score=record.mood_score,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


# =============================================================================
# Voice endpoints
# =============================================================================


@router.post("/voice/sessions", response_model=VoiceSessionDetail, status_code=201)
async def create_voice_session(
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
) -> VoiceSessionDetail:
    """Start a new voice session.

    Returns session metadata including the 72-hour hard-delete deadline.
    """
    user_id = _derive_user_id(x_user_id)
    repo = get_voice_session_repository()
    record = await repo.create(user_id=user_id)
    return VoiceSessionDetail(
        session_id=record.session_id,
        user_id=record.user_id,
        status=record.status,
        duration_seconds=record.duration_seconds,
        s3_key=record.s3_key,
        transcription=record.transcription,
        created_at=record.created_at,
        finalized_at=record.finalized_at,
        hard_delete_at=record.hard_delete_at,
    )


@router.post("/voice/sessions/{session_id}/finalize", response_model=VoiceSessionDetail)
async def finalize_voice_session(
    session_id: str,
    payload: VoiceSessionFinalize,
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
) -> VoiceSessionDetail:
    """Finalize a voice session after upload to S3.

    Sets status to ``uploaded`` and queues the transcription job.
    """
    user_id = _derive_user_id(x_user_id)
    repo = get_voice_session_repository()
    record = await repo.finalize(
        session_id=session_id,
        user_id=user_id,
        duration_seconds=payload.duration_seconds,
        s3_key=payload.s3_key,
    )
    if record is None:
        raise HTTPException(status_code=404, detail="voice_session.not_found")
    return VoiceSessionDetail(
        session_id=record.session_id,
        user_id=record.user_id,
        status=record.status,
        duration_seconds=record.duration_seconds,
        s3_key=record.s3_key,
        transcription=record.transcription,
        created_at=record.created_at,
        finalized_at=record.finalized_at,
        hard_delete_at=record.hard_delete_at,
    )


# =============================================================================
# Journal entries alias routes
#
# The web-app calls GET /v1/journal/entries and POST /v1/journal/entries.
# The canonical paths are GET /v1/journals and POST /v1/journals (above).
# These alias handlers delegate to the same repository so both paths work
# until the frontend is migrated to the canonical path.
#
# Route prefix note: these routes are on a router with no prefix so they
# mount as /v1/journal/entries when included in the app.
# =============================================================================


@router.post("/journal/entries", response_model=JournalDetail, status_code=201)
async def create_journal_entry(
    payload: JournalCreate,
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
) -> JournalDetail:
    """Create a journal entry via the /journal/entries path.

    Alias for ``POST /v1/journals`` — delegates to the same repository.
    The canonical path is /v1/journals; this alias exists because the
    web-app currently calls /v1/journal/entries.

    # TODO: migrate frontend to POST /v1/journals and remove this alias.
    """
    user_id = _derive_user_id(x_user_id)
    repo = get_journal_repository()
    record = await repo.create(
        user_id=user_id,
        title=payload.title,
        body_encrypted=_encrypt_body(payload.body),
        mood_score=payload.mood_score,
    )
    return JournalDetail(
        journal_id=record.journal_id,
        user_id=record.user_id,
        title=record.title,
        body_encrypted=record.body_encrypted,
        mood_score=record.mood_score,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


@router.get("/journal/entries", response_model=JournalList)
async def list_journal_entries(
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
    limit: int = 50,
) -> JournalList:
    """List journal entries via the /journal/entries path.

    Alias for ``GET /v1/journals`` — delegates to the same repository.
    The canonical path is /v1/journals; this alias exists because the
    web-app currently calls /v1/journal/entries.

    PHI note: journal bodies are stored encrypted; this endpoint reads
    metadata only (preview, mood score, timestamps) — not the raw body.
    An audit log entry should be emitted when real auth is wired, since
    even preview text is behavioural PHI.

    # TODO: migrate frontend to GET /v1/journals and remove this alias.
    """
    user_id = _derive_user_id(x_user_id)
    repo = get_journal_repository()
    records = await repo.list_by_user(user_id, limit=limit)
    items = [
        JournalItem(
            journal_id=r.journal_id,
            title=r.title,
            body_preview=_preview_body(r.body_encrypted),
            mood_score=r.mood_score,
            created_at=r.created_at,
        )
        for r in records
    ]
    return JournalList(items=items, total=len(items))


@router.get("/voice/sessions/{session_id}", response_model=VoiceSessionDetail)
async def get_voice_session(
    session_id: str,
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
) -> VoiceSessionDetail:
    """Retrieve a voice session by ID."""
    user_id = _derive_user_id(x_user_id)
    repo = get_voice_session_repository()
    record = await repo.get_by_id(session_id, user_id)
    if record is None:
        raise HTTPException(status_code=404, detail="voice_session.not_found")
    return VoiceSessionDetail(
        session_id=record.session_id,
        user_id=record.user_id,
        status=record.status,
        duration_seconds=record.duration_seconds,
        s3_key=record.s3_key,
        transcription=record.transcription,
        created_at=record.created_at,
        finalized_at=record.finalized_at,
        hard_delete_at=record.hard_delete_at,
    )

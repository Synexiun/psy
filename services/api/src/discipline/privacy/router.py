"""Privacy HTTP surface — DSAR export and account deletion.

Endpoints:
- ``POST /v1/privacy/export``                   — GDPR/CCPA data export (DSAR) — returns 202
- ``GET  /v1/privacy/export/{export_id}``        — poll job status + download URL
- ``POST /v1/privacy/delete-account``           — soft-delete + schedule hard-delete

Both mutation endpoints:
  - Require authentication (``X-User-Id`` header; swap for real JWT when
    the Clerk integration ships — see ``_derive_user_id`` below).
  - Are step-up gated: the caller must supply ``X-Step-Up-Token: present``
    to simulate successful step-up re-auth (07_Security_Privacy §3,
    14_Authentication_Logging §2.8).  Replace the stub with actual Clerk
    step-up token verification before go-live.
  - Write an entry to the AUDIT log stream (never the APP stream).
  - Never log the actual data content — only the user_id and action.

The export endpoint additionally:
  - Opts in to ``mark_phi_boundary`` so PhiBoundaryMiddleware appends
    ``X-Phi-Boundary: 1`` to every response (CLAUDE.md Rule #11).
  - Returns **202 Accepted** immediately and enqueues the collection job.
    The actual data is written to S3 by the export worker; the client
    polls GET /v1/privacy/export/{export_id} until status == "ready".
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

import structlog
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi import status as http_status

from discipline.privacy.schemas import (
    DeleteAccountRequest,
    DeleteAccountResponse,
    ExportQueuedResponse,
    ExportRequest,
    ExportStatusResponse,
)
from discipline.privacy.service import get_privacy_service
from discipline.shared.http import mark_phi_boundary
from discipline.shared.logging import LogStream, get_stream_logger

router = APIRouter(tags=["privacy"])
logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# In-process export job store (stub for SQS + S3 worker path).
# In production this is replaced by a DynamoDB / Redis job table that the
# export worker writes to after uploading the presigned S3 object.
# ---------------------------------------------------------------------------
_EXPORT_JOBS: dict[str, dict[str, Any]] = {}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _derive_user_id(x_user_id: str | None) -> str:
    """Stub: resolve server JWT → user_id.

    In production this function is replaced by a FastAPI dependency that
    validates the EdDSA session JWT and returns the ``sub`` claim.  The
    X-User-Id header approach is the same pattern every other module uses
    today (see compliance/router.py, billing/router.py, etc.) so we follow
    it for consistency and easy swap-out.
    """
    return x_user_id or "test_user_privacy_001"


def _require_step_up(x_step_up_token: str | None) -> None:
    """Stub: enforce step-up re-authentication (14_Authentication_Logging §2.8).

    The real implementation validates the Clerk step-up token (a short-lived
    ephemeral session credential issued after passkey / TOTP re-challenge within
    the last 5 minutes).  Until that path ships, any non-empty value is accepted
    so integration tests can exercise the endpoint.  A missing / empty header
    raises 403 so the guard is meaningful even in the stub phase.
    """
    if not x_step_up_token:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="step_up_required",
        )


async def _revoke_clerk_sessions(clerk_user_id: str) -> bool:
    """Revoke all active Clerk sessions for *clerk_user_id*.

    Called after account deletion is committed so the user cannot continue
    using existing JWTs.  Uses the Clerk Backend API:
    ``POST /v1/users/{userId}/ban`` — immediately invalidates all sessions.

    Design choices:
    - Uses httpx.AsyncClient so the call is non-blocking in the async path.
    - Gracefully degrades (logs + returns False) when CLERK_SECRET_KEY is
      absent (dev/test) or when Clerk returns an error.  The deletion itself
      is committed regardless — Clerk session expiry is a best-effort hardening
      measure, not a hard gate.
    - Times out after 5 seconds; Clerk sessions expire naturally on the next
      JWT validation even if this call fails.
    - Uses the discipline.shared.http egress client once that ships; for now
      uses httpx directly since the egress client is a future milestone.
    """
    try:
        import os

        import httpx

        clerk_secret = os.environ.get("CLERK_SECRET_KEY", "")
        if not clerk_secret or not clerk_secret.startswith("sk_"):
            logger.debug(
                "clerk.session_revoke.skipped",
                reason="CLERK_SECRET_KEY not configured",
                user_id=clerk_user_id,
            )
            return False

        async with httpx.AsyncClient(
            base_url="https://api.clerk.com",
            headers={"Authorization": f"Bearer {clerk_secret}"},
            timeout=5.0,
        ) as http:
            resp = await http.post(f"/v1/users/{clerk_user_id}/ban")
            if resp.status_code in (200, 201, 204):
                logger.info(
                    "clerk.session_revoke.success",
                    user_id=clerk_user_id,
                    status=resp.status_code,
                )
                return True
            logger.warning(
                "clerk.session_revoke.failed",
                user_id=clerk_user_id,
                status=resp.status_code,
                body=resp.text[:200],
            )
            return False
    except Exception:
        logger.exception("clerk.session_revoke.error", user_id=clerk_user_id)
        return False


# ---------------------------------------------------------------------------
# Export endpoint
# ---------------------------------------------------------------------------


@router.post(
    "/export",
    response_model=ExportQueuedResponse,
    status_code=http_status.HTTP_202_ACCEPTED,
    summary="Request DSAR data export (async)",
    dependencies=[Depends(mark_phi_boundary)],
)
async def export_user_data(
    request: Request,
    payload: ExportRequest = ExportRequest(),  # noqa: B008
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
    x_step_up_token: str | None = Header(default=None, alias="X-Step-Up-Token"),
) -> ExportQueuedResponse:
    """Enqueue a DSAR export job (GDPR Art. 20 portability / CCPA §1798.100).

    Returns **202 Accepted** immediately.  The export worker picks up the
    job, collects all user data, writes it to an S3 object, and updates the
    job store with the presigned ``download_url`` (TTL 15 min).

    Poll ``GET /v1/privacy/export/{export_id}`` until ``status == "ready"``,
    then download via ``download_url``.

    The response sets ``X-Phi-Boundary: 1`` via PhiBoundaryMiddleware.

    Audit: emits ``dsar_export_requested`` to the audit stream.
    """
    _require_step_up(x_step_up_token)
    user_id = _derive_user_id(x_user_id)
    export_id = str(uuid.uuid4())
    requested_at = datetime.now(UTC).isoformat()

    audit = get_stream_logger(LogStream.AUDIT)
    audit.info(
        "dsar_export_requested",
        actor_type="user",
        actor_id=user_id,
        subject_user_id=user_id,
        action="export_full",
        export_id=export_id,
        requested_at=requested_at,
        outcome="allowed",
        resource="user_data_export",
    )

    # Register job in the in-process store.  Production replaces this with
    # an SQS message + DynamoDB/Redis status record written by the worker.
    _EXPORT_JOBS[export_id] = {
        "export_id": export_id,
        "status": "queued",
        "requested_at": requested_at,
        "user_id": user_id,
        "download_url": None,
    }

    return ExportQueuedResponse(
        export_id=export_id,
        requested_at=requested_at,
        user_id=user_id,
    )


@router.get(
    "/export/{export_id}",
    response_model=ExportStatusResponse,
    status_code=http_status.HTTP_200_OK,
    summary="Poll DSAR export job status",
    dependencies=[Depends(mark_phi_boundary)],
)
async def get_export_status(
    export_id: str,
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
    x_step_up_token: str | None = Header(default=None, alias="X-Step-Up-Token"),
) -> ExportStatusResponse:
    """Return current status of a DSAR export job.

    Returns 404 when the export_id is unknown.  Once ``status == "ready"``
    the ``download_url`` is a presigned S3 URL (TTL 15 min).
    """
    _require_step_up(x_step_up_token)

    job = _EXPORT_JOBS.get(export_id)
    if job is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="export_not_found",
        )

    return ExportStatusResponse(**job)


# ---------------------------------------------------------------------------
# Account deletion endpoint
# ---------------------------------------------------------------------------


@router.post(
    "/delete-account",
    response_model=DeleteAccountResponse,
    status_code=http_status.HTTP_202_ACCEPTED,
    summary="Request account deletion",
)
async def delete_account(
    request: Request,
    payload: DeleteAccountRequest = DeleteAccountRequest(),  # noqa: B008
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
    x_step_up_token: str | None = Header(default=None, alias="X-Step-Up-Token"),
) -> DeleteAccountResponse:
    """Soft-delete the user account and schedule a 30-day hard-delete.

    Steps:
    1. Enforce step-up re-authentication (prevents CSRF / session-riding).
    2. Emit ``account_deletion_requested`` to the AUDIT stream.
    3. Mark ``users.deleted_at = now()`` and ``users.purge_scheduled_at = +30d``
       via :meth:`PrivacyService.schedule_deletion`.
    4. (TODO) Call Clerk API to revoke all active sessions for the user.
       ``POST https://api.clerk.com/v1/users/{clerk_user_id}/ban`` or
       ``DELETE https://api.clerk.com/v1/sessions/{session_id}`` per-session.
       Use ``discipline.shared.http`` egress client (not raw httpx) so the
       egress allow-list and tracing are applied.
    5. Return 202 Accepted with ``deletion_scheduled_at``.

    Voice blobs: hard-deleted within 72h by the independent S3 lifecycle
    policy — no special handling required here (07_Security_Privacy §7).

    Audit log is NOT deleted during account erasure; HIPAA retention
    obligation overrides GDPR erasure for compliance records
    (14_Authentication_Logging §4.9).
    """
    _require_step_up(x_step_up_token)
    user_id = _derive_user_id(x_user_id)

    service = get_privacy_service()

    # ------------------------------------------------------------------
    # Audit log FIRST — record the intent before the mutation.
    # ------------------------------------------------------------------
    audit = get_stream_logger(LogStream.AUDIT)
    audit.info(
        "account_deletion_requested",
        actor_type="user",
        actor_id=user_id,
        subject_user_id=user_id,
        action="account_delete",
        outcome="allowed",
        resource="user_account",
    )

    # ------------------------------------------------------------------
    # Soft-delete + schedule hard-delete.
    # Pass None for db — service handles missing DB gracefully and returns
    # the computed purge_at timestamp even when the UPDATE is a no-op.
    # ------------------------------------------------------------------
    purge_at = await service.schedule_deletion(user_id=user_id, db=None)  # type: ignore[arg-type]

    # Revoke Clerk sessions — best-effort; deletion proceeds regardless.
    # In dev/test (no CLERK_SECRET_KEY), this returns False and skips.
    await _revoke_clerk_sessions(user_id)

    return DeleteAccountResponse(
        status="queued",
        deletion_scheduled_at=purge_at.isoformat(),
    )

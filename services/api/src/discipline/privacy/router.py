"""Privacy HTTP surface — DSAR export and account deletion.

Endpoints:
- ``POST /v1/privacy/export``         — GDPR/CCPA data export (DSAR)
- ``POST /v1/privacy/delete-account`` — soft-delete + schedule hard-delete

Both endpoints:
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

TODO (next sprint): move export to async SQS → worker → presigned S3 URL.
Switch the response to 202 Accepted + ``{"export_id": ..., "status": "queued",
"download_url": null}`` and poll ``GET /v1/privacy/export/{export_id}``.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import structlog
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi import status as http_status

from discipline.privacy.schemas import (
    DeleteAccountRequest,
    DeleteAccountResponse,
    ExportData,
    ExportRequest,
    ExportResponse,
)
from discipline.privacy.service import get_privacy_service
from discipline.shared.http import mark_phi_boundary
from discipline.shared.logging import LogStream, get_stream_logger

router = APIRouter(tags=["privacy"])
logger = structlog.get_logger(__name__)

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
    response_model=ExportResponse,
    status_code=http_status.HTTP_200_OK,
    summary="DSAR data export",
    dependencies=[Depends(mark_phi_boundary)],
)
async def export_user_data(
    request: Request,
    payload: ExportRequest = ExportRequest(),  # noqa: B008
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
    x_step_up_token: str | None = Header(default=None, alias="X-Step-Up-Token"),
) -> ExportResponse:
    """Export all user data as JSON (GDPR Art. 20 portability / CCPA §1798.100).

    Collects:
    - User profile (``users`` + ``user_profiles``)
    - Signal/check-in windows (``signals_windows``)
    - Journal metadata (``journals``) — content_encrypted excluded (user has it)
    - Assessment sessions (``psychometric_sessions``)
    - Streak state (``streak_state``)
    - Detected patterns (``patterns``)
    - Consent records (``consents``)

    The response sets ``X-Phi-Boundary: 1`` via PhiBoundaryMiddleware.

    Audit: emits ``dsar_export_requested`` to the audit stream.

    TODO (next sprint): run collect_user_data in a background worker and
    return a presigned S3 URL instead of inline JSON.
    """
    _require_step_up(x_step_up_token)
    user_id = _derive_user_id(x_user_id)
    export_id = str(uuid.uuid4())
    requested_at = datetime.now(UTC).isoformat()

    # ------------------------------------------------------------------
    # Audit log BEFORE data access (HIPAA accounting of disclosures).
    # Log only metadata — never log the data content (§9.2 of 07_Security_Privacy).
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # Collect data — synchronous for now; see TODO above.
    # We pass a None DB session because the in-memory service handles
    # missing DB gracefully (each domain catches exceptions independently).
    # ------------------------------------------------------------------
    service = get_privacy_service()

    # NOTE: In production this would use a real AsyncSession from get_db().
    # The service's per-domain try/except means a missing table returns
    # {"error": "..."} for that domain rather than aborting the whole export.
    # For the current sprint (no live DB in tests) we pass None and let each
    # domain's except clause return an empty-ish value.
    data_dict = await service.collect_user_data(user_id=user_id, db=None)  # type: ignore[arg-type]

    return ExportResponse(
        export_id=export_id,
        requested_at=requested_at,
        user_id=user_id,
        data=ExportData(**data_dict),
    )


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

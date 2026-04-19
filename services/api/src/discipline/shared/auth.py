"""Auth dependencies shared across modules.

This module currently provides **one** dependency — :func:`require_admin` —
and is deliberately small.  The production auth flow is Clerk v6 + WebAuthn
per Docs/Technicals/14_Authentication_Logging.md; a proper role-claim check
against the session JWT will replace the shared-secret token scaffolded
here when the Clerk integration lands.

Until then, the admin surfaces (audit chain verification, future compliance
replay tools, bootstrap seeding) are gated by a single shared secret passed
in the ``X-Admin-Token`` request header.  This is **not production-grade**
auth — it is a test-harness gate that lets the endpoints ship and be
covered by tests ahead of the session JWT work.  The docstring on
:func:`require_admin` flags the replacement path explicitly so a future
reviewer doesn't mistake the scaffold for the target state.
"""

from __future__ import annotations

import hmac
import os

from fastapi import Header, HTTPException


# Dev fallback — present so local tests and container healthchecks don't
# have to set the env var.  In any environment where ``ADMIN_API_TOKEN``
# equals this value, admin endpoints are trivially bypassable; the deploy
# pipeline MUST reject this value in prod configs (see
# Docs/Technicals/08_Infrastructure_DevOps.md §config-gate).
_DEV_FALLBACK_TOKEN = "dev-admin-token"


def _admin_token() -> str:
    return os.environ.get("ADMIN_API_TOKEN", _DEV_FALLBACK_TOKEN)


def require_admin(
    x_admin_token: str | None = Header(default=None, alias="X-Admin-Token"),
) -> None:
    """FastAPI dependency — raise 403 unless ``X-Admin-Token`` matches.

    Uses ``hmac.compare_digest`` so the comparison runs in constant time
    with respect to the token value — probing the endpoint with different
    prefixes cannot leak the correct value via response-time differences.

    Production replacement path: replace the body of this function with
    a Clerk JWT parse + ``roles.includes("admin")`` check that mirrors
    the pattern used by the ``apps/web-clinician`` middleware.  The
    shape of the dependency (returning None, raising 403 on failure)
    is stable so callers don't change when the replacement lands.
    """
    if x_admin_token is None:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "auth.admin_required",
                "message": "X-Admin-Token header required",
            },
        )
    expected = _admin_token()
    if not hmac.compare_digest(x_admin_token, expected):
        raise HTTPException(
            status_code=403,
            detail={
                "code": "auth.admin_forbidden",
                "message": "invalid admin token",
            },
        )


__all__ = ["require_admin"]

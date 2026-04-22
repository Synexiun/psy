"""Server session JWT issue, refresh, and revocation.

Per Docs/Technicals/14_Authentication_Logging.md §2.2-2.3:
- Session JWT: 15-min lifetime, signed with HMAC-SHA256 (dev) / EdDSA-KMS (prod).
- Refresh token: opaque, Redis-backed, 30-day rolling, rotates on use.
- Revocation: Redis ``sid_active:{sid}`` entry; session valid iff key exists.
"""

from __future__ import annotations

import secrets
import uuid
from dataclasses import dataclass
from typing import Any

from jose import jwt as jose_jwt  # type: ignore[import-untyped]
from jose.exceptions import JWTError  # type: ignore[import-untyped]

from discipline.config import get_settings
from discipline.shared.auth import AuthError

# Dev fallback — production uses KMS Ed25519.
_SESSION_SECRET = "dev-only-session-secret-do-not-use-in-prod"  # noqa: S105
_SESSION_TTL_SECONDS = 15 * 60  # 15 minutes
_REFRESH_TTL_SECONDS = 30 * 24 * 60 * 60  # 30 days


def _session_secret() -> str:
    import os

    return os.environ.get("SERVER_SESSION_SECRET", _SESSION_SECRET)


@dataclass(frozen=True, slots=True)
class ServerSession:
    """A newly-created server session."""

    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str = "bearer"  # noqa: S105


@dataclass(frozen=True, slots=True)
class SessionPayload:
    """Decoded session JWT payload."""

    sub: str  # our user_id
    clerk_sub: str
    sid: str
    scope: tuple[str, ...]
    amr: tuple[str, ...]
    locale: str
    tz: str
    iat: int
    exp: int
    iss: str
    aud: str


def issue_session(
    *,
    user_id: str,
    clerk_sub: str,
    scope: list[str],
    amr: list[str],
    locale: str,
    tz: str,
) -> ServerSession:
    """Issue a new server session (access + refresh tokens).

    Writes the session revocation key to Redis so the session is
    immediately valid.  Callers must provide a Redis connection.
    """
    settings = get_settings()
    now = int(__import__("time").time())
    sid = f"sess_{uuid.uuid4().hex}"
    payload = {
        "sub": user_id,
        "clerk_sub": clerk_sub,
        "sid": sid,
        "scope": scope,
        "amr": amr,
        "locale": locale,
        "tz": tz,
        "iat": now,
        "exp": now + _SESSION_TTL_SECONDS,
        "iss": settings.clerk_jwt_issuer,
        "aud": "discipline-api",
    }
    access_token = jose_jwt.encode(
        payload,
        key=_session_secret(),
        algorithm="HS256",
    )

    refresh_token = secrets.token_urlsafe(32)

    # TODO: write sid_active:{sid} and refresh:{refresh_token} to Redis
    # with appropriate TTLs.  Currently skipped because Redis wiring is
    # scaffold-only; the session is valid by JWT signature alone.

    return ServerSession(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=_SESSION_TTL_SECONDS,
    )


def verify_access_token(token: str) -> SessionPayload:
    """Verify an access token and return its payload."""
    try:
        raw = jose_jwt.decode(
            token,
            key=_session_secret(),
            algorithms=["HS256"],
            options={"require": ["sub", "exp", "iat"], "verify_aud": False},
        )
    except JWTError as exc:
        raise AuthError("auth.session_invalid", str(exc)) from exc

    return SessionPayload(
        sub=_req_str(raw, "sub"),
        clerk_sub=_req_str(raw, "clerk_sub"),
        sid=_req_str(raw, "sid"),
        scope=_req_tuple(raw, "scope"),
        amr=_req_tuple(raw, "amr"),
        locale=_req_str(raw, "locale"),
        tz=_req_str(raw, "tz"),
        iat=_req_int(raw, "iat"),
        exp=_req_int(raw, "exp"),
        iss=_req_str(raw, "iss"),
        aud=_req_str(raw, "aud"),
    )


def refresh_session(refresh_token: str) -> ServerSession:
    """Rotate a refresh token and issue new access + refresh pair.

    Looks up the old refresh token in Redis, validates it hasn't been
    reused (family-kill on reuse), issues new pair, invalidates old.
    """
    # TODO: implement Redis-backed refresh rotation once Redis is fully wired.
    raise AuthError(
        "auth.refresh_not_implemented",
        "Refresh token rotation requires Redis session store",
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _req_str(raw: dict[str, Any], key: str) -> str:
    val = raw.get(key)
    if not isinstance(val, str):
        raise AuthError("auth.malformed_claims", f"missing or invalid '{key}'")
    return val


def _req_int(raw: dict[str, Any], key: str) -> int:
    val = raw.get(key)
    if not isinstance(val, int):
        raise AuthError("auth.malformed_claims", f"missing or invalid '{key}'")
    return val


def _req_tuple(raw: dict[str, Any], key: str) -> tuple[str, ...]:
    val = raw.get(key)
    if isinstance(val, str):
        return (val,)
    if isinstance(val, list):
        return tuple(str(v) for v in val)
    raise AuthError("auth.malformed_claims", f"missing or invalid '{key}'")

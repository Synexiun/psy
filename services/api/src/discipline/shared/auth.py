"""Auth dependencies shared across modules.

Production auth flow (Docs/Technicals/14_Authentication_Logging.md):

1. Client obtains Clerk session token (via Clerk SDK UI).
2. Client POSTs to ``/v1/auth/exchange`` with Clerk token.
3. Backend verifies Clerk token (JWKS), upserts user, issues our own
   server-signed session JWT (15-min lifetime).
4. All subsequent requests carry ``Authorization: Bearer <session_jwt>``.
5. Backend verifies session JWT locally — no Clerk round-trip on hot path.

This module provides:

- :class:`SessionClaims` — typed session JWT payload.
- :func:`verify_session_token` — local HMAC verification (dev fallback for
  KMS-Ed25519 in production).
- :func:`verify_clerk_token` — Clerk JWT verification (for exchange endpoint).
- :func:`require_auth` — FastAPI dependency that validates Bearer tokens.
- :func:`require_admin` — role gate; checks JWT ``scope`` first, then falls
  back to the legacy ``X-Admin-Token`` shared secret for local dev/tests.
"""

from __future__ import annotations

import hmac
import os
from dataclasses import dataclass
from typing import Any, cast

from fastapi import Header, HTTPException, Request
from jose import jwt as jose_jwt  # type: ignore[import-untyped]
from jose.exceptions import JWTError  # type: ignore[import-untyped]

from discipline.config import get_settings

# ---------------------------------------------------------------------------
# Dev / test bypass tokens — NEVER use in production.
# The deploy pipeline rejects these values (see 08_Infrastructure_DevOps). #
# ---------------------------------------------------------------------------
_DEV_FALLBACK_ADMIN_TOKEN = "dev-admin-token"  # noqa: S105
_DEV_FALLBACK_SESSION_SECRET = "dev-only-session-secret-do-not-use-in-prod"  # noqa: S105


def _admin_token() -> str:
    return os.environ.get("ADMIN_API_TOKEN", _DEV_FALLBACK_ADMIN_TOKEN)


def _session_secret() -> str:
    return os.environ.get(
        "SERVER_SESSION_SECRET",
        _DEV_FALLBACK_SESSION_SECRET,
    )


def _clerk_secret_key() -> str:
    return get_settings().clerk_secret_key


def _clerk_jwt_issuer() -> str:
    return get_settings().clerk_jwt_issuer


# ---------------------------------------------------------------------------
# Session claims
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class SessionClaims:
    """Our server-issued session JWT payload.

    Fields match the spec in 14_Authentication_Logging.md §2.2.
    No PHI is ever stored in claims.
    """

    sub: str  # our user_id
    clerk_sub: str  # Clerk's user id
    sid: str  # session id
    scope: tuple[str, ...]  # e.g. ("consumer",) or ("clinician",)
    amr: tuple[str, ...]  # auth methods: "pwd", "mfa_totp", "biometric", "sso"
    locale: str
    tz: str
    iat: int
    exp: int
    iss: str
    aud: str

    @property
    def user_id(self) -> str:
        return self.sub

    def has_scope(self, scope: str) -> bool:
        return scope in self.scope


# ---------------------------------------------------------------------------
# Token verification
# ---------------------------------------------------------------------------


class AuthError(Exception):
    """Base for auth failures.  Carries a detail dict for RFC 7807 responses."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)

    def as_detail(self) -> dict[str, str]:
        return {"code": self.code, "message": self.message}


def verify_session_token(token: str) -> SessionClaims:
    """Verify a server-issued session JWT and return typed claims.

    Uses HMAC-SHA256 with ``SERVER_SESSION_SECRET`` (dev fallback).
    Production target: EdDSA (Ed25519) via AWS KMS — the function signature
    is stable so the crypto backend can swap without caller changes.
    """
    try:
        payload = jose_jwt.decode(
            token,
            key=_session_secret(),
            algorithms=["HS256"],
            options={"require": ["sub", "exp", "iat"], "verify_aud": False},
        )
    except JWTError as exc:
        raise AuthError("auth.session_invalid", str(exc)) from exc

    return SessionClaims(
        sub=_require_str(payload, "sub"),
        clerk_sub=_require_str(payload, "clerk_sub"),
        sid=_require_str(payload, "sid"),
        scope=_require_tuple_str(payload, "scope"),
        amr=_require_tuple_str(payload, "amr"),
        locale=_require_str(payload, "locale"),
        tz=_require_str(payload, "tz"),
        iat=_require_int(payload, "iat"),
        exp=_require_int(payload, "exp"),
        iss=_require_str(payload, "iss"),
        aud=_require_str(payload, "aud"),
    )


def verify_clerk_token(token: str) -> dict[str, Any]:
    """Verify a Clerk-issued JWT (for ``/v1/auth/exchange``).

    Returns the raw Clerk payload so :mod:`identity.auth_exchange` can
    extract ``sub``, ``email``, etc. and issue our own session JWT.

    In production this verifies against Clerk's JWKS endpoint.  For unit
    tests, a test-mode bypass is provided so the exchange endpoint can be
    tested without live Clerk dependencies.
    """
    settings = get_settings()
    # Test-mode bypass: tokens prefixed "test_clerk_" verify locally with
    # the session secret so exchange tests don't need Clerk infra.
    # Format: ``test_clerk_<jwt>`` — the prefix is stripped before decode.
    _test_prefix = "test_clerk_"
    if token.startswith(_test_prefix):
        raw_jwt = token[len(_test_prefix):]
        try:
            return cast(
                "dict[str, Any]",
                jose_jwt.decode(
                    raw_jwt,
                    key=_session_secret(),
                    algorithms=["HS256"],
                    options={"require": ["sub", "exp"]},
                ),
            )
        except JWTError as exc:
            raise AuthError("auth.clerk_invalid", str(exc)) from exc

    # Production path: verify with Clerk secret.
    # NOTE: Clerk session tokens are verified against their JWKS, not the
    # secret key.  A full implementation uses ``PyJWKClient`` to fetch
    # ``https://<clerk-domain>/.well-known/jwks.json``.  This stub uses
    # the secret key as a local verifier placeholder for development.
    try:
        return cast(
            "dict[str, Any]",
            jose_jwt.decode(
                token,
                key=settings.clerk_secret_key,
                algorithms=["RS256"],
                issuer=settings.clerk_jwt_issuer,
                options={"require": ["sub", "exp"]},
            ),
        )
    except JWTError as exc:
        raise AuthError("auth.clerk_invalid", str(exc)) from exc


# ---------------------------------------------------------------------------
# FastAPI dependencies
# ---------------------------------------------------------------------------


def require_auth(
    request: Request,
    authorization: str | None = Header(default=None),
) -> SessionClaims:
    """FastAPI dependency — validate ``Authorization: Bearer <token>``.

    Returns :class:`SessionClaims` on success; raises 401 on missing,
    malformed, or invalid tokens.
    """
    if authorization is None:
        raise HTTPException(
            status_code=401,
            detail={"code": "auth.missing", "message": "Authorization header required"},
            headers={"WWW-Authenticate": "Bearer"},
        )

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=401,
            detail={"code": "auth.scheme", "message": "Expected Bearer token"},
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        claims = verify_session_token(token)
    except AuthError as exc:
        raise HTTPException(
            status_code=401,
            detail=exc.as_detail(),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    # Attach claims to request state so downstream deps / endpoints can
    # read ``request.state.user`` without re-parsing the token.
    request.state.user = claims
    return claims


def require_admin(
    request: Request,
    authorization: str | None = Header(default=None),
    x_admin_token: str | None = Header(default=None, alias="X-Admin-Token"),
) -> None:
    """FastAPI dependency — raise 403 unless caller has admin role.

    Resolution order:

    1. If ``Authorization: Bearer <jwt>`` is present, verify it as a session
       token and check that ``"admin"`` is in ``claims.scope``.
    2. Fall back to ``X-Admin-Token`` shared-secret comparison (dev/tests).

    The shared-secret path is **not production-grade** and exists only so
    admin surfaces can ship and be tested ahead of full Clerk integration.
    """
    # Attempt JWT path first.
    if authorization is not None:
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() == "bearer" and token:
            try:
                claims = verify_session_token(token)
            except AuthError:
                # Invalid JWT — do NOT fall through to shared secret;
                # an attacker probing JWTs shouldn't get a second gate.
                raise HTTPException(
                    status_code=403,
                    detail={
                        "code": "auth.admin_forbidden",
                        "message": "invalid session token",
                    },
                ) from None
            if claims.has_scope("admin"):
                request.state.user = claims
                return
            raise HTTPException(
                status_code=403,
                detail={
                    "code": "auth.admin_forbidden",
                    "message": "insufficient scope",
                },
            )

    # Fall back to shared-secret path.
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
            detail={"code": "auth.admin_forbidden", "message": "invalid admin token"},
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _require_str(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str):
        raise AuthError("auth.malformed_claims", f"missing or invalid '{key}'")
    return value


def _require_int(payload: dict[str, Any], key: str) -> int:
    value = payload.get(key)
    if not isinstance(value, int):
        raise AuthError("auth.malformed_claims", f"missing or invalid '{key}'")
    return value


def _require_tuple_str(payload: dict[str, Any], key: str) -> tuple[str, ...]:
    value = payload.get(key)
    if isinstance(value, str):
        return (value,)
    if isinstance(value, list):
        return tuple(str(v) for v in value)
    raise AuthError("auth.malformed_claims", f"missing or invalid '{key}'")


__all__ = [
    "AuthError",
    "SessionClaims",
    "require_admin",
    "require_auth",
    "verify_clerk_token",
    "verify_session_token",
]

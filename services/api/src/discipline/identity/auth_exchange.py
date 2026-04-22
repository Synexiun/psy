"""Clerk token exchange — ``POST /v1/auth/exchange``.

Per Docs/Technicals/14_Authentication_Logging.md §2.2:
1. Verify the Clerk JWT (via JWKS in prod; test bypass in dev).
2. Upsert the user in our database.
3. Issue a server-signed session JWT + refresh token.
4. Write session record to Redis.
5. Return tokens to the client.

This module intentionally does NOT call Clerk on the hot path after
exchange — all subsequent requests use our session JWT.
"""

from __future__ import annotations

from typing import Any

from discipline.identity.repository import get_user_repository
from discipline.identity.session import ServerSession, issue_session
from discipline.shared.auth import AuthError, verify_clerk_token


class ExchangeError(Exception):
    """Base for auth-exchange failures."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)

    def as_detail(self) -> dict[str, str]:
        return {"code": self.code, "message": self.message}


async def exchange_clerk_token(clerk_token: str) -> ServerSession:
    """Exchange a Clerk session token for a server session.

    Steps:
    1. Verify Clerk token.
    2. Upsert user via repository.
    3. Issue server session.
    4. Return session.
    """
    try:
        clerk_payload = verify_clerk_token(clerk_token)
    except AuthError as exc:
        raise ExchangeError("auth.exchange_invalid", exc.message) from exc

    clerk_sub = _extract_clerk_sub(clerk_payload)
    email = _extract_email(clerk_payload)
    locale = _extract_locale(clerk_payload)

    repo = get_user_repository()
    user = await repo.get_by_external_id(clerk_sub)
    if user is None:
        user = await repo.create(
            external_id=clerk_sub,
            email=email,
            locale=locale,
            timezone="UTC",
        )

    session = issue_session(
        user_id=user.user_id,
        clerk_sub=clerk_sub,
        scope=["consumer"],  # default scope; clinician/enterprise set later
        amr=["pwd"],  # default; enriched from Clerk session metadata
        locale=user.locale,
        tz=user.timezone,
    )

    return session


# ---------------------------------------------------------------------------
# Extractors
# ---------------------------------------------------------------------------


def _extract_clerk_sub(payload: dict[str, Any]) -> str:
    sub = payload.get("sub")
    if not isinstance(sub, str):
        raise ExchangeError("auth.exchange_malformed", "missing clerk sub")
    return sub


def _extract_email(payload: dict[str, Any]) -> str | None:
    # Clerk embeds email in the ``email_address`` claim.
    email = payload.get("email_address") or payload.get("email")
    return email if isinstance(email, str) else None


def _extract_locale(payload: dict[str, Any]) -> str:
    locale = payload.get("locale")
    return locale if isinstance(locale, str) else "en"


__all__ = [
    "ExchangeError",
    "exchange_clerk_token",
]

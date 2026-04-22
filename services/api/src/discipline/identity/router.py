"""Identity router — user profile, auth exchange, session management."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from discipline.identity.auth_exchange import ExchangeError, exchange_clerk_token

router = APIRouter(prefix="/me", tags=["identity"])


@router.get("")
async def current_user() -> dict[str, str]:
    """Stub — wire to UserService.get_current in the first real milestone."""
    return {"status": "not_implemented"}


@router.post("/auth/exchange")
async def auth_exchange(body: dict[str, str]) -> dict[str, str | int]:
    """Exchange a Clerk token for a server session JWT.

    Request body::

        {"clerk_token": "<clerk_session_jwt>"}

    Response::

        {
            "access_token": "<server_jwt>",
            "refresh_token": "<opaque_token>",
            "expires_in": 900,
            "token_type": "bearer"
        }
    """
    clerk_token = body.get("clerk_token")
    if not clerk_token:
        raise HTTPException(
            status_code=400,
            detail={"code": "auth.missing_clerk_token", "message": "clerk_token required"},
        )
    try:
        session = await exchange_clerk_token(clerk_token)
    except ExchangeError as exc:
        raise HTTPException(
            status_code=401,
            detail=exc.as_detail(),
        ) from exc
    return {
        "access_token": session.access_token,
        "refresh_token": session.refresh_token,
        "expires_in": session.expires_in,
        "token_type": session.token_type,
    }

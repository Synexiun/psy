"""Identity router — user profile, auth exchange, session management."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from discipline.identity.auth_exchange import ExchangeError, exchange_clerk_token
from discipline.identity.repository import get_user_repository
from discipline.identity.session_store import get_session_store
from discipline.shared.auth import AuthError

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


@router.post("/auth/refresh")
async def auth_refresh(body: dict[str, str]) -> dict[str, str | int]:
    """Rotate a refresh token and issue a new session pair.

    Request body::

        {"refresh_token": "<opaque_token>"}

    Response::

        {
            "access_token": "<new_server_jwt>",
            "refresh_token": "<new_opaque_token>",
            "expires_in": 900,
            "token_type": "bearer"
        }

    Errors:
    - 400 if refresh_token missing
    - 401 if token invalid, expired, already consumed, or session revoked
    """
    refresh_token = body.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=400,
            detail={"code": "auth.missing_refresh_token", "message": "refresh_token required"},
        )

    store = get_session_store()

    # Step 1: atomically consume the refresh token.
    result = store.consume_refresh(refresh_token)
    if result is None:
        raise HTTPException(
            status_code=401,
            detail={"code": "auth.refresh_invalid", "message": "Refresh token is invalid or already used"},
        )

    sid, family_id, stored_user_id = result

    # Step 2: verify the session is still active.
    if not store.is_active(sid):
        store.kill_family(family_id)
        raise HTTPException(
            status_code=401,
            detail={"code": "auth.session_revoked", "message": "Session has been revoked"},
        )

    # Step 3: revoke the old session before issuing the new one.
    store.revoke(sid)

    # Step 4: re-fetch full user context from DB to pick up current locale/tz.
    repo = get_user_repository()
    user = await repo.get_by_id(stored_user_id) if stored_user_id else None

    if user is None:
        raise HTTPException(
            status_code=401,
            detail={"code": "auth.user_not_found", "message": "User not found"},
        )

    # Step 5: issue new session (writes new sid_active + refresh to Redis).
    from discipline.identity.session import issue_session

    new_session = issue_session(
        user_id=user.user_id,
        clerk_sub=user.external_id,
        scope=["consumer"],
        amr=["pwd"],
        locale=user.locale,
        tz=user.timezone,
        store=store,
    )

    return {
        "access_token": new_session.access_token,
        "refresh_token": new_session.refresh_token,
        "expires_in": new_session.expires_in,
        "token_type": new_session.token_type,
    }


@router.post("/auth/logout")
async def auth_logout(body: dict[str, str]) -> dict[str, str]:
    """Revoke the current session.

    Request body::

        {"session_id": "<sid_from_jwt>"}

    The client should discard its tokens after calling this endpoint.
    """
    sid = body.get("session_id")
    if not sid:
        raise HTTPException(
            status_code=400,
            detail={"code": "auth.missing_session_id", "message": "session_id required"},
        )
    store = get_session_store()
    try:
        store.revoke(sid)
    except Exception:
        # Redis unavailable — accept the logout (token expires naturally).
        pass
    return {"status": "logged_out"}

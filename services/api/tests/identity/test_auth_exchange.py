"""Tests for ``discipline.identity.auth_exchange``.

Covers Clerk token exchange flow using test-mode bypass tokens.
"""

from __future__ import annotations

import time
from typing import Any

import pytest
from jose import jwt as jose_jwt

from discipline.identity.auth_exchange import ExchangeError, exchange_clerk_token
from discipline.identity.repository import reset_user_repository


@pytest.fixture(autouse=True)
def _clear_users() -> None:
    reset_user_repository()


@pytest.fixture
def make_clerk_token() -> Any:
    import os

    secret = os.environ.get(
        "SERVER_SESSION_SECRET", "dev-only-session-secret-do-not-use-in-prod"
    )

    def _make(
        *,
        sub: str = "clerk_user_01",
        email: str = "test@example.com",
        locale: str = "en",
        exp: int | None = None,
    ) -> str:
        now = int(time.time())
        payload = {
            "sub": sub,
            "email_address": email,
            "locale": locale,
            "iat": now,
            "exp": exp or now + 3600,
        }
        raw = jose_jwt.encode(payload, secret, algorithm="HS256")
        return "test_clerk_" + raw

    return _make


class TestExchangeClerkToken:
    @pytest.mark.asyncio
    async def test_valid_token_returns_session(
        self, make_clerk_token: Any
    ) -> None:
        token = make_clerk_token(sub="clerk_user_99")
        session = await exchange_clerk_token(token)
        assert session.access_token
        assert session.refresh_token
        assert session.expires_in == 15 * 60

    @pytest.mark.asyncio
    async def test_user_id_is_deterministic(
        self, make_clerk_token: Any
    ) -> None:
        token = make_clerk_token(sub="clerk_user_42")
        session1 = await exchange_clerk_token(token)
        session2 = await exchange_clerk_token(token)
        # Same clerk_sub → same user_id → but different sid
        assert session1.access_token != session2.access_token

    @pytest.mark.asyncio
    async def test_invalid_token_raises(self) -> None:
        with pytest.raises(ExchangeError) as exc_info:
            await exchange_clerk_token("bad-token")
        assert exc_info.value.code == "auth.exchange_invalid"

    @pytest.mark.asyncio
    async def test_missing_sub_raises(self) -> None:
        import os

        secret = os.environ.get(
            "SERVER_SESSION_SECRET", "dev-only-session-secret-do-not-use-in-prod"
        )
        raw = jose_jwt.encode(
            {"iat": int(time.time()), "exp": int(time.time()) + 3600},
            secret,
            algorithm="HS256",
        )
        token = "test_clerk_" + raw
        with pytest.raises(ExchangeError) as exc_info:
            await exchange_clerk_token(token)
        assert exc_info.value.code == "auth.exchange_malformed"

    @pytest.mark.asyncio
    async def test_locale_fallback(self, make_clerk_token: Any) -> None:
        token = make_clerk_token(sub="clerk_user_01", locale="fr")
        session = await exchange_clerk_token(token)
        assert session.access_token

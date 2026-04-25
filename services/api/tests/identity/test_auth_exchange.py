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
    async def test_locale_propagated(self, make_clerk_token: Any) -> None:
        token = make_clerk_token(sub="clerk_user_01", locale="fr")
        session = await exchange_clerk_token(token)
        assert session.access_token

    @pytest.mark.asyncio
    async def test_email_fallback_claim(self) -> None:
        """Payload with 'email' (not 'email_address') must still be accepted."""
        import os

        secret = os.environ.get(
            "SERVER_SESSION_SECRET", "dev-only-session-secret-do-not-use-in-prod"
        )
        now = int(time.time())
        raw = jose_jwt.encode(
            {"sub": "clerk_u_email_fallback", "email": "alt@example.com", "iat": now, "exp": now + 3600},
            secret,
            algorithm="HS256",
        )
        session = await exchange_clerk_token("test_clerk_" + raw)
        assert session.access_token

    @pytest.mark.asyncio
    async def test_missing_locale_defaults_to_en(self) -> None:
        """Token with no 'locale' claim must produce a session (locale defaults to en)."""
        import os

        secret = os.environ.get(
            "SERVER_SESSION_SECRET", "dev-only-session-secret-do-not-use-in-prod"
        )
        now = int(time.time())
        raw = jose_jwt.encode(
            {"sub": "clerk_u_noloc", "email_address": "x@x.com", "iat": now, "exp": now + 3600},
            secret,
            algorithm="HS256",
        )
        session = await exchange_clerk_token("test_clerk_" + raw)
        assert session.access_token

    @pytest.mark.asyncio
    async def test_new_user_created_on_first_exchange(self, make_clerk_token: Any) -> None:
        token = make_clerk_token(sub="brand_new_user_xyz")
        session = await exchange_clerk_token(token)
        assert session.access_token
        assert session.refresh_token


class TestExchangeError:
    def test_code_stored(self) -> None:
        from discipline.identity.auth_exchange import ExchangeError

        err = ExchangeError("auth.some_code", "Some message")
        assert err.code == "auth.some_code"

    def test_message_stored(self) -> None:
        from discipline.identity.auth_exchange import ExchangeError

        err = ExchangeError("code", "msg")
        assert err.message == "msg"

    def test_as_detail_returns_dict(self) -> None:
        from discipline.identity.auth_exchange import ExchangeError

        err = ExchangeError("auth.code", "detail msg")
        detail = err.as_detail()
        assert isinstance(detail, dict)

    def test_as_detail_code_key(self) -> None:
        from discipline.identity.auth_exchange import ExchangeError

        detail = ExchangeError("auth.c", "m").as_detail()
        assert detail["code"] == "auth.c"

    def test_as_detail_message_key(self) -> None:
        from discipline.identity.auth_exchange import ExchangeError

        detail = ExchangeError("code", "my message").as_detail()
        assert detail["message"] == "my message"

    def test_is_exception(self) -> None:
        from discipline.identity.auth_exchange import ExchangeError

        assert isinstance(ExchangeError("c", "m"), Exception)

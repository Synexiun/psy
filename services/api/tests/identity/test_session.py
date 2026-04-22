"""Tests for ``discipline.identity.session``.

Covers token issuance, verification, and payload shape.
"""

from __future__ import annotations

import time

import pytest

from discipline.identity.session import (
    ServerSession,
    issue_session,
    refresh_session,
    verify_access_token,
)
from discipline.shared.auth import AuthError


class TestIssueSession:
    def test_returns_server_session(self) -> None:
        session = issue_session(
            user_id="u_01",
            clerk_sub="clerk_u_01",
            scope=["consumer"],
            amr=["pwd"],
            locale="en",
            tz="UTC",
        )
        assert isinstance(session, ServerSession)
        assert session.token_type == "bearer"
        assert session.expires_in == 15 * 60
        assert session.access_token
        assert session.refresh_token


class TestVerifyAccessToken:
    def test_roundtrip(self) -> None:
        session = issue_session(
            user_id="u_42",
            clerk_sub="clerk_42",
            scope=["consumer", "clinician"],
            amr=["pwd", "mfa_totp"],
            locale="fr",
            tz="Europe/Paris",
        )
        payload = verify_access_token(session.access_token)
        assert payload.sub == "u_42"
        assert payload.clerk_sub == "clerk_42"
        assert payload.scope == ("consumer", "clinician")
        assert payload.amr == ("pwd", "mfa_totp")
        assert payload.locale == "fr"
        assert payload.tz == "Europe/Paris"
        assert payload.exp > payload.iat

    def test_invalid_token_raises(self) -> None:
        with pytest.raises(AuthError) as exc_info:
            verify_access_token("not-a-token")
        assert exc_info.value.code == "auth.session_invalid"

    def test_expired_token_raises(self) -> None:
        import os

        from jose import jwt as _jwt

        secret = os.environ.get(
            "SERVER_SESSION_SECRET", "dev-only-session-secret-do-not-use-in-prod"
        )
        expired = _jwt.encode(
            {
                "sub": "u_01",
                "clerk_sub": "c_01",
                "sid": "s_01",
                "scope": ["consumer"],
                "amr": ["pwd"],
                "locale": "en",
                "tz": "UTC",
                "iat": int(time.time()) - 3600,
                "exp": int(time.time()) - 1800,
                "iss": "test",
                "aud": "test",
            },
            secret,
            algorithm="HS256",
        )
        with pytest.raises(AuthError) as exc_info:
            verify_access_token(expired)
        assert "expired" in exc_info.value.message.lower() or "Signature" in exc_info.value.message


class TestRefreshSession:
    def test_raises_not_implemented(self) -> None:
        with pytest.raises(AuthError) as exc_info:
            refresh_session("some_token")
        assert exc_info.value.code == "auth.refresh_not_implemented"

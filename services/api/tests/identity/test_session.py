"""Tests for ``discipline.identity.session``.

Covers token issuance, verification, revocation checks, and refresh rotation.
"""

from __future__ import annotations

import time
from unittest.mock import MagicMock, patch

import pytest

from discipline.identity.session import (
    ServerSession,
    issue_session,
    refresh_session_with_context,
    verify_access_token,
)
from discipline.identity.session_store import SessionStore
from discipline.shared.auth import AuthError


def _mock_store(
    *,
    is_active: bool = True,
    consume_result: tuple[str, str, str] | None = ("sess_01", "fam_01", "u_01"),
) -> SessionStore:
    store = MagicMock(spec=SessionStore)
    store.is_active.return_value = is_active
    store.consume_refresh.return_value = consume_result
    return store


def _issue(store: SessionStore | None = None) -> ServerSession:
    return issue_session(
        user_id="u_01",
        clerk_sub="clerk_01",
        scope=["consumer"],
        amr=["pwd"],
        locale="en",
        tz="UTC",
        store=store,
    )


class TestIssueSession:
    def test_returns_server_session(self) -> None:
        store = _mock_store()
        session = _issue(store)
        assert isinstance(session, ServerSession)
        assert session.token_type == "bearer"
        assert session.expires_in == 15 * 60
        assert session.access_token
        assert session.refresh_token

    def test_activates_sid_in_redis(self) -> None:
        store = _mock_store()
        _issue(store)
        store.activate.assert_called_once()
        call_args = store.activate.call_args
        sid = call_args.args[0]
        assert sid.startswith("sess_")
        assert call_args.args[1] == "u_01"
        assert call_args.kwargs.get("ttl") == 15 * 60

    def test_stores_refresh_token_in_redis(self) -> None:
        store = _mock_store()
        session = _issue(store)
        store.store_refresh.assert_called_once()
        call_args = store.store_refresh.call_args
        assert call_args.args[0] == session.refresh_token
        # sid and family_id are positional
        assert call_args.args[1].startswith("sess_")
        assert call_args.args[2].startswith("fam_")

    def test_redis_failure_does_not_raise(self) -> None:
        store = MagicMock(spec=SessionStore)
        store.activate.side_effect = ConnectionError("Redis down")
        # Should not raise — degrades gracefully
        session = _issue(store)
        assert session.access_token


class TestVerifyAccessToken:
    def test_roundtrip_with_active_session(self) -> None:
        store = _mock_store(is_active=True)
        session = _issue(store)
        payload = verify_access_token(session.access_token, store=store)
        assert payload.sub == "u_01"
        assert payload.clerk_sub == "clerk_01"

    def test_revoked_session_raises(self) -> None:
        store = _mock_store(is_active=True)
        session = _issue(store)
        revoked_store = _mock_store(is_active=False)
        with pytest.raises(AuthError) as exc_info:
            verify_access_token(session.access_token, store=revoked_store)
        assert exc_info.value.code == "auth.session_revoked"

    def test_redis_failure_falls_back_to_jwt(self) -> None:
        store = _mock_store(is_active=True)
        session = _issue(store)
        failing_store = MagicMock(spec=SessionStore)
        failing_store.is_active.side_effect = ConnectionError("Redis down")
        # Should not raise — falls back to JWT signature check
        payload = verify_access_token(session.access_token, store=failing_store)
        assert payload.sub == "u_01"

    def test_check_revocation_false_skips_redis(self) -> None:
        store = _mock_store(is_active=True)
        session = _issue(store)
        never_called_store = MagicMock(spec=SessionStore)
        payload = verify_access_token(
            session.access_token,
            store=never_called_store,
            check_revocation=False,
        )
        never_called_store.is_active.assert_not_called()
        assert payload.sub == "u_01"

    def test_invalid_token_raises(self) -> None:
        with pytest.raises(AuthError) as exc_info:
            verify_access_token("not-a-token", check_revocation=False)
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
            verify_access_token(expired, check_revocation=False)
        assert "expired" in exc_info.value.message.lower() or "Signature" in exc_info.value.message

    def test_payload_fields_complete(self) -> None:
        store = _mock_store(is_active=True)
        session = issue_session(
            user_id="u_42",
            clerk_sub="clerk_42",
            scope=["consumer", "clinician"],
            amr=["pwd", "mfa_totp"],
            locale="fr",
            tz="Europe/Paris",
            store=store,
        )
        payload = verify_access_token(session.access_token, store=store)
        assert payload.sub == "u_42"
        assert payload.scope == ("consumer", "clinician")
        assert payload.amr == ("pwd", "mfa_totp")
        assert payload.locale == "fr"
        assert payload.tz == "Europe/Paris"
        assert payload.exp > payload.iat


class TestRefreshSessionWithContext:
    def test_issues_new_session_on_valid_refresh(self) -> None:
        issue_store = _mock_store(is_active=True)
        session = _issue(issue_store)

        refresh_store = _mock_store(
            is_active=True,
            consume_result=("sess_01", "fam_01", "u_01"),
        )
        new_session = refresh_session_with_context(
            session.refresh_token,
            user_id="u_01",
            clerk_sub="clerk_01",
            scope=["consumer"],
            amr=["pwd"],
            locale="en",
            tz="UTC",
            store=refresh_store,
        )
        assert isinstance(new_session, ServerSession)
        assert new_session.refresh_token != session.refresh_token

    def test_revokes_old_sid_on_refresh(self) -> None:
        refresh_store = _mock_store(
            is_active=True,
            consume_result=("sess_old", "fam_01", "u_01"),
        )
        refresh_session_with_context(
            "some_refresh_token",
            user_id="u_01",
            clerk_sub="clerk_01",
            scope=["consumer"],
            amr=["pwd"],
            locale="en",
            tz="UTC",
            store=refresh_store,
        )
        refresh_store.revoke.assert_called_once_with("sess_old")

    def test_invalid_refresh_token_raises(self) -> None:
        store = _mock_store(consume_result=None)
        with pytest.raises(AuthError) as exc_info:
            refresh_session_with_context(
                "bad_token",
                user_id="u_01",
                clerk_sub="clerk_01",
                scope=["consumer"],
                amr=["pwd"],
                locale="en",
                tz="UTC",
                store=store,
            )
        assert exc_info.value.code == "auth.refresh_invalid"

    def test_revoked_session_kills_family_and_raises(self) -> None:
        store = _mock_store(
            is_active=False,
            consume_result=("sess_01", "fam_compromised", "u_01"),
        )
        with pytest.raises(AuthError) as exc_info:
            refresh_session_with_context(
                "refresh_after_revoke",
                user_id="u_01",
                clerk_sub="clerk_01",
                scope=["consumer"],
                amr=["pwd"],
                locale="en",
                tz="UTC",
                store=store,
            )
        assert exc_info.value.code == "auth.session_revoked"
        store.kill_family.assert_called_once_with("fam_compromised")

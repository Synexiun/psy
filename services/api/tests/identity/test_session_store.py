"""Tests for ``discipline.identity.session_store``.

Uses mocked Redis so no live Redis connection is required.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from discipline.identity.session_store import SessionStore


@pytest.fixture
def store() -> SessionStore:
    mock_client = MagicMock()
    return SessionStore(mock_client)


class TestActivate:
    def test_sets_key_with_ttl(self, store: SessionStore) -> None:
        store.activate("sess_01", "user_01", ttl=900)
        store._client.setex.assert_called_once_with("sid_active:sess_01", 900, "user_01")


class TestIsActive:
    def test_true_when_key_exists(self, store: SessionStore) -> None:
        store._client.exists.return_value = 1
        assert store.is_active("sess_01") is True

    def test_false_when_key_missing(self, store: SessionStore) -> None:
        store._client.exists.return_value = 0
        assert store.is_active("sess_01") is False


class TestRevoke:
    def test_deletes_key(self, store: SessionStore) -> None:
        store.revoke("sess_01")
        store._client.delete.assert_called_once_with("sid_active:sess_01")


class TestStoreRefresh:
    def test_sets_refresh_token(self, store: SessionStore) -> None:
        store.store_refresh("rt_01", "sess_01", "family_01", "user_01")
        store._client.setex.assert_called_once()
        call_args = store._client.setex.call_args
        assert call_args.args[0] == "refresh:rt_01"
        assert call_args.args[2] == "sess_01:family_01:user_01"


class TestConsumeRefresh:
    def test_returns_sid_and_family(self, store: SessionStore) -> None:
        store._client.get.return_value = b"sess_01:family_01:user_01"
        store._client.delete.return_value = 1
        result = store.consume_refresh("rt_01")
        assert result == ("sess_01", "family_01", "user_01")

    def test_returns_none_on_missing_token(self, store: SessionStore) -> None:
        store._client.get.return_value = None
        assert store.consume_refresh("rt_01") is None

    def test_returns_none_on_replay(self, store: SessionStore) -> None:
        store._client.get.return_value = b"sess_01:family_01:user_01"
        store._client.delete.return_value = 0  # already consumed
        assert store.consume_refresh("rt_01") is None


class TestKillFamily:
    def test_deletes_matching_tokens(self, store: SessionStore) -> None:
        store._client.scan_iter.return_value = [b"refresh:rt_a", b"refresh:rt_b"]
        store._client.get.side_effect = [b"sid_a:family_x", b"sid_b:family_x"]
        count = store.kill_family("family_x")
        assert count == 2

    def test_skips_non_matching(self, store: SessionStore) -> None:
        store._client.scan_iter.return_value = [b"refresh:rt_a"]
        store._client.get.return_value = b"sid_a:family_y"
        count = store.kill_family("family_x")
        assert count == 0

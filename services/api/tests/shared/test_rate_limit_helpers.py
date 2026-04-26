"""Unit tests for _key_func() in discipline.shared.middleware.rate_limit.

_key_func(request) → str
  Preference chain for rate-limit bucket key:
  1. request.state.user_id (auth middleware sets this)
  2. request.state.clerk_payload["sub"] (JWT sub claim cached on state)
  3. get_remote_address(request) → remote IP (unauthenticated fallback)

  Contracts:
  - If user_id is present, it wins regardless of clerk_payload or IP.
  - If user_id is absent/None, sub from clerk_payload is used.
  - If neither is present, falls back to remote IP via slowapi's
    get_remote_address helper.
  - The same user with different session tokens still maps to the same key
    (user_id is stable across token cycles).

Uses MagicMock to simulate Starlette Request state without a running server.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from discipline.shared.middleware.rate_limit import _key_func


def _request(
    user_id: str | None = None,
    clerk_payload: dict | None = None,
    client_host: str = "1.2.3.4",
) -> MagicMock:
    req = MagicMock()
    state = MagicMock()
    # getattr(state, "user_id", None) must return user_id
    type(state).user_id = property(lambda self: user_id)  # type: ignore[assignment]
    type(state).clerk_payload = property(lambda self: clerk_payload)  # type: ignore[assignment]
    req.state = state
    req.client = MagicMock()
    req.client.host = client_host
    req.headers = {}
    return req


class TestKeyFuncPreferenceChain:
    def test_user_id_wins_over_all(self) -> None:
        req = _request(
            user_id="user-123",
            clerk_payload={"sub": "clerk_sub_456"},
            client_host="1.2.3.4",
        )
        assert _key_func(req) == "user-123"

    def test_user_id_wins_over_ip_alone(self) -> None:
        req = _request(user_id="user-abc", client_host="10.0.0.1")
        assert _key_func(req) == "user-abc"

    def test_clerk_sub_used_when_no_user_id(self) -> None:
        req = _request(user_id=None, clerk_payload={"sub": "clerk_sub_999"})
        assert _key_func(req) == "clerk_sub_999"

    def test_remote_ip_fallback_when_no_auth(self) -> None:
        req = _request(user_id=None, clerk_payload=None, client_host="5.6.7.8")
        with patch(
            "discipline.shared.middleware.rate_limit.get_remote_address",
            return_value="5.6.7.8",
        ):
            result = _key_func(req)
        assert result == "5.6.7.8"

    def test_same_user_id_across_different_requests(self) -> None:
        req1 = _request(user_id="user-stable", clerk_payload={"sub": "token-a"})
        req2 = _request(user_id="user-stable", clerk_payload={"sub": "token-b"})
        assert _key_func(req1) == _key_func(req2)

    def test_none_user_id_falls_through_to_sub(self) -> None:
        # Explicit None must not be used as the key
        req = _request(user_id=None, clerk_payload={"sub": "fallback-sub"})
        result = _key_func(req)
        assert result == "fallback-sub"
        assert result != "None"

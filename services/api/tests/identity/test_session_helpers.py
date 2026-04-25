"""Unit tests for _req_str(), _req_int(), and _req_tuple() pure helpers
in discipline.identity.session.

These three functions validate and coerce raw JWT payload dicts before the
server session is assembled.  They share a common contract:

- If the value is present and has the expected type, return it.
- If it is missing or the wrong type, raise AuthError("auth.malformed_claims", …).

_req_tuple additionally handles JWT claim polymorphism:
- A bare string is wrapped in a 1-element tuple (OIDC allows single-value claims
  as either a string or a 1-element array).
- A list is coerced element-wise to a tuple of strings.
- Anything else raises AuthError.
"""

from __future__ import annotations

import pytest

from discipline.identity.session import _req_int, _req_str, _req_tuple
from discipline.shared.auth import AuthError


# ---------------------------------------------------------------------------
# _req_str
# ---------------------------------------------------------------------------


class TestReqStr:
    def test_returns_string_value(self) -> None:
        assert _req_str({"k": "hello"}, "k") == "hello"

    def test_returns_empty_string(self) -> None:
        assert _req_str({"k": ""}, "k") == ""

    def test_missing_key_raises_auth_error(self) -> None:
        with pytest.raises(AuthError):
            _req_str({}, "k")

    def test_none_value_raises_auth_error(self) -> None:
        with pytest.raises(AuthError):
            _req_str({"k": None}, "k")

    def test_int_value_raises_auth_error(self) -> None:
        with pytest.raises(AuthError):
            _req_str({"k": 42}, "k")

    def test_list_value_raises_auth_error(self) -> None:
        with pytest.raises(AuthError):
            _req_str({"k": ["a", "b"]}, "k")

    def test_error_names_missing_key(self) -> None:
        with pytest.raises(AuthError, match="sub"):
            _req_str({}, "sub")

    def test_error_code_is_malformed_claims(self) -> None:
        try:
            _req_str({}, "sub")
        except AuthError as exc:
            assert "malformed_claims" in str(exc)


# ---------------------------------------------------------------------------
# _req_int
# ---------------------------------------------------------------------------


class TestReqInt:
    def test_returns_int_value(self) -> None:
        assert _req_int({"exp": 9999}, "exp") == 9999

    def test_returns_zero(self) -> None:
        assert _req_int({"n": 0}, "n") == 0

    def test_negative_int_accepted(self) -> None:
        assert _req_int({"n": -1}, "n") == -1

    def test_missing_key_raises_auth_error(self) -> None:
        with pytest.raises(AuthError):
            _req_int({}, "exp")

    def test_none_value_raises_auth_error(self) -> None:
        with pytest.raises(AuthError):
            _req_int({"exp": None}, "exp")

    def test_string_value_raises_auth_error(self) -> None:
        with pytest.raises(AuthError):
            _req_int({"exp": "1234"}, "exp")

    def test_float_value_raises_auth_error(self) -> None:
        # Floats are not ints — JWT specs use integer timestamps
        with pytest.raises(AuthError):
            _req_int({"exp": 1234.0}, "exp")

    def test_error_names_missing_key(self) -> None:
        with pytest.raises(AuthError, match="exp"):
            _req_int({}, "exp")


# ---------------------------------------------------------------------------
# _req_tuple — string branch (OIDC single-value claim as bare string)
# ---------------------------------------------------------------------------


class TestReqTupleStringBranch:
    def test_string_value_wrapped_in_tuple(self) -> None:
        result = _req_tuple({"aud": "client_abc"}, "aud")
        assert result == ("client_abc",)

    def test_result_is_a_tuple_not_a_list(self) -> None:
        result = _req_tuple({"aud": "x"}, "aud")
        assert isinstance(result, tuple)

    def test_empty_string_wrapped_in_tuple(self) -> None:
        result = _req_tuple({"roles": ""}, "roles")
        assert result == ("",)


# ---------------------------------------------------------------------------
# _req_tuple — list branch (standard multi-value claim)
# ---------------------------------------------------------------------------


class TestReqTupleListBranch:
    def test_list_converted_to_tuple(self) -> None:
        result = _req_tuple({"roles": ["admin", "clinician"]}, "roles")
        assert result == ("admin", "clinician")

    def test_single_element_list(self) -> None:
        result = _req_tuple({"roles": ["user"]}, "roles")
        assert result == ("user",)

    def test_empty_list_produces_empty_tuple(self) -> None:
        result = _req_tuple({"roles": []}, "roles")
        assert result == ()

    def test_list_elements_coerced_to_str(self) -> None:
        # JWT list entries are always strings in practice; coercion is defensive
        result = _req_tuple({"ids": [1, 2, 3]}, "ids")
        assert result == ("1", "2", "3")

    def test_order_preserved(self) -> None:
        roles = ["z", "a", "m"]
        result = _req_tuple({"roles": roles}, "roles")
        assert list(result) == roles


# ---------------------------------------------------------------------------
# _req_tuple — error branch
# ---------------------------------------------------------------------------


class TestReqTupleErrorBranch:
    def test_missing_key_raises_auth_error(self) -> None:
        with pytest.raises(AuthError):
            _req_tuple({}, "roles")

    def test_none_value_raises_auth_error(self) -> None:
        with pytest.raises(AuthError):
            _req_tuple({"roles": None}, "roles")

    def test_int_value_raises_auth_error(self) -> None:
        with pytest.raises(AuthError):
            _req_tuple({"roles": 42}, "roles")

    def test_dict_value_raises_auth_error(self) -> None:
        with pytest.raises(AuthError):
            _req_tuple({"roles": {"key": "val"}}, "roles")

    def test_error_names_missing_key(self) -> None:
        with pytest.raises(AuthError, match="roles"):
            _req_tuple({}, "roles")

    def test_error_code_is_malformed_claims(self) -> None:
        try:
            _req_tuple({}, "roles")
        except AuthError as exc:
            assert "malformed_claims" in str(exc)

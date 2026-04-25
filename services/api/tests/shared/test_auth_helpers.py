"""Unit tests for _require_str(), _require_int(), and _require_tuple_str() pure
helpers in discipline.shared.auth.

These helpers parse a raw JWT payload dict before assembling a SessionClaims
object.  They share this contract:
  - Present + correct type → return value
  - Missing or wrong type → raise AuthError("auth.malformed_claims", …)

Note on _require_int vs identity.session._req_int:
  _require_int has NO explicit bool guard (unlike identity.session._req_int).
  isinstance(True, int) is True in Python, so True/False are accepted as
  integers here.  This is intentional — the shared.auth module uses isinstance
  checks only for the broad type, not the bool subtype.

_require_tuple_str handles OIDC polymorphism:
  - bare str → 1-element tuple
  - list → tuple of str (elements coerced)
  - anything else → AuthError
"""

from __future__ import annotations

import pytest

from discipline.shared.auth import AuthError, _require_int, _require_str, _require_tuple_str


# ---------------------------------------------------------------------------
# _require_str
# ---------------------------------------------------------------------------


class TestRequireStr:
    def test_returns_string_value(self) -> None:
        assert _require_str({"k": "hello"}, "k") == "hello"

    def test_returns_empty_string(self) -> None:
        assert _require_str({"k": ""}, "k") == ""

    def test_missing_key_raises_auth_error(self) -> None:
        with pytest.raises(AuthError):
            _require_str({}, "k")

    def test_none_value_raises(self) -> None:
        with pytest.raises(AuthError):
            _require_str({"k": None}, "k")

    def test_int_value_raises(self) -> None:
        with pytest.raises(AuthError):
            _require_str({"k": 42}, "k")

    def test_list_value_raises(self) -> None:
        with pytest.raises(AuthError):
            _require_str({"k": ["a"]}, "k")

    def test_error_code_is_malformed_claims(self) -> None:
        try:
            _require_str({}, "sub")
        except AuthError as exc:
            assert "malformed_claims" in str(exc)

    def test_error_mentions_key(self) -> None:
        with pytest.raises(AuthError, match="sub"):
            _require_str({}, "sub")


# ---------------------------------------------------------------------------
# _require_int — note: no bool guard unlike identity.session._req_int
# ---------------------------------------------------------------------------


class TestRequireInt:
    def test_returns_int_value(self) -> None:
        assert _require_int({"exp": 9999}, "exp") == 9999

    def test_returns_zero(self) -> None:
        assert _require_int({"n": 0}, "n") == 0

    def test_negative_int_accepted(self) -> None:
        assert _require_int({"n": -1}, "n") == -1

    def test_missing_key_raises(self) -> None:
        with pytest.raises(AuthError):
            _require_int({}, "exp")

    def test_none_raises(self) -> None:
        with pytest.raises(AuthError):
            _require_int({"exp": None}, "exp")

    def test_string_raises(self) -> None:
        with pytest.raises(AuthError):
            _require_int({"exp": "1234"}, "exp")

    def test_float_raises(self) -> None:
        with pytest.raises(AuthError):
            _require_int({"exp": 1234.0}, "exp")

    def test_error_code_is_malformed_claims(self) -> None:
        try:
            _require_int({}, "exp")
        except AuthError as exc:
            assert "malformed_claims" in str(exc)

    def test_error_mentions_key(self) -> None:
        with pytest.raises(AuthError, match="exp"):
            _require_int({}, "exp")


# ---------------------------------------------------------------------------
# _require_tuple_str — string branch
# ---------------------------------------------------------------------------


class TestRequireTupleStrStringBranch:
    def test_string_wrapped_in_tuple(self) -> None:
        result = _require_tuple_str({"aud": "client_abc"}, "aud")
        assert result == ("client_abc",)

    def test_result_is_tuple(self) -> None:
        result = _require_tuple_str({"aud": "x"}, "aud")
        assert isinstance(result, tuple)

    def test_empty_string_wrapped(self) -> None:
        result = _require_tuple_str({"roles": ""}, "roles")
        assert result == ("",)


# ---------------------------------------------------------------------------
# _require_tuple_str — list branch
# ---------------------------------------------------------------------------


class TestRequireTupleStrListBranch:
    def test_list_converted_to_tuple(self) -> None:
        result = _require_tuple_str({"roles": ["admin", "clinician"]}, "roles")
        assert result == ("admin", "clinician")

    def test_single_element_list(self) -> None:
        result = _require_tuple_str({"roles": ["user"]}, "roles")
        assert result == ("user",)

    def test_empty_list_produces_empty_tuple(self) -> None:
        result = _require_tuple_str({"roles": []}, "roles")
        assert result == ()

    def test_non_string_list_elements_coerced(self) -> None:
        result = _require_tuple_str({"ids": [1, 2, 3]}, "ids")
        assert result == ("1", "2", "3")

    def test_order_preserved(self) -> None:
        roles = ["z", "a", "m"]
        result = _require_tuple_str({"roles": roles}, "roles")
        assert list(result) == roles


# ---------------------------------------------------------------------------
# _require_tuple_str — error branch
# ---------------------------------------------------------------------------


class TestRequireTupleStrErrorBranch:
    def test_missing_key_raises(self) -> None:
        with pytest.raises(AuthError):
            _require_tuple_str({}, "roles")

    def test_none_raises(self) -> None:
        with pytest.raises(AuthError):
            _require_tuple_str({"roles": None}, "roles")

    def test_int_raises(self) -> None:
        with pytest.raises(AuthError):
            _require_tuple_str({"roles": 42}, "roles")

    def test_dict_raises(self) -> None:
        with pytest.raises(AuthError):
            _require_tuple_str({"roles": {"key": "val"}}, "roles")

    def test_error_mentions_key(self) -> None:
        with pytest.raises(AuthError, match="roles"):
            _require_tuple_str({}, "roles")

    def test_error_code_is_malformed_claims(self) -> None:
        try:
            _require_tuple_str({}, "roles")
        except AuthError as exc:
            assert "malformed_claims" in str(exc)

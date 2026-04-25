"""Unit tests for _extract_clerk_sub(), _extract_email(), and
_extract_locale() pure helpers in discipline.identity.auth_exchange.

These functions pull specific claims out of a raw Clerk JWT payload dict.

_extract_clerk_sub(payload) → str
  Requires "sub" to be a non-empty string; raises ExchangeError otherwise.

_extract_email(payload) → str | None
  Prefers "email_address" (Clerk's primary claim); falls back to "email".
  Returns None when neither is a string (not a hard failure — some users have
  no email on their Clerk account).

_extract_locale(payload) → str
  Returns payload["locale"] if it's a string; defaults to "en" when absent
  or wrong type.  This default is load-bearing: the app must always have a
  valid locale even for users who never set one.
"""

from __future__ import annotations

import pytest

from discipline.identity.auth_exchange import (
    ExchangeError,
    _extract_clerk_sub,
    _extract_email,
    _extract_locale,
)


# ---------------------------------------------------------------------------
# _extract_clerk_sub
# ---------------------------------------------------------------------------


class TestExtractClerkSub:
    def test_returns_sub_when_present(self) -> None:
        assert _extract_clerk_sub({"sub": "user_abc123"}) == "user_abc123"

    def test_missing_sub_raises_exchange_error(self) -> None:
        with pytest.raises(ExchangeError):
            _extract_clerk_sub({})

    def test_none_sub_raises_exchange_error(self) -> None:
        with pytest.raises(ExchangeError):
            _extract_clerk_sub({"sub": None})

    def test_int_sub_raises_exchange_error(self) -> None:
        with pytest.raises(ExchangeError):
            _extract_clerk_sub({"sub": 42})

    def test_list_sub_raises_exchange_error(self) -> None:
        with pytest.raises(ExchangeError):
            _extract_clerk_sub({"sub": ["user_abc"]})

    def test_error_code_contains_exchange_malformed(self) -> None:
        try:
            _extract_clerk_sub({})
        except ExchangeError as exc:
            assert "exchange_malformed" in str(exc)

    def test_error_message_mentions_clerk_sub(self) -> None:
        with pytest.raises(ExchangeError, match="sub"):
            _extract_clerk_sub({})


# ---------------------------------------------------------------------------
# _extract_email — primary claim "email_address" (Clerk standard)
# ---------------------------------------------------------------------------


class TestExtractEmailPrimaryClaim:
    def test_returns_email_address_when_present(self) -> None:
        result = _extract_email({"email_address": "alice@example.com"})
        assert result == "alice@example.com"

    def test_email_address_takes_priority_over_email(self) -> None:
        result = _extract_email(
            {"email_address": "primary@example.com", "email": "secondary@example.com"}
        )
        assert result == "primary@example.com"


# ---------------------------------------------------------------------------
# _extract_email — fallback claim "email"
# ---------------------------------------------------------------------------


class TestExtractEmailFallbackClaim:
    def test_falls_back_to_email_when_email_address_absent(self) -> None:
        result = _extract_email({"email": "fallback@example.com"})
        assert result == "fallback@example.com"

    def test_falls_back_to_email_when_email_address_is_none(self) -> None:
        result = _extract_email({"email_address": None, "email": "fb@example.com"})
        assert result == "fb@example.com"

    def test_falls_back_to_email_when_email_address_is_empty_string(self) -> None:
        # Empty string is falsy — the `or` short-circuits to email
        result = _extract_email({"email_address": "", "email": "fb@example.com"})
        assert result == "fb@example.com"


# ---------------------------------------------------------------------------
# _extract_email — None return (no email available)
# ---------------------------------------------------------------------------


class TestExtractEmailNoneReturn:
    def test_returns_none_when_both_claims_absent(self) -> None:
        assert _extract_email({}) is None

    def test_returns_none_when_email_is_int(self) -> None:
        assert _extract_email({"email": 12345}) is None

    def test_returns_none_when_email_is_none(self) -> None:
        assert _extract_email({"email_address": None, "email": None}) is None

    def test_returns_none_for_empty_payload(self) -> None:
        assert _extract_email({}) is None


# ---------------------------------------------------------------------------
# _extract_locale
# ---------------------------------------------------------------------------


class TestExtractLocale:
    def test_returns_locale_when_present(self) -> None:
        assert _extract_locale({"locale": "fr"}) == "fr"

    def test_returns_ar_locale(self) -> None:
        assert _extract_locale({"locale": "ar"}) == "ar"

    def test_returns_fa_locale(self) -> None:
        assert _extract_locale({"locale": "fa"}) == "fa"

    def test_defaults_to_en_when_absent(self) -> None:
        assert _extract_locale({}) == "en"

    def test_defaults_to_en_when_locale_is_none(self) -> None:
        assert _extract_locale({"locale": None}) == "en"

    def test_defaults_to_en_when_locale_is_int(self) -> None:
        assert _extract_locale({"locale": 42}) == "en"

    def test_defaults_to_en_when_locale_is_list(self) -> None:
        assert _extract_locale({"locale": ["en"]}) == "en"

    def test_default_is_en_not_empty_string(self) -> None:
        # "en" default is load-bearing — empty string would break locale routing
        result = _extract_locale({})
        assert result == "en"
        assert len(result) > 0

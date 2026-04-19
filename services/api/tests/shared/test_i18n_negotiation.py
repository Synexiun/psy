"""Locale-negotiation tests.

Contract (Docs/Technicals/15_Internationalization.md §Locale negotiation):

1. Authenticated user's stored locale wins if it's one of the supported set.
2. Otherwise: best q-weighted match from ``Accept-Language``, primary-subtag only.
3. Fall back to English.
"""

from __future__ import annotations

import pytest

from discipline.shared.i18n.negotiation import (
    DEFAULT_LOCALE,
    RTL_LOCALES,
    SUPPORTED_LOCALES,
    is_rtl,
    negotiate_locale,
)


# ---- Supported-set invariants ----------------------------------------------


def test_supported_locales_are_en_fr_ar_fa() -> None:
    assert SUPPORTED_LOCALES == ("en", "fr", "ar", "fa")


def test_default_locale_is_english() -> None:
    assert DEFAULT_LOCALE == "en"


def test_rtl_locales_are_ar_and_fa_only() -> None:
    assert RTL_LOCALES == frozenset({"ar", "fa"})


@pytest.mark.parametrize(("locale", "expected"), [("en", False), ("fr", False), ("ar", True), ("fa", True)])
def test_is_rtl(locale: str, expected: bool) -> None:
    assert is_rtl(locale) is expected  # type: ignore[arg-type]


# ---- Priority 1: user preference wins --------------------------------------


def test_user_preference_beats_accept_language() -> None:
    locale = negotiate_locale(user_locale="fr", accept_language="en;q=0.9,ar;q=0.8")
    assert locale == "fr"


def test_user_preference_primary_subtag_only() -> None:
    """fr-CA collapses to fr at this layer."""
    locale = negotiate_locale(user_locale="fr-CA", accept_language=None)
    assert locale == "fr"


def test_unsupported_user_preference_falls_through() -> None:
    locale = negotiate_locale(user_locale="de", accept_language="ar")
    assert locale == "ar"


# ---- Priority 2: Accept-Language q-weighted match --------------------------


def test_accept_language_q_weight_picks_highest() -> None:
    locale = negotiate_locale(None, "en;q=0.3,fa;q=0.9,fr;q=0.6")
    assert locale == "fa"


def test_accept_language_primary_subtag_matches() -> None:
    locale = negotiate_locale(None, "ar-SA")
    assert locale == "ar"


def test_accept_language_no_supported_match_falls_back() -> None:
    locale = negotiate_locale(None, "de,es;q=0.8,it;q=0.5")
    assert locale == DEFAULT_LOCALE


def test_accept_language_malformed_q_treated_as_zero() -> None:
    """A malformed q= weight is treated as 0 (lowest priority) but the tag
    is still considered — downstream of a well-formed competitor."""
    locale = negotiate_locale(None, "fa;q=xyz,fr;q=0.9")
    assert locale == "fr"


# ---- Priority 3: default fallback ------------------------------------------


def test_both_inputs_missing_returns_default() -> None:
    assert negotiate_locale(None, None) == "en"


def test_empty_accept_language_returns_default() -> None:
    assert negotiate_locale(None, "") == "en"


# ---- Property-style checks -------------------------------------------------


def test_result_is_always_in_supported_set() -> None:
    """The negotiator must never return a tag outside the supported set —
    downstream code uses this as a ``Literal`` narrowing anchor."""
    cases = [
        (None, None),
        ("de", None),
        ("fr", "ar"),
        (None, "zh-CN,en;q=0.5"),
        (None, "fa-IR"),
        ("", ""),
    ]
    for user, accept in cases:
        assert negotiate_locale(user, accept) in SUPPORTED_LOCALES

"""Tests for discipline.shared.i18n.catalog — server-side message catalog.

The catalog provides translated copy for server-generated content (emails,
push notifications, PDF labels).  It is intentionally smaller than the
client-side i18n-catalog package.

Covers:
- get_message: returns correct string for valid key/locale pairs
- get_message: falls back to English for an unsupported locale
- get_message: returns the key itself when the key is absent in all locales
- get_message: en locale is always present and complete
- get_message: safety T4 headline is present in all 4 locales
- All 4 locales (en, fr, ar, fa) have the same set of keys
"""

from __future__ import annotations

import pytest

from discipline.shared.i18n.catalog import get_message


# ---------------------------------------------------------------------------
# Valid lookups
# ---------------------------------------------------------------------------


class TestGetMessage:
    def test_en_email_reset_subject(self) -> None:
        result = get_message("email.reset.subject", "en")
        assert "Discipline OS" in result

    def test_fr_email_reset_subject(self) -> None:
        result = get_message("email.reset.subject", "fr")
        assert len(result) > 0
        assert result != "email.reset.subject"

    def test_ar_push_checkin_title(self) -> None:
        result = get_message("push.check_in.title", "ar")
        assert len(result) > 0
        assert result != "push.check_in.title"

    def test_fa_pdf_report_title(self) -> None:
        result = get_message("pdf.report.title", "fa")
        assert len(result) > 0
        assert result != "pdf.report.title"

    def test_safety_t4_headline_en(self) -> None:
        """T4 safety headline must be non-empty for every locale (safety-critical copy)."""
        result = get_message("safety.t4.headline", "en")
        assert len(result) > 0
        assert result != "safety.t4.headline"

    def test_safety_t4_headline_fr(self) -> None:
        result = get_message("safety.t4.headline", "fr")
        assert len(result) > 0
        assert result != "safety.t4.headline"

    def test_safety_t4_headline_ar(self) -> None:
        result = get_message("safety.t4.headline", "ar")
        assert len(result) > 0
        assert result != "safety.t4.headline"

    def test_safety_t4_headline_fa(self) -> None:
        result = get_message("safety.t4.headline", "fa")
        assert len(result) > 0
        assert result != "safety.t4.headline"


# ---------------------------------------------------------------------------
# Fallback to English for unsupported locale
# ---------------------------------------------------------------------------


class TestLocaleCodeFallback:
    def test_falls_back_to_en_for_unknown_locale(self) -> None:
        """An unsupported locale should fall back to English, not raise."""
        result = get_message("email.reset.subject", "de")  # type: ignore[arg-type]
        en_result = get_message("email.reset.subject", "en")
        assert result == en_result

    def test_does_not_raise_for_unknown_locale(self) -> None:
        try:
            get_message("push.check_in.title", "zh")  # type: ignore[arg-type]
        except Exception:  # noqa: BLE001
            pytest.fail("get_message raised for unknown locale")


# ---------------------------------------------------------------------------
# Missing key falls back to key string
# ---------------------------------------------------------------------------


class TestMissingKeyFallback:
    def test_returns_key_for_missing_key_en(self) -> None:
        result = get_message("nonexistent.key", "en")
        assert result == "nonexistent.key"

    def test_returns_key_for_missing_key_fr(self) -> None:
        result = get_message("nonexistent.key", "fr")
        assert result == "nonexistent.key"

    def test_returns_key_for_missing_key_unknown_locale(self) -> None:
        result = get_message("totally.missing", "xx")  # type: ignore[arg-type]
        assert result == "totally.missing"

    def test_does_not_raise_for_missing_key(self) -> None:
        try:
            get_message("not.a.real.key", "en")
        except Exception:  # noqa: BLE001
            pytest.fail("get_message raised for missing key")


# ---------------------------------------------------------------------------
# Catalog completeness — all locales share the same keys
# ---------------------------------------------------------------------------


class TestCatalogCompleteness:
    _EXPECTED_KEYS = {
        "email.reset.subject",
        "push.check_in.title",
        "pdf.report.title",
        "safety.t4.headline",
    }
    _LOCALES = ["en", "fr", "ar", "fa"]

    def test_all_keys_present_in_all_locales(self) -> None:
        for locale in self._LOCALES:
            for key in self._EXPECTED_KEYS:
                result = get_message(key, locale)  # type: ignore[arg-type]
                assert result != key, f"Key '{key}' missing from '{locale}' catalog"

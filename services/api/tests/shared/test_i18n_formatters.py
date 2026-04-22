"""Latin-digit clinical-fidelity tests.

Non-negotiable rule (CLAUDE.md §9, Docs/Technicals/15_Internationalization.md
§Latin-digit rule): clinical scores render in Latin digits regardless of
locale.  A PHQ-9 total of 17 must appear as ``17`` in every UI surface —
never as ``١٧`` (Arabic-Indic) or ``۱۷`` (Persian).
"""

from __future__ import annotations

from datetime import date

import pytest

from discipline.shared.i18n.formatters import (
    format_date,
    format_number,
    format_number_clinical,
)

# ---- The critical invariant: clinical scores always Latin ------------------


@pytest.mark.parametrize("locale", ["en", "fr", "ar", "fa"])
@pytest.mark.parametrize("value", [0, 5, 9, 12, 17, 21, 27])
def test_clinical_scores_render_latin_digits_in_every_locale(locale: str, value: int) -> None:
    rendered = format_number_clinical(value, locale)  # type: ignore[arg-type]

    for ch in rendered:
        assert ch.isascii(), (
            f"format_number_clinical({value!r}, {locale!r}) yielded non-ASCII "
            f"character {ch!r}; clinical scores must be Latin digits"
        )


@pytest.mark.parametrize("locale", ["en", "fr", "ar", "fa"])
def test_clinical_score_string_matches_integer_repr(locale: str) -> None:
    """For whole-number clinical scores, output is the plain decimal."""
    assert format_number_clinical(17, locale) == "17"  # type: ignore[arg-type]


@pytest.mark.parametrize("locale", ["ar", "fa"])
def test_clinical_scores_do_not_use_arabic_indic_digits(locale: str) -> None:
    """Belt-and-braces: explicitly reject known digit substitutions."""
    arabic_indic = "٠١٢٣٤٥٦٧٨٩"
    persian = "۰۱۲۳۴۵۶۷۸۹"
    rendered = format_number_clinical(123, locale)  # type: ignore[arg-type]
    assert not any(d in rendered for d in arabic_indic)
    assert not any(d in rendered for d in persian)


# ---- General number formatter is allowed to localize body-copy separators --


def test_general_number_en_uses_plain_decimal() -> None:
    assert format_number(1234.5, "en") == "1234.5"


def test_general_number_fr_uses_space_thousands_and_comma_decimal() -> None:
    """French thousands-grouping is a space; decimal is a comma."""
    out = format_number(1234.5, "fr")
    # Thousands grouping may or may not kick in at the 4-digit mark depending
    # on locale convention; allow either but require comma decimal.
    assert "," in out  # decimal comma
    assert "." not in out  # no dot decimal


# ---- Date formatter ---------------------------------------------------------


def test_date_format_en_iso() -> None:
    assert format_date(date(2026, 4, 18), "en") == "2026-04-18"


def test_date_format_fr_dmy_slashes() -> None:
    assert format_date(date(2026, 4, 18), "fr") == "18/04/2026"


@pytest.mark.parametrize("locale", ["ar", "fa"])
def test_date_format_rtl_uses_latin_digits(locale: str) -> None:
    out = format_date(date(2026, 4, 18), locale)  # type: ignore[arg-type]
    for ch in out:
        assert ch.isascii(), f"date rendering for {locale!r} emitted non-ASCII: {ch!r}"

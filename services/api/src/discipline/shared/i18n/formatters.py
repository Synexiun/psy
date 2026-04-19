"""Locale-aware formatters.

Rule: clinical instrument scores (PHQ-9 total etc.) ALWAYS use Latin digits,
regardless of user locale.  This is a clinical-fidelity requirement, not a style
choice — see Docs/Whitepapers/02_Clinical_Evidence_Base.md §Rendering.

Use :func:`format_number_clinical` for scores and :func:`format_number` for
everything else.
"""

from __future__ import annotations

from datetime import date, datetime

from .negotiation import Locale


def format_date(d: date | datetime, locale: Locale) -> str:
    if locale == "fr":
        return d.strftime("%d/%m/%Y")
    if locale in ("ar", "fa"):
        # Use ISO-like ordering but with Latin digits; calendar stays Gregorian at the API layer.
        return d.strftime("%Y-%m-%d")
    return d.strftime("%Y-%m-%d")


def format_number(n: float | int, locale: Locale) -> str:
    # Body copy numbers may use locale digits, but body copy numbers are rare in the API.
    # Keep this simple: Latin digits, locale-appropriate separators.
    if locale == "fr":
        return f"{n:,.2f}".replace(",", " ").replace(".", ",").rstrip("0").rstrip(",")
    return f"{n:g}"


def format_number_clinical(n: float | int, _locale: Locale) -> str:
    """Clinical scores — always Latin digits, always plain decimal."""
    return f"{n:g}"


__all__ = ["format_date", "format_number", "format_number_clinical"]

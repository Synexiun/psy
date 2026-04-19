"""Locale negotiation — BCP 47 tags.

Source order:
    1. ``users.locale`` if the user is authenticated and has set a preference.
    2. ``Accept-Language`` header (best q-weighted match).
    3. ``DEFAULT_LOCALE``.

Matching is primary-subtag only; regional variants (e.g. ``fr-CA``) collapse to ``fr``
at this layer because we don't ship regional variant translations.  Currency / date
formatting DOES use the regional variant where provided (see :mod:`.formatters`).
"""

from __future__ import annotations

from typing import Literal, Sequence

Locale = Literal["en", "fr", "ar", "fa"]

SUPPORTED_LOCALES: tuple[Locale, ...] = ("en", "fr", "ar", "fa")
DEFAULT_LOCALE: Locale = "en"
RTL_LOCALES: frozenset[Locale] = frozenset({"ar", "fa"})


def is_rtl(locale: Locale) -> bool:
    return locale in RTL_LOCALES


def _parse_accept_language(header: str) -> list[tuple[str, float]]:
    out: list[tuple[str, float]] = []
    for chunk in header.split(","):
        parts = chunk.strip().split(";")
        tag = parts[0].strip().lower()
        q = 1.0
        for p in parts[1:]:
            p = p.strip()
            if p.startswith("q="):
                try:
                    q = float(p[2:])
                except ValueError:
                    q = 0.0
        if tag:
            out.append((tag, q))
    out.sort(key=lambda x: x[1], reverse=True)
    return out


def negotiate_locale(
    user_locale: str | None,
    accept_language: str | None,
    supported: Sequence[Locale] = SUPPORTED_LOCALES,
) -> Locale:
    if user_locale:
        primary = user_locale.split("-")[0].lower()
        if primary in supported:
            return primary  # type: ignore[return-value]

    if accept_language:
        for tag, _q in _parse_accept_language(accept_language):
            primary = tag.split("-")[0]
            if primary in supported:
                return primary  # type: ignore[return-value]

    return DEFAULT_LOCALE


__all__ = [
    "Locale",
    "SUPPORTED_LOCALES",
    "DEFAULT_LOCALE",
    "RTL_LOCALES",
    "is_rtl",
    "negotiate_locale",
]

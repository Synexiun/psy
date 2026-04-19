"""Package i18n catalog loader + no-MT enforcement (CLAUDE.md Rule #8).

The shared i18n catalogs live in ``packages/i18n-catalog/src/catalogs/<locale>.json``
and are consumed by every web + mobile surface.  This module provides the
backend's view of those files for two purposes:

1. **Release gating.**  A locale's ``_meta.status`` is one of ``source`` /
   ``released`` / ``draft``.  ``draft`` means "translation scaffold, not yet
   validated by a native-speaker clinical reviewer".  Per Rule #8, draft
   locales must NOT ship clinical content (PHQ-9 / GAD-7 / C-SSRS items,
   safety copy, crisis copy, severity bands).  The release gate calls
   :func:`is_locale_releasable` and refuses to flip a locale live until its
   status is ``source`` or ``released``.

2. **Runtime fallback for clinical keys.**  Even before a locale is fully
   released, the app may render in that locale (better UX than forcing all
   draft-locale users to English everywhere).  But clinical keys must fall
   back to English to avoid showing unreviewed, potentially-incorrect
   wording on safety-adjacent surfaces.  :func:`resolve_clinical_message`
   implements this: it returns the locale's translation only when the
   locale is releasable; otherwise it returns the English source.

The clinical-key boundary is encoded in :data:`CLINICAL_KEY_PREFIXES`.
Adding a new clinical surface means adding a prefix here so the no-MT
fallback covers it.

Why this is the opposite of normal i18n: most i18n libraries silently fall
back to the source language only when a key is *missing*.  Here we fall
back even when the key is *present but unverified* — because a wrong
translation of "I'm having thoughts of suicide" is worse than no translation.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any

from .negotiation import DEFAULT_LOCALE, SUPPORTED_LOCALES, Locale

# ---- Catalog status --------------------------------------------------------


class CatalogStatus(str, Enum):
    """Lifecycle state of a locale catalog.

    - ``SOURCE`` — the canonical English copy.  By definition releasable.
    - ``RELEASED`` — a translated catalog that has passed native-speaker
      clinical review.  Releasable.
    - ``DRAFT`` — scaffold awaiting review.  NOT releasable; clinical keys
      fall back to English at render time.
    """

    SOURCE = "source"
    RELEASED = "released"
    DRAFT = "draft"


_RELEASABLE_STATUSES: frozenset[CatalogStatus] = frozenset(
    {CatalogStatus.SOURCE, CatalogStatus.RELEASED}
)


# ---- Clinical-key boundary -------------------------------------------------

# Any catalog key starting with one of these prefixes is treated as clinical
# and falls back to English when the requesting locale is not releasable.
# Keep this list narrow: every prefix added widens the surface that gets
# pinned to English on draft locales, which degrades UX.  Only safety- or
# instrument-adjacent keys belong here.
CLINICAL_KEY_PREFIXES: tuple[str, ...] = (
    "crisis.",
    "assessment.",
    "severity.",
    "safety.",
)


def is_clinical_key(key: str) -> bool:
    """True if the key is on a safety/clinical surface and must not be
    machine-translated."""
    return any(key.startswith(prefix) for prefix in CLINICAL_KEY_PREFIXES)


# ---- Dataclasses -----------------------------------------------------------


@dataclass(frozen=True)
class CatalogMeta:
    locale: Locale
    direction: str  # "ltr" or "rtl"
    status: CatalogStatus
    reviewed_by: str | None
    reviewed_at: str | None
    note: str | None


@dataclass(frozen=True)
class LoadedCatalog:
    """A package catalog loaded from disk.

    ``messages`` is a *flattened* dict — nested JSON paths become dotted
    keys (e.g. ``crisis.cta.primary``) so callers can use simple string
    lookups without walking the tree.
    """

    meta: CatalogMeta
    messages: dict[str, str]


# ---- Exceptions ------------------------------------------------------------


class CatalogParityError(RuntimeError):
    """Raised when a non-source locale catalog is missing keys that exist in
    the English source-of-truth.  Release-gate uses this to refuse locales
    with incomplete coverage."""


class CatalogStatusError(ValueError):
    """Raised when a catalog's ``_meta.status`` is not a known
    :class:`CatalogStatus` value.  Indicates a malformed catalog file."""


# ---- File layout -----------------------------------------------------------

_MODULE_DIR = Path(__file__).resolve().parent
# services/api/src/discipline/shared/i18n/  ->  repo root  ->  packages/i18n-catalog/src/catalogs/
# (6 levels: i18n -> shared -> discipline -> src -> api -> services -> repo root)
_DEFAULT_CATALOGS_DIR = (
    _MODULE_DIR.parent.parent.parent.parent.parent.parent
    / "packages"
    / "i18n-catalog"
    / "src"
    / "catalogs"
)


def _catalog_path(locale: Locale, base: Path | None = None) -> Path:
    return (base or _DEFAULT_CATALOGS_DIR) / f"{locale}.json"


# ---- Parsing ---------------------------------------------------------------


def _flatten(prefix: str, obj: dict[str, Any]) -> dict[str, str]:
    out: dict[str, str] = {}
    for k, v in obj.items():
        full = f"{prefix}{k}" if prefix else k
        if isinstance(v, dict):
            out.update(_flatten(f"{full}.", v))
        elif isinstance(v, str):
            out[full] = v
        # Non-string leaves (numbers, booleans, lists) are ignored — every
        # rendered message is a string.  If the catalog grows to need
        # plural rules / arrays, revisit here.
    return out


def _parse_meta(raw_meta: dict[str, Any], locale: Locale) -> CatalogMeta:
    raw_status = raw_meta.get("status")
    try:
        status = CatalogStatus(raw_status)
    except ValueError as exc:
        raise CatalogStatusError(
            f"catalog {locale}: _meta.status={raw_status!r} is not a valid "
            f"CatalogStatus (expected one of {[s.value for s in CatalogStatus]})"
        ) from exc
    return CatalogMeta(
        locale=locale,
        direction=raw_meta.get("direction", "ltr"),
        status=status,
        reviewed_by=raw_meta.get("reviewedBy"),
        reviewed_at=raw_meta.get("reviewedAt"),
        note=raw_meta.get("note"),
    )


def _parse(raw: dict[str, Any], locale: Locale) -> LoadedCatalog:
    raw_meta = raw.get("_meta")
    if not isinstance(raw_meta, dict):
        raise CatalogStatusError(
            f"catalog {locale}: missing or invalid _meta block"
        )
    meta = _parse_meta(raw_meta, locale)
    # Strip _meta before flattening — it's not a renderable message tree.
    body = {k: v for k, v in raw.items() if k != "_meta"}
    return LoadedCatalog(meta=meta, messages=_flatten("", body))


# ---- Loading ---------------------------------------------------------------


def load_catalog(locale: Locale, *, base: Path | None = None) -> LoadedCatalog:
    """Load a single locale's catalog from disk.

    ``base`` is injectable for tests — it overrides the default
    ``packages/i18n-catalog/src/catalogs`` location.  Production callers
    omit it.
    """
    path = _catalog_path(locale, base)
    with path.open("r", encoding="utf-8") as fh:
        raw = json.load(fh)
    return _parse(raw, locale)


@lru_cache(maxsize=len(SUPPORTED_LOCALES))
def _load_default(locale: Locale) -> LoadedCatalog:
    """Cached load of the default-path catalog.  Production hot path."""
    return load_catalog(locale)


# ---- Release gating --------------------------------------------------------


def is_locale_releasable(locale: Locale) -> bool:
    """True if the locale's catalog has been validated and may ship.

    ``en`` (status=source) is always releasable.  ``fr``/``ar``/``fa`` are
    currently ``draft`` and return False until clinical review flips them
    to ``released``.

    Use this in CI release-gate scripts to refuse a deploy that would put
    an unvalidated locale in front of users.
    """
    return _load_default(locale).meta.status in _RELEASABLE_STATUSES


def releasable_locales() -> tuple[Locale, ...]:
    """All locales currently safe to ship.  Used by release-gate scripts to
    diff against the deploy manifest."""
    return tuple(loc for loc in SUPPORTED_LOCALES if is_locale_releasable(loc))


# ---- Message resolution ----------------------------------------------------


def resolve_clinical_message(key: str, locale: Locale) -> str:
    """Resolve a message, applying the no-MT rule for clinical keys.

    Behavior matrix:

    +-----------------+-------------+--------------------------------------+
    | Key kind        | Locale      | Result                               |
    +-----------------+-------------+--------------------------------------+
    | clinical        | releasable  | locale's translation (or en fallback)|
    | clinical        | draft       | en translation (no-MT rule)          |
    | non-clinical    | any         | locale's translation (or en fallback)|
    +-----------------+-------------+--------------------------------------+

    Final fallback for any path is the key string itself, surfacing the
    gap loudly in QA without breaking a render.

    The function never raises — a missing translation must not break
    a screen render.
    """
    if is_clinical_key(key) and not is_locale_releasable(locale):
        return _lookup(key, DEFAULT_LOCALE)
    primary = _lookup(key, locale)
    if primary is not None:
        return primary
    fallback = _lookup(key, DEFAULT_LOCALE)
    return fallback if fallback is not None else key


def _lookup(key: str, locale: Locale) -> str | None:
    catalog = _load_default(locale)
    return catalog.messages.get(key)


# ---- Parity check ----------------------------------------------------------


def verify_catalog_parity(*, base: Path | None = None) -> None:
    """Raise :class:`CatalogParityError` if any non-source locale catalog
    is missing keys that exist in English.

    A draft catalog is permitted to be in flux, but it must at least
    declare every key that English declares — even if the value is a
    placeholder — so QA can see the gap and the fall-back-to-en path
    is consistent.

    Used by CI; not called on the request hot path.
    """
    source_keys = set(load_catalog(DEFAULT_LOCALE, base=base).messages.keys())
    missing: dict[Locale, set[str]] = {}
    for locale in SUPPORTED_LOCALES:
        if locale == DEFAULT_LOCALE:
            continue
        keys = set(load_catalog(locale, base=base).messages.keys())
        gap = source_keys - keys
        if gap:
            missing[locale] = gap
    if missing:
        formatted = "; ".join(
            f"{loc}: {len(gap)} missing ({sorted(gap)[:3]}…)"
            for loc, gap in missing.items()
        )
        raise CatalogParityError(
            f"i18n catalog parity drift vs source ({DEFAULT_LOCALE}): {formatted}"
        )


__all__ = [
    "CLINICAL_KEY_PREFIXES",
    "CatalogMeta",
    "CatalogParityError",
    "CatalogStatus",
    "CatalogStatusError",
    "LoadedCatalog",
    "is_clinical_key",
    "is_locale_releasable",
    "load_catalog",
    "releasable_locales",
    "resolve_clinical_message",
    "verify_catalog_parity",
]

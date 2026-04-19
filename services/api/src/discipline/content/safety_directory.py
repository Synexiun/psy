"""Server-side safety directory.

This module loads the same ``hotlines.json`` shipped with
``packages/safety-directory``.  Path: ``services/api/data/safety/hotlines.json``.

Two non-negotiable guarantees live here (CLAUDE.md Rule #10):

1. **Freshness gate.**  Every hotline entry carries a ``verifiedAt`` date.
   Entries older than ``_meta.reviewWindowDays`` (90 days by default) block
   the release for their country-locale.  :func:`check_freshness` returns
   the offending entries; a release-gate script / CI job calls it and fails
   the build if the tuple is non-empty.  Runtime ``resolve()`` calls keep
   serving stale entries — showing a slightly outdated hotline is safer
   than showing nothing.

2. **Mirror parity.**  The JSON is duplicated into
   ``packages/safety-directory/src/hotlines.json`` for client bundles.  The
   two copies must be byte-for-byte identical.  :func:`verify_mirror_parity`
   compares SHA-256 digests and raises :class:`MirrorDriftError` on drift.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import date, timedelta
from functools import lru_cache
from pathlib import Path
from typing import Any

from discipline.shared.i18n import Locale

# ---- File layout -----------------------------------------------------------

_MODULE_DIR = Path(__file__).resolve().parent
# services/api/src/discipline/content/ → services/api/data/safety/
_DEFAULT_API_PATH = _MODULE_DIR.parent.parent.parent / "data" / "safety" / "hotlines.json"
# services/api/src/discipline/content/ → repo root → packages/safety-directory/src/
_DEFAULT_PACKAGE_PATH = (
    _MODULE_DIR.parent.parent.parent.parent.parent
    / "packages"
    / "safety-directory"
    / "src"
    / "hotlines.json"
)


# ---- Dataclasses -----------------------------------------------------------


@dataclass(frozen=True)
class Hotline:
    id: str
    name: str
    number: str | None
    sms: str | None
    web: str | None
    hours: str
    cost: str
    verified_at: str  # ISO 8601 date string preserved for audit


@dataclass(frozen=True)
class CountryDirectory:
    country: str
    locale: Locale
    emergency_label: str
    emergency_number: str
    hotlines: tuple[Hotline, ...]


@dataclass(frozen=True)
class DirectoryMeta:
    schema_version: str
    last_reviewed_at: date
    review_window_days: int
    reviewed_by: str


@dataclass(frozen=True)
class StaleEntry:
    """A hotline whose ``verifiedAt`` is older than the review cutoff."""

    country: str
    locale: Locale
    hotline_id: str
    verified_at: date
    review_cutoff: date
    days_stale: int


# ---- Exceptions ------------------------------------------------------------


class MirrorDriftError(RuntimeError):
    """Raised when the API copy and the package copy of hotlines.json differ."""


# ---- Loading ---------------------------------------------------------------


def _load_raw(path: Path = _DEFAULT_API_PATH) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _parse_meta(raw_meta: dict[str, Any]) -> DirectoryMeta:
    return DirectoryMeta(
        schema_version=raw_meta["schemaVersion"],
        last_reviewed_at=date.fromisoformat(raw_meta["lastReviewedAt"]),
        review_window_days=int(raw_meta["reviewWindowDays"]),
        reviewed_by=raw_meta["reviewedBy"],
    )


def _parse_directory(raw: dict[str, Any]) -> tuple[CountryDirectory, ...]:
    out: list[CountryDirectory] = []
    for entry in raw.get("entries", []):
        hotlines = tuple(
            Hotline(
                id=h["id"],
                name=h["name"],
                number=h.get("number"),
                sms=h.get("sms"),
                web=h.get("web"),
                hours=h["hours"],
                cost=h["cost"],
                verified_at=h["verifiedAt"],
            )
            for h in entry.get("hotlines", [])
        )
        out.append(
            CountryDirectory(
                country=entry["country"],
                locale=entry["locale"],
                emergency_label=entry["emergency"]["label"],
                emergency_number=entry["emergency"]["number"],
                hotlines=hotlines,
            )
        )
    return tuple(out)


@lru_cache(maxsize=1)
def _load() -> tuple[CountryDirectory, ...]:
    return _parse_directory(_load_raw())


@lru_cache(maxsize=1)
def _load_meta() -> DirectoryMeta:
    return _parse_meta(_load_raw()["_meta"])


# ---- Runtime resolution (unchanged from original) --------------------------


def resolve(country: str | None, locale: Locale) -> CountryDirectory:
    """Resolve the best-match directory for a (country, locale) pair.

    Fallback chain: exact match → same country in ``en`` → global US/en default.
    ``resolve()`` does NOT refuse stale entries; serving something is safer
    than serving nothing on a crisis path.  The freshness gate lives in CI.
    """
    directory = _load()
    if country:
        for entry in directory:
            if entry.country.upper() == country.upper() and entry.locale == locale:
                return entry
        for entry in directory:
            if entry.country.upper() == country.upper() and entry.locale == "en":
                return entry
    for entry in directory:
        if entry.country == "US" and entry.locale == "en":
            return entry
    raise RuntimeError("safety-directory: global fallback missing")


# ---- Freshness gate --------------------------------------------------------


def check_freshness(
    now: date | None = None,
    *,
    directory: tuple[CountryDirectory, ...] | None = None,
    meta: DirectoryMeta | None = None,
) -> tuple[StaleEntry, ...]:
    """Return hotlines whose ``verifiedAt`` is older than the review cutoff.

    ``now`` defaults to :meth:`date.today` but is injectable for deterministic
    tests.  ``directory`` and ``meta`` are injectable for tests that want to
    exercise the rule without rewriting the on-disk JSON.

    Edge: ``verified_at == cutoff`` is treated as **fresh** (not stale).
    The window is "older than N days"; exactly-N-days-ago is the boundary
    value that still counts.
    """
    today = now or date.today()
    dir_data = directory if directory is not None else _load()
    meta_data = meta or _load_meta()
    cutoff = today - timedelta(days=meta_data.review_window_days)

    stale: list[StaleEntry] = []
    for entry in dir_data:
        for hotline in entry.hotlines:
            verified = date.fromisoformat(hotline.verified_at)
            if verified < cutoff:
                stale.append(
                    StaleEntry(
                        country=entry.country,
                        locale=entry.locale,
                        hotline_id=hotline.id,
                        verified_at=verified,
                        review_cutoff=cutoff,
                        days_stale=(cutoff - verified).days,
                    )
                )
    return tuple(stale)


def is_locale_blocked(
    country: str,
    locale: Locale,
    now: date | None = None,
    *,
    directory: tuple[CountryDirectory, ...] | None = None,
    meta: DirectoryMeta | None = None,
) -> bool:
    """True if any hotline for the given country-locale is stale."""
    stale = check_freshness(now, directory=directory, meta=meta)
    return any(
        s.country.upper() == country.upper() and s.locale == locale for s in stale
    )


# ---- Mirror parity ---------------------------------------------------------


def compute_directory_sha256(path: Path) -> str:
    """SHA-256 of the file contents.  Used by :func:`verify_mirror_parity`."""
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_mirror_parity(
    package_path: Path | None = None,
    api_path: Path | None = None,
) -> None:
    """Raise :class:`MirrorDriftError` if the two copies of hotlines.json
    have diverged byte-for-byte.

    Defaults point at the canonical repo locations.  Tests inject tmp paths
    via the ``package_path`` / ``api_path`` arguments.
    """
    pkg_path = package_path or _DEFAULT_PACKAGE_PATH
    api_path_resolved = api_path or _DEFAULT_API_PATH
    pkg_sha = compute_directory_sha256(pkg_path)
    api_sha = compute_directory_sha256(api_path_resolved)
    if pkg_sha != api_sha:
        raise MirrorDriftError(
            "safety-directory mirror drift: package and api copies differ.\n"
            f"  package: {pkg_path} ({pkg_sha[:12]}…)\n"
            f"  api:     {api_path_resolved} ({api_sha[:12]}…)\n"
            "Both copies must be byte-for-byte identical (CLAUDE.md Rule #10)."
        )


__all__ = [
    "CountryDirectory",
    "DirectoryMeta",
    "Hotline",
    "MirrorDriftError",
    "StaleEntry",
    "check_freshness",
    "compute_directory_sha256",
    "is_locale_blocked",
    "resolve",
    "verify_mirror_parity",
]

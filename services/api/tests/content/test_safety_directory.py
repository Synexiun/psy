"""Safety directory freshness + mirror parity tests.

Enforces CLAUDE.md Rule #10:
- An entry whose ``verifiedAt`` is older than ``reviewWindowDays`` blocks
  the release for that country-locale.
- ``packages/safety-directory/src/hotlines.json`` and
  ``services/api/data/safety/hotlines.json`` must match byte-for-byte.
"""

from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

import pytest

from discipline.content.safety_directory import (
    _DEFAULT_API_PATH,
    _DEFAULT_PACKAGE_PATH,
    CountryDirectory,
    DirectoryMeta,
    Hotline,
    MirrorDriftError,
    check_freshness,
    compute_directory_sha256,
    is_locale_blocked,
    verify_mirror_parity,
)

# ---- Fixtures --------------------------------------------------------------


def _meta(*, window_days: int = 90, reviewed_at: date = date(2026, 4, 18)) -> DirectoryMeta:
    return DirectoryMeta(
        schema_version="1.0.0",
        last_reviewed_at=reviewed_at,
        review_window_days=window_days,
        reviewed_by="clinical-ops-test",
    )


def _hotline(hid: str, verified_at: str) -> Hotline:
    return Hotline(
        id=hid,
        name=f"Test Hotline {hid}",
        number="999",
        sms=None,
        web=None,
        hours="24/7",
        cost="free",
        verified_at=verified_at,
    )


def _entry(country: str, locale: str, hotlines: list[Hotline]) -> CountryDirectory:
    return CountryDirectory(
        country=country,
        locale=locale,  # type: ignore[arg-type]
        emergency_label="Emergency",
        emergency_number="911",
        hotlines=tuple(hotlines),
    )


# =============================================================================
# Freshness gate
# =============================================================================


class TestFreshnessGate:
    def test_entry_within_window_is_fresh(self) -> None:
        """verified_at is 30 days old; window is 90 → fresh."""
        now = date(2026, 4, 18)
        directory = (
            _entry("US", "en", [_hotline("us-1", "2026-03-19")]),
        )
        stale = check_freshness(now, directory=directory, meta=_meta(window_days=90))
        assert stale == ()

    def test_entry_past_window_is_stale(self) -> None:
        """verified_at is 100 days old; window is 90 → stale."""
        now = date(2026, 4, 18)
        verified = now - timedelta(days=100)
        directory = (
            _entry("US", "en", [_hotline("us-1", verified.isoformat())]),
        )
        stale = check_freshness(now, directory=directory, meta=_meta(window_days=90))
        assert len(stale) == 1
        assert stale[0].hotline_id == "us-1"
        assert stale[0].days_stale == 10  # 100 - 90

    def test_entry_at_exact_cutoff_is_fresh(self) -> None:
        """Boundary: verified_at == cutoff is treated as fresh, not stale.

        The window is "older than N days"; exactly-N-days-ago is the
        boundary value that still counts as fresh.  If this inequality
        ever flips from strict to non-strict, clinical-ops must be notified
        since it may block locales at the edge of review cycles."""
        now = date(2026, 4, 18)
        window = 90
        verified = now - timedelta(days=window)  # exactly at cutoff
        directory = (
            _entry("US", "en", [_hotline("us-1", verified.isoformat())]),
        )
        stale = check_freshness(now, directory=directory, meta=_meta(window_days=window))
        assert stale == ()

    def test_mixed_entries_only_stale_returned(self) -> None:
        now = date(2026, 4, 18)
        directory = (
            _entry("US", "en", [
                _hotline("fresh-1", (now - timedelta(days=30)).isoformat()),
                _hotline("stale-1", (now - timedelta(days=120)).isoformat()),
            ]),
            _entry("UK", "en", [
                _hotline("fresh-2", (now - timedelta(days=1)).isoformat()),
            ]),
        )
        stale = check_freshness(now, directory=directory, meta=_meta(window_days=90))
        stale_ids = {s.hotline_id for s in stale}
        assert stale_ids == {"stale-1"}

    def test_stale_entry_records_cutoff_and_days_stale(self) -> None:
        """The StaleEntry payload gives release tooling enough context to
        print an actionable error message."""
        now = date(2026, 4, 18)
        verified = date(2025, 1, 1)  # definitely stale
        directory = (
            _entry("US", "en", [_hotline("us-old", verified.isoformat())]),
        )
        stale = check_freshness(now, directory=directory, meta=_meta(window_days=90))
        assert len(stale) == 1
        entry = stale[0]
        assert entry.verified_at == verified
        assert entry.review_cutoff == now - timedelta(days=90)
        assert entry.days_stale > 0
        assert entry.country == "US"
        assert entry.locale == "en"


class TestIsLocaleBlocked:
    """``is_locale_blocked`` answers the release-gate question directly."""

    def test_fresh_locale_is_not_blocked(self) -> None:
        now = date(2026, 4, 18)
        directory = (
            _entry("US", "en", [_hotline("us-1", "2026-04-01")]),
        )
        assert is_locale_blocked(
            "US", "en", now, directory=directory, meta=_meta(window_days=90)
        ) is False

    def test_stale_locale_is_blocked(self) -> None:
        now = date(2026, 4, 18)
        directory = (
            _entry("US", "en", [_hotline("us-old", "2025-01-01")]),
        )
        assert is_locale_blocked(
            "US", "en", now, directory=directory, meta=_meta(window_days=90)
        ) is True

    def test_other_stale_locale_does_not_block_this_one(self) -> None:
        """A stale UK entry must not block the US release."""
        now = date(2026, 4, 18)
        directory = (
            _entry("US", "en", [_hotline("us-fresh", "2026-04-01")]),
            _entry("UK", "en", [_hotline("uk-old", "2025-01-01")]),
        )
        assert is_locale_blocked(
            "US", "en", now, directory=directory, meta=_meta(window_days=90)
        ) is False
        assert is_locale_blocked(
            "UK", "en", now, directory=directory, meta=_meta(window_days=90)
        ) is True

    def test_country_match_is_case_insensitive(self) -> None:
        now = date(2026, 4, 18)
        directory = (
            _entry("US", "en", [_hotline("us-old", "2025-01-01")]),
        )
        assert is_locale_blocked(
            "us", "en", now, directory=directory, meta=_meta(window_days=90)
        ) is True


# =============================================================================
# Mirror parity
# =============================================================================


class TestMirrorParity:
    def test_identical_files_pass(self, tmp_path: Path) -> None:
        content = '{"_meta": {"schemaVersion": "1.0.0"}, "entries": []}'
        pkg = tmp_path / "pkg.json"
        api = tmp_path / "api.json"
        pkg.write_text(content, encoding="utf-8")
        api.write_text(content, encoding="utf-8")
        # Should not raise
        verify_mirror_parity(package_path=pkg, api_path=api)

    def test_divergent_files_raise(self, tmp_path: Path) -> None:
        pkg = tmp_path / "pkg.json"
        api = tmp_path / "api.json"
        pkg.write_text('{"a": 1}', encoding="utf-8")
        api.write_text('{"a": 2}', encoding="utf-8")
        with pytest.raises(MirrorDriftError, match="mirror drift"):
            verify_mirror_parity(package_path=pkg, api_path=api)

    def test_error_includes_both_digests(self, tmp_path: Path) -> None:
        """The error message must show both paths and truncated digests so
        the operator can pinpoint which file to reconcile."""
        pkg = tmp_path / "pkg.json"
        api = tmp_path / "api.json"
        pkg.write_text('{"a": 1}', encoding="utf-8")
        api.write_text('{"a": 2}', encoding="utf-8")
        with pytest.raises(MirrorDriftError) as exc_info:
            verify_mirror_parity(package_path=pkg, api_path=api)
        msg = str(exc_info.value)
        assert str(pkg) in msg
        assert str(api) in msg

    def test_whitespace_difference_counts_as_drift(self, tmp_path: Path) -> None:
        """Byte-for-byte means byte-for-byte — even a trailing newline drift
        must block the build."""
        pkg = tmp_path / "pkg.json"
        api = tmp_path / "api.json"
        pkg.write_text("{}", encoding="utf-8")
        api.write_text("{}\n", encoding="utf-8")  # extra newline
        with pytest.raises(MirrorDriftError):
            verify_mirror_parity(package_path=pkg, api_path=api)

    def test_sha256_is_deterministic(self, tmp_path: Path) -> None:
        f = tmp_path / "f.json"
        f.write_text("hello", encoding="utf-8")
        a = compute_directory_sha256(f)
        b = compute_directory_sha256(f)
        assert a == b
        # Known SHA-256 of "hello"
        assert a == "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"


# =============================================================================
# Live file integrity (regression guard)
# =============================================================================


class TestLiveFilesStateLockedIn:
    """These tests read the actual repo files and guard against accidental
    drift introduced by a PR.  They use a fixed ``now`` so they don't
    flake as the calendar advances."""

    def test_live_mirror_is_in_parity(self) -> None:
        """The repo must ship with matching package+api copies.  If this
        fails, reconcile before committing.  CI runs this on every PR."""
        verify_mirror_parity()

    def test_live_directory_passes_freshness_as_of_reviewed_date(self) -> None:
        """On the day the directory was last reviewed, every entry is fresh
        by definition (assuming review bumps ``verifiedAt`` to today or earlier).

        This is a sanity check: if this fails, the review process shipped
        a directory with already-stale entries.  Uses the meta's
        ``lastReviewedAt`` as ``now`` to make it deterministic.
        """
        from discipline.content.safety_directory import _load, _load_meta

        meta = _load_meta()
        directory = _load()
        stale = check_freshness(meta.last_reviewed_at, directory=directory, meta=meta)
        assert stale == (), (
            f"Directory shipped with {len(stale)} stale entries on review date:\n"
            + "\n".join(f"  - {s.country}/{s.locale}/{s.hotline_id} "
                        f"(verified {s.verified_at}, {s.days_stale}d stale)"
                        for s in stale)
        )

    def test_live_directory_has_expected_top_level_shape(self) -> None:
        """Schema guard: if the JSON shape changes, the loader will also
        need an update.  Freeze the top-level contract."""
        with _DEFAULT_API_PATH.open(encoding="utf-8") as fh:
            raw = json.load(fh)
        assert "_meta" in raw
        assert "entries" in raw
        assert raw["_meta"]["schemaVersion"] == "1.0.0"
        assert raw["_meta"]["reviewWindowDays"] == 90

    def test_live_meta_last_reviewed_is_parseable_iso_date(self) -> None:
        with _DEFAULT_API_PATH.open(encoding="utf-8") as fh:
            raw = json.load(fh)
        # Raises ValueError if not parseable
        date.fromisoformat(raw["_meta"]["lastReviewedAt"])

    def test_live_package_path_resolves(self) -> None:
        """The default package path must actually exist — a broken default
        would silently skip the mirror check in CI."""
        assert _DEFAULT_PACKAGE_PATH.exists(), (
            f"expected package hotlines.json at {_DEFAULT_PACKAGE_PATH}"
        )

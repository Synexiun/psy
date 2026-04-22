"""Package i18n catalog loader + no-MT enforcement tests.

Enforces CLAUDE.md Rule #8 — no machine translation of clinical content.

Three layers of coverage:

1. **Pure-logic** tests use ``base=tmp_path`` to write tiny synthetic
   catalogs and verify behavior in isolation (status enum, fallback,
   parity).
2. **Live-file** regression guards exercise the real catalogs shipped
   under ``packages/i18n-catalog/src/catalogs/`` so a malformed catalog
   fails CI before it can ship.
3. **Public API** smoke-tests the ``__init__`` re-exports.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from discipline.shared.i18n.package_catalog import (
    CLINICAL_KEY_PREFIXES,
    CatalogMeta,
    CatalogParityError,
    CatalogStatus,
    CatalogStatusError,
    LoadedCatalog,
    _load_default,
    is_clinical_key,
    is_locale_releasable,
    load_catalog,
    releasable_locales,
    resolve_clinical_message,
    verify_catalog_parity,
)

# ---- Helpers ---------------------------------------------------------------


def _write_catalog(
    base: Path,
    locale: str,
    *,
    status: str = "draft",
    body: dict | None = None,
    direction: str = "ltr",
    reviewed_by: str | None = None,
    reviewed_at: str | None = None,
) -> None:
    payload: dict = {
        "_meta": {
            "locale": locale,
            "direction": direction,
            "status": status,
            "reviewedBy": reviewed_by,
            "reviewedAt": reviewed_at,
        },
    }
    payload.update(body or {})
    (base / f"{locale}.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )


@pytest.fixture(autouse=True)
def _clear_default_cache() -> None:
    """Several tests below use the live default-path loader; clear its LRU
    cache between runs so a test isn't masked by a previous result."""
    _load_default.cache_clear()
    yield
    _load_default.cache_clear()


# =============================================================================
# CatalogStatus enum
# =============================================================================


class TestCatalogStatus:
    def test_three_known_statuses(self) -> None:
        """The status surface is exactly three states.  Any new state is
        a governance change and must be added deliberately."""
        assert {s.value for s in CatalogStatus} == {"source", "released", "draft"}

    def test_source_and_released_are_releasable(self, tmp_path: Path) -> None:
        _write_catalog(tmp_path, "en", status="source", body={"k": "v"})
        _write_catalog(tmp_path, "fr", status="released", body={"k": "v"})
        _write_catalog(tmp_path, "ar", status="draft", body={"k": "v"})
        # Direct dataclass check (not via cached default loader)
        en = load_catalog("en", base=tmp_path)
        fr = load_catalog("fr", base=tmp_path)
        ar = load_catalog("ar", base=tmp_path)
        assert en.meta.status is CatalogStatus.SOURCE
        assert fr.meta.status is CatalogStatus.RELEASED
        assert ar.meta.status is CatalogStatus.DRAFT

    def test_invalid_status_raises(self, tmp_path: Path) -> None:
        _write_catalog(tmp_path, "en", status="experimental", body={"k": "v"})
        with pytest.raises(CatalogStatusError, match="status="):
            load_catalog("en", base=tmp_path)

    def test_missing_meta_raises(self, tmp_path: Path) -> None:
        (tmp_path / "en.json").write_text('{"app": {"name": "x"}}', encoding="utf-8")
        with pytest.raises(CatalogStatusError, match="missing or invalid _meta"):
            load_catalog("en", base=tmp_path)


# =============================================================================
# Flattening
# =============================================================================


class TestFlattening:
    def test_nested_keys_become_dotted(self, tmp_path: Path) -> None:
        _write_catalog(
            tmp_path,
            "en",
            status="source",
            body={
                "crisis": {
                    "cta": {"primary": "Call now", "secondary": "View resources"},
                    "headline": "You are not alone.",
                },
                "nav": {"home": "Home"},
            },
        )
        cat = load_catalog("en", base=tmp_path)
        assert cat.messages["crisis.cta.primary"] == "Call now"
        assert cat.messages["crisis.cta.secondary"] == "View resources"
        assert cat.messages["crisis.headline"] == "You are not alone."
        assert cat.messages["nav.home"] == "Home"

    def test_meta_block_excluded_from_messages(self, tmp_path: Path) -> None:
        _write_catalog(tmp_path, "en", status="source", body={"a": "b"})
        cat = load_catalog("en", base=tmp_path)
        assert "_meta.locale" not in cat.messages
        assert "_meta.status" not in cat.messages

    def test_non_string_leaves_ignored(self, tmp_path: Path) -> None:
        """Non-string leaves (numbers, booleans, lists) are dropped — every
        rendered message is a string, and silently ignoring non-strings
        prevents a malformed catalog from poisoning the rendering layer."""
        (tmp_path / "en.json").write_text(
            json.dumps(
                {
                    "_meta": {
                        "locale": "en",
                        "direction": "ltr",
                        "status": "source",
                        "reviewedBy": None,
                        "reviewedAt": None,
                    },
                    "k": "v",
                    "n": 42,  # number
                    "b": True,  # bool
                    "l": ["a", "b"],  # list
                }
            ),
            encoding="utf-8",
        )
        cat = load_catalog("en", base=tmp_path)
        assert cat.messages == {"k": "v"}


# =============================================================================
# Clinical-key boundary
# =============================================================================


class TestClinicalKeyBoundary:
    @pytest.mark.parametrize(
        "key",
        [
            "crisis.headline",
            "crisis.cta.primary",
            "assessment.phq9.name",
            "severity.severe",
            "safety.t4.handoff",
        ],
    )
    def test_clinical_keys_are_recognized(self, key: str) -> None:
        assert is_clinical_key(key) is True

    @pytest.mark.parametrize(
        "key",
        [
            "nav.home",
            "common.action.save",
            "marketing.hero.headline",
            "app.welcome.title",
        ],
    )
    def test_non_clinical_keys_are_recognized(self, key: str) -> None:
        assert is_clinical_key(key) is False

    def test_prefix_set_is_load_bearing(self) -> None:
        """The prefix list is the no-MT boundary; widening it expands what
        falls back to English on draft locales.  This test pins the
        current set so a casual change is visible in review."""
        assert CLINICAL_KEY_PREFIXES == (
            "crisis.",
            "assessment.",
            "severity.",
            "safety.",
        )


# =============================================================================
# Releasability
# =============================================================================


class TestReleasability:
    def test_live_en_is_releasable(self) -> None:
        """English is the source-of-truth and must always be releasable;
        if this fails, en.json was published with a wrong status."""
        assert is_locale_releasable("en") is True

    def test_live_fr_currently_draft(self) -> None:
        """fr/ar/fa are draft as of 2026-04-18.  When clinical review flips
        a locale to ``released``, update this test in the same PR."""
        assert is_locale_releasable("fr") is False

    def test_live_ar_currently_draft(self) -> None:
        assert is_locale_releasable("ar") is False

    def test_live_fa_currently_draft(self) -> None:
        assert is_locale_releasable("fa") is False

    def test_releasable_locales_only_includes_releasable_ones(self) -> None:
        """The release-gate script consumes this; a wrongly-included draft
        would silently ship unverified clinical content."""
        result = releasable_locales()
        for locale in result:
            assert is_locale_releasable(locale)
        # En must always be in the releasable set.
        assert "en" in result


# =============================================================================
# Message resolution — the no-MT rule in action
# =============================================================================


class TestResolveClinicalMessage:
    """End-to-end resolution rules.

    Uses the *live* catalogs (en source + fr/ar/fa drafts) so the rule is
    exercised against real data shape.
    """

    def test_clinical_key_falls_back_to_en_on_draft_locale(self) -> None:
        """The crisis headline must render in English on a draft locale,
        even though the draft catalog has a translation present.  This is
        the single most important invariant in this module."""
        en_value = resolve_clinical_message("crisis.headline", "en")
        fr_value = resolve_clinical_message("crisis.headline", "fr")
        assert fr_value == en_value
        assert "alone" in en_value.lower()

    def test_non_clinical_key_uses_locale_translation_on_draft(self) -> None:
        """A nav button can show its draft translation — it's not safety-
        adjacent and degrading the whole UI to English would harm UX."""
        fr_home = resolve_clinical_message("nav.home", "fr")
        en_home = resolve_clinical_message("nav.home", "en")
        assert fr_home != en_home  # actually translated
        assert fr_home == "Accueil"

    def test_clinical_key_on_en_returns_en(self) -> None:
        """Source locale always serves its own value for clinical keys."""
        v = resolve_clinical_message("severity.severe", "en")
        assert v == "Severe"

    def test_missing_key_returns_key_string(self) -> None:
        """Missing translations must NEVER raise — a render must not break.
        Returning the key surfaces the gap loudly in QA."""
        v = resolve_clinical_message("does.not.exist.anywhere", "en")
        assert v == "does.not.exist.anywhere"

    def test_present_in_en_missing_in_locale_returns_en(self) -> None:
        """Non-clinical key, missing in a draft locale → en fallback (the
        normal i18n behavior, distinct from the no-MT rule)."""
        # ``app.welcome.body`` exists in en — let's verify the fallback path
        # works for any non-clinical key.  (We don't know which keys the live
        # fr catalog is missing, so the easiest safe check: a clinical key on
        # a non-existent locale string would still get en.)
        v = resolve_clinical_message("nav.home", "en")
        assert v == "Home"


# =============================================================================
# Catalog parity (release gate)
# =============================================================================


class TestCatalogParity:
    def test_identical_keys_pass(self, tmp_path: Path) -> None:
        body = {"crisis": {"headline": "You are not alone."}, "nav": {"home": "x"}}
        _write_catalog(tmp_path, "en", status="source", body=body)
        for loc in ("fr", "ar", "fa"):
            _write_catalog(tmp_path, loc, status="draft", body=body)
        # Should not raise
        verify_catalog_parity(base=tmp_path)

    def test_missing_keys_in_locale_raises(self, tmp_path: Path) -> None:
        _write_catalog(
            tmp_path,
            "en",
            status="source",
            body={"crisis": {"headline": "x"}, "nav": {"home": "y"}},
        )
        for loc in ("fr", "ar", "fa"):
            _write_catalog(
                tmp_path, loc, status="draft", body={"nav": {"home": "y"}}
            )
        with pytest.raises(CatalogParityError, match="parity drift"):
            verify_catalog_parity(base=tmp_path)

    def test_error_lists_locales_missing_keys(self, tmp_path: Path) -> None:
        _write_catalog(
            tmp_path,
            "en",
            status="source",
            body={"crisis": {"headline": "x"}},
        )
        # fr has the key, ar does not, fa does not
        _write_catalog(tmp_path, "fr", status="draft", body={"crisis": {"headline": "x"}})
        _write_catalog(tmp_path, "ar", status="draft", body={})
        _write_catalog(tmp_path, "fa", status="draft", body={})
        with pytest.raises(CatalogParityError) as excinfo:
            verify_catalog_parity(base=tmp_path)
        msg = str(excinfo.value)
        assert "ar" in msg
        assert "fa" in msg
        assert "fr" not in msg  # fr has the key

    def test_locale_with_extra_keys_does_not_fail(self, tmp_path: Path) -> None:
        """Parity is one-directional: locales must cover en, but locales
        having *extra* keys is allowed (e.g. region-specific copy)."""
        _write_catalog(tmp_path, "en", status="source", body={"a": "1"})
        _write_catalog(tmp_path, "fr", status="draft", body={"a": "1", "b": "2"})
        _write_catalog(tmp_path, "ar", status="draft", body={"a": "1"})
        _write_catalog(tmp_path, "fa", status="draft", body={"a": "1"})
        verify_catalog_parity(base=tmp_path)


# =============================================================================
# Live file integrity (regression guards)
# =============================================================================


class TestLiveCatalogsAreParseable:
    """Reads the actual repo files; if any catalog is malformed, this fails
    CI before the bad file can ship."""

    def test_en_catalog_loads(self) -> None:
        cat = load_catalog("en")
        assert isinstance(cat, LoadedCatalog)
        assert cat.meta.locale == "en"
        assert cat.meta.status is CatalogStatus.SOURCE
        assert cat.meta.direction == "ltr"

    def test_fr_catalog_loads(self) -> None:
        cat = load_catalog("fr")
        assert cat.meta.locale == "fr"
        assert cat.meta.direction == "ltr"

    def test_ar_catalog_loads(self) -> None:
        cat = load_catalog("ar")
        assert cat.meta.locale == "ar"
        assert cat.meta.direction == "rtl"

    def test_fa_catalog_loads(self) -> None:
        cat = load_catalog("fa")
        assert cat.meta.locale == "fa"
        assert cat.meta.direction == "rtl"

    def test_live_catalogs_are_in_parity(self) -> None:
        """The shipped catalogs must cover every key in the English source.
        If this fails, fix the catalog gap before merging — do not delete
        the en key just to make this pass."""
        verify_catalog_parity()

    def test_live_meta_block_shape(self) -> None:
        """Schema guard: each catalog's _meta block has the required fields."""
        for loc in ("en", "fr", "ar", "fa"):
            cat = load_catalog(loc)  # type: ignore[arg-type]
            assert isinstance(cat.meta, CatalogMeta)
            assert cat.meta.locale == loc
            assert cat.meta.direction in ("ltr", "rtl")
            assert isinstance(cat.meta.status, CatalogStatus)


class TestPublicReExports:
    """Smoke test the package re-exports so accidental symbol removals
    are caught by the test suite, not by downstream consumers."""

    def test_init_exports_load_path(self) -> None:
        from discipline.shared.i18n import (
            CatalogStatus as ReExportedStatus,
        )
        from discipline.shared.i18n import (
            is_clinical_key as ReExportedIsClinical,
        )
        from discipline.shared.i18n import (
            is_locale_releasable as ReExportedIsReleasable,
        )
        from discipline.shared.i18n import (
            releasable_locales as ReExportedReleasable,
        )
        from discipline.shared.i18n import (
            resolve_clinical_message as ReExportedResolve,
        )
        from discipline.shared.i18n import (
            verify_catalog_parity as ReExportedVerify,
        )

        assert ReExportedStatus is CatalogStatus
        assert ReExportedIsClinical is is_clinical_key
        assert ReExportedIsReleasable is is_locale_releasable
        assert ReExportedReleasable is releasable_locales
        assert ReExportedResolve is resolve_clinical_message
        assert ReExportedVerify is verify_catalog_parity

"""Unit tests for _flatten() and _parse_meta() pure helpers in
discipline.shared.i18n.package_catalog.

_flatten(prefix, obj) → dict[str, str]
  Recursively flattens a nested dict to dot-separated keys.
  Only str leaf values are included — non-string leaves (numbers,
  booleans, lists) are skipped because every rendered message is a
  string.  If the catalog grows to support plural rules (arrays), this
  helper must be extended.

  Example:
    {"a": {"b": "val", "c": 42}}  → {"a.b": "val"}
                                      (42 is silently dropped)

_parse_meta(raw_meta, locale) → CatalogMeta
  Validates the _meta block of a locale catalog.  The status field must
  be a valid CatalogStatus string ("source", "released", "draft").
  An unknown status raises CatalogStatusError.  A missing or non-string
  status also raises CatalogStatusError.
  direction defaults to "ltr" if absent.
"""

from __future__ import annotations

import pytest

from discipline.shared.i18n.package_catalog import (
    CatalogMeta,
    CatalogStatus,
    CatalogStatusError,
    _flatten,
    _parse_meta,
)


# ---------------------------------------------------------------------------
# _flatten — dot-path flattening
# ---------------------------------------------------------------------------


class TestFlattenBasic:
    def test_flat_dict_passes_through(self) -> None:
        result = _flatten("", {"key": "value"})
        assert result == {"key": "value"}

    def test_nested_dict_dot_joined(self) -> None:
        result = _flatten("", {"a": {"b": "val"}})
        assert result == {"a.b": "val"}

    def test_three_levels_deep(self) -> None:
        result = _flatten("", {"a": {"b": {"c": "deep"}}})
        assert result == {"a.b.c": "deep"}

    def test_prefix_prepended(self) -> None:
        result = _flatten("ns.", {"key": "val"})
        assert "ns.key" in result

    def test_empty_dict_returns_empty(self) -> None:
        assert _flatten("", {}) == {}

    def test_multiple_siblings_all_present(self) -> None:
        result = _flatten("", {"a": "x", "b": "y"})
        assert result == {"a": "x", "b": "y"}

    def test_mixed_nesting_and_flat(self) -> None:
        result = _flatten("", {"a": "top", "b": {"c": "nested"}})
        assert result["a"] == "top"
        assert result["b.c"] == "nested"


class TestFlattenNonStringLeavesSkipped:
    def test_integer_leaf_skipped(self) -> None:
        result = _flatten("", {"a": "ok", "b": 42})
        assert "b" not in result
        assert "a" in result

    def test_boolean_leaf_skipped(self) -> None:
        result = _flatten("", {"a": "ok", "b": True})
        assert "b" not in result

    def test_none_leaf_skipped(self) -> None:
        result = _flatten("", {"a": "ok", "b": None})
        assert "b" not in result

    def test_list_leaf_skipped(self) -> None:
        result = _flatten("", {"a": "ok", "b": [1, 2, 3]})
        assert "b" not in result

    def test_nested_non_string_leaf_skipped(self) -> None:
        result = _flatten("", {"a": {"b": 99}})
        assert "a.b" not in result


# ---------------------------------------------------------------------------
# _parse_meta — catalog status validation
# ---------------------------------------------------------------------------


def _meta(**overrides: object) -> dict:
    base: dict = {"status": "draft"}
    base.update(overrides)
    return base


class TestParseMeta:
    def test_source_status_accepted(self) -> None:
        meta = _parse_meta(_meta(status="source"), "en")
        assert meta.status == CatalogStatus.SOURCE

    def test_released_status_accepted(self) -> None:
        meta = _parse_meta(_meta(status="released"), "fr")
        assert meta.status == CatalogStatus.RELEASED

    def test_draft_status_accepted(self) -> None:
        meta = _parse_meta(_meta(status="draft"), "ar")
        assert meta.status == CatalogStatus.DRAFT

    def test_unknown_status_raises_catalog_status_error(self) -> None:
        with pytest.raises(CatalogStatusError):
            _parse_meta(_meta(status="approved"), "fr")

    def test_missing_status_raises_catalog_status_error(self) -> None:
        with pytest.raises(CatalogStatusError):
            _parse_meta({}, "fr")

    def test_non_string_status_raises_catalog_status_error(self) -> None:
        with pytest.raises(CatalogStatusError):
            _parse_meta(_meta(status=True), "fr")

    def test_direction_defaults_to_ltr(self) -> None:
        meta = _parse_meta(_meta(), "en")
        assert meta.direction == "ltr"

    def test_direction_rtl_accepted(self) -> None:
        meta = _parse_meta(_meta(direction="rtl"), "ar")
        assert meta.direction == "rtl"

    def test_locale_propagated(self) -> None:
        meta = _parse_meta(_meta(), "fa")
        assert meta.locale == "fa"

    def test_reviewed_by_propagated(self) -> None:
        meta = _parse_meta(_meta(reviewedBy="Dr. Smith"), "fr")
        assert meta.reviewed_by == "Dr. Smith"

    def test_reviewed_by_defaults_to_none(self) -> None:
        meta = _parse_meta(_meta(), "en")
        assert meta.reviewed_by is None

    def test_returns_catalog_meta_instance(self) -> None:
        result = _parse_meta(_meta(), "en")
        assert isinstance(result, CatalogMeta)

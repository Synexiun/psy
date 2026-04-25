"""Unit tests for _flatten() and _parse_meta() pure helpers in
discipline.shared.i18n.package_catalog.

_flatten(prefix, obj) → dict[str, str]
  Recursively flattens a nested dict into dot-notation keys.
  Non-string leaves (numbers, booleans, lists) are silently skipped — only
  string values become messages.  This is intentional: plural rules and arrays
  are not yet supported; skipping is preferable to raising to keep catalog
  loading forward-compatible.

_parse_meta(raw_meta, locale) → CatalogMeta
  Parses the _meta block from a raw catalog JSON dict.
  Raises CatalogStatusError when _meta.status is missing, not a string, or
  not one of the three valid CatalogStatus values ("source", "released",
  "draft").
  Defaults direction to "ltr" when the key is absent.
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
# _flatten — flat input (no nesting)
# ---------------------------------------------------------------------------


class TestFlattenFlatInput:
    def test_empty_dict_returns_empty(self) -> None:
        assert _flatten("", {}) == {}

    def test_single_key_returned_unchanged(self) -> None:
        assert _flatten("", {"hello": "world"}) == {"hello": "world"}

    def test_multiple_flat_keys(self) -> None:
        inp = {"a": "va", "b": "vb", "c": "vc"}
        assert _flatten("", inp) == inp

    def test_prefix_prepended_to_each_key(self) -> None:
        result = _flatten("ns.", {"key": "val"})
        assert result == {"ns.key": "val"}

    def test_empty_prefix_leaves_keys_unchanged(self) -> None:
        result = _flatten("", {"x": "y"})
        assert result == {"x": "y"}


# ---------------------------------------------------------------------------
# _flatten — nested dicts (recursive)
# ---------------------------------------------------------------------------


class TestFlattenNestedInput:
    def test_one_level_nesting(self) -> None:
        inp = {"nav": {"home": "Home", "tools": "Tools"}}
        result = _flatten("", inp)
        assert result == {"nav.home": "Home", "nav.tools": "Tools"}

    def test_two_level_nesting(self) -> None:
        inp = {"crisis": {"button": {"call": "Call now"}}}
        result = _flatten("", inp)
        assert result == {"crisis.button.call": "Call now"}

    def test_mixed_flat_and_nested(self) -> None:
        inp = {"title": "App", "nav": {"home": "Home"}}
        result = _flatten("", inp)
        assert result == {"title": "App", "nav.home": "Home"}

    def test_siblings_at_same_level(self) -> None:
        inp = {
            "assessment": {
                "phq9": {"label": "Depression screen"},
                "gad7": {"label": "Anxiety screen"},
            }
        }
        result = _flatten("", inp)
        assert result == {
            "assessment.phq9.label": "Depression screen",
            "assessment.gad7.label": "Anxiety screen",
        }

    def test_empty_nested_dict_contributes_nothing(self) -> None:
        result = _flatten("", {"nav": {}})
        assert result == {}


# ---------------------------------------------------------------------------
# _flatten — non-string leaf handling (silent skip)
# ---------------------------------------------------------------------------


class TestFlattenNonStringLeaves:
    def test_integer_leaf_is_skipped(self) -> None:
        result = _flatten("", {"count": 42})
        assert result == {}

    def test_float_leaf_is_skipped(self) -> None:
        result = _flatten("", {"score": 7.5})
        assert result == {}

    def test_boolean_leaf_is_skipped(self) -> None:
        result = _flatten("", {"active": True})
        assert result == {}

    def test_none_leaf_is_skipped(self) -> None:
        result = _flatten("", {"key": None})
        assert result == {}

    def test_list_leaf_is_skipped(self) -> None:
        result = _flatten("", {"items": ["a", "b", "c"]})
        assert result == {}

    def test_string_siblings_of_skipped_values_are_kept(self) -> None:
        result = _flatten("", {"label": "Hello", "count": 42})
        assert result == {"label": "Hello"}
        assert "count" not in result

    def test_skipped_leaf_in_nested_dict(self) -> None:
        result = _flatten("", {"nav": {"home": "Home", "count": 5}})
        assert result == {"nav.home": "Home"}
        assert "nav.count" not in result


# ---------------------------------------------------------------------------
# _parse_meta — valid status values
# ---------------------------------------------------------------------------


class TestParseMetaValidStatus:
    def _meta(self, **kwargs) -> dict:
        base = {"status": "source", "direction": "ltr"}
        base.update(kwargs)
        return base

    def test_source_status_accepted(self) -> None:
        result = _parse_meta({"status": "source"}, "en")
        assert result.status == CatalogStatus.SOURCE

    def test_released_status_accepted(self) -> None:
        result = _parse_meta({"status": "released"}, "fr")
        assert result.status == CatalogStatus.RELEASED

    def test_draft_status_accepted(self) -> None:
        result = _parse_meta({"status": "draft"}, "ar")
        assert result.status == CatalogStatus.DRAFT

    def test_locale_propagated(self) -> None:
        result = _parse_meta({"status": "source"}, "en")
        assert result.locale == "en"

    def test_direction_defaults_to_ltr_when_absent(self) -> None:
        result = _parse_meta({"status": "source"}, "en")
        assert result.direction == "ltr"

    def test_direction_rtl_accepted(self) -> None:
        result = _parse_meta({"status": "released", "direction": "rtl"}, "ar")
        assert result.direction == "rtl"

    def test_reviewed_by_none_when_absent(self) -> None:
        result = _parse_meta({"status": "draft"}, "fa")
        assert result.reviewed_by is None

    def test_reviewed_by_populated(self) -> None:
        result = _parse_meta(
            {"status": "released", "reviewedBy": "Dr. Ahmed"}, "ar"
        )
        assert result.reviewed_by == "Dr. Ahmed"

    def test_result_is_catalog_meta_instance(self) -> None:
        result = _parse_meta({"status": "source"}, "en")
        assert isinstance(result, CatalogMeta)


# ---------------------------------------------------------------------------
# _parse_meta — invalid status (raises CatalogStatusError)
# ---------------------------------------------------------------------------


class TestParseMetaInvalidStatus:
    def test_missing_status_raises(self) -> None:
        with pytest.raises(CatalogStatusError):
            _parse_meta({}, "en")

    def test_none_status_raises(self) -> None:
        with pytest.raises(CatalogStatusError):
            _parse_meta({"status": None}, "en")

    def test_int_status_raises(self) -> None:
        with pytest.raises(CatalogStatusError):
            _parse_meta({"status": 1}, "en")

    def test_list_status_raises(self) -> None:
        with pytest.raises(CatalogStatusError):
            _parse_meta({"status": ["source"]}, "en")

    def test_unknown_string_status_raises(self) -> None:
        with pytest.raises(CatalogStatusError):
            _parse_meta({"status": "approved"}, "en")

    def test_empty_string_status_raises(self) -> None:
        with pytest.raises(CatalogStatusError):
            _parse_meta({"status": ""}, "en")

    def test_uppercase_status_raises(self) -> None:
        # CatalogStatus values are lowercase; uppercase should not be silently accepted
        with pytest.raises(CatalogStatusError):
            _parse_meta({"status": "SOURCE"}, "en")

    def test_error_is_subclass_of_value_error(self) -> None:
        with pytest.raises(ValueError):
            _parse_meta({"status": "invalid"}, "en")

    def test_error_message_mentions_locale(self) -> None:
        with pytest.raises(CatalogStatusError, match="fr"):
            _parse_meta({"status": "bad"}, "fr")

"""Unit tests for pure helpers in discipline.psychometric.scoring.dass21.

_validate_item(index_1, value) → int
  Same bool-before-int guard as HADS; 0-3 Likert range.

_severity_band(score, thresholds, subscale_name) → Severity
  Unlike HADS's module-constant thresholds, DASS-21 passes the threshold
  tuple as a parameter — callers inject the right per-subscale thresholds.
  Five bands: normal, mild, moderate, severe, extremely_severe (Antony 1998).
  Raises InvalidResponseError when score exceeds the thresholds' max (21).

_worst_severity(*severities) → Severity
  Variadic (any number of subscale bands); returns the worst using
  _SEVERITY_RANK ordering: normal < mild < moderate < severe < extremely_severe.
"""

from __future__ import annotations

import pytest

from discipline.psychometric.scoring.dass21 import (
    DASS21_ANXIETY_POSITIONS,
    DASS21_ANXIETY_SEVERITY_THRESHOLDS,
    DASS21_DEPRESSION_POSITIONS,
    DASS21_DEPRESSION_SEVERITY_THRESHOLDS,
    DASS21_STRESS_POSITIONS,
    DASS21_STRESS_SEVERITY_THRESHOLDS,
    InvalidResponseError,
    _severity_band,
    _subscale_sum,
    _validate_item,
    _worst_severity,
)


# ---------------------------------------------------------------------------
# _validate_item — accepted inputs
# ---------------------------------------------------------------------------


class TestValidateItemAccepted:
    def test_zero_accepted(self) -> None:
        assert _validate_item(1, 0) == 0

    def test_three_accepted(self) -> None:
        assert _validate_item(1, 3) == 3

    def test_all_valid_values_returned_unchanged(self) -> None:
        for v in range(4):
            assert _validate_item(1, v) == v


class TestValidateItemBoolRejection:
    def test_true_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_item(1, True)

    def test_false_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_item(1, False)


class TestValidateItemRangeRejection:
    def test_minus_1_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_item(1, -1)

    def test_4_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_item(1, 4)

    def test_error_mentions_item_index(self) -> None:
        with pytest.raises(InvalidResponseError, match="5"):
            _validate_item(5, 99)


class TestValidateItemTypeRejection:
    def test_string_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_item(1, "2")

    def test_none_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_item(1, None)

    def test_float_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_item(1, 1.0)


# ---------------------------------------------------------------------------
# _severity_band — depression thresholds (Antony 1998)
# Bands: 0-4=normal, 5-6=mild, 7-10=moderate, 11-13=severe, 14-21=extremely_severe
# ---------------------------------------------------------------------------


class TestSeverityBandDepression:
    def test_score_0_is_normal(self) -> None:
        assert _severity_band(0, DASS21_DEPRESSION_SEVERITY_THRESHOLDS, "depression") == "normal"

    def test_score_4_is_normal(self) -> None:
        assert _severity_band(4, DASS21_DEPRESSION_SEVERITY_THRESHOLDS, "depression") == "normal"

    def test_score_5_is_mild(self) -> None:
        assert _severity_band(5, DASS21_DEPRESSION_SEVERITY_THRESHOLDS, "depression") == "mild"

    def test_score_6_is_mild(self) -> None:
        assert _severity_band(6, DASS21_DEPRESSION_SEVERITY_THRESHOLDS, "depression") == "mild"

    def test_score_7_is_moderate(self) -> None:
        assert _severity_band(7, DASS21_DEPRESSION_SEVERITY_THRESHOLDS, "depression") == "moderate"

    def test_score_10_is_moderate(self) -> None:
        assert _severity_band(10, DASS21_DEPRESSION_SEVERITY_THRESHOLDS, "depression") == "moderate"

    def test_score_11_is_severe(self) -> None:
        assert _severity_band(11, DASS21_DEPRESSION_SEVERITY_THRESHOLDS, "depression") == "severe"

    def test_score_13_is_severe(self) -> None:
        assert _severity_band(13, DASS21_DEPRESSION_SEVERITY_THRESHOLDS, "depression") == "severe"

    def test_score_14_is_extremely_severe(self) -> None:
        assert _severity_band(14, DASS21_DEPRESSION_SEVERITY_THRESHOLDS, "depression") == "extremely_severe"

    def test_score_21_is_extremely_severe(self) -> None:
        assert _severity_band(21, DASS21_DEPRESSION_SEVERITY_THRESHOLDS, "depression") == "extremely_severe"

    def test_score_22_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _severity_band(22, DASS21_DEPRESSION_SEVERITY_THRESHOLDS, "depression")


# ---------------------------------------------------------------------------
# _severity_band — anxiety thresholds
# Bands: 0-3=normal, 4-5=mild, 6-7=moderate, 8-9=severe, 10-21=extremely_severe
# ---------------------------------------------------------------------------


class TestSeverityBandAnxiety:
    def test_score_3_is_normal(self) -> None:
        assert _severity_band(3, DASS21_ANXIETY_SEVERITY_THRESHOLDS, "anxiety") == "normal"

    def test_score_4_is_mild(self) -> None:
        assert _severity_band(4, DASS21_ANXIETY_SEVERITY_THRESHOLDS, "anxiety") == "mild"

    def test_score_6_is_moderate(self) -> None:
        assert _severity_band(6, DASS21_ANXIETY_SEVERITY_THRESHOLDS, "anxiety") == "moderate"

    def test_score_8_is_severe(self) -> None:
        assert _severity_band(8, DASS21_ANXIETY_SEVERITY_THRESHOLDS, "anxiety") == "severe"

    def test_score_10_is_extremely_severe(self) -> None:
        assert _severity_band(10, DASS21_ANXIETY_SEVERITY_THRESHOLDS, "anxiety") == "extremely_severe"


# ---------------------------------------------------------------------------
# _worst_severity — variadic ordering
# ---------------------------------------------------------------------------


class TestWorstSeverity:
    def test_single_value_returned(self) -> None:
        assert _worst_severity("moderate") == "moderate"

    def test_two_values_worst_returned(self) -> None:
        assert _worst_severity("mild", "severe") == "severe"

    def test_three_values_worst_returned(self) -> None:
        assert _worst_severity("normal", "moderate", "mild") == "moderate"

    def test_extremely_severe_beats_severe(self) -> None:
        assert _worst_severity("severe", "extremely_severe") == "extremely_severe"

    def test_all_same_returns_that_level(self) -> None:
        assert _worst_severity("mild", "mild", "mild") == "mild"

    def test_commutative(self) -> None:
        assert _worst_severity("normal", "extremely_severe") == _worst_severity("extremely_severe", "normal")

    def test_normal_is_least_severe(self) -> None:
        assert _worst_severity("normal", "mild") == "mild"

    def test_full_ranking_traversal(self) -> None:
        result = _worst_severity("normal", "mild", "moderate", "severe", "extremely_severe")
        assert result == "extremely_severe"


# ---------------------------------------------------------------------------
# _subscale_sum — positions coverage
# ---------------------------------------------------------------------------


class TestSubscaleSum:
    def test_seven_depression_items_all_one(self) -> None:
        items = (1,) * 21
        assert _subscale_sum(items, DASS21_DEPRESSION_POSITIONS) == 7

    def test_seven_anxiety_items_all_one(self) -> None:
        items = (1,) * 21
        assert _subscale_sum(items, DASS21_ANXIETY_POSITIONS) == 7

    def test_seven_stress_items_all_one(self) -> None:
        items = (1,) * 21
        assert _subscale_sum(items, DASS21_STRESS_POSITIONS) == 7

    def test_all_zeros_sum_is_zero(self) -> None:
        items = (0,) * 21
        assert _subscale_sum(items, DASS21_DEPRESSION_POSITIONS) == 0

    def test_all_threes_sum_is_21(self) -> None:
        items = (3,) * 21
        assert _subscale_sum(items, DASS21_DEPRESSION_POSITIONS) == 21

    def test_subscales_cover_all_21_positions(self) -> None:
        all_pos = (
            set(DASS21_DEPRESSION_POSITIONS)
            | set(DASS21_ANXIETY_POSITIONS)
            | set(DASS21_STRESS_POSITIONS)
        )
        assert all_pos == set(range(1, 22))

    def test_subscales_are_mutually_disjoint(self) -> None:
        d = set(DASS21_DEPRESSION_POSITIONS)
        a = set(DASS21_ANXIETY_POSITIONS)
        s = set(DASS21_STRESS_POSITIONS)
        assert d.isdisjoint(a)
        assert d.isdisjoint(s)
        assert a.isdisjoint(s)

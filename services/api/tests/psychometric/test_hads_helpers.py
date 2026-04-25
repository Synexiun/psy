"""Unit tests for pure helpers in discipline.psychometric.scoring.hads.

Functions tested:
  _validate_item(index_1, value) → int
    Validates a single 0-3 Likert item.  Rejects booleans (they are a
    subclass of int in Python, so isinstance(True, int) is True — the
    bool guard must come FIRST to catch this).  Rejects values outside
    0-3.  Returns the validated int unchanged.

  _severity_band(score) → Severity
    Maps a 0-21 subscale score to one of "normal" | "mild" | "moderate" |
    "severe" using HADS_SEVERITY_THRESHOLDS (Snaith 2003):
      0-7  → normal, 8-10 → mild, 11-14 → moderate, 15-21 → severe.
    Raises InvalidResponseError if score > 21.

  _worse_severity(a, b) → Severity
    Returns whichever of two severity strings is clinically worse.
    Order: normal < mild < moderate < severe.

  _apply_reverse_keying(items) → tuple[int, ...]
    Flips the 6 reverse-keyed items (positions 2,4,6,7,12,14) via
    ITEM_MAX - raw_value so higher = more distressed for all items.
    Forward-keyed items are unchanged.

  _subscale_sum(flipped, positions_1_indexed) → int
    Sums items at 1-indexed positions from the already-flipped tuple.
"""

from __future__ import annotations

import pytest

from discipline.psychometric.scoring.hads import (
    HADS_ANXIETY_POSITIONS,
    HADS_DEPRESSION_POSITIONS,
    HADS_REVERSE_ITEMS,
    HADS_SEVERITY_THRESHOLDS,
    ITEM_MAX,
    ITEM_MIN,
    InvalidResponseError,
    _apply_reverse_keying,
    _severity_band,
    _subscale_sum,
    _validate_item,
    _worse_severity,
)


# ---------------------------------------------------------------------------
# _validate_item — accepted inputs
# ---------------------------------------------------------------------------


class TestValidateItemAccepted:
    def test_zero_accepted(self) -> None:
        assert _validate_item(1, 0) == 0

    def test_one_accepted(self) -> None:
        assert _validate_item(1, 1) == 1

    def test_two_accepted(self) -> None:
        assert _validate_item(1, 2) == 2

    def test_three_accepted(self) -> None:
        assert _validate_item(1, 3) == 3

    def test_returns_the_value_unchanged(self) -> None:
        for v in range(4):
            assert _validate_item(5, v) == v


# ---------------------------------------------------------------------------
# _validate_item — boolean rejection (Python int subtype trap)
# ---------------------------------------------------------------------------


class TestValidateItemBooleanRejection:
    def test_true_raises_invalid_response_error(self) -> None:
        # bool is a subclass of int; without explicit isinstance(v, bool) guard
        # True would silently pass as 1.
        with pytest.raises(InvalidResponseError):
            _validate_item(1, True)

    def test_false_raises_invalid_response_error(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_item(1, False)

    def test_boolean_error_is_subclass_of_value_error(self) -> None:
        with pytest.raises(ValueError):
            _validate_item(1, True)


# ---------------------------------------------------------------------------
# _validate_item — range rejection
# ---------------------------------------------------------------------------


class TestValidateItemRangeRejection:
    def test_minus_1_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_item(1, -1)

    def test_4_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_item(1, 4)

    def test_100_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_item(1, 100)

    def test_error_mentions_item_index(self) -> None:
        with pytest.raises(InvalidResponseError, match="7"):
            _validate_item(7, 99)


# ---------------------------------------------------------------------------
# _validate_item — type rejection (non-int, non-bool)
# ---------------------------------------------------------------------------


class TestValidateItemTypeRejection:
    def test_string_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_item(1, "2")

    def test_float_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_item(1, 1.0)

    def test_none_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_item(1, None)


# ---------------------------------------------------------------------------
# _severity_band — valid scores (Snaith 2003 thresholds)
# ---------------------------------------------------------------------------


class TestSeverityBand:
    def test_score_0_is_normal(self) -> None:
        assert _severity_band(0) == "normal"

    def test_score_7_is_normal(self) -> None:
        assert _severity_band(7) == "normal"

    def test_score_8_is_mild(self) -> None:
        assert _severity_band(8) == "mild"

    def test_score_10_is_mild(self) -> None:
        assert _severity_band(10) == "mild"

    def test_score_11_is_moderate(self) -> None:
        assert _severity_band(11) == "moderate"

    def test_score_14_is_moderate(self) -> None:
        assert _severity_band(14) == "moderate"

    def test_score_15_is_severe(self) -> None:
        assert _severity_band(15) == "severe"

    def test_score_21_is_severe(self) -> None:
        assert _severity_band(21) == "severe"

    def test_boundary_7_to_8(self) -> None:
        assert _severity_band(7) != _severity_band(8)

    def test_boundary_10_to_11(self) -> None:
        assert _severity_band(10) != _severity_band(11)

    def test_boundary_14_to_15(self) -> None:
        assert _severity_band(14) != _severity_band(15)

    def test_score_22_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _severity_band(22)

    def test_score_100_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _severity_band(100)


# ---------------------------------------------------------------------------
# _worse_severity — ordering (normal < mild < moderate < severe)
# ---------------------------------------------------------------------------


class TestWorseSeverity:
    def test_severe_beats_moderate(self) -> None:
        assert _worse_severity("severe", "moderate") == "severe"

    def test_moderate_beats_mild(self) -> None:
        assert _worse_severity("moderate", "mild") == "moderate"

    def test_mild_beats_normal(self) -> None:
        assert _worse_severity("mild", "normal") == "mild"

    def test_equal_severities_returned(self) -> None:
        assert _worse_severity("moderate", "moderate") == "moderate"

    def test_commutative_severe_normal(self) -> None:
        assert _worse_severity("normal", "severe") == "severe"

    def test_commutative_mild_moderate(self) -> None:
        assert _worse_severity("mild", "moderate") == "moderate"

    def test_all_equal_normal(self) -> None:
        assert _worse_severity("normal", "normal") == "normal"


# ---------------------------------------------------------------------------
# _apply_reverse_keying — forward-keyed items unchanged
# ---------------------------------------------------------------------------


_ALL_ZEROS: tuple[int, ...] = (0,) * 14
_ALL_THREES: tuple[int, ...] = (3,) * 14


class TestApplyReverseKeyingForwardItems:
    def test_forward_items_unchanged_at_zero(self) -> None:
        result = _apply_reverse_keying(_ALL_ZEROS)
        # positions 1,3,5,8,9,10,11,13 are forward-keyed (not in HADS_REVERSE_ITEMS)
        forward_positions = [
            p for p in range(1, 15) if p not in HADS_REVERSE_ITEMS
        ]
        for pos in forward_positions:
            assert result[pos - 1] == 0, f"Position {pos} should be unchanged"

    def test_forward_items_unchanged_at_three(self) -> None:
        result = _apply_reverse_keying(_ALL_THREES)
        forward_positions = [
            p for p in range(1, 15) if p not in HADS_REVERSE_ITEMS
        ]
        for pos in forward_positions:
            assert result[pos - 1] == 3, f"Position {pos} should be unchanged"


# ---------------------------------------------------------------------------
# _apply_reverse_keying — reverse-keyed items flipped
# ---------------------------------------------------------------------------


class TestApplyReverseKeyingReverseItems:
    def test_zero_flips_to_three(self) -> None:
        result = _apply_reverse_keying(_ALL_ZEROS)
        for pos in HADS_REVERSE_ITEMS:
            assert result[pos - 1] == ITEM_MAX, f"Position {pos}: 0 → {ITEM_MAX}"

    def test_three_flips_to_zero(self) -> None:
        result = _apply_reverse_keying(_ALL_THREES)
        for pos in HADS_REVERSE_ITEMS:
            assert result[pos - 1] == 0, f"Position {pos}: 3 → 0"

    def test_one_flips_to_two(self) -> None:
        items = (1,) * 14
        result = _apply_reverse_keying(items)
        for pos in HADS_REVERSE_ITEMS:
            assert result[pos - 1] == 2

    def test_result_length_preserved(self) -> None:
        result = _apply_reverse_keying(_ALL_ZEROS)
        assert len(result) == 14

    def test_result_is_tuple(self) -> None:
        result = _apply_reverse_keying(_ALL_ZEROS)
        assert isinstance(result, tuple)


# ---------------------------------------------------------------------------
# _subscale_sum
# ---------------------------------------------------------------------------


class TestSubscaleSum:
    def test_anxiety_positions_all_one(self) -> None:
        # All 1s → 7 anxiety items → sum = 7
        items = (1,) * 14
        assert _subscale_sum(items, HADS_ANXIETY_POSITIONS) == 7

    def test_depression_positions_all_one(self) -> None:
        items = (1,) * 14
        assert _subscale_sum(items, HADS_DEPRESSION_POSITIONS) == 7

    def test_all_zeros_sum_is_zero(self) -> None:
        assert _subscale_sum(_ALL_ZEROS, HADS_ANXIETY_POSITIONS) == 0

    def test_all_threes_sum_is_21(self) -> None:
        assert _subscale_sum(_ALL_THREES, HADS_ANXIETY_POSITIONS) == 21
        assert _subscale_sum(_ALL_THREES, HADS_DEPRESSION_POSITIONS) == 21

    def test_subscales_are_disjoint_positions(self) -> None:
        # Anxiety and depression items use disjoint positions
        anxiety_set = set(HADS_ANXIETY_POSITIONS)
        depression_set = set(HADS_DEPRESSION_POSITIONS)
        assert anxiety_set.isdisjoint(depression_set)

    def test_subscales_cover_all_14_positions(self) -> None:
        all_positions = set(HADS_ANXIETY_POSITIONS) | set(HADS_DEPRESSION_POSITIONS)
        assert all_positions == set(range(1, 15))

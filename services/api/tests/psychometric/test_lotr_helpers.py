"""Unit tests for _validate_item() and _scored_contribution() pure helpers in
discipline.psychometric.scoring.lotr.

_validate_item(index_1, value) → int
  LOT-R is a 10-item form but only 6 items are scored; the remaining 4 are
  fillers.  ALL 10 items are validated with the same 0-4 range check — a
  value outside [0,4] in a filler position is still a wire-format violation.

_scored_contribution(index_1, value) → int
  Returns the post-flip contribution of a SCORED item to the total.
  Reverse items (positions 3, 7, 9) are flipped via (ITEM_MIN + ITEM_MAX) - value
  = 4 - value.  Forward scored items pass through unchanged.
  Filler items (positions 2, 5, 6, 8) NEVER reach this helper — it is only
  called for LOTR_SCORED_POSITIONS = (1, 3, 4, 7, 9, 10).
"""

from __future__ import annotations

import pytest

from discipline.psychometric.scoring.lotr import (
    ITEM_MAX,
    ITEM_MIN,
    LOTR_REVERSE_ITEMS,
    LOTR_SCORED_POSITIONS,
    InvalidResponseError,
    _scored_contribution,
    _validate_item,
)


# ---------------------------------------------------------------------------
# _validate_item — 0-4 Likert; all 10 positions validated identically
# ---------------------------------------------------------------------------


class TestValidateItemLotrAccepted:
    def test_zero_accepted(self) -> None:
        assert _validate_item(1, 0) == 0

    def test_four_accepted(self) -> None:
        assert _validate_item(1, 4) == 4

    def test_all_valid_values_returned_unchanged(self) -> None:
        for v in range(5):
            assert _validate_item(3, v) == v

    def test_filler_item_position_validated_same_way(self) -> None:
        # Position 2 is a filler but still validated 0-4
        assert _validate_item(2, 3) == 3


class TestValidateItemLotrBoolRejection:
    def test_true_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_item(1, True)

    def test_false_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_item(1, False)


class TestValidateItemLotrRangeRejection:
    def test_five_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_item(1, 5)

    def test_minus_1_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_item(1, -1)

    def test_error_mentions_item_index(self) -> None:
        with pytest.raises(InvalidResponseError, match="8"):
            _validate_item(8, 99)


# ---------------------------------------------------------------------------
# _scored_contribution — reverse-keyed items flipped
# Reverse positions: 3, 7, 9
# Forward scored: 1, 4, 10
# ---------------------------------------------------------------------------


class TestScoredContributionReverseItems:
    def test_reverse_item_zero_becomes_four(self) -> None:
        for pos in LOTR_REVERSE_ITEMS:
            assert _scored_contribution(pos, 0) == 4

    def test_reverse_item_four_becomes_zero(self) -> None:
        for pos in LOTR_REVERSE_ITEMS:
            assert _scored_contribution(pos, 4) == 0

    def test_reverse_item_one_becomes_three(self) -> None:
        for pos in LOTR_REVERSE_ITEMS:
            assert _scored_contribution(pos, 1) == 3

    def test_reverse_item_two_stays_two(self) -> None:
        # Midpoint is its own mirror
        for pos in LOTR_REVERSE_ITEMS:
            assert _scored_contribution(pos, 2) == 2

    def test_double_contribution_is_identity(self) -> None:
        pos = LOTR_REVERSE_ITEMS[0]
        for v in range(5):
            assert _scored_contribution(pos, _scored_contribution(pos, v)) == v

    def test_formula_is_item_min_plus_item_max_minus_value(self) -> None:
        pos = LOTR_REVERSE_ITEMS[0]
        for v in range(5):
            assert _scored_contribution(pos, v) == (ITEM_MIN + ITEM_MAX) - v


class TestScoredContributionForwardItems:
    def _forward_scored_positions(self) -> list[int]:
        return [p for p in LOTR_SCORED_POSITIONS if p not in LOTR_REVERSE_ITEMS]

    def test_forward_items_pass_through_unchanged(self) -> None:
        for pos in self._forward_scored_positions():
            for v in range(5):
                assert _scored_contribution(pos, v) == v, (
                    f"Forward position {pos} with value {v} should be unchanged"
                )

    def test_three_reverse_items_in_scored_set(self) -> None:
        assert len(LOTR_REVERSE_ITEMS) == 3

    def test_six_total_scored_positions(self) -> None:
        assert len(LOTR_SCORED_POSITIONS) == 6

    def test_reverse_items_are_subset_of_scored_positions(self) -> None:
        assert set(LOTR_REVERSE_ITEMS) <= set(LOTR_SCORED_POSITIONS)

    def test_filler_positions_not_in_scored(self) -> None:
        # Total items = 10; scored = 6; filler = 4
        all_positions = set(range(1, 11))
        filler = all_positions - set(LOTR_SCORED_POSITIONS)
        assert len(filler) == 4

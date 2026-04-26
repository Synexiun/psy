"""Unit tests for private scoring helpers in psychometric/scoring/ sub-modules.

_compute_subscale(items, positions) — brief_cope.py
  Sums two 1-indexed positions from a tuple.  Range 2-8 per Carver 1997.

_band(total) — ftnd.py
  Maps 0-10 FTND total to Fagerström 2012 severity label using
  FTND_SEVERITY_THRESHOLDS.  First band whose upper bound >= total wins.
  Raises InvalidResponseError when total > 10.

_apply_reverse(index_1, value) — rses.py
  Reverse-keys Rosenberg 1965 items in RSES_REVERSE_ITEMS:
  result = (ITEM_MIN + ITEM_MAX) - value = 3 - value.
  Items NOT in the set pass through unchanged.

_subscale_sum_raw(items, subscale_name) — scssf.py
  Sums RAW (pre-flip) item values for a named SCS-SF subscale.
  Uses 1-indexed SCSSF_SUBSCALES; converts to 0-indexed access.
  Subscale sums intentionally use RAW values — reverse-keying is only
  applied for the TOTAL computation.
"""

from __future__ import annotations

import pytest

from discipline.psychometric.scoring.brief_cope import _compute_subscale
from discipline.psychometric.scoring.ftnd import (
    FTND_SEVERITY_THRESHOLDS,
    _band,
)
from discipline.psychometric.scoring.rses import (
    ITEM_MAX as RSES_ITEM_MAX,
    ITEM_MIN as RSES_ITEM_MIN,
    RSES_REVERSE_ITEMS,
    _apply_reverse,
)
from discipline.psychometric.scoring.scssf import (
    SCSSF_SUBSCALES,
    _subscale_sum_raw,
)
from discipline.psychometric.scoring.ftnd import InvalidResponseError


# ---------------------------------------------------------------------------
# _compute_subscale — BRIEF-COPE 2-item subscale sum (1-indexed)
# ---------------------------------------------------------------------------


class TestComputeSubscale:
    def test_sums_two_1indexed_positions(self) -> None:
        items = (1, 2, 3, 4)
        # positions (1, 3) → items[0] + items[2] = 1 + 3 = 4
        assert _compute_subscale(items, (1, 3)) == 4

    def test_minimum_possible_subscale_sum(self) -> None:
        # both items = 1 → subscale sum = 2
        items = tuple([1] * 28)
        assert _compute_subscale(items, (1, 2)) == 2

    def test_maximum_possible_subscale_sum(self) -> None:
        # both items = 4 → subscale sum = 8
        items = tuple([4] * 28)
        assert _compute_subscale(items, (5, 7)) == 8

    def test_uses_1_indexed_not_0_indexed(self) -> None:
        # position 1 should access index 0 (first element = 9)
        items = (9, 1, 1, 1)
        assert _compute_subscale(items, (1, 2)) == 10

    def test_real_subscale_positions_from_carver_1997(self) -> None:
        # Self-distraction subscale: items 1 and 19 per Carver 1997
        items = list(range(1, 29))  # 1-indexed values equal their position
        result = _compute_subscale(tuple(items), (1, 19))
        assert result == 1 + 19  # items[0]=1, items[18]=19


# ---------------------------------------------------------------------------
# _band — FTND severity bands (Fagerström 2012)
# ---------------------------------------------------------------------------


class TestFtndBand:
    def test_zero_is_very_low(self) -> None:
        assert _band(0) == "very_low"

    def test_two_is_very_low(self) -> None:
        assert _band(2) == "very_low"

    def test_three_is_low(self) -> None:
        assert _band(3) == "low"

    def test_four_is_low(self) -> None:
        assert _band(4) == "low"

    def test_five_is_moderate(self) -> None:
        assert _band(5) == "moderate"

    def test_six_is_high(self) -> None:
        assert _band(6) == "high"

    def test_seven_is_high(self) -> None:
        assert _band(7) == "high"

    def test_eight_is_very_high(self) -> None:
        assert _band(8) == "very_high"

    def test_ten_is_very_high(self) -> None:
        assert _band(10) == "very_high"

    def test_eleven_raises_invalid_response_error(self) -> None:
        with pytest.raises(InvalidResponseError):
            _band(11)

    def test_all_thresholds_are_covered(self) -> None:
        # Every upper-bound value in FTND_SEVERITY_THRESHOLDS should return
        # its own label, not the prior label
        for upper, label in FTND_SEVERITY_THRESHOLDS:
            assert _band(upper) == label


# ---------------------------------------------------------------------------
# _apply_reverse — RSES reverse-keying (Rosenberg 1965)
# ---------------------------------------------------------------------------


class TestApplyReverse:
    def test_reverse_item_flipped(self) -> None:
        # Item 2 is in RSES_REVERSE_ITEMS; value 0 → 3 - 0 = 3
        assert _apply_reverse(2, 0) == RSES_ITEM_MIN + RSES_ITEM_MAX - 0

    def test_reverse_item_max_flipped_to_min(self) -> None:
        # value ITEM_MAX (3) → 3 - 3 = 0 = ITEM_MIN
        assert _apply_reverse(2, RSES_ITEM_MAX) == RSES_ITEM_MIN

    def test_reverse_item_min_flipped_to_max(self) -> None:
        assert _apply_reverse(2, RSES_ITEM_MIN) == RSES_ITEM_MAX

    def test_non_reverse_item_passes_through(self) -> None:
        # Item 1 is NOT in RSES_REVERSE_ITEMS — passes through unchanged
        assert 1 not in RSES_REVERSE_ITEMS
        assert _apply_reverse(1, 2) == 2

    def test_all_reverse_items_flipped(self) -> None:
        for idx in RSES_REVERSE_ITEMS:
            flipped = _apply_reverse(idx, 1)
            assert flipped == RSES_ITEM_MIN + RSES_ITEM_MAX - 1

    def test_all_non_reverse_items_pass_through(self) -> None:
        all_items = set(range(1, 11))
        non_reverse = all_items - set(RSES_REVERSE_ITEMS)
        for idx in non_reverse:
            assert _apply_reverse(idx, 2) == 2

    def test_mid_value_reverse(self) -> None:
        # ITEM_MIN + ITEM_MAX = 3; value 1 → 3 - 1 = 2
        assert _apply_reverse(2, 1) == 2

    def test_self_inverse_at_midpoint(self) -> None:
        # If there were a midpoint value 1.5 it would be self-inverse.
        # Closest integer test: flip(flip(v)) == v
        v = 1
        assert _apply_reverse(2, _apply_reverse(2, v)) == v


# ---------------------------------------------------------------------------
# _subscale_sum_raw — SCS-SF subscale sum (raw, pre-flip)
# ---------------------------------------------------------------------------


class TestSubscaleSumRaw:
    def _items_of(self, val: int = 1) -> tuple[int, ...]:
        """12-item tuple all set to val."""
        return tuple([val] * 12)

    def test_self_kindness_uses_positions_2_and_6(self) -> None:
        # SCSSF_SUBSCALES["self_kindness"] = (2, 6)
        # items[1] + items[5] = position 2 + position 6
        items = list(range(1, 13))  # 1-indexed values equal their position
        result = _subscale_sum_raw(tuple(items), "self_kindness")
        assert result == 2 + 6

    def test_self_judgment_uses_positions_11_and_12(self) -> None:
        items = list(range(1, 13))
        result = _subscale_sum_raw(tuple(items), "self_judgment")
        assert result == 11 + 12

    def test_all_subscales_return_int(self) -> None:
        items = self._items_of(3)
        for subscale_name in SCSSF_SUBSCALES:
            result = _subscale_sum_raw(items, subscale_name)
            assert isinstance(result, int)

    def test_all_ones_subscale_sum_is_2(self) -> None:
        # Two items, both 1 → sum = 2
        for subscale_name in SCSSF_SUBSCALES:
            assert _subscale_sum_raw(self._items_of(1), subscale_name) == 2

    def test_all_fives_subscale_sum_is_10(self) -> None:
        for subscale_name in SCSSF_SUBSCALES:
            assert _subscale_sum_raw(self._items_of(5), subscale_name) == 10

    def test_uses_raw_values_not_flipped(self) -> None:
        # Items at reverse positions (1, 4, 8, 9, 11, 12) should NOT be
        # pre-flipped: raw value 5 → subscale contribution is 5, not 1
        # over_identification subscale uses positions (1, 9) — both reverse items
        items = [1] * 12
        items[0] = 5   # position 1 (reverse item)
        items[8] = 5   # position 9 (reverse item)
        result = _subscale_sum_raw(tuple(items), "over_identification")
        assert result == 10  # 5 + 5, not (6-5) + (6-5) = 2

    def test_1_indexed_positions(self) -> None:
        # mindfulness uses positions (3, 7) → items[2] + items[6]
        items = [0] * 12
        items[2] = 4   # position 3
        items[6] = 3   # position 7
        result = _subscale_sum_raw(tuple(items), "mindfulness")
        assert result == 7

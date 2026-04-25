"""Unit tests for pure helpers in discipline.psychometric.scoring.bis11.

_reverse(value) → int
  Inverts a 1-4 response to its complement via ITEM_MIN + ITEM_MAX - value
  (= 5 - value).  Arithmetic reflection: 1↔4, 2↔3.  Uses constant arithmetic
  not hardcoded 5 — explicit dependency on scale bounds.

_classify(total) → Severity
  Maps a 30-120 BIS-11 total to a Stanford 2009 severity band:
    ≤51 → "low", ≤71 → "normal", ≤120 → "high".
  Raises InvalidResponseError when total > 120.

_validate_item(index_1, value) → int
  1-4 Likert (BIS-11 uses 1=Rarely/Never … 4=Almost Always/Always).
  Same bool-before-int guard; range is 1-4 not 0-3.
"""

from __future__ import annotations

import pytest

from discipline.psychometric.scoring.bis11 import (
    BIS11_SEVERITY_THRESHOLDS,
    BIS11_SUBSCALES,
    ITEM_MAX,
    ITEM_MIN,
    InvalidResponseError,
    _classify,
    _reverse,
    _subscale_sum,
    _validate_item,
)


# ---------------------------------------------------------------------------
# _reverse — arithmetic reflection 1-4 scale
# ---------------------------------------------------------------------------


class TestReverse:
    def test_one_flips_to_four(self) -> None:
        assert _reverse(1) == 4

    def test_four_flips_to_one(self) -> None:
        assert _reverse(4) == 1

    def test_two_flips_to_three(self) -> None:
        assert _reverse(2) == 3

    def test_three_flips_to_two(self) -> None:
        assert _reverse(3) == 2

    def test_double_flip_is_identity(self) -> None:
        for v in range(1, 5):
            assert _reverse(_reverse(v)) == v

    def test_uses_item_min_item_max_formula(self) -> None:
        # Formula: ITEM_MIN + ITEM_MAX - value
        for v in range(1, 5):
            assert _reverse(v) == ITEM_MIN + ITEM_MAX - v


# ---------------------------------------------------------------------------
# _classify — Stanford 2009 three-band classifier
# Thresholds: ≤51=low, ≤71=normal, ≤120=high
# ---------------------------------------------------------------------------


class TestClassify:
    def test_score_30_is_low(self) -> None:
        # 30 is minimum BIS-11 total (30 items × 1 = 30)
        assert _classify(30) == "low"

    def test_score_51_is_low(self) -> None:
        assert _classify(51) == "low"

    def test_score_52_is_normal(self) -> None:
        assert _classify(52) == "normal"

    def test_score_71_is_normal(self) -> None:
        assert _classify(71) == "normal"

    def test_score_72_is_high(self) -> None:
        assert _classify(72) == "high"

    def test_score_120_is_high(self) -> None:
        # 120 is maximum BIS-11 total (30 items × 4 = 120)
        assert _classify(120) == "high"

    def test_score_121_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _classify(121)

    def test_boundary_51_to_52(self) -> None:
        assert _classify(51) != _classify(52)

    def test_boundary_71_to_72(self) -> None:
        assert _classify(71) != _classify(72)


# ---------------------------------------------------------------------------
# _validate_item — 1-4 Likert (not 0-3 like HADS/DASS-21)
# ---------------------------------------------------------------------------


class TestValidateItemBis11Accepted:
    def test_one_accepted(self) -> None:
        assert _validate_item(1, 1) == 1

    def test_two_accepted(self) -> None:
        assert _validate_item(1, 2) == 2

    def test_three_accepted(self) -> None:
        assert _validate_item(1, 3) == 3

    def test_four_accepted(self) -> None:
        assert _validate_item(1, 4) == 4

    def test_returns_value_unchanged(self) -> None:
        for v in range(1, 5):
            assert _validate_item(5, v) == v


class TestValidateItemBis11BoolRejection:
    def test_true_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_item(1, True)

    def test_false_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_item(1, False)


class TestValidateItemBis11RangeRejection:
    def test_zero_raises(self) -> None:
        # BIS-11 scale starts at 1 — zero is out of range
        with pytest.raises(InvalidResponseError):
            _validate_item(1, 0)

    def test_five_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_item(1, 5)

    def test_minus_1_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_item(1, -1)

    def test_error_mentions_item_index(self) -> None:
        with pytest.raises(InvalidResponseError, match="12"):
            _validate_item(12, 99)


class TestValidateItemBis11TypeRejection:
    def test_string_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_item(1, "2")

    def test_none_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_item(1, None)

    def test_float_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_item(1, 2.0)


# ---------------------------------------------------------------------------
# _subscale_sum — subscale coverage
# ---------------------------------------------------------------------------


class TestSubscaleSumBis11:
    def test_attentional_8_items_all_one(self) -> None:
        scored = (1,) * 30
        assert _subscale_sum(scored, "attentional") == 8

    def test_motor_11_items_all_one(self) -> None:
        scored = (1,) * 30
        assert _subscale_sum(scored, "motor") == 11

    def test_non_planning_11_items_all_one(self) -> None:
        scored = (1,) * 30
        assert _subscale_sum(scored, "non_planning") == 11

    def test_all_fours_attentional_is_32(self) -> None:
        scored = (4,) * 30
        assert _subscale_sum(scored, "attentional") == 32

    def test_subscales_cover_all_30_items(self) -> None:
        all_pos = set()
        for positions in BIS11_SUBSCALES.values():
            all_pos |= set(positions)
        assert all_pos == set(range(1, 31))

    def test_subscales_are_mutually_disjoint(self) -> None:
        subscale_sets = [set(p) for p in BIS11_SUBSCALES.values()]
        for i, s1 in enumerate(subscale_sets):
            for s2 in subscale_sets[i + 1 :]:
                assert s1.isdisjoint(s2)

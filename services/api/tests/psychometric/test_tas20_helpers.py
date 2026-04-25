"""Unit tests for pure helpers in discipline.psychometric.scoring.tas20.

_validate_item(index_1, value) → int
  1-5 Likert (Bagby 1994 TAS-20 scale: 1=Strongly Disagree … 5=Strongly Agree).
  Same bool-before-int guard; range is 1-5 not 0-3 or 1-4.

_flip_if_reverse(index_1, value) → int
  Conditional flip: if index_1 is in TAS20_REVERSE_ITEMS, returns
  (ITEM_MIN + ITEM_MAX) - value = 6 - value on the 1-5 envelope.
  Non-reverse items pass through unchanged.  Positions 4, 5, 10, 18, 19
  are reverse-keyed.

_classify(total) → Band
  Maps a 20-100 post-flip total to Bagby 1994 alexithymia band:
    ≤51 → "non_alexithymic", ≤60 → "possible_alexithymia", >60 → "alexithymic".
  No upper-bound error raised — upper bound is 100 and function handles all ints.
"""

from __future__ import annotations

import pytest

from discipline.psychometric.scoring.tas20 import (
    ITEM_MAX,
    ITEM_MIN,
    TAS20_NON_ALEXITHYMIC_UPPER,
    TAS20_POSSIBLE_UPPER,
    TAS20_REVERSE_ITEMS,
    TAS20_SUBSCALES,
    InvalidResponseError,
    _classify,
    _flip_if_reverse,
    _subscale_sum,
    _validate_item,
)


# ---------------------------------------------------------------------------
# _validate_item — 1-5 Likert
# ---------------------------------------------------------------------------


class TestValidateItemTas20Accepted:
    def test_one_accepted(self) -> None:
        assert _validate_item(1, 1) == 1

    def test_five_accepted(self) -> None:
        assert _validate_item(1, 5) == 5

    def test_all_valid_range_returned_unchanged(self) -> None:
        for v in range(1, 6):
            assert _validate_item(3, v) == v


class TestValidateItemTas20BoolRejection:
    def test_true_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_item(1, True)

    def test_false_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_item(1, False)


class TestValidateItemTas20RangeRejection:
    def test_zero_raises(self) -> None:
        # TAS-20 scale starts at 1
        with pytest.raises(InvalidResponseError):
            _validate_item(1, 0)

    def test_six_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_item(1, 6)

    def test_minus_1_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_item(1, -1)

    def test_error_mentions_item_index(self) -> None:
        with pytest.raises(InvalidResponseError, match="10"):
            _validate_item(10, 99)


class TestValidateItemTas20TypeRejection:
    def test_string_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_item(1, "3")

    def test_none_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_item(1, None)

    def test_float_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_item(1, 3.0)


# ---------------------------------------------------------------------------
# _flip_if_reverse — conditional 1-5 reflection
# Reverse items: positions 4, 5, 10, 18, 19
# Formula: (ITEM_MIN + ITEM_MAX) - value = 6 - value
# ---------------------------------------------------------------------------


class TestFlipIfReverseReverseItems:
    def test_reverse_position_1_flips(self) -> None:
        pos = TAS20_REVERSE_ITEMS[0]
        assert _flip_if_reverse(pos, 1) == 5

    def test_reverse_position_5_flips(self) -> None:
        pos = TAS20_REVERSE_ITEMS[1]
        assert _flip_if_reverse(pos, 5) == 1

    def test_two_flips_to_four(self) -> None:
        pos = TAS20_REVERSE_ITEMS[0]
        assert _flip_if_reverse(pos, 2) == 4

    def test_three_stays_three(self) -> None:
        pos = TAS20_REVERSE_ITEMS[0]
        assert _flip_if_reverse(pos, 3) == 3

    def test_double_flip_is_identity(self) -> None:
        pos = TAS20_REVERSE_ITEMS[0]
        for v in range(1, 6):
            assert _flip_if_reverse(pos, _flip_if_reverse(pos, v)) == v

    def test_all_reverse_items_flip(self) -> None:
        for pos in TAS20_REVERSE_ITEMS:
            assert _flip_if_reverse(pos, 1) == 5
            assert _flip_if_reverse(pos, 5) == 1


class TestFlipIfReverseForwardItems:
    def _forward_positions(self) -> list[int]:
        return [p for p in range(1, 21) if p not in TAS20_REVERSE_ITEMS]

    def test_forward_items_pass_through_unchanged(self) -> None:
        for pos in self._forward_positions():
            for v in range(1, 6):
                assert _flip_if_reverse(pos, v) == v, (
                    f"Position {pos} with value {v} should be unchanged"
                )

    def test_forward_item_count_is_15(self) -> None:
        assert len(self._forward_positions()) == 15

    def test_reverse_item_count_is_5(self) -> None:
        assert len(TAS20_REVERSE_ITEMS) == 5


# ---------------------------------------------------------------------------
# _classify — Bagby 1994 three-band classifier
# ≤51 = non_alexithymic, ≤60 = possible_alexithymia, >60 = alexithymic
# ---------------------------------------------------------------------------


class TestClassifyTas20:
    def test_score_20_is_non_alexithymic(self) -> None:
        # 20 is the minimum (20 items × 1)
        assert _classify(20) == "non_alexithymic"

    def test_score_51_is_non_alexithymic(self) -> None:
        assert _classify(TAS20_NON_ALEXITHYMIC_UPPER) == "non_alexithymic"

    def test_score_52_is_possible_alexithymia(self) -> None:
        assert _classify(TAS20_NON_ALEXITHYMIC_UPPER + 1) == "possible_alexithymia"

    def test_score_60_is_possible_alexithymia(self) -> None:
        assert _classify(TAS20_POSSIBLE_UPPER) == "possible_alexithymia"

    def test_score_61_is_alexithymic(self) -> None:
        assert _classify(TAS20_POSSIBLE_UPPER + 1) == "alexithymic"

    def test_score_100_is_alexithymic(self) -> None:
        # 100 is the maximum (20 items × 5)
        assert _classify(100) == "alexithymic"

    def test_boundary_51_to_52(self) -> None:
        assert _classify(51) != _classify(52)

    def test_boundary_60_to_61(self) -> None:
        assert _classify(60) != _classify(61)

    def test_constants_match_expected_values(self) -> None:
        assert TAS20_NON_ALEXITHYMIC_UPPER == 51
        assert TAS20_POSSIBLE_UPPER == 60


# ---------------------------------------------------------------------------
# _subscale_sum — TAS-20 three-factor structure
# ---------------------------------------------------------------------------


class TestSubscaleSumTas20:
    def test_all_ones_returns_subscale_item_count(self) -> None:
        post_flip = (1,) * 20
        for name, positions in TAS20_SUBSCALES.items():
            expected = len(positions)
            assert _subscale_sum(post_flip, name) == expected, (
                f"Subscale '{name}': expected {expected}, "
                f"got {_subscale_sum(post_flip, name)}"
            )

    def test_subscales_cover_all_20_positions(self) -> None:
        all_pos: set[int] = set()
        for positions in TAS20_SUBSCALES.values():
            all_pos |= set(positions)
        assert all_pos == set(range(1, 21))

    def test_subscales_are_mutually_disjoint(self) -> None:
        subscale_sets = [set(p) for p in TAS20_SUBSCALES.values()]
        for i, s1 in enumerate(subscale_sets):
            for s2 in subscale_sets[i + 1 :]:
                assert s1.isdisjoint(s2)

    def test_three_subscales_present(self) -> None:
        assert len(TAS20_SUBSCALES) == 3

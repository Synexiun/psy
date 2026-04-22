"""Tests for the CES-D (Center for Epidemiologic Studies Depression Scale) scorer.

Radloff LS 1977 Applied Psychological Measurement 1(3):385-401.
20 items, 0-3 Likert, items 4/8/12/16 reverse-scored (3-raw).
Total 0-60, HIGHER = MORE depressive symptoms.
Positive screen at total >= 16 (Radloff 1977 cutoff).
No severity bands. No subscales.
"""

from __future__ import annotations

import pytest

from discipline.psychometric.scoring.cesd import (
    INSTRUMENT_VERSION,
    ITEM_COUNT,
    ITEM_MAX,
    ITEM_MIN,
    POSITIVE_SCREEN_CUTOFF,
    REVERSE_SCORED_ITEMS,
    TOTAL_MAX,
    CesdResult,
    InvalidResponseError,
    score_cesd,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _floor_items() -> list[int]:
    return [0] * ITEM_COUNT


def _ceil_items() -> list[int]:
    return [3] * ITEM_COUNT


def _scored_total(items: list[int]) -> int:
    """Compute reverse-scored total: items 4,8,12,16 → 3-raw."""
    return sum(
        (3 - v) if (i + 1) in REVERSE_SCORED_ITEMS else v
        for i, v in enumerate(items)
    )


# ---------------------------------------------------------------------------
# TestConstants
# ---------------------------------------------------------------------------

class TestConstants:
    def test_instrument_version(self) -> None:
        assert INSTRUMENT_VERSION == "cesd-1.0.0"

    def test_item_count(self) -> None:
        assert ITEM_COUNT == 20

    def test_item_min(self) -> None:
        assert ITEM_MIN == 0

    def test_item_max(self) -> None:
        assert ITEM_MAX == 3

    def test_positive_screen_cutoff(self) -> None:
        # Radloff 1977 validated cutoff.
        assert POSITIVE_SCREEN_CUTOFF == 16

    def test_total_max(self) -> None:
        assert TOTAL_MAX == 60

    def test_reverse_scored_items_set(self) -> None:
        # Radloff 1977: positively-worded items at positions 4,8,12,16.
        assert frozenset({4, 8, 12, 16}) == REVERSE_SCORED_ITEMS

    def test_reverse_scored_items_count(self) -> None:
        assert len(REVERSE_SCORED_ITEMS) == 4

    def test_total_max_matches_ceil(self) -> None:
        # All 3s: forward items contribute 3, reversed items contribute 0;
        # 16 forward × 3 + 4 reversed × 0 = 48. Wait -- need to recalculate.
        # Actually: ALL items = 3; reversed items: 3-3=0; forward items: 3.
        # total = 16*3 + 4*0 = 48. So TOTAL_MAX=60 is NOT achievable with
        # all-3s -- the theoretical max would be forward items all 3,
        # reversed items all 0. Max = 16*3 + 4*3 = 60 only if reversed
        # items contribute 3-0=3. So max is: 16 forward items × 3 (raw=3)
        # + 4 reversed items × 3 (scored = 3 - raw_0 = 3-0 = 3)
        # = 48 + 12 = 60.
        # Construct: forward items=3, reversed items=0.
        items = []
        for i in range(ITEM_COUNT):
            pos = i + 1
            if pos in REVERSE_SCORED_ITEMS:
                items.append(0)  # reversed: score = 3-0 = 3
            else:
                items.append(3)  # forward: score = 3
        r = score_cesd(items)
        assert r.total == TOTAL_MAX


# ---------------------------------------------------------------------------
# TestReverseScoringMechanism
# ---------------------------------------------------------------------------

class TestReverseScoringMechanism:
    def test_item_4_is_reversed(self) -> None:
        # item 4 raw=3 → scored=0; item 4 raw=0 → scored=3
        items_high = [0] * ITEM_COUNT
        items_low = [0] * ITEM_COUNT
        items_high[3] = 3   # item 4 raw=3 → score=0
        items_low[3] = 0    # item 4 raw=0 → score=3
        r_high = score_cesd(items_high)
        r_low = score_cesd(items_low)
        # contribution from item 4: high raw → lower score
        assert r_high.total < r_low.total

    def test_item_8_is_reversed(self) -> None:
        # item 8 raw=3 → scored=0; raw=0 → scored=3.
        # Baseline all-zero: reversed items 4,8,12,16 each score 3 → total=12.
        # Set item 8 (index 7) to 3: item 8 score drops from 3 to 0 → total=9.
        items_low = [0] * ITEM_COUNT   # item 8 raw=0 → score=3
        items_high = [0] * ITEM_COUNT
        items_high[7] = 3              # item 8 raw=3 → score=0
        r_low = score_cesd(items_low)
        r_high = score_cesd(items_high)
        assert r_high.total < r_low.total  # higher raw → lower score (reversed)
        assert r_high.total == r_low.total - 3  # exactly 3 points lower

    def test_item_12_is_reversed(self) -> None:
        # item 12 raw=3 → scored=0; raw=0 → scored=3.
        items_low = [0] * ITEM_COUNT
        items_high = [0] * ITEM_COUNT
        items_high[11] = 3
        r_low = score_cesd(items_low)
        r_high = score_cesd(items_high)
        assert r_high.total == r_low.total - 3

    def test_item_16_is_reversed(self) -> None:
        # item 16 raw=3 → scored=0; raw=0 → scored=3.
        items_low = [0] * ITEM_COUNT
        items_high = [0] * ITEM_COUNT
        items_high[15] = 3
        r_low = score_cesd(items_low)
        r_high = score_cesd(items_high)
        assert r_high.total == r_low.total - 3

    def test_item_1_is_not_reversed(self) -> None:
        # item 1 raw=3 → scored=3 (forward).
        # Baseline all-zero: total=12 (from 4 reversed items × 3).
        # Set item 1 to 3: adds 3 → total=15.
        items = [0] * ITEM_COUNT
        items[0] = 3
        r = score_cesd(items)
        assert r.total == 12 + 3  # 15

    def test_item_5_is_not_reversed(self) -> None:
        # item 5 is a forward item; raw=3 adds 3 to the baseline.
        items = [0] * ITEM_COUNT
        items[4] = 3
        r = score_cesd(items)
        assert r.total == 12 + 3  # 15

    def test_reversed_item_max_raw_contributes_zero(self) -> None:
        # All reversed items at max raw (3) → each contributes 0.
        items = [0] * ITEM_COUNT
        for pos in REVERSE_SCORED_ITEMS:
            items[pos - 1] = 3
        r = score_cesd(items)
        assert r.total == 0

    def test_reversed_item_zero_raw_contributes_max(self) -> None:
        # All reversed items at raw=0 → each contributes 3; others=0.
        # Total = 4 * 3 = 12.
        items = [0] * ITEM_COUNT
        # reversed items default to 0 already → score = 3 each
        r = score_cesd(items)
        assert r.total == 4 * 3  # 12

    def test_all_zero_total_is_12(self) -> None:
        # [0]*20: 16 forward=0 + 4 reversed score=(3-0=3) = 12
        r = score_cesd(_floor_items())
        assert r.total == 12

    def test_all_three_total_is_48(self) -> None:
        # [3]*20: 16 forward=3 + 4 reversed score=(3-3=0) = 48
        r = score_cesd(_ceil_items())
        assert r.total == 48


# ---------------------------------------------------------------------------
# TestTotalCorrectness
# ---------------------------------------------------------------------------

class TestTotalCorrectness:
    def test_total_matches_helper_all_zeros(self) -> None:
        items = _floor_items()
        r = score_cesd(items)
        assert r.total == _scored_total(items)

    def test_total_matches_helper_all_threes(self) -> None:
        items = _ceil_items()
        r = score_cesd(items)
        assert r.total == _scored_total(items)

    def test_total_matches_helper_mixed(self) -> None:
        items = [0, 1, 2, 3, 0, 1, 2, 3, 0, 1,
                 2, 3, 0, 1, 2, 3, 0, 1, 2, 3]
        assert len(items) == 20
        r = score_cesd(items)
        assert r.total == _scored_total(items)

    def test_explicit_typical_presentation(self) -> None:
        # Moderate depression presentation; all forward items=2,
        # all reversed items=1 → forward=16*2=32, reversed=4*(3-1)=8 → 40
        items = []
        for i in range(ITEM_COUNT):
            pos = i + 1
            items.append(1 if pos in REVERSE_SCORED_ITEMS else 2)
        r = score_cesd(items)
        assert r.total == 16 * 2 + 4 * (3 - 1)
        assert r.total == 40

    def test_no_reverse_keying_on_forward_items(self) -> None:
        # Increasing all forward items increases total proportionally.
        r0 = score_cesd([0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                         0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
        r1 = score_cesd([1, 0, 0, 0, 1, 0, 0, 0, 1, 0,
                         0, 0, 1, 0, 0, 0, 1, 0, 0, 0])
        # items 1,5,9,13,17 incremented by 1 (all forward items)
        assert r1.total == r0.total + 5  # 5 forward items × 1


# ---------------------------------------------------------------------------
# TestPositiveScreen
# ---------------------------------------------------------------------------

class TestPositiveScreen:
    def test_below_cutoff_is_negative(self) -> None:
        # total = 15 → negative_screen
        # forward items=1, reversed items=0 → forward=16*1=16,
        # reversed=4*(3-0)=12 → 28. Too high. Need to construct 15.
        # total=15: let's use all forward items=0, reversed=0 → total=12
        # then add 3 more from forward items.
        items = [0] * ITEM_COUNT
        items[0] = 1
        items[1] = 1
        items[2] = 1
        # total = 12 + 3 = 15
        r = score_cesd(items)
        assert r.total == 15
        assert r.positive_screen is False
        assert r.severity == "negative_screen"

    def test_at_cutoff_is_positive(self) -> None:
        # total = 16 → positive_screen
        items = [0] * ITEM_COUNT
        items[0] = 1
        items[1] = 1
        items[2] = 1
        items[4] = 1
        # total = 12 + 4 = 16
        r = score_cesd(items)
        assert r.total == 16
        assert r.positive_screen is True
        assert r.severity == "positive_screen"

    def test_above_cutoff_is_positive(self) -> None:
        items = [2] * ITEM_COUNT
        r = score_cesd(items)
        assert r.positive_screen is True

    def test_all_zeros_negative(self) -> None:
        r = score_cesd(_floor_items())
        assert r.total == 12
        assert r.positive_screen is False

    def test_all_threes_positive(self) -> None:
        r = score_cesd(_ceil_items())
        assert r.total == 48
        assert r.positive_screen is True

    def test_severity_consistent_with_positive_screen(self) -> None:
        for items in ([0]*20, [1]*20, [2]*20, [3]*20):
            r = score_cesd(items)
            if r.positive_screen:
                assert r.severity == "positive_screen"
            else:
                assert r.severity == "negative_screen"


# ---------------------------------------------------------------------------
# TestItemCountValidation
# ---------------------------------------------------------------------------

class TestItemCountValidation:
    def test_too_few_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            score_cesd([1] * 19)

    def test_too_many_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            score_cesd([1] * 21)

    def test_empty_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            score_cesd([])

    def test_error_mentions_20(self) -> None:
        with pytest.raises(InvalidResponseError, match="20"):
            score_cesd([0] * 10)


# ---------------------------------------------------------------------------
# TestItemRangeValidation
# ---------------------------------------------------------------------------

class TestItemRangeValidation:
    def test_negative_item_raises(self) -> None:
        items = [1] * ITEM_COUNT
        items[0] = -1
        with pytest.raises(InvalidResponseError):
            score_cesd(items)

    def test_item_above_3_raises(self) -> None:
        items = [1] * ITEM_COUNT
        items[5] = 4
        with pytest.raises(InvalidResponseError):
            score_cesd(items)

    def test_reversed_item_above_3_raises(self) -> None:
        items = [1] * ITEM_COUNT
        items[3] = 4  # item 4 (reversed) still validates 0-3
        with pytest.raises(InvalidResponseError):
            score_cesd(items)

    def test_error_message_mentions_position(self) -> None:
        items = [0] * ITEM_COUNT
        items[9] = 5
        with pytest.raises(InvalidResponseError, match="10"):  # 1-indexed
            score_cesd(items)

    def test_error_message_cites_range(self) -> None:
        items = [1] * ITEM_COUNT
        items[3] = 9
        with pytest.raises(InvalidResponseError, match="0-3"):
            score_cesd(items)


# ---------------------------------------------------------------------------
# TestItemTypeValidation
# ---------------------------------------------------------------------------

class TestItemTypeValidation:
    def test_true_raises(self) -> None:
        items: list = [1] * ITEM_COUNT
        items[0] = True
        with pytest.raises(InvalidResponseError):
            score_cesd(items)

    def test_false_raises(self) -> None:
        items: list = [1] * ITEM_COUNT
        items[7] = False
        with pytest.raises(InvalidResponseError):
            score_cesd(items)

    def test_float_raises(self) -> None:
        items: list = [1] * ITEM_COUNT
        items[11] = 2.0
        with pytest.raises(InvalidResponseError):
            score_cesd(items)

    def test_string_raises(self) -> None:
        items: list = [1] * ITEM_COUNT
        items[15] = "2"
        with pytest.raises(InvalidResponseError):
            score_cesd(items)

    def test_none_raises(self) -> None:
        items: list = [1] * ITEM_COUNT
        items[4] = None
        with pytest.raises(InvalidResponseError):
            score_cesd(items)


# ---------------------------------------------------------------------------
# TestResultTyping
# ---------------------------------------------------------------------------

class TestResultTyping:
    def test_result_is_cesd_result(self) -> None:
        r = score_cesd(_floor_items())
        assert isinstance(r, CesdResult)

    def test_result_is_frozen(self) -> None:
        r = score_cesd(_floor_items())
        with pytest.raises((AttributeError, TypeError)):
            r.total = 99  # type: ignore[misc]

    def test_instrument_version_pinned(self) -> None:
        r = score_cesd(_floor_items())
        assert r.instrument_version == INSTRUMENT_VERSION

    def test_items_is_tuple(self) -> None:
        r = score_cesd(_floor_items())
        assert isinstance(r.items, tuple)

    def test_items_length_20(self) -> None:
        r = score_cesd(_floor_items())
        assert len(r.items) == ITEM_COUNT

    def test_severity_is_string(self) -> None:
        r = score_cesd(_floor_items())
        assert isinstance(r.severity, str)

    def test_positive_screen_is_bool(self) -> None:
        r = score_cesd(_floor_items())
        assert isinstance(r.positive_screen, bool)

    def test_total_is_int(self) -> None:
        r = score_cesd(_floor_items())
        assert isinstance(r.total, int)

    def test_no_subscales_attribute(self) -> None:
        r = score_cesd(_floor_items())
        assert not hasattr(r, "subscales")

    def test_no_cutoff_used_attribute(self) -> None:
        r = score_cesd(_floor_items())
        assert not hasattr(r, "cutoff_used")


# ---------------------------------------------------------------------------
# TestClinicalVignettes
# ---------------------------------------------------------------------------

class TestClinicalVignettes:
    def test_healthy_non_depressed(self) -> None:
        # Low depressive symptoms — all forward items 0,
        # reversed items naturally contribute positive affect.
        r = score_cesd(_floor_items())
        assert r.positive_screen is False
        assert r.total == 12

    def test_mild_subclinical_depression(self) -> None:
        # Subclinical — some symptoms but below cutoff.
        items = [0] * ITEM_COUNT
        items[0] = 1
        items[2] = 1
        items[4] = 1
        # total = 12 + 3 = 15 → negative
        r = score_cesd(items)
        assert r.positive_screen is False

    def test_caseness_at_threshold(self) -> None:
        # Exactly at Radloff 1977 cutoff → positive screen.
        items = [0] * ITEM_COUNT
        for idx in [0, 1, 2, 4]:  # 4 forward items set to 1
            items[idx] = 1
        # total = 12 + 4 = 16 → positive
        r = score_cesd(items)
        assert r.total == 16
        assert r.positive_screen is True

    def test_moderate_depression_addiction_loop(self) -> None:
        # Franken 2006: depression mediates negative affect → craving.
        # Forward items=2, reversed=1 → 32 + 8 = 40 → positive
        items = []
        for i in range(ITEM_COUNT):
            pos = i + 1
            items.append(1 if pos in REVERSE_SCORED_ITEMS else 2)
        r = score_cesd(items)
        assert r.total == 40
        assert r.positive_screen is True

    def test_severe_depression_all_threes(self) -> None:
        # All items 3: forward=48, reversed=0 → 48 → positive
        r = score_cesd(_ceil_items())
        assert r.total == 48
        assert r.positive_screen is True

    def test_positive_affect_improvement_marker(self) -> None:
        # Reversed items improving (raw increasing) reduces total.
        # Baseline: reversed items=0 → contribute 3 each.
        # Improved: reversed items=3 → contribute 0 each.
        items_base = [0] * ITEM_COUNT  # reversed items=0
        items_impr = [0] * ITEM_COUNT
        for pos in REVERSE_SCORED_ITEMS:
            items_impr[pos - 1] = 3  # reversed items max raw
        r_base = score_cesd(items_base)
        r_impr = score_cesd(items_impr)
        assert r_impr.total < r_base.total

    def test_direction_higher_is_more_depressive(self) -> None:
        # HIGHER = MORE depressive symptoms (same direction as PHQ-9).
        # Min total 0: forward=0, reversed=3 (score=3-3=0).
        # Positions 4,8,12,16 (1-indexed = indices 3,7,11,15) are reversed.
        items_min: list[int] = []
        items_max: list[int] = []
        for i in range(ITEM_COUNT):
            pos = i + 1
            if pos in REVERSE_SCORED_ITEMS:
                items_min.append(3)  # reversed: score = 3-3 = 0
                items_max.append(0)  # reversed: score = 3-0 = 3
            else:
                items_min.append(0)  # forward: score = 0
                items_max.append(3)  # forward: score = 3
        r_min = score_cesd(items_min)
        r_max = score_cesd(items_max)
        assert r_min.total == 0
        assert r_max.total == 60
        assert r_max.total > r_min.total

    def test_rci_determinism(self) -> None:
        items = [0, 1, 2, 3, 0, 1, 2, 3, 0, 1,
                 2, 3, 0, 1, 2, 3, 0, 1, 2, 3]
        r1 = score_cesd(items)
        r2 = score_cesd(items)
        assert r1.total == r2.total
        assert r1.positive_screen == r2.positive_screen


# ---------------------------------------------------------------------------
# TestInvariants
# ---------------------------------------------------------------------------

class TestInvariants:
    def test_items_preserved_raw(self) -> None:
        # items tuple must store RAW values, not reverse-scored.
        raw = [3, 2, 1, 3, 2, 1, 0, 3, 2, 1,
               0, 3, 2, 1, 0, 3, 2, 1, 0, 3]
        assert len(raw) == 20
        r = score_cesd(raw)
        assert r.items == tuple(raw)

    def test_reversed_item_raw_stored_not_flipped(self) -> None:
        # item 4 (index 3): raw=3 stored as 3, not as 0.
        items = [0] * ITEM_COUNT
        items[3] = 3  # item 4 raw=3
        r = score_cesd(items)
        assert r.items[3] == 3  # raw value preserved
        assert r.total == 12 - 3  # reversed: 3-3=0 vs baseline 3; total=12-3=9

    def test_total_matches_helper(self) -> None:
        raw = [1, 0, 2, 1, 0, 3, 1, 2, 0, 1,
               3, 2, 1, 0, 2, 3, 1, 0, 2, 1]
        assert len(raw) == 20
        r = score_cesd(raw)
        assert r.total == _scored_total(raw)

    def test_total_lower_bound(self) -> None:
        # Min total: all forward=0, all reversed=0 → 4*3=12.
        # Actually min total = 0 only if all reversed items=3 (score=0) and all forward=0.
        items = []
        for i in range(ITEM_COUNT):
            pos = i + 1
            items.append(3 if pos in REVERSE_SCORED_ITEMS else 0)
        r = score_cesd(items)
        assert r.total == 0

    def test_total_upper_bound(self) -> None:
        # Max: all forward=3, all reversed=0 (score=3).
        items = []
        for i in range(ITEM_COUNT):
            pos = i + 1
            items.append(0 if pos in REVERSE_SCORED_ITEMS else 3)
        r = score_cesd(items)
        assert r.total == TOTAL_MAX  # 60


# ---------------------------------------------------------------------------
# TestEdgeCases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_tuple_input_accepted(self) -> None:
        r = score_cesd(tuple([0] * ITEM_COUNT))
        assert isinstance(r, CesdResult)

    def test_generator_input_accepted(self) -> None:
        r = score_cesd(x for x in ([0] * ITEM_COUNT))
        assert r.total == 12  # all-zero input → 4 reversed items contribute 3 each

    def test_does_not_mutate_input(self) -> None:
        raw = [i % (ITEM_MAX + 1) for i in range(ITEM_COUNT)]
        snapshot = raw[:]
        score_cesd(raw)
        assert raw == snapshot

    def test_complex_object_raises(self) -> None:
        items: list = [1] * ITEM_COUNT
        items[10] = complex(2, 0)
        with pytest.raises(InvalidResponseError):
            score_cesd(items)

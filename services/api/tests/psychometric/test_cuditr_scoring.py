"""Tests for the CUDIT-R (Cannabis Use Disorder Identification Test - Revised) scorer.

Adamson SJ et al. 2010 Drug and Alcohol Dependence 110(3):247-252.
8 items, items 1-7 each 0-4 Likert, item 8 0-4 (weighted x2 in total).
Total = sum(items[0:7]) + items[7] * 2; range 0-36.
Positive screen at total >= 12 (Adamson 2010 cutoff; AUC 0.93).
No severity bands. No subscales.
"""

from __future__ import annotations

import pytest

from discipline.psychometric.scoring.cuditr import (
    INSTRUMENT_VERSION,
    ITEM_8_WEIGHT,
    ITEM_COUNT,
    ITEM_MAX,
    ITEM_MIN,
    POSITIVE_SCREEN_CUTOFF,
    TOTAL_MAX,
    CuditRResult,
    InvalidResponseError,
    score_cuditr,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _items_summing_to(unweighted_total: int) -> list[int]:
    """Construct a valid 8-item list where the UNWEIGHTED sum = total.

    Useful for testing item construction independent of the weighting.
    For total computation: score = sum(items[:7]) + items[7]*2.
    """
    if unweighted_total < 0 or unweighted_total > ITEM_COUNT * ITEM_MAX:
        raise ValueError(f"Cannot construct items for unweighted_total={unweighted_total}")
    items: list[int] = []
    remaining = unweighted_total
    for _ in range(ITEM_COUNT):
        v = min(ITEM_MAX, remaining)
        items.append(v)
        remaining -= v
    return items


def _floor_items() -> list[int]:
    return [0] * ITEM_COUNT


def _ceil_items() -> list[int]:
    return [4] * ITEM_COUNT


def _weighted_total(items: list[int]) -> int:
    """Compute weighted total: sum(items[:7]) + items[7]*2."""
    return sum(items[:7]) + items[7] * ITEM_8_WEIGHT


# ---------------------------------------------------------------------------
# TestConstants
# ---------------------------------------------------------------------------

class TestConstants:
    def test_instrument_version(self) -> None:
        assert INSTRUMENT_VERSION == "cuditr-1.0.0"

    def test_item_count(self) -> None:
        assert ITEM_COUNT == 8

    def test_item_min(self) -> None:
        assert ITEM_MIN == 0

    def test_item_max(self) -> None:
        assert ITEM_MAX == 4

    def test_item_8_weight(self) -> None:
        # Adamson 2010: item 8 is weighted twice.
        assert ITEM_8_WEIGHT == 2

    def test_positive_screen_cutoff(self) -> None:
        # Adamson 2010 Table 3 — AUC 0.93 at cutoff >= 12.
        assert POSITIVE_SCREEN_CUTOFF == 12

    def test_total_max(self) -> None:
        # 7 items x 4 + 1 item x 4 x 2 = 28 + 8 = 36.
        assert TOTAL_MAX == 36

    def test_total_max_matches_ceil_items(self) -> None:
        r = score_cuditr(_ceil_items())
        assert r.total == TOTAL_MAX


# ---------------------------------------------------------------------------
# TestWeightedScoring
# ---------------------------------------------------------------------------

class TestWeightedScoring:
    def test_floor_total_is_zero(self) -> None:
        r = score_cuditr(_floor_items())
        assert r.total == 0

    def test_ceiling_total_is_36(self) -> None:
        # All 4s: sum(4*7) + 4*2 = 28 + 8 = 36
        r = score_cuditr(_ceil_items())
        assert r.total == 36

    def test_item_8_contributes_double(self) -> None:
        # item 8 = 1, all others 0 → total = 0 + 1*2 = 2
        items = [0] * 7 + [1]
        r = score_cuditr(items)
        assert r.total == 2

    def test_item_8_weight_vs_item_1_same_raw(self) -> None:
        # item 1 = 1, others 0 → total = 1
        # item 8 = 1, others 0 → total = 2
        r1 = score_cuditr([1] + [0] * 7)
        r8 = score_cuditr([0] * 7 + [1])
        assert r8.total == r1.total * ITEM_8_WEIGHT

    def test_item_8_max_contribution_is_8(self) -> None:
        # item 8 = 4, others 0 → total = 4*2 = 8
        items = [0] * 7 + [4]
        r = score_cuditr(items)
        assert r.total == 8

    def test_total_formula_explicit_mixed(self) -> None:
        # items = [1,2,3,2,1,0,1,3]: sum[:7] = 1+2+3+2+1+0+1 = 10; item8*2 = 6
        items = [1, 2, 3, 2, 1, 0, 1, 3]
        r = score_cuditr(items)
        assert r.total == 10 + 6
        assert r.total == 16

    def test_total_matches_helper(self) -> None:
        items = [2, 1, 3, 0, 4, 2, 1, 2]
        assert len(items) == 8
        r = score_cuditr(items)
        assert r.total == _weighted_total(items)

    def test_all_ones_total(self) -> None:
        # sum(1*7) + 1*2 = 7 + 2 = 9
        r = score_cuditr([1] * ITEM_COUNT)
        assert r.total == 9

    def test_all_twos_total(self) -> None:
        # sum(2*7) + 2*2 = 14 + 4 = 18
        r = score_cuditr([2] * ITEM_COUNT)
        assert r.total == 18

    def test_all_threes_total(self) -> None:
        # sum(3*7) + 3*2 = 21 + 6 = 27
        r = score_cuditr([3] * ITEM_COUNT)
        assert r.total == 27


# ---------------------------------------------------------------------------
# TestPositiveScreen
# ---------------------------------------------------------------------------

class TestPositiveScreen:
    def test_below_cutoff_is_negative(self) -> None:
        # total = 11 → negative_screen
        items = [1] * 7 + [2]  # 7 + 4 = 11
        r = score_cuditr(items)
        assert r.total == 11
        assert r.positive_screen is False
        assert r.severity == "negative_screen"

    def test_at_cutoff_is_positive(self) -> None:
        # total = 12 → positive_screen
        items = [1] * 7 + [2] + []
        # Need to construct total = 12 exactly.
        # [2,2,2,1,1,1,1,1]: sum[:7]=10, item8*2=2 → 12
        items2 = [2, 2, 2, 1, 1, 1, 1, 1]
        r = score_cuditr(items2)
        assert r.total == 12
        assert r.positive_screen is True
        assert r.severity == "positive_screen"

    def test_above_cutoff_is_positive(self) -> None:
        items = [2] * ITEM_COUNT
        r = score_cuditr(items)
        assert r.total == 18
        assert r.positive_screen is True

    def test_total_0_is_negative(self) -> None:
        r = score_cuditr(_floor_items())
        assert r.positive_screen is False

    def test_total_36_is_positive(self) -> None:
        r = score_cuditr(_ceil_items())
        assert r.positive_screen is True

    def test_boundary_11_negative(self) -> None:
        # Construct total exactly 11: items[:7] sum=9, item8 raw=1 → 9+2=11
        items = [1, 1, 1, 1, 1, 2, 2, 1]  # sum[:7]=9, 1*2=2, total=11
        assert _weighted_total(items) == 11
        r = score_cuditr(items)
        assert r.positive_screen is False

    def test_boundary_12_positive(self) -> None:
        # total = 12: items[:7] sum=10, item8 raw=1 → 10+2=12
        items = [1, 1, 2, 2, 2, 1, 1, 1]  # sum[:7]=10, item8 raw=1 → 12
        assert _weighted_total(items) == 12
        r = score_cuditr(items)
        assert r.positive_screen is True

    def test_boundary_13_positive(self) -> None:
        items = [1, 1, 2, 2, 2, 1, 2, 1]  # sum[:7]=11, item8=1 → 13
        assert _weighted_total(items) == 13
        r = score_cuditr(items)
        assert r.positive_screen is True

    def test_severity_matches_positive_screen(self) -> None:
        for items in ([0] * 8, [2] * 8, [4] * 8):
            r = score_cuditr(items)
            if r.positive_screen:
                assert r.severity == "positive_screen"
            else:
                assert r.severity == "negative_screen"


# ---------------------------------------------------------------------------
# TestItemCountValidation
# ---------------------------------------------------------------------------

class TestItemCountValidation:
    def test_too_few_items_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            score_cuditr([1] * 7)

    def test_too_many_items_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            score_cuditr([1] * 9)

    def test_empty_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            score_cuditr([])

    def test_error_message_mentions_8(self) -> None:
        with pytest.raises(InvalidResponseError, match="8"):
            score_cuditr([0] * 5)


# ---------------------------------------------------------------------------
# TestItemRangeValidation
# ---------------------------------------------------------------------------

class TestItemRangeValidation:
    def test_negative_item_raises(self) -> None:
        items = [1] * ITEM_COUNT
        items[0] = -1
        with pytest.raises(InvalidResponseError):
            score_cuditr(items)

    def test_item_above_4_raises(self) -> None:
        items = [1] * ITEM_COUNT
        items[3] = 5
        with pytest.raises(InvalidResponseError):
            score_cuditr(items)

    def test_item_8_above_4_raises(self) -> None:
        # Item 8 is still rated 0-4 (raw); weight is applied in total.
        items = [0] * 7 + [5]
        with pytest.raises(InvalidResponseError):
            score_cuditr(items)

    def test_item_4_valid_for_item_8(self) -> None:
        # Value 4 is valid for item 8 (raw range 0-4).
        items = [0] * 7 + [4]
        r = score_cuditr(items)
        assert r.items[7] == 4
        assert r.total == 8

    def test_error_message_mentions_position(self) -> None:
        items = [0] * ITEM_COUNT
        items[5] = 9
        with pytest.raises(InvalidResponseError, match="6"):  # 1-indexed
            score_cuditr(items)

    def test_error_message_cites_range(self) -> None:
        items = [2] * ITEM_COUNT
        items[2] = 7
        with pytest.raises(InvalidResponseError, match="0-4"):
            score_cuditr(items)


# ---------------------------------------------------------------------------
# TestItemTypeValidation
# ---------------------------------------------------------------------------

class TestItemTypeValidation:
    def test_true_raises(self) -> None:
        items: list = [1] * ITEM_COUNT
        items[0] = True
        with pytest.raises(InvalidResponseError):
            score_cuditr(items)

    def test_false_raises(self) -> None:
        items: list = [2] * ITEM_COUNT
        items[0] = False
        with pytest.raises(InvalidResponseError):
            score_cuditr(items)

    def test_float_raises(self) -> None:
        items: list = [1] * ITEM_COUNT
        items[4] = 2.0
        with pytest.raises(InvalidResponseError):
            score_cuditr(items)

    def test_string_raises(self) -> None:
        items: list = [1] * ITEM_COUNT
        items[6] = "3"
        with pytest.raises(InvalidResponseError):
            score_cuditr(items)

    def test_none_raises(self) -> None:
        items: list = [1] * ITEM_COUNT
        items[7] = None
        with pytest.raises(InvalidResponseError):
            score_cuditr(items)


# ---------------------------------------------------------------------------
# TestResultTyping
# ---------------------------------------------------------------------------

class TestResultTyping:
    def test_result_is_cuditr_result(self) -> None:
        r = score_cuditr(_floor_items())
        assert isinstance(r, CuditRResult)

    def test_result_is_frozen(self) -> None:
        r = score_cuditr(_floor_items())
        with pytest.raises((AttributeError, TypeError)):
            r.total = 99  # type: ignore[misc]

    def test_instrument_version_pinned(self) -> None:
        r = score_cuditr(_floor_items())
        assert r.instrument_version == INSTRUMENT_VERSION

    def test_items_is_tuple(self) -> None:
        r = score_cuditr(_floor_items())
        assert isinstance(r.items, tuple)

    def test_items_length_8(self) -> None:
        r = score_cuditr(_floor_items())
        assert len(r.items) == ITEM_COUNT

    def test_severity_is_string(self) -> None:
        r = score_cuditr(_floor_items())
        assert isinstance(r.severity, str)

    def test_positive_screen_is_bool(self) -> None:
        r = score_cuditr(_floor_items())
        assert isinstance(r.positive_screen, bool)

    def test_total_is_int(self) -> None:
        r = score_cuditr(_floor_items())
        assert isinstance(r.total, int)

    def test_no_subscales_attribute(self) -> None:
        r = score_cuditr(_floor_items())
        assert not hasattr(r, "subscales")

    def test_no_cutoff_used_attribute(self) -> None:
        r = score_cuditr(_floor_items())
        assert not hasattr(r, "cutoff_used")


# ---------------------------------------------------------------------------
# TestClinicalVignettes
# ---------------------------------------------------------------------------

class TestClinicalVignettes:
    def test_non_user_negative_screen(self) -> None:
        # Non-cannabis user — all items 0.
        r = score_cuditr(_floor_items())
        assert r.positive_screen is False
        assert r.severity == "negative_screen"

    def test_recreational_user_below_cutoff(self) -> None:
        # Infrequent recreational user — low total.
        items = [1, 0, 0, 1, 0, 1, 0, 0]  # total = 2+0=2
        r = score_cuditr(items)
        assert r.positive_screen is False

    def test_cannabis_use_disorder_positive_screen(self) -> None:
        # Adamson 2010: CUD diagnosis pattern → positive screen.
        # total >= 12
        items = [2, 2, 2, 2, 2, 2, 2, 3]  # sum[:7]=14, 3*2=6, total=20
        r = score_cuditr(items)
        assert r.positive_screen is True

    def test_cannabis_withdrawal_relapse_driver(self) -> None:
        # Haney 1999 / Budney 2003: heavy user; early morning use
        # (item 8 elevated) + high total.
        items = [3, 3, 3, 2, 2, 2, 2, 4]  # sum[:7]=17, 4*2=8, total=25
        r = score_cuditr(items)
        assert r.positive_screen is True
        assert r.total == 25

    def test_social_anxiety_self_medication_positive(self) -> None:
        # Buckner 2008 / Kedzior 2014: social-anxiety-driven CUD.
        # SPIN elevated + CUDIT-R elevated → self-medication pattern.
        items = [2, 3, 3, 2, 1, 2, 2, 2]  # sum[:7]=15, 2*2=4, total=19
        r = score_cuditr(items)
        assert r.positive_screen is True

    def test_item_8_early_morning_use_marker(self) -> None:
        # Item 8 elevated even with moderate other symptoms → positive screen.
        # Items 1-7 moderate (total=8), item 8=4 (8*2=8=8) → total=16
        items = [1, 1, 1, 1, 1, 1, 2, 4]  # sum[:7]=8, item8=4 → 8+8=16
        r = score_cuditr(items)
        assert r.positive_screen is True
        assert r.total == 16

    def test_ceiling_worst_presentation(self) -> None:
        r = score_cuditr(_ceil_items())
        assert r.total == 36
        assert r.positive_screen is True

    def test_direction_higher_is_more_harm(self) -> None:
        r_low = score_cuditr(_floor_items())
        r_high = score_cuditr(_ceil_items())
        assert r_high.total > r_low.total

    def test_rci_determinism(self) -> None:
        items = [1, 2, 3, 0, 2, 1, 3, 2]
        assert len(items) == 8
        r1 = score_cuditr(items)
        r2 = score_cuditr(items)
        assert r1.total == r2.total
        assert r1.positive_screen == r2.positive_screen


# ---------------------------------------------------------------------------
# TestInvariants
# ---------------------------------------------------------------------------

class TestInvariants:
    def test_items_preserved_verbatim(self) -> None:
        raw = [0, 1, 2, 3, 4, 3, 2, 1]
        r = score_cuditr(raw)
        assert r.items == tuple(raw)

    def test_item_8_stored_as_raw_not_weighted(self) -> None:
        # items[7] = 3 in raw → r.items[7] should be 3, not 6
        items = [0] * 7 + [3]
        r = score_cuditr(items)
        assert r.items[7] == 3
        assert r.total == 6  # 0 + 3*2 = 6

    def test_total_equals_weighted_formula(self) -> None:
        raw = [1, 2, 0, 3, 4, 1, 2, 3]
        r = score_cuditr(raw)
        expected = sum(raw[:7]) + raw[7] * ITEM_8_WEIGHT
        assert r.total == expected

    def test_lower_bound_zero(self) -> None:
        r = score_cuditr(_floor_items())
        assert r.total == 0

    def test_upper_bound_36(self) -> None:
        r = score_cuditr(_ceil_items())
        assert r.total == TOTAL_MAX

    def test_severity_consistent_with_positive_screen(self) -> None:
        for items in ([0]*8, [1]*8, [2]*8, [3]*8, [4]*8):
            r = score_cuditr(items)
            if r.positive_screen:
                assert r.severity == "positive_screen"
            else:
                assert r.severity == "negative_screen"


# ---------------------------------------------------------------------------
# TestEdgeCases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_tuple_input_accepted(self) -> None:
        r = score_cuditr(tuple([0] * ITEM_COUNT))
        assert r.total == 0

    def test_generator_input_accepted(self) -> None:
        r = score_cuditr(x for x in ([1] * ITEM_COUNT))
        assert r.total == 9  # sum(1*7) + 1*2 = 9

    def test_does_not_mutate_input(self) -> None:
        raw = [i % (ITEM_MAX + 1) for i in range(ITEM_COUNT)]
        snapshot = raw[:]
        score_cuditr(raw)
        assert raw == snapshot

    def test_complex_object_raises(self) -> None:
        items: list = [1] * ITEM_COUNT
        items[5] = complex(2, 0)
        with pytest.raises(InvalidResponseError):
            score_cuditr(items)

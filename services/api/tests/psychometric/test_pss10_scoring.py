"""PSS-10 scoring tests — Cohen 1983 / 1988.

The load-bearing correctness property of PSS-10 is **reverse-scoring
of items 4, 5, 7, 8**.  A failure mode where reversal is skipped or
mis-applied produces a plausible-looking total that is wildly wrong
clinically: a patient with good coping skills looks highly stressed,
or vice versa.  Every reversal case is pinned independently below.

Coverage strategy:
- Pin the REVERSE_SCORED_ITEMS_1INDEXED set to Cohen 1988.
- Exhaustively test the reversal mapping 0↔4, 1↔3, 2↔2.
- Boundary-test each band cutoff (0-13 low, 14-26 moderate, 27-40
  high).  Both the just-below and at-cutoff totals are pinned.
- Validate inputs: wrong count, out-of-range, wrong type, bool
  rejection.
- End-to-end clinical vignettes that a clinician would recognize.
"""

from __future__ import annotations

import pytest

from discipline.psychometric.scoring.pss10 import (
    INSTRUMENT_VERSION,
    ITEM_COUNT,
    ITEM_MAX,
    ITEM_MIN,
    PSS10_LOW_UPPER,
    PSS10_MODERATE_UPPER,
    PSS10_TOTAL_MAX,
    PSS10_TOTAL_MIN,
    InvalidResponseError,
    Pss10Result,
    REVERSE_SCORED_ITEMS_1INDEXED,
    score_pss10,
)


# Zero-indexed positions of reverse-scored items (4, 5, 7, 8 are
# 1-indexed; subtract 1 for 0-indexed array access).  Pinned here
# only for test-baseline construction — the instrument's identity
# lives in the module's REVERSE_SCORED_ITEMS_1INDEXED constant.
_REVERSE_POS_0IDX = {3, 4, 6, 7}


def _baseline_items(overrides: dict[int, int] | None = None) -> list[int]:
    """Construct a 10-item raw response list that sums to 0 BEFORE
    the overrides are applied.

    Reverse positions default to 4 (→ 0 after reversal); non-reverse
    positions default to 0.  Overriding a 0-indexed position sets
    that position to a specific raw value, and the resulting total
    is exactly the contribution from the override(s) — no noise from
    unmodified items.  This isolates the behavior of each item in
    reverse-scoring tests."""
    items: list[int] = []
    for i in range(10):
        if overrides and i in overrides:
            items.append(overrides[i])
        elif i in _REVERSE_POS_0IDX:
            items.append(4)
        else:
            items.append(0)
    return items


# =============================================================================
# Constants
# =============================================================================


class TestConstants:
    def test_item_count_is_ten(self) -> None:
        assert ITEM_COUNT == 10

    def test_item_range_is_zero_to_four(self) -> None:
        """The Cohen 1983 response scale is 0 (Never) – 4 (Very
        often).  Changing this changes the instrument."""
        assert ITEM_MIN == 0
        assert ITEM_MAX == 4

    def test_total_range(self) -> None:
        """Post-reversal sum envelope: 10 items × 0-4 = 0-40."""
        assert PSS10_TOTAL_MIN == 0
        assert PSS10_TOTAL_MAX == 40

    def test_band_cutoffs(self) -> None:
        """Commonly used cutoffs: low ≤13, moderate 14-26, high ≥27."""
        assert PSS10_LOW_UPPER == 13
        assert PSS10_MODERATE_UPPER == 26

    def test_reverse_scored_items_match_cohen(self) -> None:
        """Items 4, 5, 7, 8 are the positively worded ones per the
        published instrument.  The frozenset identity is part of
        the instrument's clinical definition — a refactor that drops
        one of these items silently mis-scores every administration."""
        assert REVERSE_SCORED_ITEMS_1INDEXED == frozenset({4, 5, 7, 8})

    def test_reverse_scored_set_is_frozen(self) -> None:
        """A set here would be mutable — a defensive cast to
        frozenset prevents a consumer from adding/removing items
        and silently breaking future scorings."""
        assert isinstance(REVERSE_SCORED_ITEMS_1INDEXED, frozenset)

    def test_instrument_version_stable(self) -> None:
        assert INSTRUMENT_VERSION == "pss10-1.0.0"


# =============================================================================
# Reverse-scoring — the biggest bug vector
# =============================================================================


class TestReverseScoring:
    """Reverse-scoring is the most common PSS-10 scoring bug.  Every
    reversal mapping AND every positive-item position is pinned."""

    def test_reversal_mapping_zero_to_four(self) -> None:
        """Patient answers 0 (Never felt confident) on a reverse-
        scored item → it counts as 4 (highly stressful).  Baseline
        contributes 0, so the total is exactly the reversed value."""
        items = _baseline_items({3: 0})  # item 4 (0-idx 3) = 0
        result = score_pss10(items)
        assert result.scored_items[3] == 4
        assert result.total == 4

    def test_reversal_mapping_four_to_zero(self) -> None:
        """Patient answers 4 (Very often felt confident) on a
        reverse-scored item → it counts as 0 (not stressful)."""
        items = _baseline_items({3: 4})
        result = score_pss10(items)
        assert result.scored_items[3] == 0
        assert result.total == 0

    def test_reversal_mapping_two_stays_two(self) -> None:
        """The midpoint (2 = Sometimes) is its own complement; good
        reverse-score implementations keep 2 unchanged.  A bug that
        applied ``4 - v`` to non-reverse items by mistake would
        silently pass a midpoint-only test — hence the companion
        'reversal only on items 4/5/7/8' test below."""
        items = _baseline_items({3: 2})
        result = score_pss10(items)
        assert result.scored_items[3] == 2
        assert result.total == 2

    def test_reversal_mapping_one_to_three(self) -> None:
        items = _baseline_items({3: 1})
        result = score_pss10(items)
        assert result.scored_items[3] == 3
        assert result.total == 3

    def test_reversal_mapping_three_to_one(self) -> None:
        items = _baseline_items({3: 3})
        result = score_pss10(items)
        assert result.scored_items[3] == 1
        assert result.total == 1

    def test_reversal_applies_only_to_items_4_5_7_8(self) -> None:
        """Non-reverse items keep their raw value.  Setting item 1
        (0-indexed 0) to 4 should produce scored 4 (not reversed to
        0).  This catches the 'reverse everything' bug — a naive
        implementation that applied ``4 - v`` to all items would
        show 0 here instead of 4."""
        items = _baseline_items({0: 4})
        result = score_pss10(items)
        assert result.scored_items[0] == 4
        assert result.total == 4

    def test_each_reverse_item_position_inverts(self) -> None:
        """For each of items 4, 5, 7, 8 in isolation: the raw value
        1 should be inverted to scored 3.  Catches a bug where only
        SOME of the four reverse positions are wired up."""
        for one_indexed in (4, 5, 7, 8):
            zero_indexed = one_indexed - 1
            items = _baseline_items({zero_indexed: 1})
            result = score_pss10(items)
            assert result.scored_items[zero_indexed] == 3, (
                f"Item {one_indexed} at 0-index {zero_indexed} not reversed"
            )
            assert result.total == 3, f"Item {one_indexed} produced total {result.total}"

    def test_non_reverse_positions_never_invert(self) -> None:
        """Items 1, 2, 3, 6, 9, 10 are NOT reverse-scored.  Each
        at isolation should remain as-is."""
        for one_indexed in (1, 2, 3, 6, 9, 10):
            zero_indexed = one_indexed - 1
            items = _baseline_items({zero_indexed: 3})
            result = score_pss10(items)
            assert result.scored_items[zero_indexed] == 3
            assert result.total == 3

    def test_raw_items_preserved_pre_reversal(self) -> None:
        """``raw_items`` in the result holds the CALLER'S inputs,
        before any reversal.  An auditor needs both: ``raw_items``
        to verify data entry, ``scored_items`` to verify summation."""
        items = [0, 0, 0, 4, 4, 0, 4, 4, 0, 0]  # all reverse items set to 4
        result = score_pss10(items)
        assert result.raw_items == tuple(items)
        # After reversal, each reverse item becomes 0.
        assert result.scored_items == (0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        assert result.total == 0


# =============================================================================
# Severity bands — boundary testing
# =============================================================================


class TestLowBand:
    def test_total_zero_is_low(self) -> None:
        """A teetotaler of stress — all items Never.  Note the
        reverse items ([0,0,0,0,0,0,0,0,0,0] with 4/5/7/8 reversed)
        yield 0+0+0+4+4+0+4+4+0+0 = 16, which is MODERATE.  A true
        'zero total' requires the reverse items to be 4s."""
        items = [0, 0, 0, 4, 4, 0, 4, 4, 0, 0]
        result = score_pss10(items)
        assert result.total == 0
        assert result.band == "low"

    def test_total_thirteen_is_low_at_boundary(self) -> None:
        """13 is the upper bound of 'low' — must classify as low."""
        # Non-reverse items sum to 13, reverse items contribute 0.
        items = [3, 3, 3, 4, 4, 3, 4, 4, 1, 0]
        result = score_pss10(items)
        assert result.total == 13
        assert result.band == "low"

    def test_total_fourteen_is_moderate(self) -> None:
        """At-cutoff the other way: 14 is the start of 'moderate'.
        Flipping the ``<=`` operator to ``<`` would drop anyone
        at exactly 14 into the wrong band."""
        items = [3, 3, 3, 4, 4, 3, 4, 4, 1, 1]
        result = score_pss10(items)
        assert result.total == 14
        assert result.band == "moderate"


class TestModerateBand:
    def test_total_fourteen_is_moderate(self) -> None:
        items = [3, 3, 3, 4, 4, 3, 4, 4, 1, 1]
        result = score_pss10(items)
        assert result.total == 14
        assert result.band == "moderate"

    def test_total_twenty_is_moderate(self) -> None:
        # Midpoint of moderate range.
        items = [3, 3, 3, 2, 2, 3, 2, 2, 3, 3]  # raw sum 26
        result = score_pss10(items)
        # Reversals: 2→2, 2→2, 2→2, 2→2 (all stay)
        # Total = 26
        assert result.total == 26
        assert result.band == "moderate"

    def test_total_twenty_six_is_moderate_at_boundary(self) -> None:
        """Upper bound of moderate."""
        items = [4, 4, 4, 2, 2, 4, 2, 2, 4, 4]
        # Non-reverse sum (positions 0,1,2,5,8,9): 4+4+4+4+4+4 = 24
        # Reverse items (3,4,6,7): 2,2,2,2 all stay 2.  Sum +8 = 32... wait
        # Let me recompute: positions 0,1,2 = 4+4+4 = 12.
        # Position 3 (reverse): 2 → 2.  Position 4 (reverse): 2 → 2.
        # Position 5: 4.  Position 6 (reverse): 2 → 2.  Position 7 (reverse): 2 → 2.
        # Position 8: 4.  Position 9: 4.
        # Total: 12 + 2 + 2 + 4 + 2 + 2 + 4 + 4 = 32.  That's high, not 26.
        # Rebuild for exactly 26:
        # Make 26 = non-reverse sum + reverse-scored sum.
        # Non-reverse (6 items): use [3,3,3,3,3,3] = 18.
        # Reverse (4 items): use [2,2,2,2] → stays [2,2,2,2] = 8.
        # Total 18 + 8 = 26.  Items: [3,3,3,2,2,3,2,2,3,3].
        items = [3, 3, 3, 2, 2, 3, 2, 2, 3, 3]
        result = score_pss10(items)
        assert result.total == 26
        assert result.band == "moderate"

    def test_total_twenty_seven_is_high(self) -> None:
        """At-cutoff the other way: 27 starts 'high'."""
        items = [3, 3, 3, 2, 2, 3, 2, 2, 3, 4]
        # 3+3+3+2+2+3+2+2+3+4 = 27
        result = score_pss10(items)
        assert result.total == 27
        assert result.band == "high"


class TestHighBand:
    def test_total_twenty_seven_is_high_at_boundary(self) -> None:
        items = [3, 3, 3, 2, 2, 3, 2, 2, 3, 4]
        result = score_pss10(items)
        assert result.total == 27
        assert result.band == "high"

    def test_total_forty_is_high_maximum(self) -> None:
        """All non-reverse items at 4 (Very often), all reverse
        items at 0 (Never felt coping) → total 40, band high."""
        items = [4, 4, 4, 0, 0, 4, 0, 0, 4, 4]
        result = score_pss10(items)
        assert result.total == 40
        assert result.band == "high"

    def test_total_thirty_is_high(self) -> None:
        """Mid-high-band sanity."""
        items = [4, 3, 3, 0, 0, 4, 0, 0, 4, 4]
        # 4+3+3+(4→0, r=4)+(4→0, r=4)+4+(4→0, r=4)+(4→0, r=4)+4+4
        # Non-reverse (0,1,2,5,8,9): 4+3+3+4+4+4 = 22
        # Reverse inputs (3,4,6,7) = 0,0,0,0 → each becomes 4.  Sum = 16.
        # Total 22 + 16 = 38.  That's high.  But I wanted 30.  Let me adjust.
        # For total 30: non-reverse [3,3,3,3,3,3]=18, reverse inputs [x,x,x,x] → scored 12.
        # Each reverse scored = 12/4 = 3.  Raw input must be 4 - 3 = 1.
        # So: items = [3, 3, 3, 1, 1, 3, 1, 1, 3, 3]
        items = [3, 3, 3, 1, 1, 3, 1, 1, 3, 3]
        result = score_pss10(items)
        assert result.total == 30
        assert result.band == "high"


# =============================================================================
# Specific totals — arithmetic pinning
# =============================================================================


class TestArithmetic:
    def test_all_zero_raw(self) -> None:
        """All items 0 — reverse items become 4 each, total = 16."""
        result = score_pss10([0] * 10)
        assert result.total == 16
        assert result.band == "moderate"

    def test_all_four_raw(self) -> None:
        """All items 4 — reverse items become 0 each, non-reverse
        contribute 4 each (6 items), total = 24."""
        result = score_pss10([4] * 10)
        assert result.total == 24
        assert result.band == "moderate"

    def test_all_two_raw_stays_twenty(self) -> None:
        """All items 2 (midpoint) — nothing changes on reversal,
        total = 20.  Pins that midpoint-only inputs don't surprise."""
        result = score_pss10([2] * 10)
        assert result.total == 20
        assert result.band == "moderate"

    def test_scored_items_length(self) -> None:
        result = score_pss10([1] * 10)
        assert len(result.scored_items) == 10

    def test_scored_items_exact_values(self) -> None:
        """Full 10-element pin of scored output for an arbitrary
        input.  Catches off-by-one in the reversal index."""
        # raw: [1, 2, 3, 4, 0, 1, 2, 3, 4, 0]
        # reverse positions (0-idx): 3, 4, 6, 7
        # position 3: 4 → 0
        # position 4: 0 → 4
        # position 6: 2 → 2
        # position 7: 3 → 1
        # scored: [1, 2, 3, 0, 4, 1, 2, 1, 4, 0]
        # total: 1+2+3+0+4+1+2+1+4+0 = 18
        result = score_pss10([1, 2, 3, 4, 0, 1, 2, 3, 4, 0])
        assert result.scored_items == (1, 2, 3, 0, 4, 1, 2, 1, 4, 0)
        assert result.total == 18


# =============================================================================
# Validation
# =============================================================================


class TestValidation:
    def test_too_few_items_raises(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 10 items"):
            score_pss10([0] * 9)

    def test_too_many_items_raises(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 10 items"):
            score_pss10([0] * 11)

    def test_item_above_max_raises(self) -> None:
        with pytest.raises(InvalidResponseError, match=r"out of range \[0, 4\]"):
            score_pss10([5, 0, 0, 0, 0, 0, 0, 0, 0, 0])

    def test_item_below_min_raises(self) -> None:
        with pytest.raises(InvalidResponseError, match=r"out of range \[0, 4\]"):
            score_pss10([-1, 0, 0, 0, 0, 0, 0, 0, 0, 0])

    def test_error_identifies_offending_item_1indexed(self) -> None:
        """The error message names the 1-indexed item so a clinician
        can point at the right question number on the paper form."""
        with pytest.raises(InvalidResponseError, match=r"item 3"):
            score_pss10([0, 0, 99, 0, 0, 0, 0, 0, 0, 0])

    def test_float_item_raises(self) -> None:
        """PSS-10 responses are integers; a float like 2.5 is a
        wire-format bug (user entered a slider value) and we
        surface it rather than silently truncating."""
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_pss10([0, 0, 2.5, 0, 0, 0, 0, 0, 0, 0])  # type: ignore[list-item]

    def test_bool_item_rejected(self) -> None:
        """``bool`` is an ``int`` subclass in Python — True/False
        would silently pass an ``isinstance(v, int)`` check and score
        as 1/0 on a 0-4 scale.  That's almost certainly a wire-
        format bug (the PSS-10 is not yes/no), so we reject it
        explicitly with a clear error message."""
        items = [0, 0, 0, True, 0, 0, 0, 0, 0, 0]  # type: ignore[list-item]
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_pss10(items)


# =============================================================================
# Result shape
# =============================================================================


class TestResultShape:
    def test_result_is_frozen(self) -> None:
        result = score_pss10([0] * 10)
        with pytest.raises(Exception):  # FrozenInstanceError
            result.total = 99  # type: ignore[misc]

    def test_raw_items_is_tuple(self) -> None:
        result = score_pss10([0] * 10)
        assert isinstance(result.raw_items, tuple)

    def test_scored_items_is_tuple(self) -> None:
        result = score_pss10([0] * 10)
        assert isinstance(result.scored_items, tuple)

    def test_instrument_version_in_result(self) -> None:
        result = score_pss10([0] * 10)
        assert result.instrument_version == INSTRUMENT_VERSION

    def test_result_type(self) -> None:
        result = score_pss10([0] * 10)
        assert isinstance(result, Pss10Result)


# =============================================================================
# Clinical scenarios — end-to-end pinning
# =============================================================================


class TestClinicalScenarios:
    """End-to-end pins of realistic patient profiles.  These are the
    tests that translate most directly to 'did we score this
    questionnaire correctly' if a clinician handed us a paper form."""

    def test_coping_well_low_stress(self) -> None:
        """Patient reports low negative items AND high confidence/
        coping (positive items) → low total.  The classic 'stress-
        resilient' profile.  If reverse-scoring is broken, this
        patient would paradoxically score as moderate or high."""
        # Never felt upset (items 1,2,3,6,9,10 = 0).
        # Very often felt confident / in control (items 4,5,7,8 = 4).
        items = [0, 0, 0, 4, 4, 0, 4, 4, 0, 0]
        result = score_pss10(items)
        assert result.total == 0
        assert result.band == "low"

    def test_overwhelmed_high_stress(self) -> None:
        """Patient reports high negative items AND low confidence/
        coping → high total.  The classic 'overwhelmed' profile."""
        items = [4, 4, 4, 0, 0, 4, 0, 0, 4, 4]
        result = score_pss10(items)
        assert result.total == 40
        assert result.band == "high"

    def test_mixed_profile_moderate(self) -> None:
        """Realistic patient: moderate negative appraisal plus
        partial coping → moderate band.  No extremes."""
        # Sometimes upset / stressed (2s on negative).
        # Sometimes confident (2 on positive, stays 2 after reversal).
        items = [2, 2, 2, 2, 2, 2, 2, 2, 2, 2]
        result = score_pss10(items)
        assert result.total == 20
        assert result.band == "moderate"

    def test_high_negative_high_positive_cancels(self) -> None:
        """Patient endorses high stress AND high coping — mixed
        signal that nets to moderate.  Pins that reverse-scoring
        correctly subtracts the coping signal from the stress signal."""
        items = [4, 4, 4, 4, 4, 4, 4, 4, 4, 4]
        result = score_pss10(items)
        # 6 non-reverse × 4 = 24
        # 4 reverse × (4 → 0) = 0
        assert result.total == 24
        assert result.band == "moderate"

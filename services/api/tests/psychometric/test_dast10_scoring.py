"""DAST-10 scoring tests — Skinner 1982.

The two load-bearing correctness properties of DAST-10 are:

1. **Item 3 is the only reverse-scored item.**  A patient who answers
   "yes, I am always able to stop" (raw 1) is endorsing *control*, so
   it must invert to 0.  A bug that reverse-scores a different item
   silently inverts the clinical meaning of that item and mis-bands
   the screen.
2. **Five-band classification with the right inclusive boundaries.**
   Getting the cutoff operator wrong (``<`` vs ``<=``) drops a patient
   on the boundary into the wrong clinical-action band — e.g. a score
   of 3 falling into "low" instead of "moderate" would skip the
   brief-intervention action step.

Coverage strategy:
- Pin ``REVERSE_SCORED_ITEMS_1INDEXED`` to Skinner 1982 (only item 3).
- Exhaustively test the reversal mapping 0↔1 on item 3.
- Pin that items 1, 2, 4–10 are NOT reversed.
- Boundary-test each band cutoff (0 none, 1–2 low, 3–5 moderate,
  6–8 substantial, 9–10 severe).  Both just-below and at-cutoff are
  pinned so a flipped operator is caught.
- Validate inputs: wrong count, out-of-range, wrong type, bool
  rejection.
- End-to-end clinical vignettes that a clinician would recognize.
"""

from __future__ import annotations

import pytest

from discipline.psychometric.scoring.dast10 import (
    DAST10_LOW_UPPER,
    DAST10_MODERATE_UPPER,
    DAST10_NONE_UPPER,
    DAST10_SUBSTANTIAL_UPPER,
    DAST10_TOTAL_MAX,
    DAST10_TOTAL_MIN,
    INSTRUMENT_VERSION,
    ITEM_COUNT,
    ITEM_MAX,
    ITEM_MIN,
    Dast10Result,
    InvalidResponseError,
    REVERSE_SCORED_ITEMS_1INDEXED,
    score_dast10,
)


# Zero-indexed position of the reverse-scored item (item 3 → 0-idx 2).
# Pinned here only for test-baseline construction — the instrument's
# identity lives in the module's REVERSE_SCORED_ITEMS_1INDEXED constant.
_REVERSE_POS_0IDX = {2}


def _baseline_items(overrides: dict[int, int] | None = None) -> list[int]:
    """Construct a 10-item raw response list that scores 0 before overrides.

    The reverse-scored position (item 3, 0-idx 2) defaults to raw 1
    ("yes, always able to stop") → scored 0.  Non-reverse positions
    default to raw 0.  Overriding a 0-indexed position sets that
    position to a specific raw value, isolating the contribution of
    each item in reverse-scoring tests — no noise from unmodified
    items.
    """
    items: list[int] = []
    for i in range(10):
        if overrides and i in overrides:
            items.append(overrides[i])
        elif i in _REVERSE_POS_0IDX:
            items.append(1)
        else:
            items.append(0)
    return items


# =============================================================================
# Constants
# =============================================================================


class TestConstants:
    def test_item_count_is_ten(self) -> None:
        assert ITEM_COUNT == 10

    def test_item_range_is_zero_to_one(self) -> None:
        """Skinner 1982 response scale is Yes/No encoded as 1/0."""
        assert ITEM_MIN == 0
        assert ITEM_MAX == 1

    def test_total_range(self) -> None:
        """Sum envelope: 10 items × 0-1 = 0-10."""
        assert DAST10_TOTAL_MIN == 0
        assert DAST10_TOTAL_MAX == 10

    def test_band_cutoffs_match_skinner_1982(self) -> None:
        """Cutoffs: 0 none, 1-2 low, 3-5 moderate, 6-8 substantial,
        9-10 severe.  Pinned so any refactor of the classifier has to
        pass through this test."""
        assert DAST10_NONE_UPPER == 0
        assert DAST10_LOW_UPPER == 2
        assert DAST10_MODERATE_UPPER == 5
        assert DAST10_SUBSTANTIAL_UPPER == 8

    def test_reverse_scored_is_only_item_3(self) -> None:
        """Item 3 ("Are you always able to stop using drugs when you
        want to?") is the only reverse-scored item in the DAST-10.
        A refactor that adds or drops items here silently mis-scores
        every administration."""
        assert REVERSE_SCORED_ITEMS_1INDEXED == frozenset({3})

    def test_reverse_scored_set_is_frozen(self) -> None:
        """Defensive cast to frozenset prevents a consumer from
        mutating the set and silently breaking future scorings."""
        assert isinstance(REVERSE_SCORED_ITEMS_1INDEXED, frozenset)

    def test_instrument_version_stable(self) -> None:
        assert INSTRUMENT_VERSION == "dast10-1.0.0"


# =============================================================================
# Reverse-scoring — the single highest-leverage bug vector
# =============================================================================


class TestReverseScoring:
    """Reverse-scoring item 3 is where DAST-10 bugs hide.  Every
    reversal mapping AND the 'only item 3 is reversed' property are
    pinned."""

    def test_reversal_raw_zero_becomes_scored_one(self) -> None:
        """Patient answers "no, I cannot always stop" → raw 0 on
        item 3 → scored 1 (endorses loss of control).  Baseline
        contributes 0, so the total is exactly 1."""
        items = _baseline_items({2: 0})  # item 3 (0-idx 2) = 0
        result = score_dast10(items)
        assert result.scored_items[2] == 1
        assert result.total == 1

    def test_reversal_raw_one_becomes_scored_zero(self) -> None:
        """Patient answers "yes, I can always stop" → raw 1 on
        item 3 → scored 0 (endorses control)."""
        items = _baseline_items({2: 1})
        result = score_dast10(items)
        assert result.scored_items[2] == 0
        assert result.total == 0

    def test_reversal_applies_only_to_item_3(self) -> None:
        """Non-reverse items keep their raw value.  Setting item 1
        (0-indexed 0) to raw 1 should produce scored 1 (not reversed
        to 0).  Catches the 'reverse everything' bug."""
        items = _baseline_items({0: 1})
        result = score_dast10(items)
        assert result.scored_items[0] == 1
        # Baseline is 0; overriding position 0 to raw 1 adds 1.
        assert result.total == 1

    def test_non_reverse_positions_never_invert(self) -> None:
        """Items 1, 2, 4, 5, 6, 7, 8, 9, 10 are NOT reverse-scored.
        Each at isolation should remain as-is.  Catches a bug where
        an off-by-one in the reverse-index set reverses a neighbor
        of item 3."""
        for one_indexed in (1, 2, 4, 5, 6, 7, 8, 9, 10):
            zero_indexed = one_indexed - 1
            items = _baseline_items({zero_indexed: 1})
            result = score_dast10(items)
            assert result.scored_items[zero_indexed] == 1, (
                f"Item {one_indexed} at 0-index {zero_indexed} should "
                f"not be reversed"
            )
            # total = 1 (the override) + 0 (item-3 baseline scored 0)
            assert result.total == 1, (
                f"Item {one_indexed} override produced total {result.total}"
            )

    def test_raw_items_preserved_pre_reversal(self) -> None:
        """``raw_items`` holds the caller's inputs, pre-reversal.  An
        auditor needs both: raw to verify data entry, scored to verify
        summation."""
        items = [1, 1, 1, 0, 0, 0, 0, 0, 0, 0]  # item 3 raw=1 (control)
        result = score_dast10(items)
        assert result.raw_items == tuple(items)
        # Item 3 reverses: raw 1 → scored 0.  All others unchanged.
        assert result.scored_items == (1, 1, 0, 0, 0, 0, 0, 0, 0, 0)
        assert result.total == 2


# =============================================================================
# Severity bands — boundary testing per Skinner 1982
# =============================================================================


class TestNoneBand:
    def test_total_zero_is_none(self) -> None:
        """Patient denies every drug-use item AND endorses control
        (item 3 raw=1 → scored 0).  No clinical action indicated."""
        items = _baseline_items()  # all zeros except item 3 = 1 → 0
        result = score_dast10(items)
        assert result.total == 0
        assert result.band == "none"

    def test_total_one_is_low_at_boundary(self) -> None:
        """A single positive item crosses out of 'none' into 'low'.
        A flipped ``<=`` to ``<`` would leave 1 in 'none'."""
        items = _baseline_items({0: 1})
        result = score_dast10(items)
        assert result.total == 1
        assert result.band == "low"


class TestLowBand:
    def test_total_one_is_low(self) -> None:
        items = _baseline_items({0: 1})
        result = score_dast10(items)
        assert result.total == 1
        assert result.band == "low"

    def test_total_two_is_low_at_boundary(self) -> None:
        """Upper bound of 'low'."""
        items = _baseline_items({0: 1, 1: 1})
        result = score_dast10(items)
        assert result.total == 2
        assert result.band == "low"

    def test_total_three_is_moderate(self) -> None:
        """At-cutoff the other way: 3 starts 'moderate' (the
        brief-intervention band)."""
        items = _baseline_items({0: 1, 1: 1, 3: 1})
        result = score_dast10(items)
        assert result.total == 3
        assert result.band == "moderate"


class TestModerateBand:
    def test_total_three_is_moderate_at_lower_boundary(self) -> None:
        items = _baseline_items({0: 1, 1: 1, 3: 1})
        result = score_dast10(items)
        assert result.total == 3
        assert result.band == "moderate"

    def test_total_five_is_moderate_at_upper_boundary(self) -> None:
        """Upper bound of moderate."""
        items = _baseline_items({0: 1, 1: 1, 3: 1, 4: 1, 5: 1})
        result = score_dast10(items)
        assert result.total == 5
        assert result.band == "moderate"

    def test_total_six_is_substantial(self) -> None:
        """At-cutoff the other way: 6 starts 'substantial' (the
        treatment-referral band)."""
        items = _baseline_items({0: 1, 1: 1, 3: 1, 4: 1, 5: 1, 6: 1})
        result = score_dast10(items)
        assert result.total == 6
        assert result.band == "substantial"


class TestSubstantialBand:
    def test_total_six_is_substantial_at_lower_boundary(self) -> None:
        items = _baseline_items({0: 1, 1: 1, 3: 1, 4: 1, 5: 1, 6: 1})
        result = score_dast10(items)
        assert result.total == 6
        assert result.band == "substantial"

    def test_total_eight_is_substantial_at_upper_boundary(self) -> None:
        """Upper bound of 'substantial'."""
        items = _baseline_items(
            {0: 1, 1: 1, 3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1}
        )
        result = score_dast10(items)
        assert result.total == 8
        assert result.band == "substantial"

    def test_total_nine_is_severe(self) -> None:
        """At-cutoff the other way: 9 starts 'severe' (the intensive-
        treatment band)."""
        items = _baseline_items(
            {0: 1, 1: 1, 3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 1}
        )
        result = score_dast10(items)
        assert result.total == 9
        assert result.band == "severe"


class TestSevereBand:
    def test_total_nine_is_severe_at_lower_boundary(self) -> None:
        items = _baseline_items(
            {0: 1, 1: 1, 3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 1}
        )
        result = score_dast10(items)
        assert result.total == 9
        assert result.band == "severe"

    def test_total_ten_is_severe_maximum(self) -> None:
        """Patient endorses every drug-use item AND cannot stop
        (item 3 raw=0 → scored 1) → maximum total 10, band severe."""
        items = [1, 1, 0, 1, 1, 1, 1, 1, 1, 1]
        result = score_dast10(items)
        assert result.total == 10
        assert result.band == "severe"


# =============================================================================
# Specific totals — arithmetic pinning
# =============================================================================


class TestArithmetic:
    def test_all_zero_raw(self) -> None:
        """All items 'no' — item 3 reverses to 1, total = 1, band low.
        A bug that skips reverse-scoring produces total=0 / band=none,
        which would under-report drug-use problems in a population
        that habitually answers 'no' to every question."""
        result = score_dast10([0] * 10)
        assert result.total == 1
        assert result.band == "low"

    def test_all_one_raw(self) -> None:
        """All items 'yes' — item 3 reverses to 0, non-item-3
        contribute 1 each (9 items), total = 9, band severe.  A bug
        that skips reverse-scoring would produce total=10, still
        severe band — but the raw/scored items tuple pin catches the
        reversal bug even when the band is coincidentally correct."""
        result = score_dast10([1] * 10)
        assert result.total == 9
        assert result.band == "severe"
        assert result.scored_items == (1, 1, 0, 1, 1, 1, 1, 1, 1, 1)

    def test_scored_items_length(self) -> None:
        result = score_dast10([0] * 10)
        assert len(result.scored_items) == 10

    def test_scored_items_exact_values(self) -> None:
        """Full 10-element pin of scored output for an arbitrary
        input.  Catches off-by-one in the reversal index."""
        # raw: [1, 0, 1, 0, 1, 0, 1, 0, 1, 0]
        # Only position 2 (item 3) reverses: raw 1 → scored 0.
        # scored: [1, 0, 0, 0, 1, 0, 1, 0, 1, 0]
        # total: 1+0+0+0+1+0+1+0+1+0 = 4
        result = score_dast10([1, 0, 1, 0, 1, 0, 1, 0, 1, 0])
        assert result.scored_items == (1, 0, 0, 0, 1, 0, 1, 0, 1, 0)
        assert result.total == 4
        assert result.band == "moderate"


# =============================================================================
# Validation
# =============================================================================


class TestValidation:
    def test_too_few_items_raises(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 10 items"):
            score_dast10([0] * 9)

    def test_too_many_items_raises(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 10 items"):
            score_dast10([0] * 11)

    def test_item_above_max_raises(self) -> None:
        """Raw 2 on a 0/1 scale is a wire-format bug."""
        with pytest.raises(InvalidResponseError, match=r"out of range \[0, 1\]"):
            score_dast10([2, 0, 0, 0, 0, 0, 0, 0, 0, 0])

    def test_item_below_min_raises(self) -> None:
        with pytest.raises(InvalidResponseError, match=r"out of range \[0, 1\]"):
            score_dast10([-1, 0, 0, 0, 0, 0, 0, 0, 0, 0])

    def test_error_identifies_offending_item_1indexed(self) -> None:
        """The error names the 1-indexed item so a clinician can
        point at the right question number on the paper form."""
        with pytest.raises(InvalidResponseError, match=r"item 5"):
            score_dast10([0, 0, 0, 0, 99, 0, 0, 0, 0, 0])

    def test_float_item_raises(self) -> None:
        """DAST-10 responses are yes/no integers; a float like 0.5
        is a wire-format bug we surface rather than silently
        truncating."""
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_dast10([0, 0, 0.5, 0, 0, 0, 0, 0, 0, 0])  # type: ignore[list-item]

    def test_bool_item_rejected(self) -> None:
        """``bool`` subclasses ``int`` in Python; True/False would
        silently pass a naive ``isinstance(v, int)`` check.  Even
        though True/False *would* numerically score correctly on the
        0/1 scale, we reject them for consistency with PSS-10 / PHQ-9
        / etc., which reject bools to catch upstream wire-format bugs
        on those wider scales."""
        items = [0, 0, 0, True, 0, 0, 0, 0, 0, 0]  # type: ignore[list-item]
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_dast10(items)


# =============================================================================
# Result shape
# =============================================================================


class TestResultShape:
    def test_result_is_frozen(self) -> None:
        result = score_dast10([0] * 10)
        with pytest.raises(Exception):  # FrozenInstanceError
            result.total = 99  # type: ignore[misc]

    def test_raw_items_is_tuple(self) -> None:
        result = score_dast10([0] * 10)
        assert isinstance(result.raw_items, tuple)

    def test_scored_items_is_tuple(self) -> None:
        result = score_dast10([0] * 10)
        assert isinstance(result.scored_items, tuple)

    def test_instrument_version_in_result(self) -> None:
        result = score_dast10([0] * 10)
        assert result.instrument_version == INSTRUMENT_VERSION

    def test_result_type(self) -> None:
        result = score_dast10([0] * 10)
        assert isinstance(result, Dast10Result)


# =============================================================================
# Clinical scenarios — end-to-end pinning
# =============================================================================


class TestClinicalScenarios:
    """End-to-end pins of realistic patient profiles.  These are the
    tests that translate most directly to 'did we score this paper
    form correctly' if a clinician handed us one."""

    def test_clean_history_none_band(self) -> None:
        """Patient denies drug use entirely and endorses that they
        could stop if they wanted to.  Should band as 'none'."""
        # All "no" except item 3 where "yes" (able to stop) = raw 1.
        items = [0, 0, 1, 0, 0, 0, 0, 0, 0, 0]
        result = score_dast10(items)
        assert result.total == 0
        assert result.band == "none"

    def test_casual_use_low_band(self) -> None:
        """Patient uses non-medical drugs and occasionally feels
        bad about it (2 endorsements) but reports control.  Classic
        'monitor' profile."""
        # item 1 yes (uses drugs), item 5 yes (feels guilty), item 3 yes (control).
        items = [1, 0, 1, 0, 1, 0, 0, 0, 0, 0]
        result = score_dast10(items)
        assert result.total == 2
        assert result.band == "low"

    def test_problematic_use_moderate_band(self) -> None:
        """Patient endorses control problems (item 3=no, scored 1),
        blackouts, guilt, and family complaints.  Four endorsements
        plus the reverse-scored contribution on item 3 → moderate."""
        # items 1, 4, 5, 6 yes; item 3 = no → scored 1.
        items = [1, 0, 0, 1, 1, 1, 0, 0, 0, 0]
        result = score_dast10(items)
        # Position 2 is raw 0 → scored 1.  Raw sum of others = 4.  Total = 5.
        assert result.total == 5
        assert result.band == "moderate"

    def test_severe_profile_intensive_treatment(self) -> None:
        """Patient endorses nearly every item including loss of
        control, withdrawal, and medical consequences.  Band 'severe'
        maps to intensive-treatment referral."""
        # All yes except item 3 = no (raw 0 → scored 1).
        items = [1, 1, 0, 1, 1, 1, 1, 1, 1, 1]
        result = score_dast10(items)
        assert result.total == 10
        assert result.band == "severe"

    def test_reverse_only_item_3_flip_sanity(self) -> None:
        """Pin the downstream consequence of flipping item 3 alone:
        a patient with no other endorsements who reports inability
        to stop (raw 0) scores 1 → band 'low'.  If the scorer treated
        item 3 like a normal item, the total would be 0 / band 'none',
        missing a meaningful clinical signal."""
        items = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        result = score_dast10(items)
        assert result.total == 1
        assert result.band == "low"

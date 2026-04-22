"""Unit tests for ERQ scorer (Gross & John 2003).

The ERQ is the "strategy choice" layer of the three-layer emotion-
processing architecture (TAS-20 identification / ERQ strategy /
DERS-16 execution).  These tests pin:

 1. Gross & John 2003 Study 1 CFA subscale assignments: reappraisal
    = (1, 3, 5, 7, 8, 10), suppression = (2, 4, 6, 9).  A silent
    refactor that reordered items or rotated subscale rows is the
    most plausible way the scorer could drift — each subscale test
    holds the mapping independently.
 2. 1-7 Likert envelope (NOT 1-5 like TAS-20 / DERS-16 / PSWQ).  The
    7-point anchor set is part of the validated instrument; the
    tests pin both boundaries (0 rejects below, 8 rejects above).
 3. Absence of reverse-keyed items — all 10 items are endorsement-
    direction for their subscale.  This is a distinguishing feature
    from TAS-20 (5 reverse) / LOT-R (3 reverse) / PSWQ (5 reverse).
 4. Bool rejection at scorer contract.  True / False must raise
    InvalidResponseError before int-range check, uniform with the
    rest of the psychometric package.
 5. Continuous-sentinel wire shape: ErqResult has no severity / no
    cutoff_used / no requires_t3 (enforced at the router dispatch
    layer; the scorer itself simply omits those fields).
 6. Clinical-vignette profile preservation: a reappraising profile
    (high on 1/3/5/7/8/10, low on 2/4/6/9) produces exactly the
    expected subscale sum pair, round-tripping the clinical signal
    we intend the instrument to carry.
"""

from __future__ import annotations

import pytest

from discipline.psychometric.scoring.erq import (
    ERQ_SUBSCALES,
    INSTRUMENT_VERSION,
    ITEM_COUNT,
    ITEM_MAX,
    ITEM_MIN,
    ErqResult,
    InvalidResponseError,
    score_erq,
)


class TestConstants:
    """Pin the Gross & John 2003 instrument constants."""

    def test_instrument_version_pinned(self) -> None:
        assert INSTRUMENT_VERSION == "erq-1.0.0"

    def test_item_count_is_ten(self) -> None:
        assert ITEM_COUNT == 10

    def test_item_min_is_one(self) -> None:
        # 1-7 Likert anchored at strongly-disagree=1, NOT 0.
        assert ITEM_MIN == 1

    def test_item_max_is_seven(self) -> None:
        # 1-7 Likert envelope (differs from TAS-20 / DERS-16's 1-5).
        assert ITEM_MAX == 7

    def test_reappraisal_subscale_has_six_items(self) -> None:
        assert len(ERQ_SUBSCALES["reappraisal"]) == 6

    def test_suppression_subscale_has_four_items(self) -> None:
        assert len(ERQ_SUBSCALES["suppression"]) == 4

    def test_reappraisal_positions_are_gross_john_2003(self) -> None:
        # Items 1, 3, 5, 7, 8, 10 per Study 1 CFA.
        assert ERQ_SUBSCALES["reappraisal"] == (1, 3, 5, 7, 8, 10)

    def test_suppression_positions_are_gross_john_2003(self) -> None:
        # Items 2, 4, 6, 9 per Study 1 CFA.
        assert ERQ_SUBSCALES["suppression"] == (2, 4, 6, 9)

    def test_all_ten_positions_covered_exactly_once(self) -> None:
        """The two subscales cover every item position exactly once.

        No item belongs to both subscales; no item is uncategorized.
        This is a stronger invariant than it looks — TAS-20 also has
        this property, but a refactor could easily add an item to
        both subscales without failing the length check above.
        """
        all_positions = (
            ERQ_SUBSCALES["reappraisal"] + ERQ_SUBSCALES["suppression"]
        )
        assert sorted(all_positions) == list(range(1, ITEM_COUNT + 1))


class TestTotalCorrectness:
    """Pin total = straight sum of 10 raw 1-7 items."""

    def test_all_ones_total_is_ten(self) -> None:
        result = score_erq([1] * 10)
        assert result.total == 10

    def test_all_sevens_total_is_seventy(self) -> None:
        result = score_erq([7] * 10)
        assert result.total == 70

    def test_all_fours_total_is_forty(self) -> None:
        # Midpoint on the 1-7 scale — sum = 4 × 10 = 40.
        result = score_erq([4] * 10)
        assert result.total == 40

    def test_total_reflects_heterogeneous_items(self) -> None:
        # Spread across the range to catch any silent integer mishap.
        items = [1, 2, 3, 4, 5, 6, 7, 1, 2, 3]
        result = score_erq(items)
        assert result.total == sum(items)
        assert result.total == 34

    def test_total_equals_reappraisal_plus_suppression(self) -> None:
        """The total is decomposable into the two subscale sums.

        This is a tautology given the ERQ coverage invariant (every
        item lives in exactly one subscale), but pinning it prevents
        a future refactor that (say) centers items or reports means
        from silently breaking the additive relationship.
        """
        items = [3, 5, 2, 7, 4, 6, 1, 3, 5, 2]
        result = score_erq(items)
        assert (
            result.total
            == result.subscale_reappraisal + result.subscale_suppression
        )

    def test_single_item_contributes_to_total(self) -> None:
        baseline = score_erq([1] * 10)
        # Flip item 1 (reappraisal) from 1 → 7; total jumps by 6.
        bumped = score_erq([7] + [1] * 9)
        assert bumped.total - baseline.total == 6

    def test_total_preserves_raw_values_across_repeats(self) -> None:
        # Scoring is a pure function — same input, same total.
        items = [2, 3, 5, 7, 1, 4, 6, 2, 4, 5]
        a = score_erq(items)
        b = score_erq(items)
        assert a.total == b.total

    def test_total_minimum_floor_is_ten(self) -> None:
        # No 0 in the Likert envelope; floor is 10, not 0.
        assert score_erq([1] * 10).total == 10

    def test_total_maximum_ceiling_is_seventy(self) -> None:
        # 7 × 10 = 70 is the ceiling per Gross & John 2003 scoring.
        assert score_erq([7] * 10).total == 70

    def test_total_is_int_type(self) -> None:
        # Wire integer — no floating-point from accidental mean use.
        result = score_erq([3] * 10)
        assert isinstance(result.total, int)


class TestSubscaleAssignments:
    """Pin Gross & John 2003 CFA subscale assignments per item."""

    def test_reappraisal_all_ones_is_six(self) -> None:
        # 6 items × 1 = 6.
        result = score_erq([1] * 10)
        assert result.subscale_reappraisal == 6

    def test_reappraisal_all_sevens_is_forty_two(self) -> None:
        # 6 items × 7 = 42.
        result = score_erq([7] * 10)
        assert result.subscale_reappraisal == 42

    def test_suppression_all_ones_is_four(self) -> None:
        # 4 items × 1 = 4.
        result = score_erq([1] * 10)
        assert result.subscale_suppression == 4

    def test_suppression_all_sevens_is_twenty_eight(self) -> None:
        # 4 items × 7 = 28.
        result = score_erq([7] * 10)
        assert result.subscale_suppression == 28

    def test_reappraisal_bump_does_not_leak_into_suppression(self) -> None:
        """Bumping a reappraisal item leaves suppression untouched.

        Mutation check: if a future refactor accidentally moved item
        1 (reappraisal) into the suppression tuple, this test would
        fail — the reappraisal sum would stay flat while suppression
        would bump instead of the expected direction.
        """
        baseline = score_erq([1] * 10)
        # Item 1 → 7 (reappraisal position).
        bumped = score_erq([7] + [1] * 9)
        assert bumped.subscale_reappraisal == baseline.subscale_reappraisal + 6
        assert bumped.subscale_suppression == baseline.subscale_suppression

    def test_suppression_bump_does_not_leak_into_reappraisal(self) -> None:
        baseline = score_erq([1] * 10)
        # Item 2 → 7 (suppression position).
        items = [1, 7, 1, 1, 1, 1, 1, 1, 1, 1]
        bumped = score_erq(items)
        assert bumped.subscale_suppression == baseline.subscale_suppression + 6
        assert bumped.subscale_reappraisal == baseline.subscale_reappraisal

    def test_reappraising_profile_subscales(self) -> None:
        """Classic reappraiser: high on R items, low on S items.

        Items 1/3/5/7/8/10 = 6 → R sum = 36.
        Items 2/4/6/9     = 2 → S sum = 8.
        """
        items = [6, 2, 6, 2, 6, 2, 6, 6, 2, 6]
        result = score_erq(items)
        assert result.subscale_reappraisal == 36
        assert result.subscale_suppression == 8

    def test_suppressing_profile_subscales(self) -> None:
        """Classic suppressor: low on R items, high on S items.

        Items 1/3/5/7/8/10 = 2 → R sum = 12.
        Items 2/4/6/9     = 6 → S sum = 24.
        """
        items = [2, 6, 2, 6, 2, 6, 2, 2, 6, 2]
        result = score_erq(items)
        assert result.subscale_reappraisal == 12
        assert result.subscale_suppression == 24


class TestItemCountValidation:
    """Reject inputs with the wrong number of items."""

    def test_nine_items_raises(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 10 items"):
            score_erq([3] * 9)

    def test_eleven_items_raises(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 10 items"):
            score_erq([3] * 11)

    def test_empty_items_raises(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 10 items"):
            score_erq([])

    def test_twenty_items_raises(self) -> None:
        # TAS-20-shaped input must not silently pass — ensures the
        # dispatch / scorer contract is not confused between sibling
        # instruments.
        with pytest.raises(InvalidResponseError, match="exactly 10 items"):
            score_erq([3] * 20)

    def test_single_item_raises(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 10 items"):
            score_erq([3])

    def test_count_error_names_actual_count(self) -> None:
        # Error message should name the received count so an
        # engineer debugging a malformed payload can see the issue.
        with pytest.raises(InvalidResponseError, match="got 5"):
            score_erq([3] * 5)


class TestItemRangeValidation:
    """Reject items outside the 1-7 Likert envelope."""

    def test_zero_rejects_below_floor(self) -> None:
        with pytest.raises(InvalidResponseError, match=r"out of range"):
            score_erq([0] + [3] * 9)

    def test_eight_rejects_above_ceiling(self) -> None:
        # 1-5 scorers like DERS-16 accept up to 5; ERQ extends to 7
        # but must reject 8.  Pins the upper boundary explicitly.
        with pytest.raises(InvalidResponseError, match=r"out of range"):
            score_erq([8] + [3] * 9)

    def test_negative_rejects(self) -> None:
        with pytest.raises(InvalidResponseError, match=r"out of range"):
            score_erq([-1] + [3] * 9)

    def test_large_positive_rejects(self) -> None:
        with pytest.raises(InvalidResponseError, match=r"out of range"):
            score_erq([100] + [3] * 9)

    def test_one_accepts_floor(self) -> None:
        result = score_erq([1] * 10)
        assert result.total == 10

    def test_seven_accepts_ceiling(self) -> None:
        result = score_erq([7] * 10)
        assert result.total == 70

    def test_range_error_names_item_position(self) -> None:
        # Error should name the 1-indexed position so a clinician
        # can cross-reference the ERQ document.
        with pytest.raises(InvalidResponseError, match="item 3"):
            score_erq([3, 3, 99, 3, 3, 3, 3, 3, 3, 3])

    def test_range_error_names_offending_value(self) -> None:
        with pytest.raises(InvalidResponseError, match="99"):
            score_erq([3, 3, 99, 3, 3, 3, 3, 3, 3, 3])

    def test_mid_sequence_out_of_range_rejects(self) -> None:
        # Validation must scan the whole sequence, not just item 1.
        items = [3, 3, 3, 3, 3, 3, 3, 3, 3, 0]
        with pytest.raises(InvalidResponseError, match="item 10"):
            score_erq(items)


class TestBoolRejection:
    """Reject bool values even though Python bool is an int subclass."""

    def test_true_rejects(self) -> None:
        # True == 1 in int arithmetic; scorer contract requires
        # explicit bool rejection so we do not silently score a
        # JSON-decoded boolean as a Likert 1.
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_erq([True] + [3] * 9)

    def test_false_rejects(self) -> None:
        # False == 0, which would ALSO fail the 1-7 range check, but
        # the bool check must fire FIRST — the error message should
        # say "must be int", not "out of range".
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_erq([False] + [3] * 9)

    def test_mixed_bool_in_sequence_rejects(self) -> None:
        items = [3, 3, 3, True, 3, 3, 3, 3, 3, 3]
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_erq(items)


class TestResultShape:
    """Pin the ErqResult dataclass contract."""

    def test_result_is_erq_result(self) -> None:
        result = score_erq([3] * 10)
        assert isinstance(result, ErqResult)

    def test_result_has_total_field(self) -> None:
        assert hasattr(score_erq([3] * 10), "total")

    def test_result_has_reappraisal_subscale(self) -> None:
        assert hasattr(score_erq([3] * 10), "subscale_reappraisal")

    def test_result_has_suppression_subscale(self) -> None:
        assert hasattr(score_erq([3] * 10), "subscale_suppression")

    def test_result_has_items_field(self) -> None:
        assert hasattr(score_erq([3] * 10), "items")

    def test_result_has_instrument_version_field(self) -> None:
        assert hasattr(score_erq([3] * 10), "instrument_version")

    def test_instrument_version_pinned_on_result(self) -> None:
        result = score_erq([3] * 10)
        assert result.instrument_version == "erq-1.0.0"

    def test_result_is_frozen(self) -> None:
        result = score_erq([3] * 10)
        with pytest.raises(Exception):  # dataclasses.FrozenInstanceError
            result.total = 99  # type: ignore[misc]

    def test_items_field_is_tuple(self) -> None:
        result = score_erq([3] * 10)
        assert isinstance(result.items, tuple)

    def test_items_preserves_input_verbatim(self) -> None:
        raw = [1, 2, 3, 4, 5, 6, 7, 1, 2, 3]
        result = score_erq(raw)
        assert result.items == tuple(raw)

    def test_no_severity_field(self) -> None:
        # Continuous-sentinel: the scorer emits NO severity band.
        # The router turns this into severity=None on the wire.
        result = score_erq([3] * 10)
        assert not hasattr(result, "severity")
        assert not hasattr(result, "band")

    def test_no_requires_t3_field(self) -> None:
        # ERQ has no safety item.  The scorer must not emit a
        # requires_t3 field at all; hard-coded False at the router.
        result = score_erq([3] * 10)
        assert not hasattr(result, "requires_t3")


class TestClinicalVignettes:
    """Plausible clinical response patterns preserved end-to-end."""

    def test_pure_reappraiser_profile(self) -> None:
        """Sevens on reappraisal items, ones on suppression items.

        R sum = 42 (max); S sum = 4 (floor).  This is the
        "protective profile" Aldao 2010 associates with the best
        outcomes across depression / anxiety / eating / substance.
        """
        items = [7, 1, 7, 1, 7, 1, 7, 7, 1, 7]
        result = score_erq(items)
        assert result.subscale_reappraisal == 42
        assert result.subscale_suppression == 4
        assert result.total == 46

    def test_pure_suppressor_profile(self) -> None:
        """Sevens on suppression items, ones on reappraisal items.

        R sum = 6 (floor); S sum = 28 (max).  This is the
        "highest-concern profile" — clinically associated with
        depression, poorer cardiovascular profile, poorer social
        relationships, and relapse risk in substance-use samples.
        """
        items = [1, 7, 1, 7, 1, 7, 1, 1, 7, 1]
        result = score_erq(items)
        assert result.subscale_reappraisal == 6
        assert result.subscale_suppression == 28
        assert result.total == 34

    def test_mixed_high_both_profile(self) -> None:
        """High on both strategies — uses everything available.

        R sum = 36; S sum = 24.  Common in anxious-achiever
        profiles; neither protective nor maximally harmful.
        """
        items = [6, 6, 6, 6, 6, 6, 6, 6, 6, 6]
        result = score_erq(items)
        assert result.subscale_reappraisal == 36
        assert result.subscale_suppression == 24
        assert result.total == 60

    def test_mixed_low_both_profile(self) -> None:
        """Low on both — doesn't actively regulate either way.

        R sum = 12; S sum = 8.  Often pairs with high DERS-16
        (no active strategy at all) — the patient's default
        is "emotion washes over me"; skills training starts
        from zero.
        """
        items = [2, 2, 2, 2, 2, 2, 2, 2, 2, 2]
        result = score_erq(items)
        assert result.subscale_reappraisal == 12
        assert result.subscale_suppression == 8
        assert result.total == 20

    def test_midline_neutral_profile(self) -> None:
        """All fours — neutral on every strategy endorsement.

        R sum = 24; S sum = 16.  Often an acquiescence / don't-
        want-to-commit response pattern; pairs with flat DERS-16
        for profile interpretation.
        """
        items = [4] * 10
        result = score_erq(items)
        assert result.subscale_reappraisal == 24
        assert result.subscale_suppression == 16
        assert result.total == 40


class TestNoSafetyRouting:
    """ERQ has no safety item — nothing ever routes to T3/T4."""

    def test_maximal_total_emits_no_requires_t3(self) -> None:
        """Even ceiling total does not carry a safety-escalation bit.

        T3/T4 routing is reserved for explicit safety instruments
        (C-SSRS, PHQ-9 item 9, PCL-5).  ERQ is a dispositional
        strategy measure; maximum suppression is clinically
        concerning but not a crisis signal.
        """
        result = score_erq([7] * 10)
        assert not hasattr(result, "requires_t3")
        assert not hasattr(result, "triggering_items")

    def test_pure_suppressor_emits_no_requires_t3(self) -> None:
        # Pure-suppressor profile is the highest-concern ERQ
        # pattern but still not a safety-escalation trigger.
        items = [1, 7, 1, 7, 1, 7, 1, 1, 7, 1]
        result = score_erq(items)
        assert not hasattr(result, "requires_t3")

    def test_no_triggering_items_field(self) -> None:
        # OCIR / PHQ-9 / PCL-5 carry triggering-items payloads.
        # ERQ has none.
        result = score_erq([3] * 10)
        assert not hasattr(result, "triggering_items")

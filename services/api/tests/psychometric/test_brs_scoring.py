"""Tests for BRS scorer — Smith et al. 2008 Brief Resilience Scale.

Direction: HIGHER SUM = MORE RESILIENT.  Opposite of PHQ-9 / GAD-7 /
AUDIT / PGSI.  Matches WHO-5 / MAAS / CD-RISC-10 higher-is-better
convention.

Reverse-keying: items 2, 4, 6 are negatively worded and are flipped
at scoring time using the ``6 - raw`` reflection idiom (shared with
TAS-20 / PSWQ / LOT-R).  The ``items`` field of the result preserves
the RAW PRE-FLIP responses — audit-trail invariant.

Band thresholds (Smith 2008 §3.3, mean-based, mapped to integer sum):

- Low     mean 1.00-2.99  ->  sum  6-17
- Normal  mean 3.00-4.30  ->  sum 18-25
- High    mean 4.31-5.00  ->  sum 26-30
"""

from __future__ import annotations

import pytest

from discipline.psychometric.scoring import brs
from discipline.psychometric.scoring.brs import (
    BRS_REVERSE_ITEMS,
    BRS_SEVERITY_THRESHOLDS,
    INSTRUMENT_VERSION,
    ITEM_COUNT,
    ITEM_MAX,
    ITEM_MIN,
    BrsResult,
    InvalidResponseError,
    score_brs,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


class TestConstants:
    """Pin the published structure of the BRS instrument.

    Any change here is a clinical decision (Smith 2008 derivation) —
    not an implementation tweak.
    """

    def test_instrument_version(self) -> None:
        assert INSTRUMENT_VERSION == "brs-1.0.0"

    def test_item_count_is_six(self) -> None:
        assert ITEM_COUNT == 6

    def test_item_min_is_one(self) -> None:
        assert ITEM_MIN == 1

    def test_item_max_is_five(self) -> None:
        assert ITEM_MAX == 5

    def test_reverse_items_are_two_four_six(self) -> None:
        # Smith 2008 Table 1: items 2, 4, 6 are the negatively
        # worded "it is hard for me to bounce back / snap back /
        # I tend to take a long time..." items.  Changing this
        # set invalidates the EFA-derived structure.
        assert BRS_REVERSE_ITEMS == (2, 4, 6)

    def test_severity_thresholds_are_smith_2008_mapped(self) -> None:
        # Pin the exact Smith 2008 bands mapped to integer sum:
        #   low  <= 17
        #   normal <= 25
        #   high <= 30
        assert BRS_SEVERITY_THRESHOLDS == (
            (17, "low"),
            (25, "normal"),
            (30, "high"),
        )

    def test_no_positive_cutoff_exported(self) -> None:
        # BRS is banded, not a binary screen.  A BRS_POSITIVE_CUTOFF
        # constant would be a category error.
        assert not hasattr(brs, "BRS_POSITIVE_CUTOFF")

    def test_no_subscales_exported(self) -> None:
        # Smith 2008 §3.2 EFA: single factor by construction.
        # Surfacing subscales would contradict the derivation.
        assert not hasattr(brs, "BRS_SUBSCALES")

    def test_public_exports(self) -> None:
        # Lock the public surface so a contributor cannot silently
        # widen the API.
        assert set(brs.__all__) == {
            "BRS_REVERSE_ITEMS",
            "BRS_SEVERITY_THRESHOLDS",
            "BrsResult",
            "INSTRUMENT_VERSION",
            "ITEM_COUNT",
            "ITEM_MAX",
            "ITEM_MIN",
            "InvalidResponseError",
            "Severity",
            "score_brs",
        }


# ---------------------------------------------------------------------------
# Total correctness — post-flip arithmetic
# ---------------------------------------------------------------------------


class TestTotalCorrectness:
    """Verify post-flip summation produces the published total."""

    def test_all_ones_total_is_eighteen(self) -> None:
        # Raw all-1s: non-reverse items 1,3,5 contribute 1+1+1=3.
        # Reverse items 2,4,6 flip 1->5 and contribute 5+5+5=15.
        # Total = 3 + 15 = 18.  Acquiescence-bias anchor: both
        # uniform-response extremes land at 18 (low-normal
        # boundary) by Smith 2008 design.
        result = score_brs([1, 1, 1, 1, 1, 1])
        assert result.total == 18

    def test_all_fives_total_is_eighteen(self) -> None:
        # Raw all-5s: non-reverse items 1,3,5 contribute 5+5+5=15.
        # Reverse items 2,4,6 flip 5->1 and contribute 1+1+1=3.
        # Total = 15 + 3 = 18.  The SAME as all-1s — this is the
        # acquiescence-bias control property.
        result = score_brs([5, 5, 5, 5, 5, 5])
        assert result.total == 18

    def test_maximally_resilient_is_thirty(self) -> None:
        # Raw [5,1,5,1,5,1] — agrees with every "I bounce back"
        # item (positions 1,3,5 = 5) and disagrees with every
        # "it is hard to bounce back" item (positions 2,4,6 = 1).
        # Post-flip: [5, 6-1=5, 5, 6-1=5, 5, 6-1=5] = 30.
        result = score_brs([5, 1, 5, 1, 5, 1])
        assert result.total == 30

    def test_minimally_resilient_is_six(self) -> None:
        # Raw [1,5,1,5,1,5] — disagrees with every positive item
        # and agrees with every negative item.
        # Post-flip: [1, 6-5=1, 1, 6-5=1, 1, 6-5=1] = 6.
        result = score_brs([1, 5, 1, 5, 1, 5])
        assert result.total == 6

    def test_all_threes_is_eighteen(self) -> None:
        # Raw [3,3,3,3,3,3] — middle responses on every item.
        # Post-flip: [3, 6-3=3, 3, 6-3=3, 3, 6-3=3] = 18.
        # The geometric center of the BRS space.
        result = score_brs([3, 3, 3, 3, 3, 3])
        assert result.total == 18

    def test_asymmetric_response_no_double_counting(self) -> None:
        # Raw [4,2,4,2,4,2] — consistent "moderately resilient"
        # pattern: agrees somewhat with positives (4), disagrees
        # somewhat with negatives (2).
        # Post-flip: [4, 6-2=4, 4, 6-2=4, 4, 6-2=4] = 24.
        result = score_brs([4, 2, 4, 2, 4, 2])
        assert result.total == 24


# ---------------------------------------------------------------------------
# Band classification — boundary pins
# ---------------------------------------------------------------------------


class TestBandClassification:
    """Pin every band boundary in both directions.

    Thresholds: low <= 17, normal <= 25, high <= 30.
    """

    def test_total_six_is_low(self) -> None:
        # Absolute minimum resilience.
        result = score_brs([1, 5, 1, 5, 1, 5])
        assert result.total == 6
        assert result.severity == "low"

    def test_total_seventeen_is_low_upper_boundary(self) -> None:
        # Last integer in the low band.  Construct post-flip
        # [3,3,3,3,3,2] = 17 via raw [3,3,3,3,3,4] (position 6
        # reverse: 6-4=2).
        result = score_brs([3, 3, 3, 3, 3, 4])
        assert result.total == 17
        assert result.severity == "low"

    def test_total_eighteen_is_normal_lower_boundary(self) -> None:
        # First integer in the normal band.
        result = score_brs([3, 3, 3, 3, 3, 3])
        assert result.total == 18
        assert result.severity == "normal"

    def test_total_twenty_five_is_normal_upper_boundary(self) -> None:
        # Last integer in the normal band.  Construct post-flip
        # [4,4,4,4,4,5] = 25 via raw [4,2,4,2,4,1].
        result = score_brs([4, 2, 4, 2, 4, 1])
        assert result.total == 25
        assert result.severity == "normal"

    def test_total_twenty_six_is_high_lower_boundary(self) -> None:
        # First integer in the high band.  Construct post-flip
        # [5,5,5,5,5,1] = 26 via raw [5,1,5,1,5,5].
        result = score_brs([5, 1, 5, 1, 5, 5])
        assert result.total == 26
        assert result.severity == "high"

    def test_total_thirty_is_high(self) -> None:
        # Absolute maximum resilience.
        result = score_brs([5, 1, 5, 1, 5, 1])
        assert result.total == 30
        assert result.severity == "high"

    def test_acquiescence_uniform_ones_is_normal(self) -> None:
        # Uniform 1s score as NORMAL despite "least agreeable"
        # response pattern — this is the BRS three-positive /
        # three-negative response-bias control in action.
        result = score_brs([1, 1, 1, 1, 1, 1])
        assert result.total == 18
        assert result.severity == "normal"

    def test_acquiescence_uniform_fives_is_normal(self) -> None:
        # Uniform 5s score as NORMAL despite "most agreeable"
        # response pattern — the same control property.
        result = score_brs([5, 5, 5, 5, 5, 5])
        assert result.total == 18
        assert result.severity == "normal"

    def test_middle_responses_are_normal(self) -> None:
        result = score_brs([3, 3, 3, 3, 3, 3])
        assert result.severity == "normal"

    def test_low_by_post_flip_not_raw(self) -> None:
        # Raw [2,2,2,2,2,2]: post-flip [2,4,2,4,2,4] = 18.  SAME
        # as all-1s / all-5s — NORMAL band, not low.  Pins the
        # invariant that the LOW band requires an informed
        # response pattern (not a uniform one).
        result = score_brs([2, 2, 2, 2, 2, 2])
        assert result.total == 18
        assert result.severity == "normal"


# ---------------------------------------------------------------------------
# Direction semantics — positive vs negative item behavior
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "item_position,raw_value,expected_post_flip",
    [
        # Non-reverse items (1, 3, 5) pass through unchanged.
        (1, 1, 1),
        (1, 3, 3),
        (1, 5, 5),
        (3, 1, 1),
        (3, 5, 5),
        (5, 1, 1),
        (5, 5, 5),
        # Reverse items (2, 4, 6) flip via 6 - raw.
        (2, 1, 5),
        (2, 3, 3),
        (2, 5, 1),
        (4, 1, 5),
        (4, 3, 3),
        (4, 5, 1),
        (6, 1, 5),
        (6, 3, 3),
        (6, 5, 1),
    ],
)
def test_reverse_scoring_direction(
    item_position: int, raw_value: int, expected_post_flip: int
) -> None:
    """Direct pin of `_flip_if_reverse` behavior for every item.

    Uses the private helper by indirection — construct a 6-item
    response where only the probed position varies from the
    all-neutral-3 baseline and verify the total shifts by the
    expected post-flip delta vs 18.
    """
    items = [3, 3, 3, 3, 3, 3]
    items[item_position - 1] = raw_value
    # Baseline post_flip sum = 18 (all 3s at every position).
    # Changing position `item_position` from 3 to `raw_value`
    # changes its post-flip from 3 to `expected_post_flip`.
    expected_total = 18 - 3 + expected_post_flip

    result = score_brs(items)
    assert result.total == expected_total


class TestDirectionSemantics:
    """Additional direction pins beyond the parametrized grid."""

    def test_max_agree_positive_increases_total(self) -> None:
        # Raise item 1 (positive) from 3 to 5 -> total +2.
        base = score_brs([3, 3, 3, 3, 3, 3]).total
        raised = score_brs([5, 3, 3, 3, 3, 3]).total
        assert raised == base + 2

    def test_max_agree_negative_decreases_total(self) -> None:
        # Raise item 2 (negative, reverse-keyed) from 3 to 5 ->
        # post-flip goes from 3 to 1 -> total -2.
        base = score_brs([3, 3, 3, 3, 3, 3]).total
        raised = score_brs([3, 5, 3, 3, 3, 3]).total
        assert raised == base - 2

    def test_higher_is_more_resilient(self) -> None:
        # Global invariant: every single-position increase toward
        # the resilient extreme raises the total.
        resilient = score_brs([5, 1, 5, 1, 5, 1]).total
        not_resilient = score_brs([1, 5, 1, 5, 1, 5]).total
        assert resilient > not_resilient


# ---------------------------------------------------------------------------
# Item-count validation
# ---------------------------------------------------------------------------


class TestItemCountValidation:
    def test_five_items_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 6"):
            score_brs([3, 3, 3, 3, 3])

    def test_seven_items_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 6"):
            score_brs([3, 3, 3, 3, 3, 3, 3])

    def test_zero_items_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 6"):
            score_brs([])

    def test_ten_items_rejected(self) -> None:
        # Trap: someone confuses BRS (6) with CD-RISC-10 (10).
        with pytest.raises(InvalidResponseError, match="exactly 6"):
            score_brs([3] * 10)

    def test_twenty_items_rejected(self) -> None:
        # Trap: someone confuses BRS (6) with TAS-20 (20).
        with pytest.raises(InvalidResponseError, match="exactly 6"):
            score_brs([3] * 20)


# ---------------------------------------------------------------------------
# Item-range validation
# ---------------------------------------------------------------------------


class TestItemRangeValidation:
    def test_zero_rejected(self) -> None:
        # BRS Likert is 1-5, not 0-5.
        with pytest.raises(InvalidResponseError, match=r"in 1-5"):
            score_brs([0, 3, 3, 3, 3, 3])

    def test_six_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match=r"in 1-5"):
            score_brs([6, 3, 3, 3, 3, 3])

    def test_negative_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match=r"in 1-5"):
            score_brs([-1, 3, 3, 3, 3, 3])

    def test_range_violation_reports_correct_index(self) -> None:
        # Pin that error messages are 1-indexed for clinician
        # readability.  Item at position 4 (0-indexed 3) is out.
        with pytest.raises(InvalidResponseError, match=r"item 4"):
            score_brs([3, 3, 3, 99, 3, 3])


# ---------------------------------------------------------------------------
# Bool rejection — CLAUDE.md standing rule
# ---------------------------------------------------------------------------


class TestBoolRejection:
    """CLAUDE.md standing rule: ``bool`` values are rejected at the
    scorer even though ``bool is int`` in Python.  This keeps the
    wire contract explicit: a BRS item is never a flag."""

    def test_true_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_brs([True, 3, 3, 3, 3, 3])

    def test_false_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_brs([False, 3, 3, 3, 3, 3])

    def test_bool_in_any_position_rejected(self) -> None:
        # Position 6 is a reverse-keyed item — make sure bool
        # rejection fires BEFORE reverse-scoring arithmetic.
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_brs([3, 3, 3, 3, 3, True])

    def test_float_rejected(self) -> None:
        # Even an integer-valued float is rejected.  Wire contract
        # is "int", not "int-like".
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_brs([3.0, 3, 3, 3, 3, 3])  # type: ignore[list-item]

    def test_none_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_brs([None, 3, 3, 3, 3, 3])  # type: ignore[list-item]


# ---------------------------------------------------------------------------
# Result shape
# ---------------------------------------------------------------------------


class TestResultShape:
    """Pin the on-the-wire envelope — absences are as important as
    presences because the routing layer reads fields by name."""

    def test_returns_brs_result(self) -> None:
        result = score_brs([3, 3, 3, 3, 3, 3])
        assert isinstance(result, BrsResult)

    def test_total_field_present(self) -> None:
        result = score_brs([3, 3, 3, 3, 3, 3])
        assert result.total == 18

    def test_severity_field_present(self) -> None:
        result = score_brs([3, 3, 3, 3, 3, 3])
        assert result.severity == "normal"

    def test_instrument_version_field_present(self) -> None:
        result = score_brs([3, 3, 3, 3, 3, 3])
        assert result.instrument_version == INSTRUMENT_VERSION

    def test_items_stores_raw_pre_flip(self) -> None:
        # Audit-trail invariant.  Raw [5,5,5,5,5,5] produces
        # post-flip [5,1,5,1,5,1], but items stores the raw.
        raw = [5, 5, 5, 5, 5, 5]
        result = score_brs(raw)
        assert result.items == tuple(raw)

    def test_items_is_tuple_not_list(self) -> None:
        # Frozen / hashable result.
        result = score_brs([3, 3, 3, 3, 3, 3])
        assert isinstance(result.items, tuple)

    def test_result_is_frozen(self) -> None:
        result = score_brs([3, 3, 3, 3, 3, 3])
        with pytest.raises((AttributeError, Exception)):
            result.total = 99  # type: ignore[misc]

    def test_result_is_hashable(self) -> None:
        # Frozen dataclass contract.
        result = score_brs([3, 3, 3, 3, 3, 3])
        assert hash(result) == hash(result)

    def test_no_positive_screen_field(self) -> None:
        # BRS is banded, not a binary screen.
        result = score_brs([3, 3, 3, 3, 3, 3])
        assert not hasattr(result, "positive_screen")

    def test_no_cutoff_used_field(self) -> None:
        result = score_brs([3, 3, 3, 3, 3, 3])
        assert not hasattr(result, "cutoff_used")

    def test_no_subscales_field(self) -> None:
        # Smith 2008 §3.2 single-factor solution.
        result = score_brs([3, 3, 3, 3, 3, 3])
        assert not hasattr(result, "subscales")

    def test_no_requires_t3_field(self) -> None:
        # No BRS item probes suicidality, self-harm, or acute-risk
        # behavior.  Acute-risk screening stays on C-SSRS / PHQ-9
        # item 9.
        result = score_brs([3, 3, 3, 3, 3, 3])
        assert not hasattr(result, "requires_t3")


# ---------------------------------------------------------------------------
# Clinical vignettes — realistic response patterns per band
# ---------------------------------------------------------------------------


class TestClinicalVignettes:
    """Hand-constructed realistic response patterns that cover
    each Smith 2008 band from typical clinical presentations."""

    def test_low_resilience_depression_profile(self) -> None:
        # Patient endorses depression-consistent low bounce-back:
        # disagrees slightly with positives, agrees slightly with
        # negatives.  Raw [2,4,2,4,2,4] -> post [2,2,2,2,2,2] = 12.
        result = score_brs([2, 4, 2, 4, 2, 4])
        assert result.total == 12
        assert result.severity == "low"

    def test_low_resilience_severe_profile(self) -> None:
        # Strong-disagree to positives, strong-agree to negatives.
        # Raw [1,5,1,5,1,5] -> post [1,1,1,1,1,1] = 6.
        result = score_brs([1, 5, 1, 5, 1, 5])
        assert result.total == 6
        assert result.severity == "low"

    def test_normal_resilience_mixed_profile(self) -> None:
        # Typical general-population pattern: moderately agree
        # with positives, moderately disagree with negatives.
        # Raw [4,2,4,2,4,2] -> post [4,4,4,4,4,4] = 24.
        result = score_brs([4, 2, 4, 2, 4, 2])
        assert result.total == 24
        assert result.severity == "normal"

    def test_normal_resilience_upper_boundary(self) -> None:
        # Close to but not crossing into high.
        # Raw [4,2,4,2,4,1] -> post [4,4,4,4,4,5] = 25.
        result = score_brs([4, 2, 4, 2, 4, 1])
        assert result.total == 25
        assert result.severity == "normal"

    def test_high_resilience_recovered_profile(self) -> None:
        # Post-treatment recovery pattern: strong positive
        # endorsement, mild disagreement with negatives.
        # Raw [5,1,5,2,5,1] -> post [5,5,5,4,5,5] = 29.
        result = score_brs([5, 1, 5, 2, 5, 1])
        assert result.total == 29
        assert result.severity == "high"

    def test_high_resilience_ceiling(self) -> None:
        # Maximum score.
        # Raw [5,1,5,1,5,1] -> post [5,5,5,5,5,5] = 30.
        result = score_brs([5, 1, 5, 1, 5, 1])
        assert result.total == 30
        assert result.severity == "high"


# ---------------------------------------------------------------------------
# Safety routing — no T3/T4 triggering from BRS
# ---------------------------------------------------------------------------


class TestNoSafetyRouting:
    """BRS probes resilience outcomes, not ideation — no item is
    a safety item.  Pin that even extreme low-resilience scores
    produce NO requires_t3 field / attribute."""

    def test_minimum_resilience_does_not_signal_safety(self) -> None:
        # Lowest possible BRS (6) is NOT a safety flag.  The
        # platform's safety framework runs on C-SSRS / PHQ-9 item
        # 9, not BRS.
        result = score_brs([1, 5, 1, 5, 1, 5])
        assert result.total == 6
        assert result.severity == "low"
        assert not hasattr(result, "requires_t3")

    def test_every_minimum_item_response_no_safety_attribute(self) -> None:
        # Even the acquiescence all-1s case (which scores normal)
        # emits no safety attribute — BRS is not a safety
        # instrument.
        result = score_brs([1, 1, 1, 1, 1, 1])
        assert not hasattr(result, "requires_t3")

    def test_every_maximum_item_response_no_safety_attribute(self) -> None:
        result = score_brs([5, 5, 5, 5, 5, 5])
        assert not hasattr(result, "requires_t3")

    def test_any_single_item_extreme_no_safety_attribute(self) -> None:
        # Position-by-position: no single item produces a safety
        # attribute.
        for position in range(6):
            for extreme in (ITEM_MIN, ITEM_MAX):
                items = [3] * 6
                items[position] = extreme
                result = score_brs(items)
                assert not hasattr(result, "requires_t3"), (
                    f"position {position + 1} value {extreme} "
                    f"unexpectedly set requires_t3"
                )

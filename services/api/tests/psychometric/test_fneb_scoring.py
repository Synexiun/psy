"""Tests for FNE-B scorer — Leary 1983 Brief Fear of Negative Evaluation.

Direction: HIGHER SUM = MORE fear of negative evaluation (lower-is-
better).  Uniform with PHQ-9 / GAD-7 / AUDIT / PSS-10 / PGSI /
SHAPS / STAI-6.  OPPOSITE of WHO-5 / BRS / RSES / FFMQ-15 / MAAS /
LOT-R.

Reverse-keying: Leary 1983 positions 2, 4, 7, 10 are the four
positively-worded items (assertions of LACK of social-evaluation
concern — "unconcerned", "rarely worry", "opinions do not bother me",
"judging me has little effect on me").  Remaining 8 items are
negatively worded.  Flipped via ``(ITEM_MIN + ITEM_MAX) - raw =
6 - raw``.  The ``items`` field of the result preserves RAW PRE-
FLIP responses — audit-trail invariant shared with BRS / RSES /
TAS-20 / PANAS-10 / FFMQ-15 / STAI-6.

Asymmetric acquiescence signature: Leary 1983's 8-straight / 4-
reverse split means CONSTANT vectors do NOT land at the midpoint.
Raw all-1s yields 28 (8 straight × 1 + 4 reverse × (6-1)=5 = 8+20);
raw all-5s yields 44 (8×5 + 4×(6-5)=1 = 40+4).  Differ-by-16 is the
Leary 1983 wire-level signature — STRONGER acquiescence-bias
sensitivity than STAI-6 (symmetric 3/3 → differ-by-0) or RSES
(symmetric 5/5 → differ-by-0), though weaker than a fully-straight
scale like BFNE-II.

No severity bands (``severity="continuous"``) — Leary 1983 did NOT
publish cutpoints.  Collins 2005 clinical-sample cutoff (>= 49) is
secondary literature.  RCI at the trajectory layer drives clinical-
significance determination.
"""

from __future__ import annotations

import pytest

from discipline.psychometric.scoring import fneb
from discipline.psychometric.scoring.fneb import (
    FNEB_REVERSE_ITEMS,
    INSTRUMENT_VERSION,
    ITEM_COUNT,
    ITEM_MAX,
    ITEM_MIN,
    InvalidResponseError,
    score_fneb,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


class TestConstants:
    """Pin the published structure of the FNE-B instrument.

    Any change here is a clinical decision (Leary 1983 derivation) —
    not an implementation tweak.  Changing the reverse-items tuple
    invalidates the r = 0.96 equivalence to the Watson & Friend 1969
    FNE established in Leary 1983's factor-analytic derivation.
    """

    def test_instrument_version(self) -> None:
        assert INSTRUMENT_VERSION == "fneb-1.0.0"

    def test_item_count_is_twelve(self) -> None:
        assert ITEM_COUNT == 12

    def test_item_min_is_one(self) -> None:
        # Leary 1983 anchor: 1 = "Not at all characteristic of me".
        assert ITEM_MIN == 1

    def test_item_max_is_five(self) -> None:
        # Leary 1983 anchor: 5 = "Extremely characteristic of me".
        # 5-point Likert, NOT the 4-point scale of STAI-6.
        assert ITEM_MAX == 5

    def test_reverse_items_are_two_four_seven_ten(self) -> None:
        # Leary 1983 Appendix: positions 2, 4, 7, 10 are the four
        # "unconcerned / rarely worry / opinions do not bother me /
        # judging has little effect" positively-worded items.
        # Changing this tuple invalidates the r = 0.96 equivalence
        # to Watson & Friend 1969 FNE and is a clinical-QA-gated
        # change.
        assert FNEB_REVERSE_ITEMS == (2, 4, 7, 10)

    def test_reverse_items_are_four_items(self) -> None:
        # Leary 1983: 4 reverse out of 12 = asymmetric 8/4 split.
        # This is the scale's acquiescence-bias signature; BFNE-II
        # (Carleton 2007) dropped all 4 reverse items citing
        # reliability concerns but that's a SEPARATE instrument.
        assert len(FNEB_REVERSE_ITEMS) == 4

    def test_reverse_items_are_in_valid_range(self) -> None:
        for position in FNEB_REVERSE_ITEMS:
            assert 1 <= position <= ITEM_COUNT

    def test_no_severity_thresholds_exported(self) -> None:
        # FNE-B is intentionally banded="continuous".  Leary 1983
        # did not publish cutpoints; a FNEB_SEVERITY_THRESHOLDS
        # tuple would violate CLAUDE.md "no hand-rolled severity
        # thresholds" rule.
        assert not hasattr(fneb, "FNEB_SEVERITY_THRESHOLDS")

    def test_no_positive_cutoff_exported(self) -> None:
        # FNE-B is not a screen.  Collins 2005's >= 49 cutoff is
        # secondary-literature and not pinned as a platform band.
        assert not hasattr(fneb, "FNEB_POSITIVE_CUTOFF")

    def test_no_subscales_exported(self) -> None:
        # FNE-B is single-factor per Leary 1983 derivation;
        # confirmed by Rodebaugh 2004 CFA and Weeks 2005.
        assert not hasattr(fneb, "FNEB_SUBSCALES")

    def test_public_exports(self) -> None:
        assert set(fneb.__all__) == {
            "FNEB_REVERSE_ITEMS",
            "INSTRUMENT_VERSION",
            "ITEM_COUNT",
            "ITEM_MAX",
            "ITEM_MIN",
            "InvalidResponseError",
            "FnebResult",
            "Severity",
            "score_fneb",
        }


# ---------------------------------------------------------------------------
# Total correctness — post-flip arithmetic
# ---------------------------------------------------------------------------


class TestTotalCorrectness:
    """Verify post-flip summation produces the canonical Leary 1983
    total in the published 12-60 range."""

    def test_all_ones_total_is_twenty_eight(self) -> None:
        # Raw all-1s: 8 straight items contribute 1 each (= 8);
        # 4 reverse items flip 1->5 each (= 20).  Total = 28.
        # Asymmetric-acquiescence-bias anchor: NOT the midpoint.
        result = score_fneb([1] * 12)
        assert result.total == 28

    def test_all_fives_total_is_forty_four(self) -> None:
        # Raw all-5s: 8 straight items contribute 5 each (= 40);
        # 4 reverse items flip 5->1 each (= 4).  Total = 44.
        # Mirror of the all-1s extreme; differ by 16 per asymmetric
        # split (contrast with STAI-6's differ-by-0 symmetric
        # property).
        result = score_fneb([5] * 12)
        assert result.total == 44

    def test_all_threes_total_is_thirty_six(self) -> None:
        # Raw all-3s: 12 items × (post-flip 3) = 36.  The geometric
        # center of the FNE-B space.  (8 straight × 3 + 4 reverse
        # × (6-3)=3 = 24 + 12 = 36.)
        result = score_fneb([3] * 12)
        assert result.total == 36

    def test_all_twos_total_is_thirty_two(self) -> None:
        # Raw all-2s: 8 straight × 2 = 16; 4 reverse × (6-2)=4 = 16.
        # Total = 32.
        result = score_fneb([2] * 12)
        assert result.total == 32

    def test_all_fours_total_is_forty(self) -> None:
        # Raw all-4s: 8 straight × 4 = 32; 4 reverse × (6-4)=2 = 8.
        # Total = 40.
        result = score_fneb([4] * 12)
        assert result.total == 40

    def test_maximally_fearful_is_sixty(self) -> None:
        # Raw [5,1,5,1,5,5,1,5,5,1,5,5] — agrees maximally with
        # every straight item and disagrees with every reverse
        # item.  Post-flip: [5,5,5,5,5,5,5,5,5,5,5,5] = 60.
        # Absolute-maximum-fear pattern.
        result = score_fneb([5, 1, 5, 1, 5, 5, 1, 5, 5, 1, 5, 5])
        assert result.total == 60

    def test_minimally_fearful_is_twelve(self) -> None:
        # Raw [1,5,1,5,1,1,5,1,1,5,1,1] — disagrees with every
        # straight item and agrees with every reverse item.
        # Post-flip all 1s = 12.  Absolute-minimum-fear pattern.
        result = score_fneb([1, 5, 1, 5, 1, 1, 5, 1, 1, 5, 1, 1])
        assert result.total == 12


# ---------------------------------------------------------------------------
# Severity — always continuous
# ---------------------------------------------------------------------------


class TestSeverity:
    """Pin the severity="continuous" invariant at every total."""

    def test_minimum_total_is_continuous(self) -> None:
        result = score_fneb([1, 5, 1, 5, 1, 1, 5, 1, 1, 5, 1, 1])
        assert result.total == 12
        assert result.severity == "continuous"

    def test_maximum_total_is_continuous(self) -> None:
        result = score_fneb([5, 1, 5, 1, 5, 5, 1, 5, 5, 1, 5, 5])
        assert result.total == 60
        assert result.severity == "continuous"

    def test_midpoint_total_is_continuous(self) -> None:
        result = score_fneb([3] * 12)
        assert result.total == 36
        assert result.severity == "continuous"

    def test_collins_2005_cutoff_not_banded(self) -> None:
        # Collins 2005 used >= 49 as clinical-range indicator in
        # a social-phobia sample.  Platform intentionally does NOT
        # fire a band at this threshold — secondary-literature
        # cutoff, not derivation-source.
        # Construct total = 49: need post-flip values summing to 49
        # across 12 items.  Example raw [5,2,5,2,4,4,2,4,4,2,4,4]
        # straight sum 5+5+4+4+4+4+4+4 = 34; reverse 2->4, 2->4,
        # 2->4, 2->4 → 16.  34+16 = 50.  Hmm let me try another.
        # Raw [5,2,5,2,4,4,2,4,4,2,4,3]: straight 5,5,4,4,4,4,4,3 = 33;
        # reverse (2,4,7,10): 6-2=4, 6-2=4, 6-2=4, 6-2=4 = 16.
        # Total 49.
        result = score_fneb([5, 2, 5, 2, 4, 4, 2, 4, 4, 2, 4, 3])
        assert result.total == 49
        assert result.severity == "continuous"

    @pytest.mark.parametrize(
        "raw_items",
        [
            [1] * 12,
            [5] * 12,
            [3] * 12,
            [1, 5, 2, 4, 3, 2, 1, 4, 5, 1, 2, 3],
            [5, 1, 5, 1, 5, 5, 1, 5, 5, 1, 5, 5],
        ],
    )
    def test_all_patterns_return_continuous(
        self, raw_items: list[int]
    ) -> None:
        result = score_fneb(raw_items)
        assert result.severity == "continuous"


# ---------------------------------------------------------------------------
# Reverse-keying parametric grid
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "item_position,raw_value,expected_post_flip",
    [
        # Reverse items (2, 4, 7, 10): post-flip = 6 - raw.
        (2, 1, 5),
        (2, 3, 3),
        (2, 5, 1),
        (4, 1, 5),
        (4, 3, 3),
        (4, 5, 1),
        (7, 1, 5),
        (7, 3, 3),
        (7, 5, 1),
        (10, 1, 5),
        (10, 3, 3),
        (10, 5, 1),
        # Non-reverse items (1, 3, 5, 6, 8, 9, 11, 12) pass through.
        (1, 1, 1),
        (1, 5, 5),
        (3, 1, 1),
        (3, 5, 5),
        (5, 1, 1),
        (5, 5, 5),
        (6, 1, 1),
        (6, 5, 5),
        (8, 1, 1),
        (8, 5, 5),
        (9, 1, 1),
        (9, 5, 5),
        (11, 1, 1),
        (11, 5, 5),
        (12, 1, 1),
        (12, 5, 5),
    ],
)
def test_reverse_scoring_direction(
    item_position: int, raw_value: int, expected_post_flip: int
) -> None:
    """Pin reverse-keying for every position / value combination.

    Baseline: all-3s → total 36.  Each position contributes 3 to
    the baseline regardless of reverse/non-reverse (reverse: 6-3=3;
    non-reverse: 3).  Changing one position to ``raw_value`` shifts
    the total by ``expected_post_flip - 3``.
    """
    items = [3] * 12
    items[item_position - 1] = raw_value
    expected_total = 36 - 3 + expected_post_flip

    result = score_fneb(items)
    assert result.total == expected_total


class TestDirectionSemantics:
    """Additional direction pins beyond the parametrized grid."""

    def test_max_agree_straight_increases_fear(self) -> None:
        # Raise item 1 (straight, "I worry about...") from 3 to 5
        # → post-flip 3 to 5 → total +2.
        base = score_fneb([3] * 12).total
        raised = score_fneb([5, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3]).total
        assert raised == base + 2

    def test_max_agree_reverse_decreases_fear(self) -> None:
        # Raise item 2 (reverse, "I am unconcerned...") from 3 to 5
        # → post-flip 3 to 1 → total -2.
        base = score_fneb([3] * 12).total
        raised = score_fneb([3, 5, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3]).total
        assert raised == base - 2

    def test_higher_is_more_fearful(self) -> None:
        # Global invariant: every single-position shift toward the
        # fearful extreme raises the total.
        fearful = score_fneb([5, 1, 5, 1, 5, 5, 1, 5, 5, 1, 5, 5]).total
        not_fearful = score_fneb(
            [1, 5, 1, 5, 1, 1, 5, 1, 1, 5, 1, 1]
        ).total
        assert fearful > not_fearful
        assert fearful == 60
        assert not_fearful == 12


# ---------------------------------------------------------------------------
# Acquiescence-bias signature — asymmetric 8/4 split
# ---------------------------------------------------------------------------


class TestAcquiescenceSignature:
    """FNE-B's 8-straight / 4-reverse asymmetric split gives a
    Leary 1983 wire-level signature DIFFERENT from STAI-6's
    symmetric 3/3 (midpoint 15 for every constant) and RSES's
    symmetric 5/5 (midpoint 15 for every constant).

    Constant-response totals:
    - all-1s = 28 (8×1 straight + 4×5 reverse)
    - all-2s = 32 (8×2 + 4×4)
    - all-3s = 36 (8×3 + 4×3)
    - all-4s = 40 (8×4 + 4×2)
    - all-5s = 44 (8×5 + 4×1)

    Linear progression with +4 per unit increase.  Differ-by-16
    between extremes is the Leary 1983 signature.
    """

    def test_all_ones_total_twenty_eight(self) -> None:
        assert score_fneb([1] * 12).total == 28

    def test_all_fives_total_forty_four(self) -> None:
        assert score_fneb([5] * 12).total == 44

    def test_extremes_differ_by_sixteen(self) -> None:
        # The signature: 8/4 asymmetric split → extremes separated
        # by 16 on a 12-60 scale.  Symmetric splits → separation 0.
        diff = score_fneb([5] * 12).total - score_fneb([1] * 12).total
        assert diff == 16

    def test_constant_progression_linear_by_four(self) -> None:
        # Uniform increments: each +1 in constant value shifts
        # total by +4 (4 items with asymmetry net = 8 - 4 = 4).
        assert score_fneb([2] * 12).total - score_fneb([1] * 12).total == 4
        assert score_fneb([3] * 12).total - score_fneb([2] * 12).total == 4
        assert score_fneb([4] * 12).total - score_fneb([3] * 12).total == 4
        assert score_fneb([5] * 12).total - score_fneb([4] * 12).total == 4

    @pytest.mark.parametrize(
        "uniform_value,expected_total",
        [(1, 28), (2, 32), (3, 36), (4, 40), (5, 44)],
    )
    def test_constant_vector_formula(
        self, uniform_value: int, expected_total: int
    ) -> None:
        # Formula: total = 8 × v + 4 × (6 - v) = 4v + 24.
        items = [uniform_value] * ITEM_COUNT
        result = score_fneb(items)
        assert result.total == expected_total
        # Validate the formula holds: 4v + 24.
        assert result.total == 4 * uniform_value + 24


# ---------------------------------------------------------------------------
# Audit invariance — items preserves RAW pre-flip
# ---------------------------------------------------------------------------


class TestAuditInvariance:
    """Pin that FnebResult.items contains the RAW pre-flip responses
    exactly as submitted, in Leary 1983 administration order."""

    def test_items_are_raw_pre_flip_at_minimum(self) -> None:
        raw = [1, 5, 1, 5, 1, 1, 5, 1, 1, 5, 1, 1]
        result = score_fneb(raw)
        assert result.items == tuple(raw)
        assert result.total == 12

    def test_items_are_raw_pre_flip_at_maximum(self) -> None:
        raw = [5, 1, 5, 1, 5, 5, 1, 5, 5, 1, 5, 5]
        result = score_fneb(raw)
        assert result.items == tuple(raw)
        assert result.total == 60

    def test_items_are_raw_not_flipped(self) -> None:
        raw = [2, 4, 1, 3, 5, 2, 1, 4, 3, 5, 2, 1]
        result = score_fneb(raw)
        assert result.items == tuple(raw)
        # Post-flip: positions 2,4,7,10 flip.
        # Straight: 2, 1, 5, 2, 4, 3, 2, 1 = 20
        # Reverse: 6-4=2, 6-3=3, 6-1=5, 6-5=1 = 11
        # Total: 31.
        assert result.total == 31

    def test_items_tuple_is_hashable(self) -> None:
        result = score_fneb([3] * 12)
        hash(result)  # must not raise

    def test_items_length_matches_item_count(self) -> None:
        result = score_fneb([3] * 12)
        assert len(result.items) == ITEM_COUNT

    def test_instrument_version_on_result(self) -> None:
        result = score_fneb([3] * 12)
        assert result.instrument_version == INSTRUMENT_VERSION
        assert result.instrument_version == "fneb-1.0.0"


# ---------------------------------------------------------------------------
# Clinical vignettes
# ---------------------------------------------------------------------------


class TestClinicalVignettes:
    """Patient-like response patterns per Leary 1983 and Collins
    2005 validation samples."""

    def test_social_phobia_clinical_range(self) -> None:
        # Collins 2005 clinical-sample pattern: mostly "extremely
        # characteristic" on straight items, mostly "not at all
        # characteristic" on reverse items.
        # Raw [5, 1, 5, 1, 5, 5, 1, 5, 5, 1, 5, 4]:
        # Straight (1,3,5,6,8,9,11,12): 5,5,5,5,5,5,5,4 = 39
        # Reverse (2,4,7,10): 6-1=5, 6-1=5, 6-1=5, 6-1=5 = 20
        # Total 59.
        result = score_fneb([5, 1, 5, 1, 5, 5, 1, 5, 5, 1, 5, 4])
        assert result.total == 59
        assert result.severity == "continuous"

    def test_student_sample_mean_leary_1983(self) -> None:
        # Leary 1983 Table 2: student-sample mean ~= 35.  Construct
        # a pattern yielding exactly 35: moderate agreement with
        # straight items (3), mild agreement with reverse items (4).
        # Raw [3, 4, 3, 4, 3, 3, 4, 3, 3, 4, 3, 3]:
        # Straight: 3×8 = 24
        # Reverse: (6-4)×4 = 8
        # Total 32.  Not 35 exactly; use different pattern.
        # Raw [4, 3, 3, 3, 3, 4, 3, 3, 4, 3, 4, 4]:
        # Straight (1,3,5,6,8,9,11,12): 4,3,3,4,3,3,4,4 = 28
        # Reverse (2,4,7,10): 6-3=3, 6-3=3, 6-3=3, 6-3=3 = 12
        # Total 40.  Hmm.  Aim for exactly 35:
        # Straight sum + reverse sum = 35.  Straight 8 items
        # summing to 23, reverse 4 flips summing to 12 works:
        # raw reverse all-3 (post-flip 3) × 4 = 12.  Straight items
        # summing to 23: e.g., [3, _, 3, _, 3, 3, _, 3, 2, _, 3, 3]
        # straight = 3+3+3+3+3+2+3+3 = 23.  Let me check:
        # Raw [3, 3, 3, 3, 3, 3, 3, 3, 2, 3, 3, 3]:
        # Straight (positions 1,3,5,6,8,9,11,12): 3+3+3+3+3+2+3+3 = 23
        # Reverse (positions 2,4,7,10): all raw 3 → post-flip 3 each
        # = 12.  Total 35.
        result = score_fneb([3, 3, 3, 3, 3, 3, 3, 3, 2, 3, 3, 3])
        assert result.total == 35
        assert result.severity == "continuous"

    def test_community_non_clinical_low(self) -> None:
        # Non-clinical respondent with low social-evaluation anxiety:
        # mild disagreement with straight items (2), mild agreement
        # with reverse items (4).
        # Raw [2, 4, 2, 4, 2, 2, 4, 2, 2, 4, 2, 2]:
        # Straight: 2×8 = 16
        # Reverse: (6-4)×4 = 8
        # Total 24.
        result = score_fneb([2, 4, 2, 4, 2, 2, 4, 2, 2, 4, 2, 2])
        assert result.total == 24
        assert result.severity == "continuous"

    def test_alcohol_social_lubrication_profile(self) -> None:
        # Patient drinks to manage social-evaluation anxiety.  Marlatt
        # 1985 Table 4.1 social-pressure relapse category.  High
        # social-evaluation concern: strong agreement with straight
        # items (4), strong disagreement with reverse items (2).
        # Raw [4, 2, 4, 2, 4, 4, 2, 4, 4, 2, 4, 4]:
        # Straight: 4×8 = 32
        # Reverse: (6-2)×4 = 16
        # Total 48.  Just below Collins 2005 >= 49 clinical
        # threshold — a subthreshold-but-clinically-salient profile.
        result = score_fneb([4, 2, 4, 2, 4, 4, 2, 4, 4, 2, 4, 4])
        assert result.total == 48
        assert result.severity == "continuous"

    def test_pre_post_cbgt_session_effect(self) -> None:
        # Heimberg 1995 CBGT: pre/post social-anxiety-session effect.
        # Pre-session elevated FNE-B, post-session reduced FNE-B.
        pre = score_fneb([5, 1, 5, 1, 5, 5, 1, 5, 5, 1, 5, 5])
        post = score_fneb([3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3])
        assert pre.total == 60
        assert post.total == 36
        # Delta 24 is a large within-session effect — well above
        # Jacobson-Truax RCI threshold at the trajectory layer.
        assert pre.total - post.total == 24


# ---------------------------------------------------------------------------
# Item-count validation
# ---------------------------------------------------------------------------


class TestItemCountValidation:
    """Reject inputs whose length is not exactly 12."""

    def test_empty_list_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 12"):
            score_fneb([])

    def test_eleven_items_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 12"):
            score_fneb([3] * 11)

    def test_thirteen_items_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 12"):
            score_fneb([3] * 13)

    def test_eight_items_rejected(self) -> None:
        # Length-trap — FNE-B is 12 items, NOT the BFNE-II 8-item
        # revision (Carleton 2007 dropped the 4 reverse items).
        with pytest.raises(InvalidResponseError, match="exactly 12"):
            score_fneb([3] * 8)

    def test_thirty_items_rejected(self) -> None:
        # Length-trap — rejects the Watson & Friend 1969 30-item
        # original FNE being submitted by mistake.
        with pytest.raises(InvalidResponseError, match="exactly 12"):
            score_fneb([1] * 30)


# ---------------------------------------------------------------------------
# Item-value validation
# ---------------------------------------------------------------------------


class TestItemValueValidation:
    """Reject values outside 1-5 or non-int."""

    def test_zero_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="1-5"):
            score_fneb([0] + [3] * 11)

    def test_six_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="1-5"):
            score_fneb([6] + [3] * 11)

    def test_negative_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="1-5"):
            score_fneb([-1] + [3] * 11)

    def test_large_integer_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="1-5"):
            score_fneb([99] + [3] * 11)

    def test_out_of_range_at_end_position_reported(self) -> None:
        with pytest.raises(InvalidResponseError, match="item 12"):
            score_fneb([3] * 11 + [0])

    def test_out_of_range_at_middle_position_reported(self) -> None:
        with pytest.raises(InvalidResponseError, match="item 7"):
            score_fneb([3, 3, 3, 3, 3, 3, 99, 3, 3, 3, 3, 3])


# ---------------------------------------------------------------------------
# Item-type validation
# ---------------------------------------------------------------------------


class TestItemTypeValidation:
    """Reject non-int item values including bool.

    CLAUDE.md standing rule: bool must be rejected EXPLICITLY before
    the int check — Python's ``bool is int`` subclassing would
    silently coerce ``True`` / ``False`` to 1 / 0 otherwise.
    """

    def test_true_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_fneb([True] + [3] * 11)

    def test_false_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_fneb([False] + [3] * 11)

    def test_float_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_fneb([3.0] + [3] * 11)

    def test_float_in_range_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_fneb([3.5] + [3] * 11)

    def test_string_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_fneb(["3"] + [3] * 11)  # type: ignore[list-item]

    def test_none_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_fneb([None] + [3] * 11)  # type: ignore[list-item]

    def test_bool_reported_at_correct_position(self) -> None:
        with pytest.raises(InvalidResponseError, match="item 7"):
            items: list = [3] * 12
            items[6] = True
            score_fneb(items)


# ---------------------------------------------------------------------------
# Result-shape invariants
# ---------------------------------------------------------------------------


class TestResultShapeInvariants:
    """Pin the FnebResult dataclass contract."""

    def test_result_is_frozen(self) -> None:
        result = score_fneb([3] * 12)
        with pytest.raises((AttributeError, TypeError)):
            result.total = 99  # type: ignore[misc]

    def test_result_has_no_subscales_field(self) -> None:
        result = score_fneb([3] * 12)
        assert not hasattr(result, "subscales")

    def test_result_has_no_requires_t3_field(self) -> None:
        result = score_fneb([3] * 12)
        assert not hasattr(result, "requires_t3")

    def test_result_has_no_positive_screen_field(self) -> None:
        result = score_fneb([3] * 12)
        assert not hasattr(result, "positive_screen")

    def test_result_total_type_is_int(self) -> None:
        result = score_fneb([3] * 12)
        assert isinstance(result.total, int)
        assert not isinstance(result.total, bool)

    def test_result_severity_type_is_str(self) -> None:
        result = score_fneb([3] * 12)
        assert isinstance(result.severity, str)
        assert result.severity == "continuous"

    def test_result_items_type_is_tuple(self) -> None:
        result = score_fneb([3] * 12)
        assert isinstance(result.items, tuple)


# ---------------------------------------------------------------------------
# Range bounds
# ---------------------------------------------------------------------------


class TestRangeBounds:
    """Every computable total must be in [12, 60]."""

    def test_minimum_possible_total_is_twelve(self) -> None:
        result = score_fneb([1, 5, 1, 5, 1, 1, 5, 1, 1, 5, 1, 1])
        assert result.total == 12

    def test_maximum_possible_total_is_sixty(self) -> None:
        result = score_fneb([5, 1, 5, 1, 5, 5, 1, 5, 5, 1, 5, 5])
        assert result.total == 60

    @pytest.mark.parametrize(
        "raw_items",
        [
            [1] * 12,
            [2] * 12,
            [3] * 12,
            [4] * 12,
            [5] * 12,
            [1, 5, 1, 5, 1, 1, 5, 1, 1, 5, 1, 1],
            [5, 1, 5, 1, 5, 5, 1, 5, 5, 1, 5, 5],
            [3, 2, 4, 3, 1, 5, 2, 4, 3, 1, 5, 2],
        ],
    )
    def test_every_valid_input_in_range(
        self, raw_items: list[int]
    ) -> None:
        result = score_fneb(raw_items)
        assert 12 <= result.total <= 60


# ---------------------------------------------------------------------------
# Wire-compatibility
# ---------------------------------------------------------------------------


class TestInputTypeCompatibility:
    """Sequence[int] — list, tuple."""

    def test_list_input(self) -> None:
        assert score_fneb([3] * 12).total == 36

    def test_tuple_input(self) -> None:
        assert score_fneb((3,) * 12).total == 36

    def test_list_and_tuple_produce_same_result(self) -> None:
        as_list = score_fneb([1, 2, 3, 4, 5, 1, 2, 3, 4, 5, 1, 2])
        as_tuple = score_fneb((1, 2, 3, 4, 5, 1, 2, 3, 4, 5, 1, 2))
        assert as_list.total == as_tuple.total
        assert as_list.items == as_tuple.items

"""Tests for STAI-6 scorer — Marteau & Bekker 1992 brief state anxiety.

Direction: HIGHER SUM = MORE STATE-ANXIOUS.  Uniform with PHQ-9 /
GAD-7 / AUDIT / PSS-10 / PGSI / SHAPS (lower-is-better).  OPPOSITE of
WHO-5 / BRS / RSES / FFMQ-15 / MAAS / LOT-R (higher-is-better).

Reverse-keying: items 1, 4, 5 are the three positively-worded state
items ("calm", "relaxed", "content") and are flipped at scoring time
via ``(ITEM_MIN + ITEM_MAX) - raw = 5 - raw``.  Items 2, 3, 6 are
negatively worded ("tense", "upset", "worried") and pass through raw.
The ``items`` field of the result preserves the RAW PRE-FLIP responses
for audit invariance — shared contract with BRS / RSES / TAS-20 /
PANAS-10 / FFMQ-15 / PGSI.

No severity bands (``severity="continuous"``) — Marteau 1992 did NOT
publish clinical cutpoints; the ≥ 40 scaled cutoff in Kvaal 2005 is
secondary-literature derivation.  Per CLAUDE.md "no hand-rolled
severity thresholds" rule, clinical-significance determination is
deferred to the trajectory layer via Jacobson-Truax RCI on the raw
total.  Same contract as OASIS / K10 / RSES / PANAS-10 / FFMQ-15.

Acquiescence-bias control (Marsh 1996): with 3 positive and 3 negative
items on a 1-4 scale, every CONSTANT-response vector lands on the
midpoint total of 15.  This is a stronger-than-FFMQ-15 property
(FFMQ-15's 8/7 asymmetric split only gives differ-by-4 between all-1s
and all-5s).  Pinned explicitly in multiple tests: a contributor who
silently changes ``STAI6_REVERSE_ITEMS`` to an asymmetric tuple will
break this invariant and the clinical equivalence to Marteau 1992.
"""

from __future__ import annotations

import pytest

from discipline.psychometric.scoring import stai6
from discipline.psychometric.scoring.stai6 import (
    INSTRUMENT_VERSION,
    ITEM_COUNT,
    ITEM_MAX,
    ITEM_MIN,
    STAI6_REVERSE_ITEMS,
    InvalidResponseError,
    score_stai6,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


class TestConstants:
    """Pin the published structure of the STAI-6 instrument.

    Any change here is a clinical decision (Marteau & Bekker 1992
    derivation) — not an implementation tweak.  Changing the reverse-
    items tuple invalidates the r = 0.94 equivalence to the full
    STAI-S established in n = 200 pre-surgical patients.
    """

    def test_instrument_version(self) -> None:
        assert INSTRUMENT_VERSION == "stai6-1.0.0"

    def test_item_count_is_six(self) -> None:
        assert ITEM_COUNT == 6

    def test_item_min_is_one(self) -> None:
        # Marteau 1992 anchor: 1 = "not at all".
        assert ITEM_MIN == 1

    def test_item_max_is_four(self) -> None:
        # Marteau 1992 anchor: 4 = "very much so".  4-point Likert,
        # NOT the 5-point scale of FFMQ-15 / BRS / RSES / PANAS-10.
        assert ITEM_MAX == 4

    def test_reverse_items_are_one_four_five(self) -> None:
        # Marteau & Bekker 1992 Table 1: positions 1 ("calm"), 4
        # ("relaxed"), 5 ("content") are positively worded.  Changing
        # this tuple invalidates the r = 0.94 equivalence to the
        # full STAI-S and is a clinical-QA-gated change.
        assert STAI6_REVERSE_ITEMS == (1, 4, 5)

    def test_reverse_items_are_three_items(self) -> None:
        # The 3-positive / 3-negative split is the acquiescence-bias
        # control (Marsh 1996).  Asymmetric splits (like FFMQ-15's
        # 8/7) lose this property.
        assert len(STAI6_REVERSE_ITEMS) == 3

    def test_reverse_items_are_in_valid_range(self) -> None:
        # Defensive pin: every reverse index is 1-6 (1-indexed).
        for position in STAI6_REVERSE_ITEMS:
            assert 1 <= position <= ITEM_COUNT

    def test_no_severity_thresholds_exported(self) -> None:
        # STAI-6 is intentionally banded="continuous".  Marteau 1992
        # did not publish cutpoints; a STAI6_SEVERITY_THRESHOLDS
        # tuple would violate CLAUDE.md "no hand-rolled severity
        # thresholds" rule.
        assert not hasattr(stai6, "STAI6_SEVERITY_THRESHOLDS")

    def test_no_positive_cutoff_exported(self) -> None:
        # STAI-6 is not a screen.  A STAI6_POSITIVE_CUTOFF constant
        # would be a category error.
        assert not hasattr(stai6, "STAI6_POSITIVE_CUTOFF")

    def test_no_subscales_exported(self) -> None:
        # STAI-6 is a single-factor instrument derived from the
        # STAI-S single-factor (Spielberger 1983).  Surfacing
        # subscales would contradict the derivation.
        assert not hasattr(stai6, "STAI6_SUBSCALES")

    def test_no_scaled_score_constant(self) -> None:
        # Marteau 1992's (total × 20) / 6 scaling is non-integer
        # for most inputs and adds no clinical information over the
        # raw total at the trajectory layer.  A STAI6_SCALE_FACTOR
        # constant would be a platform deviation.
        assert not hasattr(stai6, "STAI6_SCALE_FACTOR")

    def test_public_exports(self) -> None:
        # Lock the public surface so a contributor cannot silently
        # widen the API.
        assert set(stai6.__all__) == {
            "INSTRUMENT_VERSION",
            "ITEM_COUNT",
            "ITEM_MAX",
            "ITEM_MIN",
            "InvalidResponseError",
            "STAI6_REVERSE_ITEMS",
            "Severity",
            "Stai6Result",
            "score_stai6",
        }


# ---------------------------------------------------------------------------
# Total correctness — post-flip arithmetic
# ---------------------------------------------------------------------------


class TestTotalCorrectness:
    """Verify post-flip summation produces the canonical Marteau 1992
    total in the published 6-24 range."""

    def test_all_ones_total_is_fifteen(self) -> None:
        # Raw all-1s: reverse items 1,4,5 flip 1->4 (contributes
        # 4+4+4=12), non-reverse 2,3,6 pass through (1+1+1=3).
        # Total = 12 + 3 = 15.  Acquiescence-bias anchor: both
        # uniform-response extremes land at the midpoint.
        result = score_stai6([1, 1, 1, 1, 1, 1])
        assert result.total == 15

    def test_all_fours_total_is_fifteen(self) -> None:
        # Raw all-4s: reverse items 1,4,5 flip 4->1 (1+1+1=3),
        # non-reverse 2,3,6 pass through (4+4+4=12).
        # Total = 3 + 12 = 15.  SAME as all-1s — Marsh 1996
        # acquiescence-control property in action.
        result = score_stai6([4, 4, 4, 4, 4, 4])
        assert result.total == 15

    def test_all_twos_total_is_fifteen(self) -> None:
        # Raw all-2s: post-flip [3,2,2,3,3,2] = 15.
        result = score_stai6([2, 2, 2, 2, 2, 2])
        assert result.total == 15

    def test_all_threes_total_is_fifteen(self) -> None:
        # Raw all-3s: post-flip [2,3,3,2,2,3] = 15.
        # Every CONSTANT vector on a 1-4 scale with 3/3 reverse
        # split maps to the midpoint.  This is THE acquiescence-
        # bias control property.
        result = score_stai6([3, 3, 3, 3, 3, 3])
        assert result.total == 15

    def test_maximally_anxious_is_twenty_four(self) -> None:
        # Raw [1,4,4,1,1,4] — disagrees maximally with every
        # positive item (calm=1, relaxed=1, content=1) and agrees
        # maximally with every negative item (tense=4, upset=4,
        # worried=4).  Post-flip: [4,4,4,4,4,4] = 24.
        # The absolute-maximum-anxiety pattern.
        result = score_stai6([1, 4, 4, 1, 1, 4])
        assert result.total == 24

    def test_minimally_anxious_is_six(self) -> None:
        # Raw [4,1,1,4,4,1] — agrees maximally with every positive
        # item and disagrees with every negative item.  Post-flip:
        # [1,1,1,1,1,1] = 6.  The absolute-minimum-anxiety pattern.
        # Exact diagonal mirror of the max-anxiety pattern across
        # the reverse-keying boundary.
        result = score_stai6([4, 1, 1, 4, 4, 1])
        assert result.total == 6

    def test_asymmetric_response_no_double_counting(self) -> None:
        # Raw [3,2,2,3,3,2] — consistent "somewhat non-anxious"
        # pattern: slight agreement with positives (3), slight
        # disagreement with negatives (2).
        # Post-flip: [5-3=2, 2, 2, 5-3=2, 5-3=2, 2] = 12.
        result = score_stai6([3, 2, 2, 3, 3, 2])
        assert result.total == 12


# ---------------------------------------------------------------------------
# Severity — always continuous
# ---------------------------------------------------------------------------


class TestSeverity:
    """Pin the severity="continuous" invariant at every total.

    Marteau 1992 did not publish cutpoints; this platform emits
    continuous and defers clinical-significance to RCI at the
    trajectory layer.
    """

    def test_minimum_total_is_continuous(self) -> None:
        result = score_stai6([4, 1, 1, 4, 4, 1])
        assert result.total == 6
        assert result.severity == "continuous"

    def test_midpoint_total_is_continuous(self) -> None:
        result = score_stai6([3, 3, 3, 3, 3, 3])
        assert result.total == 15
        assert result.severity == "continuous"

    def test_maximum_total_is_continuous(self) -> None:
        result = score_stai6([1, 4, 4, 1, 1, 4])
        assert result.total == 24
        assert result.severity == "continuous"

    def test_kvaal_2005_threshold_not_banded(self) -> None:
        # Marteau 1992 scaled score would be (total × 20) / 6.
        # The widely-cited Kvaal 2005 cutoff is ≥ 40 scaled =
        # clinical anxiety, which back-maps to raw 12 on the 6-24
        # range.  Platform intentionally does NOT fire a band at
        # this threshold.
        result = score_stai6([2, 3, 3, 2, 2, 3])  # raw scores [3,3,3,3,3,3] but not...
        # Actually construct: post-flip [3,3,3,3,3,3] via raw [2,3,3,2,2,3]
        # gives total 18, severity still continuous.
        assert result.total == 18
        assert result.severity == "continuous"

    @pytest.mark.parametrize(
        "raw_items",
        [
            [1, 1, 1, 1, 1, 1],
            [4, 4, 4, 4, 4, 4],
            [2, 3, 2, 3, 2, 3],
            [3, 2, 3, 2, 3, 2],
            [1, 4, 1, 4, 1, 4],
            [4, 1, 4, 1, 4, 1],
        ],
    )
    def test_all_patterns_return_continuous(
        self, raw_items: list[int]
    ) -> None:
        # Defensive invariant: NO pattern produces a banded severity.
        result = score_stai6(raw_items)
        assert result.severity == "continuous"


# ---------------------------------------------------------------------------
# Direction semantics — reverse-keying parametric grid
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "item_position,raw_value,expected_post_flip",
    [
        # Reverse items (1, 4, 5): post-flip = 5 - raw.
        (1, 1, 4),
        (1, 2, 3),
        (1, 3, 2),
        (1, 4, 1),
        (4, 1, 4),
        (4, 2, 3),
        (4, 3, 2),
        (4, 4, 1),
        (5, 1, 4),
        (5, 2, 3),
        (5, 3, 2),
        (5, 4, 1),
        # Non-reverse items (2, 3, 6) pass through unchanged.
        (2, 1, 1),
        (2, 2, 2),
        (2, 3, 3),
        (2, 4, 4),
        (3, 1, 1),
        (3, 2, 2),
        (3, 3, 3),
        (3, 4, 4),
        (6, 1, 1),
        (6, 2, 2),
        (6, 3, 3),
        (6, 4, 4),
    ],
)
def test_reverse_scoring_direction(
    item_position: int, raw_value: int, expected_post_flip: int
) -> None:
    """Direct pin of reverse-keying behavior for every position / value.

    Uses the private helper by indirection — construct a 6-item
    response where only the probed position varies from the all-
    neutral-2.5-ish baseline (use all 2s, which gives midpoint 15),
    and verify the total shifts by the expected post-flip delta.

    Baseline: all-2s.  Position contribution at baseline:
    - positions 1,4,5 (reverse): post-flip = 5-2 = 3
    - positions 2,3,6 (non-reverse): post-flip = 2

    Baseline total: 3+2+2+3+3+2 = 15.
    """
    items = [2, 2, 2, 2, 2, 2]
    items[item_position - 1] = raw_value

    baseline_contributions = {1: 3, 2: 2, 3: 2, 4: 3, 5: 3, 6: 2}
    baseline_at_position = baseline_contributions[item_position]
    expected_total = 15 - baseline_at_position + expected_post_flip

    result = score_stai6(items)
    assert result.total == expected_total


class TestDirectionSemantics:
    """Additional direction pins beyond the parametrized grid."""

    def test_max_agree_positive_decreases_anxiety(self) -> None:
        # Raise item 1 (positive, "calm", reverse) from 2 to 4
        # -> post-flip goes from 3 to 1 -> total -2 (LESS anxiety).
        base = score_stai6([2, 2, 2, 2, 2, 2]).total
        less_anxious = score_stai6([4, 2, 2, 2, 2, 2]).total
        assert less_anxious == base - 2

    def test_max_agree_negative_increases_anxiety(self) -> None:
        # Raise item 2 (negative, "tense", non-reverse) from 2 to 4
        # -> post-flip goes from 2 to 4 -> total +2 (MORE anxiety).
        base = score_stai6([2, 2, 2, 2, 2, 2]).total
        more_anxious = score_stai6([2, 4, 2, 2, 2, 2]).total
        assert more_anxious == base + 2

    def test_higher_is_more_anxious(self) -> None:
        # Global invariant: every single-position shift toward the
        # anxious extreme raises the total.
        anxious = score_stai6([1, 4, 4, 1, 1, 4]).total
        calm = score_stai6([4, 1, 1, 4, 4, 1]).total
        assert anxious > calm
        assert anxious == 24
        assert calm == 6


# ---------------------------------------------------------------------------
# Audit invariance — items preserves RAW pre-flip
# ---------------------------------------------------------------------------


class TestAuditInvariance:
    """Pin that Stai6Result.items contains the RAW pre-flip responses
    exactly as submitted, in Marteau 1992 administration order.

    This is the audit-trail invariant shared with BRS / RSES / TAS-20 /
    PANAS-10 / FFMQ-15 / PGSI — post-flip values are for scoring;
    raw is for FHIR R4 export and clinical review.
    """

    def test_items_are_raw_pre_flip_at_minimum(self) -> None:
        raw = [4, 1, 1, 4, 4, 1]
        result = score_stai6(raw)
        assert result.items == tuple(raw)
        assert result.total == 6

    def test_items_are_raw_pre_flip_at_maximum(self) -> None:
        raw = [1, 4, 4, 1, 1, 4]
        result = score_stai6(raw)
        assert result.items == tuple(raw)
        assert result.total == 24

    def test_items_are_raw_not_flipped(self) -> None:
        # Raw input with reverse-keyed positions deliberately
        # different from non-reverse positions to distinguish raw
        # from post-flip.
        raw = [1, 2, 3, 4, 1, 2]
        result = score_stai6(raw)
        # If items stored post-flip we'd see [4,2,3,1,4,2].  They
        # don't — raw is preserved.
        assert result.items == (1, 2, 3, 4, 1, 2)
        # And scoring uses post-flip: [4,2,3,1,4,2] = 16.
        assert result.total == 16

    def test_items_tuple_is_hashable(self) -> None:
        # Frozen dataclass + tuple items → Stai6Result is hashable
        # (invariant for caching and set-membership checks).
        result = score_stai6([2, 2, 2, 2, 2, 2])
        hash(result)  # must not raise

    def test_items_length_matches_item_count(self) -> None:
        result = score_stai6([2, 2, 2, 2, 2, 2])
        assert len(result.items) == ITEM_COUNT

    def test_instrument_version_on_result(self) -> None:
        result = score_stai6([2, 2, 2, 2, 2, 2])
        assert result.instrument_version == INSTRUMENT_VERSION
        assert result.instrument_version == "stai6-1.0.0"


# ---------------------------------------------------------------------------
# Acquiescence-bias control (Marsh 1996)
# ---------------------------------------------------------------------------


class TestAcquiescenceBiasControl:
    """STAI-6's 3-positive / 3-negative symmetric reverse-keying is
    Marsh 1996's canonical acquiescence-bias control design.  Every
    CONSTANT vector on a 1-4 scale produces the midpoint total (15).
    This property is stronger than FFMQ-15's 8/7 asymmetric split
    (differ-by-4 between uniform-1s and uniform-5s).

    Pinning this property explicitly means a contributor who tweaks
    ``STAI6_REVERSE_ITEMS`` to an asymmetric tuple breaks the
    equivalence to Marteau 1992 and these tests fire.
    """

    @pytest.mark.parametrize("uniform_value", [1, 2, 3, 4])
    def test_constant_vector_gives_midpoint(
        self, uniform_value: int
    ) -> None:
        items = [uniform_value] * ITEM_COUNT
        result = score_stai6(items)
        assert result.total == 15, (
            f"Constant {uniform_value}s broke acquiescence control: "
            f"got {result.total}, expected 15"
        )

    def test_all_ones_equals_all_fours(self) -> None:
        # Direct invariance pin.
        assert score_stai6([1] * 6).total == score_stai6([4] * 6).total

    def test_all_twos_equals_all_threes(self) -> None:
        # Interior uniform pin.
        assert score_stai6([2] * 6).total == score_stai6([3] * 6).total

    def test_uniform_extremes_differ_by_zero(self) -> None:
        # Marsh 1996 symmetric-split property: extremes differ by 0
        # (NOT differ-by-4 as in FFMQ-15's asymmetric split).
        diff = abs(score_stai6([1] * 6).total - score_stai6([4] * 6).total)
        assert diff == 0


# ---------------------------------------------------------------------------
# Clinical vignettes
# ---------------------------------------------------------------------------


class TestClinicalVignettes:
    """Patient-like response patterns per Marteau 1992 and cited
    validation studies.  These tests are clinical-defensibility
    anchors — if any computation here breaks, a human-interpretable
    clinical scenario has silently changed.
    """

    def test_pre_surgical_high_state_anxiety(self) -> None:
        # Marteau 1992 derivation sample (n = 200 pre-surgical
        # patients): heightened state-anxiety profile.  Patient
        # reports moderate-high anxiety across items: not calm (1),
        # quite tense (3), upset (3), not relaxed (1), not content
        # (2), very worried (4).
        # Post-flip: [4, 3, 3, 4, 3, 4] = 21.
        result = score_stai6([1, 3, 3, 1, 2, 4])
        assert result.total == 21
        assert result.severity == "continuous"

    def test_post_session_anxiety_reduction(self) -> None:
        # Pre-session (elevated state):
        pre = score_stai6([1, 4, 3, 1, 2, 4])  # post-flip [4,4,3,4,3,4] = 22
        # Post-session (reduced state after behavioral activation):
        post = score_stai6([3, 2, 2, 3, 3, 2])  # post-flip [2,2,2,2,2,2] = 12
        assert pre.total == 22
        assert post.total == 12
        # Delta is the within-session-effect metric that drives
        # the Discipline OS intervention-efficacy measurement.
        assert pre.total - post.total == 10

    def test_community_non_clinical_low_anxiety(self) -> None:
        # Tluczek 2009 general-population sample: low state-anxiety
        # profile.  Patient reports: quite calm (3), not tense (2),
        # not upset (1), relaxed (3), content (3), slightly worried
        # (2).
        # Post-flip: [2, 2, 1, 2, 2, 2] = 11.
        result = score_stai6([3, 2, 1, 3, 3, 2])
        assert result.total == 11
        assert result.severity == "continuous"

    def test_trigger_reactivity_spike(self) -> None:
        # Marlatt 1985 cue-reactivity scenario.  Baseline low-anxiety
        # measurement, then immediately post-trigger (location / cue
        # exposure) the state-anxiety spikes.
        baseline = score_stai6([4, 1, 1, 4, 3, 2])  # post-flip [1,1,1,1,2,2]=8
        post_trigger = score_stai6([1, 3, 2, 2, 2, 3])  # [4,3,2,3,3,3]=18
        assert baseline.total == 8
        assert post_trigger.total == 18
        # Spike of 10+ points within a brief window is the
        # bandit-policy predictive signal.
        assert post_trigger.total - baseline.total >= 10

    def test_oncology_validation_sample(self) -> None:
        # Balsamo 2014 oncology-patient profile: elevated anxiety
        # across the scale.  Raw [2, 3, 3, 2, 2, 3].
        # Post-flip: [3, 3, 3, 3, 3, 3] = 18.
        result = score_stai6([2, 3, 3, 2, 2, 3])
        assert result.total == 18
        assert result.severity == "continuous"

    def test_obstetric_validation_sample(self) -> None:
        # Cowdery 2000 obstetric-patient profile: moderate state
        # anxiety (third-trimester measurement).  Raw
        # [2, 2, 2, 2, 3, 3].
        # Post-flip: [3, 2, 2, 3, 2, 3] = 15.
        result = score_stai6([2, 2, 2, 2, 3, 3])
        assert result.total == 15
        assert result.severity == "continuous"


# ---------------------------------------------------------------------------
# Item-count validation
# ---------------------------------------------------------------------------


class TestItemCountValidation:
    """Reject inputs whose length is not exactly 6."""

    def test_empty_list_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 6"):
            score_stai6([])

    def test_five_items_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 6"):
            score_stai6([2, 2, 2, 2, 2])

    def test_seven_items_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 6"):
            score_stai6([2, 2, 2, 2, 2, 2, 2])

    def test_ten_items_rejected(self) -> None:
        # Length-trap — STAI-6 is 6 items, NOT the 10-item STAI-S
        # abbreviation sometimes cited.
        with pytest.raises(InvalidResponseError, match="exactly 6"):
            score_stai6([2] * 10)

    def test_twenty_items_rejected(self) -> None:
        # Length-trap — rejects the full 20-item STAI-S being
        # submitted by mistake.
        with pytest.raises(InvalidResponseError, match="exactly 6"):
            score_stai6([2] * 20)


# ---------------------------------------------------------------------------
# Item-value validation
# ---------------------------------------------------------------------------


class TestItemValueValidation:
    """Reject values outside 1-4 or non-int."""

    def test_zero_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="1-4"):
            score_stai6([0, 2, 2, 2, 2, 2])

    def test_five_rejected(self) -> None:
        # 5 would be a valid BRS / RSES / FFMQ-15 / PANAS-10 input
        # but is OUT OF RANGE for STAI-6's 1-4 Likert.
        with pytest.raises(InvalidResponseError, match="1-4"):
            score_stai6([5, 2, 2, 2, 2, 2])

    def test_negative_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="1-4"):
            score_stai6([-1, 2, 2, 2, 2, 2])

    def test_large_integer_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="1-4"):
            score_stai6([99, 2, 2, 2, 2, 2])

    def test_out_of_range_at_end_position_reported(self) -> None:
        with pytest.raises(InvalidResponseError, match="item 6"):
            score_stai6([2, 2, 2, 2, 2, 0])

    def test_out_of_range_at_middle_position_reported(self) -> None:
        with pytest.raises(InvalidResponseError, match="item 3"):
            score_stai6([2, 2, 99, 2, 2, 2])


# ---------------------------------------------------------------------------
# Item-type validation (bool rejection, non-int rejection)
# ---------------------------------------------------------------------------


class TestItemTypeValidation:
    """Reject non-int item values, including bool.

    CLAUDE.md standing rule: bool must be rejected EXPLICITLY before
    the int check — Python's ``bool is int`` subclassing would
    silently coerce ``True`` / ``False`` to 1 / 0.  A True response
    would pass the 1-4 range check (1 is valid) while semantically
    meaning "this patient answered this item with a Python boolean",
    which is a category error at the scorer contract level.
    """

    def test_true_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_stai6([True, 2, 2, 2, 2, 2])

    def test_false_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_stai6([False, 2, 2, 2, 2, 2])

    def test_float_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_stai6([2.0, 2, 2, 2, 2, 2])

    def test_float_in_range_still_rejected(self) -> None:
        # 2.5 is in the 1-4 continuous interval but STAI-6 is Likert
        # (integer-only).  Reject.
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_stai6([2.5, 2, 2, 2, 2, 2])

    def test_string_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_stai6(["2", 2, 2, 2, 2, 2])  # type: ignore[list-item]

    def test_none_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_stai6([None, 2, 2, 2, 2, 2])  # type: ignore[list-item]

    def test_list_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_stai6([[2], 2, 2, 2, 2, 2])  # type: ignore[list-item]

    def test_bool_reported_at_correct_position(self) -> None:
        with pytest.raises(InvalidResponseError, match="item 4"):
            score_stai6([2, 2, 2, True, 2, 2])


# ---------------------------------------------------------------------------
# Result-shape invariants
# ---------------------------------------------------------------------------


class TestResultShapeInvariants:
    """Pin the Stai6Result dataclass contract."""

    def test_result_is_frozen(self) -> None:
        # Frozen dataclass — mutation must raise.
        result = score_stai6([2, 2, 2, 2, 2, 2])
        with pytest.raises((AttributeError, TypeError)):
            result.total = 99  # type: ignore[misc]

    def test_result_has_no_subscales_field(self) -> None:
        # STAI-6 is single-factor by construction.
        result = score_stai6([2, 2, 2, 2, 2, 2])
        assert not hasattr(result, "subscales")

    def test_result_has_no_scaled_score_field(self) -> None:
        # Marteau 1992 scaled score deliberately not emitted.
        result = score_stai6([2, 2, 2, 2, 2, 2])
        assert not hasattr(result, "scaled_score")

    def test_result_has_no_requires_t3_field(self) -> None:
        # STAI-6 has no ideation item.  A requires_t3 field would
        # be misleading.
        result = score_stai6([2, 2, 2, 2, 2, 2])
        assert not hasattr(result, "requires_t3")

    def test_result_has_no_positive_screen_field(self) -> None:
        # STAI-6 is not a screen.
        result = score_stai6([2, 2, 2, 2, 2, 2])
        assert not hasattr(result, "positive_screen")

    def test_result_total_type_is_int(self) -> None:
        result = score_stai6([2, 2, 2, 2, 2, 2])
        assert isinstance(result.total, int)
        # Exact int, not bool (which is an int subclass).
        assert not isinstance(result.total, bool)

    def test_result_severity_type_is_str(self) -> None:
        result = score_stai6([2, 2, 2, 2, 2, 2])
        assert isinstance(result.severity, str)
        assert result.severity == "continuous"

    def test_result_items_type_is_tuple(self) -> None:
        result = score_stai6([2, 2, 2, 2, 2, 2])
        assert isinstance(result.items, tuple)


# ---------------------------------------------------------------------------
# Range bounds — every possible post-flip total is 6-24
# ---------------------------------------------------------------------------


class TestRangeBounds:
    """Sanity-check bounds on computable totals."""

    def test_minimum_possible_total_is_six(self) -> None:
        # Constructively demonstrate lower bound.
        result = score_stai6([4, 1, 1, 4, 4, 1])
        assert result.total == 6

    def test_maximum_possible_total_is_twenty_four(self) -> None:
        # Constructively demonstrate upper bound.
        result = score_stai6([1, 4, 4, 1, 1, 4])
        assert result.total == 24

    @pytest.mark.parametrize(
        "raw_items",
        [
            [1, 1, 1, 1, 1, 1],
            [1, 2, 3, 4, 1, 2],
            [2, 2, 2, 2, 2, 2],
            [3, 3, 3, 3, 3, 3],
            [4, 4, 4, 4, 4, 4],
            [1, 4, 1, 4, 1, 4],
            [4, 1, 4, 1, 4, 1],
            [2, 3, 2, 3, 2, 3],
        ],
    )
    def test_every_valid_input_in_range(
        self, raw_items: list[int]
    ) -> None:
        result = score_stai6(raw_items)
        assert 6 <= result.total <= 24


# ---------------------------------------------------------------------------
# Wire-compatibility with common input shapes
# ---------------------------------------------------------------------------


class TestInputTypeCompatibility:
    """The scorer accepts any ``Sequence[int]`` — list, tuple, generator
    semantics.  Keeps the router contract flexible."""

    def test_list_input(self) -> None:
        result = score_stai6([2, 2, 2, 2, 2, 2])
        assert result.total == 15

    def test_tuple_input(self) -> None:
        result = score_stai6((2, 2, 2, 2, 2, 2))
        assert result.total == 15

    def test_list_and_tuple_produce_same_result(self) -> None:
        as_list = score_stai6([1, 3, 2, 4, 2, 1])
        as_tuple = score_stai6((1, 3, 2, 4, 2, 1))
        assert as_list.total == as_tuple.total
        assert as_list.items == as_tuple.items

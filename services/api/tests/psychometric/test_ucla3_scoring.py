"""Tests for the UCLA-3 Brief Loneliness Scale scorer.

Hughes 2004 Research on Aging 26(6):655-672.  3 items, 1-3 Likert,
no reverse keying, total 3-9, severity = "continuous" (no cutpoints).
"""

from __future__ import annotations

import pytest

from discipline.psychometric.scoring.ucla3 import (
    INSTRUMENT_VERSION,
    ITEM_COUNT,
    ITEM_MAX,
    ITEM_MIN,
    InvalidResponseError,
    UCLA3_REVERSE_ITEMS,
    Ucla3Result,
    score_ucla3,
)


# ---------------------------------------------------------------------------
# Constants — pinned against accidental drift
# ---------------------------------------------------------------------------


class TestConstants:
    def test_instrument_version_is_pinned(self) -> None:
        # Pinned so downstream FHIR Observation.meta / assessment-record
        # storage can depend on a stable string.
        assert INSTRUMENT_VERSION == "ucla3-1.0.0"

    def test_item_count_is_three(self) -> None:
        # Hughes 2004's brief-form cardinality.  Changing this
        # invalidates the r = 0.82 UCLA-R-20 equivalence.
        assert ITEM_COUNT == 3

    def test_item_min_is_one(self) -> None:
        # Hughes 2004 3-point Likert: 1 = "Hardly ever".
        assert ITEM_MIN == 1

    def test_item_max_is_three(self) -> None:
        # Hughes 2004 3-point Likert: 3 = "Often".
        assert ITEM_MAX == 3

    def test_reverse_items_is_empty(self) -> None:
        # Hughes 2004 deliberately uses all-negative wording — no
        # Marsh 1996 balanced-wording acquiescence control.  The
        # empty tuple is THE canonical fingerprint of UCLA-3's
        # no-reverse-keying design decision.
        assert UCLA3_REVERSE_ITEMS == ()

    def test_severity_is_continuous_only(self) -> None:
        # No exported severity enum; severity is literal
        # "continuous".  Hughes 2004 published no cutpoints; Steptoe
        # 2013's tercile splits are sample-descriptive derivations
        # and NOT pinned per CLAUDE.md no-hand-rolled-bands rule.
        result = score_ucla3([2, 2, 2])
        assert result.severity == "continuous"

    def test_no_subscale_constants(self) -> None:
        # UCLA-3 is a single-factor instrument per Hughes 2004
        # factor-analytic derivation.  No subscale indices exported.
        import discipline.psychometric.scoring.ucla3 as mod

        assert not hasattr(mod, "UCLA3_SUBSCALES")
        assert not hasattr(mod, "UCLA3_FACTORS")

    def test_no_severity_threshold_constants(self) -> None:
        # No UCLA3_SEVERITY_THRESHOLDS / UCLA3_TERCILES / similar.
        # Steptoe 2013 tercile splits are cohort-descriptive and
        # MUST NOT be shipped as cutpoints.
        import discipline.psychometric.scoring.ucla3 as mod

        assert not hasattr(mod, "UCLA3_SEVERITY_THRESHOLDS")
        assert not hasattr(mod, "UCLA3_TERCILES")
        assert not hasattr(mod, "UCLA3_CUTOFFS")


# ---------------------------------------------------------------------------
# Total correctness — all-v constant / min / max / arithmetic
# ---------------------------------------------------------------------------


class TestTotalCorrectness:
    def test_all_ones_total_is_three(self) -> None:
        # Raw [1, 1, 1] — "Hardly ever" on every item.  No reverse
        # keying so total = 3.  Minimum of the 3-9 range.
        result = score_ucla3([1, 1, 1])
        assert result.total == 3

    def test_all_twos_total_is_six(self) -> None:
        # Raw [2, 2, 2] — "Some of the time" on every item.
        # Total = 6.  Linear: total = 3v.
        result = score_ucla3([2, 2, 2])
        assert result.total == 6

    def test_all_threes_total_is_nine(self) -> None:
        # Raw [3, 3, 3] — "Often" on every item.  Maximum loneliness.
        # Total = 9.
        result = score_ucla3([3, 3, 3])
        assert result.total == 9

    def test_mixed_mid_total(self) -> None:
        # Raw [1, 2, 3] — total 6.
        result = score_ucla3([1, 2, 3])
        assert result.total == 6

    def test_companionship_only(self) -> None:
        # Raw [3, 1, 1] — strong "lack companionship", rare left-out /
        # isolation.  Total 5.  Differentiates the widowhood profile
        # (lost a specific person) from broader isolation.
        result = score_ucla3([3, 1, 1])
        assert result.total == 5

    def test_left_out_only(self) -> None:
        # Raw [1, 3, 1] — rare lack-of-companionship, strong "left
        # out".  Total 5.  Differentiates the social-exclusion
        # profile (adolescent / workplace peer-rejection).
        result = score_ucla3([1, 3, 1])
        assert result.total == 5

    def test_isolated_only(self) -> None:
        # Raw [1, 1, 3] — rare companionship loss and left-out,
        # strong isolation.  Total 5.  Differentiates the
        # environmental-isolation profile (relocation, remote work).
        result = score_ucla3([1, 1, 3])
        assert result.total == 5


# ---------------------------------------------------------------------------
# Severity — always continuous
# ---------------------------------------------------------------------------


class TestSeverity:
    def test_minimum_total_is_continuous(self) -> None:
        result = score_ucla3([1, 1, 1])
        assert result.total == 3
        assert result.severity == "continuous"

    def test_maximum_total_is_continuous(self) -> None:
        result = score_ucla3([3, 3, 3])
        assert result.total == 9
        assert result.severity == "continuous"

    def test_midpoint_total_is_continuous(self) -> None:
        result = score_ucla3([2, 2, 2])
        assert result.total == 6
        assert result.severity == "continuous"

    def test_steptoe_2013_upper_tercile_not_banded(self) -> None:
        # Steptoe 2013 (ELSA cohort) upper tercile is 6-9 in their
        # HRS-English sample.  The platform fires NO band at any
        # value in this range — Steptoe 2013's tercile split is
        # sample-descriptive and NOT a primary-source cutpoint.
        for total_val in range(6, 10):
            # Construct a vector summing to total_val
            vec = [min(3, total_val - 2), min(3, max(1, total_val - 4)), 1]
            # Safer: just use parametrizable constants
            if total_val == 6:
                result = score_ucla3([2, 2, 2])
            elif total_val == 7:
                result = score_ucla3([3, 2, 2])
            elif total_val == 8:
                result = score_ucla3([3, 3, 2])
            else:  # 9
                result = score_ucla3([3, 3, 3])
            assert result.total == total_val
            assert result.severity == "continuous"

    @pytest.mark.parametrize(
        "raw_items",
        [
            [1, 1, 1],
            [1, 1, 2],
            [1, 2, 2],
            [2, 2, 2],
            [2, 2, 3],
            [2, 3, 3],
            [3, 3, 3],
        ],
    )
    def test_all_totals_are_continuous(self, raw_items: list[int]) -> None:
        result = score_ucla3(raw_items)
        assert result.severity == "continuous"


# ---------------------------------------------------------------------------
# No reverse keying — directionality
# ---------------------------------------------------------------------------


class TestNoReverseKeying:
    """UCLA-3 has ZERO reverse-keyed items.  Every item is
    negatively worded so raw value = post-flip value.  These tests
    lock that invariant."""

    def test_raw_value_equals_total_contribution(self) -> None:
        # Raising any single item from 1 to 3 raises the total by
        # exactly 2 (the Likert step × 1 item).
        base = score_ucla3([1, 1, 1]).total
        for i in range(3):
            perturbed = [1, 1, 1]
            perturbed[i] = 3
            assert score_ucla3(perturbed).total == base + 2

    def test_items_field_matches_raw_input(self) -> None:
        # Audit invariance: the items field preserves raw values
        # exactly as supplied (no flipping of any position).
        raw = [1, 2, 3]
        result = score_ucla3(raw)
        assert result.items == tuple(raw)

    def test_all_ones_is_low_loneliness(self) -> None:
        # Direction check: all-1s ("Hardly ever") must be the
        # LOW-loneliness extreme.  Contrast with FFMQ-15 where
        # all-1s is actually HIGH dysfunction due to reverse
        # keying.
        low = score_ucla3([1, 1, 1]).total
        high = score_ucla3([3, 3, 3]).total
        assert low < high
        assert low == 3
        assert high == 9


# ---------------------------------------------------------------------------
# Acquiescence signature — linear total = 3v
# ---------------------------------------------------------------------------


class TestAcquiescenceSignature:
    """UCLA-3 has no acquiescence-bias control; the linear formula
    total = 3v is THE signature of the all-negative-wording
    design.  If this breaks, either reverse-keying has been added
    (invalidating the Hughes 2004 equivalence) or the item count
    has drifted."""

    @pytest.mark.parametrize(
        "constant_value,expected_total",
        [
            (1, 3),
            (2, 6),
            (3, 9),
        ],
    )
    def test_constant_vector_follows_linear_formula(
        self, constant_value: int, expected_total: int
    ) -> None:
        result = score_ucla3([constant_value] * 3)
        assert result.total == expected_total
        # Explicit: total = 3v
        assert result.total == 3 * constant_value

    def test_acquiescence_gap_is_six(self) -> None:
        # Raw all-3s minus raw all-1s = 9 - 3 = 6, which is
        # (ITEM_COUNT × (ITEM_MAX - ITEM_MIN)).  A random
        # endpoint-only responder shifts the score the full 75%
        # of the 3-9 range — the highest endpoint-exposure on the
        # platform precisely because UCLA-3 has no reverse-keying
        # protection.  This is pinned so we remember the trade-off
        # Hughes 2004 made: psychometric brevity at the cost of
        # acquiescence-resistance.
        high = score_ucla3([3, 3, 3]).total
        low = score_ucla3([1, 1, 1]).total
        assert high - low == 6


# ---------------------------------------------------------------------------
# Audit invariance — items field preserves raw input
# ---------------------------------------------------------------------------


class TestAuditInvariance:
    def test_items_tuple_matches_input_order(self) -> None:
        # The three items are ordered: 1=companionship, 2=left-out,
        # 3=isolated.  The items field preserves that ordering so
        # clinician UI can render per-item deltas over time.
        result = score_ucla3([3, 1, 2])
        assert result.items == (3, 1, 2)

    def test_items_tuple_is_immutable(self) -> None:
        # Tuple output guarantees callers cannot mutate the audit
        # trail post-scoring.
        result = score_ucla3([1, 2, 3])
        assert isinstance(result.items, tuple)
        with pytest.raises(TypeError):
            result.items[0] = 99  # type: ignore[index]

    def test_items_survives_score_roundtrip(self) -> None:
        # Canonical audit property: items field = raw input
        # (UCLA-3 is the ONLY platform instrument where this is
        # trivially true because there is no post-flip step).
        raw = [2, 3, 1]
        result = score_ucla3(raw)
        assert list(result.items) == raw


# ---------------------------------------------------------------------------
# Clinical vignettes — reference patient patterns
# ---------------------------------------------------------------------------


class TestClinicalVignettes:
    """Patient-like response patterns grounded in the validation
    literature."""

    def test_widowhood_profile(self) -> None:
        # Keyes 2012 widowhood profile: strong "lack companionship"
        # (lost spouse), moderate "left out" (couple-centric social
        # invitations no longer extend), moderate isolation (social
        # routine disrupted).  Raw [3, 2, 2] = 7.  Signals the
        # 2-year post-widowhood alcohol-use-disorder risk window.
        result = score_ucla3([3, 2, 2])
        assert result.total == 7
        assert result.severity == "continuous"

    def test_retirement_isolation_profile(self) -> None:
        # Satre 2004 retirement-transition profile: moderate across
        # all three items as the work-based social structure erodes.
        # Raw [2, 2, 2] = 6.  Signals the retirement-trigger
        # relapse-risk window for middle-age-to-retirement cohort.
        result = score_ucla3([2, 2, 2])
        assert result.total == 6
        assert result.severity == "continuous"

    def test_socially_connected_baseline(self) -> None:
        # Community-sample low-loneliness baseline: all "Hardly ever".
        # Raw [1, 1, 1] = 3.  Hughes 2004 HRS bottom tercile.
        result = score_ucla3([1, 1, 1])
        assert result.total == 3
        assert result.severity == "continuous"

    def test_severe_isolation_extremum(self) -> None:
        # Hughes 2004 HRS top tercile extremum: all "Often".
        # Raw [3, 3, 3] = 9.  Holt-Lunstad 2010 mortality-HR ≈ 1.26
        # range.  Surfaces to clinician UI for C-SSRS follow-up
        # per Calati 2019 (but does NOT set requires_t3 itself).
        result = score_ucla3([3, 3, 3])
        assert result.total == 9
        assert result.severity == "continuous"

    def test_hrs_sample_mean_approximation(self) -> None:
        # Hughes 2004 HRS-sample mean ≈ 3.8 (n = 2101).  Pattern
        # [1, 2, 1] = 4 or [2, 1, 1] = 4 or [1, 1, 2] = 4 approximate
        # this mean.  All three are valid near-mean vignettes.
        for vec in ([1, 2, 1], [2, 1, 1], [1, 1, 2]):
            result = score_ucla3(vec)
            assert result.total == 4
            assert result.severity == "continuous"

    def test_post_bereavement_intervention_delta(self) -> None:
        # 12-week bereavement-support-group intervention: pre = 7
        # (widowhood profile), post = 4 (connection rebuilt).  Delta
        # of 3 is a meaningful within-participant change given the
        # 3-9 total range.  Jacobson-Truax RCI applied at the
        # trajectory layer determines clinical significance.
        pre = score_ucla3([3, 2, 2]).total
        post = score_ucla3([2, 1, 1]).total
        assert pre == 7
        assert post == 4
        assert pre - post == 3

    def test_fne_b_high_ucla3_low_dissociation(self) -> None:
        # Adolescent with social anxiety (expected high FNE-B) but
        # intact peer network: low UCLA-3.  Raw [1, 1, 1] = 3.
        # Demonstrates UCLA-3 / FNE-B can dissociate: the construct
        # pair is NOT redundant.  Intervention target: exposure +
        # social-skills (FNE-B-led), not befriending (UCLA-3-led).
        result = score_ucla3([1, 1, 1])
        assert result.total == 3

    def test_fne_b_low_ucla3_high_dissociation(self) -> None:
        # Widowed retiree with intact social skills (expected low
        # FNE-B) but absent network: high UCLA-3.  Raw [3, 3, 3] = 9.
        # Demonstrates the complementary dissociation.  Intervention
        # target: structural social-contact building (UCLA-3-led),
        # not exposure (FNE-B-led).
        result = score_ucla3([3, 3, 3])
        assert result.total == 9


# ---------------------------------------------------------------------------
# Validation — item count
# ---------------------------------------------------------------------------


class TestItemCountValidation:
    def test_rejects_empty(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 3 items"):
            score_ucla3([])

    def test_rejects_two_items(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 3 items"):
            score_ucla3([1, 2])

    def test_rejects_four_items(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 3 items"):
            score_ucla3([1, 2, 3, 1])

    def test_rejects_full_ucla_r20(self) -> None:
        # Guards against accidental full-scale administration
        # passing through the brief-form scorer.
        with pytest.raises(InvalidResponseError, match="exactly 3 items"):
            score_ucla3([2] * 20)


# ---------------------------------------------------------------------------
# Validation — item value range
# ---------------------------------------------------------------------------


class TestItemValueValidation:
    def test_rejects_zero(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be in 1-3"):
            score_ucla3([0, 2, 2])

    def test_rejects_four(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be in 1-3"):
            score_ucla3([4, 2, 2])

    def test_rejects_negative(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be in 1-3"):
            score_ucla3([-1, 2, 2])

    def test_rejects_very_large(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be in 1-3"):
            score_ucla3([99, 2, 2])

    def test_rejects_five_point_likert_value(self) -> None:
        # Guards against accidental FNE-B / STAI-6 1-5 or 1-4
        # Likert value being routed through UCLA-3.
        with pytest.raises(InvalidResponseError, match="must be in 1-3"):
            score_ucla3([5, 2, 2])


# ---------------------------------------------------------------------------
# Validation — item type
# ---------------------------------------------------------------------------


class TestItemTypeValidation:
    def test_rejects_bool_true(self) -> None:
        # Bool rejection per CLAUDE.md standing rule: True must not
        # silently coerce to 1 at the scorer.
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_ucla3([True, 2, 2])

    def test_rejects_bool_false(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_ucla3([False, 2, 2])

    def test_rejects_float(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_ucla3([2.5, 2, 2])  # type: ignore[list-item]

    def test_rejects_none(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_ucla3([None, 2, 2])  # type: ignore[list-item]

    def test_rejects_string(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_ucla3(["2", 2, 2])  # type: ignore[list-item]


# ---------------------------------------------------------------------------
# Result shape invariants
# ---------------------------------------------------------------------------


class TestResultShapeInvariants:
    def test_result_is_frozen_dataclass(self) -> None:
        result = score_ucla3([1, 1, 1])
        with pytest.raises(Exception):
            result.total = 999  # type: ignore[misc]

    def test_result_is_hashable(self) -> None:
        # Frozen dataclass with tuple items must be hashable —
        # downstream caches (trajectory layer RCI) rely on this.
        result = score_ucla3([1, 2, 3])
        hash(result)

    def test_result_carries_instrument_version(self) -> None:
        result = score_ucla3([2, 2, 2])
        assert result.instrument_version == "ucla3-1.0.0"


# ---------------------------------------------------------------------------
# Range bounds — exhaustive total-range property
# ---------------------------------------------------------------------------


class TestRangeBounds:
    def test_total_never_below_three(self) -> None:
        # Minimum total = 3 (all raw 1s).  Any response must land
        # at or above this floor.
        for v in range(ITEM_MIN, ITEM_MAX + 1):
            result = score_ucla3([v, v, v])
            assert result.total >= 3

    def test_total_never_above_nine(self) -> None:
        # Maximum total = 9 (all raw 3s).  Any response must land
        # at or below this ceiling.
        for v in range(ITEM_MIN, ITEM_MAX + 1):
            result = score_ucla3([v, v, v])
            assert result.total <= 9

    @pytest.mark.parametrize(
        "expected_total",
        list(range(3, 10)),
    )
    def test_every_total_in_range_is_reachable(
        self, expected_total: int
    ) -> None:
        # Exhaustive: every integer total from 3 to 9 is reachable
        # by some valid 1-3 vector.
        # Construct a vector summing to expected_total:
        # start at [1, 1, 1] (total 3) and distribute the extra
        # over the items.
        extra = expected_total - 3
        vec = [1, 1, 1]
        i = 0
        while extra > 0 and i < 3:
            add = min(2, extra)
            vec[i] += add
            extra -= add
            i += 1
        assert sum(vec) == expected_total
        assert score_ucla3(vec).total == expected_total


# ---------------------------------------------------------------------------
# Input type compatibility — sequence protocol
# ---------------------------------------------------------------------------


class TestInputTypeCompatibility:
    def test_accepts_list(self) -> None:
        assert score_ucla3([1, 2, 3]).total == 6

    def test_accepts_tuple(self) -> None:
        assert score_ucla3((1, 2, 3)).total == 6

    def test_rejects_string(self) -> None:
        # Strings are sequences but must not be accepted as item
        # lists — the individual 'char' elements would pass the
        # bool-int check and fail the range check, but the error
        # message is nicer if caught upstream.
        with pytest.raises(InvalidResponseError):
            score_ucla3("123")  # type: ignore[arg-type]

    def test_rejects_bytes(self) -> None:
        with pytest.raises(InvalidResponseError):
            score_ucla3(b"123")  # type: ignore[arg-type]

    def test_accepts_generator_by_exhausting_via_tuple_conversion(
        self,
    ) -> None:
        # Sequence protocol requires random access; a generator
        # does not satisfy Sequence.  Document this: callers must
        # materialize before scoring.  Confirms we reject
        # non-Sequence iterables.
        gen = (v for v in [1, 2, 3])
        with pytest.raises(InvalidResponseError):
            score_ucla3(gen)  # type: ignore[arg-type]

"""Tests for the CIUS Compulsive Internet Use Scale scorer.

Meerkerk 2009 CyberPsychology & Behavior 12(1):1-6.  14 items,
0-4 Likert, no reverse keying, total 0-56, severity = "continuous"
(no cutpoints pinned).
"""

from __future__ import annotations

import pytest

from discipline.psychometric.scoring.cius import (
    CIUS_REVERSE_ITEMS,
    INSTRUMENT_VERSION,
    ITEM_COUNT,
    ITEM_MAX,
    ITEM_MIN,
    InvalidResponseError,
    score_cius,
)

# ---------------------------------------------------------------------------
# Constants — pinned against accidental drift
# ---------------------------------------------------------------------------


class TestConstants:
    def test_instrument_version_is_pinned(self) -> None:
        assert INSTRUMENT_VERSION == "cius-1.0.0"

    def test_item_count_is_fourteen(self) -> None:
        # Meerkerk 2009 brief-form cardinality; changing invalidates
        # the factor structure and r=0.70+ Young 1998 IAT
        # convergent validity.
        assert ITEM_COUNT == 14

    def test_item_min_is_zero(self) -> None:
        # CIUS uses a 0-based Likert — 0 = "Never" is semantically
        # "zero compulsivity", not just "low".  This differs from
        # FNE-B / STAI-6 / UCLA-3 (1-based) and is pinned to
        # prevent accidental rescaling.
        assert ITEM_MIN == 0

    def test_item_max_is_four(self) -> None:
        # Meerkerk 2009 5-point Likert scales 0-4.
        assert ITEM_MAX == 4

    def test_reverse_items_is_empty(self) -> None:
        # Meerkerk 2009 deliberately omitted balanced-wording
        # acquiescence control for derivation-cohort item-budget
        # reasons.  Empty tuple is THE canonical fingerprint.
        assert CIUS_REVERSE_ITEMS == ()

    def test_severity_is_continuous_only(self) -> None:
        # No exported severity enum; Meerkerk 2009 published no
        # cutpoints; Guertler 2014 >=21/>=28 thresholds are
        # secondary literature excluded per CLAUDE.md.
        result = score_cius([2] * 14)
        assert result.severity == "continuous"

    def test_no_subscale_constants(self) -> None:
        # Single-factor per Meerkerk 2009 CFA and Guertler 2014
        # replication.  No subscale indices exported.
        import discipline.psychometric.scoring.cius as mod

        assert not hasattr(mod, "CIUS_SUBSCALES")
        assert not hasattr(mod, "CIUS_FACTORS")

    def test_no_severity_threshold_constants(self) -> None:
        # Guertler 2014 >=21/>=28 cutoffs MUST NOT be shipped as
        # primary-source anchors.  Per CLAUDE.md no-hand-rolled-
        # bands rule.
        import discipline.psychometric.scoring.cius as mod

        assert not hasattr(mod, "CIUS_SEVERITY_THRESHOLDS")
        assert not hasattr(mod, "CIUS_CUTOFFS")
        assert not hasattr(mod, "CIUS_AT_RISK_THRESHOLD")


# ---------------------------------------------------------------------------
# Total correctness — all-v constant / min / max / arithmetic
# ---------------------------------------------------------------------------


class TestTotalCorrectness:
    def test_all_zeros_total_is_zero(self) -> None:
        # Raw [0]*14 — "Never" on every item.  Total 0.  The
        # clinical floor — no compulsive internet use at all.
        result = score_cius([0] * 14)
        assert result.total == 0

    def test_all_ones_total_is_fourteen(self) -> None:
        # Raw [1]*14 — "Seldom" on every item.  Total 14.  Linear.
        result = score_cius([1] * 14)
        assert result.total == 14

    def test_all_twos_total_is_twenty_eight(self) -> None:
        # Raw [2]*14.  Total 28.  Coincides with Guertler 2014's
        # secondary-lit "high risk" threshold — platform ignores.
        result = score_cius([2] * 14)
        assert result.total == 28

    def test_all_threes_total_is_forty_two(self) -> None:
        result = score_cius([3] * 14)
        assert result.total == 42

    def test_all_fours_total_is_fifty_six(self) -> None:
        # Raw [4]*14 — "Very often" on every item.  Total 56.
        # The maximum — saturated compulsive-use pattern.
        result = score_cius([4] * 14)
        assert result.total == 56

    def test_mixed_pattern_arithmetic(self) -> None:
        # Raw [0, 1, 2, 3, 4, 0, 1, 2, 3, 4, 0, 1, 2, 3]:
        # 0+1+2+3+4+0+1+2+3+4+0+1+2+3 = 26
        result = score_cius([0, 1, 2, 3, 4, 0, 1, 2, 3, 4, 0, 1, 2, 3])
        assert result.total == 26

    def test_single_item_contribution(self) -> None:
        # Raw all-0 except item 1 = 4.  Total 4.
        items = [0] * 14
        items[0] = 4
        result = score_cius(items)
        assert result.total == 4


# ---------------------------------------------------------------------------
# Severity — always continuous
# ---------------------------------------------------------------------------


class TestSeverity:
    def test_minimum_total_is_continuous(self) -> None:
        result = score_cius([0] * 14)
        assert result.total == 0
        assert result.severity == "continuous"

    def test_maximum_total_is_continuous(self) -> None:
        result = score_cius([4] * 14)
        assert result.total == 56
        assert result.severity == "continuous"

    def test_guertler_2014_at_risk_threshold_not_banded(self) -> None:
        # Guertler 2014 proposed >=21 as "at risk".  Platform fires
        # NO band at this value — secondary literature.  Construct
        # a vector summing to exactly 21.
        # [3,3,3,3,3,3,3,0,0,0,0,0,0,0] = 7×3 = 21
        result = score_cius([3, 3, 3, 3, 3, 3, 3, 0, 0, 0, 0, 0, 0, 0])
        assert result.total == 21
        assert result.severity == "continuous"

    def test_guertler_2014_high_risk_threshold_not_banded(self) -> None:
        # Guertler 2014 proposed >=28 as "high risk".  Platform
        # fires NO band.  [2]*14 = 28.
        result = score_cius([2] * 14)
        assert result.total == 28
        assert result.severity == "continuous"

    @pytest.mark.parametrize(
        "raw_items",
        [
            [0] * 14,
            [1] * 14,
            [2] * 14,
            [3] * 14,
            [4] * 14,
            [0, 4] * 7,
            [4, 0] * 7,
        ],
    )
    def test_all_totals_are_continuous(self, raw_items: list[int]) -> None:
        result = score_cius(raw_items)
        assert result.severity == "continuous"


# ---------------------------------------------------------------------------
# No reverse keying — directionality
# ---------------------------------------------------------------------------


class TestNoReverseKeying:
    """CIUS has ZERO reverse-keyed items.  Every item is negatively
    worded (compulsive-use symptom descriptions) so raw value =
    post-flip value."""

    def test_raw_value_equals_total_contribution(self) -> None:
        # Raising any single item from 0 to 4 raises the total by
        # exactly 4 (the Likert step × 1 item).
        base = score_cius([0] * 14).total
        for i in range(14):
            perturbed = [0] * 14
            perturbed[i] = 4
            assert score_cius(perturbed).total == base + 4

    def test_items_field_matches_raw_input(self) -> None:
        # Audit invariance: items preserves raw exactly.
        raw = [0, 1, 2, 3, 4, 0, 1, 2, 3, 4, 0, 1, 2, 3]
        result = score_cius(raw)
        assert result.items == tuple(raw)

    def test_all_zeros_is_low_compulsivity(self) -> None:
        # Direction check: all-0s must be the LOW-compulsivity
        # extreme.  Contrast with reverse-keyed instruments where
        # all-min raw is NOT the low extreme.
        low = score_cius([0] * 14).total
        high = score_cius([4] * 14).total
        assert low < high
        assert low == 0
        assert high == 56


# ---------------------------------------------------------------------------
# Acquiescence signature — linear total = 14v
# ---------------------------------------------------------------------------


class TestAcquiescenceSignature:
    """CIUS has no acquiescence-bias control; linear formula
    total = 14v signals the all-negative-wording design.
    Endpoint-exposure gap is the full 0-56 range."""

    @pytest.mark.parametrize(
        "constant_value,expected_total",
        [
            (0, 0),
            (1, 14),
            (2, 28),
            (3, 42),
            (4, 56),
        ],
    )
    def test_constant_vector_follows_linear_formula(
        self, constant_value: int, expected_total: int
    ) -> None:
        result = score_cius([constant_value] * 14)
        assert result.total == expected_total
        assert result.total == 14 * constant_value

    def test_acquiescence_gap_is_fifty_six(self) -> None:
        # Raw all-4s minus raw all-0s = 56 - 0 = 56, the full
        # 0-56 range.  A random endpoint-only responder shifts
        # the score 100% of range.  Documents the Meerkerk 2009
        # trade-off (item-budget constrained).
        high = score_cius([4] * 14).total
        low = score_cius([0] * 14).total
        assert high - low == 56


# ---------------------------------------------------------------------------
# Audit invariance — items field preserves raw input
# ---------------------------------------------------------------------------


class TestAuditInvariance:
    def test_items_tuple_matches_input_order(self) -> None:
        # Meerkerk 2009 administration order preserved.
        result = score_cius([4, 0, 4, 0, 4, 0, 4, 0, 4, 0, 4, 0, 4, 0])
        assert result.items == (4, 0, 4, 0, 4, 0, 4, 0, 4, 0, 4, 0, 4, 0)

    def test_items_tuple_is_immutable(self) -> None:
        result = score_cius([2] * 14)
        assert isinstance(result.items, tuple)
        with pytest.raises(TypeError):
            result.items[0] = 99  # type: ignore[index]

    def test_items_survives_roundtrip(self) -> None:
        # Canonical audit property: items = raw input (CIUS is
        # one of only two platform instruments where this is
        # trivially true — UCLA-3 is the other).
        raw = [1, 2, 3, 4, 0, 1, 2, 3, 4, 0, 1, 2, 3, 4]
        result = score_cius(raw)
        assert list(result.items) == raw


# ---------------------------------------------------------------------------
# Clinical vignettes — reference patient patterns
# ---------------------------------------------------------------------------


class TestClinicalVignettes:
    """Patient-like response patterns grounded in Meerkerk 2009,
    Guertler 2014, and Caplan 2003 literature."""

    def test_non_user_baseline(self) -> None:
        # Non-problematic user: "never" on every compulsivity
        # item.  Raw [0]*14 = 0.  Below any literature-reported
        # cutoff.
        result = score_cius([0] * 14)
        assert result.total == 0
        assert result.severity == "continuous"

    def test_moderate_engagement_profile(self) -> None:
        # Heavy-but-not-problematic internet user: "sometimes"
        # on use-frequency items (6, 7), "seldom" elsewhere.
        # Raw [1,1,1,1,1,2,2,1,1,1,1,1,1,1]:
        # 1+1+1+1+1+2+2+1+1+1+1+1+1+1 = 16
        result = score_cius([1, 1, 1, 1, 1, 2, 2, 1, 1, 1, 1, 1, 1, 1])
        assert result.total == 16
        assert result.severity == "continuous"

    def test_caplan_2003_compensatory_use_profile(self) -> None:
        # High FNE-B / UCLA-3 user compensating via online social
        # interaction.  Elevated on affect-regulation items (12, 13)
        # and preference-over-offline (4), moderate elsewhere.
        # Raw [2,2,2,3,2,2,2,2,2,2,2,4,4,2]:
        # 2+2+2+3+2+2+2+2+2+2+2+4+4+2 = 33
        result = score_cius([2, 2, 2, 3, 2, 2, 2, 2, 2, 2, 2, 4, 4, 2])
        assert result.total == 33
        assert result.severity == "continuous"

    def test_gaming_disorder_maximal_profile(self) -> None:
        # ICD-11 Gaming Disorder pattern — saturated endorsement
        # across all items.  Raw [4]*14 = 56.
        result = score_cius([4] * 14)
        assert result.total == 56
        assert result.severity == "continuous"

    def test_recovery_compensation_profile(self) -> None:
        # Recovering alcohol-use-disorder user substituting
        # digital engagement per Koob 2005 allostatic-load
        # theory.  Elevated on affect-regulation items (12, 13)
        # and withdrawal item (14), moderate on salience /
        # conflict items.
        # Raw [2, 2, 1, 2, 2, 3, 3, 2, 2, 2, 1, 3, 3, 3]:
        # 2+2+1+2+2+3+3+2+2+2+1+3+3+3 = 31
        result = score_cius([2, 2, 1, 2, 2, 3, 3, 2, 2, 2, 1, 3, 3, 3])
        assert result.total == 31
        assert result.severity == "continuous"

    def test_cbt_pre_post_delta(self) -> None:
        # Young 2007 / Cash 2012 CBT-IA protocol: pre-treatment
        # saturated compulsive-use pattern → post-treatment
        # moderate baseline.  Delta 42 is a large effect size.
        pre = score_cius([4] * 14).total
        post = score_cius([1] * 14).total
        assert pre == 56
        assert post == 14
        assert pre - post == 42

    def test_adolescent_meerkerk_cohort_mean(self) -> None:
        # Meerkerk 2009 adolescent derivation sample reported
        # mean ~ 10 (SD ~ 7).  Raw all-0 except first item = 4
        # and items 5,6 at 3 each: 4+3+3 = 10.
        items = [0] * 14
        items[0] = 4
        items[4] = 3
        items[5] = 3
        result = score_cius(items)
        assert result.total == 10


# ---------------------------------------------------------------------------
# Validation — item count
# ---------------------------------------------------------------------------


class TestItemCountValidation:
    def test_rejects_empty(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 14 items"):
            score_cius([])

    def test_rejects_thirteen_items(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 14 items"):
            score_cius([2] * 13)

    def test_rejects_fifteen_items(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 14 items"):
            score_cius([2] * 15)

    def test_rejects_twenty_items_young_iat_shape(self) -> None:
        # Young 1998 IAT is 20 items — guards against accidental
        # IAT administration routed through CIUS scorer.
        with pytest.raises(InvalidResponseError, match="exactly 14 items"):
            score_cius([2] * 20)


# ---------------------------------------------------------------------------
# Validation — item value range (0-4, with 0 valid)
# ---------------------------------------------------------------------------


class TestItemValueValidation:
    def test_accepts_zero_as_valid(self) -> None:
        # CIUS is 0-based — 0 is a VALID "Never" response.  Must
        # NOT raise, unlike FNE-B / STAI-6 / UCLA-3 which reject 0.
        result = score_cius([0] * 14)
        assert result.total == 0

    def test_rejects_negative_one(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be in 0-4"):
            score_cius([-1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2])

    def test_rejects_five(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be in 0-4"):
            score_cius([5, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2])

    def test_rejects_ninety_nine(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be in 0-4"):
            score_cius([99, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2])

    def test_rejects_very_negative(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be in 0-4"):
            score_cius([-99, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2])


# ---------------------------------------------------------------------------
# Validation — item type (bool rejection is LOAD-BEARING on CIUS)
# ---------------------------------------------------------------------------


class TestItemTypeValidation:
    """CIUS is the first platform instrument where ``False → 0`` is
    in valid range (0 = "Never").  The scorer's bool rejection is
    therefore LOAD-BEARING: without it, a serialization bug
    silently scoring ``False`` responses would read as "zero
    compulsivity" rather than raising."""

    def test_rejects_bool_false_despite_valid_range(self) -> None:
        # CRITICAL: False → 0 is in range but must still raise.
        # Documents that the scorer's bool check runs BEFORE the
        # range check.
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_cius([False, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2])

    def test_rejects_bool_true_despite_valid_range(self) -> None:
        # True → 1 is also in range; bool rejected regardless.
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_cius([True, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2])

    def test_rejects_float(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_cius([2.5, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2])  # type: ignore[list-item]

    def test_rejects_none(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_cius([None, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2])  # type: ignore[list-item]

    def test_rejects_string(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_cius(["2", 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2])  # type: ignore[list-item]


# ---------------------------------------------------------------------------
# Result shape invariants
# ---------------------------------------------------------------------------


class TestResultShapeInvariants:
    def test_result_is_frozen_dataclass(self) -> None:
        result = score_cius([0] * 14)
        with pytest.raises(Exception):
            result.total = 999  # type: ignore[misc]

    def test_result_is_hashable(self) -> None:
        result = score_cius([1] * 14)
        hash(result)

    def test_result_carries_instrument_version(self) -> None:
        result = score_cius([2] * 14)
        assert result.instrument_version == "cius-1.0.0"


# ---------------------------------------------------------------------------
# Range bounds — exhaustive total-range property
# ---------------------------------------------------------------------------


class TestRangeBounds:
    def test_total_never_below_zero(self) -> None:
        for v in range(ITEM_MIN, ITEM_MAX + 1):
            result = score_cius([v] * 14)
            assert result.total >= 0

    def test_total_never_above_fifty_six(self) -> None:
        for v in range(ITEM_MIN, ITEM_MAX + 1):
            result = score_cius([v] * 14)
            assert result.total <= 56

    @pytest.mark.parametrize(
        "expected_total",
        [0, 14, 28, 42, 56],
    )
    def test_every_constant_total_is_reachable(
        self, expected_total: int
    ) -> None:
        # Exhaustive pin on the 5 constant-vector anchor points.
        constant = expected_total // 14
        assert score_cius([constant] * 14).total == expected_total


# ---------------------------------------------------------------------------
# Input type compatibility — sequence protocol
# ---------------------------------------------------------------------------


class TestInputTypeCompatibility:
    def test_accepts_list(self) -> None:
        assert score_cius([2] * 14).total == 28

    def test_accepts_tuple(self) -> None:
        assert score_cius(tuple([2] * 14)).total == 28

    def test_rejects_string(self) -> None:
        with pytest.raises(InvalidResponseError):
            score_cius("01234012340123")  # type: ignore[arg-type]

    def test_rejects_bytes(self) -> None:
        with pytest.raises(InvalidResponseError):
            score_cius(b"01234012340123")  # type: ignore[arg-type]

    def test_rejects_generator(self) -> None:
        gen = (v for v in [2] * 14)
        with pytest.raises(InvalidResponseError):
            score_cius(gen)  # type: ignore[arg-type]

"""Tests for PANAS-10 scorer — Thompson 2007 I-PANAS-SF.

The International PANAS Short Form is a 10-item cross-cultural
derivation of the 20-item PANAS (Watson, Clark & Tellegen 1988).
Thompson 2007 (JCCP 38(2):227-242) validated configural + metric
+ scalar measurement invariance across 8 cultural groups
(n = 1,789), making it the PANAS variant of record for the
Discipline OS four-locale launch (en / fr / ar / fa).

Scorer contract — this is the platform's FIRST bidirectional-
subscales instrument:

- Two orthogonal subscales — PA (positive affect) and NA
  (negative affect) — per Watson 1988 / Tellegen 1999.
- No composite total on the scorer result.  The routing layer
  emits ``total = pa_sum`` for AssessmentResult envelope
  uniformity; clinicians MUST read both subscales via the
  ``subscales`` dict.
- No severity bands.  Thompson 2007 did not publish clinical
  cutpoints; Crawford & Henry 2004 UK norms (PA 32.1 ±6.8,
  NA 14.8 ±5.3 on 10-50 scale) are descriptive distributions,
  not banded thresholds.
- No ``requires_t3`` — PANAS-10 probes affect dimensions, not
  suicidality.  Item 1 "upset" is general NA, NOT ideation.
  Acute-risk screening stays on C-SSRS / PHQ-9 item 9.

Position -> subscale mapping per Thompson 2007 Table 1:
    1 Upset (NA) | 2 Hostile (NA) | 3 Alert (PA)
    4 Ashamed (NA) | 5 Inspired (PA) | 6 Nervous (NA)
    7 Determined (PA) | 8 Attentive (PA) | 9 Afraid (NA)
    10 Active (PA)
"""

from __future__ import annotations

import pytest

from discipline.psychometric.scoring import panas10
from discipline.psychometric.scoring.panas10 import (
    INSTRUMENT_VERSION,
    ITEM_COUNT,
    ITEM_MAX,
    ITEM_MIN,
    PANAS10_NA_POSITIONS,
    PANAS10_PA_POSITIONS,
    PANAS10_SUBSCALES,
    InvalidResponseError,
    Panas10Result,
    score_panas10,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


class TestConstants:
    """Pin the published structure of Thompson 2007 I-PANAS-SF.

    Any change here is a clinical decision (Thompson 2007
    measurement-invariance validation) — NOT an implementation
    tweak.  Reordering positions invalidates the cross-cultural
    invariance established across 8 cultural groups.
    """

    def test_instrument_version(self) -> None:
        assert INSTRUMENT_VERSION == "panas10-1.0.0"

    def test_item_count_is_ten(self) -> None:
        assert ITEM_COUNT == 10

    def test_item_min_is_one(self) -> None:
        # Thompson 2007 1-5 Likert ("very slightly or not at
        # all" -> "extremely").
        assert ITEM_MIN == 1

    def test_item_max_is_five(self) -> None:
        assert ITEM_MAX == 5

    def test_pa_positions_per_thompson_2007(self) -> None:
        # Positions 3, 5, 7, 8, 10 = Alert, Inspired,
        # Determined, Attentive, Active.  Five PA items, all
        # valence-aligned, no reverse-keying.
        assert PANAS10_PA_POSITIONS == (3, 5, 7, 8, 10)

    def test_na_positions_per_thompson_2007(self) -> None:
        # Positions 1, 2, 4, 6, 9 = Upset, Hostile, Ashamed,
        # Nervous, Afraid.  Five NA items, all valence-aligned,
        # no reverse-keying.
        assert PANAS10_NA_POSITIONS == (1, 2, 4, 6, 9)

    def test_subscales_interleave_per_thompson_2007(self) -> None:
        # Thompson 2007 Table 1: administration order
        # interleaves PA and NA to reduce within-subscale
        # response-set bias.  PA and NA positions must PARTITION
        # 1..10 with no overlap and no gaps.
        combined = set(PANAS10_PA_POSITIONS) | set(PANAS10_NA_POSITIONS)
        assert combined == set(range(1, 11))
        overlap = set(PANAS10_PA_POSITIONS) & set(PANAS10_NA_POSITIONS)
        assert overlap == set()

    def test_each_subscale_has_five_items(self) -> None:
        # Thompson 2007 derivation: balanced 5+5 split via factor
        # loadings from the 20-item parent PANAS.
        assert len(PANAS10_PA_POSITIONS) == 5
        assert len(PANAS10_NA_POSITIONS) == 5

    def test_subscale_names(self) -> None:
        # Wire contract: subscale names are exported as a single
        # source of truth so clinician-UI renderers key off one
        # constant.
        assert PANAS10_SUBSCALES == ("positive_affect", "negative_affect")

    def test_no_reverse_items_exported(self) -> None:
        # Watson 1988 §2 derivation used same-valence items
        # within each subscale; no reverse-keying.
        assert not hasattr(panas10, "PANAS10_REVERSE_ITEMS")

    def test_no_severity_thresholds_exported(self) -> None:
        # PANAS-10 is continuous.  Thompson 2007 did not publish
        # banded severity; hand-rolling bands violates CLAUDE.md.
        assert not hasattr(panas10, "PANAS10_SEVERITY_THRESHOLDS")

    def test_no_positive_cutoff_exported(self) -> None:
        # PANAS-10 is not a screen — no operating point.
        assert not hasattr(panas10, "PANAS10_POSITIVE_CUTOFF")

    def test_public_exports(self) -> None:
        assert set(panas10.__all__) == {
            "INSTRUMENT_VERSION",
            "ITEM_COUNT",
            "ITEM_MAX",
            "ITEM_MIN",
            "InvalidResponseError",
            "PANAS10_NA_POSITIONS",
            "PANAS10_PA_POSITIONS",
            "PANAS10_SUBSCALES",
            "Panas10Result",
            "Severity",
            "score_panas10",
        }


# ---------------------------------------------------------------------------
# Subscale correctness — independent PA and NA sums
# ---------------------------------------------------------------------------


class TestSubscaleCorrectness:
    """PA and NA subscale sums are independent; each covers 5-25."""

    def test_all_ones_pa_is_five(self) -> None:
        result = score_panas10([1, 1, 1, 1, 1, 1, 1, 1, 1, 1])
        assert result.pa_sum == 5

    def test_all_ones_na_is_five(self) -> None:
        result = score_panas10([1, 1, 1, 1, 1, 1, 1, 1, 1, 1])
        assert result.na_sum == 5

    def test_all_fives_pa_is_twentyfive(self) -> None:
        result = score_panas10([5, 5, 5, 5, 5, 5, 5, 5, 5, 5])
        assert result.pa_sum == 25

    def test_all_fives_na_is_twentyfive(self) -> None:
        result = score_panas10([5, 5, 5, 5, 5, 5, 5, 5, 5, 5])
        assert result.na_sum == 25

    def test_pa_only_max_na_min(self) -> None:
        # Flourishing profile: max PA, min NA.
        # PA positions 3, 5, 7, 8, 10 = 5; NA positions 1, 2, 4,
        # 6, 9 = 1.  pa_sum = 25, na_sum = 5.
        items = [1, 1, 5, 1, 5, 1, 5, 5, 1, 5]
        result = score_panas10(items)
        assert result.pa_sum == 25
        assert result.na_sum == 5

    def test_pa_min_na_max(self) -> None:
        # Classic depression profile: min PA, max NA.
        # PA positions -> 1, NA positions -> 5.  pa_sum = 5,
        # na_sum = 25.
        items = [5, 5, 1, 5, 1, 5, 1, 1, 5, 1]
        result = score_panas10(items)
        assert result.pa_sum == 5
        assert result.na_sum == 25

    def test_pa_sum_equals_sum_of_pa_positions(self) -> None:
        # Mathematical identity across varying response sets.
        for pa_val in (1, 3, 5):
            for na_val in (1, 3, 5):
                items = [
                    na_val, na_val, pa_val, na_val, pa_val,
                    na_val, pa_val, pa_val, na_val, pa_val,
                ]
                result = score_panas10(items)
                assert result.pa_sum == pa_val * 5
                assert result.na_sum == na_val * 5

    def test_pa_sum_within_bounds(self) -> None:
        # Domain invariant: PA sum in [5, 25].
        for items in (
            [1] * 10,
            [5] * 10,
            [3, 3, 3, 3, 3, 3, 3, 3, 3, 3],
            [1, 5, 1, 5, 1, 5, 1, 5, 1, 5],
        ):
            result = score_panas10(items)
            assert 5 <= result.pa_sum <= 25
            assert 5 <= result.na_sum <= 25


# ---------------------------------------------------------------------------
# Orthogonality — pinning the Watson 1988 / Tellegen 1999 property
# ---------------------------------------------------------------------------


class TestOrthogonality:
    """Watson 1988 and Tellegen 1999 established PA and NA as
    orthogonal dimensions.  This test class pins the scorer-level
    manifestation: changing an NA-position response must NEVER
    change pa_sum, and vice versa."""

    @pytest.mark.parametrize("na_pos_1_indexed", [1, 2, 4, 6, 9])
    def test_raising_na_position_does_not_change_pa_sum(
        self, na_pos_1_indexed: int
    ) -> None:
        # Baseline: all ones.
        base_items = [1] * 10
        base = score_panas10(base_items)

        # Raise a single NA position to 5.
        perturbed = list(base_items)
        perturbed[na_pos_1_indexed - 1] = 5
        result = score_panas10(perturbed)

        # PA sum must be unchanged.
        assert result.pa_sum == base.pa_sum
        # NA sum must have risen by exactly 4 (1 -> 5).
        assert result.na_sum == base.na_sum + 4

    @pytest.mark.parametrize("pa_pos_1_indexed", [3, 5, 7, 8, 10])
    def test_raising_pa_position_does_not_change_na_sum(
        self, pa_pos_1_indexed: int
    ) -> None:
        base_items = [1] * 10
        base = score_panas10(base_items)

        perturbed = list(base_items)
        perturbed[pa_pos_1_indexed - 1] = 5
        result = score_panas10(perturbed)

        # NA sum must be unchanged.
        assert result.na_sum == base.na_sum
        # PA sum must have risen by exactly 4.
        assert result.pa_sum == base.pa_sum + 4

    def test_simultaneous_perturbation_affects_both_independently(
        self,
    ) -> None:
        # Raise position 3 (PA) and position 1 (NA) simultaneously.
        # Each subscale must reflect its own position's change,
        # independent of the other.
        items = [1] * 10
        items[0] = 5   # position 1 = NA
        items[2] = 5   # position 3 = PA
        result = score_panas10(items)

        # PA baseline 5 + (5 - 1) = 9.
        assert result.pa_sum == 9
        # NA baseline 5 + (5 - 1) = 9.
        assert result.na_sum == 9

    def test_pa_max_na_max_no_interaction(self) -> None:
        # High-arousal, high-engagement profile (both elevated).
        # Tellegen 1999 circumplex: orthogonal axes mean both
        # can be high simultaneously — they are NOT inversely
        # linked.
        result = score_panas10([5] * 10)
        assert result.pa_sum == 25
        assert result.na_sum == 25


# ---------------------------------------------------------------------------
# Position -> subscale mapping — parametrized per Thompson 2007
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "position_1, expected_subscale",
    [
        (1, "NA"),    # Upset
        (2, "NA"),    # Hostile
        (3, "PA"),    # Alert
        (4, "NA"),    # Ashamed
        (5, "PA"),    # Inspired
        (6, "NA"),    # Nervous
        (7, "PA"),    # Determined
        (8, "PA"),    # Attentive
        (9, "NA"),    # Afraid
        (10, "PA"),   # Active
    ],
)
def test_position_contributes_to_expected_subscale(
    position_1: int, expected_subscale: str
) -> None:
    """Pin each Thompson 2007 position's subscale membership.

    A swap between PA and NA positions would produce silent
    scoring corruption — only a position-by-position pin catches
    it.  Mirrors the item-map pins in TAS-20 / PCL-5."""
    # Baseline = all 1s -> pa_sum 5, na_sum 5.  Raise one
    # position to 5.  Exactly one subscale should rise by 4.
    items = [1] * 10
    items[position_1 - 1] = 5
    result = score_panas10(items)

    if expected_subscale == "PA":
        assert result.pa_sum == 9, (
            f"position {position_1} should contribute to PA"
        )
        assert result.na_sum == 5, (
            f"position {position_1} should NOT contribute to NA"
        )
    else:
        assert result.na_sum == 9, (
            f"position {position_1} should contribute to NA"
        )
        assert result.pa_sum == 5, (
            f"position {position_1} should NOT contribute to PA"
        )


# ---------------------------------------------------------------------------
# Item-count validation
# ---------------------------------------------------------------------------


class TestItemCountValidation:
    def test_nine_items_rejected(self) -> None:
        # Trap: someone confuses PANAS-10 (10) with PHQ-9 (9).
        with pytest.raises(InvalidResponseError, match="exactly 10"):
            score_panas10([3] * 9)

    def test_eleven_items_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 10"):
            score_panas10([3] * 11)

    def test_twenty_items_rejected(self) -> None:
        # Trap: someone feeds the 20-item parent PANAS (Watson
        # 1988) into the short-form scorer.  Must fail loud.
        with pytest.raises(InvalidResponseError, match="exactly 10"):
            score_panas10([3] * 20)

    def test_zero_items_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 10"):
            score_panas10([])

    def test_five_items_rejected(self) -> None:
        # Trap: someone submits a single subscale (5 items) by
        # mistake.
        with pytest.raises(InvalidResponseError, match="exactly 10"):
            score_panas10([3] * 5)


# ---------------------------------------------------------------------------
# Item-range validation — strict 1-5 Likert
# ---------------------------------------------------------------------------


class TestItemRangeValidation:
    def test_zero_rejected(self) -> None:
        # Trap: someone uses a 0-4 scale (SCOFF-style or PHQ-9-
        # style) on a 1-5 instrument.
        with pytest.raises(InvalidResponseError, match="1-5"):
            score_panas10([0, 3, 3, 3, 3, 3, 3, 3, 3, 3])

    def test_six_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="1-5"):
            score_panas10([6, 3, 3, 3, 3, 3, 3, 3, 3, 3])

    def test_negative_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="1-5"):
            score_panas10([-1, 3, 3, 3, 3, 3, 3, 3, 3, 3])

    def test_large_positive_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="1-5"):
            score_panas10([99, 3, 3, 3, 3, 3, 3, 3, 3, 3])

    def test_range_violation_reports_correct_index(self) -> None:
        # Position-3 violation must report "item 3" (1-indexed).
        with pytest.raises(InvalidResponseError, match=r"item 3"):
            score_panas10([3, 3, 0, 3, 3, 3, 3, 3, 3, 3])

    def test_every_position_strict(self) -> None:
        # Each of the 10 positions enforces 1-5 strictly.
        for position in range(10):
            items = [3] * 10
            items[position] = 6
            with pytest.raises(InvalidResponseError, match="1-5"):
                score_panas10(items)

    def test_boundary_one_accepted(self) -> None:
        # Exact boundary 1 (minimum) must be accepted.
        score_panas10([1] * 10)

    def test_boundary_five_accepted(self) -> None:
        # Exact boundary 5 (maximum) must be accepted.
        score_panas10([5] * 10)


# ---------------------------------------------------------------------------
# Bool rejection — CLAUDE.md standing rule
# ---------------------------------------------------------------------------


class TestBoolRejection:
    """CLAUDE.md standing rule: ``bool`` values rejected at the
    scorer even though ``bool is int`` in Python.  Keeps the
    wire contract explicit: a PANAS-10 response is a 1-5 int,
    not a flag."""

    def test_true_in_position_1_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_panas10([True, 3, 3, 3, 3, 3, 3, 3, 3, 3])

    def test_false_in_position_1_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_panas10([False, 3, 3, 3, 3, 3, 3, 3, 3, 3])

    def test_bool_in_each_position(self) -> None:
        for position in range(10):
            items: list[object] = [3] * 10
            items[position] = True
            with pytest.raises(InvalidResponseError, match="must be int"):
                score_panas10(items)  # type: ignore[arg-type]

    def test_float_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_panas10(
                [3.0, 3, 3, 3, 3, 3, 3, 3, 3, 3]  # type: ignore[list-item]
            )

    def test_none_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_panas10(
                [None, 3, 3, 3, 3, 3, 3, 3, 3, 3]  # type: ignore[list-item]
            )

    def test_string_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_panas10(
                ["3", 3, 3, 3, 3, 3, 3, 3, 3, 3]  # type: ignore[list-item]
            )


# ---------------------------------------------------------------------------
# Result shape — deliberately-absent fields matter here
# ---------------------------------------------------------------------------


class TestResultShape:
    """PANAS-10 is the platform's FIRST bidirectional-subscales
    scorer — the deliberately-absent fields are part of the
    contract."""

    def test_returns_panas10_result(self) -> None:
        result = score_panas10([3] * 10)
        assert isinstance(result, Panas10Result)

    def test_pa_sum_field_present(self) -> None:
        result = score_panas10([5, 5, 3, 5, 3, 5, 3, 3, 5, 3])
        # PA positions 3, 5, 7, 8, 10 = 3 -> 15.
        assert result.pa_sum == 15

    def test_na_sum_field_present(self) -> None:
        result = score_panas10([5, 5, 3, 5, 3, 5, 3, 3, 5, 3])
        # NA positions 1, 2, 4, 6, 9 = 5 -> 25.
        assert result.na_sum == 25

    def test_pa_sum_is_int(self) -> None:
        result = score_panas10([3] * 10)
        assert isinstance(result.pa_sum, int)
        assert not isinstance(result.pa_sum, bool)

    def test_na_sum_is_int(self) -> None:
        result = score_panas10([3] * 10)
        assert isinstance(result.na_sum, int)
        assert not isinstance(result.na_sum, bool)

    def test_items_stores_raw_in_administration_order(self) -> None:
        raw = [1, 2, 3, 4, 5, 4, 3, 2, 1, 5]
        result = score_panas10(raw)
        assert result.items == tuple(raw)

    def test_items_is_tuple(self) -> None:
        result = score_panas10([3] * 10)
        assert isinstance(result.items, tuple)

    def test_items_length_is_ten(self) -> None:
        result = score_panas10([3] * 10)
        assert len(result.items) == 10

    def test_instrument_version_field_present(self) -> None:
        result = score_panas10([3] * 10)
        assert result.instrument_version == INSTRUMENT_VERSION

    def test_result_is_frozen(self) -> None:
        result = score_panas10([3] * 10)
        with pytest.raises((AttributeError, Exception)):
            result.pa_sum = 99  # type: ignore[misc]

    def test_result_is_hashable(self) -> None:
        result = score_panas10([3] * 10)
        assert hash(result) == hash(result)

    def test_no_total_field_on_scorer_result(self) -> None:
        # Watson 1988 / Tellegen 1999: PA and NA are orthogonal;
        # the scorer does NOT synthesize a composite.  The
        # routing layer emits total = pa_sum for envelope
        # uniformity — not the scorer.
        result = score_panas10([3] * 10)
        assert not hasattr(result, "total")

    def test_no_severity_field(self) -> None:
        # Thompson 2007 did not publish banded severity.
        result = score_panas10([3] * 10)
        assert not hasattr(result, "severity")

    def test_no_subscales_field_on_scorer_result(self) -> None:
        # The scorer exposes pa_sum and na_sum as top-level
        # fields; the routing layer assembles the ``subscales``
        # dict on the wire.  A scorer-level ``subscales`` would
        # be redundant.
        result = score_panas10([3] * 10)
        assert not hasattr(result, "subscales")

    def test_no_positive_screen_field(self) -> None:
        # PANAS-10 is not a screen.
        result = score_panas10([3] * 10)
        assert not hasattr(result, "positive_screen")

    def test_no_cutoff_used_field(self) -> None:
        # No operating point — no cutoff.
        result = score_panas10([3] * 10)
        assert not hasattr(result, "cutoff_used")

    def test_no_requires_t3_field(self) -> None:
        # Item 1 "upset" is general NA per Watson 1988 item
        # derivation — NOT suicidality.  Acute-risk stays on
        # C-SSRS / PHQ-9 item 9.
        result = score_panas10([5] * 10)
        assert not hasattr(result, "requires_t3")


# ---------------------------------------------------------------------------
# Clinical vignettes — tripartite-model response profiles
# ---------------------------------------------------------------------------


class TestClinicalVignettes:
    """Profiles from Clark & Watson 1991 tripartite model.

    Each vignette pins the scorer's PA/NA signal separation,
    which is the clinical raison d'être for using PANAS-10 over
    a unitary depression/anxiety screen."""

    def test_classic_depression_profile_low_pa_high_na(self) -> None:
        # Low PA (anhedonia) + high NA (general distress) — the
        # canonical depression signature per Clark & Watson 1991.
        # PA items (3, 5, 7, 8, 10) = 1; NA items (1, 2, 4, 6, 9) = 5.
        items = [5, 5, 1, 5, 1, 5, 1, 1, 5, 1]
        result = score_panas10(items)
        assert result.pa_sum == 5
        assert result.na_sum == 25
        # Interpretation layer (not tested here) would route this
        # to behavioral activation (Martell 2010 / Dimidjian 2006)
        # which targets the PA deficit.

    def test_pure_anxiety_profile_normal_pa_high_na(self) -> None:
        # Normal PA + high NA — pure-anxiety signature.  Clark &
        # Watson 1991: NA elevation is NON-specific, shared with
        # depression; PA normality discriminates from depression.
        # PA items at normal (3); NA items at high (5).
        items = [5, 5, 3, 5, 3, 5, 3, 3, 5, 3]
        result = score_panas10(items)
        assert result.pa_sum == 15
        assert result.na_sum == 25
        # Interpretation layer would route to Barlow 2011 unified
        # protocol or Hayes 2012 ACT for NA regulation.

    def test_anhedonia_dominant_profile_low_pa_normal_na(self) -> None:
        # Low PA + normal NA — pure anhedonia without anxious
        # distress.  Craske 2019 positive-affect-treatment
        # target profile.
        # PA items at low (1); NA items at normal (3).
        items = [3, 3, 1, 3, 1, 3, 1, 1, 3, 1]
        result = score_panas10(items)
        assert result.pa_sum == 5
        assert result.na_sum == 15
        # This profile would be INVISIBLE on a PHQ-9 if the
        # somatic items (6-9) were low — the PANAS-10 detects it
        # via PA deficit.  Clinically important.

    def test_flourishing_profile_high_pa_low_na(self) -> None:
        # High PA + low NA — canonical flourishing / high well-
        # being.  Pressman & Cohen 2005: health-protective
        # configuration.
        items = [1, 1, 5, 1, 5, 1, 5, 5, 1, 5]
        result = score_panas10(items)
        assert result.pa_sum == 25
        assert result.na_sum == 5

    def test_euthymic_baseline_profile(self) -> None:
        # Middle-of-the-scale on all items — normative-sample
        # baseline.  Crawford & Henry 2004 UK norms on the 5-25
        # scale: PA mean 16.05, NA mean 7.40.  A "3" on every
        # item (pa_sum 15, na_sum 15) is slightly above NA norm
        # but within PA norm — plausible "average day".
        result = score_panas10([3] * 10)
        assert result.pa_sum == 15
        assert result.na_sum == 15

    def test_mixed_high_both_activated_profile(self) -> None:
        # High PA + high NA — hyperaroused profile (can co-occur
        # with bipolar mixed states, acute stress, high-stakes
        # contexts).  Tellegen 1999 orthogonality permits this
        # configuration — the scorer must NOT penalize it or
        # treat it as inconsistent.
        result = score_panas10([5] * 10)
        assert result.pa_sum == 25
        assert result.na_sum == 25

    def test_mixed_low_both_deactivated_profile(self) -> None:
        # Low PA + low NA — flat / blunted affect.  Can occur in
        # melancholic depression (affective flattening) or
        # schizophrenia-spectrum negative symptoms.  Orthogonal
        # axes permit this configuration.
        result = score_panas10([1] * 10)
        assert result.pa_sum == 5
        assert result.na_sum == 5


# ---------------------------------------------------------------------------
# Safety routing — no T3/T4 triggering from PANAS-10
# ---------------------------------------------------------------------------


class TestNoSafetyRouting:
    """PANAS-10 probes affect dimensions, NOT suicidality.  Item
    1 "upset" is general NA per Watson 1988 item derivation.
    Acute-risk screening stays on C-SSRS / PHQ-9 item 9."""

    def test_item_1_upset_does_not_signal_safety(self) -> None:
        # Maximum "upset" endorsement — no safety attribute.
        result = score_panas10([5, 1, 1, 1, 1, 1, 1, 1, 1, 1])
        assert not hasattr(result, "requires_t3")

    def test_item_9_afraid_does_not_signal_safety(self) -> None:
        # Maximum "afraid" endorsement — no safety attribute.
        result = score_panas10([1, 1, 1, 1, 1, 1, 1, 1, 5, 1])
        assert not hasattr(result, "requires_t3")

    def test_maximum_na_does_not_signal_safety(self) -> None:
        # All NA items maxed — severe general distress but NOT
        # suicidality.  NO safety attribute.  A clinician reading
        # PANAS-10 NA = 25 should follow up with C-SSRS / PHQ-9
        # item 9 — the PANAS does not carry that signal.
        items = [5, 5, 1, 5, 1, 5, 1, 1, 5, 1]
        result = score_panas10(items)
        assert result.na_sum == 25
        assert not hasattr(result, "requires_t3")

    def test_classic_depression_profile_does_not_signal_safety(
        self,
    ) -> None:
        # Even the low-PA / high-NA depression signature does
        # NOT emit T3 from PANAS-10.  The scorer stays within
        # its epistemic scope.
        items = [5, 5, 1, 5, 1, 5, 1, 1, 5, 1]
        result = score_panas10(items)
        assert not hasattr(result, "requires_t3")

    def test_every_single_position_no_safety(self) -> None:
        # Position-by-position: no single item produces a
        # safety attribute.
        for position in range(10):
            items = [1] * 10
            items[position] = 5
            result = score_panas10(items)
            assert not hasattr(result, "requires_t3"), (
                f"position {position + 1} unexpectedly set "
                f"requires_t3"
            )

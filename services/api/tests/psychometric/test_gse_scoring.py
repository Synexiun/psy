"""Scorer-layer tests for GSE (Schwarzer & Jerusalem 1995)."""

from __future__ import annotations

import pytest

from discipline.psychometric.scoring.gse import (
    GSE_REVERSE_ITEMS,
    GseResult,
    INSTRUMENT_VERSION,
    ITEM_COUNT,
    ITEM_MAX,
    ITEM_MIN,
    InvalidResponseError,
    score_gse,
)


class TestConstants:
    """Pin the Schwarzer & Jerusalem 1995 structural constants.

    The constants are part of the instrument's clinical identity:
    10 items, 1-4 Likert, NO reverse-keyed items.  Changing any of
    these without a clinical QA re-validation would invalidate the
    scorer's conformance to Schwarzer & Jerusalem 1995 and break
    Scholz 2002 cross-cultural measurement invariance.
    """

    def test_item_count_is_10(self) -> None:
        assert ITEM_COUNT == 10

    def test_likert_minimum_is_1(self) -> None:
        assert ITEM_MIN == 1

    def test_likert_maximum_is_4(self) -> None:
        assert ITEM_MAX == 4

    def test_no_reverse_items(self) -> None:
        assert GSE_REVERSE_ITEMS == ()

    def test_reverse_items_is_tuple(self) -> None:
        assert isinstance(GSE_REVERSE_ITEMS, tuple)

    def test_instrument_version_pinned(self) -> None:
        assert INSTRUMENT_VERSION == "gse-1.0.0"


class TestTotalCorrectness:
    """Verify straight-sum arithmetic across the 10-40 range."""

    def test_all_ones_yields_minimum(self) -> None:
        result = score_gse([1] * 10)
        assert result.total == 10

    def test_all_fours_yields_maximum(self) -> None:
        result = score_gse([4] * 10)
        assert result.total == 40

    def test_all_twos_yields_20(self) -> None:
        result = score_gse([2] * 10)
        assert result.total == 20

    def test_all_threes_yields_30(self) -> None:
        result = score_gse([3] * 10)
        assert result.total == 30

    def test_mixed_ramp_sums_correctly(self) -> None:
        # 1+1+2+2+3+3+4+4+2+3 = 25
        result = score_gse([1, 1, 2, 2, 3, 3, 4, 4, 2, 3])
        assert result.total == 25

    def test_total_is_int_not_float(self) -> None:
        result = score_gse([1, 2, 3, 4, 1, 2, 3, 4, 1, 2])
        assert isinstance(result.total, int)

    def test_total_with_single_four_rest_one(self) -> None:
        # 1*9 + 4 = 13
        result = score_gse([4, 1, 1, 1, 1, 1, 1, 1, 1, 1])
        assert result.total == 13

    def test_total_with_single_one_rest_four(self) -> None:
        # 4*9 + 1 = 37
        result = score_gse([1, 4, 4, 4, 4, 4, 4, 4, 4, 4])
        assert result.total == 37


class TestSeverityAlwaysContinuous:
    """GSE envelope is always ``severity='continuous'``.

    Schwarzer 1995 did not publish severity bands; Scholz 2002 norms
    (mean ≈ 29, SD ≈ 4) and Luszczynska 2005 meta-analytic norms
    stay at the clinician-UI renderer layer per CLAUDE.md
    non-negotiable #9 ("Don't hand-roll severity thresholds").
    """

    @pytest.mark.parametrize("v", [1, 2, 3, 4])
    def test_uniform_response_is_continuous(self, v: int) -> None:
        result = score_gse([v] * 10)
        assert result.severity == "continuous"

    def test_minimum_total_is_continuous(self) -> None:
        # 10 is the Scholz 2002 descriptive floor.
        assert score_gse([1] * 10).severity == "continuous"

    def test_maximum_total_is_continuous(self) -> None:
        # 40 is the Scholz 2002 descriptive ceiling.
        assert score_gse([4] * 10).severity == "continuous"

    def test_near_normative_mean_is_continuous(self) -> None:
        # 29 matches Scholz 2002 normative mean on European n=4,988.
        # Still must render "continuous" — norms stay at UI layer.
        responses = [3, 3, 3, 3, 3, 3, 3, 3, 3, 2]
        result = score_gse(responses)
        assert result.total == 29
        assert result.severity == "continuous"

    def test_severity_not_none_or_empty(self) -> None:
        result = score_gse([2] * 10)
        assert result.severity
        assert result.severity != ""


class TestNoReverseKeying:
    """All 10 Schwarzer & Jerusalem 1995 items are positively worded.

    Pass-through invariant: a single high response at position N must
    increase the total by the same amount regardless of position N.
    If any position were reverse-keyed, that position would DECREASE
    the total relative to baseline.
    """

    @pytest.mark.parametrize("pos_1_indexed", list(range(1, 11)))
    def test_single_four_at_position_increases_total_uniformly(
        self, pos_1_indexed: int
    ) -> None:
        # Baseline: all 1s → total 10.
        # Flip position N to 4 → total should increase by 3 (4-1) at
        # EVERY position.  Any reverse-keyed position would violate.
        responses = [1] * 10
        responses[pos_1_indexed - 1] = 4
        result = score_gse(responses)
        assert result.total == 10 + 3

    @pytest.mark.parametrize("pos_1_indexed", list(range(1, 11)))
    def test_single_one_at_position_decreases_total_uniformly(
        self, pos_1_indexed: int
    ) -> None:
        # Baseline: all 4s → total 40.
        # Flip position N to 1 → total should decrease by 3 at every
        # position.  Any reverse-keyed position would violate.
        responses = [4] * 10
        responses[pos_1_indexed - 1] = 1
        result = score_gse(responses)
        assert result.total == 40 - 3


class TestAcquiescenceSignature:
    """The acquiescence-pattern gap pins Schwarzer's all-positive
    wording.

    With all 10 items worded "higher = more self-efficacy",
    acquiescent-responders (always-agree) score MAXIMUM and
    contrarian-responders (always-disagree) score MINIMUM — a
    100%-of-range gap.  If any item were reverse-keyed, the two
    patterns would land nearer the midpoint and the gap would
    shrink.  Schwarzer & Jerusalem 1995 reported α=0.76-0.90
    indicating acquiescence was NOT a dominant bias — but the
    scorer must faithfully reproduce the uniform-agreement gap
    as a structural invariant.
    """

    def test_uniform_agreement_vs_disagreement_full_gap(self) -> None:
        always_agree = score_gse([4] * 10)
        always_disagree = score_gse([1] * 10)
        gap = always_agree.total - always_disagree.total
        # 10 items × (4-1) = 30 = 100% of the 10-40 range
        assert gap == 30

    @pytest.mark.parametrize("v", [1, 2, 3, 4])
    def test_linear_uniform_response_produces_linear_total(
        self, v: int
    ) -> None:
        # With 10 items × v, an all-positive scale produces linear
        # mapping between response value and total.
        result = score_gse([v] * 10)
        assert result.total == 10 * v


class TestItemsPreserveRaw:
    """GSE has no reverse-keying → ``items`` should equal inputs."""

    def test_items_field_preserves_input_order(self) -> None:
        responses = [1, 2, 3, 4, 3, 2, 1, 4, 2, 3]
        result = score_gse(responses)
        assert result.items == (1, 2, 3, 4, 3, 2, 1, 4, 2, 3)

    def test_items_field_is_tuple(self) -> None:
        result = score_gse([2] * 10)
        assert isinstance(result.items, tuple)

    def test_items_field_length_is_10(self) -> None:
        result = score_gse([3] * 10)
        assert len(result.items) == 10

    def test_items_all_ints(self) -> None:
        result = score_gse([1, 2, 3, 4, 1, 2, 3, 4, 1, 2])
        for item in result.items:
            assert isinstance(item, int)

    def test_items_sum_equals_total(self) -> None:
        # Structural invariant: no reverse-keying means raw sum
        # equals the total.  Breaks if a reverse-key is introduced
        # without updating the scorer logic.
        responses = [2, 3, 4, 1, 3, 2, 4, 1, 2, 3]
        result = score_gse(responses)
        assert sum(result.items) == result.total


class TestItemCountValidation:
    """Schwarzer 1995 pinned the 10-item structure — reject others."""

    @pytest.mark.parametrize(
        "bad_count", [0, 1, 2, 5, 7, 9, 11, 12, 20]
    )
    def test_wrong_count_raises(self, bad_count: int) -> None:
        with pytest.raises(InvalidResponseError) as exc:
            score_gse([2] * bad_count)
        assert "10 items" in str(exc.value)
        assert f"got {bad_count}" in str(exc.value)

    def test_empty_list_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            score_gse([])


class TestItemValueValidation:
    """Reject out-of-range values — Schwarzer 1995 pinned 1-4 scale."""

    def test_zero_rejected(self) -> None:
        responses = [2] * 10
        responses[0] = 0
        with pytest.raises(InvalidResponseError) as exc:
            score_gse(responses)
        assert "1-4" in str(exc.value)

    def test_five_rejected(self) -> None:
        responses = [2] * 10
        responses[5] = 5
        with pytest.raises(InvalidResponseError) as exc:
            score_gse(responses)
        assert "1-4" in str(exc.value)

    def test_negative_rejected(self) -> None:
        responses = [2] * 10
        responses[9] = -1
        with pytest.raises(InvalidResponseError):
            score_gse(responses)

    def test_large_positive_rejected(self) -> None:
        responses = [2] * 10
        responses[3] = 99
        with pytest.raises(InvalidResponseError):
            score_gse(responses)

    def test_error_names_item_position(self) -> None:
        # Item 7 is "I can remain calm when facing difficulties" —
        # the error should name the item so a clinician can
        # identify which Schwarzer 1995 item was violated.
        responses = [2] * 10
        responses[6] = 9  # Item 7 (1-indexed)
        with pytest.raises(InvalidResponseError) as exc:
            score_gse(responses)
        assert "item 7" in str(exc.value)


class TestItemTypeValidation:
    """Reject non-int types.  Bool rejection per CLAUDE.md invariant.

    Python's ``bool is int`` ancestry means ``True`` / ``False``
    silently pass an ``isinstance(value, int)`` check.  The scorer
    explicitly rejects bools BEFORE the int check to prevent a
    client-side ``true`` being treated as item response "1".
    """

    def test_true_rejected_before_range_check(self) -> None:
        # True coerces to 1 (a valid Likert response), but the bool
        # check must fire FIRST per CLAUDE.md standing rule.
        responses: list[object] = [2] * 10
        responses[0] = True
        with pytest.raises(InvalidResponseError) as exc:
            score_gse(responses)  # type: ignore[arg-type]
        assert "int" in str(exc.value)

    def test_false_rejected_before_range_check(self) -> None:
        # False coerces to 0 (already out-of-range), but the bool
        # check must fire FIRST so the error message cites "int"
        # not "1-4".
        responses: list[object] = [2] * 10
        responses[4] = False
        with pytest.raises(InvalidResponseError) as exc:
            score_gse(responses)  # type: ignore[arg-type]
        assert "int" in str(exc.value)

    def test_float_rejected(self) -> None:
        responses: list[object] = [2] * 10
        responses[3] = 3.5
        with pytest.raises(InvalidResponseError) as exc:
            score_gse(responses)  # type: ignore[arg-type]
        assert "int" in str(exc.value)

    def test_string_rejected_at_scorer(self) -> None:
        # Scorer-level string rejection — at the HTTP wire, Pydantic
        # lax-mode coercion converts numeric strings to ints first
        # (documented in TestGseRouting), but the scorer itself
        # rejects strings because the scorer has no coercion layer.
        responses: list[object] = [2] * 10
        responses[7] = "3"
        with pytest.raises(InvalidResponseError) as exc:
            score_gse(responses)  # type: ignore[arg-type]
        assert "int" in str(exc.value)

    def test_none_rejected(self) -> None:
        responses: list[object] = [2] * 10
        responses[0] = None
        with pytest.raises(InvalidResponseError) as exc:
            score_gse(responses)  # type: ignore[arg-type]
        assert "int" in str(exc.value)

    def test_float_4_0_rejected_despite_value_equality(self) -> None:
        # 4.0 == 4 is True, but isinstance(4.0, int) is False.
        # The scorer must reject 4.0 rather than silently coerce.
        responses: list[object] = [2] * 10
        responses[0] = 4.0
        with pytest.raises(InvalidResponseError):
            score_gse(responses)  # type: ignore[arg-type]


class TestInvalidResponseErrorIdentity:
    """InvalidResponseError is the platform's scorer-error sentinel."""

    def test_is_subclass_of_value_error(self) -> None:
        assert issubclass(InvalidResponseError, ValueError)

    def test_catchable_as_value_error(self) -> None:
        with pytest.raises(ValueError):
            score_gse([1] * 9)


class TestResultTyping:
    """Verify the GseResult dataclass contract."""

    def test_result_is_frozen(self) -> None:
        result = score_gse([2] * 10)
        with pytest.raises(Exception):
            result.total = 999  # type: ignore[misc]

    def test_result_has_no_subscales_attr(self) -> None:
        # Scholz 2002 unidimensional factor structure → no facet
        # decomposition at the scorer layer.
        result = score_gse([2] * 10)
        assert not hasattr(result, "subscales")

    def test_result_has_no_positive_screen_attr(self) -> None:
        # GSE is not a screener.
        result = score_gse([2] * 10)
        assert not hasattr(result, "positive_screen")

    def test_result_has_no_requires_t3_attr(self) -> None:
        # No suicidality probe → no scorer-layer T3 flag.
        result = score_gse([2] * 10)
        assert not hasattr(result, "requires_t3")

    def test_result_has_no_scaled_score_attr(self) -> None:
        # GSE total is the published score — no MAAS-style means.
        result = score_gse([2] * 10)
        assert not hasattr(result, "scaled_score")

    def test_result_has_no_cutoff_attr(self) -> None:
        result = score_gse([2] * 10)
        assert not hasattr(result, "cutoff_used")

    def test_result_instrument_version_is_pinned(self) -> None:
        result = score_gse([2] * 10)
        assert result.instrument_version == INSTRUMENT_VERSION


class TestClinicalVignettes:
    """Vignettes that match published Marlatt / Bandura / Beck profiles.

    Each vignette pins a *published-literature-matched* profile
    against the scorer output.  The goal is not to verify
    interventions (those live at the clinician-UI layer) but to
    demonstrate that the scorer's output *structurally* supports the
    intervention matrix described in the module docstring.
    """

    def test_pervasive_low_confidence_profile(self) -> None:
        # Bandura 1997 §3 "pervasive low efficacy" profile — mostly
        # 1s with a scattered 2, mirroring the DTCQ-8-low +
        # GSE-low pairing that indicates mastery-experience-first
        # intervention sequencing (not high-risk-situation exposure).
        responses = [1, 1, 2, 1, 1, 1, 1, 2, 1, 1]
        result = score_gse(responses)
        assert result.total == 12  # deep in the Scholz 2002 low tail
        assert result.severity == "continuous"

    def test_competence_gap_profile(self) -> None:
        # Marlatt 2005 high-functioning-early-recovery profile:
        # GSE high + DTCQ-8 low.  Clients who are broadly competent
        # but substance-situation-specifically depleted.  GSE total
        # near normative mean.
        responses = [3, 3, 3, 3, 3, 3, 3, 3, 3, 3]
        result = score_gse(responses)
        assert result.total == 30
        assert result.severity == "continuous"

    def test_ave_pathway_profile_gse_low_brs_low(self) -> None:
        # Marlatt 1985 abstinence-violation-effect (AVE) risk profile:
        # GSE-low + BRS-low.  Cognitive-expectation deficit AND
        # behavioral-recovery deficit → lapse cascades into relapse
        # via AVE pathway.  Priority: parallel self-efficacy and
        # resilience skills (Reivich 2002 PRP).
        responses = [1, 2, 1, 1, 2, 1, 1, 2, 1, 1]
        result = score_gse(responses)
        assert result.total == 13
        assert result.severity == "continuous"

    def test_depressive_triad_profile_gse_low_lot_r_low(self) -> None:
        # Beck 1979 cognitive triad convergence: GSE-low (self-
        # competence deficit) + LOT-R low (future-pessimism).
        # Clinical-UI indication: CBT-D (Beck 1979; Hollon 2005).
        # Still "continuous" at the scorer layer.
        responses = [1, 1, 1, 2, 1, 1, 1, 1, 2, 1]
        result = score_gse(responses)
        assert result.total == 12
        assert result.severity == "continuous"

    def test_overwhelmed_and_depleted_profile(self) -> None:
        # GSE-low + SWLS-low + PSS-10-high profile: the Cohen-Wills
        # 1985 buffering-capacity-breakdown + global-dissatisfaction
        # picture.  Priority intervention: immediate stress
        # regulation + graduated mastery; life-evaluation later.
        responses = [1, 2, 2, 1, 1, 2, 1, 2, 1, 2]
        result = score_gse(responses)
        assert result.total == 15
        assert result.severity == "continuous"

    def test_full_self_efficacy_profile(self) -> None:
        # GSE-high + DTCQ-8-high: full self-efficacy.  Maintenance-
        # oriented interventions.  Total near Scholz 2002 ceiling.
        responses = [4, 4, 4, 4, 4, 4, 4, 4, 4, 4]
        result = score_gse(responses)
        assert result.total == 40
        assert result.severity == "continuous"

    def test_baseline_followup_trajectory_5pt_delta(self) -> None:
        # Jacobson & Truax 1991 RCI machinery at the trajectory
        # layer: from Scholz 2002 α=0.86, SD≈5 → RCI ≈ 5 points.
        # A 5-point GSE delta is clinically meaningful in Marlatt-
        # style relapse-prevention.  Scorer output supports the
        # delta computation downstream.
        baseline = score_gse([2, 2, 2, 2, 2, 2, 2, 2, 2, 2])
        followup = score_gse([3, 2, 3, 2, 3, 2, 2, 3, 2, 3])
        assert followup.total - baseline.total == 5
        # Both still "continuous" — severity bands do not encode
        # change; RCI does.
        assert baseline.severity == "continuous"
        assert followup.severity == "continuous"

    def test_minimum_total_produces_10_not_0(self) -> None:
        # Structural invariant: the minimum possible total is 10
        # (10 × 1), not 0.  A bug that allowed 0 responses would
        # produce 0 totals and contaminate Scholz 2002 descriptive
        # distribution comparisons.
        result = score_gse([1] * 10)
        assert result.total == 10
        assert result.total >= ITEM_COUNT * ITEM_MIN

    def test_maximum_total_produces_40_not_above(self) -> None:
        # Structural invariant: the maximum possible total is 40
        # (10 × 4), not higher.  Would indicate out-of-range
        # acceptance.
        result = score_gse([4] * 10)
        assert result.total == 40
        assert result.total <= ITEM_COUNT * ITEM_MAX


class TestResultInstanceShape:
    """The GseResult instance carries exactly the declared fields."""

    def test_result_is_gse_result(self) -> None:
        result = score_gse([2] * 10)
        assert isinstance(result, GseResult)

    def test_result_total_is_int(self) -> None:
        result = score_gse([2] * 10)
        assert isinstance(result.total, int)

    def test_result_severity_is_str(self) -> None:
        result = score_gse([2] * 10)
        assert isinstance(result.severity, str)

    def test_result_items_is_tuple_of_ints(self) -> None:
        result = score_gse([2] * 10)
        assert isinstance(result.items, tuple)
        for item in result.items:
            assert isinstance(item, int)

    def test_result_instrument_version_is_str(self) -> None:
        result = score_gse([2] * 10)
        assert isinstance(result.instrument_version, str)

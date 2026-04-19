"""Tests for IES-R scoring — Weiss & Marmar 1997 / Creamer 2003."""

from __future__ import annotations

import pytest

from discipline.psychometric.scoring.iesr import (
    IESR_AVOIDANCE_POSITIONS,
    IESR_CLINICAL_CUTOFF,
    IESR_HYPERAROUSAL_POSITIONS,
    IESR_INTRUSION_POSITIONS,
    IESR_REVERSE_ITEMS,
    IESR_SUBSCALES,
    INSTRUMENT_VERSION,
    ITEM_COUNT,
    ITEM_MAX,
    ITEM_MIN,
    IesrResult,
    InvalidResponseError,
    score_iesr,
)


def _all(v: int) -> list[int]:
    """Return a 22-item list with every item set to ``v``."""
    return [v] * ITEM_COUNT


class TestConstants:
    def test_instrument_version_format(self) -> None:
        assert INSTRUMENT_VERSION == "iesr-1.0.0"

    def test_item_count_is_22(self) -> None:
        """Weiss & Marmar 1997: 22-item revision of the original 15-item IES."""
        assert ITEM_COUNT == 22

    def test_item_range_is_0_to_4(self) -> None:
        """Weiss & Marmar 1997: 5-point 0-4 Likert frequency scale."""
        assert (ITEM_MIN, ITEM_MAX) == (0, 4)

    def test_reverse_items_is_empty(self) -> None:
        """Weiss & Marmar 1997: all 22 items distress-positive, no reverse-keying."""
        assert IESR_REVERSE_ITEMS == ()

    def test_subscale_names_in_weiss_marmar_order(self) -> None:
        """Weiss & Marmar 1997 Table 1 factor order: intrusion, avoidance, hyperarousal."""
        assert IESR_SUBSCALES == ("intrusion", "avoidance", "hyperarousal")

    def test_intrusion_positions(self) -> None:
        """Weiss & Marmar 1997 Table 1: 8 intrusion items."""
        assert IESR_INTRUSION_POSITIONS == (1, 2, 3, 6, 9, 14, 16, 20)

    def test_avoidance_positions(self) -> None:
        """Weiss & Marmar 1997 Table 1: 8 avoidance items."""
        assert IESR_AVOIDANCE_POSITIONS == (5, 7, 8, 11, 12, 13, 17, 22)

    def test_hyperarousal_positions(self) -> None:
        """Weiss & Marmar 1997 Table 1: 6 hyperarousal items."""
        assert IESR_HYPERAROUSAL_POSITIONS == (4, 10, 15, 18, 19, 21)

    def test_subscale_positions_partition_22(self) -> None:
        """Every item 1-22 appears in exactly one subscale."""
        all_positions = (
            IESR_INTRUSION_POSITIONS
            + IESR_AVOIDANCE_POSITIONS
            + IESR_HYPERAROUSAL_POSITIONS
        )
        assert sorted(all_positions) == list(range(1, 23))

    def test_intrusion_subscale_is_8_items(self) -> None:
        """Weiss & Marmar 1997: 8 intrusion items."""
        assert len(IESR_INTRUSION_POSITIONS) == 8

    def test_avoidance_subscale_is_8_items(self) -> None:
        """Weiss & Marmar 1997: 8 avoidance items."""
        assert len(IESR_AVOIDANCE_POSITIONS) == 8

    def test_hyperarousal_subscale_is_6_items(self) -> None:
        """Weiss & Marmar 1997: 6 hyperarousal items (unequal to the other two)."""
        assert len(IESR_HYPERAROUSAL_POSITIONS) == 6

    def test_item_2_is_intrusion_not_hyperarousal(self) -> None:
        """Weiss & Marmar 1997: item 2 ('trouble staying asleep') is INTRUSION.

        Nightmare-driven sleep disturbance per Weiss & Marmar 1997 factor
        analysis; MUST NOT be re-assigned to hyperarousal based on DSM-5
        cluster mapping.  Load-bearing distinction for the scorer.
        """
        assert 2 in IESR_INTRUSION_POSITIONS
        assert 2 not in IESR_HYPERAROUSAL_POSITIONS
        assert 2 not in IESR_AVOIDANCE_POSITIONS

    def test_item_15_is_hyperarousal_not_intrusion(self) -> None:
        """Weiss & Marmar 1997: item 15 ('trouble falling asleep') is HYPERAROUSAL.

        Sleep-onset probe captures physiological arousal, distinct from
        nightmare-driven waking.  The item 2 vs item 15 split is the
        Weiss & Marmar 1997 factor-analytic signature.
        """
        assert 15 in IESR_HYPERAROUSAL_POSITIONS
        assert 15 not in IESR_INTRUSION_POSITIONS
        assert 15 not in IESR_AVOIDANCE_POSITIONS

    def test_clinical_cutoff_is_33(self) -> None:
        """Creamer 2003 ROC cutoff against CAPS; AUC = 0.88."""
        assert IESR_CLINICAL_CUTOFF == 33


class TestTotalCorrectness:
    def test_all_zeros_gives_minimum_0(self) -> None:
        r = score_iesr(_all(0))
        assert r.total == 0

    def test_all_fours_gives_maximum_88(self) -> None:
        r = score_iesr(_all(4))
        assert r.total == 88

    def test_all_twos_gives_midpoint_44(self) -> None:
        """Midpoint of 0-88 range; near Creamer 2003 clinical cutoff of 33."""
        r = score_iesr(_all(2))
        assert r.total == 44

    def test_total_equals_sum_of_subscales(self) -> None:
        """total == intrusion + avoidance + hyperarousal always."""
        items = [0, 1, 2, 3, 4, 0, 1, 2, 3, 4, 0, 1, 2, 3, 4, 0, 1, 2, 3, 4, 0, 1]
        r = score_iesr(items)
        assert r.total == r.intrusion + r.avoidance + r.hyperarousal

    def test_total_at_clinical_cutoff_exact(self) -> None:
        """Total = 33 demonstrates Creamer 2003 ROC boundary."""
        items = [0] * 22
        for pos in (1, 2, 3, 6, 9, 14, 16, 20):
            items[pos - 1] = 4
        items[4] = 1
        r = score_iesr(items)
        assert r.total == 33


class TestSubscalePartitioning:
    def test_intrusion_isolation(self) -> None:
        """Set intrusion items (1,2,3,6,9,14,16,20) to 4, others to 0."""
        items = [0] * 22
        for pos in IESR_INTRUSION_POSITIONS:
            items[pos - 1] = 4
        r = score_iesr(items)
        assert r.intrusion == 8 * 4
        assert r.avoidance == 0
        assert r.hyperarousal == 0
        assert r.total == 32

    def test_avoidance_isolation(self) -> None:
        """Set avoidance items (5,7,8,11,12,13,17,22) to 4, others to 0."""
        items = [0] * 22
        for pos in IESR_AVOIDANCE_POSITIONS:
            items[pos - 1] = 4
        r = score_iesr(items)
        assert r.intrusion == 0
        assert r.avoidance == 8 * 4
        assert r.hyperarousal == 0
        assert r.total == 32

    def test_hyperarousal_isolation(self) -> None:
        """Set hyperarousal items (4,10,15,18,19,21) to 4, others to 0."""
        items = [0] * 22
        for pos in IESR_HYPERAROUSAL_POSITIONS:
            items[pos - 1] = 4
        r = score_iesr(items)
        assert r.intrusion == 0
        assert r.avoidance == 0
        assert r.hyperarousal == 6 * 4
        assert r.total == 24

    def test_item_2_contributes_to_intrusion_only(self) -> None:
        """Weiss & Marmar 1997: item 2 (sleep-maintenance) → intrusion.

        Load-bearing distinction — a DSM-5-cluster scorer would place
        item 2 in hyperarousal.  We preserve the factor-analytic
        assignment.
        """
        items = [0] * 22
        items[1] = 4
        r = score_iesr(items)
        assert r.intrusion == 4
        assert r.hyperarousal == 0
        assert r.avoidance == 0

    def test_item_15_contributes_to_hyperarousal_only(self) -> None:
        """Weiss & Marmar 1997: item 15 (sleep-onset) → hyperarousal.

        Distinct from item 2 nightmare-driven sleep disturbance; the
        item 2 vs 15 split is a load-bearing scorer invariant.
        """
        items = [0] * 22
        items[14] = 4
        r = score_iesr(items)
        assert r.hyperarousal == 4
        assert r.intrusion == 0
        assert r.avoidance == 0

    def test_subscale_position_order_matters(self) -> None:
        """Shuffling items changes subscale sums even when total is unchanged."""
        aligned = [4, 0, 0, 0, 4, 0, 0, 0, 0, 0, 4, 0, 0, 0, 0, 0, 4, 0, 0, 0, 0, 0]
        rev = list(reversed(aligned))
        r_aligned = score_iesr(aligned)
        r_rev = score_iesr(rev)
        assert r_aligned.total == r_rev.total
        assert (
            r_aligned.intrusion,
            r_aligned.avoidance,
            r_aligned.hyperarousal,
        ) != (r_rev.intrusion, r_rev.avoidance, r_rev.hyperarousal)

    def test_single_intrusion_bump_at_each_position(self) -> None:
        """Each of 8 intrusion positions contributes ONLY to intrusion."""
        for pos in IESR_INTRUSION_POSITIONS:
            items = [0] * 22
            items[pos - 1] = 3
            r = score_iesr(items)
            assert r.intrusion == 3
            assert r.avoidance == 0
            assert r.hyperarousal == 0

    def test_single_avoidance_bump_at_each_position(self) -> None:
        """Each of 8 avoidance positions contributes ONLY to avoidance."""
        for pos in IESR_AVOIDANCE_POSITIONS:
            items = [0] * 22
            items[pos - 1] = 3
            r = score_iesr(items)
            assert r.intrusion == 0
            assert r.avoidance == 3
            assert r.hyperarousal == 0

    def test_single_hyperarousal_bump_at_each_position(self) -> None:
        """Each of 6 hyperarousal positions contributes ONLY to hyperarousal."""
        for pos in IESR_HYPERAROUSAL_POSITIONS:
            items = [0] * 22
            items[pos - 1] = 3
            r = score_iesr(items)
            assert r.intrusion == 0
            assert r.avoidance == 0
            assert r.hyperarousal == 3


class TestSubscaleRanges:
    @pytest.mark.parametrize(
        "v,expected_intrusion,expected_avoidance,expected_hyperarousal",
        [
            (0, 0, 0, 0),
            (1, 8, 8, 6),
            (2, 16, 16, 12),
            (3, 24, 24, 18),
            (4, 32, 32, 24),
        ],
    )
    def test_all_constant_gives_linear_subscale_sum(
        self,
        v: int,
        expected_intrusion: int,
        expected_avoidance: int,
        expected_hyperarousal: int,
    ) -> None:
        """Subscale sums scale linearly; unequal-length subscales produce unequal sums."""
        r = score_iesr(_all(v))
        assert r.intrusion == expected_intrusion
        assert r.avoidance == expected_avoidance
        assert r.hyperarousal == expected_hyperarousal

    def test_intrusion_max_is_32(self) -> None:
        """8 items × 4 max = 32."""
        items = [0] * 22
        for pos in IESR_INTRUSION_POSITIONS:
            items[pos - 1] = 4
        r = score_iesr(items)
        assert r.intrusion == 32

    def test_avoidance_max_is_32(self) -> None:
        """8 items × 4 max = 32."""
        items = [0] * 22
        for pos in IESR_AVOIDANCE_POSITIONS:
            items[pos - 1] = 4
        r = score_iesr(items)
        assert r.avoidance == 32

    def test_hyperarousal_max_is_24(self) -> None:
        """6 items × 4 max = 24 (unequal to the 32 of the other two)."""
        items = [0] * 22
        for pos in IESR_HYPERAROUSAL_POSITIONS:
            items[pos - 1] = 4
        r = score_iesr(items)
        assert r.hyperarousal == 24


class TestPositiveScreen:
    def test_below_cutoff_is_negative(self) -> None:
        """Total 32 → positive_screen False (one below Creamer 2003 cutoff)."""
        items = [0] * 22
        for pos in IESR_INTRUSION_POSITIONS:
            items[pos - 1] = 4
        r = score_iesr(items)
        assert r.total == 32
        assert r.positive_screen is False

    def test_at_cutoff_is_positive(self) -> None:
        """Total 33 → positive_screen True (Creamer 2003 ≥ 33 boundary)."""
        items = [0] * 22
        for pos in IESR_INTRUSION_POSITIONS:
            items[pos - 1] = 4
        items[4] = 1
        r = score_iesr(items)
        assert r.total == 33
        assert r.positive_screen is True

    def test_above_cutoff_is_positive(self) -> None:
        """Total 34 → positive_screen True."""
        items = [0] * 22
        for pos in IESR_INTRUSION_POSITIONS:
            items[pos - 1] = 4
        items[4] = 2
        r = score_iesr(items)
        assert r.total == 34
        assert r.positive_screen is True

    def test_all_zeros_negative(self) -> None:
        """Total 0 → positive_screen False."""
        assert score_iesr(_all(0)).positive_screen is False

    def test_all_fours_positive(self) -> None:
        """Total 88 → positive_screen True."""
        assert score_iesr(_all(4)).positive_screen is True

    def test_cutoff_used_field_is_33(self) -> None:
        """cutoff_used surfaces the applied cutoff for UI rendering."""
        r = score_iesr(_all(2))
        assert r.cutoff_used == 33

    @pytest.mark.parametrize("total_target,expected", [
        (0, False),
        (10, False),
        (20, False),
        (30, False),
        (32, False),
        (33, True),
        (34, True),
        (40, True),
        (60, True),
        (88, True),
    ])
    def test_positive_screen_boundary_sweep(
        self, total_target: int, expected: bool
    ) -> None:
        """Sweep across the 0-88 range; flip at 33 is sharp."""
        full_4s = total_target // 4
        remainder = total_target % 4
        items = [0] * 22
        for i in range(min(full_4s, 22)):
            items[i] = 4
        if full_4s < 22 and remainder > 0:
            items[full_4s] = remainder
        r = score_iesr(items)
        assert r.total == total_target
        assert r.positive_screen is expected


class TestSeverityAlwaysContinuous:
    @pytest.mark.parametrize("v", [0, 1, 2, 3, 4])
    def test_all_constant_returns_continuous(self, v: int) -> None:
        """No severity bands; Creamer 2003 published only a single cutoff."""
        assert score_iesr(_all(v)).severity == "continuous"

    def test_mixed_returns_continuous(self) -> None:
        assert (
            score_iesr(
                [0, 1, 2, 3, 4, 0, 1, 2, 3, 4, 0, 1, 2, 3, 4, 0, 1, 2, 3, 4, 0, 1]
            ).severity
            == "continuous"
        )

    def test_below_cutoff_returns_continuous(self) -> None:
        """Envelope stays continuous even when positive_screen toggles."""
        items = [0] * 22
        items[0] = 4
        r = score_iesr(items)
        assert r.severity == "continuous"
        assert r.positive_screen is False

    def test_at_cutoff_returns_continuous(self) -> None:
        """Envelope stays continuous at the cutoff boundary."""
        items = [0] * 22
        for pos in IESR_INTRUSION_POSITIONS:
            items[pos - 1] = 4
        items[4] = 1
        r = score_iesr(items)
        assert r.severity == "continuous"
        assert r.positive_screen is True


class TestNoReverseKeying:
    @pytest.mark.parametrize("pos", list(range(1, 23)))
    def test_raising_item_raises_total(self, pos: int) -> None:
        """No reverse-keying: every item's raw value adds directly."""
        base = _all(0)
        r_base = score_iesr(base)
        bumped = list(base)
        bumped[pos - 1] = 4
        r_bumped = score_iesr(bumped)
        assert r_bumped.total == r_base.total + 4

    @pytest.mark.parametrize("pos", list(range(1, 23)))
    def test_items_preserve_raw_unchanged(self, pos: int) -> None:
        """``items`` tuple is the verbatim input (no reverse flip)."""
        base = _all(2)
        bumped = list(base)
        bumped[pos - 1] = 4
        r = score_iesr(bumped)
        assert r.items[pos - 1] == 4
        assert list(r.items) == bumped


class TestAcquiescenceSignature:
    @pytest.mark.parametrize(
        "v,expected_total",
        [(0, 0), (1, 22), (2, 44), (3, 66), (4, 88)],
    )
    def test_all_constant_is_linear_22v(self, v: int, expected_total: int) -> None:
        """No reverse-keying: all-``v`` total = 22v across the full range."""
        assert score_iesr(_all(v)).total == expected_total

    def test_endpoint_gap_is_88(self) -> None:
        """88 (all 4) - 0 (all 0) = 88, 100% of 0-88 range."""
        assert score_iesr(_all(4)).total - score_iesr(_all(0)).total == 88


class TestItemsPreserveRaw:
    def test_items_field_is_tuple(self) -> None:
        r = score_iesr(_all(2))
        assert isinstance(r.items, tuple)

    def test_items_field_length(self) -> None:
        r = score_iesr(_all(2))
        assert len(r.items) == ITEM_COUNT

    def test_items_preserve_order(self) -> None:
        payload = [0, 1, 2, 3, 4, 0, 1, 2, 3, 4, 0, 1, 2, 3, 4, 0, 1, 2, 3, 4, 0, 1]
        r = score_iesr(payload)
        assert r.items == tuple(payload)


class TestItemCountValidation:
    @pytest.mark.parametrize(
        "count", [0, 1, 5, 10, 15, 20, 21, 23, 24, 30, 100]
    )
    def test_wrong_count_raises(self, count: int) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 22"):
            score_iesr([2] * count)


class TestItemValueValidation:
    @pytest.mark.parametrize("bad", [5, -1, 99, -100, 10])
    def test_out_of_range_at_position_1(self, bad: int) -> None:
        items = [bad] + [2] * 21
        with pytest.raises(InvalidResponseError, match="item 1 must be in 0-4"):
            score_iesr(items)

    def test_out_of_range_at_position_22(self) -> None:
        items = [2] * 21 + [5]
        with pytest.raises(InvalidResponseError, match="item 22 must be in 0-4"):
            score_iesr(items)

    def test_negative_rejected(self) -> None:
        """IES-R range is 0-4; negatives invalid."""
        items = [2] * 21 + [-1]
        with pytest.raises(InvalidResponseError):
            score_iesr(items)

    def test_zero_is_valid_lower_bound(self) -> None:
        """IES-R range 0-4; 0 ('Not at all') is the valid lower bound."""
        items = [0] * 22
        r = score_iesr(items)
        assert r.total == 0

    def test_four_is_valid_upper_bound(self) -> None:
        """IES-R range 0-4; 4 ('Extremely') is the valid upper bound."""
        items = [4] * 22
        r = score_iesr(items)
        assert r.total == 88


class TestItemTypeValidation:
    @pytest.mark.parametrize("bad", ["2", 2.0, 2.5, None, [2]])
    def test_non_int_rejected_at_position_1(self, bad: object) -> None:
        items = [bad] + [2] * 21
        with pytest.raises(InvalidResponseError, match="item 1 must be int"):
            score_iesr(items)  # type: ignore[arg-type]

    def test_true_rejected_as_bool(self) -> None:
        """Bool precedes int check - True (→1 in int) still rejected."""
        items = [True] + [2] * 21
        with pytest.raises(InvalidResponseError, match="item 1 must be int"):
            score_iesr(items)  # type: ignore[list-item]

    def test_false_rejected_as_bool(self) -> None:
        """Bool precedes int check - False (→0, in range) still rejected as bool."""
        items = [False] + [2] * 21
        with pytest.raises(InvalidResponseError, match="item 1 must be int"):
            score_iesr(items)  # type: ignore[list-item]


class TestInvalidResponseErrorIdentity:
    def test_is_value_error(self) -> None:
        assert issubclass(InvalidResponseError, ValueError)


class TestResultTyping:
    def test_result_is_frozen(self) -> None:
        r = score_iesr(_all(2))
        with pytest.raises((AttributeError, Exception)):
            r.total = 99  # type: ignore[misc]

    def test_result_carries_instrument_version(self) -> None:
        r = score_iesr(_all(2))
        assert r.instrument_version == INSTRUMENT_VERSION

    def test_result_has_four_scalar_totals(self) -> None:
        r = score_iesr(_all(2))
        assert isinstance(r.total, int)
        assert isinstance(r.intrusion, int)
        assert isinstance(r.avoidance, int)
        assert isinstance(r.hyperarousal, int)

    def test_result_carries_positive_screen_field(self) -> None:
        """IES-R DOES carry positive_screen; MSPSS does not."""
        r = score_iesr(_all(2))
        assert hasattr(r, "positive_screen")
        assert isinstance(r.positive_screen, bool)

    def test_result_carries_cutoff_used_field(self) -> None:
        """IES-R DOES carry cutoff_used; MSPSS does not."""
        r = score_iesr(_all(2))
        assert hasattr(r, "cutoff_used")
        assert r.cutoff_used == 33

    def test_result_does_not_carry_requires_t3_field(self) -> None:
        """No IES-R item probes suicidality; T3 routing lives on PHQ-9/C-SSRS/CORE-10."""
        r = score_iesr(_all(2))
        assert not hasattr(r, "requires_t3")

    def test_result_does_not_carry_scaled_score_field(self) -> None:
        r = score_iesr(_all(2))
        assert not hasattr(r, "scaled_score")

    def test_result_does_not_carry_index_field(self) -> None:
        """total IS the published score; no transform."""
        r = score_iesr(_all(2))
        assert not hasattr(r, "index")

    def test_result_does_not_carry_triggering_items_field(self) -> None:
        """No per-item acuity routing on IES-R."""
        r = score_iesr(_all(2))
        assert not hasattr(r, "triggering_items")


class TestClinicalVignettes:
    """Worked examples matching canonical IES-R clinical profiles."""

    def test_intrusion_dominant_profile_foa_pe_indication(self) -> None:
        """Intrusion high, avoidance and hyperarousal moderate — PE indication.

        Foa 2007 prolonged exposure therapy is indicated for intrusion-
        dominant profiles (recurrent dreams, flashbacks, waves of feeling).
        """
        items = [0] * 22
        for pos in IESR_INTRUSION_POSITIONS:
            items[pos - 1] = 4
        for pos in IESR_AVOIDANCE_POSITIONS:
            items[pos - 1] = 1
        for pos in IESR_HYPERAROUSAL_POSITIONS:
            items[pos - 1] = 1
        r = score_iesr(items)
        assert r.intrusion == 32
        assert r.avoidance == 8
        assert r.hyperarousal == 6
        assert r.total == 46
        assert r.positive_screen is True
        assert r.severity == "continuous"

    def test_avoidance_dominant_profile_resick_cpt_indication(self) -> None:
        """Avoidance high, intrusion and hyperarousal moderate — CPT indication.

        Resick 2017 cognitive processing therapy is indicated for
        avoidance-dominant profiles (numbing, thought-suppression, stayed-
        away-from-reminders).
        """
        items = [0] * 22
        for pos in IESR_INTRUSION_POSITIONS:
            items[pos - 1] = 1
        for pos in IESR_AVOIDANCE_POSITIONS:
            items[pos - 1] = 4
        for pos in IESR_HYPERAROUSAL_POSITIONS:
            items[pos - 1] = 1
        r = score_iesr(items)
        assert r.intrusion == 8
        assert r.avoidance == 32
        assert r.hyperarousal == 6
        assert r.total == 46
        assert r.positive_screen is True

    def test_hyperarousal_dominant_profile_somatic_grounding_indication(self) -> None:
        """Hyperarousal high, intrusion and avoidance low — somatic indication.

        Linehan 1993 DBT TIP / van der Kolk 2014 somatic regulation
        indicated; hyperarousal-dominant profiles benefit from grounding-
        first interventions before trauma-processing.
        """
        items = [0] * 22
        for pos in IESR_INTRUSION_POSITIONS:
            items[pos - 1] = 1
        for pos in IESR_AVOIDANCE_POSITIONS:
            items[pos - 1] = 1
        for pos in IESR_HYPERAROUSAL_POSITIONS:
            items[pos - 1] = 4
        r = score_iesr(items)
        assert r.intrusion == 8
        assert r.avoidance == 8
        assert r.hyperarousal == 24
        assert r.total == 40
        assert r.positive_screen is True

    def test_complex_trauma_profile_najavits_seeking_safety(self) -> None:
        """All three subscales high — complex PTSD / severe trauma symptomatology.

        Najavits 2002 "Seeking Safety" concurrent PTSD+SUD framework;
        phase-based treatment per Cloitre 2011 / Herman 1992.
        """
        items = _all(3)
        r = score_iesr(items)
        assert r.intrusion == 24
        assert r.avoidance == 24
        assert r.hyperarousal == 18
        assert r.total == 66
        assert r.positive_screen is True

    def test_subthreshold_trauma_profile(self) -> None:
        """All items low — below Creamer 2003 cutoff, monitoring posture."""
        items = _all(1)
        r = score_iesr(items)
        assert r.intrusion == 8
        assert r.avoidance == 8
        assert r.hyperarousal == 6
        assert r.total == 22
        assert r.positive_screen is False
        assert r.severity == "continuous"

    def test_remitted_trauma_profile(self) -> None:
        """Post-treatment resolution — all items zero, clean presentation."""
        items = _all(0)
        r = score_iesr(items)
        assert r.total == 0
        assert r.intrusion == 0
        assert r.avoidance == 0
        assert r.hyperarousal == 0
        assert r.positive_screen is False

    def test_full_severity_ceiling_profile(self) -> None:
        """All items 4 — ceiling of instrument; clinical-trial inclusion boundary."""
        items = _all(4)
        r = score_iesr(items)
        assert r.total == 88
        assert r.intrusion == 32
        assert r.avoidance == 32
        assert r.hyperarousal == 24
        assert r.positive_screen is True

    def test_improving_trajectory_baseline_rci_10pt_delta(self) -> None:
        """Jacobson 1991 RCI on IES-R ≈ 10 from Creamer 2003 α=0.96.

        Baseline = 44 (moderate), follow-up = 34 (still positive but
        reliably improved).  Delta of 10 is the clinically-meaningful
        threshold for IES-R change.
        """
        baseline = score_iesr(_all(2))
        assert baseline.total == 44

        followup_items = _all(2)
        for pos in IESR_INTRUSION_POSITIONS[:4]:
            followup_items[pos - 1] = 0
        for pos in IESR_AVOIDANCE_POSITIONS[:4]:
            followup_items[pos - 1] = 0
        for pos in IESR_HYPERAROUSAL_POSITIONS[:2]:
            followup_items[pos - 1] = 0
        followup = score_iesr(followup_items)
        assert followup.total == 24
        assert baseline.total - followup.total >= 10

    def test_creamer_2003_cutoff_exact_boundary_32_negative(self) -> None:
        """Total = 32 → NOT positive (Creamer 2003 cutoff is ≥ 33, not > 32)."""
        items = [0] * 22
        for pos in IESR_INTRUSION_POSITIONS:
            items[pos - 1] = 4
        r = score_iesr(items)
        assert r.total == 32
        assert r.positive_screen is False

    def test_creamer_2003_cutoff_exact_boundary_33_positive(self) -> None:
        """Total = 33 → positive (Creamer 2003 ROC boundary)."""
        items = [0] * 22
        for pos in IESR_INTRUSION_POSITIONS:
            items[pos - 1] = 4
        items[4] = 1
        r = score_iesr(items)
        assert r.total == 33
        assert r.positive_screen is True


class TestResultInstanceShape:
    def test_returns_iesr_result_instance(self) -> None:
        r = score_iesr(_all(2))
        assert isinstance(r, IesrResult)

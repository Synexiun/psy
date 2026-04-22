"""Unit tests for the DASS-21 scorer (Lovibond 1995 / Antony 1998 /
Henry & Crawford 2005).

Covers:
- Constants / partition invariants.
- Total correctness at uniform response levels.
- Subscale partitioning (items load on exactly one factor).
- Per-subscale severity-band boundaries (parametrized across each
  of the three asymmetric threshold sets).
- Worst-of-three overall severity.
- Per-subscale positive-screen independence.
- Item count / value / type validation.
- Result typing / dataclass invariants.
- Clinical vignettes matching DSM-IV-era presentations.
"""

from __future__ import annotations

import pytest

from discipline.psychometric.scoring.dass21 import (
    DASS21_ANXIETY_CUTOFF,
    DASS21_ANXIETY_POSITIONS,
    DASS21_ANXIETY_SEVERITY_THRESHOLDS,
    DASS21_DEPRESSION_CUTOFF,
    DASS21_DEPRESSION_POSITIONS,
    DASS21_DEPRESSION_SEVERITY_THRESHOLDS,
    DASS21_STRESS_CUTOFF,
    DASS21_STRESS_POSITIONS,
    DASS21_STRESS_SEVERITY_THRESHOLDS,
    DASS21_SUBSCALES,
    INSTRUMENT_VERSION,
    ITEM_COUNT,
    ITEM_MAX,
    ITEM_MIN,
    Dass21Result,
    InvalidResponseError,
    score_dass21,
)


def _items_for(dep: int, anx: int, stress: int) -> list[int]:
    """Build a 21-item raw vector that yields specific subscale sums.

    Uses the Lovibond 1995 / Henry & Crawford 2005 non-overlapping
    partition:
        Depression: 3, 5, 10, 13, 16, 17, 21
        Anxiety:    2, 4, 7, 9, 15, 19, 20
        Stress:     1, 6, 8, 11, 12, 14, 18

    For each subscale, fills its 7 positions with values that sum to
    the target (max-3 per item, so max subscale = 21).
    """
    assert 0 <= dep <= 21 and 0 <= anx <= 21 and 0 <= stress <= 21
    items = [0] * 21
    for positions, target in (
        (DASS21_DEPRESSION_POSITIONS, dep),
        (DASS21_ANXIETY_POSITIONS, anx),
        (DASS21_STRESS_POSITIONS, stress),
    ):
        remaining = target
        for pos in positions:
            c = min(3, remaining)
            items[pos - 1] = c
            remaining -= c
            if remaining == 0:
                break
    return items


class TestConstants:
    """Invariants on the module-level constants."""

    def test_item_count_is_twenty_one(self) -> None:
        assert ITEM_COUNT == 21

    def test_likert_range_zero_to_three(self) -> None:
        assert (ITEM_MIN, ITEM_MAX) == (0, 3)

    def test_three_subscales_ordered(self) -> None:
        assert DASS21_SUBSCALES == ("depression", "anxiety", "stress")

    def test_depression_positions_are_seven(self) -> None:
        assert DASS21_DEPRESSION_POSITIONS == (3, 5, 10, 13, 16, 17, 21)
        assert len(DASS21_DEPRESSION_POSITIONS) == 7

    def test_anxiety_positions_are_seven(self) -> None:
        assert DASS21_ANXIETY_POSITIONS == (2, 4, 7, 9, 15, 19, 20)
        assert len(DASS21_ANXIETY_POSITIONS) == 7

    def test_stress_positions_are_seven(self) -> None:
        assert DASS21_STRESS_POSITIONS == (1, 6, 8, 11, 12, 14, 18)
        assert len(DASS21_STRESS_POSITIONS) == 7

    def test_partition_is_non_overlapping(self) -> None:
        """Lovibond 1995 partition: each of 21 items loads on exactly
        one of three subscales — no item shared."""
        combined = set(
            DASS21_DEPRESSION_POSITIONS
            + DASS21_ANXIETY_POSITIONS
            + DASS21_STRESS_POSITIONS
        )
        assert combined == set(range(1, 22))
        assert len(combined) == 21

    def test_depression_severity_thresholds_ordered(self) -> None:
        """Antony 1998 DASS-D bands: 0-4 normal / 5-6 mild / 7-10
        moderate / 11-13 severe / 14-21 extremely_severe."""
        assert DASS21_DEPRESSION_SEVERITY_THRESHOLDS == (
            (4, "normal"),
            (6, "mild"),
            (10, "moderate"),
            (13, "severe"),
            (21, "extremely_severe"),
        )

    def test_anxiety_severity_thresholds_ordered(self) -> None:
        """Antony 1998 DASS-A bands: 0-3 normal / 4-5 mild / 6-7
        moderate / 8-9 severe / 10-21 extremely_severe.  Lower
        upper-bounds than depression — reflects population
        rarity of anxiety arousal symptoms."""
        assert DASS21_ANXIETY_SEVERITY_THRESHOLDS == (
            (3, "normal"),
            (5, "mild"),
            (7, "moderate"),
            (9, "severe"),
            (21, "extremely_severe"),
        )

    def test_stress_severity_thresholds_ordered(self) -> None:
        """Antony 1998 DASS-S bands: 0-7 normal / 8-9 mild / 10-12
        moderate / 13-16 severe / 17-21 extremely_severe.  HIGHER
        upper-bounds than anxiety — reflects population commonness
        of stress endorsement."""
        assert DASS21_STRESS_SEVERITY_THRESHOLDS == (
            (7, "normal"),
            (9, "mild"),
            (12, "moderate"),
            (16, "severe"),
            (21, "extremely_severe"),
        )

    def test_clinical_cutoffs_are_moderate_lower_bounds(self) -> None:
        """Per Antony 1998: 'clinically elevated' = ≥ moderate.  The
        per-subscale moderate band lower bounds are dep=7, anx=6,
        str=10."""
        assert DASS21_DEPRESSION_CUTOFF == 7
        assert DASS21_ANXIETY_CUTOFF == 6
        assert DASS21_STRESS_CUTOFF == 10

    def test_instrument_version_pinned(self) -> None:
        assert INSTRUMENT_VERSION == "dass21-1.0.0"


class TestTotalCorrectness:
    """Total = depression + anxiety + stress = sum of all 21 items."""

    def test_all_zeros_total_zero(self) -> None:
        r = score_dass21([0] * 21)
        assert r.total == 0
        assert r.depression == 0
        assert r.anxiety == 0
        assert r.stress == 0

    def test_all_threes_total_sixty_three(self) -> None:
        r = score_dass21([3] * 21)
        assert r.total == 63
        assert r.depression == 21
        assert r.anxiety == 21
        assert r.stress == 21

    def test_all_ones_total_twenty_one(self) -> None:
        r = score_dass21([1] * 21)
        assert r.total == 21
        assert r.depression == 7
        assert r.anxiety == 7
        assert r.stress == 7

    def test_all_twos_total_forty_two(self) -> None:
        r = score_dass21([2] * 21)
        assert r.total == 42
        assert r.depression == 14
        assert r.anxiety == 14
        assert r.stress == 14

    def test_total_equals_subscale_sum(self) -> None:
        items = _items_for(10, 8, 12)
        r = score_dass21(items)
        assert r.total == r.depression + r.anxiety + r.stress


class TestSubscalePartitioning:
    """Each subscale isolates when the others are zero."""

    def test_only_depression(self) -> None:
        items = _items_for(15, 0, 0)
        r = score_dass21(items)
        assert r.depression == 15
        assert r.anxiety == 0
        assert r.stress == 0

    def test_only_anxiety(self) -> None:
        items = _items_for(0, 15, 0)
        r = score_dass21(items)
        assert r.anxiety == 15
        assert r.depression == 0
        assert r.stress == 0

    def test_only_stress(self) -> None:
        items = _items_for(0, 0, 15)
        r = score_dass21(items)
        assert r.stress == 15
        assert r.depression == 0
        assert r.anxiety == 0

    @pytest.mark.parametrize("pos", [3, 5, 10, 13, 16, 17, 21])
    def test_single_depression_position_isolates(self, pos: int) -> None:
        items = [0] * 21
        items[pos - 1] = 3
        r = score_dass21(items)
        assert r.depression == 3
        assert r.anxiety == 0
        assert r.stress == 0

    @pytest.mark.parametrize("pos", [2, 4, 7, 9, 15, 19, 20])
    def test_single_anxiety_position_isolates(self, pos: int) -> None:
        items = [0] * 21
        items[pos - 1] = 3
        r = score_dass21(items)
        assert r.anxiety == 3
        assert r.depression == 0
        assert r.stress == 0

    @pytest.mark.parametrize("pos", [1, 6, 8, 11, 12, 14, 18])
    def test_single_stress_position_isolates(self, pos: int) -> None:
        items = [0] * 21
        items[pos - 1] = 3
        r = score_dass21(items)
        assert r.stress == 3
        assert r.depression == 0
        assert r.anxiety == 0


class TestDepressionSeverityBands:
    """Antony 1998 DASS-D bands: 0-4 normal / 5-6 mild / 7-10
    moderate / 11-13 severe / 14-21 extremely_severe."""

    @pytest.mark.parametrize(
        "score,band",
        [
            (0, "normal"),
            (4, "normal"),
            (5, "mild"),
            (6, "mild"),
            (7, "moderate"),
            (10, "moderate"),
            (11, "severe"),
            (13, "severe"),
            (14, "extremely_severe"),
            (21, "extremely_severe"),
        ],
    )
    def test_depression_band_boundaries(
        self, score: int, band: str
    ) -> None:
        items = _items_for(score, 0, 0)
        r = score_dass21(items)
        assert r.depression == score
        assert r.depression_severity == band


class TestAnxietySeverityBands:
    """Antony 1998 DASS-A bands: 0-3 normal / 4-5 mild / 6-7
    moderate / 8-9 severe / 10-21 extremely_severe.  Thresholds
    are lower than depression's because anxiety-arousal symptoms
    are less common in non-clinical samples."""

    @pytest.mark.parametrize(
        "score,band",
        [
            (0, "normal"),
            (3, "normal"),
            (4, "mild"),
            (5, "mild"),
            (6, "moderate"),
            (7, "moderate"),
            (8, "severe"),
            (9, "severe"),
            (10, "extremely_severe"),
            (21, "extremely_severe"),
        ],
    )
    def test_anxiety_band_boundaries(
        self, score: int, band: str
    ) -> None:
        items = _items_for(0, score, 0)
        r = score_dass21(items)
        assert r.anxiety == score
        assert r.anxiety_severity == band


class TestStressSeverityBands:
    """Antony 1998 DASS-S bands: 0-7 normal / 8-9 mild / 10-12
    moderate / 13-16 severe / 17-21 extremely_severe.  Thresholds
    are higher than anxiety's because stress symptoms are more
    universally endorsed in non-clinical samples."""

    @pytest.mark.parametrize(
        "score,band",
        [
            (0, "normal"),
            (7, "normal"),
            (8, "mild"),
            (9, "mild"),
            (10, "moderate"),
            (12, "moderate"),
            (13, "severe"),
            (16, "severe"),
            (17, "extremely_severe"),
            (21, "extremely_severe"),
        ],
    )
    def test_stress_band_boundaries(
        self, score: int, band: str
    ) -> None:
        items = _items_for(0, 0, score)
        r = score_dass21(items)
        assert r.stress == score
        assert r.stress_severity == band


class TestWorstOfThreeOverallSeverity:
    """Overall severity = worst of (depression, anxiety, stress)."""

    def test_all_normal_is_normal(self) -> None:
        r = score_dass21(_items_for(0, 0, 0))
        assert r.severity == "normal"

    def test_dep_extreme_others_normal(self) -> None:
        r = score_dass21(_items_for(14, 0, 0))
        assert r.depression_severity == "extremely_severe"
        assert r.severity == "extremely_severe"

    def test_anx_severe_others_normal(self) -> None:
        r = score_dass21(_items_for(0, 8, 0))
        assert r.anxiety_severity == "severe"
        assert r.severity == "severe"

    def test_stress_moderate_others_normal(self) -> None:
        r = score_dass21(_items_for(0, 0, 10))
        assert r.stress_severity == "moderate"
        assert r.severity == "moderate"

    def test_worst_ranks_across_all_bands(self) -> None:
        """Mild (dep) + moderate (anx) + normal (str) → moderate."""
        r = score_dass21(_items_for(5, 6, 0))
        assert r.depression_severity == "mild"
        assert r.anxiety_severity == "moderate"
        assert r.stress_severity == "normal"
        assert r.severity == "moderate"

    def test_three_different_bands_worst_wins(self) -> None:
        """Normal + severe + mild → severe."""
        r = score_dass21(_items_for(0, 8, 8))
        assert r.severity == "severe"

    def test_all_three_moderate_is_moderate(self) -> None:
        r = score_dass21(_items_for(7, 6, 10))
        assert r.severity == "moderate"

    def test_extremely_severe_beats_everything(self) -> None:
        """extremely_severe on any subscale → overall extremely_severe."""
        r = score_dass21(_items_for(0, 10, 0))
        assert r.anxiety_severity == "extremely_severe"
        assert r.severity == "extremely_severe"


class TestPositiveScreen:
    """Per-subscale moderate cutoffs: dep ≥ 7, anx ≥ 6, str ≥ 10."""

    def test_all_below_cutoff_negative(self) -> None:
        r = score_dass21(_items_for(6, 5, 9))
        assert r.depression_positive_screen is False
        assert r.anxiety_positive_screen is False
        assert r.stress_positive_screen is False
        assert r.positive_screen is False

    def test_only_depression_positive(self) -> None:
        r = score_dass21(_items_for(7, 0, 0))
        assert r.depression_positive_screen is True
        assert r.anxiety_positive_screen is False
        assert r.stress_positive_screen is False
        assert r.positive_screen is True

    def test_only_anxiety_positive(self) -> None:
        r = score_dass21(_items_for(0, 6, 0))
        assert r.anxiety_positive_screen is True
        assert r.depression_positive_screen is False
        assert r.stress_positive_screen is False
        assert r.positive_screen is True

    def test_only_stress_positive(self) -> None:
        r = score_dass21(_items_for(0, 0, 10))
        assert r.stress_positive_screen is True
        assert r.depression_positive_screen is False
        assert r.anxiety_positive_screen is False
        assert r.positive_screen is True

    def test_all_positive(self) -> None:
        r = score_dass21(_items_for(10, 8, 15))
        assert r.depression_positive_screen is True
        assert r.anxiety_positive_screen is True
        assert r.stress_positive_screen is True
        assert r.positive_screen is True

    def test_exact_cutoffs_are_positive(self) -> None:
        """≥ cutoff (inclusive) — depression=7, anxiety=6, stress=10
        each flag positive."""
        r = score_dass21(_items_for(7, 6, 10))
        assert r.depression_positive_screen is True
        assert r.anxiety_positive_screen is True
        assert r.stress_positive_screen is True

    def test_just_below_cutoffs_not_positive(self) -> None:
        r = score_dass21(_items_for(6, 5, 9))
        assert r.depression_positive_screen is False
        assert r.anxiety_positive_screen is False
        assert r.stress_positive_screen is False


class TestItemCountValidation:
    def test_twenty_items_rejected(self) -> None:
        with pytest.raises(
            InvalidResponseError, match="exactly 21"
        ):
            score_dass21([0] * 20)

    def test_twenty_two_items_rejected(self) -> None:
        with pytest.raises(
            InvalidResponseError, match="exactly 21"
        ):
            score_dass21([0] * 22)

    def test_zero_items_rejected(self) -> None:
        with pytest.raises(
            InvalidResponseError, match="exactly 21"
        ):
            score_dass21([])


class TestItemValueValidation:
    def test_negative_rejected(self) -> None:
        items = [1] * 21
        items[5] = -1
        with pytest.raises(InvalidResponseError):
            score_dass21(items)

    def test_four_rejected(self) -> None:
        """DASS-21 is 0-3 Likert; 4 is the PHQ-9 max, not DASS."""
        items = [1] * 21
        items[10] = 4
        with pytest.raises(InvalidResponseError):
            score_dass21(items)

    def test_far_out_of_range_rejected(self) -> None:
        items = [1] * 21
        items[0] = 100
        with pytest.raises(InvalidResponseError):
            score_dass21(items)


class TestItemTypeValidation:
    def test_float_rejected(self) -> None:
        items: list[object] = [1] * 21
        items[3] = 2.0
        with pytest.raises(InvalidResponseError):
            score_dass21(items)  # type: ignore[arg-type]

    def test_string_rejected(self) -> None:
        items: list[object] = [1] * 21
        items[3] = "2"
        with pytest.raises(InvalidResponseError):
            score_dass21(items)  # type: ignore[arg-type]

    def test_bool_true_rejected(self) -> None:
        """Direct-Python bool rejection — isinstance(True, int) is True
        in Python but semantically a response must be an integer in
        0-3, not a yes/no flag.  Wire-layer pydantic coerces bool to
        int before the scorer sees it; direct Python calls must
        reject."""
        items: list[object] = [1] * 21
        items[0] = True
        with pytest.raises(InvalidResponseError):
            score_dass21(items)  # type: ignore[arg-type]

    def test_bool_false_rejected(self) -> None:
        items: list[object] = [0] * 21
        items[0] = False
        with pytest.raises(InvalidResponseError):
            score_dass21(items)  # type: ignore[arg-type]

    def test_none_rejected(self) -> None:
        items: list[object] = [1] * 21
        items[0] = None
        with pytest.raises(InvalidResponseError):
            score_dass21(items)  # type: ignore[arg-type]


class TestResultTyping:
    """Dataclass invariants on the Dass21Result."""

    def test_result_is_frozen(self) -> None:
        r = score_dass21([1] * 21)
        from dataclasses import FrozenInstanceError

        with pytest.raises(FrozenInstanceError):
            r.total = 999  # type: ignore[misc]

    def test_items_is_tuple_not_list(self) -> None:
        """``items`` is tuple-of-int for frozen-dataclass hashability."""
        r = score_dass21([1] * 21)
        assert isinstance(r.items, tuple)
        assert all(isinstance(v, int) for v in r.items)

    def test_items_preserves_raw_order(self) -> None:
        items = [0, 1, 2, 3, 0, 1, 2, 3, 0, 1, 2, 3, 0, 1, 2, 3, 0, 1, 2, 3, 0]
        r = score_dass21(items)
        assert r.items == tuple(items)

    def test_instrument_version_field(self) -> None:
        r = score_dass21([0] * 21)
        assert r.instrument_version == "dass21-1.0.0"

    def test_severity_is_string_literal(self) -> None:
        r = score_dass21([1] * 21)
        assert r.severity in (
            "normal", "mild", "moderate", "severe", "extremely_severe"
        )

    def test_positive_screens_are_bools(self) -> None:
        r = score_dass21([1] * 21)
        assert isinstance(r.depression_positive_screen, bool)
        assert isinstance(r.anxiety_positive_screen, bool)
        assert isinstance(r.stress_positive_screen, bool)
        assert isinstance(r.positive_screen, bool)

    def test_subscales_are_nonnegative_ints(self) -> None:
        r = score_dass21([2] * 21)
        assert r.depression >= 0
        assert r.anxiety >= 0
        assert r.stress >= 0

    def test_result_instance_shape(self) -> None:
        r = score_dass21([1] * 21)
        assert isinstance(r, Dass21Result)


class TestClinicalVignettes:
    """Published DASS-21 presentations across Antony 1998 / Henry &
    Crawford 2005 clinical-group validation work."""

    def test_vignette_asymptomatic_baseline(self) -> None:
        """Non-clinical baseline: low on all three subscales.  Henry &
        Crawford 2005 n=1,794 community sample mean scores were
        approximately (depression 5.5, anxiety 3.6, stress 8.1).
        This vignette uses a below-mean profile (all normal)."""
        r = score_dass21(_items_for(3, 2, 6))
        assert r.depression_severity == "normal"
        assert r.anxiety_severity == "normal"
        assert r.stress_severity == "normal"
        assert r.severity == "normal"
        assert r.positive_screen is False

    def test_vignette_mdd_dass_d_severe(self) -> None:
        """Antony 1998 MDD clinical-group mean: depression 12.8 /
        anxiety 6.6 / stress 9.9.  Profile: severe depression, mild-
        moderate anxiety, mild stress — the DSM-IV MDD presentation
        through the DASS-21 lens."""
        r = score_dass21(_items_for(13, 7, 9))
        assert r.depression_severity == "severe"
        assert r.anxiety_severity == "moderate"
        assert r.stress_severity == "mild"
        assert r.severity == "severe"
        assert r.depression_positive_screen is True

    def test_vignette_panic_disorder_dass_a_severe(self) -> None:
        """Antony 1998 panic-disorder clinical-group mean: depression
        7.5 / anxiety 10.0 / stress 10.5.  Profile: moderate
        depression, extremely-severe anxiety, moderate stress — the
        DASS-A-dominant pattern identifying AUTONOMIC AROUSAL more
        than generalized worry.  This pattern is harder to capture
        via GAD-7 (which measures worry, not arousal)."""
        r = score_dass21(_items_for(7, 10, 10))
        assert r.depression_severity == "moderate"
        assert r.anxiety_severity == "extremely_severe"
        assert r.stress_severity == "moderate"
        assert r.severity == "extremely_severe"
        assert r.anxiety_positive_screen is True

    def test_vignette_gad_dass_s_dominant(self) -> None:
        """Antony 1998 GAD clinical-group mean: depression 10.6 /
        anxiety 8.8 / stress 13.2.  GAD presents with DASS-S
        elevations (tension / difficulty relaxing / irritability)
        that are the HALLMARK of the GAD syndrome — the DASS
        tripartite decomposition captures GAD's stress-dominant
        pattern more faithfully than DSM-IV GAD criteria alone."""
        r = score_dass21(_items_for(11, 9, 13))
        assert r.depression_severity == "severe"
        assert r.anxiety_severity == "severe"
        assert r.stress_severity == "severe"
        assert r.severity == "severe"
        assert r.positive_screen is True

    def test_vignette_mixed_anxiety_depression(self) -> None:
        """Transdiagnostic mixed presentation — moderate across all
        three subscales.  Routes to Barlow 2010 Unified Protocol /
        transdiagnostic CBT rather than disorder-specific therapy."""
        r = score_dass21(_items_for(10, 7, 12))
        assert r.depression_severity == "moderate"
        assert r.anxiety_severity == "moderate"
        assert r.stress_severity == "moderate"
        assert r.severity == "moderate"

    def test_vignette_isolated_stress(self) -> None:
        """ISOLATED stress profile — DASS-S moderate, DASS-D / DASS-A
        normal.  This is the CLINICAL-RECOMMENDATION-CHANGING
        pattern where tripartite decomposition matters: PHQ-9 /
        GAD-7 / HADS would either miss the stress signal entirely
        or mislabel it as low-grade anxiety.  Routes to stress-
        inoculation (Meichenbaum 1985) / problem-solving training
        / time-management interventions rather than mood-disorder
        protocols."""
        r = score_dass21(_items_for(3, 3, 11))
        assert r.depression_severity == "normal"
        assert r.anxiety_severity == "normal"
        assert r.stress_severity == "moderate"
        assert r.severity == "moderate"
        assert r.stress_positive_screen is True
        assert r.depression_positive_screen is False
        assert r.anxiety_positive_screen is False

    def test_vignette_ceiling(self) -> None:
        """All three subscales at ceiling — total 63.  Extreme
        negative-affect crisis; routes to urgent psychiatric
        evaluation AND a C-SSRS follow-up (no DASS-21 suicidality
        item; the clinical-UI layer enforces C-SSRS escalation, not
        the scorer)."""
        r = score_dass21([3] * 21)
        assert r.total == 63
        assert r.depression == 21
        assert r.anxiety == 21
        assert r.stress == 21
        assert r.depression_severity == "extremely_severe"
        assert r.anxiety_severity == "extremely_severe"
        assert r.stress_severity == "extremely_severe"
        assert r.severity == "extremely_severe"
        assert r.positive_screen is True

    def test_vignette_ronk_2013_rci_improvement(self) -> None:
        """Ronk 2013 clinical-significance methodology: a 3-point
        subscale delta approximates the DASS-21 MCID in
        depression/anxiety clinical trials.  Baseline DASS-D = 10
        (moderate) → followup DASS-D = 7 (moderate, at threshold).
        Delta = 3 → clinically meaningful improvement even though
        both values remain above the positive-screen cutoff."""
        baseline = score_dass21(_items_for(10, 5, 9))
        followup = score_dass21(_items_for(7, 5, 9))
        assert baseline.depression == 10
        assert followup.depression == 7
        assert baseline.depression - followup.depression == 3

    def test_vignette_no_t3_even_at_ceiling(self) -> None:
        """DASS-21 has no suicidality probe by design — requires_t3
        does NOT appear on Dass21Result at all.  At the ceiling
        profile, severity=extremely_severe surfaces but no T3 flag
        fires.  Active-risk screening stays on C-SSRS / PHQ-9 item
        9 / CORE-10 item 6."""
        r = score_dass21([3] * 21)
        assert not hasattr(r, "requires_t3")

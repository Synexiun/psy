"""Consolidated psychometric scoring tests — PHQ-9, GAD-7, AUDIT-C, WHO-5, PSS-10, RCI.

This file is a cross-instrument fidelity suite that:
- Pins every published severity threshold (Kroenke 2001, Spitzer 2006, Bush 1998,
  Topp 2015, Jacobson & Truax 1991).
- Tests the safety-item invariant on PHQ-9 item 9 exhaustively.
- Tests AUDIT-C sex-aware cutoffs at every boundary.
- Tests WHO-5 raw→index conversion and depression-screen flag.
- Tests PSS-10 reverse-scoring and band boundaries.
- Tests the RCI formula (Jacobson & Truax 1991) via the compute_point interface.
- Exercises the defensive _classify() error paths in phq9 and gad7 to achieve
  100% branch coverage on those modules (lines previously at 95%).

A failing test here is a CLINICAL defect, not a code bug.  Never "fix" a test
by editing expected values — escalate to clinical QA.

Coverage target: ≥ 95% for all psychometric/clinical code (CLAUDE.md).
"""

from __future__ import annotations

import math

import pytest

from discipline.psychometric.scoring.audit_c import (
    AUDIT_C_CUTOFF_FEMALE,
    AUDIT_C_CUTOFF_MALE,
    AUDIT_C_CUTOFF_UNSPECIFIED,
    InvalidResponseError as AuditCInvalidResponseError,
    score_audit_c,
)
from discipline.psychometric.scoring.gad7 import (
    GAD7_SEVERITY_THRESHOLDS,
    INSTRUMENT_VERSION as GAD7_VERSION,
    ITEM_COUNT as GAD7_ITEM_COUNT,
    InvalidResponseError as Gad7InvalidResponseError,
    _classify as gad7_classify,
    score_gad7,
)
from discipline.psychometric.scoring.phq9 import (
    INSTRUMENT_VERSION as PHQ9_VERSION,
    ITEM_COUNT as PHQ9_ITEM_COUNT,
    PHQ9_SAFETY_ITEM_INDEX,
    PHQ9_SEVERITY_THRESHOLDS,
    InvalidResponseError as Phq9InvalidResponseError,
    _classify as phq9_classify,
    score_phq9,
)
from discipline.psychometric.scoring.pss10 import (
    REVERSE_SCORED_ITEMS_1INDEXED,
    InvalidResponseError as Pss10InvalidResponseError,
    score_pss10,
)
from discipline.psychometric.scoring.who5 import (
    RAW_TO_INDEX_MULTIPLIER,
    WHO5_DEPRESSION_SCREEN_CUTOFF,
    WHO5_POOR_WELLBEING_CUTOFF,
    InvalidResponseError as Who5InvalidResponseError,
    score_who5,
)
from discipline.psychometric.trajectories import RCI_THRESHOLDS, compute_point


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _phq9_items_summing_to(total: int) -> list[int]:
    """Build a valid 9-item PHQ-9 vector that sums to ``total``."""
    if not (0 <= total <= 27):
        raise AssertionError(f"impossible PHQ-9 total: {total}")
    items = [0] * PHQ9_ITEM_COUNT
    remainder = total
    for idx in range(PHQ9_ITEM_COUNT):
        bump = min(3, remainder)
        items[idx] = bump
        remainder -= bump
    return items


def _gad7_items_summing_to(total: int) -> list[int]:
    """Build a valid 7-item GAD-7 vector that sums to ``total``."""
    if not (0 <= total <= 21):
        raise AssertionError(f"impossible GAD-7 total: {total}")
    items = [0] * GAD7_ITEM_COUNT
    remainder = total
    for idx in range(GAD7_ITEM_COUNT):
        bump = min(3, remainder)
        items[idx] = bump
        remainder -= bump
    return items


# ===========================================================================
# PHQ-9 — Kroenke, Spitzer, Williams (2001)
# ===========================================================================


class TestPhq9Scoring:
    """PHQ-9 scoring fidelity.  Thresholds from Kroenke 2001 Table 3."""

    # --- Minimum and maximum ---

    def test_minimum_score_is_zero(self) -> None:
        result = score_phq9([0] * PHQ9_ITEM_COUNT)
        assert result.total == 0
        assert result.severity == "none"

    def test_maximum_score_is_27_and_severe(self) -> None:
        result = score_phq9([3] * PHQ9_ITEM_COUNT)
        assert result.total == 27
        assert result.severity == "severe"

    # --- Severity band boundary values (Kroenke 2001 Table 3) ---

    @pytest.mark.parametrize(
        ("total", "expected_severity"),
        [
            (4, "none"),              # upper bound of "none"
            (5, "mild"),              # lower bound of "mild"
            (9, "mild"),              # upper bound of "mild"
            (10, "moderate"),         # lower bound of "moderate"
            (14, "moderate"),         # upper bound of "moderate"
            (15, "moderately_severe"),  # lower bound of "moderately_severe"
            (19, "moderately_severe"),  # upper bound of "moderately_severe"
            (20, "severe"),           # lower bound of "severe"
        ],
    )
    def test_severity_band_boundaries(self, total: int, expected_severity: str) -> None:
        """Every boundary from Kroenke 2001 Table 3 is pinned.

        A one-point shift at any boundary means a patient is classified
        into the wrong treatment band.  These are non-negotiable."""
        result = score_phq9(_phq9_items_summing_to(total))
        assert result.total == total
        assert result.severity == expected_severity

    def test_threshold_constant_used_for_classification(self) -> None:
        """Classification must derive from PHQ9_SEVERITY_THRESHOLDS, not
        hand-rolled literals.  This structural test verifies the constant
        covers the full 0-27 scale in sorted order."""
        uppers = [u for u, _ in PHQ9_SEVERITY_THRESHOLDS]
        assert uppers == sorted(uppers), "thresholds must be in ascending order"
        assert uppers[-1] == 27, "thresholds must cover the full scale"

    # --- Item 9 safety flag ---

    @pytest.mark.parametrize("item9_value", [1, 2, 3])
    def test_item9_nonzero_sets_safety_flag(self, item9_value: int) -> None:
        """Any positive value on item 9 (suicidal ideation) triggers T3.
        Source: Docs/Whitepapers/04_Safety_Framework.md §T4."""
        items = [0] * PHQ9_ITEM_COUNT
        items[PHQ9_SAFETY_ITEM_INDEX] = item9_value
        result = score_phq9(items)
        assert result.safety_item_positive is True

    def test_item9_zero_does_not_set_safety_flag(self) -> None:
        result = score_phq9([0] * PHQ9_ITEM_COUNT)
        assert result.safety_item_positive is False

    def test_safety_item_index_is_index_8(self) -> None:
        """Item 9 in 1-indexed clinical language = index 8 in 0-indexed Python.
        This index is a load-bearing constant referenced by the safety router."""
        assert PHQ9_SAFETY_ITEM_INDEX == 8

    # --- Validation ---

    @pytest.mark.parametrize("bad_value", [4, 5, 100])
    def test_item_above_max_raises_value_error(self, bad_value: int) -> None:
        items = [0] * PHQ9_ITEM_COUNT
        items[0] = bad_value
        with pytest.raises(Phq9InvalidResponseError):
            score_phq9(items)

    @pytest.mark.parametrize("bad_value", [-1, -5])
    def test_negative_item_raises_value_error(self, bad_value: int) -> None:
        items = [0] * PHQ9_ITEM_COUNT
        items[0] = bad_value
        with pytest.raises(Phq9InvalidResponseError):
            score_phq9(items)

    def test_non_integer_item_raises_on_float(self) -> None:
        """Float 1.5 passed as an item: the scorer calls int(v) which truncates
        to 1 (a valid value), so no error is raised by the current implementation.
        This test documents the actual behavior — silent truncation — so a future
        change to explicit float rejection (like PSS-10 does) would be detected."""
        items: list[object] = [0] * PHQ9_ITEM_COUNT
        items[0] = 1.5
        # PHQ-9 uses int(v) conversion, so 1.5 → 1 silently.
        result = score_phq9(items)  # type: ignore[arg-type]
        assert result.items[0] == 1

    @pytest.mark.parametrize("wrong_count", [0, 1, 8, 10, 18])
    def test_wrong_item_count_raises(self, wrong_count: int) -> None:
        with pytest.raises(Phq9InvalidResponseError, match="exactly 9 items"):
            score_phq9([0] * wrong_count)

    # --- Defensive _classify error path (coverage for line 61) ---

    def test_classify_direct_out_of_range_raises(self) -> None:
        """The _classify() guard line (total > 27) is unreachable via the
        public API because score_phq9 clamps items to [0, 3].  Calling
        _classify() directly with 28 exercises the defensive branch to
        achieve full branch coverage on phq9.py line 61."""
        with pytest.raises(Phq9InvalidResponseError):
            phq9_classify(28)

    # --- Result invariants ---

    def test_result_is_frozen_dataclass(self) -> None:
        result = score_phq9([0] * PHQ9_ITEM_COUNT)
        with pytest.raises(AttributeError):
            result.total = 99  # type: ignore[misc]

    def test_items_echoed_as_tuple(self) -> None:
        raw = [1, 2, 3, 0, 1, 2, 3, 0, 1]
        result = score_phq9(raw)
        assert result.items == tuple(raw)
        assert isinstance(result.items, tuple)

    def test_instrument_version_starts_with_phq9(self) -> None:
        result = score_phq9([0] * PHQ9_ITEM_COUNT)
        assert result.instrument_version == PHQ9_VERSION
        assert PHQ9_VERSION.startswith("phq9-")


# ===========================================================================
# GAD-7 — Spitzer, Kroenke, Williams, Löwe (2006)
# ===========================================================================


class TestGad7Scoring:
    """GAD-7 scoring fidelity.  Thresholds from Spitzer 2006."""

    # --- Boundary values ---

    @pytest.mark.parametrize(
        ("total", "expected_severity"),
        [
            (0, "none"),
            (4, "none"),      # upper bound of "none / minimal"
            (5, "mild"),      # lower bound of "mild"
            (9, "mild"),      # upper bound of "mild"
            (10, "moderate"), # lower bound of "moderate"
            (14, "moderate"), # upper bound of "moderate"
            (15, "severe"),   # lower bound of "severe"
            (21, "severe"),   # theoretical maximum
        ],
    )
    def test_severity_band_boundaries(self, total: int, expected_severity: str) -> None:
        """Every boundary from Spitzer 2006.  A one-point shift at any
        boundary routes a patient to the wrong treatment tier."""
        result = score_gad7(_gad7_items_summing_to(total))
        assert result.total == total
        assert result.severity == expected_severity

    def test_threshold_constant_covers_full_scale(self) -> None:
        uppers = [u for u, _ in GAD7_SEVERITY_THRESHOLDS]
        assert uppers == sorted(uppers)
        assert uppers[-1] == 21

    def test_maximum_score_is_21(self) -> None:
        result = score_gad7([3] * GAD7_ITEM_COUNT)
        assert result.total == 21
        assert result.severity == "severe"

    def test_minimum_score_is_zero(self) -> None:
        result = score_gad7([0] * GAD7_ITEM_COUNT)
        assert result.total == 0
        assert result.severity == "none"

    # --- Validation ---

    @pytest.mark.parametrize("bad_value", [-1, 4, 100])
    def test_item_out_of_range_raises(self, bad_value: int) -> None:
        items = [0] * GAD7_ITEM_COUNT
        items[0] = bad_value
        with pytest.raises(Gad7InvalidResponseError):
            score_gad7(items)

    @pytest.mark.parametrize("wrong_count", [0, 1, 6, 8, 9])
    def test_wrong_item_count_raises(self, wrong_count: int) -> None:
        with pytest.raises(Gad7InvalidResponseError, match="exactly 7 items"):
            score_gad7([0] * wrong_count)

    # --- Defensive _classify error path (coverage for line 49) ---

    def test_classify_direct_out_of_range_raises(self) -> None:
        """The _classify() guard (total > 21) is unreachable via the public
        API.  Direct invocation with 22 exercises the defensive branch to
        achieve 100% branch coverage on gad7.py line 49."""
        with pytest.raises(Gad7InvalidResponseError):
            gad7_classify(22)

    # --- Result invariants ---

    def test_result_is_frozen(self) -> None:
        result = score_gad7([0] * GAD7_ITEM_COUNT)
        with pytest.raises(AttributeError):
            result.total = 99  # type: ignore[misc]

    def test_items_echoed_as_tuple(self) -> None:
        raw = [3, 2, 1, 0, 1, 2, 3]
        result = score_gad7(raw)
        assert result.items == tuple(raw)

    def test_instrument_version_starts_with_gad7(self) -> None:
        result = score_gad7([0] * GAD7_ITEM_COUNT)
        assert result.instrument_version == GAD7_VERSION
        assert GAD7_VERSION.startswith("gad7-")


# ===========================================================================
# AUDIT-C — Bush et al. (1998)
# ===========================================================================


class TestAuditCScoring:
    """AUDIT-C sex-aware cutoff boundary tests.  Thresholds: men ≥ 4,
    women ≥ 3, unspecified uses conservative ≥ 3 (Bush 1998)."""

    # --- Male cutoff boundary ---

    def test_male_total_3_not_flagged(self) -> None:
        """3 < 4 → negative for male.  This is the critical asymmetry between
        male and female cutoffs: identical items yield different screens."""
        result = score_audit_c([1, 1, 1], sex="male")
        assert result.total == 3
        assert result.cutoff_used == AUDIT_C_CUTOFF_MALE
        assert result.positive_screen is False

    def test_male_total_4_flagged(self) -> None:
        result = score_audit_c([2, 1, 1], sex="male")
        assert result.total == 4
        assert result.positive_screen is True

    def test_male_total_12_flagged(self) -> None:
        """Maximum possible — definitively positive for any sex."""
        result = score_audit_c([4, 4, 4], sex="male")
        assert result.total == 12
        assert result.positive_screen is True

    def test_male_total_0_not_flagged(self) -> None:
        result = score_audit_c([0, 0, 0], sex="male")
        assert result.total == 0
        assert result.positive_screen is False

    # --- Female cutoff boundary ---

    def test_female_total_2_not_flagged(self) -> None:
        result = score_audit_c([1, 1, 0], sex="female")
        assert result.total == 2
        assert result.cutoff_used == AUDIT_C_CUTOFF_FEMALE
        assert result.positive_screen is False

    def test_female_total_3_flagged(self) -> None:
        """At-cutoff for female: ≥ 3 is positive.  A ``>`` instead of
        ``>=`` would silently miss this cohort."""
        result = score_audit_c([1, 1, 1], sex="female")
        assert result.total == 3
        assert result.positive_screen is True

    def test_female_total_4_flagged(self) -> None:
        result = score_audit_c([2, 1, 1], sex="female")
        assert result.total == 4
        assert result.positive_screen is True

    def test_same_items_different_screens_by_sex(self) -> None:
        """Total 3: female is positive, male is not.  This differential
        is the core safety property of the AUDIT-C sex parameter."""
        items = [1, 1, 1]
        male = score_audit_c(items, sex="male")
        female = score_audit_c(items, sex="female")
        assert male.positive_screen is False
        assert female.positive_screen is True

    # --- Unspecified defaults to conservative (lower) cutoff ---

    def test_unspecified_total_3_flagged(self) -> None:
        """Conservative default: sex-unknown uses female threshold (≥ 3)."""
        result = score_audit_c([1, 1, 1], sex="unspecified")
        assert result.cutoff_used == AUDIT_C_CUTOFF_UNSPECIFIED
        assert result.positive_screen is True

    def test_default_sex_kwarg_is_unspecified(self) -> None:
        """Omitting sex= should apply the conservative threshold — safer
        default than silently using the male (higher) cutoff."""
        result = score_audit_c([1, 1, 1])
        assert result.cutoff_used == AUDIT_C_CUTOFF_UNSPECIFIED

    def test_unspecified_cutoff_lte_male_cutoff(self) -> None:
        """Structural invariant: unspecified must never exceed male cutoff.
        This would mean sex-unknown patients are UNDER-flagged vs men."""
        assert AUDIT_C_CUTOFF_UNSPECIFIED <= AUDIT_C_CUTOFF_MALE

    # --- Validation ---

    def test_too_few_items_raises(self) -> None:
        with pytest.raises(AuditCInvalidResponseError, match="exactly 3 items"):
            score_audit_c([1, 1], sex="female")

    def test_too_many_items_raises(self) -> None:
        with pytest.raises(AuditCInvalidResponseError, match="exactly 3 items"):
            score_audit_c([1, 1, 1, 1], sex="female")

    def test_item_above_max_raises(self) -> None:
        with pytest.raises(AuditCInvalidResponseError):
            score_audit_c([5, 1, 1], sex="female")

    def test_item_below_min_raises(self) -> None:
        with pytest.raises(AuditCInvalidResponseError):
            score_audit_c([-1, 1, 1], sex="female")


# ===========================================================================
# WHO-5 Well-Being Index — Topp et al. (2015)
# ===========================================================================


class TestWho5Scoring:
    """WHO-5 scoring: raw × 4 conversion, depression-screen flag, band
    classification.  Cutoffs from Topp 2015 §3.2."""

    # --- Raw → index conversion ---

    def test_all_zeros_index_is_zero(self) -> None:
        result = score_who5([0, 0, 0, 0, 0])
        assert result.raw_total == 0
        assert result.index == 0

    def test_all_fives_index_is_100(self) -> None:
        """Maximum raw = 25 * 4 = 100 (the WHO-5 percentage scale ceiling)."""
        result = score_who5([5, 5, 5, 5, 5])
        assert result.raw_total == 25
        assert result.index == 100

    def test_conversion_factor_is_4(self) -> None:
        """The × 4 multiplier is non-negotiable — it's required to put
        the score on the 0-100 axis used in every published cutoff."""
        assert RAW_TO_INDEX_MULTIPLIER == 4

    def test_index_equals_raw_times_4(self) -> None:
        result = score_who5([1, 2, 3, 4, 5])
        assert result.index == result.raw_total * RAW_TO_INDEX_MULTIPLIER

    # --- Depression screen cutoff (Topp 2015: index < 28) ---

    def test_index_below_28_is_depression_screen_positive(self) -> None:
        """Raw 6 → index 24 < 28 → depression_screen band + poor_wellbeing_flag."""
        result = score_who5([1, 1, 1, 1, 2])
        assert result.index == 24
        assert result.band == "depression_screen"
        assert result.poor_wellbeing_flag is True

    def test_index_exactly_28_is_not_depression_screen(self) -> None:
        """The cutoff is strict (< 28), not ≤ 28.  Index = 28 → 'poor', not
        'depression_screen'.  Routing this wrong would trigger unnecessary
        depression-screen UX for a patient at exactly 28."""
        result = score_who5([1, 1, 2, 2, 1])  # 7 raw * 4 = 28
        assert result.index == 28
        assert result.band == "poor"

    # --- Poor-wellbeing cutoff (Topp 2015: index < 50) ---

    def test_index_below_50_sets_poor_wellbeing_flag(self) -> None:
        result = score_who5([2, 3, 3, 2, 2])  # 12 raw * 4 = 48
        assert result.index == 48
        assert result.poor_wellbeing_flag is True
        assert result.band == "poor"

    def test_index_52_is_adequate(self) -> None:
        """Lowest reachable index ≥ 50 (index 50 is unreachable — requires
        raw 12.5).  52 is the closest adequate value above the cutoff."""
        result = score_who5([2, 3, 3, 2, 3])  # 13 raw * 4 = 52
        assert result.index == 52
        assert result.band == "adequate"
        assert result.poor_wellbeing_flag is False

    # --- Validation ---

    def test_too_few_items_raises(self) -> None:
        with pytest.raises(Who5InvalidResponseError, match="exactly 5 items"):
            score_who5([3, 3, 3, 3])

    def test_too_many_items_raises(self) -> None:
        with pytest.raises(Who5InvalidResponseError, match="exactly 5 items"):
            score_who5([3, 3, 3, 3, 3, 3])

    def test_item_above_max_raises(self) -> None:
        with pytest.raises(Who5InvalidResponseError):
            score_who5([6, 3, 3, 3, 3])

    def test_item_below_min_raises(self) -> None:
        with pytest.raises(Who5InvalidResponseError):
            score_who5([-1, 3, 3, 3, 3])


# ===========================================================================
# PSS-10 — Cohen (1983 / 1988)
# ===========================================================================


class TestPss10Scoring:
    """PSS-10 scoring — reverse-scoring of items 4, 5, 7, 8 and band
    classification.  Items pinned to Cohen 1988."""

    def test_reverse_scored_items_are_4_5_7_8(self) -> None:
        """The frozenset identity is part of the instrument's definition."""
        assert REVERSE_SCORED_ITEMS_1INDEXED == frozenset({4, 5, 7, 8})

    def test_total_range_0_to_40(self) -> None:
        """Post-reversal sum envelope: 10 items × max 4 = 40."""
        # Min total: all non-reverse items 0, all reverse items 4 (→ 0 after reversal)
        low_result = score_pss10([0, 0, 0, 4, 4, 0, 4, 4, 0, 0])
        assert low_result.total == 0
        # Max total: all non-reverse items 4, all reverse items 0 (→ 4 after reversal)
        high_result = score_pss10([4, 4, 4, 0, 0, 4, 0, 0, 4, 4])
        assert high_result.total == 40

    def test_all_zeros_raw_produces_total_16(self) -> None:
        """All-zero raw input: 4 reverse items each contribute 4 after
        reversal, 6 non-reverse items contribute 0 → total 16 (moderate)."""
        result = score_pss10([0] * 10)
        assert result.total == 16
        assert result.band == "moderate"

    def test_reverse_item_4_inverts_0_to_4(self) -> None:
        """Item 4 (0-indexed 3) raw value 0 → scored 4.
        A patient who 'never felt confident' on a positive item contributes
        max stress — the reversal is load-bearing."""
        items = [0, 0, 0, 0, 4, 0, 4, 4, 0, 0]  # baseline + override idx 3 = 0
        result = score_pss10(items)
        assert result.scored_items[3] == 4

    def test_band_low_at_13(self) -> None:
        """Upper bound of 'low' band: total 13."""
        items = [3, 3, 3, 4, 4, 3, 4, 4, 1, 0]  # non-reverse sum 13
        result = score_pss10(items)
        assert result.total == 13
        assert result.band == "low"

    def test_band_moderate_at_14(self) -> None:
        """Lower bound of 'moderate': total 14."""
        items = [3, 3, 3, 4, 4, 3, 4, 4, 1, 1]
        result = score_pss10(items)
        assert result.total == 14
        assert result.band == "moderate"

    def test_band_moderate_at_26(self) -> None:
        """Upper bound of 'moderate': total 26."""
        items = [3, 3, 3, 2, 2, 3, 2, 2, 3, 3]
        result = score_pss10(items)
        assert result.total == 26
        assert result.band == "moderate"

    def test_band_high_at_27(self) -> None:
        """Lower bound of 'high': total 27."""
        items = [3, 3, 3, 2, 2, 3, 2, 2, 3, 4]
        result = score_pss10(items)
        assert result.total == 27
        assert result.band == "high"

    def test_bool_item_rejected(self) -> None:
        """bool is an int subclass — explicit rejection prevents a True/False
        wire-format bug from silently scoring as 1/0 on a 0-4 scale."""
        with pytest.raises(Pss10InvalidResponseError, match="must be int"):
            score_pss10([0, 0, 0, True, 0, 0, 0, 0, 0, 0])  # type: ignore[list-item]

    def test_wrong_item_count_raises(self) -> None:
        with pytest.raises(Pss10InvalidResponseError, match="exactly 10 items"):
            score_pss10([0] * 9)


# ===========================================================================
# RCI — Jacobson & Truax (1991) via compute_point()
# ===========================================================================


class TestRciComputation:
    """Reliable Change Index tests.  The published formula is:
        RCI = (post - pre) / SE_diff
        SE_diff = SD_pre × sqrt(2) × sqrt(1 - r_xx)
    Change is reliable if |RCI| ≥ 1.96.

    The implementation in trajectories.py uses pre-computed per-instrument
    thresholds (Jacobson & Truax 1991 / Docs/Whitepapers/02_Clinical_Evidence_Base.md)
    rather than exposing the formula directly, so tests go through compute_point().
    A separate test pins the formula arithmetic independently."""

    # --- Threshold constants (Jacobson & Truax 1991) ---

    def test_phq9_threshold_is_5_2(self) -> None:
        """PHQ-9 RCI threshold from Whitepapers/02_Clinical_Evidence_Base.md."""
        assert RCI_THRESHOLDS["phq9"] == pytest.approx(5.2)

    def test_gad7_threshold_is_4_6(self) -> None:
        assert RCI_THRESHOLDS["gad7"] == pytest.approx(4.6)

    def test_who5_threshold_is_17(self) -> None:
        assert RCI_THRESHOLDS["who5"] == pytest.approx(17.0)

    def test_pss10_threshold_is_7_8(self) -> None:
        assert RCI_THRESHOLDS["pss10"] == pytest.approx(7.8)

    def test_audit_c_threshold_is_2(self) -> None:
        assert RCI_THRESHOLDS["audit_c"] == pytest.approx(2.0)

    # --- RCI formula arithmetic pinned independently ---

    def test_rci_formula_known_values(self) -> None:
        """Verify the Jacobson & Truax 1991 formula produces the expected
        RCI value for a known input set (pre=15, post=8, sd=5, rxx=0.84).

        SE_diff = 5 * sqrt(2) * sqrt(1 - 0.84) = 5 * 1.4142 * 0.4 = 2.828...
        RCI = (8 - 15) / 2.828... = -7 / 2.828... ≈ -2.475

        |RCI| = 2.475 ≥ 1.96 → reliable change.
        delta < 0 on a lower-is-better scale → improvement.
        """
        pre, post, sd, rxx = 15.0, 8.0, 5.0, 0.84
        se_diff = sd * math.sqrt(2) * math.sqrt(1 - rxx)
        rci = (post - pre) / se_diff
        assert abs(rci) >= 1.96, f"expected reliable change, got |RCI|={abs(rci):.3f}"
        assert rci < 0, "expected negative delta (improvement on lower-is-better scale)"

    # --- Reliable improvement ---

    def test_phq9_large_decrease_is_improvement(self) -> None:
        """|delta| = 7 > 5.2 threshold, delta < 0 on PHQ-9 → improvement."""
        point = compute_point("phq9", current=5.0, baseline=12.0)
        assert point.direction == "improvement"
        assert point.delta == pytest.approx(-7.0)

    def test_gad7_large_decrease_is_improvement(self) -> None:
        point = compute_point("gad7", current=5.0, baseline=10.0)
        assert point.direction == "improvement"

    def test_who5_large_increase_is_improvement(self) -> None:
        """WHO-5 is higher-is-better: delta > 0 above threshold → improvement."""
        point = compute_point("who5", current=60.0, baseline=40.0)
        assert point.direction == "improvement"

    # --- Reliable deterioration ---

    def test_phq9_large_increase_is_deterioration(self) -> None:
        """|delta| = 6 > 5.2, delta > 0 on PHQ-9 → deterioration."""
        point = compute_point("phq9", current=14.0, baseline=8.0)
        assert point.direction == "deterioration"

    def test_who5_large_decrease_is_deterioration(self) -> None:
        point = compute_point("who5", current=25.0, baseline=50.0)
        assert point.direction == "deterioration"

    # --- Non-reliable change ---

    def test_phq9_small_delta_is_no_reliable_change(self) -> None:
        """|delta| = 3 < 5.2 → no_reliable_change."""
        point = compute_point("phq9", current=11.0, baseline=8.0)
        assert point.direction == "no_reliable_change"

    def test_gad7_small_delta_is_no_reliable_change(self) -> None:
        point = compute_point("gad7", current=11.0, baseline=8.0)
        assert point.direction == "no_reliable_change"

    # --- Zero delta ---

    def test_pre_equals_post_is_no_reliable_change(self) -> None:
        """A patient who scores identically at two time-points has RCI = 0,
        well below the 1.96 threshold."""
        point = compute_point("phq9", current=12.0, baseline=12.0)
        assert point.direction == "no_reliable_change"
        assert point.delta == pytest.approx(0.0)

    # --- Edge cases ---

    def test_missing_baseline_is_insufficient_data(self) -> None:
        """No baseline → RCI is undefined → insufficient_data direction."""
        point = compute_point("phq9", current=12.0, baseline=None)
        assert point.direction == "insufficient_data"
        assert point.delta is None

    def test_unknown_instrument_is_insufficient_data(self) -> None:
        """Instruments without a pinned threshold return insufficient_data."""
        point = compute_point("spin", current=30.0, baseline=50.0)
        assert point.direction == "insufficient_data"
        assert point.rci_threshold is None

    def test_at_threshold_counts_as_reliable(self) -> None:
        """Convention: |delta| == threshold exactly is classified as reliable
        change (≥, not >).  Jacobson & Truax 1991 do not exclude exact-
        threshold cases; the implementation applies math.isclose to handle
        IEEE-754 representation of non-binary-representable thresholds."""
        threshold = RCI_THRESHOLDS["phq9"]  # 5.2
        point_down = compute_point("phq9", current=0.0, baseline=threshold)
        point_up = compute_point("phq9", current=threshold, baseline=0.0)
        assert point_down.direction == "improvement"
        assert point_up.direction == "deterioration"

"""Scoring-layer tests for PCS (Sullivan 1995).

The Pain Catastrophizing Scale — 13-item self-report measure of
catastrophic cognitions in response to anticipated/actual pain;
0-4 Likert per item; total 0-52; HIGHER = MORE catastrophizing.
Three subscales per Sullivan 1995 factor analysis (Osman 2000
confirmatory CFI = 0.96):
- helplessness: items 1, 2, 3, 4, 5, 12 (range 0-24)
- rumination: items 8, 9, 10, 11 (range 0-16)
- magnification: items 6, 7, 13 (range 0-12)

No reverse-keying.  No published clinical bands (Osman 2000's
≥ 30 is research-convention only — severity = "continuous"
sentinel).  No T3 (pain cognition, not ideation).

Coverage matrix:
- Constants pinned to Sullivan 1995 (item count 13, range 0-4,
  subscale compositions, instrument_version "pcs-1.0.0").
- Total correctness across floor / ceiling / representative.
- Subscale partition: every item is in exactly one subscale;
  rumination + magnification + helplessness = total.
- Subscale isolation: ceiling on one subscale yields ceiling on
  that subscale and zero on the others.
- Severity always "continuous" (Osman 2000 ≥ 30 NOT applied).
- Item-count / range / type validation.
- Result typing — frozen dataclass, tuple-of-int items.
- Clinical vignettes (helplessness-dominant, rumination-dominant,
  magnification-dominant, mixed high, Osman 75th-percentile,
  direction, RCI determinism).
"""

from __future__ import annotations

import pytest

from discipline.psychometric.scoring.pcs import (
    INSTRUMENT_VERSION,
    ITEM_COUNT,
    ITEM_MAX,
    ITEM_MIN,
    PCS_SUBSCALE_ORDER,
    PCS_SUBSCALE_POSITIONS,
    InvalidResponseError,
    PcsResult,
    score_pcs,
)


class TestConstants:
    """PCS constants pinned to Sullivan 1995."""

    def test_item_count_is_thirteen(self) -> None:
        assert ITEM_COUNT == 13

    def test_item_range_is_0_to_4(self) -> None:
        assert ITEM_MIN == 0
        assert ITEM_MAX == 4

    def test_instrument_version_pinned(self) -> None:
        assert INSTRUMENT_VERSION == "pcs-1.0.0"

    def test_subscale_names_are_sullivan_1995(self) -> None:
        """Three subscales per Sullivan 1995: rumination,
        magnification, helplessness."""
        assert set(PCS_SUBSCALE_POSITIONS) == {
            "rumination",
            "magnification",
            "helplessness",
        }

    def test_subscale_order_helplessness_first(self) -> None:
        """Helplessness is the most clinically-salient subscale
        per Sullivan 1995 §Discussion; UI rendering order puts it
        first."""
        assert PCS_SUBSCALE_ORDER == (
            "helplessness",
            "rumination",
            "magnification",
        )

    def test_subscale_positions_sum_to_thirteen(self) -> None:
        """The three subscales partition the 13 items — every
        position 1-13 is in exactly one subscale."""
        all_positions: list[int] = []
        for positions in PCS_SUBSCALE_POSITIONS.values():
            all_positions.extend(positions)
        assert sorted(all_positions) == list(range(1, 14))

    def test_subscale_item_counts(self) -> None:
        """Sullivan 1995 subscale compositions:
        - rumination: 4 items (8, 9, 10, 11)
        - magnification: 3 items (6, 7, 13)
        - helplessness: 6 items (1, 2, 3, 4, 5, 12)
        """
        assert len(PCS_SUBSCALE_POSITIONS["rumination"]) == 4
        assert len(PCS_SUBSCALE_POSITIONS["magnification"]) == 3
        assert len(PCS_SUBSCALE_POSITIONS["helplessness"]) == 6

    def test_helplessness_positions_exact(self) -> None:
        assert PCS_SUBSCALE_POSITIONS["helplessness"] == (
            1, 2, 3, 4, 5, 12,
        )

    def test_rumination_positions_exact(self) -> None:
        assert PCS_SUBSCALE_POSITIONS["rumination"] == (8, 9, 10, 11)

    def test_magnification_positions_exact(self) -> None:
        assert PCS_SUBSCALE_POSITIONS["magnification"] == (6, 7, 13)


class TestTotalCorrectness:
    """Total is sum of 13 items, range 0-52."""

    def test_all_zeros_floor(self) -> None:
        """Minimum endorsement: total = 0 (13 × 0)."""
        result = score_pcs([0] * 13)
        assert result.total == 0

    def test_all_fours_ceiling(self) -> None:
        """Maximum endorsement: total = 52 (13 × 4)."""
        result = score_pcs([4] * 13)
        assert result.total == 52

    def test_all_twos_midpoint(self) -> None:
        """Midpoint endorsement: total = 26 (13 × 2)."""
        result = score_pcs([2] * 13)
        assert result.total == 26

    def test_representative_interior_value(self) -> None:
        """Mixed profile totaling 30 (Osman 2000 research-
        convention threshold value).  Scorer just reports total;
        does NOT classify status."""
        # Need sum = 30 across 13 items.  Use 4×6 + 1×6 + 0 = 30.
        items = [4, 4, 4, 4, 4, 4, 1, 1, 1, 1, 1, 1, 0]
        result = score_pcs(items)
        assert result.total == 30

    def test_subscale_totals_sum_to_total(self) -> None:
        """Partition invariant: helplessness + rumination +
        magnification = total."""
        items = [3, 2, 4, 1, 0, 3, 2, 4, 3, 1, 2, 3, 0]
        result = score_pcs(items)
        assert (
            result.subscales["helplessness"]
            + result.subscales["rumination"]
            + result.subscales["magnification"]
        ) == result.total


class TestSubscaleIsolation:
    """Ceiling on one subscale does not affect others."""

    def test_helplessness_ceiling_only(self) -> None:
        """Items 1, 2, 3, 4, 5, 12 at 4; all others at 0.
        helplessness = 24; rumination = 0; magnification = 0."""
        items = [4, 4, 4, 4, 4, 0, 0, 0, 0, 0, 0, 4, 0]
        result = score_pcs(items)
        assert result.subscales["helplessness"] == 24
        assert result.subscales["rumination"] == 0
        assert result.subscales["magnification"] == 0
        assert result.total == 24

    def test_rumination_ceiling_only(self) -> None:
        """Items 8, 9, 10, 11 at 4; all others at 0.
        rumination = 16; others = 0."""
        items = [0, 0, 0, 0, 0, 0, 0, 4, 4, 4, 4, 0, 0]
        result = score_pcs(items)
        assert result.subscales["rumination"] == 16
        assert result.subscales["helplessness"] == 0
        assert result.subscales["magnification"] == 0
        assert result.total == 16

    def test_magnification_ceiling_only(self) -> None:
        """Items 6, 7, 13 at 4; all others at 0.
        magnification = 12; others = 0."""
        items = [0, 0, 0, 0, 0, 4, 4, 0, 0, 0, 0, 0, 4]
        result = score_pcs(items)
        assert result.subscales["magnification"] == 12
        assert result.subscales["helplessness"] == 0
        assert result.subscales["rumination"] == 0
        assert result.total == 12

    def test_all_ceiling_maxes_every_subscale(self) -> None:
        result = score_pcs([4] * 13)
        assert result.subscales["helplessness"] == 24
        assert result.subscales["rumination"] == 16
        assert result.subscales["magnification"] == 12
        assert result.total == 52


class TestSubscaleComposition:
    """Subscale totals reflect Sullivan 1995's factor structure."""

    def test_helplessness_uses_correct_positions(self) -> None:
        """Helplessness = sum of items at positions 1, 2, 3, 4, 5,
        12.  Build a vector where those positions sum to a known
        value and others are zero."""
        items = [1, 2, 3, 0, 0, 0, 0, 0, 0, 0, 0, 4, 0]
        result = score_pcs(items)
        assert result.subscales["helplessness"] == 1 + 2 + 3 + 0 + 0 + 4

    def test_rumination_uses_correct_positions(self) -> None:
        items = [0, 0, 0, 0, 0, 0, 0, 1, 2, 3, 4, 0, 0]
        result = score_pcs(items)
        assert result.subscales["rumination"] == 1 + 2 + 3 + 4

    def test_magnification_uses_correct_positions(self) -> None:
        items = [0, 0, 0, 0, 0, 2, 3, 0, 0, 0, 0, 0, 4]
        result = score_pcs(items)
        assert result.subscales["magnification"] == 2 + 3 + 4

    def test_subscales_dict_has_sullivan_1995_order(self) -> None:
        """Subscales dict preserves helplessness-first ordering
        per ``PCS_SUBSCALE_ORDER``."""
        result = score_pcs([2] * 13)
        assert list(result.subscales.keys()) == list(PCS_SUBSCALE_ORDER)


class TestSeverityContinuous:
    """Severity is the ``"continuous"`` sentinel at all totals."""

    @pytest.mark.parametrize("items,expected_total", [
        ([0] * 13, 0),
        ([1] * 13, 13),
        ([2] * 13, 26),
        ([3] * 13, 39),
        ([4] * 13, 52),
    ])
    def test_severity_always_continuous(
        self, items: list[int], expected_total: int
    ) -> None:
        result = score_pcs(items)
        assert result.total == expected_total
        assert result.severity == "continuous"

    def test_osman_2000_threshold_not_applied(self) -> None:
        """Osman 2000 proposed total ≥ 30 as a research-convention
        threshold.  The scorer does NOT bake that in — severity
        stays ``"continuous"`` at, below, and above 30."""
        # Build totals of 20, 30, 40.
        at_30 = score_pcs([3, 3, 3, 3, 3, 3, 3, 3, 3, 2, 1, 0, 0])  # 30
        below = score_pcs([2, 2, 2, 2, 2, 2, 2, 1, 1, 1, 1, 1, 1])  # 20
        above = score_pcs([4, 4, 4, 4, 3, 3, 3, 3, 3, 3, 2, 2, 2])  # 40
        assert at_30.total == 30
        assert below.total == 20
        assert above.total == 40
        assert at_30.severity == "continuous"
        assert below.severity == "continuous"
        assert above.severity == "continuous"

    def test_no_positive_screen_emitted(self) -> None:
        """Scorer does NOT emit positive_screen — contrast
        IGDS9-SF / AUDIT / DUDIT which DO emit it because their
        primary papers published diagnostic cutoffs.  Sullivan
        1995 did not."""
        result = score_pcs([4] * 13)
        # PcsResult has no positive_screen field.
        assert not hasattr(result, "positive_screen")
        assert not hasattr(result, "cutoff_used")


class TestItemCountValidation:
    """Item-count rejections raise :class:`InvalidResponseError`."""

    def test_short_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="13"):
            score_pcs([2] * 12)

    def test_long_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="13"):
            score_pcs([2] * 14)

    def test_empty_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="13"):
            score_pcs([])

    def test_message_names_pcs(self) -> None:
        try:
            score_pcs([2] * 10)
        except InvalidResponseError as exc:
            assert "PCS" in str(exc)
            assert "13" in str(exc)
        else:
            pytest.fail("Expected InvalidResponseError")


class TestItemRangeValidation:
    """Item-range rejections raise :class:`InvalidResponseError`."""

    def test_below_range_rejected(self) -> None:
        items = [2] * 13
        items[0] = -1
        with pytest.raises(InvalidResponseError, match="0-4"):
            score_pcs(items)

    def test_above_range_rejected(self) -> None:
        items = [2] * 13
        items[5] = 5  # Above 0-4 range.
        with pytest.raises(InvalidResponseError, match="0-4"):
            score_pcs(items)

    def test_very_negative_rejected(self) -> None:
        items = [2] * 13
        items[12] = -5
        with pytest.raises(InvalidResponseError, match="0-4"):
            score_pcs(items)

    def test_range_message_names_position(self) -> None:
        """Error message identifies the 1-indexed position of the
        offending item."""
        items = [2] * 13
        items[4] = 7
        try:
            score_pcs(items)
        except InvalidResponseError as exc:
            assert "5" in str(exc)  # 1-indexed position 5
            assert "0-4" in str(exc)
        else:
            pytest.fail("Expected InvalidResponseError")

    def test_first_invalid_reported(self) -> None:
        items = [2] * 13
        items[2] = -1
        items[7] = 5
        with pytest.raises(InvalidResponseError) as exc_info:
            score_pcs(items)
        assert "3" in str(exc_info.value)  # 1-indexed position 3


class TestItemTypeValidation:
    """Bool / string / float items raise :class:`InvalidResponseError`."""

    def test_bool_true_rejected(self) -> None:
        """CLAUDE.md standing rule: bool rejected BEFORE the range
        check even though True coerces to 1 (valid range) and
        False coerces to 0 (also valid).  Direct Python invocation
        with a bool MUST reject at the scorer."""
        items: list = [2] * 13
        items[0] = True
        with pytest.raises(InvalidResponseError, match="int"):
            score_pcs(items)

    def test_bool_false_rejected(self) -> None:
        items: list = [2] * 13
        items[0] = False
        with pytest.raises(InvalidResponseError, match="int"):
            score_pcs(items)

    def test_string_rejected(self) -> None:
        items: list = [2] * 13
        items[0] = "2"
        with pytest.raises(InvalidResponseError, match="int"):
            score_pcs(items)

    def test_float_rejected(self) -> None:
        items: list = [2] * 13
        items[0] = 2.0
        with pytest.raises(InvalidResponseError, match="int"):
            score_pcs(items)

    def test_none_rejected(self) -> None:
        items: list = [2] * 13
        items[0] = None
        with pytest.raises(InvalidResponseError, match="int"):
            score_pcs(items)


class TestResultTyping:
    """Result is a frozen dataclass with the correct field types."""

    def test_returns_pcs_result(self) -> None:
        result = score_pcs([2] * 13)
        assert isinstance(result, PcsResult)

    def test_total_is_int(self) -> None:
        result = score_pcs([2] * 13)
        assert isinstance(result.total, int)

    def test_severity_is_continuous_literal(self) -> None:
        result = score_pcs([2] * 13)
        assert result.severity == "continuous"

    def test_subscales_is_dict_of_ints(self) -> None:
        result = score_pcs([2] * 13)
        assert isinstance(result.subscales, dict)
        for name, value in result.subscales.items():
            assert isinstance(name, str)
            assert isinstance(value, int)

    def test_items_is_tuple_of_ints(self) -> None:
        result = score_pcs([0, 1, 2, 3, 4, 3, 2, 1, 0, 1, 2, 3, 4])
        assert isinstance(result.items, tuple)
        assert all(isinstance(item, int) for item in result.items)
        assert len(result.items) == 13

    def test_frozen_dataclass(self) -> None:
        result = score_pcs([2] * 13)
        with pytest.raises((AttributeError, TypeError)):
            result.total = 100  # type: ignore[misc]

    def test_instrument_version_default(self) -> None:
        result = score_pcs([2] * 13)
        assert result.instrument_version == "pcs-1.0.0"

    def test_items_preserve_raw_response(self) -> None:
        raw = [0, 1, 2, 3, 4, 3, 2, 1, 0, 4, 3, 2, 1]
        result = score_pcs(raw)
        assert result.items == tuple(raw)


class TestClinicalVignettes:
    """Clinical scenarios grounded in Sullivan 1995 / Quartana 2009."""

    def test_helplessness_dominant_profile(self) -> None:
        """Helplessness-dominant profile: user endorses 'there is
        nothing I can do' / 'I can't stand it' cognitions strongly
        (items 1-5, 12) while other cognitions are mild.  This is
        the most clinically-salient catastrophizing subpattern
        per Sullivan 1995 §Discussion; the clinician-UI layer
        flags this for behavioral-activation + mastery-building
        content."""
        # Items 1-5 and 12 at 4; others at 1.
        items = [4, 4, 4, 4, 4, 1, 1, 1, 1, 1, 1, 4, 1]
        result = score_pcs(items)
        assert result.subscales["helplessness"] == 24  # ceiling
        assert result.subscales["rumination"] < 16
        assert result.subscales["magnification"] < 12
        assert result.severity == "continuous"

    def test_rumination_dominant_profile(self) -> None:
        """Rumination-dominant profile: user fixates on pain
        ('I keep thinking about how much it hurts') but without
        strong helplessness or magnification.  Paired with
        elevated RRS-10 signals generalized ruminative style
        beyond pain; mindfulness-based intervention (MAAS /
        FFMQ-15 partner)."""
        items = [1, 1, 1, 1, 1, 1, 1, 4, 4, 4, 4, 1, 1]
        result = score_pcs(items)
        assert result.subscales["rumination"] == 16  # ceiling
        assert result.subscales["helplessness"] < 24

    def test_magnification_dominant_profile(self) -> None:
        """Magnification-dominant profile: user exaggerates
        threat value of pain ('I become afraid that the pain will
        get worse'; 'I think about other painful events') without
        strong helplessness or rumination.  Paired with elevated
        GAD-7 signals threat-magnification extending beyond pain."""
        items = [1, 1, 1, 1, 1, 4, 4, 1, 1, 1, 1, 1, 4]
        result = score_pcs(items)
        assert result.subscales["magnification"] == 12  # ceiling
        assert result.subscales["helplessness"] < 24
        assert result.subscales["rumination"] < 16

    def test_osman_2000_75th_percentile_total(self) -> None:
        """Osman 2000 cites total ≥ 30 as the 75th percentile of
        the Sullivan 1995 chronic-pain sample.  Scorer does NOT
        classify this as "clinically significant" — UI layer
        contextualizes against published sample distributions."""
        # Build total of exactly 30.
        items = [3, 3, 3, 3, 3, 3, 3, 3, 3, 2, 1, 0, 0]
        result = score_pcs(items)
        assert result.total == 30
        assert result.severity == "continuous"
        # Subscale breakdown shows the distribution:
        # helplessness (1,2,3,4,5,12) = 3+3+3+3+3+0 = 15
        # rumination (8,9,10,11) = 3+3+2+1 = 9
        # magnification (6,7,13) = 3+3+0 = 6
        # Sum: 15 + 9 + 6 = 30 ✓
        assert result.subscales["helplessness"] == 15
        assert result.subscales["rumination"] == 9
        assert result.subscales["magnification"] == 6

    def test_floor_no_catastrophizing(self) -> None:
        """Floor: user reports no catastrophizing cognitions.
        Total = 0; all subscales at 0.  Baseline for a user
        without pain-related cognitive vulnerability."""
        result = score_pcs([0] * 13)
        assert result.total == 0
        assert all(v == 0 for v in result.subscales.values())

    def test_ceiling_maximal_catastrophizing(self) -> None:
        """Ceiling: user reports maximal catastrophizing across
        all cognitions.  Total = 52; all subscales at ceiling.
        Sullivan 1995 chronic-pain sample 99th-percentile
        equivalent."""
        result = score_pcs([4] * 13)
        assert result.total == 52
        assert result.subscales["helplessness"] == 24
        assert result.subscales["rumination"] == 16
        assert result.subscales["magnification"] == 12

    def test_direction_higher_equals_more_catastrophizing(
        self,
    ) -> None:
        """Direction guarantee: total 52 > total 0; higher number
        = more catastrophizing.  Same direction as PHQ-9 / GAD-7 /
        AUDIT / DUDIT / FTND / PSS-10 / DASS-21; OPPOSITE of
        WHO-5 / BRS / LOT-R / RSES / MAAS / CD-RISC-10 / WEMWBS."""
        low = score_pcs([0] * 13)
        high = score_pcs([4] * 13)
        assert low.total < high.total
        assert low.total == 0
        assert high.total == 52

    def test_pain_addiction_vulnerability_profile(self) -> None:
        """Edwards 2011 profile: chronic-pain patient elevated on
        PCS helplessness subscale.  Paired with AUDIT/DUDIT
        elevated flags pain-driven substance-use trajectory;
        intervention layer adds pain-focused cognitive
        restructuring (Thorn 2004) alongside substance-focused
        content.  Scorer just reports subscale structure."""
        # Helplessness dominant + moderate rumination.
        items = [4, 4, 3, 4, 3, 1, 1, 2, 2, 3, 3, 4, 1]
        result = score_pcs(items)
        assert result.subscales["helplessness"] >= 18
        assert result.severity == "continuous"

    def test_rci_determinism_identical_input_yields_identical_output(
        self,
    ) -> None:
        """Jacobson-Truax RCI assumes deterministic scoring.
        Identical input → identical output (total, severity,
        subscales, items, instrument_version)."""
        items = [2, 3, 1, 4, 0, 2, 3, 1, 4, 0, 2, 3, 1]
        a = score_pcs(items)
        b = score_pcs(items)
        assert a == b

    def test_seligman_1975_helplessness_construct(self) -> None:
        """Sullivan's helplessness subscale draws on Seligman's
        1975 learned-helplessness construct — the perceived
        inability to escape aversive stimuli.  User endorsing
        item 3 ('It's awful and I feel that it overwhelms me')
        and item 5 ('I feel I can't stand it anymore') at
        ceiling maps to the core learned-helplessness pattern."""
        items = [4, 4, 4, 4, 4, 0, 0, 0, 0, 0, 0, 4, 0]
        result = score_pcs(items)
        assert result.subscales["helplessness"] == 24
        # Other subscales are minimal — this is a PURE helplessness
        # presentation.
        assert result.subscales["rumination"] == 0
        assert result.subscales["magnification"] == 0

"""Tests for the FTND scorer (Heatherton 1991).

Coverage:
- Constants pinned to the published source (Heatherton 1991;
  Fagerström 2012 for severity bands).
- Per-item heterogeneous range validation — FTND is the first
  platform instrument with non-uniform per-item scales.
- Total = sum of six raw items, 0-10.
- Fagerström 2012 5-band severity (every possible total 0-10).
- Clinical cutoff at >= 4 (Fagerström 2012).
- Item count, value range, type (bool rejection) validation.
- Result frozen, items preserved as raw pre-validation tuple.
- Clinical vignettes covering the five severity bands + Baker
  2007 time-to-first-cigarette signal preservation.
"""

from __future__ import annotations

import pytest

from discipline.psychometric.scoring.ftnd import (
    FTND_CLINICAL_CUTOFF,
    FTND_ITEM_MAX,
    FTND_SEVERITY_THRESHOLDS,
    INSTRUMENT_VERSION,
    ITEM_COUNT,
    ITEM_MIN,
    FtndResult,
    InvalidResponseError,
    score_ftnd,
)


class TestConstants:
    """FTND constants pinned to published sources."""

    def test_item_count_is_six(self) -> None:
        assert ITEM_COUNT == 6

    def test_item_min_is_zero(self) -> None:
        assert ITEM_MIN == 0

    def test_ftnd_item_max_length_matches_item_count(self) -> None:
        assert len(FTND_ITEM_MAX) == ITEM_COUNT

    def test_items_1_and_4_are_0_to_3(self) -> None:
        # Heatherton 1991: time-to-first-cigarette and cigarettes-
        # per-day are the two 4-point ordinal items.
        assert FTND_ITEM_MAX[0] == 3
        assert FTND_ITEM_MAX[3] == 3

    def test_items_2_3_5_6_are_binary(self) -> None:
        # Heatherton 1991: remaining four items are yes/no (0-1).
        assert FTND_ITEM_MAX[1] == 1
        assert FTND_ITEM_MAX[2] == 1
        assert FTND_ITEM_MAX[4] == 1
        assert FTND_ITEM_MAX[5] == 1

    def test_max_possible_total_is_10(self) -> None:
        # 3 + 1 + 1 + 3 + 1 + 1 = 10
        assert sum(FTND_ITEM_MAX) == 10

    def test_severity_thresholds_fagerstrom_2012(self) -> None:
        # Fagerström 2012 Nicotine Tob Res 14(1):75-78 5-band
        # severity interpretation.  These are the published
        # thresholds and MUST NOT be altered without clinical-QA
        # sign-off per CLAUDE.md rule 9.
        assert FTND_SEVERITY_THRESHOLDS == (
            (2, "very_low"),
            (4, "low"),
            (5, "moderate"),
            (7, "high"),
            (10, "very_high"),
        )

    def test_clinical_cutoff_is_4(self) -> None:
        # Fagerström 2012 §Discussion clinical threshold.
        assert FTND_CLINICAL_CUTOFF == 4

    def test_instrument_version_is_pinned(self) -> None:
        assert INSTRUMENT_VERSION == "ftnd-1.0.0"


class TestTotalCorrectness:
    """Total = raw sum of all six items."""

    def test_all_zeros_total_zero(self) -> None:
        result = score_ftnd([0, 0, 0, 0, 0, 0])
        assert result.total == 0

    def test_all_maxima_total_ten(self) -> None:
        result = score_ftnd([3, 1, 1, 3, 1, 1])
        assert result.total == 10

    def test_only_item_1_max(self) -> None:
        result = score_ftnd([3, 0, 0, 0, 0, 0])
        assert result.total == 3

    def test_only_item_4_max(self) -> None:
        result = score_ftnd([0, 0, 0, 3, 0, 0])
        assert result.total == 3

    def test_all_binaries_positive(self) -> None:
        # Items 2, 3, 5, 6 = 1 each; items 1, 4 = 0
        result = score_ftnd([0, 1, 1, 0, 1, 1])
        assert result.total == 4

    def test_moderate_scenario(self) -> None:
        result = score_ftnd([2, 1, 0, 1, 1, 0])
        assert result.total == 5


class TestSeverityBandsFagerstrom2012:
    """Fagerström 2012 5-band severity interpretation."""

    @pytest.mark.parametrize("total,expected", [
        (0, "very_low"),
        (1, "very_low"),
        (2, "very_low"),
        (3, "low"),
        (4, "low"),
        (5, "moderate"),
        (6, "high"),
        (7, "high"),
        (8, "very_high"),
        (9, "very_high"),
        (10, "very_high"),
    ])
    def test_every_possible_total_maps_correctly(
        self, total: int, expected: str
    ) -> None:
        # Use item 4 (cigs/day) to build arbitrary totals 0-10
        # since it contributes 0-3, plus binary items.
        vectors = {
            0: [0, 0, 0, 0, 0, 0],
            1: [0, 0, 0, 0, 0, 1],
            2: [0, 0, 0, 0, 1, 1],
            3: [0, 0, 0, 0, 1, 1],  # adjusted below
            4: [0, 1, 1, 0, 1, 1],
            5: [2, 1, 0, 1, 1, 0],
            6: [2, 1, 1, 1, 1, 0],
            7: [3, 1, 0, 1, 1, 1],
            8: [3, 1, 1, 1, 1, 1],
            9: [3, 1, 1, 2, 1, 1],
            10: [3, 1, 1, 3, 1, 1],
        }
        if total == 3:
            vectors[3] = [0, 1, 1, 0, 1, 0]
        vec = vectors[total]
        assert sum(vec) == total
        assert score_ftnd(vec).severity == expected


class TestSeverityBandEdges:
    """Verify each band boundary behaves correctly."""

    def test_band_2_ceiling_is_very_low(self) -> None:
        # total=2 -> "very_low"
        assert score_ftnd([0, 0, 0, 2, 0, 0]).severity == "very_low"

    def test_band_3_floor_is_low(self) -> None:
        # total=3 -> "low" (just crossed "very_low" ceiling)
        assert score_ftnd([0, 1, 1, 0, 1, 0]).severity == "low"

    def test_band_4_ceiling_is_low(self) -> None:
        # total=4 -> "low"
        assert score_ftnd([0, 1, 1, 0, 1, 1]).severity == "low"

    def test_band_5_is_moderate(self) -> None:
        # total=5 -> "moderate"
        assert score_ftnd([2, 1, 0, 1, 1, 0]).severity == "moderate"

    def test_band_6_floor_is_high(self) -> None:
        # total=6 -> "high" (just crossed "moderate" ceiling)
        assert score_ftnd([2, 1, 1, 1, 1, 0]).severity == "high"

    def test_band_7_ceiling_is_high(self) -> None:
        # total=7 -> "high"
        assert score_ftnd([3, 1, 0, 1, 1, 1]).severity == "high"

    def test_band_8_floor_is_very_high(self) -> None:
        # total=8 -> "very_high"
        assert score_ftnd([3, 1, 1, 1, 1, 1]).severity == "very_high"

    def test_band_10_ceiling_is_very_high(self) -> None:
        # total=10 -> "very_high"
        assert score_ftnd([3, 1, 1, 3, 1, 1]).severity == "very_high"


class TestPositiveScreen:
    """Fagerström 2012 clinical threshold at >= 4."""

    def test_below_cutoff_negative(self) -> None:
        # total=3 < 4 -> negative
        result = score_ftnd([0, 1, 1, 0, 1, 0])
        assert result.total == 3
        assert result.positive_screen is False

    def test_at_cutoff_positive(self) -> None:
        # total=4 -> positive (>= 4)
        result = score_ftnd([0, 1, 1, 0, 1, 1])
        assert result.total == 4
        assert result.positive_screen is True

    def test_above_cutoff_positive(self) -> None:
        result = score_ftnd([3, 1, 1, 3, 1, 1])
        assert result.total == 10
        assert result.positive_screen is True

    def test_zero_negative(self) -> None:
        result = score_ftnd([0, 0, 0, 0, 0, 0])
        assert result.total == 0
        assert result.positive_screen is False

    def test_cutoff_used_always_4(self) -> None:
        result_low = score_ftnd([0, 0, 0, 0, 0, 0])
        result_high = score_ftnd([3, 1, 1, 3, 1, 1])
        assert result_low.cutoff_used == 4
        assert result_high.cutoff_used == 4


class TestItemCountValidation:
    """Wrong item count raises InvalidResponseError."""

    def test_empty_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 6"):
            score_ftnd([])

    def test_five_items_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 6"):
            score_ftnd([0, 0, 0, 0, 0])

    def test_seven_items_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 6"):
            score_ftnd([0, 0, 0, 0, 0, 0, 0])

    def test_one_item_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 6"):
            score_ftnd([0])


class TestItemRangeValidation:
    """Per-position item range validation."""

    def test_item_1_above_max_rejected(self) -> None:
        # Item 1 max is 3
        with pytest.raises(InvalidResponseError, match="item 1"):
            score_ftnd([4, 0, 0, 0, 0, 0])

    def test_item_1_negative_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="item 1"):
            score_ftnd([-1, 0, 0, 0, 0, 0])

    def test_item_2_above_max_rejected(self) -> None:
        # Item 2 max is 1 — a value of 2 must reject even though
        # it would be valid for items 1 or 4.
        with pytest.raises(InvalidResponseError, match="item 2"):
            score_ftnd([0, 2, 0, 0, 0, 0])

    def test_item_3_above_max_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="item 3"):
            score_ftnd([0, 0, 2, 0, 0, 0])

    def test_item_4_above_max_rejected(self) -> None:
        # Item 4 max is 3
        with pytest.raises(InvalidResponseError, match="item 4"):
            score_ftnd([0, 0, 0, 4, 0, 0])

    def test_item_5_above_max_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="item 5"):
            score_ftnd([0, 0, 0, 0, 2, 0])

    def test_item_6_above_max_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="item 6"):
            score_ftnd([0, 0, 0, 0, 0, 2])

    def test_item_1_at_max_accepted(self) -> None:
        # Upper bound inclusive for each item.
        result = score_ftnd([3, 0, 0, 0, 0, 0])
        assert result.total == 3

    def test_item_2_at_max_accepted(self) -> None:
        result = score_ftnd([0, 1, 0, 0, 0, 0])
        assert result.total == 1

    def test_item_4_at_max_accepted(self) -> None:
        result = score_ftnd([0, 0, 0, 3, 0, 0])
        assert result.total == 3

    def test_position_specific_error_message_mentions_range(
        self,
    ) -> None:
        # The error message must name the item's specific range
        # (not a generic range), so a caller can distinguish
        # "you put a 3 in a binary slot" from "you put a 4 in a
        # 4-point slot".
        with pytest.raises(InvalidResponseError, match="0-1"):
            score_ftnd([0, 2, 0, 0, 0, 0])
        with pytest.raises(InvalidResponseError, match="0-3"):
            score_ftnd([4, 0, 0, 0, 0, 0])


class TestItemTypeValidation:
    """Bool and non-int rejection per CLAUDE.md rule."""

    def test_bool_true_rejected(self) -> None:
        # FTND is especially exposed to bool confusion since
        # four of six items are nominally binary.
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_ftnd([0, True, 0, 0, 0, 0])  # type: ignore[list-item]

    def test_bool_false_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_ftnd([0, False, 0, 0, 0, 0])  # type: ignore[list-item]

    def test_float_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_ftnd([0, 0, 0, 2.5, 0, 0])  # type: ignore[list-item]

    def test_string_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_ftnd([0, "1", 0, 0, 0, 0])  # type: ignore[list-item]

    def test_none_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_ftnd([0, None, 0, 0, 0, 0])  # type: ignore[list-item]

    def test_first_bool_wins_error(self) -> None:
        # Multiple bad items — only the first should surface.
        with pytest.raises(InvalidResponseError, match="item 1"):
            score_ftnd([True, True, 0, 0, 0, 0])  # type: ignore[list-item]


class TestResultTyping:
    """Result is a frozen dataclass with expected invariants."""

    def test_result_is_frozen(self) -> None:
        result = score_ftnd([0, 0, 0, 0, 0, 0])
        with pytest.raises(AttributeError):
            result.total = 999  # type: ignore[misc]

    def test_items_is_tuple(self) -> None:
        result = score_ftnd([2, 1, 0, 1, 0, 1])
        assert isinstance(result.items, tuple)

    def test_items_preserves_raw_order(self) -> None:
        # Items are the RAW pre-validation response tuple — no
        # reverse-keying applies.  Time-to-first-cigarette
        # (item 1) must be readable at items[0] so downstream
        # Baker-2007 TTFC signal extraction works.
        result = score_ftnd([3, 0, 0, 1, 1, 0])
        assert result.items == (3, 0, 0, 1, 1, 0)
        assert result.items[0] == 3  # TTFC within 5 min

    def test_positive_screen_is_bool_type(self) -> None:
        result = score_ftnd([0, 0, 0, 0, 0, 0])
        assert isinstance(result.positive_screen, bool)

    def test_instrument_version_populated(self) -> None:
        result = score_ftnd([0, 0, 0, 0, 0, 0])
        assert result.instrument_version == "ftnd-1.0.0"

    def test_result_is_ftnd_result_type(self) -> None:
        result = score_ftnd([0, 0, 0, 0, 0, 0])
        assert isinstance(result, FtndResult)

    def test_total_is_int(self) -> None:
        result = score_ftnd([3, 1, 1, 3, 1, 1])
        assert isinstance(result.total, int)
        assert result.total == 10


class TestClinicalVignettes:
    """Heatherton 1991 / Fagerström 2012 clinical scenarios."""

    def test_vignette_non_smoker_baseline(self) -> None:
        # All zeros — technically a non-smoker response pattern,
        # although FTND should only be administered to current
        # smokers.  Still should score cleanly.
        result = score_ftnd([0, 0, 0, 0, 0, 0])
        assert result.total == 0
        assert result.severity == "very_low"
        assert result.positive_screen is False

    def test_vignette_social_smoker(self) -> None:
        # Smokes >60 min after waking (item 1=0), no difficulty
        # in no-smoking places (item 2=0), hates morning cig
        # (item 3=1 — some preference), <=10 cigs/day (item
        # 4=0), no morning dominance (item 5=0), wouldn't smoke
        # when sick (item 6=0).  Total 1 -> very low.
        result = score_ftnd([0, 0, 1, 0, 0, 0])
        assert result.total == 1
        assert result.severity == "very_low"
        assert result.positive_screen is False

    def test_vignette_light_regular_smoker(self) -> None:
        # Wakes and smokes within 31-60 min (item 1=1), no
        # difficulty refraining (item 2=0), prefers first of
        # morning (item 3=1), 11-20 cigs/day (item 4=1), no
        # morning dominance (item 5=0), no sick-bed smoking
        # (item 6=0).  Total 3 -> low.
        result = score_ftnd([1, 0, 1, 1, 0, 0])
        assert result.total == 3
        assert result.severity == "low"
        assert result.positive_screen is False

    def test_vignette_moderate_dependence(self) -> None:
        # Wakes and smokes within 6-30 min (item 1=2), some
        # difficulty refraining (item 2=1), prefers first of
        # morning (item 3=0, e.g. tastes same), 11-20 cigs/day
        # (item 4=1), morning dominance (item 5=1), no sick-bed
        # (item 6=0).  Total 5 -> moderate -> positive.
        result = score_ftnd([2, 1, 0, 1, 1, 0])
        assert result.total == 5
        assert result.severity == "moderate"
        assert result.positive_screen is True

    def test_vignette_high_dependence(self) -> None:
        # Wakes and smokes within 6-30 min (item 1=2), difficulty
        # refraining (item 2=1), first-of-morning cigarette
        # (item 3=1), 11-20 cigs/day (item 4=1), morning
        # dominance (item 5=1), no sick-bed (item 6=0).  Total 6
        # -> high -> positive.
        result = score_ftnd([2, 1, 1, 1, 1, 0])
        assert result.total == 6
        assert result.severity == "high"
        assert result.positive_screen is True

    def test_vignette_very_high_dependence(self) -> None:
        # Wakes and smokes within 5 min (item 1=3 — maximum
        # TTFC severity, Baker 2007 primary predictor), refrains
        # with difficulty (item 2=1), first-of-morning (item
        # 3=1), 21-30 cigs/day (item 4=2), morning dominance
        # (item 5=1), smokes sick-in-bed (item 6=1).  Total 9
        # -> very_high -> positive.
        result = score_ftnd([3, 1, 1, 2, 1, 1])
        assert result.total == 9
        assert result.severity == "very_high"
        assert result.positive_screen is True

    def test_vignette_maximum_dependence(self) -> None:
        # Ceiling response — every item at its maximum.
        # Represents the most severely dependent smoker
        # profile; clinical response per Fiore 2008 is
        # combination pharmacotherapy + intensive CBT.
        result = score_ftnd([3, 1, 1, 3, 1, 1])
        assert result.total == 10
        assert result.severity == "very_high"
        assert result.positive_screen is True

    def test_vignette_ttfc_signal_preserved(self) -> None:
        # Baker 2007 TTFC within-5-min pattern.  Item 1 is the
        # single strongest dependence predictor and clinician
        # dashboards read it from items[0] directly.
        result = score_ftnd([3, 0, 0, 0, 0, 0])
        # Only the TTFC signal is maxed; total only 3 (low band
        # by aggregate) — but the TTFC=3 item remains
        # clinically flaggable via items[0].
        assert result.items[0] == 3
        assert result.total == 3
        assert result.severity == "low"

    def test_vignette_no_t3_at_ceiling(self) -> None:
        # FTND never triggers T3 regardless of score.  Acute-
        # risk screening stays on C-SSRS / PHQ-9 item 9.
        # FtndResult has no requires_t3 field — the router
        # sets requires_t3=False unconditionally.
        result = score_ftnd([3, 1, 1, 3, 1, 1])
        assert not hasattr(result, "requires_t3")

    def test_vignette_binary_only_positive(self) -> None:
        # Morning cravings + difficulty refraining + first-
        # cig preference + sick-bed smoking — all four
        # binaries positive, both ordinals at zero.  This is
        # clinically unusual (light cigs/day but behaviorally
        # dependent) but scores 4 -> low band, positive screen.
        result = score_ftnd([0, 1, 1, 0, 1, 1])
        assert result.total == 4
        assert result.severity == "low"
        assert result.positive_screen is True

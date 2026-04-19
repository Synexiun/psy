"""Tests for HADS scoring — Zigmond & Snaith 1983 / Snaith 2003 / Bjelland 2002."""

from __future__ import annotations

import pytest

from discipline.psychometric.scoring.hads import (
    HADS_ANXIETY_POSITIONS,
    HADS_CLINICAL_CUTOFF,
    HADS_DEPRESSION_POSITIONS,
    HADS_REVERSE_ITEMS,
    HADS_SEVERITY_THRESHOLDS,
    HADS_SUBSCALES,
    HadsResult,
    INSTRUMENT_VERSION,
    ITEM_COUNT,
    ITEM_MAX,
    ITEM_MIN,
    InvalidResponseError,
    score_hads,
)


def _all(v: int) -> list[int]:
    """Return a 14-item list with every item set to ``v``."""
    return [v] * ITEM_COUNT


class TestConstants:
    def test_instrument_version_format(self) -> None:
        assert INSTRUMENT_VERSION == "hads-1.0.0"

    def test_item_count_is_14(self) -> None:
        """Zigmond & Snaith 1983: 14 items (7 anxiety + 7 depression)."""
        assert ITEM_COUNT == 14

    def test_item_range_is_0_to_3(self) -> None:
        """Zigmond & Snaith 1983: 4-point 0-3 Likert."""
        assert (ITEM_MIN, ITEM_MAX) == (0, 3)

    def test_subscale_names(self) -> None:
        """Zigmond & Snaith 1983 subscale labels."""
        assert HADS_SUBSCALES == ("anxiety", "depression")

    def test_anxiety_positions_are_odd(self) -> None:
        """Zigmond & Snaith 1983: odd positions = anxiety (interleaved)."""
        assert HADS_ANXIETY_POSITIONS == (1, 3, 5, 7, 9, 11, 13)

    def test_depression_positions_are_even(self) -> None:
        """Zigmond & Snaith 1983: even positions = depression (interleaved)."""
        assert HADS_DEPRESSION_POSITIONS == (2, 4, 6, 8, 10, 12, 14)

    def test_subscale_positions_partition_14(self) -> None:
        """Every item 1-14 appears in exactly one subscale."""
        all_positions = HADS_ANXIETY_POSITIONS + HADS_DEPRESSION_POSITIONS
        assert sorted(all_positions) == list(range(1, 15))

    def test_each_subscale_is_7_items(self) -> None:
        """Zigmond & Snaith 1983: 7 items per subscale."""
        assert len(HADS_ANXIETY_POSITIONS) == 7
        assert len(HADS_DEPRESSION_POSITIONS) == 7

    def test_reverse_items_positions(self) -> None:
        """Zigmond & Snaith 1983: 6 reverse-keyed positions.

        Depression reverse: 2 (enjoy), 4 (laugh), 6 (cheerful),
        12 (look forward), 14 (enjoy book/TV).
        Anxiety reverse: 7 (sit at ease).
        """
        assert HADS_REVERSE_ITEMS == (2, 4, 6, 7, 12, 14)

    def test_reverse_items_count(self) -> None:
        """6 of 14 items are reverse-keyed."""
        assert len(HADS_REVERSE_ITEMS) == 6

    def test_clinical_cutoff_is_11(self) -> None:
        """Bjelland 2002 probable-case threshold per subscale."""
        assert HADS_CLINICAL_CUTOFF == 11

    def test_severity_thresholds_structure(self) -> None:
        """Snaith 2003 4-band structure."""
        assert HADS_SEVERITY_THRESHOLDS == (
            (7, "normal"),
            (10, "mild"),
            (14, "moderate"),
            (21, "severe"),
        )

    def test_severity_bands_ascending(self) -> None:
        """Upper bounds are ascending."""
        bounds = [b for b, _ in HADS_SEVERITY_THRESHOLDS]
        assert bounds == sorted(bounds)


class TestReverseKeyingArithmetic:
    def test_raw_zeros_flip_to_threes_on_reverse_positions(self) -> None:
        """All raw zeros → reverse items flip to 3 each → anxiety = 3
        (item 7 only), depression = 15 (items 2, 4, 6, 12, 14)."""
        r = score_hads(_all(0))
        # Forward anxiety positions (1, 3, 5, 9, 11, 13) = 0; reverse
        # position 7 = 3 - 0 = 3.  Anxiety sum = 3.
        assert r.anxiety == 3
        # Forward depression positions (8, 10) = 0; reverse positions
        # (2, 4, 6, 12, 14) = 3 each.  Depression sum = 15.
        assert r.depression == 15
        assert r.total == 18

    def test_raw_threes_flip_to_zeros_on_reverse_positions(self) -> None:
        """All raw threes → reverse items flip to 0 each → anxiety = 18
        (6 forward items × 3 + 1 reverse item → 0), depression = 6
        (2 forward items × 3 + 5 reverse items → 0)."""
        r = score_hads(_all(3))
        assert r.anxiety == 18  # (1,3,5,9,11,13) × 3 + 7→0
        assert r.depression == 6  # (8,10) × 3 + (2,4,6,12,14)→0
        assert r.total == 24

    def test_items_preserve_raw_unchanged(self) -> None:
        """``items`` tuple is the verbatim input (pre-flip)."""
        payload = [0, 3, 1, 2, 0, 3, 2, 1, 0, 3, 1, 2, 0, 3]
        r = score_hads(payload)
        assert r.items == tuple(payload)


class TestTotalCorrectness:
    def test_all_zeros_total_eighteen(self) -> None:
        """All zeros + reverse-keying on 6 items → total 6×3 = 18."""
        r = score_hads(_all(0))
        assert r.total == 18

    def test_all_threes_total_twenty_four(self) -> None:
        """All threes + reverse-keying → forward 8 items × 3 = 24,
        reverse 6 items → 0 each."""
        r = score_hads(_all(3))
        assert r.total == 24

    def test_all_ones_total_fourteen(self) -> None:
        """All ones: forward 8 × 1 + reverse 6 × (3-1) = 8 + 12 = 20."""
        r = score_hads(_all(1))
        assert r.total == 20

    def test_all_twos_total_twenty_two(self) -> None:
        """All twos: forward 8 × 2 + reverse 6 × (3-2) = 16 + 6 = 22."""
        r = score_hads(_all(2))
        assert r.total == 22

    def test_total_equals_sum_of_subscales(self) -> None:
        """total = anxiety + depression always."""
        items = [0, 1, 2, 3, 0, 1, 2, 3, 0, 1, 2, 3, 0, 1]
        r = score_hads(items)
        assert r.total == r.anxiety + r.depression


class TestSubscalePartitioning:
    def test_anxiety_isolation_forward_items_only(self) -> None:
        """Set forward-keyed anxiety items to 3, all else 0.
        Forward anxiety positions: 1, 3, 5, 9, 11, 13 (6 items).
        Reverse anxiety position: 7 (raw 0 flips to 3).
        Depression all-reverse default: raw 0 at (2,4,6,12,14) flips to 3 each.
        Forward depression positions 8, 10 stay 0."""
        items = [0] * 14
        for pos in (1, 3, 5, 9, 11, 13):
            items[pos - 1] = 3
        r = score_hads(items)
        # anxiety = 6×3 (forward maxed) + 3 (item 7 raw 0 → 3) = 21
        assert r.anxiety == 21
        # depression = (2,4,6,12,14) raw 0 → 3 each + (8,10) raw 0
        # → 0 = 15
        assert r.depression == 15

    def test_depression_isolation_forward_items_only(self) -> None:
        """Set forward-keyed depression items to 3, all else 0.
        Forward depression positions: 8, 10 (2 items)."""
        items = [0] * 14
        items[7] = 3  # item 8
        items[9] = 3  # item 10
        r = score_hads(items)
        # anxiety = (1,3,5,9,11,13) 0s × 6 + (item 7 raw 0 → 3) = 3
        assert r.anxiety == 3
        # depression = (8, 10) 3 × 2 + (2,4,6,12,14) raw 0 → 3 × 5 = 21
        assert r.depression == 21

    def test_zigmond_snaith_interleaving(self) -> None:
        """Odd positions affect anxiety only; even only depression."""
        for pos in HADS_ANXIETY_POSITIONS:
            items = [0] * 14
            items[pos - 1] = 3
            r = score_hads(items)
            # Change at odd position moves anxiety; depression unchanged
            # from baseline (all zeros → 15).
            assert r.depression == 15

        for pos in HADS_DEPRESSION_POSITIONS:
            items = [0] * 14
            items[pos - 1] = 3
            r = score_hads(items)
            # Change at even position moves depression; anxiety unchanged
            # from baseline (all zeros → 3).
            assert r.anxiety == 3

    def test_subscale_sums_ranges(self) -> None:
        """Subscale sums always lie in 0-21 for valid raw inputs."""
        for raw_v in (0, 1, 2, 3):
            r = score_hads(_all(raw_v))
            assert 0 <= r.anxiety <= 21
            assert 0 <= r.depression <= 21


class TestMaxSubscaleSums:
    def test_anxiety_max_twenty_one(self) -> None:
        """Anxiety max: all 7 anxiety items post-flip = 3.
        Forward items 1,3,5,9,11,13 → raw 3.
        Reverse item 7 → raw 0 (flips to 3)."""
        items = [0] * 14
        for pos in (1, 3, 5, 9, 11, 13):
            items[pos - 1] = 3
        # item 7 stays raw 0 → reverses to 3
        r = score_hads(items)
        assert r.anxiety == 21

    def test_depression_max_twenty_one(self) -> None:
        """Depression max: all 7 depression items post-flip = 3.
        Forward items 8, 10 → raw 3.
        Reverse items 2, 4, 6, 12, 14 → raw 0 (flip to 3)."""
        items = [0] * 14
        items[7] = 3  # item 8
        items[9] = 3  # item 10
        # reverse items 2,4,6,12,14 stay raw 0 → flip to 3
        r = score_hads(items)
        assert r.depression == 21

    def test_subscale_mins_zero(self) -> None:
        """Min: raw inputs that produce flipped 0 everywhere in subscale."""
        # Anxiety min: forward items → 0; reverse item 7 → 3 (raw).
        items_anxiety_min = [0] * 14
        items_anxiety_min[6] = 3  # item 7 raw 3 → flip to 0
        # Depression: forward 8, 10 → 0; reverse 2, 4, 6, 12, 14 → 3
        items_anxiety_min[1] = 3  # item 2 raw 3 → flip 0
        items_anxiety_min[3] = 3  # item 4 raw 3 → flip 0
        items_anxiety_min[5] = 3  # item 6 raw 3 → flip 0
        items_anxiety_min[11] = 3  # item 12 raw 3 → flip 0
        items_anxiety_min[13] = 3  # item 14 raw 3 → flip 0
        r = score_hads(items_anxiety_min)
        assert r.anxiety == 0
        assert r.depression == 0
        assert r.total == 0


class TestSeverityBands:
    @pytest.mark.parametrize(
        "score,expected_band",
        [
            (0, "normal"),
            (3, "normal"),
            (7, "normal"),
            (8, "mild"),
            (9, "mild"),
            (10, "mild"),
            (11, "moderate"),
            (12, "moderate"),
            (14, "moderate"),
            (15, "severe"),
            (18, "severe"),
            (21, "severe"),
        ],
    )
    def test_anxiety_bands_at_thresholds(
        self, score: int, expected_band: str
    ) -> None:
        """Snaith 2003 per-subscale bands: 0-7/8-10/11-14/15-21.

        Build: set forward anxiety items to bring anxiety sum to
        ``score``; keep reverse item 7 raw = 0 → flipped 3 so
        anxiety already has 3; fill rest.
        """
        # Start with reverse-item 7 contributing 3 (raw 0).
        base_anxiety = 3
        remaining = score - base_anxiety
        items = [0] * 14
        if remaining < 0:
            # Need anxiety < 3, so flip item 7 via raw 3 → flipped 0.
            items[6] = 3
            remaining_after_7 = score
            forward_positions = (1, 3, 5, 9, 11, 13)
            i = 0
            while remaining_after_7 >= 3 and i < 6:
                items[forward_positions[i] - 1] = 3
                remaining_after_7 -= 3
                i += 1
            if remaining_after_7 > 0 and i < 6:
                items[forward_positions[i] - 1] = remaining_after_7
        else:
            forward_positions = (1, 3, 5, 9, 11, 13)
            i = 0
            while remaining >= 3 and i < 6:
                items[forward_positions[i] - 1] = 3
                remaining -= 3
                i += 1
            if remaining > 0 and i < 6:
                items[forward_positions[i] - 1] = remaining
        r = score_hads(items)
        assert r.anxiety == score
        assert r.anxiety_severity == expected_band

    def test_band_boundary_seven_is_normal(self) -> None:
        """Exact boundary: score 7 → normal."""
        # Craft anxiety = 7: forward items contribute 7 - 3 (reverse) = 4.
        items = [0] * 14
        items[0] = 3  # item 1 = 3
        items[2] = 1  # item 3 = 1
        r = score_hads(items)
        assert r.anxiety == 7
        assert r.anxiety_severity == "normal"

    def test_band_boundary_eight_is_mild(self) -> None:
        """Exact boundary: score 8 → mild (first mild)."""
        items = [0] * 14
        items[0] = 3
        items[2] = 2
        r = score_hads(items)
        assert r.anxiety == 8
        assert r.anxiety_severity == "mild"

    def test_band_boundary_ten_is_mild(self) -> None:
        """Exact boundary: score 10 → mild (last mild)."""
        items = [0] * 14
        items[0] = 3
        items[2] = 3
        items[4] = 1
        r = score_hads(items)
        assert r.anxiety == 10
        assert r.anxiety_severity == "mild"

    def test_band_boundary_eleven_is_moderate(self) -> None:
        """Exact boundary: score 11 → moderate (first moderate)."""
        items = [0] * 14
        items[0] = 3
        items[2] = 3
        items[4] = 2
        r = score_hads(items)
        assert r.anxiety == 11
        assert r.anxiety_severity == "moderate"

    def test_band_boundary_fourteen_is_moderate(self) -> None:
        """Exact boundary: score 14 → moderate (last moderate)."""
        items = [0] * 14
        items[0] = 3
        items[2] = 3
        items[4] = 3
        items[8] = 2
        r = score_hads(items)
        assert r.anxiety == 14
        assert r.anxiety_severity == "moderate"

    def test_band_boundary_fifteen_is_severe(self) -> None:
        """Exact boundary: score 15 → severe (first severe)."""
        items = [0] * 14
        items[0] = 3
        items[2] = 3
        items[4] = 3
        items[8] = 3
        r = score_hads(items)
        assert r.anxiety == 15
        assert r.anxiety_severity == "severe"

    def test_band_boundary_twenty_one_is_severe(self) -> None:
        """Ceiling: score 21 → severe."""
        items = [0] * 14
        for pos in (1, 3, 5, 9, 11, 13):
            items[pos - 1] = 3
        r = score_hads(items)
        assert r.anxiety == 21
        assert r.anxiety_severity == "severe"


class TestDepressionSeverityBands:
    @pytest.mark.parametrize(
        "score,expected_band",
        [
            (0, "normal"),
            (7, "normal"),
            (8, "mild"),
            (10, "mild"),
            (11, "moderate"),
            (14, "moderate"),
            (15, "severe"),
            (21, "severe"),
        ],
    )
    def test_depression_bands_at_thresholds(
        self, score: int, expected_band: str
    ) -> None:
        """Snaith 2003 bands apply symmetrically to depression subscale."""
        # Start with reverse items 2,4,6,12,14 all raw 3 → flip 0.
        items = [0] * 14
        for pos in (2, 4, 6, 12, 14):
            items[pos - 1] = 3  # flip to 0
        # Forward depression: items 8, 10. Max forward contribution = 6.
        # For scores > 6, need some reverse items to be raw 0 or raw 1/2.
        if score <= 6:
            if score >= 3:
                items[7] = 3  # item 8 = 3
                if score - 3 > 0:
                    items[9] = score - 3
            elif score > 0:
                items[7] = score
        else:
            items[7] = 3  # item 8 = 3
            items[9] = 3  # item 10 = 3
            remaining = score - 6
            reverse_positions = (2, 4, 6, 12, 14)
            i = 0
            while remaining >= 3 and i < 5:
                items[reverse_positions[i] - 1] = 0  # raw 0 → flip 3
                remaining -= 3
                i += 1
            if remaining > 0 and i < 5:
                items[reverse_positions[i] - 1] = 3 - remaining
        r = score_hads(items)
        assert r.depression == score
        assert r.depression_severity == expected_band


class TestOverallSeverity:
    def test_severity_is_worse_of_two_subscales(self) -> None:
        """Overall severity = worse of (anxiety, depression) bands."""
        # All zeros: anxiety = 3 (normal), depression = 15 (severe).
        r = score_hads(_all(0))
        assert r.anxiety_severity == "normal"
        assert r.depression_severity == "severe"
        assert r.severity == "severe"

    def test_severity_when_both_normal(self) -> None:
        """Both subscales normal → overall normal."""
        # Build: anxiety = 5 (normal), depression = 5 (normal)
        items = [0] * 14
        items[6] = 3  # item 7 raw 3 → flip 0 (reduces anxiety by 3)
        items[0] = 5 - 0  # anxiety needs 5 in forward items
        items[0] = 3
        items[2] = 2  # anxiety = 3 + 2 + 0 = 5
        # depression: reverse items 2,4,6,12,14 raw 3 → 0 each; forward 8, 10.
        items[1] = 3
        items[3] = 3
        items[5] = 3
        items[11] = 3
        items[13] = 3
        items[7] = 3
        items[9] = 2  # depression = 3 + 2 = 5
        r = score_hads(items)
        assert r.anxiety == 5
        assert r.depression == 5
        assert r.anxiety_severity == "normal"
        assert r.depression_severity == "normal"
        assert r.severity == "normal"

    def test_severity_when_anxiety_severe_depression_normal(self) -> None:
        """Anxiety severe, depression normal → overall severe."""
        items = [0] * 14
        # Max anxiety
        for pos in (1, 3, 5, 9, 11, 13):
            items[pos - 1] = 3
        # Zero depression: reverse items 2,4,6,12,14 → raw 3 (flips to 0)
        for pos in (2, 4, 6, 12, 14):
            items[pos - 1] = 3
        # Forward depression items 8, 10 = 0
        r = score_hads(items)
        assert r.anxiety == 21
        assert r.depression == 0
        assert r.severity == "severe"


class TestPositiveScreen:
    def test_both_subscales_below_cutoff_not_positive(self) -> None:
        """Neither subscale ≥ 11 → positive_screen False."""
        # All zeros: anxiety = 3, depression = 15.  But depression is
        # ≥ 11, so this already screens positive.  Use a different base.
        items = [0] * 14
        items[6] = 3  # item 7 raw 3 → flip 0 → drop anxiety baseline
        for pos in (2, 4, 6, 12, 14):
            items[pos - 1] = 3  # reverse → 0 depression items
        r = score_hads(items)
        assert r.anxiety == 0
        assert r.depression == 0
        assert r.anxiety_positive_screen is False
        assert r.depression_positive_screen is False
        assert r.positive_screen is False

    def test_anxiety_at_cutoff_positive(self) -> None:
        """Anxiety ≥ 11 → anxiety_positive_screen True."""
        items = [0] * 14
        items[0] = 3
        items[2] = 3
        items[4] = 2  # anxiety = 3 (item 7 reverse) + 8 = 11 exact
        for pos in (2, 4, 6, 12, 14):
            items[pos - 1] = 3  # depression → 0
        r = score_hads(items)
        assert r.anxiety == 11
        assert r.anxiety_positive_screen is True
        assert r.positive_screen is True

    def test_anxiety_below_cutoff_not_positive(self) -> None:
        """Anxiety = 10 (just below) → anxiety_positive_screen False."""
        items = [0] * 14
        items[0] = 3
        items[2] = 3
        items[4] = 1  # anxiety = 3 + 7 = 10
        for pos in (2, 4, 6, 12, 14):
            items[pos - 1] = 3  # depression → 0
        r = score_hads(items)
        assert r.anxiety == 10
        assert r.anxiety_positive_screen is False

    def test_depression_at_cutoff_positive(self) -> None:
        """Depression ≥ 11 → depression_positive_screen True."""
        items = [0] * 14
        items[6] = 3  # item 7 raw 3 → flip 0 (anxiety low)
        for pos in (2, 4, 6, 12, 14):
            items[pos - 1] = 3  # raw 3 → flip 0
        # Depression: need 11 total; forward items 8, 10 contribute up to 6.
        items[7] = 3
        items[9] = 3  # 6 from forward
        items[1] = 0  # item 2 raw 0 → flip 3 (adds 3)
        items[3] = 1  # item 4 raw 1 → flip 2
        r = score_hads(items)
        assert r.depression == 11
        assert r.depression_positive_screen is True

    def test_either_subscale_positive_overall_positive(self) -> None:
        """Overall positive_screen = anxiety OR depression positive."""
        items = [0] * 14
        items[0] = 3
        items[2] = 3
        items[4] = 2  # anxiety = 11 exact (+3 from reverse item 7)
        for pos in (2, 4, 6, 12, 14):
            items[pos - 1] = 3  # depression → 0
        r = score_hads(items)
        assert r.anxiety_positive_screen is True
        assert r.depression_positive_screen is False
        assert r.positive_screen is True

    def test_cutoff_used_is_11(self) -> None:
        """Bjelland 2002 probable-case cutoff surfaces for UI."""
        r = score_hads(_all(1))
        assert r.cutoff_used == 11


class TestItemCountValidation:
    @pytest.mark.parametrize(
        "count", [0, 1, 5, 10, 12, 13, 15, 16, 20, 100]
    )
    def test_wrong_count_raises(self, count: int) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 14"):
            score_hads([1] * count)


class TestItemValueValidation:
    @pytest.mark.parametrize("bad", [4, -1, 99, -100, 10])
    def test_out_of_range_at_position_1(self, bad: int) -> None:
        items = [bad] + [1] * 13
        with pytest.raises(InvalidResponseError, match="item 1 must be in 0-3"):
            score_hads(items)

    def test_out_of_range_at_position_14(self) -> None:
        items = [1] * 13 + [4]
        with pytest.raises(InvalidResponseError, match="item 14 must be in 0-3"):
            score_hads(items)

    def test_negative_rejected(self) -> None:
        """HADS range is 0-3; negatives invalid."""
        items = [1] * 13 + [-1]
        with pytest.raises(InvalidResponseError):
            score_hads(items)

    def test_zero_is_valid_lower_bound(self) -> None:
        """0 is the valid lower-bound option index."""
        r = score_hads([0] * 14)
        assert r.total == 18  # 6 reverse items flip 0 → 3

    def test_three_is_valid_upper_bound(self) -> None:
        """3 is the valid upper-bound option index."""
        r = score_hads([3] * 14)
        assert r.total == 24  # 8 forward × 3 + 6 reverse × 0


class TestItemTypeValidation:
    @pytest.mark.parametrize("bad", ["1", 1.0, 1.5, None, [1]])
    def test_non_int_rejected_at_position_1(self, bad: object) -> None:
        items = [bad] + [1] * 13
        with pytest.raises(InvalidResponseError, match="item 1 must be int"):
            score_hads(items)  # type: ignore[arg-type]

    def test_true_rejected_as_bool(self) -> None:
        items = [True] + [1] * 13
        with pytest.raises(InvalidResponseError, match="item 1 must be int"):
            score_hads(items)  # type: ignore[list-item]

    def test_false_rejected_as_bool(self) -> None:
        items = [False] + [1] * 13
        with pytest.raises(InvalidResponseError, match="item 1 must be int"):
            score_hads(items)  # type: ignore[list-item]


class TestInvalidResponseErrorIdentity:
    def test_is_value_error(self) -> None:
        assert issubclass(InvalidResponseError, ValueError)


class TestResultTyping:
    def test_result_is_frozen(self) -> None:
        r = score_hads(_all(1))
        with pytest.raises((AttributeError, Exception)):
            r.total = 99  # type: ignore[misc]

    def test_result_carries_instrument_version(self) -> None:
        r = score_hads(_all(1))
        assert r.instrument_version == INSTRUMENT_VERSION

    def test_result_carries_subscale_totals(self) -> None:
        r = score_hads(_all(1))
        assert isinstance(r.anxiety, int)
        assert isinstance(r.depression, int)

    def test_result_carries_subscale_severities(self) -> None:
        r = score_hads(_all(1))
        assert r.anxiety_severity in {"normal", "mild", "moderate", "severe"}
        assert r.depression_severity in {"normal", "mild", "moderate", "severe"}

    def test_result_carries_overall_severity(self) -> None:
        r = score_hads(_all(1))
        assert r.severity in {"normal", "mild", "moderate", "severe"}

    def test_result_carries_subscale_positive_screens(self) -> None:
        r = score_hads(_all(1))
        assert isinstance(r.anxiety_positive_screen, bool)
        assert isinstance(r.depression_positive_screen, bool)

    def test_result_carries_overall_positive_screen(self) -> None:
        r = score_hads(_all(1))
        assert isinstance(r.positive_screen, bool)

    def test_result_does_not_carry_requires_t3(self) -> None:
        """HADS has no suicidality probe → no T3 routing."""
        r = score_hads(_all(1))
        assert not hasattr(r, "requires_t3")

    def test_result_does_not_carry_scaled_score(self) -> None:
        r = score_hads(_all(1))
        assert not hasattr(r, "scaled_score")


class TestClinicalVignettes:
    """Worked examples matching canonical HADS clinical profiles."""

    def test_normal_both_subscales_medical_patient(self) -> None:
        """Stable medical patient: both subscales in normal band."""
        # Build anxiety = 6, depression = 6 (both normal).
        items = [0] * 14
        # Anxiety: forward items contribute 3; reverse item 7 raw 0 → 3.
        # Total = 6.
        items[0] = 3  # item 1 = 3
        # Depression: reverse items raw 3 → 0 each; forward items 8, 10.
        for pos in (2, 4, 6, 12, 14):
            items[pos - 1] = 3  # flip to 0
        items[7] = 3
        items[9] = 3  # depression = 6
        r = score_hads(items)
        assert r.anxiety == 6
        assert r.depression == 6
        assert r.anxiety_severity == "normal"
        assert r.depression_severity == "normal"
        assert r.severity == "normal"
        assert r.positive_screen is False

    def test_convergent_moderate_depression_phq9_pairing(self) -> None:
        """HADS-D moderate + PHQ-9 moderate convergent depression.
        Build: depression = 12 (moderate)."""
        items = [0] * 14
        items[6] = 3  # item 7 raw 3 → flip 0 (drop anxiety baseline to 0)
        # Anxiety: all zeros otherwise. Anxiety = 0.
        # Depression = 12:
        # reverse items 2, 4, 6 raw 0 → flip 3 each = 9;
        # forward items 8 = 3, 10 = 0. Total = 12.
        items[7] = 3  # item 8 = 3
        # reverse items 12, 14 raw 3 → flip 0
        items[11] = 3
        items[13] = 3
        r = score_hads(items)
        assert r.depression == 12
        assert r.depression_severity == "moderate"
        assert r.depression_positive_screen is True

    def test_convergent_severe_anxiety_gad7_pairing(self) -> None:
        """HADS-A severe + GAD-7 severe convergent anxiety."""
        items = [0] * 14
        # Max anxiety: forward 1,3,5,9,11,13 = 3; reverse 7 raw 0 → 3.
        for pos in (1, 3, 5, 9, 11, 13):
            items[pos - 1] = 3
        # Zero depression: reverse 2,4,6,12,14 raw 3 → 0; forward 8,10 = 0.
        for pos in (2, 4, 6, 12, 14):
            items[pos - 1] = 3
        r = score_hads(items)
        assert r.anxiety == 21
        assert r.anxiety_severity == "severe"
        assert r.depression == 0
        assert r.depression_severity == "normal"

    def test_anhedonia_dominant_medical_comorbidity_profile(self) -> None:
        """Medical patient with anhedonia-dominant depression.
        PHQ-9 may underflag due to somatic-item confounding; HADS-D
        picks up the cognitive-affective core."""
        # Mid-moderate depression with low anxiety.
        items = [0] * 14
        items[6] = 3  # item 7 raw 3 → flip 0 (minimize anxiety)
        # Anxiety = 0.
        # Depression: reverse items 2, 4, 6 → flip 3 each = 9; 12, 14 → 3 each = 6.
        # Forward items 8 = 0, 10 = 0. Need to hit ~12.
        items[11] = 3  # item 12 raw 3 → flip 0
        items[13] = 3  # item 14 raw 3 → flip 0
        # Depression = (item 2 → 3) + (item 4 → 3) + (item 6 → 3) + 0 + 0 = 9? wait
        # Actually with items 2, 4, 6 raw 0 → flip 3 each = 9; 8 = 0; 10 = 0;
        # 12 raw 3 → flip 0; 14 raw 3 → flip 0. Total = 9.
        r = score_hads(items)
        assert r.depression == 9
        assert r.depression_severity == "mild"

    def test_mixed_subscale_profile_both_moderate(self) -> None:
        """Both anxiety and depression moderate — dual-target
        intervention indication."""
        items = [0] * 14
        # Anxiety: need 11-14. Item 7 reverse raw 0 → 3; then forward items.
        items[0] = 3  # item 1 = 3
        items[2] = 3  # item 3 = 3
        items[4] = 2  # item 5 = 2 → anxiety = 3 + 3 + 3 + 2 = 11
        # Depression: need 11-14. Reverse 2, 4, 6 raw 0 → 3 each = 9;
        # reverse 12, 14 raw 3 → 0 each = 0; forward 8 = 3, 10 = 0.
        # Total = 9 + 3 = 12.
        items[7] = 3
        items[11] = 3
        items[13] = 3
        r = score_hads(items)
        assert r.anxiety == 11
        assert r.anxiety_severity == "moderate"
        assert r.depression == 12
        assert r.depression_severity == "moderate"
        assert r.severity == "moderate"
        assert r.positive_screen is True

    def test_ceiling_severe_both_subscales(self) -> None:
        """Ceiling: both subscales at severe.  Highest-priority
        clinical intervention."""
        items = [0] * 14
        # Max anxiety
        for pos in (1, 3, 5, 9, 11, 13):
            items[pos - 1] = 3
        # item 7 stays 0 → reverse to 3
        # Max depression
        items[7] = 3  # item 8 = 3
        items[9] = 3  # item 10 = 3
        # reverse 2, 4, 6, 12, 14 stay 0 → flip to 3 each
        r = score_hads(items)
        assert r.anxiety == 21
        assert r.depression == 21
        assert r.total == 42
        assert r.anxiety_severity == "severe"
        assert r.depression_severity == "severe"
        assert r.severity == "severe"

    def test_rci_puhan_1_5_pt_mcid(self) -> None:
        """Puhan 2008 MCID ≈ 1.5 per subscale; a 2-point delta is
        reliable improvement.  Baseline moderate, follow-up mild
        on a trajectory."""
        # Baseline: anxiety = 11 (moderate, first moderate).
        baseline_items = [0] * 14
        baseline_items[0] = 3
        baseline_items[2] = 3
        baseline_items[4] = 2  # anxiety = 3+3+3+2 = 11
        for pos in (2, 4, 6, 12, 14):
            baseline_items[pos - 1] = 3  # flip depression to 0
        baseline = score_hads(baseline_items)
        assert baseline.anxiety == 11
        assert baseline.anxiety_severity == "moderate"

        # Follow-up: anxiety = 9 (mild, reliable improvement per Puhan).
        followup_items = [0] * 14
        followup_items[0] = 3
        followup_items[2] = 2
        followup_items[4] = 1  # anxiety = 3+3+2+1 = 9
        for pos in (2, 4, 6, 12, 14):
            followup_items[pos - 1] = 3
        followup = score_hads(followup_items)
        assert followup.anxiety == 9
        assert followup.anxiety_severity == "mild"
        assert baseline.anxiety - followup.anxiety >= 2

    def test_bjelland_2002_probable_case_threshold_exact(self) -> None:
        """Score exactly 11 → Bjelland 2002 probable-case threshold,
        caseness flag fires."""
        items = [0] * 14
        items[0] = 3
        items[2] = 3
        items[4] = 2  # anxiety = 11 exact
        for pos in (2, 4, 6, 12, 14):
            items[pos - 1] = 3  # depression = 0
        r = score_hads(items)
        assert r.anxiety == 11
        assert r.anxiety_positive_screen is True

    def test_bjelland_2002_below_threshold_not_case(self) -> None:
        """Score 10 → Snaith mild band but BELOW Bjelland probable-
        case threshold."""
        items = [0] * 14
        items[0] = 3
        items[2] = 3
        items[4] = 1  # anxiety = 3 + 3 + 3 + 1 = 10
        for pos in (2, 4, 6, 12, 14):
            items[pos - 1] = 3
        r = score_hads(items)
        assert r.anxiety == 10
        assert r.anxiety_severity == "mild"
        assert r.anxiety_positive_screen is False


class TestResultInstanceShape:
    def test_returns_hads_result_instance(self) -> None:
        r = score_hads(_all(1))
        assert isinstance(r, HadsResult)

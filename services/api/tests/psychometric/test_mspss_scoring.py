"""Tests for MSPSS scoring — Zimet, Dahlem, Zimet & Farley 1988."""

from __future__ import annotations

import pytest

from discipline.psychometric.scoring.mspss import (
    INSTRUMENT_VERSION,
    ITEM_COUNT,
    ITEM_MAX,
    ITEM_MIN,
    InvalidResponseError,
    MSPSS_FAMILY_POSITIONS,
    MSPSS_FRIENDS_POSITIONS,
    MSPSS_REVERSE_ITEMS,
    MSPSS_SIGNIFICANT_OTHER_POSITIONS,
    MSPSS_SUBSCALES,
    MspssResult,
    score_mspss,
)


VALID_MID = 4  # Neutral midpoint of 1-7 Likert


def _all(v: int) -> list[int]:
    """Return a 12-item list with every item set to ``v``."""
    return [v] * ITEM_COUNT


class TestConstants:
    def test_instrument_version_format(self) -> None:
        assert INSTRUMENT_VERSION == "mspss-1.0.0"

    def test_item_count_is_12(self) -> None:
        assert ITEM_COUNT == 12

    def test_item_range_is_1_to_7(self) -> None:
        assert (ITEM_MIN, ITEM_MAX) == (1, 7)

    def test_reverse_items_is_empty(self) -> None:
        """Zimet 1988: all 12 items positively worded."""
        assert MSPSS_REVERSE_ITEMS == ()

    def test_subscale_names_in_zimet_order(self) -> None:
        """Zimet 1988 §Method factor-table order: SO, Family, Friends."""
        assert MSPSS_SUBSCALES == ("significant_other", "family", "friends")

    def test_significant_other_positions(self) -> None:
        """Zimet 1988 Table 1: items 1, 2, 5, 10."""
        assert MSPSS_SIGNIFICANT_OTHER_POSITIONS == (1, 2, 5, 10)

    def test_family_positions(self) -> None:
        """Zimet 1988 Table 1: items 3, 4, 8, 11."""
        assert MSPSS_FAMILY_POSITIONS == (3, 4, 8, 11)

    def test_friends_positions(self) -> None:
        """Zimet 1988 Table 1: items 6, 7, 9, 12."""
        assert MSPSS_FRIENDS_POSITIONS == (6, 7, 9, 12)

    def test_subscale_positions_partition_12(self) -> None:
        """Every item 1-12 appears in exactly one subscale."""
        all_positions = (
            MSPSS_SIGNIFICANT_OTHER_POSITIONS
            + MSPSS_FAMILY_POSITIONS
            + MSPSS_FRIENDS_POSITIONS
        )
        assert sorted(all_positions) == list(range(1, 13))

    def test_each_subscale_is_4_items(self) -> None:
        """Zimet 1988: 4 items per subscale × 3 subscales = 12."""
        assert len(MSPSS_SIGNIFICANT_OTHER_POSITIONS) == 4
        assert len(MSPSS_FAMILY_POSITIONS) == 4
        assert len(MSPSS_FRIENDS_POSITIONS) == 4


class TestTotalCorrectness:
    def test_all_ones_gives_minimum_12(self) -> None:
        result = score_mspss(_all(1))
        assert result.total == 12

    def test_all_sevens_gives_maximum_84(self) -> None:
        result = score_mspss(_all(7))
        assert result.total == 84

    def test_all_fours_gives_midpoint_48(self) -> None:
        result = score_mspss(_all(4))
        assert result.total == 48

    def test_total_equals_sum_of_subscales(self) -> None:
        """total == significant_other + family + friends always."""
        items = [1, 7, 1, 7, 1, 7, 1, 7, 1, 7, 1, 7]
        r = score_mspss(items)
        assert r.total == r.significant_other + r.family + r.friends


class TestSubscalePartitioning:
    def test_significant_other_isolation(self) -> None:
        """Set SO items (1,2,5,10) to 7, others to 1."""
        items = [1] * 12
        for pos in MSPSS_SIGNIFICANT_OTHER_POSITIONS:
            items[pos - 1] = 7
        r = score_mspss(items)
        assert r.significant_other == 4 * 7  # 28
        assert r.family == 4 * 1  # 4
        assert r.friends == 4 * 1  # 4
        assert r.total == 28 + 4 + 4  # 36

    def test_family_isolation(self) -> None:
        """Set Family items (3,4,8,11) to 7, others to 1."""
        items = [1] * 12
        for pos in MSPSS_FAMILY_POSITIONS:
            items[pos - 1] = 7
        r = score_mspss(items)
        assert r.significant_other == 4
        assert r.family == 28
        assert r.friends == 4
        assert r.total == 36

    def test_friends_isolation(self) -> None:
        """Set Friends items (6,7,9,12) to 7, others to 1."""
        items = [1] * 12
        for pos in MSPSS_FRIENDS_POSITIONS:
            items[pos - 1] = 7
        r = score_mspss(items)
        assert r.significant_other == 4
        assert r.family == 4
        assert r.friends == 28
        assert r.total == 36

    def test_subscale_position_order_matters(self) -> None:
        """Shuffling items changes subscale sums even if total unchanged."""
        aligned = [1, 1, 7, 7, 1, 7, 7, 7, 7, 1, 7, 7]
        rev = list(reversed(aligned))
        r_aligned = score_mspss(aligned)
        r_rev = score_mspss(rev)
        assert r_aligned.total == r_rev.total
        assert (r_aligned.significant_other, r_aligned.family, r_aligned.friends) != (
            r_rev.significant_other,
            r_rev.family,
            r_rev.friends,
        )


class TestSubscaleRanges:
    @pytest.mark.parametrize(
        "v,expected_sub",
        [(1, 4), (2, 8), (3, 12), (4, 16), (5, 20), (6, 24), (7, 28)],
    )
    def test_all_constant_gives_linear_subscale_sum(
        self, v: int, expected_sub: int
    ) -> None:
        r = score_mspss(_all(v))
        assert r.significant_other == expected_sub
        assert r.family == expected_sub
        assert r.friends == expected_sub


class TestSeverityAlwaysContinuous:
    @pytest.mark.parametrize("v", [1, 2, 3, 4, 5, 6, 7])
    def test_all_constant_returns_continuous(self, v: int) -> None:
        assert score_mspss(_all(v)).severity == "continuous"

    def test_mixed_returns_continuous(self) -> None:
        assert score_mspss([1, 2, 3, 4, 5, 6, 7, 1, 2, 3, 4, 5]).severity == "continuous"

    def test_canty_mitchell_low_band_range_returns_continuous(self) -> None:
        """Mean 1-2.9 → sum 12-34.8.  Envelope stays continuous."""
        assert score_mspss(_all(2)).severity == "continuous"  # total=24

    def test_canty_mitchell_moderate_band_range_returns_continuous(self) -> None:
        """Mean 3-5 → sum 36-60.  Envelope stays continuous."""
        assert score_mspss(_all(4)).severity == "continuous"  # total=48

    def test_canty_mitchell_high_band_range_returns_continuous(self) -> None:
        """Mean 5.1-7 → sum 61.2-84.  Envelope stays continuous."""
        assert score_mspss(_all(6)).severity == "continuous"  # total=72


class TestNoReverseKeying:
    @pytest.mark.parametrize("pos", [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12])
    def test_raising_item_raises_total(self, pos: int) -> None:
        """No reverse-keying: every item's raw value adds directly."""
        base = _all(1)
        r_base = score_mspss(base)
        bumped = list(base)
        bumped[pos - 1] = 7
        r_bumped = score_mspss(bumped)
        assert r_bumped.total == r_base.total + 6

    @pytest.mark.parametrize("pos", [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12])
    def test_items_preserve_raw_unchanged(self, pos: int) -> None:
        """``items`` tuple is the verbatim input (no reverse flip)."""
        base = _all(4)
        bumped = list(base)
        bumped[pos - 1] = 7
        r = score_mspss(bumped)
        assert r.items[pos - 1] == 7
        assert list(r.items) == bumped


class TestAcquiescenceSignature:
    @pytest.mark.parametrize(
        "v,expected_total",
        [(1, 12), (2, 24), (3, 36), (4, 48), (5, 60), (6, 72), (7, 84)],
    )
    def test_all_constant_is_linear_12v(self, v: int, expected_total: int) -> None:
        """No reverse-keying: all-``v`` total = 12v across the full range."""
        assert score_mspss(_all(v)).total == expected_total

    def test_endpoint_gap_is_72(self) -> None:
        """84 (all 7) − 12 (all 1) = 72, 100% of 12-84 range."""
        assert score_mspss(_all(7)).total - score_mspss(_all(1)).total == 72


class TestItemsPreserveRaw:
    def test_items_field_is_tuple(self) -> None:
        r = score_mspss(_all(4))
        assert isinstance(r.items, tuple)

    def test_items_field_length(self) -> None:
        r = score_mspss(_all(4))
        assert len(r.items) == ITEM_COUNT

    def test_items_preserve_order(self) -> None:
        payload = [1, 2, 3, 4, 5, 6, 7, 1, 2, 3, 4, 5]
        r = score_mspss(payload)
        assert r.items == tuple(payload)


class TestItemCountValidation:
    @pytest.mark.parametrize("count", [0, 1, 5, 10, 11, 13, 14, 20, 100])
    def test_wrong_count_raises(self, count: int) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 12"):
            score_mspss([4] * count)


class TestItemValueValidation:
    @pytest.mark.parametrize("bad", [0, 8, -1, 99, -100])
    def test_out_of_range_at_position_1(self, bad: int) -> None:
        items = [bad, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4]
        with pytest.raises(InvalidResponseError, match="item 1 must be in 1-7"):
            score_mspss(items)

    def test_out_of_range_at_position_12(self) -> None:
        items = [4] * 11 + [8]
        with pytest.raises(InvalidResponseError, match="item 12 must be in 1-7"):
            score_mspss(items)

    def test_zero_is_rejected(self) -> None:
        """MSPSS range is 1-7; 0 is invalid (unlike CIUS range 0-4)."""
        items = [4] * 11 + [0]
        with pytest.raises(InvalidResponseError):
            score_mspss(items)


class TestItemTypeValidation:
    @pytest.mark.parametrize("bad", ["4", 4.0, 4.5, None, [4]])
    def test_non_int_rejected_at_position_1(self, bad: object) -> None:
        items = [bad] + [4] * 11
        with pytest.raises(InvalidResponseError, match="item 1 must be int"):
            score_mspss(items)  # type: ignore[arg-type]

    def test_true_rejected_as_bool(self) -> None:
        """Bool precedes int check — True (→1 in int) still rejected."""
        items = [True] + [4] * 11
        with pytest.raises(InvalidResponseError, match="item 1 must be int"):
            score_mspss(items)  # type: ignore[list-item]

    def test_false_rejected_as_bool(self) -> None:
        """Bool precedes int check — False (→0, out of range) rejected as bool."""
        items = [False] + [4] * 11
        with pytest.raises(InvalidResponseError, match="item 1 must be int"):
            score_mspss(items)  # type: ignore[list-item]


class TestInvalidResponseErrorIdentity:
    def test_is_value_error(self) -> None:
        assert issubclass(InvalidResponseError, ValueError)


class TestResultTyping:
    def test_result_is_frozen(self) -> None:
        r = score_mspss(_all(4))
        with pytest.raises((AttributeError, Exception)):
            r.total = 99  # type: ignore[misc]

    def test_result_carries_instrument_version(self) -> None:
        r = score_mspss(_all(4))
        assert r.instrument_version == INSTRUMENT_VERSION

    def test_result_has_four_scalar_totals(self) -> None:
        r = score_mspss(_all(4))
        assert isinstance(r.total, int)
        assert isinstance(r.significant_other, int)
        assert isinstance(r.family, int)
        assert isinstance(r.friends, int)

    def test_result_does_not_carry_positive_screen_field(self) -> None:
        r = score_mspss(_all(4))
        assert not hasattr(r, "positive_screen")

    def test_result_does_not_carry_requires_t3_field(self) -> None:
        r = score_mspss(_all(4))
        assert not hasattr(r, "requires_t3")

    def test_result_does_not_carry_scaled_score_field(self) -> None:
        r = score_mspss(_all(4))
        assert not hasattr(r, "scaled_score")


class TestClinicalVignettes:
    """Worked examples matching Zimet 1988 / Canty-Mitchell 2000 profiles."""

    def test_diffuse_deficit_profile(self) -> None:
        """All three subscales low — Holt-Lunstad 2010 isolation-risk profile."""
        items = [1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2]
        r = score_mspss(items)
        assert r.total == 18
        assert r.significant_other <= 8
        assert r.family <= 8
        assert r.friends <= 8

    def test_partner_dependent_profile(self) -> None:
        """SO high, Family and Friends low — partner-dependent support."""
        items = [7, 7, 2, 2, 7, 2, 2, 2, 2, 7, 2, 2]
        r = score_mspss(items)
        assert r.significant_other == 28
        assert r.family == 8
        assert r.friends == 8

    def test_family_only_support_profile(self) -> None:
        """Family high, SO and Friends low — early-recovery withdrawal pattern."""
        items = [2, 2, 7, 7, 2, 2, 2, 7, 2, 2, 7, 2]
        r = score_mspss(items)
        assert r.significant_other == 8
        assert r.family == 28
        assert r.friends == 8

    def test_peer_only_support_profile(self) -> None:
        """Friends high, SO and Family low — estranged-young-adult pattern."""
        items = [2, 2, 2, 2, 2, 7, 7, 2, 7, 2, 2, 7]
        r = score_mspss(items)
        assert r.significant_other == 8
        assert r.family == 8
        assert r.friends == 28

    def test_distributed_support_profile(self) -> None:
        """All three high — protective profile across sources."""
        items = _all(6)
        r = score_mspss(items)
        assert r.significant_other == 24
        assert r.family == 24
        assert r.friends == 24
        assert r.total == 72

    def test_mspss_low_pss10_high_pairing_mspss_side(self) -> None:
        """Cohen-Wills stress-buffering profile: MSPSS side of the pairing."""
        items = _all(2)
        r = score_mspss(items)
        assert r.total == 24  # mean 2.0 — Canty-Mitchell "low" band (UI layer)

    def test_mspss_low_swls_low_pairing_mspss_side(self) -> None:
        """Moos 2005 delayed-relapse + network-vulnerability: MSPSS side."""
        items = [2] * 12
        r = score_mspss(items)
        assert r.severity == "continuous"
        assert r.total < 36  # Below Canty-Mitchell moderate (renderer layer)

    def test_improving_trajectory_sample_baseline(self) -> None:
        """Baseline timepoint: moderate perceived support."""
        items = _all(4)
        r = score_mspss(items)
        assert r.total == 48

    def test_improving_trajectory_sample_followup(self) -> None:
        """Follow-up timepoint: improved perceived support (all subscales up)."""
        items = _all(5)
        r = score_mspss(items)
        assert r.total == 60
        assert r.significant_other == 20
        assert r.family == 20
        assert r.friends == 20


class TestResultInstanceShape:
    def test_returns_mspss_result_instance(self) -> None:
        r = score_mspss(_all(4))
        assert isinstance(r, MspssResult)

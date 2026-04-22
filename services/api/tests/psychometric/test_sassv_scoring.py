"""Tests for the SAS-SV (Smartphone Addiction Scale - Short Version) scorer.

Kwon M et al. 2013 PLoS ONE 8(12):e83558.
10 items, 1-6 Likert, total 10-60, HIGHER = MORE smartphone addiction.
Sex-stratified cutoffs: male >= 31, female >= 33.
No severity bands. No subscales.
"""

from __future__ import annotations

import pytest

from discipline.psychometric.scoring.sassv import (
    INSTRUMENT_VERSION,
    ITEM_COUNT,
    ITEM_MAX,
    ITEM_MIN,
    SAS_SV_CUTOFF_FEMALE,
    SAS_SV_CUTOFF_MALE,
    SAS_SV_CUTOFF_UNSPECIFIED,
    TOTAL_MAX,
    TOTAL_MIN,
    InvalidResponseError,
    SasSvResult,
    score_sas_sv,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _items(total: int) -> list[int]:
    """Construct a valid 10-item list (1-6) with the given total.

    Starts from ITEM_MIN (1) and fills up to ITEM_MAX (6).
    """
    if total < TOTAL_MIN or total > TOTAL_MAX:
        raise ValueError(f"Cannot construct SAS-SV items for total={total}")
    items: list[int] = [ITEM_MIN] * ITEM_COUNT  # baseline = 10
    remaining = total - TOTAL_MIN
    for i in range(ITEM_COUNT):
        add = min(ITEM_MAX - ITEM_MIN, remaining)
        items[i] += add
        remaining -= add
        if remaining == 0:
            break
    return items


def _floor_items() -> list[int]:
    return [1] * ITEM_COUNT


def _ceil_items() -> list[int]:
    return [6] * ITEM_COUNT


# ---------------------------------------------------------------------------
# TestConstants
# ---------------------------------------------------------------------------

class TestConstants:
    def test_instrument_version(self) -> None:
        assert INSTRUMENT_VERSION == "sas-sv-1.0.0"

    def test_item_count(self) -> None:
        assert ITEM_COUNT == 10

    def test_item_min(self) -> None:
        # SAS-SV uses 1-6 scale — NOT zero-indexed.
        assert ITEM_MIN == 1

    def test_item_max(self) -> None:
        assert ITEM_MAX == 6

    def test_cutoff_male(self) -> None:
        # Kwon 2013 Table 5.
        assert SAS_SV_CUTOFF_MALE == 31

    def test_cutoff_female(self) -> None:
        assert SAS_SV_CUTOFF_FEMALE == 33

    def test_cutoff_unspecified_equals_male(self) -> None:
        # Conservative default: lower cutoff = more sensitive.
        assert SAS_SV_CUTOFF_UNSPECIFIED == SAS_SV_CUTOFF_MALE

    def test_total_min(self) -> None:
        assert TOTAL_MIN == 10

    def test_total_max(self) -> None:
        assert TOTAL_MAX == 60

    def test_total_min_matches_floor(self) -> None:
        r = score_sas_sv(_floor_items())
        assert r.total == TOTAL_MIN

    def test_total_max_matches_ceil(self) -> None:
        r = score_sas_sv(_ceil_items())
        assert r.total == TOTAL_MAX


# ---------------------------------------------------------------------------
# TestTotalCorrectness
# ---------------------------------------------------------------------------

class TestTotalCorrectness:
    def test_floor_total_is_10(self) -> None:
        r = score_sas_sv(_floor_items())
        assert r.total == 10

    def test_ceiling_total_is_60(self) -> None:
        r = score_sas_sv(_ceil_items())
        assert r.total == 60

    def test_all_threes_total(self) -> None:
        r = score_sas_sv([3] * ITEM_COUNT)
        assert r.total == 30

    def test_all_fours_total(self) -> None:
        r = score_sas_sv([4] * ITEM_COUNT)
        assert r.total == 40

    def test_explicit_mixed(self) -> None:
        items = [1, 2, 3, 4, 5, 6, 5, 4, 3, 2]
        assert len(items) == 10
        r = score_sas_sv(items)
        assert r.total == sum(items)

    def test_total_matches_sum(self) -> None:
        items = [2, 3, 4, 5, 6, 1, 2, 3, 4, 5]
        r = score_sas_sv(items)
        assert r.total == sum(items)

    def test_no_reverse_keying(self) -> None:
        r1 = score_sas_sv([1] * ITEM_COUNT)
        r2 = score_sas_sv([2] * ITEM_COUNT)
        assert r2.total == r1.total + ITEM_COUNT


# ---------------------------------------------------------------------------
# TestSexStratifiedCutoffs
# ---------------------------------------------------------------------------

class TestSexStratifiedCutoffs:
    def test_male_cutoff_31(self) -> None:
        r = score_sas_sv(_items(31), sex="male")
        assert r.cutoff_used == 31
        assert r.positive_screen is True

    def test_male_below_cutoff(self) -> None:
        r = score_sas_sv(_items(30), sex="male")
        assert r.cutoff_used == 31
        assert r.positive_screen is False

    def test_female_cutoff_33(self) -> None:
        r = score_sas_sv(_items(33), sex="female")
        assert r.cutoff_used == 33
        assert r.positive_screen is True

    def test_female_at_male_cutoff_negative(self) -> None:
        # total=31 is positive for male but negative for female
        r = score_sas_sv(_items(31), sex="female")
        assert r.positive_screen is False

    def test_female_at_32_still_negative(self) -> None:
        r = score_sas_sv(_items(32), sex="female")
        assert r.positive_screen is False

    def test_female_at_33_positive(self) -> None:
        r = score_sas_sv(_items(33), sex="female")
        assert r.positive_screen is True

    def test_unspecified_uses_male_cutoff_31(self) -> None:
        r = score_sas_sv(_items(31), sex="unspecified")
        assert r.cutoff_used == 31
        assert r.positive_screen is True

    def test_unspecified_at_30_negative(self) -> None:
        r = score_sas_sv(_items(30), sex="unspecified")
        assert r.positive_screen is False

    def test_default_sex_is_unspecified(self) -> None:
        # No sex argument → defaults to unspecified → cutoff = 31
        r = score_sas_sv(_items(31))
        assert r.sex == "unspecified"
        assert r.cutoff_used == 31
        assert r.positive_screen is True

    def test_sex_echoed_on_result(self) -> None:
        for sex in ("male", "female", "unspecified"):
            r = score_sas_sv(_floor_items(), sex=sex)  # type: ignore[arg-type]
            assert r.sex == sex

    def test_cutoff_used_echoes_integer(self) -> None:
        rm = score_sas_sv(_floor_items(), sex="male")
        rf = score_sas_sv(_floor_items(), sex="female")
        assert rm.cutoff_used == 31
        assert rf.cutoff_used == 33

    def test_floor_negative_all_sexes(self) -> None:
        for sex in ("male", "female", "unspecified"):
            r = score_sas_sv(_floor_items(), sex=sex)  # type: ignore[arg-type]
            assert r.positive_screen is False

    def test_ceil_positive_all_sexes(self) -> None:
        for sex in ("male", "female", "unspecified"):
            r = score_sas_sv(_ceil_items(), sex=sex)  # type: ignore[arg-type]
            assert r.positive_screen is True


# ---------------------------------------------------------------------------
# TestItemCountValidation
# ---------------------------------------------------------------------------

class TestItemCountValidation:
    def test_too_few_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            score_sas_sv([1] * 9)

    def test_too_many_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            score_sas_sv([1] * 11)

    def test_empty_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            score_sas_sv([])

    def test_error_mentions_10(self) -> None:
        with pytest.raises(InvalidResponseError, match="10"):
            score_sas_sv([1] * 5)


# ---------------------------------------------------------------------------
# TestItemRangeValidation
# ---------------------------------------------------------------------------

class TestItemRangeValidation:
    def test_zero_raises(self) -> None:
        # ITEM_MIN = 1; 0 is out of range.
        items = [1] * ITEM_COUNT
        items[0] = 0
        with pytest.raises(InvalidResponseError):
            score_sas_sv(items)

    def test_negative_raises(self) -> None:
        items = [1] * ITEM_COUNT
        items[3] = -1
        with pytest.raises(InvalidResponseError):
            score_sas_sv(items)

    def test_above_6_raises(self) -> None:
        items = [1] * ITEM_COUNT
        items[5] = 7
        with pytest.raises(InvalidResponseError):
            score_sas_sv(items)

    def test_item_6_valid(self) -> None:
        items = [6] * ITEM_COUNT
        r = score_sas_sv(items)
        assert r.total == 60

    def test_item_1_valid(self) -> None:
        items = [1] * ITEM_COUNT
        r = score_sas_sv(items)
        assert r.total == 10

    def test_error_cites_range(self) -> None:
        items = [1] * ITEM_COUNT
        items[2] = 8
        with pytest.raises(InvalidResponseError, match="1-6"):
            score_sas_sv(items)

    def test_error_mentions_position(self) -> None:
        items = [1] * ITEM_COUNT
        items[7] = 0
        with pytest.raises(InvalidResponseError, match="8"):  # 1-indexed
            score_sas_sv(items)


# ---------------------------------------------------------------------------
# TestItemTypeValidation
# ---------------------------------------------------------------------------

class TestItemTypeValidation:
    def test_true_raises(self) -> None:
        items: list = [1] * ITEM_COUNT
        items[0] = True
        with pytest.raises(InvalidResponseError):
            score_sas_sv(items)

    def test_false_raises(self) -> None:
        items: list = [3] * ITEM_COUNT
        items[4] = False
        with pytest.raises(InvalidResponseError):
            score_sas_sv(items)

    def test_float_raises(self) -> None:
        items: list = [2] * ITEM_COUNT
        items[6] = 3.0
        with pytest.raises(InvalidResponseError):
            score_sas_sv(items)

    def test_string_raises(self) -> None:
        items: list = [2] * ITEM_COUNT
        items[9] = "4"
        with pytest.raises(InvalidResponseError):
            score_sas_sv(items)

    def test_none_raises(self) -> None:
        items: list = [2] * ITEM_COUNT
        items[2] = None
        with pytest.raises(InvalidResponseError):
            score_sas_sv(items)


# ---------------------------------------------------------------------------
# TestResultTyping
# ---------------------------------------------------------------------------

class TestResultTyping:
    def test_result_is_sas_sv_result(self) -> None:
        r = score_sas_sv(_floor_items())
        assert isinstance(r, SasSvResult)

    def test_result_is_frozen(self) -> None:
        r = score_sas_sv(_floor_items())
        with pytest.raises((AttributeError, TypeError)):
            r.total = 99  # type: ignore[misc]

    def test_instrument_version_pinned(self) -> None:
        r = score_sas_sv(_floor_items())
        assert r.instrument_version == INSTRUMENT_VERSION

    def test_items_is_tuple(self) -> None:
        r = score_sas_sv(_floor_items())
        assert isinstance(r.items, tuple)

    def test_items_length_10(self) -> None:
        r = score_sas_sv(_floor_items())
        assert len(r.items) == ITEM_COUNT

    def test_total_is_int(self) -> None:
        r = score_sas_sv(_floor_items())
        assert isinstance(r.total, int)

    def test_positive_screen_is_bool(self) -> None:
        r = score_sas_sv(_floor_items())
        assert isinstance(r.positive_screen, bool)

    def test_cutoff_used_is_int(self) -> None:
        r = score_sas_sv(_floor_items())
        assert isinstance(r.cutoff_used, int)

    def test_no_subscales_attribute(self) -> None:
        r = score_sas_sv(_floor_items())
        assert not hasattr(r, "subscales")


# ---------------------------------------------------------------------------
# TestClinicalVignettes
# ---------------------------------------------------------------------------

class TestClinicalVignettes:
    def test_low_user_negative(self) -> None:
        # Minimal usage — all items at minimum.
        r = score_sas_sv(_floor_items(), sex="male")
        assert r.positive_screen is False

    def test_compulsive_male_positive(self) -> None:
        # Compulsive male user above cutoff.
        r = score_sas_sv(_items(35), sex="male")
        assert r.positive_screen is True

    def test_compulsive_female_positive(self) -> None:
        # Compulsive female user above female cutoff.
        r = score_sas_sv(_items(35), sex="female")
        assert r.positive_screen is True

    def test_borderline_male_at_boundary(self) -> None:
        # Exactly at male cutoff.
        r = score_sas_sv(_items(31), sex="male")
        assert r.positive_screen is True

    def test_social_anxiety_nomophobia_very_high(self) -> None:
        # King 2010: nomophobia + social anxiety → ceiling pattern.
        r = score_sas_sv(_ceil_items(), sex="female")
        assert r.total == 60
        assert r.positive_screen is True

    def test_emotion_regulation_substitute_positive(self) -> None:
        # Elhai 2017: negative affect regulation → high SAS-SV.
        r = score_sas_sv(_items(42), sex="unspecified")
        assert r.positive_screen is True

    def test_direction_higher_is_more_compulsive(self) -> None:
        r_low = score_sas_sv(_floor_items())
        r_high = score_sas_sv(_ceil_items())
        assert r_high.total > r_low.total

    def test_rci_determinism(self) -> None:
        items = [1, 2, 3, 4, 5, 6, 5, 4, 3, 2]
        r1 = score_sas_sv(items, sex="male")
        r2 = score_sas_sv(items, sex="male")
        assert r1.total == r2.total
        assert r1.positive_screen == r2.positive_screen


# ---------------------------------------------------------------------------
# TestInvariants
# ---------------------------------------------------------------------------

class TestInvariants:
    def test_items_preserved_verbatim(self) -> None:
        raw = [1, 2, 3, 4, 5, 6, 5, 4, 3, 2]
        r = score_sas_sv(raw)
        assert r.items == tuple(raw)

    def test_total_equals_sum_of_items(self) -> None:
        raw = [3, 4, 2, 5, 1, 6, 3, 4, 2, 5]
        r = score_sas_sv(raw)
        assert r.total == sum(raw)

    def test_lower_bound(self) -> None:
        r = score_sas_sv(_floor_items())
        assert r.total == TOTAL_MIN

    def test_upper_bound(self) -> None:
        r = score_sas_sv(_ceil_items())
        assert r.total == TOTAL_MAX

    def test_severity_consistent_with_positive_screen(self) -> None:
        for sex in ("male", "female", "unspecified"):
            for items in (_floor_items(), _items(31), _ceil_items()):
                r = score_sas_sv(items, sex=sex)  # type: ignore[arg-type]
                if r.positive_screen:
                    assert r.severity == "positive_screen"
                else:
                    assert r.severity == "negative_screen"


# ---------------------------------------------------------------------------
# TestEdgeCases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_tuple_input_accepted(self) -> None:
        r = score_sas_sv(tuple([1] * ITEM_COUNT))
        assert r.total == 10

    def test_generator_input_accepted(self) -> None:
        r = score_sas_sv(x for x in ([1] * ITEM_COUNT))
        assert r.total == 10

    def test_does_not_mutate_input(self) -> None:
        raw = [1, 2, 3, 4, 5, 6, 1, 2, 3, 4]
        snapshot = raw[:]
        score_sas_sv(raw)
        assert raw == snapshot

    def test_complex_object_raises(self) -> None:
        items: list = [3] * ITEM_COUNT
        items[1] = complex(3, 0)
        with pytest.raises(InvalidResponseError):
            score_sas_sv(items)

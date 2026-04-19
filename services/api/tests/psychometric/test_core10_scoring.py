"""Scorer-layer tests for CORE-10 (Barkham 2013)."""

from __future__ import annotations

import pytest

from discipline.psychometric.scoring.core10 import (
    CORE10_CLINICAL_CUTOFF,
    CORE10_REVERSE_ITEMS,
    CORE10_RISK_ITEM,
    CORE10_SEVERITY_THRESHOLDS,
    Core10Result,
    INSTRUMENT_VERSION,
    ITEM_COUNT,
    ITEM_MAX,
    ITEM_MIN,
    InvalidResponseError,
    score_core10,
)


class TestConstants:
    """Pin the Barkham 2013 / Connell 2007 structural constants."""

    def test_item_count_is_10(self) -> None:
        assert ITEM_COUNT == 10

    def test_likert_minimum_is_0(self) -> None:
        assert ITEM_MIN == 0

    def test_likert_maximum_is_4(self) -> None:
        assert ITEM_MAX == 4

    def test_reverse_items_are_2_and_3(self) -> None:
        # Connell & Barkham 2007: items 2 (someone to turn to) and
        # 3 (able to cope) are the wellbeing/functioning items
        # worded in the distress-NEGATIVE direction.
        assert CORE10_REVERSE_ITEMS == (2, 3)

    def test_risk_item_is_6(self) -> None:
        # Connell & Barkham 2007: item 6 ("I made plans to end my
        # life") is the risk item.
        assert CORE10_RISK_ITEM == 6

    def test_clinical_cutoff_is_11(self) -> None:
        # Barkham 2013 Table 3: ≥ 11 distinguishes clinical-
        # caseness from non-clinical populations.
        assert CORE10_CLINICAL_CUTOFF == 11

    def test_severity_thresholds_pinned_to_barkham_2013(self) -> None:
        # Barkham 2013 Table 3 severity bands.
        assert CORE10_SEVERITY_THRESHOLDS == (
            (5, "healthy"),
            (10, "low"),
            (14, "mild"),
            (19, "moderate"),
            (24, "moderate_severe"),
            (40, "severe"),
        )

    def test_severity_thresholds_strictly_monotonic(self) -> None:
        bounds = [b for b, _ in CORE10_SEVERITY_THRESHOLDS]
        assert bounds == sorted(bounds)
        assert len(set(bounds)) == len(bounds)

    def test_instrument_version_pinned(self) -> None:
        assert INSTRUMENT_VERSION == "core10-1.0.0"


class TestReverseKeyingArithmetic:
    """Items 2 and 3 are reverse-keyed (flipped_v = 4 - raw_v)."""

    def test_all_zeros_gives_total_8(self) -> None:
        # 0s everywhere: items 2 and 3 flip to 4 each; others
        # remain 0.  Total = 0 + 4 + 4 + 0 + 0 + 0 + 0 + 0 + 0 + 0 = 8.
        result = score_core10([0] * 10)
        assert result.total == 8

    def test_all_fours_gives_total_32(self) -> None:
        # 4s everywhere: items 2 and 3 flip to 0 each; others
        # remain 4.  Total = 4 + 0 + 0 + 4 + 4 + 4 + 4 + 4 + 4 + 4 = 32.
        result = score_core10([4] * 10)
        assert result.total == 32

    def test_all_twos_gives_total_20(self) -> None:
        # 2s everywhere: items 2 and 3 flip to 2 each (symmetric).
        # Total = 2 × 10 = 20.  Midpoint is stationary under flip.
        result = score_core10([2] * 10)
        assert result.total == 20

    def test_item_2_reverse_keying_direction(self) -> None:
        # Raising raw item 2 DECREASES the total (reverse-keyed
        # wellbeing item).  Baseline [0]*10 = 8; same with item 2
        # = 4 should give total 4 (items 2,3 raw=4,0 flip=0,4;
        # others 0; total = 0+0+4+0+0+0+0+0+0+0 = 4).
        baseline = score_core10([0] * 10).total  # = 8
        raw = [0] * 10
        raw[1] = 4  # Item 2 (1-indexed) raw = 4
        flipped_total = score_core10(raw).total
        assert baseline - flipped_total == 4

    def test_item_3_reverse_keying_direction(self) -> None:
        # Raising raw item 3 DECREASES the total (reverse-keyed
        # functioning item).
        baseline = score_core10([0] * 10).total  # = 8
        raw = [0] * 10
        raw[2] = 4  # Item 3 (1-indexed) raw = 4
        flipped_total = score_core10(raw).total
        assert baseline - flipped_total == 4

    def test_non_reverse_item_direction(self) -> None:
        # Raising a non-reverse item (e.g., item 1) INCREASES the
        # total by the raw delta.
        baseline = score_core10([0] * 10).total  # = 8
        raw = [0] * 10
        raw[0] = 4  # Item 1 (1-indexed) raw = 4
        flipped_total = score_core10(raw).total
        assert flipped_total - baseline == 4

    def test_reverse_keyed_midpoint_invariant(self) -> None:
        # At raw = 2 on items 2 and 3, the flip is self-inverse:
        # flipped_v = 4 - 2 = 2.  Total should equal what you get
        # if you treat those items as non-reverse-keyed.
        raw = [0] * 10
        raw[1] = 2
        raw[2] = 2
        # Expected: items 2,3 flip to 2,2; others 0; total = 4.
        assert score_core10(raw).total == 4


class TestTotalRange:
    """Totals span 0-40 after reverse-keying."""

    def test_minimum_possible_total_is_0(self) -> None:
        # Achieved by setting items 2,3 to max (flip to 0) and
        # all other items to 0.
        raw = [0, 4, 4, 0, 0, 0, 0, 0, 0, 0]
        result = score_core10(raw)
        assert result.total == 0

    def test_maximum_possible_total_is_40(self) -> None:
        # Achieved by setting items 2,3 to 0 (flip to 4) and all
        # other items to 4.
        raw = [4, 0, 0, 4, 4, 4, 4, 4, 4, 4]
        result = score_core10(raw)
        assert result.total == 40

    def test_total_is_int_not_float(self) -> None:
        result = score_core10([2] * 10)
        assert isinstance(result.total, int)


class TestSeverityBands:
    """Barkham 2013 Table 3 severity-band assignment."""

    def test_total_0_is_healthy(self) -> None:
        # Raw [0,4,4,0,0,0,0,0,0,0] → total 0
        result = score_core10([0, 4, 4, 0, 0, 0, 0, 0, 0, 0])
        assert result.total == 0
        assert result.severity == "healthy"

    def test_total_5_is_healthy_upper_bound(self) -> None:
        # total=5 is within 0-5 healthy band.
        result = score_core10([1, 3, 3, 1, 1, 0, 0, 0, 0, 0])
        # 1 + 1 + 1 + 1 + 1 + 0 + 0 + 0 + 0 + 0 = 5
        assert result.total == 5
        assert result.severity == "healthy"

    def test_total_6_is_low(self) -> None:
        # total=6 enters low (6-10) band.
        result = score_core10([1, 3, 3, 1, 1, 0, 0, 0, 1, 0])
        # 1 + 1 + 1 + 1 + 1 + 0 + 0 + 0 + 1 + 0 = 6
        assert result.total == 6
        assert result.severity == "low"

    def test_total_10_is_low_upper_bound(self) -> None:
        result = score_core10([1, 3, 3, 1, 1, 0, 1, 1, 1, 1])
        # 1+1+1+1+1+0+1+1+1+1 = 9... fix the arithmetic.
        # raw=[1,3,3,1,1,0,1,1,1,1] → items 2,3 flip to 1,1
        # flipped=[1,1,1,1,1,0,1,1,1,1] → sum = 9.  Need 10.
        # Try raw=[1,3,3,1,1,0,1,1,1,2] → flipped sum = 10
        assert result.total == 9
        # Rewrite for total=10:
        result2 = score_core10([1, 3, 3, 1, 1, 0, 1, 1, 1, 2])
        assert result2.total == 10
        assert result2.severity == "low"

    def test_total_11_is_mild_at_cutoff(self) -> None:
        # Barkham 2013 clinical cutoff.
        result = score_core10([1, 3, 3, 1, 1, 0, 1, 2, 1, 2])
        # flipped=[1,1,1,1,1,0,1,2,1,2] → sum = 11
        assert result.total == 11
        assert result.severity == "mild"
        assert result.positive_screen is True

    def test_total_14_is_mild_upper_bound(self) -> None:
        result = score_core10([2, 2, 2, 2, 2, 0, 2, 2, 2, 2])
        # flipped=[2,2,2,2,2,0,2,2,2,2] → sum = 18... fix.
        # All 2s gives total 20 (shown above).  Need 14.
        # raw=[1,3,3,1,1,0,2,2,2,2] → flipped=[1,1,1,1,1,0,2,2,2,2]=13
        # raw=[1,3,3,1,2,0,2,2,2,2] → flipped=[1,1,1,1,2,0,2,2,2,2]=14
        result2 = score_core10([1, 3, 3, 1, 2, 0, 2, 2, 2, 2])
        assert result2.total == 14
        assert result2.severity == "mild"

    def test_total_15_is_moderate(self) -> None:
        result = score_core10([2, 3, 3, 2, 2, 0, 2, 2, 2, 2])
        # flipped=[2,1,1,2,2,0,2,2,2,2] → sum = 16... off.
        # Build carefully: I need sum(flipped)=15.
        # Use raw=[2,2,2,2,2,0,2,2,2,2] → flipped=[2,2,2,2,2,0,2,2,2,2]=18
        # Use raw=[1,3,3,2,2,0,2,2,2,2] → flipped=[1,1,1,2,2,0,2,2,2,2]=15
        result2 = score_core10([1, 3, 3, 2, 2, 0, 2, 2, 2, 2])
        assert result2.total == 15
        assert result2.severity == "moderate"

    def test_total_19_is_moderate_upper_bound(self) -> None:
        # Need total=19 with item 6 = 0 (so no T3 side-effect).
        # raw=[2,2,2,3,2,0,2,2,2,2] → items 2,3 flip 2→2,2→2 (self-
        # inverse); total = 2+2+2+3+2+0+2+2+2+2 = 19.
        result = score_core10([2, 2, 2, 3, 2, 0, 2, 2, 2, 2])
        assert result.total == 19
        assert result.severity == "moderate"

    def test_total_20_is_moderate_severe(self) -> None:
        result = score_core10([2] * 10)
        # All 2s → total 20 (confirmed above).
        assert result.total == 20
        assert result.severity == "moderate_severe"

    def test_total_24_is_moderate_severe_upper_bound(self) -> None:
        # Build 24: raw=[3,1,1,3,3,0,3,3,3,3] → flipped=[3,3,3,3,3,0,3,3,3,3]=27
        # raw=[2,1,1,3,3,0,3,3,3,3] → flipped=[2,3,3,3,3,0,3,3,3,3]=26
        # raw=[2,2,2,3,3,0,3,3,3,3] → flipped=[2,2,2,3,3,0,3,3,3,3]=24
        result = score_core10([2, 2, 2, 3, 3, 0, 3, 3, 3, 3])
        assert result.total == 24
        assert result.severity == "moderate_severe"

    def test_total_25_is_severe(self) -> None:
        # raw=[3,2,2,3,3,0,3,3,3,3] → flipped=[3,2,2,3,3,0,3,3,3,3]=25
        result = score_core10([3, 2, 2, 3, 3, 0, 3, 3, 3, 3])
        assert result.total == 25
        assert result.severity == "severe"

    def test_total_40_is_severe_upper_bound(self) -> None:
        # Maximum achievable total.
        result = score_core10([4, 0, 0, 4, 4, 4, 4, 4, 4, 4])
        assert result.total == 40
        assert result.severity == "severe"


class TestClinicalCutoff:
    """Barkham 2013 clinical-caseness cutoff ≥ 11."""

    def test_total_10_is_not_positive_screen(self) -> None:
        result = score_core10([1, 3, 3, 1, 1, 0, 1, 1, 1, 2])
        assert result.total == 10
        assert result.positive_screen is False

    def test_total_11_is_positive_screen(self) -> None:
        result = score_core10([1, 3, 3, 1, 1, 0, 1, 2, 1, 2])
        assert result.total == 11
        assert result.positive_screen is True

    def test_total_12_is_positive_screen(self) -> None:
        result = score_core10([1, 3, 3, 1, 2, 0, 1, 2, 1, 2])
        assert result.total == 12
        assert result.positive_screen is True

    def test_cutoff_used_always_11(self) -> None:
        # Across a range of totals, cutoff_used field always = 11.
        for total_target_raw in [
            [0] * 10,
            [2] * 10,
            [4, 0, 0, 4, 4, 4, 4, 4, 4, 4],
        ]:
            result = score_core10(total_target_raw)
            assert result.cutoff_used == 11

    def test_positive_screen_is_bool(self) -> None:
        result = score_core10([2] * 10)
        assert isinstance(result.positive_screen, bool)


class TestItem6RiskRouting:
    """CORE-10 item 6 — scorer-layer T3 on any non-zero response."""

    def test_item_6_zero_does_not_trigger_t3(self) -> None:
        # All 2s EXCEPT item 6 = 0.
        raw = [2, 2, 2, 2, 2, 0, 2, 2, 2, 2]
        result = score_core10(raw)
        assert result.requires_t3 is False
        assert result.triggering_items == ()

    @pytest.mark.parametrize("item_6_value", [1, 2, 3, 4])
    def test_item_6_non_zero_triggers_t3(self, item_6_value: int) -> None:
        # All 0s (items 2,3 max = baseline total 0) EXCEPT item 6.
        # Barkham 2013 safety guidance: any non-zero on "I made
        # plans to end my life" → mandatory clinician-review.
        raw = [0, 4, 4, 0, 0, item_6_value, 0, 0, 0, 0]
        result = score_core10(raw)
        assert result.requires_t3 is True
        assert result.triggering_items == (6,)

    def test_item_6_triggers_t3_even_at_healthy_total(self) -> None:
        # A respondent can score "healthy" overall (total < 6) AND
        # still have item 6 positive (one-off thought).  T3 fires
        # independently of total.  This is the Simon 2013 single-
        # item-suicidality precedent.
        raw = [0, 4, 4, 0, 0, 1, 0, 0, 0, 0]
        result = score_core10(raw)
        assert result.total == 1  # Healthy band
        assert result.severity == "healthy"
        assert result.requires_t3 is True
        assert result.triggering_items == (6,)

    def test_item_6_triggers_t3_at_maximum_value(self) -> None:
        # Item 6 = 4 ("Most or all the time I made plans to end
        # my life").  Must trigger T3.  Other items 0 for
        # arithmetic clarity.
        raw = [0, 4, 4, 0, 0, 4, 0, 0, 0, 0]
        result = score_core10(raw)
        assert result.requires_t3 is True
        assert 6 in result.triggering_items

    def test_triggering_items_is_tuple(self) -> None:
        raw = [0, 4, 4, 0, 0, 1, 0, 0, 0, 0]
        result = score_core10(raw)
        assert isinstance(result.triggering_items, tuple)

    def test_triggering_items_is_empty_tuple_when_no_risk(self) -> None:
        raw = [0, 4, 4, 0, 0, 0, 0, 0, 0, 0]
        result = score_core10(raw)
        assert result.triggering_items == ()

    def test_triggering_items_contains_only_item_6(self) -> None:
        # CORE-10 has ONLY item 6 as a risk item.  Even if
        # hypothetical future scorer logic were to broaden the
        # T3 criteria, the current scorer surfaces only item 6.
        raw = [4, 0, 0, 4, 4, 1, 4, 4, 4, 4]
        result = score_core10(raw)
        assert result.requires_t3 is True
        assert result.triggering_items == (6,)

    def test_item_6_routing_independent_of_reverse_keying(self) -> None:
        # Item 6 is NOT reverse-keyed (not in CORE10_REVERSE_ITEMS).
        # The T3 check uses the raw item 6 value, not flipped.
        assert CORE10_RISK_ITEM not in CORE10_REVERSE_ITEMS


class TestItemsPreserveRaw:
    """``items`` stores RAW (pre-flip) responses for audit trail."""

    def test_items_field_preserves_raw_order(self) -> None:
        raw = [0, 1, 2, 3, 4, 3, 2, 1, 0, 1]
        result = score_core10(raw)
        assert result.items == (0, 1, 2, 3, 4, 3, 2, 1, 0, 1)

    def test_items_field_is_tuple(self) -> None:
        result = score_core10([2] * 10)
        assert isinstance(result.items, tuple)

    def test_items_field_length_is_10(self) -> None:
        result = score_core10([2] * 10)
        assert len(result.items) == 10

    def test_items_preserved_pre_flip_for_items_2_and_3(self) -> None:
        # Item 2 raw=4 → flipped=0.  items[1] should be 4 (raw),
        # not 0 (post-flip).  This is the audit-invariance rule.
        raw = [0, 4, 4, 0, 0, 0, 0, 0, 0, 0]
        result = score_core10(raw)
        assert result.items[1] == 4  # Item 2 raw
        assert result.items[2] == 4  # Item 3 raw
        assert result.total == 0  # Post-flip total (confirms flip)

    def test_items_all_ints(self) -> None:
        raw = [0, 1, 2, 3, 4, 3, 2, 1, 0, 1]
        result = score_core10(raw)
        for item in result.items:
            assert isinstance(item, int)


class TestItemCountValidation:
    """Barkham 2013 pinned 10-item structure — reject others."""

    @pytest.mark.parametrize(
        "bad_count", [0, 1, 2, 5, 7, 9, 11, 12, 20]
    )
    def test_wrong_count_raises(self, bad_count: int) -> None:
        with pytest.raises(InvalidResponseError) as exc:
            score_core10([2] * bad_count)
        assert "10 items" in str(exc.value)


class TestItemValueValidation:
    """Reject out-of-range values — Connell 2007 pinned 0-4 scale."""

    def test_negative_one_rejected(self) -> None:
        raw = [2] * 10
        raw[0] = -1
        with pytest.raises(InvalidResponseError) as exc:
            score_core10(raw)
        assert "0-4" in str(exc.value)

    def test_five_rejected(self) -> None:
        raw = [2] * 10
        raw[5] = 5
        with pytest.raises(InvalidResponseError) as exc:
            score_core10(raw)
        assert "0-4" in str(exc.value)

    def test_large_positive_rejected(self) -> None:
        raw = [2] * 10
        raw[3] = 99
        with pytest.raises(InvalidResponseError):
            score_core10(raw)

    def test_error_names_item_position(self) -> None:
        raw = [2] * 10
        raw[5] = 99  # Item 6
        with pytest.raises(InvalidResponseError) as exc:
            score_core10(raw)
        assert "item 6" in str(exc.value)


class TestItemTypeValidation:
    """Reject non-int types.  Bool rejection per CLAUDE.md invariant."""

    def test_true_rejected_before_range_check(self) -> None:
        raw: list[object] = [2] * 10
        raw[0] = True
        with pytest.raises(InvalidResponseError) as exc:
            score_core10(raw)  # type: ignore[arg-type]
        assert "int" in str(exc.value)

    def test_false_rejected_before_range_check(self) -> None:
        raw: list[object] = [2] * 10
        raw[0] = False
        with pytest.raises(InvalidResponseError) as exc:
            score_core10(raw)  # type: ignore[arg-type]
        assert "int" in str(exc.value)

    def test_float_rejected(self) -> None:
        raw: list[object] = [2] * 10
        raw[0] = 2.5
        with pytest.raises(InvalidResponseError) as exc:
            score_core10(raw)  # type: ignore[arg-type]
        assert "int" in str(exc.value)

    def test_string_rejected_at_scorer(self) -> None:
        raw: list[object] = [2] * 10
        raw[0] = "2"
        with pytest.raises(InvalidResponseError) as exc:
            score_core10(raw)  # type: ignore[arg-type]
        assert "int" in str(exc.value)

    def test_none_rejected(self) -> None:
        raw: list[object] = [2] * 10
        raw[0] = None
        with pytest.raises(InvalidResponseError) as exc:
            score_core10(raw)  # type: ignore[arg-type]
        assert "int" in str(exc.value)


class TestInvalidResponseErrorIdentity:
    """InvalidResponseError is the platform scorer-error sentinel."""

    def test_is_subclass_of_value_error(self) -> None:
        assert issubclass(InvalidResponseError, ValueError)

    def test_catchable_as_value_error(self) -> None:
        with pytest.raises(ValueError):
            score_core10([1] * 9)


class TestResultTyping:
    """Verify the Core10Result dataclass contract."""

    def test_result_is_frozen(self) -> None:
        result = score_core10([2] * 10)
        with pytest.raises(Exception):
            result.total = 999  # type: ignore[misc]

    def test_result_has_no_subscales_attr(self) -> None:
        # Barkham 2013 treats CORE-10 as unidimensional routine-
        # outcome measure.  No subscales at the scorer layer.
        result = score_core10([2] * 10)
        assert not hasattr(result, "subscales")

    def test_result_has_no_index_attr(self) -> None:
        # The total IS the published score; no WHO-5-style index
        # transformation.
        result = score_core10([2] * 10)
        assert not hasattr(result, "index")

    def test_result_has_no_scaled_score_attr(self) -> None:
        result = score_core10([2] * 10)
        assert not hasattr(result, "scaled_score")

    def test_result_instrument_version_is_pinned(self) -> None:
        result = score_core10([2] * 10)
        assert result.instrument_version == INSTRUMENT_VERSION

    def test_result_severity_is_known_band(self) -> None:
        result = score_core10([2] * 10)
        allowed = {label for _, label in CORE10_SEVERITY_THRESHOLDS}
        assert result.severity in allowed


class TestClinicalVignettes:
    """Published-population-matched CORE-10 response profiles."""

    def test_recovered_patient_end_of_therapy(self) -> None:
        # Barkham 2013 typical end-of-therapy recovered case.
        # "I have felt tense once in a while but mostly fine."
        # Healthy band at total ≤ 5.
        raw = [1, 3, 3, 0, 0, 0, 1, 0, 1, 0]
        # flipped=[1,1,1,0,0,0,1,0,1,0] → 5
        result = score_core10(raw)
        assert result.total == 5
        assert result.severity == "healthy"
        assert result.positive_screen is False
        assert result.requires_t3 is False

    def test_mild_distress_iapt_intake(self) -> None:
        # Typical UK IAPT intake borderline-mild case.
        raw = [2, 2, 2, 1, 1, 0, 2, 1, 2, 2]
        # flipped=[2,2,2,1,1,0,2,1,2,2] → 15
        result = score_core10(raw)
        assert result.total == 15
        assert result.severity == "moderate"
        assert result.positive_screen is True
        assert result.requires_t3 is False

    def test_severe_depression_crisis_referral(self) -> None:
        # Severe-distress profile with no suicide-plan item
        # endorsed — still "severe" band, still no T3 at scorer
        # layer (T3 requires item 6 positive per Barkham 2013).
        raw = [4, 0, 0, 4, 3, 0, 3, 4, 4, 4]
        # flipped=[4,4,4,4,3,0,3,4,4,4] → 34
        result = score_core10(raw)
        assert result.total == 34
        assert result.severity == "severe"
        assert result.positive_screen is True
        assert result.requires_t3 is False  # Item 6 = 0

    def test_acute_suicidality_at_intake(self) -> None:
        # Severe distress WITH item-6-positive — the CORE-10's
        # designed-purpose detection case.  T3 fires; the
        # triggering_items surface drives the UI audit trail.
        raw = [4, 0, 0, 4, 3, 3, 3, 4, 4, 4]
        # flipped=[4,4,4,4,3,3,3,4,4,4] → 37
        result = score_core10(raw)
        assert result.total == 37
        assert result.severity == "severe"
        assert result.positive_screen is True
        assert result.requires_t3 is True
        assert result.triggering_items == (6,)

    def test_subclinical_but_item_6_positive(self) -> None:
        # Simon 2013 scenario: overall CORE-10 subclinical, but
        # item 6 one-off positive.  T3 MUST fire regardless of
        # total or positive_screen.
        raw = [1, 3, 3, 0, 0, 1, 1, 0, 1, 0]
        # flipped=[1,1,1,0,0,1,1,0,1,0] → 6
        result = score_core10(raw)
        assert result.total == 6
        assert result.severity == "low"
        # positive_screen is False at total=6 < 11, but T3 still
        # fires on item 6.
        assert result.positive_screen is False
        assert result.requires_t3 is True

    def test_rci_recovery_trajectory_6pt_delta(self) -> None:
        # Jacobson & Truax 1991 RCI ≈ 6 points per Barkham 2013
        # for CORE-10.  A baseline-to-follow-up 6-point delta is
        # clinically-meaningful reliable change.  Both emit
        # severity bands; trajectory layer computes the delta.
        baseline = score_core10([3, 1, 1, 3, 3, 0, 3, 3, 3, 3])
        # flipped=[3,3,3,3,3,0,3,3,3,3] → 27
        followup = score_core10([2, 2, 2, 2, 2, 0, 3, 3, 3, 2])
        # flipped=[2,2,2,2,2,0,3,3,3,2] → 21
        assert baseline.total == 27
        assert followup.total == 21
        assert baseline.total - followup.total == 6
        assert baseline.severity == "severe"
        assert followup.severity == "moderate_severe"

    def test_severity_band_boundary_10_to_11(self) -> None:
        # Boundary between "low" (≤ 10) and "mild" (≥ 11) is the
        # Barkham 2013 clinical-caseness cutoff.  An instrument
        # error at this boundary would misclassify non-clinical
        # as clinical or vice versa.
        at_ten = score_core10([1, 3, 3, 1, 1, 0, 1, 1, 1, 2])
        at_eleven = score_core10([1, 3, 3, 1, 1, 0, 1, 2, 1, 2])
        assert at_ten.total == 10
        assert at_eleven.total == 11
        assert at_ten.severity == "low"
        assert at_eleven.severity == "mild"
        assert at_ten.positive_screen is False
        assert at_eleven.positive_screen is True


class TestResultInstanceShape:
    """The Core10Result instance carries exactly the declared fields."""

    def test_result_is_core10_result(self) -> None:
        result = score_core10([2] * 10)
        assert isinstance(result, Core10Result)

    def test_result_total_is_int(self) -> None:
        result = score_core10([2] * 10)
        assert isinstance(result.total, int)

    def test_result_severity_is_str(self) -> None:
        result = score_core10([2] * 10)
        assert isinstance(result.severity, str)

    def test_result_positive_screen_is_bool(self) -> None:
        result = score_core10([2] * 10)
        assert isinstance(result.positive_screen, bool)

    def test_result_cutoff_used_is_int(self) -> None:
        result = score_core10([2] * 10)
        assert isinstance(result.cutoff_used, int)

    def test_result_requires_t3_is_bool(self) -> None:
        result = score_core10([2] * 10)
        assert isinstance(result.requires_t3, bool)

    def test_result_triggering_items_is_tuple(self) -> None:
        result = score_core10([2] * 10)
        assert isinstance(result.triggering_items, tuple)

    def test_result_items_is_tuple_of_ints(self) -> None:
        result = score_core10([2] * 10)
        assert isinstance(result.items, tuple)
        for item in result.items:
            assert isinstance(item, int)

    def test_result_instrument_version_is_str(self) -> None:
        result = score_core10([2] * 10)
        assert isinstance(result.instrument_version, str)

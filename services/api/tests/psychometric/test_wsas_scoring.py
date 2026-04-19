"""WSAS scoring tests — Mundt 2002 Work and Social Adjustment Scale.

Three load-bearing correctness properties for the 5-item WSAS:

1. **Items are 0-8 Likert — NOVEL widest envelope in the package.**
   Mundt 2002 designed the 0-8 range deliberately; prior package
   envelopes topped out at 1-7 (AAQ-II).  An item of 9 must reject
   and items of 6/7/8 must accept — pinning the ceiling at 8
   explicitly rather than inheriting from a narrower neighbor by
   accident.
2. **Cut-points are 10 and 20, not 9/19 nor 11/21.**  Mundt 2002
   published exactly these thresholds; the boundary tests pin 9/10
   and 19/20 explicitly, and 20 at-cutoff maps to "severe" (not
   "significant").
3. **Exactly 5 items, each in ``[0, 8]``.**  A response outside
   ``[0, 8]`` is a validation error, not a silent coercion.  Wrong
   item counts (PHQ-9's 9, AAQ-II's 7, K10's 10) reject with a clear
   message rather than silently taking the first 5.

Coverage strategy matches K10 / ISI / OCI-R / PCL-5 (the other
banded-severity instruments):
- Pin total-correctness across the total range.
- Pin every band boundary just-below and at-cutoff.
- Bool rejection (uniform with the rest of the package).
- Item-count and item-range rejection (including misroute checks
  from adjacent instruments).
- Clinical vignettes a clinician would recognize.
- No safety routing — WSAS has no direct suicidality item.
- No subscale fields — Mundt 2002 validates a unidimensional total.
- No cutoff_used / positive_screen (banded shape, not cutoff shape).
"""

from __future__ import annotations

import pytest

from discipline.psychometric.scoring.wsas import (
    INSTRUMENT_VERSION,
    ITEM_COUNT,
    ITEM_MAX,
    ITEM_MIN,
    InvalidResponseError,
    WSAS_SEVERITY_THRESHOLDS,
    WsasResult,
    score_wsas,
)


class TestConstants:
    """Pin the module-level constants so changes force a clinical sign-off."""

    def test_instrument_version(self):
        assert INSTRUMENT_VERSION == "wsas-1.0.0"

    def test_item_count(self):
        assert ITEM_COUNT == 5

    def test_item_min(self):
        assert ITEM_MIN == 0

    def test_item_max_is_novel_eight(self):
        assert ITEM_MAX == 8

    def test_thresholds_published(self):
        assert WSAS_SEVERITY_THRESHOLDS == (
            (20, "severe"),
            (10, "significant"),
            (0, "subclinical"),
        )

    def test_thresholds_ordered_descending(self):
        for i in range(len(WSAS_SEVERITY_THRESHOLDS) - 1):
            assert (
                WSAS_SEVERITY_THRESHOLDS[i][0]
                > WSAS_SEVERITY_THRESHOLDS[i + 1][0]
            )


class TestTotalCorrectness:
    """Simple arithmetic pin — the total is the raw sum."""

    def test_all_zero(self):
        result = score_wsas([0, 0, 0, 0, 0])
        assert result.total == 0

    def test_all_max(self):
        result = score_wsas([8, 8, 8, 8, 8])
        assert result.total == 40

    def test_mixed(self):
        result = score_wsas([3, 5, 2, 7, 4])
        assert result.total == 21

    def test_items_preserved_in_order(self):
        result = score_wsas([1, 3, 5, 7, 0])
        assert result.items == (1, 3, 5, 7, 0)

    def test_single_max_rest_zero(self):
        result = score_wsas([8, 0, 0, 0, 0])
        assert result.total == 8

    def test_total_is_int(self):
        result = score_wsas([2, 4, 6, 3, 5])
        assert isinstance(result.total, int)


class TestSeverityBands:
    """Pin the Mundt 2002 bands at every boundary."""

    def test_total_zero_is_subclinical(self):
        assert score_wsas([0, 0, 0, 0, 0]).severity == "subclinical"

    def test_total_nine_is_subclinical(self):
        # 2+2+2+2+1 = 9 — just below the significant band.
        assert score_wsas([2, 2, 2, 2, 1]).severity == "subclinical"

    def test_total_ten_is_significant(self):
        # 2+2+2+2+2 = 10 — at the significant boundary.
        assert score_wsas([2, 2, 2, 2, 2]).severity == "significant"

    def test_total_nineteen_is_significant(self):
        # 4+4+4+4+3 = 19 — just below the severe band.
        assert score_wsas([4, 4, 4, 4, 3]).severity == "significant"

    def test_total_twenty_is_severe(self):
        # 4+4+4+4+4 = 20 — at the severe boundary.
        assert score_wsas([4, 4, 4, 4, 4]).severity == "severe"

    def test_total_twenty_one_is_severe(self):
        assert score_wsas([5, 4, 4, 4, 4]).severity == "severe"

    def test_total_forty_is_severe(self):
        assert score_wsas([8, 8, 8, 8, 8]).severity == "severe"

    @pytest.mark.parametrize(
        "items,expected_total,expected_band",
        [
            ([0, 0, 0, 0, 0], 0, "subclinical"),
            ([1, 1, 1, 1, 1], 5, "subclinical"),
            ([2, 2, 2, 1, 2], 9, "subclinical"),
            ([2, 2, 2, 2, 2], 10, "significant"),
            ([3, 3, 3, 3, 2], 14, "significant"),
            ([4, 4, 4, 3, 4], 19, "significant"),
            ([4, 4, 4, 4, 4], 20, "severe"),
            ([5, 5, 5, 5, 5], 25, "severe"),
            ([6, 6, 6, 6, 6], 30, "severe"),
            ([7, 7, 7, 7, 7], 35, "severe"),
            ([8, 8, 8, 8, 8], 40, "severe"),
        ],
    )
    def test_band_parametrized(self, items, expected_total, expected_band):
        result = score_wsas(items)
        assert result.total == expected_total
        assert result.severity == expected_band


class TestItemCountValidation:
    """Wrong-length inputs must reject, not silently truncate."""

    def test_empty_list_rejects(self):
        with pytest.raises(InvalidResponseError, match="exactly 5 items"):
            score_wsas([])

    def test_four_items_rejects(self):
        with pytest.raises(InvalidResponseError, match="exactly 5 items"):
            score_wsas([1, 2, 3, 4])

    def test_six_items_rejects(self):
        with pytest.raises(InvalidResponseError, match="exactly 5 items"):
            score_wsas([1, 2, 3, 4, 5, 6])

    def test_phq9_length_rejects(self):
        # Protect against a caller routing a 9-item PHQ-9 response here.
        with pytest.raises(InvalidResponseError, match="exactly 5 items"):
            score_wsas([1] * 9)

    def test_aaq2_length_rejects(self):
        # Protect against a 7-item AAQ-II response being routed here.
        with pytest.raises(InvalidResponseError, match="exactly 5 items"):
            score_wsas([1] * 7)

    def test_k10_length_rejects(self):
        # Protect against a 10-item K10 response being routed here.
        with pytest.raises(InvalidResponseError, match="exactly 5 items"):
            score_wsas([1] * 10)


class TestItemRangeValidation:
    """0-8 envelope — accept 0 and 8, reject -1 and 9."""

    def test_negative_rejects(self):
        with pytest.raises(InvalidResponseError, match="out of range"):
            score_wsas([-1, 0, 0, 0, 0])

    def test_nine_rejects(self):
        with pytest.raises(InvalidResponseError, match="out of range"):
            score_wsas([9, 0, 0, 0, 0])

    def test_ten_rejects(self):
        with pytest.raises(InvalidResponseError, match="out of range"):
            score_wsas([10, 0, 0, 0, 0])

    def test_zero_accepts(self):
        # Zero is valid — "Not at all impaired".
        result = score_wsas([0, 0, 0, 0, 0])
        assert result.total == 0

    def test_eight_accepts_at_ceiling(self):
        # NOVEL — ceiling is 8, wider than any prior package instrument.
        result = score_wsas([8, 0, 0, 0, 0])
        assert result.total == 8

    def test_six_and_seven_accept(self):
        # Pin the 0-8 envelope as distinct from 0-4 / 0-5 / 1-5 / 0-3.
        result = score_wsas([6, 7, 6, 7, 0])
        assert result.total == 26

    @pytest.mark.parametrize("bad_value", [-5, -1, 9, 10, 100, 255])
    def test_out_of_range_rejects(self, bad_value):
        with pytest.raises(InvalidResponseError, match="out of range"):
            score_wsas([bad_value, 0, 0, 0, 0])

    def test_error_message_names_item_index(self):
        # Offending item should be the third (1-indexed).
        with pytest.raises(InvalidResponseError, match="item 3"):
            score_wsas([0, 0, 9, 0, 0])

    def test_error_message_includes_bounds(self):
        with pytest.raises(InvalidResponseError, match=r"\[0, 8\]"):
            score_wsas([0, 0, 0, 0, 9])


class TestItemTypeValidation:
    """Non-int items must reject — no silent coercion."""

    def test_float_rejects(self):
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_wsas([3.5, 0, 0, 0, 0])

    def test_string_rejects(self):
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_wsas(["3", 0, 0, 0, 0])

    def test_none_rejects(self):
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_wsas([None, 0, 0, 0, 0])


class TestBoolRejection:
    """Bool is a Python int subclass — reject explicitly at the validator."""

    def test_true_rejects(self):
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_wsas([True, 0, 0, 0, 0])

    def test_false_rejects(self):
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_wsas([False, 0, 0, 0, 0])

    def test_mixed_bool_int_rejects(self):
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_wsas([1, 2, True, 3, 4])

    def test_bool_at_last_position_rejects(self):
        with pytest.raises(InvalidResponseError, match="item 5"):
            score_wsas([0, 0, 0, 0, True])


class TestResultShape:
    """WsasResult is a frozen, hashable, introspectable dataclass."""

    def test_result_is_frozen(self):
        result = score_wsas([1, 2, 3, 4, 5])
        with pytest.raises((AttributeError, Exception)):
            result.total = 999  # type: ignore[misc]

    def test_items_is_tuple(self):
        result = score_wsas([0, 1, 2, 3, 4])
        assert isinstance(result.items, tuple)

    def test_result_is_hashable(self):
        result = score_wsas([1, 2, 3, 4, 5])
        assert hash(result) is not None

    def test_instrument_version_defaulted(self):
        result = score_wsas([0, 0, 0, 0, 0])
        assert result.instrument_version == INSTRUMENT_VERSION

    def test_result_has_no_cutoff_used_field(self):
        # WSAS is banded, not cutoff — no cutoff_used surfaces here.
        result = score_wsas([0, 0, 0, 0, 0])
        assert not hasattr(result, "cutoff_used")

    def test_result_has_no_positive_screen_field(self):
        # WSAS is banded, not cutoff — no positive_screen surfaces here.
        result = score_wsas([0, 0, 0, 0, 0])
        assert not hasattr(result, "positive_screen")

    def test_result_has_no_requires_t3_field(self):
        # WSAS has no safety item — requires_t3 must not be present.
        result = score_wsas([8, 8, 8, 8, 8])
        assert not hasattr(result, "requires_t3")

    def test_result_has_no_subscales_field(self):
        # Mundt 2002 CFA — unidimensional; no subscales.
        result = score_wsas([0, 0, 0, 0, 0])
        assert not hasattr(result, "subscales")

    def test_result_has_no_triggering_items_field(self):
        # Banded instruments don't surface triggering_items.
        result = score_wsas([8, 8, 8, 8, 8])
        assert not hasattr(result, "triggering_items")

    def test_result_repr_is_readable(self):
        result = score_wsas([4, 4, 4, 4, 4])
        rendered = repr(result)
        assert "total=20" in rendered
        assert "severe" in rendered


class TestClinicalVignettes:
    """Clinician-readable scenarios pinning the functional-impairment construct."""

    def test_mild_executive_but_working(self):
        # Slight interference across domains, still functional.
        # 1 + 2 + 1 + 1 + 1 = 6, subclinical.
        result = score_wsas([1, 2, 1, 1, 1])
        assert result.total == 6
        assert result.severity == "subclinical"

    def test_work_intact_but_relationships_impaired(self):
        # Can still work; social/private/relationships significantly
        # impaired.  0 + 1 + 4 + 4 + 5 = 14, significant.
        result = score_wsas([0, 1, 4, 4, 5])
        assert result.total == 14
        assert result.severity == "significant"

    def test_depression_with_severe_functional_impairment(self):
        # Severe impairment across every domain — 6 + 6 + 6 + 6 + 6 = 30.
        result = score_wsas([6, 6, 6, 6, 6])
        assert result.total == 30
        assert result.severity == "severe"

    def test_functional_collapse(self):
        # Maximal impairment across every domain.
        result = score_wsas([8, 8, 8, 8, 8])
        assert result.total == 40
        assert result.severity == "severe"

    def test_symptom_severity_orthogonal_to_impairment_low_case(self):
        # Patient may have high PHQ-9 (rumination, low energy) but
        # preserved function — e.g. "I feel terrible but still show
        # up to work, still manage the household".
        result = score_wsas([1, 1, 2, 2, 1])
        assert result.total == 7
        assert result.severity == "subclinical"

    def test_symptom_severity_orthogonal_to_impairment_high_case(self):
        # Patient may have low PHQ-9 but severe functional impairment
        # — e.g. post-trauma avoidance patterns without full MDD.
        result = score_wsas([6, 5, 7, 4, 5])
        assert result.total == 27
        assert result.severity == "severe"


class TestNoSafetyRouting:
    """WSAS has no safety item — requires_t3 never fires."""

    def test_all_max_does_not_fire_t3(self):
        # Even maximal functional impairment is not a suicidality gate.
        result = score_wsas([8, 8, 8, 8, 8])
        assert not hasattr(result, "requires_t3")

    def test_result_never_has_requires_t3(self):
        # Pin across severity bands.
        for items in [
            [0, 0, 0, 0, 0],
            [2, 2, 2, 2, 2],
            [4, 4, 4, 4, 4],
            [8, 8, 8, 8, 8],
        ]:
            result = score_wsas(items)
            assert not hasattr(result, "requires_t3")

    def test_severe_band_is_not_a_crisis_gate(self):
        # A "severe" WSAS is a strong signal for intensive
        # behavioral-activation work but is NOT a crisis gate.
        result = score_wsas([8, 8, 8, 8, 8])
        assert result.severity == "severe"
        assert not hasattr(result, "requires_t3")

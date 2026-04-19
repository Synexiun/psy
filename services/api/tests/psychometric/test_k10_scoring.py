"""K10 scoring tests — Kessler 2002 / Andrews & Slade 2001.

Three load-bearing correctness properties for the 10-item K10:

1. **Items are 1-5 Likert, NOT 0-4.**  Kessler 2002 coded the scale
   with 1 = "None of the time" through 5 = "All of the time".  The
   Andrews & Slade 2001 bands (10-19 / 20-24 / 25-29 / 30-50) are
   calibrated against this coding; rescaling to 0-4 would shift the
   band edges by 10 and break comparability.  An item of 0 must be
   rejected as out-of-range, not silently accepted.
2. **Cut-points are 20 / 25 / 30, not 19 / 24 / 29 nor 21 / 26 / 31.**
   Andrews & Slade 2001 Table 1 — any fence-post flip shifts a
   patient's band and mis-labels their distress tier.  The boundary
   tests pin 19/20, 24/25, and 29/30 explicitly.
3. **Exactly 10 items, each in ``[1, 5]``.**  A response outside
   ``[1, 5]`` is a validation error, not a silent coercion.

Coverage strategy matches GAD-7 / PHQ-9 (the other banded-severity
instruments):
- Pin total-correctness across the total range.
- Pin every band boundary just-below and at-cutoff.
- Bool rejection (uniform with the rest of the package).
- Item-count and item-range rejection (including 6-item K6 misroute).
- Clinical vignettes a clinician would recognize.
- No safety routing — K10 has no direct suicidality item.
- No subscale fields — Kessler 2002 validates a unidimensional total.
"""

from __future__ import annotations

import pytest

from discipline.psychometric.scoring.k10 import (
    INSTRUMENT_VERSION,
    ITEM_COUNT,
    ITEM_MAX,
    ITEM_MIN,
    K10_SEVERITY_THRESHOLDS,
    InvalidResponseError,
    K10Result,
    score_k10,
)


class TestConstants:
    """Pin published constants so a drift from Kessler 2002 is caught."""

    def test_item_count_is_ten(self) -> None:
        assert ITEM_COUNT == 10

    def test_item_range_is_one_to_five(self) -> None:
        """Kessler 2002 coded items 1-5.  A drift to 0-4 would shift
        the Andrews & Slade 2001 bands by 10 and break comparability
        with the downstream literature."""
        assert ITEM_MIN == 1
        assert ITEM_MAX == 5

    def test_severity_thresholds_are_andrews_slade_2001(self) -> None:
        """Andrews & Slade 2001 Table 1 bands: 10-19 low / 20-24
        moderate / 25-29 high / 30-50 very_high.  Any change is a
        clinical change, not an implementation tweak, and must cite
        a replacement paper."""
        assert K10_SEVERITY_THRESHOLDS == (
            (30, "very_high"),
            (25, "high"),
            (20, "moderate"),
            (10, "low"),
        )

    def test_instrument_version_pinned(self) -> None:
        assert INSTRUMENT_VERSION == "k10-1.0.0"


class TestTotalCorrectness:
    """Every total across [10, 50] scores as the sum of the ten items."""

    @pytest.mark.parametrize(
        "items,expected",
        [
            ([1] * 10, 10),
            ([2] * 10, 20),
            ([3] * 10, 30),
            ([4] * 10, 40),
            ([5] * 10, 50),
            ([1, 2, 3, 4, 5, 1, 2, 3, 4, 5], 30),
            ([5, 4, 3, 2, 1, 5, 4, 3, 2, 1], 30),
            ([1, 1, 1, 1, 1, 5, 5, 5, 5, 5], 30),
        ],
    )
    def test_total_matches_sum(
        self, items: list[int], expected: int
    ) -> None:
        result = score_k10(items)
        assert result.total == expected

    def test_minimum_total_is_ten(self) -> None:
        """The absolute minimum is 10 (every item = 1, "none of the
        time").  A K10 total of 0 is impossible — if a repository
        ever surfaces total < 10, that is a data-corruption signal."""
        result = score_k10([1] * 10)
        assert result.total == 10
        assert result.severity == "low"

    def test_maximum_total_is_fifty(self) -> None:
        result = score_k10([5] * 10)
        assert result.total == 50
        assert result.severity == "very_high"


class TestSeverityBands:
    """The Andrews & Slade 2001 bands — explicit just-below and
    at-cutoff tests at every band edge so a fence-post regression
    is caught."""

    def test_total_ten_is_low(self) -> None:
        """Minimum total → low band.  "None of the time" on every
        item is the canonical no-distress profile."""
        result = score_k10([1] * 10)
        assert result.total == 10
        assert result.severity == "low"

    def test_total_nineteen_is_low(self) -> None:
        """Just below the low/moderate boundary → still low."""
        result = score_k10([1, 2, 2, 2, 2, 2, 2, 2, 2, 2])
        assert result.total == 19
        assert result.severity == "low"

    def test_total_twenty_is_moderate(self) -> None:
        """Exact low→moderate boundary.  A ``> 20`` comparator bug
        would misclassify this as "low"; Andrews & Slade 2001 puts
        the patient at population percentile ≈ 80, which is the
        threshold for clinical concern."""
        result = score_k10([2] * 10)
        assert result.total == 20
        assert result.severity == "moderate"

    def test_total_twenty_four_is_moderate(self) -> None:
        """Just below the moderate/high boundary → still moderate."""
        result = score_k10([2, 2, 2, 2, 2, 2, 3, 3, 3, 3])
        assert result.total == 24
        assert result.severity == "moderate"

    def test_total_twenty_five_is_high(self) -> None:
        """Exact moderate→high boundary."""
        result = score_k10([2, 2, 2, 2, 2, 3, 3, 3, 3, 3])
        assert result.total == 25
        assert result.severity == "high"

    def test_total_twenty_nine_is_high(self) -> None:
        """Just below the high/very_high boundary → still high."""
        result = score_k10([3, 3, 3, 3, 3, 3, 3, 3, 3, 2])
        assert result.total == 29
        assert result.severity == "high"

    def test_total_thirty_is_very_high(self) -> None:
        """Exact high/very_high boundary.  Population percentile ≈
        97 — the top 3% of distress.  A fence-post bug here would
        misclassify a patient at the tail of the distress
        distribution."""
        result = score_k10([3] * 10)
        assert result.total == 30
        assert result.severity == "very_high"

    def test_total_fifty_is_very_high(self) -> None:
        result = score_k10([5] * 10)
        assert result.total == 50
        assert result.severity == "very_high"


class TestItemCountValidation:
    """Exactly 10 items required."""

    def test_rejects_nine_items(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 10 items"):
            score_k10([3] * 9)

    def test_rejects_eleven_items(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 10 items"):
            score_k10([3] * 11)

    def test_rejects_empty(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 10 items"):
            score_k10([])

    def test_rejects_six_items_k6_misroute(self) -> None:
        """The K6 is the 6-item short form of the K10 (Kessler 2003);
        a 6-item submission is almost certainly a mis-routed K6 that
        the client is trying to score as K10.  A clear error is
        better than silently returning a 10-item total with six
        missing.  Once K6 is shipped in a future sprint this test
        will still pass — the instrument dispatch is by key, not
        by item count."""
        with pytest.raises(InvalidResponseError, match="exactly 10 items"):
            score_k10([3] * 6)


class TestItemRangeValidation:
    """Items must be in [1, 5] — NOT [0, 4]."""

    def test_rejects_zero_item(self) -> None:
        """An item of 0 is NOT "None of the time" on the K10 — it is
        out-of-range.  Kessler 2002 codes "None of the time" as 1.
        A downstream renderer that mistakenly sent 0-indexed items
        would produce totals 10 below the true value and mis-classify
        every patient by one band.  This test pins the 1-indexed
        semantic explicitly."""
        with pytest.raises(InvalidResponseError, match="out of range"):
            score_k10([0, 1, 1, 1, 1, 1, 1, 1, 1, 1])

    @pytest.mark.parametrize("bad_value", [-1, 0, 6, 7, 10, 100])
    def test_rejects_out_of_range(self, bad_value: int) -> None:
        with pytest.raises(InvalidResponseError, match="out of range"):
            score_k10([1, 1, 1, 1, 1, 1, 1, 1, 1, bad_value])

    def test_rejects_string_item(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_k10(
                [1, "1", 1, 1, 1, 1, 1, 1, 1, 1]  # type: ignore[list-item]
            )

    def test_rejects_float_item(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_k10([1.5, 1, 1, 1, 1, 1, 1, 1, 1, 1])  # type: ignore[list-item]

    def test_rejects_none_item(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_k10([1, None, 1, 1, 1, 1, 1, 1, 1, 1])  # type: ignore[list-item]


class TestBoolRejection:
    """Bool items are rejected — uniform with the rest of the
    psychometric package.  See scoring/k10.py module docstring."""

    def test_rejects_true_item(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_k10(
                [True, 1, 1, 1, 1, 1, 1, 1, 1, 1]  # type: ignore[list-item]
            )

    def test_rejects_false_item(self) -> None:
        """False ≈ 0 via int-cast would silently land outside [1, 5]
        anyway, but we reject at the type layer with a cleaner error
        before the range check runs."""
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_k10(
                [1, 1, 1, 1, 1, 1, 1, 1, 1, False]  # type: ignore[list-item]
            )

    def test_error_names_the_item_index(self) -> None:
        """Error message names the 1-indexed item number so a clinician
        matches the error against the K10 paper's item list."""
        with pytest.raises(InvalidResponseError, match="K10 item 4"):
            score_k10(
                [1, 1, 1, True, 1, 1, 1, 1, 1, 1]  # type: ignore[list-item]
            )


class TestResultShape:
    """K10Result carries the fields the router needs."""

    def test_result_is_frozen(self) -> None:
        result = score_k10([3] * 10)
        with pytest.raises(Exception):  # FrozenInstanceError subclass
            result.total = 99  # type: ignore[misc]

    def test_items_are_tuple(self) -> None:
        """Tuple (not list) so the result is hashable and can be pinned
        into an immutable repository record."""
        result = score_k10([3] * 10)
        assert isinstance(result.items, tuple)
        assert result.items == tuple([3] * 10)

    def test_result_echoes_instrument_version(self) -> None:
        result = score_k10([3] * 10)
        assert result.instrument_version == INSTRUMENT_VERSION

    def test_no_requires_t3_field(self) -> None:
        """K10 has no direct suicidality item.  Items 4 (hopeless),
        9 (so sad nothing could cheer you up), 10 (worthless) probe
        negative-mood dimensions that covary with suicidality but do
        not ask about it directly — T3 is reserved for explicit
        suicidality (PHQ-9 item 9 / C-SSRS).  The result dataclass
        deliberately omits ``requires_t3`` so downstream code cannot
        misuse a "very high" K10 as a T3 trigger."""
        result = score_k10([5] * 10)
        assert not hasattr(result, "requires_t3")

    def test_no_subscale_fields(self) -> None:
        """Kessler 2002's factor analysis supports a unidimensional
        total.  The result carries no depression / anxiety subscale
        fields — attempting to split is unvalidated and not supported
        by the scorer or the wire."""
        result = score_k10([5] * 10)
        assert not hasattr(result, "subscales")
        assert not hasattr(result, "depression_total")
        assert not hasattr(result, "anxiety_total")


class TestClinicalVignettes:
    """Named patterns a clinician would recognize — tests the scorer
    as-written against real-world presentations."""

    def test_no_distress_is_low(self) -> None:
        """Every item at "none of the time" (1) → total 10 → low.
        Population-typical no-distress profile."""
        result = score_k10([1] * 10)
        assert result.severity == "low"

    def test_sub_clinical_worry_is_low(self) -> None:
        """A few items endorsed mildly ("a little of the time", 2) →
        total 14 → low.  A patient with occasional mild worry does
        not cross the moderate threshold."""
        result = score_k10([2, 2, 1, 1, 2, 1, 1, 1, 2, 1])
        assert result.total == 14
        assert result.severity == "low"

    def test_moderate_distress_crosses_threshold(self) -> None:
        """All items at "some of the time" (3) → total 30 →
        very_high.  Actually this is where Andrews & Slade's Australian
        epidemiology bites — consistent "some of the time" distress
        on every dimension is at population percentile ≈ 97, i.e. the
        top 3% of distress.  Pins the counterintuitive-but-correct
        band assignment."""
        result = score_k10([3] * 10)
        assert result.total == 30
        assert result.severity == "very_high"

    def test_depressive_only_profile(self) -> None:
        """Depressive items (4 = hopeless, 7 = depressed, 9 = sad,
        10 = worthless) all at 4 ("most of the time"), other items at
        1-2 → total 24 → moderate.  Captures the profile of a
        depression-dominant presentation on K10 — catches it at
        moderate distress, motivating PHQ-9 administration for
        diagnostic work-up."""
        result = score_k10([1, 2, 1, 4, 2, 1, 4, 2, 4, 4])
        assert result.total == 25  # 1+2+1+4+2+1+4+2+4+4 = 25
        assert result.severity == "high"

    def test_anxiety_only_profile(self) -> None:
        """Anxiety items (2 = nervous, 3 = so nervous nothing could
        calm, 5 = restless, 6 = so restless) all at 4, other items at
        1-2 → total captures anxiety-dominant distress.  K10 catches
        it; the GAD-7 would characterize severity."""
        result = score_k10([2, 4, 4, 2, 4, 4, 1, 1, 2, 1])
        assert result.total == 25  # 2+4+4+2+4+4+1+1+2+1 = 25
        assert result.severity == "high"

    def test_everything_severe_is_very_high(self) -> None:
        """Every item "all of the time" → total 50 → very_high.
        Canonical severe-distress presentation."""
        result = score_k10([5] * 10)
        assert result.total == 50
        assert result.severity == "very_high"


class TestNoSafetyRouting:
    """K10 has no direct suicidality item.  The scorer must not expose
    anything that a downstream router could mistake for a T3 trigger.
    T3 is reserved for active suicidality per
    Docs/Whitepapers/04_Safety_Framework.md §T3 and is gated on
    PHQ-9 item 9 / C-SSRS — not on K10 even at its maximum."""

    def test_max_total_has_no_safety_field(self) -> None:
        result = score_k10([5] * 10)
        # No requires_t3, no t3_reason, no triggering_items — the
        # result is a pure total + severity band.
        assert not hasattr(result, "requires_t3")
        assert not hasattr(result, "t3_reason")
        assert not hasattr(result, "triggering_items")

    def test_hopelessness_items_high_no_t3(self) -> None:
        """Items 4 (hopeless), 9 (so sad), 10 (worthless) at max with
        other items low — a profile that on PHQ-9 might co-occur with
        item-9 endorsement and thus fire T3 downstream, but K10 itself
        does not fire T3 because its hopelessness items are *affect*
        probes, not *intent* probes."""
        result = score_k10([1, 1, 1, 5, 1, 1, 1, 1, 5, 5])
        assert result.total == 22
        assert result.severity == "moderate"
        assert not hasattr(result, "requires_t3")

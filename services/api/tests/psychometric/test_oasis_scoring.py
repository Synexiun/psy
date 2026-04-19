"""OASIS scoring tests — Norman 2006 / Campbell-Sills 2009.

Two load-bearing correctness properties for the 5-item OASIS:

1. **Cutoff is ``>= 8``, not ``> 8`` and not ``>= 7``.**  Campbell-Sills
   2009 §Results — cutpoint 8 is the published operating point
   (sensitivity 0.87, specificity 0.66 for any anxiety disorder).  A
   fence-post bug that flipped the comparator would either miss true
   positives (``> 8`` turns an 8-total screen negative) or over-fire
   on sub-clinical anxiety (``>= 7``).  The boundary tests pin 7 and
   8 explicitly.
2. **Exactly 5 items, each in ``[0, 4]`` Likert.**  OASIS is a 0-4
   five-point Likert on frequency / intensity / avoidance / work /
   social impairment.  A response outside ``[0, 4]`` is a validation
   error, not a silent coercion.

Coverage strategy matches PC-PTSD-5 / GAD-2 / PHQ-2 (the other
cutoff-envelope instruments):
- Pin total-correctness across representative combinations.
- Pin the cutoff boundary both just-below (7) and at-cutoff (8) so
  the published operating point is nailed down.
- Bool rejection (uniform with the rest of the package).
- Item-count and item-range rejection (including 7-item GAD-7
  misroute case).
- Clinical vignettes (avoidance-only, impairment-only, symptom-only,
  balanced presentations at/below/above cutoff).
- No safety routing — OASIS has no safety item, so ``requires_t3``
  never appears on the result dataclass.  See module docstring.
- No severity bands — Norman 2006 validates only the total.  The
  result carries no ``severity`` field.
"""

from __future__ import annotations

import pytest

from discipline.psychometric.scoring.oasis import (
    INSTRUMENT_VERSION,
    ITEM_COUNT,
    ITEM_MAX,
    ITEM_MIN,
    OASIS_POSITIVE_CUTOFF,
    InvalidResponseError,
    OasisResult,
    score_oasis,
)


class TestConstants:
    """Pin published constants so a drift from Norman 2006 /
    Campbell-Sills 2009 is caught."""

    def test_item_count_is_five(self) -> None:
        assert ITEM_COUNT == 5

    def test_item_range_is_zero_to_four(self) -> None:
        assert ITEM_MIN == 0
        assert ITEM_MAX == 4

    def test_positive_cutoff_is_eight(self) -> None:
        """Campbell-Sills 2009 §Results — cutpoint 8 is the published
        operating point (sensitivity 0.87, specificity 0.66 for any
        DSM-IV anxiety disorder).  Any change to this constant is a
        clinical change, not an implementation tweak, and must cite a
        replacement paper."""
        assert OASIS_POSITIVE_CUTOFF == 8

    def test_instrument_version_pinned(self) -> None:
        assert INSTRUMENT_VERSION == "oasis-1.0.0"


class TestTotalCorrectness:
    """Every total across [0, 20] scores as the sum of the five items."""

    @pytest.mark.parametrize(
        "items,expected",
        [
            ([0, 0, 0, 0, 0], 0),
            ([1, 0, 0, 0, 0], 1),
            ([0, 0, 0, 0, 1], 1),
            ([1, 1, 1, 1, 1], 5),
            ([2, 2, 1, 1, 1], 7),
            ([2, 2, 2, 1, 1], 8),
            ([4, 0, 0, 0, 0], 4),
            ([0, 0, 0, 0, 4], 4),
            ([2, 2, 2, 2, 2], 10),
            ([3, 3, 3, 3, 3], 15),
            ([4, 4, 4, 4, 4], 20),
        ],
    )
    def test_total_matches_sum(
        self, items: list[int], expected: int
    ) -> None:
        result = score_oasis(items)
        assert result.total == expected

    def test_zero_total_is_negative(self) -> None:
        result = score_oasis([0, 0, 0, 0, 0])
        assert result.total == 0
        assert result.positive_screen is False

    def test_max_total_is_positive(self) -> None:
        result = score_oasis([4, 4, 4, 4, 4])
        assert result.total == 20
        assert result.positive_screen is True


class TestCutoffBoundary:
    """The ``>= 8`` boundary — explicit just-below and at-cutoff tests
    so a fence-post regression is caught."""

    def test_total_seven_is_below_cutoff(self) -> None:
        """Total = 7 (e.g. two items "moderate" + three "mild") →
        negative screen.  Campbell-Sills 2009 considered cutpoints
        6 and 7 but selected 8 as the operating point for best
        balance of sensitivity and specificity; the scorer must
        encode the chosen cutpoint."""
        result = score_oasis([2, 2, 1, 1, 1])
        assert result.total == 7
        assert result.positive_screen is False

    def test_total_eight_is_at_cutoff(self) -> None:
        """Total = 8 → positive screen.  This is the exact published
        cutoff; a ``> 8`` comparator bug would flip this to negative
        and under-identify a large fraction of true cases."""
        result = score_oasis([2, 2, 2, 1, 1])
        assert result.total == 8
        assert result.positive_screen is True

    def test_total_nine_is_above_cutoff(self) -> None:
        result = score_oasis([2, 2, 2, 2, 1])
        assert result.total == 9
        assert result.positive_screen is True

    def test_single_high_item_cannot_reach_cutoff(self) -> None:
        """One item at max (4), four zeros → total = 4 → negative.
        An extreme-but-isolated endorsement on one dimension does
        not cross the multi-dimensional cutoff.  Pins the scorer's
        sum-based gate against any "max-item triggers screen"
        regression."""
        result = score_oasis([4, 0, 0, 0, 0])
        assert result.total == 4
        assert result.positive_screen is False

    def test_two_high_items_reach_cutoff(self) -> None:
        """Two items at max (4) on impairment (items 4-5), three zeros
        on symptom/avoidance → total = 8 → positive.  A patient with
        severe functional impairment but low self-reported symptom
        frequency still screens positive on OASIS — OASIS' headline
        clinical contribution over GAD-7 is that it catches this
        profile."""
        result = score_oasis([0, 0, 0, 4, 4])
        assert result.total == 8
        assert result.positive_screen is True


class TestItemCountValidation:
    """Exactly 5 items required."""

    def test_rejects_four_items(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 5 items"):
            score_oasis([2, 2, 2, 2])

    def test_rejects_six_items(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 5 items"):
            score_oasis([1, 1, 1, 1, 1, 1])

    def test_rejects_empty(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 5 items"):
            score_oasis([])

    def test_rejects_two_items_gad2_misroute(self) -> None:
        """A 2-item submission is almost certainly a mis-routed GAD-2
        or PHQ-2 — rejecting with the specific count makes the
        diagnostic path obvious rather than mysteriously returning
        a sub-cutoff total."""
        with pytest.raises(InvalidResponseError, match="exactly 5 items"):
            score_oasis([2, 2])

    def test_rejects_seven_items_gad7_misroute(self) -> None:
        """A 7-item submission is almost certainly a mis-routed GAD-7.
        The error message's ``exactly 5 items`` text makes the
        mis-routing obvious on first inspection of the log line."""
        with pytest.raises(InvalidResponseError, match="exactly 5 items"):
            score_oasis([1, 1, 1, 1, 1, 1, 1])


class TestItemRangeValidation:
    """Items must be in [0, 4] — a 5-point Likert."""

    @pytest.mark.parametrize("bad_value", [-1, 5, 6, 10, 100])
    def test_rejects_out_of_range(self, bad_value: int) -> None:
        with pytest.raises(InvalidResponseError, match="out of range"):
            score_oasis([0, 0, 0, 0, bad_value])

    def test_rejects_string_item(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_oasis([1, "1", 1, 1, 1])  # type: ignore[list-item]

    def test_rejects_float_item(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_oasis([1.5, 0, 0, 0, 0])  # type: ignore[list-item]

    def test_rejects_none_item(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_oasis([1, None, 1, 1, 1])  # type: ignore[list-item]


class TestBoolRejection:
    """Bool items are rejected — uniform with the rest of the
    psychometric package.  See scoring/oasis.py module docstring."""

    def test_rejects_true_item(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_oasis([True, 0, 0, 0, 0])  # type: ignore[list-item]

    def test_rejects_false_item(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_oasis([0, 0, 0, 0, False])  # type: ignore[list-item]

    def test_error_names_the_item_index(self) -> None:
        """Error message names the 1-indexed item number so a clinician
        matches the error against the OASIS paper's item list."""
        with pytest.raises(InvalidResponseError, match="OASIS item 3"):
            score_oasis([0, 0, True, 0, 0])  # type: ignore[list-item]


class TestResultShape:
    """OasisResult carries the fields the router needs."""

    def test_result_is_frozen(self) -> None:
        result = score_oasis([2, 2, 2, 1, 1])
        with pytest.raises(Exception):  # FrozenInstanceError subclass
            result.total = 99  # type: ignore[misc]

    def test_items_are_tuple(self) -> None:
        """Tuple (not list) so the result is hashable and can be pinned
        into an immutable repository record."""
        result = score_oasis([2, 2, 2, 1, 1])
        assert isinstance(result.items, tuple)
        assert result.items == (2, 2, 2, 1, 1)

    def test_result_echoes_instrument_version(self) -> None:
        result = score_oasis([2, 2, 2, 1, 1])
        assert result.instrument_version == INSTRUMENT_VERSION

    def test_no_requires_t3_field(self) -> None:
        """OASIS has no safety item (none of the 5 items probes
        suicidality).  The result dataclass deliberately omits
        ``requires_t3`` so downstream code cannot accidentally route a
        positive anxiety-impairment screen into a T3 crisis flow —
        which would be clinically wrong.  See module docstring."""
        result = score_oasis([4, 4, 4, 4, 4])
        assert not hasattr(result, "requires_t3")

    def test_no_severity_band_field(self) -> None:
        """Norman 2006 validates only the total; no severity bands
        exist.  The dataclass intentionally carries no ``severity``
        field so the router cannot mistakenly render a banded label
        for OASIS.  The wire envelope maps ``positive_screen`` →
        "positive_screen" / "negative_screen" at the dispatch layer."""
        result = score_oasis([4, 4, 4, 4, 4])
        assert not hasattr(result, "severity")

    def test_no_subscale_fields(self) -> None:
        """OASIS items cluster conceptually into symptom (1-2) /
        avoidance (3) / impairment (4-5), but Norman 2006 validates
        only a single-factor structure.  The result carries no
        subscale fields — any future subscale attempt requires a
        replacement paper validating the split."""
        result = score_oasis([4, 4, 4, 4, 4])
        assert not hasattr(result, "symptom_total")
        assert not hasattr(result, "avoidance_total")
        assert not hasattr(result, "impairment_total")
        assert not hasattr(result, "subscales")


class TestClinicalVignettes:
    """Named patterns a clinician would recognize — tests the scorer
    as-written against real-world presentations.
    """

    def test_high_symptom_low_impairment_at_cutoff(self) -> None:
        """Frequent severe anxiety (items 1, 2 = 3 each) with no
        avoidance or impairment (items 3-5 = 0-1) → total = 7.  Below
        cutoff on OASIS — the patient reports severe symptoms but
        hasn't yet developed the functional avoidance/impairment
        pattern that Campbell-Sills 2009's cutoff is tuned to catch.
        This is the GAD-7-positive / OASIS-negative profile — they
        complement, not duplicate."""
        result = score_oasis([3, 3, 0, 1, 0])
        assert result.total == 7
        assert result.positive_screen is False

    def test_avoidance_pattern_hits_cutoff(self) -> None:
        """Moderate symptoms (items 1, 2 = 2) + strong avoidance
        (item 3 = 3) + moderate impairment (items 4, 5 = 2 each)
        → total = 11.  Positive screen — the classic anxiety-with-
        avoidance presentation that OASIS is designed to catch, and
        a first-order relapse precursor on substance-use surfaces."""
        result = score_oasis([2, 2, 3, 2, 2])
        assert result.total == 11
        assert result.positive_screen is True

    def test_impairment_dominant_crosses_cutoff(self) -> None:
        """Low-frequency / low-intensity symptoms (items 1, 2 = 1
        each) but strong impairment (items 4, 5 = 3 each) and some
        avoidance (item 3 = 2) → total = 10.  Positive.  A patient
        whose anxiety is "functional" (low intensity, high cost) —
        OASIS catches this where GAD-7 might not."""
        result = score_oasis([1, 1, 2, 3, 3])
        assert result.total == 10
        assert result.positive_screen is True

    def test_all_severe_unambiguously_positive(self) -> None:
        """Every item at max (4) → total = 20.  Unambiguous positive
        screen — canonical severe-anxiety-with-impairment presentation
        on OASIS."""
        result = score_oasis([4, 4, 4, 4, 4])
        assert result.total == 20
        assert result.positive_screen is True

    def test_sub_threshold_worry_is_negative(self) -> None:
        """Low-frequency mild symptoms only (items 1, 2 = 1 each),
        no avoidance, no impairment → total = 2.  Clearly sub-clinical,
        does not warrant any anxiety follow-up.  Pins the low-end
        decision."""
        result = score_oasis([1, 1, 0, 0, 0])
        assert result.total == 2
        assert result.positive_screen is False


class TestNoSafetyRouting:
    """OASIS has no safety item.  The scorer must not expose anything
    that a downstream router could mistake for a T3 trigger.  The T3
    pathway is reserved for active suicidality per
    Docs/Whitepapers/04_Safety_Framework.md §T3 and is gated on
    PHQ-9 item 9 / C-SSRS — not on OASIS."""

    def test_max_total_has_no_safety_field(self) -> None:
        result = score_oasis([4, 4, 4, 4, 4])
        # No requires_t3, no t3_reason, no triggering_items — the
        # result is a pure total + positive-screen boolean.
        assert not hasattr(result, "requires_t3")
        assert not hasattr(result, "t3_reason")
        assert not hasattr(result, "triggering_items")

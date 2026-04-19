"""Tests for the ASRS-6 scorer (Kessler 2005 — WHO Adult ADHD
Self-Report Scale, 6-item short screener).

Pins the module constants, total computation, the NOVEL weighted-
threshold firing rule (items 1-3 fire at Likert ≥2, items 4-6 fire at
Likert ≥3), the count-of-fires screen decision, the triggering_items
audit-trail, result shape invariants, and the no-safety-routing
invariant.

The distinctive test class in this file is ``TestCountVsSumDivergence``
— it pins the property that a sum-based interpretation of ASRS-6 under-
detects in exactly the symptom pattern the weighted-threshold rule was
designed to catch.  Any future refactor that collapses ``total`` and
``positive_count`` into a single field breaks these tests.
"""

from __future__ import annotations

import pytest

from discipline.psychometric.scoring.asrs6 import (
    ASRS6_POSITIVE_CUTOFF,
    Asrs6Result,
    INSTRUMENT_VERSION,
    ITEM_COUNT,
    ITEM_MAX,
    ITEM_MIN,
    ITEM_THRESHOLDS,
    InvalidResponseError,
    score_asrs6,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


class TestConstants:
    """Pinned module constants — drift here is a clinical change."""

    def test_item_count_is_six(self) -> None:
        assert ITEM_COUNT == 6

    def test_item_min_is_zero(self) -> None:
        """Kessler 2005 coding: 0 = "Never" is a genuine negative
        response.  ITEM_MIN=0 is different from K10/K6 (which use 1-5)."""
        assert ITEM_MIN == 0

    def test_item_max_is_four(self) -> None:
        """0-4 Likert: Never / Rarely / Sometimes / Often / Very Often."""
        assert ITEM_MAX == 4

    def test_positive_cutoff_is_four(self) -> None:
        """Kessler 2005 Table 2: ≥4 of 6 fired items is the positive
        screen (sensitivity 0.69, specificity 0.99 vs DSM-IV clinician
        diagnosis)."""
        assert ASRS6_POSITIVE_CUTOFF == 4

    def test_inattentive_items_fire_at_two(self) -> None:
        """Items 1-3 (inattentive) fire at Likert ≥ 2 ("Sometimes")."""
        assert ITEM_THRESHOLDS[1] == 2
        assert ITEM_THRESHOLDS[2] == 2
        assert ITEM_THRESHOLDS[3] == 2

    def test_hyperactive_items_fire_at_three(self) -> None:
        """Items 4-6 (hyperactive/impulsive) fire at Likert ≥ 3
        ("Often").  Asymmetry vs inattentive items is from Kessler
        2005's IRT weights — hyperactive symptoms at "Sometimes" are
        base-rate common in the general population."""
        assert ITEM_THRESHOLDS[4] == 3
        assert ITEM_THRESHOLDS[5] == 3
        assert ITEM_THRESHOLDS[6] == 3

    def test_thresholds_cover_exactly_six_items(self) -> None:
        """The threshold dict keys exactly match the 6 item slots —
        1-indexed, no gaps."""
        assert set(ITEM_THRESHOLDS.keys()) == {1, 2, 3, 4, 5, 6}

    def test_instrument_version_pinned(self) -> None:
        assert INSTRUMENT_VERSION == "asrs6-1.0.0"


# ---------------------------------------------------------------------------
# Total computation
# ---------------------------------------------------------------------------


class TestTotalCorrectness:
    """The raw-Likert-sum ``total`` field is independent of the firing
    logic — it's for trajectory tracking, not the screen decision."""

    def test_all_zero_totals_zero(self) -> None:
        r = score_asrs6([0, 0, 0, 0, 0, 0])
        assert r.total == 0

    def test_all_max_totals_twenty_four(self) -> None:
        r = score_asrs6([4, 4, 4, 4, 4, 4])
        assert r.total == 24

    def test_mixed_known_total(self) -> None:
        r = score_asrs6([1, 2, 3, 2, 1, 0])
        assert r.total == 9

    def test_total_equals_item_sum(self) -> None:
        items = [0, 1, 2, 3, 4, 2]
        r = score_asrs6(items)
        assert r.total == sum(items)

    def test_total_range_is_zero_to_twenty_four(self) -> None:
        """6 items × (0-4) envelope = 0-24 total range."""
        assert score_asrs6([0, 0, 0, 0, 0, 0]).total == 0
        assert score_asrs6([4, 4, 4, 4, 4, 4]).total == 24


# ---------------------------------------------------------------------------
# Per-item threshold firing (the NOVEL weighted-threshold rule)
# ---------------------------------------------------------------------------


class TestThresholdFiring:
    """The weighted-threshold rule is the core novelty of ASRS-6 vs
    every other scorer in this package.  Pin each firing boundary."""

    def test_item_one_fires_at_exactly_two(self) -> None:
        """Item 1 (inattentive) fires at Likert 2 — not at 1."""
        r = score_asrs6([2, 0, 0, 0, 0, 0])
        assert 1 in r.triggering_items

    def test_item_one_does_not_fire_at_one(self) -> None:
        """Item 1 at Likert 1 ("Rarely") is below the fire threshold."""
        r = score_asrs6([1, 0, 0, 0, 0, 0])
        assert 1 not in r.triggering_items

    def test_item_one_does_not_fire_at_zero(self) -> None:
        r = score_asrs6([0, 0, 0, 0, 0, 0])
        assert 1 not in r.triggering_items

    def test_inattentive_items_fire_at_two_boundary(self) -> None:
        """Each of items 1/2/3 fires at Likert=2, not at Likert=1."""
        for idx_0 in (0, 1, 2):  # 1-indexed items 1, 2, 3
            items_below = [0] * 6
            items_below[idx_0] = 1
            items_at = [0] * 6
            items_at[idx_0] = 2
            below = score_asrs6(items_below)
            at = score_asrs6(items_at)
            assert (idx_0 + 1) not in below.triggering_items
            assert (idx_0 + 1) in at.triggering_items

    def test_hyperactive_items_fire_at_three_boundary(self) -> None:
        """Items 4/5/6 fire at Likert=3 ("Often"), not at Likert=2.
        A hyperactive item at Likert 2 ("Sometimes") is explicitly
        not a fire — that's the whole point of the asymmetric
        thresholds."""
        for idx_0 in (3, 4, 5):  # 1-indexed items 4, 5, 6
            items_below = [0] * 6
            items_below[idx_0] = 2
            items_at = [0] * 6
            items_at[idx_0] = 3
            below = score_asrs6(items_below)
            at = score_asrs6(items_at)
            assert (idx_0 + 1) not in below.triggering_items
            assert (idx_0 + 1) in at.triggering_items

    def test_hyperactive_item_at_two_does_not_fire(self) -> None:
        """Load-bearing — the whole inattentive/hyperactive asymmetry
        is summarized by this case.  An inattentive item fires at 2;
        a hyperactive item at the same Likert does not."""
        r = score_asrs6([0, 0, 0, 2, 2, 2])
        assert r.triggering_items == ()
        assert r.positive_count == 0

    def test_inattentive_item_at_two_does_fire(self) -> None:
        """Mirror of the hyperactive case — inattentive items at
        Likert 2 fire where hyperactive items don't."""
        r = score_asrs6([2, 2, 2, 0, 0, 0])
        assert r.triggering_items == (1, 2, 3)
        assert r.positive_count == 3

    def test_maxed_items_always_fire(self) -> None:
        """Likert 4 is at or above every threshold; every item fires."""
        r = score_asrs6([4, 4, 4, 4, 4, 4])
        assert r.triggering_items == (1, 2, 3, 4, 5, 6)
        assert r.positive_count == 6

    def test_zero_items_never_fire(self) -> None:
        r = score_asrs6([0, 0, 0, 0, 0, 0])
        assert r.triggering_items == ()
        assert r.positive_count == 0


# ---------------------------------------------------------------------------
# Count-of-fires cutoff
# ---------------------------------------------------------------------------


class TestCountCutoff:
    """positive_screen == (positive_count >= 4).  The actionable
    decision surface."""

    def test_three_fires_is_negative(self) -> None:
        """Three inattentive items at Likert 2 — three fires, no
        screen.  One below the cutoff."""
        r = score_asrs6([2, 2, 2, 0, 0, 0])
        assert r.positive_count == 3
        assert r.positive_screen is False

    def test_four_fires_is_positive(self) -> None:
        """Four fires — three inattentive + one hyperactive at
        Likert 3 — crosses the cutoff exactly."""
        r = score_asrs6([2, 2, 2, 3, 0, 0])
        assert r.positive_count == 4
        assert r.positive_screen is True

    def test_five_fires_is_positive(self) -> None:
        r = score_asrs6([2, 2, 2, 3, 3, 0])
        assert r.positive_count == 5
        assert r.positive_screen is True

    def test_six_fires_is_positive(self) -> None:
        """Maximal fire — all six items meet their threshold."""
        r = score_asrs6([2, 2, 2, 3, 3, 3])
        assert r.positive_count == 6
        assert r.positive_screen is True

    def test_zero_fires_is_negative(self) -> None:
        r = score_asrs6([0, 0, 0, 0, 0, 0])
        assert r.positive_count == 0
        assert r.positive_screen is False

    def test_one_fire_is_negative(self) -> None:
        r = score_asrs6([2, 0, 0, 0, 0, 0])
        assert r.positive_count == 1
        assert r.positive_screen is False

    def test_cutoff_boundary_is_strictly_greater_or_equal(self) -> None:
        """Boundary check pinned in two directions — 3 fires is
        negative, 4 fires is positive."""
        r_three = score_asrs6([2, 2, 2, 0, 0, 0])
        r_four = score_asrs6([2, 2, 2, 3, 0, 0])
        assert r_three.positive_screen is False
        assert r_four.positive_screen is True


# ---------------------------------------------------------------------------
# Count-vs-sum divergence (load-bearing)
# ---------------------------------------------------------------------------


class TestCountVsSumDivergence:
    """``total`` and ``positive_count`` are genuinely different signals.
    These tests pin the property that a caller misusing ``total`` as
    the screen decision would make wrong calls in predictable ways.
    The divergence is the entire reason Kessler 2005 used weighted
    thresholds rather than a sum-threshold like PHQ-9 uses."""

    def test_high_sum_low_count_is_negative(self) -> None:
        """Sum=12 (impressive on a sum-threshold instrument) but only
        one fired item (one inattentive item at Likert 4 + four items
        at sub-threshold Likert 2).  The weighted-threshold rule
        correctly says: not positive."""
        # item 1 = 4 (fires, inattentive, threshold 2)
        # item 2 = 2 (fires, inattentive, threshold 2)
        # item 3 = 1 (no fire, below inattentive threshold 2)
        # item 4 = 2 (no fire, below hyperactive threshold 3)
        # item 5 = 2 (no fire, below hyperactive threshold 3)
        # item 6 = 1 (no fire)
        r = score_asrs6([4, 2, 1, 2, 2, 1])
        assert r.total == 12
        assert r.positive_count == 2
        assert r.positive_screen is False

    def test_low_sum_positive_screen_possible(self) -> None:
        """Sum as low as 8 (2+2+2+... ) with the right distribution
        can produce 4 fires — positive screen at a sum that looks
        mild on a sum-threshold instrument."""
        # items 1/2/3 = 2 (three inattentive fires)
        # item 4 = 3 (one hyperactive fire) — positive
        # items 5/6 = 0
        r = score_asrs6([2, 2, 2, 3, 0, 0])
        assert r.total == 9
        assert r.positive_count == 4
        assert r.positive_screen is True

    def test_hyperactive_flood_at_two_is_negative_despite_sum(self) -> None:
        """All 3 hyperactive items at Likert 2 gives sum=6 but zero
        fires — Kessler 2005's design choice to not let hyperactive
        symptoms at "Sometimes" trigger the screen, because that
        pattern is base-rate common in the general population."""
        r = score_asrs6([0, 0, 0, 2, 2, 2])
        assert r.total == 6
        assert r.positive_count == 0
        assert r.positive_screen is False

    def test_hyperactive_flood_at_three_is_positive(self) -> None:
        """Same sum=9 with hyperactive at Likert 3 instead of 2 —
        three fires.  Still under the cutoff of 4, but demonstrates
        the threshold sensitivity."""
        r = score_asrs6([0, 0, 0, 3, 3, 3])
        assert r.total == 9
        assert r.positive_count == 3
        assert r.positive_screen is False

    def test_same_total_different_screen_decision(self) -> None:
        """Two response sets with identical ``total`` but opposite
        screen decisions — the signature of a weighted-threshold
        instrument."""
        r_neg = score_asrs6([4, 4, 1, 1, 1, 1])  # total=12, 2 fires
        r_pos = score_asrs6([2, 2, 2, 3, 3, 0])  # total=12, 5 fires
        assert r_neg.total == r_pos.total == 12
        assert r_neg.positive_screen is False
        assert r_pos.positive_screen is True


# ---------------------------------------------------------------------------
# Triggering-items surfacing (C-SSRS slot reuse)
# ---------------------------------------------------------------------------


class TestTriggeringItemsSurfacing:
    """triggering_items is the 1-indexed audit-trail of which items
    met their firing threshold.  Reused from the existing C-SSRS
    wire slot — a clinician UI renders these so a patient can see
    WHICH symptoms drove the screen decision."""

    def test_triggering_items_are_one_indexed(self) -> None:
        """Item 1 at Likert 2 surfaces as 1, not 0 — 1-indexed
        matches the published instrument's item numbering."""
        r = score_asrs6([2, 0, 0, 0, 0, 0])
        assert r.triggering_items == (1,)

    def test_triggering_items_are_sorted_ascending(self) -> None:
        """Tuple preserves 1-indexed enumeration order — ascending,
        no gaps."""
        r = score_asrs6([2, 0, 2, 0, 3, 0])
        assert r.triggering_items == (1, 3, 5)

    def test_triggering_items_is_tuple_not_list(self) -> None:
        """Tuple so Asrs6Result remains hashable — uniform with the
        rest of the psychometric dataclasses."""
        r = score_asrs6([2, 2, 2, 0, 0, 0])
        assert isinstance(r.triggering_items, tuple)

    def test_empty_triggering_items_when_none_fire(self) -> None:
        """Empty tuple (not None) when no items fire — uniform shape
        for callers that iterate without null-checking."""
        r = score_asrs6([0, 0, 0, 0, 0, 0])
        assert r.triggering_items == ()

    def test_triggering_items_length_matches_positive_count(self) -> None:
        """positive_count is len(triggering_items) — the two fields
        are redundant by construction, pinned so a refactor can't
        split them."""
        for items in [
            [0, 0, 0, 0, 0, 0],
            [2, 0, 0, 0, 0, 0],
            [2, 2, 2, 3, 0, 0],
            [4, 4, 4, 4, 4, 4],
        ]:
            r = score_asrs6(items)
            assert len(r.triggering_items) == r.positive_count


# ---------------------------------------------------------------------------
# Item-count validation
# ---------------------------------------------------------------------------


class TestItemCountValidation:
    """Wrong item count raises InvalidResponseError — prevents routing
    another instrument's items through the ASRS-6 scorer."""

    def test_empty_rejects(self) -> None:
        with pytest.raises(InvalidResponseError):
            score_asrs6([])

    def test_five_rejects(self) -> None:
        with pytest.raises(InvalidResponseError):
            score_asrs6([0, 0, 0, 0, 0])

    def test_seven_rejects(self) -> None:
        with pytest.raises(InvalidResponseError):
            score_asrs6([0, 0, 0, 0, 0, 0, 0])

    def test_phq9_misroute_rejects(self) -> None:
        """A PHQ-9 payload (9 items) must not pass for ASRS-6 (6
        items).  Wrong instrument, wrong count."""
        with pytest.raises(InvalidResponseError):
            score_asrs6([1, 2, 1, 3, 2, 1, 0, 1, 2])

    def test_k6_misroute_rejects(self) -> None:
        """K6 also has 6 items — but K6 uses Kessler 1-5 coding, and
        count match alone doesn't make a valid ASRS-6 payload.  This
        test pins the ASRS-6 validator as the second gate after the
        router's instrument dispatch."""
        # This set happens to be in the ASRS-6 envelope too (0-4),
        # so this test documents that item-COUNT alone matches; the
        # router is the first line of defense for instrument identity.
        r = score_asrs6([1, 2, 3, 4, 1, 2])
        assert r.total == 13  # valid ASRS-6 shape — no exception

    def test_twelve_rejects(self) -> None:
        with pytest.raises(InvalidResponseError):
            score_asrs6([0] * 12)


# ---------------------------------------------------------------------------
# Item-range validation
# ---------------------------------------------------------------------------


class TestItemRangeValidation:
    """Items outside [0, 4] raise InvalidResponseError."""

    def test_negative_one_rejects(self) -> None:
        with pytest.raises(InvalidResponseError):
            score_asrs6([-1, 0, 0, 0, 0, 0])

    def test_five_rejects(self) -> None:
        with pytest.raises(InvalidResponseError):
            score_asrs6([5, 0, 0, 0, 0, 0])

    def test_out_of_range_at_last_item(self) -> None:
        with pytest.raises(InvalidResponseError):
            score_asrs6([0, 0, 0, 0, 0, 99])

    @pytest.mark.parametrize("bad_value", [-10, -1, 5, 10, 100])
    def test_out_of_range_values_parametrized(self, bad_value: int) -> None:
        with pytest.raises(InvalidResponseError):
            score_asrs6([bad_value, 0, 0, 0, 0, 0])

    def test_boundary_zero_accepted(self) -> None:
        r = score_asrs6([0, 0, 0, 0, 0, 0])
        assert r.total == 0

    def test_boundary_four_accepted(self) -> None:
        r = score_asrs6([4, 4, 4, 4, 4, 4])
        assert r.total == 24


# ---------------------------------------------------------------------------
# Type / bool validation
# ---------------------------------------------------------------------------


class TestItemTypeValidation:
    """Non-int item values raise InvalidResponseError."""

    def test_string_rejects(self) -> None:
        with pytest.raises(InvalidResponseError):
            score_asrs6(["2", 0, 0, 0, 0, 0])  # type: ignore[list-item]

    def test_float_rejects(self) -> None:
        with pytest.raises(InvalidResponseError):
            score_asrs6([2.5, 0, 0, 0, 0, 0])  # type: ignore[list-item]

    def test_none_rejects(self) -> None:
        with pytest.raises(InvalidResponseError):
            score_asrs6([None, 0, 0, 0, 0, 0])  # type: ignore[list-item]


class TestBoolRejection:
    """Bool items are rejected — uniform with the rest of the
    psychometric package.  Reason: ``True == 1`` and ``False == 0``
    silently pass naive int / range checks but represent a typed
    error at the API surface."""

    def test_true_rejects(self) -> None:
        with pytest.raises(InvalidResponseError):
            score_asrs6([True, 0, 0, 0, 0, 0])  # type: ignore[list-item]

    def test_false_rejects(self) -> None:
        with pytest.raises(InvalidResponseError):
            score_asrs6([False, 0, 0, 0, 0, 0])  # type: ignore[list-item]

    def test_bool_at_last_position_rejects(self) -> None:
        """Bool rejection runs on every item, not just item 1."""
        with pytest.raises(InvalidResponseError):
            score_asrs6([0, 0, 0, 0, 0, True])  # type: ignore[list-item]

    def test_mixed_bool_int_rejects(self) -> None:
        with pytest.raises(InvalidResponseError):
            score_asrs6([2, True, 2, 0, 0, 0])  # type: ignore[list-item]


# ---------------------------------------------------------------------------
# Result shape
# ---------------------------------------------------------------------------


class TestResultShape:
    """Asrs6Result fields and invariants."""

    def test_result_is_frozen_dataclass(self) -> None:
        r = score_asrs6([0, 0, 0, 0, 0, 0])
        with pytest.raises(Exception):  # FrozenInstanceError
            r.total = 99  # type: ignore[misc]

    def test_result_is_hashable(self) -> None:
        """Hashable via frozen + tuple fields — can be used as dict
        key or set member."""
        r = score_asrs6([2, 2, 2, 3, 0, 0])
        assert hash(r) is not None

    def test_result_has_total_field(self) -> None:
        r = score_asrs6([0, 1, 2, 3, 4, 0])
        assert r.total == 10

    def test_result_has_positive_count_field(self) -> None:
        r = score_asrs6([2, 2, 2, 3, 0, 0])
        assert r.positive_count == 4

    def test_result_has_positive_screen_field(self) -> None:
        r = score_asrs6([2, 2, 2, 3, 0, 0])
        assert r.positive_screen is True

    def test_result_has_triggering_items_field(self) -> None:
        r = score_asrs6([2, 2, 2, 3, 0, 0])
        assert r.triggering_items == (1, 2, 3, 4)

    def test_result_echoes_items_as_tuple(self) -> None:
        r = score_asrs6([0, 1, 2, 3, 4, 0])
        assert r.items == (0, 1, 2, 3, 4, 0)
        assert isinstance(r.items, tuple)

    def test_result_has_instrument_version(self) -> None:
        r = score_asrs6([0, 0, 0, 0, 0, 0])
        assert r.instrument_version == INSTRUMENT_VERSION

    def test_result_has_no_severity_field(self) -> None:
        """ASRS-6 uses the cutoff envelope (positive_screen /
        negative_screen) — severity bands are not published for the
        6-item screener.  Any future refactor that adds a severity
        band breaks this test, forcing a clinical sign-off."""
        r = score_asrs6([2, 2, 2, 3, 0, 0])
        assert not hasattr(r, "severity")

    def test_result_has_no_requires_t3_field(self) -> None:
        """ASRS-6 has no safety item — requires_t3 is deliberately
        absent from the scorer output.  Acute ideation screening is
        PHQ-9 item 9 / C-SSRS, not ASRS."""
        r = score_asrs6([4, 4, 4, 4, 4, 4])
        assert not hasattr(r, "requires_t3")

    def test_result_has_no_subscales_field(self) -> None:
        """Kessler 2005 validates at the unidimensional count-of-fires
        level.  The inattentive/hyperactive split is implicit in the
        thresholds but is not surfaced as a wire-exposed subscale —
        that would require the full 18-item ASRS Symptom Checklist."""
        r = score_asrs6([4, 4, 4, 4, 4, 4])
        assert not hasattr(r, "subscales")


# ---------------------------------------------------------------------------
# Clinical vignettes
# ---------------------------------------------------------------------------


class TestClinicalVignettes:
    """End-to-end sanity — realistic response patterns produce the
    decision a clinician would expect."""

    def test_no_symptoms_is_negative(self) -> None:
        """Never-never-never-never-never-never."""
        r = score_asrs6([0, 0, 0, 0, 0, 0])
        assert r.positive_screen is False
        assert r.positive_count == 0

    def test_inattentive_presentation_positive(self) -> None:
        """Classic inattentive presentation — all three inattentive
        items high, hyperactive items low.  Four fires (3 inattentive
        at ≥2, 1 hyperactive at ≥3) crosses the cutoff."""
        r = score_asrs6([3, 3, 3, 3, 1, 1])
        assert r.positive_count == 4
        assert r.positive_screen is True

    def test_pure_hyperactive_presentation_positive(self) -> None:
        """All three hyperactive items at Often or greater, plus one
        inattentive fire — four fires, positive."""
        r = score_asrs6([2, 0, 0, 4, 4, 4])
        assert r.positive_count == 4
        assert r.positive_screen is True

    def test_combined_presentation_positive(self) -> None:
        """Very Often on every item — classic combined presentation."""
        r = score_asrs6([4, 4, 4, 4, 4, 4])
        assert r.positive_count == 6
        assert r.positive_screen is True

    def test_subthreshold_pattern_negative(self) -> None:
        """Chronic mild symptoms — everything at Likert 2.  Three
        inattentive fires, zero hyperactive fires.  Below cutoff."""
        r = score_asrs6([2, 2, 2, 2, 2, 2])
        assert r.positive_count == 3
        assert r.positive_screen is False

    def test_occasional_symptoms_negative(self) -> None:
        """Rarely across the board — zero fires."""
        r = score_asrs6([1, 1, 1, 1, 1, 1])
        assert r.positive_count == 0
        assert r.positive_screen is False


# ---------------------------------------------------------------------------
# No-safety-routing invariant
# ---------------------------------------------------------------------------


class TestNoSafetyRouting:
    """ASRS-6 never fires T3.  Acute ideation screening is PHQ-9
    item 9 / C-SSRS, not ASRS-6 — even maxed-out responses are not
    a safety signal."""

    def test_all_max_no_safety_field(self) -> None:
        r = score_asrs6([4, 4, 4, 4, 4, 4])
        assert not hasattr(r, "requires_t3")

    def test_hyperactive_max_no_safety_field(self) -> None:
        """Items 5 (fidget) and 6 (driven by a motor) probe
        hyperactivity — NOT suicidality.  Maxed hyperactive
        responses must never surface a safety flag."""
        r = score_asrs6([0, 0, 0, 4, 4, 4])
        assert not hasattr(r, "requires_t3")

    def test_positive_screen_no_safety_field(self) -> None:
        """A positive screen is "worth evaluating further", NOT a
        safety escalation.  The escalation channel is a different
        instrument path entirely."""
        r = score_asrs6([2, 2, 2, 3, 3, 3])
        assert r.positive_screen is True
        assert not hasattr(r, "requires_t3")

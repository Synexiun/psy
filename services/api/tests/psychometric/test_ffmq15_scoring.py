"""Tests for FFMQ-15 scoring — Baer 2006 / Gu 2016 five-facet mindfulness."""

from __future__ import annotations

import pytest

from discipline.psychometric.scoring.ffmq15 import (
    FFMQ15_ACTING_POSITIONS,
    FFMQ15_DESCRIBING_POSITIONS,
    FFMQ15_NONJUDGING_POSITIONS,
    FFMQ15_NONREACTIVITY_POSITIONS,
    FFMQ15_OBSERVING_POSITIONS,
    FFMQ15_REVERSE_ITEMS,
    FFMQ15_SUBSCALES,
    INSTRUMENT_VERSION,
    ITEM_COUNT,
    ITEM_MAX,
    ITEM_MIN,
    Ffmq15Result,
    InvalidResponseError,
    score_ffmq15,
)

# ---------------------------------------------------------------------------
# Module constants — pin the published factor structure
# ---------------------------------------------------------------------------


class TestFfmq15ModuleConstants:
    def test_instrument_version(self) -> None:
        assert INSTRUMENT_VERSION == "ffmq15-1.0.0"

    def test_item_count_is_15(self) -> None:
        """Gu 2016 IRT derivation: 15 items — 3 per facet × 5 facets."""
        assert ITEM_COUNT == 15

    def test_item_range_is_1_to_5(self) -> None:
        """Baer 2006 Likert: 1 = 'never or very rarely true',
        5 = 'very often or always true'.  Not 0-4, not 1-7."""
        assert ITEM_MIN == 1
        assert ITEM_MAX == 5

    def test_five_facets_defined(self) -> None:
        """Baer 2006 / Gu 2016 factor structure — exactly five
        facets.  Changing this count invalidates the instrument."""
        assert len(FFMQ15_SUBSCALES) == 5
        assert FFMQ15_SUBSCALES == (
            "observing",
            "describing",
            "acting_with_awareness",
            "non_judging",
            "non_reactivity",
        )

    def test_each_facet_has_three_items(self) -> None:
        """Gu 2016 short form: 3 items per facet."""
        assert len(FFMQ15_OBSERVING_POSITIONS) == 3
        assert len(FFMQ15_DESCRIBING_POSITIONS) == 3
        assert len(FFMQ15_ACTING_POSITIONS) == 3
        assert len(FFMQ15_NONJUDGING_POSITIONS) == 3
        assert len(FFMQ15_NONREACTIVITY_POSITIONS) == 3

    def test_facet_positions_are_contiguous(self) -> None:
        """Bohlmeijer 2011 administration order: facets are
        contiguous — items 1-3, 4-6, 7-9, 10-12, 13-15."""
        assert FFMQ15_OBSERVING_POSITIONS == (1, 2, 3)
        assert FFMQ15_DESCRIBING_POSITIONS == (4, 5, 6)
        assert FFMQ15_ACTING_POSITIONS == (7, 8, 9)
        assert FFMQ15_NONJUDGING_POSITIONS == (10, 11, 12)
        assert FFMQ15_NONREACTIVITY_POSITIONS == (13, 14, 15)

    def test_facet_positions_partition_all_15_items(self) -> None:
        """Every position 1-15 belongs to exactly one facet."""
        all_positions = (
            FFMQ15_OBSERVING_POSITIONS
            + FFMQ15_DESCRIBING_POSITIONS
            + FFMQ15_ACTING_POSITIONS
            + FFMQ15_NONJUDGING_POSITIONS
            + FFMQ15_NONREACTIVITY_POSITIONS
        )
        assert sorted(all_positions) == list(range(1, 16))
        assert len(set(all_positions)) == 15

    def test_reverse_items_are_7_positions(self) -> None:
        """Baer 2006: 1 reverse in describing (pos 6), 3 in
        acting (7-9), 3 in non-judging (10-12) = 7 reverse."""
        assert FFMQ15_REVERSE_ITEMS == (6, 7, 8, 9, 10, 11, 12)
        assert len(FFMQ15_REVERSE_ITEMS) == 7

    def test_observing_has_no_reverse_items(self) -> None:
        """Baer 2006 §3.1: observing items are all positively
        worded ("I notice the smells and aromas of things", etc.)."""
        for pos in FFMQ15_OBSERVING_POSITIONS:
            assert pos not in FFMQ15_REVERSE_ITEMS

    def test_nonreactivity_has_no_reverse_items(self) -> None:
        """Baer 2006 §3.5: non-reactivity items are all
        positively worded ("I perceive my feelings and emotions
        without having to react to them", etc.)."""
        for pos in FFMQ15_NONREACTIVITY_POSITIONS:
            assert pos not in FFMQ15_REVERSE_ITEMS

    def test_acting_is_entirely_reverse(self) -> None:
        """Bohlmeijer 2011 §3.2: acting-with-awareness items are
        phrased as automatic-pilot failures — every item is
        reverse-keyed."""
        for pos in FFMQ15_ACTING_POSITIONS:
            assert pos in FFMQ15_REVERSE_ITEMS

    def test_nonjudging_is_entirely_reverse(self) -> None:
        """Baer 2006 §3.4: non-judging items are phrased as
        judgmental thoughts ("I criticize myself...") — every
        item is reverse-keyed."""
        for pos in FFMQ15_NONJUDGING_POSITIONS:
            assert pos in FFMQ15_REVERSE_ITEMS

    def test_describing_has_exactly_one_reverse(self) -> None:
        """Baer 2006 describing: items 4, 5 positive, item 6
        reverse ("It's hard for me to find the words to describe
        what I'm thinking")."""
        reverse_in_des = [
            p
            for p in FFMQ15_DESCRIBING_POSITIONS
            if p in FFMQ15_REVERSE_ITEMS
        ]
        assert reverse_in_des == [6]


# ---------------------------------------------------------------------------
# Extreme response patterns — pin the scoring floor / ceiling
# ---------------------------------------------------------------------------


class TestFfmq15Extremes:
    def test_maximum_mindfulness_total_75(self) -> None:
        """Maximum mindfulness: raw=[5,5,5,5,5,1,1,1,1,1,1,1,5,5,5].
        Every positive item at max, every reverse item at min.
        Post-flip all 5s -> total 75, every facet = 15."""
        result = score_ffmq15([5, 5, 5, 5, 5, 1, 1, 1, 1, 1, 1, 1, 5, 5, 5])
        assert result.total == 75
        assert result.observing_sum == 15
        assert result.describing_sum == 15
        assert result.acting_sum == 15
        assert result.nonjudging_sum == 15
        assert result.nonreactivity_sum == 15
        assert result.severity == "continuous"

    def test_minimum_mindfulness_total_15(self) -> None:
        """Minimum mindfulness: raw=[1,1,1,1,1,5,5,5,5,5,5,5,1,1,1].
        Every positive item at min, every reverse item at max.
        Post-flip all 1s -> total 15, every facet = 3."""
        result = score_ffmq15([1, 1, 1, 1, 1, 5, 5, 5, 5, 5, 5, 5, 1, 1, 1])
        assert result.total == 15
        assert result.observing_sum == 3
        assert result.describing_sum == 3
        assert result.acting_sum == 3
        assert result.nonjudging_sum == 3
        assert result.nonreactivity_sum == 3

    def test_midpoint_all_raw_3(self) -> None:
        """Raw all-3s: every post-flip item is also 3 (since
        6 - 3 = 3).  Grand total 45, every facet 9.  Midpoint
        is the only response pattern where raw == post-flip
        for every position."""
        result = score_ffmq15([3] * 15)
        assert result.total == 45
        assert result.observing_sum == 9
        assert result.describing_sum == 9
        assert result.acting_sum == 9
        assert result.nonjudging_sum == 9
        assert result.nonreactivity_sum == 9

    def test_acquiescence_all_raw_1_yields_43(self) -> None:
        """All raw 1: 8 positive × 1 + 7 reverse × (6-1=5) = 8+35 = 43.
        Per-facet: Obs=3 (all positive), Des=1+1+5=7, Act=5+5+5=15,
        NJ=5+5+5=15, NR=3.  The Marsh 1996 acquiescence signature
        for an asymmetric 8/7 positive/reverse split."""
        result = score_ffmq15([1] * 15)
        assert result.total == 43
        assert result.observing_sum == 3
        assert result.describing_sum == 7
        assert result.acting_sum == 15
        assert result.nonjudging_sum == 15
        assert result.nonreactivity_sum == 3

    def test_acquiescence_all_raw_5_yields_47(self) -> None:
        """All raw 5: 8 positive × 5 + 7 reverse × (6-5=1) = 40+7 = 47.
        Per-facet: Obs=15, Des=5+5+1=11, Act=1+1+1=3, NJ=1+1+1=3,
        NR=15.  The MIRROR of the all-1s acquiescence signature;
        together these pin the asymmetric-split boundary."""
        result = score_ffmq15([5] * 15)
        assert result.total == 47
        assert result.observing_sum == 15
        assert result.describing_sum == 11
        assert result.acting_sum == 3
        assert result.nonjudging_sum == 3
        assert result.nonreactivity_sum == 15

    def test_acquiescence_extremes_differ_by_four(self) -> None:
        """The all-1s and all-5s totals must differ by exactly 4
        (the asymmetry of 8 positive vs 7 reverse items).  If this
        drifts, the reverse-item count has changed from 7 and the
        instrument no longer matches Baer 2006."""
        low = score_ffmq15([1] * 15).total
        high = score_ffmq15([5] * 15).total
        assert high - low == 4


# ---------------------------------------------------------------------------
# Per-facet reverse-keying — pin the flip at each position
# ---------------------------------------------------------------------------


class TestFfmq15ReverseKeying:
    @pytest.mark.parametrize(
        "position_1,raw,expected_post_flip",
        [
            # Non-reverse positions — raw passes through unchanged
            (1, 1, 1), (1, 2, 2), (1, 3, 3), (1, 4, 4), (1, 5, 5),
            (2, 1, 1), (2, 5, 5),
            (3, 3, 3),
            (4, 1, 1), (4, 5, 5),
            (5, 2, 2), (5, 4, 4),
            (13, 1, 1), (13, 5, 5),
            (14, 3, 3),
            (15, 2, 2), (15, 4, 4),
            # Reverse positions — (6 - raw)
            (6, 1, 5), (6, 2, 4), (6, 3, 3), (6, 4, 2), (6, 5, 1),
            (7, 1, 5), (7, 5, 1),
            (8, 2, 4), (8, 4, 2),
            (9, 3, 3),
            (10, 1, 5), (10, 5, 1),
            (11, 2, 4), (11, 4, 2),
            (12, 3, 3),
        ],
    )
    def test_per_position_post_flip_value(
        self, position_1: int, raw: int, expected_post_flip: int
    ) -> None:
        """For each (position, raw-value) pair, pin the post-flip
        value by isolating the position: set every OTHER item to
        the neutral midpoint 3 (which is fixed-point under flip),
        set this position to raw, score, and subtract the neutral
        contribution from the facet sum to recover the per-
        position post-flip."""
        items = [3] * 15
        items[position_1 - 1] = raw
        result = score_ffmq15(items)

        # Recover this position's post-flip contribution from the
        # facet sum.  Every other position contributed 3.
        facet_positions = _facet_for_position(position_1)
        facet_sum = _get_facet_sum(result, position_1)
        this_position_contribution = facet_sum - 3 * (
            len(facet_positions) - 1
        )
        assert this_position_contribution == expected_post_flip

    def test_raising_position_1_raises_total(self) -> None:
        """Position 1 is observing (positive).  Raising from 3
        to 5 adds 2 to the total and to the observing facet."""
        base = score_ffmq15([3] * 15)
        raised = score_ffmq15([5, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3])
        assert raised.total == base.total + 2
        assert raised.observing_sum == base.observing_sum + 2

    def test_raising_position_6_lowers_total(self) -> None:
        """Position 6 is describing (reverse-keyed).  Raising
        from 3 to 5 LOWERS the total by 2 (post-flip 3 -> 1)."""
        base = score_ffmq15([3] * 15)
        raised = score_ffmq15([3, 3, 3, 3, 3, 5, 3, 3, 3, 3, 3, 3, 3, 3, 3])
        assert raised.total == base.total - 2
        assert raised.describing_sum == base.describing_sum - 2

    def test_raising_position_7_lowers_total(self) -> None:
        """Position 7 is acting-with-awareness (reverse-keyed —
        'I rush through activities...')."""
        base = score_ffmq15([3] * 15)
        raised = score_ffmq15([3, 3, 3, 3, 3, 3, 5, 3, 3, 3, 3, 3, 3, 3, 3])
        assert raised.total == base.total - 2
        assert raised.acting_sum == base.acting_sum - 2

    def test_raising_position_10_lowers_total(self) -> None:
        """Position 10 is non-judging (reverse-keyed — 'I
        criticize myself...')."""
        base = score_ffmq15([3] * 15)
        raised = score_ffmq15([3, 3, 3, 3, 3, 3, 3, 3, 3, 5, 3, 3, 3, 3, 3])
        assert raised.total == base.total - 2
        assert raised.nonjudging_sum == base.nonjudging_sum - 2

    def test_raising_position_13_raises_total(self) -> None:
        """Position 13 is non-reactivity (positive)."""
        base = score_ffmq15([3] * 15)
        raised = score_ffmq15([3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 5, 3, 3])
        assert raised.total == base.total + 2
        assert raised.nonreactivity_sum == base.nonreactivity_sum + 2


# ---------------------------------------------------------------------------
# Facet independence — changing one facet doesn't affect others
# ---------------------------------------------------------------------------


class TestFfmq15FacetIndependence:
    def test_observing_changes_dont_affect_other_facets(self) -> None:
        """The five-facet structure requires that perturbing
        observing items leaves the other four facet sums
        unchanged."""
        base = score_ffmq15([3] * 15)
        # Raise every observing item to 5
        items = list([3] * 15)
        for pos in FFMQ15_OBSERVING_POSITIONS:
            items[pos - 1] = 5
        perturbed = score_ffmq15(items)
        assert perturbed.observing_sum == 15
        assert perturbed.describing_sum == base.describing_sum
        assert perturbed.acting_sum == base.acting_sum
        assert perturbed.nonjudging_sum == base.nonjudging_sum
        assert perturbed.nonreactivity_sum == base.nonreactivity_sum

    def test_describing_changes_dont_affect_other_facets(self) -> None:
        base = score_ffmq15([3] * 15)
        items = list([3] * 15)
        for pos in FFMQ15_DESCRIBING_POSITIONS:
            items[pos - 1] = 5
        perturbed = score_ffmq15(items)
        assert perturbed.observing_sum == base.observing_sum
        assert perturbed.acting_sum == base.acting_sum
        assert perturbed.nonjudging_sum == base.nonjudging_sum
        assert perturbed.nonreactivity_sum == base.nonreactivity_sum

    def test_acting_changes_dont_affect_other_facets(self) -> None:
        base = score_ffmq15([3] * 15)
        items = list([3] * 15)
        for pos in FFMQ15_ACTING_POSITIONS:
            items[pos - 1] = 5
        perturbed = score_ffmq15(items)
        # Raising reverse-keyed items to 5 LOWERS the facet — acting
        # sum goes from 9 to 3.
        assert perturbed.acting_sum == 3
        assert perturbed.observing_sum == base.observing_sum
        assert perturbed.describing_sum == base.describing_sum
        assert perturbed.nonjudging_sum == base.nonjudging_sum
        assert perturbed.nonreactivity_sum == base.nonreactivity_sum

    def test_nonjudging_changes_dont_affect_other_facets(self) -> None:
        base = score_ffmq15([3] * 15)
        items = list([3] * 15)
        for pos in FFMQ15_NONJUDGING_POSITIONS:
            items[pos - 1] = 5
        perturbed = score_ffmq15(items)
        assert perturbed.nonjudging_sum == 3
        assert perturbed.observing_sum == base.observing_sum
        assert perturbed.describing_sum == base.describing_sum
        assert perturbed.acting_sum == base.acting_sum
        assert perturbed.nonreactivity_sum == base.nonreactivity_sum

    def test_nonreactivity_changes_dont_affect_other_facets(self) -> None:
        base = score_ffmq15([3] * 15)
        items = list([3] * 15)
        for pos in FFMQ15_NONREACTIVITY_POSITIONS:
            items[pos - 1] = 5
        perturbed = score_ffmq15(items)
        assert perturbed.nonreactivity_sum == 15
        assert perturbed.observing_sum == base.observing_sum
        assert perturbed.describing_sum == base.describing_sum
        assert perturbed.acting_sum == base.acting_sum
        assert perturbed.nonjudging_sum == base.nonjudging_sum

    def test_total_equals_sum_of_five_subscales(self) -> None:
        """Invariant: grand total = sum of the five facet sums."""
        for raw in (
            [1, 2, 3, 4, 5, 1, 2, 3, 4, 5, 1, 2, 3, 4, 5],
            [5, 4, 3, 2, 1, 5, 4, 3, 2, 1, 5, 4, 3, 2, 1],
            [3] * 15,
            [1] * 15,
            [5] * 15,
        ):
            r = score_ffmq15(raw)
            assert r.total == (
                r.observing_sum
                + r.describing_sum
                + r.acting_sum
                + r.nonjudging_sum
                + r.nonreactivity_sum
            )


# ---------------------------------------------------------------------------
# Audit preservation — raw items preserved pre-flip
# ---------------------------------------------------------------------------


class TestFfmq15AuditInvariance:
    def test_items_preserves_raw_pre_flip(self) -> None:
        """Platform convention (TAS-20 / PSWQ / LOT-R / BRS /
        PANAS-10 / RSES): the ``items`` field stores RAW pre-flip
        responses for audit and FHIR R4 export.  Post-flip values
        live only in the subscale sums and total."""
        raw = [1, 2, 3, 4, 5, 1, 2, 3, 4, 5, 1, 2, 3, 4, 5]
        result = score_ffmq15(raw)
        assert result.items == tuple(raw)
        # Post-flip would differ at the reverse positions
        assert result.items != (1, 2, 3, 4, 5, 5, 4, 3, 2, 1, 5, 4, 3, 4, 5)

    def test_items_preserves_raw_at_reverse_positions(self) -> None:
        """Specifically verify that a raw 5 at a reverse position
        is stored as 5, not as 1 (the post-flip value)."""
        raw = [3, 3, 3, 3, 3, 5, 5, 5, 5, 5, 5, 5, 3, 3, 3]
        result = score_ffmq15(raw)
        # Raw 5 at reverse positions must be stored raw.
        for pos in FFMQ15_REVERSE_ITEMS:
            assert result.items[pos - 1] == 5
        # But the facets containing those reverse positions
        # reflect the post-flip (each 5 -> 1, so facet = 3).
        assert result.describing_sum == 3 + 3 + 1  # 7
        assert result.acting_sum == 1 + 1 + 1  # 3
        assert result.nonjudging_sum == 1 + 1 + 1  # 3

    def test_items_is_a_tuple_not_list(self) -> None:
        """Result is a frozen dataclass; items must be an
        immutable tuple to preserve hashability."""
        result = score_ffmq15([3] * 15)
        assert isinstance(result.items, tuple)

    def test_result_is_frozen(self) -> None:
        """Ffmq15Result must be frozen — no mutation post-score."""
        result = score_ffmq15([3] * 15)
        with pytest.raises((AttributeError, Exception)):
            result.total = 0  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Clinical vignettes
# ---------------------------------------------------------------------------


class TestFfmq15ClinicalVignettes:
    def test_flourishing_mindfulness_profile(self) -> None:
        """Flourishing: every facet at ceiling.  Max observing +
        describing + awareness + non-judging + non-reactivity.
        Baer 2006 meditator subsample approached this profile."""
        result = score_ffmq15([5, 5, 5, 5, 5, 1, 1, 1, 1, 1, 1, 1, 5, 5, 5])
        assert result.total == 75
        for facet in ("observing", "describing", "acting", "nonjudging",
                      "nonreactivity"):
            assert _get_facet_by_name(result, facet) == 15

    def test_ave_non_judging_deficit_profile(self) -> None:
        """Marlatt 1985 abstinence-violation-effect substrate:
        non-judging at floor, other facets near midpoint.  The
        patient can observe, describe, act with awareness, and
        tolerate internal experience — but evaluates every
        inner event as bad/wrong.  Classic AVE precursor."""
        # Raw: midpoint everywhere except NJ at max (post-flip 1).
        result = score_ffmq15([3, 3, 3, 3, 3, 3, 3, 3, 3, 5, 5, 5, 3, 3, 3])
        assert result.nonjudging_sum == 3
        assert result.observing_sum == 9
        assert result.describing_sum == 9
        assert result.acting_sum == 9
        assert result.nonreactivity_sum == 9
        # Grand total: 9+9+9+3+9 = 39.
        assert result.total == 39

    def test_automatic_pilot_relapse_profile(self) -> None:
        """Bowen 2014 MBRP cue-reactivity signature: acting-with-
        awareness at floor, other facets normal.  The patient
        operates on autopilot — finds themselves mid-behavior
        before the urge becomes conscious.  Primary intervention
        target for MBRP per §3.2."""
        result = score_ffmq15([3, 3, 3, 3, 3, 3, 5, 5, 5, 3, 3, 3, 3, 3, 3])
        assert result.acting_sum == 3
        assert result.total == 9 + 9 + 3 + 9 + 9  # 39

    def test_alexithymia_describing_deficit_profile(self) -> None:
        """Kashdan 2015 emotional-granularity deficit / Baer 2006
        TAS-20-linked pattern: describing at floor, other facets
        near midpoint.  Patient observes internal experience
        but cannot label it — prerequisite failure for cognitive-
        restructuring work."""
        result = score_ffmq15([3, 3, 3, 1, 1, 5, 3, 3, 3, 3, 3, 3, 3, 3, 3])
        assert result.describing_sum == 3
        # Grand total: 9+3+9+9+9 = 39.
        assert result.total == 39

    def test_community_sample_midpoint_profile(self) -> None:
        """Gu 2016 non-clinical community sample approximated the
        midpoint profile.  All raw 3s -> total 45, every facet 9."""
        result = score_ffmq15([3] * 15)
        assert result.total == 45

    def test_observing_only_elevated_meditator_profile(self) -> None:
        """Baer 2008 §3: observing elevated without other facets
        is the NOVICE-MEDITATOR / NON-MEDITATOR heightened-
        awareness-without-regulation pattern.  Illustrative of
        why observing must be interpreted in CONTEXT of the
        other facets (module docstring §'Observing')."""
        result = score_ffmq15([5, 5, 5, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3])
        assert result.observing_sum == 15
        assert result.describing_sum == 9
        assert result.acting_sum == 9
        assert result.nonjudging_sum == 9
        assert result.nonreactivity_sum == 9
        # Grand total 15+9+9+9+9 = 51.
        assert result.total == 51


# ---------------------------------------------------------------------------
# Validation errors
# ---------------------------------------------------------------------------


class TestFfmq15ValidationErrors:
    def test_requires_exactly_15_items(self) -> None:
        with pytest.raises(InvalidResponseError):
            score_ffmq15([3] * 14)
        with pytest.raises(InvalidResponseError):
            score_ffmq15([3] * 16)

    def test_rejects_empty(self) -> None:
        with pytest.raises(InvalidResponseError):
            score_ffmq15([])

    def test_rejects_10_items_maas_trap(self) -> None:
        """Trap: someone confuses FFMQ-15 (15) with MAAS (15
        actually, but the full MAAS is 15 too — wait).  Actual
        trap: confuses FFMQ-15 with PANAS-10 (10) or with the
        full 39-item FFMQ."""
        with pytest.raises(InvalidResponseError):
            score_ffmq15([3] * 10)

    def test_rejects_39_items_full_ffmq_trap(self) -> None:
        """Trap: someone sends the full 39-item FFMQ — 422."""
        with pytest.raises(InvalidResponseError):
            score_ffmq15([3] * 39)

    def test_rejects_value_0(self) -> None:
        """FFMQ Likert is 1-5, not 0-4."""
        with pytest.raises(InvalidResponseError):
            score_ffmq15([0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3])

    def test_rejects_value_6(self) -> None:
        """FFMQ Likert ceiling is 5."""
        with pytest.raises(InvalidResponseError):
            score_ffmq15([6, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3])

    def test_rejects_negative_value(self) -> None:
        with pytest.raises(InvalidResponseError):
            score_ffmq15([-1, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3])

    def test_rejects_bool_true(self) -> None:
        """CLAUDE.md bool-rejection rule: True must not coerce
        to 1."""
        with pytest.raises(InvalidResponseError):
            score_ffmq15([True, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3])

    def test_rejects_bool_false(self) -> None:
        with pytest.raises(InvalidResponseError):
            score_ffmq15([False, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3])

    def test_rejects_string_value(self) -> None:
        with pytest.raises(InvalidResponseError):
            score_ffmq15(["3", 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3])  # type: ignore[list-item]

    def test_rejects_float_value(self) -> None:
        """CLAUDE.md rejects non-int values — 3.0 is not 3."""
        with pytest.raises(InvalidResponseError):
            score_ffmq15([3.0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3])  # type: ignore[list-item]

    def test_rejects_none_value(self) -> None:
        with pytest.raises(InvalidResponseError):
            score_ffmq15([None, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3])  # type: ignore[list-item]

    def test_error_message_contains_position_1_indexed(self) -> None:
        """Clinician-facing error messages use 1-indexed item
        position — matches the Baer 2006 administration form."""
        with pytest.raises(InvalidResponseError) as exc:
            score_ffmq15([3, 3, 3, 3, 99, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3])
        assert "item 5" in str(exc.value)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _facet_for_position(position_1: int) -> tuple[int, ...]:
    """Return the facet-positions tuple containing the given 1-
    indexed position."""
    for facet in (
        FFMQ15_OBSERVING_POSITIONS,
        FFMQ15_DESCRIBING_POSITIONS,
        FFMQ15_ACTING_POSITIONS,
        FFMQ15_NONJUDGING_POSITIONS,
        FFMQ15_NONREACTIVITY_POSITIONS,
    ):
        if position_1 in facet:
            return facet
    raise AssertionError(f"position {position_1} not in any facet")


def _get_facet_sum(result: Ffmq15Result, position_1: int) -> int:
    """Return the facet sum whose facet contains the given position."""
    if position_1 in FFMQ15_OBSERVING_POSITIONS:
        return result.observing_sum
    if position_1 in FFMQ15_DESCRIBING_POSITIONS:
        return result.describing_sum
    if position_1 in FFMQ15_ACTING_POSITIONS:
        return result.acting_sum
    if position_1 in FFMQ15_NONJUDGING_POSITIONS:
        return result.nonjudging_sum
    if position_1 in FFMQ15_NONREACTIVITY_POSITIONS:
        return result.nonreactivity_sum
    raise AssertionError(f"position {position_1} not in any facet")


def _get_facet_by_name(result: Ffmq15Result, name: str) -> int:
    """Return a facet sum by its short name."""
    return {
        "observing": result.observing_sum,
        "describing": result.describing_sum,
        "acting": result.acting_sum,
        "nonjudging": result.nonjudging_sum,
        "nonreactivity": result.nonreactivity_sum,
    }[name]

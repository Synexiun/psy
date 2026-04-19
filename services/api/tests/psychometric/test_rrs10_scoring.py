"""Unit tests for the RRS-10 scorer (Treynor 2003).

Covers:
- Constants (count, range, subscale partition, no-reverse pin).
- Total correctness (midline, max, min, boundary sums).
- Subscale assignments (brooding vs reflection, each item pinned).
- Item count validation (wrong-length rejection).
- Item range validation (0, 5, negatives).
- Bool rejection (CLAUDE.md standing rule).
- Result shape (dataclass frozen / field types / version pin).
- Clinical vignettes (brooding-dominant, reflection-dominant, mixed,
  community mean, clinical-elevated).
- No safety routing (no triggering-items concept in this instrument).
"""

from __future__ import annotations

import pytest

from discipline.psychometric.scoring.rrs10 import (
    INSTRUMENT_VERSION,
    InvalidResponseError,
    ITEM_COUNT,
    ITEM_MAX,
    ITEM_MIN,
    RRS10_SUBSCALES,
    Rrs10Result,
    score_rrs10,
)


class TestConstants:
    """Pin scale constants — changing any of these without an
    instrument-version bump invalidates the audit trail."""

    def test_item_count_is_ten(self) -> None:
        assert ITEM_COUNT == 10

    def test_item_min_is_one(self) -> None:
        # Treynor 2003 scale anchors: 1 = almost never.  A refactor
        # shifting the floor to 0 would silently bias every total
        # downward by 10 points and change the minimum total from
        # 10 to 0.
        assert ITEM_MIN == 1

    def test_item_max_is_four(self) -> None:
        # Treynor 2003 scale anchors: 4 = almost always.  A refactor
        # to a 0-3 or 1-5 scale would produce score-shape divergence
        # from the published validation work.
        assert ITEM_MAX == 4

    def test_instrument_version_pinned(self) -> None:
        assert INSTRUMENT_VERSION == "rrs10-1.0.0"

    def test_subscale_names_pinned(self) -> None:
        assert set(RRS10_SUBSCALES.keys()) == {"brooding", "reflection"}

    def test_brooding_items(self) -> None:
        # Treynor 2003 PCA — brooding factor loading ≥ .40.
        # Corresponds to RRS-22 items 5, 10, 13, 15, 16 renumbered.
        assert RRS10_SUBSCALES["brooding"] == (1, 3, 6, 7, 8)

    def test_reflection_items(self) -> None:
        # Treynor 2003 PCA — reflection factor loading ≥ .40.
        # Corresponds to RRS-22 items 7, 11, 12, 20, 21 renumbered.
        assert RRS10_SUBSCALES["reflection"] == (2, 4, 5, 9, 10)

    def test_subscale_partition_is_complete(self) -> None:
        # Every 1-indexed item 1..10 must land in exactly one
        # subscale.  A refactor that added an item to both (double-
        # count) or dropped an item (orphan) would break clinical
        # interpretation silently.
        all_items: list[int] = []
        for positions in RRS10_SUBSCALES.values():
            all_items.extend(positions)
        assert sorted(all_items) == list(range(1, 11))

    def test_subscale_sizes_are_five_each(self) -> None:
        # Treynor 2003 extracted two 5-item factors.  Any deviation
        # (4+6, 3+7) would break the published validation.
        assert len(RRS10_SUBSCALES["brooding"]) == 5
        assert len(RRS10_SUBSCALES["reflection"]) == 5


class TestTotalCorrectness:
    """Pin arithmetic correctness of the total field."""

    def test_min_total_is_ten(self) -> None:
        # All 1s (almost never) — floor is 10, not 0.
        result = score_rrs10([1] * 10)
        assert result.total == 10

    def test_max_total_is_forty(self) -> None:
        # All 4s (almost always) — ceiling is 40.
        result = score_rrs10([4] * 10)
        assert result.total == 40

    def test_midline_all_twos(self) -> None:
        # All 2s — total 20.  Used in community comparison.
        result = score_rrs10([2] * 10)
        assert result.total == 20

    def test_midline_all_threes(self) -> None:
        # All 3s — total 30.  Clinical-sample-adjacent territory.
        result = score_rrs10([3] * 10)
        assert result.total == 30

    def test_total_is_arithmetic_sum(self) -> None:
        items = [1, 2, 3, 4, 1, 2, 3, 4, 1, 2]
        expected = sum(items)
        result = score_rrs10(items)
        assert result.total == expected

    def test_total_equals_brooding_plus_reflection(self) -> None:
        # Because the two subscales partition all 10 items and no
        # item is reverse-scored, total must always equal the sum
        # of the two subscale sums.  Breaking this invariant means
        # the partition is broken.
        for seed in range(10):
            items = [(seed + i) % 4 + 1 for i in range(10)]
            result = score_rrs10(items)
            assert (
                result.total
                == result.subscale_brooding + result.subscale_reflection
            )

    def test_community_mean_profile(self) -> None:
        # Treynor 2003 community sample: mean brooding ≈ 10.4,
        # mean reflection ≈ 10.1.  Approximate with brooding 10,
        # reflection 10 (both ~ "sometimes" evenly).
        # Brooding items (positions 1, 3, 6, 7, 8) at value 2 each = 10.
        # Reflection items (positions 2, 4, 5, 9, 10) at value 2 each = 10.
        items = [2] * 10
        result = score_rrs10(items)
        assert result.subscale_brooding == 10
        assert result.subscale_reflection == 10
        assert result.total == 20

    def test_brooding_dominant_profile(self) -> None:
        # Clinically-elevated brooding with low reflection.
        # Brooding items at 4, reflection items at 1.
        items = [4, 1, 4, 1, 1, 4, 4, 4, 1, 1]
        result = score_rrs10(items)
        assert result.subscale_brooding == 20
        assert result.subscale_reflection == 5
        assert result.total == 25

    def test_reflection_dominant_profile(self) -> None:
        # Adaptive profile — brooding low, reflection high.
        items = [1, 4, 1, 4, 4, 1, 1, 1, 4, 4]
        result = score_rrs10(items)
        assert result.subscale_brooding == 5
        assert result.subscale_reflection == 20
        assert result.total == 25

    def test_identical_total_can_have_different_profiles(self) -> None:
        # The clinical point of separating brooding vs reflection:
        # two patients with the same total (25) can have completely
        # different subscale profiles with opposite clinical
        # implications.  This test pins that separability.
        brooding_dominant = score_rrs10([4, 1, 4, 1, 1, 4, 4, 4, 1, 1])
        reflection_dominant = score_rrs10([1, 4, 1, 4, 4, 1, 1, 1, 4, 4])
        assert brooding_dominant.total == reflection_dominant.total == 25
        assert (
            brooding_dominant.subscale_brooding
            > reflection_dominant.subscale_brooding
        )
        assert (
            reflection_dominant.subscale_reflection
            > brooding_dominant.subscale_reflection
        )


class TestSubscaleAssignments:
    """Pin which position routes to which subscale.  A regression
    here would invert the maladaptive/adaptive clinical signal."""

    def test_brooding_position_1(self) -> None:
        # Position 1 → brooding; everyone else at 1 (almost never).
        items = [4, 1, 1, 1, 1, 1, 1, 1, 1, 1]
        result = score_rrs10(items)
        assert result.subscale_brooding == 4 + 4  # item at 4, others at 1
        # brooding positions are (1, 3, 6, 7, 8); position 1 = 4,
        # positions 3, 6, 7, 8 = 1 each.  Sum = 4 + 4 = 8.
        assert result.subscale_brooding == 8
        # reflection positions are (2, 4, 5, 9, 10); all at 1. Sum = 5.
        assert result.subscale_reflection == 5

    def test_brooding_position_3(self) -> None:
        items = [1, 1, 4, 1, 1, 1, 1, 1, 1, 1]
        result = score_rrs10(items)
        assert result.subscale_brooding == 8  # 1+4+1+1+1
        assert result.subscale_reflection == 5

    def test_brooding_position_6(self) -> None:
        items = [1, 1, 1, 1, 1, 4, 1, 1, 1, 1]
        result = score_rrs10(items)
        assert result.subscale_brooding == 8
        assert result.subscale_reflection == 5

    def test_brooding_position_7(self) -> None:
        items = [1, 1, 1, 1, 1, 1, 4, 1, 1, 1]
        result = score_rrs10(items)
        assert result.subscale_brooding == 8
        assert result.subscale_reflection == 5

    def test_brooding_position_8(self) -> None:
        items = [1, 1, 1, 1, 1, 1, 1, 4, 1, 1]
        result = score_rrs10(items)
        assert result.subscale_brooding == 8
        assert result.subscale_reflection == 5

    def test_reflection_position_2(self) -> None:
        items = [1, 4, 1, 1, 1, 1, 1, 1, 1, 1]
        result = score_rrs10(items)
        assert result.subscale_brooding == 5
        assert result.subscale_reflection == 8  # 4+1+1+1+1

    def test_reflection_position_4(self) -> None:
        items = [1, 1, 1, 4, 1, 1, 1, 1, 1, 1]
        result = score_rrs10(items)
        assert result.subscale_brooding == 5
        assert result.subscale_reflection == 8

    def test_reflection_position_5(self) -> None:
        items = [1, 1, 1, 1, 4, 1, 1, 1, 1, 1]
        result = score_rrs10(items)
        assert result.subscale_brooding == 5
        assert result.subscale_reflection == 8

    def test_reflection_position_9(self) -> None:
        items = [1, 1, 1, 1, 1, 1, 1, 1, 4, 1]
        result = score_rrs10(items)
        assert result.subscale_brooding == 5
        assert result.subscale_reflection == 8

    def test_reflection_position_10(self) -> None:
        items = [1, 1, 1, 1, 1, 1, 1, 1, 1, 4]
        result = score_rrs10(items)
        assert result.subscale_brooding == 5
        assert result.subscale_reflection == 8


class TestItemCountValidation:
    """Pin count-mismatch rejection."""

    def test_zero_items_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 10"):
            score_rrs10([])

    def test_nine_items_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 10"):
            score_rrs10([1] * 9)

    def test_eleven_items_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 10"):
            score_rrs10([1] * 11)

    def test_one_item_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 10"):
            score_rrs10([2])

    def test_twenty_items_rejected(self) -> None:
        # The full RRS-22 has 22 items; a 22-item input against the
        # RRS-10 scorer would silently score only the first 10,
        # producing a dangerously wrong total if not rejected.
        with pytest.raises(InvalidResponseError, match="exactly 10"):
            score_rrs10([1] * 22)

    def test_twenty_two_items_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 10"):
            score_rrs10([2] * 22)


class TestItemRangeValidation:
    """Pin out-of-range item rejection."""

    def test_zero_rejected(self) -> None:
        # 0 is the floor in many instruments (PHQ-9, GAD-7) but NOT
        # in RRS-10 (Treynor 2003 anchors start at 1).  A developer
        # reflexively using 0-indexed Likert would silently produce
        # a total 10 points below the real value.
        items = [0] + [1] * 9
        with pytest.raises(InvalidResponseError, match="out of range"):
            score_rrs10(items)

    def test_five_rejected(self) -> None:
        # 5 would be acceptable for SCS-SF (1-5) but NOT for RRS-10
        # (1-4).  A developer mis-applying SCS-SF encoding to RRS-10
        # would produce an inflated total.
        items = [5] + [1] * 9
        with pytest.raises(InvalidResponseError, match="out of range"):
            score_rrs10(items)

    def test_seven_rejected(self) -> None:
        # 7 would be acceptable for ERQ (1-7) but NOT for RRS-10.
        items = [1, 1, 1, 1, 1, 1, 1, 1, 7, 1]
        with pytest.raises(InvalidResponseError, match="out of range"):
            score_rrs10(items)

    def test_negative_rejected(self) -> None:
        items = [-1] + [1] * 9
        with pytest.raises(InvalidResponseError, match="out of range"):
            score_rrs10(items)

    def test_large_positive_rejected(self) -> None:
        items = [1] * 9 + [100]
        with pytest.raises(InvalidResponseError, match="out of range"):
            score_rrs10(items)

    def test_range_error_names_item_position(self) -> None:
        items = [1, 1, 1, 1, 1, 9, 1, 1, 1, 1]
        with pytest.raises(InvalidResponseError, match="item 6"):
            score_rrs10(items)

    def test_range_error_reports_offending_value(self) -> None:
        items = [1] * 9 + [42]
        with pytest.raises(InvalidResponseError, match="42"):
            score_rrs10(items)

    def test_boundary_one_accepted(self) -> None:
        # 1 is the floor and must be accepted.
        score_rrs10([1] * 10)

    def test_boundary_four_accepted(self) -> None:
        # 4 is the ceiling and must be accepted.
        score_rrs10([4] * 10)


class TestBoolRejection:
    """Pin CLAUDE.md standing rule: bool is not int for psychometric
    items.  Silent bool acceptance would allow True=1 / False=0 to
    masquerade as Likert responses with wrong semantics."""

    def test_true_rejected(self) -> None:
        items: list[object] = [True] + [1] * 9
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_rrs10(items)  # type: ignore[arg-type]

    def test_false_rejected(self) -> None:
        # False == 0 numerically; if bool wasn't rejected, this
        # would be caught later by the range check — but the error
        # would cite "out of range" instead of "must be int" and
        # mask the real problem (wrong TYPE).
        items: list[object] = [False] + [1] * 9
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_rrs10(items)  # type: ignore[arg-type]

    def test_bool_in_middle_rejected(self) -> None:
        items: list[object] = [1, 2, True, 3, 1, 2, 3, 4, 1, 2]
        with pytest.raises(InvalidResponseError, match="item 3"):
            score_rrs10(items)  # type: ignore[arg-type]


class TestResultShape:
    """Pin the dataclass shape and immutability."""

    def test_returns_rrs10_result_instance(self) -> None:
        result = score_rrs10([1] * 10)
        assert isinstance(result, Rrs10Result)

    def test_result_is_frozen(self) -> None:
        result = score_rrs10([1] * 10)
        with pytest.raises((AttributeError, Exception)):
            result.total = 999  # type: ignore[misc]

    def test_total_is_int(self) -> None:
        result = score_rrs10([1, 2, 3, 4, 1, 2, 3, 4, 1, 2])
        assert isinstance(result.total, int)

    def test_subscale_brooding_is_int(self) -> None:
        result = score_rrs10([1] * 10)
        assert isinstance(result.subscale_brooding, int)

    def test_subscale_reflection_is_int(self) -> None:
        result = score_rrs10([1] * 10)
        assert isinstance(result.subscale_reflection, int)

    def test_items_is_tuple(self) -> None:
        result = score_rrs10([1, 2, 3, 4, 1, 2, 3, 4, 1, 2])
        assert isinstance(result.items, tuple)

    def test_items_length_is_ten(self) -> None:
        result = score_rrs10([1] * 10)
        assert len(result.items) == 10

    def test_items_preserves_input(self) -> None:
        raw = [1, 2, 3, 4, 1, 2, 3, 4, 1, 2]
        result = score_rrs10(raw)
        assert list(result.items) == raw

    def test_instrument_version_default_populated(self) -> None:
        result = score_rrs10([1] * 10)
        assert result.instrument_version == "rrs10-1.0.0"

    def test_result_is_hashable(self) -> None:
        # Frozen dataclass with tuple field → hashable.  Used by
        # audit-trail deduplication elsewhere in the platform.
        result = score_rrs10([1] * 10)
        hash(result)

    def test_subscale_brooding_range(self) -> None:
        # Floor 5 (all brooding items at 1), ceiling 20 (all at 4).
        min_result = score_rrs10([1] * 10)
        max_result = score_rrs10([4] * 10)
        assert min_result.subscale_brooding == 5
        assert max_result.subscale_brooding == 20

    def test_subscale_reflection_range(self) -> None:
        # Floor 5, ceiling 20.
        min_result = score_rrs10([1] * 10)
        max_result = score_rrs10([4] * 10)
        assert min_result.subscale_reflection == 5
        assert max_result.subscale_reflection == 20


class TestClinicalVignettes:
    """End-to-end clinical scenarios pinning subscale-profile
    semantics.  These document the patterns downstream intervention
    routing reads."""

    def test_passive_brooder_profile(self) -> None:
        # High brooding, moderate reflection.  Treynor 2003 reports
        # this as the prototypical maladaptive-rumination pattern
        # with the strongest prospective depression link.
        # Brooding items at 4, reflection items at 2.
        items = [4, 2, 4, 2, 2, 4, 4, 4, 2, 2]
        result = score_rrs10(items)
        assert result.subscale_brooding == 20
        assert result.subscale_reflection == 10
        # Intervention downstream: mindfulness / attention-deployment
        # BEFORE any cognitive work.

    def test_analytic_reflector_profile(self) -> None:
        # Low brooding, high reflection — the adaptive pattern.
        # Brooding at 1, reflection at 4.
        items = [1, 4, 1, 4, 4, 1, 1, 1, 4, 4]
        result = score_rrs10(items)
        assert result.subscale_brooding == 5
        assert result.subscale_reflection == 20
        # Intervention downstream: low-disruption; support reflective
        # journaling, do not over-scaffold.

    def test_disengaged_profile(self) -> None:
        # Low on both scales.  Not automatically healthy — in the
        # presence of TAS-20 alexithymia or ERQ suppression, this
        # pattern signals emotion avoidance rather than adaptive
        # resilience.
        items = [1] * 10
        result = score_rrs10(items)
        assert result.subscale_brooding == 5
        assert result.subscale_reflection == 5
        assert result.total == 10

    def test_cognitively_loaded_profile(self) -> None:
        # High on both — "mixed ruminator" that Whitmer & Gotlib
        # 2011 report is common in recently-depressed samples
        # (brooding is elevated as a trait marker, reflection is
        # elevated state-dependently as the patient tries to
        # understand what is happening).
        items = [4] * 10
        result = score_rrs10(items)
        assert result.subscale_brooding == 20
        assert result.subscale_reflection == 20
        assert result.total == 40

    def test_relapse_risk_profile(self) -> None:
        # Caselli 2010 prospective addiction profile — elevated
        # brooding independent of reflection predicts time-to-
        # relapse in alcohol-use-disorder samples.  Brooding 18,
        # reflection 10 → moderately-elevated brooding with
        # unremarkable reflection.
        # Brooding items target sum 18: use values (4, 4, 4, 3, 3) → 18.
        # Reflection items target sum 10: use values (2, 2, 2, 2, 2) → 10.
        # Position-order: 1(brood=4), 2(refl=2), 3(brood=4), 4(refl=2),
        #                 5(refl=2), 6(brood=4), 7(brood=3), 8(brood=3),
        #                 9(refl=2), 10(refl=2).
        items = [4, 2, 4, 2, 2, 4, 3, 3, 2, 2]
        result = score_rrs10(items)
        assert result.subscale_brooding == 18
        assert result.subscale_reflection == 10


class TestNoSafetyRouting:
    """Pin that RRS-10 carries no safety-item concept.  Downstream
    routing must not treat elevated rumination as imminent-harm
    signal (that belongs to C-SSRS / PHQ-9 item 9)."""

    def test_max_total_no_safety_field(self) -> None:
        # Even at ceiling, no safety flag surfaces from the scorer.
        # The scorer contract is deliberately narrow: a brood-
        # dominant rumination pattern at maximum intensity is
        # clinically elevated, not acutely life-threatening.
        result = score_rrs10([4] * 10)
        fields = set(result.__dataclass_fields__.keys())
        assert "requires_t3" not in fields
        assert "safety_flag" not in fields
        assert "triggering_items" not in fields

    def test_all_brooding_max_no_safety_field(self) -> None:
        # Even maxing out only the maladaptive subscale — the
        # prototypical highest-risk rumination pattern — does not
        # surface an imminent-harm signal from this scorer.
        items = [4, 1, 4, 1, 1, 4, 4, 4, 1, 1]
        result = score_rrs10(items)
        assert result.subscale_brooding == 20
        # No safety field on the result; harm screening stays with
        # C-SSRS.
        fields = set(result.__dataclass_fields__.keys())
        assert "requires_t3" not in fields

    def test_no_severity_field(self) -> None:
        # Treynor 2003 published no severity bands.  The scorer must
        # NOT invent any; continuous-sentinel handling happens at
        # the router level.
        result = score_rrs10([4] * 10)
        fields = set(result.__dataclass_fields__.keys())
        assert "severity" not in fields

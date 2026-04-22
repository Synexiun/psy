"""Tests for the Brief COPE scorer (Carver 1997).

Coverage:
- Constants pinned to Carver 1997 Appendix A.
- Subscale partition: 14 two-item subscales with published
  positions.
- Partition invariants (coverage of items 1-28, no overlap).
- Total = sum of all 28 items, 28-112.
- Every subscale isolated correctly.
- Severity always "continuous" (no bands).
- Item count validation.
- Range validation (item outside 1-4 rejected).
- Bool rejection per CLAUDE.md standing rule.
- Result frozen, items preserved as raw tuple.
- No fields present that shouldn't be: no positive_screen,
  no cutoff_used, no requires_t3.
- Clinical vignettes covering all 14 subscales.
"""

from __future__ import annotations

import pytest

from discipline.psychometric.scoring.brief_cope import (
    BRIEF_COPE_SUBSCALE_POSITIONS,
    BRIEF_COPE_SUBSCALES,
    INSTRUMENT_VERSION,
    ITEM_COUNT,
    ITEM_MAX,
    ITEM_MIN,
    BriefCopeResult,
    InvalidResponseError,
    score_brief_cope,
)


def _items_for(**subscale_targets: int) -> list[int]:
    """Build a 28-item raw vector where specified subscales get
    the given total (0-8), distributed across their 2 positions.

    Each position gets the target value / 2 (rounded up for first
    position when odd) but bounded to item max 4.  For simplicity
    and because max total per subscale is 8, this works perfectly
    for targets 2, 4, 6, 8 (and hits max 4 evenly).
    """
    items = [1] * 28  # Minimum item value — base all-low pattern
    for name, target in subscale_targets.items():
        assert 2 <= target <= 8, (
            f"Subscale {name} target {target} out of 2-8"
        )
        i1, i2 = BRIEF_COPE_SUBSCALE_POSITIONS[name]
        # Distribute: prefer balanced split
        v1 = min(4, (target + 1) // 2)
        v2 = target - v1
        assert 1 <= v1 <= 4 and 1 <= v2 <= 4
        items[i1 - 1] = v1
        items[i2 - 1] = v2
    return items


class TestConstants:
    """Brief COPE constants pinned to Carver 1997."""

    def test_item_count_is_twenty_eight(self) -> None:
        assert ITEM_COUNT == 28

    def test_item_range_is_1_to_4(self) -> None:
        assert ITEM_MIN == 1
        assert ITEM_MAX == 4

    def test_fourteen_subscales(self) -> None:
        assert len(BRIEF_COPE_SUBSCALES) == 14
        assert len(BRIEF_COPE_SUBSCALE_POSITIONS) == 14

    def test_subscale_names_canonical(self) -> None:
        # Carver 1997 Table 1 ordering.
        assert BRIEF_COPE_SUBSCALES == (
            "self_distraction",
            "active_coping",
            "denial",
            "substance_use",
            "use_emotional_support",
            "use_instrumental_support",
            "behavioral_disengagement",
            "venting",
            "positive_reframing",
            "planning",
            "humor",
            "acceptance",
            "religion",
            "self_blame",
        )

    def test_subscale_positions_carver_1997(self) -> None:
        # Carver 1997 Appendix A published positions.
        assert BRIEF_COPE_SUBSCALE_POSITIONS == {
            "self_distraction": (1, 19),
            "active_coping": (2, 7),
            "denial": (3, 8),
            "substance_use": (4, 11),
            "use_emotional_support": (5, 15),
            "use_instrumental_support": (10, 23),
            "behavioral_disengagement": (6, 16),
            "venting": (9, 21),
            "positive_reframing": (12, 17),
            "planning": (14, 25),
            "humor": (18, 28),
            "acceptance": (20, 24),
            "religion": (22, 27),
            "self_blame": (13, 26),
        }

    def test_instrument_version_pinned(self) -> None:
        assert INSTRUMENT_VERSION == "brief_cope-1.0.0"


class TestPartitionInvariants:
    """Verify 14 subscales partition items 1-28 correctly."""

    def test_every_position_covered_exactly_once(self) -> None:
        # Union of all subscale positions should equal {1..28}
        # with no overlap.
        all_positions: list[int] = []
        for positions in BRIEF_COPE_SUBSCALE_POSITIONS.values():
            all_positions.extend(positions)
        assert sorted(all_positions) == list(range(1, 29))

    def test_no_position_in_two_subscales(self) -> None:
        seen: set[int] = set()
        for name, positions in BRIEF_COPE_SUBSCALE_POSITIONS.items():
            for pos in positions:
                assert pos not in seen, (
                    f"Position {pos} in {name} already seen"
                )
                seen.add(pos)

    def test_each_subscale_has_two_positions(self) -> None:
        for name, positions in BRIEF_COPE_SUBSCALE_POSITIONS.items():
            assert len(positions) == 2, (
                f"Subscale {name} has {len(positions)} positions"
            )

    def test_positions_are_valid_item_indices(self) -> None:
        for name, positions in BRIEF_COPE_SUBSCALE_POSITIONS.items():
            for pos in positions:
                assert 1 <= pos <= 28, (
                    f"{name} position {pos} out of 1-28"
                )


class TestTotalCorrectness:
    """Total = raw sum of all 28 items."""

    def test_all_ones_total_twenty_eight(self) -> None:
        result = score_brief_cope([1] * 28)
        assert result.total == 28

    def test_all_fours_total_one_twelve(self) -> None:
        result = score_brief_cope([4] * 28)
        assert result.total == 112

    def test_all_twos_total_fifty_six(self) -> None:
        result = score_brief_cope([2] * 28)
        assert result.total == 56

    def test_all_threes_total_eighty_four(self) -> None:
        result = score_brief_cope([3] * 28)
        assert result.total == 84


class TestSubscaleIsolation:
    """Each subscale isolated from the others."""

    @pytest.mark.parametrize(
        "subscale_name", list(BRIEF_COPE_SUBSCALES)
    )
    def test_only_one_subscale_elevated(
        self, subscale_name: str
    ) -> None:
        # All subscales at floor (2) except target at ceiling (8).
        items = [1] * 28
        i1, i2 = BRIEF_COPE_SUBSCALE_POSITIONS[subscale_name]
        items[i1 - 1] = 4
        items[i2 - 1] = 4
        result = score_brief_cope(items)
        assert result.subscales[subscale_name] == 8
        # Every OTHER subscale must be at floor (2 = 1+1).
        for name in BRIEF_COPE_SUBSCALES:
            if name != subscale_name:
                assert result.subscales[name] == 2, (
                    f"Subscale {name} leaked while only "
                    f"{subscale_name} should be elevated"
                )


class TestSubscaleRange:
    """Each subscale sum is in the 2-8 range."""

    def test_minimum_subscale_sum(self) -> None:
        result = score_brief_cope([1] * 28)
        for name in BRIEF_COPE_SUBSCALES:
            assert result.subscales[name] == 2

    def test_maximum_subscale_sum(self) -> None:
        result = score_brief_cope([4] * 28)
        for name in BRIEF_COPE_SUBSCALES:
            assert result.subscales[name] == 8


class TestSeverityContinuous:
    """Severity is always 'continuous' per Carver 1997."""

    def test_severity_at_floor(self) -> None:
        result = score_brief_cope([1] * 28)
        assert result.severity == "continuous"

    def test_severity_at_ceiling(self) -> None:
        result = score_brief_cope([4] * 28)
        assert result.severity == "continuous"

    def test_severity_at_midpoint(self) -> None:
        result = score_brief_cope([2] * 14 + [3] * 14)
        assert result.severity == "continuous"


class TestItemCountValidation:
    """Wrong item count raises InvalidResponseError."""

    def test_empty_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 28"):
            score_brief_cope([])

    def test_twenty_seven_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 28"):
            score_brief_cope([1] * 27)

    def test_twenty_nine_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 28"):
            score_brief_cope([1] * 29)


class TestItemRangeValidation:
    """Values outside 1-4 raise InvalidResponseError."""

    def test_zero_rejected(self) -> None:
        items = [1] * 28
        items[0] = 0
        with pytest.raises(InvalidResponseError, match="item 1"):
            score_brief_cope(items)

    def test_five_rejected(self) -> None:
        items = [1] * 28
        items[14] = 5
        with pytest.raises(InvalidResponseError, match="item 15"):
            score_brief_cope(items)

    def test_negative_rejected(self) -> None:
        items = [1] * 28
        items[13] = -1
        with pytest.raises(InvalidResponseError, match="item 14"):
            score_brief_cope(items)

    def test_far_out_of_range_rejected(self) -> None:
        items = [1] * 28
        items[27] = 999
        with pytest.raises(InvalidResponseError, match="item 28"):
            score_brief_cope(items)

    def test_error_message_names_range(self) -> None:
        items = [1] * 28
        items[0] = 10
        with pytest.raises(InvalidResponseError, match="1-4"):
            score_brief_cope(items)


class TestItemTypeValidation:
    """Bool and non-int rejection per CLAUDE.md rule."""

    def test_bool_true_rejected(self) -> None:
        items: list[object] = [1] * 28
        items[0] = True
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_brief_cope(items)  # type: ignore[arg-type]

    def test_bool_false_rejected(self) -> None:
        items: list[object] = [1] * 28
        items[14] = False
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_brief_cope(items)  # type: ignore[arg-type]

    def test_float_rejected(self) -> None:
        items: list[object] = [1] * 28
        items[10] = 2.5
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_brief_cope(items)  # type: ignore[arg-type]

    def test_string_rejected(self) -> None:
        items: list[object] = [1] * 28
        items[5] = "3"
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_brief_cope(items)  # type: ignore[arg-type]

    def test_none_rejected(self) -> None:
        items: list[object] = [1] * 28
        items[20] = None
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_brief_cope(items)  # type: ignore[arg-type]


class TestResultTyping:
    """Result is a frozen dataclass with expected invariants."""

    def test_result_is_frozen(self) -> None:
        result = score_brief_cope([1] * 28)
        with pytest.raises(AttributeError):
            result.total = 999  # type: ignore[misc]

    def test_items_is_tuple(self) -> None:
        result = score_brief_cope([1] * 28)
        assert isinstance(result.items, tuple)

    def test_items_preserves_raw_order(self) -> None:
        raw = [1, 2, 3, 4, 1, 2, 3, 4] * 3 + [1, 2, 3, 4]
        assert len(raw) == 28
        result = score_brief_cope(raw)
        assert result.items == tuple(raw)

    def test_subscales_dict_has_fourteen_entries(self) -> None:
        result = score_brief_cope([1] * 28)
        assert len(result.subscales) == 14

    def test_subscales_dict_keys_match_constants(self) -> None:
        result = score_brief_cope([1] * 28)
        assert set(result.subscales.keys()) == set(BRIEF_COPE_SUBSCALES)

    def test_instrument_version_populated(self) -> None:
        result = score_brief_cope([1] * 28)
        assert result.instrument_version == "brief_cope-1.0.0"

    def test_result_is_brief_cope_result_type(self) -> None:
        result = score_brief_cope([1] * 28)
        assert isinstance(result, BriefCopeResult)

    def test_no_positive_screen_attribute(self) -> None:
        result = score_brief_cope([1] * 28)
        assert not hasattr(result, "positive_screen")

    def test_no_cutoff_used_attribute(self) -> None:
        result = score_brief_cope([1] * 28)
        assert not hasattr(result, "cutoff_used")

    def test_no_requires_t3_attribute(self) -> None:
        result = score_brief_cope([1] * 28)
        assert not hasattr(result, "requires_t3")


class TestHelperConstruction:
    """Verify _items_for helper round-trips subscale totals."""

    def test_single_subscale_target_eight(self) -> None:
        items = _items_for(self_blame=8)
        result = score_brief_cope(items)
        assert result.subscales["self_blame"] == 8

    def test_single_subscale_target_two(self) -> None:
        # Floor value (all items = 1 gives subscale = 2).
        items = [1] * 28
        result = score_brief_cope(items)
        assert result.subscales["active_coping"] == 2

    def test_multiple_subscales_independent(self) -> None:
        items = _items_for(substance_use=8, active_coping=6)
        result = score_brief_cope(items)
        assert result.subscales["substance_use"] == 8
        assert result.subscales["active_coping"] == 6
        assert result.subscales["denial"] == 2
        assert result.subscales["self_blame"] == 2


class TestClinicalVignettes:
    """Carver 1997 / Marlatt 1985 / Holahan 1987 clinical scenarios."""

    def test_vignette_adaptive_profile(self) -> None:
        # High active_coping, planning, positive_reframing,
        # acceptance, emotional support.  Low denial, substance
        # use, behavioral disengagement, self-blame.  Marlatt
        # 1985 "reinforce existing repertoire" profile.
        items = _items_for(
            active_coping=8,
            planning=8,
            positive_reframing=8,
            acceptance=8,
            use_emotional_support=8,
        )
        result = score_brief_cope(items)
        assert result.subscales["active_coping"] == 8
        assert result.subscales["planning"] == 8
        assert result.subscales["positive_reframing"] == 8
        assert result.subscales["acceptance"] == 8
        assert result.subscales["use_emotional_support"] == 8
        # Maladaptive subscales stay at floor.
        assert result.subscales["substance_use"] == 2
        assert result.subscales["self_blame"] == 2
        assert result.subscales["denial"] == 2
        assert result.subscales["behavioral_disengagement"] == 2

    def test_vignette_avoidant_profile(self) -> None:
        # High denial, substance use, behavioral disengagement,
        # self-distraction.  Linehan 2015 DBT distress-tolerance
        # / Bowen 2014 MBRP urge-surfing target population.
        items = _items_for(
            denial=8,
            substance_use=8,
            behavioral_disengagement=8,
            self_distraction=8,
        )
        result = score_brief_cope(items)
        assert result.subscales["denial"] == 8
        assert result.subscales["substance_use"] == 8
        assert result.subscales["behavioral_disengagement"] == 8
        assert result.subscales["self_distraction"] == 8

    def test_vignette_substance_coping_signal(self) -> None:
        # The CLINICALLY LOAD-BEARING Brief COPE signal for the
        # platform.  A user with elevated substance-use coping
        # score is deploying substance use as their stress
        # response — regardless of AUDIT / DUDIT / FTND status.
        items = _items_for(substance_use=8)
        result = score_brief_cope(items)
        assert result.subscales["substance_use"] == 8
        # Other subscales at floor.
        for name in BRIEF_COPE_SUBSCALES:
            if name != "substance_use":
                assert result.subscales[name] == 2

    def test_vignette_self_blame_dominant(self) -> None:
        # Holahan 1987 strongest maladaptive-coping predictor.
        # Elevated self-blame with everything else at floor —
        # attribution-focused intervention target (CBT
        # restructuring, self-compassion work).
        items = _items_for(self_blame=8)
        result = score_brief_cope(items)
        assert result.subscales["self_blame"] == 8
        assert result.subscales["active_coping"] == 2

    def test_vignette_religious_coping(self) -> None:
        # Religion subscale elevated.  Adaptive for most users
        # (Pargament 1998 meta-analysis) but can be avoidant
        # if substituting for other processing.  The scorer
        # does NOT label this as adaptive or maladaptive —
        # intervention-matching layer decides.
        items = _items_for(religion=8)
        result = score_brief_cope(items)
        assert result.subscales["religion"] == 8

    def test_vignette_humor_coping(self) -> None:
        # Humor subscale elevated.  Kuiper 2004 meta-analysis
        # shows humor generally adaptive but context-dependent.
        items = _items_for(humor=8)
        result = score_brief_cope(items)
        assert result.subscales["humor"] == 8

    def test_vignette_mixed_realistic_profile(self) -> None:
        # Realistic clinical profile: moderate active coping
        # and planning, some acceptance and emotional support,
        # minor substance use and self-blame.
        items = _items_for(
            active_coping=6,
            planning=6,
            acceptance=5,
            use_emotional_support=5,
            substance_use=4,
            self_blame=3,
        )
        result = score_brief_cope(items)
        assert result.subscales["active_coping"] == 6
        assert result.subscales["planning"] == 6
        assert result.subscales["acceptance"] == 5
        assert result.subscales["use_emotional_support"] == 5
        assert result.subscales["substance_use"] == 4
        assert result.subscales["self_blame"] == 3

    def test_vignette_no_t3_at_ceiling(self) -> None:
        # Brief COPE never triggers T3 regardless of any
        # subscale.  Acute-risk stays on C-SSRS / PHQ-9 item 9.
        result = score_brief_cope([4] * 28)
        assert not hasattr(result, "requires_t3")
        assert result.severity == "continuous"

    def test_vignette_ceiling_all_four(self) -> None:
        # All items at ceiling.  Total 112; every subscale 8.
        result = score_brief_cope([4] * 28)
        assert result.total == 112
        for name in BRIEF_COPE_SUBSCALES:
            assert result.subscales[name] == 8

    def test_vignette_floor_all_ones(self) -> None:
        # All items at floor.  Total 28; every subscale 2.
        result = score_brief_cope([1] * 28)
        assert result.total == 28
        for name in BRIEF_COPE_SUBSCALES:
            assert result.subscales[name] == 2

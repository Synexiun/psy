"""PCL-5 scoring tests — Weathers 2013 / Blevins 2015.

Three load-bearing correctness properties for the 20-item PCL-5:

1. **Cutoff is ``>= 33``, not ``> 33``.**  Blevins 2015 §Results
   selected 33 as the operating point in the Veterans validation
   sample (sensitivity 0.82, specificity 0.84).  Boundary tests pin
   32/33 and 33/34 explicitly.  A fence-post regression here would
   either miss or over-fire roughly half of the patients at the
   clinical decision point.
2. **DSM-5 cluster boundaries map items correctly.**
   - Cluster B (Intrusion): items 1-5
   - Cluster C (Avoidance): items 6-7
   - Cluster D (Negative alterations): items 8-14
   - Cluster E (Hyperarousal): items 15-20
   The 1-indexed / 0-indexed slice conversion is the likeliest
   refactor-break site.  Every cluster boundary is pinned with a
   targeted endorsement pattern that isolates exactly one cluster.
3. **Exactly 20 items, each 0-4 Likert.**  Mismatched count or
   out-of-range value is a validation error, not a silent partial
   score.

Coverage strategy:
- Pin the 32/33 cutoff boundary.
- Pin all four DSM-5 cluster boundaries with single-cluster
  endorsement tests.
- Item-count and item-range validation.
- Bool rejection.
- Clinical vignettes — intrusion-dominant, avoidance-dominant,
  full-cluster presentations.
- No safety routing.
"""

from __future__ import annotations

import pytest

from discipline.psychometric.scoring.pcl5 import (
    INSTRUMENT_VERSION,
    ITEM_COUNT,
    ITEM_MAX,
    ITEM_MIN,
    PCL5_CLUSTERS,
    PCL5_DSM5_ALGORITHM_THRESHOLDS,
    PCL5_POSITIVE_CUTOFF,
    InvalidResponseError,
    Pcl5Result,
    score_pcl5,
)


def _zeros() -> list[int]:
    return [0] * ITEM_COUNT


def _endorse_at(positions_1: list[int], level: int = 4) -> list[int]:
    """Build a 20-item list with the given 1-indexed positions set to
    ``level`` and the rest zeroed.

    Used to isolate cluster-specific endorsements so cluster-boundary
    tests don't accidentally leak responses across cluster edges.
    """
    if not (ITEM_MIN <= level <= ITEM_MAX):
        raise ValueError(f"level must be in [{ITEM_MIN}, {ITEM_MAX}]")
    items = _zeros()
    for pos in positions_1:
        items[pos - 1] = level
    return items


class TestConstants:
    """Pin published constants so a drift from Weathers 2013 / Blevins
    2015 is caught."""

    def test_item_count_is_twenty(self) -> None:
        assert ITEM_COUNT == 20

    def test_item_range_is_zero_to_four(self) -> None:
        assert ITEM_MIN == 0
        assert ITEM_MAX == 4

    def test_positive_cutoff_is_thirty_three(self) -> None:
        """Blevins 2015 §Results — cutpoint 33 balances sens/spec in
        the Veterans sample.  Any change is a clinical change."""
        assert PCL5_POSITIVE_CUTOFF == 33

    def test_clusters_match_weathers_2013(self) -> None:
        """DSM-5 cluster-to-item mapping per Weathers 2013 §Scoring.
        A refactor that reassigned an item to a different cluster
        would break the DSM-5-algorithm alignment."""
        assert PCL5_CLUSTERS == {
            "intrusion": (1, 5),
            "avoidance": (6, 7),
            "negative_mood": (8, 14),
            "hyperarousal": (15, 20),
        }

    def test_dsm5_algorithm_thresholds(self) -> None:
        """DSM-5 provisional-diagnosis requirements per Weathers 2013.
        Exposed as a constant for future clinician-UI use; pinned
        here so a refactor can't silently drift from the published
        diagnostic thresholds."""
        assert PCL5_DSM5_ALGORITHM_THRESHOLDS == (
            ("intrusion", 1),
            ("avoidance", 1),
            ("negative_mood", 2),
            ("hyperarousal", 2),
        )

    def test_instrument_version_pinned(self) -> None:
        assert INSTRUMENT_VERSION == "pcl5-1.0.0"


class TestTotalCorrectness:
    """Straight 0-80 sum."""

    def test_zero_is_minimum(self) -> None:
        result = score_pcl5(_zeros())
        assert result.total == 0

    def test_max_is_eighty(self) -> None:
        """20 items × max 4 = 80."""
        result = score_pcl5([4] * ITEM_COUNT)
        assert result.total == 80

    def test_mixed_sum(self) -> None:
        """Arbitrary mix — verifies the total is a plain sum."""
        items = [3, 2, 1, 4, 0, 2, 3, 1, 0, 4, 2, 1, 3, 0, 4, 2, 1, 3, 2, 1]
        result = score_pcl5(items)
        assert result.total == sum(items)


class TestCutoffBoundary:
    """The ``>= 33`` probable-PTSD cutoff — explicit just-below and at-
    cutoff tests so a fence-post regression is caught.
    """

    def test_total_thirty_two_below_cutoff(self) -> None:
        """Total 32 → negative screen.  A ``>= 32`` bug would flip
        this positive and over-identify patients.  Build with 8
        items at 4 (sum 32)."""
        items = _zeros()
        for i in range(8):
            items[i] = 4
        result = score_pcl5(items)
        assert result.total == 32
        assert result.positive_screen is False

    def test_total_thirty_three_at_cutoff(self) -> None:
        """Total 33 → positive screen (the exact published cutoff).
        A ``> 33`` bug would flip this negative and under-identify."""
        items = _zeros()
        for i in range(8):
            items[i] = 4
        items[8] = 1  # 32 + 1 = 33
        result = score_pcl5(items)
        assert result.total == 33
        assert result.positive_screen is True

    def test_total_thirty_four_above_cutoff(self) -> None:
        items = _zeros()
        for i in range(8):
            items[i] = 4
        items[8] = 2  # 32 + 2 = 34
        result = score_pcl5(items)
        assert result.total == 34
        assert result.positive_screen is True


class TestClusterBoundaries:
    """Each DSM-5 cluster must map to its correct item range.  Targeted
    endorsements pin the boundary between adjacent clusters so a
    refactor that shifted item 5 → cluster C or item 6 → cluster B
    would fail.
    """

    def test_cluster_intrusion_items_one_to_five(self) -> None:
        """Endorse only items 1-5 at max → cluster B total = 20,
        others = 0.  This pins the upper boundary of cluster B."""
        result = score_pcl5(_endorse_at([1, 2, 3, 4, 5]))
        assert result.cluster_intrusion == 20  # 5 items × 4
        assert result.cluster_avoidance == 0
        assert result.cluster_negative_mood == 0
        assert result.cluster_hyperarousal == 0

    def test_cluster_avoidance_items_six_and_seven(self) -> None:
        """Endorse only items 6-7 → cluster C = 8, others = 0.  This
        pins the lower boundary of cluster C (item 6 is NOT cluster B)
        and the upper boundary (item 7 is NOT cluster D)."""
        result = score_pcl5(_endorse_at([6, 7]))
        assert result.cluster_intrusion == 0
        assert result.cluster_avoidance == 8
        assert result.cluster_negative_mood == 0
        assert result.cluster_hyperarousal == 0

    def test_cluster_negative_mood_items_eight_to_fourteen(self) -> None:
        """Endorse only items 8-14 → cluster D = 28 (7 items × 4)."""
        result = score_pcl5(_endorse_at([8, 9, 10, 11, 12, 13, 14]))
        assert result.cluster_intrusion == 0
        assert result.cluster_avoidance == 0
        assert result.cluster_negative_mood == 28
        assert result.cluster_hyperarousal == 0

    def test_cluster_hyperarousal_items_fifteen_to_twenty(self) -> None:
        """Endorse only items 15-20 → cluster E = 24 (6 items × 4).
        Pins the lower boundary of cluster E (item 15 is NOT
        cluster D) and the upper boundary (item 20 ends the
        instrument)."""
        result = score_pcl5(_endorse_at([15, 16, 17, 18, 19, 20]))
        assert result.cluster_intrusion == 0
        assert result.cluster_avoidance == 0
        assert result.cluster_negative_mood == 0
        assert result.cluster_hyperarousal == 24

    def test_cluster_sum_equals_total(self) -> None:
        """The four cluster subscales sum to the total.  A refactor
        that double-counted an item (e.g. put item 7 in both cluster
        C and cluster D) would break this invariant."""
        items = [3, 2, 1, 4, 0, 2, 3, 1, 0, 4, 2, 1, 3, 0, 4, 2, 1, 3, 2, 1]
        result = score_pcl5(items)
        cluster_sum = (
            result.cluster_intrusion
            + result.cluster_avoidance
            + result.cluster_negative_mood
            + result.cluster_hyperarousal
        )
        assert cluster_sum == result.total


class TestItemCountValidation:
    """Exactly 20 items required."""

    def test_rejects_nineteen_items(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 20 items"):
            score_pcl5([0] * 19)

    def test_rejects_twenty_one_items(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 20 items"):
            score_pcl5([0] * 21)

    def test_rejects_empty(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 20 items"):
            score_pcl5([])


class TestItemRangeValidation:
    """Items must be in [0, 4]."""

    @pytest.mark.parametrize("bad_value", [-1, 5, 10])
    def test_rejects_out_of_range(self, bad_value: int) -> None:
        items = _zeros()
        items[10] = bad_value
        with pytest.raises(InvalidResponseError, match="out of range"):
            score_pcl5(items)

    def test_error_names_one_indexed_item(self) -> None:
        """Error messages use 1-indexed item numbers to match the
        PCL-5 instrument document's item list."""
        items = _zeros()
        items[14] = 99  # item 15 (index 14) → cluster E
        with pytest.raises(InvalidResponseError, match="PCL-5 item 15"):
            score_pcl5(items)

    def test_rejects_string_item(self) -> None:
        items = _zeros()
        items[0] = "4"  # type: ignore[call-overload]
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_pcl5(items)

    def test_rejects_float_item(self) -> None:
        items = _zeros()
        items[0] = 4.0  # type: ignore[call-overload]
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_pcl5(items)


class TestBoolRejection:
    """Bool items rejected even though True/False map to valid 1/0.
    Rationale: uniform wire contract across the psychometric package.
    """

    def test_rejects_true_item(self) -> None:
        items = _zeros()
        items[0] = True  # type: ignore[call-overload]
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_pcl5(items)

    def test_rejects_false_item(self) -> None:
        items = _zeros()
        items[0] = False  # type: ignore[call-overload]
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_pcl5(items)


class TestResultShape:
    """Pcl5Result carries the fields the router + future trajectory
    layer need."""

    def test_result_is_frozen(self) -> None:
        result = score_pcl5(_zeros())
        with pytest.raises(Exception):  # FrozenInstanceError subclass
            result.total = 99  # type: ignore[misc]

    def test_items_are_tuple(self) -> None:
        """Tuple so Pcl5Result is hashable and the stored repository
        record is immutable."""
        items = _endorse_at([1, 5, 10, 15, 20], level=2)
        result = score_pcl5(items)
        assert isinstance(result.items, tuple)
        assert result.items == tuple(items)

    def test_result_echoes_instrument_version(self) -> None:
        result = score_pcl5(_zeros())
        assert result.instrument_version == INSTRUMENT_VERSION

    def test_no_requires_t3_field(self) -> None:
        """PCL-5 has no safety item.  The result dataclass deliberately
        omits requires_t3 so downstream routing cannot accidentally
        escalate a severe-PTSD patient into T3.  Co-administer C-SSRS
        for suicidality differential."""
        result = score_pcl5([4] * ITEM_COUNT)
        assert not hasattr(result, "requires_t3")


class TestClinicalVignettes:
    """Named patterns a clinician would recognize."""

    def test_intrusion_dominant_presentation(self) -> None:
        """Classic flashback-driven PTSD — cluster B elevated, others
        modest.  Clinically indicates prolonged-exposure therapy
        (the cluster-B-targeted intervention).  At total >= 33 →
        positive screen + intrusion-dominant pattern."""
        # Cluster B (items 1-5) at 4; others mixed lower
        items = [4, 4, 4, 4, 4, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1, 2, 2, 1, 1, 1]
        result = score_pcl5(items)
        assert result.cluster_intrusion == 20
        assert result.cluster_intrusion > result.cluster_avoidance
        assert result.cluster_intrusion > result.cluster_negative_mood
        assert result.cluster_intrusion > result.cluster_hyperarousal
        assert result.total >= PCL5_POSITIVE_CUTOFF
        assert result.positive_screen is True

    def test_negative_mood_dominant_presentation(self) -> None:
        """Numbing / cognitive-alteration-dominant PTSD — cluster D
        elevated.  Clinically indicates cognitive-processing therapy
        (the cluster-D-targeted intervention)."""
        items = [2, 1, 1, 1, 1, 1, 1, 4, 4, 4, 4, 4, 4, 4, 2, 1, 1, 2, 1, 1]
        result = score_pcl5(items)
        assert result.cluster_negative_mood == 28
        assert result.cluster_negative_mood > result.cluster_intrusion
        assert result.cluster_negative_mood > result.cluster_avoidance
        assert result.cluster_negative_mood > result.cluster_hyperarousal
        assert result.total >= PCL5_POSITIVE_CUTOFF
        assert result.positive_screen is True

    def test_subthreshold_negative_screen(self) -> None:
        """Symptomatic but below cutoff — the "positive PC-PTSD-5 but
        negative PCL-5" pattern a clinician sees when the primary-
        care screen was sensitive but the full assessment didn't
        confirm.  A legitimate clinical outcome — route to watchful
        waiting or low-intensity intervention."""
        items = [2, 2, 1, 1, 0, 2, 1, 2, 1, 2, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1]
        result = score_pcl5(items)
        assert result.total < PCL5_POSITIVE_CUTOFF
        assert result.positive_screen is False

    def test_full_symptom_cluster(self) -> None:
        """All 20 items endorsed at 4 → clear positive, max severity
        across every cluster.  Defining case for outcome-tracking
        baseline in severe PTSD."""
        result = score_pcl5([4] * ITEM_COUNT)
        assert result.total == 80
        assert result.positive_screen is True
        assert result.cluster_intrusion == 20
        assert result.cluster_avoidance == 8
        assert result.cluster_negative_mood == 28
        assert result.cluster_hyperarousal == 24


class TestNoSafetyRouting:
    """PCL-5 has no direct suicidality item.  Item 16 (destructive
    behavior) is the closest but asks about risk-taking broadly, not
    self-harm.  The scorer must not expose anything the router could
    mistake for a T3 trigger.
    """

    def test_max_total_has_no_safety_field(self) -> None:
        result = score_pcl5([4] * ITEM_COUNT)
        assert not hasattr(result, "requires_t3")
        assert not hasattr(result, "t3_reason")
        assert not hasattr(result, "safety_item_positive")
        assert not hasattr(result, "triggering_items")

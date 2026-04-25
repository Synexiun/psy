"""Unit tests for _cluster_sum() and _validate_item() pure helpers in
discipline.psychometric.scoring.pcl5.

_cluster_sum(items, cluster_name) → int
  PCL5_CLUSTERS uses inclusive-inclusive 1-indexed ranges (unlike the
  explicit position tuples in HADS/DASS-21).  The helper slices
  items[start_1-1 : end_1] — the end_1 is inclusive in the published
  spec but Python slice end is exclusive, so slicing to end_1 (not end_1-1)
  is intentional.

  DSM-5 cluster structure (Weathers 2013):
    "intrusion"     items 1-5   (Cluster B)
    "avoidance"     items 6-7   (Cluster C)
    "negative_mood" items 8-14  (Cluster D)
    "hyperarousal"  items 15-20 (Cluster E)

_validate_item(index_1, value) → int
  0-4 Likert.  Bool guard applies.
"""

from __future__ import annotations

import pytest

from discipline.psychometric.scoring.pcl5 import (
    ITEM_MAX,
    ITEM_MIN,
    PCL5_CLUSTERS,
    InvalidResponseError,
    _cluster_sum,
    _validate_item,
)

_ALL_ZEROS: tuple[int, ...] = (0,) * 20
_ALL_FOURS: tuple[int, ...] = (4,) * 20


# ---------------------------------------------------------------------------
# _cluster_sum — DSM-5 cluster sums (inclusive-inclusive ranges)
# ---------------------------------------------------------------------------


class TestClusterSum:
    def test_intrusion_5_items_all_one(self) -> None:
        items = (1,) * 20
        assert _cluster_sum(items, "intrusion") == 5

    def test_avoidance_2_items_all_one(self) -> None:
        items = (1,) * 20
        assert _cluster_sum(items, "avoidance") == 2

    def test_negative_mood_7_items_all_one(self) -> None:
        items = (1,) * 20
        assert _cluster_sum(items, "negative_mood") == 7

    def test_hyperarousal_6_items_all_one(self) -> None:
        items = (1,) * 20
        assert _cluster_sum(items, "hyperarousal") == 6

    def test_all_zeros_sum_is_zero(self) -> None:
        for cluster in PCL5_CLUSTERS:
            assert _cluster_sum(_ALL_ZEROS, cluster) == 0

    def test_all_fours_intrusion_is_20(self) -> None:
        assert _cluster_sum(_ALL_FOURS, "intrusion") == 20

    def test_all_fours_hyperarousal_is_24(self) -> None:
        assert _cluster_sum(_ALL_FOURS, "hyperarousal") == 24

    def test_clusters_cover_all_20_items(self) -> None:
        all_positions: set[int] = set()
        for name, (start_1, end_1) in PCL5_CLUSTERS.items():
            all_positions |= set(range(start_1, end_1 + 1))
        assert all_positions == set(range(1, 21))

    def test_clusters_are_mutually_disjoint(self) -> None:
        cluster_ranges = []
        for start_1, end_1 in PCL5_CLUSTERS.values():
            cluster_ranges.append(set(range(start_1, end_1 + 1)))
        for i, r1 in enumerate(cluster_ranges):
            for r2 in cluster_ranges[i + 1 :]:
                assert r1.isdisjoint(r2)

    def test_four_clusters_present(self) -> None:
        assert len(PCL5_CLUSTERS) == 4

    def test_cluster_structure_matches_dsm5(self) -> None:
        # Pin the published DSM-5 boundaries — changing these is a clinical decision
        assert PCL5_CLUSTERS["intrusion"] == (1, 5)
        assert PCL5_CLUSTERS["avoidance"] == (6, 7)
        assert PCL5_CLUSTERS["negative_mood"] == (8, 14)
        assert PCL5_CLUSTERS["hyperarousal"] == (15, 20)


# ---------------------------------------------------------------------------
# _validate_item — 0-4 Likert
# ---------------------------------------------------------------------------


class TestValidateItemPcl5:
    def test_zero_accepted(self) -> None:
        assert _validate_item(1, 0) == 0

    def test_four_accepted(self) -> None:
        assert _validate_item(1, 4) == 4

    def test_true_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_item(1, True)

    def test_five_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_item(1, 5)

    def test_minus_1_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_item(1, -1)

    def test_error_mentions_item_index(self) -> None:
        with pytest.raises(InvalidResponseError, match="15"):
            _validate_item(15, 99)

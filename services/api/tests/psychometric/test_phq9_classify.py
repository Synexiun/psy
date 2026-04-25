"""Unit tests for _classify() pure helper in discipline.psychometric.scoring.phq9.

_classify(total) → Severity
  PHQ-9 uses Kroenke 2001 five-band severity scheme:
    ≤4  → "none"
    ≤9  → "mild"
    ≤14 → "moderate"
    ≤19 → "moderately_severe"  ← unique label in the package
    ≤27 → "severe"

  This is the most clinically critical classifier in the platform.
  Misclassification at the 10/11 boundary (mild→moderate) or 15/16
  boundary would affect intervention routing.  Boundary tests pin every
  cut-point against Kroenke 2001.

  PHQ9_SAFETY_ITEM_INDEX (item 9, zero-indexed as 8) is pinned here
  as well — its position is a clinical constant from the Kroenke 2001
  instrument, not an implementation choice.
"""

from __future__ import annotations

import pytest

from discipline.psychometric.scoring.phq9 import (
    PHQ9_SAFETY_ITEM_INDEX,
    PHQ9_SEVERITY_THRESHOLDS,
    InvalidResponseError,
    _classify,
)


# ---------------------------------------------------------------------------
# _classify — Kroenke 2001 five-band severity
# ---------------------------------------------------------------------------


class TestClassifyPhq9:
    def test_score_0_is_none(self) -> None:
        assert _classify(0) == "none"

    def test_score_4_is_none(self) -> None:
        assert _classify(4) == "none"

    def test_score_5_is_mild(self) -> None:
        assert _classify(5) == "mild"

    def test_score_9_is_mild(self) -> None:
        assert _classify(9) == "mild"

    def test_score_10_is_moderate(self) -> None:
        assert _classify(10) == "moderate"

    def test_score_14_is_moderate(self) -> None:
        assert _classify(14) == "moderate"

    def test_score_15_is_moderately_severe(self) -> None:
        # "moderately_severe" is unique to PHQ-9 in this package
        assert _classify(15) == "moderately_severe"

    def test_score_19_is_moderately_severe(self) -> None:
        assert _classify(19) == "moderately_severe"

    def test_score_20_is_severe(self) -> None:
        assert _classify(20) == "severe"

    def test_score_27_is_severe(self) -> None:
        # 27 is the maximum (9 items × 3)
        assert _classify(27) == "severe"

    def test_boundary_4_to_5(self) -> None:
        assert _classify(4) != _classify(5)

    def test_boundary_9_to_10(self) -> None:
        assert _classify(9) != _classify(10)

    def test_boundary_14_to_15(self) -> None:
        assert _classify(14) != _classify(15)

    def test_boundary_19_to_20(self) -> None:
        assert _classify(19) != _classify(20)

    def test_five_bands_in_threshold_table(self) -> None:
        assert len(PHQ9_SEVERITY_THRESHOLDS) == 5

    def test_score_28_raises(self) -> None:
        # 28 exceeds maximum — unreachable in practice but guard fires
        with pytest.raises(InvalidResponseError):
            _classify(28)


# ---------------------------------------------------------------------------
# Safety item index pinning
# ---------------------------------------------------------------------------


class TestPhq9SafetyItemIndex:
    def test_safety_item_index_is_8(self) -> None:
        # Item 9 in 1-indexed clinical language = index 8 zero-indexed
        assert PHQ9_SAFETY_ITEM_INDEX == 8

    def test_safety_item_index_is_zero_indexed(self) -> None:
        # Zero-indexed: index 8 → ninth element of a 9-item tuple
        assert PHQ9_SAFETY_ITEM_INDEX == 8
        items = tuple(range(9))
        assert items[PHQ9_SAFETY_ITEM_INDEX] == 8  # last item

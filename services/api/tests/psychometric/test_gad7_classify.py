"""Unit tests for _classify() pure helper in discipline.psychometric.scoring.gad7.

_classify(total) → Severity
  GAD-7 uses Spitzer 2006 four-band scheme:
    ≤4  → "none"
    ≤9  → "mild"
    ≤14 → "moderate"
    ≤21 → "severe"

  Note: GAD-7 has "none" not "normal" (unlike HADS) — the band labels match
  Spitzer 2006 verbatim.  The maximum is 21 (7 items × 3).
"""

from __future__ import annotations

import pytest

from discipline.psychometric.scoring.gad7 import (
    GAD7_SEVERITY_THRESHOLDS,
    InvalidResponseError,
    _classify,
)


# ---------------------------------------------------------------------------
# _classify — Spitzer 2006 four-band severity
# ---------------------------------------------------------------------------


class TestClassifyGad7:
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

    def test_score_15_is_severe(self) -> None:
        assert _classify(15) == "severe"

    def test_score_21_is_severe(self) -> None:
        # 21 is the maximum (7 items × 3)
        assert _classify(21) == "severe"

    def test_boundary_4_to_5(self) -> None:
        assert _classify(4) != _classify(5)

    def test_boundary_9_to_10(self) -> None:
        assert _classify(9) != _classify(10)

    def test_boundary_14_to_15(self) -> None:
        assert _classify(14) != _classify(15)

    def test_four_bands_in_threshold_table(self) -> None:
        assert len(GAD7_SEVERITY_THRESHOLDS) == 4

    def test_score_22_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _classify(22)

    def test_uses_none_not_normal(self) -> None:
        # Spitzer 2006 uses "none" — not "normal" like HADS
        assert _classify(0) == "none"
        assert _classify(0) != "normal"

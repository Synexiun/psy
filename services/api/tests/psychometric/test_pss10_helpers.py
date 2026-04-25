"""Unit tests for _reverse() and _classify() pure helpers in
discipline.psychometric.scoring.pss10.

_reverse(value) → int
  Inverts a 0-4 response using ``ITEM_MAX - value`` (not ITEM_MIN + ITEM_MAX - value).
  Since ITEM_MIN = 0, both formulas are equivalent here.  The explicit dependence
  on ITEM_MAX means a scale change requires only editing the constant.
  Mapping: 0↔4, 1↔3, 2↔2 (symmetric around the midpoint).

_classify(total) → Band
  PSS-10 uses a sequential if-cascade (ascending ≤) rather than a threshold
  tuple.  Three bands: ≤13 → "low", ≤26 → "moderate", else → "high".
  PSS-10 total range: 0-40 (10 items × 0-4 each, plus reverse items).
"""

from __future__ import annotations

import pytest

from discipline.psychometric.scoring.pss10 import (
    ITEM_MAX,
    ITEM_MIN,
    PSS10_LOW_UPPER,
    PSS10_MODERATE_UPPER,
    InvalidResponseError,
    _classify,
    _reverse,
)


# ---------------------------------------------------------------------------
# _reverse — 0-4 reflection
# ---------------------------------------------------------------------------


class TestReversePss10:
    def test_zero_flips_to_four(self) -> None:
        assert _reverse(0) == 4

    def test_four_flips_to_zero(self) -> None:
        assert _reverse(4) == 0

    def test_one_flips_to_three(self) -> None:
        assert _reverse(1) == 3

    def test_three_flips_to_one(self) -> None:
        assert _reverse(3) == 1

    def test_two_is_midpoint_unchanged(self) -> None:
        assert _reverse(2) == 2

    def test_double_flip_is_identity(self) -> None:
        for v in range(5):
            assert _reverse(_reverse(v)) == v

    def test_formula_is_item_max_minus_value(self) -> None:
        for v in range(5):
            assert _reverse(v) == ITEM_MAX - v

    def test_item_min_is_zero(self) -> None:
        assert ITEM_MIN == 0


# ---------------------------------------------------------------------------
# _classify — Cohen 1983 three-band classifier
# Thresholds: ≤13=low, ≤26=moderate, >26=high
# ---------------------------------------------------------------------------


class TestClassifyPss10:
    def test_score_0_is_low(self) -> None:
        assert _classify(0) == "low"

    def test_score_13_is_low(self) -> None:
        assert _classify(PSS10_LOW_UPPER) == "low"

    def test_score_14_is_moderate(self) -> None:
        assert _classify(PSS10_LOW_UPPER + 1) == "moderate"

    def test_score_26_is_moderate(self) -> None:
        assert _classify(PSS10_MODERATE_UPPER) == "moderate"

    def test_score_27_is_high(self) -> None:
        assert _classify(PSS10_MODERATE_UPPER + 1) == "high"

    def test_score_40_is_high(self) -> None:
        # 40 is the maximum (10 items × 4)
        assert _classify(40) == "high"

    def test_boundary_13_to_14(self) -> None:
        assert _classify(13) != _classify(14)

    def test_boundary_26_to_27(self) -> None:
        assert _classify(26) != _classify(27)

    def test_constants_match_expected_values(self) -> None:
        assert PSS10_LOW_UPPER == 13
        assert PSS10_MODERATE_UPPER == 26

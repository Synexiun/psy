"""Unit tests for _at_or_above_threshold() pure helper in
discipline.psychometric.trajectories.

_at_or_above_threshold(abs_delta, threshold) → bool
  Returns True if the absolute RCI delta should count as a reliable change.

  The critical behaviour is the IEEE 754 boundary case:
    RCI_THRESHOLDS["phq9"] = 5.2
    5.2 is NOT exactly representable in IEEE 754 float.
    A clinically "at threshold" delta like (18 - 12.8) computes to
    5.199999...2 in float, which would naively fail the '>= 5.2' check.
    math.isclose (rel_tol=1e-9) recovers the at-threshold case and
    correctly classifies it as reliable change.

  This is referenced in Docs/Whitepapers/02_Clinical_Evidence_Base.md:
  Jacobson & Truax 1991 — an RCI delta at exactly the threshold IS a
  reliable change.  Under-classifying it is a false negative.

RCI_THRESHOLDS (pinned from Docs/Technicals/13_Analytics_Reporting.md):
  phq9=5.2, gad7=4.6, who5=17.0, pss10=7.8, audit_c=2.0
"""

from __future__ import annotations

import pytest

from discipline.psychometric.trajectories import (
    RCI_THRESHOLDS,
    _at_or_above_threshold,
)


# ---------------------------------------------------------------------------
# _at_or_above_threshold — basic above/below
# ---------------------------------------------------------------------------


class TestAtOrAboveThresholdBasic:
    def test_clearly_above_returns_true(self) -> None:
        assert _at_or_above_threshold(10.0, 5.0) is True

    def test_clearly_below_returns_false(self) -> None:
        assert _at_or_above_threshold(3.0, 5.0) is False

    def test_zero_delta_below_any_positive_threshold(self) -> None:
        assert _at_or_above_threshold(0.0, 1.0) is False

    def test_equal_exact_returns_true(self) -> None:
        assert _at_or_above_threshold(5.0, 5.0) is True


# ---------------------------------------------------------------------------
# _at_or_above_threshold — IEEE 754 boundary (the critical clinical case)
# ---------------------------------------------------------------------------


class TestAtOrAboveThresholdFloatBoundary:
    def test_phq9_exact_decimal_5_2(self) -> None:
        # 18 - 12.8 = 5.2 exactly in decimal, but 5.1999...2 in float
        # Without math.isclose this would be False (false negative)
        delta = 18.0 - 12.8
        assert _at_or_above_threshold(delta, RCI_THRESHOLDS["phq9"]) is True

    def test_gad7_exact_decimal_4_6(self) -> None:
        # 10 - 5.4 = 4.6 in decimal, float representation may be 4.5999...
        delta = 10.0 - 5.4
        assert _at_or_above_threshold(delta, RCI_THRESHOLDS["gad7"]) is True

    def test_pss10_exact_decimal_7_8(self) -> None:
        delta = 20.0 - 12.2
        assert _at_or_above_threshold(delta, RCI_THRESHOLDS["pss10"]) is True

    def test_value_clearly_below_is_false_even_with_isclose(self) -> None:
        # 5.1 is not close to 5.2 (diff >> rel_tol=1e-9)
        assert _at_or_above_threshold(5.1, RCI_THRESHOLDS["phq9"]) is False


# ---------------------------------------------------------------------------
# RCI_THRESHOLDS — pinned from Jacobson & Truax 1991 / clinical doc
# ---------------------------------------------------------------------------


class TestRciThresholds:
    def test_phq9_threshold_is_5_2(self) -> None:
        assert RCI_THRESHOLDS["phq9"] == pytest.approx(5.2)

    def test_gad7_threshold_is_4_6(self) -> None:
        assert RCI_THRESHOLDS["gad7"] == pytest.approx(4.6)

    def test_who5_threshold_is_17(self) -> None:
        assert RCI_THRESHOLDS["who5"] == pytest.approx(17.0)

    def test_pss10_threshold_is_7_8(self) -> None:
        assert RCI_THRESHOLDS["pss10"] == pytest.approx(7.8)

    def test_audit_c_threshold_is_2(self) -> None:
        assert RCI_THRESHOLDS["audit_c"] == pytest.approx(2.0)

    def test_five_instruments_have_thresholds(self) -> None:
        assert len(RCI_THRESHOLDS) == 5

    def test_all_thresholds_positive(self) -> None:
        for instrument, threshold in RCI_THRESHOLDS.items():
            assert threshold > 0, f"{instrument} threshold must be > 0"

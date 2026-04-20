"""RCI trajectory tests.

Source: Jacobson, N.S. & Truax, P. (1991).  Clinical significance: A statistical
approach to defining meaningful change in psychotherapy research.  Journal of
Consulting and Clinical Psychology 59(1), 12–19.

Per-instrument thresholds are pinned in
Docs/Whitepapers/02_Clinical_Evidence_Base.md.
"""

from __future__ import annotations

import pytest

from discipline.psychometric.trajectories import (
    RCI_THRESHOLDS,
    TrajectoryPoint,
    compute_point,
)


# ---- Threshold values (Jacobson & Truax 1991) ------------------------------


def test_rci_thresholds_match_whitepaper() -> None:
    assert RCI_THRESHOLDS["phq9"] == pytest.approx(5.2)
    assert RCI_THRESHOLDS["gad7"] == pytest.approx(4.6)
    assert RCI_THRESHOLDS["who5"] == pytest.approx(17.0)
    assert RCI_THRESHOLDS["pss10"] == pytest.approx(7.8)
    assert RCI_THRESHOLDS["audit_c"] == pytest.approx(2.0)


# ---- Insufficient-data branch ---------------------------------------------


def test_missing_baseline_is_insufficient_data() -> None:
    point = compute_point("phq9", current=12.0, baseline=None)
    assert point.direction == "insufficient_data"
    assert point.delta is None


def test_unknown_instrument_is_insufficient_data() -> None:
    point = compute_point("fake_instrument", current=12.0, baseline=8.0)
    assert point.direction == "insufficient_data"
    assert point.rci_threshold is None


# ---- Lower-is-better instruments (PHQ-9, GAD-7, PSS-10, AUDIT-C) -----------


def test_phq9_decrease_above_threshold_is_improvement() -> None:
    point = compute_point("phq9", current=5.0, baseline=12.0)  # delta = -7 (|7| > 5.2)
    assert point.direction == "improvement"
    assert point.delta == pytest.approx(-7.0)


def test_phq9_increase_above_threshold_is_deterioration() -> None:
    point = compute_point("phq9", current=14.0, baseline=8.0)  # delta = +6 (|6| > 5.2)
    assert point.direction == "deterioration"
    assert point.delta == pytest.approx(6.0)


def test_phq9_delta_below_threshold_is_no_reliable_change() -> None:
    point = compute_point("phq9", current=11.0, baseline=8.0)  # |delta| = 3 < 5.2
    assert point.direction == "no_reliable_change"


def test_phq9_delta_exactly_at_threshold_counts_as_reliable() -> None:
    """Convention (and the code): ``abs_delta >= threshold`` is reliable
    change.  A change of exactly 5.2 on PHQ-9 counts as improvement/deterioration,
    not no-reliable-change.  If this behavior ever flips, the whitepaper
    threshold table must be re-derived.

    Uses the threshold constant directly so IEEE-754 rounding in arbitrary
    current/baseline math doesn't slide the delta below the threshold.
    """
    threshold = RCI_THRESHOLDS["phq9"]

    # delta = +threshold (increase on a lower-is-better scale) → deterioration
    point_up = compute_point("phq9", current=threshold, baseline=0.0)
    assert point_up.direction == "deterioration"

    # delta = -threshold → improvement
    point_down = compute_point("phq9", current=0.0, baseline=threshold)
    assert point_down.direction == "improvement"


# ---- Higher-is-better instruments (WHO-5) ---------------------------------


def test_who5_increase_above_threshold_is_improvement() -> None:
    point = compute_point("who5", current=60.0, baseline=40.0)  # delta = +20 > 17
    assert point.direction == "improvement"


def test_who5_decrease_above_threshold_is_deterioration() -> None:
    point = compute_point("who5", current=25.0, baseline=50.0)  # delta = -25, |25| > 17
    assert point.direction == "deterioration"


def test_who5_small_delta_is_no_reliable_change() -> None:
    point = compute_point("who5", current=55.0, baseline=45.0)  # |10| < 17
    assert point.direction == "no_reliable_change"


# ---- Result dataclass invariants ------------------------------------------


def test_trajectory_point_is_frozen() -> None:
    point = compute_point("phq9", current=5.0, baseline=12.0)
    with pytest.raises(AttributeError):
        point.direction = "improvement"  # type: ignore[misc]


def test_trajectory_point_echoes_inputs() -> None:
    point = compute_point("gad7", current=3.0, baseline=10.0)
    assert point.instrument == "gad7"
    assert point.current == pytest.approx(3.0)
    assert point.baseline == pytest.approx(10.0)
    assert point.rci_threshold == pytest.approx(4.6)


# ---- Float-precision boundary (math.isclose guard) -------------------------
# The thresholds 5.2, 4.6, 7.8 are not representable exactly in IEEE 754.
# Without math.isclose, a "clean decimal" delta that equals the threshold
# in human arithmetic (e.g. 18.0 - 12.8 == 5.2) evaluates to
# -5.199999999999999 in float, which would naively be < 5.2 and produce
# a false no_reliable_change classification.  Each test below exercises the
# real-world clinical scenario that motivated the fix.


def test_phq9_float_precision_improvement() -> None:
    # 18.0 - 12.8 = 5.2 in human arithmetic; float gives 5.199999999999999.
    # Without math.isclose this would be no_reliable_change.
    point = compute_point("phq9", current=12.8, baseline=18.0)
    assert point.direction == "improvement"


def test_phq9_float_precision_deterioration() -> None:
    # 12.8 - 18.0 = -5.2 → |delta| = 5.2 → deterioration.
    point = compute_point("phq9", current=18.0, baseline=12.8)
    assert point.direction == "deterioration"


def test_gad7_float_precision_improvement() -> None:
    # GAD-7 threshold = 4.6; 14.6 - 10.0 = 4.6 exact, but float subtraction may drift.
    point = compute_point("gad7", current=10.0, baseline=14.6)
    assert point.direction == "improvement"


def test_pss10_float_precision_improvement() -> None:
    # PSS-10 threshold = 7.8; 17.8 - 10.0 = 7.8.
    point = compute_point("pss10", current=10.0, baseline=17.8)
    assert point.direction == "improvement"


def test_audit_c_float_precision_improvement() -> None:
    # AUDIT-C threshold = 2.0 (exact in float); lower-is-better.
    point = compute_point("audit_c", current=4.0, baseline=6.0)
    assert point.direction == "improvement"


def test_audit_c_lower_is_better_direction() -> None:
    # Verify AUDIT-C is treated as lower-is-better (same as PHQ-9, GAD-7).
    point_better = compute_point("audit_c", current=2.0, baseline=7.0)
    point_worse = compute_point("audit_c", current=7.0, baseline=2.0)
    assert point_better.direction == "improvement"
    assert point_worse.direction == "deterioration"


def test_who5_float_precision_improvement() -> None:
    # WHO-5 threshold = 17.0; delta = 57.0 - 40.0 = 17.0 exactly.
    point = compute_point("who5", current=57.0, baseline=40.0)
    assert point.direction == "improvement"


def test_who5_float_precision_boundary_no_change() -> None:
    # |delta| = 16 < 17 → no_reliable_change; verifies the boundary is tight.
    point = compute_point("who5", current=56.0, baseline=40.0)
    assert point.direction == "no_reliable_change"


# ---- All-instruments threshold constant coverage ----------------------------


def test_all_threshold_instruments_have_constants() -> None:
    for instrument in ("phq9", "gad7", "who5", "pss10", "audit_c"):
        assert instrument in RCI_THRESHOLDS, f"Missing RCI threshold for {instrument}"
        assert RCI_THRESHOLDS[instrument] > 0


def test_threshold_count() -> None:
    assert len(RCI_THRESHOLDS) == 5


# ---- rci_threshold field on result ------------------------------------------


def test_rci_threshold_echoed_on_result() -> None:
    for instrument, expected in RCI_THRESHOLDS.items():
        point = compute_point(instrument, current=5.0, baseline=20.0)
        assert point.rci_threshold == pytest.approx(expected), instrument


def test_rci_threshold_none_for_unknown() -> None:
    point = compute_point("spin", current=30.0, baseline=50.0)
    assert point.rci_threshold is None

"""Reliable change index (RCI) computation.

Reference: Jacobson, N.S. & Truax, P. (1991).  Clinical significance: A statistical
approach to defining meaningful change in psychotherapy research.  Journal of
Consulting and Clinical Psychology 59(1), 12–19.

RCI thresholds per instrument (from Docs/Whitepapers/02_Clinical_Evidence_Base.md):

+------------+-----------------------------------+
| Instrument | |Δ| that counts as reliable change|
+------------+-----------------------------------+
| PHQ-9      | ≥ 5.2                             |
| GAD-7      | ≥ 4.6                             |
| WHO-5      | ≥ 17                              |
| PSS-10     | ≥ 7.8                             |
| AUDIT-C    | ≥ 2                               |
+------------+-----------------------------------+

``None`` is returned when the instrument has no validated RCI threshold or when
the baseline is missing.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

RCI_THRESHOLDS: dict[str, float] = {
    "phq9": 5.2,
    "gad7": 4.6,
    "who5": 17.0,
    "pss10": 7.8,
    "audit_c": 2.0,
}

# Float tolerance for at-threshold comparisons.  Several RCI
# thresholds (5.2, 4.6, 7.8) are not representable exactly in IEEE
# 754 — so a clinically "at threshold" delta computed from clean
# decimals like 12.8 - 18 produces -5.199999...2 in float, which
# would naively classify as no_reliable_change.  ``math.isclose``
# with the default tolerances treats these as equal, recovering the
# clinically intended at-cutoff = improvement / deterioration
# semantics from Jacobson & Truax 1991.
def _at_or_above_threshold(abs_delta: float, threshold: float) -> bool:
    """True iff |Δ| should count as reliable change.

    Uses ``math.isclose`` for the boundary so an exact-decimal at-
    threshold delta isn't lost to float representation error.  The
    tolerance is the ``math.isclose`` default (rel_tol=1e-9), which
    is well below any clinically meaningful precision."""
    return abs_delta >= threshold or math.isclose(abs_delta, threshold)


@dataclass(frozen=True)
class TrajectoryPoint:
    instrument: str
    current: float
    baseline: float | None
    delta: float | None
    rci_threshold: float | None
    direction: Literal["improvement", "deterioration", "no_reliable_change", "insufficient_data"]


def compute_point(instrument: str, current: float, baseline: float | None) -> TrajectoryPoint:
    threshold = RCI_THRESHOLDS.get(instrument)
    if baseline is None or threshold is None:
        return TrajectoryPoint(
            instrument=instrument,
            current=current,
            baseline=baseline,
            delta=None,
            rci_threshold=threshold,
            direction="insufficient_data",
        )
    delta = current - baseline
    # For all included instruments except WHO-5 a decrease is improvement.
    lower_is_better = instrument in {"phq9", "gad7", "pss10", "audit_c"}
    abs_delta = abs(delta)
    if not _at_or_above_threshold(abs_delta, threshold):
        direction: Literal[
            "improvement", "deterioration", "no_reliable_change", "insufficient_data"
        ] = "no_reliable_change"
    elif lower_is_better:
        direction = "improvement" if delta < 0 else "deterioration"
    else:
        direction = "improvement" if delta > 0 else "deterioration"
    return TrajectoryPoint(
        instrument=instrument,
        current=current,
        baseline=baseline,
        delta=delta,
        rci_threshold=threshold,
        direction=direction,
    )


__all__ = ["RCI_THRESHOLDS", "TrajectoryPoint", "compute_point"]

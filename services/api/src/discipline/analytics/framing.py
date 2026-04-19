"""Protective framing rules P1–P6 for user-facing analytics.

Authority: Docs/Business/02_Product_Requirements.md §F-14 and
Docs/Whitepapers/04_Safety_Framework.md.

P1.  No isolated raw scores.  Pair every score with a contextual label
     and, when available, the reliable-change direction vs. baseline.
P2.  A lapse never appears as a "streak reset" headline.  Resilience streak
     (urges handled) is always co-presented with days-clean.
P3.  Trend text uses non-stigmatizing language: "softer", "steadier", "heavier";
     never "better/worse" as a moral frame.
P4.  No predictions about future relapse in user-facing copy.  (ML predictions
     are used to schedule interventions, not to narrate to the user.)
P5.  If the last 7d data is sparse (<3 check-ins), suppress trend deltas and
     show "not enough data yet" rather than a misleading line.
P6.  Safety-positive signals (PHQ-9 item 9, C-SSRS) are NEVER summarized as
     "trending".  They route to the T3 safety path; analytics only records
     that the signal occurred.

This module is PURE: no I/O, no database, no HTTP.  Callers assemble inputs
from :mod:`discipline.psychometric.scoring` / :mod:`discipline.psychometric.trajectories`
and render the returned dataclasses.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from discipline.psychometric.trajectories import TrajectoryPoint

# ---- Public taxonomy --------------------------------------------------------

Tone = Literal["calm", "neutral", "alert"]
DirectionLabel = Literal["softer", "steadier", "heavier"]
SparseReason = Literal["insufficient_data"]


# ---- Exceptions -------------------------------------------------------------


class SafetyPositiveBypassError(RuntimeError):
    """Raised when caller attempts to frame a trend for a safety-positive signal.

    P6 contract: safety-positive signals (e.g. PHQ-9 item 9 = 1/2/3) route to
    the T3 safety flow.  They never appear in user-facing "trending" copy.
    A caller that reaches this function without first branching on the safety
    flag has a structural bug.  Failing loudly is intentional — silently
    folding the signal into a neutral "no_reliable_change" narrative would
    mask a clinical defect.
    """


# ---- Dataclasses ------------------------------------------------------------


@dataclass(frozen=True)
class FramedScore:
    """A single-snapshot severity framing (today's state, not trend)."""

    instrument: str
    display: str
    tone: Tone
    suppressed_reason: str | None = None


@dataclass(frozen=True)
class FramedTrend:
    """Change-over-time framing that respects P1, P3, P5, P6."""

    instrument: str
    direction_label: DirectionLabel | None
    narrative: str
    tone: Tone
    suppressed_reason: SparseReason | None = None


@dataclass(frozen=True)
class FramedResilience:
    """P2: resilience streak never stands alone; always co-presented."""

    resilience_days: int
    days_clean: int
    display: str
    tone: Tone


# ---- Severity framing (per-instrument) --------------------------------------


def frame_phq9(total: int, baseline: int | None) -> FramedScore:
    """P1 + P3: never surface the raw number without a contextual label.

    ``baseline`` is accepted for signature symmetry but is not used in the
    snapshot framing; baseline-relative narratives belong to
    :func:`frame_trend` and flow through :class:`TrajectoryPoint`.
    """
    del baseline  # reserved — see docstring
    if total <= 4:
        return FramedScore(instrument="phq9", display="low", tone="calm")
    if total <= 9:
        return FramedScore(instrument="phq9", display="mild", tone="neutral")
    if total <= 14:
        return FramedScore(instrument="phq9", display="moderate", tone="neutral")
    return FramedScore(instrument="phq9", display="noticeable", tone="alert")


def frame_gad7(total: int, baseline: int | None) -> FramedScore:
    """Spitzer 2006 bands, mapped to the same three-tone vocabulary as PHQ-9."""
    del baseline
    if total <= 4:
        return FramedScore(instrument="gad7", display="low", tone="calm")
    if total <= 9:
        return FramedScore(instrument="gad7", display="mild", tone="neutral")
    if total <= 14:
        return FramedScore(instrument="gad7", display="moderate", tone="neutral")
    return FramedScore(instrument="gad7", display="noticeable", tone="alert")


# ---- Trend framing (instrument-agnostic) ------------------------------------


_DIRECTION_TO_LABEL: dict[str, DirectionLabel] = {
    "improvement": "softer",
    "deterioration": "heavier",
    "no_reliable_change": "steadier",
}

_DIRECTION_TO_TONE: dict[str, Tone] = {
    "improvement": "calm",
    "deterioration": "alert",
    "no_reliable_change": "neutral",
}


def frame_trend(
    point: TrajectoryPoint,
    *,
    has_safety_positive: bool = False,
    n_checkins_7d: int | None = None,
) -> FramedTrend:
    """Turn a :class:`TrajectoryPoint` into user-facing trend copy.

    P5: If ``n_checkins_7d`` is provided and sparse, the trend is suppressed
    with a "not enough data yet" narrative regardless of the computed direction.

    P6: If ``has_safety_positive`` is True, raises :class:`SafetyPositiveBypassError`.
    The caller must branch on safety-positive *before* asking for a trend.
    """
    if has_safety_positive:
        raise SafetyPositiveBypassError(
            f"refusing to render trend for {point.instrument}: safety-positive "
            "signals route to T3, not analytics narration"
        )

    if n_checkins_7d is not None and sparse(n_checkins_7d):
        return FramedTrend(
            instrument=point.instrument,
            direction_label=None,
            narrative="not enough data yet",
            tone="neutral",
            suppressed_reason="insufficient_data",
        )

    if point.direction == "insufficient_data":
        return FramedTrend(
            instrument=point.instrument,
            direction_label=None,
            narrative="not enough data yet",
            tone="neutral",
            suppressed_reason="insufficient_data",
        )

    label = _DIRECTION_TO_LABEL[point.direction]
    tone = _DIRECTION_TO_TONE[point.direction]
    return FramedTrend(
        instrument=point.instrument,
        direction_label=label,
        narrative=f"things feel {label} than your baseline",
        tone=tone,
    )


# ---- Resilience (P2) --------------------------------------------------------


def frame_resilience(resilience_days: int, days_clean: int) -> FramedResilience:
    """P2: resilience streak (urges handled) MUST be co-presented with days-clean.

    A lapse resets days-clean but never resets resilience — the
    ``streak_state.resilience_days`` column is monotonically non-decreasing
    (DB trigger enforces).  This framer is the headline-copy contract that
    refuses to ever show resilience in isolation.
    """
    if resilience_days < 0 or days_clean < 0:
        raise ValueError("resilience_days and days_clean must be non-negative")
    display = f"{resilience_days} urges handled · {days_clean} days clean"
    tone: Tone = "calm" if days_clean > 0 else "neutral"
    return FramedResilience(
        resilience_days=resilience_days,
        days_clean=days_clean,
        display=display,
        tone=tone,
    )


# ---- P5 helper --------------------------------------------------------------


def sparse(n_checkins_7d: int) -> bool:
    """P5: fewer than 3 check-ins in 7d is too sparse to narrate a trend."""
    return n_checkins_7d < 3


__all__ = [
    "DirectionLabel",
    "FramedResilience",
    "FramedScore",
    "FramedTrend",
    "SafetyPositiveBypassError",
    "SparseReason",
    "Tone",
    "frame_gad7",
    "frame_phq9",
    "frame_resilience",
    "frame_trend",
    "sparse",
]

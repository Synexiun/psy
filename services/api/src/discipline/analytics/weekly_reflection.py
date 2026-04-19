"""Weekly reflection composition service.

Combines the primitives in :mod:`discipline.analytics.framing` and
:mod:`discipline.psychometric.trajectories` into a single
:class:`WeeklyReflection` payload that the mobile / email renderer consumes.

This module is PURE: the input dataclass carries everything the service needs;
repository / DB access belongs in the calling router.  Keeping it pure lets the
tests verify the P1–P6 composition behavior exhaustively without mocks.

Composition rules:

- P6 takes precedence over everything else.  If ``safety_positive_this_week``
  is set, the returned reflection has ``safety_routed=True`` and every
  analytics field is ``None``.  The UI layer MUST render the T3 safety handoff
  in that case — not "you had a tough week".  Resilience is deliberately
  omitted too: showing "42 urges handled" alongside a safety event is a tonal
  mismatch documented in the framing whitepaper.

- P5 applies uniformly.  Sparse data (``<3`` check-ins in 7d) suppresses every
  trend into an "insufficient_data" state; severity framing is still shown
  because a raw score is a snapshot, not a trend.

- P2 is always honored when a reflection is rendered at all.  Resilience
  streak and days-clean are co-presented in a single :class:`FramedResilience`.

- Severity framing (:class:`FramedScore`) is instrument-specific and only
  emitted for instruments we have severity bands for (PHQ-9, GAD-7).  Other
  instruments appear only as trends.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from discipline.psychometric.trajectories import compute_point

from .framing import (
    FramedResilience,
    FramedScore,
    FramedTrend,
    frame_gad7,
    frame_phq9,
    frame_resilience,
    frame_trend,
)


@dataclass(frozen=True)
class WeeklyReflectionInput:
    """Repository-sourced snapshot for the week.

    All fields are pre-fetched by the router; the service does no I/O.
    A ``None`` current score means the user did not complete that instrument
    this week.  A ``None`` baseline means no prior reference value — trends
    fall back to "insufficient_data".
    """

    user_id: str
    week_ending: date
    phq9_current: int | None = None
    phq9_baseline: int | None = None
    gad7_current: int | None = None
    gad7_baseline: int | None = None
    who5_current: float | None = None
    who5_baseline: float | None = None
    pss10_current: float | None = None
    pss10_baseline: float | None = None
    resilience_days: int = 0
    days_clean: int = 0
    n_checkins_7d: int = 0
    safety_positive_this_week: bool = False


@dataclass(frozen=True)
class WeeklyReflection:
    """Framed composite — never contains raw scores in a user-visible form.

    When ``safety_routed`` is ``True``, the UI layer suppresses this payload
    entirely and renders the T3 safety flow instead; the other fields are
    guaranteed to be ``None`` in that case (contract, not coincidence).
    """

    user_id: str
    week_ending: date
    safety_routed: bool
    severity_phq9: FramedScore | None
    severity_gad7: FramedScore | None
    trend_phq9: FramedTrend | None
    trend_gad7: FramedTrend | None
    trend_who5: FramedTrend | None
    trend_pss10: FramedTrend | None
    resilience: FramedResilience | None


def _build_trend(
    instrument: str,
    current: float | None,
    baseline: float | None,
    n_checkins_7d: int,
) -> FramedTrend | None:
    """Only emit a trend when we have a current value to plot against a
    baseline.  ``None`` current = user didn't take the instrument this week,
    which is quieter than rendering an "insufficient_data" chip for every
    instrument the user happens not to be on."""
    if current is None:
        return None
    return frame_trend(
        compute_point(instrument, current=current, baseline=baseline),
        n_checkins_7d=n_checkins_7d,
    )


def compose(payload: WeeklyReflectionInput) -> WeeklyReflection:
    """Compose a P1–P6-compliant weekly reflection from pre-fetched inputs."""
    if payload.safety_positive_this_week:
        return WeeklyReflection(
            user_id=payload.user_id,
            week_ending=payload.week_ending,
            safety_routed=True,
            severity_phq9=None,
            severity_gad7=None,
            trend_phq9=None,
            trend_gad7=None,
            trend_who5=None,
            trend_pss10=None,
            resilience=None,
        )

    severity_phq9 = (
        frame_phq9(payload.phq9_current, baseline=payload.phq9_baseline)
        if payload.phq9_current is not None
        else None
    )
    severity_gad7 = (
        frame_gad7(payload.gad7_current, baseline=payload.gad7_baseline)
        if payload.gad7_current is not None
        else None
    )

    return WeeklyReflection(
        user_id=payload.user_id,
        week_ending=payload.week_ending,
        safety_routed=False,
        severity_phq9=severity_phq9,
        severity_gad7=severity_gad7,
        trend_phq9=_build_trend(
            "phq9", payload.phq9_current, payload.phq9_baseline, payload.n_checkins_7d
        ),
        trend_gad7=_build_trend(
            "gad7", payload.gad7_current, payload.gad7_baseline, payload.n_checkins_7d
        ),
        trend_who5=_build_trend(
            "who5", payload.who5_current, payload.who5_baseline, payload.n_checkins_7d
        ),
        trend_pss10=_build_trend(
            "pss10",
            payload.pss10_current,
            payload.pss10_baseline,
            payload.n_checkins_7d,
        ),
        resilience=frame_resilience(
            resilience_days=payload.resilience_days,
            days_clean=payload.days_clean,
        ),
    )


__all__ = [
    "WeeklyReflection",
    "WeeklyReflectionInput",
    "compose",
]

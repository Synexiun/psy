"""Assessment scheduler.

Invariants (from Docs/Whitepapers/02_Clinical_Evidence_Base.md §Administration):
- NEVER administer during an active urge window (intervention.signal.urge_active)
- At most one instrument per session; at most one full battery per day.
- PHQ-9 baseline at onboarding, then at most every 14 days.
- GAD-7 alongside PHQ-9 when the wellbeing probe indicates.
- C-SSRS triggered only by signal, never on schedule.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from discipline.shared.i18n import Locale


@dataclass(frozen=True)
class ScheduleDecision:
    should_offer: bool
    reason: str
    instrument: str | None
    not_before: datetime | None


MIN_INTERVAL_DAYS: dict[str, int] = {
    "phq9": 14,
    "gad7": 14,
    "who5": 14,
    "audit_c": 30,
    "pss10": 30,
    "dtcq8": 14,
    "urica": 30,
}


def decide(
    instrument: str,
    last_taken_at: datetime | None,
    urge_active: bool,
    _locale: Locale,
    now: datetime | None = None,
) -> ScheduleDecision:
    now = now or datetime.utcnow()
    if urge_active:
        return ScheduleDecision(
            should_offer=False,
            reason="urge_window_active",
            instrument=instrument,
            not_before=None,
        )
    interval = MIN_INTERVAL_DAYS.get(instrument)
    if interval is None:
        return ScheduleDecision(
            should_offer=False,
            reason="unknown_instrument",
            instrument=instrument,
            not_before=None,
        )
    if last_taken_at is not None:
        earliest = last_taken_at + timedelta(days=interval)
        if now < earliest:
            return ScheduleDecision(
                should_offer=False,
                reason="too_soon",
                instrument=instrument,
                not_before=earliest,
            )
    return ScheduleDecision(
        should_offer=True,
        reason="ok",
        instrument=instrument,
        not_before=None,
    )


__all__ = ["MIN_INTERVAL_DAYS", "ScheduleDecision", "decide"]

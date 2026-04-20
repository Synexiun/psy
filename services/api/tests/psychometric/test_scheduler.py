"""Tests for discipline.psychometric.scheduler.decide().

Invariants from Docs/Whitepapers/02_Clinical_Evidence_Base.md §Administration:
- Never administer during an active urge window.
- At most one instrument per session; at most one full battery per day.
- Per-instrument minimum intervals (PHQ-9/GAD-7/WHO-5: 14 days, AUDIT-C/PSS-10/URICA: 30 days).
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from discipline.psychometric.scheduler import (
    MIN_INTERVAL_DAYS,
    ScheduleDecision,
    decide,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_NOW = datetime(2026, 1, 15, 9, 0, 0)  # fixed reference timestamp


def _decide(
    instrument: str = "phq9",
    *,
    last_taken_at: datetime | None = None,
    urge_active: bool = False,
    now: datetime = _NOW,
) -> ScheduleDecision:
    return decide(
        instrument=instrument,
        last_taken_at=last_taken_at,
        urge_active=urge_active,
        _locale="en",
        now=now,
    )


# ---------------------------------------------------------------------------
# TestUrgeWindowBlocking
# ---------------------------------------------------------------------------


class TestUrgeWindowBlocking:
    def test_urge_active_blocks_known_instrument(self) -> None:
        d = _decide("phq9", urge_active=True)
        assert d.should_offer is False

    def test_urge_active_reason(self) -> None:
        d = _decide("phq9", urge_active=True)
        assert d.reason == "urge_window_active"

    def test_urge_active_instrument_echoed(self) -> None:
        d = _decide("gad7", urge_active=True)
        assert d.instrument == "gad7"

    def test_urge_active_not_before_is_none(self) -> None:
        d = _decide("phq9", urge_active=True)
        assert d.not_before is None

    def test_urge_active_overrides_elapsed_interval(self) -> None:
        # Even if the interval has fully elapsed, urge blocks the offer.
        old = _NOW - timedelta(days=30)
        d = _decide("phq9", last_taken_at=old, urge_active=True)
        assert d.should_offer is False
        assert d.reason == "urge_window_active"

    def test_urge_active_overrides_first_time(self) -> None:
        # First-time user (no last_taken_at) still blocked by urge.
        d = _decide("phq9", last_taken_at=None, urge_active=True)
        assert d.should_offer is False

    def test_urge_active_blocks_all_known_instruments(self) -> None:
        for instrument in MIN_INTERVAL_DAYS:
            d = _decide(instrument, urge_active=True)
            assert d.should_offer is False, f"{instrument} should be blocked by urge"


# ---------------------------------------------------------------------------
# TestUnknownInstrument
# ---------------------------------------------------------------------------


class TestUnknownInstrument:
    def test_unknown_instrument_not_offered(self) -> None:
        d = _decide("nonexistent_scale")
        assert d.should_offer is False

    def test_unknown_instrument_reason(self) -> None:
        d = _decide("nonexistent_scale")
        assert d.reason == "unknown_instrument"

    def test_unknown_instrument_echoed(self) -> None:
        d = _decide("nonexistent_scale")
        assert d.instrument == "nonexistent_scale"

    def test_unknown_instrument_not_before_is_none(self) -> None:
        d = _decide("nonexistent_scale")
        assert d.not_before is None

    def test_spin_not_in_min_interval_returns_unknown(self) -> None:
        # SPIN is not in MIN_INTERVAL_DAYS — scheduler returns unknown_instrument.
        d = _decide("spin")
        assert d.reason == "unknown_instrument"


# ---------------------------------------------------------------------------
# TestFirstTimeAdministration
# ---------------------------------------------------------------------------


class TestFirstTimeAdministration:
    def test_first_time_phq9_offered(self) -> None:
        d = _decide("phq9", last_taken_at=None)
        assert d.should_offer is True

    def test_first_time_reason_ok(self) -> None:
        d = _decide("phq9", last_taken_at=None)
        assert d.reason == "ok"

    def test_first_time_not_before_is_none(self) -> None:
        d = _decide("phq9", last_taken_at=None)
        assert d.not_before is None

    def test_first_time_all_known_instruments(self) -> None:
        for instrument in MIN_INTERVAL_DAYS:
            d = _decide(instrument, last_taken_at=None)
            assert d.should_offer is True, f"{instrument} first-time should be offered"

    def test_first_time_instrument_echoed(self) -> None:
        d = _decide("audit_c", last_taken_at=None)
        assert d.instrument == "audit_c"


# ---------------------------------------------------------------------------
# TestIntervalEnforcement — too_soon
# ---------------------------------------------------------------------------


class TestIntervalTooSoon:
    def test_phq9_too_soon_one_day_after(self) -> None:
        last = _NOW - timedelta(days=1)
        d = _decide("phq9", last_taken_at=last)
        assert d.should_offer is False

    def test_phq9_too_soon_reason(self) -> None:
        last = _NOW - timedelta(days=1)
        d = _decide("phq9", last_taken_at=last)
        assert d.reason == "too_soon"

    def test_phq9_too_soon_13_days(self) -> None:
        last = _NOW - timedelta(days=13)
        d = _decide("phq9", last_taken_at=last)
        assert d.should_offer is False

    def test_phq9_not_before_equals_earliest(self) -> None:
        last = _NOW - timedelta(days=1)
        d = _decide("phq9", last_taken_at=last)
        expected = last + timedelta(days=MIN_INTERVAL_DAYS["phq9"])
        assert d.not_before == expected

    def test_audit_c_too_soon_29_days(self) -> None:
        last = _NOW - timedelta(days=29)
        d = _decide("audit_c", last_taken_at=last)
        assert d.should_offer is False

    def test_urica_too_soon_15_days(self) -> None:
        last = _NOW - timedelta(days=15)
        d = _decide("urica", last_taken_at=last)
        assert d.should_offer is False

    def test_instrument_echoed_on_too_soon(self) -> None:
        last = _NOW - timedelta(days=1)
        d = _decide("gad7", last_taken_at=last)
        assert d.instrument == "gad7"


# ---------------------------------------------------------------------------
# TestIntervalEnforcement — ok (elapsed)
# ---------------------------------------------------------------------------


class TestIntervalElapsed:
    def test_phq9_exactly_at_14_days_offered(self) -> None:
        last = _NOW - timedelta(days=14)
        d = _decide("phq9", last_taken_at=last)
        assert d.should_offer is True

    def test_phq9_reason_ok(self) -> None:
        last = _NOW - timedelta(days=14)
        d = _decide("phq9", last_taken_at=last)
        assert d.reason == "ok"

    def test_phq9_not_before_none_when_ok(self) -> None:
        last = _NOW - timedelta(days=14)
        d = _decide("phq9", last_taken_at=last)
        assert d.not_before is None

    def test_phq9_past_due_15_days_offered(self) -> None:
        last = _NOW - timedelta(days=15)
        d = _decide("phq9", last_taken_at=last)
        assert d.should_offer is True

    def test_gad7_14_days_elapsed_offered(self) -> None:
        last = _NOW - timedelta(days=14)
        d = _decide("gad7", last_taken_at=last)
        assert d.should_offer is True

    def test_audit_c_exactly_30_days_offered(self) -> None:
        last = _NOW - timedelta(days=30)
        d = _decide("audit_c", last_taken_at=last)
        assert d.should_offer is True

    def test_pss10_exactly_30_days_offered(self) -> None:
        last = _NOW - timedelta(days=30)
        d = _decide("pss10", last_taken_at=last)
        assert d.should_offer is True

    def test_urica_exactly_30_days_offered(self) -> None:
        last = _NOW - timedelta(days=30)
        d = _decide("urica", last_taken_at=last)
        assert d.should_offer is True

    def test_dtcq8_exactly_14_days_offered(self) -> None:
        last = _NOW - timedelta(days=14)
        d = _decide("dtcq8", last_taken_at=last)
        assert d.should_offer is True


# ---------------------------------------------------------------------------
# TestMinIntervalDays — constants
# ---------------------------------------------------------------------------


class TestMinIntervalConstants:
    def test_phq9_interval_14(self) -> None:
        assert MIN_INTERVAL_DAYS["phq9"] == 14

    def test_gad7_interval_14(self) -> None:
        assert MIN_INTERVAL_DAYS["gad7"] == 14

    def test_who5_interval_14(self) -> None:
        assert MIN_INTERVAL_DAYS["who5"] == 14

    def test_audit_c_interval_30(self) -> None:
        assert MIN_INTERVAL_DAYS["audit_c"] == 30

    def test_pss10_interval_30(self) -> None:
        assert MIN_INTERVAL_DAYS["pss10"] == 30

    def test_urica_interval_30(self) -> None:
        assert MIN_INTERVAL_DAYS["urica"] == 30

    def test_dtcq8_interval_14(self) -> None:
        assert MIN_INTERVAL_DAYS["dtcq8"] == 14


# ---------------------------------------------------------------------------
# TestScheduleDecisionShape
# ---------------------------------------------------------------------------


class TestScheduleDecisionShape:
    def test_result_is_frozen(self) -> None:
        d = _decide("phq9")
        with pytest.raises((AttributeError, TypeError)):
            d.should_offer = False  # type: ignore[misc]

    def test_result_is_schedule_decision(self) -> None:
        d = _decide("phq9")
        assert isinstance(d, ScheduleDecision)

    def test_should_offer_is_bool(self) -> None:
        d = _decide("phq9")
        assert isinstance(d.should_offer, bool)

    def test_reason_is_str(self) -> None:
        d = _decide("phq9")
        assert isinstance(d.reason, str)


# ---------------------------------------------------------------------------
# TestEdgeCases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_exactly_one_second_before_eligible(self) -> None:
        interval = MIN_INTERVAL_DAYS["phq9"]
        last = _NOW - timedelta(days=interval) + timedelta(seconds=1)
        d = _decide("phq9", last_taken_at=last)
        assert d.should_offer is False
        assert d.reason == "too_soon"

    def test_exactly_one_second_after_eligible(self) -> None:
        interval = MIN_INTERVAL_DAYS["phq9"]
        last = _NOW - timedelta(days=interval) - timedelta(seconds=1)
        d = _decide("phq9", last_taken_at=last)
        assert d.should_offer is True

    def test_empty_string_instrument_unknown(self) -> None:
        d = _decide("")
        assert d.reason == "unknown_instrument"

    def test_urge_false_first_time_offered(self) -> None:
        d = _decide("phq9", urge_active=False, last_taken_at=None)
        assert d.should_offer is True

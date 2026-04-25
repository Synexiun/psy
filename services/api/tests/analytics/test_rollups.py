"""Tests for discipline.analytics.rollups — DailyRollup dataclass and stub guard.

Covers:
- DailyRollup can be constructed with all fields
- DailyRollup is a frozen dataclass
- rollup_version defaults to "1.0.0"
- mood_mean and sleep_hours accept None
- wellbeing_state accepts None
- build_for_user raises NotImplementedError (stub contract)
- __all__ exports are present
"""

from __future__ import annotations

import asyncio
from datetime import date

import pytest

from discipline.analytics.rollups import DailyRollup, build_for_user


class TestDailyRollup:
    def test_can_be_constructed(self) -> None:
        r = DailyRollup(
            user_id="u-1",
            day=date(2026, 4, 25),
            urges_logged=3,
            urges_handled=2,
            tools_used=5,
            mood_mean=6.5,
            sleep_hours=7.0,
            wellbeing_state="moderate",
        )
        assert r.user_id == "u-1"

    def test_frozen(self) -> None:
        r = DailyRollup(
            user_id="u",
            day=date(2026, 4, 25),
            urges_logged=0,
            urges_handled=0,
            tools_used=0,
            mood_mean=None,
            sleep_hours=None,
            wellbeing_state=None,
        )
        with pytest.raises((AttributeError, TypeError)):
            r.urges_logged = 99  # type: ignore[misc]

    def test_rollup_version_defaults_to_1_0_0(self) -> None:
        r = DailyRollup(
            user_id="u",
            day=date(2026, 4, 25),
            urges_logged=0,
            urges_handled=0,
            tools_used=0,
            mood_mean=None,
            sleep_hours=None,
            wellbeing_state=None,
        )
        assert r.rollup_version == "1.0.0"

    def test_mood_mean_accepts_none(self) -> None:
        r = DailyRollup(
            user_id="u",
            day=date(2026, 4, 25),
            urges_logged=0,
            urges_handled=0,
            tools_used=0,
            mood_mean=None,
            sleep_hours=None,
            wellbeing_state=None,
        )
        assert r.mood_mean is None

    def test_sleep_hours_accepts_float(self) -> None:
        r = DailyRollup(
            user_id="u",
            day=date(2026, 4, 25),
            urges_logged=0,
            urges_handled=0,
            tools_used=0,
            mood_mean=None,
            sleep_hours=8.5,
            wellbeing_state=None,
        )
        assert r.sleep_hours == 8.5

    def test_wellbeing_state_accepts_string(self) -> None:
        r = DailyRollup(
            user_id="u",
            day=date(2026, 4, 25),
            urges_logged=0,
            urges_handled=0,
            tools_used=0,
            mood_mean=None,
            sleep_hours=None,
            wellbeing_state="low",
        )
        assert r.wellbeing_state == "low"

    def test_day_field_is_date(self) -> None:
        d = date(2026, 4, 25)
        r = DailyRollup(
            user_id="u",
            day=d,
            urges_logged=0,
            urges_handled=0,
            tools_used=0,
            mood_mean=None,
            sleep_hours=None,
            wellbeing_state=None,
        )
        assert r.day == d


class TestBuildForUser:
    @pytest.mark.asyncio
    async def test_raises_not_implemented(self) -> None:
        with pytest.raises(NotImplementedError):
            await build_for_user("u-1", date(2026, 4, 25))


class TestModule:
    def test_daily_rollup_in_all(self) -> None:
        from discipline.analytics import rollups

        assert "DailyRollup" in rollups.__all__

    def test_build_for_user_in_all(self) -> None:
        from discipline.analytics import rollups

        assert "build_for_user" in rollups.__all__

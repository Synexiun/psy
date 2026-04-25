"""Unit tests for _build_trend() pure helper in
discipline.analytics.weekly_reflection.

_build_trend(instrument, current, baseline, n_checkins_7d) → FramedTrend | None
  Returns None when current is None.  This is a deliberate UX choice:
  if a user didn't take the instrument this week, we emit nothing rather
  than rendering an "insufficient_data" chip for every instrument in their
  profile.  Only instruments with a current score are surfaced.

  When current is not None, delegates to frame_trend(compute_point(...))
  which applies the RCI threshold logic and P1-P6 framing rules.

  The None-when-no-current semantic is clinically important: showing an
  "insufficient_data" chip for every un-taken instrument creates alert
  fatigue and obscures the instruments that DO have data this week.
"""

from __future__ import annotations

from discipline.analytics.weekly_reflection import _build_trend


# ---------------------------------------------------------------------------
# _build_trend — None suppression
# ---------------------------------------------------------------------------


class TestBuildTrendNoneSuppression:
    def test_none_current_returns_none(self) -> None:
        result = _build_trend("phq9", current=None, baseline=10.0, n_checkins_7d=3)
        assert result is None

    def test_none_current_with_none_baseline_returns_none(self) -> None:
        result = _build_trend("gad7", current=None, baseline=None, n_checkins_7d=0)
        assert result is None

    def test_none_current_any_checkins_returns_none(self) -> None:
        for n in (0, 1, 7):
            assert _build_trend("phq9", current=None, baseline=5.0, n_checkins_7d=n) is None


# ---------------------------------------------------------------------------
# _build_trend — non-None current produces a FramedTrend
# ---------------------------------------------------------------------------


class TestBuildTrendWithCurrent:
    def test_current_with_baseline_returns_framed_trend(self) -> None:
        result = _build_trend("phq9", current=5.0, baseline=12.0, n_checkins_7d=4)
        assert result is not None

    def test_current_without_baseline_returns_framed_trend(self) -> None:
        # No baseline = insufficient_data direction, but not None
        result = _build_trend("phq9", current=5.0, baseline=None, n_checkins_7d=2)
        assert result is not None

    def test_current_zero_returns_framed_trend(self) -> None:
        # Zero is a valid current score — not falsy in the None check
        result = _build_trend("phq9", current=0.0, baseline=5.0, n_checkins_7d=1)
        assert result is not None

    def test_n_checkins_zero_does_not_suppress(self) -> None:
        # n_checkins_7d is passed to framing, not used to gate the None check
        result = _build_trend("phq9", current=8.0, baseline=14.0, n_checkins_7d=0)
        assert result is not None

    def test_result_has_instrument(self) -> None:
        result = _build_trend("gad7", current=7.0, baseline=12.0, n_checkins_7d=3)
        assert result is not None
        assert result.instrument == "gad7"

    def test_result_has_narrative(self) -> None:
        result = _build_trend("phq9", current=5.0, baseline=14.0, n_checkins_7d=5)
        assert result is not None
        assert isinstance(result.narrative, str)

    def test_result_has_tone(self) -> None:
        result = _build_trend("phq9", current=8.0, baseline=10.0, n_checkins_7d=3)
        assert result is not None
        assert result.tone is not None

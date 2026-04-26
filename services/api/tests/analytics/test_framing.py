"""Unit tests for framing.py — P1–P6 protective framing rules.

P1  No isolated raw scores — every score gets a contextual label.
P2  Lapse never appears as "streak reset" — resilience co-presented with days-clean.
P3  Non-stigmatizing language — "softer/steadier/heavier", never "better/worse".
P4  (No future-relapse predictions — enforced at call-site, not in this module.)
P5  Sparse data (<3 check-ins) suppresses trend deltas.
P6  Safety-positive signals bypass analytics narration → SafetyPositiveBypassError.
"""

from __future__ import annotations

import pytest

from discipline.analytics.framing import (
    FramedResilience,
    FramedScore,
    FramedTrend,
    SafetyPositiveBypassError,
    frame_gad7,
    frame_phq9,
    frame_resilience,
    frame_trend,
    sparse,
)
from discipline.psychometric.trajectories import TrajectoryPoint


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _point(
    direction: str = "improvement",
    instrument: str = "phq9",
    current: float = 5.0,
    baseline: float | None = 12.0,
) -> TrajectoryPoint:
    delta = (current - baseline) if baseline is not None else None
    return TrajectoryPoint(
        instrument=instrument,
        current=current,
        baseline=baseline,
        delta=delta,
        rci_threshold=5.2,
        direction=direction,  # type: ignore[arg-type]
    )


# ---------------------------------------------------------------------------
# sparse() — P5 threshold
# ---------------------------------------------------------------------------


class TestSparse:
    def test_zero_checkins_is_sparse(self) -> None:
        assert sparse(0) is True

    def test_two_checkins_is_sparse(self) -> None:
        assert sparse(2) is True

    def test_three_checkins_is_not_sparse(self) -> None:
        assert sparse(3) is False

    def test_seven_checkins_is_not_sparse(self) -> None:
        assert sparse(7) is False

    def test_boundary_is_exclusive_on_sparse_side(self) -> None:
        # 2 < 3 → sparse; 3 >= 3 → not sparse
        assert sparse(2) is True
        assert sparse(3) is False


# ---------------------------------------------------------------------------
# frame_phq9 — P1 contextual labels, P3 non-stigmatizing display values
# ---------------------------------------------------------------------------


class TestFramePhq9:
    def test_zero_is_low_calm(self) -> None:
        result = frame_phq9(0, baseline=None)
        assert result.display == "low"
        assert result.tone == "calm"

    def test_four_is_low_calm(self) -> None:
        result = frame_phq9(4, baseline=None)
        assert result.display == "low"
        assert result.tone == "calm"

    def test_five_is_mild_neutral(self) -> None:
        result = frame_phq9(5, baseline=None)
        assert result.display == "mild"
        assert result.tone == "neutral"

    def test_nine_is_mild_neutral(self) -> None:
        result = frame_phq9(9, baseline=None)
        assert result.display == "mild"
        assert result.tone == "neutral"

    def test_ten_is_moderate_neutral(self) -> None:
        result = frame_phq9(10, baseline=None)
        assert result.display == "moderate"
        assert result.tone == "neutral"

    def test_fourteen_is_moderate_neutral(self) -> None:
        result = frame_phq9(14, baseline=None)
        assert result.display == "moderate"
        assert result.tone == "neutral"

    def test_fifteen_is_noticeable_alert(self) -> None:
        result = frame_phq9(15, baseline=None)
        assert result.display == "noticeable"
        assert result.tone == "alert"

    def test_twentyseven_is_noticeable_alert(self) -> None:
        result = frame_phq9(27, baseline=None)
        assert result.display == "noticeable"
        assert result.tone == "alert"

    def test_instrument_field_is_phq9(self) -> None:
        assert frame_phq9(10, baseline=None).instrument == "phq9"

    def test_returns_framed_score(self) -> None:
        assert isinstance(frame_phq9(5, baseline=None), FramedScore)

    def test_p3_no_better_worse_in_display(self) -> None:
        for total in (0, 5, 10, 15, 27):
            result = frame_phq9(total, baseline=None)
            assert "better" not in result.display
            assert "worse" not in result.display

    def test_baseline_ignored_in_snapshot(self) -> None:
        # P1: baseline doesn't change snapshot label — that's frame_trend's job
        assert frame_phq9(5, baseline=0).display == frame_phq9(5, baseline=27).display


# ---------------------------------------------------------------------------
# frame_gad7 — Spitzer 2006 bands
# ---------------------------------------------------------------------------


class TestFrameGad7:
    def test_zero_is_low_calm(self) -> None:
        result = frame_gad7(0, baseline=None)
        assert result.display == "low"
        assert result.tone == "calm"

    def test_four_is_low_calm(self) -> None:
        assert frame_gad7(4, baseline=None).display == "low"

    def test_five_is_mild_neutral(self) -> None:
        assert frame_gad7(5, baseline=None).display == "mild"

    def test_nine_is_mild_neutral(self) -> None:
        assert frame_gad7(9, baseline=None).display == "mild"

    def test_ten_is_moderate_neutral(self) -> None:
        assert frame_gad7(10, baseline=None).display == "moderate"

    def test_fourteen_is_moderate_neutral(self) -> None:
        assert frame_gad7(14, baseline=None).display == "moderate"

    def test_fifteen_is_noticeable_alert(self) -> None:
        result = frame_gad7(15, baseline=None)
        assert result.display == "noticeable"
        assert result.tone == "alert"

    def test_instrument_field_is_gad7(self) -> None:
        assert frame_gad7(8, baseline=None).instrument == "gad7"

    def test_returns_framed_score(self) -> None:
        assert isinstance(frame_gad7(8, baseline=None), FramedScore)

    def test_bands_mirror_phq9_structure(self) -> None:
        # Both instruments share the same cut-point schema (4/9/14)
        for total, expected_display in ((4, "low"), (9, "mild"), (14, "moderate"), (15, "noticeable")):
            assert frame_gad7(total, baseline=None).display == expected_display


# ---------------------------------------------------------------------------
# frame_trend — P3, P5, P6 contracts
# ---------------------------------------------------------------------------


class TestFrameTrendP3Language:
    def test_improvement_gives_softer_label(self) -> None:
        result = frame_trend(_point("improvement"))
        assert result.direction_label == "softer"

    def test_deterioration_gives_heavier_label(self) -> None:
        result = frame_trend(_point("deterioration"))
        assert result.direction_label == "heavier"

    def test_no_reliable_change_gives_steadier_label(self) -> None:
        result = frame_trend(_point("no_reliable_change"))
        assert result.direction_label == "steadier"

    def test_p3_no_better_in_narrative(self) -> None:
        for direction in ("improvement", "deterioration", "no_reliable_change"):
            result = frame_trend(_point(direction))
            assert "better" not in result.narrative
            assert "worse" not in result.narrative

    def test_narrative_contains_direction_label(self) -> None:
        result = frame_trend(_point("improvement"))
        assert "softer" in result.narrative

    def test_improvement_tone_is_calm(self) -> None:
        assert frame_trend(_point("improvement")).tone == "calm"

    def test_deterioration_tone_is_alert(self) -> None:
        assert frame_trend(_point("deterioration")).tone == "alert"

    def test_no_reliable_change_tone_is_neutral(self) -> None:
        assert frame_trend(_point("no_reliable_change")).tone == "neutral"

    def test_instrument_propagated(self) -> None:
        result = frame_trend(_point("improvement", instrument="gad7"))
        assert result.instrument == "gad7"

    def test_returns_framed_trend(self) -> None:
        assert isinstance(frame_trend(_point("improvement")), FramedTrend)

    def test_non_sparse_result_has_no_suppressed_reason(self) -> None:
        result = frame_trend(_point("improvement"), n_checkins_7d=5)
        assert result.suppressed_reason is None


class TestFrameTrendP5Sparse:
    def test_zero_checkins_suppresses_trend(self) -> None:
        result = frame_trend(_point("improvement"), n_checkins_7d=0)
        assert result.suppressed_reason == "insufficient_data"

    def test_two_checkins_suppresses_trend(self) -> None:
        result = frame_trend(_point("deterioration"), n_checkins_7d=2)
        assert result.suppressed_reason == "insufficient_data"

    def test_three_checkins_does_not_suppress(self) -> None:
        result = frame_trend(_point("improvement"), n_checkins_7d=3)
        assert result.suppressed_reason is None

    def test_sparse_direction_label_is_none(self) -> None:
        result = frame_trend(_point("improvement"), n_checkins_7d=1)
        assert result.direction_label is None

    def test_sparse_narrative_says_not_enough_data(self) -> None:
        result = frame_trend(_point("deterioration"), n_checkins_7d=0)
        assert "not enough data" in result.narrative

    def test_sparse_tone_is_neutral(self) -> None:
        result = frame_trend(_point("deterioration"), n_checkins_7d=0)
        assert result.tone == "neutral"

    def test_p5_overrides_even_clear_deterioration(self) -> None:
        # Sparse check-ins override even a "heavier" direction
        result = frame_trend(_point("deterioration"), n_checkins_7d=2)
        assert result.direction_label is None
        assert result.suppressed_reason == "insufficient_data"

    def test_none_checkins_does_not_trigger_sparse(self) -> None:
        # n_checkins_7d=None means caller didn't provide count — don't suppress
        result = frame_trend(_point("improvement"), n_checkins_7d=None)
        assert result.suppressed_reason is None


class TestFrameTrendP6SafetyPositive:
    def test_safety_positive_raises(self) -> None:
        with pytest.raises(SafetyPositiveBypassError):
            frame_trend(_point("improvement"), has_safety_positive=True)

    def test_error_message_mentions_instrument(self) -> None:
        with pytest.raises(SafetyPositiveBypassError, match="phq9"):
            frame_trend(_point("improvement", instrument="phq9"), has_safety_positive=True)

    def test_safety_positive_false_does_not_raise(self) -> None:
        # Explicit False must not raise
        result = frame_trend(_point("improvement"), has_safety_positive=False)
        assert result is not None

    def test_p6_takes_precedence_over_sparse(self) -> None:
        # Even with sparse data, P6 raises before P5 suppression can happen
        with pytest.raises(SafetyPositiveBypassError):
            frame_trend(_point("improvement"), has_safety_positive=True, n_checkins_7d=0)


class TestFrameTrendInsufficientDataDirection:
    def test_insufficient_data_direction_suppresses_label(self) -> None:
        result = frame_trend(_point("insufficient_data"))
        assert result.direction_label is None

    def test_insufficient_data_direction_says_not_enough_data(self) -> None:
        result = frame_trend(_point("insufficient_data"))
        assert "not enough data" in result.narrative

    def test_insufficient_data_tone_is_neutral(self) -> None:
        result = frame_trend(_point("insufficient_data"))
        assert result.tone == "neutral"

    def test_insufficient_data_reason_field_set(self) -> None:
        result = frame_trend(_point("insufficient_data"))
        assert result.suppressed_reason == "insufficient_data"


# ---------------------------------------------------------------------------
# frame_resilience — P2: resilience co-presented with days-clean
# ---------------------------------------------------------------------------


class TestFrameResilience:
    def test_display_contains_resilience_days(self) -> None:
        result = frame_resilience(resilience_days=42, days_clean=7)
        assert "42" in result.display

    def test_display_contains_days_clean(self) -> None:
        result = frame_resilience(resilience_days=42, days_clean=7)
        assert "7" in result.display

    def test_display_format(self) -> None:
        result = frame_resilience(resilience_days=10, days_clean=3)
        assert result.display == "10 urges handled · 3 days clean"

    def test_days_clean_positive_tone_is_calm(self) -> None:
        result = frame_resilience(resilience_days=5, days_clean=1)
        assert result.tone == "calm"

    def test_days_clean_zero_tone_is_neutral(self) -> None:
        result = frame_resilience(resilience_days=5, days_clean=0)
        assert result.tone == "neutral"

    def test_returns_framed_resilience(self) -> None:
        assert isinstance(frame_resilience(10, 5), FramedResilience)

    def test_fields_preserved(self) -> None:
        result = frame_resilience(resilience_days=99, days_clean=14)
        assert result.resilience_days == 99
        assert result.days_clean == 14

    def test_negative_resilience_days_raises(self) -> None:
        with pytest.raises(ValueError):
            frame_resilience(resilience_days=-1, days_clean=5)

    def test_negative_days_clean_raises(self) -> None:
        with pytest.raises(ValueError):
            frame_resilience(resilience_days=10, days_clean=-1)

    def test_p2_lapse_does_not_reset_resilience(self) -> None:
        # After a lapse: days_clean=0, resilience_days unchanged
        result = frame_resilience(resilience_days=100, days_clean=0)
        assert result.resilience_days == 100
        assert result.days_clean == 0
        assert "100" in result.display

    def test_p2_no_streak_reset_framing_in_display(self) -> None:
        result = frame_resilience(resilience_days=50, days_clean=0)
        assert "reset" not in result.display.lower()
        assert "failed" not in result.display.lower()

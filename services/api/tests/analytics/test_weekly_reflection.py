"""WeeklyReflectionService composition tests.

Each branch of ``compose()`` is covered: safety short-circuit, missing
instruments, sparse-data suppression, baseline-absence, and the full
populated happy path.

A failing test here means the composition contract between the primitives
(framing + trajectories) and the router's serializer has drifted — fix at
the service layer, not by editing the P1–P6 primitives.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import date

import pytest

from discipline.analytics.framing import (
    FramedResilience,
    FramedScore,
    FramedTrend,
)
from discipline.analytics.weekly_reflection import (
    WeeklyReflectionInput,
    compose,
)


def _base_input(**overrides: object) -> WeeklyReflectionInput:
    defaults: dict[str, object] = {
        "user_id": "user_test_001",
        "week_ending": date(2026, 4, 18),
        "phq9_current": 8,
        "phq9_baseline": 14,
        "gad7_current": 6,
        "gad7_baseline": 9,
        "who5_current": 60.0,
        "who5_baseline": 40.0,
        "pss10_current": 18.0,
        "pss10_baseline": 25.0,
        "resilience_days": 42,
        "days_clean": 14,
        "n_checkins_7d": 5,
        "safety_positive_this_week": False,
    }
    defaults.update(overrides)
    return WeeklyReflectionInput(**defaults)  # type: ignore[arg-type]


# =============================================================================
# P6 short-circuit: safety-routed reflections expose nothing else
# =============================================================================


class TestSafetyRoutingShortCircuit:
    """When a safety signal fired this week, the UI layer must render the
    T3 handoff — not a cheerful "things got softer" reflection.  The service
    short-circuits by zeroing every analytics field."""

    def test_safety_flag_sets_safety_routed_true(self) -> None:
        result = compose(_base_input(safety_positive_this_week=True))
        assert result.safety_routed is True

    def test_safety_flag_suppresses_every_analytics_field(self) -> None:
        result = compose(_base_input(safety_positive_this_week=True))
        assert result.severity_phq9 is None
        assert result.severity_gad7 is None
        assert result.trend_phq9 is None
        assert result.trend_gad7 is None
        assert result.trend_who5 is None
        assert result.trend_pss10 is None
        assert result.resilience is None

    def test_safety_flag_preserves_identity_fields(self) -> None:
        """User id and week_ending survive so downstream logging can correlate."""
        result = compose(_base_input(safety_positive_this_week=True))
        assert result.user_id == "user_test_001"
        assert result.week_ending == date(2026, 4, 18)

    def test_safety_flag_short_circuits_even_with_improving_scores(self) -> None:
        """Worst silent-failure scenario: scores look fantastic but item 9
        was positive.  The reflection must still short-circuit."""
        result = compose(
            _base_input(
                safety_positive_this_week=True,
                phq9_current=0,
                phq9_baseline=20,
            )
        )
        assert result.safety_routed is True
        assert result.trend_phq9 is None


# =============================================================================
# Happy path: full data populates every field
# =============================================================================


class TestFullyPopulatedReflection:
    def test_happy_path_returns_every_field(self) -> None:
        result = compose(_base_input())
        assert result.safety_routed is False
        assert isinstance(result.severity_phq9, FramedScore)
        assert isinstance(result.severity_gad7, FramedScore)
        assert isinstance(result.trend_phq9, FramedTrend)
        assert isinstance(result.trend_gad7, FramedTrend)
        assert isinstance(result.trend_who5, FramedTrend)
        assert isinstance(result.trend_pss10, FramedTrend)
        assert isinstance(result.resilience, FramedResilience)

    def test_phq9_improvement_frames_as_softer(self) -> None:
        """Current 8, baseline 14 → delta -6, |6| > 5.2 threshold → improvement."""
        result = compose(_base_input())
        assert result.trend_phq9 is not None
        assert result.trend_phq9.direction_label == "softer"

    def test_who5_increase_frames_as_softer_too(self) -> None:
        """WHO-5 is higher-is-better but lexicon is anchored to user
        experience of distress, so improvement = softer regardless of scale direction."""
        result = compose(_base_input())
        assert result.trend_who5 is not None
        assert result.trend_who5.direction_label == "softer"

    def test_resilience_always_copresented(self) -> None:
        result = compose(_base_input())
        assert result.resilience is not None
        assert "42" in result.resilience.display
        assert "14 days clean" in result.resilience.display


# =============================================================================
# Missing instrument data (user didn't take the assessment this week)
# =============================================================================


class TestMissingInstrumentData:
    """When ``*_current`` is None, the user didn't take that instrument this
    week.  The reflection omits severity AND trend for it — cleaner than
    surfacing an "insufficient_data" chip for every opt-out."""

    def test_missing_phq9_current_hides_both_severity_and_trend(self) -> None:
        result = compose(_base_input(phq9_current=None))
        assert result.severity_phq9 is None
        assert result.trend_phq9 is None
        # Other instruments still appear
        assert result.severity_gad7 is not None
        assert result.trend_gad7 is not None

    def test_missing_gad7_current_hides_gad7_only(self) -> None:
        result = compose(_base_input(gad7_current=None))
        assert result.severity_gad7 is None
        assert result.trend_gad7 is None
        assert result.severity_phq9 is not None

    def test_missing_who5_current_hides_who5_trend(self) -> None:
        result = compose(_base_input(who5_current=None))
        assert result.trend_who5 is None
        # WHO-5 has no severity framing yet, so only trend was possible
        assert result.trend_phq9 is not None  # unaffected

    def test_all_instruments_missing_still_returns_reflection(self) -> None:
        """User with zero check-ins this week but positive streak state —
        reflection must still render the resilience headline."""
        result = compose(
            _base_input(
                phq9_current=None,
                gad7_current=None,
                who5_current=None,
                pss10_current=None,
                n_checkins_7d=0,
            )
        )
        assert result.safety_routed is False
        assert result.severity_phq9 is None
        assert result.severity_gad7 is None
        assert result.trend_phq9 is None
        assert result.resilience is not None  # still co-presented


# =============================================================================
# Baseline absence (new user, first reflection)
# =============================================================================


class TestMissingBaseline:
    """Baseline None is the first-week case.  Severity framing still works
    (it's a snapshot).  Trend falls back to insufficient_data."""

    def test_missing_phq9_baseline_still_renders_severity(self) -> None:
        result = compose(_base_input(phq9_baseline=None))
        assert result.severity_phq9 is not None

    def test_missing_phq9_baseline_produces_insufficient_data_trend(self) -> None:
        result = compose(_base_input(phq9_baseline=None))
        assert result.trend_phq9 is not None
        assert result.trend_phq9.suppressed_reason == "insufficient_data"
        assert result.trend_phq9.direction_label is None

    def test_all_baselines_missing_first_week_like(self) -> None:
        """First reflection ever — severity renders, every trend is insufficient_data."""
        result = compose(
            _base_input(
                phq9_baseline=None,
                gad7_baseline=None,
                who5_baseline=None,
                pss10_baseline=None,
            )
        )
        assert result.severity_phq9 is not None
        for trend in (
            result.trend_phq9,
            result.trend_gad7,
            result.trend_who5,
            result.trend_pss10,
        ):
            assert trend is not None
            assert trend.suppressed_reason == "insufficient_data"


# =============================================================================
# P5 sparse-data suppression (applies uniformly across all trends)
# =============================================================================


class TestSparseDataSuppression:
    @pytest.mark.parametrize("n_checkins", [0, 1, 2])
    def test_sparse_week_suppresses_every_trend(self, n_checkins: int) -> None:
        result = compose(_base_input(n_checkins_7d=n_checkins))
        for trend in (
            result.trend_phq9,
            result.trend_gad7,
            result.trend_who5,
            result.trend_pss10,
        ):
            assert trend is not None
            assert trend.suppressed_reason == "insufficient_data"

    def test_sparse_week_preserves_severity_and_resilience(self) -> None:
        """P5 suppresses trends, not snapshots.  Severity and resilience
        stay; they're not narrating change."""
        result = compose(_base_input(n_checkins_7d=1))
        assert result.severity_phq9 is not None
        assert result.resilience is not None

    def test_dense_week_does_not_suppress(self) -> None:
        result = compose(_base_input(n_checkins_7d=7))
        assert result.trend_phq9 is not None
        assert result.trend_phq9.suppressed_reason is None


# =============================================================================
# Edge cases
# =============================================================================


class TestEdgeCases:
    def test_reflection_is_frozen(self) -> None:
        result = compose(_base_input())
        with pytest.raises(AttributeError):
            result.safety_routed = True  # type: ignore[misc]

    def test_input_is_frozen(self) -> None:
        payload = _base_input()
        with pytest.raises(AttributeError):
            payload.phq9_current = 0  # type: ignore[misc]

    def test_replace_pattern_works_for_test_construction(self) -> None:
        """Sanity: dataclasses.replace works so tests can construct variants."""
        base = _base_input()
        safety = replace(base, safety_positive_this_week=True)
        assert safety.safety_positive_this_week is True
        assert base.safety_positive_this_week is False

    def test_zero_resilience_and_zero_days_clean_still_copresented(self) -> None:
        """First-day user — still gets resilience co-presentation, not a
        blank-slate suppression that could feel stigmatizing."""
        result = compose(_base_input(resilience_days=0, days_clean=0))
        assert result.resilience is not None
        assert "0 urges handled" in result.resilience.display
        assert "0 days clean" in result.resilience.display

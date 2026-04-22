"""Protective framing contract tests (rules P1–P6).

Sources:
- Docs/Business/02_Product_Requirements.md §F-14
- Docs/Whitepapers/04_Safety_Framework.md §"user-facing framing"

Each test cites the rule it defends.  Negative assertions dominate — we are
defending the user from *sentences that would harm them*, not optimizing a
number.  A test failure here is a clinical defect, not a copy-edit bug.
"""

from __future__ import annotations

import re
from dataclasses import fields

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
from discipline.psychometric.trajectories import compute_point

# Stigmatizing / moralizing tokens that MUST NOT appear anywhere in framed
# output.  Reviewed with the clinical-copy lexicon in
# Docs/bUSINESS/09_Brand_Positioning.md §voice.
_BANNED_TOKENS: tuple[str, ...] = (
    "better",
    "worse",
    "improved",
    "worsened",
    "failed",
    "failure",
    "relapsed",
    "relapse",  # deliberate: "relapse prevention" copy lives elsewhere
    "should",
    "must",
    "shouldn't",
    "mustn't",
)


def _collect_text(obj: object) -> str:
    """Concatenate all string-typed fields of a frozen dataclass for inspection."""
    texts: list[str] = []
    for f in fields(obj):  # type: ignore[arg-type]
        val = getattr(obj, f.name)
        if isinstance(val, str):
            texts.append(val)
    return " ".join(texts).lower()


def _assert_no_banned_tokens(text: str) -> None:
    for token in _BANNED_TOKENS:
        assert not re.search(rf"\b{re.escape(token)}\b", text), (
            f"framing leaked stigmatizing token {token!r}: {text!r}"
        )


# =============================================================================
# P1: No isolated raw scores
# =============================================================================


class TestP1RawScoresNeverNaked:
    """P1: Every score ships with a label.  The raw integer never surfaces
    as the whole ``display`` value."""

    @pytest.mark.parametrize("total", [0, 4, 5, 9, 10, 14, 15, 20, 27])
    def test_frame_phq9_display_is_a_word_not_a_number(self, total: int) -> None:
        result = frame_phq9(total, baseline=None)
        assert not result.display.isdigit(), (
            f"PHQ-9 framing returned raw digit {result.display!r} for total={total}"
        )
        assert result.display in {"low", "mild", "moderate", "noticeable"}

    @pytest.mark.parametrize("total", [0, 4, 5, 9, 10, 14, 15, 21])
    def test_frame_gad7_display_is_a_word_not_a_number(self, total: int) -> None:
        result = frame_gad7(total, baseline=None)
        assert not result.display.isdigit()
        assert result.display in {"low", "mild", "moderate", "noticeable"}

    def test_framed_score_tone_reflects_severity_not_score_magnitude(self) -> None:
        """Tone is a semantic tag, not a numeric bucket."""
        assert frame_phq9(0, None).tone == "calm"
        assert frame_phq9(9, None).tone == "neutral"
        assert frame_phq9(15, None).tone == "alert"


# =============================================================================
# P2: Resilience always co-presented with days-clean
# =============================================================================


class TestP2ResilienceCoPresented:
    """P2: resilience streak NEVER stands alone.  The API refuses to
    materialize a framing that has only one of the two numbers."""

    def test_framed_resilience_carries_both_fields(self) -> None:
        result = frame_resilience(resilience_days=42, days_clean=7)
        # Both numbers MUST be present in the headline string.
        assert "42" in result.display
        assert "7" in result.display

    def test_resilience_with_zero_days_clean_still_shows_both(self) -> None:
        """The worst framing regression would be hiding days_clean=0 to make
        the headline "look better".  This test defends against that."""
        result = frame_resilience(resilience_days=42, days_clean=0)
        assert "42" in result.display
        assert "0 days clean" in result.display
        assert result.tone == "neutral"  # not "calm" — days_clean just reset

    def test_resilience_never_uses_streak_reset_language(self) -> None:
        result = frame_resilience(resilience_days=10, days_clean=0)
        text = _collect_text(result)
        assert "reset" not in text
        assert "lost" not in text
        assert "broke" not in text

    def test_resilience_negative_inputs_raise(self) -> None:
        """Defensive: a negative resilience_days would violate the monotonic
        invariant enforced at the DB trigger layer."""
        with pytest.raises(ValueError):
            frame_resilience(resilience_days=-1, days_clean=0)
        with pytest.raises(ValueError):
            frame_resilience(resilience_days=0, days_clean=-1)


# =============================================================================
# P3: Non-stigmatizing tone vocabulary
# =============================================================================


class TestP3NonStigmatizingLanguage:
    """P3: The framed copy lexicon is {softer, steadier, heavier}.  Tokens
    like 'better'/'worse'/'failed' never appear."""

    @pytest.mark.parametrize(
        ("direction", "expected_label"),
        [
            ("improvement", "softer"),
            ("deterioration", "heavier"),
            ("no_reliable_change", "steadier"),
        ],
    )
    def test_trend_label_uses_approved_lexicon(
        self, direction: str, expected_label: str
    ) -> None:
        """For PHQ-9 (lower-is-better), the label mapping is direct."""
        if direction == "improvement":
            point = compute_point("phq9", current=0.0, baseline=10.0)
        elif direction == "deterioration":
            point = compute_point("phq9", current=10.0, baseline=0.0)
        else:
            point = compute_point("phq9", current=5.0, baseline=5.0)
        framed = frame_trend(point)
        assert framed.direction_label == expected_label

    def test_trend_narrative_contains_no_banned_tokens(self) -> None:
        for current, baseline in [(0.0, 10.0), (10.0, 0.0), (5.0, 5.0)]:
            point = compute_point("phq9", current=current, baseline=baseline)
            framed = frame_trend(point)
            _assert_no_banned_tokens(_collect_text(framed))

    def test_frame_phq9_severity_labels_contain_no_banned_tokens(self) -> None:
        for total in [0, 5, 10, 15, 20, 27]:
            _assert_no_banned_tokens(_collect_text(frame_phq9(total, None)))

    def test_who5_improvement_also_frames_as_softer(self) -> None:
        """WHO-5 is higher-is-better but the lexicon is anchored to the
        *user's experience of distress*, not the scale direction.  So WHO-5
        going up (more wellbeing) is still framed as "softer" at the
        user-facing layer."""
        point = compute_point("who5", current=80.0, baseline=40.0)  # delta=+40
        assert point.direction == "improvement"
        framed = frame_trend(point)
        assert framed.direction_label == "softer"


# =============================================================================
# P4: No future-relapse predictions in user-facing copy
# =============================================================================


class TestP4NoFuturePredictions:
    """P4: user-facing narrative is about *now* and *past trend* only.
    Predictive language ("likely to", "you will", "predicted") is banned."""

    _PREDICTIVE_TOKENS = ("will ", "likely", "predict", "forecast", "expected to")

    def test_trend_narrative_has_no_predictive_language(self) -> None:
        cases = [
            compute_point("phq9", current=0.0, baseline=10.0),
            compute_point("phq9", current=10.0, baseline=0.0),
            compute_point("phq9", current=5.0, baseline=5.0),
            compute_point("phq9", current=5.0, baseline=None),
        ]
        for point in cases:
            framed = frame_trend(point)
            text = _collect_text(framed)
            for tok in self._PREDICTIVE_TOKENS:
                assert tok not in text, f"predictive token {tok!r} leaked: {text!r}"

    def test_severity_framing_has_no_predictive_language(self) -> None:
        for total in [0, 10, 27]:
            framed = frame_phq9(total, None)
            text = _collect_text(framed)
            for tok in self._PREDICTIVE_TOKENS:
                assert tok not in text


# =============================================================================
# P5: Sparse data suppresses trends
# =============================================================================


class TestP5SparseDataSuppression:
    """P5: fewer than 3 check-ins in the last 7 days is too sparse to narrate."""

    @pytest.mark.parametrize("n", [0, 1, 2])
    def test_sparse_returns_true_below_three(self, n: int) -> None:
        assert sparse(n) is True

    @pytest.mark.parametrize("n", [3, 4, 5, 7, 14])
    def test_sparse_returns_false_at_or_above_three(self, n: int) -> None:
        assert sparse(n) is False

    def test_sparse_forces_insufficient_data_suppression_on_trend(self) -> None:
        point = compute_point("phq9", current=0.0, baseline=10.0)  # would be "softer"
        framed = frame_trend(point, n_checkins_7d=1)
        assert framed.suppressed_reason == "insufficient_data"
        assert framed.direction_label is None
        assert "not enough data" in framed.narrative

    def test_non_sparse_data_does_not_suppress(self) -> None:
        point = compute_point("phq9", current=0.0, baseline=10.0)
        framed = frame_trend(point, n_checkins_7d=5)
        assert framed.suppressed_reason is None
        assert framed.direction_label == "softer"

    def test_insufficient_data_trajectory_also_suppresses(self) -> None:
        """Even if n_checkins isn't passed, a TrajectoryPoint with no baseline
        is itself 'insufficient_data' and must suppress trend narration."""
        point = compute_point("phq9", current=10.0, baseline=None)
        framed = frame_trend(point)
        assert framed.suppressed_reason == "insufficient_data"
        assert framed.direction_label is None


# =============================================================================
# P6: Safety-positive NEVER appears as a trend
# =============================================================================


class TestP6SafetyPositiveBypass:
    """P6: A safety-positive signal routes to T3; analytics only records
    that the signal occurred.  Framing as a "trend" is a structural bug
    and the API fails loudly to prevent accidental neutral narration."""

    def test_safety_positive_flag_raises_bypass_error(self) -> None:
        point = compute_point("phq9", current=5.0, baseline=10.0)
        with pytest.raises(SafetyPositiveBypassError):
            frame_trend(point, has_safety_positive=True)

    def test_safety_positive_raises_even_on_apparent_improvement(self) -> None:
        """The worst silent failure: a user's total dropped but item 9 is
        still positive.  Naive framing would say "things are softer" — this
        MUST raise."""
        point = compute_point("phq9", current=2.0, baseline=15.0)  # improvement
        assert point.direction == "improvement"
        with pytest.raises(SafetyPositiveBypassError):
            frame_trend(point, has_safety_positive=True)

    def test_safety_positive_raises_even_with_sparse_data(self) -> None:
        """P6 takes precedence over P5.  Sparse data must not mask a
        safety-positive signal from being flagged as a structural bug."""
        point = compute_point("phq9", current=5.0, baseline=10.0)
        with pytest.raises(SafetyPositiveBypassError):
            frame_trend(point, has_safety_positive=True, n_checkins_7d=0)

    def test_bypass_error_message_names_the_instrument(self) -> None:
        """Operational: the error must name the instrument so ops can trace
        which caller regressed."""
        point = compute_point("phq9", current=5.0, baseline=10.0)
        with pytest.raises(SafetyPositiveBypassError) as exc_info:
            frame_trend(point, has_safety_positive=True)
        assert "phq9" in str(exc_info.value)


# =============================================================================
# Dataclass invariants
# =============================================================================


class TestDataclassInvariants:
    def test_framed_score_is_frozen(self) -> None:
        result = frame_phq9(5, None)
        with pytest.raises(AttributeError):
            result.display = "severe"  # type: ignore[misc]

    def test_framed_trend_is_frozen(self) -> None:
        point = compute_point("phq9", current=0.0, baseline=10.0)
        result = frame_trend(point)
        with pytest.raises(AttributeError):
            result.narrative = "you're totally fixed"  # type: ignore[misc]

    def test_framed_resilience_is_frozen(self) -> None:
        result = frame_resilience(10, 5)
        with pytest.raises(AttributeError):
            result.days_clean = 0  # type: ignore[misc]

    def test_dataclass_types_are_exported(self) -> None:
        """Downstream consumers (reports, router) import these names."""
        assert FramedScore.__name__ == "FramedScore"
        assert FramedTrend.__name__ == "FramedTrend"
        assert FramedResilience.__name__ == "FramedResilience"

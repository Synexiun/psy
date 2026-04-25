"""Tests for ``discipline.llm.safety_filter``.

The safety filter is a deterministic gate — no network, no ML model.
Every blocked pattern and allowed prefix is explicitly covered here.
CLAUDE.md mandates 95%+ coverage for safety-adjacent code paths.
"""

from __future__ import annotations

import pytest

from discipline.llm.safety_filter import FilterResult, SafetyFilter, SafetyFilterError


@pytest.fixture
def filt() -> SafetyFilter:
    return SafetyFilter()


# ---------------------------------------------------------------------------
# SafetyFilterError
# ---------------------------------------------------------------------------


class TestSafetyFilterError:
    def test_default_code(self) -> None:
        err = SafetyFilterError("blocked")
        assert err.code == "llm.safety_blocked"

    def test_custom_code(self) -> None:
        err = SafetyFilterError("blocked", code="custom.code")
        assert err.code == "custom.code"

    def test_reason_stored(self) -> None:
        err = SafetyFilterError("my reason")
        assert err.reason == "my reason"

    def test_is_exception(self) -> None:
        err = SafetyFilterError("blocked")
        assert isinstance(err, Exception)


# ---------------------------------------------------------------------------
# FilterResult
# ---------------------------------------------------------------------------


class TestFilterResult:
    def test_allowed_true(self) -> None:
        r = FilterResult(allowed=True)
        assert r.allowed is True
        assert r.reason is None

    def test_blocked_with_reason(self) -> None:
        r = FilterResult(allowed=False, reason="pattern matched")
        assert r.allowed is False
        assert r.reason == "pattern matched"

    def test_frozen(self) -> None:
        r = FilterResult(allowed=True)
        with pytest.raises((AttributeError, TypeError)):
            r.allowed = False  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Allowed prefixes (all 4 must bypass the free-text block)
# ---------------------------------------------------------------------------


class TestCheckPromptAllowedPrefixes:
    def test_weekly_report_template(self, filt: SafetyFilter) -> None:
        filt.check_prompt("weekly_report_template: Summarize the week.")

    def test_reflection_prompt_template(self, filt: SafetyFilter) -> None:
        filt.check_prompt("reflection_prompt_template: What went well today?")

    def test_pattern_explanation_template(self, filt: SafetyFilter) -> None:
        filt.check_prompt(
            "pattern_explanation_template: You tend to check your phone after lunch."
        )

    def test_journal_title_suggestion_template(self, filt: SafetyFilter) -> None:
        filt.check_prompt("journal_title_suggestion_template: I felt anxious today.")

    def test_prefix_matching_is_case_insensitive(self, filt: SafetyFilter) -> None:
        filt.check_prompt("WEEKLY_REPORT_TEMPLATE: content here")

    def test_allowed_prefix_with_blocked_keyword_still_passes(
        self, filt: SafetyFilter
    ) -> None:
        filt.check_prompt("reflection_prompt_template: user mentioned suicide risk")


# ---------------------------------------------------------------------------
# Blocked patterns — all 11 must be covered
# ---------------------------------------------------------------------------


class TestBlockedPatterns:
    def test_kill_yourself(self, filt: SafetyFilter) -> None:
        with pytest.raises(SafetyFilterError) as exc:
            filt.check_prompt("You should kill yourself.")
        assert exc.value.code == "llm.safety_blocked_prompt"

    def test_kill_myself(self, filt: SafetyFilter) -> None:
        with pytest.raises(SafetyFilterError):
            filt.check_prompt("I want to kill myself.")

    def test_suicide(self, filt: SafetyFilter) -> None:
        with pytest.raises(SafetyFilterError):
            filt.check_prompt("Thinking about suicide.")

    def test_self_harm_hyphen(self, filt: SafetyFilter) -> None:
        with pytest.raises(SafetyFilterError):
            filt.check_prompt("Struggling with self-harm urges.")

    def test_self_harm_space(self, filt: SafetyFilter) -> None:
        with pytest.raises(SafetyFilterError):
            filt.check_prompt("Struggling with self harm urges.")

    def test_diagnosis(self, filt: SafetyFilter) -> None:
        with pytest.raises(SafetyFilterError):
            filt.check_prompt("What diagnosis do I have?")

    def test_you_have_depression(self, filt: SafetyFilter) -> None:
        with pytest.raises(SafetyFilterError):
            filt.check_prompt("you have depression")

    def test_you_have_anxiety(self, filt: SafetyFilter) -> None:
        with pytest.raises(SafetyFilterError):
            filt.check_prompt("you have anxiety")

    def test_you_are_depressed(self, filt: SafetyFilter) -> None:
        with pytest.raises(SafetyFilterError):
            filt.check_prompt("you are depressed")

    def test_you_are_suicidal(self, filt: SafetyFilter) -> None:
        with pytest.raises(SafetyFilterError):
            filt.check_prompt("you are suicidal")

    def test_medication_recommendation(self, filt: SafetyFilter) -> None:
        with pytest.raises(SafetyFilterError):
            filt.check_prompt("What medication recommendation do you have?")

    def test_medication_advice(self, filt: SafetyFilter) -> None:
        with pytest.raises(SafetyFilterError):
            filt.check_prompt("Give me medication advice.")

    def test_take_Nmg(self, filt: SafetyFilter) -> None:
        with pytest.raises(SafetyFilterError):
            filt.check_prompt("Take 50 mg of sertraline.")

    def test_crisis_plan(self, filt: SafetyFilter) -> None:
        with pytest.raises(SafetyFilterError):
            filt.check_prompt("Help me write a crisis plan.")

    def test_hotline_number(self, filt: SafetyFilter) -> None:
        with pytest.raises(SafetyFilterError):
            filt.check_prompt("Give me the hotline number.")

    def test_therapist_recommendation(self, filt: SafetyFilter) -> None:
        with pytest.raises(SafetyFilterError):
            filt.check_prompt("I need a therapist recommendation.")

    def test_case_insensitive_kill_myself(self, filt: SafetyFilter) -> None:
        with pytest.raises(SafetyFilterError):
            filt.check_prompt("I WANT TO KILL MYSELF")

    def test_case_insensitive_suicide(self, filt: SafetyFilter) -> None:
        with pytest.raises(SafetyFilterError):
            filt.check_prompt("SUICIDE")


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_empty_prompt_blocked(self, filt: SafetyFilter) -> None:
        with pytest.raises(SafetyFilterError) as exc:
            filt.check_prompt("")
        assert "empty" in exc.value.reason.lower()

    def test_safe_free_text_allowed(self, filt: SafetyFilter) -> None:
        filt.check_prompt("I had a rough week but I managed to use the breathing tool.")

    def test_partial_word_not_blocked(self, filt: SafetyFilter) -> None:
        # "killed it" should NOT block — word-boundary enforced
        filt.check_prompt("I killed it at the gym today.")

    def test_run_prompt_returns_filter_result(self, filt: SafetyFilter) -> None:
        result = filt.run_prompt("weekly_report_template: hello")
        assert isinstance(result, FilterResult)

    def test_run_prompt_allowed_has_no_reason(self, filt: SafetyFilter) -> None:
        result = filt.run_prompt("weekly_report_template: hello")
        assert result.allowed is True
        assert result.reason is None

    def test_run_prompt_blocked_has_reason(self, filt: SafetyFilter) -> None:
        result = filt.run_prompt("suicide")
        assert result.allowed is False
        assert result.reason is not None


# ---------------------------------------------------------------------------
# check_response / run_response
# ---------------------------------------------------------------------------


class TestCheckResponse:
    def test_returns_response_unchanged_when_safe(self, filt: SafetyFilter) -> None:
        text = "Great work this week. You showed real resilience."
        assert filt.check_response(text) == text

    def test_raises_on_blocked_response(self, filt: SafetyFilter) -> None:
        with pytest.raises(SafetyFilterError) as exc:
            filt.check_response("You should kill yourself.")
        assert exc.value.code == "llm.safety_blocked_response"

    def test_empty_response_raises(self, filt: SafetyFilter) -> None:
        with pytest.raises(SafetyFilterError) as exc:
            filt.check_response("")
        assert "empty" in exc.value.reason.lower()

    def test_raises_on_diagnosis_in_response(self, filt: SafetyFilter) -> None:
        with pytest.raises(SafetyFilterError):
            filt.check_response("you have depression based on your scores.")


class TestRunResponse:
    def test_empty_blocked(self, filt: SafetyFilter) -> None:
        assert filt.run_response("").allowed is False

    def test_safe_allowed(self, filt: SafetyFilter) -> None:
        assert filt.run_response("Great job this week!").allowed is True

    def test_blocked_has_reason(self, filt: SafetyFilter) -> None:
        result = filt.run_response("take 100 mg of lorazepam")
        assert result.allowed is False
        assert result.reason is not None

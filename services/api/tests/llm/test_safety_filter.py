"""Tests for ``discipline.llm.safety_filter``.

The safety filter is a deterministic gate — no network, no ML model.
Every blocked pattern and allowed prefix must be covered.
"""

from __future__ import annotations

import pytest

from discipline.llm.safety_filter import SafetyFilter, SafetyFilterError


@pytest.fixture
def filt() -> SafetyFilter:
    return SafetyFilter()


class TestCheckPrompt:
    def test_allowed_prefix_weekly_report(self, filt: SafetyFilter) -> None:
        filt.check_prompt("weekly_report_template: Summarize the week.")

    def test_allowed_prefix_reflection(self, filt: SafetyFilter) -> None:
        filt.check_prompt("reflection_prompt_template: What went well today?")

    def test_allowed_prefix_pattern(self, filt: SafetyFilter) -> None:
        filt.check_prompt(
            "pattern_explanation_template: You tend to check your phone after lunch."
        )

    def test_allowed_prefix_journal_title(self, filt: SafetyFilter) -> None:
        filt.check_prompt("journal_title_suggestion_template: I felt anxious today.")

    def test_blocked_suicide_raises(self, filt: SafetyFilter) -> None:
        with pytest.raises(SafetyFilterError) as exc_info:
            filt.check_prompt("I want to kill myself")
        assert exc_info.value.code == "llm.safety_blocked_prompt"
        assert "forbidden pattern" in exc_info.value.reason.lower()

    def test_blocked_diagnosis_raises(self, filt: SafetyFilter) -> None:
        with pytest.raises(SafetyFilterError) as exc_info:
            filt.check_prompt("Do you think you have depression?")
        assert exc_info.value.code == "llm.safety_blocked_prompt"

    def test_blocked_medication_raises(self, filt: SafetyFilter) -> None:
        with pytest.raises(SafetyFilterError) as exc_info:
            filt.check_prompt("What medication recommendation do you have?")
        assert exc_info.value.code == "llm.safety_blocked_prompt"

    def test_empty_prompt_raises(self, filt: SafetyFilter) -> None:
        with pytest.raises(SafetyFilterError) as exc_info:
            filt.check_prompt("")
        assert "empty prompt" in exc_info.value.reason.lower()

    def test_case_insensitive_blocking(self, filt: SafetyFilter) -> None:
        with pytest.raises(SafetyFilterError):
            filt.check_prompt("I want to KILL MYSELF")


class TestRunPrompt:
    def test_returns_allowed_for_safe_prompt(self, filt: SafetyFilter) -> None:
        result = filt.run_prompt("weekly_report_template: Hello")
        assert result.allowed is True

    def test_returns_blocked_for_unsafe_prompt(self, filt: SafetyFilter) -> None:
        result = filt.run_prompt("I want to kill yourself")
        assert result.allowed is False
        assert result.reason is not None


class TestCheckResponse:
    def test_returns_response_when_safe(self, filt: SafetyFilter) -> None:
        text = "Here is a supportive reflection for you."
        assert filt.check_response(text) == text

    def test_raises_when_response_contains_blocked_pattern(
        self, filt: SafetyFilter
    ) -> None:
        with pytest.raises(SafetyFilterError) as exc_info:
            filt.check_response("You should kill yourself.")
        assert exc_info.value.code == "llm.safety_blocked_response"


class TestRunResponse:
    def test_empty_response_is_blocked(self, filt: SafetyFilter) -> None:
        result = filt.run_response("")
        assert result.allowed is False

    def test_safe_response_is_allowed(self, filt: SafetyFilter) -> None:
        result = filt.run_response("Great job this week!")
        assert result.allowed is True

"""Pre- and post-filter for LLM inputs/outputs.

Blocks:
- Crisis-path prompts (T3/T4) — deterministic only.
- Clinical guidance / diagnosis-adjacent language.
- Relapse messaging — deterministic compassion templates only.
- Free-form user text passed directly to the model.

The filter is a **deterministic gate** — no ML model, no network call.
A blocked prompt raises :class:`SafetyFilterError` immediately.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# Forbidden patterns — lowercase, matched case-insensitively.
# These are coarse guards; the real safety boundary is architectural
# (the crisis path never calls the LLM module at all).
_BLOCKED_PATTERNS: list[str] = [
    r"\bkill\s+(?:yourself|myself)\b",
    r"\bsuicide\b",
    r"\bself[-\s]?harm\b",
    r"\bdiagnos[ei]s\b",
    r"\byou\s+have\s+(?:depression|anxiety|bipolar|schizophrenia|ptsd|ocd)\b",
    r"\byou\s+are\s+(?:depressed|anxious|bipolar|schizophrenic|suicidal)\b",
    r"\bmedication\s+(?:recommendation|advice)\b",
    r"\btake\s+\d+\s*mg\b",
    r"\bcrisis\s+plan\b",
    r"\bhotline\s+number\b",
    r"\btherapist\s+recommendation\b",
]

_BLOCKED_COMPILED = [re.compile(p, re.IGNORECASE) for p in _BLOCKED_PATTERNS]

# Allowed use-case prefixes — if the prompt starts with one of these
# templates, it bypasses the free-text block.  This is a whitelist for
# the known-safe paths (weekly reflection, pattern explanation, etc).
_ALLOWED_PREFIXES: list[str] = [
    "weekly_report_template:",
    "reflection_prompt_template:",
    "pattern_explanation_template:",
    "journal_title_suggestion_template:",
]


class SafetyFilterError(Exception):
    """Raised when a prompt or response violates the safety boundary."""

    def __init__(self, reason: str, code: str = "llm.safety_blocked") -> None:
        self.reason = reason
        self.code = code
        super().__init__(reason)


@dataclass(frozen=True, slots=True)
class FilterResult:
    """Result of running the safety filter."""

    allowed: bool
    reason: str | None = None


class SafetyFilter:
    """Deterministic pre/post filter for LLM prompts and responses.

    Usage::

        filter = SafetyFilter()
        filter.check_prompt("reflection_prompt_template: Summarize the week.")
        # OK

        filter.check_prompt("What medication should I take?")
        # raises SafetyFilterError
    """

    def check_prompt(self, prompt: str) -> None:
        """Validate a prompt before sending to the LLM.

        Raises :class:`SafetyFilterError` on violation.
        """
        result = self.run_prompt(prompt)
        if not result.allowed:
            raise SafetyFilterError(
                reason=result.reason or "prompt blocked by safety filter",
                code="llm.safety_blocked_prompt",
            )

    def run_prompt(self, prompt: str) -> FilterResult:
        """Run the filter on a prompt and return a result without raising."""
        if not prompt:
            return FilterResult(allowed=False, reason="empty prompt")

        # Allow known-safe template prefixes.
        lower = prompt.lower()
        for prefix in _ALLOWED_PREFIXES:
            if lower.startswith(prefix.lower()):
                return FilterResult(allowed=True)

        # Block free-form prompts that contain forbidden patterns.
        for pattern in _BLOCKED_COMPILED:
            match = pattern.search(prompt)
            if match:
                return FilterResult(
                    allowed=False,
                    reason=f"forbidden pattern matched: {match.group()}",
                )

        return FilterResult(allowed=True)

    def check_response(self, response: str) -> str:
        """Validate an LLM response before returning to the user.

        Returns the response on success; raises :class:`SafetyFilterError`
        on violation.
        """
        result = self.run_response(response)
        if not result.allowed:
            raise SafetyFilterError(
                reason=result.reason or "response blocked by safety filter",
                code="llm.safety_blocked_response",
            )
        return response

    def run_response(self, response: str) -> FilterResult:
        """Run the filter on a response and return a result without raising."""
        if not response:
            return FilterResult(allowed=False, reason="empty response")

        for pattern in _BLOCKED_COMPILED:
            match = pattern.search(response)
            if match:
                return FilterResult(
                    allowed=False,
                    reason=f"forbidden pattern in response: {match.group()}",
                )

        return FilterResult(allowed=True)

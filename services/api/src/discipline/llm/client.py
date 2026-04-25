"""Anthropic LLM client with safety filter + per-user budget enforcement.

All LLM calls route through this module so the safety filter runs and
quotas are enforced.  No direct Anthropic SDK calls from route handlers.
"""

from __future__ import annotations

import structlog
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, ClassVar

import anthropic
import redis

from discipline.config import get_settings
from discipline.llm.safety_filter import SafetyFilter

logger = structlog.get_logger(__name__)

# Redis key pattern: llm:budget:{user_id}:{YYYY-MM-DD}
# TTL is set to 25 hours so the key always expires before the next day's window,
# even accounting for timezone drift between client and server clocks.
_BUDGET_KEY_TTL_SECONDS = 25 * 3600


@dataclass(frozen=True, slots=True)
class LLMResponse:
    """Structured LLM response."""

    content: str
    model: str
    usage_input_tokens: int
    usage_output_tokens: int


class LLMBudgetExceededError(Exception):
    """Raised when a user exceeds their daily LLM request budget."""

    def __init__(self, user_id: str, limit: int) -> None:
        self.user_id = user_id
        self.limit = limit
        super().__init__(f"User {user_id} exceeded daily LLM budget ({limit})")


class LLMClient:
    """Gateway for all LLM requests.

    Budgets (per Docs/Technicals/05_Backend_Services.md §3.12):
    - Free: 10 requests/day
    - Plus: 40 requests/day
    - Pro: 200 requests/day

    Enforced at gateway; caller must provide ``user_id`` and ``tier``.
    """

    # Default model — Haiku 4.5 for speed/cost; Sonnet 4.6 for complex tasks.
    DEFAULT_MODEL: str = "claude-3-5-haiku-20241022"

    # Budget tiers.
    BUDGETS: ClassVar[dict[str, int]] = {
        "free": 10,
        "plus": 40,
        "pro": 200,
    }

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        safety_filter: SafetyFilter | None = None,
    ) -> None:
        settings = get_settings()
        self._client = anthropic.Anthropic(
            api_key=api_key or settings.anthropic_api_key,
            base_url=base_url or settings.anthropic_base_url,
        )
        self._filter = safety_filter or SafetyFilter()

    def generate(
        self,
        *,
        user_id: str,
        tier: str,
        prompt: str,
        model: str | None = None,
        max_tokens: int = 512,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> LLMResponse:
        """Send a prompt to the LLM and return the response.

        Steps:
        1. Check user budget (raises :class:`LLMBudgetExceededError`).
        2. Run safety filter on prompt (raises :class:`SafetyFilterError`).
        3. Call Anthropic API.
        4. Run safety filter on response.
        5. Return structured response.
        """
        self._check_budget(user_id, tier)
        self._filter.check_prompt(prompt)

        response = self._client.messages.create(
            model=model or self.DEFAULT_MODEL,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}],
            **kwargs,
        )

        content = response.content[0].text if response.content else ""
        self._filter.check_response(content)

        return LLMResponse(
            content=content,
            model=response.model,
            usage_input_tokens=response.usage.input_tokens,
            usage_output_tokens=response.usage.output_tokens,
        )

    # ------------------------------------------------------------------
    # Template helpers (known-safe use cases)
    # ------------------------------------------------------------------

    def weekly_report_narrative(
        self,
        *,
        user_id: str,
        tier: str,
        summary_data: dict[str, Any],
    ) -> LLMResponse:
        """Generate a weekly report narrative."""
        prompt = (
            "weekly_report_template: Compose a brief, supportive weekly summary "
            f"based on the following structured data: {summary_data}"
        )
        return self.generate(user_id=user_id, tier=tier, prompt=prompt)

    def reflection_prompt(
        self,
        *,
        user_id: str,
        tier: str,
        context: dict[str, Any],
    ) -> LLMResponse:
        """Generate a reflection prompt from a template."""
        prompt = (
            "reflection_prompt_template: Based on the user's recent activity, "
            f"suggest one reflective question. Context: {context}"
        )
        return self.generate(user_id=user_id, tier=tier, prompt=prompt)

    def pattern_explanation(
        self,
        *,
        user_id: str,
        tier: str,
        pattern: dict[str, Any],
    ) -> LLMResponse:
        """Explain a detected pattern in plain language."""
        prompt = (
            "pattern_explanation_template: Explain the following pattern "
            f"in supportive, non-clinical language: {pattern}"
        )
        return self.generate(user_id=user_id, tier=tier, prompt=prompt)

    def journal_title_suggestion(
        self,
        *,
        user_id: str,
        tier: str,
        journal_text: str,
    ) -> LLMResponse:
        """Suggest a title for a journal entry."""
        prompt = (
            "journal_title_suggestion_template: Suggest a short, neutral title "
            f"for a journal entry that begins: {journal_text[:200]}"
        )
        return self.generate(user_id=user_id, tier=tier, prompt=prompt)

    # ------------------------------------------------------------------
    # Budget (placeholder — wire to Redis counter in production)
    # ------------------------------------------------------------------

    def _check_budget(self, user_id: str, tier: str) -> None:
        """Enforce per-user daily LLM request budget via Redis INCR.

        Uses atomic INCR + EXPIRE so the counter is consistent under concurrent
        requests.  EXPIRE is only set on the first increment (count == 1) to
        avoid resetting the TTL on every request.

        Degrades gracefully when Redis is unavailable — logs a warning and
        allows the request through so an infrastructure outage does not block
        clinical functionality (the SafetyFilter gate remains the hard boundary).
        """
        limit = self.BUDGETS.get(tier, self.BUDGETS["free"])
        date_key = datetime.now(UTC).strftime("%Y-%m-%d")
        redis_key = f"llm:budget:{user_id}:{date_key}"

        try:
            from discipline.shared.redis_client import get_redis_client

            client = get_redis_client()
            count = client.incr(redis_key)
            if count == 1:
                # First request today — set TTL so the key auto-expires.
                client.expire(redis_key, _BUDGET_KEY_TTL_SECONDS)

            if count > limit:
                # Decrement so the count reflects actual successful requests,
                # not attempts — makes monitoring dashboards easier to read.
                client.decr(redis_key)
                raise LLMBudgetExceededError(user_id, limit)

        except LLMBudgetExceededError:
            raise
        except redis.RedisError:
            logger.warning(
                "llm.budget_check.redis_unavailable",
                user_id=user_id,
                tier=tier,
            )


__all__ = [
    "LLMBudgetExceededError",
    "LLMClient",
    "LLMResponse",
]

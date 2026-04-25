"""Tests for ``discipline.llm.client``.

Uses mocked Anthropic responses so no live API calls are made.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from discipline.llm.client import LLMBudgetExceededError, LLMClient, LLMResponse
from discipline.llm.safety_filter import SafetyFilterError


def _make_client() -> LLMClient:
    return LLMClient(api_key="test-key")


def _mock_anthropic(mock_anthropic_cls: Any, response_text: str = "Hello!") -> MagicMock:
    mock_client = MagicMock()
    mock_anthropic_cls.return_value = mock_client
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text=response_text)]
    mock_message.model = "claude-3-5-haiku-20241022"
    mock_message.usage.input_tokens = 10
    mock_message.usage.output_tokens = 5
    mock_client.messages.create.return_value = mock_message
    return mock_client


class TestGenerate:
    @patch("discipline.llm.client.anthropic.Anthropic")
    def test_generate_returns_structured_response(
        self, mock_anthropic_cls: Any
    ) -> None:
        _mock_anthropic(mock_anthropic_cls, "Hello, user!")
        client = _make_client()

        resp = client.generate(
            user_id="u_01",
            tier="free",
            prompt="weekly_report_template: Summarize.",
        )

        assert isinstance(resp, LLMResponse)
        assert resp.content == "Hello, user!"
        assert resp.model == "claude-3-5-haiku-20241022"
        assert resp.usage_input_tokens == 10
        assert resp.usage_output_tokens == 5

    @patch("discipline.llm.client.anthropic.Anthropic")
    def test_generate_calls_api_with_correct_model(
        self, mock_anthropic_cls: Any
    ) -> None:
        mock_client = _mock_anthropic(mock_anthropic_cls, "OK")
        client = _make_client()

        client.generate(
            user_id="u_01",
            tier="free",
            prompt="weekly_report_template: Test.",
            model="claude-3-5-sonnet-20241022",
        )

        call_kwargs = mock_client.messages.create.call_args.kwargs
        assert call_kwargs["model"] == "claude-3-5-sonnet-20241022"
        assert call_kwargs["max_tokens"] == 512
        assert call_kwargs["temperature"] == 0.7

    def test_generate_blocks_unsafe_prompt(self) -> None:
        client = _make_client()
        with pytest.raises(SafetyFilterError):
            client.generate(
                user_id="u_01",
                tier="free",
                prompt="I want to kill myself",
            )

    @patch("discipline.llm.client.anthropic.Anthropic")
    def test_generate_blocks_unsafe_response(
        self, mock_anthropic_cls: Any
    ) -> None:
        _mock_anthropic(mock_anthropic_cls, "You should kill yourself.")
        client = _make_client()

        with pytest.raises(SafetyFilterError) as exc_info:
            client.generate(
                user_id="u_01",
                tier="free",
                prompt="weekly_report_template: Summarize.",
            )
        assert exc_info.value.code == "llm.safety_blocked_response"


class TestTemplateHelpers:
    @patch("discipline.llm.client.anthropic.Anthropic")
    def test_weekly_report_narrative_uses_correct_prefix(
        self, mock_anthropic_cls: Any
    ) -> None:
        mock_client = _mock_anthropic(mock_anthropic_cls, "Weekly summary.")
        client = _make_client()

        resp = client.weekly_report_narrative(
            user_id="u_01",
            tier="plus",
            summary_data={"mood": "good"},
        )

        assert resp.content == "Weekly summary."
        call_kwargs = mock_client.messages.create.call_args.kwargs
        assert "weekly_report_template" in call_kwargs["messages"][0]["content"]

    @patch("discipline.llm.client.anthropic.Anthropic")
    def test_reflection_prompt_uses_correct_prefix(
        self, mock_anthropic_cls: Any
    ) -> None:
        mock_client = _mock_anthropic(mock_anthropic_cls, "Reflect.")
        client = _make_client()

        client.reflection_prompt(user_id="u_01", tier="pro", context={"streak": 5})
        call_kwargs = mock_client.messages.create.call_args.kwargs
        assert "reflection_prompt_template" in call_kwargs["messages"][0]["content"]

    @patch("discipline.llm.client.anthropic.Anthropic")
    def test_pattern_explanation_uses_correct_prefix(
        self, mock_anthropic_cls: Any
    ) -> None:
        mock_client = _mock_anthropic(mock_anthropic_cls, "Pattern.")
        client = _make_client()

        client.pattern_explanation(user_id="u_01", tier="free", pattern={"type": "temporal"})
        call_kwargs = mock_client.messages.create.call_args.kwargs
        assert "pattern_explanation_template" in call_kwargs["messages"][0]["content"]

    @patch("discipline.llm.client.anthropic.Anthropic")
    def test_journal_title_suggestion_uses_correct_prefix(
        self, mock_anthropic_cls: Any
    ) -> None:
        mock_client = _mock_anthropic(mock_anthropic_cls, "Title.")
        client = _make_client()

        client.journal_title_suggestion(
            user_id="u_01", tier="free", journal_text="Today was hard."
        )
        call_kwargs = mock_client.messages.create.call_args.kwargs
        assert "journal_title_suggestion_template" in call_kwargs["messages"][0]["content"]


class TestBudgets:
    def test_budget_tiers_defined(self) -> None:
        assert LLMClient.BUDGETS["free"] == 10
        assert LLMClient.BUDGETS["plus"] == 40
        assert LLMClient.BUDGETS["pro"] == 200

    def test_budget_exceeded_error_message(self) -> None:
        err = LLMBudgetExceededError("u_01", 10)
        assert "u_01" in str(err)
        assert "10" in str(err)


# ---------------------------------------------------------------------------
# Redis budget counter
# ---------------------------------------------------------------------------


class TestRedisBudgetCounter:
    def _make_mock_redis(self, count: int = 1) -> MagicMock:
        """Return a mock Redis client where INCR always returns *count*."""
        mock_redis = MagicMock()
        mock_redis.incr.return_value = count
        mock_redis.expire.return_value = True
        mock_redis.decr.return_value = count - 1
        return mock_redis

    def test_first_request_sets_expire(self) -> None:
        """First INCR (count=1) must call EXPIRE to establish the TTL."""
        mock_redis = self._make_mock_redis(count=1)
        client = _make_client()

        with patch("discipline.shared.redis_client.get_redis_client", return_value=mock_redis):
            client._check_budget("u_01", "free")

        mock_redis.expire.assert_called_once()

    def test_subsequent_requests_do_not_reset_expire(self) -> None:
        """INCR count > 1 must NOT call EXPIRE (would reset TTL)."""
        mock_redis = self._make_mock_redis(count=2)
        client = _make_client()

        with patch("discipline.shared.redis_client.get_redis_client", return_value=mock_redis):
            client._check_budget("u_01", "free")

        mock_redis.expire.assert_not_called()

    def test_within_budget_does_not_raise(self) -> None:
        """Count at or below limit must not raise."""
        mock_redis = self._make_mock_redis(count=10)  # free tier limit = 10
        client = _make_client()

        with patch("discipline.shared.redis_client.get_redis_client", return_value=mock_redis):
            client._check_budget("u_01", "free")  # should not raise

    def test_exceed_budget_raises(self) -> None:
        """Count above free tier limit must raise LLMBudgetExceededError."""
        mock_redis = self._make_mock_redis(count=11)  # free tier limit = 10
        client = _make_client()

        with patch("discipline.shared.redis_client.get_redis_client", return_value=mock_redis):
            with pytest.raises(LLMBudgetExceededError) as exc_info:
                client._check_budget("u_01", "free")

        assert exc_info.value.limit == 10
        assert exc_info.value.user_id == "u_01"

    def test_exceed_budget_decrements_counter(self) -> None:
        """On budget exceeded, DECR is called to keep counter accurate."""
        mock_redis = self._make_mock_redis(count=11)
        client = _make_client()

        with patch("discipline.shared.redis_client.get_redis_client", return_value=mock_redis):
            with pytest.raises(LLMBudgetExceededError):
                client._check_budget("u_01", "free")

        mock_redis.decr.assert_called_once()

    def test_plus_tier_higher_limit(self) -> None:
        """Plus tier allows up to 40 requests; count=40 should not raise."""
        mock_redis = self._make_mock_redis(count=40)  # plus tier limit = 40
        client = _make_client()

        with patch("discipline.shared.redis_client.get_redis_client", return_value=mock_redis):
            client._check_budget("u_01", "plus")  # should not raise

    def test_plus_tier_exceeded(self) -> None:
        """Plus tier at count=41 must raise."""
        mock_redis = self._make_mock_redis(count=41)
        client = _make_client()

        with patch("discipline.shared.redis_client.get_redis_client", return_value=mock_redis):
            with pytest.raises(LLMBudgetExceededError) as exc_info:
                client._check_budget("u_01", "plus")

        assert exc_info.value.limit == 40

    def test_redis_unavailable_degrades_gracefully(self) -> None:
        """Redis connection error must NOT raise — request is allowed through."""
        import redis as redis_lib

        client = _make_client()

        with patch(
            "discipline.shared.redis_client.get_redis_client",
            side_effect=redis_lib.RedisError("connection refused"),
        ):
            client._check_budget("u_01", "free")  # should not raise

    def test_redis_key_includes_user_id(self) -> None:
        """The Redis key must include the user_id for per-user scoping."""
        mock_redis = self._make_mock_redis(count=1)
        client = _make_client()

        with patch("discipline.shared.redis_client.get_redis_client", return_value=mock_redis):
            client._check_budget("user_abc", "free")

        incr_key = mock_redis.incr.call_args.args[0]
        assert "user_abc" in incr_key

    def test_redis_key_includes_date(self) -> None:
        """The Redis key must include today's date for daily windowing."""
        from datetime import UTC, datetime

        mock_redis = self._make_mock_redis(count=1)
        client = _make_client()
        today = datetime.now(UTC).strftime("%Y-%m-%d")

        with patch("discipline.shared.redis_client.get_redis_client", return_value=mock_redis):
            client._check_budget("u_01", "free")

        incr_key = mock_redis.incr.call_args.args[0]
        assert today in incr_key

    def test_unknown_tier_falls_back_to_free_limit(self) -> None:
        """Unknown tier string must use the 'free' limit (10) as safety default."""
        mock_redis = self._make_mock_redis(count=11)  # above free = 10
        client = _make_client()

        with patch("discipline.shared.redis_client.get_redis_client", return_value=mock_redis):
            with pytest.raises(LLMBudgetExceededError) as exc_info:
                client._check_budget("u_01", "unknown_tier")

        assert exc_info.value.limit == 10

"""LLM gateway — Anthropic client, prompt library, safety filters.

Per Docs/Technicals/05_Backend_Services.md §3.12:
- Never on crisis path (T3/T4).
- Never for clinical guidance or diagnosis-adjacent language.
- Restricted to: weekly report narrative, reflection prompts, pattern
  explanations, journal title suggestions.

Per-user budget enforced at gateway.
"""

from discipline.llm.client import LLMClient
from discipline.llm.safety_filter import SafetyFilter, SafetyFilterError

__all__ = [
    "LLMClient",
    "SafetyFilter",
    "SafetyFilterError",
]

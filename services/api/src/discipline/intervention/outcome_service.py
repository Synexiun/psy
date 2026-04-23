"""Outcome service — records intervention outcomes for bandit feedback.

Every tool delivery is followed by an outcome (handled, dismissed, expired,
or escalated).  Outcomes feed the bandit's reward signal.

See Docs/Technicals/05_Backend_Services.md §3.4 for the bandit contract.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol


@dataclass(frozen=True, slots=True)
class OutcomeRecord:
    """Plain data object returned by the repository."""

    outcome_id: str
    user_id: str
    intervention_id: str
    tool_variant: str
    outcome: str
    recorded_at: str
    context_json: dict[str, object] | None


class OutcomeRepository(Protocol):
    """Protocol for outcome storage backends."""

    async def record(
        self,
        *,
        user_id: str,
        intervention_id: str,
        tool_variant: str,
        outcome: str,
        context_json: dict[str, object] | None,
    ) -> OutcomeRecord:
        ...

    async def list_by_user(
        self, user_id: str, *, limit: int = 50
    ) -> list[OutcomeRecord]:
        ...


# ---------------------------------------------------------------------------
# In-memory stub
# ---------------------------------------------------------------------------


class InMemoryOutcomeRepository:
    """Thread-safe in-memory store for tests and local dev."""

    def __init__(self) -> None:
        self._outcomes: dict[str, OutcomeRecord] = {}

    async def record(
        self,
        *,
        user_id: str,
        intervention_id: str,
        tool_variant: str,
        outcome: str,
        context_json: dict[str, object] | None,
    ) -> OutcomeRecord:
        from uuid import uuid4

        now = datetime.now(UTC).isoformat()
        record = OutcomeRecord(
            outcome_id=str(uuid4()),
            user_id=user_id,
            intervention_id=intervention_id,
            tool_variant=tool_variant,
            outcome=outcome,
            recorded_at=now,
            context_json=context_json,
        )
        self._outcomes[record.outcome_id] = record
        return record

    async def list_by_user(
        self, user_id: str, *, limit: int = 50
    ) -> list[OutcomeRecord]:
        results = [r for r in self._outcomes.values() if r.user_id == user_id]
        results.sort(key=lambda r: r.recorded_at, reverse=True)
        return results[:limit]


# ---------------------------------------------------------------------------
# Singleton registry
# ---------------------------------------------------------------------------

_outcome_repo: OutcomeRepository = InMemoryOutcomeRepository()


def get_outcome_repository() -> OutcomeRepository:
    return _outcome_repo


def reset_outcome_repository() -> None:
    global _outcome_repo
    _outcome_repo = InMemoryOutcomeRepository()

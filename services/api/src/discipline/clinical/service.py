"""Clinical service — relapse protocol with compassion-first responses.

AGENTS.md Rule #4: Relapse copy is compassion-first. No "you failed,"
no "streak reset" framing. Templates require clinical QA sign-off.
"""

from __future__ import annotations

import random

from discipline.clinical.repository import RelapseRecord, get_relapse_repository


_COMPASSION_TEMPLATES: list[str] = [
    "You're here. That matters. When you're ready, we can look at today together.",
    "This moment doesn't define your journey. Compassion for yourself is the next step.",
    "It's okay to struggle. Reach out when you're ready — we're here.",
    "One moment at a time. You are not alone in this.",
    "Be gentle with yourself. Recovery is not a straight line.",
]

_NEXT_STEPS: list[str] = [
    "compassion_message",
    "review_prompt",
    "streak_update_summary",
    "tool_suggestion",
    "check_in_scheduler",
]


class RelapseService:
    """Compassion-first relapse response service."""

    def __init__(self, repository: object | None = None) -> None:
        self._repo = repository or get_relapse_repository()

    async def report(
        self,
        *,
        user_id: str,
        occurred_at: str,
        behavior: str,
        severity: int,
        context_tags: list[str],
    ) -> RelapseRecord:
        """Report a relapse with a deterministic compassion response.

        The compassion message is selected deterministically from a
        clinically-reviewed template set.  No LLM is involved.
        """
        # Deterministic selection based on hash of user_id + occurred_at
        # so the same report always yields the same message (idempotent).
        seed = hash(f"{user_id}:{occurred_at}")
        rng = random.Random(seed)
        compassion = rng.choice(_COMPASSION_TEMPLATES)
        return await self._repo.create(
            user_id=user_id,
            occurred_at=occurred_at,
            behavior=behavior,
            severity=severity,
            context_tags=context_tags,
            compassion_message=compassion,
        )

    def next_steps(self, severity: int) -> list[str]:
        """Return recommended next steps based on severity.

        Higher severity → more comprehensive follow-up.
        """
        if severity >= 4:
            return _NEXT_STEPS[:4]
        if severity >= 2:
            return _NEXT_STEPS[:3]
        return _NEXT_STEPS[:2]

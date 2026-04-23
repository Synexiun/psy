"""Pattern service — detection, mining, and lifecycle.

Provides deterministic pattern detectors that operate on user data
without cross-module repository imports.  In production the service
accepts data through typed interfaces; this scaffold implements the
structural contract with stub heuristics.

Detectors shipped:
1. Temporal — peak windows within day / week.
2. Contextual — co-occurring tags (work stress, social drinking).
3. Physiological — HRV dips preceding urge by 10–30 min.
4. Compound — chained signals.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol

from discipline.pattern.repository import (
    PatternRecord,
    get_pattern_repository,
)


@dataclass(frozen=True, slots=True)
class DetectedPattern:
    """Output of a single detector run."""

    pattern_type: str
    detector: str
    confidence: float
    description: str
    metadata: dict[str, object]


class PatternService(Protocol):
    """Protocol for pattern business logic."""

    async def mine_patterns(self, user_id: str) -> list[PatternRecord]:
        """Run all detectors and persist new patterns."""
        ...

    async def list_active(self, user_id: str, *, limit: int = 50) -> list[PatternRecord]:
        ...

    async def dismiss(
        self,
        pattern_id: str,
        user_id: str,
        *,
        reason: str | None,
    ) -> PatternRecord | None:
        ...


class PatternServiceImpl:
    """Concrete pattern service with deterministic detectors."""

    async def mine_patterns(self, user_id: str) -> list[PatternRecord]:
        """Run all four detectors and persist results.

        Stub implementation: generates deterministic synthetic patterns
        so the service contract is testable.  Production replaces this
        with real signal + journal + state analysis via typed interfaces.
        """
        repo = get_pattern_repository()
        detected = _run_detectors(user_id)
        records: list[PatternRecord] = []
        for d in detected:
            record = await repo.create(
                user_id=user_id,
                pattern_type=d.pattern_type,
                detector=d.detector,
                confidence=d.confidence,
                description=d.description,
                metadata_json=d.metadata,
            )
            records.append(record)
        return records

    async def list_active(self, user_id: str, *, limit: int = 50) -> list[PatternRecord]:
        repo = get_pattern_repository()
        return await repo.list_by_user(user_id, limit=limit, status_filter="active")

    async def dismiss(
        self,
        pattern_id: str,
        user_id: str,
        *,
        reason: str | None,
    ) -> PatternRecord | None:
        repo = get_pattern_repository()
        return await repo.dismiss(pattern_id, user_id, reason=reason)


def _run_detectors(user_id: str) -> list[DetectedPattern]:
    """Run the four detector types deterministically.

    Returns synthetic but structurally valid patterns so that:
    - Tests can assert on pattern_type distribution
    - The UI can render pattern cards with metadata
    - Dismiss + re-mine cycles are idempotent in shape
    """
    now = datetime.now(UTC)
    hour = now.hour

    return [
        DetectedPattern(
            pattern_type="temporal",
            detector="peak_window",
            confidence=0.82,
            description="Urge intensity tends to rise between 5 PM and 7 PM on weekdays.",
            metadata={
                "peak_start_hour": 17,
                "peak_end_hour": 19,
                "days_of_week": ["monday", "tuesday", "wednesday", "thursday", "friday"],
                "sample_windows": 14,
            },
        ),
        DetectedPattern(
            pattern_type="contextual",
            detector="co_occurring_tags",
            confidence=0.74,
            description="Work stress and social situations co-occur in 68% of logged urges.",
            metadata={
                "tags": ["work_stress", "social_situation"],
                "co_occurrence_rate": 0.68,
                "sample_urges": 22,
            },
        ),
        DetectedPattern(
            pattern_type="physiological",
            detector="hrv_dip",
            confidence=0.61,
            description="HRV drops 10–20 ms in the 20 minutes before 45% of urges.",
            metadata={
                "hrv_drop_ms": {"min": 10, "max": 20},
                "preceding_minutes": 20,
                "coverage": 0.45,
                "sample_urges": 18,
            },
        ),
        DetectedPattern(
            pattern_type="compound",
            detector="chained_signals",
            confidence=0.55,
            description="Evening work stress + HRV dip + location change forms a compound risk signal.",
            metadata={
                "components": ["temporal_evening", "contextual_work_stress", "physiological_hrv_dip"],
                "coverage": 0.32,
                "sample_urges": 12,
            },
        ),
    ]


# Singleton instance
_pattern_service: PatternService = PatternServiceImpl()


def get_pattern_service() -> PatternService:
    return _pattern_service


def reset_pattern_service() -> None:
    global _pattern_service
    _pattern_service = PatternServiceImpl()

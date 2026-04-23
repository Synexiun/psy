"""Signal repository — signal window and state estimate storage.

Provides both an in-memory stub (for tests and pre-DB dev) and an
async SQLAlchemy implementation (for production).  The interface is
stable so callers don't change when the backend swaps.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from discipline.signal.models import SignalWindow, StateEstimate


@dataclass(frozen=True, slots=True)
class SignalWindowRecord:
    """Plain data object returned by the repository."""

    window_id: str
    user_id: str
    window_start: str
    window_end: str
    source: str
    samples_hash: str
    created_at: str


@dataclass(frozen=True, slots=True)
class StateEstimateRecord:
    """Plain data object returned by the repository."""

    estimate_id: str
    user_id: str
    state_label: str
    confidence: float
    model_version: str
    inferred_at: str
    created_at: str


class SignalWindowRepository(Protocol):
    """Protocol for signal window storage backends."""

    async def create(
        self,
        *,
        user_id: str,
        window_start: str,
        window_end: str,
        source: str,
        samples_hash: str,
        samples_json: dict[str, object],
    ) -> SignalWindowRecord:
        ...

    async def get_by_samples_hash(self, user_id: str, samples_hash: str) -> SignalWindowRecord | None:
        ...


class StateEstimateRepository(Protocol):
    """Protocol for state estimate storage backends."""

    async def create(
        self,
        *,
        user_id: str,
        state_label: str,
        confidence: float,
        model_version: str,
        inferred_at: str,
        features_json: dict[str, object] | None,
    ) -> StateEstimateRecord:
        ...

    async def latest_by_user(self, user_id: str) -> StateEstimateRecord | None:
        ...


# ---------------------------------------------------------------------------
# In-memory stubs
# ---------------------------------------------------------------------------


class InMemorySignalWindowRepository:
    """Thread-safe in-memory store for tests and local dev."""

    def __init__(self) -> None:
        self._windows: dict[str, SignalWindowRecord] = {}

    async def create(
        self,
        *,
        user_id: str,
        window_start: str,
        window_end: str,
        source: str,
        samples_hash: str,
        samples_json: dict[str, object],
    ) -> SignalWindowRecord:
        from uuid import uuid4

        now = datetime.now(UTC).isoformat()
        record = SignalWindowRecord(
            window_id=str(uuid4()),
            user_id=user_id,
            window_start=window_start,
            window_end=window_end,
            source=source,
            samples_hash=samples_hash,
            created_at=now,
        )
        self._windows[record.window_id] = record
        return record

    async def get_by_samples_hash(self, user_id: str, samples_hash: str) -> SignalWindowRecord | None:
        for r in self._windows.values():
            if r.user_id == user_id and r.samples_hash == samples_hash:
                return r
        return None


class InMemoryStateEstimateRepository:
    """Thread-safe in-memory store for tests and local dev."""

    def __init__(self) -> None:
        self._estimates: dict[str, StateEstimateRecord] = {}

    async def create(
        self,
        *,
        user_id: str,
        state_label: str,
        confidence: float,
        model_version: str,
        inferred_at: str,
        features_json: dict[str, object] | None,
    ) -> StateEstimateRecord:
        from uuid import uuid4

        now = datetime.now(UTC).isoformat()
        record = StateEstimateRecord(
            estimate_id=str(uuid4()),
            user_id=user_id,
            state_label=state_label,
            confidence=confidence,
            model_version=model_version,
            inferred_at=inferred_at,
            created_at=now,
        )
        self._estimates[record.estimate_id] = record
        return record

    async def latest_by_user(self, user_id: str) -> StateEstimateRecord | None:
        results = [r for r in self._estimates.values() if r.user_id == user_id]
        if not results:
            return None
        results.sort(key=lambda r: r.inferred_at, reverse=True)
        return results[0]


# ---------------------------------------------------------------------------
# SQLAlchemy implementations
# ---------------------------------------------------------------------------


class SQLAlchemySignalWindowRepository:
    """Production signal window storage backed by PostgreSQL."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        user_id: str,
        window_start: str,
        window_end: str,
        source: str,
        samples_hash: str,
        samples_json: dict[str, object],
    ) -> SignalWindowRecord:
        from uuid import UUID

        window = SignalWindow(
            user_id=UUID(user_id),
            window_start=datetime.fromisoformat(window_start),
            window_end=datetime.fromisoformat(window_end),
            source=source,
            samples_hash=samples_hash,
            samples_json=samples_json,
        )
        self._session.add(window)
        await self._session.flush()
        return _window_to_record(window)

    async def get_by_samples_hash(self, user_id: str, samples_hash: str) -> SignalWindowRecord | None:
        from uuid import UUID

        result = await self._session.execute(
            select(SignalWindow).where(
                SignalWindow.user_id == UUID(user_id),
                SignalWindow.samples_hash == samples_hash,
            )
        )
        window = result.scalar_one_or_none()
        return _window_to_record(window) if window else None


class SQLAlchemyStateEstimateRepository:
    """Production state estimate storage backed by PostgreSQL."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        user_id: str,
        state_label: str,
        confidence: float,
        model_version: str,
        inferred_at: str,
        features_json: dict[str, object] | None,
    ) -> StateEstimateRecord:
        from uuid import UUID

        estimate = StateEstimate(
            user_id=UUID(user_id),
            state_label=state_label,
            confidence=confidence,
            model_version=model_version,
            inferred_at=datetime.fromisoformat(inferred_at),
            features_json=features_json,
        )
        self._session.add(estimate)
        await self._session.flush()
        return _estimate_to_record(estimate)

    async def latest_by_user(self, user_id: str) -> StateEstimateRecord | None:
        from uuid import UUID

        result = await self._session.execute(
            select(StateEstimate)
            .where(StateEstimate.user_id == UUID(user_id))
            .order_by(StateEstimate.inferred_at.desc())
            .limit(1)
        )
        estimate = result.scalar_one_or_none()
        return _estimate_to_record(estimate) if estimate else None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _window_to_record(window: SignalWindow) -> SignalWindowRecord:
    return SignalWindowRecord(
        window_id=str(window.id),
        user_id=str(window.user_id),
        window_start=window.window_start.isoformat(),
        window_end=window.window_end.isoformat(),
        source=window.source,
        samples_hash=window.samples_hash,
        created_at=window.created_at.isoformat(),
    )


def _estimate_to_record(estimate: StateEstimate) -> StateEstimateRecord:
    return StateEstimateRecord(
        estimate_id=str(estimate.id),
        user_id=str(estimate.user_id),
        state_label=estimate.state_label,
        confidence=estimate.confidence,
        model_version=estimate.model_version,
        inferred_at=estimate.inferred_at.isoformat(),
        created_at=estimate.created_at.isoformat(),
    )


# ---------------------------------------------------------------------------
# Singleton registry (dev/test in-memory; prod binds to SQLAlchemy)
# ---------------------------------------------------------------------------

_signal_repo: SignalWindowRepository = InMemorySignalWindowRepository()
_state_repo: StateEstimateRepository = InMemoryStateEstimateRepository()


def get_signal_window_repository() -> SignalWindowRepository:
    return _signal_repo


def get_state_estimate_repository() -> StateEstimateRepository:
    return _state_repo


def reset_signal_repositories() -> None:
    global _signal_repo, _state_repo
    _signal_repo = InMemorySignalWindowRepository()
    _state_repo = InMemoryStateEstimateRepository()

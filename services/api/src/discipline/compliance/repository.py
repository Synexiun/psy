"""Compliance repository — consent and quick-erase storage.

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

from discipline.compliance.models import Consent, QuickEraseRequest


@dataclass(frozen=True, slots=True)
class ConsentRecord:
    """Plain data object returned by the repository."""

    consent_id: str
    user_id: str
    consent_type: str
    version: str
    granted_at: str
    ip_address_hash: str | None


@dataclass(frozen=True, slots=True)
class QuickEraseRecord:
    """Plain data object returned by the repository."""

    request_id: str
    user_id: str
    status: str
    requested_at: str
    completed_at: str | None
    error_detail: str | None


class ConsentRepository(Protocol):
    """Protocol for consent storage backends."""

    async def grant(
        self,
        *,
        user_id: str,
        consent_type: str,
        version: str,
        ip_address_hash: str | None,
    ) -> ConsentRecord:
        ...

    async def latest(self, user_id: str, consent_type: str) -> ConsentRecord | None:
        ...


class QuickEraseRepository(Protocol):
    """Protocol for quick-erase storage backends."""

    async def create(self, *, user_id: str) -> QuickEraseRecord:
        ...

    async def get_latest(self, user_id: str) -> QuickEraseRecord | None:
        ...


# ---------------------------------------------------------------------------
# In-memory stubs
# ---------------------------------------------------------------------------


class InMemoryConsentRepository:
    """Thread-safe in-memory store for tests and local dev."""

    def __init__(self) -> None:
        self._consents: dict[str, ConsentRecord] = {}

    async def grant(
        self,
        *,
        user_id: str,
        consent_type: str,
        version: str,
        ip_address_hash: str | None,
    ) -> ConsentRecord:
        from uuid import uuid4

        now = datetime.now(UTC).isoformat()
        record = ConsentRecord(
            consent_id=str(uuid4()),
            user_id=user_id,
            consent_type=consent_type,
            version=version,
            granted_at=now,
            ip_address_hash=ip_address_hash,
        )
        key = f"{user_id}:{consent_type}"
        self._consents[key] = record
        return record

    async def latest(self, user_id: str, consent_type: str) -> ConsentRecord | None:
        key = f"{user_id}:{consent_type}"
        return self._consents.get(key)


class InMemoryQuickEraseRepository:
    """Thread-safe in-memory store for tests and local dev."""

    def __init__(self) -> None:
        self._requests: dict[str, QuickEraseRecord] = {}

    async def create(self, *, user_id: str) -> QuickEraseRecord:
        from uuid import uuid4

        now = datetime.now(UTC).isoformat()
        record = QuickEraseRecord(
            request_id=str(uuid4()),
            user_id=user_id,
            status="pending",
            requested_at=now,
            completed_at=None,
            error_detail=None,
        )
        self._requests[record.request_id] = record
        return record

    async def get_latest(self, user_id: str) -> QuickEraseRecord | None:
        results = [r for r in self._requests.values() if r.user_id == user_id]
        if not results:
            return None
        results.sort(key=lambda r: r.requested_at, reverse=True)
        return results[0]


# ---------------------------------------------------------------------------
# SQLAlchemy implementations
# ---------------------------------------------------------------------------


class SQLAlchemyConsentRepository:
    """Production consent storage backed by PostgreSQL."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def grant(
        self,
        *,
        user_id: str,
        consent_type: str,
        version: str,
        ip_address_hash: str | None,
    ) -> ConsentRecord:
        from uuid import UUID

        consent = Consent(
            user_id=UUID(user_id),
            consent_type=consent_type,
            version=version,
            ip_address_hash=ip_address_hash,
        )
        self._session.add(consent)
        await self._session.flush()
        return _consent_to_record(consent)

    async def latest(self, user_id: str, consent_type: str) -> ConsentRecord | None:
        from uuid import UUID

        result = await self._session.execute(
            select(Consent)
            .where(
                Consent.user_id == UUID(user_id),
                Consent.consent_type == consent_type,
            )
            .order_by(Consent.granted_at.desc())
            .limit(1)
        )
        consent = result.scalar_one_or_none()
        return _consent_to_record(consent) if consent else None


class SQLAlchemyQuickEraseRepository:
    """Production quick-erase storage backed by PostgreSQL."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, *, user_id: str) -> QuickEraseRecord:
        from uuid import UUID

        request = QuickEraseRequest(
            user_id=UUID(user_id),
            status="pending",
        )
        self._session.add(request)
        await self._session.flush()
        return _quick_erase_to_record(request)

    async def get_latest(self, user_id: str) -> QuickEraseRecord | None:
        from uuid import UUID

        result = await self._session.execute(
            select(QuickEraseRequest)
            .where(QuickEraseRequest.user_id == UUID(user_id))
            .order_by(QuickEraseRequest.requested_at.desc())
            .limit(1)
        )
        request = result.scalar_one_or_none()
        return _quick_erase_to_record(request) if request else None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _consent_to_record(consent: Consent) -> ConsentRecord:
    return ConsentRecord(
        consent_id=str(consent.id),
        user_id=str(consent.user_id),
        consent_type=consent.consent_type,
        version=consent.version,
        granted_at=consent.granted_at.isoformat(),
        ip_address_hash=consent.ip_address_hash,
    )


def _quick_erase_to_record(request: QuickEraseRequest) -> QuickEraseRecord:
    return QuickEraseRecord(
        request_id=str(request.id),
        user_id=str(request.user_id),
        status=request.status,
        requested_at=request.requested_at.isoformat(),
        completed_at=request.completed_at.isoformat() if request.completed_at else None,
        error_detail=request.error_detail,
    )


# ---------------------------------------------------------------------------
# Singleton registry (dev/test in-memory; prod binds to SQLAlchemy)
# ---------------------------------------------------------------------------

_consent_repo: ConsentRepository = InMemoryConsentRepository()
_quick_erase_repo: QuickEraseRepository = InMemoryQuickEraseRepository()


def get_consent_repository() -> ConsentRepository:
    return _consent_repo


def get_quick_erase_repository() -> QuickEraseRepository:
    return _quick_erase_repo


def reset_compliance_repositories() -> None:
    global _consent_repo, _quick_erase_repo
    _consent_repo = InMemoryConsentRepository()
    _quick_erase_repo = InMemoryQuickEraseRepository()

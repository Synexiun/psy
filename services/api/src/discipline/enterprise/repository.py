"""Enterprise repository — org and clinician link storage.

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

from discipline.enterprise.models import ClinicianLink, Organization


@dataclass(frozen=True, slots=True)
class OrganizationRecord:
    """Plain data object returned by the repository."""

    org_id: str
    name: str
    slug: str
    tier: str
    status: str
    created_at: str
    updated_at: str


@dataclass(frozen=True, slots=True)
class ClinicianLinkRecord:
    """Plain data object returned by the repository."""

    link_id: str
    org_id: str
    clinician_user_id: str
    patient_user_id: str
    status: str
    invited_at: str
    consented_at: str | None
    revoked_at: str | None
    created_at: str
    updated_at: str


class OrganizationRepository(Protocol):
    """Protocol for organization storage backends."""

    async def create(
        self,
        *,
        name: str,
        slug: str,
        tier: str,
    ) -> OrganizationRecord:
        ...

    async def get_by_id(self, org_id: str) -> OrganizationRecord | None:
        ...

    async def list_all(self, *, limit: int = 50) -> list[OrganizationRecord]:
        ...


class ClinicianLinkRepository(Protocol):
    """Protocol for clinician link storage backends."""

    async def create(
        self,
        *,
        org_id: str,
        clinician_user_id: str,
        patient_user_id: str,
    ) -> ClinicianLinkRecord:
        ...

    async def get_by_id(self, link_id: str) -> ClinicianLinkRecord | None:
        ...

    async def list_by_clinician(
        self,
        clinician_user_id: str,
        *,
        limit: int = 50,
    ) -> list[ClinicianLinkRecord]:
        ...

    async def list_by_patient(
        self,
        patient_user_id: str,
        *,
        limit: int = 50,
    ) -> list[ClinicianLinkRecord]:
        ...

    async def list_by_org(
        self,
        org_id: str,
        *,
        limit: int = 50,
    ) -> list[ClinicianLinkRecord]:
        ...

    async def update_status(
        self,
        link_id: str,
        *,
        status: str,
        consented_at: str | None = None,
        revoked_at: str | None = None,
    ) -> ClinicianLinkRecord | None:
        ...


# ---------------------------------------------------------------------------
# In-memory stubs
# ---------------------------------------------------------------------------


class InMemoryOrganizationRepository:
    """Thread-safe in-memory store for tests and local dev."""

    def __init__(self) -> None:
        self._orgs: dict[str, OrganizationRecord] = {}

    async def create(
        self,
        *,
        name: str,
        slug: str,
        tier: str,
    ) -> OrganizationRecord:
        from uuid import uuid4

        now = datetime.now(UTC).isoformat()
        record = OrganizationRecord(
            org_id=str(uuid4()),
            name=name,
            slug=slug,
            tier=tier,
            status="active",
            created_at=now,
            updated_at=now,
        )
        self._orgs[record.org_id] = record
        return record

    async def get_by_id(self, org_id: str) -> OrganizationRecord | None:
        return self._orgs.get(org_id)

    async def list_all(self, *, limit: int = 50) -> list[OrganizationRecord]:
        results = sorted(self._orgs.values(), key=lambda r: r.created_at, reverse=True)
        return results[:limit]


class InMemoryClinicianLinkRepository:
    """Thread-safe in-memory store for tests and local dev."""

    def __init__(self) -> None:
        self._links: dict[str, ClinicianLinkRecord] = {}

    async def create(
        self,
        *,
        org_id: str,
        clinician_user_id: str,
        patient_user_id: str,
    ) -> ClinicianLinkRecord:
        from uuid import uuid4

        now = datetime.now(UTC).isoformat()
        record = ClinicianLinkRecord(
            link_id=str(uuid4()),
            org_id=org_id,
            clinician_user_id=clinician_user_id,
            patient_user_id=patient_user_id,
            status="pending",
            invited_at=now,
            consented_at=None,
            revoked_at=None,
            created_at=now,
            updated_at=now,
        )
        self._links[record.link_id] = record
        return record

    async def get_by_id(self, link_id: str) -> ClinicianLinkRecord | None:
        return self._links.get(link_id)

    async def list_by_clinician(
        self,
        clinician_user_id: str,
        *,
        limit: int = 50,
    ) -> list[ClinicianLinkRecord]:
        results = [
            r for r in self._links.values()
            if r.clinician_user_id == clinician_user_id
        ]
        results.sort(key=lambda r: r.created_at, reverse=True)
        return results[:limit]

    async def list_by_patient(
        self,
        patient_user_id: str,
        *,
        limit: int = 50,
    ) -> list[ClinicianLinkRecord]:
        results = [
            r for r in self._links.values()
            if r.patient_user_id == patient_user_id
        ]
        results.sort(key=lambda r: r.created_at, reverse=True)
        return results[:limit]

    async def list_by_org(
        self,
        org_id: str,
        *,
        limit: int = 50,
    ) -> list[ClinicianLinkRecord]:
        results = [
            r for r in self._links.values()
            if r.org_id == org_id
        ]
        results.sort(key=lambda r: r.created_at, reverse=True)
        return results[:limit]

    async def update_status(
        self,
        link_id: str,
        *,
        status: str,
        consented_at: str | None = None,
        revoked_at: str | None = None,
    ) -> ClinicianLinkRecord | None:
        record = self._links.get(link_id)
        if record is None:
            return None
        updated = ClinicianLinkRecord(
            link_id=record.link_id,
            org_id=record.org_id,
            clinician_user_id=record.clinician_user_id,
            patient_user_id=record.patient_user_id,
            status=status,
            invited_at=record.invited_at,
            consented_at=consented_at,
            revoked_at=revoked_at,
            created_at=record.created_at,
            updated_at=datetime.now(UTC).isoformat(),
        )
        self._links[link_id] = updated
        return updated


# ---------------------------------------------------------------------------
# SQLAlchemy implementations
# ---------------------------------------------------------------------------


class SQLAlchemyOrganizationRepository:
    """Production organization storage backed by PostgreSQL."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        name: str,
        slug: str,
        tier: str,
    ) -> OrganizationRecord:
        org = Organization(
            name=name,
            slug=slug,
            tier=tier,
            status="active",
        )
        self._session.add(org)
        await self._session.flush()
        return _org_to_record(org)

    async def get_by_id(self, org_id: str) -> OrganizationRecord | None:
        from uuid import UUID

        result = await self._session.execute(
            select(Organization).where(Organization.id == UUID(org_id))
        )
        org = result.scalar_one_or_none()
        return _org_to_record(org) if org else None

    async def list_all(self, *, limit: int = 50) -> list[OrganizationRecord]:
        result = await self._session.execute(
            select(Organization)
            .order_by(Organization.created_at.desc())
            .limit(limit)
        )
        return [_org_to_record(o) for o in result.scalars().all()]


class SQLAlchemyClinicianLinkRepository:
    """Production clinician link storage backed by PostgreSQL."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        org_id: str,
        clinician_user_id: str,
        patient_user_id: str,
    ) -> ClinicianLinkRecord:
        from uuid import UUID

        link = ClinicianLink(
            org_id=UUID(org_id),
            clinician_user_id=UUID(clinician_user_id),
            patient_user_id=UUID(patient_user_id),
            status="pending",
        )
        self._session.add(link)
        await self._session.flush()
        return _link_to_record(link)

    async def get_by_id(self, link_id: str) -> ClinicianLinkRecord | None:
        from uuid import UUID

        result = await self._session.execute(
            select(ClinicianLink).where(ClinicianLink.id == UUID(link_id))
        )
        link = result.scalar_one_or_none()
        return _link_to_record(link) if link else None

    async def list_by_clinician(
        self,
        clinician_user_id: str,
        *,
        limit: int = 50,
    ) -> list[ClinicianLinkRecord]:
        from uuid import UUID

        result = await self._session.execute(
            select(ClinicianLink)
            .where(ClinicianLink.clinician_user_id == UUID(clinician_user_id))
            .order_by(ClinicianLink.created_at.desc())
            .limit(limit)
        )
        return [_link_to_record(l) for l in result.scalars().all()]

    async def list_by_patient(
        self,
        patient_user_id: str,
        *,
        limit: int = 50,
    ) -> list[ClinicianLinkRecord]:
        from uuid import UUID

        result = await self._session.execute(
            select(ClinicianLink)
            .where(ClinicianLink.patient_user_id == UUID(patient_user_id))
            .order_by(ClinicianLink.created_at.desc())
            .limit(limit)
        )
        return [_link_to_record(l) for l in result.scalars().all()]

    async def list_by_org(
        self,
        org_id: str,
        *,
        limit: int = 50,
    ) -> list[ClinicianLinkRecord]:
        from uuid import UUID

        result = await self._session.execute(
            select(ClinicianLink)
            .where(ClinicianLink.org_id == UUID(org_id))
            .order_by(ClinicianLink.created_at.desc())
            .limit(limit)
        )
        return [_link_to_record(l) for l in result.scalars().all()]

    async def update_status(
        self,
        link_id: str,
        *,
        status: str,
        consented_at: str | None = None,
        revoked_at: str | None = None,
    ) -> ClinicianLinkRecord | None:
        from uuid import UUID

        result = await self._session.execute(
            select(ClinicianLink).where(ClinicianLink.id == UUID(link_id))
        )
        link = result.scalar_one_or_none()
        if link is None:
            return None
        link.status = status
        if consented_at is not None:
            link.consented_at = datetime.fromisoformat(consented_at)
        if revoked_at is not None:
            link.revoked_at = datetime.fromisoformat(revoked_at)
        await self._session.flush()
        return _link_to_record(link)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _org_to_record(org: Organization) -> OrganizationRecord:
    return OrganizationRecord(
        org_id=str(org.id),
        name=org.name,
        slug=org.slug,
        tier=org.tier,
        status=org.status,
        created_at=org.created_at.isoformat(),
        updated_at=org.updated_at.isoformat(),
    )


def _link_to_record(link: ClinicianLink) -> ClinicianLinkRecord:
    return ClinicianLinkRecord(
        link_id=str(link.id),
        org_id=str(link.org_id),
        clinician_user_id=str(link.clinician_user_id),
        patient_user_id=str(link.patient_user_id),
        status=link.status,
        invited_at=link.invited_at.isoformat(),
        consented_at=link.consented_at.isoformat() if link.consented_at else None,
        revoked_at=link.revoked_at.isoformat() if link.revoked_at else None,
        created_at=link.created_at.isoformat(),
        updated_at=link.updated_at.isoformat(),
    )


# ---------------------------------------------------------------------------
# Singleton registry (dev/test in-memory; prod binds to SQLAlchemy)
# ---------------------------------------------------------------------------

_org_repo: OrganizationRepository = InMemoryOrganizationRepository()
_link_repo: ClinicianLinkRepository = InMemoryClinicianLinkRepository()


def get_organization_repository() -> OrganizationRepository:
    return _org_repo


def get_clinician_link_repository() -> ClinicianLinkRepository:
    return _link_repo


def reset_enterprise_repositories() -> None:
    global _org_repo, _link_repo
    _org_repo = InMemoryOrganizationRepository()
    _link_repo = InMemoryClinicianLinkRepository()

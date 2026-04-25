"""Tests for discipline.enterprise.repository — org and clinician-link in-memory stores.

Covers methods not exercised by test_enterprise_service.py:
- InMemoryOrganizationRepository.get_by_id: match, None for unknown
- InMemoryClinicianLinkRepository.get_by_id: match, None for unknown
- InMemoryClinicianLinkRepository.list_by_clinician: filters correctly, ignores other clinicians
- InMemoryClinicianLinkRepository.list_by_patient: filters correctly, ignores other patients
- InMemoryClinicianLinkRepository.list_by_org: filters correctly, ignores other orgs
- InMemoryClinicianLinkRepository.update_status: status/consented_at/revoked_at set, unknown → None
- reset_enterprise_repositories: clears both repos
"""

from __future__ import annotations

import uuid

import pytest

from discipline.enterprise.repository import (
    ClinicianLinkRecord,
    InMemoryClinicianLinkRepository,
    InMemoryOrganizationRepository,
    OrganizationRecord,
    reset_enterprise_repositories,
)


@pytest.fixture(autouse=True)
def _reset() -> None:
    reset_enterprise_repositories()


async def _org(
    repo: InMemoryOrganizationRepository,
    *,
    name: str = "Acme Clinic",
    slug: str = "acme",
    tier: str = "enterprise",
) -> OrganizationRecord:
    return await repo.create(name=name, slug=slug, tier=tier)


async def _link(
    repo: InMemoryClinicianLinkRepository,
    *,
    org_id: str = "org-1",
    clinician_user_id: str = "clin-1",
    patient_user_id: str = "pat-1",
) -> ClinicianLinkRecord:
    return await repo.create(
        org_id=org_id,
        clinician_user_id=clinician_user_id,
        patient_user_id=patient_user_id,
    )


# ---------------------------------------------------------------------------
# InMemoryOrganizationRepository.get_by_id
# ---------------------------------------------------------------------------


class TestOrgGetById:
    @pytest.mark.asyncio
    async def test_returns_org_for_matching_id(self) -> None:
        repo = InMemoryOrganizationRepository()
        org = await _org(repo)
        result = await repo.get_by_id(org.org_id)
        assert result is not None
        assert result.org_id == org.org_id

    @pytest.mark.asyncio
    async def test_returns_none_for_unknown_id(self) -> None:
        repo = InMemoryOrganizationRepository()
        result = await repo.get_by_id(str(uuid.uuid4()))
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_correct_org_among_multiple(self) -> None:
        repo = InMemoryOrganizationRepository()
        o1 = await _org(repo, name="Alpha Clinic", slug="alpha")
        o2 = await _org(repo, name="Beta Clinic", slug="beta")
        result = await repo.get_by_id(o1.org_id)
        assert result is not None
        assert result.name == "Alpha Clinic"
        assert o2.org_id != o1.org_id


# ---------------------------------------------------------------------------
# InMemoryClinicianLinkRepository.get_by_id
# ---------------------------------------------------------------------------


class TestLinkGetById:
    @pytest.mark.asyncio
    async def test_returns_link_for_matching_id(self) -> None:
        repo = InMemoryClinicianLinkRepository()
        link = await _link(repo)
        result = await repo.get_by_id(link.link_id)
        assert result is not None
        assert result.link_id == link.link_id

    @pytest.mark.asyncio
    async def test_returns_none_for_unknown_id(self) -> None:
        repo = InMemoryClinicianLinkRepository()
        result = await repo.get_by_id(str(uuid.uuid4()))
        assert result is None


# ---------------------------------------------------------------------------
# list_by_clinician
# ---------------------------------------------------------------------------


class TestListByClinician:
    @pytest.mark.asyncio
    async def test_returns_links_for_matching_clinician(self) -> None:
        repo = InMemoryClinicianLinkRepository()
        await _link(repo, clinician_user_id="clin-a", patient_user_id="p1")
        await _link(repo, clinician_user_id="clin-a", patient_user_id="p2")
        results = await repo.list_by_clinician("clin-a")
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_excludes_other_clinicians_links(self) -> None:
        repo = InMemoryClinicianLinkRepository()
        await _link(repo, clinician_user_id="clin-a", patient_user_id="p1")
        await _link(repo, clinician_user_id="clin-b", patient_user_id="p2")
        results = await repo.list_by_clinician("clin-a")
        assert len(results) == 1
        assert results[0].clinician_user_id == "clin-a"

    @pytest.mark.asyncio
    async def test_returns_empty_for_unknown_clinician(self) -> None:
        repo = InMemoryClinicianLinkRepository()
        results = await repo.list_by_clinician("unknown-clin")
        assert results == []

    @pytest.mark.asyncio
    async def test_respects_limit(self) -> None:
        repo = InMemoryClinicianLinkRepository()
        for i in range(5):
            await _link(repo, clinician_user_id="clin-x", patient_user_id=f"p-{i}")
        results = await repo.list_by_clinician("clin-x", limit=3)
        assert len(results) == 3


# ---------------------------------------------------------------------------
# list_by_patient
# ---------------------------------------------------------------------------


class TestListByPatient:
    @pytest.mark.asyncio
    async def test_returns_links_for_matching_patient(self) -> None:
        repo = InMemoryClinicianLinkRepository()
        await _link(repo, clinician_user_id="clin-1", patient_user_id="pat-x")
        await _link(repo, clinician_user_id="clin-2", patient_user_id="pat-x")
        results = await repo.list_by_patient("pat-x")
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_excludes_other_patients_links(self) -> None:
        repo = InMemoryClinicianLinkRepository()
        await _link(repo, patient_user_id="pat-a")
        await _link(repo, patient_user_id="pat-b")
        results = await repo.list_by_patient("pat-a")
        assert len(results) == 1
        assert results[0].patient_user_id == "pat-a"

    @pytest.mark.asyncio
    async def test_returns_empty_for_unknown_patient(self) -> None:
        repo = InMemoryClinicianLinkRepository()
        results = await repo.list_by_patient("ghost-patient")
        assert results == []


# ---------------------------------------------------------------------------
# list_by_org
# ---------------------------------------------------------------------------


class TestListByOrg:
    @pytest.mark.asyncio
    async def test_returns_links_for_matching_org(self) -> None:
        repo = InMemoryClinicianLinkRepository()
        await _link(repo, org_id="org-alpha", clinician_user_id="c1", patient_user_id="p1")
        await _link(repo, org_id="org-alpha", clinician_user_id="c2", patient_user_id="p2")
        results = await repo.list_by_org("org-alpha")
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_excludes_other_org_links(self) -> None:
        repo = InMemoryClinicianLinkRepository()
        await _link(repo, org_id="org-a")
        await _link(repo, org_id="org-b")
        results = await repo.list_by_org("org-a")
        assert len(results) == 1
        assert results[0].org_id == "org-a"

    @pytest.mark.asyncio
    async def test_returns_empty_for_unknown_org(self) -> None:
        repo = InMemoryClinicianLinkRepository()
        results = await repo.list_by_org("org-nonexistent")
        assert results == []


# ---------------------------------------------------------------------------
# update_status
# ---------------------------------------------------------------------------


class TestUpdateStatus:
    @pytest.mark.asyncio
    async def test_sets_status(self) -> None:
        repo = InMemoryClinicianLinkRepository()
        link = await _link(repo)
        assert link.status == "pending"
        updated = await repo.update_status(link.link_id, status="consented")
        assert updated is not None
        assert updated.status == "consented"

    @pytest.mark.asyncio
    async def test_sets_consented_at(self) -> None:
        repo = InMemoryClinicianLinkRepository()
        link = await _link(repo)
        updated = await repo.update_status(
            link.link_id,
            status="consented",
            consented_at="2026-04-25T10:00:00+00:00",
        )
        assert updated is not None
        assert updated.consented_at == "2026-04-25T10:00:00+00:00"

    @pytest.mark.asyncio
    async def test_sets_revoked_at(self) -> None:
        repo = InMemoryClinicianLinkRepository()
        link = await _link(repo)
        updated = await repo.update_status(
            link.link_id,
            status="revoked",
            revoked_at="2026-04-25T12:00:00+00:00",
        )
        assert updated is not None
        assert updated.revoked_at == "2026-04-25T12:00:00+00:00"

    @pytest.mark.asyncio
    async def test_preserves_other_fields(self) -> None:
        repo = InMemoryClinicianLinkRepository()
        link = await _link(
            repo, org_id="org-99", clinician_user_id="clin-99", patient_user_id="pat-99"
        )
        updated = await repo.update_status(link.link_id, status="consented")
        assert updated is not None
        assert updated.org_id == "org-99"
        assert updated.clinician_user_id == "clin-99"
        assert updated.patient_user_id == "pat-99"

    @pytest.mark.asyncio
    async def test_returns_none_for_unknown_id(self) -> None:
        repo = InMemoryClinicianLinkRepository()
        result = await repo.update_status(str(uuid.uuid4()), status="consented")
        assert result is None

    @pytest.mark.asyncio
    async def test_updated_status_persists(self) -> None:
        repo = InMemoryClinicianLinkRepository()
        link = await _link(repo)
        await repo.update_status(link.link_id, status="revoked")
        fetched = await repo.get_by_id(link.link_id)
        assert fetched is not None
        assert fetched.status == "revoked"

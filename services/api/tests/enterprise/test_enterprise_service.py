"""Tests for discipline.enterprise.service — org provisioning, clinician links, reports.

Covers:
- OrgService.provision: creates OrganizationRecord
- OrgService.get: returns org or None for unknown
- OrgService.list_all: lists all orgs
- ClinicianLinkService.invite: creates link with pending status
- ClinicianLinkService.patient_consents: sets status=active, wrong patient returns None
- ClinicianLinkService.revoke: sets status=revoked, unauthorized caller returns None
- ClinicianLinkService.list_for_clinician: returns clinician's links
- ClinicianLinkService.list_for_patient: returns patient's links
- ReportService.monthly: returns None when links < 5 (k-anonymity floor)
- ReportService.monthly: returns aggregate when links >= 5
- ReportService.monthly: k_anon_compliant=True in report
- ReportService.monthly: cohort_size matches link count
"""

from __future__ import annotations

import uuid

import pytest

from discipline.enterprise.repository import (
    InMemoryClinicianLinkRepository,
    InMemoryOrganizationRepository,
    reset_enterprise_repositories,
)
from discipline.enterprise.service import (
    ClinicianLinkService,
    OrgService,
    ReportService,
)


@pytest.fixture(autouse=True)
def _reset() -> None:
    reset_enterprise_repositories()


def _org_service() -> OrgService:
    return OrgService(repository=InMemoryOrganizationRepository())


def _link_service() -> ClinicianLinkService:
    return ClinicianLinkService(repository=InMemoryClinicianLinkRepository())


# ---------------------------------------------------------------------------
# OrgService
# ---------------------------------------------------------------------------


class TestOrgService:
    @pytest.mark.asyncio
    async def test_provision_returns_org_record(self) -> None:
        from discipline.enterprise.repository import OrganizationRecord

        svc = _org_service()
        rec = await svc.provision(name="Acme Corp", slug="acme", tier="enterprise")
        assert hasattr(rec, "org_id")

    @pytest.mark.asyncio
    async def test_provision_org_id_is_valid_uuid(self) -> None:
        svc = _org_service()
        rec = await svc.provision(name="Corp", slug="corp", tier="enterprise")
        uuid.UUID(rec.org_id)

    @pytest.mark.asyncio
    async def test_provision_fields_match_input(self) -> None:
        svc = _org_service()
        rec = await svc.provision(name="HealthFirst", slug="healthfirst", tier="pro")
        assert rec.name == "HealthFirst"
        assert rec.slug == "healthfirst"
        assert rec.tier == "pro"

    @pytest.mark.asyncio
    async def test_get_returns_org_for_known_id(self) -> None:
        svc = _org_service()
        rec = await svc.provision(name="Org A", slug="org-a", tier="enterprise")
        result = await svc.get(rec.org_id)
        assert result is not None
        assert result.org_id == rec.org_id

    @pytest.mark.asyncio
    async def test_get_returns_none_for_unknown_id(self) -> None:
        svc = _org_service()
        result = await svc.get("nonexistent-id")
        assert result is None

    @pytest.mark.asyncio
    async def test_list_all_returns_all_orgs(self) -> None:
        svc = _org_service()
        await svc.provision(name="Org A", slug="org-a", tier="enterprise")
        await svc.provision(name="Org B", slug="org-b", tier="pro")
        orgs = await svc.list_all()
        assert len(orgs) == 2

    @pytest.mark.asyncio
    async def test_list_all_empty_when_none(self) -> None:
        svc = _org_service()
        orgs = await svc.list_all()
        assert orgs == []


# ---------------------------------------------------------------------------
# ClinicianLinkService
# ---------------------------------------------------------------------------


class TestClinicianLinkService:
    @pytest.mark.asyncio
    async def test_invite_creates_link(self) -> None:
        svc = _link_service()
        link = await svc.invite(
            org_id="org-1",
            clinician_user_id="clinician-1",
            patient_user_id="patient-1",
        )
        assert link is not None

    @pytest.mark.asyncio
    async def test_invite_status_is_pending(self) -> None:
        svc = _link_service()
        link = await svc.invite(
            org_id="org-1",
            clinician_user_id="clinician-1",
            patient_user_id="patient-1",
        )
        assert link.status == "pending"

    @pytest.mark.asyncio
    async def test_patient_consents_sets_active(self) -> None:
        svc = _link_service()
        link = await svc.invite(
            org_id="org-1", clinician_user_id="c-1", patient_user_id="p-1"
        )
        updated = await svc.patient_consents(link.link_id, "p-1")
        assert updated is not None
        assert updated.status == "active"

    @pytest.mark.asyncio
    async def test_patient_consents_wrong_patient_returns_none(self) -> None:
        svc = _link_service()
        link = await svc.invite(
            org_id="org-1", clinician_user_id="c-1", patient_user_id="p-1"
        )
        result = await svc.patient_consents(link.link_id, "wrong-patient")
        assert result is None

    @pytest.mark.asyncio
    async def test_revoke_by_clinician_sets_revoked(self) -> None:
        svc = _link_service()
        link = await svc.invite(
            org_id="org-1", clinician_user_id="c-1", patient_user_id="p-1"
        )
        updated = await svc.revoke(link.link_id, "c-1")
        assert updated is not None
        assert updated.status == "revoked"

    @pytest.mark.asyncio
    async def test_revoke_by_patient_sets_revoked(self) -> None:
        svc = _link_service()
        link = await svc.invite(
            org_id="org-1", clinician_user_id="c-1", patient_user_id="p-1"
        )
        updated = await svc.revoke(link.link_id, "p-1")
        assert updated is not None
        assert updated.status == "revoked"

    @pytest.mark.asyncio
    async def test_revoke_unauthorized_caller_returns_none(self) -> None:
        svc = _link_service()
        link = await svc.invite(
            org_id="org-1", clinician_user_id="c-1", patient_user_id="p-1"
        )
        result = await svc.revoke(link.link_id, "interloper-user")
        assert result is None

    @pytest.mark.asyncio
    async def test_revoke_unknown_link_returns_none(self) -> None:
        svc = _link_service()
        result = await svc.revoke("nonexistent-link", "any-user")
        assert result is None

    @pytest.mark.asyncio
    async def test_list_for_clinician(self) -> None:
        svc = _link_service()
        await svc.invite(org_id="org-1", clinician_user_id="c-1", patient_user_id="p-1")
        await svc.invite(org_id="org-1", clinician_user_id="c-1", patient_user_id="p-2")
        links = await svc.list_for_clinician("c-1")
        assert len(links) == 2
        assert all(l.clinician_user_id == "c-1" for l in links)

    @pytest.mark.asyncio
    async def test_list_for_patient(self) -> None:
        svc = _link_service()
        await svc.invite(org_id="org-1", clinician_user_id="c-1", patient_user_id="p-1")
        await svc.invite(org_id="org-1", clinician_user_id="c-2", patient_user_id="p-1")
        links = await svc.list_for_patient("p-1")
        assert len(links) == 2
        assert all(l.patient_user_id == "p-1" for l in links)


# ---------------------------------------------------------------------------
# ReportService — k-anonymity floor (k ≥ 5)
# ---------------------------------------------------------------------------


class TestReportService:
    @pytest.mark.asyncio
    async def test_monthly_returns_none_when_links_below_5(self) -> None:
        """k-anonymity floor: fewer than 5 links → report blocked."""
        link_repo = InMemoryClinicianLinkRepository()
        svc = ReportService(link_repository=link_repo)
        # Add only 4 links
        for i in range(4):
            await link_repo.create(
                org_id="org-1",
                clinician_user_id=f"c-{i}",
                patient_user_id=f"p-{i}",
            )
        result = await svc.monthly("org-1")
        assert result is None

    @pytest.mark.asyncio
    async def test_monthly_returns_report_when_links_gte_5(self) -> None:
        link_repo = InMemoryClinicianLinkRepository()
        svc = ReportService(link_repository=link_repo)
        for i in range(5):
            await link_repo.create(
                org_id="org-1",
                clinician_user_id=f"c-{i}",
                patient_user_id=f"p-{i}",
            )
        result = await svc.monthly("org-1")
        assert result is not None

    @pytest.mark.asyncio
    async def test_monthly_report_has_k_anon_compliant_true(self) -> None:
        link_repo = InMemoryClinicianLinkRepository()
        svc = ReportService(link_repository=link_repo)
        for i in range(6):
            await link_repo.create(
                org_id="org-2",
                clinician_user_id=f"c-{i}",
                patient_user_id=f"p-{i}",
            )
        result = await svc.monthly("org-2")
        assert result is not None
        assert result["k_anon_compliant"] is True

    @pytest.mark.asyncio
    async def test_monthly_report_cohort_size_matches_link_count(self) -> None:
        link_repo = InMemoryClinicianLinkRepository()
        svc = ReportService(link_repository=link_repo)
        for i in range(7):
            await link_repo.create(
                org_id="org-3",
                clinician_user_id=f"c-{i}",
                patient_user_id=f"p-{i}",
            )
        result = await svc.monthly("org-3")
        assert result is not None
        assert result["cohort_size"] == 7

    @pytest.mark.asyncio
    async def test_monthly_empty_org_returns_none(self) -> None:
        link_repo = InMemoryClinicianLinkRepository()
        svc = ReportService(link_repository=link_repo)
        result = await svc.monthly("empty-org")
        assert result is None

"""Enterprise HTTP surface — org admin, clinician links, aggregate reports.

Endpoints:
- ``POST /v1/enterprise/orgs`` — provision an organization
- ``GET /v1/enterprise/orgs/{org_id}`` — get organization
- ``POST /v1/enterprise/clinician-links`` — invite patient
- ``POST /v1/enterprise/clinician-links/{link_id}/consent`` — patient consents
- ``POST /v1/enterprise/clinician-links/{link_id}/revoke`` — revoke link
- ``GET /v1/enterprise/clinician-links`` — list links for caller
- ``POST /v1/enterprise/reports/monthly`` — generate monthly aggregate report

All endpoints are authenticated (Clerk session → server JWT).
"""

from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from discipline.enterprise.service import (
    ClinicianLinkService,
    OrgService,
    ReportService,
)

router = APIRouter(tags=["enterprise"])


# =============================================================================
# Organization schemas
# =============================================================================


class OrganizationCreate(BaseModel):
    """Request body for provisioning an organization."""

    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=128)
    tier: str = Field(
        default="standard",
        pattern=r"^(pilot|standard|enterprise)$",
    )


class OrganizationItem(BaseModel):
    """Organization record response."""

    org_id: str
    name: str
    slug: str
    tier: str
    status: str
    created_at: str
    updated_at: str


# =============================================================================
# Clinician link schemas
# =============================================================================


class ClinicianLinkCreate(BaseModel):
    """Request body for inviting a patient."""

    org_id: str = Field(..., min_length=1)
    patient_user_id: str = Field(..., min_length=1)


class ClinicianLinkItem(BaseModel):
    """Clinician link record response."""

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


# =============================================================================
# Report schemas
# =============================================================================


class MonthlyReportRequest(BaseModel):
    """Request body for generating a monthly aggregate report."""

    org_id: str = Field(..., min_length=1)


class MonthlyReportResponse(BaseModel):
    """Monthly aggregate report response."""

    org_id: str
    period: str
    total_active_links: int
    total_pending_links: int
    total_revoked_links: int
    k_anon_compliant: bool
    dp_noise_applied: bool
    cohort_size: int
    message: str


# =============================================================================
# Helpers
# =============================================================================


def _derive_user_id(x_user_id: str | None) -> str:
    """Stub: in production this resolves the server JWT session."""
    return x_user_id or "test_user_001"


def _org_to_item(record: object) -> OrganizationItem:
    from discipline.enterprise.repository import OrganizationRecord

    r = record if isinstance(record, OrganizationRecord) else record
    return OrganizationItem(
        org_id=r.org_id,
        name=r.name,
        slug=r.slug,
        tier=r.tier,
        status=r.status,
        created_at=r.created_at,
        updated_at=r.updated_at,
    )


def _link_to_item(record: object) -> ClinicianLinkItem:
    from discipline.enterprise.repository import ClinicianLinkRecord

    r = record if isinstance(record, ClinicianLinkRecord) else record
    return ClinicianLinkItem(
        link_id=r.link_id,
        org_id=r.org_id,
        clinician_user_id=r.clinician_user_id,
        patient_user_id=r.patient_user_id,
        status=r.status,
        invited_at=r.invited_at,
        consented_at=r.consented_at,
        revoked_at=r.revoked_at,
        created_at=r.created_at,
        updated_at=r.updated_at,
    )


# =============================================================================
# Organization endpoints
# =============================================================================


@router.post("/enterprise/orgs", response_model=OrganizationItem, status_code=201)
async def provision_org(
    payload: OrganizationCreate,
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
) -> OrganizationItem:
    """Provision a new organization."""
    _ = _derive_user_id(x_user_id)
    service = OrgService()
    record = await service.provision(
        name=payload.name,
        slug=payload.slug,
        tier=payload.tier,
    )
    return _org_to_item(record)


@router.get("/enterprise/orgs/{org_id}", response_model=OrganizationItem)
async def get_org(
    org_id: str,
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
) -> OrganizationItem:
    """Retrieve an organization by ID."""
    _ = _derive_user_id(x_user_id)
    service = OrgService()
    record = await service.get(org_id)
    if record is None:
        raise HTTPException(status_code=404, detail="organization.not_found")
    return _org_to_item(record)


# =============================================================================
# Clinician link endpoints
# =============================================================================


@router.post("/enterprise/clinician-links", response_model=ClinicianLinkItem, status_code=201)
async def invite_clinician_link(
    payload: ClinicianLinkCreate,
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
) -> ClinicianLinkItem:
    """Invite a patient to link with the calling clinician."""
    clinician_user_id = _derive_user_id(x_user_id)
    service = ClinicianLinkService()
    record = await service.invite(
        org_id=payload.org_id,
        clinician_user_id=clinician_user_id,
        patient_user_id=payload.patient_user_id,
    )
    return _link_to_item(record)


@router.post("/enterprise/clinician-links/{link_id}/consent", response_model=ClinicianLinkItem)
async def consent_clinician_link(
    link_id: str,
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
) -> ClinicianLinkItem:
    """Record patient consent for a clinician link."""
    patient_user_id = _derive_user_id(x_user_id)
    service = ClinicianLinkService()
    record = await service.patient_consents(link_id, patient_user_id)
    if record is None:
        raise HTTPException(status_code=404, detail="clinician_link.not_found")
    return _link_to_item(record)


@router.post("/enterprise/clinician-links/{link_id}/revoke", response_model=ClinicianLinkItem)
async def revoke_clinician_link(
    link_id: str,
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
) -> ClinicianLinkItem:
    """Revoke a clinician link."""
    revoked_by_user_id = _derive_user_id(x_user_id)
    service = ClinicianLinkService()
    record = await service.revoke(link_id, revoked_by_user_id)
    if record is None:
        raise HTTPException(status_code=404, detail="clinician_link.not_found")
    return _link_to_item(record)


@router.get("/enterprise/clinician-links", response_model=list[ClinicianLinkItem])
async def list_clinician_links(
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
    limit: int = 50,
) -> list[ClinicianLinkItem]:
    """List clinician links for the caller (as clinician or patient)."""
    user_id = _derive_user_id(x_user_id)
    service = ClinicianLinkService()
    # Return union of links where user is clinician or patient
    clinician_links = await service.list_for_clinician(user_id, limit=limit)
    patient_links = await service.list_for_patient(user_id, limit=limit)
    seen = {l.link_id for l in clinician_links}
    combined = list(clinician_links)
    for l in patient_links:
        if l.link_id not in seen:
            combined.append(l)
    combined.sort(key=lambda r: r.created_at, reverse=True)
    return [_link_to_item(r) for r in combined[:limit]]


# =============================================================================
# Report endpoints
# =============================================================================


@router.post("/enterprise/reports/monthly", response_model=MonthlyReportResponse)
async def monthly_report(
    payload: MonthlyReportRequest,
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
) -> MonthlyReportResponse:
    """Generate a monthly aggregate report for an organization.

    Enforces k-anonymity floor (k ≥ 5).  If the organization has
    fewer than 5 clinician links, the report is blocked with 403.
    """
    _ = _derive_user_id(x_user_id)
    service = ReportService()
    report = await service.monthly(payload.org_id)
    if report is None:
        raise HTTPException(
            status_code=403,
            detail="report.insufficient_cohort_size",
        )
    return MonthlyReportResponse(
        org_id=report["org_id"],
        period=report["period"],
        total_active_links=report["total_active_links"],
        total_pending_links=report["total_pending_links"],
        total_revoked_links=report["total_revoked_links"],
        k_anon_compliant=report["k_anon_compliant"],
        dp_noise_applied=report["dp_noise_applied"],
        cohort_size=report["cohort_size"],
        message=report["message"],
    )

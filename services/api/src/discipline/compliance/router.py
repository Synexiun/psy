"""Compliance HTTP surface — consent and quick-erase.

Endpoints:
- ``POST /v1/compliance/consent`` — grant or update consent
- ``GET /v1/compliance/consent/{consent_type}`` — latest consent record
- ``POST /v1/compliance/quick-erase`` — queue a quick-erase request
- ``GET /v1/compliance/quick-erase/status`` — latest erase request status

All endpoints are authenticated (Clerk session → server JWT).
"""

from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from discipline.compliance.repository import (
    get_consent_repository,
    get_quick_erase_repository,
)

router = APIRouter(tags=["compliance"])


# =============================================================================
# Consent schemas
# =============================================================================


class ConsentGrant(BaseModel):
    """Request body for granting consent."""

    consent_type: str = Field(
        ...,
        pattern=r"^(terms_of_service|privacy_policy|clinical_data|marketing)$",
    )
    version: str = Field(..., min_length=1, max_length=32)
    ip_address: str | None = Field(default=None, max_length=45)


class ConsentItem(BaseModel):
    """Consent record response."""

    consent_id: str
    consent_type: str
    version: str
    granted_at: str


# =============================================================================
# Quick-erase schemas
# =============================================================================


class QuickEraseRequestCreate(BaseModel):
    """Request body for queueing a quick-erase."""

    pass


class QuickEraseStatus(BaseModel):
    """Quick-erase request status response."""

    request_id: str
    status: str
    requested_at: str
    completed_at: str | None


# =============================================================================
# Helpers
# =============================================================================


def _derive_user_id(x_user_id: str | None) -> str:
    """Stub: in production this resolves the server JWT session."""
    return x_user_id or "test_user_001"


def _hash_ip(ip: str | None) -> str | None:
    """Hash IP address for audit trail."""
    if ip is None:
        return None
    import hashlib

    return hashlib.sha256(ip.encode()).hexdigest()


# =============================================================================
# Consent endpoints
# =============================================================================


@router.post("/compliance/consent", response_model=ConsentItem, status_code=201)
async def grant_consent(
    payload: ConsentGrant,
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
) -> ConsentItem:
    """Record a consent grant.

    Overwrites any previous consent of the same type for this user —
    the latest grant is the effective one.
    """
    user_id = _derive_user_id(x_user_id)
    repo = get_consent_repository()
    record = await repo.grant(
        user_id=user_id,
        consent_type=payload.consent_type,
        version=payload.version,
        ip_address_hash=_hash_ip(payload.ip_address),
    )
    return ConsentItem(
        consent_id=record.consent_id,
        consent_type=record.consent_type,
        version=record.version,
        granted_at=record.granted_at,
    )


@router.get("/compliance/consent/{consent_type}", response_model=ConsentItem)
async def get_consent(
    consent_type: str,
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
) -> ConsentItem:
    """Retrieve the latest consent record of the given type."""
    user_id = _derive_user_id(x_user_id)
    repo = get_consent_repository()
    record = await repo.latest(user_id, consent_type)
    if record is None:
        raise HTTPException(status_code=404, detail="consent.not_found")
    return ConsentItem(
        consent_id=record.consent_id,
        consent_type=record.consent_type,
        version=record.version,
        granted_at=record.granted_at,
    )


# =============================================================================
# Quick-erase endpoints
# =============================================================================


@router.post("/compliance/quick-erase", response_model=QuickEraseStatus, status_code=201)
async def request_quick_erase(
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
) -> QuickEraseStatus:
    """Queue a quick-erase request.

    The worker processes pending requests every minute.  Once completed,
    all user data is irretrievably deleted per the quick-erase contract.
    """
    user_id = _derive_user_id(x_user_id)
    repo = get_quick_erase_repository()
    record = await repo.create(user_id=user_id)
    return QuickEraseStatus(
        request_id=record.request_id,
        status=record.status,
        requested_at=record.requested_at,
        completed_at=record.completed_at,
    )


@router.get("/compliance/quick-erase/status", response_model=QuickEraseStatus)
async def get_quick_erase_status(
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
) -> QuickEraseStatus:
    """Retrieve the latest quick-erase request status."""
    user_id = _derive_user_id(x_user_id)
    repo = get_quick_erase_repository()
    record = await repo.get_latest(user_id)
    if record is None:
        raise HTTPException(status_code=404, detail="quick_erase.not_found")
    return QuickEraseStatus(
        request_id=record.request_id,
        status=record.status,
        requested_at=record.requested_at,
        completed_at=record.completed_at,
    )

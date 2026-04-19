"""Reports HTTP surface — clinician + user-export + enterprise endpoints.

The clinician-bundle endpoint is the **PHI boundary** for this surface
(CLAUDE.md Rule #11): it serves identifiable clinical data to a clinician's
session, so it must:

1. Opt in to the PHI boundary by declaring
   ``dependencies=[Depends(mark_phi_boundary)]``.  The
   :class:`PhiBoundaryMiddleware` then appends ``X-Phi-Boundary: 1`` to
   the response, so the log correlator can cross-reference the audit
   stream with the app stream.
2. Emit an audit-stream event (HMAC-Merkle chained, 6-year retention)
   recording who read what, when.

The user-export and enterprise routes remain stubs pending repository
integration; the clinician-bundle endpoint is the one fully-live FHIR
surface as of 2026-04-18.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from discipline.shared.http import mark_phi_boundary
from discipline.shared.logging import LogStream, get_stream_logger

from .enterprise import (
    K_ANONYMITY_THRESHOLD,
    OrgEngagementSnapshot,
    build_org_engagement,
)
from .fhir_bundle import BundleType, assemble_bundle
from .fhir_observation import (
    LOINC_CODES,
    ObservationSpec,
    UnsupportedInstrumentError,
)
from .user_export import (
    EmptyExportError,
    NonUtcTimestampError,
    UserExportPayload,
    build_json_archive,
)

router = APIRouter(prefix="/reports", tags=["reports"])

_audit = get_stream_logger(LogStream.AUDIT)


# ---- Request models --------------------------------------------------------


class ObservationSpecModel(BaseModel):
    """Wire-format mirror of :class:`ObservationSpec`.

    Validation here is intentionally narrow — instrument keys are
    canonical-form (``phq9``, ``gad7``, …) and must match a pinned LOINC
    code.  Unknown instruments fail at the assembler with a 422.
    """

    patient_reference: str = Field(
        ...,
        description="FHIR patient reference, e.g. 'Patient/abc123'",
        min_length=1,
    )
    instrument: str = Field(..., description="Canonical instrument key")
    score: int = Field(..., ge=0, description="Total score, non-negative")
    effective: datetime = Field(..., description="Timezone-aware UTC datetime")
    safety_item_positive: bool = Field(
        default=False,
        description="True when a safety item (e.g. PHQ-9 item 9) fired",
    )
    status: Literal["final", "amended"] = "final"

    def to_dataclass(self) -> ObservationSpec:
        return ObservationSpec(
            patient_reference=self.patient_reference,
            instrument=self.instrument,
            score=self.score,
            effective=self.effective,
            safety_item_positive=self.safety_item_positive,
            status=self.status,
        )


class OrgEngagementSnapshotModel(BaseModel):
    """Wire-format mirror of :class:`OrgEngagementSnapshot`.

    Aggregate-only per CLAUDE.md — the two ``n_*`` cohort fields are
    what feed the k-anonymity gate inside :func:`build_org_engagement`.
    Negative cohort sizes raise at the service layer (caller bug).
    """

    org_id: str = Field(..., min_length=1)
    active_members_count_7d: int = Field(..., ge=0)
    tools_used_count_7d: int = Field(..., ge=0)
    wellbeing_index_mean: float = Field(..., ge=0.0, le=100.0)
    n_active_members_7d: int = Field(..., ge=0)
    n_wellbeing_reporters: int = Field(..., ge=0)

    def to_dataclass(self) -> OrgEngagementSnapshot:
        return OrgEngagementSnapshot(
            org_id=self.org_id,
            active_members_count_7d=self.active_members_count_7d,
            tools_used_count_7d=self.tools_used_count_7d,
            wellbeing_index_mean=self.wellbeing_index_mean,
            n_active_members_7d=self.n_active_members_7d,
            n_wellbeing_reporters=self.n_wellbeing_reporters,
        )


class ClinicianBundleRequest(BaseModel):
    """Request payload for the clinician FHIR bundle endpoint.

    The clinician selects which patient observations to include (typically
    a date range over a single patient's psychometric history); the
    backend renders them into a single Bundle for export to an EHR.
    """

    clinician_id: str = Field(
        ...,
        min_length=1,
        description="Clinician requesting the bundle (used in audit events)",
    )
    patient_id: str = Field(
        ...,
        min_length=1,
        description="Patient whose observations are being exported",
    )
    observations: list[ObservationSpecModel] = Field(
        ..., min_length=1, description="One spec per Observation in the Bundle"
    )
    bundle_type: BundleType = Field(
        default="collection",
        description="'collection' for plain export; 'document' if a Composition is added",
    )
    correlation_id: str | None = Field(
        default=None,
        description="Optional caller-supplied UUID for audit cross-reference",
    )


# ---- Endpoints --------------------------------------------------------------


@router.post(
    "/fhir/clinician-bundle",
    status_code=200,
    summary="Clinician FHIR R4 export bundle (PHI surface)",
    dependencies=[Depends(mark_phi_boundary)],
)
async def generate_fhir_clinician_bundle(
    payload: ClinicianBundleRequest,
) -> dict[str, object]:
    """Render a FHIR R4 Bundle of Observations for a clinician's patient.

    PHI surface — Rule #11 + Rule #6:
    - Sets ``X-Phi-Boundary: 1`` so log correlator + CSP enforcer can
      identify this response as PHI-bearing.
    - Emits a ``phi.access`` event to the audit stream containing
      ``actor_id`` (clinician), ``subject_id`` (patient), the count of
      observations exported, and the resulting Bundle identifier.  The
      audit stream is HMAC-Merkle-chained with 6-year retention.

    The audit emission happens BEFORE the bundle is assembled.  If the
    assembler raises (e.g., unknown instrument), the audit record still
    fires — a denied or failed PHI access attempt is itself an auditable
    event.  We log the outcome (``ok`` / ``error``) on a second event
    after the assembly outcome is known.

    Returns the Bundle JSON dict directly (no envelope) so clients can
    feed it straight into a FHIR client library.
    """
    # Pre-emit: record the access intent.  Even if the assembler raises,
    # the auditor knows clinician X attempted to read patient Y's data.
    _audit.info(
        "phi.access.attempt",
        actor_id=payload.clinician_id,
        actor_role="clinician",
        subject_id=payload.patient_id,
        resource="fhir.bundle",
        resource_count=len(payload.observations),
        correlation_id=payload.correlation_id,
    )

    try:
        bundle = assemble_bundle(
            [obs.to_dataclass() for obs in payload.observations],
            identifier=payload.correlation_id,
            bundle_type=payload.bundle_type,
        )
    except UnsupportedInstrumentError as exc:
        _audit.warning(
            "phi.access.error",
            actor_id=payload.clinician_id,
            subject_id=payload.patient_id,
            error="unsupported_instrument",
            detail=str(exc),
        )
        raise HTTPException(
            status_code=422,
            detail={
                "code": "validation.unsupported_instrument",
                "message": str(exc),
                "supported_instruments": sorted(LOINC_CODES.keys()),
            },
        ) from exc
    except ValueError as exc:
        _audit.warning(
            "phi.access.error",
            actor_id=payload.clinician_id,
            subject_id=payload.patient_id,
            error="validation_error",
            detail=str(exc),
        )
        raise HTTPException(
            status_code=422,
            detail={
                "code": "validation.invalid_payload",
                "message": str(exc),
            },
        ) from exc

    # Post-emit: record the successful read with the resulting Bundle id.
    bundle_identifier = bundle.get("identifier", {})
    bundle_id_value = (
        bundle_identifier.get("value")
        if isinstance(bundle_identifier, dict)
        else None
    )
    _audit.info(
        "phi.access.ok",
        actor_id=payload.clinician_id,
        actor_role="clinician",
        subject_id=payload.patient_id,
        resource="fhir.bundle",
        bundle_identifier=bundle_id_value,
        observation_count=len(payload.observations),
    )

    # PHI boundary header is added by PhiBoundaryMiddleware on the way
    # out — this endpoint opts in via ``Depends(mark_phi_boundary)`` at
    # the route declaration.
    return bundle


@router.post("/clinical/pdf")
async def generate_clinical_pdf() -> dict[str, str]:
    """Queue a clinical PDF. Returns 202 on accept."""
    raise HTTPException(status_code=501, detail={"code": "not_implemented"})


class UserExportRequest(BaseModel):
    """Request payload for the HIPAA Right-of-Access archive endpoint.

    The caller supplies ``user_id`` + the pre-fetched section snapshots
    (profile, scores, events, etc.) rather than the endpoint pulling
    them from repositories directly — this inversion keeps the router
    testable in isolation and makes it trivial for a background export
    worker to reuse the same endpoint shape once repositories land.

    ``actor_id`` (the session user making the request) MUST equal
    ``user_id`` (the subject whose data is being exported).  Self-access
    only — a clinician exporting a patient's data uses the
    clinician-bundle endpoint instead.  Mismatch is a 403.

    Journal plaintext is NOT accepted here (and will be rejected at the
    builder if a client tries): server cannot see journal plaintext by
    design, so the archive excludes it.
    """

    actor_id: str = Field(..., min_length=1, description="Session user id")
    user_id: str = Field(
        ..., min_length=1, description="Subject whose data is being exported"
    )
    locale: str = Field(..., min_length=2, description="User locale, e.g. 'en'")
    profile: dict[str, Any] = Field(default_factory=dict)
    psychometric_scores: list[dict[str, Any]] = Field(default_factory=list)
    intervention_events: list[dict[str, Any]] = Field(default_factory=list)
    resilience_streak: dict[str, Any] = Field(default_factory=dict)
    safety_events: list[dict[str, Any]] = Field(default_factory=list)
    consents: list[dict[str, Any]] = Field(default_factory=list)


@router.post(
    "/user/export",
    status_code=200,
    summary="HIPAA Right-of-Access user data archive (PHI surface)",
    dependencies=[Depends(mark_phi_boundary)],
)
async def request_user_export(payload: UserExportRequest) -> dict[str, object]:
    """Produce a structured JSON archive of the user's data.

    PHI surface per Rule #11: the archive contains identifiable user
    data (profile, scores, event history), so the response must carry
    ``X-Phi-Boundary: 1`` for the log correlator to cross-reference the
    audit trail against the app-stream request log.

    Rule #6 — Audit emission pattern (mirrors the clinician-bundle):
    - ``user.export.attempt`` before build.
    - ``user.export.ok`` on success with the manifest sha256.
    - ``user.export.error`` on validation failure with the error kind.

    Journal plaintext: absent by design.  See ``user_export.py``
    docstring and Docs/Whitepapers/03_Privacy_Architecture.md §E2E.

    PDF summary: deferred.  ``pdf_summary`` will be populated by the
    downstream render worker; this endpoint returns it as an empty
    base64-encoded string so the schema is stable.
    """
    # Self-access enforcement: actor_id MUST equal user_id.  A clinician
    # exporting a patient's data uses POST /reports/fhir/clinician-bundle,
    # not this endpoint.  We audit the attempt before the 403 so a
    # cross-user export attempt is visible in the audit trail.
    if payload.actor_id != payload.user_id:
        _audit.warning(
            "user.export.error",
            actor_id=payload.actor_id,
            subject_id=payload.user_id,
            error="actor_subject_mismatch",
        )
        raise HTTPException(
            status_code=403,
            detail={
                "code": "auth.self_access_only",
                "message": (
                    "user export is self-access only; clinicians should "
                    "use POST /reports/fhir/clinician-bundle instead"
                ),
            },
        )

    _audit.info(
        "user.export.attempt",
        actor_id=payload.actor_id,
        actor_role="user",
        subject_id=payload.user_id,
        resource="user.export.archive",
    )

    now = datetime.now(timezone.utc)
    export_payload = UserExportPayload(
        user_id=payload.user_id,
        requested_at=now,
        generated_at=now,
        locale=payload.locale,
        profile=payload.profile,
        psychometric_scores=payload.psychometric_scores,
        intervention_events=payload.intervention_events,
        resilience_streak=payload.resilience_streak,
        safety_events=payload.safety_events,
        consents=payload.consents,
    )

    try:
        bundle = build_json_archive(export_payload)
    except EmptyExportError as exc:
        _audit.warning(
            "user.export.error",
            actor_id=payload.actor_id,
            subject_id=payload.user_id,
            error="empty_export",
            detail=str(exc),
        )
        raise HTTPException(
            status_code=422,
            detail={
                "code": "validation.empty_export",
                "message": (
                    "no data sections populated; "
                    "a user with zero records should not hit this endpoint"
                ),
            },
        ) from exc
    except NonUtcTimestampError as exc:  # pragma: no cover — server-controlled
        # Server generates the timestamps, so this path is not reachable
        # via the wire.  Kept for defense-in-depth if a future refactor
        # accepts caller-supplied timestamps.
        _audit.warning(
            "user.export.error",
            actor_id=payload.actor_id,
            subject_id=payload.user_id,
            error="non_utc_timestamp",
            detail=str(exc),
        )
        raise HTTPException(
            status_code=500,
            detail={"code": "internal.non_utc_timestamp"},
        ) from exc

    _audit.info(
        "user.export.ok",
        actor_id=payload.actor_id,
        actor_role="user",
        subject_id=payload.user_id,
        resource="user.export.archive",
        manifest_sha256=bundle.manifest_sha256,
        archive_size_bytes=len(bundle.json_archive),
    )

    # Return JSON as a decoded string (not raw bytes) so the response
    # is a normal application/json wrapper; clients can re-encode and
    # re-hash to verify the manifest against ``archive_json`` content.
    return {
        "user_id": payload.user_id,
        "manifest_sha256": bundle.manifest_sha256,
        "archive_json": bundle.json_archive.decode("utf-8"),
        "pdf_summary_available": bool(bundle.pdf_summary),
    }


@router.get("/fhir/observations")
async def fhir_observations() -> dict[str, str]:
    """Stub — single-instrument FHIR R4 observation read.

    The live export surface is ``POST /reports/fhir/clinician-bundle``;
    this GET will land later for single-Observation reads (less common
    workflow but useful for diff/sync tools).
    """
    return {"status": "not_implemented"}


@router.post(
    "/enterprise/engagement",
    status_code=200,
    summary="Org engagement aggregate (k-anonymous, non-PHI)",
)
async def enterprise_engagement(
    snapshot: OrgEngagementSnapshotModel,
) -> dict[str, object]:
    """Apply the k ≥ 5 gate to a raw org-engagement snapshot.

    Aggregate-only surface per CLAUDE.md §web-enterprise.  This route
    does **not** carry ``X-Phi-Boundary: 1`` — the data is already
    k-anonymized at the render boundary, so tagging it PHI would dilute
    the header's meaning for downstream correlators.  No audit emission
    either: enterprise aggregates aren't individual PHI access.

    Returns a JSON dict mirroring :class:`OrgEngagement`; suppressed
    cells appear as ``null`` (JSON ``None``).  Clients MUST render
    ``null`` as "insufficient data", not ``0``.
    """
    engagement = build_org_engagement(snapshot.to_dataclass())
    return {
        "org_id": engagement.org_id,
        "active_members_7d": engagement.active_members_7d,
        "tools_used_7d": engagement.tools_used_7d,
        "wellbeing_index": engagement.wellbeing_index,
        "k_anonymity_threshold": K_ANONYMITY_THRESHOLD,
    }

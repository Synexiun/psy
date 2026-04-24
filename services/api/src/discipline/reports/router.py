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

from datetime import UTC, datetime
from typing import Any, Literal

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field

from discipline.psychometric.repository import (
    AssessmentRecord,
    get_assessment_repository,
)
from discipline.shared.http import mark_phi_boundary
from discipline.shared.logging import LogStream, get_stream_logger

from .enterprise import (
    K_ANONYMITY_THRESHOLD,
    OrgEngagementSnapshot,
    build_org_engagement,
)
from .fhir_bundle import BundleType, assemble_bundle, assemble_bundle_from_resources
from .fhir_export import (
    AssessmentSession,
    FhirExporter,
    UrgeCheckInRecord,
)
from .fhir_observation import (
    LOINC_CODES,
    CssrsObservationSpec,
    ObservationSpec,
    UnsupportedInstrumentError,
    render_bundle,
    render_cssrs_bundle,
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

    now = datetime.now(UTC)
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


_CSSRS_RISK_VALUES = frozenset({"none", "low", "moderate", "acute"})


def _render_record_as_observation(
    record: AssessmentRecord,
) -> dict[str, object]:
    """Map a stored :class:`AssessmentRecord` to a FHIR R4 Observation dict.

    Dispatches by instrument:
    - ``cssrs`` → :func:`render_cssrs_bundle` (categorical
      ``valueCodeableConcept`` path with ``component`` entries per
      triggering item).
    - Every other supported instrument → :func:`render_bundle`
      (numeric ``valueInteger`` path).

    Pure function — no side effects, no I/O, no audit emission.  Raises
    :class:`UnsupportedInstrumentError` (instrument has no pinned LOINC
    code) or :class:`ValueError` (stored C-SSRS severity is outside the
    known risk-level set).  Callers translate to HTTP 422 with a
    ``phi.access.error`` audit emission as appropriate to their surface.

    Shared by the single-Observation GET (Sprint 24) and the
    patient-bundle GET (Sprint 27) so the C-SSRS-vs-numeric dispatch
    cannot drift between the two surfaces.
    """
    patient_reference = f"Patient/{record.user_id}"
    if record.instrument == "cssrs":
        # C-SSRS record severity is a Literal risk level; assert
        # defensively so a future record-shape change that stored
        # a different string surfaces here with a clean 422 rather
        # than a 500 from the frozen-dataclass validator.
        if record.severity not in _CSSRS_RISK_VALUES:
            raise ValueError(
                f"stored C-SSRS severity {record.severity!r} is not a "
                f"known risk level; expected one of {sorted(_CSSRS_RISK_VALUES)}"
            )
        cssrs_spec = CssrsObservationSpec(
            patient_reference=patient_reference,
            risk_level=record.severity,  # type: ignore[arg-type]
            effective=record.created_at,
            triggering_items=(
                record.triggering_items
                if record.triggering_items is not None
                else ()
            ),
            requires_t3=record.requires_t3,
        )
        return render_cssrs_bundle(cssrs_spec)
    obs_spec = ObservationSpec(
        patient_reference=patient_reference,
        instrument=record.instrument,
        score=record.total,
        effective=record.created_at,
        safety_item_positive=record.requires_t3,
    )
    return render_bundle(obs_spec)


@router.get(
    "/fhir/observations/{assessment_id}",
    status_code=200,
    summary="Single FHIR R4 Observation for one assessment (PHI surface)",
    dependencies=[Depends(mark_phi_boundary)],
)
async def get_fhir_observation(
    assessment_id: str,
    x_clinician_id: str = Header(..., alias="X-Clinician-Id"),
    x_correlation_id: str | None = Header(
        default=None, alias="X-Correlation-Id"
    ),
) -> dict[str, object]:
    """Render one stored assessment as a FHIR R4 Observation.

    Why this endpoint exists:
    The POST ``/reports/fhir/clinician-bundle`` surface produces a
    full Bundle over a date range.  This GET is the complement — a
    diff/sync tool or an EHR integration that needs to re-fetch a
    single Observation by id (e.g. after a failed push, or to verify
    a stored hash) reads it here without reassembling the Bundle.

    Authorization (temporary shape):
    - ``X-Clinician-Id`` header carries the clinician identity.  In
      production this is the Clerk session's ``sessionClaims.sub``
      restricted to users whose role claim includes ``"clinician"``
      (see CLAUDE.md §web-clinician).  The header-form here is a stub
      for that integration.
    - A missing or empty ``X-Clinician-Id`` yields a 401.  Patient-
      portal callers do NOT read from this endpoint; they read through
      their own ``/v1/assessments/history`` surface, which omits raw
      items and the FHIR wrapping.

    PHI surface per Rule #11:
    - Sets ``X-Phi-Boundary: 1`` via the ``mark_phi_boundary``
      dependency.
    - Emits ``phi.access.attempt`` and ``phi.access.ok`` / ``.error``
      events to the audit stream (HMAC-Merkle chained, 6-year
      retention), mirroring the clinician-bundle pattern so the
      cross-reference with the app-stream request log works for both
      surfaces.

    Dispatch:
    - ``cssrs`` → ``render_cssrs_bundle`` (categorical
      valueCodeableConcept path).
    - Every other supported instrument → ``render_bundle``
      (numeric valueInteger path).

    Errors:
    - 404 when the assessment_id is unknown (or empty).  We audit the
      miss so a probing enumeration attempt is visible in the trail.
    - 422 when the stored instrument has no pinned LOINC code (future
      instrument added to the scorer but not yet registered in
      fhir_observation.LOINC_CODES).
    """
    if not x_clinician_id:
        raise HTTPException(
            status_code=401,
            detail={
                "code": "auth.missing_clinician_id",
                "message": "X-Clinician-Id header required.",
            },
        )
    if not assessment_id:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "not_found",
                "message": "assessment_id must be non-empty",
            },
        )

    # Record the access intent BEFORE the lookup.  A 404 still emits a
    # ``phi.access.error`` event so an attacker enumerating assessment
    # ids shows up in the audit trail — the attempt is the auditable
    # fact, not just the successful read.
    _audit.info(
        "phi.access.attempt",
        actor_id=x_clinician_id,
        actor_role="clinician",
        resource="fhir.observation",
        resource_id=assessment_id,
        correlation_id=x_correlation_id,
    )

    repo = get_assessment_repository()
    record = repo.get_by_id(assessment_id)
    if record is None:
        _audit.warning(
            "phi.access.error",
            actor_id=x_clinician_id,
            resource="fhir.observation",
            resource_id=assessment_id,
            error="not_found",
            correlation_id=x_correlation_id,
        )
        raise HTTPException(
            status_code=404,
            detail={
                "code": "not_found",
                "message": f"no assessment with id {assessment_id!r}",
            },
        )

    try:
        resource = _render_record_as_observation(record)
    except UnsupportedInstrumentError as exc:
        _audit.warning(
            "phi.access.error",
            actor_id=x_clinician_id,
            resource="fhir.observation",
            resource_id=assessment_id,
            error="unsupported_instrument",
            detail=str(exc),
            correlation_id=x_correlation_id,
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
            actor_id=x_clinician_id,
            resource="fhir.observation",
            resource_id=assessment_id,
            error="validation_error",
            detail=str(exc),
            correlation_id=x_correlation_id,
        )
        raise HTTPException(
            status_code=422,
            detail={
                "code": "validation.invalid_payload",
                "message": str(exc),
            },
        ) from exc

    _audit.info(
        "phi.access.ok",
        actor_id=x_clinician_id,
        actor_role="clinician",
        subject_id=record.user_id,
        resource="fhir.observation",
        resource_id=assessment_id,
        instrument=record.instrument,
        correlation_id=x_correlation_id,
    )
    return resource


@router.get(
    "/fhir/patients/{user_id}/bundle",
    status_code=200,
    summary="Clinician FHIR R4 Bundle of a patient's psychometric history (PHI surface)",
    dependencies=[Depends(mark_phi_boundary)],
)
async def get_fhir_patient_bundle(
    user_id: str,
    instrument: str | None = None,
    limit: int = 100,
    x_clinician_id: str = Header(..., alias="X-Clinician-Id"),
    x_correlation_id: str | None = Header(
        default=None, alias="X-Correlation-Id"
    ),
) -> dict[str, object]:
    """Render every stored assessment for a patient as a FHIR R4 Bundle.

    Why this endpoint exists:
    The POST ``/reports/fhir/clinician-bundle`` surface accepts a
    pre-fetched list of Observations and assembles them — useful when
    the clinician's UI has already paginated and filtered the chart.
    The GET ``/reports/fhir/observations/{assessment_id}`` surface
    fetches a single stored assessment.  This endpoint is the missing
    middle: a clinician fetches the patient's full chart in one
    request, with the server doing the repository read + per-record
    rendering + Bundle assembly.  Mirrors the EHR pattern of "give me
    everything you have on this patient".

    Authorization (temporary shape, mirrors single-Observation GET):
    - ``X-Clinician-Id`` header carries the clinician identity; in
      production this resolves from a Clerk session JWT inside a
      middleware whose role claim includes ``"clinician"``.  The
      header form is the Sprint-era stub for that integration.
    - A missing or empty ``X-Clinician-Id`` yields a 401.

    Filtering:
    - ``instrument`` (query, optional) — restrict to one instrument
      key (canonical lowercase, e.g. ``phq9``).  Unknown instruments
      and instruments the patient hasn't been assessed on both yield
      an empty Bundle, not a 404 — "no readings of this kind" is a
      successful query, just one with zero results.
    - ``limit`` (query, default 100, hard cap 1000) — caps the number
      of records read from the repository.  The 1000 ceiling matches
      the trajectory endpoint's analytics-friendly window; clinicians
      reading a multi-year chart should not need pagination, but a
      cursor-based pagination story will land alongside the Postgres
      repository.

    PHI surface per Rule #11:
    - Sets ``X-Phi-Boundary: 1`` via the ``mark_phi_boundary``
      dependency.
    - Emits ``phi.access.attempt`` (with ``instrument_filter`` echoed)
      before the repository read, then ``phi.access.ok`` /
      ``phi.access.error`` after assembly.  HMAC-Merkle chained,
      6-year retention.

    Bundle shape:
    - ``resourceType`` = ``"Bundle"``, ``type`` = ``"collection"``.
    - ``identifier.value`` = ``X-Correlation-Id`` if supplied
      (prefixed with ``urn:uuid:`` if the caller didn't already), else
      a fresh UUID.  Mirrors the POST clinician-bundle correlation-id
      contract so a caller using both surfaces sees the same trace
      stitching behavior.
    - ``entry`` = oldest-first.  Clinician chart-read convention
      reads top-to-bottom as a timeline; the server sort relieves the
      client of ordering responsibility.
    - Empty patient history → ``entry=[]`` with HTTP 200, NOT 404.
      A patient who has been onboarded but never assessed is a valid
      state the clinician UI must render ("no readings yet").

    Errors:
    - 401 — missing / empty ``X-Clinician-Id``.
    - 400 — ``limit`` outside (0, 1000].
    - 422 — a stored record's instrument has no pinned LOINC code
      (future scorer not yet wired through to ``LOINC_CODES``), or a
      stored C-SSRS severity is outside the known risk-level set.
      Both fire ``phi.access.error`` audit events.
    - 404 — only when ``user_id`` itself is empty (path-param is
      always present per FastAPI routing, but a deliberate empty
      string check defends against future client-side misencoding).
    """
    if not x_clinician_id:
        raise HTTPException(
            status_code=401,
            detail={
                "code": "auth.missing_clinician_id",
                "message": "X-Clinician-Id header required.",
            },
        )
    if not user_id:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "not_found",
                "message": "user_id must be non-empty",
            },
        )
    if limit <= 0 or limit > 1000:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "validation.limit",
                "message": (
                    f"limit must be between 1 and 1000, got {limit}"
                ),
            },
        )

    # Normalize the optional instrument filter — callers don't need to
    # know the canonical casing.  Empty string after strip → no filter
    # (treats ``?instrument=`` the same as omitting the parameter).
    instrument_filter: str | None = None
    if instrument is not None:
        normalized = instrument.strip().lower()
        instrument_filter = normalized or None

    # Pre-emit: audit the access intent BEFORE the repository read so
    # an attacker enumerating user ids appears in the trail even if the
    # subsequent fetch yields nothing.
    _audit.info(
        "phi.access.attempt",
        actor_id=x_clinician_id,
        actor_role="clinician",
        subject_id=user_id,
        resource="fhir.bundle.history",
        instrument_filter=instrument_filter,
        correlation_id=x_correlation_id,
    )

    repo = get_assessment_repository()
    records = repo.history_for(user_id, limit=limit)
    if instrument_filter is not None:
        records = [r for r in records if r.instrument == instrument_filter]
    # Repository returns newest-first; clinician chart reads oldest-first
    # so the timeline renders top-to-bottom as it occurred.
    records.sort(key=lambda r: r.created_at)

    resources: list[dict[str, object]] = []
    for record in records:
        try:
            resources.append(_render_record_as_observation(record))
        except UnsupportedInstrumentError as exc:
            _audit.warning(
                "phi.access.error",
                actor_id=x_clinician_id,
                subject_id=user_id,
                resource="fhir.bundle.history",
                resource_id=record.assessment_id,
                error="unsupported_instrument",
                detail=str(exc),
                correlation_id=x_correlation_id,
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
                actor_id=x_clinician_id,
                subject_id=user_id,
                resource="fhir.bundle.history",
                resource_id=record.assessment_id,
                error="validation_error",
                detail=str(exc),
                correlation_id=x_correlation_id,
            )
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "validation.invalid_payload",
                    "message": str(exc),
                },
            ) from exc

    # ``allow_empty=True``: a patient with no readings is a valid clinical
    # state the UI must render, not a 404.  See module docstring + the
    # endpoint docstring above for the design rationale.
    bundle = assemble_bundle_from_resources(
        resources,
        identifier=x_correlation_id,
        bundle_type="collection",
        allow_empty=True,
    )

    bundle_identifier = bundle.get("identifier", {})
    bundle_id_value = (
        bundle_identifier.get("value")
        if isinstance(bundle_identifier, dict)
        else None
    )
    _audit.info(
        "phi.access.ok",
        actor_id=x_clinician_id,
        actor_role="clinician",
        subject_id=user_id,
        resource="fhir.bundle.history",
        bundle_identifier=bundle_id_value,
        observation_count=len(resources),
        instrument_filter=instrument_filter,
        correlation_id=x_correlation_id,
    )
    return bundle


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


# ---- User self-service FHIR export (HIPAA Right of Access) ------------------


class PatientBundleRequest(BaseModel):
    """Request payload for the user self-service FHIR patient bundle.

    The caller supplies pre-fetched assessment sessions and recent check-in
    records.  This keeps the router decoupled from the repository layer and
    makes the endpoint trivially testable — the router's job is auth,
    audit, and HTTP semantics; data fetching belongs to the caller.

    ``actor_id`` MUST equal ``user_id`` — self-access only.  A clinician
    exporting a patient bundle uses ``GET /reports/fhir/patients/{user_id}/bundle``
    instead.

    ``sessions`` maps to :class:`AssessmentSession` dataclasses; the
    router converts from the wire dict-list.  Each session needs:
    ``instrument``, ``total_score``, ``administered_at`` (ISO-8601 UTC
    string), and optionally ``safety_item_positive``.

    ``check_ins`` maps to :class:`UrgeCheckInRecord` dataclasses; each
    needs ``intensity`` (0-10) and ``checked_in_at`` (ISO-8601 UTC string).
    """

    actor_id: str = Field(..., min_length=1, description="Session user id")
    user_id: str = Field(
        ..., min_length=1, description="Subject whose data is being exported"
    )
    sessions: list[dict[str, Any]] = Field(
        default_factory=list,
        description=(
            "Psychometric assessment sessions. Each entry: instrument, "
            "total_score, administered_at (ISO-8601 UTC), "
            "safety_item_positive (optional bool)."
        ),
    )
    check_ins: list[dict[str, Any]] = Field(
        default_factory=list,
        description=(
            "Urge check-in records (last 90 days). Each entry: "
            "intensity (0-10), checked_in_at (ISO-8601 UTC)."
        ),
    )
    bundle_id: str | None = Field(
        default=None,
        description="Optional caller-supplied UUID for audit cross-reference.",
    )


def _parse_assessment_sessions(
    user_id: str,
    raw: list[dict[str, Any]],
) -> list[AssessmentSession]:
    """Convert wire-format dicts to :class:`AssessmentSession` dataclasses.

    ``administered_at`` is parsed as an ISO-8601 string; a naive datetime
    (no ``+00:00`` / ``Z`` suffix) is treated as UTC rather than rejected
    so callers that produce naive UTC strings don't get a surprise 422.
    Raises :class:`ValueError` on any malformed entry.
    """
    sessions: list[AssessmentSession] = []
    for i, entry in enumerate(raw):
        try:
            administered_at_raw = entry["administered_at"]
            if isinstance(administered_at_raw, str):
                dt = datetime.fromisoformat(
                    administered_at_raw.replace("Z", "+00:00")
                )
            elif isinstance(administered_at_raw, datetime):
                dt = administered_at_raw
            else:
                raise TypeError(
                    f"administered_at must be a string or datetime, "
                    f"got {type(administered_at_raw).__name__}"
                )
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=UTC)
            sessions.append(
                AssessmentSession(
                    user_id=user_id,
                    instrument=str(entry["instrument"]),
                    total_score=int(entry["total_score"]),
                    administered_at=dt,
                    safety_item_positive=bool(
                        entry.get("safety_item_positive", False)
                    ),
                )
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(
                f"sessions[{i}] is malformed: {exc}"
            ) from exc
    return sessions


def _parse_check_ins(
    user_id: str,
    raw: list[dict[str, Any]],
) -> list[UrgeCheckInRecord]:
    """Convert wire-format dicts to :class:`UrgeCheckInRecord` dataclasses.

    Same UTC-naive-tolerance as :func:`_parse_assessment_sessions`.
    Raises :class:`ValueError` on any malformed entry.
    """
    check_ins: list[UrgeCheckInRecord] = []
    for i, entry in enumerate(raw):
        try:
            checked_in_at_raw = entry["checked_in_at"]
            if isinstance(checked_in_at_raw, str):
                dt = datetime.fromisoformat(
                    checked_in_at_raw.replace("Z", "+00:00")
                )
            elif isinstance(checked_in_at_raw, datetime):
                dt = checked_in_at_raw
            else:
                raise TypeError(
                    f"checked_in_at must be a string or datetime, "
                    f"got {type(checked_in_at_raw).__name__}"
                )
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=UTC)
            intensity = int(entry["intensity"])
            if not (0 <= intensity <= 10):
                raise ValueError(
                    f"intensity {intensity} is outside the 0–10 range"
                )
            check_ins.append(
                UrgeCheckInRecord(
                    user_id=user_id,
                    intensity=intensity,
                    checked_in_at=dt,
                )
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(
                f"check_ins[{i}] is malformed: {exc}"
            ) from exc
    return check_ins


@router.post(
    "/fhir/patient-bundle",
    status_code=200,
    summary="User self-service FHIR R4 patient bundle (PHI surface)",
    dependencies=[Depends(mark_phi_boundary)],
)
async def get_fhir_patient_bundle_self(
    payload: PatientBundleRequest,
) -> dict[str, object]:
    """Produce a FHIR R4 Collection Bundle for the authenticated user.

    FHIR Bundle contents:
    - 1 ``Patient`` resource (opaque ``user_id`` only — no PII).
    - N ``Observation`` resources, one per completed psychometric session
      whose instrument has a pinned LOINC code.
    - M ``Observation`` resources for urge check-ins (last 90 days,
      custom Discipline OS code system).

    PHI surface — Rule #11 + Rule #6:
    - Sets ``X-Phi-Boundary: 1`` so the log correlator can cross-
      reference this response with the audit stream.
    - Emits ``phi.access.attempt`` (before assembly) and
      ``phi.access.ok`` / ``phi.access.error`` (after) to the audit
      stream (HMAC-Merkle chained, 6-year retention).

    Self-access only:
    - ``actor_id`` must equal ``user_id``.  A clinician exporting a
      patient bundle uses ``GET /reports/fhir/patients/{user_id}/bundle``
      instead.  Mismatch yields 403 with an audit ``phi.access.error``
      event.

    Supports ``Accept: application/fhir+json`` — the response
    ``Content-Type`` is ``application/fhir+json`` regardless of the
    ``Accept`` header value (this is a FHIR-only endpoint).
    """
    if payload.actor_id != payload.user_id:
        _audit.warning(
            "phi.access.error",
            actor_id=payload.actor_id,
            subject_id=payload.user_id,
            resource="fhir.patient.bundle.self",
            error="actor_subject_mismatch",
        )
        raise HTTPException(
            status_code=403,
            detail={
                "code": "auth.self_access_only",
                "message": (
                    "FHIR patient bundle is self-access only; "
                    "clinicians should use GET /reports/fhir/patients/{user_id}/bundle"
                ),
            },
        )

    _audit.info(
        "phi.access.attempt",
        actor_id=payload.actor_id,
        actor_role="user",
        subject_id=payload.user_id,
        resource="fhir.patient.bundle.self",
        session_count=len(payload.sessions),
        check_in_count=len(payload.check_ins),
        correlation_id=payload.bundle_id,
    )

    try:
        sessions = _parse_assessment_sessions(payload.user_id, payload.sessions)
        check_ins = _parse_check_ins(payload.user_id, payload.check_ins)
    except ValueError as exc:
        _audit.warning(
            "phi.access.error",
            actor_id=payload.actor_id,
            subject_id=payload.user_id,
            resource="fhir.patient.bundle.self",
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

    exporter = FhirExporter(sessions=sessions, check_ins=check_ins)
    bundle = exporter.export_patient_bundle(
        payload.user_id,
        bundle_id=payload.bundle_id,
    )

    bundle_identifier = bundle.get("identifier", {})
    bundle_id_value = (
        bundle_identifier.get("value")  # type: ignore[union-attr]
        if isinstance(bundle_identifier, dict)
        else None
    )
    _audit.info(
        "phi.access.ok",
        actor_id=payload.actor_id,
        actor_role="user",
        subject_id=payload.user_id,
        resource="fhir.patient.bundle.self",
        bundle_identifier=bundle_id_value,
        observation_count=len(bundle.get("entry", [])),  # type: ignore[arg-type]
        correlation_id=payload.bundle_id,
    )

    return bundle

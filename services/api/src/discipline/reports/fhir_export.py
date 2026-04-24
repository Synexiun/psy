"""FHIR R4 patient-level Bundle export — user self-access surface.

Specification: Docs/Technicals/13_Analytics_Reporting.md §9 (Export —
HIPAA Right of Access) and §5.3 (clinician FHIR surface).

This module is the **self-service** counterpart to the clinician-bundle
surface.  It is called by the authenticated user requesting their own
data; the bundle scope is:

- 1 ``Patient`` resource (opaque user_id only — no name, DOB, or address)
- N ``Observation`` resources, one per completed psychometric assessment
  session (all instruments, all time)
- M ``Observation`` resources for manual urge check-ins, last 90 days

PHI constraints (CLAUDE.md Rules #2, #7, #11):
- The ``Patient`` resource contains ONLY the opaque ``user_id``.  Never
  name, birthDate, address, email, or any other 18 HIPAA identifiers.
  The only reason the Patient resource exists at all is to satisfy the
  FHIR reference model; it carries no additional information.
- Raw biometric samples never appear in exports (they never leave the
  device).
- Voice blob references are never emitted (72 h auto-delete, and they
  are content-hashes / S3 keys, not clinical data).

Data sourcing:
- Psychometric assessments are read from
  :class:`discipline.psychometric.repository.InMemoryAssessmentRepository`
  (the production Postgres repository will be a drop-in swap — same
  interface, same method names).
- Urge check-ins are accepted as a direct list of
  :class:`UrgeCheckInRecord` dataclass instances, typed so the caller
  (the router) can supply them from whatever source is live.  For now
  the check-in surface stores data in memory through
  :class:`InMemoryCheckInRepository`; when that moves to Postgres the
  router passes DB rows mapped to the same dataclass shape.

No LLM in this path.  No network calls.  Pure in-process assembly.

Usage::

    exporter = FhirExporter(
        repo=get_assessment_repository(),
        check_ins=await checkin_repo.recent_for(user_id, days=90),
    )
    bundle = exporter.export_patient_bundle(user_id)
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from .fhir_bundle import assemble_bundle_from_resources
from .fhir_observation import (
    LOINC_CODES,
    ObservationSpec,
    render_bundle,
)

# ---- Custom code system for non-LOINC observations --------------------------

#: Discipline OS FHIR code system URI for proprietary observation codes.
DISCIPLINEOS_CODE_SYSTEM = "https://disciplineos.com/fhir/codes"

#: Code value for the urge-intensity observation type.
URGE_INTENSITY_CODE = "urge-intensity"
URGE_INTENSITY_DISPLAY = "Self-reported urge intensity (0–10)"


# ---- Domain value objects ---------------------------------------------------


@dataclass(frozen=True)
class AssessmentSession:
    """Minimal view of one completed psychometric assessment session.

    Fields mirror :class:`discipline.psychometric.repository.AssessmentRecord`
    so the exporter can work with the existing in-memory repository without
    importing its concrete type (keeping the dependency one-directional and
    testable with plain dataclasses).

    ``instrument`` must be a key in
    :data:`discipline.reports.fhir_observation.LOINC_CODES` or the
    record is skipped (soft-skip, not a hard failure — future instruments
    not yet registered in LOINC_CODES should not block a user's export).
    """

    user_id: str
    instrument: str
    total_score: int
    administered_at: datetime
    safety_item_positive: bool = False


@dataclass(frozen=True)
class UrgeCheckInRecord:
    """Minimal view of one manual urge check-in.

    ``intensity`` is in the 0–10 range per the UI contract (the check-in
    endpoint validates ``ge=0, le=10``).  ``checked_in_at`` must be
    timezone-aware; naive datetimes are rejected at render time.
    """

    user_id: str
    intensity: int
    checked_in_at: datetime


# ---- FHIR resource builders -------------------------------------------------


def _patient_resource(user_id: str) -> dict[str, object]:
    """Render the FHIR R4 Patient resource.

    Privacy contract (CLAUDE.md Rule #2 / 07_Security_Privacy): the
    Patient resource contains ONLY the opaque ``user_id`` as the FHIR
    ``id``.  No ``name``, ``birthDate``, ``address``, ``telecom``,
    ``identifier`` beyond the internal id, or any other 18 HIPAA
    identifiers.

    The ``meta.profile`` pins the base FHIR R4 Patient profile URL so
    receiving systems can validate conformance.
    """
    return {
        "resourceType": "Patient",
        "id": user_id,
        "meta": {
            "profile": [
                "http://hl7.org/fhir/StructureDefinition/Patient"
            ]
        },
    }


def _assessment_observation(
    session: AssessmentSession,
) -> dict[str, object] | None:
    """Render one psychometric session as a FHIR R4 Observation.

    Returns ``None`` when the instrument has no pinned LOINC code
    (soft-skip: the instrument exists in the scorer but has not yet been
    registered in :data:`LOINC_CODES`).  The caller decides whether to
    log the skip or silently omit the record.

    Delegates to :func:`render_bundle` for the LOINC / valueInteger path
    so we reuse the same renderer as the clinician surface — both surfaces
    must be byte-identical for the same underlying record.
    """
    if session.instrument not in LOINC_CODES:
        return None
    spec = ObservationSpec(
        patient_reference=f"Patient/{session.user_id}",
        instrument=session.instrument,
        score=session.total_score,
        effective=session.administered_at,
        safety_item_positive=session.safety_item_positive,
    )
    return render_bundle(spec)


def _urge_observation(
    check_in: UrgeCheckInRecord,
) -> dict[str, object]:
    """Render one urge check-in as a FHIR R4 Observation.

    Uses the Discipline OS proprietary code system (not LOINC) because
    there is no published LOINC code for a 0–10 self-reported urge
    intensity at this granularity.

    ``effectiveDateTime`` is UTC ISO-8601 with a ``Z`` suffix,
    consistent with every other Observation in this bundle.
    ``valueInteger`` carries the intensity (0–10).
    ``category`` uses the standard ``survey`` code to classify it as a
    self-reported measurement alongside the psychometric Observations.
    """
    effective_utc = check_in.checked_in_at.astimezone(UTC)
    effective_str = effective_utc.strftime("%Y-%m-%dT%H:%M:%SZ")

    return {
        "resourceType": "Observation",
        "status": "final",
        "category": [
            {
                "coding": [
                    {
                        "system": (
                            "http://terminology.hl7.org/CodeSystem/"
                            "observation-category"
                        ),
                        "code": "survey",
                        "display": "Survey",
                    }
                ]
            }
        ],
        "code": {
            "coding": [
                {
                    "system": DISCIPLINEOS_CODE_SYSTEM,
                    "code": URGE_INTENSITY_CODE,
                    "display": URGE_INTENSITY_DISPLAY,
                }
            ]
        },
        "subject": {"reference": f"Patient/{check_in.user_id}"},
        "effectiveDateTime": effective_str,
        "valueInteger": check_in.intensity,
    }


# ---- Exporter ---------------------------------------------------------------


class FhirExporter:
    """Assemble a FHIR R4 Collection Bundle for one user.

    Accepts pre-fetched data so it can be used in:
    - The HTTP request cycle (router passes in-memory repo data).
    - A background export worker (same interface, Postgres-backed rows).
    - Unit tests (plain in-memory lists of dataclasses, no DB needed).

    ``sessions`` and ``check_ins`` are accepted at construction time
    rather than via async calls so the exporter itself is a pure
    synchronous function — async I/O is handled by the caller (router or
    worker) which is already in an async context.
    """

    def __init__(
        self,
        sessions: list[AssessmentSession],
        check_ins: list[UrgeCheckInRecord],
    ) -> None:
        self._sessions = sessions
        self._check_ins = check_ins

    def export_patient_bundle(
        self,
        user_id: str,
        *,
        bundle_id: str | None = None,
        timestamp: datetime | None = None,
    ) -> dict[str, object]:
        """Assemble and return a FHIR R4 Bundle of type ``collection``.

        Bundle contents:
        1. One ``Patient`` resource (opaque ``user_id`` only — no PII).
        2. One ``Observation`` per assessment session whose instrument
           has a pinned LOINC code.  Instruments without a LOINC code
           are silently omitted.
        3. One ``Observation`` per urge check-in (custom code system).

        The bundle ``identifier`` defaults to a new UUID; callers
        passing a correlation UUID should supply it as ``bundle_id`` so
        the audit cross-reference works.

        ``timestamp`` defaults to ``datetime.now(UTC)``; tests inject a
        fixed value for deterministic assertions.
        """
        if not user_id:
            raise ValueError("user_id must be non-empty")

        resources: list[dict[str, object]] = []

        # 1. Patient resource — always first per FHIR Bundle convention.
        resources.append(_patient_resource(user_id))

        # 2. Psychometric assessment observations.
        for session in self._sessions:
            obs = _assessment_observation(session)
            if obs is not None:
                resources.append(obs)

        # 3. Urge check-in observations.
        for ci in self._check_ins:
            resources.append(_urge_observation(ci))

        effective_id = bundle_id or str(uuid.uuid4())
        effective_ts = timestamp or datetime.now(tz=UTC)

        return assemble_bundle_from_resources(
            resources,
            identifier=effective_id,
            timestamp=effective_ts,
            bundle_type="collection",
            allow_empty=True,  # A new user with no data still deserves a Patient-only bundle.
        )


__all__ = [
    "DISCIPLINEOS_CODE_SYSTEM",
    "URGE_INTENSITY_CODE",
    "AssessmentSession",
    "FhirExporter",
    "UrgeCheckInRecord",
]

"""FHIR R4 Bundle assembler — multi-Observation clinician export.

Reference: https://hl7.org/fhir/R4/bundle.html

Combines a sequence of :class:`ObservationSpec` into a single FHIR R4 Bundle
resource.  Used when the clinician export endpoint returns more than one
psychometric score at once (e.g. a patient summary covering PHQ-9 + GAD-7 +
PSS-10 over a date range).

Bundle type choice:

- ``collection`` (default) — a simple grouping of resources, no Composition
  required.  This is the right choice for the Discipline OS clinician export
  use case because we are delivering a list of Observations without any
  narrative summary.
- ``document`` — requires a Composition resource as the first entry and
  carries narrative summary semantics.  Not used here; we would add it only
  when the export includes a clinician-authored narrative.

Entry references use the ``urn:uuid:`` form, which is the standard FHIR
convention for internal references inside a single Bundle payload.  Receiving
systems can resolve these references locally without needing a FHIR server.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal

from .fhir_observation import ObservationSpec, render_bundle

BundleType = Literal["collection", "document"]

_DEFAULT_IDENTIFIER_SYSTEM = "urn:ietf:rfc:3986"


@dataclass(frozen=True)
class BundleMeta:
    """Metadata threaded through every generated Bundle.

    ``identifier`` is the UUID that uniquely identifies this Bundle payload
    in audit + tracing systems.  ``timestamp`` is when the Bundle was
    assembled (not when the underlying observations occurred — each
    Observation carries its own ``effectiveDateTime``).
    """

    identifier: str
    timestamp: datetime
    bundle_type: BundleType = "collection"


def _new_urn_uuid() -> str:
    return f"urn:uuid:{uuid.uuid4()}"


def _format_iso8601_z(dt: datetime) -> str:
    if dt.tzinfo is None:
        raise ValueError(
            "Bundle timestamp must be timezone-aware; "
            "naive datetimes are rejected to keep FHIR output unambiguous"
        )
    return dt.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def assemble_bundle_from_resources(
    resources: Sequence[dict[str, object]],
    *,
    identifier: str | None = None,
    timestamp: datetime | None = None,
    bundle_type: BundleType = "collection",
    allow_empty: bool = False,
) -> dict[str, object]:
    """Wrap pre-rendered FHIR resources in a Bundle envelope.

    Two cases this exists for that :func:`assemble_bundle` doesn't cover:

    1. **Mixed renderers** — the clinician chart-read endpoint streams
       both ``Observation`` (numeric, valueInteger) and C-SSRS
       (categorical, valueCodeableConcept) resources into one Bundle.
       :func:`assemble_bundle` only knows how to render
       :class:`ObservationSpec`; this function takes any rendered dict.
    2. **Clinically-valid empty case** — a clinician viewing a patient
       with no recorded readings should see ``entry=[]``, not a 422.
       :func:`assemble_bundle` rejects empty input because for the POST
       clinician-bundle surface an empty list is a caller bug.  Here
       the empty case is opt-in via ``allow_empty=True``.

    Identifier handling matches :func:`assemble_bundle`: a caller-supplied
    string round-trips, with ``urn:uuid:`` prefix normalization.
    """
    if not resources and not allow_empty:
        raise ValueError(
            "cannot assemble an empty Bundle; pass at least one resource "
            "or set allow_empty=True"
        )

    effective_id = identifier or str(uuid.uuid4())
    effective_ts = timestamp or datetime.now(tz=UTC)

    entries: list[dict[str, object]] = [
        {
            "fullUrl": _new_urn_uuid(),
            "resource": resource,
        }
        for resource in resources
    ]

    return {
        "resourceType": "Bundle",
        "identifier": {
            "system": _DEFAULT_IDENTIFIER_SYSTEM,
            "value": f"urn:uuid:{effective_id}"
            if not effective_id.startswith("urn:uuid:")
            else effective_id,
        },
        "type": bundle_type,
        "timestamp": _format_iso8601_z(effective_ts),
        "entry": entries,
    }


def assemble_bundle(
    specs: Sequence[ObservationSpec],
    *,
    identifier: str | None = None,
    timestamp: datetime | None = None,
    bundle_type: BundleType = "collection",
) -> dict[str, object]:
    """Render a FHIR R4 Bundle containing one Observation per spec.

    Raises ``ValueError`` on an empty spec list — an empty Bundle is almost
    always a caller bug (you meant to export *something*) and silently
    shipping ``entry=[]`` would mask the underlying issue.  When the empty
    case is clinically valid (e.g., chart-read of a patient with no
    readings yet), use :func:`assemble_bundle_from_resources` with
    ``allow_empty=True`` instead.

    ``identifier`` defaults to a newly-minted UUID; callers who correlate
    bundles with audit records should pass their own UUID through.
    ``timestamp`` defaults to :meth:`datetime.now(tz=utc)`; tests inject a
    fixed value for deterministic assertions.
    """
    if not specs:
        raise ValueError(
            "cannot assemble an empty Bundle; pass at least one ObservationSpec"
        )

    resources = [render_bundle(spec) for spec in specs]
    return assemble_bundle_from_resources(
        resources,
        identifier=identifier,
        timestamp=timestamp,
        bundle_type=bundle_type,
        allow_empty=False,
    )


__all__ = [
    "BundleMeta",
    "BundleType",
    "assemble_bundle",
    "assemble_bundle_from_resources",
]

"""FHIR R4 Observation bundle generator.

Reference:
- HL7 FHIR R4 Observation resource — https://hl7.org/fhir/R4/observation.html
- LOINC psychometric total-score codes — loinc.org

Each assessment score (PHQ-9, GAD-7, AUDIT-C, …) maps to one FHIR Observation
with the instrument-specific LOINC code in ``code.coding``.  The total score is
emitted as ``valueInteger`` (all supported instruments have integer totals).

Safety-positive observations (PHQ-9 item 9 ≥ 1) carry an ``interpretation``
entry flagging the T3 routing decision.  **The patient narrative is never
included** in the bundle — FHIR is an interop surface, not a transport for
intervention scripts or LLM output.

Conventions:
- ``effectiveDateTime`` is ISO 8601 with a ``Z`` suffix (UTC).  Never localized.
- ``status`` is always ``"final"`` — Discipline OS does not emit amended
  psychometric scores; a re-score is a new Observation, not an amendment.
- ``category`` is always ``survey`` (observation-category codesystem).
- ``subject.reference`` is expected to be a FHIR patient reference string
  such as ``"Patient/abc123"``.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal

# LOINC canonical codes for total scores.  Validated against the LOINC
# database; do not change without confirming against loinc.org and the
# published instrument validation paper.
LOINC_CODES: dict[str, str] = {
    "phq9": "44261-6",
    "gad7": "69737-5",
    "audit": "75626-2",
    "audit_c": "75624-7",
    "dast10": "82667-7",
    "who5": "89708-7",
    "pss10": "93038-1",
    # MDQ carries a published panel code (71354-5) for the Mood Disorder
    # Questionnaire; the emitted ``valueInteger`` is the ``positive_count``
    # (0-13), not a "total score" in the PHQ-9 sense.  LOINC's MDQ panel
    # entry is the correct landing point — receiving systems reading the
    # integer plus the MDQ LOINC code know to interpret it as an endorsed-
    # item count, not a severity sum.
    "mdq": "71354-5",
    # PC-PTSD-5 (Prins 2016) uses LOINC 89204-2 for the total endorsed-item
    # count.  Same semantic as MDQ: ``valueInteger`` carries the
    # ``positive_count`` (0-5), not a weighted sum.  A positive screen
    # (>= 3) is a referral signal for CAPS-5 / PCL-5 / trauma-informed
    # care, not a severity band.
    "pcptsd5": "89204-2",
    # ISI (Bastien 2001) uses LOINC 96899-5 for the total 0-28
    # severity sum.  Unlike MDQ / PC-PTSD-5, ISI's ``valueInteger`` IS
    # a weighted sum (summed 0-4 Likert items); the severity bands
    # (none/subthreshold/moderate/severe) are surfaced separately
    # via valueCodeableConcept on a paired Observation by the
    # reports layer.
    "isi": "96899-5",
    # PCL-5 (Weathers 2013) uses LOINC 91006-2 for the total 0-80
    # severity sum.  Same treatment as ISI: ``valueInteger`` carries
    # the summed 0-4 Likert items; positive_screen (>= 33 per Blevins
    # 2015) is surfaced via valueCodeableConcept on a paired
    # Observation.  A future sprint may register the four DSM-5
    # cluster subscales (B/C/D/E) as separate Observation components
    # under the PCL-5 panel — the cluster codes exist in LOINC but
    # are not emitted yet.
    "pcl5": "91006-2",
}

LOINC_DISPLAY: dict[str, str] = {
    "phq9": "Patient Health Questionnaire 9 item (PHQ-9) total score",
    "gad7": "Generalized Anxiety Disorder 7 item (GAD-7) total score",
    "audit": "Alcohol Use Disorders Identification Test (AUDIT) total score",
    "audit_c": "Alcohol Use Disorders Identification Test - Consumption (AUDIT-C) total score",
    "dast10": "Drug Abuse Screening Test 10 item (DAST-10) total score",
    "who5": "WHO-5 Well-Being Index total score",
    "pss10": "Perceived Stress Scale 10 item (PSS-10) total score",
    "mdq": "Mood Disorder Questionnaire (MDQ) positive item count",
    "pcptsd5": "Primary Care PTSD Screen for DSM-5 (PC-PTSD-5) positive item count",
    "isi": "Insomnia Severity Index (ISI) total score",
    "pcl5": "PTSD Checklist for DSM-5 (PCL-5) total score",
}

# HL7 v3 terminology URIs — pinned as constants so callers (and tests) can
# assert against them.
_LOINC_SYSTEM = "http://loinc.org"
_CATEGORY_SYSTEM = "http://terminology.hl7.org/CodeSystem/observation-category"
_INTERPRETATION_SYSTEM = (
    "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation"
)
_SAFETY_ROUTING_SYSTEM = "http://disciplineos.com/fhir/CodeSystem/safety-routing"

# C-SSRS Screen has no rollup LOINC code at the time of this writing — LOINC
# pins individual item codes and the panel container (73831-0) but not a
# single "Screen risk classification" entry.  We use Discipline-OS-namespaced
# CodeSystem URIs for the observation code, the categorical value, and the
# triggering-item identifiers.  When LOINC publishes an authoritative rollup
# code, replace _CSSRS_OBSERVATION_SYSTEM and update the migration note.
_CSSRS_OBSERVATION_SYSTEM = "http://disciplineos.com/fhir/CodeSystem/cssrs-screen"
_CSSRS_RISK_LEVEL_SYSTEM = "http://disciplineos.com/fhir/CodeSystem/cssrs-risk-level"
_CSSRS_ITEM_SYSTEM = "http://disciplineos.com/fhir/CodeSystem/cssrs-items"

# Risk band → human-readable text emitted in valueCodeableConcept.coding.display.
# Receiving systems that don't recognize the Discipline-OS CodeSystem fall back
# to the display string for human review (per FHIR R4 §2.6.7).
CSSRS_RISK_LEVEL_DISPLAYS: dict[str, str] = {
    "none": "No positive items — no immediate clinical action",
    "low": "Low risk — clinician check-in next visit",
    "moderate": "Moderate risk — supportive intervention recommended",
    "acute": "Acute risk — immediate clinical contact required",
}

# 1-indexed C-SSRS Screen item displays per Posner 2011 Recent/Lifetime form.
# Verbatim short labels — never paraphrase the validated wording in
# clinician-visible UI; these displays are summary labels only.
CSSRS_ITEM_DISPLAYS: dict[int, str] = {
    1: "Wish to be dead (passive ideation)",
    2: "Active suicidal thoughts (no method)",
    3: "Active suicidal thoughts with method (no plan or intent)",
    4: "Active suicidal ideation with some intent to act (no specific plan)",
    5: "Active suicidal ideation with specific plan and intent",
    6: "Suicidal behavior (lifetime)",
}


class UnsupportedInstrumentError(ValueError):
    """Raised when an instrument without a pinned LOINC code is rendered."""


@dataclass(frozen=True)
class ObservationSpec:
    """Inputs required to render a single psychometric Observation.

    ``effective`` should be a timezone-aware datetime; naive datetimes are
    rejected to keep the wire format unambiguous.
    """

    patient_reference: str
    instrument: str
    score: int
    effective: datetime
    safety_item_positive: bool = False
    status: Literal["final", "amended"] = "final"


def _require_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        raise ValueError(
            "ObservationSpec.effective must be timezone-aware; "
            "naive datetimes are rejected to keep FHIR output unambiguous"
        )
    return dt.astimezone(timezone.utc)


def _format_iso8601_z(dt: datetime) -> str:
    """Render as ISO 8601 with ``Z`` suffix for UTC."""
    utc = _require_utc(dt)
    return utc.strftime("%Y-%m-%dT%H:%M:%SZ")


def _code_block(instrument: str) -> dict[str, object]:
    if instrument not in LOINC_CODES:
        raise UnsupportedInstrumentError(
            f"no pinned LOINC code for instrument {instrument!r}"
        )
    return {
        "coding": [
            {
                "system": _LOINC_SYSTEM,
                "code": LOINC_CODES[instrument],
                "display": LOINC_DISPLAY[instrument],
            }
        ]
    }


def _category_block() -> list[dict[str, object]]:
    return [
        {
            "coding": [
                {
                    "system": _CATEGORY_SYSTEM,
                    "code": "survey",
                    "display": "Survey",
                }
            ]
        }
    ]


def _interpretation_block(safety_positive: bool) -> list[dict[str, object]] | None:
    """Emit the ``interpretation`` array only when a safety signal fired.

    We use a Discipline-OS CodeSystem URI rather than repurposing the HL7 v3
    abnormal-flag codes because the semantic is "this result triggered the
    T3 routing workflow", not "this is a clinically abnormal lab value".
    Receiving systems that don't recognize our CodeSystem will still see
    the ``display`` string for human review.
    """
    if not safety_positive:
        return None
    return [
        {
            "coding": [
                {
                    "system": _SAFETY_ROUTING_SYSTEM,
                    "code": "t3-routed",
                    "display": "Safety item positive — routed to T3 clinical path",
                }
            ]
        }
    ]


def render_bundle(spec: ObservationSpec) -> dict[str, object]:
    """Render a single ObservationSpec to a FHIR R4 Observation JSON dict.

    Returns a plain ``dict`` so callers can serialize with ``json.dumps``
    or assemble into a larger Bundle resource without an intermediate model.
    """
    if spec.instrument not in LOINC_CODES:
        raise UnsupportedInstrumentError(
            f"no pinned LOINC code for instrument {spec.instrument!r}"
        )
    if spec.score < 0:
        raise ValueError(f"score must be non-negative, got {spec.score}")

    resource: dict[str, object] = {
        "resourceType": "Observation",
        "status": spec.status,
        "category": _category_block(),
        "code": _code_block(spec.instrument),
        "subject": {"reference": spec.patient_reference},
        "effectiveDateTime": _format_iso8601_z(spec.effective),
        "valueInteger": spec.score,
    }
    interpretation = _interpretation_block(spec.safety_item_positive)
    if interpretation is not None:
        resource["interpretation"] = interpretation
    return resource


# ---- C-SSRS Screen (categorical) -------------------------------------------


@dataclass(frozen=True)
class CssrsObservationSpec:
    """Inputs required to render a C-SSRS Screen FHIR Observation.

    C-SSRS yields a categorical risk band (none/low/moderate/acute) per
    Posner 2011, not a numeric total.  The render output uses
    ``valueCodeableConcept`` (FHIR R4 §6.1.2.7.1) rather than the
    ``valueInteger`` path used by PHQ-9 / GAD-7 / etc.

    ``triggering_items`` carries the 1-indexed item numbers that drove
    the band, mirroring :class:`CssrsResult.triggering_items`.  They are
    emitted as FHIR ``component`` entries so a receiving EHR can review
    *which* items fired without needing the raw item responses.
    """

    patient_reference: str
    risk_level: Literal["none", "low", "moderate", "acute"]
    effective: datetime
    triggering_items: tuple[int, ...] = ()
    requires_t3: bool = False
    status: Literal["final", "amended"] = "final"


def _cssrs_code_block() -> dict[str, object]:
    return {
        "coding": [
            {
                "system": _CSSRS_OBSERVATION_SYSTEM,
                "code": "screen-risk",
                "display": (
                    "Columbia Suicide Severity Rating Scale "
                    "- Screen risk classification"
                ),
            }
        ]
    }


def _cssrs_value_block(risk_level: str) -> dict[str, object]:
    return {
        "coding": [
            {
                "system": _CSSRS_RISK_LEVEL_SYSTEM,
                "code": risk_level,
                "display": CSSRS_RISK_LEVEL_DISPLAYS[risk_level],
            }
        ]
    }


def _cssrs_component_block(triggering_items: tuple[int, ...]) -> list[dict[str, object]]:
    """One FHIR ``component`` entry per triggering item.

    Each component carries a Discipline-OS-coded item identifier and
    ``valueBoolean: true``.  Order is preserved from the input tuple
    so the display reflects the scorer's natural enumeration order
    (low → high item number).
    """
    return [
        {
            "code": {
                "coding": [
                    {
                        "system": _CSSRS_ITEM_SYSTEM,
                        "code": f"item-{i}",
                        "display": CSSRS_ITEM_DISPLAYS[i],
                    }
                ]
            },
            "valueBoolean": True,
        }
        for i in triggering_items
    ]


def render_cssrs_bundle(spec: CssrsObservationSpec) -> dict[str, object]:
    """Render a C-SSRS Screen result to a FHIR R4 Observation JSON dict.

    Validation enforced here:
    - ``risk_level`` must be one of ``none``/``low``/``moderate``/``acute``.
    - ``triggering_items`` values must be in 1..6 (C-SSRS Screen item range).
    - ``effective`` must be timezone-aware (same rule as ``ObservationSpec``).

    When ``requires_t3`` is True, an ``interpretation`` block emits the
    same ``t3-routed`` code used for PHQ-9 item 9 — receiving systems'
    safety-routing branches stay uniform across instruments.
    """
    if spec.risk_level not in CSSRS_RISK_LEVEL_DISPLAYS:
        raise ValueError(
            f"unknown C-SSRS risk_level {spec.risk_level!r}; "
            f"must be one of {sorted(CSSRS_RISK_LEVEL_DISPLAYS)}"
        )
    for item in spec.triggering_items:
        if item < 1 or item > 6:
            raise ValueError(
                f"triggering_items contains out-of-range value {item}; "
                f"C-SSRS Screen items are 1-6"
            )

    resource: dict[str, object] = {
        "resourceType": "Observation",
        "status": spec.status,
        "category": _category_block(),
        "code": _cssrs_code_block(),
        "subject": {"reference": spec.patient_reference},
        "effectiveDateTime": _format_iso8601_z(spec.effective),
        "valueCodeableConcept": _cssrs_value_block(spec.risk_level),
    }
    if spec.triggering_items:
        resource["component"] = _cssrs_component_block(spec.triggering_items)
    if spec.requires_t3:
        # Reuse the safety-routing interpretation block shape — receiving
        # EHRs key off the same `t3-routed` code regardless of source
        # instrument (PHQ-9 item 9 OR C-SSRS items 4/5/6+recency).
        interpretation = _interpretation_block(safety_positive=True)
        if interpretation is not None:
            resource["interpretation"] = interpretation
    return resource


__all__ = [
    "CSSRS_ITEM_DISPLAYS",
    "CSSRS_RISK_LEVEL_DISPLAYS",
    "CssrsObservationSpec",
    "LOINC_CODES",
    "LOINC_DISPLAY",
    "ObservationSpec",
    "UnsupportedInstrumentError",
    "render_bundle",
    "render_cssrs_bundle",
]

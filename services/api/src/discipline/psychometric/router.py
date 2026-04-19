"""Psychometric HTTP surface — PHQ-9, GAD-7, WHO-5, AUDIT, AUDIT-C,
C-SSRS, PSS-10, DAST-10, MDQ, PC-PTSD-5, ISI, PCL-5, OCI-R, PHQ-15,
PACS, BIS-11, Craving VAS, Readiness Ruler, DTCQ-8, URICA.

Single ``POST /v1/assessments`` endpoint dispatches by ``instrument``
key.  Each instrument has its own validated item count and item-value
range; the dispatch layer picks the right scorer and renders a unified
response shape.

Response shape additions over the original phq9/gad7-only design:
- ``index``: the WHO-5 Index value (raw_total × 4).  Optional because
  no other instrument uses an index conversion.  Clients reading WHO-5
  scores MUST display ``index``, not ``total`` — the published cutoffs
  are on the index scale.
- ``cutoff_used`` + ``positive_screen``: AUDIT-C-only fields surfacing
  the sex-aware cutoff that was applied.  Clients render the cutoff
  in the result UI ("positive at ≥ N").  ``positive_screen`` is also
  reused by MDQ (the three-gate Hirschfeld 2000 screen), but MDQ does
  not surface a ``cutoff_used`` — its gate is categorical (≥ 7 items +
  concurrent + moderate/serious impairment), not an ordinal cutoff.
- ``triggering_items``: C-SSRS-only — the 1-indexed item numbers that
  drove the risk band.  Clinician-facing UI renders these as the
  "these answers escalated this screen" audit trail.
- ``instrument_version``: pinned version string for downstream storage
  and FHIR Observation export.

Idempotency:
- The ``Idempotency-Key`` header is required.  Re-sending the same key
  with the same body yields the same response (the route is currently
  stateless — repository wiring to enforce this lands when the
  AssessmentRepository ships).

Safety routing:
- PHQ-9 runs through the item-9 classifier (single item positive →
  T3 check per Kroenke 2001).
- C-SSRS runs through its own triage rules: items 4/5 positive OR
  item 6 positive with ``behavior_within_3mo=True`` → T3.
- GAD-7, WHO-5, AUDIT, AUDIT-C, PSS-10, DAST-10, MDQ, PC-PTSD-5, ISI,
  PCL-5, OCI-R, PHQ-15, PACS, BIS-11, Craving VAS, Readiness Ruler,
  DTCQ-8, URICA have no safety items — ``requires_t3`` is always
  False for these instruments.  WHO-5 ``depression_screen``
  band is *not* a T3 trigger; T3 is reserved for active suicidality
  per Docs/Whitepapers/04_Safety_Framework.md §T3.  A positive MDQ
  screen is a referral signal for a bipolar-spectrum structured
  interview, not a crisis signal — see ``scoring/mdq.py`` module
  docstring.  A positive PC-PTSD-5 is a referral signal for trauma-
  informed care (CAPS-5 / PCL-5 structured interview, EMDR / TF-CBT
  intake), not a crisis signal — see ``scoring/pcptsd5.py``.  A
  severe ISI result is a referral signal for CBT-I / sleep medicine,
  not a crisis signal — see ``scoring/isi.py``.  A positive PCL-5
  screen is the structured follow-up to PC-PTSD-5 — referral for
  trauma-focused therapy (PE / CPT / EMDR), not a crisis signal —
  see ``scoring/pcl5.py``.  A positive OCI-R screen routes to
  subtype-appropriate OCD therapy (ERP / CBT-H / thought-action-
  fusion work) — not a crisis signal — see ``scoring/ocir.py``.
  A high PHQ-15 score is a somatization signal routing to
  interoceptive-exposure / somatic-awareness interventions —
  item 6 (chest pain) and item 8 (fainting) are medical-urgency
  markers surfaced by the clinician-UI layer separately and are not
  T3 triggers — see ``scoring/phq15.py``.  PACS (Flannery 1999)
  is a continuous craving measure — the trajectory layer extracts
  its signal via week-over-week Δ rather than classifying a status.
  It is *the* platform-core instrument since craving is the
  60-180s urge-to-action construct the product intervenes on, but
  it carries no crisis item and no validated severity bands.
  See ``scoring/pacs.py``.  BIS-11 (Patton 1995) is the trait-
  level impulsivity measure — the dispositional substrate that
  PACS's state-level craving rides on.  BIS-11 has no safety
  item; high impulsivity routes to DBT distress-tolerance /
  mindfulness attention training / implementation-intention work
  at the intervention-selection layer, not to T3.  See
  ``scoring/bis11.py``.  Craving VAS (Sayette 2000) is the
  single-item 0-100 EMA partner to PACS — it measures
  momentary-point craving at urge-onset and post-intervention so
  the contextual bandit can train on within-episode Δ.  No
  safety item; a VAS of 100 is "strongest craving ever felt",
  not active suicidality.  See ``scoring/craving_vas.py``.  The
  Readiness Ruler (Rollnick 1999 / Heather 2008) is the single-
  item 0-10 motivation-to-change companion — the motivation
  signal the intervention layer pairs with the craving signal to
  pick a tool variant (MI-scripted elicitation vs effortful-
  resistance vs maintenance).  Higher-is-better direction
  (opposite of VAS / PHQ-9 / GAD-7); the trajectory layer
  applies the same direction-inversion logic it uses for WHO-5.
  No safety item; a Ruler of 0 ("not ready at all") is a
  motivation signal, not a crisis signal.  See
  ``scoring/readiness_ruler.py``.  DTCQ-8 (Sklar & Turner 1999)
  is the 8-item Drug-Taking Confidence Questionnaire short form
  — coping self-efficacy across Marlatt 1985's 8 high-risk
  relapse situations on a 0-100 confidence scale.  The instrument
  is the **coping-profile partner** to PACS / VAS: where craving
  measures urge intensity and Ruler measures motivation, DTCQ-8
  measures the per-situation confidence to resist.  The
  intervention layer reads the 8-tuple profile (not just the
  aggregate mean) to pick skill-building tool variants matched
  to the weakest Marlatt category.  Higher-is-better direction
  (same as WHO-5 / Ruler) — the trajectory layer's RCI logic
  must register DTCQ-8 in the higher-is-better partition when
  Sprint-X adds DTCQ-8 trajectory coverage.  No safety item;
  a DTCQ-8 of 0 ("no confidence at all") is a skill-building
  signal, not a crisis signal.  See ``scoring/dtcq8.py``.  URICA
  (McConnaughy 1983 / DiClemente & Hughes 1990) is the 16-item
  short-form University of Rhode Island Change Assessment — the
  multi-stage profile partner to Readiness Ruler (where Ruler is
  the single-item snapshot, URICA carries the full four-stage
  distribution across precontemplation / contemplation / action /
  maintenance).  **First multi-subscale wire-exposed instrument**
  in the package — the dispatch surfaces the four subscale sums
  on the response envelope's ``subscales`` map so the intervention
  layer reads the stage profile (not just the Readiness aggregate)
  to pick stage-matched scripts.  **First signed-total instrument**
  — URICA Readiness = ``C + A + M − PC`` is a signed integer
  (range -8 to +56) where a negative value is clinically meaningful
  (precontemplation-dominant profile).  Higher-is-better direction
  (same as WHO-5 / Ruler / DTCQ-8).  No safety item; a negative
  Readiness is a motivation signal, not a crisis signal.  See
  ``scoring/urica.py``.

C-SSRS transport note:
- Clients send item responses as 0/1 ints (consistent with every other
  instrument).  The scorer coerces to bool internally; the response
  echoes the raw caller input in the stored record.
"""

from __future__ import annotations

from typing import Literal
from uuid import uuid4

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from discipline.shared.idempotency import (
    Conflict,
    Hit,
    get_idempotency_store,
    hash_pydantic,
)
from discipline.shared.logging import LogStream, get_stream_logger

from .repository import AssessmentRecord, get_assessment_repository
from .safety_items import evaluate_phq9
from .scoring.audit import (
    InvalidResponseError as AuditInvalid,
    score_audit,
)
from .scoring.bis11 import (
    InvalidResponseError as Bis11Invalid,
    score_bis11,
)
from .scoring.audit_c import (
    InvalidResponseError as AuditCInvalid,
    Sex,
    score_audit_c,
)
from .scoring.craving_vas import (
    InvalidResponseError as CravingVasInvalid,
    score_craving_vas,
)
from .scoring.cssrs import (
    InvalidResponseError as CssrsInvalid,
    score_cssrs_screen,
)
from .scoring.dast10 import InvalidResponseError as Dast10Invalid, score_dast10
from .scoring.dtcq8 import (
    InvalidResponseError as Dtcq8Invalid,
    score_dtcq8,
)
from .scoring.gad7 import InvalidResponseError as Gad7Invalid, score_gad7
from .scoring.isi import InvalidResponseError as IsiInvalid, score_isi
from .scoring.mdq import (
    ImpairmentLevel,
    InvalidResponseError as MdqInvalid,
    score_mdq,
)
from .scoring.ocir import (
    InvalidResponseError as OcirInvalid,
    score_ocir,
)
from .scoring.pacs import (
    InvalidResponseError as PacsInvalid,
    score_pacs,
)
from .scoring.pcl5 import (
    InvalidResponseError as Pcl5Invalid,
    score_pcl5,
)
from .scoring.pcptsd5 import (
    InvalidResponseError as PcPtsd5Invalid,
    score_pcptsd5,
)
from .scoring.phq9 import InvalidResponseError as Phq9Invalid, score_phq9
from .scoring.phq15 import (
    InvalidResponseError as Phq15Invalid,
    score_phq15,
)
from .scoring.pss10 import InvalidResponseError as Pss10Invalid, score_pss10
from .scoring.readiness_ruler import (
    InvalidResponseError as ReadinessRulerInvalid,
    score_readiness_ruler,
)
from .scoring.urica import (
    InvalidResponseError as UricaInvalid,
    score_urica,
)
from .scoring.who5 import InvalidResponseError as Who5Invalid, score_who5
from .trajectories import RCI_THRESHOLDS, compute_point

router = APIRouter(prefix="/assessments", tags=["psychometric"])

# Safety stream — 2-year retention, HMAC-Merkle chained, clinical-ops reader.
# Per CLAUDE.md Rule #6 the audit/safety writers are gated by import boundary.
# This module (``psychometric``) is on the allow-list because PHQ-9 item 9 and
# C-SSRS items 4/5/6 are themselves safety-routing inputs.
_safety = get_stream_logger(LogStream.SAFETY)


Instrument = Literal[
    "phq9",
    "gad7",
    "who5",
    "audit",
    "audit_c",
    "cssrs",
    "pss10",
    "dast10",
    "mdq",
    "pcptsd5",
    "isi",
    "pcl5",
    "ocir",
    "phq15",
    "pacs",
    "bis11",
    "craving_vas",
    "readiness_ruler",
    "dtcq8",
    "urica",
]


# Item-count contracts per instrument.  Pinned so a request with the
# wrong number of items fails at the router with a 422 listing the
# expected count, rather than passing a malformed list to the scorer.
_INSTRUMENT_ITEM_COUNTS: dict[Instrument, int] = {
    "phq9": 9,
    "gad7": 7,
    "who5": 5,
    "audit": 10,
    "audit_c": 3,
    "cssrs": 6,
    "pss10": 10,
    "dast10": 10,
    "mdq": 13,
    "pcptsd5": 5,
    "isi": 7,
    "pcl5": 20,
    "ocir": 18,
    "phq15": 15,
    "pacs": 5,
    "bis11": 30,
    "craving_vas": 1,
    "readiness_ruler": 1,
    "dtcq8": 8,
    "urica": 16,
}


class AssessmentRequest(BaseModel):
    """Wire-format assessment submission.

    Per-instrument item-count is validated at the route layer (after
    Pydantic) so the error message can be specific to the instrument
    ("PHQ-9 requires exactly 9 items, got N").  The Pydantic
    ``min_length=1, max_length=30`` bound is the broadest envelope
    covering every supported instrument (Craving VAS=1, DTCQ-8=8
    through BIS-11=30); a tighter check needs to know the instrument value,
    which Pydantic field validators can't see in a clean way.  Craving
    VAS (Sprint 36) dropped the floor from 3 to 1 so the single-item
    EMA instrument could flow through the same wire shape; BIS-11
    (Sprint 35) had raised the ceiling from 20 to 30.  Callers on
    multi-item instruments see no change since the per-instrument count
    check at ``_validate_item_count`` is the tight constraint.

    ``sex`` is AUDIT-C-only; ignored by other instruments.  Defaulting
    to ``None`` (rather than ``"unspecified"``) lets the router echo
    'caller did not supply' vs 'caller supplied unspecified' if that
    distinction ever matters for telemetry.

    ``behavior_within_3mo`` is C-SSRS-only; it modulates whether a
    positive item 6 (past suicidal behavior) escalates to acute T3.
    Default ``None`` means 'not supplied' — the scorer treats that
    as False (historic), producing a moderate band rather than acute.

    ``concurrent_symptoms`` and ``functional_impairment`` are MDQ-only
    — Parts 2 and 3 of the Hirschfeld 2000 instrument.  Both are
    *required* to score MDQ; the dispatch layer raises 422 if either
    is missing when ``instrument == "mdq"``.  A partial MDQ submission
    would silently produce ``negative_screen`` regardless of Part 1,
    so surfacing the gap explicitly at the wire boundary is the right
    clinical posture.
    """

    instrument: Instrument
    items: list[int] = Field(min_length=1, max_length=30)
    sex: Sex | None = Field(
        default=None,
        description="AUDIT-C only; ignored by other instruments.",
    )
    behavior_within_3mo: bool | None = Field(
        default=None,
        description=(
            "C-SSRS only; whether item 6 (past behavior) was within the "
            "past 3 months.  Drives T3 escalation for item 6 positives."
        ),
    )
    concurrent_symptoms: bool | None = Field(
        default=None,
        description=(
            "MDQ only; Part 2 — whether several Part 1 items co-occurred "
            "in the same period.  Required when instrument == 'mdq'."
        ),
    )
    functional_impairment: ImpairmentLevel | None = Field(
        default=None,
        description=(
            "MDQ only; Part 3 — one of 'none'/'minor'/'moderate'/'serious'. "
            "Required when instrument == 'mdq'.  Only 'moderate' or "
            "'serious' satisfies the Hirschfeld 2000 positive-screen gate."
        ),
    )
    user_id: str | None = Field(
        default=None,
        description=(
            "Pseudonymous subject identifier — recorded in the safety "
            "stream when a T3 fires so on-call clinicians can route "
            "contact.  In production this is derived from the session "
            "JWT, not the request body; the body field is here so "
            "test fixtures and unauthenticated diagnostic harnesses "
            "can supply one explicitly.  May be None when no T3 fires "
            "(no safety event is emitted for non-T3 results)."
        ),
    )


class AssessmentResult(BaseModel):
    """Unified result envelope across all instruments.

    Always-present fields: ``assessment_id``, ``instrument``, ``total``,
    ``severity``, ``requires_t3``, ``instrument_version``.

    Instrument-specific optional fields:
    - ``index`` — WHO-5 only; the WHO-5 Index (0–100).
    - ``cutoff_used`` — AUDIT-C only; the cutoff that was applied (3 or 4).
    - ``positive_screen`` — AUDIT-C only; whether ``total >= cutoff_used``.
    - ``t3_reason`` — PHQ-9 / C-SSRS when ``requires_t3`` is True;
      a short machine-readable reason code for logging/display.
    - ``triggering_items`` — C-SSRS only; 1-indexed item numbers that
      drove the risk band.  Empty tuple when no items fired.
    - ``subscales`` — multi-subscale instruments; a map of
      subscale-name → subscale-total.  Populated for URICA (four
      stages of change: precontemplation / contemplation / action /
      maintenance), PCL-5 (four DSM-5 clusters: intrusion / avoidance
      / negative_mood / hyperarousal), OCI-R (six OCD subtypes:
      hoarding / checking / ordering / neutralizing / washing /
      obsessing), and BIS-11 (three Patton 1995 second-order factors:
      attentional / motor / non_planning).  Each subscale is a
      non-negative integer total on the scorer's native subscale
      scale.  Keys match the scorer-module constants
      (``SUBSCALE_LABELS`` / ``PCL5_CLUSTERS`` / ``OCIR_SUBSCALES`` /
      ``BIS11_SUBSCALES``) so clinician-UI renderers key off one
      source of truth across the whole package.  Instruments without
      subscales (PHQ-9 / GAD-7 / WHO-5 / AUDIT / AUDIT-C / C-SSRS /
      PSS-10 / DAST-10 / MDQ / PC-PTSD-5 / ISI / PHQ-15 / PACS /
      Craving VAS / Readiness Ruler / DTCQ-8) emit ``subscales=None``.

    For C-SSRS, ``total`` is ``positive_count`` (the number of yes
    answers, 0-6) and ``severity`` is the risk band string.  There is
    no clinically meaningful single-number "total" for C-SSRS, but
    positive_count is the closest analogue and clients can use it for
    trajectory tracking independently of band changes.

    For PACS (Flannery 1999), Craving VAS (Sayette 2000), Readiness
    Ruler (Rollnick 1999 / Heather 2008), and DTCQ-8 (Sklar & Turner
    1999), ``severity`` is the literal sentinel ``"continuous"``.
    None of these instruments publishes severity bands; the trajectory
    layer extracts the clinical signal from ``total`` directly —
    week-over-week Δ for PACS, within-episode Δ + EMA trajectory for
    VAS, week-over-week Δ for the Ruler, week-over-week Δ on the
    coping-self-efficacy mean for DTCQ-8.  Direction semantics differ:
    VAS and PACS are higher-is-worse (craving rising = deterioration);
    the Ruler and DTCQ-8 are higher-is-better (motivation / coping-
    confidence rising = improvement, same direction as WHO-5).
    Clients rendering these results must not attempt to classify
    status from ``severity`` — show ``total`` and the trajectory chart
    instead.  DTCQ-8 additionally carries irreducible per-situation
    profile signal in the stored record's ``raw_items`` tuple; the
    response envelope exposes the aggregate ``total`` only, and
    clinician-UI surfaces reading the coping profile fetch the raw
    items through the PHI-boundary-gated repository path.
    """

    assessment_id: str
    instrument: Instrument
    total: int
    severity: str
    requires_t3: bool
    t3_reason: str | None = None
    index: int | None = None
    cutoff_used: int | None = None
    positive_screen: bool | None = None
    triggering_items: list[int] | None = None
    subscales: dict[str, int] | None = None
    instrument_version: str | None = None


def _validate_item_count(payload: AssessmentRequest) -> None:
    """Enforce per-instrument item count at the router boundary.

    Raises 422 with a specific message rather than letting the scorer
    raise ``InvalidResponseError`` later — same end behavior, but the
    error surface is one layer earlier and more diagnostic."""
    expected = _INSTRUMENT_ITEM_COUNTS[payload.instrument]
    if len(payload.items) != expected:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "validation.item_count",
                "message": (
                    f"{payload.instrument} requires exactly {expected} items, "
                    f"got {len(payload.items)}"
                ),
            },
        )


def _dispatch(payload: AssessmentRequest) -> AssessmentResult:
    """Per-instrument dispatch — pure function over the payload.

    Extracted from ``submit_assessment`` so safety-event emission can
    happen in one place after a result is built (rather than threaded
    through every per-instrument branch).  Scorer exceptions propagate
    to the caller; the HTTP layer translates them to 422.
    """
    if payload.instrument == "phq9":
        result = score_phq9(payload.items)
        safety = evaluate_phq9(result)
        return AssessmentResult(
            assessment_id=str(uuid4()),
            instrument="phq9",
            total=result.total,
            severity=result.severity,
            requires_t3=bool(safety and safety.requires_t3),
            t3_reason=safety.reason if safety else None,
            instrument_version=result.instrument_version,
        )
    if payload.instrument == "gad7":
        g = score_gad7(payload.items)
        return AssessmentResult(
            assessment_id=str(uuid4()),
            instrument="gad7",
            total=g.total,
            severity=g.severity,
            requires_t3=False,
            instrument_version=g.instrument_version,
        )
    if payload.instrument == "who5":
        w = score_who5(payload.items)
        return AssessmentResult(
            assessment_id=str(uuid4()),
            instrument="who5",
            total=w.raw_total,
            index=w.index,
            severity=w.band,
            requires_t3=False,
            instrument_version=w.instrument_version,
        )
    if payload.instrument == "audit":
        au = score_audit(payload.items)
        return AssessmentResult(
            assessment_id=str(uuid4()),
            instrument="audit",
            total=au.total,
            severity=au.band,
            requires_t3=False,
            instrument_version=au.instrument_version,
        )
    if payload.instrument == "audit_c":
        a = score_audit_c(payload.items, sex=payload.sex or "unspecified")
        return AssessmentResult(
            assessment_id=str(uuid4()),
            instrument="audit_c",
            total=a.total,
            severity="positive_screen" if a.positive_screen else "negative_screen",
            requires_t3=False,
            cutoff_used=a.cutoff_used,
            positive_screen=a.positive_screen,
            instrument_version=a.instrument_version,
        )
    if payload.instrument == "cssrs":
        # Bool coercion happens inside the scorer; passing int list
        # is fine.  ``behavior_within_3mo`` defaults to False at the
        # scorer when ``None`` is supplied — the safer default.
        c = score_cssrs_screen(
            payload.items,
            behavior_within_3mo=bool(payload.behavior_within_3mo),
        )
        return AssessmentResult(
            assessment_id=str(uuid4()),
            instrument="cssrs",
            total=c.positive_count,
            severity=c.risk,
            requires_t3=c.requires_t3,
            t3_reason="cssrs_acute_triage" if c.requires_t3 else None,
            triggering_items=list(c.triggering_items),
            instrument_version=c.instrument_version,
        )
    if payload.instrument == "pss10":
        p = score_pss10(payload.items)
        return AssessmentResult(
            assessment_id=str(uuid4()),
            instrument="pss10",
            total=p.total,
            severity=p.band,
            requires_t3=False,
            instrument_version=p.instrument_version,
        )
    if payload.instrument == "dast10":
        d = score_dast10(payload.items)
        return AssessmentResult(
            assessment_id=str(uuid4()),
            instrument="dast10",
            total=d.total,
            severity=d.band,
            requires_t3=False,
            instrument_version=d.instrument_version,
        )
    if payload.instrument == "pcptsd5":
        # Prins 2016 — 5-item PTSD screen, positive at >= 3.  Total
        # carries the positive_count (0-5); severity echoes
        # positive/negative_screen uniform with AUDIT-C and MDQ so
        # a chart-view client rendering screen-style instruments
        # uses one projection layer across all three.
        pt = score_pcptsd5(payload.items)
        return AssessmentResult(
            assessment_id=str(uuid4()),
            instrument="pcptsd5",
            total=pt.positive_count,
            severity=(
                "positive_screen" if pt.positive_screen else "negative_screen"
            ),
            requires_t3=False,
            positive_screen=pt.positive_screen,
            instrument_version=pt.instrument_version,
        )
    if payload.instrument == "isi":
        # Bastien 2001 — 7-item 0-4 Likert, total 0-28.  severity is
        # the four-band Bastien label (none/subthreshold/moderate/
        # severe) so the wire shape matches PHQ-9 / GAD-7 severity-
        # band instruments.  No safety routing — ISI is a CBT-I /
        # sleep-medicine referral signal, not a crisis signal.
        i = score_isi(payload.items)
        return AssessmentResult(
            assessment_id=str(uuid4()),
            instrument="isi",
            total=i.total,
            severity=i.severity,
            requires_t3=False,
            instrument_version=i.instrument_version,
        )
    if payload.instrument == "pcl5":
        # Weathers 2013 / Blevins 2015 — 20-item 0-4 Likert, total
        # 0-80, positive at >= 33.  Wire envelope follows PC-PTSD-5 /
        # MDQ / AUDIT-C's positive/negative_screen semantic since
        # PCL-5 is a cutoff-driven screen (not a banded severity
        # instrument like PHQ-9).  DSM-5 cluster B/C/D/E subscales
        # (intrusion / avoidance / negative_mood / hyperarousal) are
        # surfaced on the ``subscales`` envelope map so the clinician-
        # UI timeline can render cluster-level trajectory lines
        # without a per-row repository re-read.  The mapping keys
        # match ``scoring.pcl5.PCL5_CLUSTERS`` — clinician-UI
        # renderers that key off the scorer-module constant pick up
        # the same names in the response payload.  The cluster
        # profile drives trauma-focused therapy selection (PE for
        # intrusion-dominant vs CPT for negative-mood-dominant vs EMDR
        # for mixed) at the intervention-selection layer.
        pcl = score_pcl5(payload.items)
        return AssessmentResult(
            assessment_id=str(uuid4()),
            instrument="pcl5",
            total=pcl.total,
            severity=(
                "positive_screen" if pcl.positive_screen else "negative_screen"
            ),
            requires_t3=False,
            positive_screen=pcl.positive_screen,
            subscales={
                "intrusion": pcl.cluster_intrusion,
                "avoidance": pcl.cluster_avoidance,
                "negative_mood": pcl.cluster_negative_mood,
                "hyperarousal": pcl.cluster_hyperarousal,
            },
            instrument_version=pcl.instrument_version,
        )
    if payload.instrument == "ocir":
        # Foa 2002 — 18-item 0-4 Likert, total 0-72, positive at
        # >= 21.  Wire envelope matches PCL-5's screen semantic.
        # Six 3-item subscales (hoarding / checking / ordering /
        # neutralizing / washing / obsessing) are surfaced on the
        # ``subscales`` envelope map so the clinician-UI surface
        # picks the right subtype-appropriate ERP protocol
        # (ERP-for-contamination on washing-dominant vs ERP-with-
        # response-prevention on checking-dominant vs CBT-H for
        # hoarding-dominant).  Unlike PCL-5's contiguous DSM-5
        # cluster ranges, OCI-R items are deliberately distributed
        # across the instrument (item 1 = hoarding, item 2 =
        # checking, item 3 = ordering, etc.) per Foa 2002 §2.2, so
        # the scorer's per-subscale summation is load-bearing — a
        # flat contiguous-slice reading would silently miscategorize
        # every subscale.  The wire keys match ``scoring.ocir.
        # OCIR_SUBSCALES`` dict keys so clinician-UI renderers key
        # off one source of truth.
        ocir = score_ocir(payload.items)
        return AssessmentResult(
            assessment_id=str(uuid4()),
            instrument="ocir",
            total=ocir.total,
            severity=(
                "positive_screen" if ocir.positive_screen else "negative_screen"
            ),
            requires_t3=False,
            positive_screen=ocir.positive_screen,
            subscales={
                "hoarding": ocir.subscale_hoarding,
                "checking": ocir.subscale_checking,
                "ordering": ocir.subscale_ordering,
                "neutralizing": ocir.subscale_neutralizing,
                "washing": ocir.subscale_washing,
                "obsessing": ocir.subscale_obsessing,
            },
            instrument_version=ocir.instrument_version,
        )
    if payload.instrument == "phq15":
        # Kroenke 2002 — 15-item 0-2 Likert somatic symptom scale,
        # total 0-30.  Severity band (minimal/low/medium/high) uniform
        # with PHQ-9 / GAD-7 / ISI — banded-severity envelope, NOT the
        # positive/negative_screen envelope used by PCL-5 / PC-PTSD-5 /
        # OCI-R / MDQ.  No safety routing: PHQ-15 has no suicidality
        # item, and item 6 (chest pain) + item 8 (fainting) are
        # medical-urgency signals surfaced by the clinician-UI layer
        # separately rather than T3 triggers.  Sex-aware item 4
        # (menstrual problems) is handled upstream — the scorer takes
        # 15 pre-coded items; men code item 4 as 0 per Kroenke 2002.
        phq15 = score_phq15(payload.items)
        return AssessmentResult(
            assessment_id=str(uuid4()),
            instrument="phq15",
            total=phq15.total,
            severity=phq15.severity,
            requires_t3=False,
            instrument_version=phq15.instrument_version,
        )
    if payload.instrument == "bis11":
        # Patton 1995 — 30-item 1-4 Likert Barratt Impulsiveness Scale,
        # total 30-120.  Banded-severity envelope (low/normal/high) per
        # Stanford 2009 norms.  **First non-zero-based Likert in the
        # dispatch table** — the 1-4 range is pinned at the scorer and
        # enforced via InvalidResponseError → 422.  11 reverse-coded
        # items (positively-worded: "I plan tasks carefully") are
        # handled inside the scorer; callers submit raw 1-4 responses
        # and the stored record's ``total`` reflects the post-reversal
        # sum, not the raw-response sum.  No safety routing: BIS-11 is
        # a trait inventory with no suicidality / acute-harm item.
        # Three Patton 1995 second-order subscales (attentional /
        # motor / non_planning) are surfaced on the ``subscales``
        # envelope map so the intervention layer picks the profile-
        # appropriate variant: attentional-dominant → mindfulness-
        # based attention training, motor-dominant → response-delay
        # / impulse-interruption drills, non_planning-dominant →
        # implementation-intention scripting.  Distributed-item
        # composition (same as OCI-R — items are interleaved across
        # subscales, not contiguous) means the scorer's per-subscale
        # summation is load-bearing; a contiguous-slice read would
        # corrupt the aggregate.  Wire keys match
        # ``scoring.bis11.BIS11_SUBSCALES``.
        bis = score_bis11(payload.items)
        return AssessmentResult(
            assessment_id=str(uuid4()),
            instrument="bis11",
            total=bis.total,
            severity=bis.severity,
            requires_t3=False,
            subscales={
                "attentional": bis.subscale_attentional,
                "motor": bis.subscale_motor,
                "non_planning": bis.subscale_non_planning,
            },
            instrument_version=bis.instrument_version,
        )
    if payload.instrument == "pacs":
        # Flannery 1999 — 5-item 0-6 Likert Penn Alcohol Craving Scale,
        # total 0-30.  **Continuous-severity envelope** (new in Sprint 34)
        # — Flannery 1999 publishes no severity bands and the clinical
        # literature treats PACS as a week-over-week trajectory measure,
        # not a categorical screen.  The router emits
        # ``severity="continuous"`` as a sentinel so every instrument in
        # the dispatch table has a severity field (banded / screen /
        # continuous), without hand-rolling bands that would violate
        # CLAUDE.md's "Don't hand-roll severity thresholds" rule.  No
        # safety routing: craving is the *pre-behavior* signal the
        # platform intervenes on within the 60-180 second urge-to-action
        # window, not a T3 crisis marker.  A positive PACS + acute
        # suicidality still needs co-administered PHQ-9 / C-SSRS to fire
        # T3, consistent with the PHQ-15 / OCI-R / ISI safety posture.
        pacs = score_pacs(payload.items)
        return AssessmentResult(
            assessment_id=str(uuid4()),
            instrument="pacs",
            total=pacs.total,
            severity="continuous",
            requires_t3=False,
            instrument_version=pacs.instrument_version,
        )
    if payload.instrument == "craving_vas":
        # Sayette 2000 synthesis — single-item 0-100 Visual Analog Scale
        # of momentary craving.  **Continuous-severity envelope** (same
        # sentinel as PACS) — the VAS publishes no bands and the
        # literature treats it as a per-user / per-episode relative
        # signal, not a categorical severity measure.  The clinical
        # value lives in three places, none of which are absolute
        # cutoffs: (a) within-user trajectory across EMA sessions,
        # (b) within-episode Δ (pre-intervention VAS minus post-
        # intervention VAS) — the efficacy signal the bandit trains
        # on, and (c) baseline-relative deviation against the user's
        # running EMA mean.  This is the EMA partner to PACS (weekly
        # aggregated) — PACS answers 'has this week been harder?',
        # VAS answers 'is the intervention working right now?'  No
        # safety routing: a VAS of 100 is 'peak subjective craving',
        # not active suicidality; acute ideation is gated by PHQ-9
        # item 9 / C-SSRS, consistent with the PACS / PHQ-15 / OCI-R /
        # ISI safety-posture convention.  The substance context
        # (alcohol / cannabis / nicotine / opioid / gambling /
        # porn-use) is surfaced at the UI layer and stored alongside
        # the assessment at the repository layer — the scorer is
        # substance-agnostic so one validated instrument serves every
        # vertical without per-vertical branching.  See
        # ``scoring/craving_vas.py``.
        vas = score_craving_vas(payload.items)
        return AssessmentResult(
            assessment_id=str(uuid4()),
            instrument="craving_vas",
            total=vas.total,
            severity="continuous",
            requires_t3=False,
            instrument_version=vas.instrument_version,
        )
    if payload.instrument == "readiness_ruler":
        # Rollnick 1999 / Heather 2008 — single-item 0-10 motivation-
        # to-change ruler.  **Continuous-severity envelope** (same
        # sentinel as PACS / VAS) — Heather 2008 publishes no bands,
        # and the MI stages-of-change anchors (pre-contemplation /
        # contemplation / action) are pedagogical descriptions, NOT
        # clinically-validated cutoffs with consensus uptake.
        # Fabricating bands from pedagogical anchors would violate
        # CLAUDE.md's "Don't hand-roll severity thresholds" rule.
        # **Direction semantics: higher is better** — unlike Craving
        # VAS (higher = worse craving) or PHQ-9 / GAD-7 / PSS-10
        # (higher = worse symptom).  The trajectory layer must apply
        # the same direction-inversion logic it uses for WHO-5 when
        # Ruler trajectories are added; until then, wire-layer
        # behavior is identical to PACS / VAS (emit raw total + the
        # ``"continuous"`` sentinel).  The Ruler is URICA's single-
        # item equivalent — the full 16-item 4-subscale stages-of-
        # change instrument is a separate future sprint per
        # Docs/Technicals/12_Psychometric_System.md §3.1 row #10.
        # No safety routing: a Ruler score of 0 ("not ready at all")
        # is a motivation signal routing to MI-scripted interventions
        # (decisional-balance elicitation, change-talk amplification),
        # not a crisis signal.  Acute ideation is gated by PHQ-9 item
        # 9 / C-SSRS per the PACS / PHQ-15 / OCI-R / ISI / VAS
        # safety-posture convention.  See
        # ``scoring/readiness_ruler.py``.
        rr = score_readiness_ruler(payload.items)
        return AssessmentResult(
            assessment_id=str(uuid4()),
            instrument="readiness_ruler",
            total=rr.total,
            severity="continuous",
            requires_t3=False,
            instrument_version=rr.instrument_version,
        )
    if payload.instrument == "dtcq8":
        # Sklar & Turner 1999 — 8-item Drug-Taking Confidence
        # Questionnaire short form.  Each item is a 0-100 integer
        # confidence-percentage score; the aggregate is the **mean**
        # across the 8 Marlatt 1985 situation categories, not the
        # sum.  The scorer exposes ``total`` as the mean rounded to
        # int (for AssessmentResult envelope compatibility) AND
        # ``mean`` as the exact float (for FHIR valueDecimal /
        # clinician-PDF precision).  The router emits ``total`` here;
        # the ``mean`` field flows through the repository record so
        # downstream consumers (trajectory layer, FHIR export) can
        # read the precise aggregate.  **Continuous-severity
        # envelope** (same sentinel as PACS / VAS / Ruler) — Sklar
        # 1999 publishes no bands and the "50% = moderate confidence"
        # clinician-training heuristic is pedagogical shorthand, not
        # a validated cutoff with consensus uptake.  Fabricating
        # bands would violate CLAUDE.md's "Don't hand-roll severity
        # thresholds" rule.  **Direction semantics: higher is
        # better** — the third higher-is-better instrument in the
        # package after WHO-5 and Readiness Ruler.  The trajectory
        # layer must apply the same direction-inversion logic when
        # DTCQ-8 trajectory coverage is added.  **Per-situation
        # profile signal** is load-bearing here (unique to DTCQ-8
        # among shipped instruments): the intervention layer reads
        # the 8-tuple via ``SITUATION_LABELS`` positional mapping to
        # pick skill-building tool variants matched to the weakest
        # Marlatt category (e.g. social-pressure weakness routes to
        # refusal-skills, unpleasant-emotions weakness routes to
        # distress-tolerance).  The wire response envelope surfaces
        # only the aggregate ``total``; clinician-UI surfaces
        # reading the full profile go through the
        # PHI-boundary-gated repository path.  No safety routing:
        # low coping self-efficacy is a skill-building signal, not
        # a crisis signal; acute ideation is gated by PHQ-9 item 9
        # / C-SSRS per the uniform safety-posture convention.  See
        # ``scoring/dtcq8.py``.
        d = score_dtcq8(payload.items)
        return AssessmentResult(
            assessment_id=str(uuid4()),
            instrument="dtcq8",
            total=d.total,
            severity="continuous",
            requires_t3=False,
            instrument_version=d.instrument_version,
        )
    if payload.instrument == "urica":
        # McConnaughy 1983 / DiClemente & Hughes 1990 — 16-item
        # stages-of-change profile.  **First multi-subscale wire-
        # exposed instrument** in the package — the dispatch surfaces
        # the four subscale sums (precontemplation / contemplation /
        # action / maintenance) on the response envelope's ``subscales``
        # map so the intervention layer reads the stage profile
        # alongside the Readiness aggregate without a second round-trip.
        # The field shape is generic (``dict[str, int]``) so PCL-5
        # cluster surfacing, OCI-R subtypes, and BIS-11 subscales can
        # ride the same envelope in later sprints without wire-schema
        # churn.  **First signed total** — Readiness = ``C + A + M −
        # PC`` is a signed int (range −8 to +56); a negative value is
        # clinically meaningful (precontemplation-dominant profile).
        # **Continuous-severity envelope** (same sentinel as PACS /
        # VAS / Ruler / DTCQ-8) — DiClemente & Hughes 1990 publishes
        # no bands and the canonical analytic approach is
        # cluster-analysis of the profile, not cutoff thresholding.
        # Hand-rolling Readiness bands would violate CLAUDE.md's
        # "Don't hand-roll severity thresholds" rule.  **Direction
        # semantics: higher is better** — the fourth higher-is-better
        # instrument after WHO-5 / Ruler / DTCQ-8.  The trajectory
        # layer must apply the same direction-inversion logic when
        # URICA trajectory coverage is added.  No safety routing:
        # a precontemplation-dominant profile is a motivation signal
        # routing to MI-scripted interventions, not a crisis signal.
        # Acute ideation is gated by PHQ-9 item 9 / C-SSRS per the
        # uniform safety-posture convention.  See ``scoring/urica.py``.
        u = score_urica(payload.items)
        return AssessmentResult(
            assessment_id=str(uuid4()),
            instrument="urica",
            total=u.total,
            severity="continuous",
            requires_t3=False,
            subscales={
                "precontemplation": u.precontemplation,
                "contemplation": u.contemplation,
                "action": u.action,
                "maintenance": u.maintenance,
            },
            instrument_version=u.instrument_version,
        )
    # mdq — Hirschfeld 2000 three-gate positive screen.  Both Part 2
    # (concurrent_symptoms) and Part 3 (functional_impairment) are
    # required.  Raise MdqInvalid here (translated to 422 at the HTTP
    # layer) rather than forwarding partial input to the scorer — the
    # scorer's own strict-bool / strict-str checks would reject with a
    # less diagnostic message, and silently defaulting to False / "none"
    # would produce a misleading negative_screen.
    if payload.concurrent_symptoms is None:
        raise MdqInvalid(
            "MDQ requires concurrent_symptoms (Part 2 yes/no) — "
            "omit instrument=mdq or supply the field"
        )
    if payload.functional_impairment is None:
        raise MdqInvalid(
            "MDQ requires functional_impairment (Part 3: one of "
            "'none'/'minor'/'moderate'/'serious')"
        )
    m = score_mdq(
        payload.items,
        concurrent_symptoms=payload.concurrent_symptoms,
        functional_impairment=payload.functional_impairment,
    )
    # ``total`` carries the positive-item count (0-13) — the closest
    # single-number analogue, and the value the FHIR Observation
    # emits as ``valueInteger``.  ``severity`` is the three-gate
    # outcome so the response shape is uniform with AUDIT-C's
    # positive/negative screen semantic.
    return AssessmentResult(
        assessment_id=str(uuid4()),
        instrument="mdq",
        total=m.positive_count,
        severity="positive_screen" if m.positive_screen else "negative_screen",
        requires_t3=False,
        positive_screen=m.positive_screen,
        instrument_version=m.instrument_version,
    )


def _emit_t3_safety_event(
    result: AssessmentResult, *, user_id: str | None
) -> None:
    """Record a T3 fire to the safety stream.

    Privacy contract (CLAUDE.md Rule #6 + Whitepaper 04 §T3):
    - Includes: ``assessment_id``, ``user_id``, ``instrument``,
      ``severity``, ``total``, ``t3_reason``, ``triggering_items``.
    - Excludes: raw item responses, free-text patient narrative, any
      LLM output.  The 1-indexed ``triggering_items`` numbers are
      diagnostic ("items 4 and 5 fired") and not item *values* (binary
      responses), so they're safe to include.

    The 2-year retention + clinical-ops-only IAM on the safety stream
    is what makes including ``user_id`` defensible — it's the same data
    boundary as a clinical chart note.
    """
    _safety.warning(
        "psychometric.t3_fire",
        assessment_id=result.assessment_id,
        user_id=user_id,
        instrument=result.instrument,
        severity=result.severity,
        total=result.total,
        t3_reason=result.t3_reason,
        triggering_items=result.triggering_items,
    )


@router.post("", response_model=AssessmentResult, status_code=201)
async def submit_assessment(
    payload: AssessmentRequest,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
) -> AssessmentResult:
    """Score an assessment and return a deterministic typed result.

    Safety routing happens BEFORE the response is returned; PHQ-9
    callers rely on ``requires_t3`` to switch to the crisis path UI.
    See Docs/Whitepapers/04_Safety_Framework.md §T4.

    When ``requires_t3`` is True (PHQ-9 item 9 OR C-SSRS items 4/5/6
    +recency), a Merkle-chained event is emitted to the safety stream
    so on-call clinical operators can correlate with downstream contact
    workflows.  GAD-7 / WHO-5 / AUDIT-C / PSS-10 / DAST-10 never fire
    T3, so they never emit a safety event.

    Idempotency (RFC 7238-style):
    - Same ``Idempotency-Key`` + same body → return the cached
      response and skip side-effects (re-scoring, safety emission).
    - Same key + different body → 409 Conflict.
    - Entries expire after 24 h (see
      :mod:`discipline.shared.idempotency`).
    """
    _validate_item_count(payload)

    store = get_idempotency_store()
    body_hash = hash_pydantic(payload)
    cached = store.lookup(idempotency_key, body_hash)
    if isinstance(cached, Conflict):
        raise HTTPException(
            status_code=409,
            detail={
                "code": "idempotency.conflict",
                "message": (
                    "Idempotency-Key was previously seen with a different "
                    "request body.  Pick a new key or resubmit the original "
                    "body."
                ),
            },
        )
    if isinstance(cached, Hit):
        # Replay: return stored response and skip the safety emission.
        # Storing an AssessmentResult in the cache means we re-serve the
        # same assessment_id + identical severity/total fields, which is
        # what a retrying client expects on a network retry.
        return cached.response

    try:
        result = _dispatch(payload)
    except (
        Phq9Invalid,
        Gad7Invalid,
        Who5Invalid,
        AuditInvalid,
        AuditCInvalid,
        CssrsInvalid,
        Pss10Invalid,
        Dast10Invalid,
        MdqInvalid,
        PcPtsd5Invalid,
        IsiInvalid,
        Pcl5Invalid,
        OcirInvalid,
        Phq15Invalid,
        PacsInvalid,
        Bis11Invalid,
        CravingVasInvalid,
        ReadinessRulerInvalid,
        Dtcq8Invalid,
        UricaInvalid,
    ) as exc:
        raise HTTPException(
            status_code=422,
            detail={"code": "validation.invalid_payload", "message": str(exc)},
        ) from exc

    if result.requires_t3:
        _emit_t3_safety_event(result, user_id=payload.user_id)

    # Persist the record when a user_id is supplied.  Unauthenticated
    # diagnostic harnesses omit user_id; those submissions still score
    # and still emit safety events, but leave no history trail — which
    # matches the clinical posture that a phantom 'anonymous user'
    # timeline has no owner and no value.
    if payload.user_id:
        _persist_record(payload, result)

    # Only cache successful results.  A 422 re-raises on replay by
    # rerunning validation — the invalid payload is deterministic, so
    # caching the exception would save a few microseconds at the cost
    # of a much more complex cache invalidation story.
    store.store(idempotency_key, body_hash, result)
    return result


def _persist_record(
    payload: AssessmentRequest, result: AssessmentResult
) -> None:
    """Save the submitted event to the assessment repository.

    The record captures the full request context (raw items plus the
    per-instrument options ``sex`` / ``behavior_within_3mo``) so a
    later FHIR Observation re-render (Sprint 24 and beyond) does not
    need to re-fetch from a second source.  ``/history`` only surfaces
    the summary projection; the stored shape carries the full event.
    """
    repo = get_assessment_repository()
    # Convert list → tuple so the frozen dataclass stays hashable and
    # immutable.  A shared list reference would otherwise let a caller
    # mutate the stored record from the outside.
    raw_items = tuple(payload.items)
    triggering = (
        tuple(result.triggering_items)
        if result.triggering_items is not None
        else None
    )
    # Copy the subscale dict so a future caller that mutates their
    # reference (e.g. a test harness reusing a submission builder)
    # doesn't retroactively alter the stored record.  ``None`` stays
    # ``None`` — the repository record carries the "no subscales
    # applicable" signal verbatim for instruments that don't surface
    # subscales on the wire.
    subscales = (
        dict(result.subscales) if result.subscales is not None else None
    )
    record = AssessmentRecord(
        assessment_id=result.assessment_id,
        user_id=payload.user_id or "",
        instrument=result.instrument,
        total=result.total,
        severity=result.severity,
        requires_t3=result.requires_t3,
        raw_items=raw_items,
        created_at=repo.now(),
        t3_reason=result.t3_reason,
        index=result.index,
        cutoff_used=result.cutoff_used,
        positive_screen=result.positive_screen,
        triggering_items=triggering,
        subscales=subscales,
        instrument_version=result.instrument_version,
        sex=payload.sex,
        behavior_within_3mo=payload.behavior_within_3mo,
        concurrent_symptoms=payload.concurrent_symptoms,
        functional_impairment=payload.functional_impairment,
    )
    repo.save(record)


# =============================================================================
# Trajectory — RCI (Reliable Change Index) per Jacobson & Truax 1991
# =============================================================================


# Direction literal mirrors the trajectories module so the response
# schema is type-safe across the boundary.  Keeping it in sync is
# checked at import time — a regression where the trajectories module
# adds/removes a direction would surface as a Pydantic validation
# error on the response, not a silent shape drift.
TrajectoryDirection = Literal[
    "improvement", "deterioration", "no_reliable_change", "insufficient_data"
]


class TrajectoryRequest(BaseModel):
    """Single-instrument trajectory query.

    ``instrument`` accepts any string — unknown values gracefully fall
    through to ``insufficient_data`` rather than 422-ing.  This matches
    the trajectories module's own contract: the endpoint mirrors the
    library's tolerance so a renderer that asks about a not-yet-validated
    instrument receives a typed answer ("we have no RCI threshold")
    rather than an HTTP error.

    ``baseline`` is optional; ``None`` produces ``insufficient_data``
    with the threshold still echoed so the UI can show 'no comparison
    available — collect a second reading'.
    """

    instrument: str
    current: float
    baseline: float | None = None


class TrajectoryResponse(BaseModel):
    """Typed trajectory point.

    All fields except ``direction`` are echoed verbatim from the input
    or computed deterministically:
    - ``delta`` is ``current - baseline`` when both are present, else
      ``None``.  Sign convention matches the underlying scale (e.g.
      negative on PHQ-9 means symptoms decreased).
    - ``rci_threshold`` is the per-instrument |Δ| that counts as
      reliable change; pinned in
      ``Docs/Whitepapers/02_Clinical_Evidence_Base.md``.
    - ``direction`` is the clinical interpretation: lower-is-better
      instruments invert the sign so improvement is always positive
      semantically, regardless of the underlying scale.
    """

    instrument: str
    current: float
    baseline: float | None
    delta: float | None
    rci_threshold: float | None
    direction: TrajectoryDirection


@router.post(
    "/trajectory",
    response_model=TrajectoryResponse,
    status_code=200,
    tags=["psychometric"],
)
async def compute_trajectory(payload: TrajectoryRequest) -> TrajectoryResponse:
    """Compute the reliable-change-index trajectory for one instrument.

    Pure computation — no idempotency key required, no DB writes.
    The endpoint is safe to call repeatedly; identical inputs always
    yield identical outputs.

    Direction interpretation by instrument:
    - PHQ-9 / GAD-7 / PSS-10 / AUDIT-C / DAST-10: lower is better;
      ``delta < 0`` with |delta| ≥ threshold → improvement.
    - WHO-5: higher is better; ``delta > 0`` with |delta| ≥ threshold
      → improvement.

    Unknown instruments and missing baselines both produce
    ``direction='insufficient_data'`` with HTTP 200 — this is a
    successful query, just one with no comparable trajectory.
    """
    # Normalize instrument to lowercase so callers don't need to know
    # the canonical casing.  The thresholds dict keys are lowercase by
    # convention.
    instrument = payload.instrument.strip().lower()
    point = compute_point(
        instrument=instrument,
        current=payload.current,
        baseline=payload.baseline,
    )
    return TrajectoryResponse(
        instrument=instrument,
        current=point.current,
        baseline=point.baseline,
        delta=point.delta,
        rci_threshold=point.rci_threshold,
        direction=point.direction,
    )


@router.get("/trajectory/thresholds", tags=["psychometric"])
async def trajectory_thresholds() -> dict[str, float]:
    """Return the per-instrument RCI threshold table.

    Useful for UI surfaces that want to render '|Δ| ≥ N counts as
    reliable change' tooltips alongside the trajectory chart, without
    hard-coding the table on the client side.  The values come from
    the same source-of-truth dict as the trajectory computation —
    one source, no drift."""
    return dict(RCI_THRESHOLDS)


class AssessmentHistoryItem(BaseModel):
    """Summary row for a single historical assessment.

    Deliberately omits ``raw_items`` — the user's literal answers on a
    validated clinical instrument are PHI that the history timeline
    does not need.  A clinician viewing a single Observation (Sprint 24
    GET ``/reports/fhir/observations/{id}``) reads the raw items
    through that PHI-boundary-gated endpoint instead; the history
    surface is the patient's own timeline view.

    Field shape matches :class:`AssessmentResult` for the fields that
    overlap, so a client rendering either response uses the same
    projection layer.
    """

    assessment_id: str
    instrument: str
    total: int
    severity: str
    requires_t3: bool
    created_at: str  # ISO-8601 UTC — consumed by chart-plot code as-is
    t3_reason: str | None = None
    index: int | None = None
    cutoff_used: int | None = None
    positive_screen: bool | None = None
    triggering_items: list[int] | None = None
    subscales: dict[str, int] | None = None
    instrument_version: str | None = None


class AssessmentHistoryResponse(BaseModel):
    """Envelope for the history endpoint.

    ``items`` is newest-first, capped at ``limit``.  ``limit`` is
    echoed so a client rendering pagination can display "showing 50 of
    N" without a second call; ``total`` is the absolute count for
    this user (not the returned page size) so the UI can decide
    whether to surface a "load older" control.
    """

    items: list[AssessmentHistoryItem]
    limit: int
    total: int


@router.get(
    "/history",
    response_model=AssessmentHistoryResponse,
    tags=["psychometric"],
)
async def history(
    x_user_id: str = Header(..., alias="X-User-Id"),
    limit: int = 50,
) -> AssessmentHistoryResponse:
    """Return the authenticated user's assessment timeline.

    Authentication (temporary shape):
    - ``X-User-Id`` header carries the pseudonymous subject id.  In
      production this is derived from the Clerk session JWT inside an
      auth middleware and injected here; the header form is a
      scaffolding stub so the Sprint 23 endpoint is testable before
      the Clerk v6 integration lands.  Callers must NOT supply an
      ``X-User-Id`` from a client-controlled source in a production
      deploy — the server-side middleware overwrite is what makes the
      identity trustable.
    - A missing or empty ``X-User-Id`` yields a 401.  ``limit`` must
      be a positive integer; 0 and negatives are 400.

    Response projection:
    - Items are newest-first by ``created_at``.
    - ``raw_items`` is deliberately omitted (see
      :class:`AssessmentHistoryItem`).  Clinician-portal views that
      need raw items go through Sprint 24's FHIR Observation GET.

    This endpoint does NOT touch the idempotency cache — GET is
    idempotent by HTTP semantics so there's nothing to deduplicate.
    """
    if not x_user_id:
        raise HTTPException(
            status_code=401,
            detail={
                "code": "auth.missing_user_id",
                "message": "X-User-Id header required.",
            },
        )
    if limit <= 0:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "validation.limit",
                "message": f"limit must be positive, got {limit}",
            },
        )

    repo = get_assessment_repository()
    records = repo.history_for(x_user_id, limit=limit)
    total = repo.count_for(x_user_id)

    items = [
        AssessmentHistoryItem(
            assessment_id=r.assessment_id,
            instrument=r.instrument,
            total=r.total,
            severity=r.severity,
            requires_t3=r.requires_t3,
            created_at=r.created_at.isoformat(),
            t3_reason=r.t3_reason,
            index=r.index,
            cutoff_used=r.cutoff_used,
            positive_screen=r.positive_screen,
            triggering_items=(
                list(r.triggering_items)
                if r.triggering_items is not None
                else None
            ),
            subscales=(
                dict(r.subscales) if r.subscales is not None else None
            ),
            instrument_version=r.instrument_version,
        )
        for r in records
    ]
    return AssessmentHistoryResponse(items=items, limit=limit, total=total)


# =============================================================================
# Trajectory from history — reads the repository, builds an RCI-annotated series
# =============================================================================


class TrajectoryHistoryBaseline(BaseModel):
    """The earliest recorded reading for this instrument — the baseline
    against which every later reading is compared.

    Surfaced as a distinct shape (rather than the first entry in
    ``points``) so the chart renderer can visually distinguish the
    baseline (flat horizontal reference line) from subsequent readings
    (trajectory points).  A ``null`` baseline means the user has no
    records for this instrument yet — the client renders a 'collect a
    first reading' prompt, not an error state.
    """

    assessment_id: str
    score: float
    created_at: str


class TrajectoryHistoryPoint(BaseModel):
    """One reading strictly after the baseline, annotated with its
    reliable-change interpretation.

    ``delta`` is ``None`` when the instrument has no validated RCI
    threshold (C-SSRS, DAST-10, unknown instruments) — matching the
    :mod:`discipline.psychometric.trajectories` contract that a missing
    threshold suppresses the arithmetic delta as well.  A future UI
    sprint that wants raw deltas for non-RCI instruments can add them
    as a separate field without breaking this contract.
    """

    assessment_id: str
    score: float
    created_at: str
    delta: float | None
    direction: TrajectoryDirection


class TrajectoryHistoryResponse(BaseModel):
    """Time series for one instrument across the user's timeline.

    ``rci_threshold`` is the per-instrument |Δ| that counts as reliable
    change.  ``null`` for instruments without a validated threshold
    (C-SSRS, DAST-10) — in which case every point's ``direction`` is
    ``insufficient_data``.  The series is still returned with real
    scores and timestamps so a non-annotated chart can still render.

    Zero-record and one-record cases intentionally return HTTP 200
    rather than 404: 'this user has no readings yet' is a successful
    state the UI needs to render, not a not-found error.
    """

    instrument: str
    rci_threshold: float | None
    baseline: TrajectoryHistoryBaseline | None
    points: list[TrajectoryHistoryPoint]


_WHO5_INSTRUMENT = "who5"


def _rci_score_for(record: AssessmentRecord) -> float:
    """Pick the value that aligns with the RCI threshold scale.

    The published WHO-5 reliable-change threshold (17 points) is on the
    *index* scale (0-100), not the raw total (0-25).  Every other
    instrument is scored on the same scale as its RCI threshold (PHQ-9
    total matches the 5.2 threshold, etc.).  Rendering a WHO-5
    trajectory against raw totals would silently compress deltas by 4×
    and misclassify every clinically meaningful change as
    ``no_reliable_change``.
    """
    if record.instrument == _WHO5_INSTRUMENT and record.index is not None:
        return float(record.index)
    return float(record.total)


@router.get(
    "/trajectory/{instrument}",
    response_model=TrajectoryHistoryResponse,
    status_code=200,
    tags=["psychometric"],
)
async def trajectory_from_history(
    instrument: str,
    x_user_id: str = Header(..., alias="X-User-Id"),
) -> TrajectoryHistoryResponse:
    """Build the user's RCI-annotated trajectory for one instrument.

    Reads the authenticated user's records via the in-memory assessment
    repository, filters to this instrument, sorts oldest-first, treats
    the earliest record as the baseline per Jacobson & Truax 1991, and
    computes a reliable-change annotation for every subsequent record.

    Baseline shape (clinical contract):
    - Zero records for this instrument → ``baseline=None``, empty
      ``points``.
    - One record → baseline populated, empty ``points``.  RCI needs
      two readings by definition.
    - Two or more records → baseline + one point per subsequent record.

    Instruments without a validated RCI threshold (C-SSRS, DAST-10,
    unknown strings) return ``rci_threshold=None`` and every point's
    ``direction`` is ``insufficient_data``.  This mirrors
    :func:`discipline.psychometric.trajectories.compute_point` so the
    GET endpoint is a drop-in for the POST /trajectory path when both
    baseline and current scores are known.

    Authentication mirrors ``/history`` — missing or empty
    ``X-User-Id`` is 401.  The path parameter is stripped + lowercased
    so callers don't need to know the canonical casing.

    Route registration: this route is declared AFTER
    ``GET /trajectory/thresholds`` so the static-literal route wins —
    a request to ``/trajectory/thresholds`` returns the threshold table,
    not a trajectory for a user named 'thresholds'.
    """
    if not x_user_id:
        raise HTTPException(
            status_code=401,
            detail={
                "code": "auth.missing_user_id",
                "message": "X-User-Id header required.",
            },
        )

    instrument = instrument.strip().lower()
    repo = get_assessment_repository()
    # History is normally paginated at 50, but trajectory is an analytics
    # view across the full timeline.  10 000 covers ~200 years of weekly
    # check-ins per instrument — safely past any real retention window.
    all_records = repo.history_for(x_user_id, limit=10000)
    for_instrument = [r for r in all_records if r.instrument == instrument]
    # Repository returns newest-first; trajectories need oldest-first so
    # the earliest reading is the baseline.
    for_instrument.sort(key=lambda r: r.created_at)

    threshold = RCI_THRESHOLDS.get(instrument)

    if not for_instrument:
        return TrajectoryHistoryResponse(
            instrument=instrument,
            rci_threshold=threshold,
            baseline=None,
            points=[],
        )

    baseline_record = for_instrument[0]
    baseline_score = _rci_score_for(baseline_record)
    baseline = TrajectoryHistoryBaseline(
        assessment_id=baseline_record.assessment_id,
        score=baseline_score,
        created_at=baseline_record.created_at.isoformat(),
    )

    points: list[TrajectoryHistoryPoint] = []
    for record in for_instrument[1:]:
        score = _rci_score_for(record)
        point = compute_point(
            instrument=instrument,
            current=score,
            baseline=baseline_score,
        )
        points.append(
            TrajectoryHistoryPoint(
                assessment_id=record.assessment_id,
                score=score,
                created_at=record.created_at.isoformat(),
                delta=point.delta,
                direction=point.direction,
            )
        )

    return TrajectoryHistoryResponse(
        instrument=instrument,
        rci_threshold=threshold,
        baseline=baseline,
        points=points,
    )

"""Psychometric HTTP surface — PHQ-9, GAD-7, WHO-5, AUDIT, AUDIT-C,
C-SSRS, PSS-10, DAST-10, MDQ, PC-PTSD-5, ISI.

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
- GAD-7, WHO-5, AUDIT, AUDIT-C, PSS-10, DAST-10, MDQ, PC-PTSD-5, ISI
  have no safety items — ``requires_t3`` is always False for these
  instruments.  WHO-5 ``depression_screen`` band is *not* a T3
  trigger; T3 is reserved for active suicidality per
  Docs/Whitepapers/04_Safety_Framework.md §T3.  A positive MDQ screen
  is a referral signal for a bipolar-spectrum structured interview,
  not a crisis signal — see ``scoring/mdq.py`` module docstring.
  A positive PC-PTSD-5 is a referral signal for trauma-informed care
  (CAPS-5 / PCL-5 structured interview, EMDR / TF-CBT intake), not a
  crisis signal — see ``scoring/pcptsd5.py``.  A severe ISI result
  is a referral signal for CBT-I / sleep medicine, not a crisis
  signal — see ``scoring/isi.py``.

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
from .scoring.audit_c import (
    InvalidResponseError as AuditCInvalid,
    Sex,
    score_audit_c,
)
from .scoring.cssrs import (
    InvalidResponseError as CssrsInvalid,
    score_cssrs_screen,
)
from .scoring.dast10 import InvalidResponseError as Dast10Invalid, score_dast10
from .scoring.gad7 import InvalidResponseError as Gad7Invalid, score_gad7
from .scoring.isi import InvalidResponseError as IsiInvalid, score_isi
from .scoring.mdq import (
    ImpairmentLevel,
    InvalidResponseError as MdqInvalid,
    score_mdq,
)
from .scoring.pcptsd5 import (
    InvalidResponseError as PcPtsd5Invalid,
    score_pcptsd5,
)
from .scoring.phq9 import InvalidResponseError as Phq9Invalid, score_phq9
from .scoring.pss10 import InvalidResponseError as Pss10Invalid, score_pss10
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
}


class AssessmentRequest(BaseModel):
    """Wire-format assessment submission.

    Per-instrument item-count is validated at the route layer (after
    Pydantic) so the error message can be specific to the instrument
    ("PHQ-9 requires exactly 9 items, got N").  The Pydantic
    ``min_length=3, max_length=13`` bound is the broadest envelope
    covering every supported instrument (AUDIT-C=3 through MDQ=13);
    a tighter check needs to know the instrument value, which
    Pydantic field validators can't see in a clean way.

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
    items: list[int] = Field(min_length=3, max_length=13)
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

    For C-SSRS, ``total`` is ``positive_count`` (the number of yes
    answers, 0-6) and ``severity`` is the risk band string.  There is
    no clinically meaningful single-number "total" for C-SSRS, but
    positive_count is the closest analogue and clients can use it for
    trajectory tracking independently of band changes.
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

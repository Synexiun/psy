"""URICA short — University of Rhode Island Change Assessment, 16-item.

URICA operationalizes Prochaska & DiClemente's **transtheoretical
stages-of-change model** into a quantitative profile: four subscale
scores (precontemplation / contemplation / action / maintenance) that
together describe the user's current distance from therapeutic action.
It is the full multi-item instrument for which Readiness Ruler
(Sprint 37) is the single-item equivalent — where the Ruler reduces
stages-of-change to a 0-10 snapshot, URICA preserves the *profile*
across the four stages, making it possible to distinguish a user who
is "high contemplation, low action" (thinking about change but not
yet acting) from one who is "low precontemplation, high maintenance"
(post-action, working on relapse prevention) even when both produce
similar aggregate readiness scores.

The full 32-item URICA was introduced in

    McConnaughy EA, Prochaska JO, Velicer WF (1983).  *Stages of
    change in psychotherapy: measurement and sample profiles.*
    Psychotherapy: Theory, Research & Practice 20(3):368-375.

with confirmatory psychometric validation in

    McConnaughy EA, DiClemente CC, Prochaska JO, Velicer WF (1989).
    *Stages of change in psychotherapy: a follow-up report.*
    Psychotherapy 26(4):494-503.

demonstrating α = 0.88-0.89 across subscales and stable four-factor
structure across clinical populations.  The 16-item short form —
four items per subscale, selected from the 32-item pool by
within-subscale item-total correlation — was adopted in

    DiClemente CC, Hughes SO (1990).  *Stages of change profiles in
    outpatient alcoholism treatment.*  Journal of Substance Abuse
    2(2):217-235.

and later validated in the broader addiction-treatment context in

    Carney MM, Kivlahan DR (1995).  *Motivational subtypes among
    veterans seeking substance abuse treatment: profiles based on
    stages of change.*  Psychology of Addictive Behaviors 9(2):135-142.

The short form demonstrates r = 0.92-0.95 with the 32-item form
across subscales, at half the administration time.

Clinical relevance to the Discipline OS platform:
URICA is the **multi-stage profile instrument** — paired with
Readiness Ruler as its single-item snapshot (Ruler = "where are you
today?", URICA = "*what does your stages-of-change distribution look
like?*").  The intervention layer uses the four-subscale profile to
pick therapist-scripts that match the user's stage-composition, not
just aggregate readiness:

- **High precontemplation, low others** → decisional-balance
  elicitation, empathic reflection of ambivalence.
- **High contemplation, low action** → change-talk amplification,
  self-efficacy building.
- **High action, high maintenance** → relapse-prevention planning,
  implementation-intentions consolidation.
- **High maintenance, rising precontemplation** → classic relapse
  warning signature (maintenance fading as precontemplation
  endorsement creeps back).  The trajectory layer reading
  URICA across weeks flags this pattern as a high-priority
  intervention-window opening.

The cadence per Docs/Technicals/12_Psychometric_System.md §3.1 is
**monthly** (vs Ruler's weekly and craving VAS's EMA).  A monthly
URICA + weekly Ruler + daily VAS gives the intervention layer three
temporal windows on the motivation construct — the slowest-moving
is the stage-composition shift URICA measures.

Instrument structure (DiClemente & Hughes 1990):

**16 items, each on a 1-5 Likert scale** (1 = Strongly Disagree,
2 = Disagree, 3 = Undecided, 4 = Agree, 5 = Strongly Agree),
organized into 4 subscales of 4 items each.  The positional order
is pinned: items 1-4 → Precontemplation, 5-8 → Contemplation,
9-12 → Action, 13-16 → Maintenance.

Example items (abridged — the full verbatim item bank is
maintained in the content layer):

Precontemplation (items 1-4): "As far as I'm concerned, I don't
have any problems that need changing."  "All this talk about
psychology is boring."  (Higher endorsement = more
precontemplation = further from action.)

Contemplation (items 5-8): "I think I might be ready for some
self-improvement."  "I have been thinking that I might want to
change something about myself."  (Higher endorsement = more
contemplation.)

Action (items 9-12): "I am actively working on my problem."  "I am
doing something about the problems that had been bothering me."
(Higher endorsement = more active change-behavior.)

Maintenance (items 13-16): "I am here to prevent myself from
having a relapse."  "After all I had done to try to change my
problem, every now and again it comes back to haunt me."  (Higher
endorsement = more maintenance-stage work.)

Scoring (DiClemente & Hughes 1990):

**Subscale totals** — straight sum of the 4 items in each subscale,
range 4-20 per subscale.  No reverse-coding: each item is
positively-keyed to its stage (higher endorsement = more of that
stage), so item-level inversions would invalidate the stage-
construct meaning.

**Readiness composite** — the load-bearing summary score:

    Readiness = Contemplation + Action + Maintenance − Precontemplation

Range: 3×4 − 20 = **−8** (pure precontemplation profile) through
3×20 − 4 = **+56** (deep action / maintenance profile, minimal
precontemplation endorsement).  **Signed integer** — a negative
reading is clinically meaningful and indicates the user is further
from action than a neutral stance.  This is the *first signed
total* in the psychometric package; PHQ-9 / GAD-7 / PACS / DTCQ-8
and every other instrument produces non-negative totals.

The signed composite is the canonical URICA summary (Project MATCH
1997, DiClemente 2004); alternative formulations that normalize by
subscale means produce essentially the same trajectory signal at
float precision, but lose information relative to the sum form.
Keeping it as a signed int preserves RCI arithmetic without
floating-point drift.

**Direction semantics — higher is better**:
Following WHO-5 / Readiness Ruler / DTCQ-8, rising URICA Readiness
is therapeutic *improvement*.  The trajectory layer must register
URICA in the higher-is-better partition alongside WHO-5 / Ruler /
DTCQ-8.  The zero-crossing is an additional signal unique to URICA:
a Readiness trajectory crossing from positive to negative is a
particularly clinically salient shift (dropping below "neutral"
is not the same as reducing a PHQ-9 from 10 to 8).

Severity bands — deliberately absent:
DiClemente & Hughes 1990 and subsequent URICA validation papers
publish **no absolute cutoffs**.  The canonical analytic approach
is cluster analysis of the four-subscale profile (McConnaughy 1983,
Project MATCH 1997) — users are grouped into motivational subtypes
(precontemplators, contemplators, participators, etc.) based on
*relative* subscale patterns, not on Readiness thresholds.  A
hand-rolled Readiness cutoff would violate CLAUDE.md's "Don't
hand-roll severity thresholds" rule and obscure the stage-profile
signal that is the whole clinical point of the instrument.

Accordingly the scorer emits no severity band; the router envelope
uses ``severity="continuous"`` as a sentinel (uniform with PACS /
Craving VAS / Readiness Ruler / DTCQ-8).  The clinical value lives
in the 4-subscale profile, which the router *does* surface on the
wire (the first multi-subscale wire-exposed instrument in the
package — PCL-5, OCI-R, and BIS-11 compute subscales but defer
surfacing until their dedicated cluster/subscale UI ships).

Safety routing:
URICA carries no suicidality item and no acute-harm item.
``requires_t3`` is deliberately absent — a precontemplation-
dominant profile is a motivation signal routing to MI-scripted
interventions, not a crisis signal.  Low readiness (or even
negative Readiness) pairs with low-agency mood profiles but the
product responds with stage-matched motivational work rather than
T4 human handoff.  Acute ideation is gated by PHQ-9 item 9 /
C-SSRS per the uniform safety-posture convention across PACS /
PHQ-15 / OCI-R / ISI / VAS / Ruler / DTCQ-8.

Bool rejection note:
Uniform with the rest of the psychometric package — bool items
are rejected at the validator.  A caller submitting ``True`` /
``False`` as shorthand for agree/disagree would have their response
silently coerced to 1 / 0.  On URICA's 1-5 scale, ``0`` is out of
range and would fail item-range validation, but catching the bool
at the type check produces a more diagnostic error ("must be int,
got True").

FHIR / LOINC note:
LOINC has codes for various stage-of-change instruments but no
widely-adopted code for the URICA 16-item short form.  Per the
DTCQ-8 / PACS / VAS / Ruler / C-SSRS precedent, URICA is NOT
registered in ``LOINC_CODE`` / ``LOINC_DISPLAY`` at this time; the
FHIR export will use a system-local code when the reports-layer
render path is extended in a later sprint.  The four subscale
scores will be emitted as Observation components (matching the
FHIR R4 component pattern for multi-part instruments) so the
stage profile is recoverable from the exported record.

Behavior-target neutrality:
The scorer is behavior-agnostic — "the problem" in the URICA item
wording is resolved at the UI layer (alcohol, drugs, gambling,
porn-use, etc.) based on the user's vertical.  This matches
McConnaughy 1983's original transtheoretical-model framing, which
was deliberately cross-diagnostic.

References:
- McConnaughy EA, Prochaska JO, Velicer WF (1983).  *Stages of
  change in psychotherapy: measurement and sample profiles.*
  Psychotherapy: Theory, Research & Practice 20(3):368-375.
- McConnaughy EA, DiClemente CC, Prochaska JO, Velicer WF (1989).
  *Stages of change in psychotherapy: a follow-up report.*
  Psychotherapy 26(4):494-503.
- DiClemente CC, Hughes SO (1990).  *Stages of change profiles in
  outpatient alcoholism treatment.*  Journal of Substance Abuse
  2(2):217-235.
- Carney MM, Kivlahan DR (1995).  *Motivational subtypes among
  veterans seeking substance abuse treatment.*  Psychology of
  Addictive Behaviors 9(2):135-142.
- Project MATCH Research Group (1997).  *Matching alcoholism
  treatments to client heterogeneity: Project MATCH posttreatment
  drinking outcomes.*  Journal of Studies on Alcohol 58(1):7-29.
- DiClemente CC (2004).  *Readiness to Change Questionnaire:
  scoring and interpretation.*  University of Maryland, Baltimore
  County.
- Prochaska JO, DiClemente CC (1983).  *Stages and processes of
  self-change of smoking.*  Journal of Consulting and Clinical
  Psychology 51(3):390-395.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

INSTRUMENT_VERSION = "urica-1.0.0"
ITEM_COUNT = 16
ITEM_MIN = 1
ITEM_MAX = 5
SUBSCALE_SIZE = 4

# Positional subscale slots.  Tuples (not range objects / lists) so
# the mapping is immutable at import time — the intervention layer's
# per-subscale profile read is load-bearing, and a mutable ordering
# would be silently corruptible.
#
# Order matches DiClemente & Hughes 1990's administration order:
# Precontemplation (items 1-4) → Contemplation (5-8) → Action (9-12)
# → Maintenance (13-16).  A reorder would silently swap the stage
# attribution of every response.
SUBSCALE_PRECONTEMPLATION_SLOTS: tuple[int, ...] = (0, 1, 2, 3)
SUBSCALE_CONTEMPLATION_SLOTS: tuple[int, ...] = (4, 5, 6, 7)
SUBSCALE_ACTION_SLOTS: tuple[int, ...] = (8, 9, 10, 11)
SUBSCALE_MAINTENANCE_SLOTS: tuple[int, ...] = (12, 13, 14, 15)

# Public label tuple — matches DTCQ-8's SITUATION_LABELS pattern.
# The intervention layer and the FHIR exporter read subscale names
# through this constant rather than hard-coding strings.
SUBSCALE_LABELS: tuple[str, ...] = (
    "precontemplation",
    "contemplation",
    "action",
    "maintenance",
)


class InvalidResponseError(ValueError):
    """Raised on item-count, item-range, or item-type violations."""


@dataclass(frozen=True)
class UricaResult:
    """Typed URICA short-form output.

    Fields:
    - ``total``: the Readiness composite —
      ``contemplation + action + maintenance − precontemplation``.
      Range **−8 to +56** (signed int).  Flows into the trajectory
      layer as a **higher-is-better** continuous motivation signal
      with clinically-meaningful zero-crossing semantics (negative
      Readiness = further from action than neutral).
    - ``precontemplation``: sum of items 1-4, range 4-20.  Higher =
      more precontemplation-stage endorsement.
    - ``contemplation``: sum of items 5-8, range 4-20.
    - ``action``: sum of items 9-12, range 4-20.
    - ``maintenance``: sum of items 13-16, range 4-20.
    - ``items``: verbatim 16-tuple, pinned for auditability AND for
      downstream consumers who want per-item profile analysis
      (cluster-analytic subtyping per McConnaughy 1983).

    Deliberately-absent fields:
    - No ``severity`` field — DiClemente & Hughes 1990 publishes no
      bands; the literature treats URICA cluster-analytically, not
      cutoff-categorically.  The router envelope emits
      ``severity="continuous"`` as a sentinel (uniform with PACS /
      Craving VAS / Ruler / DTCQ-8).
    - No ``requires_t3`` field — URICA measures motivation-profile,
      not crisis.  A precontemplation-dominant profile is a
      motivation signal, not a T3 trigger; acute suicidality is
      gated by PHQ-9 / C-SSRS.
    """

    total: int
    precontemplation: int
    contemplation: int
    action: int
    maintenance: int
    items: tuple[int, ...]
    instrument_version: str = INSTRUMENT_VERSION


def _validate_item(index_1: int, value: object) -> int:
    """Validate a single 1-5 URICA Likert item and return the int value.

    ``index_1`` is the 1-indexed item number (1-16) so error messages
    name the item a clinician would recognize from the DiClemente &
    Hughes 1990 instrument document.  The per-item subscale attribution
    is not included in the error message — the 1-indexed number is
    sufficient and the subscale label would leak implementation detail
    into validation text.
    """
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidResponseError(
            f"URICA item {index_1} must be int, got {value!r}"
        )
    if value < ITEM_MIN or value > ITEM_MAX:
        raise InvalidResponseError(
            f"URICA item {index_1} out of range "
            f"[{ITEM_MIN}, {ITEM_MAX}]: {value}"
        )
    return value


def _subscale_sum(items: tuple[int, ...], slots: tuple[int, ...]) -> int:
    """Sum the 4 items at the given positional slots.

    Extracted to a helper so the Readiness-composite arithmetic reads
    as ``C + A + M - PC`` at the call site rather than four inline
    slice-sums.  ``slots`` is one of the ``SUBSCALE_*_SLOTS`` constants.
    """
    return sum(items[i] for i in slots)


def score_urica(raw_items: Sequence[int]) -> UricaResult:
    """Score a URICA short-form response set.

    Inputs:
    - ``raw_items``: 16 integers, each 1-5 Likert, positional in the
      DiClemente & Hughes 1990 administration order (items 1-4 =
      Precontemplation, 5-8 = Contemplation, 9-12 = Action, 13-16 =
      Maintenance).

    Raises :class:`InvalidResponseError` on:
    - Wrong number of items (anything other than 16).
    - A non-int / bool item value.
    - An item outside ``[1, 5]``.

    Returns a :class:`UricaResult` with:
    - The four subscale sums (each 4-20).
    - The Readiness composite as ``total`` (signed int, -8 to +56).
    - The pinned 16-tuple.

    No severity band is emitted — see module docstring.
    """
    if len(raw_items) != ITEM_COUNT:
        raise InvalidResponseError(
            f"URICA requires exactly {ITEM_COUNT} items, got {len(raw_items)}"
        )
    items = tuple(
        _validate_item(index_1=i + 1, value=v)
        for i, v in enumerate(raw_items)
    )

    precontemplation = _subscale_sum(items, SUBSCALE_PRECONTEMPLATION_SLOTS)
    contemplation = _subscale_sum(items, SUBSCALE_CONTEMPLATION_SLOTS)
    action = _subscale_sum(items, SUBSCALE_ACTION_SLOTS)
    maintenance = _subscale_sum(items, SUBSCALE_MAINTENANCE_SLOTS)

    # Readiness composite per DiClemente & Hughes 1990 /
    # Project MATCH 1997.  Signed — a negative result is clinically
    # meaningful (precontemplation-dominant profile).
    total = contemplation + action + maintenance - precontemplation

    return UricaResult(
        total=total,
        precontemplation=precontemplation,
        contemplation=contemplation,
        action=action,
        maintenance=maintenance,
        items=items,
    )


__all__ = [
    "INSTRUMENT_VERSION",
    "InvalidResponseError",
    "ITEM_COUNT",
    "ITEM_MAX",
    "ITEM_MIN",
    "SUBSCALE_SIZE",
    "SUBSCALE_PRECONTEMPLATION_SLOTS",
    "SUBSCALE_CONTEMPLATION_SLOTS",
    "SUBSCALE_ACTION_SLOTS",
    "SUBSCALE_MAINTENANCE_SLOTS",
    "SUBSCALE_LABELS",
    "UricaResult",
    "score_urica",
]

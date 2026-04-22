"""CORE-10 — Clinical Outcomes in Routine Evaluation (Barkham 2013).

The CORE-10 is a 10-item global measure of psychological distress
designed for session-by-session routine-outcome monitoring in
psychological therapy.  Barkham, Bewick, Mullin, Gilbody, Connell,
Cahill, Mellor-Clark, Richards, Unsworth & Evans (2013) published
the canonical validation in *Counselling and Psychotherapy Research*
13(1):3-13, deriving the 10-item short form from the 34-item CORE-OM
(Evans, Mellor-Clark, Margison, Barkham, Audin, Connell & McGrath
2000) and validating it against structured clinical interviews on a
n=1,241 UK NHS IAPT sample.  Connell & Barkham (2007) published the
CORE-10 User Manual Version 1.1 (CORE System Trust / CORE IMS),
which is the pinned source-of-truth for the item text, the
administration order, the response scale, the reverse-keying
convention, and the Barkham 2013 severity bands.

Clinical relevance to the Discipline OS platform:

The CORE-10 fills the **routine-outcome-tracking** gap in the
platform's roster.  Prior instruments each measure a single
construct (PHQ-9 depression, GAD-7 anxiety, PSS-10 stress, WHO-5
wellbeing); CORE-10 measures **global psychological distress** as
an umbrella construct that cuts across affective, somatic,
interpersonal, and functional dimensions.  The CORE-10 is the
instrument UK NHS IAPT services administer **every session** as
the primary outcome measure — its three-year cumulative RCI / JT
trajectory is the backbone of UK-NHS-equivalent routine outcome
reporting.

Construct placement relative to the existing roster:

- **PHQ-9** (Kroenke 2001) measures major-depressive-disorder
  symptom burden on the DSM-IV 9-symptom criterion set.  CORE-10
  covers depression (items 8, 9), anxiety (items 1, 5), risk
  (item 6), but is NOT a DSM-criterion measure.
- **GAD-7** (Spitzer 2006) measures generalized-anxiety-disorder
  symptom burden on 7 DSM-IV-based items.  CORE-10 samples
  anxiety (items 1, 5) but does not cover worry-specific GAD
  criteria.
- **PSS-10** (Cohen 1983) measures perceived-stress appraisal on
  10 items.  CORE-10 overlaps on the coping/functioning dimension
  (items 2, 3) but frames the construct as session-by-session
  distress, not dispositional stress perception.
- **WHO-5** (Bech 1998) measures affective wellbeing on 5 items.
  CORE-10 covers the inverse end — distress — with two
  reverse-keyed wellbeing items (2, 3) that overlap modestly
  with WHO-5 constructs.
- **C-SSRS** (Posner 2011) is a structured acuity-triage
  instrument for active suicidality.  CORE-10 has a single risk
  item (item 6: "I made plans to end my life") which is a
  PLANNING-LEVEL suicidality probe — equivalent to C-SSRS item 3
  (ideation with method, intent, or plan).  Any non-zero value
  on CORE-10 item 6 → scorer-layer T3 flag, consistent with
  Barkham 2013 guidance and the platform's PHQ-9-item-9 precedent.

The CORE-10 item 6 makes this the **third instrument with scorer-
layer T3 routing** (after PHQ-9 item 9 per Kroenke 2001 and C-SSRS
items 4/5/6 per Posner 2011).  The routing threshold is a **single
non-zero response on item 6** — "Only occasionally" (= 1) or higher
indicates that the respondent has made plans to end their life at
least once in the past week.  Barkham 2013 and subsequent IAPT
safety guidance treat this as a mandatory clinician-review trigger.

Pairings with existing instruments:

- **CORE-10 trajectory + PHQ-9 / GAD-7** — CORE-10 is the
  primary RCI-based routine-outcome measure; PHQ-9 and GAD-7
  surface construct-specific severity for session-specific case
  formulation.  The Barkham 2013 RCI ≈ 6 points lets the
  trajectory layer flag Jacobson & Truax 1991 reliable change on
  a session-to-session granularity.
- **CORE-10 item 6 positive + PHQ-9 item 9 positive** — two
  independent suicidality probes co-positive → C-SSRS follow-up
  at the clinician-UI layer.  BOTH scorers set requires_t3 on
  their own, so the safety event fires regardless of which
  instrument was administered.
- **CORE-10 severe (≥ 25) + WSAS clinically-significant
  (≥ 20)** — "distressed-AND-impaired" profile.  Intervention
  match: intensive clinical engagement / referral to higher
  level of care (Mundt 2002 / Marks 1986).
- **CORE-10 moderate (15-19) + readiness-ruler low** — ambivalent
  about change despite moderate distress.  Intervention match:
  Rollnick 1999 / Heather 2008 motivational-interviewing
  elicitation of change talk.
- **CORE-10 healthy (0-5) at follow-up after baseline moderate+**
  — Barkham 2013 RCI-based recovery signal.  Maintenance-
  oriented interventions.

Barkham 2013 severity bands (NOT hand-rolled — taken verbatim from
Table 3 of the Barkham 2013 publication):

    Healthy:                0-5
    Low level:              6-10
    Mild:                   11-14
    Moderate:               15-19
    Moderate-to-severe:     20-24
    Severe:                 25-40

Clinical cutoff: **≥ 11** (Barkham 2013 Table 3).  A total ≥ 11
distinguishes clinical-caseness from non-clinical populations; a
total < 11 is the "healthy" / "low level" category.

Instrument structure (Connell & Barkham 2007):

**10 items, each on a 5-point Likert frequency scale (0-4)**:
    0 = Not at all
    1 = Only occasionally
    2 = Sometimes
    3 = Often
    4 = Most or all the time

Timeframe: past week.

**Two reverse-keyed items** (wellbeing / functioning items —
higher raw response = LESS distress; reverse to align sum-
direction):

    Item 2: "I have felt I have someone to turn to for support
            when needed."  (wellbeing / social-support; REVERSE)
    Item 3: "I have felt able to cope when things go wrong."
            (functioning / coping; REVERSE)

The remaining 8 items are worded in the distress-positive
direction (higher raw = MORE distress).

Verbatim CORE-10 item text (Connell & Barkham 2007 administration
order):

    1.  I have felt tense, anxious or nervous.
    2.  I have felt I have someone to turn to for support when
        needed.                                         [REVERSE]
    3.  I have felt able to cope when things go wrong.  [REVERSE]
    4.  Talking to people has felt too much for me.
    5.  I have felt panic or terror.
    6.  I made plans to end my life.                    [RISK]
    7.  I have had difficulty getting to sleep or staying
        asleep.
    8.  I have felt despairing or hopeless.
    9.  I have felt unhappy.
    10. Unwanted images or memories have been distressing me.

Scoring:

- Apply reverse-keying to items 2 and 3: ``flipped_v = 4 - raw_v``.
- Total = straight sum of the 10 post-flip values, range 0-40.
- Lookup severity band from Barkham 2013 Table 3.
- Positive screen: total ≥ 11.
- **Risk check**: item 6 raw > 0 → requires_t3 = True, and 6
  surfaces in triggering_items.
- Raw items preserved in ``items`` field (audit invariance — the
  scorer stores the pre-flip values so a clinician can reconstruct
  the original responses).

T3 posture:

CORE-10 item 6 raw > 0 → scorer-layer requires_t3 = True.
Threshold is **any non-zero response** (Only occasionally,
Sometimes, Often, Most or all the time) — Barkham 2013 and
CORE-IMS safety guidance treat "I made plans to end my life" as
a mandatory clinician-review trigger regardless of frequency.
The single-item threshold parallels PHQ-9 item 9 (Kroenke 2001;
any non-zero) and is MORE conservative than C-SSRS (which
requires specific item / behavior combinations for T3).

The triggering_items surface carries 6 (1-indexed) so the
clinician-UI renderer can display "the CORE-10 item 6 response
escalated this screen" as an audit trail, matching C-SSRS
triggering_items semantics.

Design invariants preserved:

- **10-item exact count**.  Barkham 2013 pinned the 10-item
  structure.  CORE-OM (34-item), CORE-SF-A (18-item), and
  CORE-SF-B (18-item) are separate instruments with different
  psychometrics; if shipped they warrant separate scorers.
- **Administration order pinned**.  Connell & Barkham 2007
  published the order; Barkham 2013 validation was conducted at
  the pinned order.
- **Reverse-keyed items pinned**.  Items 2 and 3 are the
  wellbeing/functioning items in CORE-10 v1.1; changing the
  reverse-keying list would break the alignment with the
  Barkham 2013 severity bands.
- **Bool rejection at the scorer.**  Platform-wide invariant per
  CLAUDE.md standing rule: True/False booleans are rejected
  before the int check.
- **Risk threshold pinned at ≥ 1**.  Any non-zero on item 6 →
  T3.  This matches PHQ-9 item 9 (Kroenke 2001) and Barkham 2013
  routine-outcome-monitoring safety guidance.

Citations:

- Barkham M, Bewick B, Mullin T, Gilbody S, Connell J, Cahill J,
  Mellor-Clark J, Richards D, Unsworth G, Evans C (2013).  *The
  CORE-10: A short measure of psychological distress for routine
  use in the psychological therapies.*  Counselling and
  Psychotherapy Research 13(1):3-13.  (Canonical derivation;
  n=1,241; Cronbach α=0.90; RCI=6; severity-band cutoffs pinned
  in Table 3.)
- Connell J, Barkham M (2007).  *CORE-10 User Manual, Version 1.1.*
  CORE System Trust & CORE Information Management Systems Ltd.
  (Pinned source-of-truth for item text, administration order,
  reverse-keying convention, and scoring procedure.)
- Evans C, Mellor-Clark J, Margison F, Barkham M, Audin K,
  Connell J, McGrath G (2000).  *CORE: Clinical Outcomes in
  Routine Evaluation.*  Journal of Mental Health 9(3):247-255.
  (Foundational CORE-OM 34-item derivation; basis for the
  CORE-10 item selection.)
- Mellor-Clark J, Barkham M, Connell J, Evans C (1999).  *Practice-
  based evidence and standardised evaluation: Informing the design
  of the CORE System.*  European Journal of Psychotherapy,
  Counselling and Health 2(3):357-374.  (CORE measurement system
  design rationale.)
- Leach C, Lucock M, Barkham M, Stiles WB, Noble R, Iveson S
  (2006).  *Transforming between Beck Depression Inventory and
  CORE-OM scores in routine clinical practice.*  British Journal
  of Clinical Psychology 45(2):153-166.  (Convergent validity
  across depression instruments.)
- Jacobson NS, Truax P (1991).  *Clinical significance: A
  statistical approach to defining meaningful change in
  psychotherapy research.*  Journal of Consulting and Clinical
  Psychology 59(1):12-19.  (RCI methodology; Barkham 2013 pinned
  RCI=6 for CORE-10.)
- Kroenke K, Spitzer RL, Williams JBW (2001).  *The PHQ-9:
  Validity of a brief depression severity measure.*  Journal of
  General Internal Medicine 16(9):606-613.  (PHQ-9 item 9
  precedent for any-non-zero T3 threshold.)
- Posner K, Brown GK, Stanley B, Brent DA, Yershova KV, Oquendo
  MA, Currier GW, Melvin GA, Greenhill L, Shen S, Mann JJ (2011).
  *The Columbia-Suicide Severity Rating Scale: Initial validity
  and internal consistency findings from three multisite studies
  with adolescents and adults.*  American Journal of Psychiatry
  168(12):1266-1277.  (C-SSRS item 3 planning-level suicidality
  precedent for CORE-10 item 6 handling.)
- Simon GE, Rutter CM, Peterson D, Oliver M, Whiteside U,
  Operskalski B, Ludman EJ (2013).  *Does response on the PHQ-9
  Depression Questionnaire predict subsequent suicide attempt or
  suicide death?*  Psychiatric Services 64(12):1195-1202.
  (Convergent support for any-non-zero T3 threshold on single-
  item suicidality probes.)
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

INSTRUMENT_VERSION = "core10-1.0.0"
ITEM_COUNT = 10
ITEM_MIN, ITEM_MAX = 0, 4

# Connell & Barkham 2007 CORE-10 v1.1: items 2 and 3 are the
# wellbeing/functioning items worded in the distress-NEGATIVE
# direction (higher raw = LESS distress).  Reverse-keying aligns
# sum-direction: flipped_v = 4 - raw_v.  1-indexed per the
# published administration order.
CORE10_REVERSE_ITEMS: tuple[int, ...] = (2, 3)

# Item 6 is the risk / suicidality-planning probe per Connell &
# Barkham 2007.  Any non-zero value → scorer-layer T3 flag.  The
# 1-indexed position IS the position clinicians identify the item
# by when reading a CORE-10 protocol.
CORE10_RISK_ITEM: int = 6

# Barkham 2013 clinical cutoff.  ≥ 11 distinguishes clinical-
# caseness from non-clinical populations.  < 11 is the "healthy"
# / "low level" category.
CORE10_CLINICAL_CUTOFF: int = 11

# Barkham 2013 Table 3 severity bands.  Pinned as an ordered list
# of (upper_inclusive_bound, label) tuples so band lookup is
# linear-scan with early termination.  NOT hand-rolled — matches
# Barkham 2013 verbatim.
CORE10_SEVERITY_THRESHOLDS: tuple[tuple[int, str], ...] = (
    (5, "healthy"),
    (10, "low"),
    (14, "mild"),
    (19, "moderate"),
    (24, "moderate_severe"),
    (40, "severe"),
)


class InvalidResponseError(ValueError):
    """Raised on item-count, item-range, or item-type violations."""


Severity = Literal[
    "healthy", "low", "mild", "moderate", "moderate_severe", "severe"
]


@dataclass(frozen=True)
class Core10Result:
    """Typed CORE-10 output.

    Fields:
    - ``total``: 0-40 sum of the ten 0-4 Likert items AFTER
      reverse-keying items 2 and 3.  Higher = MORE psychological
      distress (opposite direction from WHO-5 / GSE / BRS / SWLS;
      uniform with PHQ-9 / GAD-7 / PSS-10 "higher-is-more-distress").
    - ``severity``: Barkham 2013 Table 3 severity band.  One of
      ``"healthy"``, ``"low"``, ``"mild"``, ``"moderate"``,
      ``"moderate_severe"``, ``"severe"``.
    - ``positive_screen``: True if total ≥ 11 (Barkham 2013
      clinical cutoff).  Flagged in the UI as "clinical caseness".
    - ``cutoff_used``: the clinical cutoff applied (11).  Surfaced
      for the UI ("positive at ≥ N" rendering).
    - ``requires_t3``: True if item 6 raw response > 0.  CORE-10
      item 6 ("I made plans to end my life") — any non-zero
      response triggers scorer-layer T3 routing, matching PHQ-9
      item 9 (Kroenke 2001) and C-SSRS item 3 (Posner 2011)
      precedents.
    - ``triggering_items``: 1-indexed item numbers that drove the
      T3 flag.  For CORE-10 this is either ``(6,)`` if item 6 > 0
      or ``()`` otherwise.  Matches C-SSRS triggering_items
      semantics.
    - ``items``: verbatim 10-tuple of RAW 0-4 responses in
      Connell & Barkham 2007 administration order (pre-flip).
      Preserved for audit invariance and FHIR R4 export so a
      clinician can reconstruct the original responses before
      reverse-keying was applied.
    """

    total: int
    severity: Severity
    positive_screen: bool
    cutoff_used: int
    requires_t3: bool
    triggering_items: tuple[int, ...]
    items: tuple[int, ...]
    instrument_version: str = INSTRUMENT_VERSION


def _validate_item(index_1: int, value: object) -> int:
    """Validate a single 0-4 Likert item.

    Bool rejection per CLAUDE.md standing rule: ``bool`` values
    are rejected before the int check because Python's ``bool is
    int`` ancestry would silently accept ``True`` / ``False``.
    """
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidResponseError(
            f"CORE-10 item {index_1} must be int, got {value!r}"
        )
    if not (ITEM_MIN <= value <= ITEM_MAX):
        raise InvalidResponseError(
            f"CORE-10 item {index_1} must be in {ITEM_MIN}-{ITEM_MAX}, "
            f"got {value}"
        )
    return value


def _severity_band(total: int) -> Severity:
    """Look up the Barkham 2013 severity band for a given total."""
    for upper_bound, label in CORE10_SEVERITY_THRESHOLDS:
        if total <= upper_bound:
            return label  # type: ignore[return-value]
    # Unreachable — the last threshold is 40 which is the maximum
    # possible total after validation.
    raise InvalidResponseError(
        f"CORE-10 total {total} exceeds Barkham 2013 severity bands"
    )


def score_core10(raw_items: Sequence[int]) -> Core10Result:
    """Score a CORE-10 response set.

    Inputs:
    - ``raw_items``: 10 items, each 0-4 Likert (0 = Not at all,
      4 = Most or all the time), in Connell & Barkham 2007
      administration order.

    Raises :class:`InvalidResponseError` on:
    - Wrong number of items (must be exactly 10).
    - A non-int / bool item value.
    - An item outside ``[0, 4]``.

    Computes:
    - Reverse-keys items 2 and 3 (wellbeing / functioning items):
      ``flipped_v = 4 - raw_v``.
    - ``total``: sum of post-flip values, range 0-40.
    - ``severity``: Barkham 2013 Table 3 band.
    - ``positive_screen``: True if total ≥ 11.
    - ``requires_t3``: True if item 6 raw > 0 (Barkham 2013
      safety guidance).
    - ``triggering_items``: (6,) if requires_t3 else ().
    - ``items``: tuple of RAW responses (pre-flip — audit
      invariance).

    Platform-wide invariants preserved:
    - Reverse-keying items 2 and 3 (Connell & Barkham 2007).
    - Barkham 2013 severity bands taken verbatim (not hand-rolled).
    - Scorer-layer T3 routing on item 6 > 0 (platform-third
      instrument with this pattern after PHQ-9 and C-SSRS).
    """
    if len(raw_items) != ITEM_COUNT:
        raise InvalidResponseError(
            f"CORE-10 requires exactly {ITEM_COUNT} items, "
            f"got {len(raw_items)}"
        )
    raw = tuple(
        _validate_item(index_1=i + 1, value=v)
        for i, v in enumerate(raw_items)
    )

    # Reverse-key items 2 and 3 (1-indexed).  Post-flip values
    # feed into the total; raw values stay in the items field.
    flipped = list(raw)
    for pos_1_indexed in CORE10_REVERSE_ITEMS:
        flipped[pos_1_indexed - 1] = ITEM_MAX - raw[pos_1_indexed - 1]

    total = sum(flipped)
    severity = _severity_band(total)
    positive_screen = total >= CORE10_CLINICAL_CUTOFF

    # Barkham 2013 item-6 risk check — any non-zero response on
    # "I made plans to end my life" → scorer-layer T3.  Matches
    # PHQ-9 item 9 (Kroenke 2001) any-non-zero precedent.
    item_6_raw = raw[CORE10_RISK_ITEM - 1]
    requires_t3 = item_6_raw > 0
    triggering_items: tuple[int, ...] = (
        (CORE10_RISK_ITEM,) if requires_t3 else ()
    )

    return Core10Result(
        total=total,
        severity=severity,
        positive_screen=positive_screen,
        cutoff_used=CORE10_CLINICAL_CUTOFF,
        requires_t3=requires_t3,
        triggering_items=triggering_items,
        items=raw,
    )


__all__ = [
    "CORE10_CLINICAL_CUTOFF",
    "CORE10_REVERSE_ITEMS",
    "CORE10_RISK_ITEM",
    "CORE10_SEVERITY_THRESHOLDS",
    "INSTRUMENT_VERSION",
    "ITEM_COUNT",
    "ITEM_MAX",
    "ITEM_MIN",
    "Core10Result",
    "InvalidResponseError",
    "Severity",
    "score_core10",
]

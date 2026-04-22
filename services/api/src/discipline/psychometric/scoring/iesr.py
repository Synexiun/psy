"""IES-R — Impact of Event Scale-Revised (Weiss & Marmar 1997).

The Impact of Event Scale-Revised is the most widely-used self-
report measure of subjective distress in response to a specific
traumatic event.  Weiss & Marmar (1997) revised the original 15-
item IES (Horowitz, Wilner & Alvarez 1979) by adding a 7-item
hyperarousal subscale matching DSM-IV PTSD criterion D, yielding
the current 22-item three-subscale instrument.  Creamer, Bell &
Failla (2003; Behaviour Research and Therapy 41(12):1489-1496)
published the canonical psychometric validation on n=386 Vietnam
veterans, reporting Cronbach α ≥ 0.87 for each subscale, ROC AUC
= 0.88 for total score against CAPS structured diagnostic
interview, and the widely-cited clinical cutoff of total ≥ 33 for
probable PTSD.

Clinical relevance to the Discipline OS platform:

The IES-R fills a **non-DSM-aligned trauma-symptom-clustering**
gap in the platform's trauma roster.  Prior trauma instruments
each take a different angle:

- **PC-PTSD-5** (Prins 2016) is a 5-item first-pass PTSD
  screener (any-3-positive → referral) — a TRIAGE tool, not a
  symptom-severity measure.
- **PCL-5** (Weathers 2013) is a 20-item DSM-5-ALIGNED symptom
  severity measure — each item maps to a specific DSM-5 Criterion
  B/C/D/E symptom.  Best for DSM-5 diagnostic-workup contexts
  (structured interview preparation, disability evaluation).
- **IES-R** (Weiss & Marmar 1997) is a 22-item FACTOR-ANALYTIC
  three-subscale measure (intrusion / avoidance / hyperarousal)
  derived from Horowitz 1979's information-processing theory of
  trauma response (Horowitz "stress response syndrome").  Best
  for subjective-distress tracking and clinical-trial outcome
  reporting, where the three-subscale decomposition maps to
  distinct clinical targets.
- **ACEs** (Felitti 1998) is a 10-item LIFETIME-EXPOSURE
  instrument — it counts distinct categories of childhood
  adversity; it is NOT a symptom-severity measure.

Trauma is clinically central to the Discipline OS population.
Felitti 1998 (n=17,337 Kaiser) established the dose-response
relationship between childhood adversity and adult substance-
use disorder (ACE score ≥ 4 → ~10× increased SUD risk).  van
der Kolk 1996 documented dissociation / affect-dysregulation
as mediator between trauma exposure and addictive behavior.
Najavits 2002 operationalized the PTSD + SUD intervention
framework ("Seeking Safety") around concurrent symptom
tracking.  IES-R provides the routine-outcome tracking
instrument for that framework.

Construct placement against PCL-5:

Both IES-R and PCL-5 measure trauma-symptom severity, but they
partition the symptom space differently:

    DSM-5 / PCL-5 (4 clusters):
      Criterion B: Intrusion (5 items)
      Criterion C: Avoidance (2 items)
      Criterion D: Negative cognitions & mood (7 items)
      Criterion E: Hyperarousal & reactivity (6 items)

    IES-R / Weiss & Marmar 1997 (3 factors):
      Intrusion (8 items)       — includes dreams, waves of feeling
      Avoidance (8 items)       — includes emotional numbing
      Hyperarousal (6 items)    — physiological arousal + concentration

PCL-5 separates negative cognitions/mood from avoidance; IES-R
folds emotional numbing into avoidance.  PCL-5's cluster D
(negative cognitions/mood) corresponds to a MIXTURE of IES-R's
avoidance (numbing) and intrusion (rumination).

The two instruments are moderately-to-strongly correlated
(r ≈ 0.80 across samples; Beck 2008) but neither is a strict
superset of the other.  Concurrent administration is common in
trauma-specialty clinics; for routine-outcome contexts one is
usually sufficient.

Pairings with existing instruments:

- **IES-R high total + PCL-5 high total** — convergent PTSD
  signal; structured-interview workup (CAPS-5) at clinician-UI.
- **IES-R intrusion high + avoidance low** — "intrusion-
  dominant" profile.  Prolonged exposure therapy indication
  (Foa 2007 PE; Rauch 2009 massed PE protocol).
- **IES-R avoidance high + intrusion low** — "avoidance-
  dominant" profile.  Cognitive processing therapy indication
  (Resick 2017 CPT) with emphasis on stuck-points and trauma-
  related cognitions.
- **IES-R hyperarousal high + PSS-10 high** — physiological
  dysregulation.  Priority intervention: grounding / somatic-
  regulation (Linehan 1993 DBT TIP / paced breathing;
  van der Kolk 2014 somatic work).
- **IES-R high + AAQ-II high** — trauma-symptom-severity plus
  experiential avoidance.  Acceptance and Commitment Therapy
  indication (Hayes 2004 ACT; Walser 2007 ACT for PTSD).
- **IES-R high + ACEs ≥ 4** — trauma-symptom-severity plus
  complex-trauma history.  Consider complex-PTSD workup per
  ICD-11; phase-based trauma treatment per Cloitre 2011 /
  Herman 1992.
- **IES-R trajectory** — Jacobson & Truax 1991 RCI on IES-R
  total from Creamer 2003 α = 0.96 and SD ≈ 18 → RCI ≈ 10.
  A 10-point IES-R total delta is clinically meaningful across
  trauma-focused treatment episodes.

Instrument structure (Weiss & Marmar 1997):

**22 items, each on a 5-point Likert frequency scale (0-4)**:
    0 = Not at all
    1 = A little bit
    2 = Moderately
    3 = Quite a bit
    4 = Extremely

Timeframe: past 7 days, with reference to a specific traumatic
event identified at administration.

**ALL 22 items are positively worded** — higher response =
MORE symptom severity.  There are **NO reverse-keyed items** in
Weiss & Marmar 1997.

**Three-subscale partitioning** (Weiss & Marmar 1997 Table 1,
1-indexed administration order):

    Intrusion (8 items):     1, 2, 3, 6, 9, 14, 16, 20
    Avoidance (8 items):     5, 7, 8, 11, 12, 13, 17, 22
    Hyperarousal (6 items):  4, 10, 15, 18, 19, 21

Item 2 ("I had trouble staying asleep") classifies as
**intrusion** because Weiss & Marmar 1997 grouped nightmare-
driven sleep disturbance (Horowitz Criterion B4 recurrent
dreams) under intrusion, separately from physiological-
hyperarousal sleep disturbance.  Item 15 ("I had trouble
falling asleep") classifies as **hyperarousal** — general
physiological arousal impacting sleep onset, distinct from
nightmare-driven waking.  This distinction is load-bearing
and the scorer MUST preserve the Weiss & Marmar 1997
factor assignment, NOT the DSM-5 criterion mapping.

Verbatim IES-R item text (Weiss & Marmar 1997 administration
order):

    1.  Any reminder brought back feelings about it.
        [Intrusion]
    2.  I had trouble staying asleep.
        [Intrusion — nightmare-driven]
    3.  Other things kept making me think about it.
        [Intrusion]
    4.  I felt irritable and angry.
        [Hyperarousal]
    5.  I avoided letting myself get upset when I thought
        about it or was reminded of it.
        [Avoidance]
    6.  I thought about it when I didn't mean to.
        [Intrusion]
    7.  I felt as if it hadn't happened or wasn't real.
        [Avoidance — derealization-adjacent]
    8.  I stayed away from reminders of it.
        [Avoidance]
    9.  Pictures about it popped into my mind.
        [Intrusion]
    10. I was jumpy and easily startled.
        [Hyperarousal]
    11. I tried not to think about it.
        [Avoidance]
    12. I was aware that I still had a lot of feelings about
        it, but I didn't deal with them.
        [Avoidance — numbing]
    13. My feelings about it were kind of numb.
        [Avoidance — numbing]
    14. I found myself acting or feeling like I was back at
        that time.
        [Intrusion — flashback]
    15. I had trouble falling asleep.
        [Hyperarousal — sleep-onset]
    16. I had waves of strong feelings about it.
        [Intrusion]
    17. I tried to remove it from my memory.
        [Avoidance]
    18. I had trouble concentrating.
        [Hyperarousal]
    19. Reminders of it caused me to have physical reactions,
        such as sweating, trouble breathing, nausea, or a
        pounding heart.
        [Hyperarousal]
    20. I had dreams about it.
        [Intrusion]
    21. I felt watchful and on-guard.
        [Hyperarousal]
    22. I tried not to talk about it.
        [Avoidance]

Scoring:

- Apply NO reverse-keying (all items distress-positive).
- Subscale sums (Weiss & Marmar 1997):
    intrusion      = sum of 8 intrusion items    (range 0-32)
    avoidance      = sum of 8 avoidance items    (range 0-32)
    hyperarousal   = sum of 6 hyperarousal items  (range 0-24)
- Total (Creamer 2003) = sum of all 22 items (range 0-88)
  = intrusion + avoidance + hyperarousal.
- Positive screen: total ≥ 33 (Creamer 2003 ROC cutoff;
  AUC=0.88 against CAPS).

T3 posture:

No IES-R item probes suicidality.  Item 4 ("irritable and
angry"), item 10 ("jumpy and easily startled"), and item 21
("watchful and on-guard") are HYPERAROUSAL probes, NOT self-
harm or ideation probes.  Item 15 ("trouble falling asleep") is
a sleep-onset probe, NOT a hopelessness probe.  Active-risk
screening stays on C-SSRS / PHQ-9 item 9 / CORE-10 item 6.  A
high IES-R combined with high PHQ-9 surfaces at the clinician-
UI layer as a C-SSRS follow-up prompt, NOT as a scorer-layer
T3 flag.  Same renderer-versus-scorer-layer boundary
established for SWLS / MSPSS / UCLA-3 / GSE.

Design invariants preserved:

- **22-item exact count**.  Weiss & Marmar 1997 pinned the
  22-item structure.  The original IES (Horowitz 1979) is
  15-item and lacks the hyperarousal subscale; if shipped it
  warrants a separate scorer.
- **Administration order pinned**.  Weiss & Marmar 1997
  factor-analytic validation was conducted at the pinned order.
- **Subscale partition positions pinned**.  The item-to-
  subscale mapping is load-bearing; a client that re-ordered
  items per-subscale would still compute the correct total but
  misattribute subscale sums.  Item 2 → intrusion and item 15
  → hyperarousal distinction MUST NOT be "corrected" to DSM-5
  cluster mapping.
- **Strict 0-4 Likert range** at the scorer.  Weiss & Marmar
  1997 explicitly pinned the 0-4 response scale.
- **Bool rejection at the scorer.**  Platform-wide invariant
  per CLAUDE.md standing rule.

Citations:

- Weiss DS, Marmar CR (1997).  *The Impact of Event Scale—
  Revised.*  In JP Wilson & TM Keane (Eds.), Assessing
  Psychological Trauma and PTSD (pp. 399-411).  Guilford
  Press, New York.  (Canonical derivation; three-subscale
  factor structure; 22-item administration order.)
- Creamer M, Bell R, Failla S (2003).  *Psychometric
  properties of the Impact of Event Scale—Revised.*
  Behaviour Research and Therapy 41(12):1489-1496.  (n=386
  Vietnam veterans; α ≥ 0.87 per subscale; total α=0.96;
  ROC AUC=0.88; clinical cutoff ≥ 33 for probable PTSD.)
- Horowitz M, Wilner N, Alvarez W (1979).  *Impact of Event
  Scale: A measure of subjective stress.*  Psychosomatic
  Medicine 41(3):209-218.  (Original 15-item IES; basis for
  the IES-R extension; Horowitz 1986 stress-response-
  syndrome theory.)
- Beck JG, Grant DM, Read JP, Clapp JD, Coffey SF, Miller LM,
  Palyo SA (2008).  *The Impact of Event Scale—Revised:
  Psychometric properties in a sample of motor vehicle
  accident survivors.*  Journal of Anxiety Disorders
  22(2):187-198.  (Convergent validity with PCL-5; r≈0.80
  total-to-total; basis for IES-R × PCL-5 concurrent
  administration guidance.)
- Felitti VJ, Anda RF, Nordenberg D, Williamson DF, Spitz AM,
  Edwards V, Koss MP, Marks JS (1998).  *Relationship of
  childhood abuse and household dysfunction to many of the
  leading causes of death in adults: The Adverse Childhood
  Experiences (ACE) Study.*  American Journal of Preventive
  Medicine 14(4):245-258.  (n=17,337 Kaiser cohort; ACE ≥ 4
  → ~10× SUD risk; basis for IES-R + ACEs pairing rationale.)
- van der Kolk BA, Pelcovitz D, Roth S, Mandel FS, McFarlane
  A, Herman JL (1996).  *Dissociation, somatization, and
  affect dysregulation: The complexity of adaptation of
  trauma.*  American Journal of Psychiatry 153(7 Suppl):
  83-93.  (Trauma-addiction mediation pathway.)
- Najavits LM (2002).  *Seeking Safety: A Treatment Manual
  for PTSD and Substance Abuse.*  Guilford Press, New York.
  (Concurrent PTSD+SUD intervention framework; basis for
  IES-R in routine-outcome tracking.)
- Foa EB, Hembree EA, Rothbaum BO (2007).  *Prolonged
  Exposure Therapy for PTSD: Emotional Processing of
  Traumatic Experiences, Therapist Guide.*  Oxford
  University Press.  (Prolonged Exposure; IES-R intrusion-
  dominant indication.)
- Resick PA, Monson CM, Chard KM (2017).  *Cognitive
  Processing Therapy for PTSD: A Comprehensive Manual.*
  Guilford Press.  (CPT; IES-R avoidance-dominant
  indication.)
- Hayes SC, Luoma JB, Bond FW, Masuda A, Lillis J (2006).
  *Acceptance and Commitment Therapy: Model, processes and
  outcomes.*  Behaviour Research and Therapy 44(1):1-25.
  (ACT model; IES-R × AAQ-II pairing.)
- Jacobson NS, Truax P (1991).  *Clinical significance: A
  statistical approach to defining meaningful change in
  psychotherapy research.*  Journal of Consulting and
  Clinical Psychology 59(1):12-19.  (RCI methodology;
  IES-R RCI ≈ 10 from Creamer 2003 α=0.96 and SD ≈ 18.)
- Weathers FW, Litz BT, Keane TM, Palmieri PA, Marx BP,
  Schnurr PP (2013).  *The PTSD Checklist for DSM-5 (PCL-5).*
  National Center for PTSD.  (Companion DSM-5-aligned
  measure.)
- Prins A, Bovin MJ, Smolenski DJ, Marx BP, Kimerling R,
  Jenkins-Guarnieri MA, Kaloupek DG, Schnurr PP, Kaiser AP,
  Leyva YE, Tiet QQ (2016).  *The Primary Care PTSD Screen
  for DSM-5 (PC-PTSD-5): Development and evaluation within
  a veteran primary care sample.*  Journal of General
  Internal Medicine 31(10):1206-1211.  (First-pass PTSD
  screener companion.)
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

INSTRUMENT_VERSION = "iesr-1.0.0"
ITEM_COUNT = 22
ITEM_MIN, ITEM_MAX = 0, 4

# Weiss & Marmar 1997: all 22 items positively worded.  No reverse-
# keyed positions.  Pinned as empty tuple so a future change that
# adds reverse-keying would require updating this constant AND the
# module docstring, triggering clinical review.
IESR_REVERSE_ITEMS: tuple[int, ...] = ()

# Weiss & Marmar 1997 Table 1 subscale partitioning (1-indexed).
# Item 2 ("trouble staying asleep") classifies as INTRUSION
# (nightmare-driven) per Weiss & Marmar 1997; MUST NOT be
# re-assigned to hyperarousal based on DSM-5 cluster mapping.
IESR_INTRUSION_POSITIONS: tuple[int, ...] = (1, 2, 3, 6, 9, 14, 16, 20)
IESR_AVOIDANCE_POSITIONS: tuple[int, ...] = (5, 7, 8, 11, 12, 13, 17, 22)
IESR_HYPERAROUSAL_POSITIONS: tuple[int, ...] = (4, 10, 15, 18, 19, 21)

# Subscale label-key ordering.  Clinician-UI renderers key off this
# list so a single source-of-truth controls the dict-key order.
IESR_SUBSCALES: tuple[str, str, str] = (
    "intrusion",
    "avoidance",
    "hyperarousal",
)

# Creamer 2003 ROC cutoff against CAPS structured diagnostic
# interview.  AUC = 0.88 at total ≥ 33.  Widely cited; standard
# cutoff in routine-outcome and clinical-trial reporting.
IESR_CLINICAL_CUTOFF: int = 33


class InvalidResponseError(ValueError):
    """Raised on item-count, item-range, or item-type violations."""


Severity = Literal["continuous"]


@dataclass(frozen=True)
class IesrResult:
    """Typed IES-R output.

    Fields:
    - ``total``: 0-88 sum of all 22 items.  Higher = MORE trauma-
      symptom severity.  Uniform with PCL-5 / PHQ-9 / GAD-7 /
      CORE-10 "higher-is-more-distress" direction.
    - ``intrusion``: 0-32 sum of the 8 intrusion items (positions
      1, 2, 3, 6, 9, 14, 16, 20).  Weiss & Marmar 1997 Factor 1.
    - ``avoidance``: 0-32 sum of the 8 avoidance items (positions
      5, 7, 8, 11, 12, 13, 17, 22).  Weiss & Marmar 1997 Factor 2.
    - ``hyperarousal``: 0-24 sum of the 6 hyperarousal items
      (positions 4, 10, 15, 18, 19, 21).  Weiss & Marmar 1997
      Factor 3 (added to the original IES).
    - ``severity``: literal ``"continuous"`` sentinel.  Creamer
      2003 published a single clinical cutoff (≥ 33) and ROC
      characteristics, but no severity bands.  Envelope stays
      ``"continuous"`` per CLAUDE.md non-negotiable #9.
    - ``positive_screen``: True if total ≥ 33 (Creamer 2003
      cutoff).  Flagged in the UI as "probable PTSD — refer for
      CAPS-5 structured diagnostic interview".
    - ``cutoff_used``: the clinical cutoff applied (33).
      Surfaced for the UI ("positive at ≥ N" rendering).
    - ``items``: verbatim 22-tuple of raw 0-4 responses in Weiss
      & Marmar 1997 administration order (pre-partition).
      Preserved for audit invariance and FHIR R4 export.

    Deliberately-absent fields:
    - No ``requires_t3`` — no IES-R item probes suicidality.
      Hyperarousal items do not map to scorer-layer T3.  Acute-
      risk screening stays on C-SSRS / PHQ-9 item 9 / CORE-10
      item 6.
    - No ``triggering_items`` — no C-SSRS-style item-level
      acuity routing.
    - No ``index`` — the total IS the published score.
    - No ``scaled_score`` — no transformation applied.
    """

    total: int
    intrusion: int
    avoidance: int
    hyperarousal: int
    severity: Severity
    positive_screen: bool
    cutoff_used: int
    items: tuple[int, ...]
    instrument_version: str = INSTRUMENT_VERSION


def _validate_item(index_1: int, value: object) -> int:
    """Validate a single 0-4 Likert item."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidResponseError(
            f"IES-R item {index_1} must be int, got {value!r}"
        )
    if not (ITEM_MIN <= value <= ITEM_MAX):
        raise InvalidResponseError(
            f"IES-R item {index_1} must be in {ITEM_MIN}-{ITEM_MAX}, "
            f"got {value}"
        )
    return value


def _subscale_sum(
    items: tuple[int, ...], positions_1_indexed: tuple[int, ...]
) -> int:
    return sum(items[p - 1] for p in positions_1_indexed)


def score_iesr(raw_items: Sequence[int]) -> IesrResult:
    """Score an IES-R response set.

    Inputs:
    - ``raw_items``: 22 items, each 0-4 Likert (0 = Not at all,
      4 = Extremely), in Weiss & Marmar 1997 administration
      order.

    Raises :class:`InvalidResponseError` on:
    - Wrong number of items (must be exactly 22).
    - A non-int / bool item value.
    - An item outside ``[0, 4]``.

    Computes:
    - ``intrusion``: sum of positions 1, 2, 3, 6, 9, 14, 16, 20.
    - ``avoidance``: sum of positions 5, 7, 8, 11, 12, 13, 17, 22.
    - ``hyperarousal``: sum of positions 4, 10, 15, 18, 19, 21.
    - ``total``: sum of all 22 items (equals subscale sum).
    - ``severity``: always ``"continuous"``.
    - ``positive_screen``: True if total ≥ 33 (Creamer 2003).
    - ``items``: tuple of raw responses (identity under zero-
      reverse-keying).

    Platform-wide invariants preserved:
    - No reverse-keying (Weiss & Marmar 1997 all-distress-positive).
    - Subscale partition from Weiss & Marmar 1997 Factor 1/2/3
      (NOT re-mapped to DSM-5 clusters).
    - Creamer 2003 cutoff taken verbatim.
    - No T3 flag (no suicidality probe).
    """
    if len(raw_items) != ITEM_COUNT:
        raise InvalidResponseError(
            f"IES-R requires exactly {ITEM_COUNT} items, "
            f"got {len(raw_items)}"
        )
    items = tuple(
        _validate_item(index_1=i + 1, value=v)
        for i, v in enumerate(raw_items)
    )

    intrusion = _subscale_sum(items, IESR_INTRUSION_POSITIONS)
    avoidance = _subscale_sum(items, IESR_AVOIDANCE_POSITIONS)
    hyperarousal = _subscale_sum(items, IESR_HYPERAROUSAL_POSITIONS)
    total = intrusion + avoidance + hyperarousal

    positive_screen = total >= IESR_CLINICAL_CUTOFF

    return IesrResult(
        total=total,
        intrusion=intrusion,
        avoidance=avoidance,
        hyperarousal=hyperarousal,
        severity="continuous",
        positive_screen=positive_screen,
        cutoff_used=IESR_CLINICAL_CUTOFF,
        items=items,
    )


__all__ = [
    "IESR_AVOIDANCE_POSITIONS",
    "IESR_CLINICAL_CUTOFF",
    "IESR_HYPERAROUSAL_POSITIONS",
    "IESR_INTRUSION_POSITIONS",
    "IESR_REVERSE_ITEMS",
    "IESR_SUBSCALES",
    "INSTRUMENT_VERSION",
    "ITEM_COUNT",
    "ITEM_MAX",
    "ITEM_MIN",
    "IesrResult",
    "InvalidResponseError",
    "Severity",
    "score_iesr",
]

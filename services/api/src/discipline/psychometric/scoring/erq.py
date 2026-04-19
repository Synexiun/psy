"""ERQ — Emotion Regulation Questionnaire (Gross & John 2003).

The ERQ is a validated 10-item self-report measure of two distinct
**emotion regulation strategies** — how an individual typically alters
the trajectory of an emotional response.  Rooted in James Gross's
process model of emotion regulation (Gross 1998, 2002), the ERQ
differentiates an *antecedent-focused* strategy applied early in the
emotion-generative cycle (cognitive reappraisal) from a *response-
focused* strategy applied after the emotion is already active
(expressive suppression).  The distinction is not ornamental — it is
the central therapeutic finding of the emotion-regulation literature
over the past two decades:

- **Cognitive reappraisal** reliably predicts BETTER outcomes on every
  indicator studied — higher positive affect, lower depression, higher
  life satisfaction, better interpersonal functioning, better physical
  health (Gross & John 2003; Aldao, Nolen-Hoeksema & Schweizer 2010
  meta-analysis of 114 studies).
- **Expressive suppression** reliably predicts WORSE outcomes on the
  same indicators — lower positive affect, higher depression, poorer
  social relationships, worse cardiovascular profile, paradoxically
  HIGHER physiological arousal (the suppressed emotion doesn't
  disappear, it intensifies sympathetically; Gross 1998, Butler 2003).

The clinical question the ERQ answers is therefore not "does this
patient regulate their emotions?" (which DERS-16 answers) but
"WHICH strategy does this patient reach for when regulation is
attempted, regardless of whether it succeeds?"  A patient can score
low on DERS-16 (effectively regulated) while scoring high on
suppression (effectively regulated via a strategy that predicts
worse long-term outcomes) — a clinically critical profile that would
be invisible without ERQ.

Clinical relevance to the Discipline OS platform:
The platform now has a three-layer emotion-processing architecture
from the assessment instruments alone:

 1. **TAS-20** — upstream: can the patient IDENTIFY the emotion?
    (If DIF is high, downstream strategy choice is moot.)
 2. **ERQ** — midstream: WHICH strategy does the patient reach for?
    (Reappraisal vs suppression; independent of success.)
 3. **DERS-16** — downstream: can the patient EXECUTE regulation?
    (Capacity for the strategy once chosen.)

The intervention layer reads this three-layer profile when routing
to process-level interventions:

- High TAS-20 DIF → affect-labeling tools FIRST (mindfulness observe
  / describe skills) before either ERQ-informed strategy training or
  DERS-16-targeted capacity work.
- TAS-20 DIF OK, ERQ suppression >> reappraisal → cognitive
  reappraisal training (CBT restructuring variants, ACT defusion
  variants that convert a "content-swap" strategy into a "relational-
  swap" strategy) before skill-building.
- TAS-20 DIF OK, ERQ reappraisal already high, DERS-16 high →
  capacity-building / distress-tolerance work (DBT skills) — the
  patient knows the right strategy but the emotional load has
  overwhelmed execution capacity.

The ERQ also pairs with:

- **PHQ-9 / GAD-7**: high suppression independently predicts slower
  response to standard CBT for depression / anxiety; a patient with
  ERQ suppression elevated is a candidate for reappraisal-first
  sequencing (vs the default CBT protocol which assumes the patient
  will try restructuring homework willingly).
- **AAQ-II**: ERQ suppression and AAQ-II experiential avoidance
  correlate substantially but are not identical — suppression is
  ONE form of avoidance (of the outward expression), while AAQ-II
  captures avoidance of the internal experience itself.  Two scales,
  two constructs; both worth measuring.
- **PSS-10**: high perceived stress × ERQ suppression signals
  chronic sympathetic load (the suppressed stress response doesn't
  abate, it accumulates); this subgroup benefits from reappraisal
  work plus autonomic-regulation tools (HRV biofeedback variants).
- **Relapse-prevention framing**: in substance-use / compulsive-
  behavior populations, suppression predicts relapse more strongly
  than reappraisal protects (Bonn-Miller 2011, Hofmann 2012) — the
  inability to actively reappraise is less clinically dangerous than
  the active use of suppression, which paradoxically amplifies the
  state the patient is trying to manage.  The platform reads
  elevated suppression as a preemptive relapse-risk signal.

Instrument structure (Gross & John 2003):

**10 items, each on a 7-point Likert scale** scored:
    1 = strongly disagree
    2 = disagree
    3 = slightly disagree
    4 = neutral
    5 = slightly agree
    6 = agree
    7 = strongly agree

**Two subscales** per Gross & John 2003 Study 1 CFA:

- **Reappraisal** (6 items: 1, 3, 5, 7, 8, 10)
    1. "When I want to feel more positive emotion (such as joy or
        amusement), I change what I'm thinking about."
    3. "When I want to feel less negative emotion (such as sadness
        or anger), I change what I'm thinking about."
    5. "When I'm faced with a stressful situation, I make myself
        think about it in a way that helps me stay calm."
    7. "When I want to feel more positive emotion, I change the way
        I'm thinking about the situation."
    8. "I control my emotions by changing the way I think about the
        situation I'm in."
   10. "When I want to feel less negative emotion, I change the way
        I'm thinking about the situation."

- **Suppression** (4 items: 2, 4, 6, 9)
    2. "I keep my emotions to myself."
    4. "When I am feeling positive emotions, I am careful not to
        express them."
    6. "I control my emotions by not expressing them."
    9. "When I am feeling negative emotions, I make sure not to
        express them."

**No reverse scoring.**  Every item is worded in the
strategy-endorsement direction; higher Likert = stronger endorsement
of the strategy named by the subscale.  This is a distinguishing
feature versus TAS-20 (5 reverse items), LOT-R (3 reverse items),
and PSWQ (5 reverse items): the ERQ authors deliberately worded all
10 items in the construct-endorsement direction to keep the two
subscale scores directly interpretable.

**No published severity bands.**  Gross & John 2003 report the
instrument as a dispositional continuous measure — higher/lower
reappraisal and higher/lower suppression scores, with group
comparisons (e.g., clinical vs control) done on the raw continuous
scores rather than against a cutoff.  Subsequent validation
(Gross 2007 review, Melka 2011 factor-structure confirmation) has
NOT introduced severity bands.  The router therefore emits
``severity=None`` (continuous-sentinel) and ``cutoff_used=None`` —
the clinical signal is the subscale profile, not a categorical
classification.

**Scoring convention**: Gross & John 2003 report MEAN subscale
scores (sum / n_items) to keep the two subscales on the same 1-7
metric; much subsequent work reports sums.  The ``Tas20Result``
pattern in this codebase uses SUMS for wire consistency with the
other subscale-bearing instruments (DERS-16, TAS-20) and to keep
all subscale fields integer-typed (no floating-point in the audit
trail).  Reported sums are:

    reappraisal: 6 items × 1-7 Likert = sum in [6, 42]
    suppression: 4 items × 1-7 Likert = sum in [4, 28]
    total:       10 items × 1-7 Likert = sum in [10, 70]

The clinical interpretation reads the subscale pair (reappraisal,
suppression) as a 2-tuple, not the sum.  A patient with
(reappraisal=30, suppression=10) has a strongly-reappraising
profile; a patient with (reappraisal=30, suppression=25) has a
mixed profile using both strategies; a patient with (reappraisal=
15, suppression=25) has a suppression-dominant profile (clinically
the highest-concern pattern in most samples studied).  The router's
``subscales`` envelope ships both values so downstream can reason
over the 2-tuple.

Safety routing:
- ERQ has NO safety item.  It does not screen for suicidality,
  self-harm, or acute risk — asking whether a patient typically
  reappraises or suppresses does not elicit imminent-harm signal.
- Safety routing stays with C-SSRS, PHQ-9 item 9, PCL-5, OCIR (and
  associated triggering-items response pattern).  ``requires_t3``
  is hard-coded ``False`` at the router.

References:
- Gross JJ, John OP (2003).  *Individual differences in two emotion
  regulation processes: Implications for affect, relationships, and
  well-being.*  Journal of Personality and Social Psychology
  85(2):348-362.  (Primary validation — Study 1: item selection +
  CFA; Study 2: convergent validity with Big Five; Study 3:
  discriminant validity + interpersonal consequences; Study 4:
  affective consequences; Study 5: physical-health consequences.)
- Gross JJ (1998).  *The emerging field of emotion regulation: An
  integrative review.*  Review of General Psychology 2(3):271-299.
  (Process model: antecedent-focused vs response-focused
  strategies — the theoretical spine the ERQ operationalizes.)
- Gross JJ (2002).  *Emotion regulation: Affective, cognitive, and
  social consequences.*  Psychophysiology 39(3):281-291.
  (Extends the process model with the empirical cost of
  suppression — sympathetic arousal is HIGHER under suppression
  than under free expression.)
- Butler EA, Egloff B, Wilhelm FH, Smith NC, Erickson EA,
  Gross JJ (2003).  *The social consequences of expressive
  suppression.*  Emotion 3(1):48-67.  (Interpersonal cost of
  suppression — partners of suppressors rate them as less
  affiliative and less authentic.)
- Aldao A, Nolen-Hoeksema S, Schweizer S (2010).  *Emotion-
  regulation strategies across psychopathology: A meta-analytic
  review.*  Clinical Psychology Review 30(2):217-237.  (Meta-
  analysis of 114 studies — reappraisal protective, suppression
  risk-elevating, across depression / anxiety / eating / substance
  use.)
- Hofmann SG, Heering S, Sawyer AT, Asnaani A (2009).  *How to
  handle anxiety: The effects of reappraisal, acceptance, and
  suppression strategies on anxious arousal.*  Behaviour Research
  and Therapy 47(5):389-394.  (Reappraisal and acceptance
  dampen anxiety; suppression amplifies it — the direct
  experimental contrast.)
- Bonn-Miller MO, Vujanovic AA, Boden MT, Gross JJ (2011).
  *Posttraumatic stress, difficulties in emotion regulation, and
  coping-oriented marijuana use.*  Cognitive Behaviour Therapy
  40(1):34-44.  (Suppression-relapse link in substance-use
  populations.)
- Melka SE, Lancaster SL, Bryant AR, Rodriguez BF (2011).
  *Confirmatory factor and measurement invariance analyses of the
  Emotion Regulation Questionnaire.*  Journal of Clinical
  Psychology 67(12):1283-1293.  (Two-factor structure confirmation
  across clinical and nonclinical samples; factorial invariance
  across gender.)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

INSTRUMENT_VERSION = "erq-1.0.0"
ITEM_COUNT = 10
ITEM_MIN = 1
ITEM_MAX = 7

# Gross & John 2003 Study 1 CFA — 1-indexed item positions per
# subscale.  A refactor that reordered items or rotated subscale
# rows would silently miscategorize the clinical signal; every
# subscale test pins its item mapping independently.  All 10 items
# are worded in the strategy-endorsement direction (no reverse
# items) so subscale sums operate on raw values directly.
ERQ_SUBSCALES: dict[str, tuple[int, ...]] = {
    "reappraisal": (1, 3, 5, 7, 8, 10),
    "suppression": (2, 4, 6, 9),
}


class InvalidResponseError(ValueError):
    """Raised on item-count, item-range, or item-type violations."""


@dataclass(frozen=True)
class ErqResult:
    """Typed ERQ output.

    Fields:
    - ``total``: 10-70, the straight sum of the 10 Likert items.
      Minimum 10 because every item's lowest response value is 1
      ("strongly disagree"), not 0 — uniform with DERS-16 / K10 /
      K6 / AAQ-II / TAS-20 floor semantics.  The total is primarily
      an audit-trail convenience; clinical reads should go through
      the subscale pair, not the aggregate.
    - ``subscale_reappraisal`` / ``subscale_suppression``: the two
      subscale sums per Gross & John 2003 CFA assignments.
      Reappraisal 6-42 (6 items × 1-7); Suppression 4-28 (4 items
      × 1-7).  Surfaced on the router's AssessmentResult envelope
      via the ``subscales`` map (wire keys: ``reappraisal`` /
      ``suppression``).
    - ``items``: verbatim 10-tuple input, pinned for auditability.

    Deliberately-absent fields:
    - No ``severity`` field — Gross & John 2003 published no bands;
      ERQ is a continuous dimensional measure.  The router envelope
      emits ``severity=None`` (continuous-sentinel) — uniform with
      DERS-16 / Craving VAS / PACS / K6 / PSWQ / SDS / BRS.
    - No ``cutoff_used`` / ``positive_screen`` — continuous
      instrument, no cutoff shape.
    - No ``requires_t3`` field — ERQ has no safety item.
    """

    total: int
    subscale_reappraisal: int
    subscale_suppression: int
    items: tuple[int, ...]
    instrument_version: str = INSTRUMENT_VERSION


def _validate_item(index_1: int, value: object) -> int:
    """Validate a single 1-7 Likert item and return the int value.

    ``index_1`` is the 1-indexed item number (1-10) so error
    messages name the item a clinician would recognize from the
    ERQ document.
    """
    # Bool rejection — uniform with the rest of the psychometric package.
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidResponseError(
            f"ERQ item {index_1} must be int, got {value!r}"
        )
    if value < ITEM_MIN or value > ITEM_MAX:
        raise InvalidResponseError(
            f"ERQ item {index_1} out of range "
            f"[{ITEM_MIN}, {ITEM_MAX}]: {value}"
        )
    return value


def _subscale_sum(items: tuple[int, ...], subscale_name: str) -> int:
    """Sum the items belonging to a named subscale.

    ERQ_SUBSCALES holds 1-indexed positions; convert to 0-indexed
    array access here.  A refactor that shifted the subscale index
    tuples would break the clinical signal silently — every
    subscale test pins its item mapping independently.  No reverse-
    keying flip is needed because all 10 items are direction-aligned
    with their subscale's construct.
    """
    positions_1 = ERQ_SUBSCALES[subscale_name]
    return sum(items[pos - 1] for pos in positions_1)


def score_erq(raw_items: Sequence[int]) -> ErqResult:
    """Score an ERQ response set.

    Inputs:
    - ``raw_items``: 10 items, each 1-7 Likert (1 = "strongly
      disagree", 7 = "strongly agree").  No reverse-keying —
      every item is endorsement-direction for its subscale.

    Raises :class:`InvalidResponseError` on:
    - Wrong number of items (must be exactly 10).
    - A non-int / bool item value.
    - An item outside ``[1, 7]``.

    Computes:
    - Total (10-70).
    - Reappraisal subscale sum (6-42).
    - Suppression subscale sum (4-28).

    No severity band is emitted — see module docstring.
    """
    if len(raw_items) != ITEM_COUNT:
        raise InvalidResponseError(
            f"ERQ requires exactly {ITEM_COUNT} items, got {len(raw_items)}"
        )
    items = tuple(
        _validate_item(index_1=i + 1, value=v)
        for i, v in enumerate(raw_items)
    )
    total = sum(items)

    return ErqResult(
        total=total,
        subscale_reappraisal=_subscale_sum(items, "reappraisal"),
        subscale_suppression=_subscale_sum(items, "suppression"),
        items=items,
    )


__all__ = [
    "ERQ_SUBSCALES",
    "ErqResult",
    "INSTRUMENT_VERSION",
    "InvalidResponseError",
    "ITEM_COUNT",
    "ITEM_MAX",
    "ITEM_MIN",
    "score_erq",
]

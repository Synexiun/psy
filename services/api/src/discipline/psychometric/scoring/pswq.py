"""PSWQ — Penn State Worry Questionnaire (Meyer, Miller, Metzger & Borkovec 1990).

PSWQ is the gold-standard self-report measure of **trait-level worry** —
the dispositional tendency to engage in excessive, uncontrollable,
negative-valence future-oriented cognitive activity.  It is the CBT-
for-GAD process-target instrument: GAD-7 measures anxiety *symptoms*
over a two-week window (state-level severity), PSWQ measures the
dispositional worry *process* that cognitive therapy for GAD explicitly
targets.  A patient can have low GAD-7 (well-controlled symptoms) and
high PSWQ (persistent worry trait still present), or vice versa; the
two instruments answer different clinical questions and the trajectory
layer reads them as orthogonal axes.

Clinical relevance to the Discipline OS platform:
Worry is the cognitive substrate of many compulsive behaviors the
platform intervenes on — hypervigilant checking, reassurance-seeking,
pre-emptive substance use to quiet rumination, catastrophization-
driven avoidance.  PSWQ surfaces whether a patient's compulsive cycle
is worry-driven (CBT-for-GAD tool variants: worry-postponement,
decatastrophizing, uncertainty-acceptance exposures) versus
affect-regulation-driven (DBT distress-tolerance tools per DERS-16)
versus experiential-avoidance-driven (ACT defusion per AAQ-II).
Together with GAD-7 (state anxiety), AAQ-II (psychological
inflexibility), DERS-16 (emotion dysregulation), PCL-5 (trauma-driven
hyperarousal), and OCI-R (compulsive subtype), PSWQ gives the
intervention-selection layer a cognitive-process axis distinct from
symptom / regulation / inflexibility / trauma dimensions.

Instrument structure (Meyer 1990):

**16 items, each on a 1-5 Likert scale** scored:
    1 = not at all typical of me
    2 = rarely typical of me
    3 = somewhat typical of me
    4 = often typical of me
    5 = very typical of me

Critically, **5 items are reverse-keyed** (items 1, 3, 8, 10, 11):
these items are worded in the worry-ABSENT direction (e.g., "If I do
not have enough time to do everything, I do not worry about it" —
item 1).  A high raw Likert on a reverse-keyed item reflects LOW
trait-worry; a low raw Likert reflects HIGH trait-worry.  Before
summing, reverse-keyed items must be flipped with the arithmetic
reflection ``flipped = (ITEM_MIN + ITEM_MAX) - raw`` = ``6 - raw``,
so on the same post-flip scale every item contributes in the same
direction: higher = more worry.

**First reverse-keying pattern in the package.**  Earlier instruments
(PHQ-9, GAD-7, DERS-16, AAQ-II, WSAS, etc.) were uniformly worded in
the target-construct direction.  PSWQ is the first to use mixed-
direction items, which Meyer 1990 adopted deliberately to reduce
response-set bias (all-positive-worded scales pick up on acquiescence;
mixed-direction forces item-level reading).  Future reverse-keyed
instruments (LOT-R, SCS-SF, Rosenberg, ERQ, MAAS, TAS-20) will reuse
the ``REVERSE_ITEMS`` frozen-tuple + arithmetic-reflection idiom
established here.

The 16 items (verbatim from Meyer 1990 Appendix):

 1. If I do not have enough time to do everything, I do not worry
    about it.  **[REVERSE]**
 2. My worries overwhelm me.
 3. I do not tend to worry about things.  **[REVERSE]**
 4. Many situations make me worry.
 5. I know I should not worry about things, but I just cannot help it.
 6. When I am under pressure I worry a lot.
 7. I am always worrying about something.
 8. I find it easy to dismiss worrisome thoughts.  **[REVERSE]**
 9. As soon as I finish one task, I start to worry about everything
    else I have to do.
10. I never worry about anything.  **[REVERSE]**
11. When there is nothing more I can do about a concern, I do not
    worry about it any more.  **[REVERSE]**
12. I have been a worrier all my life.
13. I notice that I have been worrying about things.
14. Once I start worrying, I cannot stop.
15. I worry all the time.
16. I worry about projects until they are all done.

Range: 16-80 (post-flip sum; minimum is every item at 1 post-flip,
maximum is every item at 5 post-flip).

**Higher is worse.**  Uniform with PHQ-9 / GAD-7 / DERS-16 / PCL-5 /
OCI-R / K10 / WSAS — opposite of WHO-5 / DTCQ-8 / Readiness Ruler /
CD-RISC-10.  Clients rendering PSWQ scores reuse the higher-is-worse
visual language from the anxiety-cluster instruments (a falling PSWQ
is an IMPROVEMENT).

Severity bands — deliberately absent:
Meyer 1990 published general-population and GAD-sample means (GAD
patients ~67, general adults ~48, normal controls ~42 per follow-up
studies) but did NOT publish banded clinical thresholds.  Downstream
papers proposed cuts:

- Behar 2003 suggested 45/62 (low/moderate/high worry) tertiles in a
  student sample.
- Startup & Erickson 2006 proposed ≥ 56 as a GAD-diagnostic cut in a
  treatment-seeking sample.
- Fresco 2003 replicated mid-50s as a rough GAD-threshold.

These cuts are **sample-specific and not cross-calibrated** against a
shared gold-standard clinical criterion.  Per CLAUDE.md's "don't
hand-roll severity thresholds" rule, PSWQ ships as a **continuous
dimensional measure** uniform with Craving VAS / PACS / DERS-16 /
CD-RISC-10.  The router envelope emits ``severity="continuous"`` as
the sentinel; the trajectory layer extracts the clinical signal via
RCI-style change detection (Jacobson & Truax 1991) rather than banded
classification.  The clinician UI may surface a "above GAD-sample
mean" context flag (score ≥ 60) as contextual information — that flag
is NOT a classification and NOT a gate.

Envelope choice:
Continuous-total shape uniform with PACS / Craving VAS / DERS-16 /
CD-RISC-10.  ``cutoff_used`` / ``positive_screen`` are NOT set.  No
``subscales`` dict — Meyer 1990 validated the unidimensional factor
structure, and Brown 1992's confirmatory analyses sustained that
single-factor solution (though some downstream papers have proposed
two-factor splits in specific populations, those are not considered
the canonical scoring shape).

Safety routing:
PSWQ has **no direct safety item**.  The 16 items probe the worry-
process construct only (intensity, persistence, uncontrollability,
chronicity); none probe suicidality, self-harm, intent, or crisis
behavior.  ``requires_t3`` is never set — acute ideation screening is
PHQ-9 item 9 / C-SSRS, not PSWQ.  Clinical posture: a high PSWQ is a
strong signal for CBT-for-GAD tool variants but is not itself a crisis
gate.

Bool rejection note:
Uniform with the rest of the psychometric package — bool items are
rejected at the validator.  See mdq.py, pcptsd5.py, isi.py, pcl5.py,
ocir.py, bis11.py, phq2.py, gad2.py, oasis.py, k10.py, sds.py, k6.py,
dudit.py, asrs6.py, aaq2.py, wsas.py, ders16.py, cdrisc10.py for the
shared rationale.

References:
- Meyer TJ, Miller ML, Metzger RL, Borkovec TD (1990).  *Development
  and validation of the Penn State Worry Questionnaire.*  Behaviour
  Research and Therapy 28(6):487-495.
- Brown TA, Antony MM, Barlow DH (1992).  *Psychometric properties of
  the Penn State Worry Questionnaire in a clinical anxiety disorders
  sample.*  Behaviour Research and Therapy 30(1):33-37.
- Behar E, Alcaine O, Zuellig AR, Borkovec TD (2003).  *Screening for
  generalized anxiety disorder using the Penn State Worry
  Questionnaire: A receiver operating characteristic analysis.*
  Journal of Behavior Therapy and Experimental Psychiatry 34(1):25-43.
- Startup HM, Erickson TM (2006).  *The Penn State Worry Questionnaire
  (PSWQ).*  In: Davey & Wells (eds.), *Worry and its Psychological
  Disorders*, Wiley.
- Fresco DM, Mennin DS, Heimberg RG, Turk CL (2003).  *Using the Penn
  State Worry Questionnaire to identify individuals with generalized
  anxiety disorder: A receiver operating characteristic analysis.*
  Journal of Behavior Therapy and Experimental Psychiatry 34(3-4):283-291.
- Jacobson NS, Truax P (1991).  *Clinical significance: A statistical
  approach to defining meaningful change in psychotherapy research.*
  Journal of Consulting and Clinical Psychology 59(1):12-19.  (RCI
  framing for continuous-instrument trajectory analysis on the
  platform.)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

INSTRUMENT_VERSION = "pswq-1.0.0"
ITEM_COUNT = 16
ITEM_MIN = 1
ITEM_MAX = 5

# Reverse-keyed item positions (1-indexed) per Meyer 1990.  These
# items are worded in the worry-ABSENT direction; a high raw Likert
# reflects LOW trait-worry and must be flipped to the standard
# higher-is-more-worry direction before summing.  Encoded as a
# frozen tuple so equality checks are hash-stable and the scorer
# cannot mutate the reverse set at runtime.
PSWQ_REVERSE_ITEMS: tuple[int, ...] = (1, 3, 8, 10, 11)


class InvalidResponseError(ValueError):
    """Raised on item-count, item-range, or item-type violations."""


@dataclass(frozen=True)
class PswqResult:
    """Typed PSWQ output.

    Fields:
    - ``total``: 16-80, the post-flip sum of the 16 Likert items.
      Higher is worse (more trait-worry) — same directionality as
      PHQ-9 / GAD-7 / DERS-16 / PCL-5 / OCI-R / K10 / WSAS, opposite
      of WHO-5 / DTCQ-8 / Readiness Ruler / CD-RISC-10.  Minimum is
      16 (every post-flip item at 1), not 0 — same floor semantic as
      DERS-16's 1-5 envelope.
    - ``items``: verbatim input tuple, pinned for auditability.  These
      are the RAW user responses BEFORE the reverse-flip is applied,
      so the audit trail preserves exactly what the patient ticked.
      The post-flip values used for the total are an internal detail
      of ``score_pswq`` and are not surfaced.

    Deliberately-absent fields:
    - No ``severity`` field — Meyer 1990 published no cross-
      calibrated banded thresholds; downstream cuts (Behar 2003 /
      Startup & Erickson 2006 / Fresco 2003) are sample-specific.
      The router envelope emits ``severity="continuous"`` as a
      sentinel (uniform with DERS-16 / CD-RISC-10 / Craving VAS /
      PACS).
    - No ``cutoff_used`` / ``positive_screen`` — continuous
      instrument, no cutoff shape.
    - No ``requires_t3`` field — PSWQ has no safety item.
    - No ``subscales`` — Meyer 1990 / Brown 1992 CFA validates
      unidimensional structure.
    """

    total: int
    items: tuple[int, ...]
    instrument_version: str = INSTRUMENT_VERSION


def _validate_item(index_1: int, value: object) -> int:
    """Validate a single 1-5 Likert item and return the int value.

    ``index_1`` is the 1-indexed item number (1-16) so error messages
    name the item a clinician would recognize from the PSWQ document.
    """
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidResponseError(
            f"PSWQ item {index_1} must be int, got {value!r}"
        )
    if value < ITEM_MIN or value > ITEM_MAX:
        raise InvalidResponseError(
            f"PSWQ item {index_1} out of range "
            f"[{ITEM_MIN}, {ITEM_MAX}]: {value}"
        )
    return value


def _flip_if_reverse(index_1: int, value: int) -> int:
    """Apply the reverse-keying flip to item ``index_1``'s value.

    For reverse-keyed items (1, 3, 8, 10, 11 per Meyer 1990), the
    raw response is flipped via arithmetic reflection so the post-
    flip value contributes to the total in the same direction as
    the other items.  On a 1-5 Likert, ``flipped = 6 - raw``:
        raw 1 → 5, raw 2 → 4, raw 3 → 3, raw 4 → 2, raw 5 → 1.

    Non-reverse-keyed items pass through unchanged.  This helper is
    the single point of truth for the reverse-keying logic; future
    reverse-keyed instruments can reuse the pattern by passing a
    different reverse-set and Likert range.
    """
    if index_1 in PSWQ_REVERSE_ITEMS:
        return (ITEM_MIN + ITEM_MAX) - value
    return value


def score_pswq(raw_items: Sequence[int]) -> PswqResult:
    """Score a PSWQ response set.

    Inputs:
    - ``raw_items``: 16 items, each 1-5 Likert (1 = "not at all
      typical of me", 5 = "very typical of me").  Raw responses are
      taken AS-IS from the patient; the reverse-keying flip for items
      1, 3, 8, 10, 11 is applied internally before summing — callers
      should NOT pre-flip the raw values.

    Raises :class:`InvalidResponseError` on:
    - Wrong number of items.
    - A non-int / bool item value.
    - An item outside ``[1, 5]``.

    Computes:
    - Post-flip sum (16-80) — higher is worse (more trait-worry).
      The ``items`` field of the result preserves the raw pre-flip
      tuple for auditability.

    No severity band is emitted — see module docstring.
    """
    if len(raw_items) != ITEM_COUNT:
        raise InvalidResponseError(
            f"PSWQ requires exactly {ITEM_COUNT} items, got {len(raw_items)}"
        )
    raw_validated = tuple(
        _validate_item(index_1=i + 1, value=v)
        for i, v in enumerate(raw_items)
    )
    total = sum(
        _flip_if_reverse(index_1=i + 1, value=v)
        for i, v in enumerate(raw_validated)
    )

    return PswqResult(
        total=total,
        items=raw_validated,
    )


__all__ = [
    "INSTRUMENT_VERSION",
    "InvalidResponseError",
    "ITEM_COUNT",
    "ITEM_MAX",
    "ITEM_MIN",
    "PSWQ_REVERSE_ITEMS",
    "PswqResult",
    "score_pswq",
]

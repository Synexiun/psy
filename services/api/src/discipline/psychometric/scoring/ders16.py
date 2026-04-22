"""DERS-16 — Difficulties in Emotion Regulation Scale, 16-item
short form (Bjureberg, Ljótsson, Tull, Hedman, Sahlin, Lundh,
Bjärehed, DiLillo, Messman-Moore, Gumpert, Gratz 2016).

DERS-16 is the validated short form of the original 36-item DERS
(Gratz & Roemer 2004).  It measures **emotion dysregulation** —
the Dialectical Behavior Therapy (DBT) target construct — across
five confirmatory-factor-validated subscales.  Where AAQ-II
measures psychological inflexibility (the ACT target construct)
and PHQ-9 / GAD-7 measure CBT-aligned symptom severity, DERS-16
measures the regulatory-process dimension that DBT interventions
(distress-tolerance, emotion regulation skills, wise-mind)
directly address.

Clinical relevance to the Discipline OS platform:
The platform's intervention layer ships DBT-variant tool
variants (distress-tolerance, radical acceptance, wise-mind,
emotion-surf skills) alongside ACT-variant and CBT-variant
tools.  Until now the assessment layer had no target-construct
measurement for the DBT pillar — the contextual bandit could
read the ACT target (AAQ-II), CBT-aligned symptom severity
(PHQ-9 / GAD-7), and functional outcome (WSAS) but not the DBT
target.  DERS-16 closes that gap.  Together with AAQ-II and
PHQ-9 / GAD-7, DERS-16 completes the **three-way process-target
triangle** so the bandit can route process-level decisions to
the therapeutic frame whose target construct the patient's
profile loads most heavily on — rather than defaulting to CBT
because CBT is the instrument default.

Pairing with existing instruments:
DERS-16 is **process-level orthogonal** to the symptom-severity
instruments (PHQ-9 / GAD-7 / K10 / PCL-5) and **process-level
adjacent** to AAQ-II:

- AAQ-II measures the **relationship** to internal experience
  (experiential avoidance, cognitive fusion).
- DERS-16 measures the **regulatory capacity** for internal
  experience (awareness, acceptance, impulse control,
  strategy access, clarity).

The overlap is substantial — both load on a broader "emotional
processing difficulty" factor — but DERS-16's subscale structure
surfaces clinically actionable differentiation: a patient
high on Impulse but low on Clarity differs clinically from one
high on Clarity but low on Strategies, and the DBT skills
curriculum has distinct modules for each.  The intervention
layer reads the 5-tuple profile (not just the aggregate total)
to pick skill-building tool variants matched to the weakest
regulatory capacity.

Instrument structure (Bjureberg 2016):

**16 items, each on a 1-5 Likert scale** scored:
    1 = Almost never (0-10%)
    2 = Sometimes (11-35%)
    3 = About half the time (36-65%)
    4 = Most of the time (66-90%)
    5 = Almost always (91-100%)

All items are worded in the **dysregulation direction** — higher
Likert = more emotion dysregulation.  Bjureberg 2016 pruned the
6 awareness-subscale items from the original DERS-36; those
awareness items required reverse-keying, and dropping them means
DERS-16 has **no reverse-keyed items** (uniform with PHQ-9 /
GAD-7 / K10 / etc., and unlike WHO-5 / DTCQ-8 / Readiness Ruler
which are higher-is-better).

The 16 items and subscale assignments (Bjureberg 2016 Table 2):

 1. I have difficulty making sense out of my feelings. (Clarity)
 2. I am confused about how I feel. (Clarity)
 3. When I'm upset, I have difficulty getting work done. (Goals)
 4. When I'm upset, I become out of control. (Impulse)
 5. When I'm upset, I believe that I will remain that way for a
    long time. (Strategies)
 6. When I'm upset, I believe that I'll end up feeling very
    depressed. (Strategies)
 7. When I'm upset, I have difficulty focusing on other things.
    (Goals)
 8. When I'm upset, I feel out of control. (Impulse)
 9. When I'm upset, I feel ashamed with myself for feeling that
    way. (Nonacceptance)
10. When I'm upset, I feel like I am weak. (Nonacceptance)
11. When I'm upset, I have difficulty controlling my behaviors.
    (Impulse)
12. When I'm upset, I believe that there is nothing I can do to
    make myself feel better. (Strategies)
13. When I'm upset, I become irritated with myself for feeling
    that way. (Nonacceptance)
14. When I'm upset, I start to feel very bad about myself.
    (Strategies)
15. When I'm upset, I have difficulty thinking about anything
    else. (Goals)
16. When I'm upset, my emotions feel overwhelming. (Strategies)

Subscale item counts (Bjureberg 2016):
- Nonacceptance: 3 items (9, 10, 13) — subscale range 3-15
- Goals: 3 items (3, 7, 15) — subscale range 3-15
- Impulse: 3 items (4, 8, 11) — subscale range 3-15
- Strategies: 5 items (5, 6, 12, 14, 16) — subscale range 5-25
- Clarity: 2 items (1, 2) — subscale range 2-10

Total sums to 16 items.  ``DERS16_SUBSCALES`` encodes the
1-indexed item positions per subscale; a refactor that reordered
items or flattened the subscale structure must update this
constant or the subscale outputs will silently miscategorize.

Range: total 16-80.

Severity bands — deliberately absent:
Bjureberg 2016 did NOT publish banded severity thresholds.  The
paper reports convergent / discriminant validity and CFA fit but
proposes no "mild / moderate / severe" cutpoints.  Downstream
literature (Fowler 2014 PTSD samples, Hallion 2018 mixed-anxiety
samples) proposes cutoffs, but these are not cross-calibrated
against a shared clinical criterion and vary by sample.  Per
CLAUDE.md's "don't hand-roll severity thresholds" rule, DERS-16
ships as a **continuous dimensional measure** with the subscale
dict exposed for clinician-UI use.  The router envelope emits
``severity="continuous"`` as a sentinel (uniform with Craving VAS
/ PACS).  The trajectory layer extracts the clinical signal via
RCI-style change detection (Jacobson & Truax 1991) rather than
banded classification.

Envelope choice:
Continuous-total shape uniform with PACS / Craving VAS.
``cutoff_used`` / ``positive_screen`` are NOT set.  ``subscales``
is populated with the 5-key Bjureberg 2016 dict; the router
surfaces these on the unified AssessmentResult envelope.

Safety routing:
DERS-16 has **no direct safety item**.  The 16 items probe
regulatory-process difficulty; item 4 (out of control) and
item 8 (out of control) probe impulse-control loss but not
suicidality or self-harm intent.  Item 14 (feel very bad about
myself) probes self-critical affect but not suicidality.
``requires_t3`` is never set — acute ideation screening is
PHQ-9 item 9 / C-SSRS, not DERS-16.  Same posture as the rest
of the no-safety-item instrument set.  Clinical posture: a
high DERS-16 total / Impulse subscale is a strong signal for
DBT-variant intervention tools but is not itself a crisis gate.

Bool rejection note:
Uniform with the rest of the psychometric package — bool items
are rejected at the validator.  See mdq.py, pcptsd5.py, isi.py,
pcl5.py, ocir.py, bis11.py, phq2.py, gad2.py, oasis.py, k10.py,
sds.py, k6.py, dudit.py, asrs6.py, aaq2.py, wsas.py for the
shared rationale.

References:
- Bjureberg J, Ljótsson B, Tull MT, Hedman E, Sahlin H, Lundh LG,
  Bjärehed J, DiLillo D, Messman-Moore T, Gumpert CH, Gratz KL
  (2016).  *Development and Validation of a Brief Version of the
  Difficulties in Emotion Regulation Scale: The DERS-16.*
  Journal of Psychopathology and Behavioral Assessment
  38(2):284-296.
- Gratz KL, Roemer L (2004).  *Multidimensional assessment of
  emotion regulation and dysregulation: Development, factor
  structure, and initial validation of the Difficulties in
  Emotion Regulation Scale.*  Journal of Psychopathology and
  Behavioral Assessment 26(1):41-54.
- Linehan MM (1993).  *Cognitive-behavioral treatment of
  borderline personality disorder.*  New York: Guilford Press.
  (DBT target-construct framing for the emotion-dysregulation
  transdiagnostic model.)
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

INSTRUMENT_VERSION = "ders16-1.0.0"
ITEM_COUNT = 16
ITEM_MIN = 1
ITEM_MAX = 5

# Bjureberg 2016 Table 2 — 1-indexed item positions per subscale.
# A refactor that reordered items or rotated subscale rows
# (e.g. so "Impulse" accidentally picked up Goals items) would
# silently miscategorize the clinical signal; every subscale
# test pins its item mapping independently.
DERS16_SUBSCALES: dict[str, tuple[int, ...]] = {
    "nonacceptance": (9, 10, 13),
    "goals": (3, 7, 15),
    "impulse": (4, 8, 11),
    "strategies": (5, 6, 12, 14, 16),
    "clarity": (1, 2),
}


class InvalidResponseError(ValueError):
    """Raised on item-count, item-range, or item-type violations."""


@dataclass(frozen=True)
class Ders16Result:
    """Typed DERS-16 output.

    Fields:
    - ``total``: 16-80, the straight sum of the 16 Likert items.
      Minimum 16 because every item's lowest response value is 1
      ("almost never"), not 0 — same floor semantic as K10 / K6 /
      AAQ-II.
    - ``subscale_nonacceptance`` / ``subscale_goals`` /
      ``subscale_impulse`` / ``subscale_strategies`` /
      ``subscale_clarity``: five subscale totals per Bjureberg 2016
      item-assignment.  Each subscale is a non-negative integer
      total on its native scale (Nonacceptance / Goals / Impulse
      3-15; Strategies 5-25; Clarity 2-10).  Surfaced on the
      router's AssessmentResult envelope via the ``subscales`` map
      (wire keys are the un-prefixed forms — ``nonacceptance`` /
      ``goals`` / ``impulse`` / ``strategies`` / ``clarity`` — per
      ``DERS16_SUBSCALES``).
    - ``items``: verbatim input tuple, pinned for auditability.

    Deliberately-absent fields:
    - No ``severity`` field — Bjureberg 2016 published no bands;
      DERS-16 is a continuous dimensional measure.  The router
      envelope emits ``severity="continuous"`` as a sentinel
      (uniform with Craving VAS / PACS).
    - No ``cutoff_used`` / ``positive_screen`` — continuous
      instrument, no cutoff shape.
    - No ``requires_t3`` field — DERS-16 has no safety item.
    """

    total: int
    subscale_nonacceptance: int
    subscale_goals: int
    subscale_impulse: int
    subscale_strategies: int
    subscale_clarity: int
    items: tuple[int, ...]
    instrument_version: str = INSTRUMENT_VERSION


def _validate_item(index_1: int, value: object) -> int:
    """Validate a single 1-5 Likert item and return the int value.

    ``index_1`` is the 1-indexed item number (1-16) so error
    messages name the item a clinician would recognize from the
    DERS-16 document.
    """
    # Bool rejection — uniform with the rest of the psychometric package.
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidResponseError(
            f"DERS-16 item {index_1} must be int, got {value!r}"
        )
    if value < ITEM_MIN or value > ITEM_MAX:
        raise InvalidResponseError(
            f"DERS-16 item {index_1} out of range "
            f"[{ITEM_MIN}, {ITEM_MAX}]: {value}"
        )
    return value


def _subscale_sum(items: tuple[int, ...], subscale_name: str) -> int:
    """Sum the items belonging to a named subscale.

    DERS16_SUBSCALES holds 1-indexed positions; convert to 0-indexed
    array access here.  A refactor that shifted the subscale index
    tuples would break the clinical signal silently — every
    subscale test pins its item mapping independently.
    """
    positions_1 = DERS16_SUBSCALES[subscale_name]
    return sum(items[pos - 1] for pos in positions_1)


def score_ders16(raw_items: Sequence[int]) -> Ders16Result:
    """Score a DERS-16 response set.

    Inputs:
    - ``raw_items``: 16 items, each 1-5 Likert (1 = "Almost never",
      5 = "Almost always").

    Raises :class:`InvalidResponseError` on:
    - Wrong number of items.
    - A non-int / bool item value.
    - An item outside ``[1, 5]``.

    Computes:
    - Total score (16-80).
    - Five subscale totals per Bjureberg 2016 item assignments.

    No severity band is emitted — see module docstring.
    """
    if len(raw_items) != ITEM_COUNT:
        raise InvalidResponseError(
            f"DERS-16 requires exactly {ITEM_COUNT} items, got {len(raw_items)}"
        )
    items = tuple(
        _validate_item(index_1=i + 1, value=v)
        for i, v in enumerate(raw_items)
    )
    total = sum(items)

    return Ders16Result(
        total=total,
        subscale_nonacceptance=_subscale_sum(items, "nonacceptance"),
        subscale_goals=_subscale_sum(items, "goals"),
        subscale_impulse=_subscale_sum(items, "impulse"),
        subscale_strategies=_subscale_sum(items, "strategies"),
        subscale_clarity=_subscale_sum(items, "clarity"),
        items=items,
    )


__all__ = [
    "DERS16_SUBSCALES",
    "INSTRUMENT_VERSION",
    "ITEM_COUNT",
    "ITEM_MAX",
    "ITEM_MIN",
    "Ders16Result",
    "InvalidResponseError",
    "score_ders16",
]

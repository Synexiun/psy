"""RRS-10 — Ruminative Responses Scale, 10-item (Treynor 2003).

The RRS-10 is the psychometrically refined subset of Nolen-Hoeksema's
original 22-item Ruminative Responses Scale (RRS-22, part of the
Response Styles Questionnaire, Nolen-Hoeksema & Morrow 1991).  The
22-item scale confounded rumination with depressive symptom content —
12 of its items asked about things a depressed person thinks about
*because they are depressed* (e.g., "Think about your feelings of
fatigue"), producing spurious correlations between rumination and
depression severity that were driven by content overlap rather than
process.

Treynor, Gonzalez & Nolen-Hoeksema 2003 applied principal-components
analysis to the 10 non-depressive-symptom items of the RRS-22 and
extracted a clean two-factor structure:

- **Brooding** (5 items) — a passive, self-critical, evaluative
  comparison of one's current state with some unachieved standard
  ("What am I doing to deserve this?", "Why can't I handle things
  better?").  Brooding is the *maladaptive* factor: it uniquely
  predicts depressive-symptom severity prospectively and correlates
  with poorer psychosocial outcomes, independent of concurrent
  depression.
- **Reflection** (5 items) — a purposeful turn-inward to engage in
  cognitive problem-solving to alleviate one's depressive symptoms
  ("Go away by yourself and think about why you feel this way",
  "Analyze recent events to try to understand why you are
  depressed").  Reflection is the *adaptive* factor: cross-
  sectionally it modestly predicts concurrent depressive symptoms
  (it tracks current distress), but prospectively it is either
  neutral or protective — it supports active coping rather than
  passive perseveration.

This two-factor split is the entire clinical point of using RRS-10
over RRS-22.  "Does this patient ruminate?" is the wrong clinical
question — most distressed patients do.  "Which KIND of rumination
dominates?" is the question that routes treatment.

Clinical relevance to the Discipline OS platform:
The emotion-processing architecture now reads a five-layer profile:

 1. **TAS-20** — upstream: can the patient IDENTIFY the emotion?
 2. **ERQ** — midstream: WHICH strategy does the patient reach for?
 3. **DERS-16** — downstream: can the patient EXECUTE regulation?
 4. **SCS-SF** — affective color: what is the self-stance toward
    the emotion?  (Compassion vs shame.)
 5. **RRS-10** — attentional/cognitive loop: once the feeling is
    present, does the patient BROOD (passive, evaluative, self-
    critical) or REFLECT (active, analytic, problem-solving)?

Rumination is the mediator that converts transient affect into
sustained distress.  The process model that underwrites this
platform's T2/T3 intervention window (60–180 s between urge and
action) treats brooding as the *attentional engine* that keeps an
urge alive past the point where decay would naturally resolve it.
A user who notices an urge at t=0 and brood-ruminates will still be
escalating at t=180 s; a user who notices the same urge and applies
detached analytic reflection (or, better, a mindfulness / grounding
intervention) will have dropped below threshold by then.

The RRS-10 profile therefore directly gates intervention choice:

- High brooding, low reflection → mindfulness / attention-deployment
  tools (detached mindfulness, 3-minute breathing space, urge-
  surfing) PRIOR to any cognitive intervention.  Cognitive work on
  a brood-dominant mind amplifies the loop.
- High brooding, high reflection → analytical reframing tools
  (Socratic questioning, behavioural-activation worksheets) after
  a brief attention-deployment bridge.  The patient has the
  analytic capacity; they need to stop brooding long enough to use
  it.
- Low brooding, high reflection → low-intervention coasting —
  encourage reflective journaling / problem-solving; do not
  disrupt an adaptive process with unnecessary scaffolding.
- Low brooding, low reflection → evaluate for emotion-avoidance
  (TAS-20 DIF, ERQ suppression, AAQ-II).  Lack of rumination in
  the presence of distress markers on other instruments signals
  disengagement, not health.

Substance-use / compulsive-behaviour specifically:
- **Caselli et al. 2010, 2012** — rumination is the primary
  cognitive mediator of craving persistence in alcohol-use-
  disorder samples.  Brooding specifically predicts time-to-
  relapse prospectively; reflection does not.  The Desire Thinking
  construct (elaborated from RRS brooding) is now the target of
  metacognitive therapy for addictions (Spada 2015).
- **Nolen-Hoeksema 2008** (transdiagnostic review) — brooding
  mediates the link between negative life events and each of:
  depression, anxiety, alcohol problems, binge eating, and self-
  injury.  The platform reads elevated brooding as a cross-
  construct amplifier.
- **Watkins 2008** (concrete vs abstract processing) — adaptive
  reflection tends to be concrete (specific situation, specific
  feeling); maladaptive brooding is abstract ("why me?", "why is
  my life like this?").  Interventions that shift brooding to
  concrete self-examination convert maladaptive rumination into
  reflection.

Instrument structure (Treynor, Gonzalez & Nolen-Hoeksema 2003):

**10 items, each on a 4-point Likert scale** scored:
    1 = almost never
    2 = sometimes
    3 = often
    4 = almost always

Items are statements following the stem "People think and do many
different things when they feel depressed.  Please read each of the
items below and indicate whether you almost never, sometimes, often,
or almost always think or do each one when you feel down, sad, or
depressed.  Please indicate what you GENERALLY do, not what you
think you should do."

**Two subscales** per Treynor 2003 PCA:

- **Brooding** (5 items: 1, 3, 6, 7, 8)
   1. "What am I doing to deserve this?"        [RRS-22 item 5]
   3. "Why do I always react this way?"         [RRS-22 item 10]
   6. "Think 'Why do I have problems other people don't have?'"
                                                [RRS-22 item 13]
   7. "Think 'Why can't I handle things better?'"
                                                [RRS-22 item 15]
   8. "Think about a recent situation, wishing it had gone better."
                                                [RRS-22 item 16]

- **Reflection** (5 items: 2, 4, 5, 9, 10)
   2. "Analyze recent events to try to understand why you are
       depressed."                              [RRS-22 item 7]
   4. "Go away by yourself and think about why you feel this way."
                                                [RRS-22 item 11]
   5. "Write down what you are thinking about and analyze it."
                                                [RRS-22 item 12]
   9. "Analyze your personality to try to understand why you are
       depressed."                              [RRS-22 item 20]
  10. "Go someplace alone to think about your feelings."
                                                [RRS-22 item 21]

Items are presented in the RRS-10 in the order inherited from the
RRS-22 (5, 7, 10, 11, 12, 13, 15, 16, 20, 21 renumbered 1-10);
this is the Treynor-preserving ordering used in the validation
literature and carried forward here so audit-trail items are
traceable to published psychometric work.

**No reverse scoring.**  Every item is worded in the rumination-
endorsement direction; higher Likert = more rumination of the
subscale's type.  Aligned with ERQ (both were validated with no
reverse items as a deliberate choice to keep subscale sums directly
interpretable without flip-arithmetic).

**No published severity bands.**  Treynor 2003 and subsequent
validation work (Whitmer & Gotlib 2011, Schoofs 2010, Siegle 2004)
report RRS-10 as a dispositional continuous measure.  Clinical
interpretation reads the subscale pair (brooding, reflection) as
a 2-tuple, not a categorical classification.  The router therefore
emits ``severity=None`` (continuous-sentinel) and ``cutoff_used=
None`` — uniform with DERS-16 / ERQ / BRS / PSWQ / SDS / K6 / SCS-SF.

**Scoring convention**: Treynor 2003 reports SUMS for both
subscales.  This matches the platform convention used for DERS-16,
TAS-20, ERQ, and SCS-SF (integer sums, no floating-point in the
audit trail).  Reported sums:

    brooding:   5 items × 1-4 Likert = sum in [5, 20]
    reflection: 5 items × 1-4 Likert = sum in [5, 20]
    total:     10 items × 1-4 Likert = sum in [10, 40]

Clinical interpretation reads the subscale pair.  Treynor 2003
reports mean brooding ≈ 10.4 (SD 3.1) and mean reflection ≈ 10.1
(SD 3.1) in a community sample, with clinical samples typically
elevated ~2-3 points on brooding specifically.  The platform does
NOT hard-code thresholds because (a) Treynor 2003 did not publish
them and (b) population norms vary substantially across samples
(Schoofs 2010 Belgian adults, Whitmer & Gotlib 2011 US students);
clinician-reported trajectory over repeat administration is the
primary clinical signal.

Safety routing:
- RRS-10 has NO safety item.  It does not screen for suicidality,
  self-harm, or acute risk.  Note: the RRS-22 contains items that
  reference suicidal-ideation content ("Think 'I won't be able to
  do my job if I don't snap out of this'", etc.) but the RRS-10
  subset is entirely process-focused (attentional style) with no
  content that would elicit imminent-harm signal.
- Safety routing stays with C-SSRS, PHQ-9 item 9, PCL-5, OCIR.
  ``requires_t3`` is hard-coded ``False`` at the router.

References:
- Treynor W, Gonzalez R, Nolen-Hoeksema S (2003).  *Rumination
  reconsidered: A psychometric analysis.*  Cognitive Therapy and
  Research 27(3):247-259.  (Primary validation — PCA of 10 non-
  symptom-confounded items from RRS-22, extraction of brooding and
  reflection factors.)
- Nolen-Hoeksema S, Morrow J (1991).  *A prospective study of
  depression and posttraumatic stress symptoms after a natural
  disaster: The 1989 Loma Prieta earthquake.*  Journal of
  Personality and Social Psychology 61(1):115-121.  (Original
  Response Styles Questionnaire — parent of RRS-22.)
- Nolen-Hoeksema S, Wisco BE, Lyubomirsky S (2008).  *Rethinking
  rumination.*  Perspectives on Psychological Science 3(5):400-
  424.  (Transdiagnostic review — brooding as cross-construct
  amplifier.)
- Watkins ER (2008).  *Constructive and unconstructive repetitive
  thought.*  Psychological Bulletin 134(2):163-206.  (Concrete vs
  abstract processing distinction; theoretical scaffold for why
  brooding is maladaptive and reflection is adaptive.)
- Caselli G, Ferretti C, Leoni M, Rebecchi D, Rovetto F, Spada MM
  (2010).  *Rumination as a predictor of drinking behaviour in
  alcohol abusers: A prospective study.*  Addiction 105(6):1041-
  1048.  (Brooding → prospective alcohol relapse; reflection not
  predictive.)
- Caselli G, Bortolai C, Leoni M, Rovetto F, Spada MM (2012).
  *Rumination in problem drinkers.*  Addiction Research and
  Theory 16(6):564-571.  (Replication + desire-thinking
  construct.)
- Spada MM, Caselli G, Nikčević AV, Wells A (2015).  *Metacognition
  in addictive behaviors.*  Addictive Behaviors 44:9-15.
  (Metacognitive therapy for addictions — brooding-target
  intervention protocol.)
- Whitmer AJ, Gotlib IH (2011).  *Brooding and reflection
  reconsidered: A factor analytic examination of rumination in
  currently depressed, formerly depressed, and never depressed
  individuals.*  Cognitive Therapy and Research 35(2):99-107.
  (Two-factor structure confirmation across clinical phases.)
- Schoofs H, Hermans D, Raes F (2010).  *Brooding and reflection
  as subtypes of rumination: Evidence from confirmatory factor
  analysis in nonclinical samples using the Dutch Ruminative
  Response Scale.*  Journal of Psychopathology and Behavioral
  Assessment 32(4):609-617.  (Cross-cultural / translation
  confirmation of two-factor structure.)
- Siegle GJ, Moore PM, Thase ME (2004).  *Rumination: One
  construct, many features in healthy individuals, depressed
  individuals, and individuals with lupus.*  Cognitive Therapy
  and Research 28(5):645-668.  (Rumination × physiological
  substrate — sustained amygdala engagement during brooding.)
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

INSTRUMENT_VERSION = "rrs10-1.0.0"
ITEM_COUNT = 10
ITEM_MIN = 1
ITEM_MAX = 4

# Treynor, Gonzalez & Nolen-Hoeksema 2003 PCA — 1-indexed item
# positions per subscale.  The mapping PRESERVES the RRS-22
# item numbering order: when the 10 non-symptom-confounded items
# (RRS-22 #5, #7, #10, #11, #12, #13, #15, #16, #20, #21) are
# renumbered 1-10 in order, brooding lands at (1, 3, 6, 7, 8) and
# reflection at (2, 4, 5, 9, 10).  A refactor that reordered items
# would silently miscategorize brooding (maladaptive) as reflection
# (adaptive) — the clinical signal runs through subscale assignment,
# not just item inclusion.
RRS10_SUBSCALES: dict[str, tuple[int, ...]] = {
    "brooding": (1, 3, 6, 7, 8),
    "reflection": (2, 4, 5, 9, 10),
}


class InvalidResponseError(ValueError):
    """Raised on item-count, item-range, or item-type violations."""


@dataclass(frozen=True)
class Rrs10Result:
    """Typed RRS-10 output.

    Fields:
    - ``total``: 10-40, the straight sum of the 10 Likert items.
      Minimum 10 because every item's lowest response value is 1
      ("almost never"), not 0 — uniform with ERQ / TAS-20 / DERS-16
      floor semantics.  The total is an audit-trail convenience;
      clinical reads go through the (brooding, reflection) pair,
      which is the actual psychometric target.
    - ``subscale_brooding`` / ``subscale_reflection``: the two
      subscale sums per Treynor 2003 PCA assignments.  Both range
      5-20 (5 items × 1-4 Likert).  Surfaced on the router's
      AssessmentResult envelope via the ``subscales`` map (wire
      keys: ``brooding`` / ``reflection``).
    - ``items``: verbatim 10-tuple input, pinned for auditability.

    Deliberately-absent fields:
    - No ``severity`` field — Treynor 2003 published no bands;
      RRS-10 is a continuous dimensional measure.  The router
      envelope emits ``severity=None`` (continuous-sentinel) —
      uniform with DERS-16 / ERQ / BRS / PSWQ / SDS / K6 / SCS-SF.
    - No ``cutoff_used`` / ``positive_screen`` — continuous
      instrument, no cutoff shape.
    - No ``requires_t3`` field — RRS-10 has no safety item.
    """

    total: int
    subscale_brooding: int
    subscale_reflection: int
    items: tuple[int, ...]
    instrument_version: str = INSTRUMENT_VERSION


def _validate_item(index_1: int, value: object) -> int:
    """Validate a single 1-4 Likert item and return the int value.

    ``index_1`` is the 1-indexed item number (1-10) so error
    messages name the item a clinician would recognize from the
    RRS-10 document.
    """
    # Bool rejection — uniform with the rest of the psychometric package.
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidResponseError(
            f"RRS-10 item {index_1} must be int, got {value!r}"
        )
    if value < ITEM_MIN or value > ITEM_MAX:
        raise InvalidResponseError(
            f"RRS-10 item {index_1} out of range "
            f"[{ITEM_MIN}, {ITEM_MAX}]: {value}"
        )
    return value


def _subscale_sum(items: tuple[int, ...], subscale_name: str) -> int:
    """Sum the items belonging to a named subscale.

    RRS10_SUBSCALES holds 1-indexed positions; convert to 0-indexed
    array access here.  No reverse-keying flip is needed because
    all 10 items are direction-aligned with their subscale's
    construct (higher = more rumination of that type).
    """
    positions_1 = RRS10_SUBSCALES[subscale_name]
    return sum(items[pos - 1] for pos in positions_1)


def score_rrs10(raw_items: Sequence[int]) -> Rrs10Result:
    """Score an RRS-10 response set.

    Inputs:
    - ``raw_items``: 10 items, each 1-4 Likert (1 = "almost never",
      4 = "almost always").  No reverse-keying — every item is
      endorsement-direction for its subscale.  Item order follows
      Treynor 2003 (inherited from RRS-22 items 5, 7, 10, 11, 12,
      13, 15, 16, 20, 21 renumbered 1-10 in order).

    Raises :class:`InvalidResponseError` on:
    - Wrong number of items (must be exactly 10).
    - A non-int / bool item value.
    - An item outside ``[1, 4]``.

    Computes:
    - Total (10-40).
    - Brooding subscale sum (5-20).
    - Reflection subscale sum (5-20).

    No severity band is emitted — see module docstring.
    """
    if len(raw_items) != ITEM_COUNT:
        raise InvalidResponseError(
            f"RRS-10 requires exactly {ITEM_COUNT} items, got {len(raw_items)}"
        )
    items = tuple(
        _validate_item(index_1=i + 1, value=v)
        for i, v in enumerate(raw_items)
    )
    total = sum(items)

    return Rrs10Result(
        total=total,
        subscale_brooding=_subscale_sum(items, "brooding"),
        subscale_reflection=_subscale_sum(items, "reflection"),
        items=items,
    )


__all__ = [
    "INSTRUMENT_VERSION",
    "ITEM_COUNT",
    "ITEM_MAX",
    "ITEM_MIN",
    "RRS10_SUBSCALES",
    "InvalidResponseError",
    "Rrs10Result",
    "score_rrs10",
]

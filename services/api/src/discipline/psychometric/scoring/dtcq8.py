"""DTCQ-8 — Drug-Taking Confidence Questionnaire, 8-item short form.

The Drug-Taking Confidence Questionnaire (DTCQ) is the **coping
self-efficacy** instrument paired with the Inventory of Drug-Taking
Situations (IDTS) in Annis's addiction-treatment framework.  Where
IDTS measures situational *vulnerability* ("how often have you used
in this kind of situation?"), DTCQ measures situational *confidence*
("how confident are you that you could resist using in this kind of
situation?").  The two are the situational-specificity companions
to the general self-efficacy construct Bandura 1977 formalized; in
relapse-prevention terms they operationalize Marlatt & Gordon 1985's
"high-risk situation" taxonomy into a measurable coping profile.

The original DTCQ was introduced in

    Sklar SM, Annis HM, Turner NE (1997).  *Development and validation
    of the Drug-Taking Confidence Questionnaire: a measure of coping
    self-efficacy.*  Addictive Behaviors 22(5):655-670.

as a 50-item instrument mirroring the 50-situation IDTS.  The
8-item short form — adopted throughout the Discipline OS platform —
was validated in

    Sklar SM, Turner NE (1999).  *A brief measure for the assessment
    of coping self-efficacy among alcohol and other drug users.*
    Addiction 94(5):723-729.

which demonstrated α = 0.87 and strong factor-structure parallel with
the full 50-item DTCQ (r = 0.94 with the long form across samples).
Sklar 1999 preserves Marlatt's 8-category taxonomy by picking one
prototype item per category, yielding an 8-item instrument that
captures the full coping-self-efficacy profile in ~90 seconds of
administration.

Clinical relevance to the Discipline OS platform:
DTCQ-8 is the **coping-profile** instrument — the only shipped
instrument where the *per-item* profile, not just the aggregate
score, carries irreducible clinical signal.  PHQ-9, GAD-7, PSS-10
answer "how symptomatic?" with a single number.  PACS and Craving
VAS answer "how strong is the urge?" with a single number.  DTCQ-8
answers "*where* is this person weak?" — a user with low confidence
in social-pressure situations (item 7) but high confidence in
unpleasant-emotions situations (item 1) has a fundamentally
different intervention profile than a user with the opposite pattern.
The former routes to social-skills / refusal-skills work; the latter
routes to distress-tolerance / emotion-regulation work.

Accordingly the intervention layer reads the 8-tuple, not just the
aggregate — see Docs/Technicals/12_Psychometric_System.md §3.1
(coping-profile-driven tool selection).  The wire format remains a
positional ``items: list[int]`` for consistency with every other
instrument, but the positional mapping is *semantic* (not just
auditability-preserving as with VAS / Ruler), so the module exposes
``SITUATION_LABELS`` as a public constant and the module docstring
pins the positional order below.

Instrument structure (Sklar & Turner 1999):

**8 items, each on a 0-100 integer scale** of confidence to resist
using in the situation ("How confident are you that you could
resist [using/drinking] if ...").  Anchors: 0 = "Not at all
confident", 100 = "Very confident".  The 0-100 scale is deliberately
the *same* as Craving VAS's range (Sayette 2000), so a caller
switching between instruments sees one integer scale — but DTCQ-8
is higher-is-better (confidence = coping capacity), while VAS is
higher-is-worse (intensity = urge to use).  The trajectory-layer
direction semantics must match this (see below).

Positional item order (Sklar 1999, preserving Marlatt & Gordon 1985):

 1. **Unpleasant emotions** — "... if I was feeling depressed about
    things in general."  Negative-affect situations.

 2. **Physical discomfort** — "... if I had trouble sleeping."
    Physical-state situations (pain, fatigue, withdrawal).

 3. **Pleasant emotions** — "... if I wanted to celebrate with a
    friend."  Positive-affect situations.

 4. **Testing personal control** — "... if I thought I could handle
    using just a little."  Testing-willpower situations.

 5. **Urges and temptations** — "... if I suddenly had an urge to use."
    Cue-reactivity situations.

 6. **Conflict with others** — "... if I had an argument with a
    friend."  Interpersonal-conflict situations.

 7. **Social pressure to use** — "... if someone pressured me to
    use."  Direct/indirect social-pressure situations.

 8. **Pleasant times with others** — "... if I was having a good
    time with friends and they decided to use."  Social-positive
    situations.

Scoring (Sklar & Turner 1999):
- **Mean across the 8 items** (NOT the sum).  Range 0-100 on Annis's
  coping-self-efficacy percentage scale — a user whose mean is 80
  reports 80% confidence in their coping repertoire across the eight
  high-risk categories.
- No reverse-coding.  No weighting — each of Marlatt's 8 categories
  weighs equally.
- Sklar 1999 does NOT recommend subscale partitioning of the 8-item
  form (the 50-item form has 8× 5-item subscales, one per Marlatt
  category, but the 8-item form has one item per category so the
  "subscale score" is just the per-item score).

**Aggregation shape**: the platform exposes both ``total`` (int,
the mean rounded to the nearest integer) and ``mean`` (float, the
exact mean).  Rationale:

- ``total: int`` keeps the router envelope uniform with every other
  instrument in the dispatch table — the AssessmentResult contract
  is ``total: int``, and downgrading to ``float`` would ripple
  through 17 sibling instruments, FHIR valueInteger emission, and
  every chart renderer.

- ``mean: float`` preserves the exact aggregate for FHIR
  ``valueDecimal`` emission and clinician-PDF precision.  A user
  with items [50, 50, 50, 50, 50, 50, 50, 51] has mean 50.125 —
  rounding to int 50 loses the "just above threshold" signal that
  a clinician reading the PDF should see.  The 8-item mean will
  always be a decimal with resolution 0.125 so the loss is
  real, not theoretical.

The per-item integer responses are preserved verbatim in ``items``
so the intervention layer can read the per-situation profile
without re-deriving it from any aggregate.

**Direction semantics** — higher is better:
Like WHO-5 and Readiness Ruler (the two prior higher-is-better
instruments), a rising DTCQ-8 score is *improvement* (the user
reports growing coping self-efficacy).  The trajectory layer's
RCI direction logic must register DTCQ-8 in the higher-is-better
partition alongside WHO-5 and Ruler — applying the PHQ-9 /
GAD-7 / PSS-10 / PACS / VAS direction would report improvement
as deterioration and vice-versa.

Severity bands — deliberately absent:
Sklar 1999 publishes no cutoffs.  The clinical literature treats
DTCQ-8 as a continuous coping-self-efficacy estimate; the 50-point
midpoint is sometimes described in clinical-training contexts as
"moderate confidence" but this is pedagogical shorthand, not a
validated cutoff with consensus uptake.  Accordingly the scorer
emits no severity band; the router envelope uses
``severity="continuous"`` as a sentinel (uniform with PACS,
Craving VAS, and Readiness Ruler).

Fabricating bands here would violate CLAUDE.md's "Don't hand-roll
severity thresholds" rule.

Safety routing:
DTCQ-8 has no suicidality item and no acute-harm item.
``requires_t3`` is deliberately absent — low coping self-efficacy
is a vulnerability signal routing to skill-building / MI interventions,
not a crisis signal.  A DTCQ-8 score of 0 ("no confidence at all")
pairs with low-agency / high-craving profiles and the product
responds with interventions matched to the weakest situation-category;
acute ideation is gated by PHQ-9 item 9 / C-SSRS per the uniform
safety-posture convention across PACS / PHQ-15 / OCI-R / ISI / VAS /
Ruler.

Bool rejection note:
Uniform with the rest of the psychometric package — bool items are
rejected at the validator.  A caller submitting ``True`` / ``False``
as shorthand for "yes / no confident" would have their response
silently coerced to 1 / 0 on a 0-100 scale, producing a misleading
"essentially zero confidence" signal instead of surfacing the wire-
format error.

FHIR / LOINC note:
LOINC has a code for the 50-item DTCQ panel but no widely-adopted
code for the 8-item short form.  Per the PACS / VAS / Ruler /
C-SSRS precedent, DTCQ-8 is NOT registered in ``LOINC_CODE`` /
``LOINC_DISPLAY`` at this time; the FHIR export will use a
system-local code when the reports-layer render path is extended
in a later sprint.  The per-item ``components`` array on the FHIR
Observation will preserve the 8-tuple so the coping-profile is
recoverable from the exported record — unlike single-score
instruments where ``valueInteger`` alone is sufficient.

Substance-class neutrality:
Sklar 1999 validated the instrument across alcohol, stimulant, and
opioid samples; the short-form parallel validation spans the full
substance spectrum.  The scorer is substance-agnostic — the
vertical (alcohol / cannabis / nicotine / opioid / gambling /
porn-use) is resolved at the UI layer.  Making the scorer
substance-agnostic lets the same validated instrument serve every
vertical without per-vertical branching, matching Sklar 1999's
validation posture and uniform with Ruler / VAS / PACS.

References:
- Sklar SM, Annis HM, Turner NE (1997).  *Development and validation
  of the Drug-Taking Confidence Questionnaire: a measure of coping
  self-efficacy.*  Addictive Behaviors 22(5):655-670.
- Sklar SM, Turner NE (1999).  *A brief measure for the assessment
  of coping self-efficacy among alcohol and other drug users.*
  Addiction 94(5):723-729.
- Annis HM, Graham JM (1988).  *Situational Confidence Questionnaire
  (SCQ-39): User's Guide.*  Addiction Research Foundation, Toronto.
- Marlatt GA, Gordon JR, eds. (1985).  *Relapse Prevention:
  Maintenance Strategies in the Treatment of Addictive Behaviors.*
  Guilford Press, New York.
- Bandura A (1977).  *Self-efficacy: toward a unifying theory of
  behavioral change.*  Psychological Review 84(2):191-215.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

INSTRUMENT_VERSION = "dtcq8-1.0.0"
ITEM_COUNT = 8
ITEM_MIN = 0
ITEM_MAX = 100

# Marlatt's 8-category taxonomy, positional in the order Sklar 1999
# administers.  Exposed as a module constant (tuple of str) so the
# intervention layer reading the per-situation profile can use one
# source-of-truth for situation labels rather than hand-maintaining
# a parallel table.  Tuple, not list, so downstream code cannot
# mutate the ordering — the positional mapping is load-bearing.
SITUATION_LABELS: tuple[str, ...] = (
    "unpleasant_emotions",
    "physical_discomfort",
    "pleasant_emotions",
    "testing_personal_control",
    "urges_and_temptations",
    "conflict_with_others",
    "social_pressure_to_use",
    "pleasant_times_with_others",
)


class InvalidResponseError(ValueError):
    """Raised on item-count, item-range, or item-type violations."""


@dataclass(frozen=True)
class Dtcq8Result:
    """Typed DTCQ-8 output.

    Fields:
    - ``total``: 0-100, the mean confidence across the 8 situations,
      **rounded to the nearest integer** via banker's rounding
      (Python's built-in ``round``).  Flows into the trajectory
      layer as a **higher-is-better** continuous coping signal —
      a week-over-week Δ of +5 is improvement.  Kept as ``int`` so
      the AssessmentResult envelope is uniform with every other
      instrument (PHQ-9 total, GAD-7 total, PACS total).
    - ``mean``: the *exact* mean as a float.  For FHIR valueDecimal
      emission and clinician-PDF precision; a user with items
      ``[50, 50, 50, 50, 50, 50, 50, 51]`` has mean ``50.125`` which
      rounds to ``total = 50`` — the PDF should still show the
      precise value so the clinician sees the "just above threshold"
      signal.
    - ``items``: verbatim input tuple (length 8), pinned for
      auditability AND for the intervention layer's per-situation
      profile read.  The positional mapping is :data:`SITUATION_LABELS`.

    Deliberately-absent fields:
    - No ``severity`` field — Sklar 1999 publishes no bands.  The
      router envelope emits ``severity="continuous"`` as a sentinel
      (uniform with PACS, Craving VAS, Readiness Ruler).
    - No ``requires_t3`` field — DTCQ-8 measures coping self-efficacy,
      not crisis.  Low self-efficacy is a skill-building signal, not
      a T3 trigger; acute suicidality is gated by PHQ-9 / C-SSRS.
    - No subscale fields — the 8-item form has one item per Marlatt
      category, so per-category "scores" are just the per-item values
      already in ``items``.  The intervention layer reads
      ``items[i]`` directly through :data:`SITUATION_LABELS`.
    """

    total: int
    mean: float
    items: tuple[int, ...]
    instrument_version: str = INSTRUMENT_VERSION


def _validate_item(index_1: int, value: object) -> int:
    """Validate a single 0-100 DTCQ-8 item and return the int value.

    ``index_1`` is the 1-indexed item number (1-8) so error messages
    name the item a clinician would recognize from the Sklar 1999
    instrument document.  The per-item label in :data:`SITUATION_LABELS`
    is not included in the error message — the 1-indexed number is
    sufficient and the label would leak implementation detail into
    validation text.
    """
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidResponseError(
            f"DTCQ-8 item {index_1} must be int, got {value!r}"
        )
    if value < ITEM_MIN or value > ITEM_MAX:
        raise InvalidResponseError(
            f"DTCQ-8 item {index_1} out of range "
            f"[{ITEM_MIN}, {ITEM_MAX}]: {value}"
        )
    return value


def score_dtcq8(raw_items: Sequence[int]) -> Dtcq8Result:
    """Score a DTCQ-8 response set.

    Inputs:
    - ``raw_items``: 8 integers, each 0-100, positional per
      :data:`SITUATION_LABELS` (unpleasant_emotions,
      physical_discomfort, pleasant_emotions, testing_personal_control,
      urges_and_temptations, conflict_with_others,
      social_pressure_to_use, pleasant_times_with_others).

    Raises :class:`InvalidResponseError` on:
    - Wrong number of items (anything other than 8).
    - A non-int / bool item value.
    - An item outside ``[0, 100]``.

    Returns a :class:`Dtcq8Result` with:
    - ``total``: the mean across items, rounded to int via
      :func:`round` (banker's rounding — Python default).
    - ``mean``: the exact float mean.
    - ``items``: the pinned 8-tuple.

    No severity band is emitted — see module docstring.
    """
    if len(raw_items) != ITEM_COUNT:
        raise InvalidResponseError(
            f"DTCQ-8 requires exactly {ITEM_COUNT} items, got {len(raw_items)}"
        )
    items = tuple(
        _validate_item(index_1=i + 1, value=v)
        for i, v in enumerate(raw_items)
    )
    mean = sum(items) / ITEM_COUNT
    total = round(mean)

    return Dtcq8Result(
        total=total,
        mean=mean,
        items=items,
    )


__all__ = [
    "INSTRUMENT_VERSION",
    "ITEM_COUNT",
    "ITEM_MAX",
    "ITEM_MIN",
    "SITUATION_LABELS",
    "Dtcq8Result",
    "InvalidResponseError",
    "score_dtcq8",
]

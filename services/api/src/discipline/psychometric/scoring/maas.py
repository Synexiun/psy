"""MAAS — Mindful Attention Awareness Scale (Brown & Ryan 2003).

The MAAS is the most widely validated dispositional (trait) measure
of **mindful attention** — the day-to-day frequency with which a
person is consciously aware of and present to what is happening,
versus being on "automatic pilot" or cognitively absorbed in thought
about the past or future.  The construct operationalized is the
*presence of attention*, not the moral / evaluative components some
later mindfulness scales add (acceptance, non-judgment, compassion);
Brown & Ryan 2003 deliberately restricted the MAAS to the
attentional / awareness component as the psychometrically cleanest
target.

Clinical relevance to the Discipline OS platform:

The platform's 60–180 s urge-intervention window depends on the user
being able to NOTICE the rising urge before it progresses to action.
Mindful attention is the exact capacity that short-circuits that
escalation — it is the skill that every in-app grounding / urge-
surfing / 3-minute-breathing-space tool is training and that every
intervention outcome study on mindfulness-based relapse prevention
(MBRP; Bowen, Chawla & Marlatt 2010; Bowen et al. 2014 RCT) has
used the MAAS as its primary dispositional outcome measure.

The MAAS therefore plays a dual clinical role in this platform:

 1. **Baseline stratification** — a user whose MAAS score is low at
    enrollment is a candidate for mindfulness-first intervention
    sequencing.  Cognitive or behavioural tools assume a user who
    can notice their internal state; without that scaffolding, the
    tools are applied to a patient who cannot yet observe the state
    they are meant to regulate.
 2. **Outcome measure** — every mindfulness-based tool variant in
    the ToolRegistry (grounding, 5-4-3-2-1 sensory, body scan,
    urge-surfing, 3-minute breathing space) is training MAAS.
    Repeated administration of the MAAS is how we validate whether
    the tool variants are producing dispositional change, not just
    in-session affect regulation.

Profile pairing with other instruments the platform ships:

- **RRS-10 (Sprint 58)** — high brooding + low MAAS is the
  prototypical "trapped in the loop" profile (Bowen 2014,
  Jermann 2009).  The low-MAAS patient literally does not have
  the attentional skill to notice the brood as it rises, let
  alone step back from it.  Mindfulness-based intervention
  targets the MAAS; the RRS-brooding improvement follows as a
  downstream consequence.  High brooding + moderate MAAS signals
  skill availability without automatic deployment under stress
  — a different intervention target (implementation intentions,
  cued practice).
- **TAS-20 (Sprint 55)** — high alexithymia (DIF) + low MAAS
  signals a patient who cannot identify emotions AND cannot
  attend to the bodily signals from which emotion identification
  is built.  Treatment sequence: body-scan / interoceptive
  attention first (MAAS-targeted), then affect-labeling (TAS-20-
  targeted).  The sequence matters — doing affect-labeling
  homework with a low-MAAS patient produces false negatives
  (they don't notice the feelings to label them).
- **ERQ (Sprint 56)** — MAAS correlates negatively with
  suppression and positively with reappraisal (Brown 2003
  Study 3), but causally the relationship is: low MAAS →
  fewer moments of noticing the early emotion → no opportunity
  to apply reappraisal → default to suppression.  The MAAS is
  thus an *antecedent* of strategy selection, not a strategy
  itself.  The platform routes low-MAAS patients to attention-
  training tools BEFORE strategy training.
- **SCS-SF (Sprint 57)** — MAAS and the SCS-SF mindfulness
  subscale (items 3, 7) are correlated but distinct — MAAS
  captures the attentional component; SCS-SF mindfulness
  captures non-reactive acceptance of thought content.  Neff &
  Germer 2013 treat them as complementary facets; the platform
  surfaces both.
- **PSS-10 (perceived stress)** — MAAS buffers perceived stress
  prospectively (Brown 2003 Study 4 diary; Weinstein, Brown &
  Ryan 2009).  Low MAAS × high PSS-10 signals a patient whose
  stress is accumulating with no moment-to-moment release
  mechanism.

Instrument structure (Brown & Ryan 2003 Study 1 EFA, Carlson &
Brown 2005 CFA confirmation):

**15 items, each on a 6-point Likert scale** scored:
    1 = almost always
    2 = very frequently
    3 = somewhat frequently
    4 = somewhat infrequently
    5 = very infrequently
    6 = almost never

**All 15 items are worded in the MINDLESSNESS direction.**  For
example:
    "I could be experiencing some emotion and not be conscious of
     it until some time later."
    "I find myself doing things without paying attention."
    "I rush through activities without being really attentive to
     them."

Because every item is phrased as "I am NOT attending", and the
Likert anchors run from "almost always [mindless]" (1) to "almost
never [mindless]" (6), the **native direction of the total score is
already higher = more mindful**.  No flip-arithmetic / reverse-
keying is required at the scorer level — the item wording and the
Likert anchoring jointly produce the interpretable direction.  This
is a distinguishing design choice from SCS-SF (which has 6 reverse
items) and TAS-20 (5 reverse items), and is shared with ERQ (no
reverse items, all direction-aligned).

**Single factor (unidimensional).**  Brown & Ryan 2003 Study 1 EFA
extracted a single factor accounting for 30–35% of variance across
student / community / cancer-patient samples; Carlson & Brown 2005
CFA confirmed single-factor structure; MacKillop & Anderson 2007
provided IRT confirmation.  Subsequent work has tested competing
multi-factor models but the empirical consensus (as summarized in
Park, Reilly-Spong & Gross 2013 systematic review) is that the
MAAS is unidimensional in its validated form, distinguishing it
from the FFMQ / KIMS which are multi-facet by design.

The platform therefore emits NO subscale fields on the MAAS
envelope — this is the first 15+ item instrument shipped with a
continuous-sentinel envelope and no subscale map.  (Prior
unidimensional-continuous instruments — PSWQ 16, CD-RISC-10 10,
K6 6, BRS 6, DTCQ-8 8 — follow the same envelope but at smaller
item counts.)

**Scoring convention**: Brown & Ryan 2003 report the MAAS as the
MEAN of the 15 items (1.0–6.0 metric).  The platform stores the
SUM (15–90) on the wire for integer auditability, uniform with the
DERS-16 / ERQ / RRS-10 / SCS-SF / TAS-20 subscaled instruments.
Downstream renderers divide by 15 to recover the mean-metric value
when comparing against the published Brown 2003 descriptive bands.
The sum-vs-mean choice is a wire-shape decision (integer storage
for HMAC-chained audit records), not a psychometric decision;
scoring fidelity is identical.

**No published severity bands.**  Brown & Ryan 2003 and every
subsequent major validation (Carlson 2005, MacKillop 2007,
Christopher 2009 factor invariance, Park 2013 systematic review)
report MAAS as a dispositional continuous measure.  Descriptive
"low / moderate / high" ranges appear in the literature (e.g.,
Carmody 2008 reports mean ≈ 3.8 pre-intervention, ≈ 4.3 post-
intervention in MBSR samples; Brown 2003 Study 3 community mean
≈ 4.1, SD 0.7) but these are sample-dependent descriptive
comparisons, not validated severity cutoffs.  Hand-rolling a
cutoff from descriptive ranges would violate CLAUDE.md's "Don't
hand-roll severity thresholds" rule.  The router emits
``severity="continuous"`` (continuous-sentinel) and leaves
clinical interpretation to the clinician-facing trajectory view
(trend over repeated administration is the primary clinical
signal for mindfulness change; Brown 2003 Study 4 8-day diary
established within-person variability as the meaningful signal).

Higher-is-better direction (uniform with WHO-5, CD-RISC-10, LOT-R,
DTCQ-8, BRS, SCS-SF total).  This is the directional signature of
a *capacity / resource* instrument rather than a *pathology*
instrument.

Safety routing:
- MAAS has NO safety item.  It does not screen for suicidality,
  self-harm, or acute risk.  The 15 items probe attentional
  default-mode patterns; none probe imminent-harm content.
- Safety routing stays with C-SSRS, PHQ-9 item 9, PCL-5, OCIR.
  ``requires_t3`` is hard-coded ``False`` at the router.

References:
- Brown KW, Ryan RM (2003).  *The benefits of being present:
  Mindfulness and its role in psychological well-being.*  Journal
  of Personality and Social Psychology 84(4):822-848.  (PRIMARY
  validation — Study 1 EFA / item selection; Study 2 convergent/
  discriminant validity; Study 3 clinical-sample MAAS × distress;
  Study 4 experience-sampling within-person variability; Study 5
  cancer-patient pre-post MBSR intervention sensitivity.)
- Carlson LE, Brown KW (2005).  *Validation of the Mindful
  Attention Awareness Scale in a cancer population.*  Journal
  of Psychosomatic Research 58(1):29-33.  (CFA confirmation of
  single-factor structure; clinical-population validation.)
- MacKillop J, Anderson EJ (2007).  *Further psychometric
  validation of the Mindful Attention Awareness Scale (MAAS).*
  Journal of Psychopathology and Behavioral Assessment 29(4):
  289-293.  (IRT single-factor confirmation; measurement
  invariance across age / gender.)
- Christopher MS, Charoensuk S, Gilbert BD, Neary TJ, Pearce KL
  (2009).  *Mindfulness in Thailand and the United States: A
  case of apples versus oranges?*  Journal of Clinical Psychology
  65(6):590-612.  (Cross-cultural factor invariance.)
- Park T, Reilly-Spong M, Gross CR (2013).  *Mindfulness: A
  systematic review of instruments to measure an emergent
  patient-reported outcome (PRO).*  Quality of Life Research
  22(10):2639-2659.  (Systematic review — MAAS as most
  frequently validated single-facet mindfulness measure.)
- Brown KW, Ryan RM, Creswell JD (2007).  *Mindfulness:
  Theoretical foundations and evidence for its salutary
  effects.*  Psychological Inquiry 18(4):211-237.  (Theoretical
  framework — attentional mindfulness as a self-regulatory
  resource.)
- Weinstein N, Brown KW, Ryan RM (2009).  *A multi-method
  examination of the effects of mindfulness on stress
  attribution, coping, and emotional well-being.*  Journal of
  Research in Personality 43(3):374-385.  (MAAS × stress
  appraisal / coping — the mechanism by which mindful attention
  buffers stress reactivity.)
- Bowen S, Chawla N, Marlatt GA (2010).  *Mindfulness-Based
  Relapse Prevention for Addictive Behaviors: A Clinician's
  Guide.*  Guilford Press.  (MBRP manual — MAAS as primary
  trait-mindfulness outcome.)
- Bowen S et al. (2014).  *Relative efficacy of mindfulness-based
  relapse prevention, standard relapse prevention, and treatment
  as usual for substance use disorders: A randomized clinical
  trial.*  JAMA Psychiatry 71(5):547-556.  (RCT evidence for
  MBRP efficacy; MAAS as secondary outcome.)
- Carmody J, Baer RA (2008).  *Relationships between mindfulness
  practice and levels of mindfulness, medical and psychological
  symptoms and well-being in a mindfulness-based stress
  reduction program.*  Journal of Behavioral Medicine 31(1):
  23-33.  (MBSR pre-post MAAS change ≈ 0.5 SD; sensitivity-to-
  change benchmark.)
- Jermann F et al. (2009).  *Mindful Attention Awareness Scale
  (MAAS): Psychometric properties of the French translation
  and exploration of its relations with emotion regulation
  strategies.*  Psychological Assessment 21(4):506-514.
  (French-language validation; MAAS × suppression × reappraisal
  correlation matrix establishing MAAS as antecedent to strategy
  choice.)
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

INSTRUMENT_VERSION = "maas-1.0.0"
ITEM_COUNT = 15
ITEM_MIN = 1
ITEM_MAX = 6


class InvalidResponseError(ValueError):
    """Raised on item-count, item-range, or item-type violations."""


@dataclass(frozen=True)
class MaasResult:
    """Typed MAAS output.

    Fields:
    - ``total``: 15-90, the straight sum of the 15 Likert items.
      Minimum 15 because every item's lowest response value is 1
      ("almost always [mindless]"), not 0 — uniform with ERQ /
      TAS-20 / DERS-16 / RRS-10 / SCS-SF floor semantics.  Higher
      total indicates MORE mindful attention (the direction is
      produced by the combination of mindlessness-direction item
      wording × 1-to-6 Likert anchoring; no flip arithmetic
      required).
    - ``items``: verbatim 15-tuple input, pinned for auditability.

    Deliberately-absent fields:
    - No ``severity`` field — Brown & Ryan 2003 published no
      bands; MAAS is a continuous dimensional measure.  The
      router envelope emits ``severity="continuous"`` (continuous-
      sentinel) — uniform with DERS-16 / ERQ / BRS / PSWQ / SDS /
      K6 / SCS-SF / RRS-10.
    - No ``subscales`` — Brown & Ryan 2003 / Carlson & Brown 2005
      / MacKillop & Anderson 2007 confirmed single-factor
      (unidimensional) structure.  Surfacing a subscale map on
      the wire would be a psychometric fabrication.
    - No ``cutoff_used`` / ``positive_screen`` — continuous
      instrument, no cutoff shape.
    - No ``requires_t3`` field — MAAS has no safety item.
    """

    total: int
    items: tuple[int, ...]
    instrument_version: str = INSTRUMENT_VERSION


def _validate_item(index_1: int, value: object) -> int:
    """Validate a single 1-6 Likert item and return the int value.

    ``index_1`` is the 1-indexed item number (1-15) so error
    messages name the item a clinician would recognize from the
    MAAS document.
    """
    # Bool rejection — uniform with the rest of the psychometric package.
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidResponseError(
            f"MAAS item {index_1} must be int, got {value!r}"
        )
    if value < ITEM_MIN or value > ITEM_MAX:
        raise InvalidResponseError(
            f"MAAS item {index_1} out of range "
            f"[{ITEM_MIN}, {ITEM_MAX}]: {value}"
        )
    return value


def score_maas(raw_items: Sequence[int]) -> MaasResult:
    """Score a MAAS response set.

    Inputs:
    - ``raw_items``: 15 items, each 1-6 Likert (1 = "almost always
      [mindless]", 6 = "almost never [mindless]").  All items are
      worded in the mindlessness direction; the anchoring gives
      higher total = more mindful attention automatically.  No
      reverse-keying flip at the scorer layer.

    Raises :class:`InvalidResponseError` on:
    - Wrong number of items (must be exactly 15).
    - A non-int / bool item value.
    - An item outside ``[1, 6]``.

    Computes:
    - Total (15-90).

    No severity band is emitted — see module docstring.
    No subscales are emitted — unidimensional construct.
    """
    if len(raw_items) != ITEM_COUNT:
        raise InvalidResponseError(
            f"MAAS requires exactly {ITEM_COUNT} items, got {len(raw_items)}"
        )
    items = tuple(
        _validate_item(index_1=i + 1, value=v)
        for i, v in enumerate(raw_items)
    )
    total = sum(items)

    return MaasResult(total=total, items=items)


__all__ = [
    "INSTRUMENT_VERSION",
    "ITEM_COUNT",
    "ITEM_MAX",
    "ITEM_MIN",
    "InvalidResponseError",
    "MaasResult",
    "score_maas",
]

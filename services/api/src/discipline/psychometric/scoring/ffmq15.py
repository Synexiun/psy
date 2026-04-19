"""FFMQ-15 — Five-Facet Mindfulness Questionnaire, Short Form.

The Five-Facet Mindfulness Questionnaire (FFMQ) was developed by
Baer, Smith, Hopkins, Krietemeyer & Toney (2006 Assessment 13(1):
27-45) as a 39-item integration of five previously-distinct
mindfulness measures (Mindful Attention Awareness Scale, Kentucky
Inventory of Mindfulness Skills, Freiburg Mindfulness Inventory,
Cognitive and Affective Mindfulness Scale - Revised, Southampton
Mindfulness Questionnaire).  Exploratory and confirmatory factor
analysis of the pooled item pool (n = 613 undergraduates + n =
268 meditators) produced a five-facet structure that replicated
across multiple subsequent samples and has become the most
widely-used model of trait mindfulness.  The FFMQ-15 short form
(15 items, 3 per facet) was derived by Gu, Strauss, Crane, Barnhofer,
Karl, Cavanagh & Kuyken (2016 Psychological Assessment 28(7):791-
802) via item-response-theory analysis on n = 2,876 participants
across five clinical and non-clinical samples, selecting the 3
highest-discriminating items per facet while preserving the five-
factor structure of Baer 2006.

Clinical relevance to the Discipline OS platform:

FFMQ-15 provides the platform's **facet-decomposition of
mindfulness** — extending the single-factor MAAS (Brown & Ryan
2003) with a five-dimensional breakdown.  Where MAAS gives ONE
mindfulness total (present-moment awareness), FFMQ-15 gives five
independently-interpretable sub-dimensions:

1. **Observing** — attention to internal and external experiences
   (sensations, perceptions, thoughts, feelings).  This facet
   shows the most complex relationship with clinical outcomes;
   Baer 2008 demonstrated that in non-meditators, HIGH observing
   can correlate with POSITIVE symptoms (heightened awareness
   without regulatory skill), but in meditators the correlation
   inverts — observing becomes protective once paired with the
   other facets.  Clinically, this means observing should be
   interpreted in CONTEXT of the other four facets, never alone.
2. **Describing** — ability to label internal experiences with
   words.  Linked to emotional granularity (Kashdan 2015) and
   alexithymia (Baer 2006 reported r = -0.59 with TAS-20).
   Low describing + high negative affect is the alexithymia-
   distress signature.  Describing is a prerequisite for
   cognitive-behavioral restructuring — patients cannot
   challenge thoughts they cannot articulate.
3. **Acting with awareness** — engaged attention to present-
   moment activity (opposite: automatic-pilot, distraction).
   The facet most directly implicated in cue-reactivity and
   relapse: automatic-pilot operation is how a patient in
   recovery finds themselves mid-behavior before the urge
   becomes conscious.  Bowen 2014 Mindfulness-Based Relapse
   Prevention §3.2 targets this facet as the primary lever —
   interrupting the automatic-pilot loop is the behavioral
   mechanism of MBRP's effect.
4. **Non-judging of inner experience** — not evaluating thoughts
   and feelings as good / bad, right / wrong.  The facet most
   strongly inversely correlated with depression (Baer 2008
   r = -0.54 with BDI).  The Marlatt 1985 abstinence-violation-
   effect loop (low self-esteem -> relapse -> shame -> further
   low self-esteem) is fundamentally a NON-JUDGING FAILURE —
   the patient evaluates their inner experience and finds it
   unacceptable, triggering the AVE cascade.  Non-judging is
   the protective factor against AVE; Neff 2003 self-
   compassion overlaps heavily with this facet (r ~ 0.59 per
   Baer 2006).
5. **Non-reactivity to inner experience** — allowing thoughts
   and feelings to arise and pass without getting caught up
   in them.  Target of acceptance-based interventions (Hayes
   2012 ACT §6; Segal 2013 MBCT §4).  Low non-reactivity is
   the cognitive-fusion signature — thoughts feel like facts
   rather than passing mental events.  Clinically, non-
   reactivity is the hardest facet to change; it requires
   sustained practice rather than insight.

The five-facet decomposition is **clinically load-bearing** for
the Discipline OS intervention-matching engine.  A MAAS total
tells you a patient has mindfulness impairment; a FFMQ-15 facet
profile tells you WHICH impairment, and therefore which
intervention:

- Low observing -> body-scan / sensory-grounding work (Kabat-
  Zinn 1990 §2).
- Low describing -> emotion-labeling / affect-literacy skills
  (linguistically-scaffolded exposure per Kircanski 2012).
- Low acting-with-awareness -> Mindfulness-Based Relapse
  Prevention urge-surfing and automatic-pilot-interruption
  (Bowen 2014 §3.2).
- Low non-judging -> self-compassion-based work (Neff 2011;
  Gilbert 2010 CFT).  Same lever as low RSES; mutually
  reinforcing.
- Low non-reactivity -> acceptance and defusion (Hayes 2012
  ACT).

This means FFMQ-15 is the FIRST PLATFORM INSTRUMENT whose
subscales directly map to five independent intervention tools.
PANAS-10 (Sprint 65) introduced the bidirectional-subscales
envelope (PA + NA).  FFMQ-15 extends this to **penta-subscales**
— the first five-subscale instrument on the platform.

Scoring:

- 15 items, 5-point Likert (1 = "never or very rarely true", 2 =
  "rarely true", 3 = "sometimes true", 4 = "often true", 5 = "very
  often or always true"), 3 items per facet.
- Reverse-keying: items 6, 7, 8, 9, 10, 11, 12 (7 items).  The
  describing facet has one reverse item (position 6, "It's hard
  for me to find the words to describe what I'm thinking").  The
  acting-with-awareness facet is entirely reverse-keyed (positions
  7, 8, 9 — "I rush through activities without being really
  attentive to them", "I do jobs or tasks automatically without
  being aware of what I'm doing", "I find myself doing things
  without paying attention").  The non-judging facet is entirely
  reverse-keyed (positions 10, 11, 12 — "I criticize myself for
  having irrational or inappropriate emotions", "I think some of
  my emotions are bad or inappropriate and I shouldn't feel them",
  "I tell myself I shouldn't be feeling the way I'm feeling").
  Observing (1-3) and Non-reactivity (13-15) are entirely
  positively worded.
- Flip formula: ``(ITEM_MIN + ITEM_MAX) - raw = 6 - raw``.
- Subscale totals: each 3-15 (post-flip).
- Grand total: 15-75 (post-flip sum of all 15 items).

The asymmetric positive / reverse split (9 positive + 6 reverse
— wait, 9 positive + 6 reverse in the 15-item form; describing
has 1 reverse so 2 positive describing items; acting 3 reverse;
non-judging 3 reverse; observing 3 positive; non-reactivity 3
positive; = 9 positive + 6 reverse when describing's reverse is
the one item 6).

Actually counting: positions 1, 2, 3, 4, 5 positive (observing +
2 describing) = 5 positive; 6 reverse (describing); 7, 8, 9
reverse (acting) = 3 reverse; 10, 11, 12 reverse (non-judging) =
3 reverse; 13, 14, 15 positive (non-reactivity) = 3 positive.
Total: 8 positive + 7 reverse.

Acquiescence-bias control (Marsh 1996 / Baer 2006 §3.4):

All-raw-1: positives = 8×1 = 8; reverses post-flip = 7×(6-1) = 35;
total 43.  All-raw-5: positives = 40; reverses post-flip = 7×1 =
7; total 47.  Unlike symmetric scales (RSES / BRS / LOT-R), the
two extremes do NOT converge — because the FFMQ-15 has 8 positive
and 7 reverse items (one-off), the acquiescence extremes land at
43 and 47 respectively (separation of 4).  This is the MINIMUM
possible separation for a near-balanced 15-item instrument and
still bounds acquiescence bias tightly (< 6% of the 15-75 range).

Platform envelope (uniform with PANAS-10):

- ``total``: grand total 15-75 (post-flip sum of all items).
- ``subscales``: 5-key dict with per-facet post-flip sums.
- ``severity``: literal ``"continuous"``.  Neither Baer 2006 nor
  Gu 2016 published clinical bands — the trajectory layer
  applies Jacobson-Truax RCI per facet.
- No ``positive_screen`` / ``cutoff_used`` — FFMQ-15 is not a
  screen.
- No ``requires_t3`` — no item probes suicidality.

References:
- Baer RA, Smith GT, Hopkins J, Krietemeyer J, Toney L (2006).
  *Using self-report assessment methods to explore facets of
  mindfulness.*  Assessment 13(1):27-45.  (Canonical 39-item
  FFMQ derivation; EFA + CFA across two samples, five-factor
  solution replicated.)
- Gu J, Strauss C, Crane C, Barnhofer T, Karl A, Cavanagh K,
  Kuyken W (2016).  *Examining the factor structure of the 39-
  item and 15-item versions of the Five Facets Mindfulness
  Questionnaire before and after mindfulness-based cognitive
  therapy for people with recurrent depression.*  Psychological
  Assessment 28(7):791-802.  (FFMQ-15 IRT derivation; n = 2,876;
  item selection preserving five-factor structure.)
- Baer RA, Smith GT, Lykins E, Button D, Krietemeyer J, Sauer S,
  Walsh E, Duggan D, Williams JMG (2008).  *Construct validity
  of the Five Facet Mindfulness Questionnaire in meditating and
  nonmeditating samples.*  Assessment 15(3):329-342.  (Observing-
  facet interpretation depends on meditation experience; this
  paper established why observing must be read in context of
  other facets.)
- Bohlmeijer E, ten Klooster PM, Fledderus M, Veehof M, Baer R
  (2011).  *Psychometric properties of the Five Facet Mindfulness
  Questionnaire in depressed adults and development of a short
  form.*  Assessment 18(3):308-320.  (FFMQ-SF-24 Dutch short form;
  methodological template for the later 15-item version;
  confirmed five-facet structure in clinical depression sample.)
- Brown KW, Ryan RM (2003).  *The benefits of being present:
  Mindfulness and its role in psychological well-being.*  Journal
  of Personality and Social Psychology 84(4):822-848.  (Single-
  factor MAAS derivation; the platform's single-facet mindfulness
  instrument — FFMQ-15 is the five-facet complement.)
- Kabat-Zinn J (1990).  *Full Catastrophe Living: Using the Wisdom
  of Your Body and Mind to Face Stress, Pain, and Illness.*
  Delacorte.  (MBSR; observing-facet intervention template via
  body-scan.)
- Segal ZV, Williams JMG, Teasdale JD (2013).  *Mindfulness-Based
  Cognitive Therapy for Depression, 2nd Ed.*  Guilford Press.
  (MBCT; non-reactivity and non-judging facet interventions.)
- Bowen S, Chawla N, Marlatt GA (2014).  *Mindfulness-Based
  Relapse Prevention for Addictive Behaviors: A Clinician's
  Guide.*  Guilford Press.  (MBRP; acting-with-awareness facet
  as the primary lever for cue-reactivity interruption — directly
  relevant to the Discipline OS product thesis.)
- Hayes SC, Strosahl KD, Wilson KG (2012).  *Acceptance and
  Commitment Therapy: The Process and Practice of Mindful Change,
  2nd Ed.*  Guilford Press.  (ACT; non-reactivity facet as the
  cognitive-fusion / defusion target.)
- Neff KD (2003).  *Self-compassion: An alternative
  conceptualization of a healthy attitude toward oneself.*  Self
  and Identity 2(2):85-101.  (Self-compassion construct; heavy
  conceptual overlap with non-judging facet — per Baer 2006
  r ~ 0.59.)
- Kashdan TB, Barrett LF, McKnight PE (2015).  *Unpacking emotion
  differentiation: Transforming unevenness in experience into
  meaningful distinctions.*  Current Directions in Psychological
  Science 24(1):10-16.  (Emotional granularity; cognitive
  complement to the describing facet.)
- Marsh HW (1996).  *Positive and negative global self-esteem: A
  substantively meaningful distinction or artifactors?*  Journal
  of Personality and Social Psychology 70(4):810-819.
  (Acquiescence-bias framework inherited from the RSES wiring;
  applied here to the asymmetric 8/7 positive/reverse split.)
- Jacobson NS, Truax P (1991).  *Clinical significance: A
  statistical approach to defining meaningful change in
  psychotherapy research.*  Journal of Consulting and Clinical
  Psychology 59(1):12-19.  (RCI applied to per-facet scores in
  the trajectory layer, not at this scorer level.)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence

INSTRUMENT_VERSION = "ffmq15-1.0.0"
ITEM_COUNT = 15
ITEM_MIN, ITEM_MAX = 1, 5


# Baer 2006 / Gu 2016 five-facet mapping (1-indexed).  The item
# order is CONTIGUOUS by facet (3 consecutive items per facet) —
# this is the Bohlmeijer 2011 administration template, chosen
# over interleaved orderings for simpler clinician review and
# self-report introspection.  Changing these tuples invalidates
# the Baer 2006 / Gu 2016 factor structure.
FFMQ15_OBSERVING_POSITIONS: tuple[int, ...] = (1, 2, 3)
FFMQ15_DESCRIBING_POSITIONS: tuple[int, ...] = (4, 5, 6)
FFMQ15_ACTING_POSITIONS: tuple[int, ...] = (7, 8, 9)
FFMQ15_NONJUDGING_POSITIONS: tuple[int, ...] = (10, 11, 12)
FFMQ15_NONREACTIVITY_POSITIONS: tuple[int, ...] = (13, 14, 15)


# Baer 2006 reverse-keyed items (1-indexed).  Describing has ONE
# reverse item at position 6 ("It's hard for me to find the words
# to describe what I'm thinking").  Acting-with-awareness is
# ENTIRELY reverse-keyed at positions 7, 8, 9 (Bohlmeijer 2011
# §3.2 — every acting-with-awareness item is phrased as an
# automatic-pilot failure).  Non-judging is ENTIRELY reverse-
# keyed at positions 10, 11, 12 (every non-judging item is
# phrased as a judgmental thought — "I criticize myself...", "I
# think some of my emotions are bad...", "I tell myself I
# shouldn't be feeling...").  Observing (1-3) and Non-reactivity
# (13-15) are entirely positively worded.
FFMQ15_REVERSE_ITEMS: tuple[int, ...] = (6, 7, 8, 9, 10, 11, 12)


# Subscale-name constants used in the wire subscales dict.
# Exported so clinician-UI renderers key off one source of truth.
FFMQ15_SUBSCALES: tuple[str, ...] = (
    "observing",
    "describing",
    "acting_with_awareness",
    "non_judging",
    "non_reactivity",
)


class InvalidResponseError(ValueError):
    """Raised on item-count, item-range, or item-type violations."""


Severity = Literal["continuous"]


@dataclass(frozen=True)
class Ffmq15Result:
    """Typed FFMQ-15 output.

    Fields:
    - ``total``: 15-75 sum of post-flip item values.  HIGHER =
      MORE mindfulness (higher-is-better direction, uniform
      with WHO-5 / BRS / PANAS-10 PA / LOT-R / MAAS / CD-RISC-10
      / RSES).
    - ``observing_sum``, ``describing_sum``, ``acting_sum``,
      ``nonjudging_sum``, ``nonreactivity_sum``: per-facet 3-15
      post-flip sums.  These are the **clinically load-bearing**
      outputs — the grand total is a summary for trajectory
      tracking, but intervention matching routes on the facet
      profile (see module docstring §"Scoring").
    - ``severity``: literal ``"continuous"`` sentinel.  Baer
      2006 and Gu 2016 did not publish clinical cutpoints at
      either the grand-total or facet level.
    - ``items``: verbatim 15-tuple of RAW pre-flip 1-5
      responses in Bohlmeijer 2011 administration order
      (3-items-per-facet contiguous).  Raw preserved for audit
      invariance and FHIR R4 export per platform convention
      (TAS-20 / PSWQ / LOT-R / BRS / RSES).

    Deliberately-absent fields:
    - No ``positive_screen`` / ``cutoff_used`` — FFMQ-15 is not
      a screen.
    - No ``requires_t3`` — no item probes suicidality.  Non-
      judging items (10-12) mention "my emotions are bad" but
      are self-evaluative, NOT ideation — the clinical content
      is shame / self-criticism, which flows to RSES-linked
      AVE-substrate concerns, not to acute-risk handling.
      C-SSRS / PHQ-9 item 9 remain the T3 sources.
    """

    total: int
    severity: Severity
    observing_sum: int
    describing_sum: int
    acting_sum: int
    nonjudging_sum: int
    nonreactivity_sum: int
    items: tuple[int, ...]
    instrument_version: str = INSTRUMENT_VERSION


def _validate_item(index_1: int, value: object) -> int:
    """Validate a single 1-5 Likert item.

    Bool rejection per CLAUDE.md standing rule: ``bool`` values
    are rejected before the int check because Python's
    ``bool is int`` coercion would silently accept ``True`` /
    ``False`` as item responses.
    """
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidResponseError(
            f"FFMQ-15 item {index_1} must be int, got {value!r}"
        )
    if not (ITEM_MIN <= value <= ITEM_MAX):
        raise InvalidResponseError(
            f"FFMQ-15 item {index_1} must be in {ITEM_MIN}-{ITEM_MAX}, "
            f"got {value}"
        )
    return value


def _apply_reverse_keying(
    raw_items: tuple[int, ...], reverse_positions_1: tuple[int, ...]
) -> tuple[int, ...]:
    """Return a new tuple with reverse-keyed positions flipped via
    ``(ITEM_MIN + ITEM_MAX) - raw``.  Non-reverse positions are
    copied unchanged.  Operates on 1-indexed positions for
    consistency with the clinical-literature convention."""
    reverse_set = frozenset(reverse_positions_1)
    flipped: list[int] = []
    for i, raw in enumerate(raw_items):
        position_1 = i + 1
        if position_1 in reverse_set:
            flipped.append((ITEM_MIN + ITEM_MAX) - raw)
        else:
            flipped.append(raw)
    return tuple(flipped)


def _subscale_sum(
    post_flip_items: tuple[int, ...], positions_1: tuple[int, ...]
) -> int:
    """Sum POST-FLIP items at the given 1-indexed positions."""
    return sum(post_flip_items[pos - 1] for pos in positions_1)


def score_ffmq15(raw_items: Sequence[int]) -> Ffmq15Result:
    """Score a FFMQ-15 response set.

    Inputs:
    - ``raw_items``: 15 items, each 1-5 Likert (1 = "never or
      very rarely true", 5 = "very often or always true"), in
      Bohlmeijer 2011 contiguous-facet administration order:
        1-3.   Observing
        4-6.   Describing (position 6 reverse-keyed)
        7-9.   Acting with awareness (all reverse-keyed)
        10-12. Non-judging (all reverse-keyed)
        13-15. Non-reactivity

    Raises :class:`InvalidResponseError` on:
    - Wrong number of items (must be exactly 15).
    - A non-int / bool item value.
    - An item outside ``[1, 5]``.

    Computes:
    - Per-facet post-flip sums (each 3-15).
    - Grand total as sum of the five facet sums (15-75).
    - ``items`` preserves RAW pre-flip for audit.

    Changing ``FFMQ15_REVERSE_ITEMS`` or any facet position-tuple
    invalidates the Baer 2006 / Gu 2016 factor structure and
    breaks published norms.
    """
    if len(raw_items) != ITEM_COUNT:
        raise InvalidResponseError(
            f"FFMQ-15 requires exactly {ITEM_COUNT} items, "
            f"got {len(raw_items)}"
        )
    raw = tuple(
        _validate_item(index_1=i + 1, value=v)
        for i, v in enumerate(raw_items)
    )

    post_flip = _apply_reverse_keying(raw, FFMQ15_REVERSE_ITEMS)

    observing_sum = _subscale_sum(post_flip, FFMQ15_OBSERVING_POSITIONS)
    describing_sum = _subscale_sum(post_flip, FFMQ15_DESCRIBING_POSITIONS)
    acting_sum = _subscale_sum(post_flip, FFMQ15_ACTING_POSITIONS)
    nonjudging_sum = _subscale_sum(post_flip, FFMQ15_NONJUDGING_POSITIONS)
    nonreactivity_sum = _subscale_sum(
        post_flip, FFMQ15_NONREACTIVITY_POSITIONS
    )

    total = (
        observing_sum
        + describing_sum
        + acting_sum
        + nonjudging_sum
        + nonreactivity_sum
    )

    return Ffmq15Result(
        total=total,
        severity="continuous",
        observing_sum=observing_sum,
        describing_sum=describing_sum,
        acting_sum=acting_sum,
        nonjudging_sum=nonjudging_sum,
        nonreactivity_sum=nonreactivity_sum,
        items=raw,
    )


__all__ = [
    "FFMQ15_ACTING_POSITIONS",
    "FFMQ15_DESCRIBING_POSITIONS",
    "FFMQ15_NONJUDGING_POSITIONS",
    "FFMQ15_NONREACTIVITY_POSITIONS",
    "FFMQ15_OBSERVING_POSITIONS",
    "FFMQ15_REVERSE_ITEMS",
    "FFMQ15_SUBSCALES",
    "Ffmq15Result",
    "INSTRUMENT_VERSION",
    "ITEM_COUNT",
    "ITEM_MAX",
    "ITEM_MIN",
    "InvalidResponseError",
    "Severity",
    "score_ffmq15",
]

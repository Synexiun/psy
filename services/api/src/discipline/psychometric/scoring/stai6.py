"""STAI-6 — State-Trait Anxiety Inventory Short Form (Marteau & Bekker 1992).

The 6-item State-Trait Anxiety Inventory short form is the brief
derivation of the state-anxiety subscale of the full 20-item
STAI (Spielberger, Gorsuch, Lushene, Vagg & Jacobs 1983 Consulting
Psychologists Press).  Theresa M. Marteau and Hilary Bekker
derived the 6-item form in n = 200 participants (Marteau & Bekker
1992 British Journal of Clinical Psychology 31:301-306,
"Development of a six-item short form of the state scale of the
Spielberger State-Trait Anxiety Inventory"), demonstrating
equivalence to the full 20-item scale (r = 0.94 with full STAI-S)
across a patient-preparation-for-surgery design.  The STAI-6 has
since been validated across obstetric (Cowdery 2000), oncology
(Balsamo 2014), anxiety-disorder (van Knippenberg 1990), and
general-population (Tluczek 2009) samples.  It is the briefest
validated state-anxiety instrument in wide clinical use.

Clinical relevance to the Discipline OS platform:

STAI-6 fills the platform's **state-vs-trait anxiety distinction
gap**.  The existing anxiety coverage is trait-anchored:

- GAD-7 (Spitzer 2006): "over the last 2 weeks" — a 14-day
  trait-ish window; measures persistent anxiety severity.
- GAD-2 (Kroenke 2007): same 2-week window; 2-item screen.
- OASIS (Norman 2006): "in the last week" — a 7-day window;
  overall anxiety severity and impairment.
- AAQ-II (Bond 2011): experiential-avoidance trait; no temporal
  anchor (measures general tendency).
- PSWQ (Meyer 1990): pathological worry tendency; general trait.

None measure **momentary state anxiety** — the here-and-now
experience of anxious activation that Spielberger's (1966, 1983)
seminal state / trait distinction isolated.  State anxiety is
transient, situation-dependent, and FLUCTUATES moment-to-moment;
trait anxiety is a stable disposition.  The clinical difference
is mechanistically central:

1. **Pre / post intervention-session effect measurement.**  A
   behavioral-activation or exposure session is expected to
   REDUCE state anxiety immediately post-session.  Measuring
   this effect with GAD-7 would fail — GAD-7's 14-day window
   averages across the session, making a single-session effect
   invisible.  STAI-6 is the correct instrument: administer
   pre-session, administer post-session, compute the RCI
   delta, and the trajectory layer has an objective
   within-session-effect metric.  This is the canonical
   efficacy-measurement use case for the Discipline OS
   intervention engine.
2. **Trigger-vs-baseline detection.**  The platform's cue-
   reactivity pipeline expects state anxiety to SPIKE in
   response to trigger stimuli (location, people, emotional
   state).  STAI-6 at baseline and after a naturalistic
   trigger-exposure discriminates reactive-profile patients
   from chronically-anxious patients — the former are
   treatment targets for exposure-based work (Craske 2014),
   the latter for generalized-anxiety protocols (Dugas 2010).
3. **Relapse-risk gating.**  Marlatt 1985 identified elevated
   state anxiety as a PROXIMAL relapse precipitant (pp. 137-
   142 — "negative emotional states" as the most common
   relapse determinant in a sample of 137 relapses).  A STAI-6
   spike in the hour before a reported craving episode is a
   predictive signal that feeds the intervention-bandit
   policy.

Scoring:

- 6 items, 4-point Likert (1 = "not at all", 2 = "somewhat",
  3 = "moderately so", 4 = "very much so") anchored to the
  present moment ("Indicate how you feel right now, at this
  moment").
- Items (Marteau & Bekker 1992 Table 1):
    1. I feel calm       (positive, REVERSE-keyed)
    2. I am tense         (negative)
    3. I feel upset       (negative)
    4. I am relaxed       (positive, REVERSE-keyed)
    5. I feel content     (positive, REVERSE-keyed)
    6. I am worried       (negative)
- Post-flip = (ITEM_MIN + ITEM_MAX) - raw = 5 - raw at positions
  1, 4, 5.  Non-reverse positions (2, 3, 6) pass through raw.
- Total: sum of post-flip items, range 6-24.  HIGHER = more
  anxious (lower-is-better direction — OPPOSITE of WHO-5 /
  BRS / RSES / FFMQ-15 / MAAS / LOT-R; SAME as PHQ-9 / GAD-7 /
  AUDIT / PSS-10 / PGSI).
- Marteau & Bekker 1992 §2.3 recommended a scaled score of
  (total × 20) / 6, giving a 20-80 range comparable to the
  full 20-item STAI state subscale.  The platform does NOT
  emit this scaled score: (1) it is a non-integer for most
  inputs, requiring floating-point rendering that breaks the
  CLAUDE.md Latin-digits-always policy edge case; (2) Jacobson-
  Truax RCI at the trajectory layer works on the raw total
  directly without requiring the scaled score; (3) secondary
  literature (Kvaal 2005, Balsamo 2014) is divided on whether
  clinical cutpoints should be applied to scaled or raw
  totals.  Clinicians reading STAI-6 totals on this platform
  read the raw 6-24 sum; the trajectory layer computes delta
  and clinical-significance via RCI, not via absolute bands.

No severity bands:

Marteau & Bekker 1992 did NOT publish clinical cutpoints.
Spielberger 1983 STAI manual did not publish definitive bands
for the state subscale either; the widely-cited "≥ 40 = clinical
anxiety" threshold is Kvaal 2005's secondary-literature cutoff
(validated against HADS), not a derivation-source anchor.
Per CLAUDE.md "no hand-rolled severity thresholds" rule, the
platform emits severity="continuous" and lets the trajectory
layer apply Jacobson-Truax RCI for clinical-significance
determination.  Hand-rolling bands here would violate the rule.

No T3 gating:

STAI-6 has NO ideation item.  The six items probe calm / tense /
upset / relaxed / content / worried — all state-affect descriptors.
"Upset" (item 3) is general distress, NOT suicidality.  Acute-
risk screening stays on C-SSRS / PHQ-9 item 9.

References:
- Marteau TM, Bekker H (1992).  *The development of a six-item
  short-form of the state scale of the Spielberger State-Trait
  Anxiety Inventory (STAI).*  British Journal of Clinical
  Psychology 31(3):301-306.  (Canonical 6-item derivation;
  n = 200 pre-surgical patients; r = 0.94 with full STAI-S.)
- Spielberger CD, Gorsuch RL, Lushene R, Vagg PR, Jacobs GA
  (1983).  *Manual for the State-Trait Anxiety Inventory
  (Form Y).*  Consulting Psychologists Press, Palo Alto CA.
  (Canonical full 20-item STAI manual; state / trait
  distinction; item derivation and psychometric reference.)
- Spielberger CD (1966).  *Anxiety and Behavior.*  Academic
  Press, New York.  (Original state / trait anxiety theoretical
  framework — anxiety as a transient emotional response to a
  specific situation vs. a stable disposition.)
- Cowdery KH, Knapp H (2000).  *Validation of the short-form
  STAI in obstetric patients.*  Journal of Reproductive and
  Infant Psychology 18(3):237-240.  (Obstetric-sample
  validation; r = 0.92 with full STAI-S.)
- Balsamo M, Romanelli R, Innamorati M, Ciccarese G, Carlucci
  L, Saggino A (2014).  *The State-Trait Anxiety Inventory:
  Shadows and lights on its construct validity.*  Journal of
  Psychopathology and Behavioral Assessment 36(4):577-585.
  (Oncology-sample validation; discussion of STAI-S
  psychometric strengths and limitations.)
- van Knippenberg FCE, Duivenvoorden HJ, Bonke B, Passchier J
  (1990).  *Shortening the State-Trait Anxiety Inventory.*
  Journal of Clinical Epidemiology 43(9):995-1000.  (Earlier
  short-form derivation; 4-item version subsequently superseded
  by Marteau & Bekker 1992's 6-item form.)
- Tluczek A, Henriques JB, Brown RL (2009).  *Support for the
  reliability and validity of a six-item state anxiety scale
  derived from the State-Trait Anxiety Inventory.*  Journal
  of Nursing Measurement 17(1):19-28.  (General-population
  validation; confirmed factor structure equivalent to the
  full STAI-S single-factor model.)
- Kvaal K, Ulstein I, Nordhus IH, Engedal K (2005).  *The
  Spielberger State-Trait Anxiety Inventory (STAI): The state
  scale in detecting mental disorders in geriatric patients.*
  International Journal of Geriatric Psychiatry 20(7):629-
  634.  (Geriatric-sample cutoff study; ≥ 40 scaled ~=
  clinical anxiety caseness.  Secondary-literature cutpoint —
  informs clinician interpretation but not pinned as a
  platform band.)
- Marlatt GA, Gordon JR (1985).  *Relapse Prevention:
  Maintenance Strategies in the Treatment of Addictive
  Behaviors.*  Guilford Press.  (Negative emotional states
  including state anxiety as the most common proximal relapse
  determinant — pp. 137-142.  Direct clinical rationale for
  real-time state-anxiety measurement on the Discipline OS
  platform.)
- Craske MG, Treanor M, Conway CC, Zbozinek T, Vervliet B
  (2014).  *Maximizing exposure therapy: An inhibitory
  learning approach.*  Behaviour Research and Therapy 58:10-
  23.  (Exposure-therapy intervention — STAI-6 pre/post
  measurement is the canonical within-session efficacy metric.)
- Dugas MJ, Robichaud M (2010).  *Cognitive-Behavioral
  Treatment for Generalized Anxiety Disorder: From Science
  to Practice.*  Routledge.  (GAD-specific trait-anxiety
  intervention; complements STAI-6 state measurement with
  GAD-7 trait measurement.)
- Jacobson NS, Truax P (1991).  *Clinical significance: A
  statistical approach to defining meaningful change in
  psychotherapy research.*  Journal of Consulting and
  Clinical Psychology 59(1):12-19.  (RCI applied to the STAI-6
  raw total in the trajectory layer.)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence

INSTRUMENT_VERSION = "stai6-1.0.0"
ITEM_COUNT = 6
ITEM_MIN, ITEM_MAX = 1, 4


# Marteau & Bekker 1992 reverse-keyed items (1-indexed).  These
# are the three positively-worded state items: "I feel calm"
# (position 1), "I am relaxed" (position 4), "I feel content"
# (position 5).  Negative-worded items (2, 3, 6 — "I am tense",
# "I feel upset", "I am worried") pass through raw.  Post-flip
# = (ITEM_MIN + ITEM_MAX) - raw = 5 - raw.  Changing this tuple
# invalidates Marteau & Bekker 1992 factor structure and breaks
# the r = 0.94 equivalence to the full STAI-S.
STAI6_REVERSE_ITEMS: tuple[int, ...] = (1, 4, 5)


class InvalidResponseError(ValueError):
    """Raised on item-count, item-range, or item-type violations."""


Severity = Literal["continuous"]


@dataclass(frozen=True)
class Stai6Result:
    """Typed STAI-6 output.

    Fields:
    - ``total``: 6-24 sum of post-flip item values.  HIGHER =
      MORE state anxiety (lower-is-better direction — uniform
      with PHQ-9 / GAD-7 / AUDIT / PSS-10 / PGSI / SHAPS).
    - ``severity``: literal ``"continuous"`` sentinel.  Marteau
      & Bekker 1992 did not publish clinical cutpoints; the
      ≥ 40 scaled cutoff in Kvaal 2005 is secondary literature
      and not pinned here per CLAUDE.md.
    - ``items``: verbatim 6-tuple of RAW pre-flip 1-4
      responses in Marteau & Bekker 1992 administration order
      (calm, tense, upset, relaxed, content, worried).  Raw
      preserved for audit invariance.

    Deliberately-absent fields:
    - No ``scaled_score`` — Marteau 1992's (total × 20) / 6
      scaling is non-integer for most inputs and adds no
      clinical information over the raw total per §"Scoring".
    - No ``subscales`` — STAI-6 derives from the State-subscale
      of STAI; it is already a single-factor instrument.
      Spielberger 1983 did not establish sub-dimensions within
      State (which Anxiety-Present vs Anxiety-Absent was
      proposed by Spielberger 1980 as a two-factor alternative
      but not operationalized in the 6-item form).
    - No ``positive_screen`` / ``cutoff_used`` — STAI-6 is not
      a screen.
    - No ``requires_t3`` — no item probes suicidality.
    """

    total: int
    severity: Severity
    items: tuple[int, ...]
    instrument_version: str = INSTRUMENT_VERSION


def _validate_item(index_1: int, value: object) -> int:
    """Validate a single 1-4 Likert item.

    Bool rejection per CLAUDE.md standing rule: ``bool`` values
    are rejected before the int check because Python's
    ``bool is int`` coercion would silently accept ``True`` /
    ``False`` as item responses.
    """
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidResponseError(
            f"STAI-6 item {index_1} must be int, got {value!r}"
        )
    if not (ITEM_MIN <= value <= ITEM_MAX):
        raise InvalidResponseError(
            f"STAI-6 item {index_1} must be in {ITEM_MIN}-{ITEM_MAX}, "
            f"got {value}"
        )
    return value


def _apply_reverse_keying(
    raw_items: tuple[int, ...], reverse_positions_1: tuple[int, ...]
) -> tuple[int, ...]:
    """Return a new tuple with reverse-keyed positions flipped via
    ``(ITEM_MIN + ITEM_MAX) - raw``.  Non-reverse positions copy
    unchanged."""
    reverse_set = frozenset(reverse_positions_1)
    flipped: list[int] = []
    for i, raw in enumerate(raw_items):
        position_1 = i + 1
        if position_1 in reverse_set:
            flipped.append((ITEM_MIN + ITEM_MAX) - raw)
        else:
            flipped.append(raw)
    return tuple(flipped)


def score_stai6(raw_items: Sequence[int]) -> Stai6Result:
    """Score a STAI-6 response set.

    Inputs:
    - ``raw_items``: 6 items, each 1-4 Likert (1 = "not at all",
      4 = "very much so"), in Marteau & Bekker 1992
      administration order:
        1. I feel calm       (REVERSE-keyed)
        2. I am tense
        3. I feel upset
        4. I am relaxed      (REVERSE-keyed)
        5. I feel content    (REVERSE-keyed)
        6. I am worried

    Raises :class:`InvalidResponseError` on:
    - Wrong number of items (must be exactly 6).
    - A non-int / bool item value.
    - An item outside ``[1, 4]``.

    Computes:
    - Post-flip sum, range 6-24.  ``items`` preserves RAW pre-
      flip for audit and FHIR R4 export.

    Changing ``STAI6_REVERSE_ITEMS`` invalidates Marteau & Bekker
    1992 factor structure and breaks the r = 0.94 equivalence
    with the full STAI-S.
    """
    if len(raw_items) != ITEM_COUNT:
        raise InvalidResponseError(
            f"STAI-6 requires exactly {ITEM_COUNT} items, "
            f"got {len(raw_items)}"
        )
    raw = tuple(
        _validate_item(index_1=i + 1, value=v)
        for i, v in enumerate(raw_items)
    )
    post_flip = _apply_reverse_keying(raw, STAI6_REVERSE_ITEMS)
    total = sum(post_flip)

    return Stai6Result(
        total=total,
        severity="continuous",
        items=raw,
    )


__all__ = [
    "INSTRUMENT_VERSION",
    "ITEM_COUNT",
    "ITEM_MAX",
    "ITEM_MIN",
    "InvalidResponseError",
    "STAI6_REVERSE_ITEMS",
    "Severity",
    "Stai6Result",
    "score_stai6",
]

"""TAS-20 — Toronto Alexithymia Scale (Bagby, Parker & Taylor 1994).

TAS-20 is the validated 20-item self-report measure of **alexithymia** —
the trait-level difficulty identifying feelings, describing feelings to
others, and an externally-oriented cognitive style that privileges
concrete/mechanistic thinking over internal emotional experience.  The
construct literally means "no words for feelings" (from Greek *a-* +
*lexis* + *thymia*); alexithymic patients experience physiological
arousal without a clear cognitive label for the emotion driving it,
which leaves them unable to deploy the emotion-regulation strategies
that downstream therapies (DBT, CBT, ACT) all presuppose.

Clinical relevance to the Discipline OS platform:
Alexithymia is the **upstream** emotion-identification construct that
gates access to **downstream** emotion-regulation training.  A patient
who cannot identify "I am angry right now" cannot plausibly deploy a
regulation strategy targeted at anger.  The platform therefore reads
TAS-20 as an affect-labeling prerequisite check:

- DERS-16 (emotion-regulation DIFFICULTY): downstream — how well the
  patient manages an already-identified emotion.
- TAS-20 (emotion-identification DIFFICULTY): upstream — whether the
  patient can identify the emotion to begin with.

A patient with high TAS-20 AND high DERS-16 routes FIRST to affect-
labeling interventions (Taylor & Bagby 2004 recommend Emotion
Regulation Therapy with upstream emotion-identification work; DBT's
"Observe" / "Describe" mindfulness skills before the regulation
skills; CBT emotion-awareness logs before cognitive restructuring)
before DBT-style distress-tolerance / regulation training will
return benefit.  The intervention-selection layer gates the
regulation-training tools behind a TAS-20 DIF score check — if DIF
is high, upstream affect-labeling is prioritized.

Alexithymia also:
- Predicts poorer response to standard CBT across depression /
  anxiety / addiction populations (Ogrodniczuk 2011 meta-analysis).
- Elevates somatization risk (Taylor 1997 — alexithymic arousal
  without cognitive label presents as bodily complaints; pairs with
  PHQ-15 for the somatization-cluster clinical picture).
- Predicts relapse risk in substance-use disorders (Cleland 2005;
  Thorberg 2009 — inability to identify emotional triggers leaves
  the patient unable to preempt the craving-to-use pathway).
- Pairs with AAQ-II: alexithymia and psychological inflexibility are
  partially overlapping constructs (both involve disconnection from
  internal experience), but AAQ-II measures avoidance OF experience
  while TAS-20 measures inability to IDENTIFY the experience.

Instrument structure (Bagby 1994):

**20 items, each on a 1-5 Likert scale** scored:
    1 = strongly disagree
    2 = moderately disagree
    3 = neither agree nor disagree
    4 = moderately agree
    5 = strongly agree

**Three subscales** per Bagby 1994 three-factor CFA:
- **DIF** — Difficulty Identifying Feelings (7 items: 1, 3, 6, 7, 9, 13, 14)
  "I am often confused about what emotion I am feeling."  (item 1)
- **DDF** — Difficulty Describing Feelings (5 items: 2, 4, 11, 12, 17)
  "It is difficult for me to find the right words for my feelings." (item 2)
- **EOT** — Externally-Oriented Thinking (8 items: 5, 8, 10, 15, 16, 18, 19, 20)
  "I prefer to talk to people about their daily activities rather than
  their feelings." (item 15)

Subscale sums reconstruct to the 20-item total.

**Five items are reverse-keyed** (items 4, 5, 10, 18, 19).  These items
are worded in the alexithymia-ABSENT direction (e.g., "I am able to
describe my feelings easily" — item 4).  A high raw Likert on a
reverse-keyed item reflects LOW alexithymia; a low raw Likert reflects
HIGH alexithymia.  Before summing, reverse-keyed items are flipped
with the arithmetic-reflection idiom reused from PSWQ / LOT-R:
``flipped = (ITEM_MIN + ITEM_MAX) - raw`` = ``6 - raw`` on the 1-5
envelope.  The reverse-item distribution by subscale:

- DIF: 0 reverse items — all 7 items are direct.
- DDF: 1 reverse item (position 4).
- EOT: 4 reverse items (positions 5, 10, 18, 19).

Subscale totals and the 20-item total are computed from the POST-
flipped values so every contribution is in the alexithymia direction.

The ``items`` field on the result preserves the PATIENT'S raw pre-
flip responses — audit-trail invariant continues from PSWQ / LOT-R.

Range: 20-100 (post-flip sum of 20 items).  Midline (all raw = 3)
lands at 60 because 6-3 = 3 flip-invariant.

**Higher is worse** (more alexithymia) — same direction as PHQ-9 /
GAD-7 / DERS-16 / PCL-5 / OCI-R / K10 / WSAS / PSWQ; opposite of
WHO-5 / DTCQ-8 / Readiness Ruler / CD-RISC-10 / LOT-R.

Severity bands (Bagby 1994, replicated in Taylor 1997, pinned across
the validation literature):

    ≤51      → non-alexithymic
    52 - 60  → possible alexithymia
    ≥61      → alexithymic (clinical threshold)

These bands are published thresholds cross-calibrated against
external-criterion validation (structured clinical interview, MMPI
alexithymia scales) — they are NOT hand-rolled.  The cutoffs
re-introduce banded classification after five consecutive continuous-
sentinel instruments (WSAS, DERS-16, CD-RISC-10, PSWQ, LOT-R), and
are pinned as module constants ``TAS20_NON_ALEXITHYMIC_UPPER`` (=51)
and ``TAS20_POSSIBLE_UPPER`` (=60) so they can be referenced in
clinician-UI rendering and FHIR export without re-reading the
Bagby 1994 paper at every call site.

Notable clinical interpretation:
- A midline responder (raw all-3s → 60) lands in the "possible
  alexithymia" band, NOT non-alexithymic.  This is a deliberate
  property of Bagby's threshold placement — the midline of the
  Likert scale corresponds to "neither agree nor disagree" on
  alexithymia-identifying statements, which is itself evidence of
  poor emotional self-knowledge.  The clinician UI should render
  this band distinctively because it is the "borderline" group that
  benefits most from affect-labeling intervention (the non-
  alexithymic group has the skill already; the alexithymic group
  may need longer-horizon upstream work).

Envelope choice:
Banded severity + 3 subscales.  ``cutoff_used`` / ``positive_screen``
are NOT set — TAS-20 uses three bands, not a single binary cutoff.
(AUDIT's ``positive_screen`` semantic fires only on the harmful /
dependence bands; TAS-20 could apply a parallel ≥61 semantic but
downstream clinicians read the three-way band directly — a hardcoded
binary screen would conceal the "possible" middle band.)

Safety routing:
TAS-20 has **no direct safety item**.  The 20 items probe emotion-
identification / description / externally-oriented cognition; none
probe suicidality or crisis behavior.  ``requires_t3`` is never set.
Acute ideation screening stays on PHQ-9 item 9 / C-SSRS.  However,
the alexithymia construct is a clinical-risk amplifier — alexithymic
patients in crisis often present without verbal disclosure of the
emotion driving the crisis, which is exactly why PHQ-9 item 9 and
C-SSRS exist as independent behavioral-item screens.  The platform
does not gate crisis routing on TAS-20.

Bool rejection note:
Uniform with the rest of the psychometric package — bool items are
rejected at the validator.

References:
- Bagby RM, Parker JDA, Taylor GJ (1994).  *The twenty-item Toronto
  Alexithymia Scale — I. Item selection and cross-validation of the
  factor structure.*  Journal of Psychosomatic Research 38(1):23-32.
  (Original instrument paper; three-factor CFA; 52/61 cutpoints.)
- Bagby RM, Taylor GJ, Parker JDA (1994).  *The twenty-item Toronto
  Alexithymia Scale — II. Convergent, discriminant, and concurrent
  validity.*  Journal of Psychosomatic Research 38(1):33-40.
  (Companion paper — external-criterion validation of the cutoffs.)
- Taylor GJ, Bagby RM, Parker JDA (1997).  *Disorders of Affect
  Regulation: Alexithymia in Medical and Psychiatric Illness.*
  Cambridge University Press.  (Comprehensive clinical monograph;
  somatization / SUD / treatment-response framing.)
- Taylor GJ, Bagby RM (2004).  *New trends in alexithymia research.*
  Psychotherapy and Psychosomatics 73(2):68-77.  (Emotion-
  Regulation-Therapy framing for upstream affect-labeling work.)
- Ogrodniczuk JS, Piper WE, Joyce AS (2011).  *Effect of alexithymia
  on the process and outcome of psychotherapy: a programmatic
  review.*  Psychiatry Research 190(1):43-48.  (Meta-analytic
  evidence of poorer CBT response in high-alexithymia patients.)
- Cleland C, Magura S, Foote J, Rosenblum A, Kosanke N (2005).
  *Psychometric properties of the Toronto Alexithymia Scale (TAS-20)
  for substance users.*  Journal of Psychosomatic Research 58(3):
  299-306.  (SUD-specific validation.)
- Thorberg FA, Young RM, Sullivan KA, Lyvers M (2009).  *Alexithymia
  and alcohol use disorders: a critical review.*  Addictive
  Behaviors 34(3):237-245.  (Relapse-risk framing.)
- Jacobson NS, Truax P (1991).  *Clinical significance.*  J
  Consulting Clinical Psychology 59(1):12-19.  (RCI framing for
  subscale trajectory analysis on the platform.)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence

INSTRUMENT_VERSION = "tas20-1.0.0"
ITEM_COUNT = 20
ITEM_MIN = 1
ITEM_MAX = 5

# Bagby 1994 three-factor structure — 1-indexed item positions per
# subscale.  A refactor that reordered items or rotated subscale
# rows would silently miscategorize the clinical signal; every
# subscale test pins its item mapping independently.
TAS20_SUBSCALES: dict[str, tuple[int, ...]] = {
    "dif": (1, 3, 6, 7, 9, 13, 14),       # 7 items, no reverse
    "ddf": (2, 4, 11, 12, 17),            # 5 items, item 4 reverse
    "eot": (5, 8, 10, 15, 16, 18, 19, 20),  # 8 items, items 5/10/18/19 reverse
}

# Reverse-keyed items per Bagby 1994.  These items are worded in
# the alexithymia-ABSENT direction; flipped before summing so each
# post-flip value contributes in the alexithymia direction.
TAS20_REVERSE_ITEMS: tuple[int, ...] = (4, 5, 10, 18, 19)

# Bagby 1994 cutoffs, replicated in Taylor 1997.  These are
# published thresholds cross-calibrated against external-criterion
# validation — not hand-rolled.
TAS20_NON_ALEXITHYMIC_UPPER = 51  # ≤51 = non-alexithymic
TAS20_POSSIBLE_UPPER = 60          # 52-60 = possible; ≥61 = alexithymic

TAS20_TOTAL_MIN = 20  # post-flip floor (direct=1, reverse=5 → 15+5 = 20)
TAS20_TOTAL_MAX = 100  # post-flip ceiling (direct=5, reverse=1 → 75+25 = 100)

Band = Literal["non_alexithymic", "possible_alexithymia", "alexithymic"]


class InvalidResponseError(ValueError):
    """Raised on item-count, item-range, or item-type violations."""


@dataclass(frozen=True)
class Tas20Result:
    """Typed TAS-20 output.

    Fields:
    - ``total``: 20-100, the post-flip sum of the 20 Likert items.
      Minimum 20 because every item's lowest post-flip value is 1
      (a non-alexithymic responder disagrees with direct items and
      strongly agrees with reverse items, both flipping to 1).
      Higher is worse (more alexithymia).
    - ``band``: "non_alexithymic" (≤51), "possible_alexithymia"
      (52-60), or "alexithymic" (≥61) per Bagby 1994.
    - ``subscale_dif`` / ``subscale_ddf`` / ``subscale_eot``: the
      three subscale totals (DIF 7-35, DDF 5-25, EOT 8-40) computed
      from post-flip values.  Surfaced on the router envelope via
      the ``subscales`` map (wire keys: ``dif`` / ``ddf`` / ``eot``).
    - ``items``: verbatim 20-tuple input — the PATIENT'S raw pre-
      flip responses, pinned for auditability.  The reverse-keying
      flip on items 4, 5, 10, 18, 19 is an internal scoring detail
      of ``score_tas20`` and is not surfaced in ``items``.

    Deliberately-absent fields:
    - No ``cutoff_used`` / ``positive_screen`` — TAS-20 has three
      bands, not a single binary cutoff; ``band`` carries the full
      classification.
    - No ``requires_t3`` field — TAS-20 has no safety item.
    """

    total: int
    band: Band
    subscale_dif: int
    subscale_ddf: int
    subscale_eot: int
    items: tuple[int, ...]
    instrument_version: str = INSTRUMENT_VERSION


def _validate_item(index_1: int, value: object) -> int:
    """Validate a single 1-5 Likert item and return the int value.

    ``index_1`` is the 1-indexed item number (1-20) so error
    messages name the item a clinician would recognize from the
    TAS-20 document.
    """
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidResponseError(
            f"TAS-20 item {index_1} must be int, got {value!r}"
        )
    if value < ITEM_MIN or value > ITEM_MAX:
        raise InvalidResponseError(
            f"TAS-20 item {index_1} out of range "
            f"[{ITEM_MIN}, {ITEM_MAX}]: {value}"
        )
    return value


def _flip_if_reverse(index_1: int, value: int) -> int:
    """Return the post-flip value for item ``index_1``.

    Reuses the arithmetic-reflection idiom from PSWQ / LOT-R:
    ``flipped = ITEM_MIN + ITEM_MAX - raw`` = ``6 - raw`` on the
    1-5 envelope.  Non-reverse items pass through unchanged.
    """
    if index_1 in TAS20_REVERSE_ITEMS:
        return (ITEM_MIN + ITEM_MAX) - value
    return value


def _subscale_sum(
    post_flip: tuple[int, ...], subscale_name: str
) -> int:
    """Sum the post-flip items belonging to a named subscale.

    ``TAS20_SUBSCALES`` holds 1-indexed positions; convert to
    0-indexed array access here.  The sum operates on post-flip
    values so within-subscale reverse items contribute in the
    alexithymia direction (otherwise the DDF subscale would double-
    count reverse-item 4 contrary to direction).
    """
    positions_1 = TAS20_SUBSCALES[subscale_name]
    return sum(post_flip[pos - 1] for pos in positions_1)


def _classify(total: int) -> Band:
    """Map a 20-100 post-flip total to a Bagby 1994 band."""
    if total <= TAS20_NON_ALEXITHYMIC_UPPER:
        return "non_alexithymic"
    if total <= TAS20_POSSIBLE_UPPER:
        return "possible_alexithymia"
    return "alexithymic"


def score_tas20(raw_items: Sequence[int]) -> Tas20Result:
    """Score a TAS-20 response set.

    Inputs:
    - ``raw_items``: 20 items, each 1-5 Likert (1 = "strongly
      disagree", 5 = "strongly agree").  Reverse-keying on items
      4, 5, 10, 18, 19 is applied internally before summing —
      callers should NOT pre-flip the raw values.

    Raises :class:`InvalidResponseError` on:
    - Wrong number of items (must be exactly 20).
    - A non-int / bool item value.
    - An item outside ``[1, 5]``.

    Computes:
    - Post-flip total (20-100).
    - Bagby 1994 band (non_alexithymic / possible_alexithymia /
      alexithymic).
    - Three subscale totals (DIF, DDF, EOT) from post-flip values.

    The ``items`` field of the result preserves the PATIENT'S raw
    pre-flip responses — audit-trail invariant.
    """
    if len(raw_items) != ITEM_COUNT:
        raise InvalidResponseError(
            f"TAS-20 requires exactly {ITEM_COUNT} items, got {len(raw_items)}"
        )
    validated_raw = tuple(
        _validate_item(index_1=i + 1, value=v)
        for i, v in enumerate(raw_items)
    )
    post_flip = tuple(
        _flip_if_reverse(index_1=i + 1, value=v)
        for i, v in enumerate(validated_raw)
    )
    total = sum(post_flip)

    return Tas20Result(
        total=total,
        band=_classify(total),
        subscale_dif=_subscale_sum(post_flip, "dif"),
        subscale_ddf=_subscale_sum(post_flip, "ddf"),
        subscale_eot=_subscale_sum(post_flip, "eot"),
        items=validated_raw,
    )


__all__ = [
    "Band",
    "INSTRUMENT_VERSION",
    "InvalidResponseError",
    "ITEM_COUNT",
    "ITEM_MAX",
    "ITEM_MIN",
    "TAS20_NON_ALEXITHYMIC_UPPER",
    "TAS20_POSSIBLE_UPPER",
    "TAS20_REVERSE_ITEMS",
    "TAS20_SUBSCALES",
    "TAS20_TOTAL_MAX",
    "TAS20_TOTAL_MIN",
    "Tas20Result",
    "score_tas20",
]

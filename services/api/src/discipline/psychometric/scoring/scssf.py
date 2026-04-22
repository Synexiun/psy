"""SCS-SF — Self-Compassion Scale, Short Form (Raes, Pommier, Neff &
Van Gucht 2011).

The SCS-SF is the validated 12-item abbreviation of the 26-item
Self-Compassion Scale (SCS; Neff 2003).  It measures the trait-level
construct of **self-compassion** — the capacity to respond to one's
own suffering / failure / inadequacy with warmth rather than harsh
self-criticism, to experience personal failings as part of a common
human experience rather than in isolation, and to hold painful
thoughts / feelings in balanced awareness rather than over-
identifying with them (Neff 2003a, 2003b theoretical definition).

The construct is the empirically documented **antagonist of shame**:
patients who score higher on self-compassion experience less shame,
shame-avoidance behavior, shame-driven rumination, and shame-driven
relapse across depression, anxiety, eating, and substance-use
populations (MacBeth & Gumley 2012 meta-analysis of 14 clinical
studies; Kelly 2010 eating disorders; Brooks 2012 SUD).

Clinical relevance to the Discipline OS platform:
The platform's product CLAUDE.md enshrines the **"compassion-first
relapse copy"** rule as a non-negotiable: the relapse template
library must never use "you failed" / "streak reset" framing, and
templates require clinical QA sign-off to change.  The rule is
not ornamental — it reflects the documented mechanism by which
shame-avoidance DRIVES the next relapse:

 1. Patient relapses.
 2. Shame + self-judgment.
 3. Motivation-to-avoid-shame > motivation-to-recover.
 4. Patient disengages from the treatment surface (stops logging,
    stops journaling, ignores nudges — the "abstinence violation
    effect", Marlatt 1985).
 5. Disengagement → next relapse at higher severity.

The platform interrupts this loop at step 3 via compassion-first
copy (step 3 → step 3') and at step 4 via proactive re-engagement
nudges that DO NOT shame the patient.  SCS-SF is the measurement
lever:  the intervention layer reads low SCS-SF (or elevated
uncompassionate-self-responding) as a relapse-risk flag and routes
the affected patient to compassion-focused therapy (CFT — Gilbert
2014) tool variants BEFORE the next urge episode.  High SCS-SF is
the protective profile — patient can absorb a relapse without the
shame-spiral, and the platform can deprioritize relapse-prevention
routing in favor of other process-level work.

Pairing with existing instruments:
- **PHQ-9 / GAD-7 / PSS-10**: self-criticism mediates depression
  and anxiety (Luyten 2013; Werner 2019).  Patient with moderate
  PHQ-9 + low SCS-SF responds better to CFT than to standard CBT;
  intervention routing reads the pair, not either measure alone.
- **AAQ-II**: self-compassion and psychological flexibility are
  partially overlapping constructs (both involve a non-judgmental
  relationship to internal experience) — SCS-SF measures the
  KINDNESS component while AAQ-II measures the ACCEPTANCE
  component.
- **DERS-16 / ERQ / TAS-20**: the three-layer emotion-processing
  architecture (identify → choose strategy → execute).  SCS-SF
  adds a 4th layer — the AFFECTIVE COLOR of the regulation
  attempt.  A patient who identifies emotion (TAS-20 OK), chooses
  reappraisal (ERQ OK), and executes the regulation (DERS-16 OK)
  but does so with harsh self-criticism (low SCS-SF) shows the
  "high-functioning-but-miserable" profile the platform's copy
  layer must not reinforce.
- **Substance-use cluster (AUDIT / DAST / URICA / DTCQ-8)**: low
  SCS-SF is a documented relapse predictor in SUD populations
  (Brooks 2012; Kelly 2010 eating disorders as proxy) —
  independently of craving intensity (PACS / VAS) and coping
  confidence (DTCQ-8).  The contextual bandit layer adds SCS-SF
  as a process-state feature in the relapse-prevention decision
  surface.

Instrument structure (Raes 2011):

**12 items, each on a 1-5 Likert scale** scored:
    1 = almost never
    2 = rarely
    3 = half the time
    4 = often
    5 = almost always

Six 2-item subscales per Neff 2003 / Raes 2011 factor structure —
three "compassionate" and three "uncompassionate" construct dyads:

COMPASSIONATE (positive-keyed — higher = more self-compassion):
- **Self-Kindness (SK)**: items 2, 6
    2.  "I try to be understanding and patient towards those
         aspects of my personality I don't like."
    6.  "When I'm going through a very hard time, I give myself
         the caring and tenderness I need."
- **Common Humanity (CH)**: items 5, 10
    5.  "I try to see my failings as part of the human condition."
   10.  "When I feel inadequate in some way, I try to remind
         myself that feelings of inadequacy are shared by most
         people."
- **Mindfulness (M)**: items 3, 7
    3.  "When something painful happens I try to take a balanced
         view of the situation."
    7.  "When something upsets me I try to keep my emotions in
         balance."

UNCOMPASSIONATE (negative-keyed — higher raw = LESS self-compassion):
- **Self-Judgment (SJ)**: items 11, 12
   11.  "I'm disapproving and judgmental about my own flaws and
         inadequacies."
   12.  "I'm intolerant and impatient towards those aspects of my
         personality I don't like."
- **Isolation (I)**: items 4, 8
    4.  "When I think about my inadequacies, it tends to make me
         feel more separate and cut off from the rest of the world."
    8.  "When I'm feeling down I tend to feel like most other
         people are probably happier than I am."
- **Over-Identification (OI)**: items 1, 9
    1.  "When I fail at something important to me I become
         consumed by feelings of inadequacy."
    9.  "When I'm feeling down I tend to obsess and fixate on
         everything that's wrong."

**Reverse-keying**: the 6 uncompassionate items (1, 4, 8, 9, 11,
12) are reverse-scored for the TOTAL computation so the aggregate
lands in the self-compassion direction (higher total = more self-
compassion).  **Subscale sums are computed on RAW values** (not
post-flip) so each subscale reports its native construct:
``subscale_sj`` directly reads as "how much self-judgment does
this patient endorse" — NOT as "how much reversed-self-judgment
(i.e. lack-of-self-judgment)".  This is opposite to the TAS-20
convention (where subscales are POST-flip because all three
TAS-20 subscales measure the same pathology and should align).
SCS-SF subscales intentionally preserve the positive / negative
dyad structure so a clinician can read the dyad imbalance
directly ("high SK but also high SJ" = positive self-beliefs co-
existing with harsh self-criticism, a profile CFT specifically
targets).

**Scoring convention**: Raes 2011 reports MEAN scores (sum / 2
per subscale; sum / 12 post-flip for total).  This codebase uses
SUMS for wire consistency with the rest of the psychometric
package (integer type, no floating-point in the audit trail).
Reported sums are:

    per subscale (raw, 2 items × 1-5):       sum in [2, 10]
    total (post-flip, 12 items × 1-5):       sum in [12, 60]

Clinical interpretation:
- Total < 30 (on the raw 12-60 scale): low self-compassion.
  Tangney 2011 associates this range with elevated shame-proneness
  and SUD-relapse risk.  Route to CFT tool variants.
- Total 30-45: moderate self-compassion.  Typical non-clinical
  range (Neff 2003 normative data).
- Total > 45: high self-compassion.  Protective profile.

These are descriptive interpretations from the literature, NOT
published cutoffs — Raes 2011 and Neff 2016 do NOT publish
validated severity bands for the SCS-SF total.  The router
therefore emits ``severity="continuous"`` (uniform with DERS-16
/ ERQ / BRS / PSWQ / SDS / K6 / CD-RISC-10 / LOT-R); hand-rolling
cutoffs from the descriptive ranges would violate CLAUDE.md's
"Don't hand-roll severity thresholds" rule.

**Subscale reliability caveat**: Raes 2011 reports α = 0.55-0.81
across the 6 subscales in the validation sample.  Two-item
subscales are inherently lower-reliability than the 6-item CSR /
USR higher-order factors (α > 0.85 in most samples).  The wire
exposes all 6 subscales because clinicians familiar with SCS work
expect the 6-factor profile, and FHIR Observation export is
more faithful at the subscale grain, but the clinician-UI layer
should render the subscale card with an α caveat footnote
(and a two-factor summary card for the primary read).

Safety routing:
- SCS-SF has NO safety item.  It does not screen for suicidality,
  self-harm, or acute risk — self-compassion is a trait, not a
  state, and none of the 12 items probe crisis behavior.  Acute
  risk screening stays on PHQ-9 item 9 and C-SSRS.
  ``requires_t3`` is hard-coded ``False`` at the router.

References:
- Raes F, Pommier E, Neff KD, Van Gucht D (2011).  *Construction
  and factorial validation of a short form of the Self-Compassion
  Scale.*  Clinical Psychology & Psychotherapy 18(3):250-255.
  (Primary validation — 12-item selection from SCS-26, CFA
  confirming 6-factor structure, near-perfect correlation
  r ≥ 0.97 between SCS-SF and SCS-26 totals.)
- Neff KD (2003a).  *Self-compassion: An alternative
  conceptualization of a healthy attitude toward oneself.*
  Self and Identity 2(2):85-101.  (Theoretical construct
  definition — the 3-component model: self-kindness vs self-
  judgment, common humanity vs isolation, mindfulness vs over-
  identification.)
- Neff KD (2003b).  *The development and validation of a scale
  to measure self-compassion.*  Self and Identity 2(3):223-250.
  (SCS-26 primary validation.)
- Neff KD (2016).  *The Self-Compassion Scale is a valid and
  theoretically coherent measure of self-compassion.*
  Mindfulness 7(1):264-274.  (Scoring methodology defense
  against factor-analytic critiques — total score is valid for
  applied/clinical use.)
- Muris P, Petrocchi N (2017).  *Protection or vulnerability? A
  meta-analysis of the relations between the positive and
  negative components of self-compassion and psychopathology.*
  Clinical Psychology & Psychotherapy 24(2):373-383.  (The
  opposing meta-analytic position — CSR and USR load on
  different psychopathology outcomes.)
- Neff KD, Germer CK (2013).  *A pilot study and randomized
  controlled trial of the mindful self-compassion program.*
  Journal of Clinical Psychology 69(1):28-44.  (MSC — the
  direct treatment protocol SCS-SF is the companion measure
  for.)
- MacBeth A, Gumley A (2012).  *Exploring compassion: A meta-
  analysis of the association between self-compassion and
  psychopathology.*  Clinical Psychology Review 32(6):545-552.
  (14-study meta-analysis — negative relationship with
  depression, anxiety, and stress.)
- Gilbert P (2014).  *The origins and nature of compassion
  focused therapy.*  British Journal of Clinical Psychology
  53(1):6-41.  (CFT — the therapeutic protocol the intervention
  layer routes high-shame / low-SCS-SF patients to.)
- Brooks M, Kay-Lambkin F, Bowman J, Childs S (2012).
  *Self-compassion amongst clients with problematic alcohol
  use.*  Mindfulness 3(4):308-317.  (SUD-population validation
  of self-compassion as a relapse protective factor.)
- Tangney JP, Stuewig J, Mashek DJ (2007).  *Moral emotions
  and moral behavior.*  Annual Review of Psychology 58:345-372.
  (Shame-relapse pathway in addiction populations — the
  mechanism the compassion-first copy rule targets.)
- Marlatt GA, Gordon JR (1985).  *Relapse prevention:
  Maintenance strategies in the treatment of addictive
  behaviors.*  New York: Guilford Press.  (The "abstinence
  violation effect" Marlatt named — shame after relapse
  driving disengagement and the next relapse.)
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

INSTRUMENT_VERSION = "scssf-1.0.0"
ITEM_COUNT = 12
ITEM_MIN = 1
ITEM_MAX = 5

# Raes 2011 Table 1 — 1-indexed item positions per subscale.  Six
# 2-item subscales partition the 12 items exactly (every item is
# in exactly one subscale).  A refactor that reordered items would
# silently miscategorize the clinical signal; every subscale test
# pins its item mapping independently.  The subscale ordering
# mirrors Raes 2011 Table 2 (SK, SJ, CH, I, M, OI) to match the
# factor-loadings table a clinician is likely to cross-reference.
SCSSF_SUBSCALES: dict[str, tuple[int, ...]] = {
    "self_kindness": (2, 6),
    "self_judgment": (11, 12),
    "common_humanity": (5, 10),
    "isolation": (4, 8),
    "mindfulness": (3, 7),
    "over_identification": (1, 9),
}

# The 6 uncompassionate-direction items.  These items ARE reverse-
# keyed for the TOTAL computation (so the aggregate reads in the
# self-compassion direction), but the SUBSCALE sums use RAW
# values (native construct direction).  This asymmetry is
# deliberate — see module docstring for the rationale.
SCSSF_REVERSE_ITEMS: tuple[int, ...] = (1, 4, 8, 9, 11, 12)

SCSSF_TOTAL_MIN = 12  # 12 items × minimum post-flip value of 1
SCSSF_TOTAL_MAX = 60  # 12 items × maximum post-flip value of 5


class InvalidResponseError(ValueError):
    """Raised on item-count, item-range, or item-type violations."""


@dataclass(frozen=True)
class ScsSfResult:
    """Typed SCS-SF output.

    Fields:
    - ``total``: 12-60, the POST-FLIP sum (negative-direction items
      reverse-scored) so the aggregate reads in the self-compassion
      direction.  Higher total = more self-compassion.
    - ``subscale_self_kindness`` / ``subscale_self_judgment`` /
      ``subscale_common_humanity`` / ``subscale_isolation`` /
      ``subscale_mindfulness`` / ``subscale_over_identification``:
      six 2-item subscale sums on RAW values (native construct
      direction — NOT post-flip).  Each subscale range is 2-10.
      Surfaced on the router's AssessmentResult envelope via the
      ``subscales`` map (wire keys match the 6 subscale names
      without the ``subscale_`` prefix).
    - ``items``: verbatim 12-tuple input — the PATIENT'S raw pre-
      flip responses, pinned for auditability.  The reverse-keying
      flip on items 1, 4, 8, 9, 11, 12 is an internal scoring
      detail of ``score_scssf`` for the TOTAL computation; it is
      not surfaced in ``items`` and does NOT propagate to the
      subscale sums.

    Deliberately-absent fields:
    - No ``severity`` field — Raes 2011 published no bands; SCS-SF
      is a continuous dimensional measure.  The router envelope
      emits ``severity="continuous"`` (uniform with DERS-16 / ERQ /
      BRS / PSWQ / SDS / K6 / CD-RISC-10 / LOT-R / PACS / BIS-11).
    - No ``cutoff_used`` / ``positive_screen`` — continuous
      instrument, no cutoff shape.
    - No ``requires_t3`` field — SCS-SF has no safety item.
    """

    total: int
    subscale_self_kindness: int
    subscale_self_judgment: int
    subscale_common_humanity: int
    subscale_isolation: int
    subscale_mindfulness: int
    subscale_over_identification: int
    items: tuple[int, ...]
    instrument_version: str = INSTRUMENT_VERSION


def _validate_item(index_1: int, value: object) -> int:
    """Validate a single 1-5 Likert item and return the int value."""
    # Bool rejection — uniform with the rest of the psychometric package.
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidResponseError(
            f"SCS-SF item {index_1} must be int, got {value!r}"
        )
    if value < ITEM_MIN or value > ITEM_MAX:
        raise InvalidResponseError(
            f"SCS-SF item {index_1} out of range "
            f"[{ITEM_MIN}, {ITEM_MAX}]: {value}"
        )
    return value


def _flip_if_reverse(index_1: int, value: int) -> int:
    """Return the post-flip value for item ``index_1``.

    Reuses the arithmetic-reflection idiom from PSWQ / LOT-R /
    TAS-20: ``flipped = ITEM_MIN + ITEM_MAX - raw`` = ``6 - raw``
    on the 1-5 envelope.  Non-reverse items pass through unchanged.

    NOTE: ``_flip_if_reverse`` is used ONLY for the TOTAL
    computation.  Subscale sums deliberately use raw values
    (native construct direction).
    """
    if index_1 in SCSSF_REVERSE_ITEMS:
        return (ITEM_MIN + ITEM_MAX) - value
    return value


def _subscale_sum_raw(
    items: tuple[int, ...], subscale_name: str
) -> int:
    """Sum the RAW items belonging to a named subscale.

    SCSSF_SUBSCALES holds 1-indexed positions; convert to 0-indexed
    array access here.  The sum operates on RAW values (NOT post-
    flip) so each subscale reports its NATIVE construct direction:
    ``subscale_self_judgment`` reads as "how much self-judgment
    does this patient endorse", not "how much reversed-self-
    judgment".
    """
    positions_1 = SCSSF_SUBSCALES[subscale_name]
    return sum(items[pos - 1] for pos in positions_1)


def score_scssf(raw_items: Sequence[int]) -> ScsSfResult:
    """Score an SCS-SF response set.

    Inputs:
    - ``raw_items``: 12 items, each 1-5 Likert (1 = "almost never",
      5 = "almost always").  Reverse-keying on items 1, 4, 8, 9,
      11, 12 is applied INTERNALLY for the TOTAL computation only
      — subscale sums retain the raw values.  Callers should NOT
      pre-flip raw values.

    Raises :class:`InvalidResponseError` on:
    - Wrong number of items (must be exactly 12).
    - A non-int / bool item value.
    - An item outside ``[1, 5]``.

    Computes:
    - Post-flip total (12-60, self-compassion direction).
    - Six raw subscale sums (2-10 each, native construct direction).

    The ``items`` field of the result preserves the PATIENT'S raw
    pre-flip responses — audit-trail invariant.
    """
    if len(raw_items) != ITEM_COUNT:
        raise InvalidResponseError(
            f"SCS-SF requires exactly {ITEM_COUNT} items, got {len(raw_items)}"
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

    return ScsSfResult(
        total=total,
        subscale_self_kindness=_subscale_sum_raw(
            validated_raw, "self_kindness"
        ),
        subscale_self_judgment=_subscale_sum_raw(
            validated_raw, "self_judgment"
        ),
        subscale_common_humanity=_subscale_sum_raw(
            validated_raw, "common_humanity"
        ),
        subscale_isolation=_subscale_sum_raw(
            validated_raw, "isolation"
        ),
        subscale_mindfulness=_subscale_sum_raw(
            validated_raw, "mindfulness"
        ),
        subscale_over_identification=_subscale_sum_raw(
            validated_raw, "over_identification"
        ),
        items=validated_raw,
    )


__all__ = [
    "INSTRUMENT_VERSION",
    "ITEM_COUNT",
    "ITEM_MAX",
    "ITEM_MIN",
    "SCSSF_REVERSE_ITEMS",
    "SCSSF_SUBSCALES",
    "SCSSF_TOTAL_MAX",
    "SCSSF_TOTAL_MIN",
    "InvalidResponseError",
    "ScsSfResult",
    "score_scssf",
]

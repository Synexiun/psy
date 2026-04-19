"""GSE — General Self-Efficacy Scale (Schwarzer & Jerusalem 1995).

The General Self-Efficacy Scale is the most widely-used self-report
instrument for **trait-level general self-efficacy** — Bandura's
(1977, 1997) construct of belief in one's capability to organize and
execute courses of action required to produce desired outcomes.
Schwarzer & Jerusalem published it in Weinman, Wright & Johnston
(Eds.), *Measures in Health Psychology: A User's Portfolio* (NFER-
NELSON 1995, pp. 35-37).  Scholz, Gutiérrez-Doña, Sud & Schwarzer
2002 (*European Journal of Psychological Assessment* 18(3):242-251)
published the canonical cross-cultural validation with n=19,120
across 25 countries (extended to 28), confirming unidimensional
factor structure and median α=0.86.

Clinical relevance to the Discipline OS platform:

The GSE fills a **general self-efficacy dimension gap** in the
platform's roster.  Prior instruments touch self-efficacy-adjacent
constructs but do not measure general self-efficacy directly:

- **DTCQ-8** (Sprint covered Sklar & Turner 1999 Drug-Taking
  Confidence Questionnaire 8-item short form) measures SITUATION-
  SPECIFIC coping self-efficacy across Marlatt 1985's 8 high-risk
  relapse situations on a 0-100 confidence scale.  Trait-level vs
  situation-level: DTCQ-8 probes "can I resist in THIS situation?"
  while GSE probes "do I generally believe I can handle what comes
  my way?"  The two are correlated (r ≈ 0.40 per Luszczynska 2005)
  but distinct.
- **BRS** (Sprint 38) measures BOUNCE-BACK RESILIENCE — the
  behavioral-recovery dimension.  Self-efficacy is the cognitive-
  expectation dimension; resilience is the behavioral-outcome
  dimension.
- **RSES** (Sprint covering Rosenberg 1965) measures GLOBAL SELF-
  ESTEEM — the global evaluative attitude toward the self.  Self-
  esteem is "do I value myself?"; self-efficacy is "do I believe I
  can DO things?"  Distinct constructs; Bandura 1997 §2 explicitly
  differentiated them.
- **GSE** measures GENERAL SELF-EFFICACY — "do I generally believe
  my competence and resourcefulness are sufficient to navigate
  challenges?"  The **trait-level backdrop** against which
  situation-specific self-efficacies (DTCQ-8 coping, exercise-
  adherence, medication-adherence) are formed.

For relapse-prevention specifically, general self-efficacy is a
documented moderator of abstinence outcomes.  Marlatt & Gordon 1985
(*Relapse Prevention*, Guilford Press) placed self-efficacy at the
center of the cognitive-behavioral model of relapse: low self-
efficacy increases the probability that a high-risk situation leads
to a lapse, and the "abstinence violation effect" (AVE) following a
lapse — the cognitive-affective shift from "I slipped" to "I'm a
failure" — is mediated by eroded self-efficacy beliefs.  Luszczynska,
Scholz & Schwarzer 2005 (*Journal of Psychology* 139(5):439-457)
meta-analyzed n=16,657 GSE observations and confirmed predictive
validity for positive affect, optimism, and work satisfaction; and
inverse associations with depression, anxiety, burnout, and stress
symptomatology.

Pairings with existing instruments:

- **GSE low + DTCQ-8 low** — trait-level deficit + situation-
  specific deficit.  The "pervasive-low-confidence" profile.
  Intervention match: Bandura 1997 mastery-experiences approach
  (small-step successes build trait-level self-efficacy) before
  situation-specific skill work.  Avoid jumping directly to high-
  risk-situation exposure — the client lacks the trait-level
  foundation to tolerate the failure probability.
- **GSE high + DTCQ-8 low** — generally confident but substance-
  situation-specific deficit.  "Competence-gap" profile common in
  high-functioning clients early in recovery.  Intervention match:
  Marlatt 2005 coping-skills training focused on the specific low-
  confidence DTCQ-8 situations — the trait-level foundation is
  intact, so situation-specific skills can be built directly.
- **GSE low + DTCQ-8 high** — situation-specific confident but
  generally depleted.  Less common; often reflects recent abstinence
  milestone inflating substance-specific confidence while underlying
  trait self-efficacy remains depressed.  Intervention match:
  generalization / transfer work (how does the client's substance-
  resisting confidence apply to other life domains?).
- **GSE high + DTCQ-8 high** — full self-efficacy profile.
  Protective; maintenance-oriented interventions.
- **GSE low + BRS low** — cognitive-expectation deficit + behavioral-
  recovery deficit.  Cascades into the Marlatt 1985 AVE pathway:
  lapse → catastrophic cognition → no bounce-back → full relapse.
  Intervention match: parallel self-efficacy rebuilding + resilience-
  skills training (Reivich 2002 Penn Resiliency Program).
- **GSE low + LOT-R low** — self-efficacy deficit + pessimism.
  "Neither-competent-nor-hopeful" profile.  Closely parallels Beck
  1979 depressive-cognitive-triad (self, world, future); CBT-D
  indication (Beck 1979; Hollon 2005).
- **GSE low + SWLS low + PSS-10 high** — the "overwhelmed-and-
  depleted" profile.  Cohen-Wills 1985 buffering-capacity breakdown
  combined with global dissatisfaction.  Priority intervention:
  immediate stress-regulation + graduated mastery experiences;
  life-evaluation work later.
- **GSE trajectory (longitudinal)** — Jacobson-Truax RCI on GSE
  is a mid-horizon measure (faster than SWLS, slower than PACS /
  VAS).  From Scholz 2002 α=0.86 and SD≈5 on European n=4,988
  normative sample → RCI ≈ 5 points.  A 5-point GSE delta is
  clinically meaningful in a Marlatt-style relapse-prevention
  program.

Instrument structure (Schwarzer & Jerusalem 1995):

**10 items, each on a 4-point Likert agreement scale**:
    1 = Not at all true
    2 = Hardly true
    3 = Moderately true
    4 = Exactly true

**ALL 10 items are positively worded** — agreement indicates higher
self-efficacy.  There are **NO reverse-keyed items** in Schwarzer
& Jerusalem 1995.  This matches MSPSS (Sprint 73) and SWLS (Sprint
72) in the "all-positive-wording, rely on α to detect acquiescence"
design pattern.  Schwarzer & Jerusalem reported α = 0.76-0.90
across samples; Scholz 2002 confirmed α median 0.86 across 25
countries — indicating coherent-interpretation dominance over
acquiescence bias.

Verbatim Schwarzer & Jerusalem 1995 item text (administration order):

    1.  I can always manage to solve difficult problems if I try
        hard enough.
    2.  If someone opposes me, I can find the means and ways to
        get what I want.
    3.  It is easy for me to stick to my aims and accomplish my
        goals.
    4.  I am confident that I could deal efficiently with
        unexpected events.
    5.  Thanks to my resourcefulness, I know how to handle
        unforeseen situations.
    6.  I can solve most problems if I invest the necessary
        effort.
    7.  I can remain calm when facing difficulties because I can
        rely on my coping abilities.
    8.  When I am confronted with a problem, I can usually find
        several solutions.
    9.  If I am in trouble, I can usually think of a solution.
    10. I can usually handle whatever comes my way.

Scoring:

- Total = straight sum of all 10 items, range 10-40.
- Higher = more general self-efficacy (uniform direction with
  WHO-5 / LOT-R / BRS / MAAS / RSES / SWLS / MSPSS / PANAS-10 PA
  "higher-is-better").

Severity:

- Envelope: ``"continuous"``.  Schwarzer & Jerusalem 1995 did not
  publish severity bands.  Scholz 2002 normative mean ≈ 29 (SD ≈ 4)
  on a Eurasian n=4,988 sample; Luszczynska 2005 meta-analytic
  norms cluster in the 28-32 range across diverse populations.
  These are DESCRIPTIVE DISTRIBUTIONS, not clinical cutoffs — there
  is no validated GSE-versus-structured-clinical-interview cutoff
  because "generalized self-efficacy" has no external diagnostic
  criterion.  Per CLAUDE.md non-negotiable #9 ("Don't hand-roll
  severity thresholds"), the envelope stays ``"continuous"`` and
  clinicians compare against the normative distribution via
  RCI / percentile machinery downstream (Jacobson & Truax 1991).

T3 posture:

No GSE item probes suicidality.  Item 7 ("remain calm when facing
difficulties because I can rely on my coping abilities") is a
coping-confidence probe, NOT a self-harm or ideation probe.  Acute-
risk screening stays on C-SSRS / PHQ-9 item 9.  GSE low paired with
high PHQ-9 / LOT-R low surfaces at the clinician-UI layer as a
C-SSRS follow-up prompt (per Beck 1979 depressive-cognitive-triad
× Beck 1985 hopelessness-suicide-risk convergence), NOT as a
scorer-layer T3 flag.  Same renderer-versus-scorer-layer boundary
established for SWLS / MSPSS / UCLA-3.

Design invariants preserved:

- **10-item exact count**.  Schwarzer & Jerusalem 1995 pinned the
  10-item structure.  Reduced forms exist (GSE-6 Romppel 2013; GSE-
  3 Luszczynska 2005 supplement) but have different psychometric
  properties and warrant a separate scorer if shipped.
- **Administration order pinned**.  Scholz 2002 cross-cultural
  measurement invariance depends on administration order.
- **Strict 1-4 Likert range** at the scorer.  Schwarzer 1995
  explicitly pinned the 1-4 response scale; 0 and 5 are out-of-
  range.
- **Bool rejection at the scorer.**  Platform-wide invariant per
  CLAUDE.md standing rule: True/False booleans are rejected before
  the int check.  Under HTTP/Pydantic wire layer, ``true`` round-
  trips as ``1`` and is accepted at the valid-range layer; ``false``
  round-trips as ``0`` and is rejected by range.  Same defence-in-
  depth layering as SWLS / MSPSS.

Citations:

- Schwarzer R, Jerusalem M (1995).  *Generalized Self-Efficacy
  Scale.*  In J Weinman, S Wright, M Johnston (Eds.), Measures in
  Health Psychology: A User's Portfolio (pp. 35-37).  NFER-NELSON,
  Windsor UK.  (Canonical derivation.)
- Scholz U, Gutiérrez-Doña B, Sud S, Schwarzer R (2002).  *Is
  General Self-Efficacy a Universal Construct?  Psychometric
  Findings from 25 Countries.*  European Journal of Psychological
  Assessment 18(3):242-251.  (Cross-cultural validation; n = 19,120;
  unidimensional factor structure; median α = 0.86.)
- Luszczynska A, Scholz U, Schwarzer R (2005).  *The General Self-
  Efficacy Scale: Multicultural validation studies.*  Journal of
  Psychology 139(5):439-457.  (n = 16,657 meta; convergent /
  discriminant validity; norms across populations.)
- Bandura A (1977).  *Self-efficacy: Toward a unifying theory of
  behavioral change.*  Psychological Review 84(2):191-215.
  (Foundational self-efficacy theory; basis for the GSE construct
  the scale was designed to measure.)
- Bandura A (1997).  *Self-Efficacy: The Exercise of Control.*
  W.H. Freeman, New York.  (Comprehensive self-efficacy theory;
  Chapter 3 mastery-experience approach for self-efficacy
  building; basis for the GSE-low × DTCQ-8-low intervention match.)
- Marlatt GA, Gordon JR (1985).  *Relapse Prevention: Maintenance
  Strategies in the Treatment of Addictive Behaviors.*  Guilford
  Press, New York.  (Cognitive-behavioral model of relapse;
  self-efficacy as central moderator; abstinence violation effect
  mediated by eroded self-efficacy beliefs.)
- Marlatt GA, Donovan DM (Eds., 2005).  *Relapse Prevention:
  Maintenance Strategies in the Treatment of Addictive Behaviors*
  (2nd ed.).  Guilford Press, New York.  (Updated coping-skills
  training protocols; basis for the GSE-high × DTCQ-8-low
  intervention match.)
- Beck AT, Rush AJ, Shaw BF, Emery G (1979).  *Cognitive Therapy
  of Depression.*  Guilford Press, New York.  (Depressive-cognitive
  triad; basis for the GSE-low × LOT-R-low CBT-D indication.)
- Hollon SD, Stewart MO, Strunk D (2005).  *Enduring effects for
  cognitive behavior therapy in the treatment of depression and
  anxiety.*  Annual Review of Psychology 57:285-315.  (CBT-D
  enduring-effects meta; basis for intervention pairing rationale.)
- Reivich K, Shatte A (2002).  *The Resilience Factor: 7 Essential
  Skills for Overcoming Life's Inevitable Obstacles.*  Broadway
  Books, New York.  (Penn Resiliency Program; basis for GSE-low ×
  BRS-low resilience-skills-parallel intervention sequencing.)
- Sklar SM, Turner NE (1999).  *A brief measure for the assessment
  of coping self-efficacy among alcohol and other drug users.*
  Addiction 94(5):723-729.  (DTCQ-8 validation; basis for the
  GSE-trait × DTCQ-8-situation pairing analysis.)
- Jacobson NS, Truax P (1991).  *Clinical significance: A
  statistical approach to defining meaningful change in
  psychotherapy research.*  Journal of Consulting and Clinical
  Psychology 59(1):12-19.  (RCI methodology applied to GSE at
  trajectory layer; from Scholz 2002 α = 0.86 and SD ≈ 5 → RCI
  ≈ 5 points on the 10-40 total.)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence

INSTRUMENT_VERSION = "gse-1.0.0"
ITEM_COUNT = 10
ITEM_MIN, ITEM_MAX = 1, 4


# Schwarzer & Jerusalem 1995: NO reverse-keyed items.  All 10 items
# worded in the "higher = more self-efficacy" direction.  Pinned as
# empty tuple so a future change that adds reverse-keying would
# require updating this constant AND the module docstring, triggering
# clinical review.
GSE_REVERSE_ITEMS: tuple[int, ...] = ()


class InvalidResponseError(ValueError):
    """Raised on item-count, item-range, or item-type violations."""


Severity = Literal["continuous"]


@dataclass(frozen=True)
class GseResult:
    """Typed GSE output.

    Fields:
    - ``total``: 10-40 straight sum of the ten 1-4 Likert items.
      Higher = more general self-efficacy (uniform with WHO-5 /
      LOT-R / BRS / MAAS / RSES / SWLS / MSPSS "higher-is-better"
      direction).  Flows into the FHIR Observation's
      ``valueInteger`` at the reporting layer.
    - ``severity``: literal ``"continuous"`` sentinel.  Schwarzer
      1995 did not publish severity bands; Scholz 2002 normative
      distribution (mean ≈ 29, SD ≈ 4) and Luszczynska 2005 meta-
      analytic norms stay at the clinician-UI renderer layer per
      CLAUDE.md non-negotiable #9.
    - ``items``: verbatim 10-tuple of raw 1-4 responses in Schwarzer
      & Jerusalem 1995 administration order.  Preserved for audit
      invariance and FHIR R4 export.

    Deliberately-absent fields:
    - No ``subscales`` — Scholz 2002 cross-cultural validation
      (n=19,120 across 25 countries) confirmed unidimensional factor
      structure.  Partitioning into facets would over-fit the
      published structure and invalidate Scholz 2002 cross-cultural
      measurement invariance.
    - No ``positive_screen`` / ``cutoff_used`` — GSE is not a
      screen; general self-efficacy is a continuous-dimensional
      measure without a validated diagnostic gate.
    - No ``requires_t3`` — no GSE item probes suicidality.  Item 7
      ("remain calm when facing difficulties") is a coping-
      confidence probe, NOT a self-harm or ideation probe.  Acute-
      risk screening stays on C-SSRS / PHQ-9 item 9.
    """

    total: int
    severity: Severity
    items: tuple[int, ...]
    instrument_version: str = INSTRUMENT_VERSION


def _validate_item(index_1: int, value: object) -> int:
    """Validate a single 1-4 Likert item.

    ``index_1`` is the 1-indexed item number (1-10) so error
    messages name the item a clinician would recognize from the
    Schwarzer & Jerusalem 1995 administration order.

    Bool rejection per CLAUDE.md standing rule: ``bool`` values
    are rejected before the int check because Python's
    ``bool is int`` coercion would silently accept ``True`` /
    ``False`` as item responses.  The bool check precedes the
    range check so that even ``True`` (coerces to 1, a valid
    Likert response) is rejected when passed directly as a bool.
    """
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidResponseError(
            f"GSE item {index_1} must be int, got {value!r}"
        )
    if not (ITEM_MIN <= value <= ITEM_MAX):
        raise InvalidResponseError(
            f"GSE item {index_1} must be in {ITEM_MIN}-{ITEM_MAX}, "
            f"got {value}"
        )
    return value


def score_gse(raw_items: Sequence[int]) -> GseResult:
    """Score a GSE response set.

    Inputs:
    - ``raw_items``: 10 items, each 1-4 Likert (1 = Not at all
      true, 4 = Exactly true), in Schwarzer & Jerusalem 1995
      administration order.

    Raises :class:`InvalidResponseError` on:
    - Wrong number of items (must be exactly 10).
    - A non-int / bool item value.
    - An item outside ``[1, 4]``.

    Computes:
    - ``total``: straight sum of the 10 items, range 10-40.
    - ``severity``: always ``"continuous"`` (Scholz 2002 norms
      stay at the clinician-UI renderer layer).
    - ``items``: tuple of raw responses (GSE has no reverse-keyed
      positions, so raw = post-flip).

    Platform-wide invariants preserved:
    - No reverse-keying (Schwarzer 1995 all-positive wording).
    - Unidimensional factor structure (Scholz 2002).
    - No T3 flag (no suicidality probe).
    """
    if len(raw_items) != ITEM_COUNT:
        raise InvalidResponseError(
            f"GSE requires exactly {ITEM_COUNT} items, "
            f"got {len(raw_items)}"
        )
    items = tuple(
        _validate_item(index_1=i + 1, value=v)
        for i, v in enumerate(raw_items)
    )
    total = sum(items)

    return GseResult(
        total=total,
        severity="continuous",
        items=items,
    )


__all__ = [
    "GSE_REVERSE_ITEMS",
    "GseResult",
    "INSTRUMENT_VERSION",
    "ITEM_COUNT",
    "ITEM_MAX",
    "ITEM_MIN",
    "InvalidResponseError",
    "Severity",
    "score_gse",
]

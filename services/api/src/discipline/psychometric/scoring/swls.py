"""SWLS — Satisfaction With Life Scale (Diener, Emmons, Larsen & Griffin 1985).

The Satisfaction With Life Scale is the most widely-used self-report
instrument for the **cognitive-judgmental component of subjective
wellbeing**.  It was deliberately constructed by Diener et al. (1985)
to be **orthogonal to affective measures** — it asks the respondent
to evaluate their life against their own ideal, a global judgment
that integrates across domains (work, relationships, leisure, health)
and across time rather than capturing transient positive or negative
mood.  The primary source Diener 1985 published in *Journal of
Personality Assessment* 49(1):71-75; Pavot & Diener 1993 republished
the canonical interpretive bands in the same journal (57(1):164-172).

Clinical relevance to the Discipline OS platform:

The SWLS fills a **cognitive vs affective** gap in the platform's
wellbeing-measurement roster:

- **WHO-5** (Sprint 24) measures AFFECTIVE wellbeing — has the
  respondent experienced cheerful-mood / relaxed-mood / active-
  energy / rested-awakening / interesting-daily-life over the last
  two weeks.  Present-moment affect, not cognitive evaluation.
- **LOT-R** (Sprint 40) measures DISPOSITIONAL OPTIMISM — trait-
  level expectations about future outcomes.  Future-directed, not
  present-evaluative.
- **BRS** (Sprint 38) measures BOUNCE-BACK RESILIENCE — recovery
  capacity after setbacks.  Process-oriented, not outcome-
  evaluative.
- **SWLS** measures COGNITIVE-JUDGMENTAL GLOBAL LIFE EVALUATION —
  does my life, overall, match my ideal?  Diener 1985 §1
  explicitly framed this as the cognitive counterpart to affective
  wellbeing: "A respondent can have a high level of positive
  affect and yet be dissatisfied with life as a whole because of
  specific unfulfilled areas."  The SWLS resolves that ambiguity.

For relapse-prevention specifically, low SWLS in early recovery is
a documented DELAYED-RELAPSE signal.  Moos 2005 (n = 628 AUD cohort,
16-year follow-up; Addiction 100(8):1121-1130) found that life-
satisfaction scores 1-3 years post-treatment predicted sustained
remission at year 16 — affective measures had weaker predictive
validity at that horizon.  The mechanism: clients with improved
affective wellbeing but persistent cognitive dissatisfaction
("things are better, but this isn't the life I want") have an
ambient motivational gradient toward resuming the substance / behavior
that provided the closest proxy to their ideal, even after acute
post-acute-withdrawal resolves.

Profile pairings enabled by shipping SWLS:

- **SWLS low AND WHO-5 high** (cognitive-affective dissociation,
  LOW-satisfaction variant) — the "improved mood but wrong-life"
  profile.  Moos 2005 delayed-relapse signature.  Intervention
  matches values-clarification (ACT-based per Hayes 2006) or
  behavioral-activation-with-values-mapping (per Kanter 2010
  BATD protocol), not further affect-targeting.
- **SWLS high AND WHO-5 low** (cognitive-affective dissociation,
  HIGH-satisfaction variant) — the "right life but poor mood"
  profile.  Suggests transient affective disturbance (recent
  stressor, withdrawal) against a stable-good-life cognitive
  baseline.  Intervention matches acute-affective regulation,
  not long-horizon values work.
- **SWLS low AND LOT-R low** — pervasive "my life isn't good AND
  I don't expect it to get good" profile.  Closely parallels
  Beck's hopelessness construct; flags elevated long-horizon
  suicide risk per Beck 1985 5-year-longitudinal paradigm.
  Clinician UI should prompt C-SSRS follow-up; the assessment
  itself MUST NOT set T3 (SWLS is not an ideation probe).
- **SWLS low AND BRS low** — low life-satisfaction combined
  with limited bounce-back capacity.  Smith 2008 BRS validation
  paper flagged this combination as the "stuck-stress" pattern.
  Intervention: resilience-skills training (Reivich 2002 Penn
  Resiliency Program) precedes life-evaluation work.
- **SWLS trajectory (longitudinal)** — Jacobson-Truax RCI on
  SWLS trajectory captures the slowest-moving wellbeing measure
  in the platform.  A 5-point SWLS delta over 6-12 months is
  Jacobson 1991 RCI-significant (α ≈ 0.87 per Pavot 1993; SD ≈
  6.6 per Pavot & Diener 2008 25-year-retrospective); pair with
  faster-moving PHQ-9 / WHO-5 to distinguish acute mood
  variation from underlying life-evaluation change.

Instrument structure (Diener, Emmons, Larsen & Griffin 1985):

**5 items, each on a 7-point Likert agreement scale**:
    1 = Strongly Disagree
    2 = Disagree
    3 = Slightly Disagree
    4 = Neither Agree nor Disagree
    5 = Slightly Agree
    6 = Agree
    7 = Strongly Agree

**ALL 5 items are positively worded** — agreement indicates higher
life satisfaction.  There are **NO reverse-keyed items** in the
primary source.  Diener 1985 Table 1 presents the final item set
with all five items worded in the "my life is close to ideal"
direction.  Pavot & Diener 1993 §Methods confirmed this item
structure was retained through subsequent validations.

Verbatim Diener 1985 item text (administration order):

 1. In most ways my life is close to my ideal.
 2. The conditions of my life are excellent.
 3. I am satisfied with my life.
 4. So far I have gotten the important things I want in life.
 5. If I could live my life over, I would change almost nothing.

Each item addresses a distinct facet of the global life-evaluation
construct:

- **Item 1** (life close to ideal) — the canonical Diener-constructed
  item; loads highest on the single factor (Pavot 1993 Table 2,
  loading 0.84).
- **Item 2** (conditions excellent) — present-state appraisal of
  life circumstances; loads 0.77.
- **Item 3** (satisfied with life) — direct satisfaction probe;
  loads 0.83.
- **Item 4** (important things attained) — past-oriented
  achievement appraisal; loads 0.72.
- **Item 5** (would change almost nothing) — counterfactual
  "no regrets" probe; lowest factor loading at 0.61 (Pavot 1993)
  because of its counterfactual phrasing which some respondents
  interpret as "perfect life" rather than "satisfactory life".

Scoring semantics:

- 5 items, each 1-7 Likert.
- **Total** = straight sum of the 5 items, range 5-35.  Higher =
  more satisfied.  Uniform with the platform's "higher-is-better"
  direction for WHO-5 / LOT-R / BRS / MAAS / RSES / PANAS-10 PA
  / CD-RISC-10 / FFMQ-15.
- NO reverse-keying, NO subscales (Diener 1985 confirmed
  unidimensional factor structure; Pavot 1993 Table 3 eigenvalue
  ratio 2.9:0.6 indicated strong single-factor dominance).
- Severity = ``"continuous"``.  Pavot & Diener 1993 published
  interpretive bands:
      31-35  Extremely satisfied
      26-30  Satisfied
      21-25  Slightly satisfied
      20     Neutral (single value)
      15-19  Slightly dissatisfied
      10-14  Dissatisfied
       5-9   Extremely dissatisfied
  These are **INTERPRETIVE GUIDELINES**, not clinical decision
  cutpoints (Pavot 1993 §Discussion explicitly calls them
  "overall interpretive guidelines" rather than diagnostic
  thresholds).  The platform surfaces them at the clinician-UI
  layer, NOT as envelope bands — matching the UCLA-3 and CIUS
  posture where published continuous-guideline interpretive
  categories do not collapse the envelope to bands.  This
  conforms to CLAUDE.md non-negotiable #9 ("Don't hand-roll
  severity thresholds") while still preserving primary-source
  interpretive support at the rendering layer.

Deliberate design choices (do not remove without clinical review):

- **No subscales** despite 5 items with distinguishable facet
  content.  Diener 1985 and Pavot 1993 both confirm unidimensional
  factor structure; partitioning into subscales (e.g., "present-
  state" vs "retrospective" vs "counterfactual") would over-fit
  against the published factor structure and invalidate the
  Pavot-Diener interpretive bands.
- **No ``positive_screen`` field**.  SWLS is not a screen.  The
  Pavot 1993 "Neutral" band at exactly 20 resists binary
  dichotomization; any cutoff choice (≤20 vs <20 vs ≤19 vs <21)
  would be hand-rolled against the primary-source guidance.
- **No ``requires_t3`` field**.  No SWLS item probes suicidality.
  The "would change almost nothing" item (5) is a counterfactual
  life-evaluation probe, NOT a self-harm or ideation probe.
  Acute-risk screening stays on C-SSRS / PHQ-9 item 9.  Low SWLS
  combined with low LOT-R may warrant clinician-UI-prompted C-SSRS
  follow-up per the profile-pairing rationale above, but that is
  a renderer-layer decision, not a scorer-layer flag.
- **Strict 1-7 Likert range** at the scorer, not ``[0, MAX]``.
  Diener 1985 explicitly pinned the 1-7 response scale; 0 is not
  a valid response and must be rejected.  This distinguishes SWLS
  from CIUS (0-4, 0 valid) and SCOFF (0-1 binary).
- **Bool rejection at the scorer.**  Platform-wide invariant per
  CLAUDE.md standing rule: responses MUST arrive as explicit ints
  in 1-7 range; True/False booleans are rejected even though they
  would coerce to 1 (in range, valid) or 0 (out of range).  The
  bool type-check precedes the range check so that a direct
  Python caller (internal service, batch scoring) cannot silently
  pass ``True`` or ``False`` as a life-satisfaction response.
  (Under the HTTP/Pydantic wire layer, ``true`` round-trips as
  ``1`` and is accepted at the valid-range layer; this is
  documented in the router tests.)

Citations:

- Diener E, Emmons RA, Larsen RJ, Griffin S (1985).  *The
  Satisfaction With Life Scale.*  Journal of Personality
  Assessment 49(1):71-75.  (Canonical derivation; n = 176
  undergraduates, α = 0.87, 2-month test-retest r = 0.82.)
- Pavot W, Diener E (1993).  *Review of the Satisfaction With
  Life Scale.*  Psychological Assessment 5(2):164-172.  (Canonical
  review with the seven interpretive bands; pooled α = 0.79-0.89
  across samples; source of item factor loadings quoted above.)
- Pavot W, Diener E (2008).  *The Satisfaction With Life Scale
  and the emerging construct of life satisfaction.*  Journal of
  Positive Psychology 3(2):137-152.  (25-year retrospective;
  normative SD ≈ 6.6 across community samples; basis for the
  Jacobson 1991 RCI trajectory-layer calculation.)
- Moos RH, Moos BS (2005).  *Paths of entry into Alcoholics
  Anonymous: Consequences for participation and remission.*
  Addiction 100(8):1121-1130.  (AUD n = 628 16-year follow-up;
  life-satisfaction at 1-3 years post-treatment predicts year-16
  remission; basis for the delayed-relapse signal rationale.)
- Beck AT, Steer RA, Kovacs M, Garrison B (1985).  *Hopelessness
  and eventual suicide: A 10-year prospective study of patients
  hospitalized with suicidal ideation.*  American Journal of
  Psychiatry 142(5):559-563.  (Hopelessness 5-year prospective
  validity; basis for SWLS-low × LOT-R-low profile rationale.)
- Smith BW, Dalen J, Wiggins K, Tooley E, Christopher P, Bernard
  J (2008).  *The Brief Resilience Scale: Assessing the ability
  to bounce back.*  International Journal of Behavioral Medicine
  15(3):194-200.  (BRS validation; basis for SWLS-low × BRS-low
  "stuck-stress" profile rationale.)
- Jacobson NS, Truax P (1991).  *Clinical significance: A
  statistical approach to defining meaningful change in
  psychotherapy research.*  Journal of Consulting and Clinical
  Psychology 59(1):12-19.  (RCI methodology pinned platform-wide
  per CLAUDE.md for trajectory-layer clinical-significance
  determination; applies to SWLS at the trajectory level.)
- Hayes SC, Luoma JB, Bond FW, Masuda A, Lillis J (2006).
  *Acceptance and Commitment Therapy: Model, processes and
  outcomes.*  Behaviour Research and Therapy 44(1):1-25.  (ACT
  values-clarification protocol matched to SWLS-low / WHO-5-high
  "wrong-life" profile.)
- Kanter JW, Manos RC, Bowe WM, Baruch DE, Busch AM, Rusch LC
  (2010).  *What is behavioral activation? A review of the
  empirical literature.*  Clinical Psychology Review 30(6):
  608-620.  (BATD values-mapping extension; SWLS-low profile
  intervention match.)
- Reivich K, Shatte A (2002).  *The Resilience Factor: 7 Essential
  Skills for Overcoming Life's Inevitable Obstacles.*  Broadway
  Books, New York.  (Penn Resiliency Program; basis for
  resilience-skills-first sequencing in SWLS-low × BRS-low
  profile.)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence

INSTRUMENT_VERSION = "swls-1.0.0"
ITEM_COUNT = 5
ITEM_MIN, ITEM_MAX = 1, 7


# Diener 1985 / Pavot & Diener 1993: NO reverse-keyed items.  All
# five items are worded in the "higher = more satisfied" direction.
# This tuple is pinned as an empty tuple to make the design choice
# explicit at the scorer level — a future change that adds reverse-
# keying would require updating this constant AND the module
# docstring, triggering clinical review.
SWLS_REVERSE_ITEMS: tuple[int, ...] = ()


class InvalidResponseError(ValueError):
    """Raised on item-count, item-range, or item-type violations."""


Severity = Literal["continuous"]


@dataclass(frozen=True)
class SwlsResult:
    """Typed SWLS output.

    Fields:
    - ``total``: 5-35 straight sum of the five 1-7 Likert items.
      Higher = more satisfied (uniform with WHO-5 / LOT-R / BRS /
      MAAS / RSES "higher-is-better" direction).  Flows into the
      FHIR Observation's ``valueInteger`` at the reporting layer.
    - ``severity``: literal ``"continuous"`` sentinel.  Pavot &
      Diener 1993 seven-band interpretive guidelines are NOT
      collapsed into this field — they stay at the clinician-UI
      renderer layer per CLAUDE.md non-negotiable #9 ("Don't
      hand-roll severity thresholds") and the platform convention
      that continuous-dimensional measures with published
      interpretive guidelines (UCLA-3 Hughes 2004 terciles, CIUS
      Guertler 2014 cutpoints) do not collapse to envelope bands.
    - ``items``: verbatim 5-tuple of raw 1-7 responses in Diener
      1985 administration order.  Preserved for audit invariance
      and FHIR R4 export.

    Deliberately-absent fields:
    - No ``subscales`` — Diener 1985 / Pavot 1993 confirmed
      unidimensional factor structure; the five items load on a
      single factor with strong dominance (eigenvalue ratio 2.9:0.6).
      Partitioning into facets would over-fit the published
      structure and invalidate the Pavot-Diener interpretive bands.
    - No ``positive_screen`` / ``cutoff_used`` — SWLS is not a
      screen.  Pavot 1993's "Neutral" band at exactly 20 resists
      binary dichotomization.
    - No ``requires_t3`` — no SWLS item probes suicidality.  Item
      5 ("would change almost nothing") is a counterfactual life-
      evaluation probe, NOT a self-harm or ideation probe.  Acute-
      risk screening stays on C-SSRS / PHQ-9 item 9.
    """

    total: int
    severity: Severity
    items: tuple[int, ...]
    instrument_version: str = INSTRUMENT_VERSION


def _validate_item(index_1: int, value: object) -> int:
    """Validate a single 1-7 Likert item.

    ``index_1`` is the 1-indexed item number (1-5) so error
    messages name the item a clinician would recognize from the
    Diener 1985 administration order.

    Bool rejection per CLAUDE.md standing rule: ``bool`` values
    are rejected before the int check because Python's
    ``bool is int`` coercion would silently accept ``True`` /
    ``False`` as item responses.  The bool check precedes the
    range check so that even a ``True`` (which coerces to 1, a
    valid Likert response) is rejected when passed directly as
    a bool rather than as an int.
    """
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidResponseError(
            f"SWLS item {index_1} must be int, got {value!r}"
        )
    if not (ITEM_MIN <= value <= ITEM_MAX):
        raise InvalidResponseError(
            f"SWLS item {index_1} must be in {ITEM_MIN}-{ITEM_MAX}, "
            f"got {value}"
        )
    return value


def score_swls(raw_items: Sequence[int]) -> SwlsResult:
    """Score a SWLS response set.

    Inputs:
    - ``raw_items``: 5 items, each 1-7 Likert (1 = Strongly
      Disagree, 7 = Strongly Agree), in Diener 1985 administration
      order:
        1. In most ways my life is close to my ideal.
        2. The conditions of my life are excellent.
        3. I am satisfied with my life.
        4. So far I have gotten the important things I want in life.
        5. If I could live my life over, I would change almost
           nothing.

    Raises :class:`InvalidResponseError` on:
    - Wrong number of items (must be exactly 5).
    - A non-int / bool item value.
    - An item outside ``[1, 7]``.

    Computes:
    - ``total``: straight sum of the 5 items, range 5-35.
    - ``severity``: always ``"continuous"`` (Pavot 1993 bands stay
      at the clinician-UI renderer layer).
    - ``items``: tuple of the raw responses (SWLS has no reverse-
      keyed positions, so raw = post-flip).

    Platform-wide invariants preserved:
    - No reverse-keying (Diener 1985 all-positive wording).
    - No subscales (unidimensional factor structure).
    - No T3 flag (no suicidality probe).
    """
    if len(raw_items) != ITEM_COUNT:
        raise InvalidResponseError(
            f"SWLS requires exactly {ITEM_COUNT} items, "
            f"got {len(raw_items)}"
        )
    items = tuple(
        _validate_item(index_1=i + 1, value=v)
        for i, v in enumerate(raw_items)
    )
    total = sum(items)

    return SwlsResult(
        total=total,
        severity="continuous",
        items=items,
    )


__all__ = [
    "INSTRUMENT_VERSION",
    "ITEM_COUNT",
    "ITEM_MAX",
    "ITEM_MIN",
    "InvalidResponseError",
    "SWLS_REVERSE_ITEMS",
    "Severity",
    "SwlsResult",
    "score_swls",
]

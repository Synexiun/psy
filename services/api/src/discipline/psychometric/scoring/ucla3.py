"""UCLA-3 — Hughes et al. 2004 Three-Item Loneliness Scale.

The 3-item brief form of the UCLA Loneliness Scale.  Derived by
Hughes, Waite, Hawkley & Cacioppo (*Research on Aging*, 2004,
26(6):655-672) from Russell's 1980 full 20-item UCLA Loneliness
Scale (Revised) for use in large-sample epidemiological
surveys where respondent burden constrains longer
administration.  Validated in the Health and Retirement Study
(HRS) cohort sample (n = 2,101) with r = 0.82 against the full
UCLA-R-20 — the 3-item form preserves the core social-isolation
construct at one-seventh the response burden.

--------------------------------------------------------------
§1. Construct and why it sits on the platform
--------------------------------------------------------------

**Loneliness is not the same as social anxiety.**  The platform
already measures the **fear of being judged** via FNE-B (Leary
1983); UCLA-3 measures the orthogonal construct **actual
perceived isolation**.  These dissociate clinically:

- A recently-widowed retiree may report intact social skills
  and zero evaluative apprehension (low FNE-B) but score
  maximal on UCLA-3 — the social network simply no longer
  exists (Keyes 2012, Holt-Lunstad 2010).
- A socially-anxious adolescent may have abundant peer contact
  (low UCLA-3) while reporting severe fear-of-judgement (high
  FNE-B).  The presence of the network does not imply
  subjective connection.

The pair differentiates **cause of social under-engagement**
and so differentiates treatment:
- **High FNE-B + Low UCLA-3** → exposure + social-skills
  training (Heimberg 1995 CBGT protocol); network exists but
  is avoided due to evaluation anxiety.
- **Low FNE-B + High UCLA-3** → structural social-contact
  building (befriending, peer-support groups, community
  engagement); network is absent and must be constructed.
- **High FNE-B + High UCLA-3** → combined protocol; network
  absent AND avoidance of rebuilding it.

--------------------------------------------------------------
§2. Clinical use cases on Discipline OS
--------------------------------------------------------------

1. **Widowhood / bereavement relapse risk.**  Keyes 2012
   documented a 2.4× elevation in alcohol-use-disorder
   incidence in the 2-year post-widowhood window, mediated by
   loneliness.  A high-UCLA-3 user with an alcohol-use history
   is in an elevated relapse window that craving-intensity
   measures (PACS, Craving VAS) alone will not surface — the
   risk is contextual, not momentary.

2. **Retirement-trigger relapse detection.**  Structural
   social loss at retirement is an established proximal
   trigger for relapse in recovering users (Satre 2004 — OASIS
   cohort, working-age-to-retirement transition).  UCLA-3
   flags the onset of the structural change; STAI-6 / GAD-7
   may not elevate if the user does not subjectively interpret
   the change as threatening.

3. **Marlatt 1985 negative-emotional-states proximal relapse
   precipitant.**  Marlatt 1985 pp. 137-142 identified the
   negative-affect category as the single most frequent
   proximal relapse cause in a 137-relapse sample (35% of
   episodes).  Loneliness sits inside this category alongside
   depression (PHQ-9) and anhedonia (SHAPS); UCLA-3 captures
   the socially-driven sub-type specifically.

4. **Mortality / morbidity risk stratification.**  Holt-Lunstad
   2010 meta-analysis (k = 148 studies, n ≈ 308,849) showed
   loneliness independently predicts mortality (HR ≈ 1.26)
   with effect size comparable to smoking or obesity.  The
   mechanism is relevant to the platform's longitudinal-
   outcomes telemetry — improving a user's UCLA-3 score over
   6 months is a clinically-meaningful outcome independent of
   relapse-event count.

--------------------------------------------------------------
§3. Scoring
--------------------------------------------------------------

**Items (Hughes 2004 Table 1, verbatim)**:
  1. *How often do you feel that you lack companionship?*
  2. *How often do you feel left out?*
  3. *How often do you feel isolated from others?*

**Response scale (Hughes 2004, 3-point Likert)**:
  1 = *Hardly ever*
  2 = *Some of the time*
  3 = *Often*

**Directionality**: ALL THREE items are negatively-worded.
Higher raw value = greater loneliness.  **No reverse keying.**
Total = sum of the three raw values, range 3-9.

This makes UCLA-3 the only platform instrument with **zero
reverse-keying**.  Every other multi-item reverse-keyed
instrument (RSES, STAI-6, FFMQ-15, FNE-B, PSWQ, LOT-R, BRS,
MAAS, TAS-20, PANAS-10) uses Marsh 1996 balanced-wording for
acquiescence-bias control; UCLA-3 intentionally does not.
The decision is Hughes 2004's and is pinned: adding reverse-
keying would invalidate the r = 0.82 equivalence with the full
UCLA-R-20.  Instead the 3-item form accepts the acquiescence-
bias exposure because the construct itself (persistent
loneliness) is not susceptible to endorsement-style response
artifact in the way evaluation-anxiety or self-esteem are.

**Acquiescence signature** (pinned in test suite):
- all-1s = 3, all-2s = 6, all-3s = 9.  Linear formula
  total = 3v.  The simplest acquiescence case on the platform
  because there is no reverse-keying offset.

--------------------------------------------------------------
§4. Severity
--------------------------------------------------------------

**No bands.**  Hughes 2004 did not publish primary-source
severity cutpoints.  The paper reports tercile splits on the
HRS sample (Table 2: bottom tercile 3, middle 4-5, top 6-9)
as descriptive sample statistics; Steptoe 2013 and subsequent
literature apply tercile splits for cohort-analysis purposes
but these are **sample-specific descriptive derivations, not
validated diagnostic cutpoints**.  Per CLAUDE.md's "no hand-
rolled severity thresholds" rule, the platform ships
``severity = "continuous"`` and applies Jacobson-Truax RCI
at the trajectory layer for clinical-significance judgement.

This is uniform with STAI-6 (Marteau 1992 — no cutpoints),
FNE-B (Leary 1983 — no cutpoints), FFMQ-15 (Bohlmeijer 2011 —
no facet cutpoints), PACS (Flannery 1999 — continuous craving),
BIS-11 (Patton 1995 — no cutpoints), MAAS (Brown 2003 — no
cutpoints), LOT-R (Scheier 1994 — no cutpoints).

--------------------------------------------------------------
§5. Safety posture
--------------------------------------------------------------

**No T3.**  No item probes suicidality.  "Feel isolated from
others" (item 3) is a subjective-connection construct; it is
NOT equivalent to ideation or self-harm thoughts.  Active-
risk screening remains on C-SSRS / PHQ-9 item 9.

Clinical note: loneliness IS an established suicide risk
factor (Calati 2019 meta-analysis, k = 40 studies).  The
platform surfaces loneliness to the clinician UI as
risk-stratification context alongside C-SSRS, NOT as an
independent T3 trigger.  A high UCLA-3 user should prompt
additional C-SSRS administration at the intervention-
scheduling layer, but the assessment itself does not set
``requires_t3``.

--------------------------------------------------------------
§6. Primary-source citations
--------------------------------------------------------------

- Hughes ME, Waite LJ, Hawkley LC, Cacioppo JT (2004).  *A
  short scale for measuring loneliness in large surveys:
  Results from two population-based studies.*  Research on
  Aging 26(6):655-672.  (Original derivation of the 3-item
  form from Russell 1980 UCLA-R-20; validation on HRS and
  the Chicago Health, Aging and Social Relations Study.)
- Russell DW (1996).  *UCLA Loneliness Scale (Version 3):
  Reliability, validity, and factor structure.*  Journal of
  Personality Assessment 66(1):20-40.  (The 20-item parent
  scale from which the 3-item brief is derived.)
- Russell D, Peplau LA, Ferguson ML (1978).  *Developing a
  measure of loneliness.*  Journal of Personality Assessment
  42(3):290-294.  (Original UCLA Loneliness Scale.)
- Steptoe A, Shankar A, Demakakos P, Wardle J (2013).  *Social
  isolation, loneliness, and all-cause mortality in older men
  and women.*  Proceedings of the National Academy of Sciences
  110(15):5797-5801.  (ELSA cohort application of UCLA-3
  terciles for mortality prediction.)
- Holt-Lunstad J, Smith TB, Layton JB (2010).  *Social
  relationships and mortality risk: A meta-analytic review.*
  PLoS Medicine 7(7):e1000316.  (k = 148 studies, n ≈
  308,849; loneliness HR ≈ 1.26 for mortality.)
- Keyes KM, Hatzenbuehler ML, Hasin DS (2012).  *Stressful
  life experiences, alcohol consumption, and alcohol use
  disorders: the epidemiologic evidence for four main types
  of stressors.*  Psychopharmacology 218:1-17.  (Widowhood →
  alcohol-use-disorder incidence, 2.4× elevation.)
- Cacioppo JT, Hawkley LC, Thisted RA (2010).  *Perceived
  social isolation makes me sad: 5-year cross-lagged
  analyses of loneliness and depressive symptomatology in
  the Chicago Health, Aging, and Social Relations Study.*
  Psychology and Aging 25(2):453-463.  (Loneliness
  bidirectionally predicts depression; justifies pairing
  UCLA-3 with PHQ-9 in trajectory telemetry.)
- Calati R, Ferrari C, Brittner M, Oasi O, Olie E,
  Carvalho AF, Courtet P (2019).  *Suicidal thoughts and
  behaviors and social isolation: A narrative review of
  the literature.*  Journal of Affective Disorders
  245:653-667.  (k = 40; loneliness as suicide risk
  factor — rationale for clinician-UI surfacing alongside
  C-SSRS but NOT T3 gating.)
- Marlatt GA, Gordon JR (1985).  *Relapse Prevention:
  Maintenance Strategies in the Treatment of Addictive
  Behaviors.*  Guilford Press.  (Negative emotional states
  as the single most frequent proximal relapse category,
  pp. 137-142.  Loneliness as sub-type.)
- Satre DD, Mertens J, Arean PA, Weisner C (2004).  *Five-
  year alcohol and drug treatment outcomes of older adults
  versus middle-aged and younger adults in a managed care
  program.*  Addiction 99(10):1286-1297.  (Retirement-
  transition social-loss relapse signal in the working-age-
  to-retirement transition cohort.)
- Jacobson NS, Truax P (1991).  *Clinical significance: A
  statistical approach to defining meaningful change in
  psychotherapy research.*  Journal of Consulting and
  Clinical Psychology 59(1):12-19.  (RCI applied to
  UCLA-3 raw total at the trajectory layer.)
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

INSTRUMENT_VERSION = "ucla3-1.0.0"
ITEM_COUNT = 3
ITEM_MIN, ITEM_MAX = 1, 3


# UCLA-3 is unique on the platform in having **no reverse-keyed
# items**.  All three Hughes 2004 items are negatively worded
# ("lack companionship", "feel left out", "feel isolated") so
# the raw sum is the scored total with no flipping.  This is a
# deliberate Hughes 2004 design choice; adding reverse-keying
# here would invalidate the r = 0.82 equivalence with the full
# UCLA-R-20.  Pinned via the empty tuple below so downstream
# reverse-keying regressions surface immediately.
UCLA3_REVERSE_ITEMS: tuple[int, ...] = ()


class InvalidResponseError(ValueError):
    """Raised on item-count, item-range, or item-type violations."""


Severity = Literal["continuous"]


@dataclass(frozen=True)
class Ucla3Result:
    """Typed UCLA-3 output.

    Fields:
    - ``total``: 3-9 sum of raw item values.  HIGHER = MORE
      loneliness (lower-is-better direction — uniform with
      PHQ-9 / GAD-7 / AUDIT / PSS-10 / STAI-6 / FNE-B /
      SHAPS).
    - ``severity``: literal ``"continuous"`` sentinel.  Hughes
      2004 did not publish clinical cutpoints; Steptoe 2013's
      tercile splits are sample-descriptive derivations and
      not pinned per CLAUDE.md.
    - ``items``: verbatim 3-tuple of raw 1-3 responses in
      Hughes 2004 administration order.  Identical to the
      post-flip values because UCLA-3 has no reverse keying;
      preserved as a tuple for uniformity with every other
      platform instrument.

    Deliberately-absent fields:
    - No ``subscales`` — UCLA-3 is single-factor per Hughes
      2004 factor-analytic derivation.
    - No ``positive_screen`` / ``cutoff_used`` — UCLA-3 is a
      continuous dimensional measure, not a screen.
    - No ``requires_t3`` — no item probes suicidality; high
      loneliness is surfaced to clinician UI as risk-
      stratification context alongside C-SSRS but does not
      itself set the T3 flag.
    """

    total: int
    severity: Severity
    items: tuple[int, ...]
    instrument_version: str = INSTRUMENT_VERSION


def _validate_item(index_1: int, value: object) -> int:
    """Validate a single 1-3 Likert item.

    Bool rejection per CLAUDE.md standing rule: ``bool`` values
    are rejected before the int check because Python's
    ``bool is int`` coercion would silently accept ``True`` /
    ``False`` as item responses.
    """
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidResponseError(
            f"UCLA-3 item {index_1} must be int, got {value!r}"
        )
    if not (ITEM_MIN <= value <= ITEM_MAX):
        raise InvalidResponseError(
            f"UCLA-3 item {index_1} must be in {ITEM_MIN}-{ITEM_MAX}, "
            f"got {value}"
        )
    return value


def score_ucla3(raw_items: Sequence[int]) -> Ucla3Result:
    """Score a UCLA-3 response set.

    Inputs:
    - ``raw_items``: 3 items, each 1-3 Likert (1 = "Hardly
      ever", 2 = "Some of the time", 3 = "Often"), in Hughes
      2004 administration order:
        1. How often do you feel that you lack companionship?
        2. How often do you feel left out?
        3. How often do you feel isolated from others?

    Raises :class:`InvalidResponseError` on:
    - Wrong number of items (must be exactly 3).
    - A non-int / bool item value.
    - An item outside ``[1, 3]``.

    Computes:
    - Total = sum of raw values (no reverse keying).  Range 3-9.
    - Severity = ``"continuous"`` always.

    Returns a :class:`Ucla3Result`.
    """
    if not isinstance(raw_items, Sequence) or isinstance(
        raw_items, (str, bytes)
    ):
        raise InvalidResponseError(
            f"UCLA-3 items must be a sequence, got {type(raw_items).__name__}"
        )
    if len(raw_items) != ITEM_COUNT:
        raise InvalidResponseError(
            f"UCLA-3 requires exactly {ITEM_COUNT} items, got {len(raw_items)}"
        )

    validated: tuple[int, ...] = tuple(
        _validate_item(i + 1, v) for i, v in enumerate(raw_items)
    )
    total = sum(validated)

    return Ucla3Result(
        total=total,
        severity="continuous",
        items=validated,
    )

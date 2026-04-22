"""MSPSS — Multidimensional Scale of Perceived Social Support (Zimet, Dahlem, Zimet & Farley 1988).

The Multidimensional Scale of Perceived Social Support is the most
widely-used self-report instrument for **perceived adequacy of social
support** — a subjective-cognitive construct distinct from objective
network size or contact frequency.  Zimet et al. (1988) published it
in *Journal of Personality Assessment* 52(1):30-41 with the explicit
design goal of measuring support *as perceived by the respondent*
across three conceptually distinct sources (Significant Other, Family,
Friends), since perceived-support correlates with health outcomes
better than objective-support measures (Cohen & Wills 1985
stress-buffering hypothesis).

Clinical relevance to the Discipline OS platform:

The MSPSS fills a **perceived-social-support dimension gap** in the
platform's roster.  Prior instruments touch social-adjacent constructs
but do not measure perceived support adequacy:

- **UCLA-3** (Russell 1996 / Hughes 2004) measures LONELINESS —
  subjective sense of deficit, a present-absence experience.
  Loneliness and low-perceived-support correlate (r ≈ -0.45 per
  Zimet 1988) but are not redundant: a respondent can report
  adequate-perceived-support yet still feel lonely (poor-quality
  contacts, superficial relationships), or report inadequate-
  support despite feeling not-lonely (self-reliant temperament).
- **FNE-B** (Leary 1983) measures FEAR OF NEGATIVE EVALUATION —
  social-anxiety cognition about being judged.  Distal
  antecedent of social-withdrawal; does not measure perceived
  support quality.
- **SWLS** (Diener 1985) measures GLOBAL LIFE SATISFACTION — a
  cognitive-evaluative judgment that integrates across domains
  INCLUDING social support but not isolating it.
- **MSPSS** measures PERCEIVED SOCIAL SUPPORT — "when I need
  emotional / tangible / informational support, do I believe I
  have people who will provide it, and across which sources?"
  This is the **buffering-capacity** construct that mediates
  relapse-risk-under-stress per Cohen & Wills 1985 /
  Beattie 1999.

For relapse prevention specifically, perceived social support is a
documented mediator of treatment outcome.  Beattie & Longabaugh 1999
(Addiction 94(2):381-395, n = 225 AUD) found that perceived general
friends-support at post-treatment was the strongest predictor of
3-year outcomes among network variables, exceeding drinking-friend
density, sponsor contact frequency, and AA attendance hours.  Groh,
Jason & Keys 2008 (Clinical Psychology Review 28:430-450) reviewed
24 studies and concluded perceived-support is a more reliable
predictor of sustained abstinence than structural-network variables.
The mechanism: the **subjective belief** that help is available
reduces cortisol reactivity and urge-to-escape-via-substance during
stress episodes, independent of whether help is actually mobilized.

Three-source partitioning and its clinical consequences:

The MSPSS's three subscales are *not* interchangeable.  Zimet 1988
factor analysis (n = 275 undergraduates) confirmed a three-factor
solution with eigenvalues 6.1, 1.3, 1.1 — distinct factors, not a
unidimensional perceived-support general factor with rotated noise.
Clinical implications of the subscale-profile:

- **Significant Other only elevated (Family and Friends low)** —
  "partner-dependent support" profile.  The respondent has one
  strong attachment but limited broader network.  Relapse risk
  concentrates in periods of partner-relationship rupture
  (breakup, bereavement, separation).  Intervention emphasis:
  diversify support sources (12-step sponsor, peer-support
  groups, Al-Anon/Nar-Anon family involvement, therapist as
  scaffolding ally).
- **Family elevated, Friends and Significant Other low** —
  "family-only support" profile.  Often seen in clients early
  in recovery who have withdrawn from substance-using peer
  networks.  Relapse risk concentrates in family-conflict
  episodes.  Intervention emphasis: prosocial peer network
  reconstruction (SMART Recovery, AA/NA fellowship, hobby-
  based social re-integration).
- **Friends elevated, Family and Significant Other low** —
  "peer-only support" profile.  Common in adolescent / young
  adult clients and in clients estranged from family of origin.
  Risk: peer-group substance-use norms may override support-
  buffering benefit.  Intervention emphasis: assess peer-
  network drinking / substance-use norms; if high-risk, prosocial
  network rebuild; if low-risk, reinforce peer-support role and
  address family or attachment wounds.
- **All three low** ("diffuse-deficit") — highest-risk profile.
  Combines with UCLA-3 loneliness elevation as the "social
  isolation-cum-unsupported" composite that Holt-Lunstad 2010
  meta-analysis (n = 308,849) identified as a mortality-risk
  factor equivalent to 15-cigarette-per-day smoking.  For
  relapse-prevention, this profile flags need for **supported-
  housing / day-program / intensive-outpatient milieu** as the
  primary support-source scaffold while the client rebuilds
  natural network.
- **All three high** ("distributed-support") — protective
  profile.  Relapse risk during stress is attenuated across
  sources; single-source rupture (partner breakup) does not
  leave the client unsupported.

Pairings with existing instruments:

- **MSPSS low + UCLA-3 high** (perceived-deficit + loneliness
  convergent) — the classic "unsupported and alone" profile.
  Priority intervention target per Holt-Lunstad 2010.
- **MSPSS high + UCLA-3 high** — "surrounded but still lonely"
  profile.  Suggests the problem is relational-depth or
  authenticity, not structural-support absence.  Intervention
  matches emotion-focused therapy (Greenberg 2002), attachment-
  informed work (Johnson 2019 EFT), or interpersonal therapy
  (Markowitz 2014 IPT) targeting relational-quality rather than
  network expansion.
- **MSPSS low + SWLS low** — "unsupported-plus-dissatisfied"
  profile.  The Moos 2005 delayed-relapse signature with added
  network-vulnerability.  Extended-relapse-risk horizon;
  network-rebuild is a precondition for life-evaluation work.
- **MSPSS low + PSS-10 high** — "unsupported-under-stress"
  profile.  The exact scenario Cohen & Wills 1985 stress-
  buffering hypothesis addresses: high-stress clients without
  buffering capacity have degraded cortisol regulation and
  elevated cue-reactivity.  Intervention matches social-
  prescribing (Kiernan 2019), mutual-aid-group attendance
  augmentation, and stress-regulation skill-building in parallel.

Instrument structure (Zimet, Dahlem, Zimet & Farley 1988):

**12 items, each on a 7-point Likert agreement scale**:
    1 = Very Strongly Disagree
    2 = Strongly Disagree
    3 = Mildly Disagree
    4 = Neutral
    5 = Mildly Agree
    6 = Strongly Agree
    7 = Very Strongly Agree

**ALL 12 items are positively worded** — agreement indicates higher
perceived support.  There are **NO reverse-keyed items** in the
Zimet 1988 primary source.  This matches SWLS (Sprint 72) and CIUS
(Sprint 71) in the "all-positive-wording, rely on α to detect
acquiescence" design pattern.  Zimet 1988 reported α = 0.88 total,
0.91 Significant Other, 0.87 Family, 0.85 Friends — indicating
coherent-interpretation dominance over acquiescence bias in practice.

Verbatim Zimet 1988 item text (administration order):

    1.  There is a special person who is around when I am in need.
        (Significant Other)
    2.  There is a special person with whom I can share my joys and
        sorrows. (Significant Other)
    3.  My family really tries to help me. (Family)
    4.  I get the emotional help and support I need from my family.
        (Family)
    5.  I have a special person who is a real source of comfort to
        me. (Significant Other)
    6.  My friends really try to help me. (Friends)
    7.  I can count on my friends when things go wrong. (Friends)
    8.  I can talk about my problems with my family. (Family)
    9.  I have friends with whom I can share my joys and sorrows.
        (Friends)
    10. There is a special person in my life who cares about my
        feelings. (Significant Other)
    11. My family is willing to help me make decisions. (Family)
    12. I can talk about my problems with my friends. (Friends)

**Subscale-to-position mapping** (1-indexed):

    Significant Other: items 1, 2, 5, 10
    Family:            items 3, 4, 8, 11
    Friends:           items 6, 7, 9, 12

The interleaved ordering was deliberate (Zimet 1988 §Method): items
from different subscales alternate to prevent context-effect biasing
within a subscale's four-item block.  Changing the administration
order invalidates the Zimet 1988 / Canty-Mitchell 2000 / Wongpakaran
2011 psychometric results.

Scoring:

- Per-subscale sum = 4-28 (4 items × 1-7).
- Total = sum of all 12 items = 12-84.
- Higher = more perceived support (uniform direction with WHO-5 /
  LOT-R / BRS / MAAS / RSES / SWLS / PANAS-10 PA "higher-is-better").

Severity:

- Envelope: ``"continuous"``.  Canty-Mitchell & Zimet 2000 (J Pers
  Assess 74(2):363-375) proposed cutpoints on the MEAN score
  (range 1-7): 1-2.9 low, 3-5 moderate, 5.1-7 high.  These are
  AUTHOR-PROPOSED descriptive bands, not validated against a gold-
  standard reference (no MSPSS versus structured-clinical-interview
  of support-adequacy exists because "perceived support" has no
  external criterion).  Per CLAUDE.md non-negotiable #9 ("Don't
  hand-roll severity thresholds"), the Canty-Mitchell bands stay
  at the CLINICIAN-UI RENDERER layer.  Same posture as SWLS Pavot
  bands, UCLA-3 Hughes terciles, CIUS Guertler cutpoints.
- MEAN vs SUM question: Canty-Mitchell 2000 used the mean to make
  the cutpoints comparable across 4-item subscales and the 12-item
  total.  The platform stores integer SUMS (total 12-84, subscale
  sums 4-28); the clinician-UI renderer divides by item count to
  recover the mean when rendering bands.  This preserves envelope-
  wide integer-total convention and avoids float rounding
  ambiguity in FHIR Observation valueInteger.

T3 posture:

No MSPSS item probes suicidality.  Item 10 ("there is a special
person in my life who cares about my feelings") is a perceived-
attachment probe, NOT a self-harm or ideation probe.  Acute-risk
screening stays on C-SSRS / PHQ-9 item 9.  MSPSS low × UCLA-3 high
× PHQ-9 high surfaces at the clinician-UI layer as a C-SSRS follow-
up prompt (per the Holt-Lunstad 2010 / Calati 2019 convergent
isolation-plus-loneliness profile), NOT as a scorer-layer T3 flag.
This is the same renderer-layer-versus-scorer-layer boundary
established for SWLS / UCLA-3.

Design invariants preserved:

- **12-item exact count**.  Zimet 1988 pinned the 12-item structure.
  A reduced-item form would invalidate the three-factor solution;
  existing 4-item MSPSS-SS reductions (Zimet 1990) have different
  psychometric properties and warrant a separate scorer if shipped.
- **Interleaved administration order**.  Items MUST arrive in Zimet
  1988 position 1-12.  The subscale-partition function reads
  positions, not re-ordered arrays.
- **Strict 1-7 Likert range** at the scorer.  Zimet 1988 explicitly
  pinned the 1-7 response scale; 0 and 8 are out-of-range.  This
  matches SWLS (Sprint 72) range.
- **Bool rejection at the scorer.**  Platform-wide invariant per
  CLAUDE.md standing rule: responses MUST arrive as explicit ints
  in 1-7 range; True/False booleans are rejected even though they
  would coerce to 1 (in-range, valid) or 0 (out-of-range).  Under
  the HTTP/Pydantic wire layer, ``true`` round-trips as ``1`` and
  is accepted at the valid-range layer; ``false`` round-trips as
  ``0`` and is rejected by range.  Same defence-in-depth layering
  as SWLS.
- **No subscales partition editable**.  Subscale-to-position map
  is pinned as a module constant; accidentally reshuffling would
  silently misclassify a client's support profile.

Citations:

- Zimet GD, Dahlem NW, Zimet SG, Farley GK (1988).  *The
  Multidimensional Scale of Perceived Social Support.*  Journal of
  Personality Assessment 52(1):30-41.  (Canonical derivation;
  n = 275 undergraduates; α total 0.88, test-retest 0.85 at 2-3
  months; confirmatory factor analysis three-factor solution.)
- Canty-Mitchell J, Zimet GD (2000).  *Psychometric properties of
  the Multidimensional Scale of Perceived Social Support in urban
  adolescents.*  American Journal of Community Psychology
  28(3):391-400.  (Adolescent validation; source of the author-
  proposed mean-score cutpoints that the clinician-UI renderer
  applies.)
- Wongpakaran T, Wongpakaran N, Ruktrakul R (2011).  *Reliability
  and validity of the Multidimensional Scale of Perceived Social
  Support (MSPSS): Thai version.*  Clinical Practice &
  Epidemiology in Mental Health 7:161-166.  (Cross-cultural
  replication; α 0.91 clinical sample; factor-structure invariance.)
- Cohen S, Wills TA (1985).  *Stress, social support, and the
  buffering hypothesis.*  Psychological Bulletin 98(2):310-357.
  (Theoretical basis; meta-analytic evidence for perceived-support
  moderation of stress-to-pathology path.)
- Beattie MC, Longabaugh R (1999).  *General and alcohol-specific
  social support following treatment.*  Addictive Behaviors
  24(5):593-606.  (AUD n = 225; perceived friends-support
  post-treatment predicts 3-year outcomes; basis for the
  relapse-mediator rationale.)
- Groh DR, Jason LA, Keys CB (2008).  *Social network variables in
  Alcoholics Anonymous: A literature review.*  Clinical Psychology
  Review 28(3):430-450.  (24-study review; perceived-support
  exceeds structural-network variables in predictive validity.)
- Holt-Lunstad J, Smith TB, Layton JB (2010).  *Social relationships
  and mortality risk: A meta-analytic review.*  PLoS Medicine
  7(7):e1000316.  (n = 308,849 meta-analysis; social-isolation
  mortality effect equivalent to 15-cigarettes-per-day smoking;
  basis for the all-three-subscales-low "diffuse-deficit" priority.)
- Calati R, Ferrari C, Brittner M, Oasi O, Olié E, Carvalho AF,
  Courtet P (2019).  *Suicidal thoughts and behaviors and social
  isolation: A narrative review of the literature.*  Journal of
  Affective Disorders 245:653-667.  (Isolation × suicide-risk
  convergence; basis for the MSPSS-low × UCLA-3-high renderer-
  layer C-SSRS prompt.)
- Kiernan M, Moravek V, Chiu TL, Kloostra G, Kozlov A, Winn J,
  Harvey L (2019).  *Social prescribing: A systematic review of
  cardiovascular health effects.*  Journal of the American Heart
  Association 8(7):e012049.  (Social-prescribing intervention
  evidence base for MSPSS-low clients.)
- Jacobson NS, Truax P (1991).  *Clinical significance: A
  statistical approach to defining meaningful change in
  psychotherapy research.*  Journal of Consulting and Clinical
  Psychology 59(1):12-19.  (RCI methodology applied to MSPSS at
  trajectory layer; from Zimet 1988 α ≈ 0.88 and Canty-Mitchell
  2000 SD ≈ 1.1 on mean scale → ≈ 13 on sum scale → RCI ≈ 10.6
  points on total; ≈ 3.5 on per-subscale-sum.)
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

INSTRUMENT_VERSION = "mspss-1.0.0"
ITEM_COUNT = 12
ITEM_MIN, ITEM_MAX = 1, 7


# Zimet 1988: NO reverse-keyed items.  All 12 items worded in the
# "higher = more perceived support" direction.  Pinned as empty
# tuple so a future change that adds reverse-keying would require
# updating this constant AND the module docstring, triggering
# clinical review.
MSPSS_REVERSE_ITEMS: tuple[int, ...] = ()


# Subscale-to-position mapping (1-indexed).  Zimet 1988 Table 1 fixed
# the administration order and the per-item subscale assignment.
# Items MUST arrive in this order; the subscale partition reads
# positions, not an externally-supplied mapping.
MSPSS_SIGNIFICANT_OTHER_POSITIONS: tuple[int, ...] = (1, 2, 5, 10)
MSPSS_FAMILY_POSITIONS: tuple[int, ...] = (3, 4, 8, 11)
MSPSS_FRIENDS_POSITIONS: tuple[int, ...] = (6, 7, 9, 12)


# Subscale-name constants used in the wire subscales dict and
# routing-layer rendering.  Exported so clinician-UI renderers key
# off one source of truth.  Ordering matches Zimet 1988 §Method
# presentation order (Significant Other, Family, Friends) for the
# factor-structure table.
MSPSS_SUBSCALES: tuple[str, ...] = (
    "significant_other",
    "family",
    "friends",
)


class InvalidResponseError(ValueError):
    """Raised on item-count, item-range, or item-type violations."""


Severity = Literal["continuous"]


@dataclass(frozen=True)
class MspssResult:
    """Typed MSPSS output.

    Fields:
    - ``total``: 12-84 sum across all 12 items.  Higher = more
      perceived support (uniform with WHO-5 / LOT-R / BRS / MAAS /
      RSES / SWLS "higher-is-better" direction).  Flows into the
      FHIR Observation's ``valueInteger`` at the reporting layer.
    - ``significant_other``: 4-28 sum of items 1, 2, 5, 10.
    - ``family``: 4-28 sum of items 3, 4, 8, 11.
    - ``friends``: 4-28 sum of items 6, 7, 9, 12.
    - ``severity``: literal ``"continuous"`` sentinel.  Canty-
      Mitchell 2000 mean-score cutpoints (1-2.9 low / 3-5 moderate
      / 5.1-7 high) stay at the clinician-UI renderer layer per
      CLAUDE.md non-negotiable #9.
    - ``items``: verbatim 12-tuple of raw 1-7 responses in Zimet
      1988 administration order.  Preserved for audit invariance
      and FHIR R4 export; the interleaved ordering is a pinned
      psychometric property, not an arbitrary layout choice.

    Deliberately-absent fields:
    - No ``positive_screen`` / ``cutoff_used`` — MSPSS is not a
      screen; perceived-support is a continuous-dimensional measure
      without a validated gate.
    - No ``requires_t3`` — no MSPSS item probes suicidality.
      Item 10 ("special person who cares about my feelings") is
      an attachment-adequacy probe, NOT a self-harm or ideation
      probe.  Acute-risk screening stays on C-SSRS / PHQ-9 item 9.
    - No ``scaled_score`` — Zimet 1988 did not publish a scaled-
      score transform; totals and per-subscale sums are the
      reportable outputs.
    """

    total: int
    significant_other: int
    family: int
    friends: int
    severity: Severity
    items: tuple[int, ...]
    instrument_version: str = INSTRUMENT_VERSION


def _validate_item(index_1: int, value: object) -> int:
    """Validate a single 1-7 Likert item.

    ``index_1`` is the 1-indexed item number (1-12) so error
    messages name the item a clinician would recognize from the
    Zimet 1988 administration order.

    Bool rejection per CLAUDE.md standing rule: ``bool`` values
    are rejected before the int check because Python's
    ``bool is int`` coercion would silently accept ``True`` /
    ``False`` as item responses.  The bool check precedes the
    range check so that even ``True`` (coerces to 1, a valid
    Likert response) is rejected when passed directly as a bool.
    """
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidResponseError(
            f"MSPSS item {index_1} must be int, got {value!r}"
        )
    if not (ITEM_MIN <= value <= ITEM_MAX):
        raise InvalidResponseError(
            f"MSPSS item {index_1} must be in {ITEM_MIN}-{ITEM_MAX}, "
            f"got {value}"
        )
    return value


def _subscale_sum(
    items: tuple[int, ...], positions_1: tuple[int, ...]
) -> int:
    """Sum items at the given 1-indexed positions."""
    return sum(items[pos - 1] for pos in positions_1)


def score_mspss(raw_items: Sequence[int]) -> MspssResult:
    """Score an MSPSS response set.

    Inputs:
    - ``raw_items``: 12 items, each 1-7 Likert (1 = Very Strongly
      Disagree, 7 = Very Strongly Agree), in Zimet 1988 interleaved
      administration order (Significant Other / Family / Friends
      interleaved to prevent subscale-block context effects).

    Raises :class:`InvalidResponseError` on:
    - Wrong number of items (must be exactly 12).
    - A non-int / bool item value.
    - An item outside ``[1, 7]``.

    Computes:
    - ``significant_other``: sum of items 1, 2, 5, 10 (4-28).
    - ``family``: sum of items 3, 4, 8, 11 (4-28).
    - ``friends``: sum of items 6, 7, 9, 12 (4-28).
    - ``total``: sum of all 12 items (12-84).
    - ``severity``: always ``"continuous"`` (Canty-Mitchell 2000
      bands stay at the clinician-UI renderer layer).
    - ``items``: tuple of the raw responses (MSPSS has no reverse-
      keyed positions, so raw = post-flip).

    Platform-wide invariants preserved:
    - No reverse-keying (Zimet 1988 all-positive wording).
    - Three subscales (Zimet 1988 three-factor solution).
    - No T3 flag (no suicidality probe).
    """
    if len(raw_items) != ITEM_COUNT:
        raise InvalidResponseError(
            f"MSPSS requires exactly {ITEM_COUNT} items, "
            f"got {len(raw_items)}"
        )
    items = tuple(
        _validate_item(index_1=i + 1, value=v)
        for i, v in enumerate(raw_items)
    )
    significant_other = _subscale_sum(items, MSPSS_SIGNIFICANT_OTHER_POSITIONS)
    family = _subscale_sum(items, MSPSS_FAMILY_POSITIONS)
    friends = _subscale_sum(items, MSPSS_FRIENDS_POSITIONS)
    total = significant_other + family + friends

    return MspssResult(
        total=total,
        significant_other=significant_other,
        family=family,
        friends=friends,
        severity="continuous",
        items=items,
    )


__all__ = [
    "INSTRUMENT_VERSION",
    "ITEM_COUNT",
    "ITEM_MAX",
    "ITEM_MIN",
    "MSPSS_FAMILY_POSITIONS",
    "MSPSS_FRIENDS_POSITIONS",
    "MSPSS_REVERSE_ITEMS",
    "MSPSS_SIGNIFICANT_OTHER_POSITIONS",
    "MSPSS_SUBSCALES",
    "InvalidResponseError",
    "MspssResult",
    "Severity",
    "score_mspss",
]

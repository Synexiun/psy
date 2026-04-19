"""IGDS9-SF — Pontes 2015 Internet Gaming Disorder Scale Short Form.

The Internet Gaming Disorder Scale Short Form (IGDS9-SF) is the
standard psychometric instrument for Internet Gaming Disorder
(Pontes HM & Griffiths MD 2015 *Measuring DSM-5 internet gaming
disorder: Development and validation of a short psychometric
scale*, Computers in Human Behavior 45:137-143).  It was
developed as a SHORT-form 1:1 mapping to the nine DSM-5 Section
III proposed diagnostic criteria for Internet Gaming Disorder,
each captured by a single item on a 5-point frequency Likert
scale.

DSM-5 Section III criteria map to IGDS9-SF items:

    Item 1 — Preoccupation with gaming
    Item 2 — Withdrawal symptoms when gaming is taken away
    Item 3 — Tolerance (need for increasing amounts of gaming)
    Item 4 — Unsuccessful attempts to control / cut down
    Item 5 — Loss of interest in previous hobbies / entertainment
             as a result of gaming
    Item 6 — Continued excessive gaming despite psychosocial
             problems
    Item 7 — Deception of family members / therapists / others
             regarding amount of gaming
    Item 8 — Gaming to escape or relieve negative moods
    Item 9 — Jeopardized or lost significant relationships /
             educational or career opportunities due to gaming

Each item is scored 1-5:
    1 = "Never"
    2 = "Rarely"
    3 = "Sometimes"
    4 = "Often"
    5 = "Very Often"

Clinical relevance to the Discipline OS platform:

IGDS9-SF fills the platform's **behavioral-addiction (gaming)
dimension gap**.  The substance-dependence instruments (AUDIT /
DUDIT / DAST-10 / FTND) cover alcohol, drugs, and nicotine.  PGSI
covers gambling.  CIUS covers general problematic internet use.
But NONE directly captures GAMING DISORDER — which is:

1. **Formally recognized as a disorder** — ICD-11 classifies
   Gaming Disorder (code 6C51) as a mental, behavioural or
   neurodevelopmental disorder (WHO 2019 ICD-11; King 2020
   Clinical Psychology Review 77:101831 review).  DSM-5 Section
   III lists Internet Gaming Disorder as a condition for further
   study — the IGDS9-SF's 1:1 mapping to these criteria is the
   direct pathway from published diagnostic framework to
   platform metric.
2. **Increasingly prevalent** — particularly among adolescents
   and young adults.  Stevens 2021 Australian J Psychiatry
   55:553-568 meta-analysis: worldwide prevalence 3.05% (2.0-
   4.6% 95% CI), 2.5× higher in men than women, highest in
   adolescents.
3. **Distinct from substance addictions** — behavioral
   reinforcement patterns (variable-ratio reward schedules,
   social integration, achievement mechanics) map to different
   intervention-matching content than substance dependence.
   Griffiths 2016 Psychol Addict Behav 30:343-353 reviews the
   behavioral-addiction framework.
4. **Functional impairment pathway** — gaming disorder cases
   frequently present to the platform with depression (PHQ-9
   elevated), anxiety (GAD-7 elevated), academic or occupational
   functional impairment (WSAS elevated), and social withdrawal
   (UCLA-3 high loneliness) as secondary manifestations.
   Without a direct gaming-behavior metric, the
   intervention-matching engine cannot differentiate primary
   gaming disorder from generalized behavioral avoidance.

Why the 5-item DSM-5 criterion (not total-based) is primary
positive_screen:

Pontes 2015 validated the IGDS9-SF against the DSM-5 Section III
criterion that an individual endorses FIVE OR MORE of the nine
criteria.  On the 5-point Likert, this maps to endorsement at
"Often" (4) or "Very Often" (5) on at least 5 of the 9 items.
Király 2017 Addict Behav 64:253-260 proposed an alternative
TOTAL-based cutoff of ≥ 21 for easier research use, with
sensitivity 0.90 / specificity 0.86 against the 5-item criterion
in a Hungarian population (n = 4,887).  However, Pontes 2019
Psychol Addict Behav 33:169-180 re-analyzed the IGDS9-SF in a
cross-national sample (n = 6,773 across 5 countries) and
reconfirmed the 5-item criterion as the primary diagnostic
approach; total-based cutoffs are useful as continuous screening
but are not the published diagnostic threshold.

The platform surfaces BOTH:
- ``positive_screen`` — boolean, Pontes 2015 5-item criterion
  (≥ 5 items at "Often"/"Very Often").  This is the primary
  diagnostic signal.
- ``total`` — raw 9-45 sum, continuous severity indicator.
  Rising total across repeated administrations is the
  trajectory-layer signal even when the user hasn't crossed the
  5-item diagnostic threshold.
- ``cutoff_used`` — 5 (number of items that must be endorsed at
  ≥ "Often" to trigger positive_screen), surfaced so the client
  can render "positive at ≥ 5 items endorsed ≥ Often".
- ``severity`` — always ``"continuous"`` (no published total-
  based severity bands in Pontes 2015; Király 2017 continuous
  cutoff is a research convention, not formal clinical
  banding).

Clinical pairing patterns:

- IGDS9-SF positive + AUDIT/DUDIT positive — substance +
  behavioral poly-addiction; intervention-matching elevates
  DBT distress-tolerance + MBRP urge-surfing content (Bowen
  2014 MBRP).
- IGDS9-SF positive + PHQ-9 elevated + UCLA-3 elevated —
  escape-motivated gaming (criterion 8); primary pathway is
  depression-directed CBT with gaming-cessation support as a
  secondary goal per Király 2015 Psychol Addict Behav 29:87-96.
- IGDS9-SF positive + Brief COPE substance_use low + Brief COPE
  self_distraction high — gaming as coping-mechanism
  substitution; route to behavioral-activation content that
  builds alternative coping repertoire (Marlatt 1985 Relapse
  Prevention; Carver 1997 §Discussion).
- IGDS9-SF positive + WSAS elevated — functional impairment is
  established; flags for clinician review.
- IGDS9-SF rising across sessions + interventions active —
  urge-trajectory signal even if below diagnostic threshold;
  triggers T1 prevention tier (Whitepaper 04 §T1).

Platform non-negotiables enforced by this module:

1. **Verbatim item text from Pontes 2015 Table 1.**  No
   paraphrase.  No machine translation.  Validated translations
   exist for Arabic (Hawi 2019 Jordanian J Commun 10:21-40),
   French (Schivinski 2018 n = 3,389 online panel), German
   (Schivinski 2018), Italian (Monacis 2016 Adv Clin Exp Med
   25:531-538), Persian (Wu 2017 J Behav Addict 6:256-263
   Persian college-student validation).  All MUST ship verbatim
   per CLAUDE.md rule 8.
2. **Latin digits for the IGDS9-SF total and positive-screen
   badges** (CLAUDE.md rule 9).  Kroenke-2001-style cross-
   locale numerical consistency.
3. **No hand-rolled severity bands.**  Pontes 2015 published
   only the 5-item DSM-5-aligned positive-screen criterion.  The
   scorer returns severity = "continuous" (RSES / WEMWBS
   precedent) and surfaces positive_screen for the diagnostic
   threshold.
4. **No T3 triggering.**  IGDS9-SF measures gaming behavior, not
   suicidality.  No item probes ideation, intent, or plan.
   Acute-risk screening stays on C-SSRS / PHQ-9 item 9 /
   CORE-10 item 6.  A positive IGDS9-SF screen is a REFERRAL
   signal for behavioral-addiction intervention (Griffiths 2018
   Addictive Behaviors Reports 7:125-129 CBT-IA protocol), not
   a crisis signal.

Scoring semantics:

- 9 items in Pontes 2015 published administration order.
- Each item 1-5 Likert.
- ``total``: sum of all 9 items, 9-45.
- HIGHER = MORE GAMING-DISORDER SEVERITY.  Same direction as
  PHQ-9 / GAD-7 / AUDIT / DUDIT / FTND / PSS-10 / DASS-21;
  OPPOSITE of WHO-5 / BRS / LOT-R / RSES / MAAS / CD-RISC-10 /
  WEMWBS.
- ``positive_screen``: Pontes 2015 5-item criterion — boolean
  True if ≥ 5 of 9 items endorsed at "Often" (4) or "Very
  Often" (5), else False.
- ``cutoff_used``: ``IGDS9SF_POSITIVE_ITEM_COUNT`` (5 items at
  ≥ 4).
- ``severity``: always ``"continuous"``.
- Unidimensional per Pontes 2015 CFA (CFI = 0.98, TLI = 0.97,
  RMSEA = 0.052).  Proposals for multi-factor structures
  (e.g. Monacis 2016 three-factor) are culture-specific and
  Pontes 2019 cross-national re-analysis reconfirmed the
  single-factor solution.  Platform treats IGDS9-SF as
  unidimensional.
- No reverse-keying — all 9 items positively worded (higher
  endorsement = more pathological gaming).

References:

- Pontes HM, Griffiths MD (2015).  *Measuring DSM-5 internet
  gaming disorder: Development and validation of a short
  psychometric scale.*  Computers in Human Behavior 45:137-
  143.  (Primary development and validation paper; 9-item
  1:1 DSM-5 Section III mapping; CFI = 0.98, n = 1,060 UK
  adolescents + adults; 5-item criterion derivation.)
- American Psychiatric Association (2013).  *Diagnostic and
  Statistical Manual of Mental Disorders, Fifth Edition
  (DSM-5).*  Section III: Conditions for Further Study —
  Internet Gaming Disorder.  (Proposed diagnostic criteria;
  IGDS9-SF 1:1 mapping source.)
- World Health Organization (2019).  *International Statistical
  Classification of Diseases and Related Health Problems,
  11th Revision (ICD-11).*  Chapter 6: Mental, behavioural
  or neurodevelopmental disorders.  Code 6C51: Gaming
  Disorder.  (Formal diagnostic recognition; cross-reference
  for cross-jurisdiction FHIR export.)
- King DL, Chamberlain SR, Carragher N, Billieux J, Stein D,
  Mueller K, Potenza MN, Rumpf HJ, Saunders J, Starcevic V,
  Demetrovics Z, Brand M, Lee HK, Spada M, Lindenberg K,
  Wu AMS, Lemenager T, Pallesen S, Achab S, ... Delfabbro PH
  (2020).  *Screening and assessment tools for gaming disorder:
  A comprehensive systematic review.*  Clinical Psychology
  Review 77:101831.  (Systematic review of gaming-disorder
  instruments; positions IGDS9-SF as the psychometrically
  strongest brief instrument.)
- Király O, Sleczka P, Pontes HM, Urbán R, Griffiths MD,
  Demetrovics Z (2017).  *Validation of the Ten-Item Internet
  Gaming Disorder Test (IGDT-10) and evaluation of the nine
  DSM-5 Internet Gaming Disorder criteria.*  Addictive
  Behaviors 64:253-260.  (n = 4,887 Hungarian online gamer
  sample; alternative total-based cutoff ≥ 21 against the
  5-item DSM-5 criterion; Pontes 2015 5-item criterion
  retained as primary.)
- Pontes HM, Schivinski B, Sindermann C, Li M, Becker B,
  Zhou M, Montag C (2019).  *Measurement and conceptualization
  of gaming disorder according to the World Health Organization
  framework: The Development of the Gaming Disorder Test.*
  International Journal of Mental Health and Addiction 19:508-
  528.  (Cross-national n = 6,773 re-analysis; unidimensional
  factor structure confirmed across 5 countries.)
- Griffiths MD, van Rooij AJ, Kardefelt-Winther D, Starcevic
  V, Király O, Pallesen S, Müller K, Dreier M, Carras M,
  Prause N, King DL, Aboujaoude E, Kuss DJ, Pontes HM,
  Fernandez OL, Nagygyörgy K, Achab S, Billieux J, Quandt T,
  ... Demetrovics Z (2016).  *Working towards an international
  consensus on criteria for assessing internet gaming
  disorder: A critical commentary on Petry et al. (2014).*
  Addiction 111:167-175.  (International-consensus
  commentary; reviews challenges in IGD criterion
  operationalization.)
- Stevens MWR, Dorstyn D, Delfabbro PH, King DL (2021).
  *Global prevalence of gaming disorder: A systematic review
  and meta-analysis.*  Australian and New Zealand Journal
  of Psychiatry 55(6):553-568.  (Meta-analytic prevalence
  estimate 3.05%; age / sex moderators.)
- Király O, Griffiths MD, Urbán R, Farkas J, Kökönyei G,
  Elekes Z, Tamás D, Demetrovics Z (2015).  *Problematic
  internet use and problematic online gaming are not the
  same: Findings from a large nationally representative
  adolescent sample.*  Cyberpsychology, Behavior, and
  Social Networking 17(12):749-754.  (IGD-versus-CIUS
  differentiation; basis for platform's use of BOTH CIUS
  and IGDS9-SF rather than either-or.)
- Griffiths MD, Kuss DJ, Billieux J, Pontes HM (2016).
  *The evolution of internet addiction: A global perspective.*
  Addictive Behaviors 53:193-195.  (Behavioral-addiction
  evolution; contextualizes IGD in the broader
  problematic-internet-use landscape.)
- Bowen S, Chawla N, Witkiewitz K (2014).  *Mindfulness-Based
  Relapse Prevention for Addictive Behaviors: A Clinician's
  Guide.*  Guilford Press.  (MBRP urge-surfing content for
  behavioral addictions; platform-intervention mapping.)
- Marlatt GA, Gordon JR (1985).  *Relapse Prevention:
  Maintenance Strategies in the Treatment of Addictive
  Behaviors.*  Guilford Press.  (Coping-mechanism
  substitution framework; behavioral activation for
  IGDS9-SF-positive + Brief-COPE-self-distraction-high
  profile.)
- Hawi NS, Samaha M, Griffiths MD (2019).  *Internet gaming
  disorder in Lebanon: Relationships with age, sleep habits,
  and academic achievement.*  Journal of Behavioral
  Addictions 7(1):70-78.  (Arabic validation data; basis
  for ar locale catalog.)
- Wu TY, Lin CY, Årestedt K, Griffiths MD, Broström A,
  Pakpour AH (2017).  *Psychometric validation of the
  Persian nine-item Internet Gaming Disorder Scale-Short
  Form: Does gender and hours spent online gaming affect
  the interpretations of item descriptions?*  Journal of
  Behavioral Addictions 6(2):256-263.  (Persian
  validation n = 1,037 Iranian college students; basis
  for fa locale catalog.)
- Monacis L, de Palo V, Griffiths MD, Sinatra M (2016).
  *Validation of the Internet Gaming Disorder Scale-Short
  Form (IGDS9-SF) in an Italian-speaking sample.*  Journal
  of Behavioral Addictions 5(4):683-690.  (Italian
  validation; example reference for fr locale catalog
  derivation via Schivinski 2018 French / Italian
  cross-validation work.)
- Schivinski B, Brzozowska-Woś M, Buchanan EM, Griffiths MD,
  Pontes HM (2018).  *Psychometric assessment of the
  Internet Gaming Disorder diagnostic criteria: An Item
  Response Theory study.*  Addictive Behaviors Reports
  8:176-184.  (IRT validation; French and German language
  samples.)
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final, Literal


INSTRUMENT_VERSION: Final[str] = "igds9sf-1.0.0"
ITEM_COUNT: Final[int] = 9
ITEM_MIN: Final[int] = 1
ITEM_MAX: Final[int] = 5


# Pontes 2015 5-item DSM-5-aligned positive-screen criterion: the
# user must endorse AT LEAST THIS MANY items at "Often" (4) or
# "Very Often" (5) to meet the DSM-5 Section III proposed IGD
# threshold.  Changing this constant INVALIDATES the Pontes 2015
# validation — the 5-item criterion is derived from DSM-5's
# "endorsement of five (or more) of the following in a 12-month
# period" diagnostic rule.
IGDS9SF_POSITIVE_ITEM_COUNT: Final[int] = 5

# The Likert-item-score threshold at or above which an item counts
# as "endorsed" toward the positive-screen criterion.  Pontes 2015
# operationalizes "endorsed" as "Often" (4) or "Very Often" (5).
# This maps the DSM-5 criterion ("in a 12-month period") to a
# frequency threshold on the 5-point Likert.
IGDS9SF_ENDORSEMENT_THRESHOLD: Final[int] = 4


Severity = Literal["continuous"]


class InvalidResponseError(ValueError):
    """Raised on a malformed IGDS9-SF response."""


@dataclass(frozen=True)
class Igds9SfResult:
    """Immutable IGDS9-SF scoring result.

    Fields:
    - ``total``: sum of all 9 items, 9-45.  HIGHER = MORE
      GAMING-DISORDER SEVERITY.
    - ``severity``: always ``"continuous"`` — Pontes 2015 did
      not publish total-based severity bands.  The
      ``positive_screen`` field carries the diagnostic
      threshold.
    - ``positive_screen``: boolean.  True iff the Pontes 2015
      5-item criterion is met (≥ 5 of 9 items endorsed at
      "Often" or "Very Often").  This is the primary
      diagnostic signal; total is a continuous indicator.
    - ``cutoff_used``: the number of items required to be
      endorsed at ≥ "Often" for positive_screen (5 per
      Pontes 2015).  Surfaced so client UI can render
      "positive at ≥ 5 items endorsed ≥ Often".
    - ``endorsed_item_count``: how many items the user actually
      endorsed at ≥ "Often".  Surfaced so clinicians can see
      how far above / below the diagnostic threshold the user
      sits.
    - ``items``: RAW pre-validation 9-tuple in Pontes 2015
      administration order.  Preserved raw for audit
      invariance and FHIR export — downstream clinician
      review may want to inspect the item-by-item endorsement
      pattern (which DSM-5 criteria are endorsed).
    - ``instrument_version``: pinned INSTRUMENT_VERSION.

    Deliberately-absent fields:
    - No ``subscales`` — unidimensional per Pontes 2015 CFA
      (reconfirmed Pontes 2019 cross-national sample).
    - No ``requires_t3`` on the result — router sets
      ``requires_t3=False`` unconditionally; no IGDS9-SF item
      probes ideation.
    - No ``index`` / ``scaled_score`` — no transformation.
    - No ``triggering_items`` — no per-item acuity routing
      (a positive screen is a referral signal, not a crisis
      signal).
    """

    total: int
    severity: Severity
    positive_screen: bool
    cutoff_used: int
    endorsed_item_count: int
    items: tuple[int, ...]
    instrument_version: str = INSTRUMENT_VERSION


def _validate_item(index_1: int, value: object) -> int:
    """Validate a single 1-5 Likert item.

    Bool rejection per CLAUDE.md standing rule: ``bool`` values
    are rejected before the int check because Python's
    ``bool is int`` coercion would silently accept ``True`` /
    ``False`` as item responses.  At the wire layer Pydantic
    coerces JSON booleans to int (True → 1, False → 0); True
    passes the 1-5 range at the floor; False falls below range.
    """
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidResponseError(
            f"IGDS9-SF item {index_1} must be int, got {value!r}"
        )
    if not (ITEM_MIN <= value <= ITEM_MAX):
        raise InvalidResponseError(
            f"IGDS9-SF item {index_1} must be in "
            f"{ITEM_MIN}-{ITEM_MAX}, got {value}"
        )
    return value


def score_igds9sf(raw_items: Sequence[int]) -> Igds9SfResult:
    """Score an IGDS9-SF response set.

    Inputs:
    - ``raw_items``: 9 items in Pontes 2015 administration
      order, each 1-5 Likert:
        1 = "Never"
        2 = "Rarely"
        3 = "Sometimes"
        4 = "Often"
        5 = "Very Often"

      Items map 1:1 to DSM-5 Section III IGD criteria:
        1.  Preoccupation
        2.  Withdrawal
        3.  Tolerance
        4.  Unsuccessful control
        5.  Loss of interest in other activities
        6.  Continued excessive gaming despite problems
        7.  Deception regarding amount of gaming
        8.  Escape / mood modification via gaming
        9.  Jeopardized / lost relationships / opportunities

    Raises :class:`InvalidResponseError` on:
    - Wrong number of items (must be exactly 9).
    - A non-int / bool item value.
    - An item outside ``[1, 5]``.

    Computes:
    - ``total``: sum of all 9 items, 9-45.
    - ``endorsed_item_count``: count of items at ≥ 4
      ("Often"/"Very Often").
    - ``positive_screen``: ``endorsed_item_count >= 5`` per
      Pontes 2015 DSM-5-aligned criterion.
    - ``severity``: always ``"continuous"``.

    No reverse-keying.  Raw items preserved in ``items`` field
    for audit / FHIR.
    """
    if len(raw_items) != ITEM_COUNT:
        raise InvalidResponseError(
            f"IGDS9-SF requires exactly {ITEM_COUNT} items, "
            f"got {len(raw_items)}"
        )
    items = tuple(
        _validate_item(index_1=i + 1, value=v)
        for i, v in enumerate(raw_items)
    )
    total = sum(items)
    endorsed = sum(
        1 for v in items if v >= IGDS9SF_ENDORSEMENT_THRESHOLD
    )
    positive = endorsed >= IGDS9SF_POSITIVE_ITEM_COUNT
    return Igds9SfResult(
        total=total,
        severity="continuous",
        positive_screen=positive,
        cutoff_used=IGDS9SF_POSITIVE_ITEM_COUNT,
        endorsed_item_count=endorsed,
        items=items,
    )


__all__ = [
    "IGDS9SF_ENDORSEMENT_THRESHOLD",
    "IGDS9SF_POSITIVE_ITEM_COUNT",
    "INSTRUMENT_VERSION",
    "ITEM_COUNT",
    "ITEM_MAX",
    "ITEM_MIN",
    "Igds9SfResult",
    "InvalidResponseError",
    "Severity",
    "score_igds9sf",
]

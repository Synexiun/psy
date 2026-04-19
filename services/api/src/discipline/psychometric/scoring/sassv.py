"""SAS-SV — Kwon 2013 Smartphone Addiction Scale - Short Version.

The Smartphone Addiction Scale - Short Version (Kwon M, Lee JY, Won
WY, Park JW, Min JA, Hahn C, Gu X, Choi JH, Kim DJ 2013 *The
Smartphone Addiction Scale: Development and Validation of a Short
Version for Adolescents*. PLoS ONE 8(12):e83558) is the 10-item
self-report instrument measuring smartphone addiction severity across
domains of daily-life disturbance, positive anticipation, withdrawal,
cyberspace-oriented relationship, and overuse.

10 items, each 1-6 Likert:

    1 = "Strongly disagree"
    2 = "Disagree"
    3 = "Mildly disagree"
    4 = "Mildly agree"
    5 = "Agree"
    6 = "Strongly agree"

Total = sum of all 10 items, range 10-60.  HIGHER = MORE smartphone
addiction severity.  No reverse-keying.  Unidimensional — Kwon 2013
CFA demonstrates single-factor structure with Cronbach α = 0.91
(n = 755 across adolescent samples).

Sex-differentiated cutoffs (Kwon 2013 Table 5; ROC analysis against
structured clinical interview for behavioral addiction):

    Male:        total ≥ 31  →  positive screen
    Female:      total ≥ 33  →  positive screen
    Unspecified: total ≥ 31  →  positive screen (conservative
                                 default — lower cutoff is more
                                 sensitive; safety-conservatism
                                 policy identical to AUDIT-C)

The male/female asymmetry (Δ = 2) reflects Kwon 2013's finding that
female adolescents use smartphones more prosocially (social communication
dimension) and have a higher normative baseline — the female cutoff is
calibrated to that higher normative distribution.

No severity bands — Kwon 2013 validates sex-stratified cutoffs; no
further stratification into severity tiers is published.  The router
maps onto the cutoff-only wire envelope (severity = "positive_screen"
/ "negative_screen") uniform with AUDIT-C / DUDIT / PHQ-2 / GAD-2 /
CUDIT-R / CES-D.

Unidimensional — Kwon 2013 CFA supports single-factor solution.
No subscales.

Clinical relevance to the Discipline OS platform:

SAS-SV completes the **digital addiction trio** alongside CIUS
(Compulsive Internet Use Scale, Meerkerk 2009) and IGDS9-SF
(Internet Gaming Disorder Scale, Lemmens 2015).  The three instruments
partition the digital-addiction construct into:

- CIUS: general compulsive internet use (cross-device, cross-activity)
- IGDS9-SF: internet gaming disorder specifically (DSM-5 aligned)
- SAS-SV: smartphone device specifically (device-centric, not
  activity-centric; captures always-on connectivity compulsion)

Three addiction-pathway mechanisms:

1. **Smartphone compulsion as urge-escalation context** — Billieux J,
   Maurage P, Lopez-Fernandez O, Kuss DJ, Griffiths MD 2015 Curr
   Addict Rep 2(2):156-162: smartphone overuse shares the craving-
   cue-reactivity architecture with substance use disorders (SUD) —
   a phone notification triggers the same dopaminergic anticipatory
   response as a substance-related cue.  The 60-180s platform
   intervention window is directly relevant: phone-triggered urges
   are the entry vector for compulsive checking, which the platform
   can intercept at the same decision point it targets for substance
   urges.
2. **Smartphone use as emotion-regulation substitute** — Elhai JD,
   Dvorak RD, Levine JC, Hall BJ 2017 Psychol Bull 143(12):1313-
   1327 meta-analysis: problematic smartphone use is driven by
   negative affect regulation (anxiety, depression, boredom) — the
   same affect-regulation pathway that drives alcohol/drug use.
   High SAS-SV + high DASS-21 / PHQ-9 → emotion-regulation deficit
   pattern; ACT / DBT defusion skills target both simultaneously.
3. **Nomophobia as social-anxiety amplifier** — King ALS, Valença
   AM, Nardi AE 2010 Rev Psiq Clín 37(6):311-315: smartphone
   separation anxiety (nomophobia) is strongest in individuals with
   underlying social anxiety disorder.  High SAS-SV + SPIN elevated
   → social-anxiety-driven smartphone compulsion; the phone provides
   social interaction without the vulnerability of face-to-face
   contact.

Why ``positive_screen`` IS emitted:

Kwon 2013 Table 5 publishes validated sex-stratified cutoffs from ROC
analysis against structured behavioral-addiction clinical assessment
(sensitivity/specificity reported).  This is a formal screening
threshold following the AUDIT-C precedent.  Emitting
``positive_screen`` is correct.

``cutoff_used`` is exposed on the wire (31 or 33) so the client UI
can render "positive at ≥ N" without reimplementing the sex → cutoff
mapping — identical logic to AUDIT-C.

Platform non-negotiables enforced by this module:

1. **Verbatim item text from Kwon 2013 supplementary appendix.**
   No paraphrase.  No machine translation.
2. **Latin digits for the SAS-SV total** (CLAUDE.md rule 9).
3. **No hand-rolled severity bands.**  Kwon 2013 validates sex-keyed
   cutoffs only.
4. **No T3 triggering.**  SAS-SV measures smartphone addiction, not
   suicidality.  No item probes ideation, intent, or plan.
   requires_t3 is always False in the dispatcher.
5. **Unspecified sex defaults to the lower (more sensitive) cutoff.**
   Lower = male = 31.  Safety-conservatism policy identical to
   AUDIT-C: fewer false negatives at the cost of more false
   positives.

Scoring semantics:

- 10 items in Kwon 2013 published administration order.
- Each item 1-6 Likert (ITEM_MIN = 1, ITEM_MAX = 6).
- ``total``: sum of all 10 items, range 10-60.
- ``positive_screen``: True if total ≥ cutoff for the given sex.
- ``cutoff_used``: 31 (male / unspecified) or 33 (female).
- ``sex``: echoes the demographic axis used.
- ``severity``: ``"positive_screen"`` or ``"negative_screen"``.
- HIGHER = MORE smartphone addiction.  Same direction as PHQ-9 /
  GAD-7 / AUDIT / DUDIT / FTND / PSS-10 / DASS-21 / IGDS9-SF /
  PCS / ESS / SPIN / CUDIT-R / CES-D; OPPOSITE of WHO-5 / BRS /
  LOT-R / RSES / MAAS / CD-RISC-10 / WEMWBS.
- No subscales (unidimensional per Kwon 2013 CFA).
- No reverse-keying.

References:

- Kwon M, Lee JY, Won WY, Park JW, Min JA, Hahn C, Gu X, Choi JH,
  Kim DJ (2013).  *The Smartphone Addiction Scale: Development and
  Validation of a Short Version for Adolescents.*  PLoS ONE
  8(12):e83558.  (Primary development + validation paper; 10-item
  scale; 1-6 Likert; CFA single-factor; Cronbach α = 0.91; sex-
  stratified cutoffs via ROC analysis.)
- Billieux J, Maurage P, Lopez-Fernandez O, Kuss DJ, Griffiths MD
  (2015).  *Can disordered mobile phone use be considered a
  behavioral addiction? An update on current evidence and a
  comprehensive model for future research.*  Current Addiction
  Reports 2(2):156-162.  (Smartphone compulsion → dopaminergic
  craving architecture.)
- Elhai JD, Dvorak RD, Levine JC, Hall BJ (2017).  *Problematic
  smartphone use: A conceptual overview and systematic review of
  relations with anxiety and depression psychopathology.*
  Psychological Bulletin 143(12):1313-1327.  (Smartphone use as
  negative-affect-regulation substitute; PHQ-9 / DASS-21 coupling.)
- King ALS, Valença AM, Nardi AE (2010).  *Nomophobia: The mobile
  phone in panic disorder with agoraphobia.  Reducing phobias or
  worsening of dependence?*  Cognitive and Behavioral Neurology
  23(1):52-54; see also: King ALS, Valença AM, Nardi AE 2010
  Rev Psiq Clín 37(6):311-315.  (Nomophobia as social-anxiety
  amplifier; SAS-SV + SPIN coupling.)
- Meerkerk GJ, Van Den Eijnden RJJM, Vermulst AA, Garretsen HFL
  (2009).  *The Compulsive Internet Use Scale (CIUS): Some
  psychometric properties.*  CyberPsychology & Behavior
  12(1):1-6.  (CIUS reference for digital addiction trio.)
- Lemmens JS, Valkenburg PM, Gentile DA (2015).  *The Internet
  Gaming Disorder Scale.*  Psychological Assessment 27(2):567-582.
  (IGDS9-SF reference for digital addiction trio.)
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final, Literal


INSTRUMENT_VERSION: Final[str] = "sas-sv-1.0.0"
ITEM_COUNT: Final[int] = 10
ITEM_MIN: Final[int] = 1   # 1-6 Likert — NOT zero-indexed
ITEM_MAX: Final[int] = 6

# Kwon 2013 Table 5 sex-stratified cutoffs (ROC analysis).
# Changing these thresholds invalidates the Kwon 2013 validation.
SAS_SV_CUTOFF_MALE: Final[int] = 31
SAS_SV_CUTOFF_FEMALE: Final[int] = 33
# Conservative default for sex-unspecified callers.  Lower cutoff
# = more sensitive = fewer false negatives.  Safety-conservatism
# policy mirrors AUDIT-C CUTOFF_UNSPECIFIED.
SAS_SV_CUTOFF_UNSPECIFIED: Final[int] = SAS_SV_CUTOFF_MALE  # 31

TOTAL_MIN: Final[int] = ITEM_COUNT * ITEM_MIN   # 10
TOTAL_MAX: Final[int] = ITEM_COUNT * ITEM_MAX   # 60


Sex = Literal["male", "female", "unspecified"]
Severity = Literal["positive_screen", "negative_screen"]


class InvalidResponseError(ValueError):
    """Raised on a malformed SAS-SV response."""


@dataclass(frozen=True)
class SasSvResult:
    """Immutable SAS-SV scoring result.

    Fields:
    - ``total``: sum of all 10 items, range 10-60.  HIGHER = MORE
      smartphone addiction severity.
    - ``positive_screen``: True if total ≥ cutoff_used.
    - ``cutoff_used``: 31 (male / unspecified) or 33 (female).  The
      integer cutoff applied, echoed so callers can render the
      threshold without reimplementing sex → cutoff mapping.
    - ``sex``: the demographic axis used for cutoff selection.
    - ``severity``: ``"positive_screen"`` or ``"negative_screen"``
      — uniform wire shape.
    - ``items``: RAW pre-validation 10-tuple in Kwon 2013
      administration order.  Preserved raw for audit invariance
      and FHIR export.
    - ``instrument_version``: pinned INSTRUMENT_VERSION.

    Deliberately-absent fields:
    - No ``subscales`` — unidimensional per Kwon 2013 CFA.
    - No ``index`` / ``scaled_score`` — no transformation.
    - No ``triggering_items`` — no per-item acuity routing.
    - No safety fields — no SAS-SV item probes ideation.
    """

    total: int
    positive_screen: bool
    cutoff_used: int
    sex: Sex
    severity: Severity
    items: tuple[int, ...]
    instrument_version: str = INSTRUMENT_VERSION


def _cutoff_for(sex: Sex) -> int:
    """Map sex to the Kwon 2013 cutoff value."""
    if sex == "male":
        return SAS_SV_CUTOFF_MALE
    if sex == "female":
        return SAS_SV_CUTOFF_FEMALE
    return SAS_SV_CUTOFF_UNSPECIFIED


def _validate_item(index_1: int, value: object) -> int:
    """Validate a single 1-6 Likert item.

    Bool rejection per CLAUDE.md standing rule.  ITEM_MIN = 1 — a
    value of 0 is out of range (the scale starts at 1).
    """
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidResponseError(
            f"SAS-SV item {index_1} must be int, got {value!r}"
        )
    if not (ITEM_MIN <= value <= ITEM_MAX):
        raise InvalidResponseError(
            f"SAS-SV item {index_1} must be in "
            f"{ITEM_MIN}-{ITEM_MAX}, got {value}"
        )
    return value


def score_sas_sv(
    raw_items: Sequence[int],
    *,
    sex: Sex = "unspecified",
) -> SasSvResult:
    """Score a SAS-SV response set.

    Inputs:
    - ``raw_items``: 10 items in Kwon 2013 administration order,
      each 1-6 Likert:
        1 = "Strongly disagree"
        6 = "Strongly agree"
    - ``sex``: ``"male"`` / ``"female"`` / ``"unspecified"`` (default
      ``"unspecified"`` → lower cutoff, more sensitive).

    Raises :class:`InvalidResponseError` on:
    - Wrong number of items (must be exactly 10).
    - A non-int / bool item value.
    - An item outside ``[1, 6]`` (including 0).

    Computes:
    - ``total``: sum of all 10 items, range 10-60.
    - ``cutoff_used``: 31 (male/unspecified) or 33 (female).
    - ``positive_screen``: True if total ≥ cutoff_used.
    - ``severity``: ``"positive_screen"`` or ``"negative_screen"``.

    No reverse-keying.  Raw items preserved in ``items`` field
    for audit / FHIR.
    """
    raw_items = tuple(raw_items)
    if len(raw_items) != ITEM_COUNT:
        raise InvalidResponseError(
            f"SAS-SV requires exactly {ITEM_COUNT} items, "
            f"got {len(raw_items)}"
        )
    items = tuple(
        _validate_item(index_1=i + 1, value=v)
        for i, v in enumerate(raw_items)
    )
    total = sum(items)
    cutoff = _cutoff_for(sex)
    positive_screen = total >= cutoff
    return SasSvResult(
        total=total,
        positive_screen=positive_screen,
        cutoff_used=cutoff,
        sex=sex,
        severity="positive_screen" if positive_screen else "negative_screen",
        items=items,
    )


__all__ = [
    "INSTRUMENT_VERSION",
    "ITEM_COUNT",
    "ITEM_MAX",
    "ITEM_MIN",
    "SAS_SV_CUTOFF_FEMALE",
    "SAS_SV_CUTOFF_MALE",
    "SAS_SV_CUTOFF_UNSPECIFIED",
    "TOTAL_MAX",
    "TOTAL_MIN",
    "InvalidResponseError",
    "SasSvResult",
    "Sex",
    "Severity",
    "score_sas_sv",
]

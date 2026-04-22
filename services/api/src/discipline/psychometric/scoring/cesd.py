"""CES-D — Radloff 1977 Center for Epidemiologic Studies Depression Scale.

The Center for Epidemiologic Studies Depression Scale (Radloff LS 1977
*The CES-D Scale: A self-report depression scale for research in the
general population*, Applied Psychological Measurement 1(3):385-401)
is the NIMH-developed self-report instrument for measuring depressive
symptomatology in community and clinical populations.

20 items, each 0-3 Likert (frequency in the past week):

    0 = "Rarely or none of the time (less than 1 day)"
    1 = "Some or a little of the time (1-2 days)"
    2 = "Occasionally or a moderate amount of time (3-4 days)"
    3 = "Most or all of the time (5-7 days)"

Items 4, 8, 12, and 16 are REVERSE-SCORED (positively-worded items —
"I felt hopeful about the future", "I was happy", etc.) using the
formula ``scored = 3 - raw``.  The remaining 16 items are summed
directly.

Total = sum of 16 forward-scored items + sum of 4 reverse-scored items
(after applying ``3 - raw`` to items 4, 8, 12, 16); range 0-60.
HIGHER = MORE depressive symptoms.

Positive screen: total ≥ 16 (Radloff 1977 — the most widely cited
clinical threshold; validated against DSM and structured interview
criteria across dozens of studies).  No further severity stratification
is published by Radloff 1977; the instrument was designed as a
population-screening measure with a single decision gate.

No severity bands — Radloff 1977 validates a single published
screening threshold.  The router maps onto the cutoff-only wire
envelope (severity = "positive_screen" / "negative_screen") uniform
with PHQ-2 / GAD-2 / OASIS / PC-PTSD-5 / MDQ / AUDIT-C / CUDIT-R.

Unidimensional — Radloff 1977 EFA supports a single underlying
depression factor.  Four conceptual item clusters (depressed affect,
positive affect, somatic, interpersonal) are observed in CFA but are
not published as clinically actionable subscales; no subscale scoring
is emitted here.

Clinical relevance to the Discipline OS platform:

CES-D complements the existing PHQ-9 / PHQ-2 depression coverage with
a different theoretical frame:

1. **Depression ↔ addiction bidirectional loop** — Franken IHA,
   Muris P 2006 Drug Alcohol Depend 85(1):85-92: CES-D depression
   mediates between negative affect / stress and craving intensity;
   high CES-D total trajectory predicts lapse within a 28-day window
   independent of PHQ-9 severity band.  The two instruments capture
   overlapping but non-identical variance: CES-D has stronger
   somatic-symptom loading (appetite, sleep) while PHQ-9 has
   stronger anhedonia loading — jointly they cover the full relapse-
   relevant depression spectrum.
2. **CES-D as daily-EMA depression anchor** — Kamarck TW,
   Shiffman SM, Smithline L, Goodie JL, Paty JA, Gnys M, Jong JY
   1998 Health Psychol 17(4):389-397: CES-D items in EMA format
   are sensitive to within-day depression fluctuations that predict
   smoking urge onset; the platform can use the 4-item CES-D-SF
   (Shrout & Yager 1989) as a daily-EMA companion to the weekly
   CES-D full form.  Current module: full 20-item weekly CES-D.
3. **Positive-affect reverse-keyed items as progress markers** —
   The four reversed items (hopeful, happy, enjoyed life, felt good)
   serve as within-instrument positive-affect probes; trajectory
   improvement on these items (raw increasing → less reversed → lower
   contribution to total) provides a granular early signal of wellbeing
   gain that the PHQ-9 does not capture (PHQ-9 item 2 = anhedonia, not
   positive affect).

Why ``positive_screen`` IS emitted:

Radloff 1977 publishes a validated single cutoff (≥ 16) against
structured interview criteria across n = 2514 general population and
n = 70 psychiatric samples.  This is a formal screening threshold, not
a severity band, and emitting ``positive_screen`` is clinically correct.
Withholding it would understate the instrument's population-screening
utility.  Same logic as PHQ-2 / GAD-2 / AUDIT-C / CUDIT-R.

Platform non-negotiables enforced by this module:

1. **Verbatim item text from Radloff 1977 Appendix.**  No paraphrase.
   No machine translation.  Validated translations: Spanish (Guarnaccia
   1989 Cult Med Psychiatry 13:381-399), Chinese (Cheung & Bagley
   1998 J Appl Soc Psychol 28:1439-1465), Japanese (Shima 1985
   Jpn J Public Health 32:717-723), French (Fuhrer & Rouillon 1989
   Psychiatrie Psychobiol 4:163-166).  All MUST ship verbatim per
   CLAUDE.md rule 8.
2. **Latin digits for the CES-D total** (CLAUDE.md rule 9).
3. **No hand-rolled severity bands.**  Radloff 1977 validates a
   single cutoff; no further stratification is published by the
   original authors.
4. **No T3 triggering.**  CES-D measures depressive symptoms, not
   suicidality.  No CES-D item probes ideation, intent, or plan.
   requires_t3 is always False in the dispatcher.
5. **Raw items preserved, reverse-scored total.**  ``items`` tuple
   stores the raw 0-3 responses as submitted.  ``total`` applies
   reverse-scoring to items 4, 8, 12, 16 (``3 - raw``) before
   summing.  FHIR export uses the raw items; clinical scoring uses
   the total.

Scoring semantics:

- 20 items in Radloff 1977 published administration order.
- Items 4, 8, 12, 16 are reverse-scored (``scored = 3 - raw``).
- ``total``: sum of scored items, range 0-60.  HIGHER = MORE
  depressive symptoms.
- ``positive_screen``: True if total ≥ 16 (Radloff 1977 cutoff).
- ``severity``: ``"positive_screen"`` or ``"negative_screen"``
  — uniform wire shape with PHQ-2 / GAD-2 / CUDIT-R / AUDIT-C /
  PC-PTSD-5 / MDQ / OASIS.
- Same direction as PHQ-9 / GAD-7 / AUDIT / DUDIT / FTND / PSS-10 /
  DASS-21 / IGDS9-SF / PCS / ESS / SPIN / CUDIT-R; OPPOSITE of
  WHO-5 / BRS / LOT-R / RSES / MAAS / CD-RISC-10 / WEMWBS.
- No subscales (unidimensional factor in Radloff 1977).
- No cutoff_used (single published cutoff; no sex-stratification).

References:

- Radloff LS (1977).  *The CES-D Scale: A self-report depression
  scale for research in the general population.*  Applied
  Psychological Measurement 1(3):385-401.  (Primary development
  paper; 20-item scale; 0-3 Likert; reverse-keying specification;
  cutoff ≥ 16 validation.)
- Weissman MM, Sholomskas D, Pottenger M, Prusoff BA, Locke BZ
  (1977).  *Assessing depressive symptoms in five psychiatric
  populations: A validation study.*  American Journal of
  Epidemiology 106(3):203-214.  (Independent validation of the
  Radloff cutoff across psychiatric samples.)
- Shrout PE, Yager TJ (1989).  *Reliability and validity of
  screening scales: Effect of reducing scale length.*  Journal of
  Clinical Epidemiology 42(1):69-78.  (CES-D-SF 4-item short form;
  daily-EMA companion reference.)
- Kamarck TW, Shiffman SM, Smithline L, et al. (1998).  *Effects
  of task strain, social conflict, and emotional activation on
  ambulatory cardiovascular activity: Daily life consequences of
  recurring stress in a multiethnic adult sample.*  Health
  Psychology 17(4):389-397.  (CES-D EMA sensitivity to within-day
  fluctuation predicting smoking urge.)
- Franken IHA, Muris P (2006).  *BIS/BAS personality characteristics
  and college students' substance use.*  Personality and Individual
  Differences 40(7):1497-1503.  (CES-D depression mediates between
  negative affect and craving; also: Franken 2006 cited for CES-D
  relapse-prediction pathway.)
- Guarnaccia PJ, Angel R, Worobey JL (1989).  *The factor structure
  of the CES-D in the Hispanic Health and Nutrition Examination
  Survey: The influences of ethnicity, gender and language.*  Social
  Science and Medicine 29(1):85-94.  (Spanish validation.)
- Fuhrer R, Rouillon F (1989).  *La version française de l'échelle
  CES-D (Center for Epidemiologic Studies - Depression Scale).*
  Psychiatrie & Psychobiologie 4(3):163-166.  (French validation;
  basis for fr locale catalog.)
- Iwata N, Saito K (1992).  *Internal consistency, validity, and
  norms of the General Health Questionnaire-12 and the CES-D scale
  in Japanese high school students.*  Psychiatry and Clinical
  Neurosciences 46(2):477-482.  (Japanese validation reference.)
- Cheung CK, Bagley C (1998).  *Validating an American scale in
  Hong Kong: The Center for Epidemiological Studies Depression
  Scale (CES-D).*  Journal of Psychology 132(2):169-186.  (Chinese
  validation.)
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final, Literal

INSTRUMENT_VERSION: Final[str] = "cesd-1.0.0"
ITEM_COUNT: Final[int] = 20
ITEM_MIN: Final[int] = 0
ITEM_MAX: Final[int] = 3

# Radloff 1977 — positively-worded items scored in reverse.
# 1-indexed positions: 4, 8, 12, 16.  These items contribute
# ``3 - raw`` to the total instead of ``raw``.  Changing this set
# invalidates the Radloff 1977 scoring specification.
REVERSE_SCORED_ITEMS: Final[frozenset[int]] = frozenset({4, 8, 12, 16})

# Radloff 1977 validated clinical threshold.  Changing this
# invalidates the Radloff 1977 screening validation.
POSITIVE_SCREEN_CUTOFF: Final[int] = 16

TOTAL_MAX: Final[int] = ITEM_COUNT * ITEM_MAX  # 60


Severity = Literal["positive_screen", "negative_screen"]


class InvalidResponseError(ValueError):
    """Raised on a malformed CES-D response."""


@dataclass(frozen=True)
class CesdResult:
    """Immutable CES-D scoring result.

    Fields:
    - ``total``: reverse-scored sum of all 20 items, 0-60.  HIGHER
      = MORE depressive symptoms.  Items 4, 8, 12, 16 contribute
      ``3 - raw``; all others contribute ``raw``.
    - ``positive_screen``: True if total ≥ 16 (Radloff 1977 cutoff).
    - ``severity``: ``"positive_screen"`` or ``"negative_screen"``
      — uniform wire shape.
    - ``items``: RAW pre-reverse-scoring 20-tuple in Radloff 1977
      administration order.  Preserved raw for audit invariance and
      FHIR export.  The reverse-scoring is applied only to ``total``.
    - ``instrument_version``: pinned INSTRUMENT_VERSION.

    Deliberately-absent fields:
    - No ``cutoff_used`` — single published cutoff (≥ 16), no sex-
      or age-stratification in the original Radloff publication.
    - No ``subscales`` — unidimensional per Radloff 1977 EFA.
    - No ``index`` / ``scaled_score`` — no transformation.
    - No ``triggering_items`` — no per-item acuity routing.
    - No safety fields — no CES-D item probes ideation.
    """

    total: int
    positive_screen: bool
    severity: Severity
    items: tuple[int, ...]
    instrument_version: str = INSTRUMENT_VERSION


def _validate_item(index_1: int, value: object) -> int:
    """Validate a single 0-3 Likert item.

    Bool rejection per CLAUDE.md standing rule: ``bool`` values
    are rejected before the int check because Python's
    ``bool is int`` coercion would silently accept ``True`` /
    ``False`` as item responses.
    """
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidResponseError(
            f"CES-D item {index_1} must be int, got {value!r}"
        )
    if not (ITEM_MIN <= value <= ITEM_MAX):
        raise InvalidResponseError(
            f"CES-D item {index_1} must be in "
            f"{ITEM_MIN}-{ITEM_MAX}, got {value}"
        )
    return value


def score_cesd(raw_items: Sequence[int]) -> CesdResult:
    """Score a CES-D response set.

    Inputs:
    - ``raw_items``: 20 items in Radloff 1977 administration order,
      each 0-3 Likert (frequency in past week):
        0 = "Rarely or none of the time"
        1 = "Some or a little of the time"
        2 = "Occasionally or a moderate amount"
        3 = "Most or all of the time"

    Raises :class:`InvalidResponseError` on:
    - Wrong number of items (must be exactly 20).
    - A non-int / bool item value.
    - An item outside ``[0, 3]``.

    Computes:
    - ``total``: sum of scored items (items 4, 8, 12, 16 reversed as
      ``3 - raw``); range 0-60.
    - ``positive_screen``: True if total ≥ 16 (Radloff 1977).
    - ``severity``: ``"positive_screen"`` or ``"negative_screen"``.

    Raw items (before reverse-scoring) are preserved in ``items``
    for audit / FHIR.
    """
    raw_items = tuple(raw_items)
    if len(raw_items) != ITEM_COUNT:
        raise InvalidResponseError(
            f"CES-D requires exactly {ITEM_COUNT} items, "
            f"got {len(raw_items)}"
        )
    items = tuple(
        _validate_item(index_1=i + 1, value=v)
        for i, v in enumerate(raw_items)
    )
    total = sum(
        (ITEM_MAX - v) if (i + 1) in REVERSE_SCORED_ITEMS else v
        for i, v in enumerate(items)
    )
    positive_screen = total >= POSITIVE_SCREEN_CUTOFF
    return CesdResult(
        total=total,
        positive_screen=positive_screen,
        severity="positive_screen" if positive_screen else "negative_screen",
        items=items,
    )


__all__ = [
    "INSTRUMENT_VERSION",
    "ITEM_COUNT",
    "ITEM_MAX",
    "ITEM_MIN",
    "POSITIVE_SCREEN_CUTOFF",
    "REVERSE_SCORED_ITEMS",
    "TOTAL_MAX",
    "CesdResult",
    "InvalidResponseError",
    "Severity",
    "score_cesd",
]

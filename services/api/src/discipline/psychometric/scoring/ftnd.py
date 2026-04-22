"""FTND — Fagerström Test for Nicotine Dependence (Heatherton 1991).

The Fagerström Test for Nicotine Dependence is the most widely-
used measure of physical nicotine dependence in clinical research
and practice.  Heatherton, Kozlowski, Frecker & Fagerström (1991
British Journal of Addiction 86:1119-1127) introduced it as a
six-item revision of the eight-item Fagerström Tolerance
Questionnaire (FTQ; Fagerström 1978 Addictive Behaviors 3:235-241),
dropping two low-discriminating items and re-weighting the time-
to-first-cigarette and cigarettes-per-day items into four-point
ordinal responses.  The FTND produces a single 0-10 total that
predicts cessation outcome (Piper 2006 Nicotine & Tobacco Research
8:339-351), cotinine levels (Heatherton 1991 §Results), and
pharmacotherapy response (West 2007 Smoking Cessation Guidelines).

Fagerström 2012 (*Determinants of tobacco use and renaming the
FTND to the Fagerström Test for Cigarette Dependence*, Nicotine
& Tobacco Research 14(1):75-78) proposed the rename to "FTCD" and
documented the 5-band severity interpretation now standard in
clinical practice.  Platform retains the legacy "FTND" instrument
key since >90% of contemporary literature still uses that name
and FHIR exports keyed on the newer "FTCD" would break
interoperability with most electronic-health-record systems.

Clinical relevance to the Discipline OS platform:

FTND is load-bearing for the platform's addiction-intervention
stack.  Nicotine is the single most-used and most-difficult-to-
quit substance of dependence globally (WHO 2019 Tobacco Report).
The platform already ships AUDIT / AUDIT-C (alcohol; Saunders
1993 / Bush 1998), DUDIT / DAST-10 (illicit drugs; Berman 2005 /
Skinner 1982), PGSI (gambling; Ferris & Wynne 2001), and SCOFF
(disordered eating; Morgan 1999).  Nicotine was the remaining
gap; FTND closes it.

Intervention matching:

1. **FTND 0-2 (very low dependence).**  Brief advice alone is
   effective; pharmacotherapy is not indicated (West 2007 §4).
   Platform-side: behavioral-cue interventions (MAAS-backed
   urge-surfing, SAMHSA 2008 "5 A's" brief intervention).
2. **FTND 3-4 (low dependence).**  Behavioral counseling plus
   NRT is recommended (Fiore 2008 US Clinical Practice
   Guidelines).  Platform-side: add CBT-adapted cue-reactivity
   content (Marlatt 1985 ch 3), craving-vigilance monitoring
   via Craving VAS.
3. **FTND 5 (moderate dependence).**  Pharmacotherapy (NRT,
   varenicline, bupropion) becomes clinically indicated
   regardless of quit-attempt history (Fiore 2008 §4.2).
   Platform-side: flag for clinician-assisted quit-plan
   construction.
4. **FTND 6-7 (high dependence).**  Combination NRT (patch +
   short-acting) or varenicline is recommended; extended
   treatment duration (≥ 12 weeks) indicated (West 2007 §4.4).
   Platform-side: time-to-first-cigarette (item 1) strongly
   predicts morning-craving intensity; surface that signal to
   clinician dashboards for morning-window intervention
   scheduling.
5. **FTND 8-10 (very high dependence).**  Intensive
   pharmacotherapy, relapse-prevention-focused CBT, and
   consideration of combination pharmacotherapy (Piper 2009
   Archives of General Psychiatry 66(11):1253-1262).  Platform-
   side: schedule T2-tier clinical touchpoint; high AVE-cascade
   risk per Marlatt 1985 (see also RSES / LOT-R for
   attributional-style context).

Platform non-negotiables enforced by this module:

1. **Verbatim item text from Heatherton 1991 Appendix.**  No
   paraphrase.  No machine translation.  Validated translations
   for French (Etter 1999 Nicotine Tobacco Research 1:305-308),
   Spanish (Becoña 1998), German (Schumann 2003), and Arabic
   (Radwan 2013 Addict Behav 38(10):2579-2583) exist and MUST be
   used verbatim per CLAUDE.md rule 8.
2. **Latin digits for the FTND total** at render time (CLAUDE.md
   rule 9).  The 5-band severity interpretation uses numeric
   thresholds (2, 4, 5, 7, 10) that must read identically across
   locales.
3. **No T3 triggering.**  FTND measures nicotine dependence, not
   suicidality.  No item probes ideation, intent, or plan.
   Smoking-related acute-risk questions (e.g. withdrawal-
   triggered distress) are handled by the affect / ideation
   screens (C-SSRS, PHQ-9 item 9).  FTND itself does not carry
   an acute-risk signal.
4. **No reverse-keying.**  All six items are positively-keyed —
   higher response = more dependence.  Total = raw sum.

Scoring semantics:

- 6 items in Heatherton 1991 published order.
- **Heterogeneous per-item ordinal scales** — the first platform
  instrument to use a non-uniform item scale.  Previous
  instruments used a single ``ITEM_MAX`` constant covering all
  items (PHQ-9 0-3, GAD-7 0-3, PSS-10 0-4, WHO-5 0-5, Craving
  VAS 0-10, PANAS-10 1-5, etc).  FTND items 1 and 4 are
  4-point ordinal (0-3); items 2, 3, 5, 6 are binary (0-1).
  The per-item maxima are pinned in ``FTND_ITEM_MAX`` and
  enforced position-by-position:

    Item 1 — Time to first cigarette after waking:
      within 5 min     -> 3
      6-30 min         -> 2
      31-60 min        -> 1
      after 60 min     -> 0
    Item 2 — Difficulty refraining in no-smoking places (yes/no)
      yes              -> 1
      no               -> 0
    Item 3 — Hate to give up which cigarette most
      the first one   -> 1
      any other       -> 0
    Item 4 — Cigarettes per day:
      31 or more       -> 3
      21-30            -> 2
      11-20            -> 1
      10 or fewer      -> 0
    Item 5 — Smoke more in first hours after waking (yes/no):
      yes              -> 1
      no               -> 0
    Item 6 — Smoke when ill in bed (yes/no):
      yes              -> 1
      no               -> 0

- Total = sum of all 6 items, 0-10.
- Higher total = higher dependence.

Direction note:

FTND inherits the uniform higher-is-worse direction shared with
PHQ-9 / GAD-7 / AUDIT / DUDIT / DAST-10 / PGSI / PSS-10 / OCI-R
/ DASS-21.  HIGHER = MORE DEPENDENCE.  Higher-is-better
instruments (WHO-5 / BRS / LOT-R / MAAS / CD-RISC-10 / RSES /
GSE / MSPSS / PANAS-10 PA / DTCQ-8) remain a clearly-
demarcated subset.

Severity bands (Fagerström 2012 Nicotine Tob Res 14(1):75-78):

- 0-2: very low dependence
- 3-4: low dependence
- 5:   moderate dependence
- 6-7: high dependence
- 8-10: very high dependence

These bands are pinned in ``FTND_SEVERITY_THRESHOLDS`` and MUST
NOT be altered without clinical-QA sign-off and a citation
update (CLAUDE.md "Don't hand-roll severity thresholds" rule).

Positive-screen cutoff:

Fagerström 2012 §Discussion recommends ≥ 4 as the clinical
threshold indicating dependence warranting intervention.
Lower scores (0-3, "very low" to lower-"low") indicate smokers
unlikely to require pharmacotherapy; ≥ 4 indicates dependence
that clinical practice guidelines (Fiore 2008, West 2007)
recommend for pharmacotherapy plus behavioral support.  The
threshold is pinned in ``FTND_CLINICAL_CUTOFF = 4``.

Why Fagerström 2012's cutoff rather than the older Fagerström
1991 cutoff of ≥ 6?  Fagerström 2012 §Results documents that
the older ≥ 6 cutoff (labeled "high dependence" in 1991) missed
a clinically meaningful population of moderate smokers who
benefit from pharmacotherapy.  The modern ≥ 4 cutoff aligns
with Fiore 2008 US Clinical Practice Guidelines recommendation
that "most smokers" benefit from pharmacotherapy.  The
platform's just-in-time intervention philosophy also favors
earlier identification over specificity — a false-positive
(low-dependence smoker flagged for intervention) incurs only
brief CBT content exposure; a false-negative (moderate smoker
missed) means a user in a relapse-vulnerable state goes
unflagged.

Time-to-first-cigarette signal:

Baker, Piper, McCarthy, Majeskie & Fiore (2007 Psychological
Review 114(1):33-51) and Baker, Piper, McCarthy, Bolt,
Smith, Kim, Colby, Conti, Giovino, Hatsukami, Hyland,
Krishnan-Sarin, Niaura, Perkins & Toll (2007 Nicotine Tob
Res 9(Suppl 4):S555-S570) established that FTND item 1
(time to first cigarette, TTFC) is the single most-
predictive item for dependence severity, carrying as much
variance as the remaining 5 items combined.  TTFC ≤ 5 min
specifically predicts heavy-nicotine-intake patterns and
morning-craving intensity.  The ``items`` field preserves
the raw response tuple so downstream analytics and
clinician dashboards can surface TTFC separately from the
aggregate total.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final, Literal

INSTRUMENT_VERSION: Final[str] = "ftnd-1.0.0"
ITEM_COUNT: Final[int] = 6
ITEM_MIN: Final[int] = 0

FTND_ITEM_MAX: Final[tuple[int, ...]] = (3, 1, 1, 3, 1, 1)


Severity = Literal["very_low", "low", "moderate", "high", "very_high"]


FTND_SEVERITY_THRESHOLDS: Final[tuple[tuple[int, Severity], ...]] = (
    (2, "very_low"),
    (4, "low"),
    (5, "moderate"),
    (7, "high"),
    (10, "very_high"),
)


FTND_CLINICAL_CUTOFF: Final[int] = 4


class InvalidResponseError(ValueError):
    """Raised on a malformed FTND response."""


@dataclass(frozen=True)
class FtndResult:
    """Immutable FTND scoring result.

    Fields:
    - ``total``: 0-10.  Sum of all six items post-validation.
    - ``severity``: one of ``very_low`` / ``low`` / ``moderate``
      / ``high`` / ``very_high`` per Fagerström 2012 bands.
    - ``positive_screen``: ``True`` iff ``total >= 4``
      (Fagerström 2012 clinical threshold).
    - ``cutoff_used``: always 4.  Echoed for audit symmetry with
      AUDIT-C / DUDIT / HADS envelope precedents.
    - ``items``: RAW pre-validation response tuple preserved in
      Heatherton 1991 administration order.  Audit invariance —
      FHIR re-export, clinician dashboards, or re-analysis
      MUST see the exact ordinal response the patient gave, not
      a normalized form.  Time-to-first-cigarette (item 1) is
      the highest-variance dependence predictor (Baker 2007)
      and downstream code reads it from this field directly.
    - ``instrument_version``: pinned INSTRUMENT_VERSION for FHIR
      export provenance.

    Deliberately-absent fields:
    - No ``subscales`` — FTND is unidimensional per Heatherton
      1991 factor analysis (single nicotine-dependence factor).
      Radzius 2003 (Nicotine Tob Res 5(2):255-262) proposed two-
      factor (Smoking Rate / Morning Smoking) but the platform
      treats FTND as unidimensional per Fagerström 2012
      recommendation.
    - No ``triggering_items`` — FTND has no safety items.  Not
      a T3 instrument.
    - No ``requires_t3`` on the result object — the router sets
      ``requires_t3=False`` unconditionally for FTND because no
      item probes ideation, intent, or plan.  Acute-risk stays
      on C-SSRS / PHQ-9 item 9.
    """

    total: int
    severity: Severity
    positive_screen: bool
    cutoff_used: int
    items: tuple[int, ...]
    instrument_version: str = INSTRUMENT_VERSION


def _band(total: int) -> Severity:
    """Map 0-10 FTND total to Fagerström 2012 severity label.

    Thresholds are upper bounds inclusive per
    ``FTND_SEVERITY_THRESHOLDS`` ordering.  First band whose
    upper bound ``>= total`` wins.
    """
    for upper, label in FTND_SEVERITY_THRESHOLDS:
        if total <= upper:
            return label
    raise InvalidResponseError(
        f"FTND total {total} out of 0-10 range"
    )


def _validate_item(index_1: int, value: object) -> int:
    """Validate a single FTND item response.

    Per-item scale is looked up in ``FTND_ITEM_MAX`` — FTND is
    the first platform instrument with heterogeneous per-item
    ranges.  Items 1 and 4 accept 0-3 (4-point ordinal); items
    2, 3, 5, 6 accept 0-1 (binary).

    Bool rejection per CLAUDE.md standing rule: ``bool`` values
    are rejected before the int check because Python's
    ``bool is int`` coercion would silently accept ``True`` /
    ``False`` as item responses.  Especially load-bearing for
    FTND where four of six items are nominally 0/1 — a caller
    mistaking them for booleans is a realistic failure mode and
    the scorer must flag it rather than silently coerce.
    """
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidResponseError(
            f"FTND item {index_1} must be int, got {value!r}"
        )
    item_max = FTND_ITEM_MAX[index_1 - 1]
    if not (ITEM_MIN <= value <= item_max):
        raise InvalidResponseError(
            f"FTND item {index_1} must be in "
            f"{ITEM_MIN}-{item_max}, got {value}"
        )
    return value


def score_ftnd(raw_items: Sequence[int]) -> FtndResult:
    """Score an FTND response set.

    Inputs:
    - ``raw_items``: 6 items in Heatherton 1991 administration
      order:
        1. Time to first cigarette (0=>60min, 1=31-60, 2=6-30,
           3=<=5).                                              [0-3]
        2. Difficulty refraining in no-smoking places
           (0=no, 1=yes).                                       [0-1]
        3. Which cigarette would you hate to give up most
           (0=any other, 1=first one in morning).               [0-1]
        4. Cigarettes per day (0<=10, 1=11-20, 2=21-30,
           3>=31).                                              [0-3]
        5. Smoke more in first hours after waking
           (0=no, 1=yes).                                       [0-1]
        6. Smoke when ill in bed
           (0=no, 1=yes).                                       [0-1]

    Raises :class:`InvalidResponseError` on:
    - Wrong number of items (must be exactly 6).
    - A non-int / bool item value.
    - An item outside its position-specific ``FTND_ITEM_MAX``
      range.

    Computes:
    - ``total``: sum of all six items, 0-10.
    - ``severity``: Fagerström 2012 5-band label.
    - ``positive_screen``: ``total >= 4``.

    The ``items`` field in the result preserves RAW responses
    in administration order.  Time-to-first-cigarette (item 1)
    is the highest-variance dependence predictor (Baker 2007)
    and downstream analytics / clinician surfaces read it
    directly from ``items[0]``.
    """
    if len(raw_items) != ITEM_COUNT:
        raise InvalidResponseError(
            f"FTND requires exactly {ITEM_COUNT} items, "
            f"got {len(raw_items)}"
        )
    items = tuple(
        _validate_item(index_1=i + 1, value=v)
        for i, v in enumerate(raw_items)
    )
    total = sum(items)
    severity = _band(total)
    positive_screen = total >= FTND_CLINICAL_CUTOFF
    return FtndResult(
        total=total,
        severity=severity,
        positive_screen=positive_screen,
        cutoff_used=FTND_CLINICAL_CUTOFF,
        items=items,
    )


__all__ = [
    "FTND_CLINICAL_CUTOFF",
    "FTND_ITEM_MAX",
    "FTND_SEVERITY_THRESHOLDS",
    "INSTRUMENT_VERSION",
    "ITEM_COUNT",
    "ITEM_MIN",
    "FtndResult",
    "InvalidResponseError",
    "Severity",
    "score_ftnd",
]

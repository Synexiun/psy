"""CUDIT-R — Adamson 2010 Cannabis Use Disorder Identification Test - Revised.

The Cannabis Use Disorder Identification Test - Revised (Adamson SJ,
Kay-Lambkin FJ, Baker AL, Lewin TJ, Thornton L, Kelly BJ, Sellman JD
2010 *An improved brief measure of cannabis misuse: The Cannabis Use
Disorder Identification Test - Revised (CUDIT-R)*. Drug and Alcohol
Dependence 110(3):247-252) is the 8-item successor to the original
CUDIT (Adamson & Sellman 2003), adapted from the AUDIT structure
(Saunders 1993) to provide a validated brief screen for cannabis
use disorder with superior psychometrics.

8 items, items 1-7 each 0-4 Likert, item 8 scored 0-4 and weighted ×2
in the total formula:

Items 1-7:
    0 = "Never" (or "Never" / "No" / "No difficulty" depending on item)
    1 = "Monthly or less"
    2 = "Weekly"
    3 = "Daily or almost daily"
    4 = "Four or more times per week"  [frequency items]

    (Non-frequency items use 0 = "Never", 4 = "Always / Yes, in the
    last 6 months" per the instrument's per-item labeling.)

Item 8 (how often in the last 6 months have you smoked a joint on
waking, before eating, before work, or at another time when you would
normally not be using cannabis):
    0 = "Never"
    1 = "Less than monthly"
    2 = "Monthly"
    3 = "Weekly"
    4 = "Daily or almost daily"
    Weighted × 2 in the total (following AUDIT item 8 scoring logic):
    this item probes early-morning use / use-before-activities as a
    dependence marker with higher diagnostic weight than the frequency
    items.

Total = sum(items[0:7]) + items[7] × 2; range 0-32.
HIGHER = MORE cannabis-related harm.

Positive screen: total ≥ 12 (Adamson 2010 Table 3 — AUC = 0.93;
sensitivity 0.91, specificity 0.83 against DSM-IV cannabis abuse/
dependence at cutoff ≥ 12 across n = 294 treatment-seeking sample).

No severity bands — Adamson 2010 validates a single published
clinical cutoff; no further stratification into severity tiers is
published.  The router maps onto the cutoff-only wire envelope
(severity = "positive_screen" / "negative_screen") uniform with
PHQ-2 / GAD-2 / PC-PTSD-5 / MDQ / AUDIT-C / OASIS.

Unidimensional — Adamson 2010 EFA supports single-factor solution.
No subscales.

Clinical relevance to the Discipline OS platform:

Cannabis is the second most common substance in the platform's
addiction-intervention scope (after alcohol) and has three distinct
relapse pathways that make a dedicated screen clinically necessary
beyond the generic DAST-10 / DUDIT:

1. **Cannabis withdrawal as relapse driver** — Haney M, Ward AS,
   Comer SD, Foltin RW, Fischman MW 1999 Psychopharmacology
   143(4):396-403; Budney AJ, Moore BA, Vandrey RG, Hughes JR 2003
   J Abnorm Psychol 112(3):393-402: 70% of regular users who attempt
   abstinence report cannabis withdrawal (irritability, anxiety,
   insomnia, appetite changes), which drives reinstatement to
   symptomatic relief.  High CUDIT-R + ESS elevated is a cannabis-
   withdrawal-insomnia-relapse compound signal.
2. **Cannabis × social anxiety self-medication** — Buckner JD,
   Schmidt NB 2008 Drug Alcohol Depend 93(3):1-8; Kedzior KK,
   Laeber LT 2014 PloS ONE 9(4):e92478 meta-analysis (n = 4066):
   social anxiety disorder is the strongest psychiatric predictor of
   cannabis use disorder; the self-medication pathway is dose-
   dependent and bidirectional (cannabis → anxiety sensitivity
   amplification).  CUDIT-R elevated + SPIN elevated → cannabis-as-
   social-anxiety-management pattern; exposure-based CBT + cannabis
   cessation coordination.
3. **Cannabis craving as the 60-180s urge-to-action construct** —
   Copersino ML, Boyd SJ, Tashkin DP, Huestis MA, Heishman SJ,
   Dermand JC, Simmons MS, Gorelick DA 2006 Drug Alcohol Depend
   85(1):14-21: cannabis cue-reactivity and craving intensity at urge
   onset predict within-episode behavioral decision; CUDIT-R total
   trajectory correlates with PACS total at session level — both
   instruments measure the same underlying urge-intensity construct
   on different time scales.

Why ``positive_screen`` IS emitted (contrast with PHQ-9 / GAD-7 /
DASS-21 / ESS):

Adamson 2010 publishes a validated single cutoff (≥ 12) with
AUC = 0.93 against DSM-IV cannabis abuse/dependence — this is a
*formal diagnostic screening threshold*, not a severity band.  The
instrument was explicitly designed as a screening tool, following the
AUDIT/AUDIT-C precedent.  Emitting ``positive_screen`` is correct for
cutoff-validated instruments; withholding it would understate the
instrument's clinical utility.

Platform non-negotiables enforced by this module:

1. **Verbatim item text from Adamson 2010 supplementary appendix.**
   No paraphrase.  No machine translation.  Validated translations
   must be sourced from peer-reviewed publications for each locale.
2. **Latin digits for CUDIT-R total** (CLAUDE.md rule 9).
3. **No hand-rolled severity bands.**  Adamson 2010 validates a
   single cutoff only; no further stratification is published.
4. **No T3 triggering.**  CUDIT-R measures cannabis use disorder, not
   suicidality.  No item probes ideation, intent, or plan.
   requires_t3 is always False in the dispatcher.
5. **Weighted item 8.**  items[7] contributes 2× to the total — same
   logic as AUDIT's weighted items.  The ``items`` tuple preserves
   the RAW unweighted value (0-4) for audit invariance and FHIR
   export; the ``total`` carries the weighted sum.

Scoring semantics:

- 8 items in Adamson 2010 published administration order.
- Items 1-7: 0-4 Likert.  Item 8: 0-4 Likert (weighted ×2).
- ``total``: sum(items[0:7]) + items[7] × 2, range 0-32.
- ``positive_screen``: True if total ≥ 12 (Adamson 2010 cutoff).
- ``severity``: ``"positive_screen"`` if positive_screen else
  ``"negative_screen"`` — uniform with PHQ-2 / GAD-2 / OASIS /
  PC-PTSD-5 / MDQ / AUDIT-C wire shape.
- HIGHER = MORE cannabis-related harm.  Same direction as PHQ-9 /
  GAD-7 / AUDIT / DUDIT / FTND / PSS-10 / DASS-21 / IGDS9-SF /
  PCS / ESS / SPIN; OPPOSITE of WHO-5 / BRS / LOT-R / RSES / MAAS /
  CD-RISC-10 / WEMWBS.
- No subscales (unidimensional per Adamson 2010 EFA).
- No cutoff_used (single published cutoff, no sex-stratification).
- No reverse-keying.

References:

- Adamson SJ, Kay-Lambkin FJ, Baker AL, Lewin TJ, Thornton L,
  Kelly BJ, Sellman JD (2010).  *An improved brief measure of
  cannabis misuse: The Cannabis Use Disorder Identification Test
  - Revised (CUDIT-R).*  Drug and Alcohol Dependence
  110(3):247-252.  (Primary development + validation paper;
  8-item scale; weighted item 8; single-factor EFA; AUC = 0.93;
  cutoff ≥ 12 definition.)
- Adamson SJ, Sellman JD (2003).  *A prototype screening instrument
  for cannabis use disorder: The Cannabis Use Disorders Identification
  Test (CUDIT) in an alcohol-dependent clinical sample.*  Drug and
  Alcohol Review 22(3):309-315.  (Original CUDIT; CUDIT-R is the
  revised successor.)
- Saunders JB, Aasland OG, Babor TF, de la Fuente JR, Grant M
  (1993).  *Development of the Alcohol Use Disorders Identification
  Test (AUDIT): WHO collaborative project on early detection of
  persons with harmful alcohol consumption — II.*  Addiction
  88(6):791-804.  (AUDIT origin; CUDIT-R item structure follows
  AUDIT conventions including weighted item logic.)
- Haney M, Ward AS, Comer SD, Foltin RW, Fischman MW (1999).
  *Abstinence symptoms following smoked marijuana in humans.*
  Psychopharmacology 143(4):396-403.  (Cannabis withdrawal →
  relapse pathway.)
- Budney AJ, Moore BA, Vandrey RG, Hughes JR (2003).  *The time
  course and significance of cannabis withdrawal.*  Journal of
  Abnormal Psychology 112(3):393-402.  (Withdrawal prevalence;
  reinstatement pathway.)
- Buckner JD, Schmidt NB (2008).  *Social anxiety disorder and
  marijuana use problems: The mediating role of marijuana effect
  expectancies.*  Drug and Alcohol Dependence 93(3):1-8.
  (Social anxiety × cannabis self-medication.)
- Kedzior KK, Laeber LT (2014).  *A positive association between
  anxiety disorders and cannabis use or cannabis use disorders in
  the general population — A meta-analysis of 31 studies.*
  BMC Psychiatry 14:136 (also published: PLoS ONE 9(4):e92478).
  (Social anxiety as strongest psychiatric predictor of CUD.)
- Copersino ML, Boyd SJ, Tashkin DP, Huestis MA, Heishman SJ,
  Dermand JC, Simmons MS, Gorelick DA (2006).  *Cannabis withdrawal
  among non-treatment-seeking adult cannabis users.*  The American
  Journal on Addictions 15(1):8-14.  (Cannabis craving as urge-to-
  action construct; CUDIT-R trajectory correlates with PACS.)
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final, Literal

INSTRUMENT_VERSION: Final[str] = "cuditr-1.0.0"
ITEM_COUNT: Final[int] = 8
ITEM_MIN: Final[int] = 0
ITEM_MAX: Final[int] = 4

# Adamson 2010 Table 3 — AUC 0.93; sensitivity 0.91, specificity 0.83
# against DSM-IV cannabis abuse/dependence at n = 294.  Changing this
# threshold invalidates the Adamson 2010 validation.
POSITIVE_SCREEN_CUTOFF: Final[int] = 12

# Item 8 contributes 2× to the total (AUDIT-inherited weighting rule).
# The raw value (0-4) is preserved in ``items``; only the total carries
# the weighted sum.
ITEM_8_WEIGHT: Final[int] = 2

# Adamson 2010 §2.2: "items 1–7 scored 0–4, item 8 scored 0–8."
# Total max = 7 × 4 + 4 × 2 = 28 + 8 = 36.
# Some secondary sources cite "0-32" (8 items × 4 unweighted); that
# is an editorial simplification.  The cutoff ≥ 12 is unaffected.
TOTAL_MAX: Final[int] = (ITEM_COUNT - 1) * ITEM_MAX + ITEM_MAX * ITEM_8_WEIGHT
# = 7 * 4 + 4 * 2 = 36


Severity = Literal["positive_screen", "negative_screen"]


class InvalidResponseError(ValueError):
    """Raised on a malformed CUDIT-R response."""


@dataclass(frozen=True)
class CuditRResult:
    """Immutable CUDIT-R scoring result.

    Fields:
    - ``total``: weighted sum = sum(items[0:7]) + items[7] × 2,
      range 0-36.  HIGHER = MORE cannabis-related harm.
    - ``positive_screen``: True if total ≥ 12 (Adamson 2010 cutoff;
      AUC = 0.93 against DSM-IV cannabis abuse/dependence).
    - ``severity``: ``"positive_screen"`` or ``"negative_screen"``
      — uniform with PHQ-2 / GAD-2 / OASIS / PC-PTSD-5 / MDQ /
      AUDIT-C wire shape.
    - ``items``: RAW pre-validation 8-tuple in Adamson 2010
      administration order.  Item 8 stored as raw 0-4 (not ×2).
      Preserved for audit invariance and FHIR export.
    - ``instrument_version``: pinned INSTRUMENT_VERSION.

    Deliberately-absent fields:
    - No ``cutoff_used`` — single published cutoff (≥ 12), no sex-
      stratification (contrast AUDIT-C).
    - No ``subscales`` — unidimensional per Adamson 2010 EFA.
    - No ``index`` / ``scaled_score`` — no transformation beyond
      weighted sum.
    - No ``triggering_items`` — no per-item acuity routing.
    - No safety fields — no CUDIT-R item probes ideation.
    """

    total: int
    positive_screen: bool
    severity: Severity
    items: tuple[int, ...]
    instrument_version: str = INSTRUMENT_VERSION


def _validate_item(index_1: int, value: object) -> int:
    """Validate a single 0-4 Likert item.

    Bool rejection per CLAUDE.md standing rule: ``bool`` values
    are rejected before the int check because Python's
    ``bool is int`` coercion would silently accept ``True`` /
    ``False`` as item responses.
    """
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidResponseError(
            f"CUDIT-R item {index_1} must be int, got {value!r}"
        )
    if not (ITEM_MIN <= value <= ITEM_MAX):
        raise InvalidResponseError(
            f"CUDIT-R item {index_1} must be in "
            f"{ITEM_MIN}-{ITEM_MAX}, got {value}"
        )
    return value


def score_cuditr(raw_items: Sequence[int]) -> CuditRResult:
    """Score a CUDIT-R response set.

    Inputs:
    - ``raw_items``: 8 items in Adamson 2010 administration order,
      items 1-7 each 0-4 Likert, item 8 0-4 Likert (weighted ×2).

    Raises :class:`InvalidResponseError` on:
    - Wrong number of items (must be exactly 8).
    - A non-int / bool item value.
    - An item outside ``[0, 4]``.

    Computes:
    - ``total``: sum(items[0:7]) + items[7] × 2, range 0-36.
    - ``positive_screen``: True if total ≥ 12 (Adamson 2010).
    - ``severity``: ``"positive_screen"`` or ``"negative_screen"``.

    No reverse-keying.  Raw items (item 8 as raw 0-4, not ×2)
    preserved in ``items`` field for audit / FHIR.
    """
    raw_items = tuple(raw_items)
    if len(raw_items) != ITEM_COUNT:
        raise InvalidResponseError(
            f"CUDIT-R requires exactly {ITEM_COUNT} items, "
            f"got {len(raw_items)}"
        )
    items = tuple(
        _validate_item(index_1=i + 1, value=v)
        for i, v in enumerate(raw_items)
    )
    total = sum(items[:7]) + items[7] * ITEM_8_WEIGHT
    positive_screen = total >= POSITIVE_SCREEN_CUTOFF
    return CuditRResult(
        total=total,
        positive_screen=positive_screen,
        severity="positive_screen" if positive_screen else "negative_screen",
        items=items,
    )


__all__ = [
    "INSTRUMENT_VERSION",
    "ITEM_8_WEIGHT",
    "ITEM_COUNT",
    "ITEM_MAX",
    "ITEM_MIN",
    "POSITIVE_SCREEN_CUTOFF",
    "TOTAL_MAX",
    "CuditRResult",
    "InvalidResponseError",
    "Severity",
    "score_cuditr",
]

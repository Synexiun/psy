"""AUDIT — Alcohol Use Disorders Identification Test (Saunders 1993,
10-item full form).

The full 10-item AUDIT is the WHO reference instrument for detecting
alcohol-use disorders.  It extends the 3-item AUDIT-C (consumption
subset) with seven items probing dependence symptoms and alcohol-
related problems, yielding a four-zone classification used worldwide
for risk stratification in primary care and behavioral-health intake.

Item structure (Saunders 1993, "In the past year..."):

**Consumption (items 1-3, 0-4 scale)** — identical to AUDIT-C wording:
 1. How often do you have a drink containing alcohol?
 2. How many drinks containing alcohol do you have on a typical day
    when drinking?
 3. How often do you have six or more drinks on one occasion?

**Dependence symptoms (items 4-6, 0-4 scale):**
 4. How often during the last year have you found that you were not
    able to stop drinking once you had started?
 5. How often during the last year have you failed to do what was
    normally expected of you because of drinking?
 6. How often during the last year have you needed a first drink in
    the morning to get yourself going after a heavy drinking session?

**Alcohol-related problems (items 7-10, mixed scales):**
 7. How often during the last year have you had a feeling of guilt or
    remorse after drinking? (0-4 scale)
 8. How often during the last year have you been unable to remember
    what happened the night before because of drinking? (0-4 scale)
 9. Have you or someone else been injured because of your drinking?
    **(0, 2, or 4 only — restricted 3-point scale)**
10. Has a relative, friend, doctor, or other health-care worker been
    concerned about your drinking or suggested you cut down?
    **(0, 2, or 4 only — restricted 3-point scale)**

Items 9 and 10 use a restricted 3-point scale per the WHO AUDIT manual
(0 = No, 2 = Yes, but not in the last year, 4 = Yes, during the last
year).  Accepting 1 or 3 on these items is a wire-format bug — the
instrument's published response set does not include those values and
the scorer rejects them to surface the bug at the boundary.

Total range: 0-40.

Severity zones (Saunders 1993 / WHO 2001 AUDIT manual):

- 0-7    low_risk       — Zone I: low-risk drinking or abstinence;
                          alcohol education.
- 8-15   hazardous      — Zone II: simple advice focused on reducing
                          consumption.
- 16-19  harmful        — Zone III: simple advice plus brief
                          counseling and continued monitoring.
- 20-40  dependence     — Zone IV: referral for diagnostic evaluation
                          and treatment.

The bands map to WHO-recommended action steps, not to DSM diagnoses;
AUDIT is a screen, not a diagnostic instrument.  A score of 20+ does
not diagnose alcohol dependence — it identifies a high probability
that a full clinical evaluation is warranted.

Safety routing:
AUDIT has **no safety item** (no C-SSRS-style suicidality question,
no PHQ-9-style item 9).  ``requires_t3`` is never set by this scorer.
A patient scoring Zone IV who is also in acute distress needs a
separate C-SSRS or PHQ-9 — the AUDIT's high-severity band is a
treatment-referral signal, not a crisis signal.

Relationship to AUDIT-C:
Items 1-3 of the full AUDIT are the AUDIT-C.  If a clinician submits
a full AUDIT, the first three items can also be interpreted through
AUDIT-C's sex-aware cutoffs for a secondary screen result — but this
scorer does NOT compute that.  A caller who wants both results must
submit both instruments; each is persisted as its own record.

Bool rejection note:
Python's ``bool`` subclasses ``int``, so ``isinstance(True, int)`` is
True and True/False would silently score as 1/0.  For the 0-4 scale
items that would mis-score (1 and 0 both map to clinically distinct
responses: "never" vs "monthly or less").  We reject bool inputs
explicitly.

References:
- Saunders JB, Aasland OG, Babor TF, de la Fuente JR, Grant M (1993).
  *Development of the Alcohol Use Disorders Identification Test
  (AUDIT): WHO Collaborative Project on Early Detection of Persons
  with Harmful Alcohol Consumption — II.* Addiction 88(6):791-804.
- Babor TF, Higgins-Biddle JC, Saunders JB, Monteiro MG (2001).
  *AUDIT: The Alcohol Use Disorders Identification Test — Guidelines
  for Use in Primary Care* (2nd ed.).  World Health Organization.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence

INSTRUMENT_VERSION = "audit-1.0.0"
ITEM_COUNT = 10
ITEM_MIN = 0
ITEM_MAX = 4

# Items 9 and 10 use the WHO-published 3-point scale (0, 2, 4 only).
# Pinned as a frozenset so the validation loop can check membership
# without a per-item if/else chain.  Mirrors DAST-10's frozen
# "special items" constant shape.
RESTRICTED_SCALE_ITEMS_1INDEXED: frozenset[int] = frozenset({9, 10})
RESTRICTED_SCALE_VALUES: frozenset[int] = frozenset({0, 2, 4})

# Severity-zone upper bounds per Saunders 1993 / WHO 2001.  Inclusive:
# low_risk at <=7, hazardous at <=15, harmful at <=19, dependence >=20.
AUDIT_LOW_RISK_UPPER = 7
AUDIT_HAZARDOUS_UPPER = 15
AUDIT_HARMFUL_UPPER = 19
AUDIT_TOTAL_MIN = 0
AUDIT_TOTAL_MAX = 40

Band = Literal["low_risk", "hazardous", "harmful", "dependence"]


class InvalidResponseError(ValueError):
    """Raised on item-count, item-range, or item-type violations."""


@dataclass(frozen=True)
class AuditResult:
    """Typed AUDIT output.

    Fields:
    - ``total``: 0-40, sum of all 10 items with items 9/10 constrained
      to the 3-point scale (0, 2, 4).
    - ``band``: ``low_risk`` / ``hazardous`` / ``harmful`` /
      ``dependence`` per WHO zones.  Maps directly to the clinician
      action ladder (education → advice → brief counseling → referral).
    - ``items``: verbatim caller input, pinned for auditability.  A
      clinician reviewing the record can re-derive both total and band
      from the items without trusting the stored aggregates.

    Unlike AUDIT-C there is NO sex-aware cutoff — the full AUDIT's
    zones are sex-neutral (WHO 2001 manual).  A regression that added
    a sex field here would silently deviate from the published scoring.
    """

    total: int
    band: Band
    items: tuple[int, ...]
    instrument_version: str = INSTRUMENT_VERSION


def _classify(total: int) -> Band:
    """Map total → severity zone per Saunders 1993 / WHO 2001.

    Zones are contiguous and non-overlapping; the first matching
    inclusive upper bound wins.  A total outside [0, 40] cannot reach
    this function (the scorer validates item ranges upstream), so no
    out-of-range clause is needed."""
    if total <= AUDIT_LOW_RISK_UPPER:
        return "low_risk"
    if total <= AUDIT_HAZARDOUS_UPPER:
        return "hazardous"
    if total <= AUDIT_HARMFUL_UPPER:
        return "harmful"
    return "dependence"


def _validate_item(index_1: int, value: object) -> int:
    """Validate a single item response and return the int value.

    ``index_1`` is the 1-indexed item number (1-10) so error messages
    can name the item the caller would recognize from the instrument
    document.  Items 9 and 10 are checked against the restricted
    3-point scale; all others against the 0-4 range.
    """
    # ``bool`` is a subclass of ``int``; reject before the int check so
    # True/False don't silently score as 1/0.
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidResponseError(
            f"AUDIT item {index_1} must be int, got {value!r}"
        )
    if index_1 in RESTRICTED_SCALE_ITEMS_1INDEXED:
        if value not in RESTRICTED_SCALE_VALUES:
            raise InvalidResponseError(
                f"AUDIT item {index_1} must be 0, 2, or 4 "
                f"(restricted 3-point scale per WHO 2001), got {value}"
            )
        return value
    if value < ITEM_MIN or value > ITEM_MAX:
        raise InvalidResponseError(
            f"AUDIT item {index_1} out of range "
            f"[{ITEM_MIN}, {ITEM_MAX}]: {value}"
        )
    return value


def score_audit(raw_items: Sequence[int]) -> AuditResult:
    """Score a full 10-item AUDIT response set.

    Inputs are 10 integer item responses in the published item order
    (1-10).  Items 1-8 are on the 0-4 scale; items 9 and 10 are on the
    restricted 0/2/4 scale per WHO 2001.

    Raises :class:`InvalidResponseError` on:
    - Wrong number of items (must be exactly 10).
    - A non-int item value (bools rejected explicitly for consistency
      with the rest of the psychometric package).
    - Item 1-8 value outside [0, 4].
    - Item 9 or 10 value outside {0, 2, 4}.

    Partial scoring is never acceptable — the zone classification
    would be systematically biased downward if even one item is
    missing, which could under-refer a patient in Zone IV.
    """
    if len(raw_items) != ITEM_COUNT:
        raise InvalidResponseError(
            f"AUDIT requires exactly {ITEM_COUNT} items, got {len(raw_items)}"
        )
    items = tuple(
        _validate_item(index_1=i + 1, value=v) for i, v in enumerate(raw_items)
    )
    total = sum(items)
    return AuditResult(total=total, band=_classify(total), items=items)


__all__ = [
    "AUDIT_HARMFUL_UPPER",
    "AUDIT_HAZARDOUS_UPPER",
    "AUDIT_LOW_RISK_UPPER",
    "AUDIT_TOTAL_MAX",
    "AUDIT_TOTAL_MIN",
    "AuditResult",
    "Band",
    "INSTRUMENT_VERSION",
    "InvalidResponseError",
    "ITEM_COUNT",
    "ITEM_MAX",
    "ITEM_MIN",
    "RESTRICTED_SCALE_ITEMS_1INDEXED",
    "RESTRICTED_SCALE_VALUES",
    "score_audit",
]

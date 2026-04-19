"""DUDIT — Drug Use Disorders Identification Test (Berman, Bergman,
Palmstierna, Schlyter 2003, 2005).

DUDIT is an 11-item parallel to the 10-item AUDIT, developed for
substance-use screening beyond alcohol.  Where AUDIT-C gives the
alcohol-hazardous-use signal in 3 items, DUDIT covers general drug use
(illicit drugs, non-medical prescription use, solvents) in 11 items.
Together with AUDIT-C (alcohol) and the Gossop 1995 SDS (specific-
substance dependence), DUDIT completes the substance-use screening
trio at the Discipline OS assessment layer.

Instrument structure (Berman 2005):

**Items 1-9 — 0-4 Likert frequency scale:**
    0 = Never
    1 = Once a month or less (items 1-2) / 1 time (items 3, 5-9)
    2 = 2-4 times a month (items 1-2) / 2-3 times a week (items 3, 5-9)
    3 = 2-3 times a week (items 1-2) / 4-6 times a week (items 3, 5-9)
    4 = 4 or more times a week (items 1-2) / 7 or more times a week

The Likert semantic varies by item but the numerical coding is uniform
0-4; for scoring purposes only the number matters, not the text.

**Items 10-11 — trinary 0/2/4 scale:**
    0 = No
    2 = Yes, but not in the last year
    4 = Yes, during the last year

Note: items 10-11 reject responses of 1 or 3 even though those fall
within the numerical envelope 0-4.  This is the novel validator shape
of DUDIT — non-uniform per-index ranges — and the reason the package
routes items 10-11 through a separate trinary validator.

The 11 items (Berman 2003 Table 1):
 1. How often do you use drugs other than alcohol?
 2. Do you use more than one type of drug on the same occasion?
 3. How many times do you take drugs on a typical day when you use drugs?
 4. How often are you influenced heavily by drugs?
 5. Over the past year, have you felt that your longing for drugs was
    so strong that you could not resist it?
 6. Has it happened that you have not been able to stop taking drugs
    once you started?
 7. How often have you taken drugs and then neglected to do something
    you should have done?
 8. How often have you needed to take a drug the morning after heavy
    drug use the day before?
 9. How often have you had guilt feelings or a bad conscience because
    you used drugs?
 10. Have you or anyone else been hurt (mentally or physically) because
     you used drugs?
 11. Has a doctor, nurse, psychologist, or social worker been worried
     about your drug use or said that you should stop?

Range: total 0-44 (items 1-9 contribute 0-36; items 10-11 contribute
0-8).  Unlike K10 / K6 / AUDIT-C, ITEM_MIN = 0 — Berman's coding puts
"Never" at 0 so a total of 0 is a genuine negative response, not a
coding artifact.

Sex-keyed cutoffs (Berman 2005):

| Sex          | Cutoff | Screen signal                              |
| ------------ | ------ | ------------------------------------------ |
| Male         | ≥ 6    | Probable drug-related problems             |
| Female       | ≥ 2    | Probable drug-related problems             |
| Unspecified  | ≥ 2    | Conservative default — matches female cutoff |

Validation (Berman 2005 against DSM-IV drug abuse/dependence):
- Men cutoff ≥6: sensitivity 0.90, specificity 0.88
- Women cutoff ≥2: sensitivity ~0.85, specificity ~0.80

The male/female asymmetry is larger than AUDIT-C's (6 vs 2 ≈ 3× gap;
AUDIT-C is 4 vs 3).  Reason per Berman 2005 §4 — women show drug-
related harm at substantially lower use frequencies than men; the
cutoff reflects the population distribution of use patterns, not
tolerance or metabolism alone.  A conservative safety posture for
sex-unspecified callers uses the female cutoff (= 2), mirroring the
AUDIT-C convention.

Envelope choice:
Cutoff envelope (positive_screen / negative_screen) with
``cutoff_used`` surfaced on the wire — uniform with AUDIT-C and SDS.
Berman 2005 did not publish a banded severity scale; some
secondary sources present ordinal bands (mild/moderate/severe) but
those are not calibrated against a published clinical criterion.
Per CLAUDE.md's "don't hand-roll severity thresholds" rule, the
banded shape is refused and the package surfaces only the Berman
2005 sex-keyed cutoff.

Safety routing:
DUDIT has **no direct safety item**.  Items 4 (heavily influenced),
5 (irresistible longing), and 6 (loss of control) probe substance-
use loss-of-control dimensions that may covary with impulsivity, but
none asks about suicidal thoughts, plans, or intent.  ``requires_t3``
is never set by this scorer — acute ideation screening is PHQ-9
item 9 / C-SSRS, not DUDIT.  Same posture as AUDIT-C and SDS.

Bool rejection note:
Uniform with the rest of the psychometric package — bool items are
rejected at the validator.  See mdq.py, pcptsd5.py, isi.py, pcl5.py,
ocir.py, bis11.py, phq2.py, gad2.py, oasis.py, k10.py, sds.py, k6.py
for the shared rationale.

References:
- Berman AH, Bergman H, Palmstierna T, Schlyter F (2003).  DUDIT —
  *The Drug Use Disorders Identification Test: MANUAL.*  Karolinska
  Institutet, Department of Clinical Neuroscience.
- Berman AH, Bergman H, Palmstierna T, Schlyter F (2005).  *Evaluation
  of the Drug Use Disorders Identification Test (DUDIT) in
  criminal-justice and detoxification settings and in a Swedish
  population sample.*  European Addiction Research 11(1):22-31.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence

INSTRUMENT_VERSION = "dudit-1.0.0"
ITEM_COUNT = 11

# Items 1-9 use the 0-4 Likert coding.
LIKERT_ITEM_MIN = 0
LIKERT_ITEM_MAX = 4

# Items 10-11 use the trinary 0/2/4 coding.  Responses of 1 or 3 are
# out-of-range even though they fall within the numerical envelope
# 0-4 — this is the novel validator shape of DUDIT.
TRINARY_VALUES: frozenset[int] = frozenset({0, 2, 4})

# 1-indexed item numbers that use the trinary scale (the last two
# DUDIT items — consequences and third-party concern).
TRINARY_ITEM_INDICES_1: frozenset[int] = frozenset({10, 11})

# Berman 2005 cutoffs.  Pinned as module constants so any change
# forces a clinical sign-off rather than slipping through as a tweak.
# Sensitivity / specificity calibration data is cited in the module
# docstring.
DUDIT_CUTOFF_MALE = 6
DUDIT_CUTOFF_FEMALE = 2
# Conservative default for sex-unspecified callers.  Mirrors the
# female cutoff (lower = more sensitive = safer in screening context).
# Same safety-conservatism convention as AUDIT-C.
DUDIT_CUTOFF_UNSPECIFIED = 2


# Reuse the AUDIT-C ``Sex`` shape verbatim — same demographic axis,
# same clinical convention.  A non-binary or prefer-not-to-say caller
# supplies ``"unspecified"`` (or simply omits) to receive the
# conservative threshold.
Sex = Literal["male", "female", "unspecified"]


class InvalidResponseError(ValueError):
    """Raised on item-count, item-range, or item-type violations."""


@dataclass(frozen=True)
class DuditResult:
    """Typed DUDIT output.

    Fields:
    - ``total``: 0-44, sum of the eleven items (items 1-9 contribute
      0-36; items 10-11 contribute 0-8).
    - ``cutoff_used``: the integer cutoff applied (2 or 6), surfaced
      so downstream renderers can show 'positive at ≥ N' without
      re-implementing the sex → cutoff mapping.
    - ``positive_screen``: ``total >= cutoff_used``.  The actionable
      flag — true means route to follow-up.
    - ``sex``: the demographic axis used to select the cutoff.
      Echoed for audit traceability.
    - ``items``: verbatim item echo.

    Safety posture: ``requires_t3`` is deliberately absent from this
    dataclass.  DUDIT has no safety item.  See module docstring.
    """

    total: int
    cutoff_used: int
    positive_screen: bool
    sex: Sex
    items: tuple[int, ...]
    instrument_version: str = INSTRUMENT_VERSION


def _cutoff_for(sex: Sex) -> int:
    """Map sex to the Berman 2005 cutoff value.

    ``unspecified`` falls back to the lower (more sensitive) cutoff —
    safety-conservatism in screening.  Same convention as AUDIT-C.
    """
    if sex == "male":
        return DUDIT_CUTOFF_MALE
    if sex == "female":
        return DUDIT_CUTOFF_FEMALE
    return DUDIT_CUTOFF_UNSPECIFIED


def _validate_item(index_1: int, value: object) -> int:
    """Validate a single DUDIT item.

    ``index_1`` is the 1-indexed item number (1-11).  Items 1-9 take
    the 0-4 Likert envelope; items 10-11 take the {0, 2, 4} trinary
    envelope.  A response of 1 or 3 on an item-10/11 slot is rejected
    even though it sits within the numerical envelope 0-4 — that's
    the novel validator shape DUDIT contributes to this package.
    """
    # Bool rejection — uniform with the rest of the psychometric package.
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidResponseError(
            f"DUDIT item {index_1} must be int, got {value!r}"
        )

    if index_1 in TRINARY_ITEM_INDICES_1:
        if value not in TRINARY_VALUES:
            raise InvalidResponseError(
                f"DUDIT item {index_1} must be 0, 2, or 4 "
                f"(trinary yes/no-but-not-in-last-year/yes-in-last-year): "
                f"got {value}"
            )
        return value

    # Likert items 1-9.
    if value < LIKERT_ITEM_MIN or value > LIKERT_ITEM_MAX:
        raise InvalidResponseError(
            f"DUDIT item {index_1} out of range "
            f"[{LIKERT_ITEM_MIN}, {LIKERT_ITEM_MAX}]: {value}"
        )
    return value


def score_dudit(
    raw_items: Sequence[int],
    *,
    sex: Sex = "unspecified",
) -> DuditResult:
    """Score a DUDIT response set with a sex-aware cutoff.

    Inputs:
    - ``raw_items``: 11 items.  Items 1-9 are 0-4 Likert; items 10-11
      are {0, 2, 4} trinary.
    - ``sex``: demographic axis used to select the cutoff.  Defaults
      to ``"unspecified"`` so callers without a sex value get the
      safety-conservative behavior automatically (= female cutoff).

    Raises :class:`InvalidResponseError` on:
    - Wrong number of items.
    - A non-int / bool item value.
    - A Likert item (1-9) outside ``[0, 4]``.
    - A trinary item (10-11) outside ``{0, 2, 4}``.
    """
    if len(raw_items) != ITEM_COUNT:
        raise InvalidResponseError(
            f"DUDIT requires exactly {ITEM_COUNT} items, got {len(raw_items)}"
        )
    items = tuple(
        _validate_item(index_1=i + 1, value=v)
        for i, v in enumerate(raw_items)
    )
    total = sum(items)
    cutoff = _cutoff_for(sex)
    return DuditResult(
        total=total,
        cutoff_used=cutoff,
        positive_screen=total >= cutoff,
        sex=sex,
        items=items,
    )


__all__ = [
    "DUDIT_CUTOFF_FEMALE",
    "DUDIT_CUTOFF_MALE",
    "DUDIT_CUTOFF_UNSPECIFIED",
    "DuditResult",
    "INSTRUMENT_VERSION",
    "ITEM_COUNT",
    "InvalidResponseError",
    "LIKERT_ITEM_MAX",
    "LIKERT_ITEM_MIN",
    "Sex",
    "TRINARY_ITEM_INDICES_1",
    "TRINARY_VALUES",
    "score_dudit",
]

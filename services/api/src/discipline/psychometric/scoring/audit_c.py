"""AUDIT-C alcohol-use screening — Bush et al. (1998).

A 3-item subset of the full 10-item AUDIT (Saunders 1993), validated
as a stand-alone screen for hazardous drinking and active alcohol use
disorders.  Each item is scored 0–4; total ranges 0–12.

Items (verbatim wording per Bush 1998):

1. How often did you have a drink containing alcohol in the past year?
   0 = Never, 1 = Monthly or less, 2 = 2–4 times a month,
   3 = 2–3 times a week, 4 = 4 or more times a week.

2. How many drinks containing alcohol did you have on a typical day
   when you were drinking in the past year?
   0 = 1 or 2, 1 = 3 or 4, 2 = 5 or 6, 3 = 7–9, 4 = 10 or more.

3. How often did you have six or more drinks on one occasion in the
   past year?
   0 = Never, 1 = Less than monthly, 2 = Monthly, 3 = Weekly,
   4 = Daily or almost daily.

Cutoffs (Bush 1998):

- Men: total ≥ 4 = positive screen.
- Women: total ≥ 3 = positive screen.
- Sex unspecified / non-binary / prefer-not-to-say: use the LOWER
  cutoff (≥ 3).  This is a safety-conservatism call — it's better to
  over-flag and let a clinician adjudicate than to under-flag and
  miss a problem-drinking signal.

Notes:
- The instrument's scoring is a pure sum.  It does NOT enforce
  internal consistency (e.g., a 0 on item 1 with high values on items
  2/3 is mathematically possible but logically incoherent — the
  instrument lets it through; we match that behavior).
- AUDIT-C is a SCREEN, not a diagnosis.  A positive screen indicates
  hazardous drinking *probability* and routes the user to a follow-up
  conversation, not an automatic referral.

References:
- Bush K, Kivlahan DR, McDonell MB, Fihn SD, Bradley KA (1998).
  *The AUDIT alcohol consumption questions (AUDIT-C): an effective
  brief screening test for problem drinking.* Arch Intern Med
  158(16):1789-1795.
- Saunders JB, Aasland OG, Babor TF, et al. (1993). *Development of
  the Alcohol Use Disorders Identification Test (AUDIT).* Addiction
  88(6):791-804.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

INSTRUMENT_VERSION = "audit-c-1.0.0"
ITEM_COUNT = 3
ITEM_MIN, ITEM_MAX = 0, 4

# Bush 1998 cutoffs.  Pinned as module constants so any change forces
# a clinical sign-off rather than slipping through as a tweak.
AUDIT_C_CUTOFF_MALE = 4
AUDIT_C_CUTOFF_FEMALE = 3
# Conservative default for sex-unspecified callers.  Mirrors female
# cutoff (lower = more sensitive = safer in screening context).
AUDIT_C_CUTOFF_UNSPECIFIED = 3


# ``Sex`` is the demographic axis that selects the cutoff, NOT a claim
# about gender identity.  A non-binary user can supply ``"unspecified"``
# (or simply omit) to receive the conservative threshold.  We avoid the
# more politically-loaded ``Gender`` here to make clear this is a
# clinical-screening parameter pinned to published validation data.
Sex = Literal["male", "female", "unspecified"]


class InvalidResponseError(ValueError):
    """Raised on item-count or item-range violations."""


@dataclass(frozen=True)
class AuditCResult:
    """Typed AUDIT-C output.

    Fields:
    - ``total``: 0–12, sum of the three items.
    - ``cutoff_used``: the integer cutoff that was applied (3 or 4),
      surfaced so downstream renderers can show 'positive at ≥ N'
      without re-implementing the sex → cutoff mapping.
    - ``positive_screen``: ``total >= cutoff_used``.  The actionable
      flag — true means route to follow-up.
    - ``sex``: the demographic axis used to select the cutoff.
      Echoed for audit traceability.
    - ``items``: verbatim item echo.
    """

    total: int
    cutoff_used: int
    positive_screen: bool
    sex: Sex
    items: tuple[int, ...]
    instrument_version: str = INSTRUMENT_VERSION


def _cutoff_for(sex: Sex) -> int:
    """Map sex to the Bush 1998 cutoff value.

    ``unspecified`` falls back to the lower (more sensitive) cutoff —
    safety-conservatism in screening."""
    if sex == "male":
        return AUDIT_C_CUTOFF_MALE
    if sex == "female":
        return AUDIT_C_CUTOFF_FEMALE
    return AUDIT_C_CUTOFF_UNSPECIFIED


def score_audit_c(
    raw_items: Sequence[int],
    *,
    sex: Sex = "unspecified",
) -> AuditCResult:
    """Score an AUDIT-C response set with a sex-aware cutoff.

    ``sex`` defaults to ``"unspecified"`` so callers that don't have
    or don't want to send a sex value get the safety-conservative
    behavior automatically.

    Raises :class:`InvalidResponseError` on item-count or item-range
    violations; partial scoring is never acceptable for a clinical
    screen.
    """
    if len(raw_items) != ITEM_COUNT:
        raise InvalidResponseError(
            f"AUDIT-C requires exactly {ITEM_COUNT} items, got {len(raw_items)}"
        )
    items = tuple(int(v) for v in raw_items)
    for idx, v in enumerate(items):
        if v < ITEM_MIN or v > ITEM_MAX:
            raise InvalidResponseError(
                f"AUDIT-C item {idx + 1} out of range "
                f"[{ITEM_MIN}, {ITEM_MAX}]: {v}"
            )
    total = sum(items)
    cutoff = _cutoff_for(sex)
    return AuditCResult(
        total=total,
        cutoff_used=cutoff,
        positive_screen=total >= cutoff,
        sex=sex,
        items=items,
    )


__all__ = [
    "AUDIT_C_CUTOFF_FEMALE",
    "AUDIT_C_CUTOFF_MALE",
    "AUDIT_C_CUTOFF_UNSPECIFIED",
    "INSTRUMENT_VERSION",
    "AuditCResult",
    "InvalidResponseError",
    "Sex",
    "score_audit_c",
]

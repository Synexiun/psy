"""PHQ-9 scoring — Kroenke, Spitzer, Williams (2001).

PHQ-9 has nine items, each scored 0–3 ("Not at all", "Several days", "More than
half the days", "Nearly every day").  Total is the straight sum, 0–27.

Severity bands (Kroenke 2001, Table 3):
    0–4   None / minimal
    5–9   Mild
    10–14 Moderate
    15–19 Moderately severe
    20–27 Severe

Item 9 ("Thoughts that you would be better off dead, or of hurting yourself in some
way") MUST be inspected by ``discipline.psychometric.safety_items.evaluate_phq9``
before a response is returned to the user.  Any positive value on item 9 routes
through the safety framework — see Docs/Whitepapers/04_Safety_Framework.md §T4.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

INSTRUMENT_VERSION = "phq9-1.0.0"
ITEM_COUNT = 9
ITEM_MIN, ITEM_MAX = 0, 3

PHQ9_SEVERITY_THRESHOLDS: tuple[tuple[int, str], ...] = (
    (4, "none"),
    (9, "mild"),
    (14, "moderate"),
    (19, "moderately_severe"),
    (27, "severe"),
)

PHQ9_SAFETY_ITEM_INDEX = 8  # zero-indexed; item 9 in one-indexed clinical language


class InvalidResponseError(ValueError):
    """Raised when raw items fail validation.  Never caught — partial scoring is a bug."""


Severity = Literal["none", "mild", "moderate", "moderately_severe", "severe"]


@dataclass(frozen=True)
class Phq9Result:
    total: int
    severity: Severity
    items: tuple[int, ...]
    safety_item_positive: bool
    instrument_version: str = INSTRUMENT_VERSION


def _classify(total: int) -> Severity:
    for upper, label in PHQ9_SEVERITY_THRESHOLDS:
        if total <= upper:
            return label  # type: ignore[return-value]
    # Unreachable — classified list ends at 27.
    raise InvalidResponseError(f"total out of range: {total}")


def score_phq9(raw_items: Sequence[int]) -> Phq9Result:
    if len(raw_items) != ITEM_COUNT:
        raise InvalidResponseError(
            f"PHQ-9 requires exactly {ITEM_COUNT} items, got {len(raw_items)}"
        )
    items = tuple(int(v) for v in raw_items)
    for idx, v in enumerate(items):
        if v < ITEM_MIN or v > ITEM_MAX:
            raise InvalidResponseError(
                f"PHQ-9 item {idx + 1} out of range [{ITEM_MIN}, {ITEM_MAX}]: {v}"
            )
    total = sum(items)
    return Phq9Result(
        total=total,
        severity=_classify(total),
        items=items,
        safety_item_positive=items[PHQ9_SAFETY_ITEM_INDEX] > 0,
    )


__all__ = [
    "INSTRUMENT_VERSION",
    "PHQ9_SEVERITY_THRESHOLDS",
    "InvalidResponseError",
    "Phq9Result",
    "Severity",
    "score_phq9",
]

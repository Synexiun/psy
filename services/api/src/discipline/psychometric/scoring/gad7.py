"""GAD-7 scoring — Spitzer, Kroenke, Williams, Löwe (2006).

Seven items, each 0–3.  Total 0–21.

Severity bands (Spitzer 2006):
     0–4   None / minimal
     5–9   Mild
    10–14  Moderate
    15–21  Severe
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

INSTRUMENT_VERSION = "gad7-1.0.0"
ITEM_COUNT = 7
ITEM_MIN, ITEM_MAX = 0, 3

GAD7_SEVERITY_THRESHOLDS: tuple[tuple[int, str], ...] = (
    (4, "none"),
    (9, "mild"),
    (14, "moderate"),
    (21, "severe"),
)


class InvalidResponseError(ValueError):
    """Raised when raw items fail validation."""


Severity = Literal["none", "mild", "moderate", "severe"]


@dataclass(frozen=True)
class Gad7Result:
    total: int
    severity: Severity
    items: tuple[int, ...]
    instrument_version: str = INSTRUMENT_VERSION


def _classify(total: int) -> Severity:
    for upper, label in GAD7_SEVERITY_THRESHOLDS:
        if total <= upper:
            return label  # type: ignore[return-value]
    raise InvalidResponseError(f"total out of range: {total}")


def score_gad7(raw_items: Sequence[int]) -> Gad7Result:
    if len(raw_items) != ITEM_COUNT:
        raise InvalidResponseError(
            f"GAD-7 requires exactly {ITEM_COUNT} items, got {len(raw_items)}"
        )
    items = tuple(int(v) for v in raw_items)
    for idx, v in enumerate(items):
        if v < ITEM_MIN or v > ITEM_MAX:
            raise InvalidResponseError(
                f"GAD-7 item {idx + 1} out of range [{ITEM_MIN}, {ITEM_MAX}]: {v}"
            )
    total = sum(items)
    return Gad7Result(total=total, severity=_classify(total), items=items)


__all__ = [
    "GAD7_SEVERITY_THRESHOLDS",
    "INSTRUMENT_VERSION",
    "Gad7Result",
    "InvalidResponseError",
    "Severity",
    "score_gad7",
]

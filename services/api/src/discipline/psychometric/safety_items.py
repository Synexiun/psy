"""PHQ-9 item 9 / C-SSRS → safety routing.

The rule is simple and absolute: ANY positive value on PHQ-9 item 9, OR ANY positive
C-SSRS ideation/behavior item, triggers the T3 safety path.  No threshold tuning,
no per-user calibration, no LLM in the loop.

Downstream:
- The ``intervention.t3`` router receives ``SafetyRoutingSignal`` events.
- The T4 escalation (to emergency resources) is a UI-side decision informed by
  :func:`evaluate_phq9` output; this module does NOT trigger T4 directly.

See Docs/Whitepapers/04_Safety_Framework.md §Safety items.
"""

from __future__ import annotations

from dataclasses import dataclass

from .scoring.phq9 import Phq9Result


@dataclass(frozen=True)
class SafetyRoutingSignal:
    requires_t3: bool
    reason: str
    source: str  # e.g. "phq9.item9", "cssrs.ideation.4"


def evaluate_phq9(result: Phq9Result) -> SafetyRoutingSignal | None:
    if result.safety_item_positive:
        return SafetyRoutingSignal(
            requires_t3=True,
            reason="phq9_item9_positive",
            source="phq9.item9",
        )
    return None


__all__ = ["SafetyRoutingSignal", "evaluate_phq9"]

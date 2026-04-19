"""C-SSRS Screen — Posner et al. (2008/2011) suicidality assessment.

The Columbia Suicide Severity Rating Scale (C-SSRS) Screen is the
6-item structured screen that follows up on PHQ-9 item 9 / patient-
report concern.  Where PHQ-9 item 9 is a single-item screen, C-SSRS
asks structured questions to differentiate **passive ideation** from
**active intent / plan / behavior** — which is the difference between
"check in next visit" and "do not let this person walk out alone".

Items (Lifetime version of the screen, verbatim wording per Posner
2011 Recent/Lifetime form):

1. Have you wished you were dead or wished you could go to sleep
   and not wake up? (passive ideation)
2. Have you actually had any thoughts of killing yourself?
   (active ideation, no method)
3. Have you been thinking about how you might do this?
   (active ideation, with method, no specific plan or intent)
4. Have you had these thoughts and had some intention of acting on them?
   (active ideation with some intent to act, no specific plan)
5. Have you started to work out or worked out the details of how to
   kill yourself? Do you intend to carry out this plan?
   (active ideation with specific plan and intent)
6. Have you ever done anything, started to do anything, or prepared to
   do anything to end your life? (suicidal behavior — past)

Routing rules (Posner 2011 §Triage decisions):

- Items 1-2 only → low risk; clinician check-in.
- Item 3 positive → moderate risk flag; supportive intervention.
- Item 4 OR item 5 positive → **acute T3 trigger**.  This is the
  threshold below which a person should not leave unsupervised.
- Item 6 positive WITH ``behavior_within_3mo=True`` → **acute T3**.
  Recent past behavior is the strongest single predictor of near-term
  re-attempt; the scorer needs the caller's recency judgment because
  it has no clock of its own.
- Item 6 positive but NOT within 3 months → **moderate**.  Lifetime
  history of suicidal behavior is a known longitudinal risk factor
  (Posner 2011 §Discussion) — it never returns "none" even when the
  active-ideation items are all negative.  Defaulting to "none" here
  would understate risk for a patient with a prior attempt who is
  currently asymptomatic.

The escalation logic is **disjunctive** — any single triggering item
fires T3.  A refactor that joins them with ``and`` would silently
suppress the majority of acute cases.  Every routing path is tested.

Reference:
- Posner K, Brown GK, Stanley B, Brent DA, Yershova KV, Oquendo MA,
  Currier GW, Melvin GA, Greenhill L, Shen S, Mann JJ (2011).
  *The Columbia–Suicide Severity Rating Scale: initial validity and
  internal consistency findings from three multisite studies with
  adolescents and adults.* Am J Psychiatry 168(12):1266-1277.
- Original Posner K, Oquendo MA, Gould M, et al. (2007/2008).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence

INSTRUMENT_VERSION = "cssrs-screen-1.0.0"
ITEM_COUNT = 6

# Zero-indexed item positions for clarity at the call site.  One-
# indexed names live in the docstring + clinician-facing UI.
ITEM_PASSIVE_IDEATION = 0
ITEM_ACTIVE_IDEATION = 1
ITEM_METHOD = 2
ITEM_INTENT = 3
ITEM_PLAN = 4
ITEM_PAST_BEHAVIOR = 5

# Risk band labels mirror the Posner 2011 triage table.  "acute" maps
# to the T3 crisis path; "moderate" to a supportive intervention;
# "low" to clinician check-in next visit; "none" to no positive items.
Risk = Literal["none", "low", "moderate", "acute"]


class InvalidResponseError(ValueError):
    """Raised on item-count violations.  Item *values* are bool by type
    so range-checking is the type system's job."""


@dataclass(frozen=True)
class CssrsResult:
    """Typed C-SSRS Screen output.

    Fields:
    - ``items``: verbatim bool tuple (length 6).
    - ``positive_count``: how many items were True.  Useful for
      tracking change over time independently of the risk band.
    - ``risk``: clinical band per Posner 2011 triage rules.
    - ``requires_t3``: True iff items 4/5 fired OR item 6 fired with
      ``behavior_within_3mo``.  This is the actionable flag — UI keys
      crisis routing on this single boolean.
    - ``triggering_items``: 1-indexed item numbers that drove the
      escalation, for clinician review and audit.  Empty tuple when
      no items fired.
    - ``behavior_within_3mo``: echoed input — pinned in result so the
      audit trail records the recency judgment that drove the band.
    """

    items: tuple[bool, ...]
    positive_count: int
    risk: Risk
    requires_t3: bool
    triggering_items: tuple[int, ...]
    behavior_within_3mo: bool
    instrument_version: str = INSTRUMENT_VERSION


def _classify(
    items: tuple[bool, ...],
    *,
    behavior_within_3mo: bool,
) -> tuple[Risk, bool, tuple[int, ...]]:
    """Apply the Posner 2011 triage rules.

    Returns ``(risk_band, requires_t3, triggering_items)`` so the
    caller can populate one consistent set of fields.

    Triage precedence (highest first):
    - Item 4 OR 5 positive → acute T3.
    - Item 6 positive with recent behavior → acute T3.
    - Item 3 positive OR item 6 positive (historic) → moderate.
    - Items 1-2 positive (only) → low.
    - Nothing positive → none.

    The precedence matters: a person with items 1+2+4 positive is
    ``acute``, not ``low``.  Without ordering by severity, a naive
    "first match" classifier could mis-bucket them.

    Historic item 6 is intentionally a ``moderate`` signal even when
    every other item is negative: lifetime history of suicidal
    behavior is itself a longitudinal risk factor and should never
    classify as ``none``."""
    triggering: list[int] = []

    intent_positive = items[ITEM_INTENT]
    plan_positive = items[ITEM_PLAN]
    behavior_positive = items[ITEM_PAST_BEHAVIOR]
    method_positive = items[ITEM_METHOD]

    if intent_positive:
        triggering.append(ITEM_INTENT + 1)
    if plan_positive:
        triggering.append(ITEM_PLAN + 1)
    if behavior_positive and behavior_within_3mo:
        triggering.append(ITEM_PAST_BEHAVIOR + 1)

    if triggering:
        return "acute", True, tuple(triggering)

    # Item 3 positive (any) or item 6 positive (historic only — recent
    # was already routed to acute above) → moderate.  Both can fire
    # together; both surface in triggering_items.
    if method_positive or behavior_positive:
        moderate_items: list[int] = []
        if method_positive:
            moderate_items.append(ITEM_METHOD + 1)
        if behavior_positive:
            moderate_items.append(ITEM_PAST_BEHAVIOR + 1)
        return "moderate", False, tuple(moderate_items)

    if items[ITEM_PASSIVE_IDEATION] or items[ITEM_ACTIVE_IDEATION]:
        passive_active: list[int] = []
        if items[ITEM_PASSIVE_IDEATION]:
            passive_active.append(ITEM_PASSIVE_IDEATION + 1)
        if items[ITEM_ACTIVE_IDEATION]:
            passive_active.append(ITEM_ACTIVE_IDEATION + 1)
        return "low", False, tuple(passive_active)

    return "none", False, ()


def score_cssrs_screen(
    raw_items: Sequence[bool],
    *,
    behavior_within_3mo: bool = False,
) -> CssrsResult:
    """Score a C-SSRS Screen response set.

    Inputs are the 6 boolean item responses, in the published item
    order (1-6).  ``behavior_within_3mo`` defaults to ``False`` —
    the safer default in the absence of recency context is "treat
    item 6 as historic, not acute" so we don't over-trigger T3 on
    long-past behavior.  Callers WITH recency context (interview
    answer "yes, in the past 3 months") must pass ``True``.

    Raises :class:`InvalidResponseError` if the wrong number of
    items is supplied; partial scoring is never acceptable for a
    suicidality instrument.
    """
    if len(raw_items) != ITEM_COUNT:
        raise InvalidResponseError(
            f"C-SSRS Screen requires exactly {ITEM_COUNT} items, "
            f"got {len(raw_items)}"
        )
    items = tuple(bool(v) for v in raw_items)
    positive_count = sum(1 for v in items if v)
    risk, requires_t3, triggering = _classify(
        items, behavior_within_3mo=behavior_within_3mo
    )
    return CssrsResult(
        items=items,
        positive_count=positive_count,
        risk=risk,
        requires_t3=requires_t3,
        triggering_items=triggering,
        behavior_within_3mo=behavior_within_3mo,
    )


__all__ = [
    "CssrsResult",
    "INSTRUMENT_VERSION",
    "InvalidResponseError",
    "ITEM_ACTIVE_IDEATION",
    "ITEM_INTENT",
    "ITEM_METHOD",
    "ITEM_PASSIVE_IDEATION",
    "ITEM_PAST_BEHAVIOR",
    "ITEM_PLAN",
    "Risk",
    "score_cssrs_screen",
]

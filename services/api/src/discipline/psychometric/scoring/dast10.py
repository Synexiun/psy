"""DAST-10 — Drug Abuse Screening Test (Skinner 1982, 10-item short form).

The DAST-10 is a 10-item self-report screen for drug-use problems in
the past 12 months.  It is widely used in primary care, behavioral
health, and substance-use treatment intake because it runs in under
two minutes and produces a single categorical band that maps directly
to a clinical action ladder.

Items (Skinner 1982, "In the past 12 months..."):

 1. Have you used drugs other than those required for medical reasons?
 2. Do you abuse more than one drug at a time?
 3. Are you always able to stop using drugs when you want to?  [REVERSE]
 4. Have you had "blackouts" or "flashbacks" as a result of drug use?
 5. Do you ever feel bad or guilty about your drug use?
 6. Does your spouse (or parents) ever complain about your involvement
    with drugs?
 7. Have you neglected your family because of your use of drugs?
 8. Have you engaged in illegal activities in order to obtain drugs?
 9. Have you ever experienced withdrawal symptoms (felt sick) when
    you stopped taking drugs?
10. Have you had medical problems as a result of your drug use (e.g.
    memory loss, hepatitis, convulsions, bleeding, etc.)?

Response scale: 0 = No, 1 = Yes.  A patient who answers "no" to item 3
("Are you always able to stop?") is endorsing lack of control, so
item 3 is **reverse-scored** (raw 0 → 1, raw 1 → 0) before summation.
This is the only reverse-scored item in the instrument; mis-applying
reverse-scoring to any other item silently inverts the clinical meaning
of that item and mis-bands the screen.

Total range: 0-10.

Severity bands (Skinner 1982, documented in SAMHSA and Cocco &
Carey 1998 scoring guidance):

- 0        none          — no problems reported (no clinical action)
- 1–2      low           — monitor, re-assess later
- 3–5      moderate      — further assessment / brief intervention
- 6–8      substantial   — assessment + treatment referral
- 9–10     severe        — intensive treatment evaluation

The bands map to action, not diagnosis — the DAST-10 is not a DSM
diagnostic instrument.  A "substantial" or "severe" band prompts a
full clinical assessment; the scorer does not itself diagnose a
substance use disorder.

Safety routing:
The DAST-10 has **no safety item** (no C-SSRS-style suicidality
question, no PHQ-9-style item 9).  ``requires_t3`` is never set by
this scorer.  If a patient scores severe and is in acute distress,
that signal comes from a separate co-administered C-SSRS or PHQ-9,
not from the DAST-10 itself.

Bool rejection note:
Python's ``bool`` subclasses ``int``, so ``isinstance(True, int)``
is True and True/False would silently score as 1/0.  For most
instruments that's a wire-format bug we reject; for the DAST-10
specifically it would happen to produce the clinically correct
mapping, but accepting booleans would be inconsistent with the
other instruments in this package and hide wire-format bugs on the
client side.  We reject bool inputs explicitly for consistency.

Reference:
- Skinner HA (1982). *The Drug Abuse Screening Test.* Addictive
  Behaviors 7(4):363-371.
- Cocco KM, Carey KB (1998). *Psychometric properties of the Drug
  Abuse Screening Test in psychiatric outpatients.* Psychological
  Assessment 10(4):408-414.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

INSTRUMENT_VERSION = "dast10-1.0.0"
ITEM_COUNT = 10
ITEM_MIN = 0
ITEM_MAX = 1

# 1-indexed item number that is positively worded and therefore
# reverse-scored.  Item 3 ("Are you always able to stop using drugs
# when you want to?") is the only reverse-scored item in the DAST-10.
# Pinned as a frozenset (parallel to PSS-10's reverse-scored set)
# so downstream readers have a consistent interface across the
# instrument family, even though there's only one element here.
REVERSE_SCORED_ITEMS_1INDEXED: frozenset[int] = frozenset({3})

# Severity-band cutoffs per Skinner 1982.  Inclusive upper bounds:
# none at 0, low <= 2, moderate <= 5, substantial <= 8, severe >= 9.
DAST10_NONE_UPPER = 0
DAST10_LOW_UPPER = 2
DAST10_MODERATE_UPPER = 5
DAST10_SUBSTANTIAL_UPPER = 8
DAST10_TOTAL_MIN = 0
DAST10_TOTAL_MAX = 10

Band = Literal["none", "low", "moderate", "substantial", "severe"]


class InvalidResponseError(ValueError):
    """Raised on item-count, item-range, or item-type violations."""


@dataclass(frozen=True)
class Dast10Result:
    """Typed DAST-10 output.

    Fields:
    - ``total``: sum after reverse-scoring (0-10).  This is the
      published total — clients display this, not ``raw_items`` sum.
    - ``band``: ``none`` / ``low`` / ``moderate`` / ``substantial``
      / ``severe`` per the documented cutoffs.
    - ``raw_items``: the verbatim caller input, pre-reversal.  Pinned
      in the result so an auditor can verify the reversal was applied
      correctly without re-running the scorer.
    - ``scored_items``: post-reversal item values, in 1-10 order.
      Useful for FHIR export where each item is a separate Observation
      component and consumers want the *scored* value.
    """

    total: int
    band: Band
    raw_items: tuple[int, ...]
    scored_items: tuple[int, ...]
    instrument_version: str = INSTRUMENT_VERSION


def _reverse(value: int) -> int:
    """Invert a 0/1 response to its complement (0↔1).

    Implemented as ``ITEM_MAX - value`` rather than ``1 - value`` so
    a future change to the response scale (hypothetical 0-N variant)
    requires only changing ``ITEM_MAX`` — keeps the dependency on
    the scale explicit."""
    return ITEM_MAX - value


def _classify(total: int) -> Band:
    """Map total → severity band per Skinner 1982.

    The bands are contiguous and non-overlapping; precedence is by
    inclusive upper bound so the first matching bucket wins.  A total
    outside [0, 10] cannot reach this function (the scorer validates
    item ranges upstream), so no out-of-range clause is needed."""
    if total <= DAST10_NONE_UPPER:
        return "none"
    if total <= DAST10_LOW_UPPER:
        return "low"
    if total <= DAST10_MODERATE_UPPER:
        return "moderate"
    if total <= DAST10_SUBSTANTIAL_UPPER:
        return "substantial"
    return "severe"


def score_dast10(raw_items: Sequence[int]) -> Dast10Result:
    """Score a DAST-10 response set.

    Inputs are 10 integer item responses (0 = No, 1 = Yes) in the
    published item order (1-10).  Item 3 is reverse-scored inside
    the function; callers pass the raw response value.

    Raises :class:`InvalidResponseError` on:
    - Wrong number of items (must be exactly 10).
    - An item value outside [0, 1].
    - A non-int item value (bools coerce to 0/1 implicitly via
      ``isinstance(bool, int)`` but we reject them explicitly for
      consistency with the rest of the psychometric package; see the
      module docstring for rationale).

    Partial scoring is never acceptable — the band would be
    misclassified if even one item is missing.
    """
    if len(raw_items) != ITEM_COUNT:
        raise InvalidResponseError(
            f"DAST-10 requires exactly {ITEM_COUNT} items, got {len(raw_items)}"
        )

    raw_list: list[int] = []
    for index, value in enumerate(raw_items, start=1):
        # ``bool`` is an ``int`` subclass — reject it before the int
        # check so True/False don't silently become 1/0.
        if isinstance(value, bool) or not isinstance(value, int):
            raise InvalidResponseError(
                f"DAST-10 item {index} must be int in [{ITEM_MIN}, {ITEM_MAX}], "
                f"got {value!r}"
            )
        if value < ITEM_MIN or value > ITEM_MAX:
            raise InvalidResponseError(
                f"DAST-10 item {index} out of range "
                f"[{ITEM_MIN}, {ITEM_MAX}]: {value}"
            )
        raw_list.append(value)

    scored_list = [
        _reverse(v) if (i + 1) in REVERSE_SCORED_ITEMS_1INDEXED else v
        for i, v in enumerate(raw_list)
    ]
    total = sum(scored_list)
    band = _classify(total)

    return Dast10Result(
        total=total,
        band=band,
        raw_items=tuple(raw_list),
        scored_items=tuple(scored_list),
    )


__all__ = [
    "DAST10_LOW_UPPER",
    "DAST10_MODERATE_UPPER",
    "DAST10_NONE_UPPER",
    "DAST10_SUBSTANTIAL_UPPER",
    "DAST10_TOTAL_MAX",
    "DAST10_TOTAL_MIN",
    "INSTRUMENT_VERSION",
    "ITEM_COUNT",
    "ITEM_MAX",
    "ITEM_MIN",
    "REVERSE_SCORED_ITEMS_1INDEXED",
    "Band",
    "Dast10Result",
    "InvalidResponseError",
    "score_dast10",
]

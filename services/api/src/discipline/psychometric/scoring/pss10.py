"""PSS-10 — Perceived Stress Scale (Cohen 1983 / 1988).

The 10-item Perceived Stress Scale measures the degree to which
situations in the past month are appraised as stressful, uncontrollable
and overloading.  It is the most widely used psychological instrument
for measuring perception of stress.

Items (verbatim Cohen 1988 wording — "In the last month, how often
have you ..."):

1. ...been upset because of something that happened unexpectedly?
2. ...felt that you were unable to control the important things in
   your life?
3. ...felt nervous and "stressed"?
4. ...felt confident about your ability to handle your personal
   problems?                                              [POSITIVE]
5. ...felt that things were going your way?               [POSITIVE]
6. ...found that you could not cope with all the things that you
   had to do?
7. ...been able to control irritations in your life?      [POSITIVE]
8. ...felt that you were on top of things?                [POSITIVE]
9. ...been angered because of things that were outside of your
   control?
10. ...felt difficulties were piling up so high that you could not
    overcome them?

Response scale (Cohen 1983):
    0 = Never
    1 = Almost never
    2 = Sometimes
    3 = Fairly often
    4 = Very often

Scoring:
- Items 4, 5, 7, 8 are positively worded — they must be **reverse-
  scored** before summation (0↔4, 1↔3, 2 unchanged).  A patient who
  reports high coping ("4: very often felt confident") would otherwise
  inflate the stress score; the reverse keeps the high-stress
  direction monotonic across all 10 items.
- After reversal, sum the 10 items.  Total range 0-40.

Severity bands (commonly used cutoffs; documented in the PSS-10
psychometric literature including State of New Hampshire DHHS and
Mind Garden distributor guidance):
- 0-13:  low perceived stress
- 14-26: moderate perceived stress
- 27-40: high perceived stress

These bands are descriptive, not diagnostic — PSS-10 is NOT a
clinical screen for any specific disorder.  We expose the band so
trajectory tracking can flag *change*; treatment decisions are made
from the change, not the raw level.

The instrument has no safety items — there is no "T3 trigger" path
in the PSS-10 result.

Reference:
- Cohen S, Kamarck T, Mermelstein R (1983). *A global measure of
  perceived stress.* J Health Soc Behav 24(4):385-396.
- Cohen S, Williamson G (1988). *Perceived stress in a probability
  sample of the United States.* In Spacapan & Oskamp (eds.), The
  Social Psychology of Health.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

INSTRUMENT_VERSION = "pss10-1.0.0"
ITEM_COUNT = 10
ITEM_MIN = 0
ITEM_MAX = 4

# 1-indexed item numbers that are positively worded and therefore
# reverse-scored.  Pinned here as a frozenset so a refactor cannot
# silently drop or add an item — the membership is part of the
# instrument's identity.
REVERSE_SCORED_ITEMS_1INDEXED: frozenset[int] = frozenset({4, 5, 7, 8})

# Severity-band cutoffs.  ``low`` is total <= 13; ``moderate`` is
# 14-26 inclusive; ``high`` is total >= 27.  Documented in the PSS-10
# literature; see module docstring.
PSS10_LOW_UPPER = 13
PSS10_MODERATE_UPPER = 26
PSS10_TOTAL_MIN = 0
PSS10_TOTAL_MAX = 40

Band = Literal["low", "moderate", "high"]


class InvalidResponseError(ValueError):
    """Raised on item-count, item-range, or item-type violations."""


@dataclass(frozen=True)
class Pss10Result:
    """Typed PSS-10 output.

    Fields:
    - ``total``: sum after reverse-scoring (0-40).  This is the
      published total — clients display this, not ``raw_items_sum``.
    - ``band``: ``low`` / ``moderate`` / ``high`` per the documented
      cutoffs.
    - ``raw_items``: the verbatim caller input, pre-reversal.  Pinned
      in the result so an auditor can verify the reversal was applied
      correctly without re-running the scorer.
    - ``scored_items``: post-reversal item values, in 1-10 order.
      Useful for FHIR export where each item is a separate Observation
      component and consumers want the *scored* value, not the raw
      response.
    """

    total: int
    band: Band
    raw_items: tuple[int, ...]
    scored_items: tuple[int, ...]
    instrument_version: str = INSTRUMENT_VERSION


def _reverse(value: int) -> int:
    """Invert a 0-4 response to its complement (0↔4, 1↔3, 2↔2).

    Implemented as ``ITEM_MAX - value`` rather than a lookup table
    so a future change to the response scale (e.g. a 0-5 variant)
    requires only changing ``ITEM_MAX`` — keeps the dependency on
    the scale explicit."""
    return ITEM_MAX - value


def _classify(total: int) -> Band:
    """Map total → severity band.  Precedence is by inclusive
    ranges, not first-match — re-ordering the ``if`` chain would
    not change the band assignment, but the explicit cutoffs make
    the boundaries readable."""
    if total <= PSS10_LOW_UPPER:
        return "low"
    if total <= PSS10_MODERATE_UPPER:
        return "moderate"
    return "high"


def score_pss10(raw_items: Sequence[int]) -> Pss10Result:
    """Score a PSS-10 response set.

    Inputs are the 10 integer item responses (range 0-4) in the
    published item order (1-10).  Items 4, 5, 7, 8 are reverse-scored
    inside the function; callers pass the raw response value.

    Raises :class:`InvalidResponseError` on:
    - Wrong number of items (must be exactly 10).
    - An item value outside [0, 4].
    - A non-int item value (bools coerce to 0/1 implicitly via
      ``isinstance(bool, int)`` but we reject them explicitly because
      a boolean response to a 0-4 scale is almost certainly a wire-
      format bug, not intent).

    Partial scoring is never acceptable — the band would be
    misclassified if even one item is missing.
    """
    if len(raw_items) != ITEM_COUNT:
        raise InvalidResponseError(
            f"PSS-10 requires exactly {ITEM_COUNT} items, got {len(raw_items)}"
        )

    raw_list: list[int] = []
    for index, value in enumerate(raw_items, start=1):
        # ``bool`` is an ``int`` subclass — reject it before the int
        # check so True/False don't silently become 1/0 on a 0-4 scale.
        if isinstance(value, bool) or not isinstance(value, int):
            raise InvalidResponseError(
                f"PSS-10 item {index} must be int in [{ITEM_MIN}, {ITEM_MAX}], "
                f"got {value!r}"
            )
        if value < ITEM_MIN or value > ITEM_MAX:
            raise InvalidResponseError(
                f"PSS-10 item {index} out of range "
                f"[{ITEM_MIN}, {ITEM_MAX}]: {value}"
            )
        raw_list.append(value)

    scored_list = [
        _reverse(v) if (i + 1) in REVERSE_SCORED_ITEMS_1INDEXED else v
        for i, v in enumerate(raw_list)
    ]
    total = sum(scored_list)
    band = _classify(total)

    return Pss10Result(
        total=total,
        band=band,
        raw_items=tuple(raw_list),
        scored_items=tuple(scored_list),
    )


__all__ = [
    "INSTRUMENT_VERSION",
    "ITEM_COUNT",
    "ITEM_MAX",
    "ITEM_MIN",
    "PSS10_LOW_UPPER",
    "PSS10_MODERATE_UPPER",
    "PSS10_TOTAL_MAX",
    "PSS10_TOTAL_MIN",
    "REVERSE_SCORED_ITEMS_1INDEXED",
    "Band",
    "InvalidResponseError",
    "Pss10Result",
    "score_pss10",
]

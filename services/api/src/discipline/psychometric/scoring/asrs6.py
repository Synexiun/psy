"""ASRS-v1.1 Screener (Kessler 2005) — 6-item WHO Adult ADHD
Self-Report Scale short screener.

The ASRS-v1.1 Screener is the World Health Organization's brief
adult-ADHD screen, derived from the full 18-item ASRS-v1.1 by
selecting the six items with the strongest predictive value for
DSM-IV adult ADHD diagnosis (Kessler 2005 §4).  Widely adopted in
primary care and behavioral health because it runs in under a minute
and produces a single categorical decision that maps to "consistent
with ADHD / further evaluation warranted" vs "not consistent".

Clinical relevance to the Discipline OS platform:
Adult ADHD is a significant behavioral health construct that
co-occurs with the existing instrument coverage — PHQ-9 depression,
GAD-7 anxiety, BIS-11 impulsivity, AUDIT-C / DUDIT / SDS substance
use — at rates well above base (Kessler 2006, Wilens 2013).  A
patient with an undetected adult-ADHD diagnosis presenting as
co-occurring distress / substance use is a common missed-diagnosis
pattern in primary care; the ASRS-6 screen surfaces the construct
without committing to a diagnostic workup.  The ASRS is NOT a
diagnostic instrument — a positive screen is a "worth evaluating
further" signal, not a diagnosis.

Instrument structure (Kessler 2005, "In the past 6 months, how
often have you..."):

**6 items, each on a 0-4 Likert scale:**
    0 = Never
    1 = Rarely
    2 = Sometimes
    3 = Often
    4 = Very Often

The six items (Kessler 2005 Figure 1):
 1. How often do you have trouble wrapping up the final details of
    a project once the challenging parts have been done?
 2. How often do you have difficulty getting things in order when
    you have to do a task that requires organization?
 3. How often do you have problems remembering appointments or
    obligations?
 4. When you have a task that requires a lot of thought, how often
    do you avoid or delay getting started?
 5. How often do you fidget or squirm with your hands or feet when
    you have to sit down for a long time?
 6. How often do you feel overly active and compelled to do things,
    like you were driven by a motor?

**Novel weighted-threshold scoring (Kessler 2005, Figure 1):**

Each item "fires" at a different Likert threshold depending on its
discriminative point per the logistic-regression weights published
in Kessler 2005:

| Items | Fires when response ≥ |
| ----- | --------------------- |
| 1, 2, 3 (inattentive) | 2 ("Sometimes") |
| 4, 5, 6 (hyperactive/impulsive) | 3 ("Often") |

The screen decision is a **count of fired items**, not a sum of
responses:

- Count of fired items ≥ 4 → **positive screen** (consistent with
  adult-ADHD symptoms, sensitivity 0.69, specificity 0.99 vs
  clinician-rated DSM-IV diagnosis per Kessler 2005 Table 2)
- Count of fired items ≤ 3 → negative screen

This is a distinct wire envelope shape from the sum-vs-cutoff
pattern used by every other instrument in this package: two items
at response 4 plus four items at response 1 produces a total of 12
(impressive on a sum-threshold instrument) but only one firing item
(count=1, clearly negative).  A caller using ``total`` to interpret
ADHD symptom burden would under-detect in exactly the pattern the
weighted-threshold is designed to catch.  The scorer exposes both
``total`` (for trajectory tracking) and ``positive_count`` (for the
screen decision) so trajectory and screen semantics stay separate.

Cutoff envelope choice:
Cutoff envelope (positive_screen / negative_screen) uniform with
PHQ-2 / GAD-2 / OASIS / PC-PTSD-5 / AUDIT-C / SDS / K6 / DUDIT.
Kessler 2005 did not publish banded severity thresholds for the
6-item screener — the full 18-item ASRS-v1.1 Symptom Checklist
supports continuous symptom-count tracking but the 6-item screener
is published as a binary decision gate only.  Per CLAUDE.md's
"don't hand-roll severity thresholds" rule, severity banding is
refused.

Triggering-items surfacing:
The 1-indexed item numbers that fired their per-item threshold are
exposed on the wire via ``triggering_items``, reusing the existing
C-SSRS pattern.  A clinician-UI renders these as "these items met
their threshold" so a patient can see WHICH symptoms contributed to
the screen decision, not just the aggregate count.  Empty tuple
when no items fire.

Safety routing:
ASRS-6 has **no direct safety item**.  Items 5 (fidget) and 6
(driven by a motor) probe hyperactivity — NOT suicidality or
acute-harm intent.  ``requires_t3`` is never set by this scorer —
acute ideation screening is PHQ-9 item 9 / C-SSRS, not ASRS.  Same
posture as the rest of the no-safety-item instrument set.

Subscale posture:
The inattentive (items 1-3) vs hyperactive/impulsive (items 4-6)
factor split is implicit in the thresholds (≥2 vs ≥3) but is NOT
surfaced as a wire-exposed subscale.  Kessler 2005 validates the
screener at the unidimensional "count of fires" level, not at the
subscale level.  Clinicians needing the symptom-dimension split
should administer the full 18-item ASRS-v1.1 Symptom Checklist,
not back-calculate from the 6-item screener.

Bool rejection note:
Uniform with the rest of the psychometric package — bool items are
rejected at the validator.  See mdq.py, pcptsd5.py, isi.py, pcl5.py,
ocir.py, bis11.py, phq2.py, gad2.py, oasis.py, k10.py, sds.py, k6.py,
dudit.py for the shared rationale.

References:
- Kessler RC, Adler L, Ames M, Demler O, Faraone S, Hiripi E, Howes
  MJ, Jin R, Secnik K, Spencer T, Ustun TB, Walters EE (2005).  *The
  World Health Organization Adult ADHD Self-Report Scale (ASRS): a
  short screening scale for use in the general population.*
  Psychological Medicine 35(2):245-256.
- Kessler RC, Adler L, Barkley R, Biederman J, Conners CK, Demler O,
  et al. (2006).  *The prevalence and correlates of adult ADHD in
  the United States: results from the National Comorbidity Survey
  Replication.*  American Journal of Psychiatry 163(4):716-723.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

INSTRUMENT_VERSION = "asrs6-1.0.0"
ITEM_COUNT = 6
ITEM_MIN = 0
ITEM_MAX = 4

# Per-item firing thresholds per Kessler 2005 Figure 1.  Pinned as a
# module-level dict so a change is a clinical sign-off, not a tweak.
# Keys are 1-indexed item numbers; values are the minimum Likert
# response at which the item "fires".
#
# Inattentive items (1-3) fire at "Sometimes" or greater (≥ 2).
# Hyperactive/impulsive items (4-6) fire at "Often" or greater (≥ 3).
# The asymmetry is from Kessler 2005's item-response-theory weights —
# hyperactive symptoms at "Sometimes" frequency are base-rate common
# in the general population and would produce a false-positive
# flood if they fired at the same threshold as inattentive items.
ITEM_THRESHOLDS: dict[int, int] = {
    1: 2,
    2: 2,
    3: 2,
    4: 3,
    5: 3,
    6: 3,
}

# Count-of-fired-items cutoff (Kessler 2005).  ≥ 4 of 6 fired items
# signals probable adult ADHD symptoms (sensitivity 0.69, specificity
# 0.99 vs DSM-IV clinician-rated diagnosis).
ASRS6_POSITIVE_CUTOFF = 4


class InvalidResponseError(ValueError):
    """Raised on item-count, item-range, or item-type violations."""


@dataclass(frozen=True)
class Asrs6Result:
    """Typed ASRS-6 output.

    Fields:
    - ``total``: 0-24, the raw Likert sum.  Useful for week-over-week
      trajectory tracking independently of the screen decision.  A
      caller MUST NOT use ``total`` to interpret the screen — a sum
      of 12 can occur with only one fired item.  Use
      ``positive_count`` / ``positive_screen`` for the screen
      decision.
    - ``positive_count``: 0-6, the count of items that met their
      per-item firing threshold.  The actual screen input.
    - ``positive_screen``: ``positive_count >= ASRS6_POSITIVE_CUTOFF``.
      The actionable flag.
    - ``triggering_items``: 1-indexed item numbers that fired.
      Surfaced on the wire via the existing ``triggering_items``
      slot (reusing the C-SSRS precedent).  Empty tuple when no
      items fire.
    - ``items``: verbatim input echo.

    Safety posture: ``requires_t3`` is deliberately absent.  ASRS-6
    has no safety item.  See module docstring.
    """

    total: int
    positive_count: int
    positive_screen: bool
    triggering_items: tuple[int, ...]
    items: tuple[int, ...]
    instrument_version: str = INSTRUMENT_VERSION


def _validate_item(index_1: int, value: object) -> int:
    """Validate a single ASRS-6 Likert item and return the int value.

    ``index_1`` is the 1-indexed item number (1-6) so error messages
    name the item a clinician would recognize.
    """
    # Bool rejection — uniform with the rest of the psychometric package.
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidResponseError(
            f"ASRS-6 item {index_1} must be int, got {value!r}"
        )
    if value < ITEM_MIN or value > ITEM_MAX:
        raise InvalidResponseError(
            f"ASRS-6 item {index_1} out of range "
            f"[{ITEM_MIN}, {ITEM_MAX}]: {value}"
        )
    return value


def score_asrs6(raw_items: Sequence[int]) -> Asrs6Result:
    """Score an ASRS-6 response set using the Kessler 2005 weighted-
    threshold rule.

    Inputs:
    - ``raw_items``: 6 items, each 0-4 Likert (0 = "Never",
      4 = "Very Often").

    Raises :class:`InvalidResponseError` on:
    - Wrong number of items.
    - A non-int / bool item value.
    - An item outside ``[0, 4]``.

    Computes:
    - ``total``: raw Likert sum (0-24).
    - Per-item "fire" decision using ``ITEM_THRESHOLDS`` — items 1-3
      fire at ≥ 2, items 4-6 fire at ≥ 3.
    - ``positive_count``: number of fired items (0-6).
    - ``positive_screen``: ``positive_count >= 4``.
    - ``triggering_items``: 1-indexed numbers of fired items.
    """
    if len(raw_items) != ITEM_COUNT:
        raise InvalidResponseError(
            f"ASRS-6 requires exactly {ITEM_COUNT} items, got {len(raw_items)}"
        )
    items = tuple(
        _validate_item(index_1=i + 1, value=v)
        for i, v in enumerate(raw_items)
    )
    total = sum(items)
    triggering = tuple(
        i + 1
        for i, v in enumerate(items)
        if v >= ITEM_THRESHOLDS[i + 1]
    )
    positive_count = len(triggering)
    return Asrs6Result(
        total=total,
        positive_count=positive_count,
        positive_screen=positive_count >= ASRS6_POSITIVE_CUTOFF,
        triggering_items=triggering,
        items=items,
    )


__all__ = [
    "ASRS6_POSITIVE_CUTOFF",
    "Asrs6Result",
    "INSTRUMENT_VERSION",
    "ITEM_COUNT",
    "ITEM_MAX",
    "ITEM_MIN",
    "ITEM_THRESHOLDS",
    "InvalidResponseError",
    "score_asrs6",
]

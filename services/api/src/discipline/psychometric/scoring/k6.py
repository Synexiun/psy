"""K6 — Kessler Psychological Distress Scale, 6-item short form
(Kessler, Barker, Colpe, Epstein, Gfroerer, Hiripi, Howes, Normand,
Manderscheid, Walters, Zaslavsky 2003).

The K6 is a 6-item short form of the K10 (Kessler 2002), developed for
use in large population surveys where the 10-item form is too long.
Per Kessler 2003 Table 1 the K6 items are the *same six items* that
carried the highest loadings on the Kessler 2002 dominant factor —
items covering nervousness, hopelessness, restlessness, depressed
mood, effortful fatigue, and worthlessness.

Clinical relevance to the Discipline OS platform:
K6 fills the daily-EMA / short-sample slot in the cross-cutting-
distress pillar, mirroring the PHQ-9 → PHQ-2 and GAD-7 → GAD-2
companion pattern.  Per Docs/Technicals/12_Psychometric_System.md the
full K10 administers quarterly / baseline; a daily or weekly K6
offers the same distress construct at a patient burden low enough
for an EMA (6 items × ~5s = ~30s on a phone).  The National Survey
on Drug Use and Health (NSDUH) has used K6 since 2008 as its core
mental-health screener, making it the reference short-form distress
measure in U.S. epidemiology.

Instrument structure (Kessler 2003, "In the past 30 days, about
how often did you feel..."):

**6 items, each on a 1-5 Likert scale** — identical coding to K10:
    1 = None of the time
    2 = A little of the time
    3 = Some of the time
    4 = Most of the time
    5 = All of the time

The six items (Kessler 2003 Table 1):
 1. Nervous.
 2. Hopeless.
 3. Restless or fidgety.
 4. So depressed that nothing could cheer you up.
 5. That everything was an effort.
 6. Worthless.

Range: 6-30 total (every item scores ≥ 1, not 0).  ITEM_MIN = 1 —
same load-bearing invariant as K10.  The published Kessler 2003
cutoff is calibrated against the 1-5 coding; a client that submits
0-indexed items would shift totals by 6 and collapse a positive SMI
screen into a negative one.

Positive-screen cutoff (Kessler 2003):

| Total  | Screen            | Population % (NSDUH) |
| ------ | ----------------- | -------------------- |
| 6-12   | Negative screen   | ~97%                 |
| 13-30  | Positive (SMI)    | ~3%                  |

**Cutoff ≥ 13 signals probable serious mental illness (SMI)** —
Kessler 2003's validated cutoff against the 12-month DSM-IV SMI
criterion (AUC 0.87, sensitivity 0.36, specificity 0.96 at the
general-population prevalence).  This is the cutoff adopted by
NSDUH, the WHO World Mental Health Survey Initiative, and the
downstream literature.  Changing it is a clinical change, not an
implementation tweak.

No severity bands:
Unlike K10 (Andrews & Slade 2001 published low / moderate / high /
very_high bands on the 10-50 total), K6 is canonically reported as a
*binary* cutoff screen — Kessler 2003 published only the ≥13 SMI gate.
Some downstream studies have back-calculated K10-style bands onto
K6 totals but those are secondary derivatives, not Kessler's
primary validation.  The router maps K6 onto the cutoff envelope
(severity = "positive_screen" / "negative_screen") uniform with
PHQ-2 / GAD-2 / OASIS / PC-PTSD-5 / AUDIT-C / SDS — *not* the
banded envelope K10 uses.  This is the clinically defensible wire
shape: if a patient needs banded-severity distress tracking, the
right answer is K10, not K6 with invented bands.

Reference-scale note:
A K6 is a *distress* screen, not a diagnostic signal.  A positive
K6 (≥13) says the patient has distress at population-percentile
≈ 97, which is an action signal (work up with K10 + PHQ-9 + GAD-7
+ C-SSRS as indicated), not a diagnosis.  Same clinical posture
as K10.

Subscale note:
Kessler 2003 validated K6 as unidimensional (by design — the six
items were selected for their loading on the K10 dominant factor).
No subscales are wire-exposed.

Safety routing:
K6 has **no direct safety item**.  Items 2 (hopeless), 4 (so
depressed nothing could cheer you up), and 6 (worthless) probe
negative-mood / hopelessness dimensions that may *covary* with
suicidality, but none of the 6 items asks about suicidal thoughts,
plans, or intent.  ``requires_t3`` is never set by this scorer —
acute suicidality screening is the job of PHQ-9 item 9 / C-SSRS,
not K6.  Same posture as K10.

Bool rejection note:
Uniform with the rest of the psychometric package — bool items are
rejected at the validator.  See mdq.py, pcptsd5.py, isi.py, pcl5.py,
ocir.py, bis11.py, phq2.py, gad2.py, oasis.py, k10.py, sds.py for
the shared rationale.

References:
- Kessler RC, Barker PR, Colpe LJ, Epstein JF, Gfroerer JC, Hiripi E,
  Howes MJ, Normand SL, Manderscheid RW, Walters EE, Zaslavsky AM
  (2003).  *Screening for serious mental illness in the general
  population.*  Archives of General Psychiatry 60(2):184-189.
- Kessler RC, Andrews G, Colpe LJ, Hiripi E, Mroczek DK, Normand SL,
  Walters EE, Zaslavsky AM (2002).  *Short screening scales to
  monitor population prevalences and trends in non-specific
  psychological distress.*  Psychological Medicine 32(6):959-976.
- Furukawa TA, Kessler RC, Slade T, Andrews G (2003).  *The
  performance of the K6 and K10 screening scales for psychological
  distress in the Australian National Survey of Mental Health and
  Well-Being.*  Psychological Medicine 33(2):357-362.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

INSTRUMENT_VERSION = "k6-1.0.0"
ITEM_COUNT = 6
ITEM_MIN = 1
ITEM_MAX = 5

# Kessler 2003 SMI cutoff.  Pinned as a module constant so any change
# forces a clinical sign-off rather than slipping through as a tweak.
# Sources for the cutoff value and its calibration are cited in the
# module docstring.
K6_POSITIVE_CUTOFF = 13


class InvalidResponseError(ValueError):
    """Raised on item-count, item-range, or item-type violations."""


@dataclass(frozen=True)
class K6Result:
    """Typed K6 output.

    Fields:
    - ``total``: 6-30, the straight sum of the 6 Likert items.
      Minimum 6 because every item's lowest response value is 1
      ("none of the time"), not 0.  This is the field that flows
      into the FHIR Observation's ``valueInteger`` and into the
      trajectory layer.
    - ``positive_screen``: ``total >= K6_POSITIVE_CUTOFF``
      (≥ 13 per Kessler 2003).  The actionable SMI-screen flag.
    - ``items``: verbatim input tuple, pinned for auditability.

    Safety posture: ``requires_t3`` is deliberately absent from this
    dataclass.  K6 has no safety item.  See module docstring.
    """

    total: int
    positive_screen: bool
    items: tuple[int, ...]
    instrument_version: str = INSTRUMENT_VERSION


def _validate_item(index_1: int, value: object) -> int:
    """Validate a single 1-5 Likert item and return the int value.

    ``index_1`` is the 1-indexed item number (1-6) so error messages
    name the item a clinician would recognize from the K6 document.
    """
    # Bool rejection — uniform with the rest of the psychometric package.
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidResponseError(
            f"K6 item {index_1} must be int, got {value!r}"
        )
    if value < ITEM_MIN or value > ITEM_MAX:
        raise InvalidResponseError(
            f"K6 item {index_1} out of range "
            f"[{ITEM_MIN}, {ITEM_MAX}]: {value}"
        )
    return value


def score_k6(raw_items: Sequence[int]) -> K6Result:
    """Score a K6 response set and assign the Kessler 2003 SMI screen.

    Inputs:
    - ``raw_items``: 6 items, each 1-5 Likert (1 = "None of the
      time", 5 = "All of the time"), same coding as K10.

    Raises :class:`InvalidResponseError` on:
    - Wrong number of items.
    - A non-int / bool item value.
    - An item outside ``[1, 5]``.

    Computes:
    - Total score (6-30).
    - Positive screen when ``total >= 13`` (Kessler 2003 SMI gate).
    """
    if len(raw_items) != ITEM_COUNT:
        raise InvalidResponseError(
            f"K6 requires exactly {ITEM_COUNT} items, got {len(raw_items)}"
        )
    items = tuple(
        _validate_item(index_1=i + 1, value=v)
        for i, v in enumerate(raw_items)
    )
    total = sum(items)

    return K6Result(
        total=total,
        positive_screen=total >= K6_POSITIVE_CUTOFF,
        items=items,
    )


__all__ = [
    "INSTRUMENT_VERSION",
    "InvalidResponseError",
    "ITEM_COUNT",
    "ITEM_MAX",
    "ITEM_MIN",
    "K6_POSITIVE_CUTOFF",
    "K6Result",
    "score_k6",
]

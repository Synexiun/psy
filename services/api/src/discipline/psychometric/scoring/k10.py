"""K10 — Kessler Psychological Distress Scale, 10-item form
(Kessler, Andrews, Colpe, Hiripi, Mroczek, Normand, Walters, Zaslavsky
2002).

The K10 is a 10-item general psychological distress screener designed
for population mental-health surveys and primary-care triage.  Unlike
PHQ-9 (depression-specific) or GAD-7 (anxiety-specific), the K10
measures a single cross-cutting distress construct — the instrument's
items span depressive (hopeless / worthless / sad), anxiety (nervous /
restless), and arousal (tired / effort) symptoms, and Kessler 2002
deliberately validated a *unidimensional* total score.  A K10 result
reads as "how much general psychological distress does this person
carry, regardless of diagnostic category?"

Clinical relevance to the Discipline OS platform:
On the Discipline OS clinical tiers K10 fills a distinct slot from
the depression / anxiety / trauma pillar: it catches distress whose
driver is still being worked up, and it is the standard instrument
for population-level severity banding (Andrews & Slade 2001's bands
are the canonical reference for Australia's National Survey of
Mental Health and Wellbeing and for a large downstream evidence
base).  Per Docs/Technicals/12_Psychometric_System.md, K10 occupies
the quarterly / baseline general-distress slot: administered at
enrollment + every 90 days to track the coarse "are you worse /
same / better?" signal independent of per-construct work (PHQ-9
monthly, GAD-7 monthly, etc.).

Instrument structure (Kessler 2002, "In the past 4 weeks, about
how often did you feel..."):

**10 items, each on a 1-5 Likert scale** scored:
    1 = None of the time
    2 = A little of the time
    3 = Some of the time
    4 = Most of the time
    5 = All of the time

Note: items are **1-indexed on the Likert**, not 0-indexed.  This is
Kessler's original coding; the published Andrews & Slade 2001 bands
are calibrated against the 1-5 scale yielding a total range of 10-50.
Some later adaptations rescaled items to 0-4 (total 0-40) for
semantic ease but that breaks comparability with the published bands
and is not used here.  The scorer's ``ITEM_MIN = 1`` constant is the
first ITEM_MIN != 0 in the package; it is load-bearing for band
interpretation and must not be rescaled without citing a replacement
paper.

The ten items:
 1. Tired out for no good reason.
 2. Nervous.
 3. So nervous that nothing could calm you down.
 4. Hopeless.
 5. Restless or fidgety.
 6. So restless you could not sit still.
 7. Depressed.
 8. That everything was an effort.
 9. So sad that nothing could cheer you up.
10. Worthless.

Range: 10-50 total (every item scores ≥ 1, even "none of the time").

Severity bands (Andrews & Slade 2001):

| Total | Band          | Population % |
| ----- | ------------- | ------------ |
| 10-19 | Low           | ~67%         |
| 20-24 | Moderate      | ~20%         |
| 25-29 | High          | ~10%         |
| 30-50 | Very high     | ~3%          |

Andrews & Slade 2001 is the canonical banding reference — their bands
are endorsed by the Australian Bureau of Statistics, the WHO World
Mental Health Survey Initiative, and the downstream literature
(Furukawa 2003, Kessler 2003).  Changing the bands is a clinical
change, not an implementation tweak, and must cite a replacement paper.

Reference-scale note:
Unlike PHQ-9 / GAD-7 whose bands have explicit diagnostic
interpretation ("moderate depression" = DSM-5 depressive episode
probable), K10 bands are *distress severity* bands — not a
diagnostic signal.  A "very high" K10 says the patient has
distress at population-percentile ≈ 97, which is an action signal
(full work-up), not a diagnosis.

Subscale note:
Kessler 2002 factor-analyzed K10 and reported a dominant single
factor; some downstream literature has reported a 2-factor
(depression vs. anxiety) split but this has not been validated for
clinical use.  The scorer exposes only the total — no subscales
wire-exposed.  Attempting to split items into depression / anxiety
subscales would produce unvalidated scores.

Safety routing:
K10 has **no direct safety item**.  Item 4 (hopeless), item 9 (so
sad that nothing could cheer you up), and item 10 (worthless) probe
negative-mood / hopelessness dimensions that may *covary* with
suicidality, but none of the 10 items asks about suicidal thoughts,
plans, or intent.  ``requires_t3`` is never set by this scorer —
acute suicidality screening is the job of PHQ-9 item 9 / C-SSRS,
not K10.  A patient with a "very high" K10 (score 30+) and active
suicidality needs a co-administered C-SSRS; that is a separate
instrument submission per the Safety Framework.  Clinical posture:
a "very high" K10 is a strong signal to *work the patient up with
safety-gated instruments*, not an excuse to skip them.

Bool rejection note:
Uniform with the rest of the psychometric package — bool items are
rejected at the validator.  See mdq.py, pcptsd5.py, isi.py, pcl5.py,
ocir.py, bis11.py, phq2.py, gad2.py, oasis.py for the shared
rationale.

References:
- Kessler RC, Andrews G, Colpe LJ, Hiripi E, Mroczek DK, Normand SL,
  Walters EE, Zaslavsky AM (2002).  *Short screening scales to
  monitor population prevalences and trends in non-specific
  psychological distress.*  Psychological Medicine 32(6):959-976.
- Andrews G, Slade T (2001).  *Interpreting scores on the Kessler
  Psychological Distress Scale (K10).*  Australian and New Zealand
  Journal of Public Health 25(6):494-497.
- Furukawa TA, Kessler RC, Slade T, Andrews G (2003).  *The
  performance of the K6 and K10 screening scales for psychological
  distress in the Australian National Survey of Mental Health and
  Well-Being.*  Psychological Medicine 33(2):357-362.
- Kessler RC, Barker PR, Colpe LJ, Epstein JF, Gfroerer JC, Hiripi E,
  Howes MJ, Normand SL, Manderscheid RW, Walters EE, Zaslavsky AM
  (2003).  *Screening for serious mental illness in the general
  population.*  Archives of General Psychiatry 60(2):184-189.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence

INSTRUMENT_VERSION = "k10-1.0.0"
ITEM_COUNT = 10
ITEM_MIN = 1
ITEM_MAX = 5

# Published bands per Andrews & Slade 2001: cut-points at 20 / 25 / 30
# over a total range of 10-50.  Exposed as a module constant so the
# trajectory layer and the clinician UI render the same band edges
# with no drift.  Changing these is a clinical change, not an
# implementation tweak.
K10_SEVERITY_THRESHOLDS: tuple[tuple[int, str], ...] = (
    (30, "very_high"),
    (25, "high"),
    (20, "moderate"),
    (10, "low"),
)

Severity = Literal["low", "moderate", "high", "very_high"]


class InvalidResponseError(ValueError):
    """Raised on item-count, item-range, or item-type violations."""


@dataclass(frozen=True)
class K10Result:
    """Typed K10 output.

    Fields:
    - ``total``: 10-50, the straight sum of the 10 Likert items.
      Minimum 10 because every item's lowest response value is 1
      ("none of the time"), not 0.  This is the field that flows
      into the FHIR Observation's ``valueInteger`` and into the
      trajectory layer.
    - ``severity``: one of ``"low" | "moderate" | "high" | "very_high"``
      per Andrews & Slade 2001.  Flipping this alone (e.g. a reviewer
      override) is NOT supported — the result is immutable; re-score
      to change.
    - ``items``: verbatim input tuple, pinned for auditability.

    Safety posture: ``requires_t3`` is deliberately absent from this
    dataclass.  K10 has no safety item.  See module docstring.
    """

    total: int
    severity: Severity
    items: tuple[int, ...]
    instrument_version: str = INSTRUMENT_VERSION


def _validate_item(index_1: int, value: object) -> int:
    """Validate a single 1-5 Likert item and return the int value.

    ``index_1`` is the 1-indexed item number (1-10) so error messages
    name the item a clinician would recognize from the K10 document.
    """
    # Bool rejection — uniform with the rest of the psychometric package.
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidResponseError(
            f"K10 item {index_1} must be int, got {value!r}"
        )
    if value < ITEM_MIN or value > ITEM_MAX:
        raise InvalidResponseError(
            f"K10 item {index_1} out of range "
            f"[{ITEM_MIN}, {ITEM_MAX}]: {value}"
        )
    return value


def _band_for_total(total: int) -> Severity:
    """Map a K10 total to its Andrews & Slade 2001 severity band.

    The thresholds tuple is ordered descending so the first match
    wins; this makes the band-at-cutoff semantics explicit (total=30
    is "very_high", not "high")."""
    for threshold, band in K10_SEVERITY_THRESHOLDS:
        if total >= threshold:
            return band  # type: ignore[return-value]
    # Unreachable — minimum possible total is 10 (ITEM_MIN=1 × 10 items),
    # which is >= the lowest threshold.  Guard anyway so mypy is happy.
    raise InvalidResponseError(
        f"K10 total {total} below minimum 10 — validator bug"
    )


def score_k10(raw_items: Sequence[int]) -> K10Result:
    """Score a K10 response set and assign the Andrews & Slade 2001
    severity band.

    Inputs:
    - ``raw_items``: 10 items, each 1-5 Likert (1 = "None of the
      time", 5 = "All of the time").

    Raises :class:`InvalidResponseError` on:
    - Wrong number of items.
    - A non-int / bool item value.
    - An item outside ``[1, 5]``.

    Computes:
    - Total score (10-50).
    - Severity band via Andrews & Slade 2001 thresholds
      (10-19 low / 20-24 moderate / 25-29 high / 30-50 very_high).
    """
    if len(raw_items) != ITEM_COUNT:
        raise InvalidResponseError(
            f"K10 requires exactly {ITEM_COUNT} items, got {len(raw_items)}"
        )
    items = tuple(
        _validate_item(index_1=i + 1, value=v)
        for i, v in enumerate(raw_items)
    )
    total = sum(items)
    severity = _band_for_total(total)

    return K10Result(
        total=total,
        severity=severity,
        items=items,
    )


__all__ = [
    "INSTRUMENT_VERSION",
    "InvalidResponseError",
    "ITEM_COUNT",
    "ITEM_MAX",
    "ITEM_MIN",
    "K10_SEVERITY_THRESHOLDS",
    "K10Result",
    "Severity",
    "score_k10",
]

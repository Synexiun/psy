"""PHQ-2 — Patient Health Questionnaire-2 ultra-short depression screener
(Kroenke, Spitzer, Williams 2003).

The PHQ-2 is the 2-item ultra-short depression screener composed of
PHQ-9 items 1 (anhedonia — "little interest or pleasure in doing
things") and 2 (depressed mood — "feeling down, depressed, or
hopeless").  It is the canonical *pre-screener* in Kroenke's two-stage
approach: a patient who screens positive on PHQ-2 progresses to the
full PHQ-9 for severity banding and item-9 safety evaluation; a
negative PHQ-2 skips PHQ-9 administration entirely.  The instrument
is NOT a diagnostic tool and it is NOT a severity measure — it is a
binary decision gate ("administer the full PHQ-9? yes/no") tuned to
maximize sensitivity for any depressive disorder.

Clinical relevance to the Discipline OS platform:
The product collects psychometrics on weekly, daily, and per-episode
cadences.  Per Docs/Technicals/12_Psychometric_System.md, PHQ-9 is
appropriate for weekly severity tracking but is friction-heavy for
daily check-ins — 9 items plus an item-9 safety evaluation prompt is
too much on an EMA surface.  PHQ-2 is the daily-EMA partner:
  - 2 items (~15 seconds to administer),
  - no item-9 — so no in-line safety-routing interrupt on the daily
    check-in surface (acute ideation stays gated by C-SSRS and the
    weekly PHQ-9),
  - cutoff-only ("are symptoms rising enough to surface full PHQ-9
    this week?") rather than severity-banded.
A patient whose daily PHQ-2 crosses the positive cutoff across two
consecutive checks is surfaced to the clinician workflow with a
"promote to PHQ-9 this week" recommendation — the 2-item instrument
is the triage gate, the 9-item instrument is the severity measure.

Instrument structure (Kroenke 2003):

**2 items, each on a 0-3 Likert scale** — identical wording to PHQ-9
items 1 and 2, asked "Over the last 2 weeks, how often have you been
bothered by..." scored:
    0 = Not at all
    1 = Several days
    2 = More than half the days
    3 = Nearly every day

The two items:
 1. Little interest or pleasure in doing things.
 2. Feeling down, depressed, or hopeless.

Range: 0-6 total.

Positive-screen cutoff (Kroenke 2003):
A score of ``>= 3`` is the published cutoff, with sensitivity 0.83
and specificity 0.92 for *any* depressive disorder and sensitivity
0.87 / specificity 0.78 for *major depression* specifically in the
primary-care validation sample.  Kroenke 2003 selected cutpoint 3
as the best balance between sensitivity and specificity across
clinical targets; lower cutpoints (2) were considered but rejected
for over-firing on sub-clinical low-mood days.  Changing the cutoff
is a clinical change, not an implementation tweak.

Reference-scale note:
Unlike PHQ-9's five-band severity scale (none / mild / moderate /
moderately_severe / severe), PHQ-2 publishes NO severity bands.
Kroenke 2003 is explicit about this: the 2-item short form is a
binary decision gate, and the clinical literature has been uniform
in the 20+ years since in NOT endorsing any PHQ-2 severity bands.
Attempting to back-calculate bands from the PHQ-9 thresholds (e.g.
"PHQ-2 total × 4.5 ≈ PHQ-9 total, so map bands that way") produces
clinically invalid categorizations — the two items carry only ~22%
of PHQ-9's variance and do not capture anhedonia/sleep/concentration/
psychomotor dimensions.  The router renders PHQ-2 on the cutoff-
only wire envelope (severity = positive_screen / negative_screen),
uniform with PC-PTSD-5 / MDQ / AUDIT-C — not the banded envelope
used by PHQ-9 itself.

Safety routing:
PHQ-2 has **no direct safety item** — item 9 of PHQ-9 (suicidality)
is deliberately excluded from the 2-item short form.  ``requires_t3``
is never set by this scorer.  Clinical posture: a patient who needs
daily depression check-ins AND is at risk for acute ideation should
be on PHQ-9 (the full form with in-line safety evaluation) OR the
C-SSRS daily EMA variant — PHQ-2 is the wrong instrument for that
patient regardless of the numeric score.  The instrument-choice
decision is itself clinical, not an implementation shortcut.

Bool rejection note:
Uniform with the rest of the psychometric package — bool items are
rejected at the validator.  Rationale: keep the wire contract uniform
across every instrument so a front-end that strictly types item
values as `number` does not accidentally send `true`/`false` and
produce a silent 1/0 coercion.  See mdq.py, pcptsd5.py, isi.py,
pcl5.py, ocir.py, bis11.py for the shared rationale.

References:
- Kroenke K, Spitzer RL, Williams JB (2003).  *The Patient Health
  Questionnaire-2: Validity of a Two-Item Depression Screener.*
  Medical Care 41(11):1284-1292.
- Löwe B, Kroenke K, Gräfe K (2005).  *Detecting and monitoring
  depression with a two-item questionnaire (PHQ-2).*  Journal of
  Psychosomatic Research 58(2):163-171.
- Arroll B, Goodyear-Smith F, Crengle S, Gunn J, Kerse N, Fishman T,
  Falloon K, Hatcher S (2010).  *Validation of PHQ-2 and PHQ-9 to
  screen for major depression in the primary care population.*
  Annals of Family Medicine 8(4):348-353.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence

INSTRUMENT_VERSION = "phq2-1.0.0"
ITEM_COUNT = 2
ITEM_MIN = 0
ITEM_MAX = 3

# Published cutoff per Kroenke 2003 §Results: "a PHQ-2 score of 3 had
# a sensitivity of 83% and a specificity of 92% for any depressive
# disorder".  Exposed as a module constant so the trajectory layer
# and the clinician UI render the same threshold value with no drift.
# Changing this is a clinical change, not an implementation tweak.
PHQ2_POSITIVE_CUTOFF = 3


Screen = Literal["positive_screen", "negative_screen"]


class InvalidResponseError(ValueError):
    """Raised on item-count, item-range, or item-type violations."""


@dataclass(frozen=True)
class Phq2Result:
    """Typed PHQ-2 output.

    Fields:
    - ``total``: 0-6, the straight sum of the 2 Likert items.  This is
      the field that flows into the FHIR Observation's ``valueInteger``.
    - ``positive_screen``: True iff ``total >= 3`` per Kroenke 2003.
      Flipping this alone (e.g. a reviewer override) is NOT supported
      — the result is immutable; re-score to change.
    - ``items``: verbatim input tuple, pinned for auditability.

    Safety posture: ``requires_t3`` is deliberately absent from this
    dataclass.  PHQ-2 excludes PHQ-9 item 9 by design — a patient on
    PHQ-2 who needs acute-ideation gating should be on PHQ-9 or
    C-SSRS instead.  See module docstring.
    """

    total: int
    positive_screen: bool
    items: tuple[int, ...]
    instrument_version: str = INSTRUMENT_VERSION


def _validate_item(index_1: int, value: object) -> int:
    """Validate a single 0-3 Likert item and return the int value.

    ``index_1`` is the 1-indexed item number (1 or 2) so error messages
    name the item a clinician would recognize from the PHQ-2 document.
    """
    # Bool rejection — uniform with the rest of the psychometric package.
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidResponseError(
            f"PHQ-2 item {index_1} must be int, got {value!r}"
        )
    if value < ITEM_MIN or value > ITEM_MAX:
        raise InvalidResponseError(
            f"PHQ-2 item {index_1} out of range "
            f"[{ITEM_MIN}, {ITEM_MAX}]: {value}"
        )
    return value


def score_phq2(raw_items: Sequence[int]) -> Phq2Result:
    """Score a PHQ-2 response set and apply the ``>= 3`` positive-screen
    cutoff per Kroenke 2003.

    Inputs:
    - ``raw_items``: 2 items, each 0-3 Likert severity.

    Raises :class:`InvalidResponseError` on:
    - Wrong number of items.
    - A non-int / bool item value.
    - An item outside ``[0, 3]``.

    Computes:
    - Total score (0-6).
    - Probable-depression ``positive_screen`` via the ``>= 3`` cutoff.
    """
    if len(raw_items) != ITEM_COUNT:
        raise InvalidResponseError(
            f"PHQ-2 requires exactly {ITEM_COUNT} items, got {len(raw_items)}"
        )
    items = tuple(
        _validate_item(index_1=i + 1, value=v)
        for i, v in enumerate(raw_items)
    )
    total = sum(items)
    positive_screen = total >= PHQ2_POSITIVE_CUTOFF

    return Phq2Result(
        total=total,
        positive_screen=positive_screen,
        items=items,
    )


__all__ = [
    "INSTRUMENT_VERSION",
    "InvalidResponseError",
    "ITEM_COUNT",
    "ITEM_MAX",
    "ITEM_MIN",
    "PHQ2_POSITIVE_CUTOFF",
    "Phq2Result",
    "Screen",
    "score_phq2",
]

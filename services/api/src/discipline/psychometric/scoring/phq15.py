"""PHQ-15 — Patient Health Questionnaire, Somatic Symptom Scale
(Kroenke, Spitzer, Williams 2002).

The PHQ-15 is a 15-item self-report scale for somatic symptom severity
over the past four weeks.  It is the somatic-symptom member of the
PHQ family (PHQ-9 / GAD-7 / PHQ-15) and was introduced in Kroenke 2002
as the scoring complement to PHQ-9 for primary-care screening of
functional somatic syndromes and treatment response in
anxiety/depression comorbid with somatization.

Clinical relevance to the Discipline OS platform:
Somatization is a well-documented precursor and maintenance factor
for compulsive behavior cycles.  Per
Docs/Whitepapers/02_Clinical_Evidence_Base.md §compulsive, patients
whose anxiety and dysphoria present predominantly as bodily
complaints (tension headache, GI distress, fatigue) frequently use
substance use, compulsive behavior, or rigid ritual as
interoceptive-regulation strategies.  A rising PHQ-15 without a
parallel rise in PHQ-9 / GAD-7 is the clinical signature of
"affect → body → behavior" pathways that respond to interoceptive
exposure and somatic-awareness interventions rather than standard
cognitive restructuring.  Surfacing PHQ-15 alongside PHQ-9 lets the
platform differentiate cognitive-rumination-dominant vs
somatization-dominant presentations and route to the correct
intervention track.

Instrument structure (Kroenke 2002):

**15 items, each on a 0-2 Likert scale**.  Note the 0-2 range vs.
the 0-3 range of PHQ-9 and 0-4 of GAD-7 / ISI — Kroenke 2002 chose a
tighter scale because bothered-at-all is the clinically meaningful
step for somatic symptoms (the "a little vs a lot" granularity maps
cleanly to the 0/1/2 levels):
    0 = Not bothered at all
    1 = Bothered a little
    2 = Bothered a lot

Instruction prompt is "During the past 4 weeks, how much have you
been bothered by any of the following problems?" — item wording
is verbatim from Kroenke 2002 Appendix:

 1. Stomach pain
 2. Back pain
 3. Pain in your arms, legs, or joints (knees, hips, etc.)
 4. Menstrual cramps or other problems with your periods
    (women only; men code as 0)
 5. Headaches
 6. Chest pain
 7. Dizziness
 8. Fainting spells
 9. Feeling your heart pound or race
10. Shortness of breath
11. Pain or problems during sexual intercourse
12. Constipation, loose bowels, or diarrhea
13. Nausea, gas, or indigestion
14. Feeling tired or having low energy
15. Trouble sleeping

Sex handling (item 4):
PHQ-15 item 4 is sex-specific — it asks about menstrual problems.
Kroenke 2002 convention is:
- Women respond to all 15 items.
- Men code item 4 as 0 ("Not bothered at all") and the 15-item total
  (maximum 30) is interpreted against the same published cutoffs.
The scorer does NOT take a sex parameter — it expects 15 pre-coded
items.  The clinician-UI / mobile-UI layer hides item 4 for men and
submits 0 for that index.  This keeps the scorer pure (no demographic
state) and matches how AUDIT-C's sex-aware cutoff is lifted out of the
scorer into the router dispatch.

Scoring (Kroenke 2002):
- Straight sum of the 15 items (no reverse-coding, unlike PSS-10).
  All items are worded so 0 = "not bothered" and 2 = "bothered a lot".
- Total range: 0-30.

Severity bands (Kroenke 2002 §Results; replicated in Kroenke 2010
PHQ-SADS review):
    0-4:   minimal somatic symptoms
    5-9:   low somatic symptoms
    10-14: medium somatic symptoms
    15-30: high somatic symptoms

These are the Kroenke 2002 published thresholds and are pinned here
as a module constant so the trajectory layer and the clinician UI
render the same severity values.  Changing them is a clinical change,
not an implementation tweak.

Safety routing:
PHQ-15 has **no direct safety item** — item 6 (chest pain) and item 8
(fainting spells) are medical-urgency markers in some triage contexts
but are NOT crisis-routing signals in the platform's T3 sense (T3 is
reserved for active suicidality per
Docs/Whitepapers/04_Safety_Framework.md §T3).  A severe PHQ-15 with
chest pain is a medical-evaluation routing signal that the clinician-
UI layer surfaces separately; it is not the same signal as PHQ-9
item 9 positive.  ``requires_t3`` is deliberately absent from this
result.  A patient with a positive PHQ-15 AND acute suicidality
needs a co-administered PHQ-9 / C-SSRS submission to fire T3.

Bool rejection note:
Uniform with the rest of the psychometric package — bool items
are rejected at the validator.  See isi.py, mdq.py, pcptsd5.py,
pcl5.py, ocir.py for the shared rationale.

References:
- Kroenke K, Spitzer RL, Williams JBW (2002).  *The PHQ-15: validity
  of a new measure for evaluating the severity of somatic symptoms.*
  Psychosomatic Medicine 64(2):258-266.
- Kroenke K, Spitzer RL, Williams JBW, Löwe B (2010).  *The Patient
  Health Questionnaire Somatic, Anxiety, and Depressive Symptom
  Scales: a systematic review.*  General Hospital Psychiatry
  32(4):345-359.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence

INSTRUMENT_VERSION = "phq15-1.0.0"
ITEM_COUNT = 15
ITEM_MIN = 0
ITEM_MAX = 2

# Published severity bands per Kroenke 2002 §Results.  Tuple-of-tuples
# so the classify step is explicit about the upper boundary of each
# band — a fence-post mistake here (``<`` vs ``<=``) would mis-
# classify the boundary patients, which is precisely where clinical
# decision-making (medium → high → referral for somatic-dominant
# work-up) concentrates.
PHQ15_SEVERITY_THRESHOLDS: tuple[tuple[int, str], ...] = (
    (4, "minimal"),
    (9, "low"),
    (14, "medium"),
    (30, "high"),
)


Severity = Literal["minimal", "low", "medium", "high"]


class InvalidResponseError(ValueError):
    """Raised on item-count, item-range, or item-type violations."""


@dataclass(frozen=True)
class Phq15Result:
    """Typed PHQ-15 output.

    Fields:
    - ``total``: 0-30, straight sum of the 15 items.  Flows into the
      FHIR Observation's ``valueInteger``.  PHQ-15's LOINC panel
      scores it as an ascending severity sum.
    - ``severity``: one of the four Kroenke 2002 bands
      (minimal/low/medium/high).  Immutable — re-score to change.
    - ``items``: verbatim input tuple, pinned for auditability.

    Safety posture: ``requires_t3`` is deliberately absent.  PHQ-15
    has no suicidality item; item 6 (chest pain) and item 8 (fainting)
    are medical-evaluation signals surfaced separately by the
    clinician-UI layer, not T3 crisis triggers.  A patient with
    positive PHQ-15 AND acute suicidality needs a co-administered
    PHQ-9 / C-SSRS submission to fire T3.
    """

    total: int
    severity: Severity
    items: tuple[int, ...]
    instrument_version: str = INSTRUMENT_VERSION


def _classify(total: int) -> Severity:
    """Map a 0-30 total to a Kroenke 2002 severity band.

    The thresholds tuple is in ascending upper-bound order, so the
    first match is the band.  An out-of-range total would fall past
    every threshold — that condition is a scorer bug and raises
    InvalidResponseError rather than returning a nonsense band.
    """
    for upper, label in PHQ15_SEVERITY_THRESHOLDS:
        if total <= upper:
            return label  # type: ignore[return-value]
    raise InvalidResponseError(f"PHQ-15 total out of range: {total}")


def _validate_item(index_1: int, value: object) -> int:
    """Validate a single 0-2 Likert item and return the int value.

    ``index_1`` is the 1-indexed item number (1-15) so error messages
    name the item a clinician would recognize from the instrument
    document.
    """
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidResponseError(
            f"PHQ-15 item {index_1} must be int, got {value!r}"
        )
    if value < ITEM_MIN or value > ITEM_MAX:
        raise InvalidResponseError(
            f"PHQ-15 item {index_1} out of range "
            f"[{ITEM_MIN}, {ITEM_MAX}]: {value}"
        )
    return value


def score_phq15(raw_items: Sequence[int]) -> Phq15Result:
    """Score a PHQ-15 response set and apply the Kroenke 2002 severity
    bands.

    Inputs:
    - ``raw_items``: 15 items, each 0-2 Likert severity.  For male
      respondents, item 4 should be supplied as 0 (per Kroenke 2002
      convention) — the scorer does not inspect sex; upstream UI
      submits the sex-normalized 15-tuple.

    Raises :class:`InvalidResponseError` on:
    - Wrong number of items.
    - A non-int / bool item value.
    - An item outside ``[0, 2]``.
    """
    if len(raw_items) != ITEM_COUNT:
        raise InvalidResponseError(
            f"PHQ-15 requires exactly {ITEM_COUNT} items, got {len(raw_items)}"
        )
    items = tuple(
        _validate_item(index_1=i + 1, value=v)
        for i, v in enumerate(raw_items)
    )
    total = sum(items)

    return Phq15Result(
        total=total,
        severity=_classify(total),
        items=items,
    )


__all__ = [
    "INSTRUMENT_VERSION",
    "InvalidResponseError",
    "ITEM_COUNT",
    "ITEM_MAX",
    "ITEM_MIN",
    "PHQ15_SEVERITY_THRESHOLDS",
    "Phq15Result",
    "Severity",
    "score_phq15",
]

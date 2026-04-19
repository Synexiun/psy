"""OASIS — Overall Anxiety Severity And Impairment Scale
(Norman, Cissell, Means-Christensen, Stein 2006).

The OASIS is a 5-item brief measure of anxiety severity AND functional
impairment — the distinguishing feature vs. GAD-7 (which indexes
symptom severity only) and GAD-2 (a binary screen).  Where GAD-7
answers "how severe is the symptom burden?", OASIS answers the
adjacent clinical question "how much is anxiety costing the patient
in day-to-day life?" — a patient may screen sub-threshold on GAD-7
yet endorse substantial avoidance / work / social impairment on OASIS.

Clinical relevance to the Discipline OS platform:
Anxiety's treatment-response signal is impairment-weighted, not
symptom-count weighted: a patient whose worry drops from "constant"
to "frequent" may look flat on GAD-7 while OASIS' avoidance +
work/social items capture the real functional improvement.  Per
Docs/Technicals/12_Psychometric_System.md, OASIS occupies the
anxiety-impairment slot in the weekly / biweekly tier, paired with
GAD-7 when a clinician wants both the symptom and impairment views.
For relapse-prevention surfaces, the avoidance item (item 3) is
itself a first-order relapse-driver signal — avoidance of reminders,
places, or situations is a classic precursor to compensatory
behavioral engagement.

Instrument structure (Norman 2006, "In the past week..."):

**5 items, each on a 0-4 Likert scale** scored:
    0 = None / Not at all
    1 = Infrequent / Mild
    2 = Occasional / Moderate
    3 = Frequent / Severe
    4 = Constant / Extreme

The five items:
 1. How often have you felt anxious?  (symptom frequency)
 2. When you felt anxious, how intense or severe was your anxiety?
    (symptom intensity)
 3. How often did you avoid situations, places, objects, or
    activities because of anxiety or fear?  (avoidance)
 4. How much did your anxiety interfere with your ability to do the
    things you needed to do at work, at school, or at home?
    (work/school/home impairment)
 5. How much has anxiety interfered with your social life and
    relationships?  (social impairment)

Range: 0-20 total.

Positive-screen cutoff (Campbell-Sills 2009):
A score of ``>= 8`` is the published clinical cutoff, validated by
Campbell-Sills, Norman, Craske, Sullivan, Lang, Chavira, Bystritsky,
Sherbourne, Roy-Byrne, Stein (2009) on the CALM primary-care sample
(sensitivity 0.87, specificity 0.66 for any DSM-IV anxiety disorder
diagnosis).  Norman 2006 itself reported construct validity against
the ADIS-IV but left the cut-score to downstream validation;
Campbell-Sills 2009 is the canonical operating-point reference cited
in the GAD literature.  Changing this cutoff is a clinical change,
not an implementation tweak, and must cite a replacement paper.

Reference-scale note:
Like PSS-10 and PC-PTSD-5, OASIS publishes NO severity bands —
Norman 2006 validates the total as a continuous measure of severity/
impairment, and the downstream literature has been uniform in
reporting only the cutoff.  The wire envelope renders OASIS on the
cutoff-only envelope (severity = positive_screen / negative_screen),
uniform with PHQ-2 / GAD-2 / PC-PTSD-5 / MDQ / AUDIT-C — not the
banded envelope used by GAD-7 itself.  The ``total`` field carries
the continuous interpretation for trajectory plotting; the
``positive_screen`` boolean is the binary decision gate.

Subscale note:
OASIS items cover three conceptual dimensions — symptom severity
(items 1-2), avoidance (item 3), and impairment (items 4-5) — but
Norman 2006 validates **only the total score**.  The published
factor analysis showed a single-factor structure; attempts to
subscale-score OASIS on the 3 dimensions produce unvalidated
categorizations and are not supported by the scorer or the wire
envelope.  Router emits ``subscales=None`` — future sprints must not
back-calculate subscales without a replacement paper.

Safety routing:
OASIS has **no direct safety item**.  The 5 items probe frequency /
intensity / avoidance / work impairment / social impairment; none
probe suicidality or acute-harm intent.  ``requires_t3`` is never
set by this scorer.  A patient with a positive OASIS AND active
suicidality needs a co-administered PHQ-9 (for item-9 safety
evaluation) or C-SSRS — that is a separate instrument submission
per the safety framework.  A positive OASIS screen routes to a
clinical follow-up for anxiety assessment (co-administered GAD-7
for symptom severity banding, structured anxiety interview if
indicated), not to a crisis flow.

Bool rejection note:
Uniform with the rest of the psychometric package — bool items are
rejected at the validator.  See mdq.py, pcptsd5.py, isi.py, pcl5.py,
ocir.py, bis11.py, phq2.py, gad2.py for the shared rationale.

References:
- Norman SB, Cissell SH, Means-Christensen AJ, Stein MB (2006).
  *Development and validation of an Overall Anxiety Severity And
  Impairment Scale (OASIS).*  Depression and Anxiety 23(4):245-249.
- Campbell-Sills L, Norman SB, Craske MG, Sullivan G, Lang AJ,
  Chavira DA, Bystritsky A, Sherbourne C, Roy-Byrne P, Stein MB
  (2009).  *Validation of a brief measure of anxiety-related
  severity and impairment: the Overall Anxiety Severity and
  Impairment Scale (OASIS).*  Journal of Affective Disorders
  112(1-3):92-101.
- Bragdon LB, Diefenbach GJ, Hannan S, Tolin DF (2016).
  *Psychometric properties of the Overall Anxiety Severity and
  Impairment Scale (OASIS) among psychiatric outpatients.*  Journal
  of Affective Disorders 201:112-115.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence

INSTRUMENT_VERSION = "oasis-1.0.0"
ITEM_COUNT = 5
ITEM_MIN = 0
ITEM_MAX = 4

# Published cutoff per Campbell-Sills 2009 §Results: "an OASIS score
# of 8 was found to be optimal for detecting the presence of any
# anxiety disorder" (sensitivity 0.87, specificity 0.66).  Exposed as
# a module constant so the trajectory layer and the clinician UI
# render the same threshold value with no drift.  Changing this is a
# clinical change, not an implementation tweak.
OASIS_POSITIVE_CUTOFF = 8


Screen = Literal["positive_screen", "negative_screen"]


class InvalidResponseError(ValueError):
    """Raised on item-count, item-range, or item-type violations."""


@dataclass(frozen=True)
class OasisResult:
    """Typed OASIS output.

    Fields:
    - ``total``: 0-20, the straight sum of the 5 Likert items.  This
      is the field that flows into the FHIR Observation's
      ``valueInteger`` and into the trajectory layer for continuous
      severity tracking.
    - ``positive_screen``: True iff ``total >= 8`` per Campbell-Sills
      2009.  Flipping this alone (e.g. a reviewer override) is NOT
      supported — the result is immutable; re-score to change.
    - ``items``: verbatim input tuple, pinned for auditability.

    Safety posture: ``requires_t3`` is deliberately absent from this
    dataclass.  OASIS has no safety item.  See module docstring.
    """

    total: int
    positive_screen: bool
    items: tuple[int, ...]
    instrument_version: str = INSTRUMENT_VERSION


def _validate_item(index_1: int, value: object) -> int:
    """Validate a single 0-4 Likert item and return the int value.

    ``index_1`` is the 1-indexed item number (1-5) so error messages
    name the item a clinician would recognize from the OASIS document.
    """
    # Bool rejection — uniform with the rest of the psychometric package.
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidResponseError(
            f"OASIS item {index_1} must be int, got {value!r}"
        )
    if value < ITEM_MIN or value > ITEM_MAX:
        raise InvalidResponseError(
            f"OASIS item {index_1} out of range "
            f"[{ITEM_MIN}, {ITEM_MAX}]: {value}"
        )
    return value


def score_oasis(raw_items: Sequence[int]) -> OasisResult:
    """Score an OASIS response set and apply the ``>= 8`` positive-
    screen cutoff per Campbell-Sills 2009.

    Inputs:
    - ``raw_items``: 5 items, each 0-4 Likert severity / frequency.

    Raises :class:`InvalidResponseError` on:
    - Wrong number of items.
    - A non-int / bool item value.
    - An item outside ``[0, 4]``.

    Computes:
    - Total score (0-20).
    - Clinically-significant-anxiety ``positive_screen`` via ``>= 8``.
    """
    if len(raw_items) != ITEM_COUNT:
        raise InvalidResponseError(
            f"OASIS requires exactly {ITEM_COUNT} items, got "
            f"{len(raw_items)}"
        )
    items = tuple(
        _validate_item(index_1=i + 1, value=v)
        for i, v in enumerate(raw_items)
    )
    total = sum(items)
    positive_screen = total >= OASIS_POSITIVE_CUTOFF

    return OasisResult(
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
    "OASIS_POSITIVE_CUTOFF",
    "OasisResult",
    "Screen",
    "score_oasis",
]

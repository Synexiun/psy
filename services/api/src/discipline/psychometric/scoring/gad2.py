"""GAD-2 — Generalized Anxiety Disorder 2-item ultra-short screener
(Kroenke, Spitzer, Williams, Monahan, Löwe 2007).

The GAD-2 is the 2-item ultra-short anxiety screener composed of
GAD-7 items 1 ("feeling nervous, anxious, or on edge") and 2 ("not
being able to stop or control worrying").  It is the canonical
*pre-screener* in Kroenke's two-stage approach for anxiety, mirroring
the PHQ-2 / PHQ-9 relationship for depression: a patient who screens
positive on GAD-2 progresses to the full GAD-7 for severity banding;
a negative GAD-2 skips GAD-7 administration entirely.  The instrument
is NOT a diagnostic tool and it is NOT a severity measure — it is a
binary decision gate ("administer the full GAD-7? yes/no") tuned to
maximize sensitivity for generalized anxiety disorder (GAD) and,
secondarily, for panic / social-anxiety / PTSD presentations.

Clinical relevance to the Discipline OS platform:
GAD-2 is the companion to PHQ-2 on the daily-EMA affective check-in
surface.  PHQ-2 alone covers depression; anxiety is an orthogonal
relapse / distress driver that is clinically expected to be measured
alongside depression on primary-care and EMA surfaces.  Per
Docs/Technicals/12_Psychometric_System.md, the daily-EMA tier bundles
PHQ-2 + GAD-2 (4 items total, ~30 seconds to administer) so a single
daily check-in surfaces both constructs:
  - depressed mood / anhedonia (PHQ-2),
  - nervousness / uncontrolled worry (GAD-2).
When either crosses its positive cutoff across consecutive daily
checks, the clinician workflow recommends promotion to the matching
full instrument (PHQ-9 / GAD-7) that week for severity banding.
Shipping PHQ-2 without GAD-2 would strand the daily-EMA surface with
only half of the affective signal it needs.

Instrument structure (Kroenke 2007):

**2 items, each on a 0-3 Likert scale** — identical wording to GAD-7
items 1 and 2, asked "Over the last 2 weeks, how often have you been
bothered by..." scored:
    0 = Not at all
    1 = Several days
    2 = More than half the days
    3 = Nearly every day

The two items:
 1. Feeling nervous, anxious, or on edge.
 2. Not being able to stop or control worrying.

Range: 0-6 total.

Positive-screen cutoff (Kroenke 2007):
A score of ``>= 3`` is the published cutoff, with sensitivity 0.86
and specificity 0.83 for generalized anxiety disorder in the primary-
care validation sample (Kroenke 2007 §Table 3).  The same cutoff
also performs well (sensitivity 0.76-0.82) for panic disorder,
social anxiety disorder, and PTSD, so GAD-2 functions as a
broad-anxiety screener, not a GAD-specific one.  Kroenke 2007
explicitly recommends cutpoint 3 as the operating point for
primary-care screening; lower cutpoints (2) were considered but
rejected for over-firing on sub-clinical situational worry.
Changing this cutoff is a clinical change, not an implementation
tweak.

Reference-scale note:
Unlike GAD-7's four-band severity scale (none / mild / moderate /
severe), GAD-2 publishes NO severity bands.  Kroenke 2007 is
explicit about this: the 2-item short form is a binary decision
gate, and the downstream literature has been uniform in NOT
endorsing any GAD-2 severity bands.  Attempting to back-calculate
bands from the GAD-7 thresholds (e.g. by ratio) produces clinically
invalid categorizations — the two items carry only a subset of
GAD-7's variance and do not capture restlessness / irritability /
concentration / somatic-tension dimensions.  The router renders
GAD-2 on the cutoff-only wire envelope (severity =
positive_screen / negative_screen), uniform with PHQ-2 /
PC-PTSD-5 / MDQ / AUDIT-C — not the banded envelope used by GAD-7
itself.

Safety routing:
GAD-2 has **no direct safety item** (same as GAD-7, which also has
none).  Anxiety items probe worry / nervousness; none probe
suicidality or acute-harm intent.  ``requires_t3`` is never set by
this scorer.  A patient with a positive GAD-2 AND active
suicidality needs a co-administered PHQ-9 (for item-9 safety
evaluation) or C-SSRS — that is a separate instrument submission
per the safety framework.  Clinical posture: a patient who needs
daily anxiety check-ins AND is at acute risk should be on C-SSRS
(the dedicated suicide-risk instrument) OR the weekly PHQ-9 — the
instrument-choice decision is itself clinical, not an
implementation shortcut.

Bool rejection note:
Uniform with the rest of the psychometric package — bool items
are rejected at the validator.  See mdq.py, pcptsd5.py, isi.py,
pcl5.py, ocir.py, bis11.py, phq2.py for the shared rationale.

References:
- Kroenke K, Spitzer RL, Williams JB, Monahan PO, Löwe B (2007).
  *Anxiety disorders in primary care: prevalence, impairment,
  comorbidity, and detection.*  Annals of Internal Medicine
  146(5):317-325.
- Plummer F, Manea L, Trepel D, McMillan D (2016).  *Screening for
  anxiety disorders with the GAD-7 and GAD-2: a systematic review
  and diagnostic metaanalysis.*  General Hospital Psychiatry
  39:24-31.
- Löwe B, Decker O, Müller S, Brähler E, Schellberg D, Herzog W,
  Herzberg PY (2008).  *Validation and standardization of the
  Generalized Anxiety Disorder Screener (GAD-7) in the general
  population.*  Medical Care 46(3):266-274.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence

INSTRUMENT_VERSION = "gad2-1.0.0"
ITEM_COUNT = 2
ITEM_MIN = 0
ITEM_MAX = 3

# Published cutoff per Kroenke 2007 §Table 3: "A cut point of 3 on
# the GAD-2 had a sensitivity of 86% and a specificity of 83% for
# generalized anxiety disorder".  Exposed as a module constant so
# the trajectory layer and the clinician UI render the same threshold
# value with no drift.  Changing this is a clinical change, not an
# implementation tweak.
GAD2_POSITIVE_CUTOFF = 3


Screen = Literal["positive_screen", "negative_screen"]


class InvalidResponseError(ValueError):
    """Raised on item-count, item-range, or item-type violations."""


@dataclass(frozen=True)
class Gad2Result:
    """Typed GAD-2 output.

    Fields:
    - ``total``: 0-6, the straight sum of the 2 Likert items.  This is
      the field that flows into the FHIR Observation's ``valueInteger``.
    - ``positive_screen``: True iff ``total >= 3`` per Kroenke 2007.
      Flipping this alone (e.g. a reviewer override) is NOT supported
      — the result is immutable; re-score to change.
    - ``items``: verbatim input tuple, pinned for auditability.

    Safety posture: ``requires_t3`` is deliberately absent from this
    dataclass.  GAD-2 has no safety item (GAD-7 itself has none
    either).  See module docstring.
    """

    total: int
    positive_screen: bool
    items: tuple[int, ...]
    instrument_version: str = INSTRUMENT_VERSION


def _validate_item(index_1: int, value: object) -> int:
    """Validate a single 0-3 Likert item and return the int value.

    ``index_1`` is the 1-indexed item number (1 or 2) so error messages
    name the item a clinician would recognize from the GAD-2 document.
    """
    # Bool rejection — uniform with the rest of the psychometric package.
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidResponseError(
            f"GAD-2 item {index_1} must be int, got {value!r}"
        )
    if value < ITEM_MIN or value > ITEM_MAX:
        raise InvalidResponseError(
            f"GAD-2 item {index_1} out of range "
            f"[{ITEM_MIN}, {ITEM_MAX}]: {value}"
        )
    return value


def score_gad2(raw_items: Sequence[int]) -> Gad2Result:
    """Score a GAD-2 response set and apply the ``>= 3`` positive-screen
    cutoff per Kroenke 2007.

    Inputs:
    - ``raw_items``: 2 items, each 0-3 Likert severity.

    Raises :class:`InvalidResponseError` on:
    - Wrong number of items.
    - A non-int / bool item value.
    - An item outside ``[0, 3]``.

    Computes:
    - Total score (0-6).
    - Probable-anxiety ``positive_screen`` via the ``>= 3`` cutoff.
    """
    if len(raw_items) != ITEM_COUNT:
        raise InvalidResponseError(
            f"GAD-2 requires exactly {ITEM_COUNT} items, got {len(raw_items)}"
        )
    items = tuple(
        _validate_item(index_1=i + 1, value=v)
        for i, v in enumerate(raw_items)
    )
    total = sum(items)
    positive_screen = total >= GAD2_POSITIVE_CUTOFF

    return Gad2Result(
        total=total,
        positive_screen=positive_screen,
        items=items,
    )


__all__ = [
    "GAD2_POSITIVE_CUTOFF",
    "INSTRUMENT_VERSION",
    "InvalidResponseError",
    "ITEM_COUNT",
    "ITEM_MAX",
    "ITEM_MIN",
    "Gad2Result",
    "Screen",
    "score_gad2",
]

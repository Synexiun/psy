"""PC-PTSD-5 — Primary Care PTSD Screen for DSM-5 (Prins 2016).

The PC-PTSD-5 is a 5-item yes/no screener for probable PTSD in primary-
care settings, replacing the earlier PC-PTSD-4 with an explicit
DSM-5 alignment.  It is NOT a diagnostic instrument — a positive
screen identifies patients who warrant a structured interview (CAPS-5,
PCL-5 full form), not a PTSD diagnosis.

Clinical relevance to the Discipline OS platform:
Trauma exposure is a first-order relapse driver across substance-use
disorders; per Docs/Whitepapers/02_Clinical_Evidence_Base.md §trauma,
patients with PTSD have ~2-3x higher relapse rates without trauma-
informed care.  Surfacing a PTSD screen lets the clinician route a
patient into trauma-informed treatment before a relapse cascade, not
after.

Instrument structure (Prins 2016, "In the past month, have you...")

**5 binary symptom items (0 = no, 1 = yes)**:
 1. Had nightmares about the event(s) or thought about the event(s)
    when you did not want to?
 2. Tried hard not to think about the event(s) or went out of your
    way to avoid situations that reminded you of the event(s)?
 3. Been constantly on guard, watchful, or easily startled?
 4. Felt numb or detached from people, activities, or your
    surroundings?
 5. Felt guilty or unable to stop blaming yourself or others for the
    event(s) or any problems the event(s) may have caused?

Positive-screen cutoff (Prins 2016):
A score of ≥ 3 positive items is the optimal primary-care cutoff
with sensitivity 0.95 and specificity 0.85 in the VA validation
sample.  Lower cutoffs (≥ 2) were considered in the published work;
≥ 3 was selected as the operating point for best specificity without
sacrificing clinically-meaningful sensitivity.  Changing the cutoff
is a clinical change, not an implementation tweak.

Trauma-exposure precursor:
The validated administration of PC-PTSD-5 begins with a trauma-
exposure gate item ("In your life, have you ever experienced a
traumatic event..."); a negative answer terminates the instrument
with an implicit score of 0.  That gating is an administration
concern, not a scoring concern — if the 5 items are on the wire,
the patient presumably cleared the gate at the UI layer.  A
downstream sprint can add an explicit ``trauma_exposed: bool`` field
if we need to distinguish "no trauma exposure" from "trauma-exposed
but no symptoms" in reporting; the scorer's contract here is the
5-item symptom count, not the gate.

Safety routing:
PC-PTSD-5 has **no direct safety item** — unlike PHQ-9 item 9 or
C-SSRS items 4/5/6, none of the 5 symptoms probe suicidality or
acute crisis state.  ``requires_t3`` is never set by this scorer.
A positive PC-PTSD-5 screen is a referral signal for trauma-
informed care (CAPS-5, PCL-5, EMDR / TF-CBT intake), not a crisis
signal.  A clinician working up a newly-positive screen should
co-administer a C-SSRS if acute suicidality is on the differential;
that is a separate instrument submission.

Bool rejection note:
Python's ``bool`` subclasses ``int`` so ``isinstance(True, int)`` is
True.  Items are 0/1 which overlaps bool's True/False — and unlike
most of the psychometric package, the bool→int conversion here is
*semantically correct* (True is "yes" is 1).  However, we still
reject bools to keep the wire format uniform with the rest of the
package.  The same rationale is documented in mdq.py.

References:
- Prins A, Bovin MJ, Smolenski DJ, Marx BP, Kimerling R, Jenkins-
  Guarnieri MA, Kaloupek DG, Schnurr PP, Kaiser AP, Leyva YE, Tiet QQ
  (2016).  *The Primary Care PTSD Screen for DSM-5 (PC-PTSD-5):
  development and evaluation within a Veteran primary care sample.*
  Journal of General Internal Medicine 31(10):1206-1211.
- Bovin MJ, Kimerling R, Weathers FW, Prins A, Marx BP, Post EP,
  Schnurr PP (2021).  *Diagnostic accuracy and acceptability of the
  Primary Care Posttraumatic Stress Disorder Screen for the Diagnostic
  and Statistical Manual of Mental Disorders (Fifth Edition) among US
  Veterans.*  JAMA Network Open 4(2):e2036733.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence

INSTRUMENT_VERSION = "pcptsd5-1.0.0"
ITEM_COUNT = 5
ITEM_MIN = 0
ITEM_MAX = 1

# Published cutoff per Prins 2016 §Results: "a cutpoint of 3 was
# identified as optimally efficient" (sensitivity 0.95, specificity
# 0.85).  Exposed as a module constant so the trajectory layer + the
# clinician UI render the same threshold value with no drift.
PCPTSD5_POSITIVE_CUTOFF = 3

# Total can equal the cutoff without crossing it — the gate uses ``>=``,
# and the boundary test in the scorer module is named ``...at_cutoff``
# to match.  Pinning the value here keeps the gate logic readable
# (``positive_count >= PCPTSD5_POSITIVE_CUTOFF``) instead of a bare
# magic number at the gate site.


Screen = Literal["positive_screen", "negative_screen"]


class InvalidResponseError(ValueError):
    """Raised on item-count, item-range, or item-type violations."""


@dataclass(frozen=True)
class PcPtsd5Result:
    """Typed PC-PTSD-5 output.

    Fields:
    - ``positive_count``: 0-5, the number of items endorsed ``yes``.
      This is the field to store as the FHIR Observation's
      ``valueInteger`` — the PC-PTSD-5's LOINC panel scores it as a
      count of endorsed items, not a weighted sum.
    - ``positive_screen``: True iff ``positive_count >= 3`` per Prins
      2016.  Flipping this alone (e.g. a reviewer override) is NOT
      supported — the result is immutable; re-score to change.
    - ``items``: verbatim input tuple, pinned for auditability.

    Safety posture: ``requires_t3`` is deliberately absent from this
    dataclass.  Downstream routing code that asks "should this fire
    T3?" for a PC-PTSD-5 record must answer False without consulting
    this result — which is what the router does.  See the module
    docstring for the rationale on why PTSD screens are not a crisis
    signal.
    """

    positive_count: int
    positive_screen: bool
    items: tuple[int, ...]
    instrument_version: str = INSTRUMENT_VERSION


def _validate_item(index_1: int, value: object) -> int:
    """Validate a single yes/no item and return the int value.

    ``index_1`` is the 1-indexed item number (1-5) so error messages
    name the item a clinician would recognize from the instrument
    document.
    """
    # Reject bool explicitly — uniform with the rest of the psychometric
    # package.  See module docstring for the full rationale.
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidResponseError(
            f"PC-PTSD-5 item {index_1} must be int, got {value!r}"
        )
    if value < ITEM_MIN or value > ITEM_MAX:
        raise InvalidResponseError(
            f"PC-PTSD-5 item {index_1} out of range "
            f"[{ITEM_MIN}, {ITEM_MAX}]: {value}"
        )
    return value


def score_pcptsd5(raw_items: Sequence[int]) -> PcPtsd5Result:
    """Score a PC-PTSD-5 response set and apply the ≥ 3 positive-screen
    cutoff per Prins 2016.

    Inputs:
    - ``raw_items``: 5 items, each 0 (no) or 1 (yes).

    Raises :class:`InvalidResponseError` on:
    - Wrong number of items.
    - A non-int / bool item value.
    - An item outside ``[0, 1]``.

    The trauma-exposure precursor gate is handled at the UI
    administration layer, not here — if the caller submitted 5 items,
    the scorer treats the gate as satisfied.  See module docstring.
    """
    if len(raw_items) != ITEM_COUNT:
        raise InvalidResponseError(
            f"PC-PTSD-5 requires exactly {ITEM_COUNT} items, got "
            f"{len(raw_items)}"
        )
    items = tuple(
        _validate_item(index_1=i + 1, value=v)
        for i, v in enumerate(raw_items)
    )
    positive_count = sum(items)
    positive_screen = positive_count >= PCPTSD5_POSITIVE_CUTOFF

    return PcPtsd5Result(
        positive_count=positive_count,
        positive_screen=positive_screen,
        items=items,
    )


__all__ = [
    "INSTRUMENT_VERSION",
    "InvalidResponseError",
    "ITEM_COUNT",
    "ITEM_MAX",
    "ITEM_MIN",
    "PCPTSD5_POSITIVE_CUTOFF",
    "PcPtsd5Result",
    "Screen",
    "score_pcptsd5",
]

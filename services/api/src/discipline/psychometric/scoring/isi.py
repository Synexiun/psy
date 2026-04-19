"""ISI — Insomnia Severity Index (Morin 1993; Bastien 2001).

The Insomnia Severity Index is a 7-item self-report screener for
clinical insomnia and its functional impact over the past two weeks.
Bastien 2001 is the validation paper that anchors the current
operating characteristics (Cronbach α = 0.74; sensitivity 0.942,
specificity 0.764 at a cutoff of 10 in the clinical sample, and at
a cutoff of 15 as a conservative screen for moderate-or-severe
insomnia in community samples — Morin 2011).

Clinical relevance to the Discipline OS platform:
Sleep disruption is a first-order relapse precursor across
substance-use disorders — per Docs/Whitepapers/02_Clinical_Evidence_Base.md
§sleep, patients with moderate-to-severe insomnia have substantially
elevated relapse rates within the first 90 days post-treatment
compared to good-sleep counterparts.  Surfacing an ISI screen lets
the clinician route a patient into CBT-I (cognitive-behavioral
therapy for insomnia) or sleep-medicine referral before the
sleep-disruption → emotional-dysregulation → urge-surge → relapse
cascade has time to compound.

Instrument structure (Bastien 2001; Morin 1993):

**7 items, each on a 0-4 Likert scale**:
 1. Difficulty falling asleep (severity: 0=None → 4=Very severe)
 2. Difficulty staying asleep (severity)
 3. Problems waking up too early (severity)
 4. How SATISFIED/DISSATISFIED are you with your current sleep
    pattern? (0=Very satisfied → 4=Very dissatisfied)
 5. How NOTICEABLE to others do you think your sleep problem is
    in terms of impairing the quality of your life? (0=Not at all
    noticeable → 4=Very much noticeable)
 6. How WORRIED/DISTRESSED are you about your current sleep
    problem? (0=Not at all worried → 4=Very much worried)
 7. To what extent do you consider your sleep problem to
    INTERFERE with your daily functioning (e.g., daytime fatigue,
    mood, ability to function at work/daily chores, concentration,
    memory, etc.) CURRENTLY? (0=Not at all interfering → 4=Very
    much interfering)

Scoring (Bastien 2001):
- Straight sum of the 7 items (no reverse-coding, unlike PSS-10).
  All seven items are worded so that 0 = "no problem" and 4 = "very
  severe problem" — the direction is uniform.  Items 4, 5, 6, and 7
  look conceptually different from 1-3 but the verbiage is chosen so
  the same 0-4 scale maps cleanly to an ascending severity without
  inversion.
- Total range: 0-28.

Severity bands (Bastien 2001 Table 2 / Morin 2011):
    0-7:   no clinically significant insomnia
    8-14:  subthreshold insomnia
    15-21: moderate clinical insomnia
    22-28: severe clinical insomnia

These are the published bands.  The commonly-cited clinical-referral
threshold is ``>= 15`` (moderate or severe) in community samples;
``>= 10`` is a more sensitive cutoff used in some primary-care
contexts.  The scorer surfaces the four-band label verbatim and
leaves the referral decision to the clinician-UI layer — a policy
change to ``>= 10`` would be a UI and analytics change, not a scorer
change.

Safety routing:
ISI has **no direct safety item** — unlike PHQ-9 item 9 or C-SSRS
items 4/5/6, none of the 7 items probes suicidality or acute crisis
state.  ``requires_t3`` is never set by this scorer.  A severe ISI
result is a referral signal for CBT-I / sleep medicine, not a crisis
signal.  A clinician working up a severely-insomniac patient with
depressive or anxiety co-morbidity should co-administer PHQ-9 +
C-SSRS if acute suicidality is on the differential; that is a
separate instrument submission.

Bool rejection note:
Python's ``bool`` subclasses ``int`` so ``isinstance(True, int)`` is
True.  Items are 0-4, so bool's True/False map to 0 and 1 which are
valid item values — a silent coercion would pass validation.  We
still reject bools to keep the wire format uniform with the rest of
the psychometric package.  The same rationale is documented in
mdq.py and pcptsd5.py.

References:
- Morin CM (1993).  *Insomnia: Psychological Assessment and
  Management.*  Guilford Press.
- Bastien CH, Vallières A, Morin CM (2001).  *Validation of the
  Insomnia Severity Index as an outcome measure for insomnia
  research.*  Sleep Medicine 2(4):297-307.
- Morin CM, Belleville G, Bélanger L, Ivers H (2011).  *The Insomnia
  Severity Index: psychometric indicators to detect insomnia cases
  and evaluate treatment response.*  Sleep 34(5):601-608.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence

INSTRUMENT_VERSION = "isi-1.0.0"
ITEM_COUNT = 7
ITEM_MIN = 0
ITEM_MAX = 4

# Published severity bands per Bastien 2001 Table 2 and replicated
# in Morin 2011.  Tuple-of-tuples so the classify step is explicit
# about the upper boundary of each band — a fence-post mistake here
# (e.g. ``<`` vs ``<=``) would mis-classify the boundary patients
# who are precisely where clinical decision-making matters most.
ISI_SEVERITY_THRESHOLDS: tuple[tuple[int, str], ...] = (
    (7, "none"),
    (14, "subthreshold"),
    (21, "moderate"),
    (28, "severe"),
)


Severity = Literal["none", "subthreshold", "moderate", "severe"]


class InvalidResponseError(ValueError):
    """Raised on item-count, item-range, or item-type violations."""


@dataclass(frozen=True)
class IsiResult:
    """Typed ISI output.

    Fields:
    - ``total``: 0-28, straight sum of the 7 items.  This is the
      field to store as the FHIR Observation's ``valueInteger`` —
      ISI's LOINC panel scores it as an ascending severity sum.
    - ``severity``: one of the four Bastien 2001 bands.  Flipping
      this alone (e.g. a reviewer override) is NOT supported — the
      result is immutable; re-score to change.
    - ``items``: verbatim input tuple, pinned for auditability.

    Safety posture: ``requires_t3`` is deliberately absent from this
    dataclass.  Downstream routing code that asks "should this fire
    T3?" for an ISI record must answer False without consulting
    this result — which is what the router does.  See the module
    docstring for the rationale on why ISI is not a crisis signal.
    """

    total: int
    severity: Severity
    items: tuple[int, ...]
    instrument_version: str = INSTRUMENT_VERSION


def _classify(total: int) -> Severity:
    """Map a 0-28 total to a Bastien 2001 severity band.

    The thresholds tuple is in ascending upper-bound order, so the
    first match is the band.  An out-of-range total would fall past
    every threshold — that condition is a scorer bug and raises
    InvalidResponseError rather than returning a nonsense band.
    """
    for upper, label in ISI_SEVERITY_THRESHOLDS:
        if total <= upper:
            return label  # type: ignore[return-value]
    raise InvalidResponseError(f"ISI total out of range: {total}")


def _validate_item(index_1: int, value: object) -> int:
    """Validate a single 0-4 Likert item and return the int value.

    ``index_1`` is the 1-indexed item number (1-7) so error messages
    name the item a clinician would recognize from the instrument
    document.
    """
    # Reject bool explicitly — uniform with the rest of the psychometric
    # package.  See module docstring for the full rationale.
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidResponseError(
            f"ISI item {index_1} must be int, got {value!r}"
        )
    if value < ITEM_MIN or value > ITEM_MAX:
        raise InvalidResponseError(
            f"ISI item {index_1} out of range "
            f"[{ITEM_MIN}, {ITEM_MAX}]: {value}"
        )
    return value


def score_isi(raw_items: Sequence[int]) -> IsiResult:
    """Score an ISI response set and apply the Bastien 2001 severity
    bands.

    Inputs:
    - ``raw_items``: 7 items, each 0-4 Likert severity.

    Raises :class:`InvalidResponseError` on:
    - Wrong number of items.
    - A non-int / bool item value.
    - An item outside ``[0, 4]``.
    """
    if len(raw_items) != ITEM_COUNT:
        raise InvalidResponseError(
            f"ISI requires exactly {ITEM_COUNT} items, got {len(raw_items)}"
        )
    items = tuple(
        _validate_item(index_1=i + 1, value=v)
        for i, v in enumerate(raw_items)
    )
    total = sum(items)

    return IsiResult(
        total=total,
        severity=_classify(total),
        items=items,
    )


__all__ = [
    "INSTRUMENT_VERSION",
    "ISI_SEVERITY_THRESHOLDS",
    "InvalidResponseError",
    "ITEM_COUNT",
    "ITEM_MAX",
    "ITEM_MIN",
    "IsiResult",
    "Severity",
    "score_isi",
]

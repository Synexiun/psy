"""PACS — Penn Alcohol Craving Scale (Flannery, Volpicelli, Pettinati 1999).

The Penn Alcohol Craving Scale is a 5-item self-report instrument
developed at the University of Pennsylvania Addiction Treatment
Research Center to capture the *subjective* craving construct in
alcohol-use-disorder patients.  It was introduced in

    Flannery BA, Volpicelli JR, Pettinati HM (1999).  *Psychometric
    properties of the Penn Alcohol Craving Scale.*  Alcoholism:
    Clinical and Experimental Research 23(8):1289-1295.

as a short, reliable alternative to the longer Obsessive-Compulsive
Drinking Scale (OCDS, Anton 1995) — Flannery 1999 demonstrated
α = 0.92, high test-retest reliability, and strong predictive
validity for relapse in the 12 weeks following detoxification.

Clinical relevance to the Discipline OS platform:
Craving is the **central construct** this product intervenes on.
The entire platform thesis — per
Docs/Whitepapers/01_Methodology.md §urge-to-action and
Docs/Whitepapers/02_Clinical_Evidence_Base.md §craving — rests on
the 60-180 second window between a rising urge and a behavior, and
PACS is the only shipped instrument in the psychometric package
that directly measures that construct.  AUDIT / AUDIT-C / DAST-10
measure consumption and consequences (what already happened);
PACS measures urge (what is about to happen).  A rising weekly
PACS without rising AUDIT is the classic "dry but craving" pattern
that precedes relapse and is precisely the window interoceptive-
exposure and cue-reactivity interventions target.

Instrument structure (Flannery 1999):

**5 items, each on a 0-6 Likert scale** covering the
phenomenological dimensions of craving across the prior week:

 1. **Frequency of craving thoughts** — "How often have you thought
    about drinking or about how good a drink would make you feel?"
    0 = Never, ..., 6 = Nearly all of the time.

 2. **Peak intensity of craving** — "At its most severe point, how
    strong was your urge to drink?"
    0 = None, ..., 6 = Extremely strong.

 3. **Duration of craving** — "How much time have you spent thinking
    about drinking or how good a drink would make you feel?"
    0 = None at all, ..., 6 = Nearly all the time.

 4. **Resistance / self-efficacy** — "How difficult would it have
    been to resist taking a drink if you knew a bottle was in your
    house?"
    0 = Not difficult at all, ..., 6 = Would not be able to resist.

 5. **Overall average craving** — "Please rate your overall average
    alcohol craving for the past week."
    0 = None at all, ..., 6 = Extreme.

Scoring (Flannery 1999):
- Straight sum of the 5 items.  No reverse-coding, no subscale
  partitioning — Flannery 1999 explicitly validates the instrument
  as a single-factor scale.
- Total range: 0-30.

Severity bands — deliberately absent:
Flannery 1999 publishes **no severity thresholds** and there is no
subsequent publication that has produced clinically-validated
cutoffs with consensus uptake.  The clinical literature treats
PACS as a *continuous* outcome measure (trajectory over weeks)
rather than a categorical screen.  Accordingly, this scorer does
NOT emit a severity band, and the router envelope uses
``severity="continuous"`` as a sentinel — the product is
monitoring trajectory, not classifying status.

Fabricating bands here would violate the CLAUDE.md non-negotiable
"Don't hand-roll severity thresholds" rule (which exists because
Kroenke 2001 / Spitzer 2006 / Jacobson & Truax 1991 thresholds
are clinically-validated while hand-rolled ones are
clinician-misleading).  The trajectory layer is where this
instrument's signal is extracted — a week-over-week Δ of +5
points is meaningful regardless of absolute level.

Safety routing:
PACS has no suicidality item and no acute-harm item.  ``requires_t3``
is deliberately absent — craving is the *pre-behavior* signal the
platform intervenes on, not a crisis-escalation marker.  A positive
PACS AND acute suicidality needs a co-administered PHQ-9 / C-SSRS
submission to fire T3, consistent with the PHQ-15 / OCI-R / ISI
safety-posture convention documented in those scorers.

Bool rejection note:
Uniform with the rest of the psychometric package — bool items
are rejected at the validator.  See isi.py, mdq.py, pcptsd5.py,
pcl5.py, ocir.py, phq15.py for the shared rationale.

FHIR / LOINC note:
PACS does **not** have a verified LOINC panel code at the time of
writing.  Per the C-SSRS precedent
(services/api/src/discipline/reports/fhir_observation.py §C-SSRS),
unregistered instruments follow a separate render path rather
than risk emitting an incorrect LOINC.  PACS therefore is NOT
registered in LOINC_CODE or LOINC_DISPLAY; its FHIR export will
use a system-local code when the reports-layer render path is
extended in a later sprint.

References:
- Flannery BA, Volpicelli JR, Pettinati HM (1999).  *Psychometric
  properties of the Penn Alcohol Craving Scale.*  Alcoholism:
  Clinical and Experimental Research 23(8):1289-1295.
- Anton RF, Moak DH, Latham P (1995).  *The Obsessive Compulsive
  Drinking Scale: a self-rated instrument for the quantification
  of thoughts about alcohol and drinking behavior.*  Alcoholism:
  Clinical and Experimental Research 19(1):92-99.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

INSTRUMENT_VERSION = "pacs-1.0.0"
ITEM_COUNT = 5
ITEM_MIN = 0
ITEM_MAX = 6


class InvalidResponseError(ValueError):
    """Raised on item-count, item-range, or item-type violations."""


@dataclass(frozen=True)
class PacsResult:
    """Typed PACS output.

    Fields:
    - ``total``: 0-30, straight sum of the 5 items.  Flows into the
      trajectory layer as the continuous craving signal — the
      clinical decision surface is week-over-week Δ, not absolute.
    - ``items``: verbatim input tuple, pinned for auditability.

    Deliberately-absent fields:
    - No ``severity`` field — Flannery 1999 publishes no bands and
      the literature treats PACS as a continuous measure.  The
      router envelope emits ``severity="continuous"`` as a sentinel.
    - No ``requires_t3`` field — PACS has no suicidality / acute-harm
      item.  Craving is a pre-behavior signal the platform
      intervenes on; it is not a crisis-escalation marker.
    - No subscale fields — Flannery 1999 validates a single-factor
      scale; partitioning into "frequency / intensity / resistance"
      subscales would be a post-hoc construct the authors did not
      endorse.
    """

    total: int
    items: tuple[int, ...]
    instrument_version: str = INSTRUMENT_VERSION


def _validate_item(index_1: int, value: object) -> int:
    """Validate a single 0-6 Likert item and return the int value.

    ``index_1`` is the 1-indexed item number (1-5) so error messages
    name the item a clinician would recognize from the instrument
    document.
    """
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidResponseError(
            f"PACS item {index_1} must be int, got {value!r}"
        )
    if value < ITEM_MIN or value > ITEM_MAX:
        raise InvalidResponseError(
            f"PACS item {index_1} out of range "
            f"[{ITEM_MIN}, {ITEM_MAX}]: {value}"
        )
    return value


def score_pacs(raw_items: Sequence[int]) -> PacsResult:
    """Score a PACS response set.

    Inputs:
    - ``raw_items``: 5 items, each 0-6 Likert (frequency, peak
      intensity, duration, resistance, overall).

    Raises :class:`InvalidResponseError` on:
    - Wrong number of items.
    - A non-int / bool item value.
    - An item outside ``[0, 6]``.

    Returns a :class:`PacsResult` with the total and the pinned
    item tuple.  No severity band is emitted — see module docstring.
    """
    if len(raw_items) != ITEM_COUNT:
        raise InvalidResponseError(
            f"PACS requires exactly {ITEM_COUNT} items, got {len(raw_items)}"
        )
    items = tuple(
        _validate_item(index_1=i + 1, value=v)
        for i, v in enumerate(raw_items)
    )
    total = sum(items)

    return PacsResult(
        total=total,
        items=items,
    )


__all__ = [
    "INSTRUMENT_VERSION",
    "ITEM_COUNT",
    "ITEM_MAX",
    "ITEM_MIN",
    "InvalidResponseError",
    "PacsResult",
    "score_pacs",
]

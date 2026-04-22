"""WSAS — Work and Social Adjustment Scale (Mundt, Marks, Shear,
Greist 2002).

The WSAS is a 5-item self-report measure of **functional
impairment** — how much the patient's presenting problem interferes
with their actual day-to-day life across five canonical life
domains: work/ability to work, home management, social leisure,
private leisure, and ability to form/maintain close relationships.
Where PHQ-9 / GAD-7 / K10 / PCL-5 measure symptom severity and
AAQ-II measures the relationship to internal experience, WSAS
measures the **downstream functional cost** — two patients with
identical PHQ-9 totals can differ sharply on WSAS, and the WSAS
difference is what tells the clinician which one is functionally
closer to baseline recovery.

Clinical relevance to the Discipline OS platform:
WSAS is the canonical functional-impairment outcome measure in the
UK IAPT / stepped-care pathway, where it is administered alongside
PHQ-9 and GAD-7 at every session to track the *functional* arc
independently of symptom change (Clark 2011 IAPT evaluation).  The
platform's reporting layer needs this signal for the P1-P6 narrative
framing: a trajectory where PHQ-9 is improving but WSAS is static
or worsening is a distinct clinical picture ("symptoms are easing
but daily-life functioning has not yet recovered — intervention
should shift toward behavioral activation / committed action")
versus a trajectory where both improve in lockstep ("on the
expected recovery path — keep going").  Without a functional-
impairment measure the platform cannot distinguish these cases,
and the bandit cannot route to behavioral-activation / values-
committed-action tool variants on the evidence of functional
stasis.

Pairing with existing instruments:
WSAS is **orthogonal** to every other measure in the package:

- PHQ-9 / GAD-7 / K10 / K6 / PCL-5 / OCI-R / PHQ-15 measure symptom
  severity (what the patient is experiencing).
- AAQ-II measures experiential avoidance / cognitive fusion (the
  relationship to internal experience).
- BIS-11 measures trait impulsivity.
- URICA / Readiness Ruler measure stage-of-change commitment.
- DTCQ-8 measures coping self-efficacy.
- WSAS measures **functional impairment** — the observable,
  behavioral cost (can the patient work? manage home? sustain
  relationships?).

High symptom severity with low functional impairment and vice versa
both occur and are both clinically informative.  A patient with
PHQ-9=8 (mild) and WSAS=28 (severe) has much larger clinical urgency
than a patient with PHQ-9=8 and WSAS=4 — despite identical
"depression severity."  Neither dimension dominates; both must be
read together.

Instrument structure (Mundt 2002):

**5 items, each on a 0-8 Likert scale** scored:
    0 = Not at all impaired
    2 = Slightly impaired
    4 = Definitely impaired
    6 = Markedly impaired
    8 = Very severely impaired, can't carry on any activities
(odd numbers are intermediate ratings between the anchor labels;
Mundt 2002 designed the 0-8 range deliberately to give patients
more resolution than a 5-point scale — anchor labels are placed at
0/2/4/6/8 with intermediate unanchored points at 1/3/5/7.)

The five items (Mundt 2002, with the stem "Because of my [problem]"):
 1. My ability to work is impaired.  (0 = not at all impaired.)
 2. My home management (cleaning, tidying, shopping, cooking,
    looking after home or children, paying bills) is impaired.
 3. My social leisure activities (with other people, such as
    parties, bars, clubs, outings, visits, dating, home
    entertaining) are impaired.
 4. My private leisure activities (done alone, such as reading,
    gardening, collecting, sewing, walking alone) are impaired.
 5. My ability to form and maintain close relationships with
    others, including those I live with, is impaired.

All items are keyed in the **impairment direction** — higher Likert
= more functional impairment.  There are no reverse-keyed items.
Direction is uniform with PHQ-9 / GAD-7 / K10 / K6 / ISI / PSS-10 /
DAST-10 / PCL-5 / OCI-R / PHQ-15 / BIS-11 / AAQ-II (higher = worse)
and opposite of WHO-5 / Readiness Ruler / DTCQ-8 (higher = better).

Range: total 0-40.

**First 0-8 Likert instrument in the package.**  Prior instruments
use 0-3 (C-SSRS yes/no scaled), 0-4 (PHQ-9 / GAD-7 / DUDIT items
1-9), 0-5 (WHO-5 / PCL-5 / OCI-R), 1-5 (K10 / K6), or 1-7 (AAQ-II).
The widened 0-8 Likert range is the widest per-item resolution in
the package — Mundt 2002 argued the 9-point scale reduces both
ceiling and floor compression and gives sufficient resolution to
detect clinically meaningful change with the Reliable Change Index
(Jacobson & Truax 1991), which is the basis for the platform's
trajectory layer.  The envelope ``ITEM_MIN = 0`` is shared with
every 0-indexed instrument; the ceiling of 8 is novel and the
scorer enforces ``[0, 8]`` at the validator.

Severity bands (Mundt 2002):

| Total  | Band              | Interpretation                      |
| ------ | ----------------- | ----------------------------------- |
| 0-9    | subclinical       | No clinically significant impairment |
| 10-19  | significant       | Significant functional impairment (less severe) |
| 20-40  | severe            | Moderately severe or worse functional impairment |

Mundt 2002 published exactly these three bands.  The cutoff at 20
was derived against SCID-diagnosed depressive-episode patients and
reflects the threshold above which functional restoration (not just
symptom reduction) typically requires active behavioral
intervention.  The cutoff at 10 demarcates subclinical from the
treatment-indicated range.  Per CLAUDE.md's "don't hand-roll
severity thresholds" rule, the scorer ships exactly these three
Mundt 2002 bands — splitting "severe" into "moderate-severe" (20-29)
and "severe" (30-40) is unpublished and is refused.

Envelope choice:
Banded envelope (severity: subclinical / significant / severe) —
uniform with PHQ-9 / GAD-7 / ISI / DAST-10 / PCL-5 / OCI-R / BIS-11 /
PHQ-15 / K10 / DUDIT.  ``cutoff_used`` / ``positive_screen`` are
not set (banded instruments do not surface a single cutoff).

Safety routing:
WSAS has **no direct safety item**.  The five items probe functional
domains (work / home / social / private / relationships), none of
which references suicidality, self-harm intent, or crisis
behavior.  ``requires_t3`` is never set by this scorer — acute
ideation screening is PHQ-9 item 9 / C-SSRS, not WSAS.  Same
posture as the rest of the no-safety-item instrument set.
Clinical posture: a "severe" WSAS (≥20) is a strong signal for
intensive behavioral-activation / committed-action work but is not
itself a crisis gate.

Subscale posture:
Mundt 2002's confirmatory factor analysis supports a
**unidimensional** structure for WSAS — the five life-domain items
load on a single functional-impairment factor.  Although one might
imagine a "productive" (work / home) vs "social" (social leisure /
close relationships) split, Mundt 2002 explicitly rejected it based
on the factor structure.  No subscales are surfaced on the wire.

Bool rejection note:
Uniform with the rest of the psychometric package — bool items are
rejected at the validator.  See mdq.py, pcptsd5.py, isi.py, pcl5.py,
ocir.py, bis11.py, phq2.py, gad2.py, oasis.py, k10.py, sds.py, k6.py,
dudit.py, asrs6.py, aaq2.py for the shared rationale.

References:
- Mundt JC, Marks IM, Shear MK, Greist JM (2002).  *The Work and
  Social Adjustment Scale: A simple measure of impairment in
  functioning.*  British Journal of Psychiatry 180:461-464.
- Clark DM (2011).  *Implementing NICE guidelines for the
  psychological treatment of depression and anxiety disorders: The
  IAPT experience.*  International Review of Psychiatry
  23(4):318-327.
- Jacobson NS, Truax P (1991).  *Clinical significance: A
  statistical approach to defining meaningful change in
  psychotherapy research.*  Journal of Consulting and Clinical
  Psychology 59(1):12-19.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

INSTRUMENT_VERSION = "wsas-1.0.0"
ITEM_COUNT = 5
ITEM_MIN = 0
ITEM_MAX = 8

# Mundt 2002 published bands — cut-points at 10 and 20 over a total
# range of 0-40.  Exposed as a module constant so the trajectory
# layer and clinician UI render the same band edges with no drift.
# Changing these is a clinical change, not an implementation tweak.
WSAS_SEVERITY_THRESHOLDS: tuple[tuple[int, str], ...] = (
    (20, "severe"),
    (10, "significant"),
    (0, "subclinical"),
)

Severity = Literal["subclinical", "significant", "severe"]


class InvalidResponseError(ValueError):
    """Raised on item-count, item-range, or item-type violations."""


@dataclass(frozen=True)
class WsasResult:
    """Typed WSAS output.

    Fields:
    - ``total``: 0-40, the straight sum of the five 0-8 Likert items.
      Direction semantic: higher = more functional impairment (same
      as PHQ-9 / GAD-7 / K10 / AAQ-II, opposite of WHO-5 / DTCQ-8).
    - ``severity``: one of ``"subclinical" | "significant" | "severe"``
      per Mundt 2002.  Flipping this alone (e.g. a reviewer
      override) is NOT supported — the result is immutable; re-score
      to change.
    - ``items``: verbatim input tuple, pinned for auditability.

    Safety posture: ``requires_t3`` is deliberately absent from this
    dataclass.  WSAS has no safety item.  See module docstring.
    """

    total: int
    severity: Severity
    items: tuple[int, ...]
    instrument_version: str = INSTRUMENT_VERSION


def _validate_item(index_1: int, value: object) -> int:
    """Validate a single 0-8 Likert item and return the int value.

    ``index_1`` is the 1-indexed item number (1-5) so error messages
    name the item a clinician would recognize from the WSAS document.

    WSAS uses the 0-8 Mundt 2002 Likert — ``ITEM_MAX = 8`` is novel
    in the package (prior widest was AAQ-II's 1-7).  A response of 9
    is rejected even though other instruments might treat 9 as
    reasonable.
    """
    # Bool rejection — uniform with the rest of the psychometric package.
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidResponseError(
            f"WSAS item {index_1} must be int, got {value!r}"
        )
    if value < ITEM_MIN or value > ITEM_MAX:
        raise InvalidResponseError(
            f"WSAS item {index_1} out of range "
            f"[{ITEM_MIN}, {ITEM_MAX}]: {value}"
        )
    return value


def _band_for_total(total: int) -> Severity:
    """Map a WSAS total to its Mundt 2002 severity band.

    The thresholds tuple is ordered descending so the first match
    wins; this makes the band-at-cutoff semantics explicit (total=20
    is "severe", not "significant"; total=10 is "significant", not
    "subclinical")."""
    for threshold, band in WSAS_SEVERITY_THRESHOLDS:
        if total >= threshold:
            return band  # type: ignore[return-value]
    # Unreachable — minimum possible total is 0, which matches the
    # lowest threshold.  Guard anyway so mypy is happy.
    raise InvalidResponseError(
        f"WSAS total {total} below minimum 0 — validator bug"
    )


def score_wsas(raw_items: Sequence[int]) -> WsasResult:
    """Score a WSAS response set and assign the Mundt 2002 severity band.

    Inputs:
    - ``raw_items``: 5 items, each 0-8 Likert (0 = "Not at all
      impaired", 8 = "Very severely impaired").

    Raises :class:`InvalidResponseError` on:
    - Wrong number of items.
    - A non-int / bool item value.
    - An item outside ``[0, 8]``.

    Computes:
    - Total score (0-40).
    - Severity band via Mundt 2002 thresholds
      (0-9 subclinical / 10-19 significant / 20-40 severe).
    """
    if len(raw_items) != ITEM_COUNT:
        raise InvalidResponseError(
            f"WSAS requires exactly {ITEM_COUNT} items, got {len(raw_items)}"
        )
    items = tuple(
        _validate_item(index_1=i + 1, value=v)
        for i, v in enumerate(raw_items)
    )
    total = sum(items)
    severity = _band_for_total(total)

    return WsasResult(
        total=total,
        severity=severity,
        items=items,
    )


__all__ = [
    "INSTRUMENT_VERSION",
    "ITEM_COUNT",
    "ITEM_MAX",
    "ITEM_MIN",
    "WSAS_SEVERITY_THRESHOLDS",
    "InvalidResponseError",
    "Severity",
    "WsasResult",
    "score_wsas",
]

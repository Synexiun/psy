"""CD-RISC-10 — Connor-Davidson Resilience Scale, 10-item short form
(Campbell-Sills & Stein 2007).

CD-RISC-10 is the validated 10-item short form of the original 25-item
Connor-Davidson Resilience Scale (Connor & Davidson 2003).
Campbell-Sills & Stein 2007 re-analyzed Connor 2003's five-factor
structure, identified cross-loadings and poor-fit items, and derived a
10-item unidimensional scale with superior CFA fit (CFI .95, RMSEA .06
versus the 25-item's multi-factor ambiguity).  It measures **trait
resilience** — the capacity to adapt, recover, and maintain function
in the face of stress, adversity, illness, and trauma.

Clinical relevance to the Discipline OS platform:
Resilience is the product's core construct.  The platform ships a
monotonically-increasing "resilience streak" (see CLAUDE.md Rule #3 —
``streak_state.resilience_days`` is non-decreasing), the recovery-
pathway framing, the relapse-as-data framing, and the compassion-first
messaging tier — all of which presuppose a measurable resilience
dimension at the patient level.  Until now the assessment layer had
no validated resilience measure to ground this.  CD-RISC-10 closes
that gap: it gives the trajectory layer a construct-aligned score the
bandit can read to answer the questions "is the platform's cumulative
intervention arc moving this patient's resilience?", "is resilience
decoupling from symptom severity (PHQ-9 stays flat while CD-RISC-10
rises — the expected recovery signature)?", and "which patients have
below-population resilience at intake and need a heavier scaffold?"

Pairing with existing instruments:
CD-RISC-10 is **construct-level orthogonal** to every symptom measure
and **process-level complementary** to the therapeutic-frame
instruments:

- AAQ-II (ACT target: psychological inflexibility) and DERS-16 (DBT
  target: emotion dysregulation) measure *process impairment*.
- PHQ-9 / GAD-7 / K10 / PCL-5 measure *symptom severity*.
- WSAS measures *functional impairment* (behavioral outcome).
- CD-RISC-10 measures *resilience capacity* (recovery-slope
  underpinning).

The expected therapeutic arc on the platform is the cross-instrument
pattern: process measures fall (inflexibility / dysregulation drop),
symptom measures follow (PHQ-9 / GAD-7 drop), functional measures
recover (WSAS falls), and resilience measures RISE.  CD-RISC-10
instruments the last axis.  The trajectory layer surfaces a
"resilience-decoupling" signal when CD-RISC-10 rises while PHQ-9
stays flat — the early recovery-leading-indicator that precedes
clinical-score change by weeks in the published trajectory literature
(Connor & Davidson 2003 noted resilience-score improvement preceding
clinical improvement in the anxiety-disorder cohort).

Instrument structure (Campbell-Sills & Stein 2007):

**10 items, each on a 0-4 Likert scale** scored:
    0 = not true at all
    1 = rarely true
    2 = sometimes true
    3 = often true
    4 = true nearly all the time

All 10 items are worded in the **resilience direction** — higher
Likert = more resilience.  Campbell-Sills & Stein 2007 pruned the 15
items of the original 25-item CD-RISC that carried cross-loadings or
loaded weakly onto the primary factor; the remaining 10 load cleanly
onto a single resilience construct.  Uniform positively-worded design
means NO reverse-keying (same posture as WHO-5, DTCQ-8, Readiness
Ruler — the other higher-is-better instruments).

The 10 items (Campbell-Sills & Stein 2007 Appendix — item numbers
here are the CD-RISC-10 positions, not the original CD-RISC-25
positions):

 1. Able to adapt to change.
 2. Can deal with whatever comes my way.
 3. Try to see the humorous side of problems.
 4. Having to cope with stress can make me stronger.
 5. Tend to bounce back after illness, injury, or other hardships.
 6. Can achieve my goals despite obstacles.
 7. Under pressure, can focus and think clearly.
 8. Not easily discouraged by failure.
 9. Think of myself as a strong person when dealing with life's
    challenges and difficulties.
10. Can handle unpleasant or painful feelings like sadness, fear,
    and anger.

Range: 0-40.

**Higher is better.**  Uniform with WHO-5 / DTCQ-8 / Readiness Ruler.
Clients rendering CD-RISC-10 scores must not reuse the higher-is-worse
visual language from PHQ-9 / GAD-7 / DERS-16 / PCL-5 / OCI-R / K10 /
WSAS — a falling CD-RISC-10 score is a DETERIORATION, not an
improvement, and the dashboards must encode this directionality
explicitly.

Severity bands — deliberately absent:
Campbell-Sills & Stein 2007 reported general-population means — mean
31.8 ± 5.4 in the U.S. general adult sample (N=764) — but did NOT
publish banded severity thresholds.  Connor & Davidson 2003 reported
cutpoints for the 25-item scale but those do not translate linearly
to the 10-item form; downstream papers that propose 10-item bands
(e.g. low/moderate/high tertiles) are sample-specific and not
cross-calibrated against a shared clinical criterion.  Per CLAUDE.md's
"don't hand-roll severity thresholds" rule, CD-RISC-10 ships as a
**continuous dimensional measure** uniform with Craving VAS / PACS /
DERS-16.  The router envelope emits ``severity="continuous"`` as the
sentinel; the trajectory layer extracts the clinical signal via
RCI-style change detection (Jacobson & Truax 1991) rather than banded
classification.  The platform layer may surface a "below general-
population mean" flag (score < 31) as contextual information on the
clinician UI — that flag is NOT a classification and NOT a gate.

Envelope choice:
Continuous-total shape uniform with PACS / Craving VAS / DERS-16.
``cutoff_used`` / ``positive_screen`` are NOT set.  No ``subscales``
dict — Campbell-Sills & Stein 2007 CFA validates the unidimensional
structure (the 25-item's five-factor structure was explicitly
rejected for the 10-item form).

Safety routing:
CD-RISC-10 has **no direct safety item**.  The 10 items probe
resilience-capacity constructs (adaptability, coping, humor,
post-stress growth, bounce-back, goal persistence, focus under
pressure, failure-tolerance, self-strength, distress-tolerance); none
probe suicidality, self-harm, or crisis behavior.  ``requires_t3`` is
never set — acute ideation screening is PHQ-9 item 9 / C-SSRS, not
CD-RISC-10.  Clinical posture: a low CD-RISC-10 is a strong signal
for longer-horizon scaffolding but is not itself a crisis gate.

Bool rejection note:
Uniform with the rest of the psychometric package — bool items are
rejected at the validator.  See mdq.py, pcptsd5.py, isi.py, pcl5.py,
ocir.py, bis11.py, phq2.py, gad2.py, oasis.py, k10.py, sds.py, k6.py,
dudit.py, asrs6.py, aaq2.py, wsas.py, ders16.py for the shared
rationale.

References:
- Campbell-Sills L, Stein MB (2007).  *Psychometric analysis and
  refinement of the Connor-Davidson Resilience Scale (CD-RISC):
  Validation of a 10-item measure of resilience.*  Journal of
  Traumatic Stress 20(6):1019-1028.
- Connor KM, Davidson JRT (2003).  *Development of a new resilience
  scale: The Connor-Davidson Resilience Scale (CD-RISC).*  Depression
  and Anxiety 18(2):76-82.
- Jacobson NS, Truax P (1991).  *Clinical significance: A statistical
  approach to defining meaningful change in psychotherapy research.*
  Journal of Consulting and Clinical Psychology 59(1):12-19.  (RCI
  framing for continuous-instrument trajectory analysis on the
  platform.)
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

INSTRUMENT_VERSION = "cdrisc10-1.0.0"
ITEM_COUNT = 10
ITEM_MIN = 0
ITEM_MAX = 4


class InvalidResponseError(ValueError):
    """Raised on item-count, item-range, or item-type violations."""


@dataclass(frozen=True)
class Cdrisc10Result:
    """Typed CD-RISC-10 output.

    Fields:
    - ``total``: 0-40, the straight sum of the 10 Likert items.
      Higher is better (more resilience) — opposite directionality
      from PHQ-9 / GAD-7 / DERS-16 / PCL-5 / OCI-R / K10 / WSAS.
      Minimum 0 because every item's lowest response value is 0
      ("not true at all") — same floor semantic as PHQ-9 / GAD-7 /
      OCI-R / AUDIT / DAST-10.
    - ``items``: verbatim input tuple, pinned for auditability.

    Deliberately-absent fields:
    - No ``severity`` field — Campbell-Sills & Stein 2007 published
      no banded thresholds.  The router envelope emits
      ``severity="continuous"`` as a sentinel (uniform with Craving
      VAS / PACS / DERS-16).
    - No ``cutoff_used`` / ``positive_screen`` — continuous
      instrument, no cutoff shape.
    - No ``requires_t3`` field — CD-RISC-10 has no safety item.
    - No ``subscales`` — Campbell-Sills & Stein 2007 CFA validates
      unidimensional structure; the 25-item's five-factor split was
      explicitly rejected for the 10-item form.
    """

    total: int
    items: tuple[int, ...]
    instrument_version: str = INSTRUMENT_VERSION


def _validate_item(index_1: int, value: object) -> int:
    """Validate a single 0-4 Likert item and return the int value.

    ``index_1`` is the 1-indexed item number (1-10) so error messages
    name the item a clinician would recognize from the CD-RISC-10
    document.
    """
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidResponseError(
            f"CD-RISC-10 item {index_1} must be int, got {value!r}"
        )
    if value < ITEM_MIN or value > ITEM_MAX:
        raise InvalidResponseError(
            f"CD-RISC-10 item {index_1} out of range "
            f"[{ITEM_MIN}, {ITEM_MAX}]: {value}"
        )
    return value


def score_cdrisc10(raw_items: Sequence[int]) -> Cdrisc10Result:
    """Score a CD-RISC-10 response set.

    Inputs:
    - ``raw_items``: 10 items, each 0-4 Likert (0 = "not true at all",
      4 = "true nearly all the time").

    Raises :class:`InvalidResponseError` on:
    - Wrong number of items.
    - A non-int / bool item value.
    - An item outside ``[0, 4]``.

    Computes:
    - Total score (0-40) — higher is better (more resilience).

    No severity band is emitted — see module docstring.
    """
    if len(raw_items) != ITEM_COUNT:
        raise InvalidResponseError(
            f"CD-RISC-10 requires exactly {ITEM_COUNT} items, got {len(raw_items)}"
        )
    items = tuple(
        _validate_item(index_1=i + 1, value=v)
        for i, v in enumerate(raw_items)
    )
    total = sum(items)

    return Cdrisc10Result(
        total=total,
        items=items,
    )


__all__ = [
    "INSTRUMENT_VERSION",
    "ITEM_COUNT",
    "ITEM_MAX",
    "ITEM_MIN",
    "Cdrisc10Result",
    "InvalidResponseError",
    "score_cdrisc10",
]

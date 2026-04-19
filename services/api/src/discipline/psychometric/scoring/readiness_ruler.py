"""Readiness Ruler — single-item 0-10 motivation-to-change measure.

The Readiness Ruler is the canonical **motivational-interviewing (MI)**
short assessment: a single integer on a 0-10 line asking "how ready
are you to change [target behavior]?" anchored by "not ready at all"
(0) and "completely ready" (10).  It operationalizes the
transtheoretical-model stages of change (Prochaska & DiClemente 1983)
into a single-item snapshot that can be administered inside a routine
brief intervention.

The Ruler originates with

    Rollnick S, Mason P, Butler C (1999).  *Health Behaviour Change:
    A Guide for Practitioners.*  Churchill Livingstone, London.

as part of the MI toolkit for brief-intervention work, and was
formally validated for the alcohol-brief-intervention setting in

    Heather N, Smailes D, Cassidy P (2008).  *Development of a
    Readiness Ruler for use with alcohol brief interventions.*
    Drug and Alcohol Dependence 98(3):235-240.

Heather 2008 demonstrated that the 0-10 Ruler carries the same
predictive power for downstream behavioral change as the longer
URICA / Stages-of-Change questionnaires, while taking < 10 seconds
to complete — the key ergonomic win for routine EMA administration.

Clinical relevance to the Discipline OS platform:
The Readiness Ruler is the **motivation companion** to the craving
signal.  Where the Craving VAS (Sprint 36) measures the intensity
of the urge, the Ruler measures the strength of the user's intent
to *resist* that urge.  Together they form the two-axis motivation ×
craving frame the intervention layer reads to pick a tool variant:

- **Low craving + high readiness** → maintenance tools (journaling,
  values reflection, social-commitment reinforcement).
- **High craving + high readiness** → effortful-resistance tools
  (urge-surfing, implementation intentions, delay-of-gratification).
- **High craving + low readiness** → motivation-first tools
  (decisional-balance review, change-talk elicitation, MI-scripted
  clinician prompts).
- **Low craving + low readiness** → risk-awareness tools (relapse
  warning-signs review, past-consequence recall).

The cadence per ``Docs/Technicals/12_Psychometric_System.md`` §3.1 is
**weekly** (whereas Craving VAS is EMA).  A weekly Ruler + daily VAS
gives the intervention layer a slower-moving motivation signal against
which the faster-moving craving signal can be contextualized.

Instrument structure (Heather 2008):

**1 item, 0-10 integer scale** — "On a scale of 0 to 10, how ready
are you to change?" (0 = not ready at all, 10 = completely ready).

The 0-10 range is a deliberate compromise between the rich gradient
of a 0-100 VAS and the coarse ordinality of a 5-band Likert.  Heather
2008 validated exactly 0-10 against longer instruments; abbreviating
to 0-5 or extending to 0-100 would invalidate the correlations.

Scoring (Heather 2008):
- ``total`` is the single integer response.  Range 0-10.
- No reverse-coding, no subscale partitioning.

**Direction semantics** — higher is better:
Unlike every other single-item instrument in the package (Craving
VAS where higher = worse craving), Readiness Ruler is a
*positively-valenced* continuous measure: higher readiness is the
therapeutic target.  For the scorer this is a no-op (we store the
integer as submitted).  For the downstream **trajectory layer** this
matters: a week-over-week Δ of +2 on the Ruler is *improvement*,
while a Δ of +2 on VAS / PHQ-9 / GAD-7 is *deterioration*.

The platform already handles this inversion for WHO-5 (0-25 raw →
0-100 Index, higher is better); the Ruler is the second such
instrument.  When the trajectory-layer RCI thresholds gain Ruler
coverage, it must register as a higher-is-better direction alongside
WHO-5 — the PHQ-9 / GAD-7 / PSS-10 / VAS direction would report
improvement as deterioration and vice-versa.

Severity bands — deliberately absent:
The Ruler publishes no bands.  Heather 2008 treats the single integer
as a continuous motivation estimate; the MI literature treats any
score ≥ 7 as "action-stage readiness" and any score ≤ 3 as
"pre-contemplation", but these anchor descriptions are **pedagogical
shorthand**, not clinically-validated cutoffs with consensus uptake.
Fabricating severity bands from pedagogical anchors would violate
CLAUDE.md's "Don't hand-roll severity thresholds" rule.  Accordingly
the scorer emits no severity band; the router envelope uses
``severity="continuous"`` as a sentinel (uniform with PACS and
Craving VAS).

The full stages-of-change classification (precontemplation /
contemplation / preparation / action / maintenance) is the construct
**URICA** measures (16 items, 4 subscale scores — planned for a
future sprint per §3.1 row #10).  The Ruler is URICA's
single-item equivalent, not a replacement for it.

Safety routing:
Readiness Ruler carries no suicidality item and no acute-harm item.
``requires_t3`` is deliberately absent — a Ruler score of 0 ("not
ready at all") is a motivation signal, not a crisis signal.  Low
motivation pairs with low-agency mood profiles, and the product
responds with MI-scripted interventions rather than T4 handoff.
Acute ideation is gated by PHQ-9 item 9 / C-SSRS, consistent with
the PACS / PHQ-15 / OCI-R / ISI / VAS safety-posture convention.

Bool rejection note:
Uniform with the rest of the psychometric package — bool items are
rejected at the validator.  A caller submitting ``True`` / ``False``
as shorthand for "yes / no ready" would have their response silently
coerced to 1 / 0, producing a misleading "barely ready" signal
instead of surfacing the wire-format error.

FHIR / LOINC note:
LOINC has codes for various motivation and stages-of-change
instruments but no widely-adopted single-item Readiness Ruler code.
Per the Craving VAS / PACS / C-SSRS precedent, the Readiness Ruler
is NOT registered in ``LOINC_CODE`` / ``LOINC_DISPLAY`` at this
time; the FHIR export will use a system-local code when the
reports-layer render path is extended in a later sprint.

Behavior-target neutrality:
The scorer is behavior-agnostic — "ready to change" is resolved at
the UI layer (ready to stop drinking / using / gambling / etc.)
based on the user's vertical.  Making the scorer target-agnostic
lets the same validated instrument serve every vertical without
per-vertical branching, matching Heather 2008's validation posture
(which demonstrated construct validity against behavior change
across alcohol, tobacco, and illicit-drug samples).

References:
- Rollnick S, Mason P, Butler C (1999).  *Health Behaviour Change:
  A Guide for Practitioners.*  Churchill Livingstone.
- Heather N, Smailes D, Cassidy P (2008).  *Development of a
  Readiness Ruler for use with alcohol brief interventions.*  Drug
  and Alcohol Dependence 98(3):235-240.
- Miller WR, Rollnick S (2013).  *Motivational Interviewing: Helping
  People Change* (3rd ed.).  Guilford Press.
- Prochaska JO, DiClemente CC (1983).  *Stages and processes of
  self-change of smoking: toward an integrative model of change.*
  Journal of Consulting and Clinical Psychology 51(3):390-395.
- LaBrie JW, Quinlan T, Schiffman JE, Earleywine ME (2005).
  *Performance of alcohol and safer sex change rulers compared with
  readiness to change questionnaires.*  Psychology of Addictive
  Behaviors 19(1):112-115.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

INSTRUMENT_VERSION = "readiness_ruler-1.0.0"
ITEM_COUNT = 1
ITEM_MIN = 0
ITEM_MAX = 10


class InvalidResponseError(ValueError):
    """Raised on item-count, item-range, or item-type violations."""


@dataclass(frozen=True)
class ReadinessRulerResult:
    """Typed Readiness Ruler output.

    Fields:
    - ``total``: 0-10, the single integer Ruler response.  Flows into
      the trajectory layer as a **higher-is-better** continuous
      motivation signal — a week-over-week Δ of +2 is improvement.
      For a single-item instrument ``total`` is literally ``items[0]``;
      the field is kept for wire-shape uniformity across the package.
    - ``items``: verbatim input tuple (length 1), pinned for
      auditability.

    Deliberately-absent fields:
    - No ``severity`` field — Heather 2008 publishes no bands, and the
      MI-literature pedagogical anchors (pre-contemplation / action /
      etc.) are not clinically-validated cutoffs.  The router envelope
      emits ``severity="continuous"`` as a sentinel (uniform with PACS
      and Craving VAS).
    - No ``requires_t3`` field — the Ruler measures motivation, not
      crisis.  A score of 0 ("not ready at all") is a motivation
      signal, not a T3 trigger; acute suicidality is gated by PHQ-9 /
      C-SSRS.
    - No subscale fields — the Ruler is URICA's single-item
      equivalent, not a subscaled instrument.  URICA's 4-subscale
      stages-of-change score is a separate instrument planned for a
      future sprint.
    """

    total: int
    items: tuple[int, ...]
    instrument_version: str = INSTRUMENT_VERSION


def _validate_item(index_1: int, value: object) -> int:
    """Validate the single 0-10 Ruler item and return the int value.

    ``index_1`` is the 1-indexed item number (always 1 for the Ruler)
    so the error-message contract is uniform with every multi-item
    scorer.
    """
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidResponseError(
            f"Readiness Ruler item {index_1} must be int, got {value!r}"
        )
    if value < ITEM_MIN or value > ITEM_MAX:
        raise InvalidResponseError(
            f"Readiness Ruler item {index_1} out of range "
            f"[{ITEM_MIN}, {ITEM_MAX}]: {value}"
        )
    return value


def score_readiness_ruler(
    raw_items: Sequence[int],
) -> ReadinessRulerResult:
    """Score a Readiness Ruler response.

    Inputs:
    - ``raw_items``: exactly 1 integer on 0-10.

    Raises :class:`InvalidResponseError` on:
    - Wrong number of items (anything other than 1).
    - A non-int / bool item value.
    - An item outside ``[0, 10]``.

    Returns a :class:`ReadinessRulerResult` with ``total`` == the
    single integer response and the pinned item tuple.  No severity
    band is emitted — see module docstring.
    """
    if len(raw_items) != ITEM_COUNT:
        raise InvalidResponseError(
            f"Readiness Ruler requires exactly {ITEM_COUNT} item, "
            f"got {len(raw_items)}"
        )
    items = tuple(
        _validate_item(index_1=i + 1, value=v)
        for i, v in enumerate(raw_items)
    )
    total = items[0]

    return ReadinessRulerResult(
        total=total,
        items=items,
    )


__all__ = [
    "INSTRUMENT_VERSION",
    "InvalidResponseError",
    "ITEM_COUNT",
    "ITEM_MAX",
    "ITEM_MIN",
    "ReadinessRulerResult",
    "score_readiness_ruler",
]

"""Craving VAS — single-item 0-100 Visual Analog Scale of momentary craving.

The craving Visual Analog Scale is the canonical **point-in-time** craving
measure used across addiction research: a single integer on a 0-100 line
anchored by "no craving at all" (0) and "strongest craving I have ever
felt" (100).  Unlike the multi-item recall-based scales (PACS, OCDS),
the VAS asks a single question — "right now, how strong is your urge?"
— and returns a continuous intensity estimate.

The measurement-of-craving literature treats the VAS as the de-facto
EMA (ecological momentary assessment) instrument because it is (a)
fast enough to answer in < 5 seconds inside a phone prompt, (b)
substance-agnostic (used in alcohol, tobacco, cannabis, opioid,
stimulant, gambling, and food-craving trials), and (c) has decades of
convergent-validity data against other craving measures and behavioral
outcomes.  The foundational review is

    Sayette MA, Shiffman S, Tiffany ST, Niaura RS, Martin CS, Shadel WG
    (2000).  *The measurement of drug craving.*  Addiction 95(Suppl 2):
    S189-S210.

which synthesizes the psychometric case for single-item VAS craving
measures; Rosenberg 2009 extends this with a systematic review of
craving measurement in substance-use trials and documents the VAS as
"the most frequently employed craving assessment tool" (Rosenberg HS
2009, Clin Psychol Rev 29(6):519-534).

Clinical relevance to the Discipline OS platform:
The Craving VAS is **the EMA partner to PACS**.  They answer different
clinical questions:

- **PACS** — "has this past week been harder than last week?"
  (trajectory, 5-item recall, weekly cadence)
- **Craving VAS** — "is the intervention working RIGHT NOW?"
  (instantaneous, 1-item, EMA cadence — ad-hoc + pre/post intervention)

The VAS is also the direct instrumentation of the 60-180 second
urge-to-action window documented in
Docs/Whitepapers/01_Methodology.md §urge-to-action: the product
surfaces a VAS prompt at urge-onset, delivers an intervention, then
re-prompts for a post-intervention VAS.  The within-episode Δ
(pre-VAS minus post-VAS) is the per-session efficacy signal the
contextual bandit trains on.  A week of post-VAS scores lower than
pre-VAS scores by an average of ≥ 10 points is the behavioral-change
signature the intervention layer is optimizing for.

Instrument structure (Sayette 2000 synthesis):

**1 item, 0-100 integer scale** ("Please rate your current craving
from 0 to 100, where 0 = no craving at all and 100 = the strongest
craving you have ever felt.").

The 0-100 range is NOT a Likert anchor — it's a pseudo-continuous
visual line.  Historical paper-and-pencil versions used a 100 mm line
with anchor labels at the ends; the digital administration pins the
response to an integer slider (0-100) so the stored record is
unambiguously comparable across administrations.  Half-points
(56.5, etc.) are not accepted — callers must submit an integer.

Scoring (Sayette 2000):
- ``total`` is the single integer response.  Range 0-100.
- No reverse-coding, no subscale partitioning — the instrument is
  intentionally one-dimensional.

Severity bands — deliberately absent:
The VAS publishes no severity thresholds.  A "60" means different
things for different users, different substances, and different
episodes.  What is clinically meaningful is:

1. **Within-user trajectory** — does this user's mean EMA VAS decline
   week-over-week as the program progresses? (trajectory layer)
2. **Within-episode delta** — does the post-intervention VAS drop
   below the pre-intervention VAS by ≥ 10 points? (bandit layer)
3. **Baseline-relative deviation** — is this week's mean VAS elevated
   vs the user's own running baseline? (relapse-risk layer)

All three are *relative* measures — absolute cutoffs would impose a
misleading universality on a signal the literature treats as
user-calibrated.  Accordingly this scorer emits no severity band;
the router envelope uses ``severity="continuous"`` as a sentinel
(uniform with PACS from Sprint 34).  Fabricating VAS bands here would
violate CLAUDE.md's "Don't hand-roll severity thresholds" rule.

Safety routing:
Craving VAS has no suicidality item and no acute-harm item.
``requires_t3`` is deliberately absent — the VAS measures urge, not
crisis.  A VAS of 100 is "peak subjective craving", not active
suicidality.  Co-administered PHQ-9 / C-SSRS submissions remain the
T3 gate when acute ideation is present, consistent with the PACS /
PHQ-15 / OCI-R / ISI safety-posture convention.

Bool rejection note:
Uniform with the rest of the psychometric package — bool items are
rejected at the validator.  The caller might be tempted to pass
``True`` / ``False`` as shorthand for "some / none" craving; silently
coercing those to 1 / 0 would produce meaningless VAS values.

FHIR / LOINC note:
LOINC has a generic "craving assessment" code but no widely-adopted
VAS-specific panel code.  Per the PACS / C-SSRS precedent, the Craving
VAS is NOT registered in ``LOINC_CODE`` / ``LOINC_DISPLAY`` at this
time; the FHIR export will use a system-local code when the
reports-layer render path is extended in a later sprint.  When a
LOINC code is verified, registration is a single-file update in
``services/api/src/discipline/reports/fhir_observation.py``.

Substance-class neutrality:
This scorer accepts a single integer and does not ask which substance
the craving is for.  The substance context is surfaced upstream (the
UI prompts "craving for alcohol" / "craving for nicotine" / etc.
based on the user's vertical) and stored alongside the assessment at
the repository layer.  Making the scorer substance-agnostic lets the
same validated instrument serve every vertical (alcohol, cannabis,
nicotine, opioid, gambling, porn-use) without per-vertical branching
— and it matches the underlying literature where the VAS is deployed
substance-agnostically.

References:
- Sayette MA, Shiffman S, Tiffany ST, Niaura RS, Martin CS, Shadel WG
  (2000).  *The measurement of drug craving.*  Addiction 95(Suppl 2):
  S189-S210.
- Rosenberg HS (2009).  *Clinical and laboratory assessment of the
  subjective experience of drug craving.*  Clinical Psychology Review
  29(6):519-534.
- Tiffany ST, Wray JM (2012).  *The clinical significance of drug
  craving.*  Annals of the New York Academy of Sciences 1248:1-17.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

INSTRUMENT_VERSION = "craving_vas-1.0.0"
ITEM_COUNT = 1
ITEM_MIN = 0
ITEM_MAX = 100


class InvalidResponseError(ValueError):
    """Raised on item-count, item-range, or item-type violations."""


@dataclass(frozen=True)
class CravingVasResult:
    """Typed Craving VAS output.

    Fields:
    - ``total``: 0-100, the single integer VAS response.  Flows into the
      trajectory layer as a continuous momentary-craving signal.  For a
      single-item instrument ``total`` is literally ``items[0]`` — the
      field is kept for wire-shape uniformity with every multi-item
      scorer in the package.
    - ``items``: verbatim input tuple (length 1), pinned for auditability.

    Deliberately-absent fields:
    - No ``severity`` field — the VAS publishes no bands and the
      literature treats it as a per-user / per-episode relative signal.
      The router envelope emits ``severity="continuous"`` as a sentinel
      (uniform with PACS).
    - No ``requires_t3`` field — the VAS measures urge intensity, not
      crisis.  Peak craving (VAS = 100) is not a T3 trigger; acute
      suicidality via PHQ-9 / C-SSRS is the T3 gate.
    - No subscale fields — the instrument is intentionally
      one-dimensional by design.
    """

    total: int
    items: tuple[int, ...]
    instrument_version: str = INSTRUMENT_VERSION


def _validate_item(index_1: int, value: object) -> int:
    """Validate the single 0-100 VAS item and return the int value.

    ``index_1`` is the 1-indexed item number (always 1 for VAS) so the
    error-message contract is uniform with every multi-item scorer.
    """
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidResponseError(
            f"Craving VAS item {index_1} must be int, got {value!r}"
        )
    if value < ITEM_MIN or value > ITEM_MAX:
        raise InvalidResponseError(
            f"Craving VAS item {index_1} out of range "
            f"[{ITEM_MIN}, {ITEM_MAX}]: {value}"
        )
    return value


def score_craving_vas(raw_items: Sequence[int]) -> CravingVasResult:
    """Score a Craving VAS response.

    Inputs:
    - ``raw_items``: exactly 1 integer on 0-100.

    Raises :class:`InvalidResponseError` on:
    - Wrong number of items (anything other than 1).
    - A non-int / bool item value.
    - An item outside ``[0, 100]``.

    Returns a :class:`CravingVasResult` with ``total`` == the single
    integer response and the pinned item tuple.  No severity band is
    emitted — see module docstring.
    """
    if len(raw_items) != ITEM_COUNT:
        raise InvalidResponseError(
            f"Craving VAS requires exactly {ITEM_COUNT} item, "
            f"got {len(raw_items)}"
        )
    items = tuple(
        _validate_item(index_1=i + 1, value=v)
        for i, v in enumerate(raw_items)
    )
    total = items[0]

    return CravingVasResult(
        total=total,
        items=items,
    )


__all__ = [
    "INSTRUMENT_VERSION",
    "ITEM_COUNT",
    "ITEM_MAX",
    "ITEM_MIN",
    "CravingVasResult",
    "InvalidResponseError",
    "score_craving_vas",
]

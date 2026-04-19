"""LOT-R — Life Orientation Test Revised (Scheier, Carver & Bridges 1994).

LOT-R is the validated 10-item revision of the original Life Orientation
Test (Scheier & Carver 1985).  It measures **dispositional optimism** —
the generalized outcome expectancy that good things (rather than bad)
will happen to a person across life domains.  Scheier 1994 re-analyzed
the 1985 LOT's factor structure, dropped items that loaded on a
neuroticism / general-affect secondary factor (items 2, 5, 6, 8 of the
original 12) and retained only those that loaded cleanly on the
optimism-pessimism primary factor.  The result is a 6-scored-item
unidimensional measure that cleanly separates trait optimism from
overlapping affect constructs.

Clinical relevance to the Discipline OS platform:
Dispositional optimism is the **outcome-expectancy** trait that pairs
with CD-RISC-10's resilience **capacity** trait to form the two-axis
trait-positive-psychology layer:

- CD-RISC-10 answers "CAN I bounce back?"
- LOT-R answers "DO I EXPECT good things to happen?"

Both are higher-is-better, both are continuous/no-bands, both are
published-norm-reference (Scheier 1994 general-pop norms for LOT-R;
Campbell-Sills & Stein 2007 for CD-RISC-10).  Together they predict
treatment adherence (optimists stay in treatment longer — Carver 2010
meta-analysis), effort allocation to behavior-change tools (optimistic
patients engage more with implementation-intention scaffolding), and
recovery-slope steepness (the trajectory literature consistently finds
optimism predicts post-intervention recovery velocity above baseline-
severity covariates).  The intervention-selection layer reads LOT-R
as an effort-expectancy prior: low-optimism patients route to "small-
wins" scaffolding (short implementation intentions, early success
reinforcement), high-optimism patients tolerate longer-horizon
intervention arcs without disengagement.

Complements the instruments already shipped:
- CD-RISC-10 (resilience capacity) — direct pair, both higher-is-better
- AAQ-II (ACT target: psychological inflexibility)
- DERS-16 (DBT target: emotion dysregulation)
- PHQ-9 / GAD-7 (symptom severity)
- WSAS (functional impairment)
- PSWQ (trait worry) — opposite-direction construct; high PSWQ +
  low LOT-R is the pessimistic-worrier profile, the classic GAD-
  ruminator cluster that responds to CBT-for-GAD + optimism
  training combined interventions (Hanssen 2013).

Instrument structure (Scheier, Carver & Bridges 1994):

**10 items total, 6 scored + 4 filler**, each on a 0-4 Likert scale
scored:
    0 = strongly disagree
    1 = disagree
    2 = neutral
    3 = agree
    4 = strongly agree

**Scored items** (1-indexed positions in the form):
- Item 1: "In uncertain times, I usually expect the best."  [direct]
- Item 3: "If something can go wrong for me, it will."  [REVERSE]
- Item 4: "I'm always optimistic about my future."  [direct]
- Item 7: "I hardly ever expect things to go my way."  [REVERSE]
- Item 9: "I rarely count on good things happening to me."  [REVERSE]
- Item 10: "Overall, I expect more good things to happen to me than bad."  [direct]

**Filler items** (1-indexed positions — NOT scored):
- Item 2: "It's easy for me to relax."
- Item 5: "I enjoy my friends a lot."
- Item 6: "It's important for me to keep busy."
- Item 8: "I don't get upset too easily."

The filler items are present on the patient-facing form to obscure
the instrument's purpose against demand characteristics (optimism is
a socially-desirable trait; respondents may inflate scores if they
recognize the construct).  They are NOT summed into the total.  The
router accepts a 10-item payload (because the form displays 10 items
to the patient) and the scorer drops the 4 filler positions during
summation.  An audit-trail constraint: the stored record preserves
all 10 raw responses — the patient ticked them and they exist in the
record — but only 6 contribute to the score.

**First filler-item pattern in the package.**  Earlier instruments
scored every validated-input item.  LOT-R is the first with within-
form camouflage.  The scorer encodes the scored positions as a frozen
tuple ``LOTR_SCORED_POSITIONS = (1, 3, 4, 7, 9, 10)``; summation
iterates only those positions.  The audit-trail invariant is that
``items`` on the result preserves the RAW 10-item tuple (all 10
responses the patient ticked), not just the 6 scored values.

Reverse-keying — reuses the pattern established by PSWQ:
Items 3, 7, 9 are worded in the PESSIMISM direction.  A high raw
Likert on those items reflects LOW optimism; the scorer applies the
same arithmetic-reflection flip established in PSWQ (``flipped =
ITEM_MIN + ITEM_MAX - raw`` = ``4 - raw`` on this envelope):
    raw 0 → 4, raw 1 → 3, raw 2 → 2, raw 3 → 1, raw 4 → 0.

Post-flip, every scored item contributes in the optimism direction.

Range: 0-24 (post-flip sum of the 6 scored items).

**Higher is better.**  Uniform with CD-RISC-10 / WHO-5 / DTCQ-8 /
Readiness Ruler.  Clients rendering LOT-R scores must not reuse the
higher-is-worse visual language from PHQ-9 / GAD-7 / DERS-16 / PCL-5 /
OCI-R / K10 / WSAS / PSWQ — a falling LOT-R is a DETERIORATION.

Severity bands — deliberately absent:
Scheier 1994 reported general-population means (~14-15 in U.S. adult
samples) and the LOT-R has been used extensively in health-psychology
research (Carver 2010 reviews over 400 studies), but Scheier 1994 did
NOT publish banded clinical thresholds and no downstream paper has
cross-calibrated cuts against a shared clinical criterion.  Per
CLAUDE.md's "don't hand-roll severity thresholds" rule, LOT-R ships
as a **continuous dimensional measure** uniform with PACS / Craving
VAS / DERS-16 / CD-RISC-10 / PSWQ.  The router envelope emits
``severity="continuous"`` as the sentinel; the trajectory layer
extracts the clinical signal via RCI-style change detection (Jacobson
& Truax 1991) rather than banded classification.  The platform layer
may surface a "below general-population mean" flag (score < 14) as
contextual information on the clinician UI — that flag is NOT a
classification and NOT a gate.

Envelope choice:
Continuous-total shape uniform with PACS / Craving VAS / DERS-16 /
CD-RISC-10 / PSWQ.  ``cutoff_used`` / ``positive_screen`` are NOT
set.  No ``subscales`` dict — Scheier 1994 factor analysis sustained
the unidimensional structure (an optimism-pessimism two-factor split
has been proposed by Chang 1997 but is sample-specific and not the
canonical scoring; we ship the unidimensional total per Scheier 1994).

Safety routing:
LOT-R has **no direct safety item**.  The 10 items probe the
optimism-pessimism construct and general affect fillers; none probe
suicidality, self-harm, or crisis behavior.  ``requires_t3`` is never
set — acute ideation screening is PHQ-9 item 9 / C-SSRS, not LOT-R.
Clinical posture: a low LOT-R is a strong signal for outcome-
expectancy scaffolding (small-wins framing, early-success
reinforcement, implementation intentions with short horizons) but is
not itself a crisis gate.

Bool rejection note:
Uniform with the rest of the psychometric package — bool items are
rejected at the validator.  See mdq.py, pcptsd5.py, isi.py, pcl5.py,
ocir.py, bis11.py, phq2.py, gad2.py, oasis.py, k10.py, sds.py, k6.py,
dudit.py, asrs6.py, aaq2.py, wsas.py, ders16.py, cdrisc10.py, pswq.py
for the shared rationale.

References:
- Scheier MF, Carver CS, Bridges MW (1994).  *Distinguishing optimism
  from neuroticism (and trait anxiety, self-mastery, and self-
  esteem): A reevaluation of the Life Orientation Test.*  Journal of
  Personality and Social Psychology 67(6):1063-1078.
- Scheier MF, Carver CS (1985).  *Optimism, coping, and health:
  Assessment and implications of generalized outcome expectancies.*
  Health Psychology 4(3):219-247.
- Carver CS, Scheier MF, Segerstrom SC (2010).  *Optimism.*  Clinical
  Psychology Review 30(7):879-889.
- Chang EC, D'Zurilla TJ, Maydeu-Olivares A (1994).  *Assessing the
  dimensionality of optimism and pessimism using a multimeasure
  approach.*  Cognitive Therapy and Research 18(2):143-160.  (Two-
  factor split proposal — sample-specific; we ship unidimensional.)
- Hanssen MM, Vancleef LMG, Vlaeyen JWS, Peters ML (2013).  *More
  optimism, less pain! The influence of generalized and pain-specific
  expectations on experienced cold-pressor pain.*  Journal of
  Behavioral Medicine 36(1):47-58.  (Applied-clinical framing for
  optimism-training interventions.)
- Jacobson NS, Truax P (1991).  *Clinical significance: A statistical
  approach to defining meaningful change in psychotherapy research.*
  Journal of Consulting and Clinical Psychology 59(1):12-19.  (RCI
  framing for continuous-instrument trajectory analysis on the
  platform.)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

INSTRUMENT_VERSION = "lotr-1.0.0"
ITEM_COUNT = 10
ITEM_MIN = 0
ITEM_MAX = 4

# Scored item positions (1-indexed) per Scheier 1994.  The 6 items
# that load on the optimism-pessimism primary factor.  Encoded as a
# frozen tuple so the scorer cannot mutate the scored set at runtime
# and equality checks are hash-stable.
LOTR_SCORED_POSITIONS: tuple[int, ...] = (1, 3, 4, 7, 9, 10)

# Filler item positions (1-indexed) per Scheier 1994.  Included on
# the form to obscure the instrument's purpose against demand
# characteristics; NOT summed into the total.  Exposed as a named
# constant so downstream callers (clinician-UI layer, audit
# documentation) can distinguish scored from filler positions
# programmatically.
LOTR_FILLER_POSITIONS: tuple[int, ...] = (2, 5, 6, 8)

# Reverse-keyed item positions (1-indexed) per Scheier 1994.  These
# items are worded in the pessimism direction; flipped before summing
# so the post-flip value contributes in the optimism direction
# uniformly.
LOTR_REVERSE_ITEMS: tuple[int, ...] = (3, 7, 9)


class InvalidResponseError(ValueError):
    """Raised on item-count, item-range, or item-type violations."""


@dataclass(frozen=True)
class LotrResult:
    """Typed LOT-R output.

    Fields:
    - ``total``: 0-24, the post-flip sum of the 6 scored items.
      Higher is better (more trait optimism) — same directionality
      as CD-RISC-10 / WHO-5 / DTCQ-8 / Readiness Ruler, opposite of
      PHQ-9 / GAD-7 / DERS-16 / PCL-5 / OCI-R / K10 / WSAS / PSWQ.
      Minimum 0 (every scored item at 0 post-flip), maximum 24
      (every scored item at 4 post-flip).  The 4 filler items do NOT
      contribute.
    - ``items``: verbatim 10-tuple input, pinned for auditability.
      **All 10 raw responses preserved** — including the 4 filler
      items the patient ticked on the form.  The audit trail shows
      what the patient saw and answered, not just the scored subset.
      The reverse-keying flip on items 3, 7, 9 is an internal detail
      of ``score_lotr`` and is not surfaced in ``items``.

    Deliberately-absent fields:
    - No ``severity`` field — Scheier 1994 published no banded
      thresholds.  The router envelope emits ``severity="continuous"``
      as a sentinel (uniform with DERS-16 / CD-RISC-10 / PSWQ /
      Craving VAS / PACS).
    - No ``cutoff_used`` / ``positive_screen`` — continuous
      instrument, no cutoff shape.
    - No ``requires_t3`` field — LOT-R has no safety item.
    - No ``subscales`` — Scheier 1994 sustained the unidimensional
      structure.  Chang 1997's optimism/pessimism two-factor split
      is sample-specific and not the canonical scoring.
    """

    total: int
    items: tuple[int, ...]
    instrument_version: str = INSTRUMENT_VERSION


def _validate_item(index_1: int, value: object) -> int:
    """Validate a single 0-4 Likert item and return the int value.

    Every item in the 10-item payload — scored AND filler — is
    range-validated identically.  Rationale: the filler items are on
    the patient-facing form with the same response options as the
    scored items; a value outside [0, 4] in a filler position is a
    wire-format violation just as surely as in a scored position.
    """
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidResponseError(
            f"LOT-R item {index_1} must be int, got {value!r}"
        )
    if value < ITEM_MIN or value > ITEM_MAX:
        raise InvalidResponseError(
            f"LOT-R item {index_1} out of range "
            f"[{ITEM_MIN}, {ITEM_MAX}]: {value}"
        )
    return value


def _scored_contribution(index_1: int, value: int) -> int:
    """Return the post-flip contribution of item ``index_1`` to the
    total, applying the reverse-keying flip if the item is in the
    reverse set.

    Called only for items in ``LOTR_SCORED_POSITIONS`` — filler
    items never reach this helper.  Reuses the arithmetic-reflection
    idiom established in PSWQ: ``flipped = ITEM_MIN + ITEM_MAX -
    raw`` = ``4 - raw`` on this envelope.
    """
    if index_1 in LOTR_REVERSE_ITEMS:
        return (ITEM_MIN + ITEM_MAX) - value
    return value


def score_lotr(raw_items: Sequence[int]) -> LotrResult:
    """Score a LOT-R response set.

    Inputs:
    - ``raw_items``: 10 items, each 0-4 Likert (0 = "strongly
      disagree", 4 = "strongly agree").  All 10 items are validated
      for type / range; only the 6 scored positions (1, 3, 4, 7, 9,
      10) contribute to the total.  Reverse-keying on items 3, 7, 9
      is applied internally before summing — callers should NOT
      pre-flip the raw values.

    Raises :class:`InvalidResponseError` on:
    - Wrong number of items (must be exactly 10).
    - A non-int / bool item value at ANY position (scored or filler).
    - An item outside ``[0, 4]`` at ANY position.

    Computes:
    - Post-flip sum of scored items (0-24) — higher is better (more
      dispositional optimism).  The ``items`` field of the result
      preserves all 10 raw responses including the 4 filler positions.

    No severity band is emitted — see module docstring.
    """
    if len(raw_items) != ITEM_COUNT:
        raise InvalidResponseError(
            f"LOT-R requires exactly {ITEM_COUNT} items, got {len(raw_items)}"
        )
    validated = tuple(
        _validate_item(index_1=i + 1, value=v)
        for i, v in enumerate(raw_items)
    )
    total = sum(
        _scored_contribution(index_1=pos, value=validated[pos - 1])
        for pos in LOTR_SCORED_POSITIONS
    )

    return LotrResult(
        total=total,
        items=validated,
    )


__all__ = [
    "INSTRUMENT_VERSION",
    "InvalidResponseError",
    "ITEM_COUNT",
    "ITEM_MAX",
    "ITEM_MIN",
    "LOTR_FILLER_POSITIONS",
    "LOTR_REVERSE_ITEMS",
    "LOTR_SCORED_POSITIONS",
    "LotrResult",
    "score_lotr",
]

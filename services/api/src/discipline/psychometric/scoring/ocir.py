"""OCI-R — Obsessive-Compulsive Inventory (Revised) (Foa 2002).

The OCI-R is an 18-item self-report screener for obsessive-compulsive
disorder and its symptom subtypes.  It is the short-form replacement
for the 42-item OCI (Foa 1998) and is the most widely used self-report
OCD screener in both clinical and research settings.

Clinical relevance to the Discipline OS platform:
OCD and obsessive-compulsive spectrum disorders sit at the core of
the platform's "compulsive behavior cycles" scope.  Per
Docs/Whitepapers/02_Clinical_Evidence_Base.md §compulsive, distinct
OCD subtypes predict distinct intervention responses — contamination-
/washing-dominant presentations respond to exposure and response
prevention (ERP), hoarding presentations respond to cognitive-
behavioral therapy adapted for hoarding (CBT-H), and obsessing-
dominant presentations benefit from cognitive therapy targeting
thought-action fusion.  Surfacing the subscale pattern lets the
clinician route the patient to the correct intervention rather
than a generic "CBT for OCD" prescription.

Instrument structure (Foa 2002):

**18 items, each on a 0-4 Likert scale**:
Each item asks "The following statements refer to experiences that
many people have in their everyday lives. Circle the number that
best describes how much that experience has DISTRESSED or BOTHERED
you during the past month":
    0 = Not at all
    1 = A little
    2 = Moderately
    3 = A lot
    4 = Extremely

Items are deliberately interleaved across the six subscales so
respondents do not infer the factor structure (Foa 2002 §Method):

**Six 3-item subscales** (1-indexed item numbers):
- **Hoarding** (items 1, 7, 13): saving, discarding difficulty, clutter.
  Note — Hoarding Disorder is a distinct DSM-5 diagnosis in its own
  chapter (Obsessive-Compulsive and Related Disorders); the OCI-R
  hoarding subscale still validly indexes hoarding symptoms even
  though it predates the nosological split.
- **Checking** (items 2, 8, 14): doors, stove, checking repeatedly.
- **Ordering** (items 3, 9, 15): arrangement, symmetry, precision.
- **Neutralizing** (items 4, 10, 16): counting, mental rituals,
  undoing distress with a specific thought or action.
- **Washing** (items 5, 11, 17): contamination concerns, hand-washing,
  shower/bath duration.
- **Obsessing** (items 6, 12, 18): intrusive thoughts, thought control
  difficulty, unwanted unpleasant thoughts.

Scoring (Foa 2002):
- Straight sum of the 18 items (no reverse-coding) — total range 0-72.
- Each subscale is a sum of its 3 items (range 0-12 per subscale).
- Probable-OCD cutoff is ``>= 21`` per Foa 2002 §Results (sensitivity
  0.74, specificity 0.75 in the clinical sample), confirmed in
  Abramowitz 2006.  The cutoff balances sensitivity/specificity and
  is the operating point cited in Foa 2002's primary recommendation
  for screening use.

Safety routing:
OCI-R has no direct safety item — obsessive-content items (e.g.
unwanted distressing thoughts) can superficially resemble the
"intrusive thoughts" of crisis presentations, but they do NOT probe
suicidality or acute harm.  ``requires_t3`` is never set by this
scorer.  A patient with a positive OCI-R AND active suicidality
needs a co-administered C-SSRS submission.

Subscale architecture note:
Unlike PCL-5 where clusters map to contiguous item ranges
(cluster B = items 1-5), OCI-R subscales are deliberately
distributed.  This means the scorer needs a per-subscale
*index tuple* rather than a (start, end) pair.  The
``OCIR_SUBSCALES`` constant below encodes the 1-indexed item
positions per subscale; a refactor that reordered items or flattened
subscale structure must update this constant or the subscale
outputs will silently miscategorize.

Bool rejection note:
Uniform with the rest of the psychometric package — bool items
are rejected at the validator.  See mdq.py, pcptsd5.py, isi.py,
pcl5.py for the shared rationale.

References:
- Foa EB, Huppert JD, Leiberg S, Langner R, Kichic R, Hajcak G,
  Salkovskis PM (2002).  *The Obsessive-Compulsive Inventory:
  development and validation of a short version.*  Psychological
  Assessment 14(4):485-496.
- Abramowitz JS, Deacon BJ (2006).  *Psychometric properties and
  construct validity of the Obsessive-Compulsive Inventory —
  Revised: replication and extension with a clinical sample.*
  Journal of Anxiety Disorders 20(8):1016-1035.
- Hajcak G, Huppert JD, Simons RF, Foa EB (2004).  *Psychometric
  properties of the OCI-R in a college sample.*  Behaviour Research
  and Therapy 42(1):115-123.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

INSTRUMENT_VERSION = "ocir-1.0.0"
ITEM_COUNT = 18
ITEM_MIN = 0
ITEM_MAX = 4

# Published probable-OCD cutoff per Foa 2002 §Results: ``>= 21``
# balances sensitivity 0.74 / specificity 0.75 in the clinical
# sample and is the operating point cited in the screening-use
# recommendation.  Exposed as a module constant so the trajectory
# layer and the clinician UI render the same threshold value.
# Changing this is a clinical change, not an implementation tweak.
OCIR_POSITIVE_CUTOFF = 21

# Subscale → 1-indexed item positions per Foa 2002 Table 1.  Items
# are INTERLEAVED (not contiguous) so respondents do not infer the
# factor structure during administration — a refactor that resorted
# items into contiguous blocks would technically still score the
# same totals but would break the validated administration design,
# so the 1-indexed positions are pinned here verbatim from the paper.
OCIR_SUBSCALES: dict[str, tuple[int, int, int]] = {
    "hoarding": (1, 7, 13),
    "checking": (2, 8, 14),
    "ordering": (3, 9, 15),
    "neutralizing": (4, 10, 16),
    "washing": (5, 11, 17),
    "obsessing": (6, 12, 18),
}


Screen = Literal["positive_screen", "negative_screen"]


class InvalidResponseError(ValueError):
    """Raised on item-count, item-range, or item-type violations."""


@dataclass(frozen=True)
class OcirResult:
    """Typed OCI-R output.

    Fields:
    - ``total``: 0-72, sum of the 18 items.  Flows into the FHIR
      Observation's ``valueInteger``.
    - ``positive_screen``: True iff ``total >= 21`` per Foa 2002.
    - ``subscale_hoarding`` / ``subscale_checking`` /
      ``subscale_ordering`` / ``subscale_neutralizing`` /
      ``subscale_washing`` / ``subscale_obsessing``: six 3-item
      subscale totals (each 0-12).  Clinically meaningful for
      intervention choice (ERP for washing-dominant, CBT-H for
      hoarding-dominant, thought-action-fusion work for obsessing-
      dominant).  Surfaced on the router's AssessmentResult envelope
      via the ``subscales`` map (Sprint 40); wire keys are the
      un-prefixed forms (``hoarding`` / ``checking`` / ``ordering`` /
      ``neutralizing`` / ``washing`` / ``obsessing``) per
      ``OCIR_SUBSCALES``.
    - ``items``: verbatim input tuple, pinned for auditability.

    Safety posture: ``requires_t3`` is deliberately absent.  OCI-R
    has no suicidality item; obsessing-content items resemble
    "intrusive thoughts" but do not probe acute harm.
    """

    total: int
    positive_screen: bool
    subscale_hoarding: int
    subscale_checking: int
    subscale_ordering: int
    subscale_neutralizing: int
    subscale_washing: int
    subscale_obsessing: int
    items: tuple[int, ...]
    instrument_version: str = INSTRUMENT_VERSION


def _validate_item(index_1: int, value: object) -> int:
    """Validate a single 0-4 Likert item and return the int value.

    ``index_1`` is the 1-indexed item number (1-18) so error messages
    name the item a clinician would recognize from the OCI-R document.
    """
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidResponseError(
            f"OCI-R item {index_1} must be int, got {value!r}"
        )
    if value < ITEM_MIN or value > ITEM_MAX:
        raise InvalidResponseError(
            f"OCI-R item {index_1} out of range "
            f"[{ITEM_MIN}, {ITEM_MAX}]: {value}"
        )
    return value


def _subscale_sum(items: tuple[int, ...], subscale_name: str) -> int:
    """Sum the three items belonging to a named subscale.

    OCIR_SUBSCALES holds 1-indexed positions; convert to 0-indexed
    array access here.  A refactor that shifted the subscale index
    tuples (e.g. rotated the subscale rows so "washing" picked up
    checking items) would break the clinical signal silently —
    every subscale test pins its three-item mapping independently.
    """
    positions_1 = OCIR_SUBSCALES[subscale_name]
    return sum(items[pos - 1] for pos in positions_1)


def score_ocir(raw_items: Sequence[int]) -> OcirResult:
    """Score an OCI-R response set.

    Inputs:
    - ``raw_items``: 18 items, each 0-4 Likert severity.

    Raises :class:`InvalidResponseError` on:
    - Wrong number of items.
    - A non-int / bool item value.
    - An item outside ``[0, 4]``.

    Computes:
    - Total score (0-72).
    - Six 3-item subscale totals (each 0-12).
    - Probable-OCD positive_screen via the ``>= 21`` cutoff.
    """
    if len(raw_items) != ITEM_COUNT:
        raise InvalidResponseError(
            f"OCI-R requires exactly {ITEM_COUNT} items, got {len(raw_items)}"
        )
    items = tuple(
        _validate_item(index_1=i + 1, value=v)
        for i, v in enumerate(raw_items)
    )
    total = sum(items)

    return OcirResult(
        total=total,
        positive_screen=total >= OCIR_POSITIVE_CUTOFF,
        subscale_hoarding=_subscale_sum(items, "hoarding"),
        subscale_checking=_subscale_sum(items, "checking"),
        subscale_ordering=_subscale_sum(items, "ordering"),
        subscale_neutralizing=_subscale_sum(items, "neutralizing"),
        subscale_washing=_subscale_sum(items, "washing"),
        subscale_obsessing=_subscale_sum(items, "obsessing"),
        items=items,
    )


__all__ = [
    "INSTRUMENT_VERSION",
    "ITEM_COUNT",
    "ITEM_MAX",
    "ITEM_MIN",
    "OCIR_POSITIVE_CUTOFF",
    "OCIR_SUBSCALES",
    "InvalidResponseError",
    "OcirResult",
    "Screen",
    "score_ocir",
]

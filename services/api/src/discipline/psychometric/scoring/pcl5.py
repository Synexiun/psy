"""PCL-5 — PTSD Checklist for DSM-5 (Weathers 2013; Blevins 2015).

The PCL-5 is the 20-item structured follow-up self-report for PTSD
assessment aligned with DSM-5 criteria.  Unlike PC-PTSD-5 (Prins
2016, 5 binary items — a primary-care screener), PCL-5 is a
full-severity assessment with validated cutoffs and DSM-5 cluster
subscales suitable for treatment planning and outcome tracking.

Clinical relevance to the Discipline OS platform:
PCL-5 is the structured follow-up instrument for a patient who
screens positive on PC-PTSD-5.  Per Docs/Whitepapers/02_Clinical_Evidence_Base.md
§trauma, surfacing the full PCL-5 lets the clinician:
  (1) confirm vs. rule out the primary-care screen,
  (2) baseline symptom severity for outcome measurement,
  (3) identify the dominant DSM-5 symptom cluster for intervention
      choice (e.g. prolonged exposure for a cluster-B-dominant
      presentation vs. cognitive processing therapy for a cluster-D-
      dominant presentation),
  (4) track treatment-response via RCI on the total score.

Instrument structure (Weathers 2013):

**20 items, each on a 0-4 Likert scale**:
Each item asks "In the past month, how much were you bothered by..."
scored:
    0 = Not at all
    1 = A little bit
    2 = Moderately
    3 = Quite a bit
    4 = Extremely

Items map to DSM-5 PTSD symptom clusters:
- **Cluster B (Intrusion) — items 1-5**: repeated disturbing memories,
  dreams, flashback reactions, emotional reactivity to reminders,
  physical reactivity to reminders.
- **Cluster C (Avoidance) — items 6-7**: avoiding memories/thoughts/
  feelings, avoiding external reminders.
- **Cluster D (Negative alterations in cognitions and mood) —
  items 8-14**: difficulty remembering traumatic event, negative
  beliefs, blame, negative emotions, loss of interest, detachment,
  inability to experience positive emotions.
- **Cluster E (Alterations in arousal and reactivity) —
  items 15-20**: irritable behavior/anger, self-destructive behavior,
  hypervigilance, exaggerated startle, concentration difficulty,
  sleep disturbance.

Scoring (Weathers 2013; Blevins 2015):
- Sum of the 20 items is the total score (range 0-80).
- Cluster subscales are the sum of the items in each cluster.
- Probable-PTSD cutoff is ``>= 33`` per Blevins 2015 Veterans sample;
  this cutoff balances sensitivity and specificity and is the
  operating point cited in the National Center for PTSD guidance.

Subscale totals are surfaced on the result dataclass for downstream
use (intervention choice, trajectory analysis by cluster) AND on the
router's AssessmentResult envelope via the generic ``subscales:
dict[str, int] | None`` field (Sprint 40).  The wire keys
(``intrusion`` / ``avoidance`` / ``negative_mood`` / ``hyperarousal``)
match ``PCL5_CLUSTERS`` so clinician-UI renderers key off one source
of truth.

DSM-5 diagnostic algorithm (alternative to cutoff, requires clinical
interpretation — NOT a screener decision):
A provisional DSM-5 PTSD diagnosis requires endorsement at >= 2
("moderately") on:
  - 1 cluster B item, 1 cluster C item, 2 cluster D items, 2 cluster E
    items.
This algorithm is available via ``PCL5_DSM5_ALGORITHM_THRESHOLDS`` but
the scorer's ``positive_screen`` uses only the ``>= 33`` total-score
cutoff — the DSM-5 algorithm is a clinician-reviewed diagnostic
aid, not an automated routing decision.  A future sprint may expose
an explicit ``dsm5_provisional`` boolean if the clinician workflow
demands it.

Safety routing:
PCL-5 has no direct safety item — item 16 ("destructive behavior")
is the closest to self-harm language but asks about risk-taking
broadly, not suicidality.  ``requires_t3`` is never set by this
scorer.  A patient with a positive PCL-5 and active suicidality
needs a co-administered C-SSRS; that is a separate instrument
submission per the safety framework.

Bool rejection note:
Consistent with the rest of the psychometric package — bool items
are rejected at the validator.  See mdq.py, pcptsd5.py, isi.py.

References:
- Weathers FW, Litz BT, Keane TM, Palmieri PA, Marx BP, Schnurr PP
  (2013).  *The PTSD Checklist for DSM-5 (PCL-5).*  National Center
  for PTSD.  www.ptsd.va.gov
- Blevins CA, Weathers FW, Davis MT, Witte TK, Domino JL (2015).
  *The Posttraumatic Stress Disorder Checklist for DSM-5 (PCL-5):
  development and initial psychometric evaluation.*  Journal of
  Traumatic Stress 28(6):489-498.
- Bovin MJ, Marx BP, Weathers FW, Gallagher MW, Rodriguez P,
  Schnurr PP, Keane TM (2016).  *Psychometric properties of the
  PTSD Checklist for Diagnostic and Statistical Manual of Mental
  Disorders — Fifth Edition (PCL-5) in veterans.*  Psychological
  Assessment 28(11):1379-1391.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

INSTRUMENT_VERSION = "pcl5-1.0.0"
ITEM_COUNT = 20
ITEM_MIN = 0
ITEM_MAX = 4

# Published probable-PTSD cutoff per Blevins 2015 §Results: ``>= 33``
# balances sensitivity 0.82 / specificity 0.84 in the Veterans sample
# and is the operating point cited in National Center for PTSD
# clinician guidance.  Exposed as a module constant so the trajectory
# layer and the clinician UI render the same threshold value with no
# drift.  Changing this is a clinical change, not an implementation
# tweak.
PCL5_POSITIVE_CUTOFF = 33

# DSM-5 cluster → 1-indexed item ranges per Weathers 2013 §Scoring.
# Kept as 1-indexed (inclusive start, inclusive end) because that's
# how the instrument document presents the mapping — a reader
# cross-referencing to the PCL-5 paper sees the same indices.  The
# scorer converts to 0-indexed slice bounds internally.
PCL5_CLUSTERS: dict[str, tuple[int, int]] = {
    "intrusion": (1, 5),          # Cluster B
    "avoidance": (6, 7),          # Cluster C
    "negative_mood": (8, 14),     # Cluster D
    "hyperarousal": (15, 20),     # Cluster E
}

# DSM-5 alternative algorithm thresholds per Weathers 2013 §Diagnostic.
# Each tuple is (cluster_name, minimum_items_at_or_above_2).  Exposed
# for future clinician-UI use — not currently consumed by the scorer.
PCL5_DSM5_ALGORITHM_THRESHOLDS: tuple[tuple[str, int], ...] = (
    ("intrusion", 1),
    ("avoidance", 1),
    ("negative_mood", 2),
    ("hyperarousal", 2),
)


Screen = Literal["positive_screen", "negative_screen"]


class InvalidResponseError(ValueError):
    """Raised on item-count, item-range, or item-type violations."""


@dataclass(frozen=True)
class Pcl5Result:
    """Typed PCL-5 output.

    Fields:
    - ``total``: 0-80, sum of the 20 items.  This is the field that
      flows into the FHIR Observation's ``valueInteger``.
    - ``positive_screen``: True iff ``total >= 33`` per Blevins 2015.
    - ``cluster_intrusion`` / ``cluster_avoidance`` /
      ``cluster_negative_mood`` / ``cluster_hyperarousal``: DSM-5
      cluster B/C/D/E subscale totals.  Clinically meaningful for
      intervention choice (e.g. exposure therapy for intrusion-
      dominant presentations, cognitive processing therapy for
      negative-mood-dominant presentations).  Surfaced on the router's
      AssessmentResult envelope via the ``subscales`` map (Sprint 40);
      wire keys are the un-prefixed forms (``intrusion`` / ``avoidance``
      / ``negative_mood`` / ``hyperarousal``) per ``PCL5_CLUSTERS``.
    - ``items``: verbatim input tuple, pinned for auditability.

    Safety posture: ``requires_t3`` is deliberately absent.  PCL-5
    has no direct suicidality item and a positive screen is a
    referral signal for trauma-focused therapy, not a crisis signal.
    See module docstring.
    """

    total: int
    positive_screen: bool
    cluster_intrusion: int
    cluster_avoidance: int
    cluster_negative_mood: int
    cluster_hyperarousal: int
    items: tuple[int, ...]
    instrument_version: str = INSTRUMENT_VERSION


def _validate_item(index_1: int, value: object) -> int:
    """Validate a single 0-4 Likert item and return the int value.

    ``index_1`` is the 1-indexed item number (1-20) so error messages
    name the item a clinician would recognize from the PCL-5 document.
    """
    # Bool rejection — uniform with the rest of the psychometric package.
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidResponseError(
            f"PCL-5 item {index_1} must be int, got {value!r}"
        )
    if value < ITEM_MIN or value > ITEM_MAX:
        raise InvalidResponseError(
            f"PCL-5 item {index_1} out of range "
            f"[{ITEM_MIN}, {ITEM_MAX}]: {value}"
        )
    return value


def _cluster_sum(items: tuple[int, ...], cluster_name: str) -> int:
    """Sum items belonging to a DSM-5 cluster.

    PCL5_CLUSTERS is 1-indexed inclusive-inclusive; convert to a
    0-indexed slice here.  A refactor that shifted the cluster
    boundaries (e.g. included item 6 in cluster B instead of C)
    would break the validated DSM-5 mapping and the downstream
    intervention-choice logic — the cluster tests pin this.
    """
    start_1, end_1 = PCL5_CLUSTERS[cluster_name]
    return sum(items[start_1 - 1 : end_1])


def score_pcl5(raw_items: Sequence[int]) -> Pcl5Result:
    """Score a PCL-5 response set.

    Inputs:
    - ``raw_items``: 20 items, each 0-4 Likert severity.

    Raises :class:`InvalidResponseError` on:
    - Wrong number of items.
    - A non-int / bool item value.
    - An item outside ``[0, 4]``.

    Computes:
    - Total score (0-80).
    - Cluster B/C/D/E subscales.
    - Probable-PTSD positive_screen via the ``>= 33`` cutoff.
    """
    if len(raw_items) != ITEM_COUNT:
        raise InvalidResponseError(
            f"PCL-5 requires exactly {ITEM_COUNT} items, got {len(raw_items)}"
        )
    items = tuple(
        _validate_item(index_1=i + 1, value=v)
        for i, v in enumerate(raw_items)
    )
    total = sum(items)

    return Pcl5Result(
        total=total,
        positive_screen=total >= PCL5_POSITIVE_CUTOFF,
        cluster_intrusion=_cluster_sum(items, "intrusion"),
        cluster_avoidance=_cluster_sum(items, "avoidance"),
        cluster_negative_mood=_cluster_sum(items, "negative_mood"),
        cluster_hyperarousal=_cluster_sum(items, "hyperarousal"),
        items=items,
    )


__all__ = [
    "INSTRUMENT_VERSION",
    "ITEM_COUNT",
    "ITEM_MAX",
    "ITEM_MIN",
    "PCL5_CLUSTERS",
    "PCL5_DSM5_ALGORITHM_THRESHOLDS",
    "PCL5_POSITIVE_CUTOFF",
    "InvalidResponseError",
    "Pcl5Result",
    "Screen",
    "score_pcl5",
]

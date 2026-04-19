"""BIS-11 — Barratt Impulsiveness Scale, 11th edition
(Patton, Stanford, Barratt 1995).

The BIS-11 is a 30-item self-report measure of **impulsiveness as a
stable personality trait**.  It is the most widely-cited impulsivity
instrument in the clinical literature and is the reference measure
for the dispositional construct (as opposed to state-level urge
measures like PACS).

Clinical relevance to the Discipline OS platform:
Impulsivity is the trait-level substrate of the compulsive-behavior
cycle the product intervenes on.  Per
Docs/Whitepapers/02_Clinical_Evidence_Base.md §compulsive, the
60-180 second urge-to-action window the platform targets is gated
*behaviorally* by dispositional impulsivity — a high-BIS patient
bridges craving→act faster and with less deliberation than a
low-BIS patient.  A rising PACS (craving, state) with high
baseline BIS-11 (impulsivity, trait) is the highest-risk profile
for imminent relapse; a rising PACS with low BIS-11 has a longer
intervention window.  Pairing the two instruments is what lets
the platform calibrate intervention intensity to the trait-by-
state interaction rather than treating every craving spike
identically.

Instrument structure (Patton 1995):

**30 items, each on a 1-4 Likert scale**.  Note the 1-4 range
vs. the 0-based scales of every other instrument in the package —
Patton 1995's response anchors start at "Rarely/Never = 1" rather
than 0.  The scorer enforces the 1-4 range; submitting a 0 raises
InvalidResponseError:
    1 = Rarely/Never
    2 = Occasionally
    3 = Often
    4 = Almost Always/Always

Instruction prompt (verbatim Patton 1995):
"People differ in the ways they act and think in different
situations. This is a test to measure some of the ways in which
you act and think. Read each statement and circle the appropriate
circle on the right side of this page."

**Reverse-coded items** (1-indexed; Patton 1995 Table 1):
Items 1, 7, 8, 9, 10, 12, 13, 15, 20, 29, 30 are positively worded
("I plan tasks carefully", "I am self-controlled", ...) and must be
reverse-scored before summation so higher total = higher impulsivity
is monotonic across all 30 items.  Reverse formula for a 1-4 scale:
``ITEM_MIN + ITEM_MAX - value = 5 - value`` (so 1↔4, 2↔3).

**Three second-order subscales** (Patton 1995 Table 2):
- **Attentional impulsiveness** (8 items: 5, 6, 9R, 11, 20R, 24, 26,
  28) — difficulty concentrating, racing thoughts, present-focus
  cognitive style.  Range 8-32.
- **Motor impulsiveness** (11 items: 2, 3, 4, 16, 17, 19, 21, 22,
  23, 25, 30R) — acting without thinking, restlessness, action-
  oriented approach to stimuli.  Range 11-44.
- **Non-planning impulsiveness** (11 items: 1R, 7R, 8R, 10R, 12R,
  13R, 14, 15R, 18, 27, 29R) — lack of forethought, preference for
  the immediate over the long-term.  Range 11-44.

(R = reverse-coded for that item.)  Items are NOT contiguous per
subscale — they are distributed across the instrument so
respondents do not infer the factor structure during
administration.  The OCI-R distributed-subscale precedent
(``scoring/ocir.py``) is followed here.

Scoring (Patton 1995; Stanford 2009 bands):
- Reverse-score the 11 reverse-coded items (1-4 flip via 5 - v).
- Straight sum the 30 scored items → total range 30-120.
- Subscale totals are sums over the scored (post-reversal) values.

Severity bands — Stanford 2009 normative cutoffs:
Stanford KL, Mathias CW, Dougherty DM, Lake SL, Anderson NE,
Patton JH (2009) *Fifty years of the Barratt Impulsiveness Scale:
an update and review* (Personality and Individual Differences
47(5):385-395) pins the widely-cited thresholds:

    <= 51:   "low"     — over-controlled / may indicate exaggeratedly
                         careful response bias or genuinely low
                         impulsivity; clinician-UI flags as possible
                         socially-desirable-responding pattern.
    52-71:  "normal"   — within normative range.
    >= 72:  "high"     — Stanford 2009 operationalization of "highly
                         impulsive"; the treatment-relevant threshold
                         cited in the addiction / ADHD / personality-
                         disorder literature as the cutoff at which
                         impulsivity-specific interventions (DBT
                         distress tolerance, mindfulness-based
                         attention training, stimulus-control
                         planning) are indicated.

These thresholds are pinned as a module constant so the trajectory
layer and the clinician UI render the same values.  Changing them
is a clinical change, not an implementation tweak.

Safety routing:
BIS-11 has no direct safety item — it probes trait impulsiveness
across attention / motor / planning without asking about self-harm
or suicidality.  ``requires_t3`` is deliberately absent from this
result.  A patient with a high BIS-11 AND acute suicidality needs a
co-administered PHQ-9 / C-SSRS submission to fire T3, consistent
with the PHQ-15 / OCI-R / ISI / PCL-5 / PACS safety posture.

Bool rejection note:
Uniform with the rest of the psychometric package — bool items
are rejected at the validator.  See isi.py, mdq.py, pcptsd5.py,
pcl5.py, ocir.py, phq15.py, pacs.py for the shared rationale.

FHIR / LOINC note:
BIS-11 does NOT have a universally-published LOINC panel code that
can be cited with the same confidence as the PHQ-family codes.  Per
the C-SSRS / PACS precedent, unregistered instruments follow a
separate render path rather than risk emitting an unverified LOINC.
BIS-11 is therefore NOT registered in LOINC_CODES / LOINC_DISPLAY;
its FHIR export will use a system-local code when the reports layer
is extended in a later sprint.

References:
- Patton JH, Stanford MS, Barratt ES (1995).  *Factor structure of
  the Barratt Impulsiveness Scale.*  Journal of Clinical Psychology
  51(6):768-774.
- Stanford MS, Mathias CW, Dougherty DM, Lake SL, Anderson NE,
  Patton JH (2009).  *Fifty years of the Barratt Impulsiveness
  Scale: an update and review.*  Personality and Individual
  Differences 47(5):385-395.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence

INSTRUMENT_VERSION = "bis11-1.0.0"
ITEM_COUNT = 30
# First non-zero-based scale in the package — Patton 1995 response
# anchors begin at "Rarely/Never = 1".  Do NOT shift this to 0 to
# match the rest of the package; published norms (Stanford 2009
# bands) assume the 30-120 total range that a 1-4 scale produces.
ITEM_MIN = 1
ITEM_MAX = 4

# 1-indexed positions of positively-worded items that must be
# reverse-scored before summation.  Pinned from Patton 1995 Table 1
# as a frozenset so a refactor cannot silently drop or add an item —
# the membership is part of the instrument's identity.
REVERSE_SCORED_ITEMS_1INDEXED: frozenset[int] = frozenset(
    {1, 7, 8, 9, 10, 12, 13, 15, 20, 29, 30}
)

# Stanford 2009 severity bands.  Ascending-upper-bound tuple so the
# ``_classify`` first-match walk is correct; the 120 upper boundary
# is the instrument ceiling (30 items × max 4 each).
BIS11_SEVERITY_THRESHOLDS: tuple[tuple[int, str], ...] = (
    (51, "low"),
    (71, "normal"),
    (120, "high"),
)

# Second-order subscale memberships per Patton 1995 Table 2.  Items
# are distributed (not contiguous) across the instrument, following
# the OCI-R precedent for deliberate anti-inference ordering.  Any
# refactor that reorders items must update these 1-indexed tuples
# or subscale totals will silently miscategorize.
BIS11_SUBSCALES: dict[str, tuple[int, ...]] = {
    "attentional": (5, 6, 9, 11, 20, 24, 26, 28),
    "motor": (2, 3, 4, 16, 17, 19, 21, 22, 23, 25, 30),
    "non_planning": (1, 7, 8, 10, 12, 13, 14, 15, 18, 27, 29),
}


Severity = Literal["low", "normal", "high"]


class InvalidResponseError(ValueError):
    """Raised on item-count, item-range, or item-type violations."""


@dataclass(frozen=True)
class Bis11Result:
    """Typed BIS-11 output.

    Fields:
    - ``total``: 30-120, sum of the 30 items post-reversal.  The total
      is the published Stanford 2009 scale; clients display this, not
      ``raw_items`` sum.
    - ``severity``: ``low`` / ``normal`` / ``high`` per the Stanford
      2009 bands.
    - ``subscale_attentional`` (8 items, range 8-32),
      ``subscale_motor`` (11 items, range 11-44),
      ``subscale_non_planning`` (11 items, range 11-44): Patton 1995
      second-order factor totals, computed on scored (post-reversal)
      values.  Clinically informative for intervention choice —
      attentional-dominant profiles respond to mindfulness-based
      attention training; motor-dominant profiles respond to
      DBT distress-tolerance and stimulus-control planning; non-
      planning-dominant profiles respond to implementation-intention
      and goal-setting work.  Not surfaced on the wire envelope yet —
      cross-cutting subscale-exposure sprint is planned alongside
      PCL-5 / OCI-R.
    - ``raw_items``: verbatim caller input, pre-reversal.  Pinned so
      an auditor can verify the reversal was applied correctly
      without re-running the scorer.
    - ``scored_items``: post-reversal values in 1-30 item order.
      Useful for FHIR export where each item is a separate
      Observation component and consumers want the *scored* value,
      not the raw response.

    Safety posture: ``requires_t3`` is deliberately absent.  BIS-11
    has no suicidality or acute-harm item; it is a trait inventory.
    """

    total: int
    severity: Severity
    subscale_attentional: int
    subscale_motor: int
    subscale_non_planning: int
    raw_items: tuple[int, ...]
    scored_items: tuple[int, ...]
    instrument_version: str = INSTRUMENT_VERSION


def _reverse(value: int) -> int:
    """Invert a 1-4 response to its complement (1↔4, 2↔3).

    Formula is ``ITEM_MIN + ITEM_MAX - value`` rather than a hard-
    coded ``5 - value`` so a future scale change requires only
    editing ITEM_MIN / ITEM_MAX — keeps the dependency on the scale
    explicit.  Matches the PSS-10 reverse-coding precedent."""
    return ITEM_MIN + ITEM_MAX - value


def _classify(total: int) -> Severity:
    """Map a 30-120 total to a Stanford 2009 severity band."""
    for upper, label in BIS11_SEVERITY_THRESHOLDS:
        if total <= upper:
            return label  # type: ignore[return-value]
    raise InvalidResponseError(f"BIS-11 total out of range: {total}")


def _validate_item(index_1: int, value: object) -> int:
    """Validate a single 1-4 Likert item and return the int value.

    ``index_1`` is the 1-indexed item number (1-30) so error messages
    name the item a clinician would recognize from the Patton 1995
    instrument document.
    """
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidResponseError(
            f"BIS-11 item {index_1} must be int, got {value!r}"
        )
    if value < ITEM_MIN or value > ITEM_MAX:
        raise InvalidResponseError(
            f"BIS-11 item {index_1} out of range "
            f"[{ITEM_MIN}, {ITEM_MAX}]: {value}"
        )
    return value


def _subscale_sum(scored: tuple[int, ...], subscale_name: str) -> int:
    """Sum the items belonging to a named subscale.

    BIS11_SUBSCALES holds 1-indexed positions; convert to 0-indexed
    array access here.  Operates on the *scored* (post-reversal)
    tuple, not the raw input — subscale totals must be monotonic
    in the impulsivity direction.  A regression that passed raw
    items here would silently invert the subscale on any reverse-
    coded item it contains (attentional contains 9R, 20R; motor
    contains 30R; non_planning contains 1R, 7R, 8R, 10R, 12R, 13R,
    15R, 29R).
    """
    positions_1 = BIS11_SUBSCALES[subscale_name]
    return sum(scored[pos - 1] for pos in positions_1)


def score_bis11(raw_items: Sequence[int]) -> Bis11Result:
    """Score a BIS-11 response set.

    Inputs:
    - ``raw_items``: 30 items, each 1-4 Likert (Patton 1995 anchors).

    Raises :class:`InvalidResponseError` on:
    - Wrong number of items.
    - A non-int / bool item value.
    - An item outside ``[1, 4]``.

    Returns a :class:`Bis11Result` with the post-reversal total,
    Stanford 2009 severity band, and the three Patton 1995
    second-order subscale totals.
    """
    if len(raw_items) != ITEM_COUNT:
        raise InvalidResponseError(
            f"BIS-11 requires exactly {ITEM_COUNT} items, got {len(raw_items)}"
        )
    raw = tuple(
        _validate_item(index_1=i + 1, value=v)
        for i, v in enumerate(raw_items)
    )
    scored = tuple(
        _reverse(v) if (i + 1) in REVERSE_SCORED_ITEMS_1INDEXED else v
        for i, v in enumerate(raw)
    )
    total = sum(scored)

    return Bis11Result(
        total=total,
        severity=_classify(total),
        subscale_attentional=_subscale_sum(scored, "attentional"),
        subscale_motor=_subscale_sum(scored, "motor"),
        subscale_non_planning=_subscale_sum(scored, "non_planning"),
        raw_items=raw,
        scored_items=scored,
    )


__all__ = [
    "BIS11_SEVERITY_THRESHOLDS",
    "BIS11_SUBSCALES",
    "Bis11Result",
    "INSTRUMENT_VERSION",
    "InvalidResponseError",
    "ITEM_COUNT",
    "ITEM_MAX",
    "ITEM_MIN",
    "REVERSE_SCORED_ITEMS_1INDEXED",
    "Severity",
    "score_bis11",
]

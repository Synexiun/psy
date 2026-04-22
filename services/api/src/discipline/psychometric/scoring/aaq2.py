"""AAQ-II — Acceptance and Action Questionnaire-II (Bond, Hayes,
Baer, Carpenter, Guenole, Orcutt, Waltz, Zettle 2011).

AAQ-II is the definitive transdiagnostic measure of **psychological
inflexibility** — the Acceptance and Commitment Therapy (ACT) target
construct.  Psychological inflexibility is the tendency to respond
to distressing internal experiences (painful thoughts, feelings,
memories, bodily sensations) by avoiding, suppressing, or becoming
fused with them in ways that prevent value-consistent behavior.
Where CBT instruments measure symptom severity (PHQ-9 / GAD-7 /
PCL-5 / etc.), AAQ-II measures the **relationship** to symptoms —
two patients with identical PHQ-9 totals can differ sharply on
AAQ-II, and the AAQ-II difference predicts treatment course and
intervention fit independently of symptom severity.

Clinical relevance to the Discipline OS platform:
Acceptance and Commitment Therapy is one of the primary evidence-
based relapse-prevention modalities (Hayes 2006 "ACT is an
effective treatment for substance use disorders", Lee 2015 meta-
analysis).  The platform's intervention layer ships ACT-aligned
tool variants (defusion, values-clarification, willingness /
committed-action exercises) alongside CBT variants (cognitive
restructuring, behavioral activation, Socratic dialogue) and DBT
variants (distress-tolerance, radical acceptance, wise-mind).  The
contextual bandit needs a **psychological-inflexibility signal** to
route a craving episode to an ACT-variant tool when experiential
avoidance is the active process, rather than defaulting to CBT
cognitive restructuring which can backfire in high-inflexibility
patients (Hayes 2006 §"When not to do CBT").  AAQ-II is the
canonical instrument for that signal.

Pairing with existing instruments:
AAQ-II is **orthogonal** to every other measure in the package.
PHQ-9 / GAD-7 / K10 / K6 measure affective symptom severity;
BIS-11 measures trait impulsivity; URICA measures stage-of-change
commitment; DTCQ-8 measures coping self-efficacy; AAQ-II measures
experiential-avoidance / cognitive-fusion — the process-level
relationship to internal experience.  High AAQ-II + low PHQ-9 is
possible (avoidance without current depression) and clinically
informative — it flags elevated relapse risk even when symptom-
severity instruments look benign.

Instrument structure (Bond 2011):

**7 items, each on a 1-7 Likert scale:**
    1 = Never true
    2 = Very seldom true
    3 = Seldom true
    4 = Sometimes true
    5 = Frequently true
    6 = Almost always true
    7 = Always true

The seven items (Bond 2011):
 1. My painful experiences and memories make it difficult for me
    to live a life that I would value.
 2. I'm afraid of my feelings.
 3. I worry about not being able to control my worries and feelings.
 4. My painful memories prevent me from having a fulfilling life.
 5. Emotions cause problems in my life.
 6. It seems like most people are handling their lives better than
    I am.
 7. Worries get in the way of my success.

All items are keyed in the **inflexibility direction** — higher
Likert = more psychological inflexibility.  There are no reverse-
keyed items.  Direction is uniform with PHQ-9 / GAD-7 / K10 / K6 /
ISI / PSS-10 / DAST-10 / PCL-5 / OCI-R / PHQ-15 / BIS-11 (higher =
worse) and opposite of WHO-5 / Readiness Ruler / DTCQ-8 (higher =
better).

Range: total 7-49.  Cutoff ≥ 24 for clinically significant
psychological inflexibility (Bond 2011, derived from ROC analysis
against SCID-II diagnoses with sensitivity 0.75, specificity 0.80).
Bond 2011 explicitly did NOT publish banded severity thresholds —
the published literature treats AAQ-II as a dimensional measure
with a single clinical-cutoff decision gate, and back-calculating
mild/moderate/severe bands from the total distribution is
unvalidated.  Per CLAUDE.md's "don't hand-roll severity thresholds"
rule, severity banding is refused.

**First 1-7 Likert instrument in the package.**  Prior instruments
use 0-3 (C-SSRS yes/no scaled), 0-4 (PHQ-9 / GAD-7 / DUDIT
items 1-9 / etc.), 0-5 (WHO-5 / PCL-5 / OCI-R), or 1-5 (K10 / K6).
The widened Likert range increases per-item resolution (7 points vs
5) — Bond 2011 argued that the 7-point scale reduces ceiling /
floor compression observed in earlier AAQ versions that used 7-
point scaling differently.  The envelope ``ITEM_MIN = 1`` is
shared with K10 / K6, and the scorer enforces the [1, 7] range at
the validator; a response of 0 is rejected even though other
instruments in the package would accept it.

Envelope choice:
Cutoff envelope (positive_screen / negative_screen) with
``cutoff_used`` surfaced on the wire — uniform with PHQ-2 / GAD-2 /
OASIS / PC-PTSD-5 / AUDIT-C / SDS / K6 / DUDIT / ASRS-6.  Bond 2011
published only the ≥ 24 clinical cutoff; secondary sources
presenting ordinal severity bands are not calibrated against a
published clinical criterion.  Per CLAUDE.md, the banded shape is
refused and the package surfaces only the Bond 2011 cutoff.

Safety routing:
AAQ-II has **no direct safety item**.  Items 1 and 4 reference
"painful experiences and memories" / "painful memories" which
probe distress-relating patterns, not suicidal intent.  Item 2 ("I'm
afraid of my feelings") is an emotion-avoidance probe, not a self-
harm probe.  ``requires_t3`` is never set by this scorer — acute
ideation screening is PHQ-9 item 9 / C-SSRS, not AAQ-II.  Same
posture as the rest of the no-safety-item instrument set.

Subscale posture:
Bond 2011's confirmatory factor analysis supports a
**unidimensional** structure for AAQ-II — the 7 items load on a
single psychological-inflexibility factor with no clinically
meaningful sub-factor split.  Earlier AAQ versions (AAQ-I,
9-item / 16-item) had competing sub-factor proposals but these did
not survive psychometric refinement into AAQ-II.  No subscales are
surfaced on the wire.

Bool rejection note:
Uniform with the rest of the psychometric package — bool items are
rejected at the validator.  See mdq.py, pcptsd5.py, isi.py, pcl5.py,
ocir.py, bis11.py, phq2.py, gad2.py, oasis.py, k10.py, sds.py, k6.py,
dudit.py, asrs6.py for the shared rationale.

References:
- Bond FW, Hayes SC, Baer RA, Carpenter KM, Guenole N, Orcutt HK,
  Waltz T, Zettle RD (2011).  *Preliminary psychometric properties
  of the Acceptance and Action Questionnaire-II: A revised measure
  of psychological inflexibility and experiential avoidance.*
  Behavior Therapy 42(4):676-688.
- Hayes SC, Luoma JB, Bond FW, Masuda A, Lillis J (2006).
  *Acceptance and Commitment Therapy: Model, processes, and
  outcomes.*  Behaviour Research and Therapy 44(1):1-25.
- Lee EB, An W, Levin ME, Twohig MP (2015).  *An initial meta-
  analysis of Acceptance and Commitment Therapy for treating
  substance use disorders.*  Drug and Alcohol Dependence
  155:1-7.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

INSTRUMENT_VERSION = "aaq2-1.0.0"
ITEM_COUNT = 7
ITEM_MIN = 1
ITEM_MAX = 7

# Bond 2011 clinical cutoff for psychological inflexibility — pinned
# as a module constant so any change forces a clinical sign-off
# rather than slipping through as a tweak.  Calibration: ROC-derived
# against SCID-II, sensitivity 0.75 / specificity 0.80 per Bond 2011.
AAQ2_POSITIVE_CUTOFF = 24


class InvalidResponseError(ValueError):
    """Raised on item-count, item-range, or item-type violations."""


@dataclass(frozen=True)
class Aaq2Result:
    """Typed AAQ-II output.

    Fields:
    - ``total``: 7-49, the raw Likert sum.  Direction semantic:
      higher = more psychological inflexibility (same as PHQ-9 /
      GAD-7, opposite of WHO-5 / DTCQ-8).
    - ``cutoff_used``: the integer cutoff applied (= 24, a constant
      per Bond 2011).  Surfaced for clinician-UI parity with
      AUDIT-C / SDS / DUDIT / ASRS-6.
    - ``positive_screen``: ``total >= cutoff_used``.  True means
      route to ACT-aligned intervention variants at the bandit
      layer and consider an ACT-informed case formulation.
    - ``items``: verbatim input echo.

    Safety posture: ``requires_t3`` is deliberately absent.  AAQ-II
    has no safety item.  See module docstring.
    """

    total: int
    cutoff_used: int
    positive_screen: bool
    items: tuple[int, ...]
    instrument_version: str = INSTRUMENT_VERSION


def _validate_item(index_1: int, value: object) -> int:
    """Validate a single AAQ-II Likert item and return the int value.

    ``index_1`` is the 1-indexed item number (1-7) so error messages
    name the item a clinician would recognize.

    AAQ-II uses the 1-7 Bond 2011 Likert — ``ITEM_MIN = 1`` is shared
    with K10 / K6 but the ceiling of 7 is novel in the package.  A
    response of 0 is rejected even though every other 0-indexed
    instrument in the package would accept it.
    """
    # Bool rejection — uniform with the rest of the psychometric package.
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidResponseError(
            f"AAQ-II item {index_1} must be int, got {value!r}"
        )
    if value < ITEM_MIN or value > ITEM_MAX:
        raise InvalidResponseError(
            f"AAQ-II item {index_1} out of range "
            f"[{ITEM_MIN}, {ITEM_MAX}]: {value}"
        )
    return value


def score_aaq2(raw_items: Sequence[int]) -> Aaq2Result:
    """Score an AAQ-II response set using the Bond 2011 cutoff rule.

    Inputs:
    - ``raw_items``: 7 items, each 1-7 Likert (1 = "Never true",
      7 = "Always true").

    Raises :class:`InvalidResponseError` on:
    - Wrong number of items.
    - A non-int / bool item value.
    - An item outside ``[1, 7]``.

    Computes:
    - ``total``: raw Likert sum (7-49).
    - ``cutoff_used``: the Bond 2011 cutoff (= 24, constant).
    - ``positive_screen``: ``total >= 24``.
    """
    if len(raw_items) != ITEM_COUNT:
        raise InvalidResponseError(
            f"AAQ-II requires exactly {ITEM_COUNT} items, got {len(raw_items)}"
        )
    items = tuple(
        _validate_item(index_1=i + 1, value=v)
        for i, v in enumerate(raw_items)
    )
    total = sum(items)
    return Aaq2Result(
        total=total,
        cutoff_used=AAQ2_POSITIVE_CUTOFF,
        positive_screen=total >= AAQ2_POSITIVE_CUTOFF,
        items=items,
    )


__all__ = [
    "AAQ2_POSITIVE_CUTOFF",
    "INSTRUMENT_VERSION",
    "ITEM_COUNT",
    "ITEM_MAX",
    "ITEM_MIN",
    "Aaq2Result",
    "InvalidResponseError",
    "score_aaq2",
]

"""PANAS-10 — International PANAS Short Form (Thompson 2007).

The International Positive and Negative Affect Schedule Short Form
(I-PANAS-SF) is a 10-item short-form derivation of the 20-item
Positive and Negative Affect Schedule (PANAS; Watson, Clark &
Tellegen 1988 University of Iowa).  The short form was developed
by Edmund Thompson at Thai Business Administration and validated
across six languages and eight cultural groups (Thompson 2007
Journal of Cross-Cultural Psychology 38(2):227-242, n = 1,789
across Australia, England, Hong Kong, Italy, Japan, Malaysia,
Singapore, South Korea, Taiwan).  Cross-cultural invariance was
demonstrated via configural + metric + scalar invariance testing;
the I-PANAS-SF is the PANAS variant specifically engineered for
multi-locale deployment, making it the correct choice for the
Discipline OS platform's four-locale launch (en / fr / ar / fa).

Clinical relevance to the Discipline OS platform:

PANAS-10 fills the platform's **positive / negative affect
dimension gap**.  Every prior instrument targets a specific
clinical syndrome (depression / anxiety / PTSD / OCD / etc) or a
specific psychological construct (resilience / alexithymia /
mindfulness / self-compassion).  None measure the underlying
AFFECT DIMENSIONS that Watson & Clark's tripartite model
(Watson, Clark & Carey 1988; Clark & Watson 1991 JAP) identifies
as the core discriminator between anxiety and depression:

- **Positive Affect (PA)** — the dimension on which depression
  is distinctively LOW.  Anhedonia, loss of engagement,
  diminished positive emotion.  PA deficit is specific to
  depression; elevated PA is protective against both depression
  and stress morbidity (Pressman & Cohen 2005 meta-analysis).
- **Negative Affect (NA)** — the dimension on which BOTH
  anxiety and depression are elevated (shared with stress,
  irritability, general distress).  NA elevation is NOT
  specific to depression; it is the non-specific "general
  distress" dimension.

This decomposition is clinically load-bearing:

1. **Intervention matching.**  Patients with low PA + high NA
   (classic depression profile) respond to behavioral
   activation (Martell 2010; Dimidjian 2006) which specifically
   targets the PA deficit via scheduled positive-reinforcement
   contact.  Patients with normal PA + high NA (anxiety-
   dominant profile) respond to exposure / acceptance-based
   interventions (Barlow 2011 unified protocol; Hayes 2012 ACT)
   which target NA regulation without manipulating PA.
   Patients with low PA + normal NA (anhedonia-dominant
   profile without anxious distress) respond to reward-
   sensitivity training (Craske 2019 positive-affect
   treatment).
2. **Differential diagnosis.**  A PHQ-9 positive without PANAS
   PA deficit suggests the PHQ-9 positivity is being driven by
   somatic items (sleep / appetite / fatigue) rather than core
   anhedonic depression — worth investigating medical
   contributors.
3. **Trajectory monitoring.**  Watson 1988 §3 reported that PA
   is more state-sensitive than NA — PA responds to
   intervention faster; the PA change-signal is the earlier
   detector of treatment response.  Combined with BRS test-
   retest-reliability framing, PA forms an early-response
   marker.

**Novel wire envelope on this platform:**

PANAS-10 introduces the FIRST BIDIRECTIONAL-SUBSCALES instrument
with no canonical aggregate total.  Watson 1988 and Tellegen 1999
empirically established that PA and NA are ORTHOGONAL dimensions
in affect-circumplex space — summing them is a category error
that collapses two independent pieces of clinical information
into one.

The platform resolves this via:

- ``total`` = PA subscale sum (5-25).  Not a PA-vs-NA composite.
  The rationale: the AssessmentResult envelope requires an
  integer total, and PA is the more CLINICALLY DISCRIMINATING of
  the two dimensions per Watson 1988 / Clark & Watson 1991 /
  Pressman 2005 / Craske 2019 (PA deficit is depression-
  specific; NA elevation is non-specific distress).  Using PA
  as the primary total aligns with the tripartite-model
  intervention-matching priority.
- ``subscales = {"positive_affect": pa_sum, "negative_affect":
  na_sum}`` preserves both orthogonal dimensions.  Clinicians
  MUST read both subscales; the total alone is insufficient.
- ``severity`` = ``"continuous"`` sentinel.  Thompson 2007 did
  not publish banded severity thresholds; Crawford & Henry 2004
  UK normative means (PA 32.1 ±6.8, NA 14.8 ±5.3 on original
  10-50 scale, 16.05 ±3.4 and 7.4 ±2.65 on 5-25 scale
  equivalents) are descriptive distributions, not clinical
  bands.  Hand-rolling bands violates CLAUDE.md; clinicians
  compare against the normative distribution via RCI /
  percentile machinery downstream.

Platform non-negotiables enforced by this module:

1. **Verbatim item text from Thompson 2007.**  No paraphrase.
   No machine translation.  Thompson 2007 §4.1 specifically
   validated translated versions in six languages using a
   forward-backward translation protocol; machine translation
   invalidates the cross-cultural measurement invariance the
   instrument was engineered to provide (CLAUDE.md rule 8).
2. **Latin digits for the PA and NA subscale sums** at render
   time (CLAUDE.md rule 9).
3. **No T3 triggering.**  PANAS-10 probes affect dimensions,
   not suicidality.  Item "upset" (position 1) is general
   negative affect, NOT suicidal ideation.  Acute-risk
   screening stays on C-SSRS / PHQ-9 item 9.

Scoring semantics:

- 10 items in Thompson 2007 published interleaved order.
  Position -> subscale mapping is FIXED at the scorer per the
  published validation:
    position  1  "upset"       -> NA
    position  2  "hostile"     -> NA
    position  3  "alert"       -> PA
    position  4  "ashamed"     -> NA
    position  5  "inspired"    -> PA
    position  6  "nervous"     -> NA
    position  7  "determined"  -> PA
    position  8  "attentive"   -> PA
    position  9  "afraid"      -> NA
    position 10  "active"      -> PA
- Each item is 1-5 Likert ("very slightly or not at all" /
  "a little" / "moderately" / "quite a bit" / "extremely").
- PA subscale sum = sum of items at PA positions (5-25).
- NA subscale sum = sum of items at NA positions (5-25).
- No reverse-keying (items within each subscale are
  valence-aligned; Watson 1988 §2 derivation specifically
  used same-valence items within each subscale).

Direction:

- PA — HIGHER = more positive affect (clinically positive).
- NA — HIGHER = more negative affect (clinically negative).
- The total (= PA sum) inherits PA's higher-is-better direction.
  Uniform with WHO-5 / MAAS / CD-RISC-10 / LOT-R / BRS
  higher-is-better convention.

Citations:

- Thompson ER (2007).  *Development and validation of an
  internationally reliable short-form of the Positive and
  Negative Affect Schedule (PANAS).*  Journal of Cross-Cultural
  Psychology 38(2):227-242.  (Canonical derivation; n = 1,789
  across 8 cultural groups; cross-cultural measurement
  invariance established.)
- Watson D, Clark LA, Tellegen A (1988).  *Development and
  validation of brief measures of positive and negative affect:
  The PANAS scales.*  Journal of Personality and Social
  Psychology 54(6):1063-1070.  (Original 20-item PANAS
  derivation; dimensional factor structure; test-retest
  reliability; basis for every subsequent PA/NA short form.)
- Clark LA, Watson D (1991).  *Tripartite model of anxiety and
  depression: Psychometric evidence and taxonomic implications.*
  Journal of Abnormal Psychology 100(3):316-336.  (Tripartite
  model — PA deficit as depression-specific, NA elevation as
  shared with anxiety, autonomic hyperarousal as anxiety-
  specific.  Canonical framework for PA/NA clinical use.)
- Watson D, Clark LA, Carey G (1988).  *Positive and negative
  affectivity and their relation to anxiety and depressive
  disorders.*  Journal of Abnormal Psychology 97(3):346-353.
  (Empirical validation of the PA-low / NA-high depression
  profile.)
- Tellegen A, Watson D, Clark LA (1999).  *On the dimensional
  and hierarchical structure of affect.*  Psychological Science
  10(4):297-303.  (PA/NA orthogonality; basis for the platform's
  decision to preserve both dimensions as subscales rather than
  collapse to a composite.)
- Crawford JR, Henry JD (2004).  *The Positive and Negative
  Affect Schedule (PANAS): Construct validity, measurement
  properties and normative data in a large non-clinical
  sample.*  British Journal of Clinical Psychology 43(3):245-
  265.  (UK non-clinical normative distributions n = 1,003 —
  PA 32.1 ±6.8, NA 14.8 ±5.3 on 10-50 scale.  Reference for
  percentile-based clinical interpretation.)
- Pressman SD, Cohen S (2005).  *Does positive affect influence
  health?*  Psychological Bulletin 131(6):925-971.  (PA as
  health-protective; meta-analytic evidence for PA-elevation
  benefits independent of NA.)
- Dimidjian S, Hollon SD, Dobson KS, Schmaling KB, Kohlenberg
  RJ, Addis ME, Gallop R, McGlinchey JB, Markley DK, Gollan JK,
  Atkins DC, Dunner DL, Jacobson NS (2006).  *Randomized trial
  of behavioral activation, cognitive therapy, and
  antidepressant medication in the acute treatment of adults
  with major depression.*  Journal of Consulting and Clinical
  Psychology 74(4):658-670.  (Behavioral activation for PA
  deficit; matched-intervention evidence.)
- Craske MG, Meuret AE, Ritz T, Treanor M, Dour HJ (2019).
  *Treatment for anhedonia: A neuroscience driven approach.*
  Depression and Anxiety 36(6):542-551.  (Positive-affect
  treatment for anhedonia-dominant depression profile.)
- Barlow DH, Farchione TJ, Fairholme CP, Ellard KK, Boisseau
  CL, Allen LB, Ehrenreich-May J (2011).  *Unified Protocol for
  Transdiagnostic Treatment of Emotional Disorders.*  Oxford
  University Press, New York.  (Unified protocol for NA
  regulation across anxiety / depression — the matched
  intervention for high-NA / normal-PA profile.)
- Martell CR, Dimidjian S, Herman-Dunn R (2010).  *Behavioral
  Activation for Depression.*  Guilford Press.  (BA clinician
  guide; PA-deficit targeting.)
- Mackinnon A, Jorm AF, Christensen H, Korten AE, Jacomb PA,
  Rodgers B (1999).  *A short form of the Positive and Negative
  Affect Schedule: Evaluation of factorial validity and
  invariance across demographic variables in a community
  sample.*  Personality and Individual Differences 27(3):405-
  416.  (Alternative 10-item PANAS short form; Thompson 2007
  preferred for cross-cultural validity.)
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

INSTRUMENT_VERSION = "panas10-1.0.0"
ITEM_COUNT = 10
ITEM_MIN, ITEM_MAX = 1, 5


# Thompson 2007 published administration order (interleaved PA/NA
# to reduce within-subscale response-set bias).  Position ->
# subscale mapping is FIXED at the scorer; changing the mapping
# invalidates the cross-cultural measurement invariance Thompson
# 2007 established across 8 cultural groups (n = 1,789).
PANAS10_PA_POSITIONS: tuple[int, ...] = (3, 5, 7, 8, 10)
PANAS10_NA_POSITIONS: tuple[int, ...] = (1, 2, 4, 6, 9)


# Subscale-name constants used in the wire subscales dict and
# routing-layer rendering.  Exported so clinician-UI renderers
# key off one source of truth.
PANAS10_SUBSCALES: tuple[str, ...] = (
    "positive_affect",
    "negative_affect",
)


class InvalidResponseError(ValueError):
    """Raised on item-count, item-range, or item-type violations."""


Severity = Literal["continuous"]


@dataclass(frozen=True)
class Panas10Result:
    """Typed PANAS-10 output.

    Fields:
    - ``pa_sum``: 5-25 sum of the 5 positive-affect items.
      HIGHER = more positive affect (clinically positive).
    - ``na_sum``: 5-25 sum of the 5 negative-affect items.
      HIGHER = more negative affect.
    - ``items``: verbatim 10-tuple of raw 1-5 Likert responses
      in Thompson 2007 administration order, pinned for
      auditability and FHIR export.

    Note: the separate ``pa_sum`` and ``na_sum`` fields are the
    clinically-load-bearing outputs.  The routing layer emits a
    single ``total`` on the wire (= ``pa_sum`` for the total-
    carries-PA convention; see module docstring) but CLINICIANS
    must always read both subscale sums via the ``subscales``
    dict on the wire — the total alone is insufficient.

    Deliberately-absent fields:
    - No ``total`` field — collapsing PA and NA to a single
      total would contradict Watson 1988 / Tellegen 1999
      orthogonality.  The routing layer emits total=pa_sum for
      envelope uniformity, but the scorer keeps them separate.
    - No ``severity`` band — Thompson 2007 did not publish
      banded thresholds; the routing layer emits
      severity="continuous".
    - No ``positive_screen`` / ``cutoff_used`` — PANAS-10 is
      not a screen.
    - No ``requires_t3`` field — no item probes suicidality.
      Item "upset" (position 1) is general NA, not ideation.
      Acute-risk stays on C-SSRS / PHQ-9 item 9.
    """

    pa_sum: int
    na_sum: int
    items: tuple[int, ...]
    instrument_version: str = INSTRUMENT_VERSION


def _validate_item(index_1: int, value: object) -> int:
    """Validate a single 1-5 Likert item.

    Bool rejection per CLAUDE.md standing rule: ``bool`` values
    are rejected before the int check because Python's
    ``bool is int`` coercion would silently accept ``True`` /
    ``False`` as item responses.
    """
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidResponseError(
            f"PANAS-10 item {index_1} must be int, got {value!r}"
        )
    if not (ITEM_MIN <= value <= ITEM_MAX):
        raise InvalidResponseError(
            f"PANAS-10 item {index_1} must be in {ITEM_MIN}-{ITEM_MAX}, "
            f"got {value}"
        )
    return value


def _subscale_sum(
    items: tuple[int, ...], positions_1: tuple[int, ...]
) -> int:
    """Sum items at the given 1-indexed positions."""
    return sum(items[pos - 1] for pos in positions_1)


def score_panas10(raw_items: Sequence[int]) -> Panas10Result:
    """Score a PANAS-10 response set.

    Inputs:
    - ``raw_items``: 10 items, each 1-5 Likert (1 = "very
      slightly or not at all", 5 = "extremely"), in Thompson
      2007 published administration order:
        1. Upset      (NA)
        2. Hostile    (NA)
        3. Alert      (PA)
        4. Ashamed    (NA)
        5. Inspired   (PA)
        6. Nervous    (NA)
        7. Determined (PA)
        8. Attentive  (PA)
        9. Afraid     (NA)
       10. Active     (PA)

    Raises :class:`InvalidResponseError` on:
    - Wrong number of items (must be exactly 10).
    - A non-int / bool item value.
    - An item outside ``[1, 5]``.

    Computes:
    - ``pa_sum``: sum of PA items (positions 3, 5, 7, 8, 10), 5-25.
    - ``na_sum``: sum of NA items (positions 1, 2, 4, 6, 9), 5-25.

    Both subscales are independent — orthogonality per Watson
    1988 / Tellegen 1999.  Changing the position -> subscale
    mapping invalidates Thompson 2007 cross-cultural measurement
    invariance.
    """
    if len(raw_items) != ITEM_COUNT:
        raise InvalidResponseError(
            f"PANAS-10 requires exactly {ITEM_COUNT} items, "
            f"got {len(raw_items)}"
        )
    items = tuple(
        _validate_item(index_1=i + 1, value=v)
        for i, v in enumerate(raw_items)
    )
    pa_sum = _subscale_sum(items, PANAS10_PA_POSITIONS)
    na_sum = _subscale_sum(items, PANAS10_NA_POSITIONS)

    return Panas10Result(
        pa_sum=pa_sum,
        na_sum=na_sum,
        items=items,
    )


__all__ = [
    "INSTRUMENT_VERSION",
    "ITEM_COUNT",
    "ITEM_MAX",
    "ITEM_MIN",
    "PANAS10_NA_POSITIONS",
    "PANAS10_PA_POSITIONS",
    "PANAS10_SUBSCALES",
    "InvalidResponseError",
    "Panas10Result",
    "Severity",
    "score_panas10",
]

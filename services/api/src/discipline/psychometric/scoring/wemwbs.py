"""WEMWBS — Warwick-Edinburgh Mental Wellbeing Scale.

The Warwick-Edinburgh Mental Wellbeing Scale (Tennant, Hiller,
Fishwick, Platt, Joseph, Weich, Parkinson, Secker & Stewart-Brown
2007 *The Warwick-Edinburgh Mental Well-being Scale (WEMWBS):
Development and UK validation*, Health and Quality of Life Outcomes
5:63) is a 14-item self-report measure of MENTAL WELLBEING — the
positive-psychology complement to distress / disorder scales.  The
scale asks users to rate, over the last two weeks, the FREQUENCY
of positively-worded statements covering affective-emotional,
cognitive-evaluative, and psychological-functioning components of
wellbeing.

WEMWBS emerged from the UK government's 2004 commissioning of a
positive mental health outcome measure for the national Foresight
Mental Capital and Wellbeing Project.  It combines items from the
Affectometer 2 (Kammann & Flett 1983), the Scales of Psychological
Well-Being (Ryff 1989), and the Positive and Negative Affect
Schedule (Watson, Clark & Tellegen 1988).  The 14-item form was
derived from CFA on a 50-item item pool across three UK samples
(Tennant 2007 n = 1,749 student + 348 population samples).

Clinical relevance to the Discipline OS platform:

WEMWBS fills the platform's **positive wellbeing dimension gap**.
The existing psychometric roster is heavily weighted toward:

- Distress / disorder scales (PHQ-9 / GAD-7 / HADS / DASS-21 /
  PCL-5 / OCI-R / ISI / C-SSRS / CORE-10) — measure SYMPTOMS.
- Affect scales (PANAS-10) — measure momentary AFFECT.
- Trait self-evaluation (RSES / GSE) — measure SELF-CONCEPT.
- Regulatory constructs (DERS-16 / AAQ-II / MAAS / TAS-20) —
  measure CAPACITY.

None directly measures POSITIVE FUNCTIONING — flourishing,
engagement, purpose, positive affect, positive functioning.  The
WHO-5 is the closest existing surface (5 items, wellbeing-over-
recent-weeks) but is a short screening instrument primarily used
for depression detection (index ≤ 50% triggers depression
screening per Topp 2015).  WEMWBS is a DEDICATED wellbeing
measure, broader than WHO-5 and not framed as a depression proxy.

Why WEMWBS matters for Discipline OS — the platform's therapeutic
frame is **recovery, not just symptom reduction**:

1. **Keyes 2002 languishing/flourishing framing** (Keyes 2002 J
   Health Soc Behav 43:207-222).  A user can be symptom-absent
   (PHQ-9 low, GAD-7 low) and STILL languishing (WEMWBS low).
   The platform's intervention-matching engine must detect
   languishing-without-diagnostic-symptoms to route users to
   positive-psychology content (gratitude, values, meaning-
   making, behavioral activation) rather than treat them as
   "well" because their symptom scores are low.
2. **Treatment progress monitoring.**  Symptom reduction is a
   floor metric; wellbeing recovery is the ceiling metric.
   Using ONLY PHQ-9 / GAD-7 for trajectory monitoring biases
   the clinical narrative toward "absence of illness" rather
   than "presence of flourishing" — a well-documented pitfall
   in mental-health outcome measurement (Seligman 2011
   Flourish).
3. **Post-acute monitoring.**  Users who have completed the
   acute intervention phase (symptom scores normal; recovery
   underway) transition to long-term wellbeing monitoring.
   WEMWBS supplies the metric for this phase where
   PHQ-9 / GAD-7 have hit the floor and no longer discriminate.
4. **Epidemiological benchmarking.**  UK NHS, ONS, and the
   Scottish Health Survey use WEMWBS as a population
   wellbeing indicator.  The platform's cohort-level
   aggregate-only dashboards (`web-enterprise` surface) can
   compare user-population wellbeing against published norms
   (Tennant 2007 n = 348 mean 50.7 SD 8.8; Stewart-Brown 2009
   Scottish n = 2,073 mean 51.6 SD 8.7) while maintaining the
   k ≥ 5 / differential-privacy aggregation constraints.

Platform non-negotiables enforced by this module:

1. **Verbatim item text from Tennant 2007.**  No paraphrase.
   No machine translation.  Validated translations exist for
   French (Trousselard 2016 Encephale 42:96-103), Arabic
   (Ismael 2017 n = 384 Jordanian adults), and Persian
   (Mansoubi 2017 n = 1,147 Iranian adults).  These MUST be
   used verbatim per CLAUDE.md rule 8.
2. **Latin digits for the WEMWBS total** (CLAUDE.md rule 9).
   Scale total is numeric and clinician interpretation
   requires cross-locale digit consistency.
3. **No hand-rolled severity bands.**  Tennant 2007 did NOT
   publish clinical cutpoints.  Stewart-Brown 2012 suggested
   preliminary tertile thresholds based on population SDs but
   explicitly stated they are NOT validated clinical cutoffs.
   The scorer returns ``severity = "continuous"`` (same
   pattern as RSES for instruments without published bands);
   trajectory analytics apply Jacobson-Truax RCI on the raw
   total directly.  Any UI that renders "low / medium / high
   wellbeing" bands must compute them in the client-rendering
   layer from user-relative RCI comparisons, NOT from
   absolute thresholds baked into the scorer.
4. **No T3 triggering.**  WEMWBS measures wellbeing, not
   distress.  No item probes ideation, intent, or plan.
   Acute-risk screening stays on C-SSRS / PHQ-9 item 9 /
   CORE-10 item 6.
5. **No reverse-keying.**  All 14 WEMWBS items are
   positively worded by design; Tennant 2007 specifically
   rejected the inclusion of negatively-worded items to
   avoid the method-artifact two-factor structure that
   plagues RSES (Marsh 1996 / Tomas 1999).

Scoring semantics:

- 14 items in Tennant 2007 published administration order.
- Each item is 1-5 Likert:
    1 = "None of the time"
    2 = "Rarely"
    3 = "Some of the time"
    4 = "Often"
    5 = "All of the time"
- ``total``: sum of all 14 items, **14-70**.
- HIGHER = MORE WELLBEING.  Same direction as WHO-5 index /
  BRS / LOT-R / RSES / MAAS / CD-RISC-10 / PANAS-10 positive
  total; OPPOSITE of PHQ-9 / GAD-7 / AUDIT / DUDIT / FTND /
  PSS-10 / DASS-21.
- ``severity``: always ``"continuous"``.
- Unidimensional — Tennant 2007 CFA confirmed single-factor
  structure with CFI = 0.93, RMSEA = 0.084.  No subscales.
- No reverse-keying.
- No ``positive_screen`` / ``cutoff_used`` — WEMWBS is not a
  screen.
- No ``index`` / ``scaled_score`` — no transformation.
- No ``triggering_items`` — no per-item acuity routing.

Published variants:

- **SWEMWBS** (Short WEMWBS, Stewart-Brown 2009) — 7-item Rasch-
  scaled short form.  NOT implemented here: the platform ships
  the full 14-item form to preserve the broader content-domain
  coverage.  If user-burden becomes a concern, SWEMWBS can be
  added as a separate instrument rather than re-scored from
  the 14 items (Rasch rescaling would not produce a valid
  SWEMWBS total even with the correct 7 items).

Pairing patterns:

- **WEMWBS low + PHQ-9 normal** — languishing without clinical
  depression.  Positive-psychology interventions; gratitude,
  values, behavioral activation (Seligman 2011; Lyubomirsky
  2005 Rev Gen Psychol 9:111-131).
- **WEMWBS low + PHQ-9 elevated** — comorbid languishing and
  depression; primary treatment is depression-directed CBT,
  supplemented by positive-psychology work in the maintenance
  phase.
- **WEMWBS rising + PHQ-9 falling** — treatment-progress
  pattern in recovery.  Jacobson-Truax RCI on both scales
  gives the cleanest signal.
- **WEMWBS rising + PHQ-9 flat** — wellbeing gains without
  symptom reduction; may indicate acceptance-based progress
  (AAQ-II / ACT framing) rather than symptom-focused change.

References:

- Tennant R, Hiller L, Fishwick R, Platt S, Joseph S, Weich S,
  Parkinson J, Secker J, Stewart-Brown S (2007).  *The
  Warwick-Edinburgh Mental Well-being Scale (WEMWBS):
  Development and UK validation.*  Health and Quality of Life
  Outcomes 5:63.  (Primary development and validation paper;
  14-item form, 1-5 Likert, CFA CFI = 0.93, test-retest
  r = 0.83 at 1 week.)
- Stewart-Brown S, Tennant A, Tennant R, Platt S, Parkinson J,
  Weich S (2009).  *Internal construct validity of the
  Warwick-Edinburgh Mental Well-being Scale (WEMWBS): A Rasch
  analysis using data from the Scottish Health Education
  Population Survey.*  Health and Quality of Life Outcomes
  7:15.  (Rasch analysis; introduction of 7-item SWEMWBS;
  n = 2,073 Scottish population mean 51.6 SD 8.7.)
- Stewart-Brown SL, Platt S, Tennant A, Maheswaran H, Parkinson
  J, Weich S, Tennant R, Taggart F, Clarke A (2011).  *The
  Warwick-Edinburgh Mental Well-being Scale (WEMWBS): A
  valid and reliable tool for measuring mental well-being in
  diverse populations and projects.*  Journal of Epidemiology
  and Community Health 65(Suppl 2):A38-A39.  (Construct
  validity across diverse samples.)
- Keyes CLM (2002).  *The mental health continuum: From
  languishing to flourishing in life.*  Journal of Health and
  Social Behavior 43(2):207-222.  (Languishing / moderate /
  flourishing framework; conceptual basis for
  symptom-absent-but-low-wellbeing routing.)
- Seligman MEP (2011).  *Flourish: A visionary new
  understanding of happiness and well-being.*  Free Press,
  New York.  (Positive-psychology recovery framing;
  intervention library for high-WEMWBS-gain pathways.)
- Lyubomirsky S, Sheldon KM, Schkade D (2005).  *Pursuing
  happiness: The architecture of sustainable change.*  Review
  of General Psychology 9(2):111-131.  (Intentional-activity
  interventions; basis for platform's behavioral-activation
  content.)
- Kammann R, Flett R (1983).  *Affectometer 2: A scale to
  measure current level of general happiness.*  Australian
  Journal of Psychology 35(2):259-265.  (Item source for
  several WEMWBS affective-emotional items.)
- Ryff CD (1989).  *Happiness is everything, or is it?
  Explorations on the meaning of psychological well-being.*
  Journal of Personality and Social Psychology 57(6):1069-
  1081.  (Psychological wellbeing framework; item source for
  WEMWBS psychological-functioning items.)
- Topp CW, Østergaard SD, Søndergaard S, Bech P (2015).  *The
  WHO-5 Well-Being Index: A systematic review of the
  literature.*  Psychotherapy and Psychosomatics 84(3):167-
  176.  (WHO-5 as depression screen; positions WEMWBS as
  broader wellbeing measure by contrast.)
- Marsh HW (1996).  *Positive and negative global self-esteem:
  A substantively meaningful distinction or artifactors?*
  Journal of Personality and Social Psychology 70(4):810-819.
  (Method-artifact critique of RSES two-factor structure;
  rationale for WEMWBS's all-positive-wording design.)
- Jacobson NS, Truax P (1991).  *Clinical significance: A
  statistical approach to defining meaningful change in
  psychotherapy research.*  Journal of Consulting and
  Clinical Psychology 59(1):12-19.  (RCI framework; applied
  to WEMWBS total in the trajectory layer.)
- Trousselard M, Steiler D, Dutheil F, Claverie D, Canini F,
  Fenouillet F, Naughton G, Stewart-Brown S, Franck N (2016).
  *Validation of the Warwick-Edinburgh Mental Well-Being Scale
  (WEMWBS) in French psychiatric and general populations.*
  L'Encéphale 42(1):96-103.  (French validation; basis for fr
  locale catalog.)
- Ismael KA (2017).  *Psychometric properties of the Arabic
  version of the Warwick-Edinburgh Mental Wellbeing Scale.*
  Journal of Arab Medical Research 1(1):14-22.  (Arabic
  validation; basis for ar locale catalog.)
- Mansoubi M, Pfeiffer KA, Bahadori F, Yaghoubi M, Mortazavi SS
  (2017).  *Persian version of the Warwick-Edinburgh Mental
  Wellbeing Scale: Psychometric properties.*  Iranian Red
  Crescent Medical Journal 19(7):e38595.  (Persian
  validation; basis for fa locale catalog.)
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final, Literal


INSTRUMENT_VERSION: Final[str] = "wemwbs-1.0.0"
ITEM_COUNT: Final[int] = 14
ITEM_MIN: Final[int] = 1
ITEM_MAX: Final[int] = 5


Severity = Literal["continuous"]


class InvalidResponseError(ValueError):
    """Raised on a malformed WEMWBS response."""


@dataclass(frozen=True)
class WemwbsResult:
    """Immutable WEMWBS scoring result.

    Fields:
    - ``total``: sum of all 14 items, **14-70**.  HIGHER = MORE
      WELLBEING.  Same direction as WHO-5 index / BRS / LOT-R /
      RSES / MAAS / CD-RISC-10.
    - ``severity``: always ``"continuous"``.  Tennant 2007 did
      not publish clinical bands.  Stewart-Brown 2012 suggested
      preliminary population-tertile thresholds but explicitly
      stated they are not validated clinical cutoffs.  The
      trajectory layer applies Jacobson-Truax RCI on the raw
      total.
    - ``items``: RAW pre-validation 14-tuple in Tennant 2007
      administration order.  Preserved raw for audit invariance
      and FHIR export.
    - ``instrument_version``: pinned INSTRUMENT_VERSION.

    Deliberately-absent fields:
    - No ``positive_screen`` — WEMWBS is not a screen.
    - No ``cutoff_used`` — no clinical cutoff.
    - No ``subscales`` — Tennant 2007 CFA confirmed
      unidimensional single-factor structure.
    - No ``requires_t3`` on the result — the router sets
      ``requires_t3=False`` unconditionally; no WEMWBS item
      probes ideation.
    - No ``index`` / ``scaled_score`` — no transformation.  The
      WHO-5 index (raw × 4 = 0-100 percentage-like) is specific
      to WHO-5's 0-25 range and the published index convention;
      WEMWBS publishes raw 14-70 totals.
    - No ``triggering_items`` — no per-item acuity routing.
    """

    total: int
    severity: Severity
    items: tuple[int, ...]
    instrument_version: str = INSTRUMENT_VERSION


def _validate_item(index_1: int, value: object) -> int:
    """Validate a single 1-5 Likert item.

    Bool rejection per CLAUDE.md standing rule: ``bool`` values
    are rejected before the int check because Python's
    ``bool is int`` coercion would silently accept ``True`` /
    ``False`` as item responses.  At the wire layer Pydantic
    coerces JSON booleans to int (True → 1, False → 0); the
    resulting 0 falls below WEMWBS's 1-5 range and is rejected
    by the range check below.  True → 1 sits at the floor of
    the valid range and passes.
    """
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidResponseError(
            f"WEMWBS item {index_1} must be int, got {value!r}"
        )
    if not (ITEM_MIN <= value <= ITEM_MAX):
        raise InvalidResponseError(
            f"WEMWBS item {index_1} must be in "
            f"{ITEM_MIN}-{ITEM_MAX}, got {value}"
        )
    return value


def score_wemwbs(raw_items: Sequence[int]) -> WemwbsResult:
    """Score a WEMWBS response set.

    Inputs:
    - ``raw_items``: 14 items in Tennant 2007 administration
      order, each 1-5 Likert:
        1 = "None of the time"
        2 = "Rarely"
        3 = "Some of the time"
        4 = "Often"
        5 = "All of the time"

      Items (Tennant 2007 Appendix verbatim):
        1.  I've been feeling optimistic about the future
        2.  I've been feeling useful
        3.  I've been feeling relaxed
        4.  I've been feeling interested in other people
        5.  I've had energy to spare
        6.  I've been dealing with problems well
        7.  I've been thinking clearly
        8.  I've been feeling good about myself
        9.  I've been feeling close to other people
        10. I've been feeling confident
        11. I've been able to make up my own mind about things
        12. I've been feeling loved
        13. I've been interested in new things
        14. I've been feeling cheerful

    Raises :class:`InvalidResponseError` on:
    - Wrong number of items (must be exactly 14).
    - A non-int / bool item value.
    - An item outside ``[1, 5]``.

    Computes:
    - ``total``: sum of all 14 items, 14-70.
    - ``severity``: always ``"continuous"``.

    No reverse-keying — all items positively worded by design.
    Raw items preserved in ``items`` field for audit.
    """
    if len(raw_items) != ITEM_COUNT:
        raise InvalidResponseError(
            f"WEMWBS requires exactly {ITEM_COUNT} items, "
            f"got {len(raw_items)}"
        )
    items = tuple(
        _validate_item(index_1=i + 1, value=v)
        for i, v in enumerate(raw_items)
    )
    total = sum(items)
    return WemwbsResult(
        total=total,
        severity="continuous",
        items=items,
    )


__all__ = [
    "INSTRUMENT_VERSION",
    "ITEM_COUNT",
    "ITEM_MAX",
    "ITEM_MIN",
    "InvalidResponseError",
    "Severity",
    "WemwbsResult",
    "score_wemwbs",
]

"""HADS — Hospital Anxiety and Depression Scale (Zigmond & Snaith 1983).

The Hospital Anxiety and Depression Scale is the single most widely-
used self-report screener for anxiety and depression in medical /
hospital populations.  Zigmond & Snaith (1983; Acta Psychiatrica
Scandinavica 67(6):361-370) developed the 14-item instrument
specifically to screen non-psychiatric hospital outpatients where
the somatic items on PHQ-9-era instruments (sleep, appetite,
fatigue, psychomotor change) would be CONFOUNDED by the patient's
medical comorbidities.  The instrument's central design choice
was to EXCLUDE somatic symptom items — every HADS item probes
cognitive / affective symptoms only — so a patient with cancer,
cardiac disease, chronic pain, or any somatically-distressing
illness can be screened without somatic-symptom confounds
inflating the score.

Snaith (2003; Health and Quality of Life Outcomes 1:29) — the 25-
year retrospective co-authored by the original instrument creator —
confirmed the 4-band per-subscale severity structure (0-7 normal /
8-10 mild / 11-14 moderate / 15-21 severe) that is the canonical
reporting convention.  Bjelland, Dahl, Haug & Neckelmann (2002;
Journal of Psychosomatic Research 52(2):69-77) meta-analytically
validated the ≥ 8 cutoff (sensitivity ~0.78-0.90, specificity
~0.74-0.78) for "possible case" and ≥ 11 for "probable case"
across 747 studies.  Herrmann (1997) provides the reference
German-language translation psychometrics (n=6,200 patients;
α=0.80 anxiety, α=0.81 depression).

Clinical relevance to the Discipline OS platform:

The HADS fills a **medical-comorbidity-setting** gap in the
platform's depression/anxiety roster.  Prior instruments each
take a different angle:

- **PHQ-9** (Kroenke 2001) measures DSM-IV-specific MDD symptom
  burden on the DSM 9-symptom criterion set.  Includes sleep
  (item 3), appetite (item 5), fatigue (item 4), psychomotor
  change (item 8), and concentration (item 7) — all of which
  are CONFOUNDED by somatic illness.
- **GAD-7** (Spitzer 2006) measures GAD worry on 7 items.
  Includes restlessness (item 5), irritability (item 6), and
  sleep disturbance implicit in item 4 — somatically-confounded
  in chronic pain / inflammation contexts.
- **HADS** (Zigmond & Snaith 1983) measures cognitive / affective
  anxiety and depression on 14 items WITH NO SOMATIC ITEMS.
  Designed specifically for patients whose medical illness
  would inflate somatic-symptom scorers.
- **PHQ-15** (Kroenke 2002) measures the SOMATIZATION construct
  directly — 15 items, all somatic.  Complementary pole of the
  same clinical question HADS avoids.

The Discipline OS population includes substance-use-disorder
patients with high rates of medical comorbidity (hepatitis C,
HIV, cardiovascular disease, chronic pain) where somatic-symptom
confounding is a real issue.  HADS provides the comorbidity-
robust screener.

Construct placement against PHQ-9 / GAD-7:

HADS and PHQ-9 / GAD-7 measure overlapping but non-identical
constructs.  Cross-instrument correlations reported in Bjelland
2002 and subsequent validations:

    HADS-A ↔ GAD-7:  r ≈ 0.74
    HADS-D ↔ PHQ-9:  r ≈ 0.66  (lower due to somatic-item
                                  exclusion; HADS-D captures
                                  anhedonia-core, PHQ-9 captures
                                  broader MDD phenotype)

Pairings with existing instruments:

- **HADS-D high + PHQ-9 high** — convergent depression signal;
  both scorers elevated → strong indication for evidence-based
  depression treatment (MBCT / CBT / behavioral activation).
- **HADS-D high + PHQ-9 normal** — anhedonia-dominant
  presentation without somatic burden; classic medical-
  comorbidity profile (PHQ-9 may have underflagged due to
  illness masking somatic items).
- **HADS-A high + GAD-7 high** — convergent anxiety signal;
  cognitive/affective + worry-specific convergent evidence.
- **HADS-A high + GAD-7 normal** — cognitive-anxiety without
  worry-rumination core; more likely panic/phobia-spectrum.
- **HADS (either) ≥ 11 + C-SSRS not administered** — Bjelland
  2002 probable-caseness threshold; trigger structured
  psychiatric workup at clinician-UI.
- **HADS-D ≥ 11 + PHQ-9 item 9 positive** — HADS has no
  suicidality probe; a convergent HADS-D + PHQ-9-item-9
  positive pattern surfaces the C-SSRS follow-up prompt at
  the clinician-UI renderer layer.
- **HADS × PHQ-15** — distress (HADS) + somatization (PHQ-15)
  co-elevation is the classic functional-somatic-syndrome
  profile (Barsky 2005 / Kroenke 2007); mind-body-oriented
  intervention (ACT / MBSR for somatic-focused populations).
- **HADS trajectory** — Puhan 2008 RCI on HADS-A and HADS-D
  is ≈ 1.5 per subscale (MCID).  A 1.5-point per-subscale
  delta is clinically meaningful; the platform's trajectory
  layer extracts this via week-over-week subscale Δ.

Instrument structure (Zigmond & Snaith 1983):

**14 items, each on a 4-point Likert scale (0-3)**.  Response
option semantics vary per item — some items are worded so the
first option (0) is the HEALTHIEST response, others are worded
so the first option is the MOST DISTRESSED response.  This
alternation is DELIBERATE: Zigmond & Snaith 1983 alternated
directions within each subscale to prevent acquiescence-bias
contamination of the subscale totals.

**Two-subscale partitioning** (interleaved administration order,
1-indexed):

    Anxiety (HADS-A, 7 items):     1, 3, 5, 7, 9, 11, 13  (odd)
    Depression (HADS-D, 7 items):  2, 4, 6, 8, 10, 12, 14 (even)

Interleaved 1-2-1-2 across the card.  A client that reshuffled
items per-subscale for administration would change response
distribution (subscale-block effects) and is explicitly NOT
validated.

**Reverse-keyed items** (6 of 14):

    Depression reverse items:  2 (enjoy things), 4 (laugh),
                               6 (cheerful), 12 (look forward),
                               14 (enjoy book/TV)
    Anxiety reverse items:     7 (sit at ease and relaxed)

For reverse-keyed items, the verbatim option index from the
card is flipped as ``flipped_v = 3 - raw_v`` so the per-subscale
sum is in the distress-positive direction (higher = more
symptomatic).  The ``items`` field preserves the RAW (pre-flip)
responses for audit invariance and FHIR R4 export — a clinician
can reconstruct the original response pattern as administered.

Verbatim item text (Zigmond & Snaith 1983, interleaved
administration order):

    1.  I feel tense or 'wound up'
        [Anxiety — forward: 3=Most of the time .. 0=Not at all]
    2.  I still enjoy the things I used to enjoy
        [Depression — REVERSE: 0=Definitely as much ..
         3=Hardly at all]
    3.  I get a sort of frightened feeling as if something
        awful is about to happen
        [Anxiety — forward: 3=Very definitely .. 0=Not at all]
    4.  I can laugh and see the funny side of things
        [Depression — REVERSE: 0=As much as I always could ..
         3=Not at all]
    5.  Worrying thoughts go through my mind
        [Anxiety — forward: 3=A great deal of the time ..
         0=Only occasionally]
    6.  I feel cheerful
        [Depression — REVERSE: 0=Most of the time ..
         3=Not at all]
    7.  I can sit at ease and feel relaxed
        [Anxiety — REVERSE: 0=Definitely .. 3=Not at all]
    8.  I feel as if I am slowed down
        [Depression — forward: 3=Nearly all the time ..
         0=Not at all]
    9.  I get a sort of frightened feeling like 'butterflies'
        in the stomach
        [Anxiety — forward: 3=Very often .. 0=Not at all]
    10. I have lost interest in my appearance
        [Depression — forward: 3=Definitely ..
         0=I take just as much care as ever]
    11. I feel restless as if I have to be on the move
        [Anxiety — forward: 3=Very much indeed ..
         0=Not at all]
    12. I look forward with enjoyment to things
        [Depression — REVERSE: 0=As much as I ever did ..
         3=Hardly at all]
    13. I get sudden feelings of panic
        [Anxiety — forward: 3=Very often indeed ..
         0=Not at all]
    14. I can enjoy a good book or radio or TV program
        [Depression — REVERSE: 0=Often .. 3=Very seldom]

Scoring:

- Apply reverse-keying to positions (2, 4, 6, 7, 12, 14) before
  summing:  ``flipped_v = 3 - raw_v``.
- Anxiety subscale (HADS-A) sum = sum of 7 anxiety items after
  reverse-keying.  Range 0-21.
- Depression subscale (HADS-D) sum = sum of 7 depression items
  after reverse-keying.  Range 0-21.
- Total = anxiety_sum + depression_sum.  Range 0-42.  Snaith
  2003 notes the total is a valid overall-distress aggregate but
  the PRIMARY reporting units are the two subscale totals.
- Severity band per subscale (Snaith 2003):
    0-7:   normal
    8-10:  mild
    11-14: moderate
    15-21: severe
- Positive screen per subscale (Bjelland 2002):  subscale ≥ 11.
- Envelope ``severity`` at top level reports the WORSE of the two
  subscale bands — anxiety and depression are reported
  independently in ``subscale_severities`` ({"anxiety": band,
  "depression": band}) so the clinician-UI renderer can show
  both bands without information loss.

T3 posture:

No HADS item probes suicidality.  Zigmond & Snaith 1983
deliberately excluded self-harm items because the instrument
is designed for non-psychiatric medical settings where
suicidality screening is handled separately.  A high HADS-D
combined with a positive PHQ-9 item 9 surfaces at the
clinician-UI layer as a C-SSRS follow-up prompt, NOT as a
scorer-layer T3 flag.  Same renderer-versus-scorer-layer
boundary established for SWLS / MSPSS / UCLA-3 / GSE / IES-R.

Design invariants preserved:

- **14-item exact count**.  Zigmond & Snaith 1983 pinned the
  14-item structure; no published short or long form is
  validated.
- **Interleaved administration order pinned**.  Zigmond &
  Snaith 1983 alternated subscales 1-2-1-2 across the card
  to prevent context effects.
- **Subscale partition by item parity pinned**.  Odd = anxiety,
  even = depression is the original administration structure;
  this is DIFFERENT from IES-R (position-based) and MSPSS
  (blocked).
- **Reverse-keying positions pinned** to (2, 4, 6, 7, 12, 14).
  The 6-item reverse pattern is the Zigmond & Snaith 1983
  acquiescence-control design.
- **Per-subscale 0-21 range**.
- **Severity bands from Snaith 2003** (never hand-rolled per
  CLAUDE.md non-negotiable #9).  Bjelland 2002 validated
  ≥ 11 as "probable case".
- **Bool rejection at the scorer.**  Platform-wide invariant.

Citations:

- Zigmond AS, Snaith RP (1983).  *The Hospital Anxiety and
  Depression Scale.*  Acta Psychiatrica Scandinavica
  67(6):361-370.  (Canonical derivation; 14-item interleaved
  administration order; reverse-keyed positions; construct
  placement in medical-comorbidity populations.)
- Snaith RP (2003).  *The Hospital Anxiety and Depression
  Scale.*  Health and Quality of Life Outcomes 1:29.  (25-year
  retrospective by the original co-author; pinned 4-band per-
  subscale severity structure 0-7/8-10/11-14/15-21.)
- Bjelland I, Dahl AA, Haug TT, Neckelmann D (2002).  *The
  validity of the Hospital Anxiety and Depression Scale.  An
  updated literature review.*  Journal of Psychosomatic
  Research 52(2):69-77.  (Meta-analytic validation across 747
  studies; ≥ 8 "possible case" and ≥ 11 "probable case"
  thresholds; convergent validity r ≈ 0.74 HADS-A × GAD-7.)
- Herrmann C (1997).  *International experiences with the
  Hospital Anxiety and Depression Scale — a review of
  validation data and clinical results.*  Journal of
  Psychosomatic Research 42(1):17-41.  (n=6,200; α=0.80
  anxiety, α=0.81 depression; cross-cultural validation.)
- Puhan MA, Frey M, Büchi S, Schünemann HJ (2008).  *The
  minimal important difference of the Hospital Anxiety and
  Depression Scale in patients with chronic obstructive
  pulmonary disease.*  Health and Quality of Life Outcomes
  6:46.  (MCID ≈ 1.5 per subscale; RCI methodology
  application.)
- Kroenke K, Spitzer RL, Williams JB (2001).  *The PHQ-9:
  Validity of a brief depression severity measure.*  Journal
  of General Internal Medicine 16(9):606-613.  (Companion
  DSM-IV depression severity measure; HADS-D × PHQ-9 pairing
  rationale.)
- Spitzer RL, Kroenke K, Williams JB, Löwe B (2006).  *A brief
  measure for assessing generalized anxiety disorder: the
  GAD-7.*  Archives of Internal Medicine 166(10):1092-1097.
  (Companion GAD severity measure; HADS-A × GAD-7 pairing
  rationale.)
- Kroenke K, Spitzer RL, Williams JB (2002).  *The PHQ-15:
  Validity of a new measure for evaluating the severity of
  somatic symptoms.*  Psychosomatic Medicine 64(2):258-266.
  (Complementary somatization measure; HADS × PHQ-15 mind-
  body pairing rationale.)
- Barsky AJ, Peekna HM, Borus JF (2005).  *Somatic symptom
  reporting in women and men.*  Journal of General Internal
  Medicine 16(4):266-275.  (Functional-somatic-syndrome
  framing for HADS × PHQ-15.)
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

INSTRUMENT_VERSION = "hads-1.0.0"
ITEM_COUNT = 14
ITEM_MIN, ITEM_MAX = 0, 3

# Zigmond & Snaith 1983: interleaved administration order.
# Odd-numbered items = anxiety subscale.  Even-numbered items =
# depression subscale.  This pattern is DIFFERENT from MSPSS
# (blocked) and IES-R (position-based); matches Zigmond & Snaith
# 1983 acquiescence-control design.
HADS_ANXIETY_POSITIONS: tuple[int, ...] = (1, 3, 5, 7, 9, 11, 13)
HADS_DEPRESSION_POSITIONS: tuple[int, ...] = (2, 4, 6, 8, 10, 12, 14)

# Zigmond & Snaith 1983 Table 1: 6 reverse-keyed items.
# Depression reverse: 2 (enjoy things), 4 (laugh), 6 (cheerful),
# 12 (look forward), 14 (enjoy book/TV).
# Anxiety reverse: 7 (sit at ease and feel relaxed).
# For these positions, flipped_v = 3 - raw_v so the per-subscale
# sum is in the distress-positive direction.
HADS_REVERSE_ITEMS: tuple[int, ...] = (2, 4, 6, 7, 12, 14)

# Subscale label-key ordering.  Clinician-UI renderers key off
# this list so a single source-of-truth controls dict-key order.
HADS_SUBSCALES: tuple[str, str] = ("anxiety", "depression")

# Snaith 2003 4-band per-subscale severity structure.  Stored as
# (upper_bound, label) pairs in ascending order; lookup scans for
# the first upper_bound ≥ score.
HADS_SEVERITY_THRESHOLDS: tuple[tuple[int, str], ...] = (
    (7, "normal"),
    (10, "mild"),
    (14, "moderate"),
    (21, "severe"),
)

# Bjelland 2002 "probable case" threshold per subscale.
HADS_CLINICAL_CUTOFF: int = 11


class InvalidResponseError(ValueError):
    """Raised on item-count, item-range, or item-type violations."""


Severity = Literal["normal", "mild", "moderate", "severe"]


@dataclass(frozen=True)
class HadsResult:
    """Typed HADS output.

    Fields:
    - ``total``: 0-42 sum of all 14 items AFTER reverse-keying.  The
      overall distress aggregate; Snaith 2003 notes this is a valid
      overall-distress summary but the PRIMARY reporting units are
      the two subscale totals.
    - ``anxiety``: 0-21 sum of the 7 anxiety items (positions 1, 3,
      5, 7, 9, 11, 13) after reverse-keying position 7.
    - ``depression``: 0-21 sum of the 7 depression items (positions
      2, 4, 6, 8, 10, 12, 14) after reverse-keying positions
      2, 4, 6, 12, 14.
    - ``anxiety_severity``: Snaith 2003 band label for HADS-A
      (normal/mild/moderate/severe).
    - ``depression_severity``: Snaith 2003 band label for HADS-D.
    - ``severity``: the WORSE of the two subscale bands.  Ordering:
      normal < mild < moderate < severe.  Surfaced at the
      envelope-level ``severity`` field for trajectory charting
      and UI priority-sorting.
    - ``anxiety_positive_screen``: True if anxiety ≥ 11
      (Bjelland 2002 probable-case threshold).
    - ``depression_positive_screen``: True if depression ≥ 11.
    - ``positive_screen``: True if EITHER subscale ≥ 11 — surfaced
      as the envelope-level ``positive_screen`` field for "any
      caseness detected" filtering.
    - ``cutoff_used``: the per-subscale clinical cutoff (11).
    - ``items``: verbatim 14-tuple of raw 0-3 responses in Zigmond
      & Snaith 1983 administration order (pre-reverse-keying).
      Preserved for audit invariance and FHIR R4 export.

    Deliberately-absent fields:
    - No ``requires_t3`` — no HADS item probes suicidality.
      Active-risk screening stays on C-SSRS / PHQ-9 item 9 /
      CORE-10 item 6.
    - No ``triggering_items`` — no C-SSRS-style item-level
      acuity routing.
    - No ``index`` — total / subscale sums ARE the published
      scores.
    - No ``scaled_score`` — no transformation applied.
    """

    total: int
    anxiety: int
    depression: int
    anxiety_severity: Severity
    depression_severity: Severity
    severity: Severity
    anxiety_positive_screen: bool
    depression_positive_screen: bool
    positive_screen: bool
    cutoff_used: int
    items: tuple[int, ...]
    instrument_version: str = INSTRUMENT_VERSION


def _validate_item(index_1: int, value: object) -> int:
    """Validate a single 0-3 Likert item."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidResponseError(
            f"HADS item {index_1} must be int, got {value!r}"
        )
    if not (ITEM_MIN <= value <= ITEM_MAX):
        raise InvalidResponseError(
            f"HADS item {index_1} must be in {ITEM_MIN}-{ITEM_MAX}, "
            f"got {value}"
        )
    return value


def _severity_band(score: int) -> Severity:
    """Map a 0-21 subscale score to a Snaith 2003 band."""
    for upper_bound, label in HADS_SEVERITY_THRESHOLDS:
        if score <= upper_bound:
            return label  # type: ignore[return-value]
    raise InvalidResponseError(
        f"Subscale score {score} exceeds max (21)"
    )


_SEVERITY_RANK: dict[str, int] = {
    "normal": 0,
    "mild": 1,
    "moderate": 2,
    "severe": 3,
}


def _worse_severity(a: Severity, b: Severity) -> Severity:
    """Return whichever of two subscale severities is worse."""
    return a if _SEVERITY_RANK[a] >= _SEVERITY_RANK[b] else b


def _apply_reverse_keying(items: tuple[int, ...]) -> tuple[int, ...]:
    """Flip the 6 reverse-keyed items to the distress-positive direction."""
    out = list(items)
    for pos in HADS_REVERSE_ITEMS:
        out[pos - 1] = ITEM_MAX - items[pos - 1]
    return tuple(out)


def _subscale_sum(
    flipped: tuple[int, ...], positions_1_indexed: tuple[int, ...]
) -> int:
    return sum(flipped[p - 1] for p in positions_1_indexed)


def score_hads(raw_items: Sequence[int]) -> HadsResult:
    """Score a HADS response set.

    Inputs:
    - ``raw_items``: 14 items, each 0-3 verbatim option index from
      the Zigmond & Snaith 1983 administration card.  For reverse-
      keyed items (2, 4, 6, 7, 12, 14), 0 is the HEALTHIEST option
      on the card and 3 is the MOST DISTRESSED option on the card.
      For forward-keyed items, 0 is the most distressed option.
      The scorer handles the direction-inversion; clients send
      what the respondent SELECTED.

    Raises :class:`InvalidResponseError` on:
    - Wrong number of items (must be exactly 14).
    - A non-int / bool item value.
    - An item outside ``[0, 3]``.

    Computes:
    - Reverse-keys positions (2, 4, 6, 7, 12, 14):
      ``flipped_v = 3 - raw_v``.
    - ``anxiety``: sum of positions 1, 3, 5, 7, 9, 11, 13 after
      reverse-keying.
    - ``depression``: sum of positions 2, 4, 6, 8, 10, 12, 14
      after reverse-keying.
    - ``total``: anxiety + depression.
    - ``anxiety_severity`` / ``depression_severity``: Snaith 2003
      band for each subscale.
    - ``severity``: the WORSE of the two subscale bands.
    - ``anxiety_positive_screen`` / ``depression_positive_screen``:
      True if the respective subscale ≥ 11 (Bjelland 2002).
    - ``positive_screen``: True if either subscale is positive.
    - ``items``: tuple of the RAW pre-flip responses (audit
      invariance).

    Platform-wide invariants preserved:
    - Reverse-keying applied at scorer (audit preserves raw).
    - Subscale partition from Zigmond & Snaith 1983 pinned.
    - Snaith 2003 severity bands taken verbatim.
    - Bjelland 2002 cutoff ≥ 11 per subscale.
    - No T3 flag (no suicidality probe).
    """
    if len(raw_items) != ITEM_COUNT:
        raise InvalidResponseError(
            f"HADS requires exactly {ITEM_COUNT} items, "
            f"got {len(raw_items)}"
        )
    raw = tuple(
        _validate_item(index_1=i + 1, value=v)
        for i, v in enumerate(raw_items)
    )

    flipped = _apply_reverse_keying(raw)

    anxiety = _subscale_sum(flipped, HADS_ANXIETY_POSITIONS)
    depression = _subscale_sum(flipped, HADS_DEPRESSION_POSITIONS)
    total = anxiety + depression

    anxiety_band = _severity_band(anxiety)
    depression_band = _severity_band(depression)
    overall_band = _worse_severity(anxiety_band, depression_band)

    a_positive = anxiety >= HADS_CLINICAL_CUTOFF
    d_positive = depression >= HADS_CLINICAL_CUTOFF

    return HadsResult(
        total=total,
        anxiety=anxiety,
        depression=depression,
        anxiety_severity=anxiety_band,
        depression_severity=depression_band,
        severity=overall_band,
        anxiety_positive_screen=a_positive,
        depression_positive_screen=d_positive,
        positive_screen=a_positive or d_positive,
        cutoff_used=HADS_CLINICAL_CUTOFF,
        items=raw,
    )


__all__ = [
    "HADS_ANXIETY_POSITIONS",
    "HADS_CLINICAL_CUTOFF",
    "HADS_DEPRESSION_POSITIONS",
    "HADS_REVERSE_ITEMS",
    "HADS_SEVERITY_THRESHOLDS",
    "HADS_SUBSCALES",
    "INSTRUMENT_VERSION",
    "ITEM_COUNT",
    "ITEM_MAX",
    "ITEM_MIN",
    "HadsResult",
    "InvalidResponseError",
    "Severity",
    "score_hads",
]

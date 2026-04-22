"""DASS-21 — Depression Anxiety Stress Scales short form (Lovibond & Lovibond 1995).

The Depression Anxiety Stress Scales 21-item version is the
abbreviated self-report instrument derived from the 42-item
DASS-42 (Lovibond & Lovibond 1995; Behaviour Research and Therapy
33(3):335-343).  The 21-item short form was validated by Henry &
Crawford (2005; British Journal of Clinical Psychology 44(Pt
2):227-239; n=1,794 non-clinical adults) and Antony, Bieling,
Cox, Enns & Swinson (1998; Psychological Assessment 10(2):176-
181; n=717 clinical adults across anxiety and depressive
disorder diagnoses).  The instrument partitions the negative-
affect space into three distinguishable factors — depression,
anxiety, and stress — that capture a richer picture of emotional
dysregulation than a two-factor depression/anxiety partition.

Clinical relevance to the Discipline OS platform:

DASS-21 is the **three-factor negative-affect decomposition**
that extends the platform's mood screener roster.  Prior
instruments provide different angles:

- **PHQ-9** measures DSM-IV MDD on 9 criterion symptoms (includes
  somatic items).
- **GAD-7** measures GAD worry on 7 items.
- **HADS** measures cognitive anxiety and cognitive depression on
  14 items with NO somatic items (medical-comorbidity robust).
- **PHQ-15** measures somatization on 15 somatic items.
- **PSS-10** measures perceived stress on 10 items.
- **DASS-21** measures DEPRESSION, ANXIETY, and STRESS on 21 items
  in a single administration, with Henry & Crawford 2005 factor-
  analytic validation of the three-factor structure.

The DASS-21 STRESS subscale captures TENSION / DIFFICULTY RELAXING /
IRRITABILITY / IMPATIENCE content that PSS-10 measures from a
different perspective (cognitive appraisal of stressors).  The two
stress measures are complementary: PSS-10 assesses the ENVIRONMENT-
AS-STRESSFUL appraisal (Cohen & Kamarck 1983 model); DASS-21 Stress
assesses the ORGANISM-AS-STRESSED symptom burden (Lovibond 1998
tripartite model).

The DASS-21 DEPRESSION and ANXIETY subscales differ subtly from
HADS-D / HADS-A and PHQ-9 / GAD-7:
- DASS-21 Depression emphasizes ANHEDONIA, DEVALUATION OF LIFE,
  HOPELESSNESS, and LACK-OF-INTEREST over cognitive-negativity.
- DASS-21 Anxiety emphasizes AUTONOMIC AROUSAL (trembling, dry
  mouth, breathing difficulties, scared/panicky) over GAD-style
  worry — it is a more PANIC / ACUTE-ANXIETY construct than GAD-7.

Tripartite model (Clark & Watson 1991):
- DEPRESSION = LOW positive affect + high negative affect
- ANXIETY = HIGH physiological arousal + high negative affect
- STRESS = HIGH negative affect WITHOUT the specific low-positive-
  affect (depression) or physiological-arousal (anxiety) markers

DASS-21 is the instrument that most faithfully implements the
tripartite model in a single administration.

Administration: 21 items, 0-3 Likert ("Did not apply to me at all"
to "Applied to me very much or most of the time"), past-week
timeframe.  No reverse-keying (all items worded so higher = more
distress).  Total: 0-63.  Per-subscale: 0-21.

Subscale partitioning (Lovibond & Lovibond 1995 Section 3; Henry
& Crawford 2005 Table 1):

    Depression (7 items): 3, 5, 10, 13, 16, 17, 21
    Anxiety    (7 items): 2, 4, 7, 9, 15, 19, 20
    Stress     (7 items): 1, 6, 8, 11, 12, 14, 18

The partition is non-overlapping — each item loads on exactly one
factor per Henry & Crawford 2005 confirmatory factor analysis
(χ²/df = 2.67, CFI = 0.94, RMSEA = 0.05 for the three-factor
solution).  A one-factor "general negative affect" model or two-
factor (depression + combined-anxiety-stress) model fits
significantly worse.

Severity bands (Antony 1998 / Henry & Crawford 2005 per-subscale
thresholds on the native DASS-21 scale — derived by halving the
Lovibond 1995 DASS-42 thresholds, the convention documented in
the DASS manual second edition):

    Depression:
        0–4   normal
        5–6   mild
        7–10  moderate
        11–13 severe
        14–21 extremely severe

    Anxiety:
        0–3   normal
        4–5   mild
        6–7   moderate
        8–9   severe
        10–21 extremely severe

    Stress:
        0–7   normal
        8–9   mild
        10–12 moderate
        13–16 severe
        17–21 extremely severe

Note the asymmetry: stress is "harder to get into severe
ranges" than anxiety — a stress score of 10 is moderate but an
anxiety score of 10 is extremely severe.  This reflects Lovibond
1995 population norms: stress symptoms are more universally
endorsed in a normal population than anxiety-arousal symptoms,
so the thresholds are shifted to preserve band meaning.  Per
CLAUDE.md non-negotiable #9 (never hand-roll severity
thresholds), the asymmetric thresholds are taken verbatim from
Lovibond 1995 / Antony 1998 / Henry & Crawford 2005.

Clinical cutoff — the "clinically elevated" convention is
per-subscale ≥ moderate:
    Depression ≥ 7
    Anxiety    ≥ 6
    Stress     ≥ 10
``positive_screen`` flags if ANY subscale meets its respective
moderate threshold.

Overall severity = worst-of-three-subscale-bands per a 5-level
rank (normal < mild < moderate < severe < extremely_severe).  A
patient severe on anxiety but normal on depression and stress
gets severity = severe — the clinician's primary-triage value.

T3 posture — DASS-21 has NO suicidality item.  Item 3 ("I
couldn't seem to experience any positive feeling at all") and
item 13 ("I felt down-hearted and blue") are anhedonia /
cognitive-depression probes, NOT ideation probes.  Item 17 ("I
felt I wasn't worth much as a person") is a worthlessness probe
— clinically concerning but NOT equivalent to the PHQ-9 item 9
"thoughts that you would be better off dead" active-risk probe.
Active-risk screening stays on C-SSRS / PHQ-9 item 9 / CORE-10
item 6.  Same renderer-versus-scorer boundary used for HADS /
IES-R / MSPSS / SWLS / GSE.

Clinical pairings the scorer output supports:

- DASS-21 Depression high + PHQ-9 high — convergent MDD signal
  across tripartite (DASS-D: anhedonia-dominant) and DSM-IV
  (PHQ-9: full criterion set) frames.
- DASS-21 Anxiety high + GAD-7 low — PANIC / AUTONOMIC-AROUSAL
  pattern (DASS-A: physiological; GAD-7: worry).  Routes to
  interoceptive-exposure / PACE / panic-disorder protocols
  rather than generalized-worry CBT.
- DASS-21 Stress high + PSS-10 high — convergent
  stress-response signal from both ORGANISM (DASS) and
  APPRAISAL (PSS) perspectives.
- DASS-21 Stress high + DASS-21 Depression and Anxiety normal —
  ISOLATED stress profile.  Routes to stress-inoculation /
  problem-solving / time-management interventions.  The isolated-
  stress case is the one where tripartite decomposition changes
  clinical recommendation; PHQ-9 / GAD-7 / HADS would miss this
  presentation entirely or mislabel it as low-grade anxiety.
- DASS-21 + CD-RISC-10 — distress-resilience pairing; high DASS
  and low CD-RISC identifies the resilience-intervention target.
- DASS-21 trajectory — Ronk 2013 (Journal of Affective
  Disorders 148(1):59-64) MCID ≈ 3 points per subscale in
  depression/anxiety clinical-trials contexts, Sprinkle 2020
  RCI methodology confirms.

Instrument version: ``dass21-1.0.0``.

References
----------
- Lovibond SH, Lovibond PF (1995).  *Manual for the Depression
  Anxiety Stress Scales* (2nd ed.).  Sydney: Psychology
  Foundation of Australia.  (Canonical source — item list,
  administration, DASS-42 severity thresholds, DASS-21 halving
  convention.)
- Lovibond PF, Lovibond SH (1995).  *The structure of negative
  emotional states: Comparison of the Depression Anxiety Stress
  Scales (DASS) with the Beck Depression and Anxiety Inventories.*
  Behaviour Research and Therapy 33(3):335-343.  (Tripartite
  model validation; DASS-42 factor structure.)
- Henry JD, Crawford JR (2005).  *The short-form version of the
  Depression Anxiety Stress Scales (DASS-21): Construct validity
  and normative data in a large non-clinical sample.*  British
  Journal of Clinical Psychology 44(Pt 2):227-239.  (n=1,794;
  CFA validation of three-factor structure; DASS-21 normative
  data.)
- Antony MM, Bieling PJ, Cox BJ, Enns MW, Swinson RP (1998).
  *Psychometric properties of the 42-item and 21-item versions
  of the Depression Anxiety Stress Scales in clinical groups
  and a community sample.*  Psychological Assessment
  10(2):176-181.  (n=717 clinical + community; per-subscale
  severity thresholds on DASS-21 scale.)
- Clark LA, Watson D (1991).  *Tripartite model of anxiety and
  depression: Psychometric evidence and taxonomic implications.*
  Journal of Abnormal Psychology 100(3):316-336.  (Theoretical
  framework for the three-factor solution.)
- Ronk FR, Korman JR, Hooke GR, Page AC (2013).  *Assessing
  clinical significance of treatment outcomes using the DASS-21.*
  Psychological Assessment 25(4):1103-1110.  (RCI and MCID
  methodology for DASS-21 trajectory scoring.)
- Cohen S, Kamarck T, Mermelstein R (1983).  *A global measure
  of perceived stress.*  Journal of Health and Social Behavior
  24(4):385-396.  (PSS-10 companion instrument — ORGANISM vs
  APPRAISAL stress decomposition rationale.)
- Kroenke K, Spitzer RL, Williams JB (2001).  *The PHQ-9:
  Validity of a brief depression severity measure.*  Journal of
  General Internal Medicine 16(9):606-613.  (PHQ-9 pairing
  reference.)
- Spitzer RL, Kroenke K, Williams JB, Löwe B (2006).  *A brief
  measure for assessing generalized anxiety disorder: the
  GAD-7.*  Archives of Internal Medicine 166(10):1092-1097.
  (GAD-7 pairing reference.)
- Zigmond AS, Snaith RP (1983).  *The hospital anxiety and
  depression scale.*  Acta Psychiatr Scand 67(6):361-370.
  (HADS pairing reference.)
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

INSTRUMENT_VERSION = "dass21-1.0.0"
ITEM_COUNT = 21
ITEM_MIN, ITEM_MAX = 0, 3

# Lovibond & Lovibond 1995 Section 3 / Henry & Crawford 2005 Table 1
# three-factor partition.  Each item loads on exactly one factor.
DASS21_DEPRESSION_POSITIONS: tuple[int, ...] = (3, 5, 10, 13, 16, 17, 21)
DASS21_ANXIETY_POSITIONS: tuple[int, ...] = (2, 4, 7, 9, 15, 19, 20)
DASS21_STRESS_POSITIONS: tuple[int, ...] = (1, 6, 8, 11, 12, 14, 18)

# Subscale label ordering — clinician-UI renderers key off this
# tuple so a single source-of-truth controls dict-key order.
DASS21_SUBSCALES: tuple[str, str, str] = ("depression", "anxiety", "stress")

# Antony 1998 / Henry & Crawford 2005 per-subscale severity
# thresholds on the native DASS-21 scale (derived from Lovibond
# 1995 DASS-42 thresholds halved — the second-edition manual
# convention).  Stored as ascending (upper_bound, label) pairs;
# lookup scans for the first upper_bound ≥ score.  Note the
# asymmetry: stress thresholds are SHIFTED HIGHER than anxiety
# thresholds because stress symptoms are more universally
# endorsed in non-clinical populations (Lovibond 1995 normative
# data).  Per CLAUDE.md non-negotiable #9 these asymmetric bands
# are taken verbatim and not hand-rolled.
DASS21_DEPRESSION_SEVERITY_THRESHOLDS: tuple[tuple[int, str], ...] = (
    (4, "normal"),
    (6, "mild"),
    (10, "moderate"),
    (13, "severe"),
    (21, "extremely_severe"),
)
DASS21_ANXIETY_SEVERITY_THRESHOLDS: tuple[tuple[int, str], ...] = (
    (3, "normal"),
    (5, "mild"),
    (7, "moderate"),
    (9, "severe"),
    (21, "extremely_severe"),
)
DASS21_STRESS_SEVERITY_THRESHOLDS: tuple[tuple[int, str], ...] = (
    (7, "normal"),
    (9, "mild"),
    (12, "moderate"),
    (16, "severe"),
    (21, "extremely_severe"),
)

# Per-subscale "clinically elevated" cutoffs — the moderate-band
# lower bound per Antony 1998.  Used for ``positive_screen``: any
# subscale at-or-above its moderate threshold is flagged.
DASS21_DEPRESSION_CUTOFF: int = 7
DASS21_ANXIETY_CUTOFF: int = 6
DASS21_STRESS_CUTOFF: int = 10


class InvalidResponseError(ValueError):
    """Raised on item-count, item-range, or item-type violations."""


Severity = Literal[
    "normal", "mild", "moderate", "severe", "extremely_severe"
]


@dataclass(frozen=True)
class Dass21Result:
    """Typed DASS-21 output.

    Fields:
    - ``total``: 0-63 sum of all 21 items.  The overall negative-
      affect aggregate; Henry & Crawford 2005 notes this is a valid
      overall-distress summary but the PRIMARY reporting units are
      the three subscale totals.
    - ``depression``: 0-21 sum of the 7 depression items (positions
      3, 5, 10, 13, 16, 17, 21).
    - ``anxiety``: 0-21 sum of the 7 anxiety items (positions
      2, 4, 7, 9, 15, 19, 20).
    - ``stress``: 0-21 sum of the 7 stress items (positions
      1, 6, 8, 11, 12, 14, 18).
    - ``depression_severity``: Antony 1998 / Henry & Crawford 2005
      band label for DASS-D (normal / mild / moderate / severe /
      extremely_severe).
    - ``anxiety_severity``: Antony 1998 band label for DASS-A.
    - ``stress_severity``: Antony 1998 band label for DASS-S.
    - ``severity``: the WORST of the three subscale bands.
      Ordering: normal < mild < moderate < severe <
      extremely_severe.  Surfaced at the envelope-level
      ``severity`` field for trajectory charting and UI priority-
      sorting.
    - ``depression_positive_screen``: True if depression ≥ 7
      (DASS-21 moderate threshold).
    - ``anxiety_positive_screen``: True if anxiety ≥ 6.
    - ``stress_positive_screen``: True if stress ≥ 10.
    - ``positive_screen``: True if ANY subscale meets its moderate
      threshold — surfaced as the envelope-level
      ``positive_screen`` field for "any caseness detected"
      filtering.
    - ``items``: verbatim 21-tuple of raw 0-3 responses in
      Lovibond 1995 administration order.

    Deliberately-absent fields:
    - No ``requires_t3`` — no DASS-21 item probes active
      suicidality.
    - No ``triggering_items`` — no C-SSRS-style item-level
      acuity routing.
    - No ``index`` — total / subscale sums ARE the published
      scores.
    - No single ``cutoff_used`` — the three subscales have
      different moderate thresholds (7 / 6 / 10) so no single
      integer represents the per-subscale cutoffs.  The router
      envelope will omit the ``cutoff_used`` field.
    """

    total: int
    depression: int
    anxiety: int
    stress: int
    depression_severity: Severity
    anxiety_severity: Severity
    stress_severity: Severity
    severity: Severity
    depression_positive_screen: bool
    anxiety_positive_screen: bool
    stress_positive_screen: bool
    positive_screen: bool
    items: tuple[int, ...]
    instrument_version: str = INSTRUMENT_VERSION


def _validate_item(index_1: int, value: object) -> int:
    """Validate a single 0-3 Likert item."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidResponseError(
            f"DASS-21 item {index_1} must be int, got {value!r}"
        )
    if not (ITEM_MIN <= value <= ITEM_MAX):
        raise InvalidResponseError(
            f"DASS-21 item {index_1} must be in {ITEM_MIN}-{ITEM_MAX}, "
            f"got {value}"
        )
    return value


def _severity_band(
    score: int,
    thresholds: tuple[tuple[int, str], ...],
    subscale_name: str,
) -> Severity:
    """Map a 0-21 subscale score to an Antony 1998 band."""
    for upper_bound, label in thresholds:
        if score <= upper_bound:
            return label  # type: ignore[return-value]
    raise InvalidResponseError(
        f"DASS-21 {subscale_name} score {score} exceeds max (21)"
    )


_SEVERITY_RANK: dict[str, int] = {
    "normal": 0,
    "mild": 1,
    "moderate": 2,
    "severe": 3,
    "extremely_severe": 4,
}


def _worst_severity(*severities: Severity) -> Severity:
    """Return whichever of n subscale severities is worst."""
    return max(severities, key=lambda s: _SEVERITY_RANK[s])


def _subscale_sum(
    items: tuple[int, ...], positions_1_indexed: tuple[int, ...]
) -> int:
    return sum(items[p - 1] for p in positions_1_indexed)


def score_dass21(raw_items: Sequence[int]) -> Dass21Result:
    """Score a DASS-21 response set.

    Inputs:
    - ``raw_items``: 21 items, each 0-3 verbatim option index from
      the Lovibond 1995 administration card (0 = "Did not apply to
      me at all"; 3 = "Applied to me very much or most of the
      time"; past-week timeframe).  No reverse-keying — all items
      worded so higher raw = more distress.

    Raises :class:`InvalidResponseError` on:
    - Wrong number of items (must be exactly 21).
    - A non-int / bool item value.
    - An item outside ``[0, 3]``.

    Computes:
    - ``depression``: sum of positions 3, 5, 10, 13, 16, 17, 21.
    - ``anxiety``: sum of positions 2, 4, 7, 9, 15, 19, 20.
    - ``stress``: sum of positions 1, 6, 8, 11, 12, 14, 18.
    - ``total``: depression + anxiety + stress (= sum of all 21
      items since the partition is non-overlapping).
    - Per-subscale severity band (Antony 1998 / Henry & Crawford
      2005 thresholds).
    - ``severity``: the WORST of the three subscale bands.
    - Per-subscale positive_screen (at-or-above moderate threshold
      per Antony 1998).
    - ``positive_screen``: True if ANY subscale is positive.
    - ``items``: tuple of the raw responses (audit invariance).

    Platform-wide invariants preserved:
    - Three-factor partition from Henry & Crawford 2005 pinned.
    - Antony 1998 / Henry & Crawford 2005 severity bands taken
      verbatim.
    - Asymmetric per-subscale thresholds preserved (per CLAUDE.md
      non-negotiable #9 — no hand-rolling).
    - No T3 flag (no suicidality probe).
    """
    if len(raw_items) != ITEM_COUNT:
        raise InvalidResponseError(
            f"DASS-21 requires exactly {ITEM_COUNT} items, "
            f"got {len(raw_items)}"
        )
    items = tuple(
        _validate_item(index_1=i + 1, value=v)
        for i, v in enumerate(raw_items)
    )

    depression = _subscale_sum(items, DASS21_DEPRESSION_POSITIONS)
    anxiety = _subscale_sum(items, DASS21_ANXIETY_POSITIONS)
    stress = _subscale_sum(items, DASS21_STRESS_POSITIONS)
    total = depression + anxiety + stress

    depression_band = _severity_band(
        depression, DASS21_DEPRESSION_SEVERITY_THRESHOLDS, "depression"
    )
    anxiety_band = _severity_band(
        anxiety, DASS21_ANXIETY_SEVERITY_THRESHOLDS, "anxiety"
    )
    stress_band = _severity_band(
        stress, DASS21_STRESS_SEVERITY_THRESHOLDS, "stress"
    )
    overall_band = _worst_severity(
        depression_band, anxiety_band, stress_band
    )

    d_positive = depression >= DASS21_DEPRESSION_CUTOFF
    a_positive = anxiety >= DASS21_ANXIETY_CUTOFF
    s_positive = stress >= DASS21_STRESS_CUTOFF

    return Dass21Result(
        total=total,
        depression=depression,
        anxiety=anxiety,
        stress=stress,
        depression_severity=depression_band,
        anxiety_severity=anxiety_band,
        stress_severity=stress_band,
        severity=overall_band,
        depression_positive_screen=d_positive,
        anxiety_positive_screen=a_positive,
        stress_positive_screen=s_positive,
        positive_screen=d_positive or a_positive or s_positive,
        items=items,
    )


__all__ = [
    "DASS21_ANXIETY_CUTOFF",
    "DASS21_ANXIETY_POSITIONS",
    "DASS21_ANXIETY_SEVERITY_THRESHOLDS",
    "DASS21_DEPRESSION_CUTOFF",
    "DASS21_DEPRESSION_POSITIONS",
    "DASS21_DEPRESSION_SEVERITY_THRESHOLDS",
    "DASS21_STRESS_CUTOFF",
    "DASS21_STRESS_POSITIONS",
    "DASS21_STRESS_SEVERITY_THRESHOLDS",
    "DASS21_SUBSCALES",
    "INSTRUMENT_VERSION",
    "ITEM_COUNT",
    "ITEM_MAX",
    "ITEM_MIN",
    "Dass21Result",
    "InvalidResponseError",
    "Severity",
    "score_dass21",
]

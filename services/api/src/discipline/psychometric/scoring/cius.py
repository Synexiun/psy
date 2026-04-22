"""CIUS — Meerkerk 2009 Compulsive Internet Use Scale.

The 14-item self-report measure of problematic / compulsive
internet use developed by Meerkerk, Van Den Eijnden, Vermulst &
Garretsen (*CyberPsychology & Behavior*, 2009, 12(1):1-6).
Derived from earlier Young 1998 Internet Addiction Test and
Griffiths 1998 behavioral-addiction criteria via an iterative
factor-analytic refinement on a Dutch adolescent / adult
sample (n = 447 derivation + n = 16,925 cross-validation).
Cronbach α = 0.89; single-factor CFA confirmed.

--------------------------------------------------------------
§1. Why CIUS sits on the platform
--------------------------------------------------------------

The platform's construct inventory now includes social-
evaluative anxiety (FNE-B), loneliness / perceived isolation
(UCLA-3), craving intensity (PACS, Craving VAS), and
substance-use severity (AUDIT, DAST-10, DUDIT, PGSI).  CIUS
fills a different kind of slot: **behavioral-addiction
substrate** for a construct that the user may reach for
instead of alcohol / substances / gambling.  Three use cases
drive the measurement:

1. **Caplan 2003 compensatory-internet-use detection.**
   Caplan's (2003) preference-for-online-social-interaction
   model predicts that high FNE-B (social-evaluation anxiety)
   or high UCLA-3 (loneliness) drives problematic internet
   use as an affect-regulation substitute.  The triad FNE-B
   + UCLA-3 + CIUS lets the platform differentiate:
   - High FNE-B + low UCLA-3 + high CIUS → socially-avoidant
     digital compensation (treatment: in-vivo exposure + use
     limits, not more online socialization).
   - Low FNE-B + high UCLA-3 + high CIUS → isolation-
     compensating digital substitution (treatment: structural
     social-contact building + use limits).
   - High FNE-B + high UCLA-3 + high CIUS → combined
     protocol; the digital compensation is doing both jobs.

2. **Cross-addiction relapse-risk detection.**  Koob 2005
   allostatic reward-deficiency theory predicts that
   abstinence from a primary addictive substrate often
   produces compensatory engagement with a secondary
   behavioral substrate.  For a recovering alcohol-use-
   disorder user, a rising CIUS trajectory over 3-6 months
   is a canonical early-warning signal of relapse pressure
   on the primary substrate — the brain is finding
   alternative allostatic load rather than resolving it.
   This is the core reason CIUS sits on a RELAPSE-
   prevention platform: it surfaces the "before the relapse"
   compensation cycle.

3. **ICD-11 / DSM-5 behavioral-addiction overlap.**
   ICD-11 codes Gaming Disorder (6C51) under "Disorders Due
   to Addictive Behaviours"; DSM-5 Section III lists
   Internet Gaming Disorder for further study.  CIUS
   captures the broader internet-as-substrate construct
   (not gaming-specific) — for clinical completeness the
   platform can surface CIUS alongside AUDIT / DAST-10 in
   the substance-use-disorder-panel render.

--------------------------------------------------------------
§2. Scoring
--------------------------------------------------------------

**Items (Meerkerk 2009 Table 1, abbreviated reference; full
copy-edited text lives in the i18n catalog)**:
  1. difficult to stop using the Internet when online
  2. continue to use Internet despite intention to stop
  3. others (partner/children/parents) say use less
  4. prefer Internet over time with others
  5. short of sleep because of Internet
  6. think about Internet when not online
  7. look forward to next Internet session
  8. think should use Internet less often
  9. unsuccessfully tried to spend less time on Internet
  10. rush through (home) work to go on Internet
  11. neglect daily obligations for Internet
  12. go on Internet when feeling down
  13. use Internet to escape sorrows / negative feelings
  14. feel restless / frustrated / irritated when cannot use

**Response scale (Meerkerk 2009 original)**:
  0 = Never
  1 = Seldom
  2 = Sometimes
  3 = Often
  4 = Very often

**Directionality**: All 14 items are negatively-worded
("difficult to stop", "continue despite intention", etc.);
higher raw value = more compulsive use.  **No reverse
keying.**  Total = sum of raw values, range 0-56.

Acquiescence signature: any all-v constant vector yields
total = 14v (all-0s = 0, all-1s = 14, all-2s = 28, all-3s =
42, all-4s = 56).  CIUS has the second-widest endpoint-
exposure on the platform after UCLA-3 (full 0-56 range
between the extremes) — Meerkerk 2009 did not include
balanced-wording because the derivation was constrained to
fit inside an 18-wave Dutch cohort telemetry panel with a
strict item-count budget.

--------------------------------------------------------------
§3. Severity
--------------------------------------------------------------

**No bands.**  Meerkerk 2009 derivation paper did not
publish primary-source cutpoints.  Guertler 2014 (n = 2512
German adult sample) proposed ≥ 21 as an "at risk" marker
and ≥ 28 as "high risk"; these are later-literature
secondary derivations validated against Young 1998 IAT cuts,
NOT primary-source anchors.  Per CLAUDE.md "no hand-rolled
severity thresholds" rule, the platform ships
``severity = "continuous"`` and applies Jacobson-Truax RCI
at the trajectory layer for clinical-significance judgement
on the raw 0-56 total.

This is uniform with STAI-6, FNE-B, UCLA-3, PACS, BIS-11,
MAAS, LOT-R, FFMQ-15 (all continuous, no cutpoints on the
scorer — cutpoints applied at the clinician-UI surface
only when they are primary-source anchors).

--------------------------------------------------------------
§4. Safety posture
--------------------------------------------------------------

**No T3.**  No item probes suicidality.  "Feel restless,
frustrated, or irritated when you cannot use the Internet"
(item 14) is a withdrawal-symptom construct (Griffiths 1998
behavioral-addiction criterion), NOT active-risk ideation.
Clinician UI surfaces high CIUS alongside substance-use
panel results as cross-addiction context; no T3 gating.

--------------------------------------------------------------
§5. Scale origin — why 0-4 and not 1-5
--------------------------------------------------------------

The 0-based Likert is deliberate: Meerkerk 2009 scored the
"Never" response as genuine ZERO compulsivity (not just
"low").  Subsequent applications (e.g., Guertler 2014 German
validation) preserved the 0-4 scale.  The platform follows
Meerkerk 2009's original scoring exactly to preserve the
r = 0.70+ convergent validity with Young's 1998 IAT that
Meerkerk 2009 reported.

Consequence for the platform: CIUS is the first instrument
with a valid ``0`` response, which means Pydantic's
``false → 0`` coercion PASSES the range check.  The scorer's
strict-bool rejection remains essential (per CLAUDE.md) —
otherwise ``False`` (semantic "no") would silently score as
"never" (semantic "zero compulsivity").  Tests pin this
distinction explicitly.

--------------------------------------------------------------
§6. Primary-source citations
--------------------------------------------------------------

- Meerkerk GJ, Van Den Eijnden RJJM, Vermulst AA, Garretsen
  HFL (2009).  *The Compulsive Internet Use Scale (CIUS):
  Some psychometric properties.*  CyberPsychology & Behavior
  12(1):1-6.  (Original derivation; Dutch adolescent /
  adult sample; Cronbach α = 0.89; single-factor CFA.)
- Young KS (1998).  *Internet addiction: The emergence of a
  new clinical disorder.*  CyberPsychology & Behavior
  1(3):237-244.  (Precursor IAT on which CIUS convergent
  validity is anchored; Griffiths 1998 behavioral-addiction
  criteria used as item-generation frame.)
- Griffiths MD (1998).  *Internet addiction: Does it really
  exist?*  In J. Gackenbach (Ed.), *Psychology and the
  Internet* (pp. 61-75).  Academic Press.  (Behavioral-
  addiction criteria framework — salience, mood
  modification, tolerance, withdrawal, conflict, relapse.
  Direct rationale for CIUS items 6, 12, 13, 14.)
- Caplan SE (2003).  *Preference for online social
  interaction: A theory of problematic Internet use and
  psychosocial well-being.*  Communication Research
  30(6):625-648.  (Compensatory-internet-use theoretical
  model; rationale for FNE-B / UCLA-3 / CIUS triad clinical
  use case.)
- Guertler D, Broda A, Bischof A, Kastirke N, Meyer C,
  John U, Rumpf H-J (2014).  *Factor structure of the
  Compulsive Internet Use Scale.*  Cyberpsychology,
  Behavior, and Social Networking 17(1):46-51.  (German
  n = 2512 sample; confirmed single-factor structure;
  tentative ≥ 21 / ≥ 28 cutpoints — SECONDARY literature,
  NOT pinned here per CLAUDE.md.)
- Koob GF, Le Moal M (2005).  *Plasticity of reward
  neurocircuitry and the "dark side" of drug addiction.*
  Nature Neuroscience 8(11):1442-1444.  (Allostatic
  reward-deficiency theory; cross-addiction compensation;
  rationale for §1 use case 2.)
- American Psychiatric Association (2013).  *Diagnostic
  and Statistical Manual of Mental Disorders, Fifth
  Edition.*  Section III — Internet Gaming Disorder
  (research diagnosis).  (Clinical-parity framing for
  surfacing CIUS alongside substance-use measures.)
- World Health Organization (2019).  *ICD-11 for Mortality
  and Morbidity Statistics.*  6C51 Gaming Disorder.
  (Codified behavioral-addiction parity.)
- Jacobson NS, Truax P (1991).  *Clinical significance:
  A statistical approach to defining meaningful change in
  psychotherapy research.*  Journal of Consulting and
  Clinical Psychology 59(1):12-19.  (RCI applied to raw
  CIUS total at the trajectory layer.)
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

INSTRUMENT_VERSION = "cius-1.0.0"
ITEM_COUNT = 14
ITEM_MIN, ITEM_MAX = 0, 4


# CIUS has ZERO reverse-keyed items — all 14 are negatively
# worded (compulsive-use symptom descriptions).  Meerkerk 2009
# omitted Marsh 1996 balanced-wording to keep the instrument
# within the derivation-cohort's item budget.  Empty tuple
# documents the design decision; changing it would invalidate
# the r = 0.70+ convergent validity with Young 1998 IAT.
CIUS_REVERSE_ITEMS: tuple[int, ...] = ()


class InvalidResponseError(ValueError):
    """Raised on item-count, item-range, or item-type violations."""


Severity = Literal["continuous"]


@dataclass(frozen=True)
class CiusResult:
    """Typed CIUS output.

    Fields:
    - ``total``: 0-56 sum of raw item values.  HIGHER = MORE
      compulsive internet use (lower-is-better direction —
      uniform with PHQ-9 / GAD-7 / AUDIT / PSS-10 / STAI-6 /
      FNE-B / UCLA-3 / SHAPS).
    - ``severity``: literal ``"continuous"`` sentinel.
      Meerkerk 2009 published no cutpoints; Guertler 2014's
      ≥ 21 / ≥ 28 thresholds are secondary literature and
      NOT pinned per CLAUDE.md.
    - ``items``: verbatim 14-tuple of raw 0-4 responses in
      Meerkerk 2009 administration order.  Identical to the
      post-flip values because CIUS has no reverse keying.

    Deliberately-absent fields:
    - No ``subscales`` — CIUS is single-factor per Meerkerk
      2009 CFA and Guertler 2014 replication.
    - No ``positive_screen`` / ``cutoff_used`` — no screen.
    - No ``requires_t3`` — no item probes suicidality.
    """

    total: int
    severity: Severity
    items: tuple[int, ...]
    instrument_version: str = INSTRUMENT_VERSION


def _validate_item(index_1: int, value: object) -> int:
    """Validate a single 0-4 Likert item.

    Bool rejection per CLAUDE.md standing rule: ``bool`` values
    are rejected before the int check because Python's
    ``bool is int`` coercion would silently accept ``True`` /
    ``False`` as item responses.  This matters especially for
    CIUS because ``False → 0`` is a VALID range value ("never")
    — without explicit bool rejection, a serialization bug
    could score ``False`` responses as legitimate "no
    compulsivity" rather than raising an error.
    """
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidResponseError(
            f"CIUS item {index_1} must be int, got {value!r}"
        )
    if not (ITEM_MIN <= value <= ITEM_MAX):
        raise InvalidResponseError(
            f"CIUS item {index_1} must be in {ITEM_MIN}-{ITEM_MAX}, "
            f"got {value}"
        )
    return value


def score_cius(raw_items: Sequence[int]) -> CiusResult:
    """Score a CIUS response set.

    Inputs:
    - ``raw_items``: 14 items, each 0-4 Likert (0 = "Never",
      1 = "Seldom", 2 = "Sometimes", 3 = "Often", 4 = "Very
      often"), in Meerkerk 2009 administration order.

    Raises :class:`InvalidResponseError` on:
    - Wrong number of items (must be exactly 14).
    - A non-int / bool item value.
    - An item outside ``[0, 4]``.

    Computes:
    - Total = sum of raw values (no reverse keying).  Range 0-56.
    - Severity = ``"continuous"`` always.

    Returns a :class:`CiusResult`.
    """
    if not isinstance(raw_items, Sequence) or isinstance(
        raw_items, (str, bytes)
    ):
        raise InvalidResponseError(
            f"CIUS items must be a sequence, got {type(raw_items).__name__}"
        )
    if len(raw_items) != ITEM_COUNT:
        raise InvalidResponseError(
            f"CIUS requires exactly {ITEM_COUNT} items, got {len(raw_items)}"
        )

    validated: tuple[int, ...] = tuple(
        _validate_item(i + 1, v) for i, v in enumerate(raw_items)
    )
    total = sum(validated)

    return CiusResult(
        total=total,
        severity="continuous",
        items=validated,
    )

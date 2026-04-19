"""PGSI — Problem Gambling Severity Index (Ferris & Wynne 2001).

The Problem Gambling Severity Index is the 9-item severity subscale
extracted from the Canadian Problem Gambling Index (CPGI).  It is
the most widely validated population-screening instrument for
disordered gambling — used in the Australian Longitudinal Study of
Problem Gambling, the UK Gambling Commission's Gambling Behaviour in
Great Britain survey, the Canadian Community Health Survey, and as
the screening backbone for most US state problem-gambling
prevalence studies.  Ferris & Wynne 2001 §5 derived the 9 items from
a pool of 31 candidate items via factor analysis + clinician
validation; the 9-item retained set showed superior psychometric
properties (α = 0.84, κ with DSM-IV pathological gambling diagnosis
= 0.83) versus competitor screens (SOGS, DSM-IV items) in the
Canadian population sample (n = 3,120).

Clinical relevance to the Discipline OS platform:

PGSI is the platform's FIRST behavioral-addiction instrument.  Every
instrument shipped prior targets either a substance-use dimension
(AUDIT / AUDIT-C / DAST-10 / DUDIT / SDS / PACS / Craving VAS /
DTCQ-8 / URICA) or an internalizing / regulatory dimension (PHQ-9 /
GAD-7 / PSS-10 / OCI-R / PCL-5 / SHAPS / MAAS / DERS-16).  PGSI
expands the clinical scope to **compulsive-behavior cycles that are
not substance-mediated** — the exact 60-180 s urge-to-action window
the product intervenes on, applied to a non-substance reinforcer.

Gambling co-occurs with substance use disorder at 10-20% in general
population samples (Lorains, Cowlishaw & Thomas 2011 systematic
review) and at 35-60% in clinical SUD samples (Cunningham-Williams
1998; Petry 2005 NESARC).  The reinforcer class differs (variable-
ratio intermittent monetary reward vs pharmacological reward) but
the core behavioral-addiction mechanics converge on:

- intermittent variable-ratio reinforcement (Skinner 1957 schedule
  that produces the most resistant extinction pattern);
- reward-circuit sensitization (Reuter 2005 fMRI; Potenza 2003
  showed ventral striatum activation in problem gamblers parallels
  cocaine-cue activation patterns);
- cue-triggered urge (Sodano 2013 — gambling-cue reactivity parallels
  SUD cue reactivity);
- tolerance / escalation ("needed larger bets for the same
  excitement" = PGSI item 2, direct analogue to DSM-5 SUD
  tolerance criterion);
- loss of control and harm despite consequences (items 1, 4, 8);
- attempts to recover lost ground via the addiction itself
  ("chasing losses" — PGSI item 3, direct analogue to post-SUD-
  lapse escalation patterns Marlatt 1985 described as the
  abstinence-violation effect).

The platform uses PGSI to:

1. **Detect the co-occurring behavioral-addiction profile** at
   enrollment.  A patient whose AUDIT-C is positive AND PGSI is
   moderate-risk or problem-gambler is a dual-addiction profile —
   the gambling dimension commonly goes unmeasured in standard
   substance-focused programs and produces treatment-failure
   patterns when the untreated gambling serves as a substitute
   reinforcer post-abstinence (Petry 2005; Grant 2011 integrated-
   care framework).

2. **Provide a non-substance reinforcer target for users whose
   primary compulsive pattern is gambling**, not substance use.
   Gambling disorder was reclassified from DSM-IV "Impulse Control
   Disorders Not Elsewhere Classified" to DSM-5 "Substance-Related
   and Addictive Disorders" precisely because the behavioral-
   addiction mechanics are indistinguishable from SUD mechanics
   (APA 2013; Petry 2013 reclassification rationale).  The same
   CBT / MI / urge-surfing / contingency-management tools the
   platform deploys for SUD apply to gambling (Petry 2016 CBT
   for problem gambling meta-analysis; Yakovenko 2015 MI
   meta-analysis).

3. **Dose treatment intensity** per Ferris 2001 severity bands.
   Low-risk gambling (PGSI 1-2) receives psychoeducation + brief
   motivational feedback (Cunningham 2014 brief-intervention RCT
   showed sufficiency at this band).  Moderate-risk (3-7) adds
   structured CBT components.  Problem gambling (>= 8) indicates
   referral to specialist behavioral-addiction care with
   consideration of naltrexone pharmacotherapy (Kim 2001;
   Grant 2008 meta-analysis).

Profile pairing with other instruments the platform ships:

- **AUDIT-C / DUDIT + PGSI**: dual-addiction profile.  Integrated
  treatment (Petry 2005) — both addictions treated concurrently
  rather than sequentially, because untreated gambling frequently
  becomes the post-SUD-abstinence substitute reinforcer.
- **ACEs (Sprint 61) + PGSI**: high ACE + positive PGSI = trauma-
  driven behavioral-addiction profile (Felitti 2003 includes
  gambling as an ACE dose-response outcome; Hodgins 2010 trauma-
  gambling causal review).  TIC sequencing applies to gambling
  identically to substance-use disorder.
- **PHQ-9 + PGSI**: depressed-gambler profile.  Kessler 2008
  NCS-R found 38% of problem gamblers have MDD; the depressive
  content often functions as both precedent (pre-gambling negative
  affect) and consequence (post-loss shame) — Hodgins 2005
  recommends concurrent mood treatment rather than gambling-only
  focus.
- **BIS-11 + PGSI**: high impulsivity + positive PGSI = the
  trait-impulsivity-driven gambling profile (Steel & Blaszczynski
  1998; Alessi & Petry 2003).  DBT distress-tolerance skills and
  implementation-intention work are better-fit than exposure-
  centric approaches for this profile.
- **SHAPS (Sprint 60) + PGSI**: positive SHAPS + positive PGSI =
  the anhedonic-compulsive-gambler profile.  Gambling functions
  as reward-recruitment for a hypo-responsive reward system
  (Blaszczynski & Nower 2002 pathways model — Pathway 2 "emotionally
  vulnerable" subtype).  BA + gambling-specific CBT in combination.
- **C-SSRS / PHQ-9 item 9**: problem gamblers have 3.4x elevated
  suicide-attempt risk vs non-gamblers (Moghaddam 2015 meta-
  analysis); acute safety screening continues via C-SSRS / PHQ-9
  item 9 — PGSI item 9 ("felt guilty") is NOT a safety item
  despite the word overlap.

Instrument structure (Ferris & Wynne 2001):

**9 items, each 0-3 Likert**:
- 0 = Never
- 1 = Sometimes
- 2 = Most of the time
- 3 = Almost always

Positional item order (Ferris & Wynne 2001 administration order
preserved):

 1. Bet more than you could really afford to lose
 2. Needed to gamble with larger amounts of money to get the same
    feeling of excitement (tolerance)
 3. Gone back another day to try to win back the money you lost
    (chasing losses)
 4. Borrowed money or sold anything to get money to gamble
 5. Felt that you might have a problem with gambling
 6. Gambling caused you any health problems, including stress or
    anxiety
 7. People criticized your betting or told you that you had a
    gambling problem, regardless of whether or not you thought it
    was true
 8. Gambling caused any financial problems for you or your
    household
 9. Felt guilty about the way you gamble or what happens when you
    gamble

All 9 items are worded in a unidirectional (higher = more problem)
direction — no reverse scoring.  Total = sum of 9 items, 0-27.

**Severity bands (Ferris & Wynne 2001 §5, Table 5.1):**

    0     Non-problem gambler
    1-2   Low-risk gambler
    3-7   Moderate-risk gambler
    8-27  Problem gambler

The bands are population-derived operating points against the
Canadian community sample's SOGS / DSM-IV concurrent criterion
(Ferris 2001 Table 4.5: kappa with DSM-IV pathological gambling =
0.83 at the >= 8 cutoff; sensitivity 0.83, specificity 0.92).
Currie 2013 re-analysis of the Canadian sample (n = 12,229 across
4 population surveys) confirmed the cut-points; Williams & Volberg
2014 recommended no revision.  The cut-points are pinned as
``PGSI_SEVERITY_THRESHOLDS`` — hand-rolling alternative cutoffs
violates CLAUDE.md's "Don't hand-roll severity thresholds" rule.

**Novel wire contributions on this platform:**

First **behavioral-addiction severity-banded** instrument.  AUDIT
is also 4-band (low-risk / increasing-risk / high-risk / possible-
dependence per Saunders 1993) but targets substance use.  PGSI
is the first non-substance severity-banded instrument on the
platform — the wire envelope matches AUDIT-pattern (total + band)
rather than screen-pattern (AUDIT-C / PC-PTSD-5 / OCI-R) or
cutoff-pattern (SHAPS / ACEs).

Higher-is-worse direction — trajectory-layer RCI direction logic
must register PGSI in the higher-is-worse partition alongside
PHQ-9 / GAD-7 / PSS-10 / K6 / SHAPS / ACEs, NOT with WHO-5 / MAAS /
CD-RISC-10 (higher-is-better).

Safety routing:

PGSI has NO acute-safety item.  Item 5 ("felt you might have a
problem with gambling") and item 9 ("felt guilty about the way
you gamble") are problem-awareness / affect items, not
suicide-ideation / self-harm items.  Acute ideation screening
stays on C-SSRS / PHQ-9 item 9.  ``requires_t3`` is hard-coded
``False`` at the router.  A positive PGSI is a *referral signal*
for behavioral-addiction care (specialist or integrated SUD/
gambling program), not a crisis signal.  The well-established
problem-gambler-suicide-risk association (Moghaddam 2015 meta-
analysis 3.4x elevated attempt risk) is handled at the PROFILE
level (PGSI + PHQ-9 + C-SSRS), not via per-PGSI-item T3
triggering.

References:

- Ferris J, Wynne H (2001).  *The Canadian Problem Gambling
  Index: Final Report.*  Canadian Centre on Substance Abuse,
  Ottawa.  (PRIMARY — 9-item PGSI derivation; bands 0 / 1-2 /
  3-7 / 8+; n = 3,120 Canadian community sample.)
- Currie SR, Hodgins DC, Casey DM (2013).  *Validity of the
  Problem Gambling Severity Index interpretive categories.*
  Journal of Gambling Studies 29(2):311-327.  (Confirmed the
  3-7 moderate-risk / 8+ problem-gambler cut-points across
  n = 12,229 Canadian surveys.)
- Williams RJ, Volberg RA (2014).  *The classification accuracy
  of four problem gambling assessment instruments in population
  research.*  International Gambling Studies 14(1):15-28.
  (Comparative validity — PGSI best classification accuracy
  among SOGS, NODS, CPGI short-form, and PGSI in population
  research contexts.)
- Lorains FK, Cowlishaw S, Thomas SA (2011).  *Prevalence of
  comorbid disorders in problem and pathological gambling:
  Systematic review and meta-analysis of population surveys.*
  Addiction 106(3):490-498.  (Epi — PGSI-positive prevalence
  of SUD and mood disorders; basis for dual-addiction framing.)
- Petry NM, Stinson FS, Grant BF (2005).  *Comorbidity of DSM-IV
  pathological gambling and other psychiatric disorders:
  Results from the National Epidemiologic Survey on Alcohol and
  Related Conditions.*  Journal of Clinical Psychiatry 66(5):
  564-574.  (NESARC comorbidity — 73% of pathological gamblers
  have lifetime alcohol use disorder.)
- Potenza MN, Steinberg MA, Skudlarski P, Fulbright RK, Lacadie
  CM, Wilber MK, Rounsaville BJ, Gore JC, Wexler BE (2003).
  *Gambling urges in pathological gambling: A functional magnetic
  resonance imaging study.*  Archives of General Psychiatry
  60(8):828-836.  (Ventral-striatum activation to gambling cues
  mirrors cocaine-cue activation — neural basis for behavioral-
  addiction reclassification.)
- American Psychiatric Association (2013).  *Diagnostic and
  Statistical Manual of Mental Disorders (DSM-5).*  Washington,
  DC.  (Reclassification of pathological gambling to "Substance-
  Related and Addictive Disorders" — gambling disorder.)
- Petry NM, Blanco C, Auriacombe M, Borges G, Bucholz K, Crowley
  TJ, Grant BF, Hasin DS, O'Brien C (2013).  *An overview of and
  rationale for changes proposed for pathological gambling in
  DSM-5.*  Journal of Gambling Studies 30(2):493-502.
  (Reclassification rationale.)
- Blaszczynski A, Nower L (2002).  *A pathways model of problem
  and pathological gambling.*  Addiction 97(5):487-499.
  (Three-pathway etiology — behaviorally-conditioned,
  emotionally-vulnerable, antisocial-impulsivist subtypes;
  basis for profile-pairing treatment selection.)
- Petry NM, Ginley MK, Rash CJ (2016).  *A systematic review of
  treatments for problem gambling.*  Psychology of Addictive
  Behaviors 31(8):951-961.  (CBT / MI / pharmacotherapy
  evidence base for PGSI-banded treatment dosing.)
- Moghaddam JF, Yoon G, Dickerson DL, Kim SW, Westermeyer J
  (2015).  *Suicidal ideation and suicide attempts in five groups
  with different severities of gambling: Findings from the
  National Epidemiologic Survey on Alcohol and Related
  Conditions.*  American Journal of Addictions 24(4):292-298.
  (3.4x suicide-attempt-risk elevation in problem gamblers —
  basis for profile-level safety framing rather than per-PGSI-
  item T3 triggering.)
- Hodgins DC, Peden N (2010).  *Natural course of gambling
  disorders: Forty-month follow-up.*  Journal of Gambling
  Issues 25:1-20.  (Recovery trajectories; framing for
  longitudinal PGSI re-administration.)
- Cunningham JA, Hodgins DC, Toneatto T (2014).  *A randomized
  controlled trial of a personalized feedback intervention for
  problem gamblers.*  PLoS ONE 9(2):e86616.  (Brief-intervention
  sufficiency at low-risk band.)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence

INSTRUMENT_VERSION = "pgsi-1.0.0"
ITEM_COUNT = 9
ITEM_MIN, ITEM_MAX = 0, 3


# Published severity thresholds per Ferris & Wynne 2001 §5 Table 5.1;
# confirmed by Currie 2013 (n = 12,229) and Williams & Volberg 2014.
# Tuple pairs are (upper-inclusive bound, band label) — classify
# picks the FIRST label whose bound >= total.  Changing these values
# is a clinical decision, not an implementation tweak — they are the
# population-derived operating points against DSM-IV pathological-
# gambling diagnosis (Ferris 2001 kappa = 0.83 at the >= 8 cutoff).
PGSI_SEVERITY_THRESHOLDS: tuple[tuple[int, str], ...] = (
    (0, "non_problem"),
    (2, "low_risk"),
    (7, "moderate_risk"),
    (27, "problem_gambler"),
)


class InvalidResponseError(ValueError):
    """Raised on item-count, item-range, or item-type violations."""


Severity = Literal[
    "non_problem",
    "low_risk",
    "moderate_risk",
    "problem_gambler",
]


@dataclass(frozen=True)
class PgsiResult:
    """Typed PGSI output.

    Fields:
    - ``total``: 0-27, straight sum of the 9 items.  Higher = more
      gambling problem severity.  Flows into the FHIR Observation's
      ``valueInteger``.
    - ``severity``: one of the four Ferris & Wynne 2001 bands
      ("non_problem" / "low_risk" / "moderate_risk" /
      "problem_gambler").
    - ``items``: verbatim 9-tuple of raw Likert responses, pinned
      for auditability and FHIR export.

    Deliberately-absent fields:
    - No ``positive_screen`` / ``cutoff_used`` — PGSI is banded
      (4 bands), not binary screen (uniform with PHQ-9 / GAD-7 /
      AUDIT banded pattern, NOT AUDIT-C / PC-PTSD-5 / SHAPS /
      ACEs screen pattern).  The clinically-meaningful information
      is the 4-way category, not a binary above/below cutoff.
    - No ``subscales`` — PGSI is unidimensional by design.
      Ferris 2001 §5 extracted the 9-item set via factor analysis
      from a 31-item pool precisely to retain a single-factor
      severity dimension; surfacing subscales would contradict
      the derivation.
    - No ``requires_t3`` field — PGSI probes gambling severity,
      not current ideation; no item is a safety item.  Acute-risk
      screening stays on C-SSRS / PHQ-9 item 9.
    """

    total: int
    severity: Severity
    items: tuple[int, ...]
    instrument_version: str = INSTRUMENT_VERSION


def _classify(total: int) -> Severity:
    """Map a total to a Ferris & Wynne 2001 severity band."""
    for upper, label in PGSI_SEVERITY_THRESHOLDS:
        if total <= upper:
            return label  # type: ignore[return-value]
    # Unreachable — classified list ends at 27.
    raise InvalidResponseError(f"total out of range: {total}")


def _validate_item(index_1: int, value: object) -> int:
    """Validate a single 0-3 Likert item.

    ``index_1`` is the 1-indexed item number (1-9) so error messages
    name the item a clinician would recognize from the Ferris &
    Wynne 2001 administration order.

    Bool rejection per CLAUDE.md standing rule: ``bool`` values are
    rejected before the int check because Python's ``bool is int``
    coercion would silently accept ``True`` / ``False`` as item
    responses.
    """
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidResponseError(
            f"PGSI item {index_1} must be int, got {value!r}"
        )
    if not (ITEM_MIN <= value <= ITEM_MAX):
        raise InvalidResponseError(
            f"PGSI item {index_1} must be in {ITEM_MIN}-{ITEM_MAX}, "
            f"got {value}"
        )
    return value


def score_pgsi(raw_items: Sequence[int]) -> PgsiResult:
    """Score a PGSI response set.

    Inputs:
    - ``raw_items``: 9 integers, each 0-3 (Never / Sometimes /
      Most of the time / Almost always), positional per Ferris &
      Wynne 2001 administration order.

    Raises :class:`InvalidResponseError` on:
    - Wrong number of items (must be exactly 9).
    - A non-int / bool item value.
    - An item value outside the 0-3 Likert range.

    Computes:
    - ``total``: straight sum of the 9 items, 0-27.
    - ``severity``: four-band classification per Ferris & Wynne
      2001 thresholds.
    """
    if len(raw_items) != ITEM_COUNT:
        raise InvalidResponseError(
            f"PGSI requires exactly {ITEM_COUNT} items, got {len(raw_items)}"
        )
    items = tuple(
        _validate_item(index_1=i + 1, value=v)
        for i, v in enumerate(raw_items)
    )
    total = sum(items)
    severity = _classify(total)

    return PgsiResult(
        total=total,
        severity=severity,
        items=items,
    )


__all__ = [
    "INSTRUMENT_VERSION",
    "ITEM_COUNT",
    "ITEM_MAX",
    "ITEM_MIN",
    "InvalidResponseError",
    "PGSI_SEVERITY_THRESHOLDS",
    "PgsiResult",
    "Severity",
    "score_pgsi",
]

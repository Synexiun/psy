"""ACEs — Adverse Childhood Experiences Questionnaire (Felitti 1998).

The ACEs Questionnaire is the instrument originally administered in
the landmark Kaiser Permanente / U.S. CDC Adverse Childhood
Experiences Study (Felitti et al. 1998; n = 17,337 adult HMO members)
that established the dose-response relationship between childhood
adversity and essentially every major adult health outcome —
including, most load-bearing for this platform, substance use
disorder (SUD) initiation, severity, and relapse across every
substance class examined.

Clinical relevance to the Discipline OS platform:

ACEs is the **etiological-stratification** instrument.  Where every
other instrument the platform ships measures a *current state* (PHQ-9
current depression, SHAPS current anhedonia, MAAS current mindful
attention), ACEs measures a *historical exposure* — the cumulative
count of before-age-18 adversity categories the patient was subject
to.  That historical exposure is among the single strongest
predictors of adult SUD:

- Felitti 1998 §Results: ACE count ≥ 4 = 4.7× alcoholism risk,
  10.3× injection drug use risk, 2.9× lifetime smoking initiation,
  2.5× adult suicide-attempt risk — all compared to ACE = 0.
- Dube 2003 §Discussion: the dose-response survives adjustment for
  adult income, education, current mental health, and current
  substance use — ACE exposure predicts SUD independent of every
  adult confounder tested.
- Anda 2006 neurobiological review: HPA-axis dysregulation, prefrontal
  / limbic maturation disruption, and reward-circuit hyposensitivity
  are the proximate mechanisms linking childhood adversity to adult
  compulsive behavior.
- Hughes 2017 international meta-analysis (n = 253,719 across 37
  studies): ACE ≥4 = 7.4× problem drinking risk, 10.2× problem drug
  use risk — replicating Felitti 1998 across high-, middle-, and
  low-income-country samples.

The platform uses the ACE score to **stratify treatment sequencing
at enrollment**.  A patient with ACE ≥ 4 is routed to **trauma-
informed-care (TIC) sequencing** BEFORE standard CBT-based
relapse-prevention intervention.  Skipping this stratification
produces predictable treatment-failure patterns:

- A patient with unprocessed childhood trauma and high ACE score
  entering standard exposure / cue-exposure work often dissociates
  during exposure sessions — exposure fails because the patient is
  not present to habituate.
- A patient with emotional-abuse ACE content entering cognitive-
  restructuring work frequently mis-categorizes internal self-talk
  as "realistic self-criticism" rather than a trauma-driven
  automatic pattern — the restructuring step mis-anchors against a
  trauma schema.
- A patient with household-substance-abuse ACE content frequently
  experiences normalization / identification with the substance as
  the attachment figure — naïve "substance = enemy" framing
  under-treats this attachment-replacement dimension (van der Kolk
  2014; Khantzian 1997 self-medication hypothesis).

Profile pairing with other instruments the platform ships:

- **SHAPS (Sprint 60)**: high ACE + positive SHAPS = the
  developmental-anhedonia profile (Anda 2006 — childhood adversity
  produces stable reward-circuit hypofunction).  Treatment: BA +
  TIC in combination, NOT mindfulness-only (Bowen 2014 MBRP is
  contraindicated as standalone for this subtype; Briere 2012
  recommends TIC precedence).
- **MAAS (Sprint 59)**: high ACE + low MAAS = the
  dissociative-attention profile — the patient cannot attend to
  present-moment experience because present-moment attention
  triggers trauma cue-reactivity.  Grounding / 5-4-3-2-1 sensory
  tools BEFORE open-awareness meditation (MBSR/MBRP-style).
- **DERS-16 (Sprint 53)**: high ACE + high DERS nonacceptance =
  the chronic-dysregulation profile — emotion dysregulation as
  trauma sequela (van der Kolk 2014 developmental-trauma
  framework).  DBT skills-first sequencing (Linehan 1993) BEFORE
  insight-oriented work.
- **PCL-5**: high ACE + positive PCL-5 = the chronic PTSD
  profile — trauma-focused therapy (PE / CPT / EMDR) is indicated
  but requires the stabilization-phase Herman 1992 three-stage
  model specifies before direct trauma-processing can be
  productive.
- **AUDIT-C / DUDIT**: high ACE + positive SUD screen = the
  self-medication profile (Khantzian 1997) — integrated trauma/
  SUD treatment (Najavits 2002 Seeking Safety) indicated rather
  than sequential SUD-first-then-trauma work, because the SUD is
  functioning as the trauma-management strategy.
- **C-SSRS / PHQ-9 item 9**: high ACE + positive suicidality
  screen requires coordinated safety planning beyond per-
  instrument response — ACEs are a persistent lifetime
  suicide-risk multiplier (Dube 2001; Felitti 2003), not a
  time-limited current-state signal.

Instrument structure (Felitti 1998):

**10 items, each binary (0 = No, 1 = Yes)**.  Items ask whether
the respondent experienced the named category of adversity at any
point before age 18.

Positional item order (Felitti 1998 Appendix A, administration
order preserved):

 1. Emotional abuse — "Did a parent or other adult in the
    household often or very often swear at you, insult you,
    put you down, or humiliate you?  Or act in a way that made
    you afraid that you might be physically hurt?"
 2. Physical abuse — "Did a parent or other adult in the
    household often or very often push, grab, slap, or throw
    something at you?  Or ever hit you so hard that you had
    marks or were injured?"
 3. Sexual abuse — "Did an adult or person at least 5 years
    older than you ever touch or fondle you or have you touch
    their body in a sexual way?  Or attempt or actually have
    oral, anal, or vaginal intercourse with you?"
 4. Emotional neglect — "Did you often or very often feel that
    no one in your family loved you or thought you were
    important or special?  Or your family didn't look out for
    each other, feel close to each other, or support each
    other?"
 5. Physical neglect — "Did you often or very often feel that
    you didn't have enough to eat, had to wear dirty clothes,
    and had no one to protect you?  Or your parents were too
    drunk or high to take care of you or take you to the
    doctor if you needed it?"
 6. Mother treated violently — "Was your mother or stepmother
    often or very often pushed, grabbed, slapped, or had
    something thrown at her?  Or sometimes, often, or very
    often kicked, bitten, hit with a fist, or hit with
    something hard?  Or ever repeatedly hit over at least a
    few minutes, or threatened with a gun or knife?"
 7. Household substance abuse — "Did you live with anyone who
    was a problem drinker or alcoholic, or who used street
    drugs?"
 8. Household mental illness — "Was a household member
    depressed or mentally ill, or did a household member
    attempt suicide?"
 9. Parental separation or divorce — "Were your parents ever
    separated or divorced?"
10. Incarcerated household member — "Did a household member
    go to prison?"

The 10 items cluster conceptually into three domains — abuse
(items 1-3), neglect (items 4-5), household dysfunction (items
6-10) — but Felitti 1998 and every major replication (Dong 2004;
Dube 2003; Hughes 2017) score the instrument as a single total.
The three-domain grouping is a conceptual organization for
descriptive reporting, NOT a psychometrically-partitioned
subscale structure with validated clinical cutoffs at the
subscale level.

Dong 2004 confirmed single-factor structure at the total-score
level and rejected three-factor models (abuse / neglect /
dysfunction) as producing unstable per-domain cutoffs.  The
platform therefore emits NO subscale fields on the wire —
surfacing a subscales map would create the false impression of
validated per-domain cutoffs where only the total-score cutoff
is validated.

**Scoring (Felitti 1998):**

Total = sum of the 10 binary items, range 0-10.  Higher = more
adversity (higher-is-worse direction).  No reverse items, no
Likert — pure binary summation.

**Positive-screen cutoff** (Felitti 1998 §Results):

    total >= 4  →  positive_screen (high adversity exposure)
    total <  4  →  negative_screen

Felitti 1998 selected ACE ≥ 4 as the operating point at which
multiple adult-health outcomes (alcoholism, illicit drug use,
depression, suicide attempt, smoking) show ≥ 4× relative risk
compared to ACE = 0.  Dong 2004 and Hughes 2017 confirmed the
same operating point internationally.  The cutoff is exposed as
a module constant ``ACES_POSITIVE_CUTOFF = 4`` and surfaced in
the router's ``cutoff_used`` field (uniform with SHAPS / OCI-R /
MDQ / PC-PTSD-5 / AUDIT-C wire semantics).

**Novel wire contributions on this platform:**

1. First BINARY-item instrument.  Every prior scorer accepts a
   Likert range (0-3 PHQ-9, 0-4 OCI-R, 1-4 SHAPS, 1-6 MAAS, 1-7
   ERQ).  ACEs accepts only ``0`` or ``1``; any other value —
   including values in range but not binary (e.g. 2, 3) — is a
   validation error.  The ``_validate_item`` path checks both
   type (int / not-bool) AND binary-value constraint.  A
   refactor that loosened the binary check to a ``0 <= v <= 10``
   range check would silently accept out-of-structure values.

2. First RETROSPECTIVE (historical) instrument.  Every prior
   instrument measures current state (past 2 weeks for PHQ-9,
   past month for OCI-R, past week for SHAPS, dispositional-
   current for MAAS).  ACEs measures lifetime exposure before
   age 18 — a one-time stratification measurement rather than a
   trajectory-tracking repeated measure.  The trajectory layer
   therefore treats ACEs specially: one administration per
   patient at enrollment; re-administration is not clinically
   meaningful (the count can only go up as the patient recalls
   additional items, and Felitti 1998 found test-retest at 1.5
   years was r = 0.66 — partly re-measurement error, partly
   genuine memory recovery).  Upstream trajectory logic handles
   this — the scorer itself is stateless and does not
   differentiate.

Higher-is-worse direction — trajectory-layer RCI direction logic
must register ACEs in the higher-is-worse partition alongside
PHQ-9 / GAD-7 / PSS-10 / K6 / SHAPS, NOT with WHO-5 / MAAS /
CD-RISC-10 (higher-is-better).

Safety routing:

ACEs has NO acute-safety item.  Every item asks about events
BEFORE age 18 (retrospective), not current ideation, current
behavior, or current risk.  A patient with ACE = 10 is a
clinically-elevated-risk profile, but that elevation is
DISPOSITIONAL risk across the patient's lifespan, not
time-limited current-state crisis.  Acute ideation screening
stays on C-SSRS / PHQ-9 item 9.  ``requires_t3`` is hard-coded
``False`` at the router.

Content-sensitivity note:

Items 1-3 (abuse) and item 6 (witnessing maternal violence) are
content-sensitive — the administration UI renders a content
warning and an opt-out before presentation, and provides
immediate post-administration support resources.  This is a
UI-layer concern handled in the web-app / mobile surfaces, not
a scorer-layer concern.  The scorer accepts any well-formed
10-binary-item input; the UI is responsible for informed
consent and aftercare.

Bool rejection note:

Even though the item values ARE binary (0/1), the platform's
uniform convention is to reject ``bool`` values at the
validator and require explicit ``int`` 0 or 1.  This is
because Python's ``bool is int`` coercion would silently
accept ``True`` / ``False`` — a caller submitting boolean
shorthand for "yes / no" would pass validation without
explicit type commitment, and any future refactor that
widened the accepted value range would have no type signal
to reject the boolean shorthand.  See CLAUDE.md "bool
rejection" standing rule.

References:

- Felitti VJ, Anda RF, Nordenberg D, Williamson DF, Spitz AM,
  Edwards V, Koss MP, Marks JS (1998).  *Relationship of
  childhood abuse and household dysfunction to many of the
  leading causes of death in adults: The Adverse Childhood
  Experiences (ACE) Study.*  American Journal of Preventive
  Medicine 14(4):245-258.  (PRIMARY — 17,337 Kaiser HMO
  members; dose-response across 10+ outcome variables;
  cutoff >= 4 established.)
- Dube SR, Felitti VJ, Dong M, Chapman DP, Giles WH, Anda RF
  (2003).  *Childhood abuse, neglect, and household
  dysfunction and the risk of illicit drug use: The Adverse
  Childhood Experiences Study.*  Pediatrics 111(3):564-572.
  (SUD-specific replication — drug use onset, lifetime use,
  and recent problematic use all dose-response to ACE count.)
- Dube SR, Anda RF, Felitti VJ, Edwards VJ, Croft JB (2002).
  *Adverse childhood experiences and personal alcohol abuse
  as an adult.*  Addictive Behaviors 27(5):713-725.
  (Alcohol-specific dose-response validation.)
- Dube SR, Anda RF, Felitti VJ, Chapman DP, Williamson DF,
  Giles WH (2001).  *Childhood abuse, household dysfunction,
  and the risk of attempted suicide throughout the life
  span.*  JAMA 286(24):3089-3096.  (Lifetime suicide-risk
  dose-response.)
- Anda RF, Felitti VJ, Bremner JD, Walker JD, Whitfield C,
  Perry BD, Dube SR, Giles WH (2006).  *The enduring effects
  of abuse and related adverse experiences in childhood: A
  convergence of evidence from neurobiology and
  epidemiology.*  European Archives of Psychiatry and
  Clinical Neuroscience 256(3):174-186.  (Mechanism review —
  HPA-axis, prefrontal / limbic development, reward-circuit
  hypofunction.)
- Dong M, Anda RF, Felitti VJ, Dube SR, Williamson DF,
  Thompson TJ, Loo CM, Giles WH (2004).  *The interrelatedness
  of multiple forms of childhood abuse, neglect, and
  household dysfunction.*  Child Abuse & Neglect 28(7):
  771-784.  (Factor-structure analysis — single-factor
  total-score validity; rejection of three-subscale model.)
- Hughes K, Bellis MA, Hardcastle KA, Sethi D, Butchart A,
  Mikton C, Jones L, Dunne MP (2017).  *The effect of
  multiple adverse childhood experiences on health: A
  systematic review and meta-analysis.*  Lancet Public Health
  2(8):e356-e366.  (Meta-analysis — 37 studies, n = 253,719;
  confirms dose-response internationally; ACE >= 4 = 7.4×
  problem drinking, 10.2× problem drug use.)
- van der Kolk BA (2014).  *The Body Keeps the Score: Brain,
  Mind, and Body in the Healing of Trauma.*  Viking.
  (Clinical-literature integration — developmental-trauma
  framework underlying TIC sequencing.)
- Khantzian EJ (1997).  *The self-medication hypothesis of
  substance use disorders: A reconsideration and recent
  applications.*  Harvard Review of Psychiatry 4(5):231-244.
  (Self-medication mechanism — trauma → SUD causal pathway.)
- Najavits LM (2002).  *Seeking Safety: A Treatment Manual
  for PTSD and Substance Abuse.*  Guilford.  (Integrated
  trauma/SUD treatment manual — indicated for high-ACE +
  positive-SUD-screen profile.)
- Briere J, Scott C (2012).  *Principles of Trauma Therapy:
  A Guide to Symptoms, Evaluation, and Treatment.*  SAGE.
  (TIC-sequencing rationale — stabilization before trauma-
  processing for high-ACE presentations.)
- Herman JL (1992).  *Trauma and Recovery.*  Basic Books.
  (Three-stage-model safety / remembrance / reconnection
  — prerequisite for productive trauma-focused therapy.)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence

INSTRUMENT_VERSION = "aces-1.0.0"
ITEM_COUNT = 10
ITEM_MIN = 0
ITEM_MAX = 1

# Published positive-screen cutoff per Felitti 1998 §Results.  ACE
# count >= 4 is the operating point at which multiple adult-health
# outcomes show >= 4x relative risk vs ACE = 0.  Exposed as a module
# constant so trajectory-layer RCI thresholding and the clinician-UI
# render path both key off one source-of-truth.  Changing this is
# a clinical decision, not an implementation tweak.
ACES_POSITIVE_CUTOFF = 4


Screen = Literal["positive_screen", "negative_screen"]


class InvalidResponseError(ValueError):
    """Raised on item-count, item-range, or item-type violations."""


@dataclass(frozen=True)
class AcesResult:
    """Typed ACEs output.

    Fields:
    - ``total``: 0-10, count of endorsed adversity categories.
      Higher = more adversity.  Flows into the FHIR Observation's
      ``valueInteger``.
    - ``positive_screen``: ``True`` iff ``total >= 4`` per Felitti
      1998.  Uniform with SHAPS / OCI-R / MDQ / PC-PTSD-5 /
      AUDIT-C wire shape.
    - ``items``: verbatim 10-tuple of binary inputs, pinned for
      auditability AND for downstream consumers (clinical UI
      rendering specific endorsed categories; FHIR export; the
      trajectory layer's special-case one-time-measurement
      handling).

    Deliberately-absent fields:
    - No ``severity`` field — the router emits the
      positive/negative_screen string via its envelope, uniform
      with SHAPS / OCI-R / MDQ / PC-PTSD-5 / AUDIT-C.  Felitti
      1998 / Dong 2004 did not publish additional severity
      bands beyond the ≥4 cutoff; the cumulative-risk gradient
      above 4 is a continuous phenomenon, not a banded one.
      Hand-rolling additional bands (e.g. "severe" at ≥7) would
      violate CLAUDE.md's "Don't hand-roll severity thresholds"
      rule.
    - No ``subscales`` — Dong 2004 confirmed single-factor
      structure at the total-score level and rejected the
      three-subscale (abuse / neglect / dysfunction) model as
      producing unstable per-domain cutoffs.  Surfacing a
      subscale map on the wire would create the false
      impression of validated per-domain cutoffs.
    - No ``requires_t3`` field — ACEs probes retrospective
      childhood exposure, not current ideation; no item is a
      safety item.  Acute-risk screening stays on C-SSRS /
      PHQ-9 item 9.
    """

    total: int
    positive_screen: bool
    items: tuple[int, ...]
    instrument_version: str = INSTRUMENT_VERSION


def _validate_item(index_1: int, value: object) -> int:
    """Validate a single binary ACE item and return the int value.

    ``index_1`` is the 1-indexed item number (1-10) so error
    messages name the item a clinician would recognize from the
    Felitti 1998 administration order (emotional abuse / physical
    abuse / sexual abuse / emotional neglect / physical neglect /
    maternal violence witnessing / household substance abuse /
    household mental illness / parental separation / incarcerated
    household member).

    Three-layer validation:
    1. Bool rejection (uniform with the rest of the psychometric
       package — see CLAUDE.md standing rule).
    2. Type must be int (not float, not str).
    3. Value must be exactly 0 or 1 — NOT just "in a range".
       A bare ``0 <= v <= 10`` check would silently accept 2, 3,
       etc. and pass them through to the sum, producing a total
       that mis-represents the endorsed-item-count semantic.
    """
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidResponseError(
            f"ACEs item {index_1} must be int, got {value!r}"
        )
    if value != 0 and value != 1:
        raise InvalidResponseError(
            f"ACEs item {index_1} must be binary (0 or 1), got {value}"
        )
    return value


def score_aces(raw_items: Sequence[int]) -> AcesResult:
    """Score an ACEs response set.

    Inputs:
    - ``raw_items``: 10 binary integers, each 0 (No) or 1 (Yes),
      positional per Felitti 1998 administration order.

    Raises :class:`InvalidResponseError` on:
    - Wrong number of items (must be exactly 10).
    - A non-int / bool item value.
    - An item value other than 0 or 1 (including integers within
      the range 2-10 that would pass a loose range-check).

    Computes:
    - ``total``: straight sum of the 10 binary items, 0-10.
    - ``positive_screen``: ``total >= 4``.
    """
    if len(raw_items) != ITEM_COUNT:
        raise InvalidResponseError(
            f"ACEs requires exactly {ITEM_COUNT} items, got {len(raw_items)}"
        )
    items = tuple(
        _validate_item(index_1=i + 1, value=v)
        for i, v in enumerate(raw_items)
    )
    total = sum(items)
    positive_screen = total >= ACES_POSITIVE_CUTOFF

    return AcesResult(
        total=total,
        positive_screen=positive_screen,
        items=items,
    )


__all__ = [
    "ACES_POSITIVE_CUTOFF",
    "AcesResult",
    "INSTRUMENT_VERSION",
    "InvalidResponseError",
    "ITEM_COUNT",
    "ITEM_MAX",
    "ITEM_MIN",
    "Screen",
    "score_aces",
]

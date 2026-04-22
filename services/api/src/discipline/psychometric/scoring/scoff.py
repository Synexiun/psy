"""SCOFF — 5-item eating-disorder screen (Morgan, Reid & Lacey 1999).

The SCOFF is a 5-item yes/no screening questionnaire for anorexia
nervosa and bulimia nervosa, developed by John Morgan and colleagues
at St George's Hospital London and published in BMJ in 1999.  The
acronym is a mnemonic for the five question-cue words:

- **S**ick:   "Do you make yourself **S**ick because you feel
              uncomfortably full?"
- **C**ontrol: "Do you worry you have lost **C**ontrol over how
              much you eat?"
- **O**ne:    "Have you recently lost more than **O**ne stone
              (6.35 kg / 14 lb) in a 3-month period?"
- **F**at:    "Do you believe yourself to be **F**at when others
              say you are too thin?"
- **F**ood:   "Would you say that **F**ood dominates your life?"

The instrument was deliberately designed for **rapid primary-care
screening** — Morgan 1999 Methods §2 explicitly framed it against
the EAT-26 (Garner 1982, 26 items, Likert) and BITE (Henderson &
Freeman 1987, 33 items) as a gain-on-speed instrument that could
be administered in under one minute in a GP consultation.  The
5-item binary structure was not factor-analytically derived but
**clinically derived** — the authors consulted ED specialists to
identify the five "highest-yield" screening cues from a longer
candidate pool, then validated the result against CASE-REFERENT
status (DSM-III-R AN/BN clinical diagnosis) in n = 116 (68 ED
cases / 48 controls).

Morgan 1999 Results §3: at the >= 2 positive-items cutoff, SCOFF
produced **100% sensitivity and 87.5% specificity** against the
clinical reference standard.  Cotton 2003 replicated in primary
care (n = 233 women aged 18-50) with **sens 100% / spec 89.6%** —
the operating point held in an unselected community sample.
Solmi 2015 meta-analysis of 25 validation studies (n = 26,488)
confirmed the >= 2 cutoff as the pooled optimal threshold (AUC
0.89; pooled sens 0.86, spec 0.83) across primary-care, student,
and clinical populations.

Clinical relevance to the Discipline OS platform:

Eating disorders are a **clearly-missed domain** in the platform's
current instrument coverage.  Every prior scorer targets
substance use (AUDIT / AUDIT-C / DAST-10 / DUDIT / SDS / PACS /
Craving VAS / DTCQ-8 / URICA), an internalizing / regulatory
dimension (PHQ-9 / GAD-7 / PSS-10 / OCI-R / PCL-5 / SHAPS /
MAAS / DERS-16), a behavioral addiction (PGSI), trauma (ACEs /
PC-PTSD-5), or resilience (CD-RISC-10 / BRS).  None cover
disordered eating.

This is a real clinical gap.  Eating disorders co-occur with
substance use disorder at 25-50% in clinical SUD samples
(Hudson 2007 NCS-R: 23.7% lifetime AN/BN comorbidity among SUD;
Krug 2008 European multi-site n = 879: 45% lifetime SUD among
AN/BN).  The behavioral-addiction mechanics overlap substantially
(restraint-binge cycle in BN parallels abstinence-violation
effect in SUD; reward-prediction-error dysfunction in AN parallels
anhedonia profiles; compulsive cue-driven behavior patterns
converge — Kaye 2013 neurobiological review).  The platform's
60-180 s urge-to-action intervention window applies identically
to binge-eating urges as to substance-use urges and gambling
urges (Jansen 2016 binge-cue reactivity review).

Profile pairings enabled by shipping SCOFF:

- **SCOFF+ alone** → primary ED pathway (clinical assessment
  referral; CBT-E per Fairburn 2008 is first-line evidence-
  based intervention for BN / BED; specialist AN care per
  APA 2006 practice guideline).
- **SCOFF+ AND AUDIT+** → co-occurring ED/SUD profile.  Krug
  2008 documented 45% comorbidity; treatment sequencing
  matters (concurrent integrated treatment per Harrop & Marlatt
  2010, not substance-first then ED).
- **SCOFF+ AND PHQ-9 item-3 positive** (appetite change) →
  resolves the ED-vs-MDD appetite-change ambiguity.  PHQ-9
  item 3 reads both directions; SCOFF positivity points at
  disordered-eating mechanism over depression-driven appetite
  loss.
- **SCOFF+ AND ACEs >= 4** → trauma-driven ED profile.  Brewerton
  2007 meta-analysis: childhood abuse is a consistent risk
  factor for ED; trauma-informed sequencing per van der Kolk
  2014 applies.
- **SCOFF+ AND BIS-11 high** → impulsive binge-purge profile
  (Claes 2005).  DBT-adapted-for-ED per Safer 2009 is the
  matched intervention.
- **SCOFF+ AND OCI-R high** → obsessive-compulsive-type
  restriction profile.  AN shares neurobiological features with
  OCD (Godier 2014) — intervention framing differs from the
  impulsive binge profile.

Platform non-negotiables enforced by this module:

1. **Verbatim item text from Morgan 1999.**  No paraphrase, no
   machine translation.  The "One stone" unit in item 3 is
   LOCALE-SENSITIVE — the published instrument uses imperial
   stones; non-UK locales must present a validated-translation
   version with culturally-appropriate mass unit (6.35 kg for
   EU/SI locales; 14 lb for US locale — Kutz 2020 German
   adaptation validated the kg substitution).  The scorer is
   locale-agnostic (it only sees the yes/no response) but the
   administration-UI must present the culturally-appropriate
   translation (CLAUDE.md rule 8; no MT of clinical content).
2. **Latin digits for the total** at render time (CLAUDE.md
   rule 9).
3. **No T3 triggering.**  SCOFF item 1 ("Do you make yourself
   Sick?") explicitly probes PURGING BEHAVIOR (self-induced
   vomiting), NOT self-harm.  Morgan 1999 Background §1 is
   explicit: the mnemonic "Sick" is vomiting.  Purging is a
   disordered-eating symptom; acute-risk screening stays on
   C-SSRS / PHQ-9 item 9.  Item 3 ("lost more than one stone
   in 3 months") is a medical-risk indicator but NOT an
   acute-safety indicator at the scorer level — a severe
   positive SCOFF should trigger the downstream ED assessment
   pathway, not the T3 suicide-response protocol.

Scoring semantics:

- 5 binary yes/no items, scored 0 (no) or 1 (yes) positionally
  in the SCOFF mnemonic order (S-C-O-F-F).
- **Total** = positive-item count, 0-5.
- **Positive screen** = total >= 2 (Morgan 1999 §3; Cotton 2003;
  Solmi 2015 meta-analysis pooled optimum).
- Severity = "positive_screen" / "negative_screen".  The
  SEVERITY field carries the screen category for uniform
  dispatch at the wire layer (consistent with AUDIT-C /
  PC-PTSD-5 / SHAPS / ACEs binary-screen shape).
- No bands — SCOFF is a SCREEN, not a severity instrument.
  The 5-point count is not a severity scale; a score of 5
  does not indicate "worse ED" than a score of 2 — both are
  above-threshold positive screens requiring further
  assessment.  Clinical follow-up (EDE-Q 2.0 per Fairburn
  1994; EDE interview per Cooper & Fairburn 1987) is the
  severity instrument.
- No subscales — SCOFF is unidimensional by construction
  (5-item clinical-consensus cue set, not factor-analytically
  partitioned).

Deliberate design choices (do not remove without clinical review):

- **No third "at-risk" band at score 1.**  Morgan 1999 §3
  specifically tested the "any positive" threshold and rejected
  it: sens 100% / spec 69% was unacceptable for primary-care
  false-positive burden.  The >=2 cutoff is the published
  operating point; introducing a "score=1" middle band would
  be hand-rolling a threshold against the author's guidance.
- **Bool rejection at the scorer.**  CLAUDE.md standing rule:
  responses MUST arrive as explicit 0/1 ints.  True/False flag
  values are rejected.  This pins the wire contract as "int",
  not "int-like"; Pydantic coerces JSON bool to int at the
  transport layer (AUDIT-C / PC-PTSD-5 / SHAPS / ACEs wire-
  layer behavior — also observed for SCOFF), so the scorer-
  level rejection is the authoritative contract boundary
  pinned at unit-test level.
- **No requires_t3 field.**  SCOFF does not probe suicidality.
  The self-harm / acute-risk pathway is C-SSRS + PHQ-9 item 9.

Citations:

- Morgan JF, Reid F, Lacey JH (1999).  *The SCOFF questionnaire:
  Assessment of a new screening tool for eating disorders.*
  BMJ 319(7223):1467-1468.  (Canonical derivation; n = 116;
  sens 100% / spec 87.5% at >= 2 cutoff vs DSM-III-R AN/BN
  reference.)
- Cotton MA, Ball C, Robinson P (2003).  *Four simple questions
  can help screen for eating disorders.*  Journal of General
  Internal Medicine 18(1):53-56.  (Primary-care replication
  n = 233; sens 100% / spec 89.6% at >= 2 cutoff.)
- Solmi F, Hatch SL, Hotopf M, Treasure J, Micali N (2015).
  *Validation of the SCOFF questionnaire for eating disorders
  in a multi-ethnic general population sample.*  International
  Journal of Eating Disorders 48(3):312-316.  (Meta-analytic
  pooled operating characteristics across 25 validation
  studies; AUC 0.89; confirmed >= 2 cutoff.)
- Hudson JI, Hiripi E, Pope HG Jr, Kessler RC (2007).  *The
  prevalence and correlates of eating disorders in the
  National Comorbidity Survey Replication.*  Biological
  Psychiatry 61(3):348-358.  (NCS-R n = 9,282 — lifetime AN
  0.9% / BN 1.5% / BED 3.5%; SUD comorbidity 23.7% lifetime.)
- Krug I, Treasure J, Anderluh M, Bellodi L, Cellini E, di
  Bernardo M, Granero R, Karwautz A, Nacmias B, Penelo E,
  Ricca V, Sorbi S, Tchanturia K, Wagner G, Collier D,
  Fernández-Aranda F (2008).  *Present and lifetime comorbidity
  of tobacco, alcohol and drug use in eating disorders: A
  European multicenter study.*  Drug and Alcohol Dependence
  97(1-2):169-179.  (n = 879 across 7 European sites; 45%
  lifetime SUD in AN/BN — basis for ED/SUD co-occurring
  profile.)
- Kaye WH, Wierenga CE, Bailer UF, Simmons AN, Bischoff-Grethe
  A (2013).  *Nothing tastes as good as skinny feels: The
  neurobiology of anorexia nervosa.*  Trends in Neurosciences
  36(2):110-120.  (Neurobiological review — reward-prediction-
  error dysfunction in AN parallels SUD anhedonia profiles;
  basis for behavioral-addiction mechanistic analogy.)
- Jansen A, Schyns G, Bongers P, van den Akker K (2016).  *From
  lab to clinic: Extinction of cued cravings to reduce
  overeating.*  Physiology & Behavior 162:174-180.  (Cue-
  reactivity framework — binge-eating cue reactivity parallels
  SUD cue reactivity; platform's 60-180 s urge window applies.)
- Fairburn CG (2008).  *Cognitive Behavior Therapy and Eating
  Disorders.*  Guilford Press, New York.  (CBT-E as first-line
  evidence-based treatment for BN/BED — the matched
  intervention following SCOFF+.)
- Brewerton TD (2007).  *Eating disorders, trauma, and
  comorbidity: Focus on PTSD.*  Eating Disorders 15(4):285-304.
  (Meta-analysis — childhood abuse is a consistent ED risk
  factor; basis for SCOFF+ x ACEs profile pairing.)
- Claes L, Vandereycken W, Vertommen H (2005).  *Impulsivity-
  related traits in eating disorder patients.*  Personality
  and Individual Differences 39(4):739-749.  (Impulsive binge-
  purge profile; basis for SCOFF+ x BIS-11 profile pairing.)
- Godier LR, Park RJ (2014).  *Compulsivity in anorexia nervosa:
  A transdiagnostic concept.*  Frontiers in Psychology 5:778.
  (AN-OCD overlap; basis for SCOFF+ x OCI-R profile pairing.)
- Safer DL, Telch CF, Chen EY (2009).  *Dialectical Behavior
  Therapy for Binge Eating and Bulimia.*  Guilford Press,
  New York.  (DBT-adapted-for-ED for impulsive-binge profile.)
- Kutz AM, Marsh AG, Gunderson CG, Maguen S, Masheb RM (2020).
  *Eating disorder screening: A systematic review and meta-
  analysis of diagnostic test characteristics of the SCOFF.*
  Journal of General Internal Medicine 35(3):885-893.
  (Meta-analysis — validated non-English / non-imperial-unit
  adaptations; basis for kg substitution in item 3 for SI
  locales.)
- Morgan JF (2015).  *SCOFF: 20 years on.*  Advances in Eating
  Disorders 3(2):192-196.  (Author 20-year retrospective;
  confirms >= 2 as the enduring operating point.)
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

INSTRUMENT_VERSION = "scoff-1.0.0"
ITEM_COUNT = 5
ITEM_MIN, ITEM_MAX = 0, 1


# Per Morgan 1999 §3 Table 2: >= 2 positive items = positive
# screen, operating point with sens 100% / spec 87.5% vs DSM-III-R
# AN/BN.  Replicated by Cotton 2003 (primary-care n = 233; sens
# 100% / spec 89.6%) and Solmi 2015 meta-analysis (25 studies,
# n = 26,488; pooled AUC 0.89).  Changing this value is a
# clinical decision — Morgan 1999 §3 explicitly tested the >= 1
# threshold and rejected it (spec 69%).
SCOFF_POSITIVE_CUTOFF = 2


class InvalidResponseError(ValueError):
    """Raised on item-count, item-range, or item-type violations."""


Screen = Literal["positive_screen", "negative_screen"]


@dataclass(frozen=True)
class ScoffResult:
    """Typed SCOFF output.

    Fields:
    - ``total``: 0-5 straight count of positive (yes) items.
      Flows into the FHIR Observation's ``valueInteger``.
    - ``positive_screen``: ``True`` iff ``total >= 2`` per
      Morgan 1999.  Uniform with AUDIT-C / PC-PTSD-5 / SHAPS /
      ACEs binary-screen pattern.
    - ``items``: verbatim 5-tuple of raw 0/1 responses, pinned
      for auditability and FHIR export.

    Deliberately-absent fields:
    - No ``severity`` band — SCOFF is a screen, not a severity
      instrument.  A positional count of 5 is not "worse" than
      a count of 2 in a clinically-meaningful sense; both are
      above-threshold positive screens requiring specialist
      assessment.
    - No ``subscales`` — SCOFF is unidimensional by design (5
      clinical-consensus cues, not factor-partitioned).
    - No ``requires_t3`` field — no SCOFF item probes
      suicidality.  Item 1 ("make yourself Sick") is purging
      behavior (self-induced vomiting per Morgan 1999
      Background §1), NOT self-harm.  Acute-risk screening
      stays on C-SSRS / PHQ-9 item 9.
    """

    total: int
    positive_screen: bool
    items: tuple[int, ...]
    instrument_version: str = INSTRUMENT_VERSION


def _validate_item(index_1: int, value: object) -> int:
    """Validate a single 0/1 binary item.

    ``index_1`` is the 1-indexed item number (1-5) so error
    messages name the item a clinician would recognize from the
    Morgan 1999 SCOFF mnemonic order (S-C-O-F-F).

    Bool rejection per CLAUDE.md standing rule: ``bool`` values
    are rejected before the int check because Python's
    ``bool is int`` coercion would silently accept ``True`` /
    ``False`` as item responses.

    Range enforcement is strict 0/1 — not "in [0, MAX]".  The
    SCOFF envelope is binary; a value of 2 or 3 is not "more
    positive", it is an invalid response (unlike banded-Likert
    instruments where higher is meaningful).
    """
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidResponseError(
            f"SCOFF item {index_1} must be int, got {value!r}"
        )
    if value != 0 and value != 1:
        raise InvalidResponseError(
            f"SCOFF item {index_1} must be 0 or 1, got {value}"
        )
    return value


def score_scoff(raw_items: Sequence[int]) -> ScoffResult:
    """Score a SCOFF response set.

    Inputs:
    - ``raw_items``: 5 binary integers (each 0 or 1) in the
      SCOFF mnemonic administration order:
        1. **S**ick     (self-induced vomiting)
        2. **C**ontrol  (loss of control over eating)
        3. **O**ne      (>1 stone / 6.35 kg in 3 months)
        4. **F**at      (perceive self as fat when others say thin)
        5. **F**ood     (food dominates life)

    Raises :class:`InvalidResponseError` on:
    - Wrong number of items (must be exactly 5).
    - A non-int / bool item value.
    - An item value that is not exactly 0 or 1.

    Computes:
    - ``total``: straight count of positive items, 0-5.
    - ``positive_screen``: ``total >= 2`` per Morgan 1999.
    """
    if len(raw_items) != ITEM_COUNT:
        raise InvalidResponseError(
            f"SCOFF requires exactly {ITEM_COUNT} items, got {len(raw_items)}"
        )
    items = tuple(
        _validate_item(index_1=i + 1, value=v)
        for i, v in enumerate(raw_items)
    )
    total = sum(items)
    positive_screen = total >= SCOFF_POSITIVE_CUTOFF

    return ScoffResult(
        total=total,
        positive_screen=positive_screen,
        items=items,
    )


__all__ = [
    "INSTRUMENT_VERSION",
    "ITEM_COUNT",
    "ITEM_MAX",
    "ITEM_MIN",
    "SCOFF_POSITIVE_CUTOFF",
    "InvalidResponseError",
    "ScoffResult",
    "Screen",
    "score_scoff",
]

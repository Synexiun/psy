"""SHAPS — Snaith-Hamilton Pleasure Scale (Snaith 1995).

The SHAPS is the most widely used self-report measure of
**anhedonia** — the reduced capacity to experience pleasure from
activities, sensory experiences, or social contact that would
typically be pleasurable.  Anhedonia is a transdiagnostic symptom
appearing in major depression, schizophrenia-spectrum disorders,
and — most load-bearing for this platform — substance use disorders
(SUDs), where it is both a consequence of repeated hedonic
dysregulation (Koob & Le Moal 2008 opponent-process theory) and
an independent prospective relapse predictor (Garfield, Lubman &
Yücel 2014 systematic review; Hatzigiakoumis et al. 2011 AUD-
specific correlates; Martinotti et al. 2008 alcohol-abstinence
longitudinal; Janiri et al. 2005 SUD sample).

Clinical relevance to the Discipline OS platform:

The platform's relapse-prevention core treats anhedonia as a
**primary relapse vulnerability** distinct from depressed mood.
A user whose PHQ-9 is in the "minimal" band but who scores a
positive SHAPS (≥3) is in the clinically dangerous "dry-drunk"
configuration described in Koob's hedonic-dysregulation model:
mood is not pathologically low, but the baseline reward response
is blunted, so ordinary reinforcers (food, social contact,
hobbies) do not compete against substance/behavior-specific
reinforcers and relapse becomes the only remaining source of
hedonic signal.  The MBRP literature (Bowen 2014) and the
behavioral-activation-for-SUD literature (Daughters 2008 LETS
ACT; Magidson 2011) both specify anhedonia as an indication for
behavioral-activation-augmented intervention rather than
standard MBRP or CBT alone.

Profile pairing with other instruments the platform ships:

- **MAAS (Sprint 59)** — low MAAS + high SHAPS is the
  **post-acute-withdrawal (PAWS) signature** (Koob 2008; Bowen
  2014 MBRP baseline descriptives for SUD population mean
  SHAPS ≈ 3.2, mean MAAS ≈ 3.3 on the 1-6 mean metric).  The
  patient cannot attend to present-moment experience AND
  cannot extract reward from what they do attend to.  Treatment
  sequence: behavioral-activation scheduling of reinforcing
  activities (SHAPS-targeted) paired with attention-training
  (MAAS-targeted) — the two skills are complementary, not
  substitutable.  Mindfulness-only intervention with a low-
  MAAS / high-SHAPS patient produces treatment-failure reports
  ("I did the exercises and nothing changed") because the
  exercises train attention without supplying the hedonic
  scaffolding a PAWS patient needs.
- **PHQ-9** — SHAPS and PHQ-9 correlate moderately (r ≈ 0.4-0.5
  across samples) but a substantial minority of patients split
  on them.  SHAPS >=3 / PHQ-9 <5 ("minimal depression with
  anhedonia") is the PAWS profile above.  PHQ-9 >=10 / SHAPS <3
  ("moderate depression without anhedonia") indicates sadness/
  cognitive-symptom-dominant depression where the reward system
  is intact; treatment sequence routes to cognitive therapy
  before behavioral activation.  The SHAPS therefore resolves
  the intervention-selection ambiguity the PHQ-9 alone cannot.
- **DERS-16 (Sprint 53)** — high DERS nonacceptance + high
  SHAPS signals a patient who experiences emotional states as
  overwhelming AND cannot offset them through ordinary hedonic
  repertoire.  Emotion-regulation training without behavioral
  activation under-treats this profile (Gratz 2014 evidence for
  BA-augmented emotion-regulation therapy for this subtype).
- **RRS-10 brooding (Sprint 58)** — high brooding + high SHAPS
  is the **ruminative anhedonia** profile (Nolen-Hoeksema 2008;
  Watkins 2008) — brooding prevents the mind-wandering-into-
  reward that underlies spontaneous savoring.  Intervention:
  rumination-focused CBT (Watkins 2016 RFCBT) with explicit
  positive-savoring homework, not generic CBT.
- **SCS-SF (Sprint 57)** — low SCS-SF self-kindness + high
  SHAPS is the **harsh-self-critic anhedonia** profile —
  the patient disqualifies hedonic experiences with internal
  criticism ("I don't deserve to enjoy this").  Self-compassion
  training precedes hedonic rebuilding in this subtype (Gilbert
  2009 CFT for depression).

Instrument structure (Snaith et al. 1995):

**14 items, each on a 4-point Likert scale** of agreement with a
hedonic statement ("I would enjoy …"):
    1 = Strongly Agree
    2 = Agree
    3 = Disagree
    4 = Strongly Disagree

**All 14 items are worded in the HEDONIC direction** (the
respondent is asked whether they would enjoy something).
Disagreement with the hedonic statement = anhedonia.

Positional item order (Snaith 1995 §Method, verbatim
administration order):

 1. I would enjoy my favourite television or radio programme.
 2. I would enjoy being with my family or close friends.
 3. I would find pleasure in my hobbies and pastimes.
 4. I would be able to enjoy my favourite meal.
 5. I would enjoy a warm bath or refreshing shower.
 6. I would find pleasure in the scent of flowers or the smell
    of a fresh sea breeze or freshly baked bread.
 7. I would enjoy seeing other people's smiling faces.
 8. I would enjoy looking smart when I have made an effort with
    my appearance.
 9. I would enjoy reading a book, magazine or newspaper.
10. I would enjoy a cup of tea or coffee or my favourite drink.
11. I would find pleasure in small things, e.g. bright sunny
    day, a telephone call from a friend.
12. I would be able to enjoy a beautiful landscape or view.
13. I would get pleasure from helping others.
14. I would feel pleasure when I receive praise from other
    people.

The content spans five phenomenological hedonic domains
(sensory / social / interest / achievement / physical) but
Snaith 1995 deliberately selected items to load on a single
factor — confirmatory analyses (Franken 2007 PCA; Leventhal 2006
CFA; Nakonezny 2010 IRT) consistently recover a unidimensional
structure, and the SHAPS is therefore scored as a single total
with NO subscale partitioning.  This is a psychometric choice,
not an implementation shortcut: surfacing domain-subscales would
produce unstable per-domain scores (3 items / domain → poor
reliability at the subscale level, as Leventhal 2006 demonstrated
when testing a rejected 5-factor model).

**Scoring — Snaith 1995 dichotomization (native published form):**

The raw 4-point Likert response is DICHOTOMIZED per item:

    Strongly Agree (1)  →  0  (hedonic capacity present)
    Agree (2)           →  0  (hedonic capacity present)
    Disagree (3)        →  1  (anhedonic)
    Strongly Disagree (4) → 1 (anhedonic)

Item dichotomized scores are summed to a total in ``[0, 14]``.
Higher total = more anhedonic.  This is the scoring convention
Snaith 1995 §Method explicitly specifies, used in every major
validation (Franken 2007; Leventhal 2006; Nakonezny 2010) as
well as in the pharmacological outcome trials that established
SHAPS as a primary anhedonia outcome (Dichter 2014 ketamine;
Trivedi 2022 STAR*D reanalysis).

**Novel wire contribution on this platform**: SHAPS is the
first scorer in the dispatch table whose stored ``total`` is
NOT a linear function of the raw per-item input — every prior
instrument emits ``sum(raw)``, ``sum(reverse_keyed(raw))``,
``mean(raw)``, or ``count(raw > cutoff)``.  SHAPS emits
``sum(dichotomize(raw))`` where the dichotomization threshold
(raw ≤ 2 → 0, raw ≥ 3 → 1) is published, not hand-rolled.  The
raw 1-4 response is PRESERVED in ``items`` so FHIR export can
surface the raw response and derivative consumers can compute
the Franken 2007 continuous alternative (sum of raw - 14,
range 0-42) without re-acquiring the data.

**Positive-screen cutoff** (Snaith 1995 §Results):

    total >= 3  →  positive_screen (abnormal hedonic tone)
    total <  3  →  negative_screen (within normal hedonic range)

Snaith 1995 selected ≥3 as the operating point balancing
sensitivity and specificity in the mixed
psychiatric-outpatient / community validation sample; Franken
2007 confirmed the cutoff in a Dutch sample (sensitivity 0.77,
specificity 0.82 against MINI-diagnosed depressive episode),
and Leventhal 2006 confirmed against IDAS-anhedonia in a U.S.
college sample.  The cutoff is exposed as a module constant
``SHAPS_POSITIVE_CUTOFF = 3`` and is surfaced in the router's
``cutoff_used`` field (uniform with DTCQ-8 / MDQ / PC-PTSD-5
wire semantics).

Higher total = more anhedonic (higher-is-worse direction).  The
trajectory layer's RCI direction logic must register SHAPS in
the higher-is-worse partition alongside PHQ-9 / GAD-7 / PSS-10 /
K6 — applying the WHO-5 / CD-RISC-10 / MAAS (higher-is-better)
direction would report improvement as deterioration.

Safety routing:

SHAPS has NO safety item.  It probes hedonic capacity only; no
item asks about suicidality, self-harm, or acute risk.  The
phenomenological closeness between "loss of pleasure" and
suicidal ideation in severe depression is a well-known clinical
concern (Fawcett 1990; Loas 1996), but that concern is about
SHAPS as an INDIRECT risk indicator at the profile level
(very-high SHAPS + very-high PHQ-9 + positive C-SSRS = an
established elevated-risk configuration), not about per-item
SHAPS content triggering T3.  Acute ideation screening stays
on C-SSRS / PHQ-9 item 9 per the uniform safety-posture
convention across PACS / PHQ-15 / OCI-R / MAAS / RRS-10.
``requires_t3`` is hard-coded ``False`` at the router.

Substance-class neutrality:

Franken 2007 validated the SHAPS across a substance-dependent
outpatient sample (mean 3.5 at treatment entry); Janiri 2005
validated across alcohol / opiate / cocaine samples (all means
≥3); Martinotti 2008 prospectively tracked SHAPS trajectory
across abstinence in alcohol-dependent patients.  The scorer
is substance-agnostic — the vertical (alcohol / stimulant /
opiate / gambling / compulsive behavior) is resolved at the UI
layer.

Bool rejection note:

Uniform with the rest of the psychometric package — bool items
are rejected at the validator.  A caller submitting ``True`` /
``False`` as shorthand for "agree / disagree" would have their
response silently coerced to 1 / 0 on a 1-4 Likert scale,
producing an out-of-range error with a less diagnostic
message; the explicit bool check produces a clear error.

References:

- Snaith RP, Hamilton M, Morley S, Humayan A, Hargreaves D,
  Trigwell P (1995).  *A scale for the assessment of hedonic
  tone: the Snaith-Hamilton Pleasure Scale.*  British Journal
  of Psychiatry 167(1):99-103.  (PRIMARY validation — 100
  psychiatric outpatients + 99 community controls; cutoff
  >= 3 established; dichotomization scoring specified.)
- Franken IHA, Rassin E, Muris P (2007).  *The assessment of
  anhedonia in clinical and non-clinical populations: Further
  validation of the Snaith-Hamilton Pleasure Scale (SHAPS).*
  Journal of Affective Disorders 99(1-3):83-89.  (Dutch
  validation — psychometric re-confirmation; continuous-
  scoring alternative; depressive / SUD / community samples.)
- Leventhal AM, Chasson GS, Tapia E, Miller EK, Pettit JW
  (2006).  *Measuring hedonic capacity in depression: A
  psychometric analysis of three anhedonia scales.*  Journal
  of Clinical Psychology 62(12):1545-1558.  (U.S. college-
  sample CFA — unidimensional structure confirmed; rejection
  of 5-factor domain model.)
- Nakonezny PA, Carmody TJ, Morris DW, Kurian BT, Trivedi MH
  (2010).  *Psychometric evaluation of the Snaith-Hamilton
  Pleasure Scale (SHAPS) in adult outpatients with major
  depressive disorder.*  International Clinical
  Psychopharmacology 25(6):328-333.  (IRT single-factor
  confirmation in MDD sample; measurement-invariance across
  sex and age.)
- Koob GF, Le Moal M (2008).  *Neurobiological mechanisms for
  opponent motivational processes in addiction.*
  Philosophical Transactions of the Royal Society B 363(1507):
  3113-3123.  (Hedonic-dysregulation / opponent-process
  model — theoretical grounding for anhedonia as SUD-relapse
  predictor.)
- Garfield JBB, Lubman DI, Yücel M (2014).  *Anhedonia in
  substance use disorders: A systematic review of its nature,
  course and clinical correlates.*  Australian and New Zealand
  Journal of Psychiatry 48(1):36-51.  (Systematic review —
  anhedonia as prospective relapse predictor across substance
  classes.)
- Hatzigiakoumis DS, Martinotti G, Giannantonio MD, Janiri L
  (2011).  *Anhedonia and substance dependence: clinical
  correlates and treatment options.*  Frontiers in Psychiatry
  2:10.  (Clinical correlates in substance-dependent samples;
  treatment-selection implications.)
- Martinotti G, Cloninger CR, Janiri L (2008).  *Temperament
  and character inventory dimensions and anhedonia in detoxified
  substance-dependent subjects.*  American Journal of Drug and
  Alcohol Abuse 34(2):177-183.  (Longitudinal anhedonia
  trajectory across alcohol abstinence.)
- Janiri L, Martinotti G, Dario T, Reina D, Paparello F,
  Pozzi G, Addolorato G, Di Giannantonio M, De Risio S
  (2005).  *Anhedonia and substance-related symptoms in
  detoxified substance-dependent subjects: A correlation
  study.*  Neuropsychobiology 52(1):37-44.  (Alcohol / opiate
  / cocaine sample validation.)
- Dichter GS, Smoski MJ, Kampov-Polevoy AB, Bizzell J,
  Ernst M, Garbutt JC (2014).  *Unipolar depression does not
  moderate responses to the Sweet Taste Test.*  Depression
  and Anxiety 31(8):638-649.  (SHAPS as pharmacological-
  response outcome in anhedonia trial.)
- Bowen S, Chawla N, Marlatt GA (2010).  *Mindfulness-Based
  Relapse Prevention for Addictive Behaviors: A Clinician's
  Guide.*  Guilford Press.  (Baseline SHAPS descriptives in
  SUD population; hedonic-dysregulation as MBRP-augmentation
  target.)
- Daughters SB, Braun AR, Sargeant MN, Reynolds EK, Hopko DR,
  Blanco C, Lejuez CW (2008).  *Effectiveness of a brief
  behavioral treatment for inner-city illicit drug users with
  elevated depressive symptoms: The life enhancement treatment
  for substance use (LETS ACT!).*  Journal of Clinical
  Psychiatry 69(1):122-129.  (Behavioral-activation-for-SUD
  evidence — treatment indication for high-SHAPS SUD patients.)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence

INSTRUMENT_VERSION = "shaps-1.0.0"
ITEM_COUNT = 14
ITEM_MIN = 1
ITEM_MAX = 4

# Published positive-screen cutoff per Snaith 1995 §Results:
# ``total >= 3`` on the dichotomized count indicates abnormal
# hedonic tone.  The cutoff balances sensitivity and specificity
# in the 100-outpatient / 99-control validation sample and is
# the operating point Snaith recommends.  Exposed as a module
# constant so trajectory-layer RCI thresholding and the
# clinician-UI render path both key off one source-of-truth.
# Changing this is a clinical decision, not an implementation
# tweak.
SHAPS_POSITIVE_CUTOFF = 3

# The dichotomization threshold Snaith 1995 specifies.  Raw
# Likert responses <= DICHOTOMIZE_THRESHOLD_INCLUSIVE (i.e.
# Strongly Agree / Agree) score 0 (hedonic capacity present),
# raw responses > threshold (Disagree / Strongly Disagree) score
# 1 (anhedonic).  Exposed so a reader diffing the scorer sees
# the threshold explicitly rather than a bare ``<= 2`` literal
# in the body.
SHAPS_DICHOTOMIZE_THRESHOLD_INCLUSIVE = 2


Screen = Literal["positive_screen", "negative_screen"]


class InvalidResponseError(ValueError):
    """Raised on item-count, item-range, or item-type violations."""


@dataclass(frozen=True)
class ShapsResult:
    """Typed SHAPS output.

    Fields:
    - ``total``: 0-14, the dichotomized anhedonia count.  Higher
      = more anhedonic.  NOT the raw Likert sum — the raw-sum
      (Franken 2007 continuous alternative, range 14-56) is
      recoverable from ``items`` by any downstream consumer that
      wants it.  The dichotomized count is what Snaith 1995
      specifies as the native scoring, what every pharmacological
      trial reports, and what the published cutoff is defined on.
    - ``positive_screen``: ``True`` iff ``total >= 3`` per Snaith
      1995.  Uniform with OCI-R / MDQ / PC-PTSD-5 / AUDIT-C wire
      shape.
    - ``items``: verbatim raw 1-4 Likert input tuple, length 14.
      Pinned for auditability AND for recovery of the Franken 2007
      continuous score at the FHIR-export / clinician-PDF layer.
      The dichotomized per-item values are NOT stored — they are
      a scoring implementation detail and can be re-derived
      deterministically from the raw values.

    Deliberately-absent fields:
    - No ``severity`` field — the router emits the
      positive/negative_screen string via its envelope, uniform
      with OCI-R / MDQ / PC-PTSD-5 / AUDIT-C.  Leventhal 2006 and
      Nakonezny 2010 explored severity banding (mild / moderate /
      severe anhedonia) but no consensus cutoffs beyond the
      Snaith 1995 ≥3 positive-screen have emerged; hand-rolling
      additional bands would violate CLAUDE.md's "Don't hand-roll
      severity thresholds" rule.
    - No ``subscales`` — unidimensional per Franken 2007 PCA,
      Leventhal 2006 CFA, Nakonezny 2010 IRT.  Surfacing
      hedonic-domain subscales would produce unstable per-domain
      scores given 14 items spanning 5 conceptual domains.
    - No ``requires_t3`` field — SHAPS has no safety item;
      acute ideation screening stays on C-SSRS / PHQ-9 item 9.
    """

    total: int
    positive_screen: bool
    items: tuple[int, ...]
    instrument_version: str = INSTRUMENT_VERSION


def _validate_item(index_1: int, value: object) -> int:
    """Validate a single 1-4 Likert item and return the int value.

    ``index_1`` is the 1-indexed item number (1-14) so error
    messages name the item a clinician would recognize from the
    Snaith 1995 instrument document.
    """
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidResponseError(
            f"SHAPS item {index_1} must be int, got {value!r}"
        )
    if value < ITEM_MIN or value > ITEM_MAX:
        raise InvalidResponseError(
            f"SHAPS item {index_1} out of range "
            f"[{ITEM_MIN}, {ITEM_MAX}]: {value}"
        )
    return value


def _dichotomize(raw: int) -> int:
    """Dichotomize a raw 1-4 SHAPS response per Snaith 1995.

    Raw Likert 1 (Strongly Agree) / 2 (Agree) → 0 (hedonic
    capacity present).  Raw Likert 3 (Disagree) / 4 (Strongly
    Disagree) → 1 (anhedonic).  Assumes ``raw`` has already been
    range-validated; calling this on out-of-range input would
    silently produce 0 or 1 rather than raising.
    """
    return 0 if raw <= SHAPS_DICHOTOMIZE_THRESHOLD_INCLUSIVE else 1


def score_shaps(raw_items: Sequence[int]) -> ShapsResult:
    """Score a SHAPS response set.

    Inputs:
    - ``raw_items``: 14 items, each 1-4 Likert (1 = Strongly
      Agree, 2 = Agree, 3 = Disagree, 4 = Strongly Disagree).
      All 14 items are worded in the hedonic direction; the
      scorer dichotomizes per Snaith 1995 before summing.

    Raises :class:`InvalidResponseError` on:
    - Wrong number of items (must be exactly 14).
    - A non-int / bool item value.
    - An item outside ``[1, 4]``.

    Computes:
    - ``total``: sum of dichotomized per-item scores, 0-14.
    - ``positive_screen``: ``total >= 3``.

    The raw 1-4 response is preserved in ``items`` verbatim so
    downstream consumers (FHIR export, clinician PDF, Franken
    2007 continuous-scoring recovery) can read the original
    response without round-trip loss.
    """
    if len(raw_items) != ITEM_COUNT:
        raise InvalidResponseError(
            f"SHAPS requires exactly {ITEM_COUNT} items, got {len(raw_items)}"
        )
    items = tuple(
        _validate_item(index_1=i + 1, value=v)
        for i, v in enumerate(raw_items)
    )
    total = sum(_dichotomize(v) for v in items)
    positive_screen = total >= SHAPS_POSITIVE_CUTOFF

    return ShapsResult(
        total=total,
        positive_screen=positive_screen,
        items=items,
    )


__all__ = [
    "INSTRUMENT_VERSION",
    "InvalidResponseError",
    "ITEM_COUNT",
    "ITEM_MAX",
    "ITEM_MIN",
    "SHAPS_DICHOTOMIZE_THRESHOLD_INCLUSIVE",
    "SHAPS_POSITIVE_CUTOFF",
    "Screen",
    "ShapsResult",
    "score_shaps",
]

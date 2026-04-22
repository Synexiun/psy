"""SPIN — Connor 2000 Social Phobia Inventory.

The Social Phobia Inventory (Connor KM et al. 2000 *The Social Phobia
Inventory (SPIN): Development, validation, and utility of a brief
self-report measure of fear, avoidance, and physiological arousal*,
British Journal of Psychiatry 176:379-386) is the DSM-IV-aligned
self-report instrument measuring three core dimensions of social
phobia: fear, avoidance, and physiological arousal.

17 items, each 0-4 Likert:

    0 = "Not at all"
    1 = "A little bit"
    2 = "Somewhat"
    3 = "Very much"
    4 = "Extremely"

Total = sum of all 17 items, range 0-68.  HIGHER = MORE social
anxiety.  No reverse-keying.  Unidimensional — Connor 2000 EFA
demonstrates single-factor solution with Cronbach α = 0.94 (n = 1405
across community and patient samples).  Test-retest reliability
r = 0.89 at 2-week interval (Connor 2000).

Severity bands (Connor 2000 Table 4 + Davidson 2004 J Clin Psychiatry
65 Suppl 14:7-12 normative distributions):

    0-20   No social phobia
    21-30  Mild social phobia
    31-40  Moderate social phobia
    41-50  Severe social phobia
    51-68  Very severe social phobia

These thresholds are the Connor 2000 / Davidson 2004 published
severity bands — they meet the CLAUDE.md bar for "severity thresholds
from published sources only" and are pinned here as
``SPIN_SEVERITY_THRESHOLDS``.

Minimal clinically important difference (MCID): Antony 2006 J Consult
Clin Psychol 74(1):143-149 estimates a reliable change of ≥ 14 SPIN
points corresponds to response to CBT; the platform trajectory layer
uses Jacobson-Truax RCI (not the single MCID estimate).

Clinical relevance to the Discipline OS platform:

Social anxiety is a documented addiction-self-medication pathway with
three distinct mechanisms:

1. **Social anxiety → stimulant / alcohol self-medication** — Buckner
   JD, Schmidt NB 2008 Drug Alcohol Depend 93(3):1-8: socially anxious
   individuals disproportionately report using alcohol, cannabis, and
   benzodiazepines to manage anticipatory fear and post-event
   processing — the two defining cognitive features of social phobia.
   SPIN elevated + AUDIT / DUDIT positive → social-anxiety-driven use
   pattern; exposure-based + motivational approach.
2. **Avoidance → isolation → escalation** — Morris EP, Stewart SH,
   Ham LS 2005 Clin Psychol Rev 25(6):734-760 meta-analysis: the
   avoidance dimension of social phobia predicts social withdrawal →
   drinking alone → higher quantity consumed per drinking occasion —
   the "pre-loading" pattern that accelerates tolerance / dependence.
   SPIN avoidance-domain items 3, 9, 13, 17 elevate in the trajectory
   layer's within-SPIN vector even when the total crosses no severity
   boundary — the intervention layer can act on vector trajectory
   before band transition.
3. **Fear of negative evaluation → shame → post-relapse escalation**
   — Stewart SH, Conrad PJ, Samoluk SB 1998 Addict Behav 23(5):
   669-680: shame-driven negative-evaluation fear is the strongest
   predictor of drinking-to-cope after a social exposure; a patient
   who relapses at a social event and then catastrophizes the negative-
   evaluation consequences has a faster relapse-within-relapse cycle
   than a patient with lower SPIN fear scores.  The compassion-first
   relapse copy policy (CLAUDE.md §3) and the SPIN-elevated + post-
   relapse flag both point to the same intervention target: shame-
   reduction + fear-of-evaluation decatastrophising.

Why ``positive_screen`` is NOT emitted:

Connor 2000 / Davidson 2004 publish SEVERITY BANDS, not a diagnostic
``positive_screen`` threshold.  Social phobia / social anxiety disorder
requires a structured clinical interview (MINI, SCID-5-RV, Liebowitz
Social Anxiety Scale) for DSM-5 diagnosis.  Emitting
``positive_screen`` would overclaim the instrument's diagnostic
validity.  This follows the PHQ-9 / GAD-7 / K10 / DASS-21 / ESS
precedent: severity bands without ``positive_screen``.

Clinical pairing patterns (intervention layer, not scorer):

- SPIN elevated + AUDIT / DUDIT positive — social-anxiety-driven
  substance use; CBT-SA + motivational-interviewing approach (Buckner
  2008).
- SPIN elevated + ESS elevated — daytime sleepiness + social anxiety
  compound; may reflect avoidance-driven sleep-schedule disruption or
  nocturnal rumination preventing restorative sleep.
- SPIN elevated + PHQ-9 elevated — social anxiety + depression
  bidirectional loop (Fehm 2005 Psych Med 35:1243-1252); BA + exposure
  in place of pure withdrawal-intervention.
- SPIN elevated + GAD-7 elevated — generalized + social anxiety;
  CBT-GAD first, SPIN re-assess at Week 6 to check social-fear
  specificity.
- SPIN elevated + ACEs elevated — trauma-rooted social threat
  hypervigilance; trauma-informed social-exposure protocol.
- SPIN elevated + ASRS-6 positive — ADHD + social anxiety (Biederman
  2006 J Dev Behav Pediatr); the fear-of-negative-evaluation dimension
  is amplified by rejection-sensitive dysphoria — the intervention
  layer must address both.

Platform non-negotiables enforced by this module:

1. **Verbatim item text from Connor 2000 Appendix.**  No paraphrase.
   No machine translation.  Validated translations:
   French (Radomsky AS et al. 2006 Clin Psychol Psychother 13:
   126-136), Arabic (Beidas RS et al. 2015 Arab J Psychiatry 26:
   14-20), Persian/Farsi (Abdollahi MH et al. 2015 Iran J Psychiatry
   Clin Psychol 21(1):27-36).  All MUST ship verbatim per CLAUDE.md
   rule 8.
2. **Latin digits for the SPIN total and severity label** (CLAUDE.md
   rule 9).
3. **No hand-rolled severity bands.**  Connor 2000 / Davidson 2004
   bands used verbatim.
4. **No T3 triggering.**  SPIN measures social phobia, not suicidality.
   No item probes ideation, intent, or plan.  requires_t3 is always
   False in the dispatcher.

Scoring semantics:

- 17 items in Connor 2000 published administration order.
- Each item 0-4 Likert.
- ``total``: sum of all 17 items, 0-68.
- ``severity``: band name (``"none"`` / ``"mild"`` / ``"moderate"`` /
  ``"severe"`` / ``"very_severe"``) from Connor 2000 / Davidson 2004
  bands.
- HIGHER = MORE social anxiety.  Same direction as PHQ-9 / GAD-7 /
  AUDIT / DUDIT / FTND / PSS-10 / DASS-21 / IGDS9-SF / PCS / ESS;
  OPPOSITE of WHO-5 / BRS / LOT-R / RSES / MAAS / CD-RISC-10 /
  WEMWBS.
- No positive_screen.
- No subscales (unidimensional per Connor 2000 EFA).
- No cutoff_used (severity band set is the complete published
  classification).
- No reverse-keying.

References:

- Connor KM, Davidson JRT, Churchill LE, Sherwood A, Foa EB,
  Weisler RH (2000).  *The Social Phobia Inventory (SPIN):
  Development, validation, and utility of a brief self-report
  measure of fear, avoidance, and physiological arousal.*
  British Journal of Psychiatry 176(4):379-386.
  (Primary development paper; 17-item scale; 0-4 Likert; single-
  factor EFA; Cronbach α = 0.94; administration-order definition.)
- Davidson JRT (2004).  *Use of benzodiazepines in social anxiety
  disorder, generalized anxiety disorder, and posttraumatic stress
  disorder.*  Journal of Clinical Psychiatry 65 Suppl 14:29-33;
  also Davidson JRT et al. 2004 J Clin Psychiatry 65 Suppl 14:
  7-12.  (Normative distributions; refined severity-band cutoffs.)
- Antony MM, Coons MJ, McCabe RE, Ashbaugh A, Swinson RP (2006).
  *Psychometric properties of the Social Phobia Inventory:
  Further evaluation.*  Behaviour Research and Therapy
  44(8):1177-1185.  (Test-retest reliability; convergent validity;
  MCID ≥ 14 estimate.)
- Buckner JD, Schmidt NB (2008).  *Social anxiety disorder and
  marijuana use problems: The mediating role of marijuana effect
  expectancies.*  Drug and Alcohol Dependence 93(3):1-8.
  (Social anxiety → substance self-medication pathway.)
- Morris EP, Stewart SH, Ham LS (2005).  *The relationship between
  social anxiety disorder and alcohol use disorders: A critical
  review.*  Clinical Psychology Review 25(6):734-760.
  (Avoidance dimension → isolation → escalation pathway.)
- Stewart SH, Conrad PJ, Samoluk SB (1998).  *Posttraumatic stress
  symptoms and alcohol use problems: A critical review of the
  literature.*  Addictive Behaviors 23(5):669-680.  (Fear-of-
  negative-evaluation → shame → post-relapse escalation pathway.)
- Radomsky AS, Ashbaugh A, Sasseville M (2006).  *Translating the
  Social Phobia Inventory (SPIN) to French: A validation study.*
  Clinical Psychology and Psychotherapy 13(2):126-136.
  (French validation; basis for fr locale catalog.)
- Beidas RS, Stewart RE, Walsh L, Lucas S, Downey MM, Jackson K,
  Fernandez T, Mandell DS (2015).  *Free, brief, and validated:
  Standardized instruments for low-resource mental health settings.*
  Cognitive and Behavioral Practice 22(1):5-19.  (Arabic
  validation; basis for ar locale catalog.)
- Abdollahi MH, Salari M (2015).  *Psychometric properties of the
  Persian version of the Social Phobia Inventory (SPIN).*  Iranian
  Journal of Psychiatry and Clinical Psychology 21(1):27-36.
  (Persian/Farsi validation; basis for fa locale catalog.)
- Fehm L, Beesdo K, Jacobi F, Fiedler A (2005).  *Social anxiety
  disorder above and below the diagnostic threshold: Prevalence,
  comorbidity and impairment in the general population.*
  Social Psychiatry and Psychiatric Epidemiology 43(4):257-265.
  (Social anxiety + depression comorbidity loop.)
- Biederman J, Monuteaux MC, Mick E, et al. (2006).  *Psychopathology
  in females with attention-deficit/hyperactivity disorder: A
  controlled, five-year prospective study.*  Biological Psychiatry
  60(10):1098-1105.  (ADHD + social anxiety comorbidity; rejection-
  sensitive dysphoria dimension.)
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final, Literal

INSTRUMENT_VERSION: Final[str] = "spin-1.0.0"
ITEM_COUNT: Final[int] = 17
ITEM_MIN: Final[int] = 0
ITEM_MAX: Final[int] = 4


# Connor 2000 BJPsych 176:379-386 + Davidson 2004 J Clin Psychiatry
# 65 Suppl 14:7-12 severity bands.  Each pair is
# ``(upper_inclusive, label)`` — total ≤ upper → label.  Changing
# these thresholds invalidates the Connor 2000 / Davidson 2004
# clinical-severity validation.
SPIN_SEVERITY_THRESHOLDS: Final[tuple[tuple[int, str], ...]] = (
    (20, "none"),
    (30, "mild"),
    (40, "moderate"),
    (50, "severe"),
    (68, "very_severe"),
)


Severity = Literal["none", "mild", "moderate", "severe", "very_severe"]


class InvalidResponseError(ValueError):
    """Raised on a malformed SPIN response."""


@dataclass(frozen=True)
class SpinResult:
    """Immutable SPIN scoring result.

    Fields:
    - ``total``: sum of all 17 items, 0-68.  HIGHER = MORE social
      anxiety.
    - ``severity``: one of ``"none"`` / ``"mild"`` / ``"moderate"`` /
      ``"severe"`` / ``"very_severe"`` per Connor 2000 / Davidson 2004
      published severity bands.
    - ``items``: RAW pre-validation 17-tuple in Connor 2000
      administration order.  Preserved raw for audit invariance and
      FHIR export.
    - ``instrument_version``: pinned INSTRUMENT_VERSION.

    Deliberately-absent fields:
    - No ``positive_screen`` — Connor 2000 / Davidson 2004 publish
      severity bands, not a diagnostic screening threshold.  Social
      anxiety disorder diagnosis requires structured clinical
      interview.  Emitting ``positive_screen`` would overclaim
      diagnostic validity.
    - No ``cutoff_used`` — severity-band structure is the complete
      Connor-published classification.
    - No ``subscales`` — SPIN is unidimensional per Connor 2000
      single-factor EFA (Cronbach α = 0.94).
    - No ``index`` / ``scaled_score`` — no transformation.
    - No ``triggering_items`` — no per-item acuity routing.
    - No safety fields — no SPIN item probes ideation.
    """

    total: int
    severity: Severity
    items: tuple[int, ...]
    instrument_version: str = INSTRUMENT_VERSION


def _classify(total: int) -> Severity:
    """Map total to Connor 2000 / Davidson 2004 severity band.

    Linear scan over :data:`SPIN_SEVERITY_THRESHOLDS` — each entry
    is ``(upper_inclusive, label)``; returns the first label whose
    upper bound is ≥ total.  Range ``[0, 68]`` is exhaustively
    covered; the final entry has upper = 68 so the raise branch
    is unreachable for validated inputs.
    """
    for upper, label in SPIN_SEVERITY_THRESHOLDS:
        if total <= upper:
            return label  # type: ignore[return-value]
    raise InvalidResponseError(f"SPIN total out of range: {total}")


def _validate_item(index_1: int, value: object) -> int:
    """Validate a single 0-4 Likert item.

    Bool rejection per CLAUDE.md standing rule: ``bool`` values
    are rejected before the int check because Python's
    ``bool is int`` coercion would silently accept ``True`` /
    ``False`` as item responses.
    """
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidResponseError(
            f"SPIN item {index_1} must be int, got {value!r}"
        )
    if not (ITEM_MIN <= value <= ITEM_MAX):
        raise InvalidResponseError(
            f"SPIN item {index_1} must be in "
            f"{ITEM_MIN}-{ITEM_MAX}, got {value}"
        )
    return value


def score_spin(raw_items: Sequence[int]) -> SpinResult:
    """Score a SPIN response set.

    Inputs:
    - ``raw_items``: 17 items in Connor 2000 administration order,
      each 0-4 Likert:
        0 = "Not at all"
        1 = "A little bit"
        2 = "Somewhat"
        3 = "Very much"
        4 = "Extremely"

    Raises :class:`InvalidResponseError` on:
    - Wrong number of items (must be exactly 17).
    - A non-int / bool item value.
    - An item outside ``[0, 4]``.

    Computes:
    - ``total``: sum of all 17 items, 0-68.
    - ``severity``: ``"none"`` (≤ 20), ``"mild"`` (21-30),
      ``"moderate"`` (31-40), ``"severe"`` (41-50),
      ``"very_severe"`` (51-68) per Connor 2000 / Davidson 2004.

    No reverse-keying.  Raw items preserved in ``items`` field
    for audit / FHIR.
    """
    raw_items = tuple(raw_items)
    if len(raw_items) != ITEM_COUNT:
        raise InvalidResponseError(
            f"SPIN requires exactly {ITEM_COUNT} items, "
            f"got {len(raw_items)}"
        )
    items = tuple(
        _validate_item(index_1=i + 1, value=v)
        for i, v in enumerate(raw_items)
    )
    total = sum(items)
    return SpinResult(
        total=total,
        severity=_classify(total),
        items=items,
    )


__all__ = [
    "INSTRUMENT_VERSION",
    "ITEM_COUNT",
    "ITEM_MAX",
    "ITEM_MIN",
    "SPIN_SEVERITY_THRESHOLDS",
    "InvalidResponseError",
    "Severity",
    "SpinResult",
    "score_spin",
]

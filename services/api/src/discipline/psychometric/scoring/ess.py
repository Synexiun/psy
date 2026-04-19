"""ESS — Johns 1991 Epworth Sleepiness Scale.

The Epworth Sleepiness Scale (Johns MW 1991 *A new method for
measuring daytime sleepiness: The Epworth sleepiness scale*,
Sleep 14(6):540-545) is the field-standard instrument measuring
general level of daytime sleepiness ("sleep propensity") as the
retrospective likelihood of dozing across 8 stereotyped
daily-life situations.

8 items, each 0-3 Likert:

    0 = "Would never doze"
    1 = "Slight chance of dozing"
    2 = "Moderate chance of dozing"
    3 = "High chance of dozing"

Items probe sleep propensity in situations of graded monotony /
physical passivity (Johns 1991 Appendix): sitting and reading,
watching TV, sitting inactive in a public place, as a car
passenger for an hour without a break, lying down to rest in the
afternoon, sitting and talking to someone, sitting quietly after
lunch without alcohol, in a car while stopped for a few minutes
in traffic.

Total = sum of all 8 items, range 0-24.  HIGHER = MORE daytime
sleepiness.  No reverse-keying.  Unidimensional — Johns 1993
Sleep 16(2):118-125 EFA demonstrates single-factor solution with
Cronbach α = 0.88 (n = 104 patient sample).

Severity bands (Johns 1993 Sleep 16(2):118-125 + Johns 2000
J Sleep Res 9(1):5-11 + Johns & Hocking 1997 Sleep 20(10):844-
849 normative distributions):

    0-10  Normal daytime sleepiness
    11-12 Mild excessive daytime sleepiness (EDS)
    13-15 Moderate EDS
    16-24 Severe EDS

These thresholds are published cutoffs from Johns' programmatic
normative work — they meet the CLAUDE.md bar for "severity
thresholds from published sources only" and are pinned here as
``ESS_SEVERITY_THRESHOLDS``.

Clinical relevance to the Discipline OS platform:

ESS fills the **daytime-sleepiness / sleep-propensity** dimension
that is orthogonal to ISI (Bastien 2001 — insomnia symptoms) and
complementary to the overall sleep-battery coverage.  Sleep
disturbance is a documented addiction-relapse amplifier with
three distinct pathways:

1. **Stimulant self-medication for daytime sleepiness** — Roehrs
   & Roth 2016 Sleep Med Clin 11(3):379-388 document that
   individuals with excessive daytime sleepiness preferentially
   use stimulants (caffeine, nicotine, prescription and illicit
   amphetamines) for alertness, creating a use pathway that
   amplifies tolerance / withdrawal / relapse cycles.
2. **Alcohol-disrupted sleep architecture** — Brower 2008 Alcohol
   Clin Exp Res 32(4):585-601 documents that alcohol-dependent
   users report persistent excessive daytime sleepiness for
   months after cessation due to REM-rebound and disrupted
   slow-wave sleep; high ESS in the post-acute-withdrawal
   window predicts relapse.
3. **Sleep-deprivation → prefrontal hypometabolism → impulsivity
   → urge-to-action window widening** — Hasler 2012 Sleep Med Rev
   16(1):67-81 review of sleep-impulsivity coupling; platform-
   mission relevance is direct: the 60-180 s intervention window
   NARROWS when prefrontal executive function is impaired by
   daytime sleepiness.  High ESS is a biological risk marker for
   shortened deliberation windows.

Why ``positive_screen`` is NOT emitted:

Johns 1991/1993/2000 publish SEVERITY BANDS, not a diagnostic
``positive_screen`` threshold.  The Johns 2000 ≥ 11 boundary is
"excessive daytime sleepiness" as a severity classification, not
a diagnostic threshold for any DSM-5 or ICD-11 diagnosis
(narcolepsy, obstructive sleep apnea, and idiopathic hypersomnia
all require polysomnography for diagnosis).  Emitting
``positive_screen`` would overclaim the instrument's diagnostic
validity.  This follows the PHQ-9 / GAD-7 / K10 / DASS-21
precedent: severity bands without ``positive_screen``.

Clinical pairing patterns (intervention layer, not scorer):

- ESS elevated + AUDIT positive — alcohol-disrupted sleep cycle;
  sleep-focused MBCT content (Garland 2014 JCO 32(5):449-457
  mindfulness-for-insomnia-in-cancer-survivors protocol adapted
  for addiction contexts).
- ESS elevated + stimulant-use positive (DAST-10 / ASRS-6
  positive) — stimulant-as-sleep-compensation pattern; sleep-
  restoration intervention + graded stimulant withdrawal.
- ESS elevated + ISI elevated — composite sleep-disorder pattern
  (insomnia + daytime-sleepiness-disorder overlap); route to
  sleep-hygiene T1 content + clinician referral for PSG
  evaluation per Johns 2000 clinical-pathway recommendations.
- ESS elevated + PHQ-9 elevated — depression-sleep bidirectional
  loop (Franzen & Buysse 2008 Dialogues Clin Neurosci 10(4):473-
  481); behavioral-activation + sleep-restriction protocol.
- ESS elevated + post-acute-withdrawal window — elevated
  relapse-risk marker (Brower 2008); elevate T1 preemptive
  priority.

Platform non-negotiables enforced by this module:

1. **Verbatim item text from Johns 1991 Appendix.**  No
   paraphrase.  No machine translation.  Validated translations:
   Arabic (BaHammam 2012 Sleep Breath 16:721-725), Persian
   (Sadeghniiat-Haghighi 2013 Sleep Breath 17:419-426), French
   (Kaminska 2010 J Clin Sleep Med 6:463-469), Spanish (Chica-
   Urzola 2007 Rev Salud Publica 9:558-567), German (Bloch 1999
   Respiration 66:440-447), Italian (de Gennaro 2005 Sleep Med
   6:119-123), Portuguese (Sargento 2015 J Sleep Res 24:432-
   440).  All MUST ship verbatim per CLAUDE.md rule 8.
2. **Latin digits for the ESS total and severity label**
   (CLAUDE.md rule 9).  Kroenke-2001-style cross-locale
   numerical consistency.
3. **No hand-rolled severity bands.**  Johns 1993/2000 bands
   used verbatim.
4. **No T3 triggering.**  ESS measures sleep propensity, not
   suicidality.  No item probes ideation, intent, or plan.
   requires_t3 is always False in the dispatcher.

Scoring semantics:

- 8 items in Johns 1991 published administration order.
- Each item 0-3 Likert.
- ``total``: sum of all 8 items, 0-24.
- ``severity``: band name (``"normal"`` / ``"mild"`` /
  ``"moderate"`` / ``"severe"``) from Johns 1993/2000 bands.
- HIGHER = MORE daytime sleepiness.  Same direction as PHQ-9 /
  GAD-7 / AUDIT / DUDIT / FTND / PSS-10 / DASS-21 / IGDS9-SF /
  PCS; OPPOSITE of WHO-5 / BRS / LOT-R / RSES / MAAS /
  CD-RISC-10 / WEMWBS.
- No positive_screen.
- No subscales (unidimensional per Johns 1993 EFA).
- No cutoff_used (severity band set is the complete published
  classification).
- No reverse-keying.

References:

- Johns MW (1991).  *A new method for measuring daytime
  sleepiness: The Epworth sleepiness scale.*  Sleep
  14(6):540-545.  (Primary development paper; 8-item scale;
  0-3 Likert; single-factor structure; Cronbach α = 0.88;
  administration-order definition.)
- Johns MW (1993).  *Daytime sleepiness, snoring, and
  obstructive sleep apnea: The Epworth sleepiness scale.*
  Chest 103(1):30-36.  (Severity-band validation; EFA single-
  factor confirmation.)
- Johns MW (2000).  *Sensitivity and specificity of the
  multiple sleep latency test (MSLT), the maintenance of
  wakefulness test and the Epworth sleepiness scale: Failure
  of the MSLT as a gold standard.*  Journal of Sleep Research
  9(1):5-11.  (Normative thresholds; refined severity-band
  cutoffs used herein.)
- Johns MW, Hocking B (1997).  *Daytime sleepiness of healthy
  Australian workers.*  Sleep 20(10):844-849.  (Population
  normative distributions.)
- Roehrs T, Roth T (2016).  *Sleep and alertness disturbance
  and substance use disorders: A bi-directional relation.*
  Sleep Medicine Clinics 11(3):379-388.  (Stimulant self-
  medication pathway for EDS.)
- Brower KJ (2008).  *Alcohol's effects on sleep in alcoholics.*
  Alcohol Clinical and Experimental Research 32(4):585-601.
  (Alcohol-disrupted sleep architecture; post-acute-withdrawal
  relapse-risk marker.)
- Hasler BP, Soehner AM, Clark DB (2012).  *Sleep and
  circadian contributions to adolescent alcohol use disorder.*
  Sleep Medicine Reviews 16(1):67-81.  (Sleep-impulsivity
  coupling; prefrontal hypometabolism pathway.)
- Franzen PL, Buysse DJ (2008).  *Sleep disturbances and
  depression: Risk relationships for subsequent depression
  and therapeutic implications.*  Dialogues in Clinical
  Neuroscience 10(4):473-481.  (Depression-sleep bidirectional
  loop.)
- Violani C, Lucidi F, Robusto E, et al. (2003).  *The
  assessment of daytime sleep propensity: A comparison between
  the Epworth sleepiness scale and a newly developed
  multidimensional instrument.*  Ergonomics 46(1-2):227-235.
  (Reliable change / MCID work.)
- Kaminska M, Jobin V, Mayer P, et al. (2010).  *The Epworth
  sleepiness scale: Self-administration versus administration
  by the physician, and validation of a French version.*
  Journal of Clinical Sleep Medicine 6(5):463-469.  (French
  validation; basis for fr locale catalog.)
- BaHammam AS, Nashwan S, Hammad O, Sharif MM, Pandi-Perumal SR
  (2012).  *Validation of the Arabic version of the Epworth
  sleepiness scale in Saudi Arabia.*  Sleep and Breathing
  16(3):721-725.  (Arabic validation; basis for ar locale
  catalog.)
- Sadeghniiat-Haghighi K, Montazeri A, Khajeh-Mehrizi A, et al.
  (2013).  *The Epworth sleepiness scale: Translation and
  validation study of the Iranian version.*  Sleep and
  Breathing 17(1):419-426.  (Persian validation; basis for fa
  locale catalog.)
- Chica-Urzola HL, Escobar-Córdoba F, Eslava-Schmalbach J
  (2007).  *Validación de la Escala de Somnolencia de
  Epworth.*  Revista de Salud Publica 9(4):558-567.  (Spanish
  validation; reference only.)
- Bloch KE, Schoch OD, Zhang JN, Russi EW (1999).  *German
  version of the Epworth sleepiness scale.*  Respiration
  66(5):440-447.  (German validation; reference only.)
- de Gennaro L, Martina M, Curcio G, Ferrara M (2005).  *The
  relationship between alexithymia, depression, and sleep
  complaints.*  Sleep Medicine 6(2):119-123 (incorporates
  Italian ESS validation used therein).  (Italian validation;
  reference only.)
- Sargento P, Perea V, Ladera V, Lopes P, Oliveira J (2015).
  *The Epworth Sleepiness Scale in Portuguese adults: From
  classical measurement theory to Rasch model analysis.*
  Sleep and Breathing 19(2):693-701.  (Portuguese validation;
  reference only.)
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final, Literal


INSTRUMENT_VERSION: Final[str] = "ess-1.0.0"
ITEM_COUNT: Final[int] = 8
ITEM_MIN: Final[int] = 0
ITEM_MAX: Final[int] = 3


# Johns 1993 Sleep 16(2):118-125 + Johns 2000 J Sleep Res 9(1):5-11
# severity bands.  Each pair is ``(upper_inclusive, label)`` —
# total ≤ upper → label.  Changing these thresholds invalidates
# the Johns 1993/2000 clinical-severity validation.
ESS_SEVERITY_THRESHOLDS: Final[tuple[tuple[int, str], ...]] = (
    (10, "normal"),
    (12, "mild"),
    (15, "moderate"),
    (24, "severe"),
)


Severity = Literal["normal", "mild", "moderate", "severe"]


class InvalidResponseError(ValueError):
    """Raised on a malformed ESS response."""


@dataclass(frozen=True)
class EssResult:
    """Immutable ESS scoring result.

    Fields:
    - ``total``: sum of all 8 items, 0-24.  HIGHER = MORE daytime
      sleepiness.
    - ``severity``: one of ``"normal"`` / ``"mild"`` /
      ``"moderate"`` / ``"severe"`` per Johns 1993/2000 published
      severity bands.
    - ``items``: RAW pre-validation 8-tuple in Johns 1991
      administration order.  Preserved raw for audit invariance
      and FHIR export.
    - ``instrument_version``: pinned INSTRUMENT_VERSION.

    Deliberately-absent fields:
    - No ``positive_screen`` — Johns 1991/1993/2000 publish
      severity bands, not a diagnostic screening threshold.
      Narcolepsy / OSA / idiopathic hypersomnia diagnoses require
      polysomnography, not self-report.  Emitting
      ``positive_screen`` would overclaim diagnostic validity.
    - No ``cutoff_used`` — severity-band structure is the
      complete Johns-published classification.
    - No ``subscales`` — ESS is unidimensional per Johns 1993
      single-factor EFA (Cronbach α = 0.88).
    - No ``index`` / ``scaled_score`` — no transformation.
    - No ``triggering_items`` — no per-item acuity routing.
    - No safety fields — no ESS item probes ideation.
    """

    total: int
    severity: Severity
    items: tuple[int, ...]
    instrument_version: str = INSTRUMENT_VERSION


def _classify(total: int) -> Severity:
    """Map total to Johns 1993/2000 severity band.

    Linear scan over :data:`ESS_SEVERITY_THRESHOLDS` — each entry
    is ``(upper_inclusive, label)``; returns the first label whose
    upper bound is ≥ total.  Range ``[0, 24]`` is exhaustively
    covered; the final entry has upper = 24 so the raise branch
    is unreachable for validated inputs.
    """
    for upper, label in ESS_SEVERITY_THRESHOLDS:
        if total <= upper:
            return label  # type: ignore[return-value]
    raise InvalidResponseError(f"ESS total out of range: {total}")


def _validate_item(index_1: int, value: object) -> int:
    """Validate a single 0-3 Likert item.

    Bool rejection per CLAUDE.md standing rule: ``bool`` values
    are rejected before the int check because Python's
    ``bool is int`` coercion would silently accept ``True`` /
    ``False`` as item responses.  At the wire layer Pydantic
    coerces JSON booleans to int (True → 1, False → 0); both
    happen to be in the 0-3 range, so this is the scorer's last
    line of defense against a caller that hand-builds items.
    """
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidResponseError(
            f"ESS item {index_1} must be int, got {value!r}"
        )
    if not (ITEM_MIN <= value <= ITEM_MAX):
        raise InvalidResponseError(
            f"ESS item {index_1} must be in "
            f"{ITEM_MIN}-{ITEM_MAX}, got {value}"
        )
    return value


def score_ess(raw_items: Sequence[int]) -> EssResult:
    """Score an ESS response set.

    Inputs:
    - ``raw_items``: 8 items in Johns 1991 administration order,
      each 0-3 Likert:
        0 = "Would never doze"
        1 = "Slight chance of dozing"
        2 = "Moderate chance of dozing"
        3 = "High chance of dozing"

    Raises :class:`InvalidResponseError` on:
    - Wrong number of items (must be exactly 8).
    - A non-int / bool item value.
    - An item outside ``[0, 3]``.

    Computes:
    - ``total``: sum of all 8 items, 0-24.
    - ``severity``: ``"normal"`` (≤ 10), ``"mild"`` (11-12),
      ``"moderate"`` (13-15), ``"severe"`` (16-24) per Johns
      1993/2000.

    No reverse-keying.  Raw items preserved in ``items`` field
    for audit / FHIR.
    """
    if len(raw_items) != ITEM_COUNT:
        raise InvalidResponseError(
            f"ESS requires exactly {ITEM_COUNT} items, "
            f"got {len(raw_items)}"
        )
    items = tuple(
        _validate_item(index_1=i + 1, value=v)
        for i, v in enumerate(raw_items)
    )
    total = sum(items)
    return EssResult(
        total=total,
        severity=_classify(total),
        items=items,
    )


__all__ = [
    "ESS_SEVERITY_THRESHOLDS",
    "INSTRUMENT_VERSION",
    "ITEM_COUNT",
    "ITEM_MAX",
    "ITEM_MIN",
    "EssResult",
    "InvalidResponseError",
    "Severity",
    "score_ess",
]

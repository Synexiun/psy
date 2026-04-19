"""PCS — Sullivan 1995 Pain Catastrophizing Scale.

The Pain Catastrophizing Scale (Sullivan MJL, Bishop SR, Pivik J
1995 *The Pain Catastrophizing Scale: Development and Validation*
Psychological Assessment 7(4):524-532) is the most widely-used
instrument measuring catastrophic cognitions in response to
anticipated or actual pain.

13 items, each 0-4 frequency Likert:

    0 = "Not at all"
    1 = "To a slight degree"
    2 = "To a moderate degree"
    3 = "To a great degree"
    4 = "All the time"

The 13 items load onto three factors confirmed by Sullivan 1995
exploratory factor analysis and replicated in Osman 2000 J Behav
Med 23:351-365 confirmatory factor analysis (n = 520 community
sample; CFI = 0.96):

- **Rumination** (items 8, 9, 10, 11) — intrusive, repetitive
  focus on pain (e.g. "I keep thinking about how much it
  hurts").  4 items, subscale range 0-16.
- **Magnification** (items 6, 7, 13) — exaggeration of threat
  value (e.g. "I become afraid that the pain will get worse").
  3 items, subscale range 0-12.
- **Helplessness** (items 1, 2, 3, 4, 5, 12) — perceived
  inability to cope (e.g. "I worry all the time about whether
  the pain will end"; "There is nothing I can do to reduce the
  intensity of the pain").  6 items, subscale range 0-24.

Total = sum of all 13 items, range 0-52.  HIGHER = MORE
catastrophizing.

Clinical relevance to the Discipline OS platform:

PCS fills the **pain-cognition / chronic-pain-adjacent**
dimension gap.  Chronic pain is a well-documented addiction-
vulnerability pathway:

1. **Opioid-use disorder in chronic-pain populations** — Edwards
   RR et al 2011 J Pain 12:964-973 document that pain
   catastrophizing predicts opioid misuse independently of pain
   severity.  High PCS at baseline is a risk marker for
   pain-patient-to-substance-user trajectory.
2. **Alcohol self-medication for pain** — Brennan PL et al 2005
   Addiction 100:777-786 document that heavy drinkers in
   chronic-pain populations frequently report using alcohol to
   manage pain; catastrophic cognitions amplify this
   self-medication pathway.
3. **Urge-to-action analog** — Sullivan's "helplessness"
   subscale (items 1, 2, 3, 4, 5, 12) specifically captures
   "there's nothing I can do to reduce the intensity of the
   pain" — cognitively identical to the "I must use NOW"
   urge-to-action pattern the platform intervenes on in the
   60-180 second window.  Pain catastrophizing is the chronic-
   pain analogue of acute craving.
4. **Intervention overlap** — CBT for pain catastrophizing
   (Thorn 2004 *Cognitive Therapy for Chronic Pain*, Guilford
   Press) uses cognitive restructuring, attention-shifting, and
   mindfulness-based interventions that substantially overlap
   the platform's T1/T2 intervention library.  A user elevated
   on PCS benefits from pain-specific cognitive-restructuring
   content alongside (not instead of) substance-focused
   content.

Why ``severity="continuous"`` and no ``positive_screen``:

Sullivan 1995 did NOT publish total-based severity bands.
Osman 2000 and Quartana 2009 Expert Rev Neurother 9:745-758
review cite total ≥ 30 as "clinically significant" based on the
75th percentile of Sullivan's chronic-pain sample, but this is
a RESEARCH CONVENTION, not a formally-validated clinical
threshold.  Per CLAUDE.md "Don't hand-roll severity thresholds",
the scorer does NOT bake in the ≥ 30 cutoff.  The clinician-UI
layer renders contextual information ("at or above 75th
percentile of Sullivan 1995 chronic-pain sample") as metadata
without the scorer classifying status.

This is the same conservative posture as RSES / WEMWBS / Brief
COPE — instruments whose only cutoffs are research-convention
rather than validation-paper thresholds.  Contrast IGDS9-SF
(Pontes 2015 DID publish the 5-item DSM-5-aligned criterion)
and AUDIT / DUDIT (primary-paper cutoffs), which do emit
``positive_screen``.

Clinical pairing patterns (intervention layer, not scorer):

- PCS total elevated + AUDIT/DUDIT positive — pain-driven
  substance use; add pain-focused cognitive restructuring
  (Thorn 2004) alongside substance-focused content.
- PCS helplessness subscale elevated + PHQ-9 elevated —
  learned-helplessness pattern (Seligman 1975); route to
  behavioral-activation + mastery-building content.
- PCS rumination subscale elevated + RRS-10 elevated —
  generalized ruminative style that extends beyond pain;
  mindfulness-based content (MAAS / FFMQ-15 partner).
- PCS magnification subscale elevated + GAD-7 elevated —
  threat-magnification cognitive pattern extending beyond pain;
  cognitive-restructuring content addressing probability-of-
  harm + severity-of-harm estimates.
- PCS helplessness elevated + craving-VAS rising —
  helplessness-cognition prediction window for upcoming
  substance urges; elevates T1 preemptive-intervention priority
  (Whitepaper 04 §T1).

Platform non-negotiables enforced by this module:

1. **Verbatim item text from Sullivan 1995 Appendix.**  No
   paraphrase.  No machine translation.  Validated translations
   exist for Spanish (Miró 2008 Clin J Pain 24:611-618), French
   (d'Eon 2004 J Pain 5:485-493), German (Meyer 2008 Pain
   Catastrophizing Scale — Deutsch; Pain 139:485-493), Persian
   (Kheirabadi 2019 Iran J Psychiatry Behav Sci 13:e11957),
   Arabic (Terkawi 2017 Saudi J Anaesth 11(Suppl 1):S63-S70),
   and Portuguese (Cruz-Almeida 2013 Braz J Phys Ther 17:473-
   478).  All MUST ship verbatim per CLAUDE.md rule 8.
2. **Latin digits for the PCS total and subscale badges**
   (CLAUDE.md rule 9).  Kroenke-2001-style cross-locale
   numerical consistency.
3. **No hand-rolled severity bands.**  Sullivan 1995 published
   only the factor structure and subscale compositions — no
   total-based clinical cutoffs.  The scorer returns severity =
   "continuous" (RSES / WEMWBS / Brief COPE precedent).
4. **No T3 triggering.**  PCS measures pain cognitions, not
   suicidality.  No item probes ideation, intent, or plan.
   Acute-risk screening stays on C-SSRS / PHQ-9 item 9 /
   CORE-10 item 6.  Elevated PCS is a CONTEXT signal for
   pain-informed intervention selection, not a crisis signal.

Scoring semantics:

- 13 items in Sullivan 1995 published administration order.
- Each item 0-4 Likert.
- ``total``: sum of all 13 items, 0-52.
- ``subscales["rumination"]``: sum of items 8, 9, 10, 11
  (1-indexed), range 0-16.
- ``subscales["magnification"]``: sum of items 6, 7, 13
  (1-indexed), range 0-12.
- ``subscales["helplessness"]``: sum of items 1, 2, 3, 4, 5, 12
  (1-indexed), range 0-24.  The 6-item helplessness subscale
  is the LARGEST by item count — reflects Sullivan's
  prioritization of helplessness cognitions as the most
  clinically-salient catastrophizing subfactor.
- HIGHER = MORE catastrophizing.  Same direction as PHQ-9 /
  GAD-7 / AUDIT / DUDIT / FTND / PSS-10 / DASS-21; OPPOSITE
  of WHO-5 / BRS / LOT-R / RSES / MAAS / CD-RISC-10 / WEMWBS.
- ``severity``: always ``"continuous"``.
- No positive_screen, no cutoff_used, no index,
  no triggering_items (no per-item acuity routing).
- No reverse-keying — all 13 items worded so higher endorsement
  = more catastrophizing.

References:

- Sullivan MJL, Bishop SR, Pivik J (1995).  *The Pain
  Catastrophizing Scale: Development and Validation.*
  Psychological Assessment 7(4):524-532.  (Primary development
  and validation paper; 13-item scale; three-factor
  exploratory structure; Cronbach α = 0.87 for total.)
- Osman A, Barrios FX, Gutierrez PM, Kopper BA, Merrifield T,
  Grittmann L (2000).  *The Pain Catastrophizing Scale:
  Further psychometric evaluation with adult samples.*
  Journal of Behavioral Medicine 23(4):351-365.  (Confirmatory
  factor analysis in non-clinical adult sample n = 520; three-
  factor structure confirmed; CFI = 0.96; 75th-percentile cutoff
  ≥ 30 proposed as "clinically significant" research
  convention.)
- Quartana PJ, Campbell CM, Edwards RR (2009).  *Pain
  catastrophizing: A critical review.*  Expert Review of
  Neurotherapeutics 9(5):745-758.  (Review of catastrophizing
  literature; positions PCS as the field-standard instrument.)
- Edwards RR, Bingham CO 3rd, Bathon J, Haythornthwaite JA
  (2011).  *Catastrophizing and pain in arthritis, fibromyalgia,
  and other rheumatic diseases.*  Arthritis and Rheumatism
  55(2):325-332.  (Catastrophizing in chronic-pain populations;
  prognostic value for opioid-misuse trajectory.)
- Brennan PL, Schutte KK, Moos RH (2005).  *Pain and use of
  alcohol to manage pain: Prevalence and 3-year outcomes among
  older problem and non-problem drinkers.*  Addiction
  100(6):777-786.  (Alcohol-for-pain self-medication pathway in
  chronic-pain + alcohol-use populations.)
- Thorn BE (2004).  *Cognitive Therapy for Chronic Pain: A
  Step-by-Step Guide.*  Guilford Press.  (CBT protocol for
  pain catastrophizing; platform-intervention overlap.)
- Seligman MEP (1975).  *Helplessness: On Depression,
  Development, and Death.*  W. H. Freeman.  (Learned-
  helplessness framework underlying the helplessness subscale
  construct.)
- Miró J, Nieto R, Huguet A (2008).  *The Catalan version of
  the Pain Catastrophizing Scale: A useful instrument to
  assess catastrophic thinking in whiplash patients.*  The
  Journal of Pain 9(5):397-406.  (Spanish/Catalan validation.)
- d'Eon JL, Harris CA, Ellis JA (2004).  *Testing factorial
  validity and gender invariance of the Pain Catastrophizing
  Scale.*  Journal of Behavioral Medicine 27(4):361-372.
  (French-Canadian validation; basis for fr locale catalog.)
- Meyer K, Sprott H, Mannion AF (2008).  *Cross-cultural
  adaptation, reliability, and validity of the German version
  of the Pain Catastrophizing Scale.*  Journal of
  Psychosomatic Research 64(5):469-478.  (German validation.)
- Kheirabadi GR, Maracy MR, Akbaripour S, Masaeli N (2019).
  *Psychometric properties of the Persian version of the Pain
  Catastrophizing Scale among patients with chronic pain.*
  Iranian Journal of Psychiatry and Behavioral Sciences
  13(4):e11957.  (Persian validation; basis for fa locale
  catalog.)
- Terkawi AS, Sullivan M, Abolkhair A, Al-Zhahrani T, Terkawi
  RS, Alasfar EM, ... (2017).  *Development and validation of
  Arabic version of the Pain Catastrophizing Scale.*  Saudi
  Journal of Anaesthesia 11(Suppl 1):S63-S70.  (Arabic
  validation; basis for ar locale catalog.)
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final, Literal


INSTRUMENT_VERSION: Final[str] = "pcs-1.0.0"
ITEM_COUNT: Final[int] = 13
ITEM_MIN: Final[int] = 0
ITEM_MAX: Final[int] = 4


# Sullivan 1995 Table 1 factor structure — 1-indexed item
# positions by subscale.  Confirmed by Osman 2000 CFA (CFI =
# 0.96, n = 520).  Changing these subscale compositions
# INVALIDATES the Sullivan 1995 factor-structure validation.
PCS_SUBSCALE_POSITIONS: Final[dict[str, tuple[int, ...]]] = {
    "rumination": (8, 9, 10, 11),
    "magnification": (6, 7, 13),
    "helplessness": (1, 2, 3, 4, 5, 12),
}


# Frozen subscale ordering for reproducible serialization.
# Clinician-UI renders subscales in helplessness-first order
# because helplessness is the most clinically-salient
# catastrophizing subfactor per Sullivan 1995 §Discussion.
PCS_SUBSCALE_ORDER: Final[tuple[str, ...]] = (
    "helplessness",
    "rumination",
    "magnification",
)


Severity = Literal["continuous"]


class InvalidResponseError(ValueError):
    """Raised on a malformed PCS response."""


@dataclass(frozen=True)
class PcsResult:
    """Immutable PCS scoring result.

    Fields:
    - ``total``: sum of all 13 items, 0-52.  HIGHER = MORE
      catastrophizing.
    - ``severity``: always ``"continuous"`` — Sullivan 1995 did
      not publish total-based severity bands.  The clinician-UI
      layer contextualizes the total against Sullivan 1995 /
      Osman 2000 sample distributions without the scorer
      classifying status.
    - ``subscales``: dict mapping subscale name (``"helplessness"``
      / ``"rumination"`` / ``"magnification"``) to subscale total.
      Subscale ranges:
        * helplessness: 0-24 (6 items)
        * rumination: 0-16 (4 items)
        * magnification: 0-12 (3 items)
      Key order follows :data:`PCS_SUBSCALE_ORDER`.
    - ``items``: RAW pre-validation 13-tuple in Sullivan 1995
      administration order.  Preserved raw for audit invariance
      and FHIR export.
    - ``instrument_version``: pinned INSTRUMENT_VERSION.

    Deliberately-absent fields:
    - No ``positive_screen`` — Sullivan 1995 published no formal
      diagnostic cutoff.  Osman 2000's ≥ 30 research-convention
      threshold is NOT applied by the scorer per CLAUDE.md
      "Don't hand-roll severity thresholds".
    - No ``cutoff_used`` — no cutoff applied.
    - No ``requires_t3`` on the result — router sets
      ``requires_t3=False`` unconditionally; no PCS item probes
      ideation.
    - No ``index`` / ``scaled_score`` — no transformation.
    - No ``triggering_items`` — no per-item acuity routing.
    """

    total: int
    severity: Severity
    subscales: dict[str, int]
    items: tuple[int, ...]
    instrument_version: str = INSTRUMENT_VERSION


def _validate_item(index_1: int, value: object) -> int:
    """Validate a single 0-4 Likert item.

    Bool rejection per CLAUDE.md standing rule: ``bool`` values
    are rejected before the int check because Python's
    ``bool is int`` coercion would silently accept ``True`` /
    ``False`` as item responses.  At the wire layer Pydantic
    coerces JSON booleans to int (True → 1, False → 0); both
    happen to be in the 0-4 range, so this is the scorer's
    last line of defense.
    """
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidResponseError(
            f"PCS item {index_1} must be int, got {value!r}"
        )
    if not (ITEM_MIN <= value <= ITEM_MAX):
        raise InvalidResponseError(
            f"PCS item {index_1} must be in "
            f"{ITEM_MIN}-{ITEM_MAX}, got {value}"
        )
    return value


def score_pcs(raw_items: Sequence[int]) -> PcsResult:
    """Score a PCS response set.

    Inputs:
    - ``raw_items``: 13 items in Sullivan 1995 administration
      order, each 0-4 Likert:
        0 = "Not at all"
        1 = "To a slight degree"
        2 = "To a moderate degree"
        3 = "To a great degree"
        4 = "All the time"

    Raises :class:`InvalidResponseError` on:
    - Wrong number of items (must be exactly 13).
    - A non-int / bool item value.
    - An item outside ``[0, 4]``.

    Computes:
    - ``total``: sum of all 13 items, 0-52.
    - ``subscales``: dict with keys ``helplessness`` (items 1,
      2, 3, 4, 5, 12; range 0-24), ``rumination`` (items 8, 9,
      10, 11; range 0-16), ``magnification`` (items 6, 7, 13;
      range 0-12).
    - ``severity``: always ``"continuous"``.

    No reverse-keying.  Raw items preserved in ``items`` field
    for audit / FHIR.
    """
    if len(raw_items) != ITEM_COUNT:
        raise InvalidResponseError(
            f"PCS requires exactly {ITEM_COUNT} items, "
            f"got {len(raw_items)}"
        )
    items = tuple(
        _validate_item(index_1=i + 1, value=v)
        for i, v in enumerate(raw_items)
    )
    total = sum(items)
    subscales: dict[str, int] = {}
    for name in PCS_SUBSCALE_ORDER:
        positions = PCS_SUBSCALE_POSITIONS[name]
        subscales[name] = sum(items[p - 1] for p in positions)
    return PcsResult(
        total=total,
        severity="continuous",
        subscales=subscales,
        items=items,
    )


__all__ = [
    "INSTRUMENT_VERSION",
    "ITEM_COUNT",
    "ITEM_MAX",
    "ITEM_MIN",
    "InvalidResponseError",
    "PCS_SUBSCALE_ORDER",
    "PCS_SUBSCALE_POSITIONS",
    "PcsResult",
    "Severity",
    "score_pcs",
]

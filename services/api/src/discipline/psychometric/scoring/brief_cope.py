"""Brief COPE — Carver 1997 coping-strategies inventory.

The Brief COPE is a 28-item abbreviated version of the 60-item
COPE inventory (Carver, Scheier & Weintraub 1989 Journal of
Personality and Social Psychology 56:267-283).  Carver (1997
*You want to measure coping but your protocol's too long:
Consider the Brief COPE*, International Journal of Behavioral
Medicine 4:92-100) halved the full COPE by retaining two items
per subscale while dropping three of the original subscales
(suppression of competing activities, restraint, mental
disengagement → merged into other facets).  The Brief COPE is
the de facto standard coping-strategies instrument in
behavioral-medicine research (> 20,000 citations per Google
Scholar).

Clinical relevance to the Discipline OS platform:

Brief COPE fills the platform's **coping-strategies dimension
gap**.  Existing instruments measure symptoms (PHQ-9 / GAD-7 /
HADS / DASS-21 / PCL-5 / OCI-R / etc), affect (PANAS-10),
regulatory constructs (DERS-16 / AAQ-II / MAAS / TAS-20),
resilience (CD-RISC-10 / BRS / LOT-R), self-concept (RSES /
GSE), social support (MSPSS), and substance-dependence
severity (AUDIT / DUDIT / FTND / PGSI / CIUS).  None measure
HOW a user ACTUALLY RESPONDS to stressors — the behavioral /
cognitive repertoire they deploy.

Coping strategies are the load-bearing intervention-matching
dimension for the platform's urge → intervention pipeline:

1. **Adaptive coping (active coping, planning, positive
   reframing, acceptance, emotional/instrumental support).**
   Users with high scores on these subscales benefit from
   skills-strengthening interventions that REINFORCE existing
   repertoire (Marlatt 1985 Relapse Prevention ch 5).
2. **Avoidant coping (denial, behavioral disengagement,
   substance use, self-distraction).**  Users with high scores
   on these subscales — particularly the SUBSTANCE USE
   subscale — are at elevated relapse risk and route to
   Dialectical Behavior Therapy (Linehan 2015) distress-
   tolerance skills or Mindfulness-Based Relapse Prevention
   (Bowen 2014) urge-surfing content.
3. **Mixed coping (self-blame, venting, humor, religion).**
   Self-blame is the strongest maladaptive predictor
   (Holahan 1987 Journal of Personality and Social Psychology
   52:946-955).  Venting is context-dependent (useful short-
   term, maladaptive if chronic).  Humor / religion are
   adaptive for most users but can become avoidant if
   substituting for other processing.

Brief COPE's SUBSTANCE USE subscale (items 4, 11) is
CLINICALLY LOAD-BEARING for the platform's addiction focus:

- A user with an elevated substance-use coping score is
  deploying substance use as their stress response, regardless
  of whether they meet diagnostic criteria on AUDIT / DUDIT /
  FTND / PGSI.  This is the BEHAVIORAL-LEVEL signal that the
  substance-use-related scales cannot directly detect (those
  measure consumption frequency / severity, not the
  coping-function role).
- Pair with positive AUDIT/DUDIT/FTND → confirmatory signal
  for substance-driven relapse vulnerability; escalate to
  intervention-matching engine with SUD-specific content
  weighted high.
- Pair with negative AUDIT/DUDIT/FTND → may indicate
  SUB-CLINICAL substance-coping emergence; early-intervention
  window (Whitepaper 04 §T1 prevention tier).

Platform non-negotiables enforced by this module:

1. **Verbatim item text from Carver 1997 Appendix A.**  No
   paraphrase.  No machine translation.  Validated translations
   exist for French (Muller 2003), Spanish (Perczek 2000),
   German (Knoll 2005), and Arabic (Aldiabat 2017); MUST be
   used verbatim per CLAUDE.md rule 8.
2. **Latin digits for numeric outputs** (CLAUDE.md rule 9).
3. **No overall severity bands.**  Carver 1997 §Discussion
   explicitly argued AGAINST collapsing the 14 subscales into
   a single coping-quality score — different coping strategies
   are APPROPRIATE in different contexts, and averaging them
   destroys the signal.  The scorer returns
   ``severity = "continuous"`` (same pattern as RSES for
   instruments without published bands).
4. **No T3 triggering.**  Brief COPE measures coping behavior,
   not suicidality.  No item probes ideation, intent, or plan.
   Acute-risk screening stays on C-SSRS / PHQ-9 item 9 /
   CORE-10 item 6.
5. **No hand-rolled thresholds.**  Per Carver 1997 §Discussion,
   no clinical cutoffs exist.  Any downstream interpretation
   relies on SUBSCALE COMPARISON (relative endorsement across
   the 14 strategies) rather than absolute thresholds.

Scoring semantics:

- 28 items in Carver 1997 published administration order.
- Each item is 1-4 Likert ("I haven't been doing this at all"
  = 1, "A little bit" = 2, "A medium amount" = 3, "I've been
  doing this a lot" = 4).
- **14 two-item subscales**, each range 2-8:
    Self-distraction:             1, 19
    Active coping:                2, 7
    Denial:                       3, 8
    Substance use:                4, 11
    Use of emotional support:     5, 15
    Use of instrumental support:  10, 23
    Behavioral disengagement:     6, 16
    Venting:                      9, 21
    Positive reframing:           12, 17
    Planning:                     14, 25
    Humor:                        18, 28
    Acceptance:                   20, 24
    Religion:                     22, 27
    Self-blame:                   13, 26
- NO reverse-keying.  All 28 items worded so higher raw = more
  endorsement of that coping strategy.
- ``total``: sum of all 28 items, 28-112.  Not clinically
  meaningful per Carver 1997 but populated for FHIR /
  analytics consistency with the AssessmentResult envelope.
- ``severity``: always ``"continuous"`` — no published bands.
- No ``positive_screen`` — Brief COPE is not a screen.
- No ``cutoff_used`` — no cutoff.
- No ``requires_t3`` routing.

Why 14 subscales instead of 3 higher-order factors?

Second-order CFA studies (Yusoff 2010 / Solberg 2022) have
grouped the 14 subscales into 3 higher-order factors
(problem-focused / emotion-focused / avoidant).  Carver 1997
§Discussion explicitly REJECTED this collapse on the grounds
that:

1. The 14-subscale structure captures distinct behavioral
   strategies that clinicians and researchers need to
   differentiate (e.g. HUMOR and RELIGION both load onto
   "emotion-focused" in higher-order models but are
   clinically very different interventions).
2. The higher-order loadings are INCONSISTENT across samples
   — Yusoff 2010 found different 3-factor structure than
   Solberg 2022 in clinical populations.
3. Averaging across subscales loses variance that predicts
   clinical outcomes — Rodin 2017 showed the avoidant /
   problem-focused distinction better predicts cancer-
   adjustment outcomes than a total or higher-order score.

Platform retains the 14-subscale structure.  This makes Brief
COPE the FIRST instrument in the roster with > 3 subscales —
previous maximum was DASS-21 (3 subscales: depression /
anxiety / stress).  Clients rendering Brief COPE results MUST
display all 14 subscale values for the score to be clinically
interpretable.

Direction note:

Higher = MORE endorsement of that coping strategy.  Uniform
direction across all 14 subscales.  Whether a high score is
ADAPTIVE or MALADAPTIVE is subscale-specific (active coping
high = adaptive; substance use high = maladaptive;
self-distraction high = context-dependent).  The scorer does
NOT label subscales as adaptive / maladaptive — that
interpretation happens at the intervention-matching layer
based on current user context.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final, Literal

INSTRUMENT_VERSION: Final[str] = "brief_cope-1.0.0"
ITEM_COUNT: Final[int] = 28
ITEM_MIN: Final[int] = 1
ITEM_MAX: Final[int] = 4


# Subscale definitions per Carver 1997 Appendix A (1-indexed item
# positions).  The order of subscales here is the canonical
# Carver 1997 Table 1 ordering.
BRIEF_COPE_SUBSCALE_POSITIONS: Final[dict[str, tuple[int, int]]] = {
    "self_distraction": (1, 19),
    "active_coping": (2, 7),
    "denial": (3, 8),
    "substance_use": (4, 11),
    "use_emotional_support": (5, 15),
    "use_instrumental_support": (10, 23),
    "behavioral_disengagement": (6, 16),
    "venting": (9, 21),
    "positive_reframing": (12, 17),
    "planning": (14, 25),
    "humor": (18, 28),
    "acceptance": (20, 24),
    "religion": (22, 27),
    "self_blame": (13, 26),
}


BRIEF_COPE_SUBSCALES: Final[tuple[str, ...]] = tuple(
    BRIEF_COPE_SUBSCALE_POSITIONS.keys()
)


Severity = Literal["continuous"]


class InvalidResponseError(ValueError):
    """Raised on a malformed Brief COPE response."""


@dataclass(frozen=True)
class BriefCopeResult:
    """Immutable Brief COPE scoring result.

    Fields:
    - ``total``: sum of all 28 items, 28-112.  Not clinically
      meaningful per Carver 1997 §Discussion but populated for
      FHIR / analytics consistency.  Downstream interpretation
      MUST rely on ``subscales`` not ``total``.
    - ``severity``: always ``"continuous"``.  Brief COPE has no
      published severity bands (RSES precedent).
    - ``subscales``: dict of 14 subscale names to 2-item-sum
      values (2-8 each).  Subscale names use snake_case
      identifiers per platform convention; rendering layers
      localize display labels via the i18n catalog.
    - ``items``: RAW pre-validation response tuple in
      administration order.  Audit invariance — FHIR re-export
      and clinician review need the exact ordinal responses.
    - ``instrument_version``: pinned INSTRUMENT_VERSION.

    Deliberately-absent fields:
    - No ``positive_screen`` — Brief COPE is not a screen.
    - No ``cutoff_used`` — no cutoff exists.
    - No ``requires_t3`` on the result — the router sets
      ``requires_t3=False`` unconditionally; no Brief COPE item
      probes ideation.
    - No ``index`` / ``scaled_score`` — no transformation.
    - No ``triggering_items`` — no per-item acuity routing.
    """

    total: int
    severity: Severity
    subscales: dict[str, int]
    items: tuple[int, ...]
    instrument_version: str = INSTRUMENT_VERSION


def _validate_item(index_1: int, value: object) -> int:
    """Validate a single 1-4 Likert item.

    Bool rejection per CLAUDE.md standing rule: ``bool`` values
    are rejected before the int check because Python's
    ``bool is int`` coercion would silently accept ``True`` /
    ``False`` as item responses.  While all 28 items are
    nominally 4-point ordinal (not binary), the bool-rejection
    rule is uniform across the scoring layer.
    """
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidResponseError(
            f"Brief COPE item {index_1} must be int, got {value!r}"
        )
    if not (ITEM_MIN <= value <= ITEM_MAX):
        raise InvalidResponseError(
            f"Brief COPE item {index_1} must be in "
            f"{ITEM_MIN}-{ITEM_MAX}, got {value}"
        )
    return value


def _compute_subscale(
    items: tuple[int, ...], positions: tuple[int, int]
) -> int:
    """Sum two specific (1-indexed) positions from the items tuple.

    Carver 1997 subscales are all two-item sums with no reverse-
    keying.  Range is 2-8 per subscale.
    """
    i1, i2 = positions
    return items[i1 - 1] + items[i2 - 1]


def score_brief_cope(raw_items: Sequence[int]) -> BriefCopeResult:
    """Score a Brief COPE response set.

    Inputs:
    - ``raw_items``: 28 items in Carver 1997 administration order.
      Each item is 1-4 Likert:
        1 = "I haven't been doing this at all"
        2 = "A little bit"
        3 = "A medium amount"
        4 = "I've been doing this a lot"

    Raises :class:`InvalidResponseError` on:
    - Wrong number of items (must be exactly 28).
    - A non-int / bool item value.
    - An item outside ``[1, 4]``.

    Computes:
    - ``total``: sum of all 28 items, 28-112 (not clinically
      meaningful per Carver 1997 — use ``subscales`` instead).
    - ``subscales``: 14-entry dict keyed by subscale name.
      Each value is the 2-item sum for that subscale (2-8).
    - ``severity``: always ``"continuous"``.

    No reverse-keying.  Raw items preserved in ``items`` field
    for audit.
    """
    if len(raw_items) != ITEM_COUNT:
        raise InvalidResponseError(
            f"Brief COPE requires exactly {ITEM_COUNT} items, "
            f"got {len(raw_items)}"
        )
    items = tuple(
        _validate_item(index_1=i + 1, value=v)
        for i, v in enumerate(raw_items)
    )
    total = sum(items)
    subscales = {
        name: _compute_subscale(items, positions)
        for name, positions in BRIEF_COPE_SUBSCALE_POSITIONS.items()
    }
    return BriefCopeResult(
        total=total,
        severity="continuous",
        subscales=subscales,
        items=items,
    )


__all__ = [
    "BRIEF_COPE_SUBSCALES",
    "BRIEF_COPE_SUBSCALE_POSITIONS",
    "INSTRUMENT_VERSION",
    "ITEM_COUNT",
    "ITEM_MAX",
    "ITEM_MIN",
    "BriefCopeResult",
    "InvalidResponseError",
    "Severity",
    "score_brief_cope",
]

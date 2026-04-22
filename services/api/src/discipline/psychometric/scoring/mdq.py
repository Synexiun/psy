"""MDQ — Mood Disorder Questionnaire (Hirschfeld 2000).

The MDQ is a 13-item yes/no screener for lifetime bipolar-spectrum
symptoms, paired with two gating questions that together distinguish
a screen-positive ("refer for full clinical evaluation") from a
below-threshold result.  It is NOT a diagnostic instrument — a positive
MDQ identifies patients who warrant a structured interview (SCID,
MINI), not a bipolar diagnosis.

Instrument structure (Hirschfeld 2000, "Has there ever been a period
of time when..."):

**Part 1 — 13 binary symptom items (0 = no, 1 = yes)**:
 1. Felt so good or hyper that other people thought you were not
    your normal self, or you were so hyper you got into trouble?
 2. Were so irritable that you shouted at people or started fights?
 3. Felt much more self-confident than usual?
 4. Got much less sleep than usual and found you didn't miss it?
 5. Were much more talkative or spoke much faster than usual?
 6. Thoughts raced through your head or you couldn't slow your mind?
 7. Were so easily distracted by things around you that you had
    trouble concentrating or staying on track?
 8. Had much more energy than usual?
 9. Were much more active or did many more things than usual?
10. Were much more social or outgoing than usual?
11. Were much more interested in sex than usual?
12. Did things that were unusual for you or others thought were
    excessive, foolish, or risky?
13. Spending money got you or your family into trouble?

**Part 2 — Concurrent occurrence (yes/no)**:
 "If you checked YES to more than one, have several of these ever
  happened during the same period of time?"

**Part 3 — Functional impairment (4-point ordinal)**:
 "How much of a problem did any of these cause you — like being
  unable to work; having family, money, or legal troubles; getting
  into arguments or fights?"
 - no problem
 - minor problem
 - moderate problem
 - serious problem

Positive-screen gate (Hirschfeld 2000):
A positive MDQ screen requires ALL THREE:
 1. ≥ 7 of 13 Part 1 items endorsed.
 2. Part 2 = yes (symptoms co-occurred in the same period).
 3. Part 3 in {moderate, serious} (functional impairment).

Failing any single gate flips the result to negative_screen, even
with high item counts.  A patient with 13/13 items positive but no
impairment is still negative — Hirschfeld's validation study
(sensitivity 0.73, specificity 0.90 in a psychiatric sample) relies
on all three gates together; dropping any one inflates false
positives well above the published specificity.

Safety routing:
MDQ has **no safety item** (no suicidality probe, no PHQ-9-style
item 9, no C-SSRS-equivalent).  ``requires_t3`` is never set by
this scorer.  A positive MDQ result is a referral signal, not a
crisis signal.  A clinician working up a newly-positive MDQ should
still co-administer a C-SSRS or PHQ-9 to rule out acute suicidality,
but that's a separate instrument submission and a separate record.

Relationship to PHQ-9:
MDQ and PHQ-9 address orthogonal axes: PHQ-9 probes current
depressive-episode severity; MDQ probes lifetime hypomanic/manic
symptoms.  A patient with PHQ-9 severe AND MDQ positive is
screening positive for bipolar depression rather than unipolar
depression — the treatment implications differ (antidepressant
monotherapy risk, mood-stabilizer indication).  The two scores are
independent records; the scorer here does not attempt a
combined-screen rollup.

Bool rejection note:
Python's ``bool`` subclasses ``int`` so ``isinstance(True, int)`` is
True.  Part 1 items are 0/1 which overlaps bool's True/False — and
unlike most of the psychometric package, the bool→int conversion
here is *semantically correct* (True is "yes" is 1).  However, we
still reject bools in Part 1 to keep the wire format uniform with
the rest of the package (every scorer has the same no-bool rule).
Part 2 is a separate ``concurrent_symptoms: bool`` function argument
where bool is intentional and required.

References:
- Hirschfeld RM, Williams JB, Spitzer RL, Calabrese JR, Flynn L,
  Keck PE Jr, Lewis L, McElroy SL, Post RM, Rapport DJ, Russell JM,
  Sachs GS, Zajecka J (2000).  *Development and validation of a
  screening instrument for bipolar spectrum disorder: the Mood
  Disorder Questionnaire.*  American Journal of Psychiatry
  157(11):1873-5.
- Hirschfeld RM, Holzer C, Calabrese JR, et al. (2003).  *Validity
  of the Mood Disorder Questionnaire: a general population study.*
  American Journal of Psychiatry 160(1):178-80.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

INSTRUMENT_VERSION = "mdq-1.0.0"
ITEM_COUNT = 13
ITEM_MIN = 0
ITEM_MAX = 1

# Published gate per Hirschfeld 2000 §Results: "a cutpoint of 7 or more
# positive items on section 1, plus a response of 'yes' to question 2,
# plus an answer of 'moderate' or 'serious' to question 3, produced an
# optimal sensitivity/specificity balance."  Constants are 1-indexed
# thresholds (≥ 7 means ``positive_count >= MDQ_POSITIVE_ITEM_THRESHOLD``).
MDQ_POSITIVE_ITEM_THRESHOLD = 7

# The 4-point Hirschfeld impairment scale.  Ordered least-to-most severe
# so a future ordinal comparison (rather than set membership) stays
# readable.  The scorer uses set membership against
# ``MDQ_POSITIVE_IMPAIRMENT_LEVELS`` since the published gate is
# categorical ("moderate or serious"), not an ordinal cutoff.
ImpairmentLevel = Literal["none", "minor", "moderate", "serious"]

MDQ_IMPAIRMENT_LEVELS: frozenset[str] = frozenset(
    {"none", "minor", "moderate", "serious"}
)

# Only these two levels satisfy gate 3.  Pinned as a frozenset so the
# validation check is a single ``in`` membership test rather than an
# ``or`` chain that a refactor could accidentally split.
MDQ_POSITIVE_IMPAIRMENT_LEVELS: frozenset[str] = frozenset(
    {"moderate", "serious"}
)


Screen = Literal["positive_screen", "negative_screen"]


class InvalidResponseError(ValueError):
    """Raised on item-count, item-range, item-type, or gate-field
    violations."""


@dataclass(frozen=True)
class MdqResult:
    """Typed MDQ output.

    Fields:
    - ``positive_count``: 0-13, the number of Part 1 items endorsed
      ``yes`` (= 1).  This is the field to store as the FHIR
      Observation's ``valueInteger`` — it is a well-defined integer
      regardless of whether the overall screen was positive.
    - ``concurrent_symptoms``: Part 2 answer, preserved verbatim so a
      clinician reviewing the record can re-derive the positive-screen
      decision without trusting the ``positive_screen`` aggregate.
    - ``functional_impairment``: Part 3 answer, same rationale.
    - ``positive_screen``: True iff all three gates passed.  Flipping
      this alone (e.g. if a reviewer overrides one of the gates) is
      NOT supported — the result is immutable; re-score to change.
    - ``items``: verbatim Part 1 tuple, pinned for auditability.

    Safety posture: ``requires_t3`` is deliberately absent from this
    dataclass.  Downstream routing code that asks "should this fire
    T3?" for an MDQ record must answer False without consulting this
    result — which is what the router does.
    """

    positive_count: int
    concurrent_symptoms: bool
    functional_impairment: ImpairmentLevel
    positive_screen: bool
    items: tuple[int, ...]
    instrument_version: str = INSTRUMENT_VERSION


def _validate_item(index_1: int, value: object) -> int:
    """Validate a single Part 1 yes/no item and return the int value.

    ``index_1`` is the 1-indexed item number (1-13) so error messages
    name the item a clinician would recognize from the instrument
    document.
    """
    # Reject bool explicitly — see module docstring.  Uniform with the
    # rest of the psychometric package (no scorer accepts True/False
    # for an item response).
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidResponseError(
            f"MDQ item {index_1} must be int, got {value!r}"
        )
    if value < ITEM_MIN or value > ITEM_MAX:
        raise InvalidResponseError(
            f"MDQ item {index_1} out of range "
            f"[{ITEM_MIN}, {ITEM_MAX}]: {value}"
        )
    return value


def _validate_concurrent(value: object) -> bool:
    """Part 2 ``concurrent_symptoms`` flag must be strictly bool.

    A non-bool here is a wire-format bug — Part 2 is yes/no by
    instrument definition, and ``None`` / missing is not a valid
    published response.  Refusing silently-coerced int values (0/1)
    keeps the field contract crisp: the caller must have asked the
    patient and received yes or no, not "left blank".
    """
    if not isinstance(value, bool):
        raise InvalidResponseError(
            f"MDQ concurrent_symptoms must be bool, got {value!r}"
        )
    return value


def _validate_impairment(value: object) -> ImpairmentLevel:
    """Part 3 ``functional_impairment`` must be one of the four published
    categorical labels."""
    if not isinstance(value, str):
        raise InvalidResponseError(
            f"MDQ functional_impairment must be str, got {value!r}"
        )
    if value not in MDQ_IMPAIRMENT_LEVELS:
        raise InvalidResponseError(
            f"MDQ functional_impairment must be one of "
            f"{sorted(MDQ_IMPAIRMENT_LEVELS)}, got {value!r}"
        )
    # The Literal narrowing is safe because the set membership check
    # above is exhaustive over the Literal's member strings.
    return value  # type: ignore[return-value]


def score_mdq(
    raw_items: Sequence[int],
    *,
    concurrent_symptoms: bool,
    functional_impairment: ImpairmentLevel,
) -> MdqResult:
    """Score an MDQ response set and apply the three-gate positive
    screen per Hirschfeld 2000.

    Inputs:
    - ``raw_items``: 13 Part 1 items, each 0 (no) or 1 (yes).
    - ``concurrent_symptoms``: Part 2 answer as bool.
    - ``functional_impairment``: Part 3 answer as one of
      ``none`` / ``minor`` / ``moderate`` / ``serious``.

    Raises :class:`InvalidResponseError` on:
    - Wrong number of Part 1 items.
    - A non-int / bool Part 1 item value.
    - A Part 1 item outside ``[0, 1]``.
    - A non-bool ``concurrent_symptoms``.
    - A ``functional_impairment`` outside the four-label vocabulary.

    Partial scoring is unsupported — all three parts must be present.
    A scorer that accepted missing Part 2 or Part 3 would silently
    produce ``negative_screen`` regardless of the Part 1 item count,
    because the gate conjunction would short-circuit on the missing
    part — a caller who forgot to forward Part 2/3 would get a
    misleadingly-negative result.  Explicit validation forces the
    bug to surface at the submit boundary.
    """
    if len(raw_items) != ITEM_COUNT:
        raise InvalidResponseError(
            f"MDQ requires exactly {ITEM_COUNT} Part 1 items, got "
            f"{len(raw_items)}"
        )
    items = tuple(
        _validate_item(index_1=i + 1, value=v)
        for i, v in enumerate(raw_items)
    )
    concurrent = _validate_concurrent(concurrent_symptoms)
    impairment = _validate_impairment(functional_impairment)
    positive_count = sum(items)

    # Three-gate conjunction per Hirschfeld 2000.  All three must hold;
    # a refactor that accidentally changes ``and`` to ``or`` here would
    # inflate positive screens dramatically — guard at the test layer
    # with a vignette per gate.
    positive_screen = (
        positive_count >= MDQ_POSITIVE_ITEM_THRESHOLD
        and concurrent
        and impairment in MDQ_POSITIVE_IMPAIRMENT_LEVELS
    )

    return MdqResult(
        positive_count=positive_count,
        concurrent_symptoms=concurrent,
        functional_impairment=impairment,
        positive_screen=positive_screen,
        items=items,
    )


__all__ = [
    "INSTRUMENT_VERSION",
    "ITEM_COUNT",
    "ITEM_MAX",
    "ITEM_MIN",
    "MDQ_IMPAIRMENT_LEVELS",
    "MDQ_POSITIVE_IMPAIRMENT_LEVELS",
    "MDQ_POSITIVE_ITEM_THRESHOLD",
    "ImpairmentLevel",
    "InvalidResponseError",
    "MdqResult",
    "Screen",
    "score_mdq",
]

"""MDQ scoring tests — Hirschfeld 2000.

Two load-bearing correctness properties for the 13-item MDQ:

1. **Three-gate positive-screen conjunction.**  Hirschfeld 2000's
   validated cutoff requires ALL THREE of:
   - ≥ 7 of 13 Part 1 items endorsed,
   - Part 2 (concurrent_symptoms) = yes, and
   - Part 3 (functional_impairment) ∈ {moderate, serious}.
   A refactor that accepted any single gate, or an ``or`` chain instead
   of an ``and`` chain, would inflate positive screens dramatically and
   break the published sensitivity/specificity balance (Hirschfeld 2000
   reports 0.73/0.90).  The tests pin each gate individually plus the
   conjunction.
2. **Part 3 only gates on moderate-or-serious.**  The four-label
   impairment scale (none/minor/moderate/serious) must pass two
   specific labels and fail the other two.  A fence-post bug here would
   either over-fire (moderate-minor slippage) or under-fire.

Coverage strategy:
- Pin the ≥ 7 item threshold both just-below and at-cutoff.
- Pin the Part 2 gate with otherwise-perfect gates.
- Pin every Part 3 label with otherwise-perfect gates.
- Exhaustively pin that Part 1 items 1-13 accept {0, 1} and reject
  everything else.
- Bool rejection on items (uniform with the rest of the package).
- Bool *required* on concurrent_symptoms (the opposite rule — see
  module docstring).
- Categorical vocabulary enforced on functional_impairment.
- Clinical vignettes a clinician would recognize.
"""

from __future__ import annotations

import pytest

from discipline.psychometric.scoring.mdq import (
    INSTRUMENT_VERSION,
    ITEM_COUNT,
    ITEM_MAX,
    ITEM_MIN,
    MDQ_IMPAIRMENT_LEVELS,
    MDQ_POSITIVE_IMPAIRMENT_LEVELS,
    MDQ_POSITIVE_ITEM_THRESHOLD,
    ImpairmentLevel,
    InvalidResponseError,
    MdqResult,
    score_mdq,
)


def _items(positive_count: int) -> list[int]:
    """Build a 13-item Part 1 list with the first ``positive_count``
    items set to 1 (yes) and the rest 0 (no).

    Order doesn't matter for the positive-screen gate — the scorer sums
    before comparing — but keeping the helper explicit means a reader
    sees "six positives" and the test intent is obvious.
    """
    if positive_count < 0 or positive_count > ITEM_COUNT:
        raise ValueError(
            f"positive_count must be in [0, {ITEM_COUNT}], got {positive_count}"
        )
    return [1] * positive_count + [0] * (ITEM_COUNT - positive_count)


def _score(
    positive_count: int,
    *,
    concurrent: bool = True,
    impairment: ImpairmentLevel = "serious",
) -> MdqResult:
    """Helper: score with conservative defaults on Part 2 and Part 3.

    Defaults to ``concurrent=True`` and ``impairment='serious'`` so a
    test focused on the Part 1 gate doesn't accidentally fail on Part
    2/3 — callers override either when that's the axis under test.
    """
    return score_mdq(
        _items(positive_count),
        concurrent_symptoms=concurrent,
        functional_impairment=impairment,
    )


# =============================================================================
# Constants — pinned to Hirschfeld 2000
# =============================================================================


class TestConstants:
    def test_item_count_is_thirteen(self) -> None:
        """MDQ Part 1 is exactly 13 binary items per Hirschfeld 2000.
        The panel is instrument-canonical; a refactor must not reshape it."""
        assert ITEM_COUNT == 13

    def test_item_range_is_zero_to_one(self) -> None:
        """Each Part 1 item is yes/no — encoded 0/1 on the wire."""
        assert ITEM_MIN == 0
        assert ITEM_MAX == 1

    def test_positive_item_threshold_is_seven(self) -> None:
        """Hirschfeld 2000 §Results: '≥ 7 positive items' is the first
        of three gates.  Changing this constant is a clinical change."""
        assert MDQ_POSITIVE_ITEM_THRESHOLD == 7

    def test_impairment_levels_are_the_four_published(self) -> None:
        """Four-point Hirschfeld impairment scale.  Adding or removing
        a label would break both the scorer gate and the wire format."""
        assert frozenset(
            {"none", "minor", "moderate", "serious"}
        ) == MDQ_IMPAIRMENT_LEVELS

    def test_positive_impairment_levels_are_moderate_serious(self) -> None:
        """Only moderate and serious satisfy the Part 3 gate.
        Demoting minor into this set would over-fire the screen against
        the published specificity of 0.90."""
        assert frozenset(
            {"moderate", "serious"}
        ) == MDQ_POSITIVE_IMPAIRMENT_LEVELS

    def test_positive_impairment_is_subset_of_all_levels(self) -> None:
        """Structural invariant — the positive set must live inside the
        overall vocabulary.  A typo in either constant would surface
        here as the subset check failing."""
        assert MDQ_POSITIVE_IMPAIRMENT_LEVELS <= MDQ_IMPAIRMENT_LEVELS

    def test_instrument_version_stable(self) -> None:
        assert INSTRUMENT_VERSION == "mdq-1.0.0"


# =============================================================================
# Gate 1 — Part 1 item-count threshold (≥ 7 positives)
# =============================================================================


class TestPart1ItemCountGate:
    def test_six_positives_below_threshold_negative(self) -> None:
        """Six positives — one below the published threshold.  Even with
        concurrent=True and serious impairment, the screen must stay
        negative.  A refactor that used ``>`` instead of ``>=`` would
        flip at seven; a refactor that used ``> 5`` instead of ``>= 7``
        would flip here."""
        r = _score(6)
        assert r.positive_count == 6
        assert r.positive_screen is False

    def test_seven_positives_at_threshold_positive(self) -> None:
        """At-cutoff inclusive: seven positives + concurrent + serious
        impairment → positive_screen.  This is the minimum-positive
        case that crosses the gate."""
        r = _score(7)
        assert r.positive_count == 7
        assert r.positive_screen is True

    def test_thirteen_positives_top_of_scale_positive(self) -> None:
        """Maximum Part 1 score with the other two gates satisfied."""
        r = _score(13)
        assert r.positive_count == 13
        assert r.positive_screen is True

    def test_zero_positives_negative(self) -> None:
        """All-zero Part 1 can never fire regardless of Part 2/3."""
        r = _score(0)
        assert r.positive_count == 0
        assert r.positive_screen is False


# =============================================================================
# Gate 2 — Part 2 concurrent_symptoms gate
# =============================================================================


class TestPart2ConcurrentGate:
    def test_concurrent_false_blocks_positive_screen(self) -> None:
        """Even with 13/13 Part 1 items and serious impairment, a False
        Part 2 answer keeps the screen negative.  This is the exact
        clinical case called out in the scorer module docstring."""
        r = score_mdq(
            _items(13),
            concurrent_symptoms=False,
            functional_impairment="serious",
        )
        assert r.positive_count == 13
        assert r.concurrent_symptoms is False
        assert r.positive_screen is False

    def test_concurrent_true_required_for_positive_screen(self) -> None:
        """Same item count + same impairment, Part 2 flipped to True →
        positive.  Pairs with the False case above to pin the gate."""
        r = score_mdq(
            _items(7),
            concurrent_symptoms=True,
            functional_impairment="serious",
        )
        assert r.concurrent_symptoms is True
        assert r.positive_screen is True


# =============================================================================
# Gate 3 — Part 3 functional_impairment gate
# =============================================================================


class TestPart3ImpairmentGate:
    def test_none_impairment_blocks(self) -> None:
        r = score_mdq(
            _items(13),
            concurrent_symptoms=True,
            functional_impairment="none",
        )
        assert r.functional_impairment == "none"
        assert r.positive_screen is False

    def test_minor_impairment_blocks(self) -> None:
        """Minor impairment is the load-bearing 'near-miss' case.  The
        patient endorses severe symptoms but minor real-world impact —
        per Hirschfeld 2000 that is NOT a positive screen.  A refactor
        that treated this boundary as >= minor (rather than membership
        in {moderate, serious}) would flip this assertion."""
        r = score_mdq(
            _items(13),
            concurrent_symptoms=True,
            functional_impairment="minor",
        )
        assert r.functional_impairment == "minor"
        assert r.positive_screen is False

    def test_moderate_impairment_passes(self) -> None:
        r = score_mdq(
            _items(7),
            concurrent_symptoms=True,
            functional_impairment="moderate",
        )
        assert r.functional_impairment == "moderate"
        assert r.positive_screen is True

    def test_serious_impairment_passes(self) -> None:
        r = score_mdq(
            _items(7),
            concurrent_symptoms=True,
            functional_impairment="serious",
        )
        assert r.functional_impairment == "serious"
        assert r.positive_screen is True


# =============================================================================
# Gate conjunction — every combinatorial case
# =============================================================================


class TestGateConjunction:
    """Exhaustively pin the three-gate AND.

    The failure mode this protects against is a refactor that replaces
    the ``and`` chain with ``or`` — an instrument with ≥ 7 items would
    start firing regardless of Part 2 or Part 3, dramatically inflating
    positive screens against the published specificity.  Each row below
    has exactly one gate failing and must stay negative."""

    def test_items_pass_concurrent_fail_impairment_pass(self) -> None:
        r = score_mdq(
            _items(7),
            concurrent_symptoms=False,
            functional_impairment="serious",
        )
        assert r.positive_screen is False

    def test_items_pass_concurrent_pass_impairment_fail(self) -> None:
        r = score_mdq(
            _items(7),
            concurrent_symptoms=True,
            functional_impairment="minor",
        )
        assert r.positive_screen is False

    def test_items_fail_concurrent_pass_impairment_pass(self) -> None:
        r = score_mdq(
            _items(6),
            concurrent_symptoms=True,
            functional_impairment="serious",
        )
        assert r.positive_screen is False

    def test_all_three_gates_pass_positive(self) -> None:
        """The only combination that produces positive_screen is all
        three gates passing simultaneously."""
        r = score_mdq(
            _items(7),
            concurrent_symptoms=True,
            functional_impairment="moderate",
        )
        assert r.positive_screen is True

    def test_all_three_gates_fail_negative(self) -> None:
        """Zero positives + Part 2 False + minor impairment — the
        opposite of a positive screen on every gate."""
        r = score_mdq(
            _items(0),
            concurrent_symptoms=False,
            functional_impairment="none",
        )
        assert r.positive_screen is False


# =============================================================================
# Part 1 item validation — range + type
# =============================================================================


class TestPart1ItemValidation:
    @pytest.mark.parametrize("item_idx", list(range(1, 14)))
    def test_every_item_accepts_zero_and_one(self, item_idx: int) -> None:
        """Each Part 1 item must accept both 0 and 1.  A regression
        that narrowed any item's domain would silently drop valid
        responses for just that item — hard to notice without a
        per-item assertion."""
        for value in (0, 1):
            items = [0] * ITEM_COUNT
            items[item_idx - 1] = value
            r = score_mdq(
                items,
                concurrent_symptoms=False,
                functional_impairment="none",
            )
            assert r.items[item_idx - 1] == value

    @pytest.mark.parametrize("value", [-1, 2, 3, 10])
    def test_out_of_range_rejected(self, value: int) -> None:
        items = [0] * ITEM_COUNT
        items[0] = value
        with pytest.raises(InvalidResponseError, match="item 1"):
            score_mdq(
                items,
                concurrent_symptoms=False,
                functional_impairment="none",
            )

    def test_bool_true_rejected_on_item(self) -> None:
        """True happens to correspond to the valid value 1 (yes), but
        the wire-format rule across the psychometric package is 'no
        bools in item lists'.  The uniform rule is worth a tiny amount
        of redundancy because a caller sending bools on *other*
        instruments (PHQ-9, AUDIT) would land on silently-wrong scores."""
        items: list[int] = [0] * ITEM_COUNT
        items[0] = True  # type: ignore[list-item]
        with pytest.raises(InvalidResponseError, match="item 1"):
            score_mdq(
                items,
                concurrent_symptoms=False,
                functional_impairment="none",
            )

    def test_bool_false_rejected_on_item(self) -> None:
        items: list[int] = [0] * ITEM_COUNT
        items[0] = False  # type: ignore[list-item]
        with pytest.raises(InvalidResponseError, match="item 1"):
            score_mdq(
                items,
                concurrent_symptoms=False,
                functional_impairment="none",
            )

    def test_string_rejected(self) -> None:
        items: list[int] = [0] * ITEM_COUNT
        items[0] = "1"  # type: ignore[list-item]
        with pytest.raises(InvalidResponseError, match="item 1"):
            score_mdq(
                items,
                concurrent_symptoms=False,
                functional_impairment="none",
            )

    def test_float_rejected(self) -> None:
        """1.0 would coerce but 0.5 wouldn't — the uniform rule is to
        reject every non-int, not to accept exact-integer floats."""
        items: list[int] = [0] * ITEM_COUNT
        items[0] = 1.0  # type: ignore[list-item]
        with pytest.raises(InvalidResponseError, match="item 1"):
            score_mdq(
                items,
                concurrent_symptoms=False,
                functional_impairment="none",
            )

    def test_none_rejected(self) -> None:
        items: list[int] = [0] * ITEM_COUNT
        items[0] = None  # type: ignore[list-item]
        with pytest.raises(InvalidResponseError, match="item 1"):
            score_mdq(
                items,
                concurrent_symptoms=False,
                functional_impairment="none",
            )

    def test_wrong_item_count_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 13"):
            score_mdq(
                [0] * 12,
                concurrent_symptoms=False,
                functional_impairment="none",
            )

    def test_empty_list_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 13"):
            score_mdq(
                [],
                concurrent_symptoms=False,
                functional_impairment="none",
            )


# =============================================================================
# Part 2 validation — strict bool required
# =============================================================================


class TestPart2Validation:
    """Part 2 is a yes/no by instrument design.  Unlike items, bool is
    *required* here — silent coercion of 0/1 would let a caller who
    forgot to ask the patient slip a stray integer through."""

    def test_int_zero_rejected(self) -> None:
        """0 is not False — the scorer rejects silent coercion so a
        missing Part 2 surface as a 422 at the wire boundary."""
        with pytest.raises(InvalidResponseError, match="concurrent_symptoms"):
            score_mdq(
                _items(7),
                concurrent_symptoms=0,  # type: ignore[arg-type]
                functional_impairment="serious",
            )

    def test_int_one_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="concurrent_symptoms"):
            score_mdq(
                _items(7),
                concurrent_symptoms=1,  # type: ignore[arg-type]
                functional_impairment="serious",
            )

    def test_string_yes_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="concurrent_symptoms"):
            score_mdq(
                _items(7),
                concurrent_symptoms="yes",  # type: ignore[arg-type]
                functional_impairment="serious",
            )

    def test_none_rejected(self) -> None:
        """None is not False — a caller who left Part 2 unanswered
        must fail loudly, not silently score as negative."""
        with pytest.raises(InvalidResponseError, match="concurrent_symptoms"):
            score_mdq(
                _items(7),
                concurrent_symptoms=None,  # type: ignore[arg-type]
                functional_impairment="serious",
            )


# =============================================================================
# Part 3 validation — categorical vocabulary
# =============================================================================


class TestPart3Validation:
    def test_unknown_label_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="functional_impairment"):
            score_mdq(
                _items(7),
                concurrent_symptoms=True,
                functional_impairment="severe",  # type: ignore[arg-type]
            )

    def test_empty_string_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="functional_impairment"):
            score_mdq(
                _items(7),
                concurrent_symptoms=True,
                functional_impairment="",  # type: ignore[arg-type]
            )

    def test_non_str_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="functional_impairment"):
            score_mdq(
                _items(7),
                concurrent_symptoms=True,
                functional_impairment=0,  # type: ignore[arg-type]
            )

    def test_error_message_lists_valid_labels(self) -> None:
        """The error for a bad label must enumerate the valid set so a
        client developer sees the fix without reading the docstring."""
        with pytest.raises(InvalidResponseError) as exc_info:
            score_mdq(
                _items(7),
                concurrent_symptoms=True,
                functional_impairment="bad",  # type: ignore[arg-type]
            )
        msg = str(exc_info.value)
        for label in ("none", "minor", "moderate", "serious"):
            assert label in msg


# =============================================================================
# Result shape and immutability
# =============================================================================


class TestResultShape:
    def test_items_echoed_verbatim(self) -> None:
        """The result carries the caller's Part 1 items unchanged so
        an auditor can re-derive the positive_count without trusting
        the stored aggregate."""
        items = [0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0]
        r = score_mdq(
            items,
            concurrent_symptoms=True,
            functional_impairment="moderate",
        )
        assert r.items == tuple(items)

    def test_items_stored_as_tuple(self) -> None:
        """Tuple keeps the result hashable and immutable.  A list
        field would let a caller mutate stored items after the fact."""
        r = _score(7)
        assert isinstance(r.items, tuple)

    def test_result_is_frozen(self) -> None:
        r = _score(7)
        with pytest.raises(Exception):
            r.positive_count = 99  # type: ignore[misc]

    def test_positive_count_matches_sum(self) -> None:
        """``positive_count`` must equal the literal sum of Part 1 —
        a subtle off-by-one in the aggregation (e.g. counting unique
        positions instead of values) would diverge here."""
        r = _score(9)
        assert r.positive_count == sum(r.items)

    def test_instrument_version_in_result(self) -> None:
        r = _score(7)
        assert r.instrument_version == "mdq-1.0.0"

    def test_fields_preserved_for_audit(self) -> None:
        """The stored Part 2 + Part 3 inputs round-trip into the result
        so a clinician reading the record can re-derive the positive
        screen without consulting a second source."""
        r = score_mdq(
            _items(8),
            concurrent_symptoms=True,
            functional_impairment="moderate",
        )
        assert r.concurrent_symptoms is True
        assert r.functional_impairment == "moderate"


# =============================================================================
# Clinical vignettes — a clinician should recognize each of these
# =============================================================================


class TestClinicalVignettes:
    def test_classic_hypomanic_episode_positive(self) -> None:
        """High-confidence hypomanic presentation: elevated mood,
        decreased sleep, racing thoughts, more talkative, more social,
        risk-taking, spending.  Concurrent during a bounded period with
        moderate real-world impact.  The Hirschfeld 2000 use case."""
        # Items 1, 3, 4, 5, 6, 8, 9, 10, 12, 13 endorsed → 10 positives.
        items = [1, 0, 1, 1, 1, 1, 0, 1, 1, 1, 0, 1, 1]
        r = score_mdq(
            items,
            concurrent_symptoms=True,
            functional_impairment="moderate",
        )
        assert r.positive_count == 10
        assert r.positive_screen is True

    def test_irritability_only_no_full_criteria_negative(self) -> None:
        """Patient endorses irritability and conflict symptoms but
        only a handful of other items, and no functional impairment.
        Classic 'trait irritability' that must not screen positive as
        bipolar spectrum."""
        # Items 2 (irritable), 7 (distractible), 12 (risky) → 3 positives.
        items = [0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0]
        r = score_mdq(
            items,
            concurrent_symptoms=True,
            functional_impairment="minor",
        )
        assert r.positive_count == 3
        assert r.positive_screen is False

    def test_high_items_but_impairment_none_negative(self) -> None:
        """Hirschfeld 2000 worked example: a patient with lifetime
        hypomanic-like episodes that never caused functional problems
        is NOT a positive screen.  The gate conjunction prevents this
        profile from flipping positive even with 11/13 items."""
        items = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0]
        r = score_mdq(
            items,
            concurrent_symptoms=True,
            functional_impairment="none",
        )
        assert r.positive_count == 11
        assert r.positive_screen is False

    def test_non_concurrent_symptoms_negative(self) -> None:
        """Symptoms endorsed across the patient's life but never
        during the same period — closer to a dysthymic or mixed
        presentation than a bipolar episode.  Part 2 correctly gates
        this out even with high items and serious impairment."""
        items = [1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0]
        r = score_mdq(
            items,
            concurrent_symptoms=False,
            functional_impairment="serious",
        )
        assert r.positive_count == 9
        assert r.positive_screen is False


# =============================================================================
# Safety posture — no T3 routing from this instrument
# =============================================================================


class TestNoSafetyRouting:
    def test_result_has_no_requires_t3_field(self) -> None:
        """MDQ has no safety item (no suicidality probe).  The result
        dataclass deliberately omits ``requires_t3`` so a future
        dispatcher can't accidentally wire an MDQ result into the
        T3 router — the absence is the guard."""
        r = _score(13)
        assert not hasattr(r, "requires_t3")

    def test_positive_screen_is_not_crisis_signal(self) -> None:
        """A positive MDQ is a referral signal for a structured
        bipolar interview, NOT a crisis signal.  The router layer
        must never set requires_t3=True off MDQ; the scorer gives it
        nothing to key on."""
        r = _score(13)
        # Two complementary checks: the field doesn't exist, AND the
        # result as a whole contains no hint of T3 semantics.
        assert not hasattr(r, "requires_t3")
        assert not hasattr(r, "t3_reason")

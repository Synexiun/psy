"""OCI-R scoring tests — Foa 2002 / Abramowitz 2006.

Three load-bearing correctness properties for the 18-item OCI-R:

1. **Cutoff is ``>= 21``, not ``> 21``.**  Foa 2002 §Results selected
   21 as the operating point (sensitivity 0.74, specificity 0.75 in
   the clinical sample).  Boundary tests pin 20/21 and 21/22
   explicitly.  A fence-post regression here would either miss or
   over-fire at the clinical decision point.
2. **Subscale boundaries map DISTRIBUTED (interleaved) items, not
   contiguous ranges.**  Unlike PCL-5 where cluster B = items 1-5
   contiguously, OCI-R's six subscales use interleaved 1-indexed
   triples:
     - hoarding = (1, 7, 13)
     - checking = (2, 8, 14)
     - ordering = (3, 9, 15)
     - neutralizing = (4, 10, 16)
     - washing = (5, 11, 17)
     - obsessing = (6, 12, 18)
   Each subscale test endorses only those three positions and
   verifies the other five subscales stay at zero.  A refactor that
   rotated or shifted the subscale index tuples (e.g. swapped
   hoarding and checking rows) would break the clinical signal
   silently.
3. **Exactly 18 items, each 0-4 Likert.**  Mismatched count or
   out-of-range value is a validation error, not a silent partial
   score.

Coverage strategy:
- Pin the 20/21 cutoff boundary.
- Pin all six subscales with single-subscale endorsement tests
  isolating the three distributed item positions.
- Invariant: six subscale sums equal the total.
- Item-count and item-range validation.
- Bool rejection.
- Clinical vignettes — washing-dominant (contamination), hoarding-
  dominant, obsessing-dominant presentations.
- No safety routing.
"""

from __future__ import annotations

import pytest

from discipline.psychometric.scoring.ocir import (
    INSTRUMENT_VERSION,
    ITEM_COUNT,
    ITEM_MAX,
    ITEM_MIN,
    OCIR_POSITIVE_CUTOFF,
    OCIR_SUBSCALES,
    InvalidResponseError,
    score_ocir,
)


def _zeros() -> list[int]:
    return [0] * ITEM_COUNT


def _endorse_at(positions_1: list[int], level: int = 4) -> list[int]:
    """Build an 18-item list with the given 1-indexed positions set to
    ``level`` and the rest zeroed.

    Used to isolate subscale-specific endorsements so subscale-boundary
    tests don't accidentally leak responses across the interleaved
    subscale positions.
    """
    if not (ITEM_MIN <= level <= ITEM_MAX):
        raise ValueError(f"level must be in [{ITEM_MIN}, {ITEM_MAX}]")
    items = _zeros()
    for pos in positions_1:
        items[pos - 1] = level
    return items


class TestConstants:
    """Pin published constants so a drift from Foa 2002 is caught."""

    def test_item_count_is_eighteen(self) -> None:
        assert ITEM_COUNT == 18

    def test_item_range_is_zero_to_four(self) -> None:
        assert ITEM_MIN == 0
        assert ITEM_MAX == 4

    def test_positive_cutoff_is_twenty_one(self) -> None:
        """Foa 2002 §Results — cutpoint 21 balances sens/spec in the
        clinical sample.  Any change is a clinical change."""
        assert OCIR_POSITIVE_CUTOFF == 21

    def test_subscales_match_foa_2002(self) -> None:
        """Six 3-item subscales per Foa 2002 Table 1, 1-indexed
        positions.  A refactor that resorted items into contiguous
        blocks or rotated the subscale rows would break the validated
        administration design — pinned verbatim from the paper."""
        assert OCIR_SUBSCALES == {
            "hoarding": (1, 7, 13),
            "checking": (2, 8, 14),
            "ordering": (3, 9, 15),
            "neutralizing": (4, 10, 16),
            "washing": (5, 11, 17),
            "obsessing": (6, 12, 18),
        }

    def test_instrument_version_pinned(self) -> None:
        assert INSTRUMENT_VERSION == "ocir-1.0.0"


class TestTotalCorrectness:
    """Straight 0-72 sum (no reverse-coding)."""

    def test_zero_is_minimum(self) -> None:
        result = score_ocir(_zeros())
        assert result.total == 0

    def test_max_is_seventy_two(self) -> None:
        """18 items × max 4 = 72."""
        result = score_ocir([4] * ITEM_COUNT)
        assert result.total == 72

    def test_mixed_sum(self) -> None:
        """Arbitrary mix — verifies the total is a plain sum."""
        items = [3, 2, 1, 4, 0, 2, 3, 1, 0, 4, 2, 1, 3, 0, 4, 2, 1, 3]
        result = score_ocir(items)
        assert result.total == sum(items)


class TestCutoffBoundary:
    """The ``>= 21`` probable-OCD cutoff — explicit just-below and at-
    cutoff tests so a fence-post regression is caught.
    """

    def test_total_twenty_below_cutoff(self) -> None:
        """Total 20 → negative screen.  A ``>= 20`` bug would flip
        this positive and over-identify patients.  Build with 5
        items at 4 (sum 20)."""
        items = _zeros()
        for i in range(5):
            items[i] = 4
        result = score_ocir(items)
        assert result.total == 20
        assert result.positive_screen is False

    def test_total_twenty_one_at_cutoff(self) -> None:
        """Total 21 → positive screen (the exact Foa 2002 cutoff).
        A ``> 21`` bug would flip this negative and under-identify."""
        items = _zeros()
        for i in range(5):
            items[i] = 4
        items[5] = 1  # 20 + 1 = 21
        result = score_ocir(items)
        assert result.total == 21
        assert result.positive_screen is True

    def test_total_twenty_two_above_cutoff(self) -> None:
        items = _zeros()
        for i in range(5):
            items[i] = 4
        items[5] = 2  # 20 + 2 = 22
        result = score_ocir(items)
        assert result.total == 22
        assert result.positive_screen is True


class TestSubscaleBoundaries:
    """Each subscale must map to its correct DISTRIBUTED (interleaved)
    1-indexed positions.  A refactor that rotated subscale rows or
    shifted an item into a neighboring subscale would silently
    mis-categorize the clinical signal — every subscale test
    endorses exactly three positions and verifies the other five
    subscales stay at zero.
    """

    def test_hoarding_items_one_seven_thirteen(self) -> None:
        """Endorse only items 1, 7, 13 at max → hoarding = 12,
        others = 0.  Pins the positions of the first subscale row."""
        result = score_ocir(_endorse_at([1, 7, 13]))
        assert result.subscale_hoarding == 12  # 3 items × 4
        assert result.subscale_checking == 0
        assert result.subscale_ordering == 0
        assert result.subscale_neutralizing == 0
        assert result.subscale_washing == 0
        assert result.subscale_obsessing == 0

    def test_checking_items_two_eight_fourteen(self) -> None:
        """Endorse only items 2, 8, 14 → checking = 12, others = 0."""
        result = score_ocir(_endorse_at([2, 8, 14]))
        assert result.subscale_hoarding == 0
        assert result.subscale_checking == 12
        assert result.subscale_ordering == 0
        assert result.subscale_neutralizing == 0
        assert result.subscale_washing == 0
        assert result.subscale_obsessing == 0

    def test_ordering_items_three_nine_fifteen(self) -> None:
        """Endorse only items 3, 9, 15 → ordering = 12, others = 0."""
        result = score_ocir(_endorse_at([3, 9, 15]))
        assert result.subscale_hoarding == 0
        assert result.subscale_checking == 0
        assert result.subscale_ordering == 12
        assert result.subscale_neutralizing == 0
        assert result.subscale_washing == 0
        assert result.subscale_obsessing == 0

    def test_neutralizing_items_four_ten_sixteen(self) -> None:
        """Endorse only items 4, 10, 16 → neutralizing = 12, others = 0."""
        result = score_ocir(_endorse_at([4, 10, 16]))
        assert result.subscale_hoarding == 0
        assert result.subscale_checking == 0
        assert result.subscale_ordering == 0
        assert result.subscale_neutralizing == 12
        assert result.subscale_washing == 0
        assert result.subscale_obsessing == 0

    def test_washing_items_five_eleven_seventeen(self) -> None:
        """Endorse only items 5, 11, 17 → washing = 12, others = 0.
        Pinning this is important because 'washing-dominant' drives
        ERP intervention selection — a refactor that mis-routed
        washing items would surface as the wrong clinical
        recommendation, not a crash."""
        result = score_ocir(_endorse_at([5, 11, 17]))
        assert result.subscale_hoarding == 0
        assert result.subscale_checking == 0
        assert result.subscale_ordering == 0
        assert result.subscale_neutralizing == 0
        assert result.subscale_washing == 12
        assert result.subscale_obsessing == 0

    def test_obsessing_items_six_twelve_eighteen(self) -> None:
        """Endorse only items 6, 12, 18 → obsessing = 12, others = 0.
        Pins the last subscale row; item 18 is the final item of
        the instrument."""
        result = score_ocir(_endorse_at([6, 12, 18]))
        assert result.subscale_hoarding == 0
        assert result.subscale_checking == 0
        assert result.subscale_ordering == 0
        assert result.subscale_neutralizing == 0
        assert result.subscale_washing == 0
        assert result.subscale_obsessing == 12

    def test_subscale_sum_equals_total(self) -> None:
        """The six subscales sum to the total.  A refactor that
        double-counted an item (put item 7 in both hoarding and
        checking) or dropped an item (left item 18 out of all
        subscales) would break this invariant."""
        items = [3, 2, 1, 4, 0, 2, 3, 1, 0, 4, 2, 1, 3, 0, 4, 2, 1, 3]
        result = score_ocir(items)
        subscale_sum = (
            result.subscale_hoarding
            + result.subscale_checking
            + result.subscale_ordering
            + result.subscale_neutralizing
            + result.subscale_washing
            + result.subscale_obsessing
        )
        assert subscale_sum == result.total


class TestItemCountValidation:
    """Exactly 18 items required."""

    def test_rejects_seventeen_items(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 18 items"):
            score_ocir([0] * 17)

    def test_rejects_nineteen_items(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 18 items"):
            score_ocir([0] * 19)

    def test_rejects_empty(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 18 items"):
            score_ocir([])


class TestItemRangeValidation:
    """Items must be in [0, 4]."""

    @pytest.mark.parametrize("bad_value", [-1, 5, 10])
    def test_rejects_out_of_range(self, bad_value: int) -> None:
        items = _zeros()
        items[9] = bad_value
        with pytest.raises(InvalidResponseError, match="out of range"):
            score_ocir(items)

    def test_error_names_one_indexed_item(self) -> None:
        """Error messages use 1-indexed item numbers to match the
        OCI-R instrument document."""
        items = _zeros()
        items[12] = 99  # item 13 (index 12) — hoarding position
        with pytest.raises(InvalidResponseError, match="OCI-R item 13"):
            score_ocir(items)

    def test_rejects_string_item(self) -> None:
        items = _zeros()
        items[0] = "4"  # type: ignore[call-overload]
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_ocir(items)

    def test_rejects_float_item(self) -> None:
        items = _zeros()
        items[0] = 4.0  # type: ignore[call-overload]
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_ocir(items)


class TestBoolRejection:
    """Bool items rejected even though True/False map to valid 1/0.
    Rationale: uniform wire contract across the psychometric package
    (same policy as MDQ, PCL-5, PC-PTSD-5, ISI).
    """

    def test_rejects_true_item(self) -> None:
        items = _zeros()
        items[0] = True  # type: ignore[call-overload]
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_ocir(items)

    def test_rejects_false_item(self) -> None:
        items = _zeros()
        items[0] = False  # type: ignore[call-overload]
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_ocir(items)


class TestResultShape:
    """OcirResult carries the fields the router + future subscale
    surfacing layer need."""

    def test_result_is_frozen(self) -> None:
        result = score_ocir(_zeros())
        with pytest.raises(Exception):  # FrozenInstanceError subclass
            result.total = 99  # type: ignore[misc]

    def test_items_are_tuple(self) -> None:
        """Tuple so OcirResult is hashable and the stored repository
        record is immutable."""
        items = _endorse_at([1, 5, 10, 15, 18], level=2)
        result = score_ocir(items)
        assert isinstance(result.items, tuple)
        assert result.items == tuple(items)

    def test_result_echoes_instrument_version(self) -> None:
        result = score_ocir(_zeros())
        assert result.instrument_version == INSTRUMENT_VERSION

    def test_no_requires_t3_field(self) -> None:
        """OCI-R has no safety item.  The result dataclass deliberately
        omits requires_t3 so downstream routing cannot accidentally
        escalate a severe-OCD patient into T3.  Co-administer C-SSRS
        for suicidality differential (OCD has elevated suicidality
        risk but OCI-R items don't probe it)."""
        result = score_ocir([4] * ITEM_COUNT)
        assert not hasattr(result, "requires_t3")


class TestClinicalVignettes:
    """Named patterns a clinician would recognize.  Subscale dominance
    drives intervention selection per Docs/Whitepapers/02_Clinical_
    Evidence_Base.md §compulsive."""

    def test_washing_dominant_presentation(self) -> None:
        """Classic contamination-OCD pattern — washing subscale elevated,
        others modest.  Clinically indicates exposure and response
        prevention (ERP) — the washing-dominant-targeted intervention."""
        # Washing (5, 11, 17) at 4; others mixed lower
        items = [1, 1, 1, 1, 4, 1, 1, 1, 1, 1, 4, 1, 1, 1, 1, 1, 4, 1]
        result = score_ocir(items)
        assert result.subscale_washing == 12
        assert result.subscale_washing > result.subscale_hoarding
        assert result.subscale_washing > result.subscale_checking
        assert result.subscale_washing > result.subscale_ordering
        assert result.subscale_washing > result.subscale_neutralizing
        assert result.subscale_washing > result.subscale_obsessing
        assert result.total >= OCIR_POSITIVE_CUTOFF
        assert result.positive_screen is True

    def test_hoarding_dominant_presentation(self) -> None:
        """Hoarding-dominant pattern — saving/discarding difficulty.
        Clinically indicates CBT-H (cognitive-behavioral therapy
        adapted for hoarding), a different intervention than
        classic ERP."""
        # Hoarding (1, 7, 13) at 4; others mixed lower
        items = [4, 1, 1, 1, 1, 1, 4, 1, 1, 1, 1, 1, 4, 1, 1, 1, 1, 1]
        result = score_ocir(items)
        assert result.subscale_hoarding == 12
        assert result.subscale_hoarding > result.subscale_checking
        assert result.subscale_hoarding > result.subscale_ordering
        assert result.subscale_hoarding > result.subscale_neutralizing
        assert result.subscale_hoarding > result.subscale_washing
        assert result.subscale_hoarding > result.subscale_obsessing

    def test_obsessing_dominant_presentation(self) -> None:
        """Pure-obsessional pattern — intrusive thoughts, thought control
        difficulty.  Clinically indicates cognitive therapy targeting
        thought-action fusion rather than standard ERP."""
        # Obsessing (6, 12, 18) at 4; others mixed lower
        items = [1, 1, 1, 1, 1, 4, 1, 1, 1, 1, 1, 4, 1, 1, 1, 1, 1, 4]
        result = score_ocir(items)
        assert result.subscale_obsessing == 12
        assert result.subscale_obsessing > result.subscale_hoarding
        assert result.subscale_obsessing > result.subscale_checking
        assert result.subscale_obsessing > result.subscale_ordering
        assert result.subscale_obsessing > result.subscale_neutralizing
        assert result.subscale_obsessing > result.subscale_washing

    def test_subthreshold_negative_screen(self) -> None:
        """Symptomatic but below cutoff — legitimate clinical outcome
        that routes to watchful waiting / psychoeducation rather than
        formal ERP."""
        # All items at 1 → total 18, below cutoff 21
        result = score_ocir([1] * ITEM_COUNT)
        assert result.total == 18
        assert result.total < OCIR_POSITIVE_CUTOFF
        assert result.positive_screen is False

    def test_full_symptom_cluster(self) -> None:
        """All 18 items endorsed at 4 → clear positive, max severity
        across every subscale.  Defining case for outcome-tracking
        baseline in severe OCD."""
        result = score_ocir([4] * ITEM_COUNT)
        assert result.total == 72
        assert result.positive_screen is True
        # Every subscale at 12 (3 items × 4)
        assert result.subscale_hoarding == 12
        assert result.subscale_checking == 12
        assert result.subscale_ordering == 12
        assert result.subscale_neutralizing == 12
        assert result.subscale_washing == 12
        assert result.subscale_obsessing == 12


class TestNoSafetyRouting:
    """OCI-R has no direct suicidality item.  Obsessing-subscale items
    (intrusive thoughts, unwanted unpleasant thoughts) superficially
    resemble the "intrusive thoughts" of crisis presentations but do
    NOT probe acute harm.  The scorer must not expose anything the
    router could mistake for a T3 trigger.
    """

    def test_max_total_has_no_safety_field(self) -> None:
        result = score_ocir([4] * ITEM_COUNT)
        assert not hasattr(result, "requires_t3")
        assert not hasattr(result, "t3_reason")
        assert not hasattr(result, "safety_item_positive")
        assert not hasattr(result, "triggering_items")

    def test_obsessing_max_has_no_safety_field(self) -> None:
        """Even when the obsessing subscale is maxed out (the one that
        looks most like 'intrusive thoughts'), the result carries no
        safety-routing fields.  A renderer that tried to key off
        obsessing > threshold to escalate would over-fire and
        desensitize the safety queue."""
        result = score_ocir(_endorse_at([6, 12, 18]))
        assert not hasattr(result, "requires_t3")
        assert not hasattr(result, "t3_reason")

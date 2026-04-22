"""PC-PTSD-5 scoring tests — Prins 2016.

Two load-bearing correctness properties for the 5-item PC-PTSD-5:

1. **Cutoff is ``>= 3``, not ``> 3`` and not ``>= 2``.**  Prins 2016
   selected cutpoint 3 as optimally efficient (sensitivity 0.95,
   specificity 0.85) in the VA primary-care validation sample.  A
   fence-post bug that flipped the comparator would either miss true
   positives (``> 3`` turns a 3-of-5 screen negative) or over-fire
   (``>= 2`` turns the under-cutoff band positive).  The boundary
   tests pin 2/3 and 3/3 explicitly.
2. **Exactly 5 items, each in ``{0, 1}``.**  PC-PTSD-5 is pure binary
   yes/no — a 0-4 Likert-style response or a count > 1 is a
   validation error, not a silent coercion.  Item-range and
   item-count tests pin this.

Coverage strategy:
- Pin positive-count correctness across the full 0-5 range.
- Pin the cutoff boundary both just-below (2) and at-cutoff (3).
- Bool rejection on items (uniform with the rest of the package —
  rationale in scoring/pcptsd5.py module docstring).
- Item-count and item-range rejection.
- Clinical vignettes a clinician would recognize (pure avoider,
  hypervigilant-only, full symptom cluster).
- No safety routing — PC-PTSD-5 has no suicidality item, so
  ``requires_t3`` never appears on the result dataclass (unlike
  Phq9Result / CssrsResult).
"""

from __future__ import annotations

import pytest

from discipline.psychometric.scoring.pcptsd5 import (
    INSTRUMENT_VERSION,
    ITEM_COUNT,
    ITEM_MAX,
    ITEM_MIN,
    PCPTSD5_POSITIVE_CUTOFF,
    InvalidResponseError,
    score_pcptsd5,
)


def _items(positive_count: int) -> list[int]:
    """Build a 5-item list with ``positive_count`` items set to 1.

    Order doesn't matter for the cutoff gate — the scorer sums the
    endorsed items — but the helper makes test intent explicit
    ("three positives" → item list).
    """
    if positive_count < 0 or positive_count > ITEM_COUNT:
        raise ValueError(
            f"positive_count must be in [0, {ITEM_COUNT}], "
            f"got {positive_count}"
        )
    return [1] * positive_count + [0] * (ITEM_COUNT - positive_count)


class TestConstants:
    """Pin published constants so a drift from Prins 2016 is caught."""

    def test_item_count_is_five(self) -> None:
        assert ITEM_COUNT == 5

    def test_item_range_is_binary(self) -> None:
        assert ITEM_MIN == 0
        assert ITEM_MAX == 1

    def test_positive_cutoff_is_three(self) -> None:
        """Prins 2016 §Results — cutpoint 3 is the published operating
        point (sensitivity 0.95, specificity 0.85).  Any change to this
        constant is a clinical change, not an implementation tweak, and
        must cite a replacement paper."""
        assert PCPTSD5_POSITIVE_CUTOFF == 3

    def test_instrument_version_pinned(self) -> None:
        assert INSTRUMENT_VERSION == "pcptsd5-1.0.0"


class TestPositiveCountCorrectness:
    """Every possible 0-5 count sums correctly."""

    @pytest.mark.parametrize("n", [0, 1, 2, 3, 4, 5])
    def test_positive_count_matches_endorsed_items(self, n: int) -> None:
        result = score_pcptsd5(_items(n))
        assert result.positive_count == n

    def test_zero_positives_is_negative(self) -> None:
        result = score_pcptsd5([0, 0, 0, 0, 0])
        assert result.positive_count == 0
        assert result.positive_screen is False

    def test_all_positives_is_positive(self) -> None:
        result = score_pcptsd5([1, 1, 1, 1, 1])
        assert result.positive_count == 5
        assert result.positive_screen is True


class TestCutoffBoundary:
    """The ``>= 3`` boundary — explicit just-below and at-cutoff tests
    so a fence-post regression is caught."""

    def test_two_positives_is_below_cutoff(self) -> None:
        """2 of 5 endorsed → negative screen.  Prins 2016 considered
        cutpoint 2 but selected 3 for better specificity; the scorer
        must encode the chosen operating point."""
        result = score_pcptsd5(_items(2))
        assert result.positive_count == 2
        assert result.positive_screen is False

    def test_three_positives_is_at_cutoff(self) -> None:
        """3 of 5 endorsed → positive screen.  This is the exact
        published cutoff; a ``> 3`` comparator bug would flip this
        to negative and under-identify ~half of true cases."""
        result = score_pcptsd5(_items(3))
        assert result.positive_count == 3
        assert result.positive_screen is True

    def test_four_positives_is_above_cutoff(self) -> None:
        result = score_pcptsd5(_items(4))
        assert result.positive_count == 4
        assert result.positive_screen is True


class TestItemOrderIndependence:
    """Sum-based gates are order-independent — pin it so a refactor
    that replaced ``sum()`` with an index-sensitive path is caught."""

    def test_positives_at_end_scores_same(self) -> None:
        # 3 positives clustered at the end
        result = score_pcptsd5([0, 0, 1, 1, 1])
        assert result.positive_count == 3
        assert result.positive_screen is True

    def test_positives_interleaved_scores_same(self) -> None:
        # 3 positives interleaved
        result = score_pcptsd5([1, 0, 1, 0, 1])
        assert result.positive_count == 3
        assert result.positive_screen is True


class TestItemCountValidation:
    """Exactly 5 items required."""

    def test_rejects_four_items(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 5 items"):
            score_pcptsd5([1, 1, 1, 0])

    def test_rejects_six_items(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 5 items"):
            score_pcptsd5([1, 1, 1, 0, 0, 0])

    def test_rejects_empty(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 5 items"):
            score_pcptsd5([])


class TestItemRangeValidation:
    """Items must be exactly 0 or 1 — PC-PTSD-5 is binary yes/no."""

    @pytest.mark.parametrize("bad_value", [-1, 2, 3, 10, 100])
    def test_rejects_out_of_range(self, bad_value: int) -> None:
        items = [0, 0, bad_value, 0, 0]
        with pytest.raises(InvalidResponseError, match="out of range"):
            score_pcptsd5(items)

    def test_rejects_string_item(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_pcptsd5([1, 0, "1", 0, 0])  # type: ignore[list-item]

    def test_rejects_float_item(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_pcptsd5([1.0, 0, 1, 0, 0])  # type: ignore[list-item]

    def test_rejects_none_item(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_pcptsd5([1, None, 1, 0, 0])  # type: ignore[list-item]


class TestBoolRejection:
    """Bool items are rejected even though ``True``/``False`` happen to
    match the 1/0 wire values.  Rationale: uniform wire contract across
    the psychometric package.  See scoring/pcptsd5.py module docstring.
    """

    def test_rejects_true_item(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_pcptsd5([True, 0, 1, 0, 0])  # type: ignore[list-item]

    def test_rejects_false_item(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_pcptsd5([0, False, 1, 0, 0])  # type: ignore[list-item]

    def test_error_names_the_item_index(self) -> None:
        """Error message names the 1-indexed item number so a clinician
        matches the error against the PC-PTSD-5 paper's item list."""
        with pytest.raises(InvalidResponseError, match="PC-PTSD-5 item 3"):
            score_pcptsd5([0, 0, True, 0, 0])  # type: ignore[list-item]


class TestResultShape:
    """PcPtsd5Result carries the fields the router needs."""

    def test_result_is_frozen(self) -> None:
        result = score_pcptsd5(_items(3))
        with pytest.raises(Exception):  # FrozenInstanceError subclass
            result.positive_count = 99  # type: ignore[misc]

    def test_items_are_tuple(self) -> None:
        """Tuple (not list) so the result is hashable and can be pinned
        into an immutable repository record."""
        result = score_pcptsd5(_items(3))
        assert isinstance(result.items, tuple)
        assert result.items == (1, 1, 1, 0, 0)

    def test_result_echoes_instrument_version(self) -> None:
        result = score_pcptsd5(_items(3))
        assert result.instrument_version == INSTRUMENT_VERSION

    def test_no_requires_t3_field(self) -> None:
        """PC-PTSD-5 has no safety item.  The result dataclass
        deliberately omits ``requires_t3`` so downstream code cannot
        accidentally route a positive PTSD screen into a T3 crisis
        flow — which would be clinically wrong.  See module docstring."""
        result = score_pcptsd5(_items(5))
        assert not hasattr(result, "requires_t3")


class TestClinicalVignettes:
    """Named patterns a clinician would recognize — tests the scorer
    as-written against real-world presentations.
    """

    def test_avoider_only(self) -> None:
        """Single-symptom presentation (only item 2 — avoidance).
        Below cutoff — a screen that flips positive on one endorsed
        item would fail this case."""
        # Items: [nightmares, avoidance, hypervigilance, numb, guilt]
        result = score_pcptsd5([0, 1, 0, 0, 0])
        assert result.positive_count == 1
        assert result.positive_screen is False

    def test_hypervigilant_and_numb(self) -> None:
        """Two-symptom presentation (items 3 + 4).  Still below the
        published cutoff — PC-PTSD-5 discriminates on symptom
        *breadth*, not severity."""
        result = score_pcptsd5([0, 0, 1, 1, 0])
        assert result.positive_count == 2
        assert result.positive_screen is False

    def test_intrusion_avoidance_hyperarousal(self) -> None:
        """Classic DSM-5 cluster pattern (items 1 + 2 + 3 — intrusion,
        avoidance, hyperarousal).  At the published cutoff → positive
        screen, routes to CAPS-5 / PCL-5 referral."""
        result = score_pcptsd5([1, 1, 1, 0, 0])
        assert result.positive_count == 3
        assert result.positive_screen is True

    def test_full_symptom_cluster(self) -> None:
        """All 5 symptoms endorsed — unambiguous positive screen."""
        result = score_pcptsd5([1, 1, 1, 1, 1])
        assert result.positive_count == 5
        assert result.positive_screen is True


class TestNoSafetyRouting:
    """PC-PTSD-5 is a referral signal, not a crisis signal.  The
    scorer must not expose anything that a downstream router could
    mistake for a T3 trigger.  The T3 pathway is reserved for active
    suicidality per Docs/Whitepapers/04_Safety_Framework.md §T3.
    """

    def test_max_positive_has_no_safety_field(self) -> None:
        result = score_pcptsd5([1, 1, 1, 1, 1])
        # No requires_t3, no t3_reason, no triggering_items — the
        # result is a pure screen count + boolean.
        assert not hasattr(result, "requires_t3")
        assert not hasattr(result, "t3_reason")
        assert not hasattr(result, "triggering_items")

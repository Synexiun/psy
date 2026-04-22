"""PHQ-2 scoring tests — Kroenke 2003.

Two load-bearing correctness properties for the 2-item PHQ-2:

1. **Cutoff is ``>= 3``, not ``> 3`` and not ``>= 2``.**  Kroenke 2003
   selected cutpoint 3 as the operating point (sensitivity 0.83,
   specificity 0.92 for any depressive disorder).  A fence-post bug
   that flipped the comparator would either miss true positives
   (``> 3`` turns a 3-total screen negative) or over-fire on
   sub-clinical low-mood days (``>= 2``).  The boundary tests pin 2
   and 3 explicitly.
2. **Exactly 2 items, each in ``[0, 3]`` Likert.**  PHQ-2 is a 0-3
   four-point Likert on anhedonia (item 1) and depressed mood
   (item 2) — identical wording to PHQ-9 items 1 and 2.  A response
   outside ``[0, 3]`` is a validation error, not a silent coercion.

Coverage strategy:
- Pin total-correctness across representative combinations.
- Pin the cutoff boundary both just-below (2) and at-cutoff (3) so
  the published operating point is nailed down.
- Bool rejection (uniform with the rest of the package).
- Item-count and item-range rejection.
- Clinical vignettes a clinician would recognize (anhedonia-only,
  depressed-mood-only, both-moderate, both-severe).
- No safety routing — PHQ-2 deliberately excludes PHQ-9 item 9, so
  ``requires_t3`` never appears on the result dataclass (unlike
  Phq9Result / CssrsResult).  See module docstring.
"""

from __future__ import annotations

import pytest

from discipline.psychometric.scoring.phq2 import (
    INSTRUMENT_VERSION,
    ITEM_COUNT,
    ITEM_MAX,
    ITEM_MIN,
    PHQ2_POSITIVE_CUTOFF,
    InvalidResponseError,
    score_phq2,
)


class TestConstants:
    """Pin published constants so a drift from Kroenke 2003 is caught."""

    def test_item_count_is_two(self) -> None:
        assert ITEM_COUNT == 2

    def test_item_range_is_zero_to_three(self) -> None:
        assert ITEM_MIN == 0
        assert ITEM_MAX == 3

    def test_positive_cutoff_is_three(self) -> None:
        """Kroenke 2003 §Results — cutpoint 3 is the published operating
        point (sensitivity 0.83 / specificity 0.92 for any depressive
        disorder).  Any change to this constant is a clinical change,
        not an implementation tweak, and must cite a replacement paper.
        """
        assert PHQ2_POSITIVE_CUTOFF == 3

    def test_instrument_version_pinned(self) -> None:
        assert INSTRUMENT_VERSION == "phq2-1.0.0"


class TestTotalCorrectness:
    """Every total across [0, 6] scores as the sum of the two items."""

    @pytest.mark.parametrize(
        "items,expected",
        [
            ([0, 0], 0),
            ([1, 0], 1),
            ([0, 1], 1),
            ([1, 1], 2),
            ([2, 1], 3),
            ([1, 2], 3),
            ([3, 0], 3),
            ([0, 3], 3),
            ([2, 2], 4),
            ([3, 2], 5),
            ([3, 3], 6),
        ],
    )
    def test_total_matches_sum(
        self, items: list[int], expected: int
    ) -> None:
        result = score_phq2(items)
        assert result.total == expected

    def test_zero_total_is_negative(self) -> None:
        result = score_phq2([0, 0])
        assert result.total == 0
        assert result.positive_screen is False

    def test_max_total_is_positive(self) -> None:
        result = score_phq2([3, 3])
        assert result.total == 6
        assert result.positive_screen is True


class TestCutoffBoundary:
    """The ``>= 3`` boundary — explicit just-below and at-cutoff tests
    so a fence-post regression is caught."""

    def test_total_two_is_below_cutoff(self) -> None:
        """Total = 2 (e.g. both items "several days") → negative screen.
        Kroenke 2003 considered cutpoint 2 but rejected it for
        over-firing on sub-clinical low-mood days; the scorer must
        encode the chosen operating point."""
        result = score_phq2([1, 1])
        assert result.total == 2
        assert result.positive_screen is False

    def test_total_three_is_at_cutoff(self) -> None:
        """Total = 3 → positive screen.  This is the exact published
        cutoff; a ``> 3`` comparator bug would flip this to negative
        and under-identify a large fraction of true cases."""
        result = score_phq2([2, 1])
        assert result.total == 3
        assert result.positive_screen is True

    def test_total_four_is_above_cutoff(self) -> None:
        result = score_phq2([2, 2])
        assert result.total == 4
        assert result.positive_screen is True

    def test_single_max_item_hits_cutoff(self) -> None:
        """One item maxed (3), the other zero — total = 3 → positive.
        Clinically meaningful: "every day depressed mood, no anhedonia"
        is a positive screen for evaluation.  The cutoff is on the
        *total*, not on per-item thresholds."""
        result = score_phq2([3, 0])
        assert result.total == 3
        assert result.positive_screen is True


class TestItemCountValidation:
    """Exactly 2 items required."""

    def test_rejects_one_item(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 2 items"):
            score_phq2([1])

    def test_rejects_three_items(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 2 items"):
            score_phq2([1, 1, 1])

    def test_rejects_empty(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 2 items"):
            score_phq2([])

    def test_rejects_nine_items_phq9_misroute(self) -> None:
        """A 9-item submission is almost certainly a mis-routed PHQ-9 —
        rejecting with the specific count makes the diagnostic path
        obvious rather than mysteriously returning a total of 2."""
        with pytest.raises(InvalidResponseError, match="exactly 2 items"):
            score_phq2([0, 0, 0, 0, 0, 0, 0, 0, 0])


class TestItemRangeValidation:
    """Items must be in [0, 3] — a 4-point Likert."""

    @pytest.mark.parametrize("bad_value", [-1, 4, 5, 10, 100])
    def test_rejects_out_of_range(self, bad_value: int) -> None:
        with pytest.raises(InvalidResponseError, match="out of range"):
            score_phq2([0, bad_value])

    def test_rejects_string_item(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_phq2([1, "1"])  # type: ignore[list-item]

    def test_rejects_float_item(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_phq2([1.5, 0])  # type: ignore[list-item]

    def test_rejects_none_item(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_phq2([1, None])  # type: ignore[list-item]


class TestBoolRejection:
    """Bool items are rejected — uniform with the rest of the
    psychometric package.  See scoring/phq2.py module docstring."""

    def test_rejects_true_item(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_phq2([True, 0])  # type: ignore[list-item]

    def test_rejects_false_item(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_phq2([0, False])  # type: ignore[list-item]

    def test_error_names_the_item_index(self) -> None:
        """Error message names the 1-indexed item number so a clinician
        matches the error against the PHQ-2 paper's item list."""
        with pytest.raises(InvalidResponseError, match="PHQ-2 item 2"):
            score_phq2([0, True])  # type: ignore[list-item]


class TestResultShape:
    """Phq2Result carries the fields the router needs."""

    def test_result_is_frozen(self) -> None:
        result = score_phq2([2, 1])
        with pytest.raises(Exception):  # FrozenInstanceError subclass
            result.total = 99  # type: ignore[misc]

    def test_items_are_tuple(self) -> None:
        """Tuple (not list) so the result is hashable and can be pinned
        into an immutable repository record."""
        result = score_phq2([2, 1])
        assert isinstance(result.items, tuple)
        assert result.items == (2, 1)

    def test_result_echoes_instrument_version(self) -> None:
        result = score_phq2([2, 1])
        assert result.instrument_version == INSTRUMENT_VERSION

    def test_no_requires_t3_field(self) -> None:
        """PHQ-2 deliberately excludes PHQ-9 item 9 (suicidality).  The
        result dataclass omits ``requires_t3`` so downstream code cannot
        accidentally treat a positive PHQ-2 screen as a crisis signal —
        which would be clinically wrong (cf. PHQ-9 where item 9
        presence makes T3 routing necessary).  See module docstring."""
        result = score_phq2([3, 3])
        assert not hasattr(result, "requires_t3")

    def test_no_severity_band_field(self) -> None:
        """PHQ-2 publishes no severity bands (Kroenke 2003).  The
        dataclass intentionally carries no ``severity`` field so the
        router cannot mistakenly render a banded label for PHQ-2.  The
        wire envelope maps ``positive_screen`` → "positive_screen" /
        "negative_screen" at the dispatch layer."""
        result = score_phq2([3, 3])
        assert not hasattr(result, "severity")


class TestClinicalVignettes:
    """Named patterns a clinician would recognize — tests the scorer
    as-written against real-world presentations.
    """

    def test_anhedonia_only_moderate(self) -> None:
        """Anhedonia "several days" (item 1 = 1), no depressed mood
        (item 2 = 0).  Below cutoff — a single mild endorsement does
        not warrant progression to full PHQ-9."""
        result = score_phq2([1, 0])
        assert result.total == 1
        assert result.positive_screen is False

    def test_depressed_mood_only_moderate(self) -> None:
        """Depressed mood "several days" (item 2 = 1), no anhedonia
        (item 1 = 0).  Below cutoff — symmetric with the anhedonia-
        only case (order independence)."""
        result = score_phq2([0, 1])
        assert result.total == 1
        assert result.positive_screen is False

    def test_both_moderate_hits_cutoff(self) -> None:
        """Anhedonia "more than half the days" + depressed mood
        "several days" (items = [2, 1] → total 3).  At cutoff →
        positive screen, routes to full PHQ-9 administration."""
        result = score_phq2([2, 1])
        assert result.total == 3
        assert result.positive_screen is True

    def test_both_severe_unambiguously_positive(self) -> None:
        """Both items "nearly every day" (items = [3, 3] → total 6).
        Unambiguous positive screen — canonical major-depression
        presentation on PHQ-2."""
        result = score_phq2([3, 3])
        assert result.total == 6
        assert result.positive_screen is True


class TestNoSafetyRouting:
    """PHQ-2 deliberately excludes PHQ-9 item 9 (suicidality).  The
    scorer must not expose anything that a downstream router could
    mistake for a T3 trigger.  The T3 pathway is reserved for active
    suicidality per Docs/Whitepapers/04_Safety_Framework.md §T3 and
    is gated on PHQ-9 / C-SSRS — not on PHQ-2."""

    def test_max_total_has_no_safety_field(self) -> None:
        result = score_phq2([3, 3])
        # No requires_t3, no t3_reason, no triggering_items — the
        # result is a pure total + positive-screen boolean.
        assert not hasattr(result, "requires_t3")
        assert not hasattr(result, "t3_reason")
        assert not hasattr(result, "triggering_items")

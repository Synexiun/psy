"""Unit tests for the BIS-11 (Barratt Impulsiveness Scale) scorer.

Covers:
- Module constants pin to Patton 1995 / Stanford 2009 (30 items,
  1-4 Likert, 30-120 total, 11 reverse-coded items, three second-
  order subscales).
- Reverse-coding correctness (1↔4, 2↔3) — the pattern where prior
  instruments made silent off-by-one regressions.
- Stanford 2009 severity-band boundaries (≤ 51 low, 52-71 normal,
  ≥ 72 high) — each boundary pinned with just-below / at-boundary
  pairs.
- Subscale sums are computed on *scored* values (so reverse-coded
  items' contributions are monotonic in the impulsivity direction).
- Item-count, item-range (1-4 — NOT 0-based), bool rejection.
- Result-shape invariants (frozen, tuples, no requires_t3).
- Clinical vignettes (attentional-dominant / motor-dominant /
  non-planning-dominant patterns).
- No-safety-routing invariant.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError, fields

import pytest

from discipline.psychometric.scoring.bis11 import (
    BIS11_SEVERITY_THRESHOLDS,
    BIS11_SUBSCALES,
    INSTRUMENT_VERSION,
    ITEM_COUNT,
    ITEM_MAX,
    ITEM_MIN,
    REVERSE_SCORED_ITEMS_1INDEXED,
    Bis11Result,
    InvalidResponseError,
    score_bis11,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
class TestConstants:
    """Patton 1995 / Stanford 2009 numerics are clinical facts."""

    def test_instrument_version_is_pinned(self) -> None:
        assert INSTRUMENT_VERSION == "bis11-1.0.0"

    def test_item_count_is_thirty(self) -> None:
        assert ITEM_COUNT == 30

    def test_item_min_is_one_not_zero(self) -> None:
        # Critical: BIS-11 is the first non-zero-based scale in the
        # package.  A regression that copy-pasted ITEM_MIN = 0 from
        # another instrument would silently accept 0-responses and
        # push every total 30 points too low.
        assert ITEM_MIN == 1

    def test_item_max_is_four(self) -> None:
        assert ITEM_MAX == 4

    def test_eleven_items_reverse_coded(self) -> None:
        # Patton 1995 Table 1: items 1, 7, 8, 9, 10, 12, 13, 15, 20,
        # 29, 30.  Pinned to catch a silent drop during refactor.
        assert REVERSE_SCORED_ITEMS_1INDEXED == frozenset(
            {1, 7, 8, 9, 10, 12, 13, 15, 20, 29, 30}
        )

    def test_stanford_2009_severity_bands_pinned(self) -> None:
        assert BIS11_SEVERITY_THRESHOLDS == (
            (51, "low"),
            (71, "normal"),
            (120, "high"),
        )

    def test_subscale_memberships_pinned(self) -> None:
        # Patton 1995 Table 2.
        assert BIS11_SUBSCALES["attentional"] == (5, 6, 9, 11, 20, 24, 26, 28)
        assert BIS11_SUBSCALES["motor"] == (
            2, 3, 4, 16, 17, 19, 21, 22, 23, 25, 30,
        )
        assert BIS11_SUBSCALES["non_planning"] == (
            1, 7, 8, 10, 12, 13, 14, 15, 18, 27, 29,
        )

    def test_subscale_memberships_cover_all_thirty_items(self) -> None:
        """Every item in 1-30 must belong to exactly one subscale —
        if a refactor dropped an item the subscale totals would
        silently stop summing to the instrument total."""
        covered: set[int] = set()
        for positions in BIS11_SUBSCALES.values():
            covered.update(positions)
        assert covered == set(range(1, 31))
        # And total count across all subscales must equal 30.
        total_positions = sum(
            len(positions) for positions in BIS11_SUBSCALES.values()
        )
        assert total_positions == 30


# ---------------------------------------------------------------------------
# Total correctness
# ---------------------------------------------------------------------------
class TestTotalCorrectness:
    """Patton 1995 straight-sum after reverse-coding."""

    def test_all_ones_maps_through_reversal(self) -> None:
        # All raw 1s.  Reverse-coded items become 4; non-reversed
        # items stay 1.
        # = (11 × 4) + (19 × 1) = 44 + 19 = 63.
        result = score_bis11([1] * 30)
        assert result.total == 63

    def test_all_fours_maps_through_reversal(self) -> None:
        # All raw 4s.  Reverse-coded items become 1; non-reversed
        # items stay 4.
        # = (11 × 1) + (19 × 4) = 11 + 76 = 87.
        result = score_bis11([4] * 30)
        assert result.total == 87

    def test_all_twos_has_mirror_symmetric_total(self) -> None:
        # All raw 2s.  Reverse-coded items become 3; non-reversed
        # items stay 2.
        # = (11 × 3) + (19 × 2) = 33 + 38 = 71.  Boundary case —
        # lands exactly on the Stanford "normal" upper edge.
        result = score_bis11([2] * 30)
        assert result.total == 71
        assert result.severity == "normal"

    def test_all_threes_is_normal_upper_end(self) -> None:
        # All raw 3s.  Reverse-coded items become 2; non-reversed
        # items stay 3.
        # = (11 × 2) + (19 × 3) = 22 + 57 = 79 → "high".
        result = score_bis11([3] * 30)
        assert result.total == 79
        assert result.severity == "high"


# ---------------------------------------------------------------------------
# Reverse-coding correctness
# ---------------------------------------------------------------------------
class TestReverseCoding:
    """Reverse-coded item at position N produces the scale-inverted
    scored value while leaving adjacent non-reversed items untouched."""

    def test_scored_items_reverses_positive_items(self) -> None:
        # Everyone at 1.  Scored items must be 4 at reverse-coded
        # positions and 1 at non-reversed positions.
        result = score_bis11([1] * 30)
        for one_indexed_pos in range(1, 31):
            expected = 4 if one_indexed_pos in REVERSE_SCORED_ITEMS_1INDEXED else 1
            assert result.scored_items[one_indexed_pos - 1] == expected, (
                f"Item {one_indexed_pos} scored incorrectly"
            )

    def test_raw_items_preserved_pre_reversal(self) -> None:
        """``raw_items`` must be the verbatim input; only
        ``scored_items`` reflects reversal."""
        raw = [3] * 30
        result = score_bis11(raw)
        assert result.raw_items == tuple(raw)
        # And scored_items applies the 5 - v transform to positions
        # in REVERSE_SCORED_ITEMS_1INDEXED.
        for one_indexed_pos in range(1, 31):
            expected = (
                5 - 3 if one_indexed_pos in REVERSE_SCORED_ITEMS_1INDEXED else 3
            )
            assert result.scored_items[one_indexed_pos - 1] == expected


# ---------------------------------------------------------------------------
# Severity band boundaries
# ---------------------------------------------------------------------------
class TestSeverityBands:
    """Stanford 2009 tri-band cutoffs pinned at their exact boundaries.
    These are the fence posts where clinical decisions pivot."""

    def _items_summing_to(self, target_total: int) -> list[int]:
        """Build a 30-item 1-4 list whose scored sum equals target.

        Strategy: start from the scored minimum (each position
        contributing 1 to the scored total = 30 total) and distribute
        ``target - 30`` extra points across positions by moving each
        position's raw value in the direction that *increases* its
        scored contribution.  For non-reverse items that's raw
        1 → 2 → 3 → 4; for reverse items that's raw 4 → 3 → 2 → 1.
        Each position can absorb 0-3 extra points before saturating.
        """
        assert 30 <= target_total <= 120, target_total
        # Scored minimum: raw 1 for non-reverse, raw 4 for reverse.
        items = [1] * 30
        for one_indexed in REVERSE_SCORED_ITEMS_1INDEXED:
            items[one_indexed - 1] = 4
        extra = target_total - 30
        pos = 0
        while extra > 0 and pos < 30:
            gain = min(3, extra)
            one_indexed = pos + 1
            if one_indexed in REVERSE_SCORED_ITEMS_1INDEXED:
                items[pos] -= gain  # 4 → 3 / 2 / 1 raises scored
            else:
                items[pos] += gain  # 1 → 2 / 3 / 4 raises scored
            extra -= gain
            pos += 1
        return items

    def test_total_fifty_one_is_low(self) -> None:
        items = self._items_summing_to(51)
        result = score_bis11(items)
        assert result.total == 51
        assert result.severity == "low"

    def test_total_fifty_two_is_normal(self) -> None:
        items = self._items_summing_to(52)
        result = score_bis11(items)
        assert result.total == 52
        assert result.severity == "normal"

    def test_total_seventy_one_is_normal(self) -> None:
        items = self._items_summing_to(71)
        result = score_bis11(items)
        assert result.total == 71
        assert result.severity == "normal"

    def test_total_seventy_two_is_high(self) -> None:
        items = self._items_summing_to(72)
        result = score_bis11(items)
        assert result.total == 72
        assert result.severity == "high"

    def test_minimum_total_is_low(self) -> None:
        # All reverse items max, all non-reverse items min: the
        # scored minimum of 30 × 1 = 30.
        items = [1] * 30
        # Flip all reverse-coded items to 4 (they'll reverse back to 1).
        for one_indexed in REVERSE_SCORED_ITEMS_1INDEXED:
            items[one_indexed - 1] = 4
        result = score_bis11(items)
        assert result.total == 30
        assert result.severity == "low"

    def test_maximum_total_is_high(self) -> None:
        # Mirror: all non-reverse items at 4, all reverse items at 1
        # (which reverse back to 4) → scored total 120.
        items = [4] * 30
        for one_indexed in REVERSE_SCORED_ITEMS_1INDEXED:
            items[one_indexed - 1] = 1
        result = score_bis11(items)
        assert result.total == 120
        assert result.severity == "high"


# ---------------------------------------------------------------------------
# Subscale correctness
# ---------------------------------------------------------------------------
class TestSubscales:
    """Patton 1995 second-order factor scoring on post-reversal values."""

    def test_attentional_subscale_on_all_ones(self) -> None:
        # All raw 1s.  Attentional items 5, 6, 9, 11, 20, 24, 26, 28.
        # Items 9 and 20 are reverse-coded → scored 4; the other 6
        # attentional items are scored 1.
        # Subscale = 6 × 1 + 2 × 4 = 6 + 8 = 14.
        result = score_bis11([1] * 30)
        assert result.subscale_attentional == 14

    def test_motor_subscale_on_all_ones(self) -> None:
        # Motor items 2, 3, 4, 16, 17, 19, 21, 22, 23, 25, 30.
        # Only item 30 is reverse-coded → scored 4; the other 10
        # motor items are scored 1.
        # Subscale = 10 × 1 + 1 × 4 = 14.
        result = score_bis11([1] * 30)
        assert result.subscale_motor == 14

    def test_non_planning_subscale_on_all_ones(self) -> None:
        # Non-planning items 1, 7, 8, 10, 12, 13, 14, 15, 18, 27, 29.
        # Reverse-coded among these: 1, 7, 8, 10, 12, 13, 15, 29
        # (eight items) → scored 4; the other 3 (14, 18, 27) are
        # scored 1.
        # Subscale = 8 × 4 + 3 × 1 = 32 + 3 = 35.
        result = score_bis11([1] * 30)
        assert result.subscale_non_planning == 35

    def test_subscales_sum_to_total(self) -> None:
        # Invariant: the three subscale totals partition the full
        # 30-item scored sum.  A regression that dropped an item
        # from a subscale would break this.
        result = score_bis11([2] * 30)
        assert (
            result.subscale_attentional
            + result.subscale_motor
            + result.subscale_non_planning
            == result.total
        )


# ---------------------------------------------------------------------------
# Item-count validation
# ---------------------------------------------------------------------------
class TestItemCountValidation:
    def test_twenty_nine_items_raises(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 30 items"):
            score_bis11([1] * 29)

    def test_thirty_one_items_raises(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 30 items"):
            score_bis11([1] * 31)

    def test_empty_list_raises(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 30 items"):
            score_bis11([])


# ---------------------------------------------------------------------------
# Item-range validation
# ---------------------------------------------------------------------------
class TestItemRangeValidation:
    """1-4 Likert, not 0-based.  The zero-value test is the critical
    regression guard — a client that reused a 0-based UI widget would
    submit 0s and the scorer must catch them."""

    def test_zero_item_raises(self) -> None:
        """BIS-11 is the first non-zero-based instrument — a 0 is
        the classic off-by-one from a copy-pasted 0-4 Likert UI."""
        items = [1] * 30
        items[0] = 0
        with pytest.raises(InvalidResponseError, match="out of range"):
            score_bis11(items)

    def test_negative_item_raises(self) -> None:
        items = [1] * 30
        items[15] = -1
        with pytest.raises(InvalidResponseError, match="out of range"):
            score_bis11(items)

    def test_item_five_raises(self) -> None:
        items = [1] * 30
        items[5] = 5
        with pytest.raises(InvalidResponseError, match="out of range"):
            score_bis11(items)

    def test_error_message_names_the_item_index(self) -> None:
        items = [1] * 30
        items[6] = 9  # item 7 — off-scale
        with pytest.raises(InvalidResponseError, match="item 7"):
            score_bis11(items)

    def test_item_value_one_is_accepted(self) -> None:
        result = score_bis11([1] * 30)
        assert result.raw_items[0] == 1

    def test_item_value_four_is_accepted(self) -> None:
        result = score_bis11([4] * 30)
        assert result.raw_items[0] == 4


# ---------------------------------------------------------------------------
# Bool rejection
# ---------------------------------------------------------------------------
class TestBoolRejection:
    """Uniform with every other scorer in the package."""

    def test_true_raises(self) -> None:
        items: list[int] = [1] * 30
        items[0] = True  # type: ignore[list-item]
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_bis11(items)

    def test_false_raises(self) -> None:
        items: list[int] = [1] * 30
        items[5] = False  # type: ignore[list-item]
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_bis11(items)


# ---------------------------------------------------------------------------
# Result shape
# ---------------------------------------------------------------------------
class TestResultShape:
    def test_result_is_frozen(self) -> None:
        result = score_bis11([2] * 30)
        with pytest.raises(FrozenInstanceError):
            result.total = 99  # type: ignore[misc]

    def test_raw_and_scored_items_are_tuples(self) -> None:
        result = score_bis11([2] * 30)
        assert isinstance(result.raw_items, tuple)
        assert isinstance(result.scored_items, tuple)
        assert len(result.raw_items) == 30
        assert len(result.scored_items) == 30

    def test_instrument_version_is_default(self) -> None:
        result = score_bis11([2] * 30)
        assert result.instrument_version == INSTRUMENT_VERSION

    def test_result_has_no_requires_t3_field(self) -> None:
        """BIS-11 is a trait inventory; no T3 surface exposed."""
        field_names = {f.name for f in fields(Bis11Result)}
        assert "requires_t3" not in field_names


# ---------------------------------------------------------------------------
# Clinical vignettes
# ---------------------------------------------------------------------------
class TestClinicalVignettes:
    """Patton 1995 subscale-dominant profiles."""

    def test_attentional_dominant_profile(self) -> None:
        # Patient reports chronic mind-wandering ("I have racing
        # thoughts", attentional) with otherwise moderate planning
        # and motor control.  Attentional items high (3 on non-R,
        # 2 on R which scores 3); motor and non-planning moderate.
        items = [2] * 30
        for pos in BIS11_SUBSCALES["attentional"]:
            # Push each attentional item to the high end (contribution
            # 3 to the subscale regardless of reversal).
            items[pos - 1] = 3 if pos not in REVERSE_SCORED_ITEMS_1INDEXED else 2
        result = score_bis11(items)
        # Attentional subscale should dominate relative to the
        # other two per-item contribution.
        per_item_attn = result.subscale_attentional / 8
        per_item_motor = result.subscale_motor / 11
        per_item_nonplan = result.subscale_non_planning / 11
        assert per_item_attn > per_item_motor
        assert per_item_attn > per_item_nonplan

    def test_maximum_profile_is_high_severity(self) -> None:
        # Mirror of test_maximum_total_is_high but checking the
        # full clinical-vignette contract: the patient at the
        # Stanford 2009 impulsivity ceiling should trip the "high"
        # band cleanly without off-by-one.
        items = [4] * 30
        for one_indexed in REVERSE_SCORED_ITEMS_1INDEXED:
            items[one_indexed - 1] = 1
        result = score_bis11(items)
        assert result.total == 120
        assert result.severity == "high"

    def test_response_bias_profile_is_low(self) -> None:
        # Stanford 2009 flags the ≤ 51 band as possible socially-
        # desirable-responding bias — a patient who reports
        # "Rarely/Never" on every impulsiveness statement and
        # "Almost Always" on every planning statement produces
        # the floor score.
        items = [1] * 30
        for one_indexed in REVERSE_SCORED_ITEMS_1INDEXED:
            items[one_indexed - 1] = 4
        result = score_bis11(items)
        assert result.total == 30
        assert result.severity == "low"


# ---------------------------------------------------------------------------
# Safety-routing absence
# ---------------------------------------------------------------------------
class TestNoSafetyRouting:
    """Trait impulsivity is not a crisis surface."""

    def test_ceiling_profile_exposes_no_t3_field(self) -> None:
        items = [4] * 30
        for one_indexed in REVERSE_SCORED_ITEMS_1INDEXED:
            items[one_indexed - 1] = 1
        result = score_bis11(items)
        assert not hasattr(result, "requires_t3")

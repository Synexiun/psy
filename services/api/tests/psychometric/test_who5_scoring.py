"""WHO-5 Well-Being Index scoring tests — Topp 2015.

Every cutoff boundary is pinned.  Changing a cutoff here forces the
change through code review rather than letting it slide as a silent
edit — these thresholds are citation-anchored to Topp 2015 §3.2 and
any movement requires a clinical sign-off.

The ``raw_total × 4 = index`` conversion is also pinned at every
published reference point.  Shipping the raw total where the index was
expected would silently mis-trigger every clinical cutoff.
"""

from __future__ import annotations

import pytest

from discipline.psychometric.scoring.who5 import (
    INSTRUMENT_VERSION,
    InvalidResponseError,
    RAW_TO_INDEX_MULTIPLIER,
    WHO5_DEPRESSION_SCREEN_CUTOFF,
    WHO5_POOR_WELLBEING_CUTOFF,
    Who5Result,
    score_who5,
)


# =============================================================================
# Constants — pinned to published source
# =============================================================================


class TestConstants:
    def test_item_count_is_five(self) -> None:
        """Sanity: a WHO-5 with a different number of items isn't WHO-5."""
        # Round-trip through a known-good score — 5 items required.
        result = score_who5([0, 0, 0, 0, 0])
        assert len(result.items) == 5

    def test_conversion_factor_is_four(self) -> None:
        """The ``× 4`` multiplier is non-negotiable.  A change here
        would move every cutoff into nonsense space."""
        assert RAW_TO_INDEX_MULTIPLIER == 4

    def test_poor_wellbeing_cutoff_is_fifty(self) -> None:
        """Topp 2015 §3.2 primary screening cutoff."""
        assert WHO5_POOR_WELLBEING_CUTOFF == 50

    def test_depression_screen_cutoff_is_twenty_eight(self) -> None:
        """Topp 2015 §3.2 depression screening cutoff (higher
        specificity)."""
        assert WHO5_DEPRESSION_SCREEN_CUTOFF == 28

    def test_instrument_version_stable(self) -> None:
        """Downstream storage / FHIR bundles include the instrument
        version.  Changing it is a schema migration."""
        assert INSTRUMENT_VERSION == "who5-1.0.0"


# =============================================================================
# Arithmetic — raw → index conversion
# =============================================================================


class TestIndexConversion:
    def test_all_zeros_index_zero(self) -> None:
        result = score_who5([0, 0, 0, 0, 0])
        assert result.raw_total == 0
        assert result.index == 0

    def test_all_fives_index_hundred(self) -> None:
        """Maximum possible score — the 0–100 ceiling."""
        result = score_who5([5, 5, 5, 5, 5])
        assert result.raw_total == 25
        assert result.index == 100

    def test_all_threes_index_sixty(self) -> None:
        """Mid-range reference point — 15 raw * 4 = 60 index."""
        result = score_who5([3, 3, 3, 3, 3])
        assert result.raw_total == 15
        assert result.index == 60

    def test_mixed_items_raw_plus_index_consistent(self) -> None:
        result = score_who5([1, 2, 3, 4, 5])
        assert result.raw_total == 15
        assert result.index == result.raw_total * RAW_TO_INDEX_MULTIPLIER

    @pytest.mark.parametrize(
        "items, expected_raw, expected_index",
        [
            ([5, 5, 5, 5, 5], 25, 100),
            ([4, 4, 4, 4, 4], 20, 80),
            ([3, 3, 3, 3, 3], 15, 60),
            ([2, 2, 2, 2, 2], 10, 40),
            ([1, 1, 1, 1, 1], 5, 20),
            ([0, 0, 0, 0, 0], 0, 0),
        ],
    )
    def test_index_at_uniform_item_values(
        self, items: list[int], expected_raw: int, expected_index: int
    ) -> None:
        result = score_who5(items)
        assert result.raw_total == expected_raw
        assert result.index == expected_index


# =============================================================================
# Band classification — every boundary
# =============================================================================


class TestBandBoundaries:
    """The ``<`` vs ``<=`` distinction at cutoff boundaries is the most
    common clinical-scoring bug.  Every boundary value is pinned here
    so a refactor can't silently move a threshold by 1."""

    def test_index_zero_is_depression_screen(self) -> None:
        """Floor case — can't be higher-severity than this."""
        result = score_who5([0, 0, 0, 0, 0])
        assert result.band == "depression_screen"
        assert result.poor_wellbeing_flag is True

    def test_just_below_depression_cutoff(self) -> None:
        """Raw 6 → index 24 → < 28 → depression_screen.  Uses
        distributed values (each item capped at 5) to mirror a real
        user response pattern."""
        result = score_who5([1, 1, 1, 1, 2])  # 6 raw, 24 index
        assert result.index == 24
        assert result.band == "depression_screen"

    def test_at_depression_cutoff_is_poor_not_screen(self) -> None:
        """``< 28`` is strict.  Index == 28 is POOR, not
        depression_screen.  If this flipped to ``<=``, a patient with
        an index of exactly 28 would be mis-bucketed as positive for
        depression screen, which triggers a different UI path and
        possibly a referral."""
        result = score_who5([1, 1, 2, 2, 1])  # 7 raw, 28 index
        assert result.index == 28
        assert result.band == "poor"
        assert result.poor_wellbeing_flag is True

    def test_just_above_depression_cutoff(self) -> None:
        result = score_who5([2, 2, 2, 1, 1])  # 8 raw, 32 index
        assert result.index == 32
        assert result.band == "poor"

    def test_just_below_poor_cutoff(self) -> None:
        """Index 48 — still poor band (< 50)."""
        result = score_who5([2, 3, 3, 2, 2])  # 12 raw, 48 index
        assert result.index == 48
        assert result.band == "poor"
        assert result.poor_wellbeing_flag is True

    def test_at_poor_cutoff_is_adequate(self) -> None:
        """``< 50`` is strict.  Index == 50 is ADEQUATE, not poor.
        A patient hitting exactly 50 should not receive the
        poor-wellbeing flag in UI."""
        result = score_who5([3, 3, 3, 2, 2])  # not 13 — wait
        # Build an exact-50 example explicitly:
        exact = score_who5([2, 3, 3, 2, 3])  # 13 raw * 4 = 52 — not 50
        # Correct exact 50: 12.5 raw isn't possible.  Index 50 requires
        # raw 12.5 which is not integer-representable, so the CLOSEST
        # boundary-testable values are 48 (poor) and 52 (adequate).
        # This pins the boundary: 52 is adequate.
        assert exact.index == 52
        assert exact.band == "adequate"
        assert exact.poor_wellbeing_flag is False

    def test_reachable_indexes_are_multiples_of_four(self) -> None:
        """Structural property: every reachable index is divisible by 4
        (raw sum * 4).  This is why the 50 cutoff maps to 48/52 in
        practice — index == 50 is unreachable.  Callers designing
        UI bands should know this to avoid off-by-one visual artifacts."""
        samples: list[list[int]] = [
            [0, 0, 0, 0, 0],
            [1, 0, 0, 0, 0],
            [2, 2, 2, 2, 3],
            [3, 3, 3, 3, 3],
            [4, 4, 4, 4, 4],
            [5, 5, 5, 5, 5],
        ]
        for items in samples:
            result = score_who5(items)
            assert result.index % RAW_TO_INDEX_MULTIPLIER == 0

    def test_high_wellbeing_adequate(self) -> None:
        result = score_who5([4, 4, 5, 4, 5])  # 22 raw, 88 index
        assert result.index == 88
        assert result.band == "adequate"
        assert result.poor_wellbeing_flag is False

    def test_maximum_is_adequate(self) -> None:
        result = score_who5([5, 5, 5, 5, 5])
        assert result.index == 100
        assert result.band == "adequate"
        assert result.poor_wellbeing_flag is False


# =============================================================================
# Poor-wellbeing flag consistency
# =============================================================================


class TestPoorWellbeingFlag:
    """The flag is a derived boolean that must stay consistent with the
    band.  ``depression_screen`` is by definition also poor wellbeing
    (28 < 50); ``poor`` is poor; ``adequate`` is not."""

    def test_depression_screen_is_also_poor(self) -> None:
        result = score_who5([1, 1, 1, 1, 1])  # 5 raw, 20 index
        assert result.band == "depression_screen"
        assert result.poor_wellbeing_flag is True

    def test_poor_band_is_poor(self) -> None:
        result = score_who5([2, 2, 2, 2, 3])  # 11 raw, 44 index
        assert result.band == "poor"
        assert result.poor_wellbeing_flag is True

    def test_adequate_is_not_poor(self) -> None:
        result = score_who5([3, 3, 3, 3, 4])  # 16 raw, 64 index
        assert result.band == "adequate"
        assert result.poor_wellbeing_flag is False


# =============================================================================
# Validation
# =============================================================================


class TestValidation:
    def test_too_few_items_raises(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 5 items"):
            score_who5([3, 3, 3, 3])

    def test_too_many_items_raises(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 5 items"):
            score_who5([3, 3, 3, 3, 3, 3])

    def test_empty_raises(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 5 items"):
            score_who5([])

    def test_item_above_max_raises(self) -> None:
        """Item values > 5 are a caller bug — probably a 0-10 scale
        was used instead of the WHO-5 0-5 scale."""
        with pytest.raises(InvalidResponseError, match=r"out of range \[0, 5\]"):
            score_who5([6, 3, 3, 3, 3])

    def test_item_below_min_raises(self) -> None:
        with pytest.raises(InvalidResponseError, match=r"out of range \[0, 5\]"):
            score_who5([-1, 3, 3, 3, 3])

    def test_error_identifies_offending_item_one_indexed(self) -> None:
        """Clinician-facing error messages use 1-indexed item numbers
        (item 3, not item 2) — matches the instrument's own wording."""
        with pytest.raises(InvalidResponseError, match=r"item 3"):
            score_who5([3, 3, 99, 3, 3])


# =============================================================================
# Output shape — frozen dataclass, items preserved
# =============================================================================


class TestResultShape:
    def test_result_is_frozen(self) -> None:
        """Frozen so a downstream handler can't mutate a scored result
        post-hoc (e.g., 'oops, I meant severity=adequate') which would
        silently diverge from the raw total in the audit log."""
        result = score_who5([3, 3, 3, 3, 3])
        with pytest.raises(Exception):  # FrozenInstanceError
            result.index = 999  # type: ignore[misc]

    def test_items_echoed_verbatim(self) -> None:
        """The items tuple is preserved in the result for audit
        traceability — a clinician disputing a score can verify it
        from the stored items."""
        result = score_who5([0, 1, 2, 3, 4])
        assert result.items == (0, 1, 2, 3, 4)

    def test_items_is_tuple_not_list(self) -> None:
        """Tuple, not list — immutable so the stored audit record
        can't be tampered with after serialization."""
        result = score_who5([3, 3, 3, 3, 3])
        assert isinstance(result.items, tuple)

    def test_instrument_version_in_result(self) -> None:
        result = score_who5([3, 3, 3, 3, 3])
        assert result.instrument_version == INSTRUMENT_VERSION

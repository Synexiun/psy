"""AUDIT-C scoring tests — Bush 1998.

Sex-aware cutoffs are the headline feature here.  Every cutoff
boundary per sex is pinned: a regression at any of these points would
silently change which patients are flagged for follow-up, which has
direct clinical consequences (over-flag wastes clinician time;
under-flag misses problem-drinking signals).
"""

from __future__ import annotations

import pytest

from discipline.psychometric.scoring.audit_c import (
    AUDIT_C_CUTOFF_FEMALE,
    AUDIT_C_CUTOFF_MALE,
    AUDIT_C_CUTOFF_UNSPECIFIED,
    INSTRUMENT_VERSION,
    InvalidResponseError,
    score_audit_c,
)

# =============================================================================
# Constants — pinned to Bush 1998
# =============================================================================


class TestConstants:
    def test_male_cutoff_is_four(self) -> None:
        """Bush 1998: men score positive at ≥ 4.  Changing this is a
        clinical decision and should never slip through as a tweak."""
        assert AUDIT_C_CUTOFF_MALE == 4

    def test_female_cutoff_is_three(self) -> None:
        """Bush 1998: women score positive at ≥ 3.  The lower threshold
        reflects sex-differential alcohol metabolism and is published."""
        assert AUDIT_C_CUTOFF_FEMALE == 3

    def test_unspecified_cutoff_uses_lower(self) -> None:
        """Safety-conservatism: when sex is unknown we use the lower
        (more sensitive) threshold to avoid under-flagging."""
        assert AUDIT_C_CUTOFF_UNSPECIFIED == AUDIT_C_CUTOFF_FEMALE
        assert AUDIT_C_CUTOFF_UNSPECIFIED == 3

    def test_unspecified_strictly_le_male_cutoff(self) -> None:
        """Structural invariant: the unspecified cutoff must NEVER
        exceed the male cutoff.  If a refactor flipped this, sex-
        unknown users would be UNDER-flagged compared to men, which
        is the opposite of the safety-conservative posture."""
        assert AUDIT_C_CUTOFF_UNSPECIFIED <= AUDIT_C_CUTOFF_MALE

    def test_instrument_version_stable(self) -> None:
        assert INSTRUMENT_VERSION == "audit-c-1.0.0"


# =============================================================================
# Male cutoff boundary
# =============================================================================


class TestMaleCutoff:
    def test_total_three_male_negative(self) -> None:
        """Boundary: 3 < 4 → negative for male.  The most subtle
        cutoff edge — a male patient with 3 (e.g. 1+1+1) is NOT
        flagged, while a female patient with the same total IS."""
        result = score_audit_c([1, 1, 1], sex="male")
        assert result.total == 3
        assert result.cutoff_used == 4
        assert result.positive_screen is False

    def test_total_four_male_positive(self) -> None:
        """At-cutoff for male — `>= 4` is the rule, so 4 is positive."""
        result = score_audit_c([2, 1, 1], sex="male")
        assert result.total == 4
        assert result.positive_screen is True

    def test_total_five_male_positive(self) -> None:
        result = score_audit_c([2, 2, 1], sex="male")
        assert result.total == 5
        assert result.positive_screen is True

    def test_total_zero_male_negative(self) -> None:
        """Floor case — a teetotaler can't be a positive screen."""
        result = score_audit_c([0, 0, 0], sex="male")
        assert result.total == 0
        assert result.positive_screen is False

    def test_total_twelve_male_positive(self) -> None:
        """Maximum possible — definitively positive for any sex."""
        result = score_audit_c([4, 4, 4], sex="male")
        assert result.total == 12
        assert result.positive_screen is True


# =============================================================================
# Female cutoff boundary
# =============================================================================


class TestFemaleCutoff:
    def test_total_two_female_negative(self) -> None:
        result = score_audit_c([1, 1, 0], sex="female")
        assert result.total == 2
        assert result.cutoff_used == 3
        assert result.positive_screen is False

    def test_total_three_female_positive(self) -> None:
        """At-cutoff for female — 3 is positive (≥ 3).  Flipping the
        operator to ``>`` would silently downgrade a quarter of the
        problem-drinking female patients to 'negative screen' in
        production."""
        result = score_audit_c([1, 1, 1], sex="female")
        assert result.total == 3
        assert result.cutoff_used == 3
        assert result.positive_screen is True

    def test_total_four_female_positive(self) -> None:
        result = score_audit_c([2, 1, 1], sex="female")
        assert result.total == 4
        assert result.positive_screen is True

    def test_total_zero_female_negative(self) -> None:
        result = score_audit_c([0, 0, 0], sex="female")
        assert result.total == 0
        assert result.positive_screen is False


# =============================================================================
# Unspecified — falls back to the lower threshold
# =============================================================================


class TestUnspecifiedCutoff:
    def test_total_three_unspecified_positive(self) -> None:
        """Same total, sex unknown — uses lower cutoff, comes out
        positive.  This is intentionally over-sensitive."""
        result = score_audit_c([1, 1, 1], sex="unspecified")
        assert result.total == 3
        assert result.cutoff_used == 3
        assert result.positive_screen is True

    def test_total_two_unspecified_negative(self) -> None:
        result = score_audit_c([1, 1, 0], sex="unspecified")
        assert result.total == 2
        assert result.positive_screen is False

    def test_default_sex_is_unspecified(self) -> None:
        """When the caller omits ``sex``, behavior is the conservative
        default (lower cutoff).  This is a load-bearing default —
        a caller who forgets the kwarg gets safer behavior, not
        unsafer behavior."""
        result = score_audit_c([1, 1, 1])  # no sex kwarg
        assert result.cutoff_used == AUDIT_C_CUTOFF_UNSPECIFIED
        assert result.positive_screen is True


# =============================================================================
# Sex differential matters
# =============================================================================


class TestSexDifferential:
    """Identical item responses should produce different screen results
    when sex differs.  These tests prove the cutoff actually depends
    on sex; a refactor that accidentally hard-coded one cutoff would
    pass single-sex tests but fail here."""

    def test_total_three_male_vs_female_differ(self) -> None:
        items = [1, 1, 1]
        male = score_audit_c(items, sex="male")
        female = score_audit_c(items, sex="female")
        assert male.total == female.total == 3
        assert male.positive_screen is False
        assert female.positive_screen is True

    def test_cutoff_used_reflects_sex(self) -> None:
        """``cutoff_used`` is rendered in the UI ('positive at ≥ N').
        Must reflect the sex-specific cutoff, not the male one."""
        male = score_audit_c([0, 0, 0], sex="male")
        female = score_audit_c([0, 0, 0], sex="female")
        unspec = score_audit_c([0, 0, 0], sex="unspecified")
        assert male.cutoff_used == 4
        assert female.cutoff_used == 3
        assert unspec.cutoff_used == 3

    def test_sex_echoed_in_result(self) -> None:
        """Audit traceability: the sex used for cutoff selection is
        part of the result so a downstream auditor can verify the
        decision without re-running the scorer."""
        result = score_audit_c([1, 1, 1], sex="male")
        assert result.sex == "male"


# =============================================================================
# Validation
# =============================================================================


class TestValidation:
    def test_too_few_items_raises(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 3 items"):
            score_audit_c([1, 1], sex="female")

    def test_too_many_items_raises(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 3 items"):
            score_audit_c([1, 1, 1, 1], sex="female")

    def test_item_above_max_raises(self) -> None:
        """Item values > 4 are out of range — probably a 0-5 scale was
        used by mistake (WHO-5's range)."""
        with pytest.raises(InvalidResponseError, match=r"out of range \[0, 4\]"):
            score_audit_c([5, 1, 1], sex="female")

    def test_item_below_min_raises(self) -> None:
        with pytest.raises(InvalidResponseError, match=r"out of range \[0, 4\]"):
            score_audit_c([-1, 1, 1], sex="female")

    def test_error_identifies_offending_item(self) -> None:
        """1-indexed item number in the error — matches the Bush 1998
        item-numbering convention so a clinician reading the error
        can immediately point at the right question."""
        with pytest.raises(InvalidResponseError, match=r"item 2"):
            score_audit_c([1, 99, 1], sex="female")


# =============================================================================
# Edge cases — coherent vs incoherent item patterns
# =============================================================================


class TestEdgeCases:
    """The instrument doesn't enforce internal logical consistency
    (e.g., 'never drinks alcohol' but 'has 10+ on a typical drinking
    day' is mathematically possible per the published scoring).  We
    pin that we follow the published behavior — these aren't bugs."""

    def test_zero_freq_with_high_quantity_scores_normally(self) -> None:
        """Item 1 = 0 (never drinks) with item 2 = 4 (10+ on typical
        day) is logically odd but mathematically valid per Bush.
        We do NOT short-circuit — the published instrument doesn't."""
        result = score_audit_c([0, 4, 4], sex="female")
        assert result.total == 8
        assert result.positive_screen is True

    def test_max_items_is_max_total(self) -> None:
        """All-fours item set isn't valid (max is 4, not 5).  All-fours
        per the actual range yields 12."""
        result = score_audit_c([4, 4, 4], sex="male")
        assert result.total == 12

    def test_minimum_positive_screen_male(self) -> None:
        """Smallest possible positive screen for a male patient: any
        4-total combination."""
        result = score_audit_c([1, 2, 1], sex="male")
        assert result.total == 4
        assert result.positive_screen is True

    def test_maximum_negative_screen_female(self) -> None:
        """Largest possible negative screen for a female patient:
        2 (3 - 1)."""
        result = score_audit_c([1, 1, 0], sex="female")
        assert result.total == 2
        assert result.positive_screen is False


# =============================================================================
# Output shape
# =============================================================================


class TestResultShape:
    def test_result_is_frozen(self) -> None:
        result = score_audit_c([1, 1, 1], sex="male")
        with pytest.raises(Exception):  # FrozenInstanceError
            result.positive_screen = True  # type: ignore[misc]

    def test_items_echoed_verbatim(self) -> None:
        result = score_audit_c([0, 1, 2], sex="female")
        assert result.items == (0, 1, 2)

    def test_items_is_tuple(self) -> None:
        result = score_audit_c([1, 1, 1], sex="male")
        assert isinstance(result.items, tuple)

    def test_instrument_version_in_result(self) -> None:
        result = score_audit_c([1, 1, 1], sex="male")
        assert result.instrument_version == INSTRUMENT_VERSION

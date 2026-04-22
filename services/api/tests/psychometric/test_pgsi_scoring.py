"""Unit tests for the PGSI scorer.

Ferris & Wynne 2001 — Problem Gambling Severity Index.
9 items, 0-3 Likert, total 0-27, four bands:
    0     non_problem
    1-2   low_risk
    3-7   moderate_risk
    8-27  problem_gambler

Tests pin the clinically-load-bearing contract:

- Constants match Ferris & Wynne 2001 Table 5.1.
- Four-band classification pinned at every boundary (0/1, 2/3, 7/8).
- Unidimensional structure — result dataclass has NO ``subscales``
  field (Ferris 2001 §5 extracted the 9-item set via factor analysis
  from a 31-item pool precisely to retain single-factor severity).
- No ``positive_screen`` / ``cutoff_used`` fields (PGSI is banded,
  not screen).
- No ``requires_t3`` field (no acute-safety item; acute-ideation
  screening stays on C-SSRS / PHQ-9 item 9).
- Bool rejection per CLAUDE.md standing rule.

References
----------
- Ferris J, Wynne H.  *The Canadian Problem Gambling Index: Final
  Report.*  Canadian Centre on Substance Abuse, 2001.
- Currie SR et al.  *Validity of the Problem Gambling Severity
  Index interpretive categories.*  J Gambl Stud 2013;29:311-327.
"""

from __future__ import annotations

import pytest

from discipline.psychometric.scoring.pgsi import (
    INSTRUMENT_VERSION,
    ITEM_COUNT,
    ITEM_MAX,
    ITEM_MIN,
    PGSI_SEVERITY_THRESHOLDS,
    InvalidResponseError,
    score_pgsi,
)

# --------------------------------------------------------------------
# Constants — pin Ferris & Wynne 2001 source-of-truth values.
# --------------------------------------------------------------------


class TestConstants:
    """Pin published constants."""

    def test_item_count_is_9(self) -> None:
        assert ITEM_COUNT == 9

    def test_item_min_is_0(self) -> None:
        assert ITEM_MIN == 0

    def test_item_max_is_3(self) -> None:
        assert ITEM_MAX == 3

    def test_instrument_version_pinned(self) -> None:
        assert INSTRUMENT_VERSION == "pgsi-1.0.0"

    def test_severity_thresholds_match_ferris_2001(self) -> None:
        """Ferris & Wynne 2001 §5 Table 5.1 — 0 non-problem,
        1-2 low-risk, 3-7 moderate-risk, 8+ problem."""
        assert PGSI_SEVERITY_THRESHOLDS == (
            (0, "non_problem"),
            (2, "low_risk"),
            (7, "moderate_risk"),
            (27, "problem_gambler"),
        )

    def test_thresholds_are_immutable_tuple(self) -> None:
        """PGSI_SEVERITY_THRESHOLDS is an immutable tuple-of-tuples."""
        assert isinstance(PGSI_SEVERITY_THRESHOLDS, tuple)
        for threshold in PGSI_SEVERITY_THRESHOLDS:
            assert isinstance(threshold, tuple)

    def test_no_positive_cutoff_constant(self) -> None:
        """PGSI is banded, not screen — no single cutoff constant."""
        import discipline.psychometric.scoring.pgsi as pgsi_module

        assert not hasattr(pgsi_module, "PGSI_POSITIVE_CUTOFF")

    def test_no_subscales_constant(self) -> None:
        """Ferris 2001 retained unidimensional structure."""
        import discipline.psychometric.scoring.pgsi as pgsi_module

        assert not hasattr(pgsi_module, "PGSI_SUBSCALES")

    def test_exported_symbols(self) -> None:
        import discipline.psychometric.scoring.pgsi as pgsi_module

        expected = {
            "INSTRUMENT_VERSION",
            "ITEM_COUNT",
            "ITEM_MAX",
            "ITEM_MIN",
            "InvalidResponseError",
            "PGSI_SEVERITY_THRESHOLDS",
            "PgsiResult",
            "Severity",
            "score_pgsi",
        }
        assert set(pgsi_module.__all__) == expected


# --------------------------------------------------------------------
# Total correctness — straight sum of 9 items.
# --------------------------------------------------------------------


class TestTotalCorrectness:
    """Verify total is a straight sum of the 9 Likert items."""

    def test_all_zeros_total_zero(self) -> None:
        result = score_pgsi([0] * 9)
        assert result.total == 0

    def test_all_threes_total_27(self) -> None:
        result = score_pgsi([3] * 9)
        assert result.total == 27

    def test_all_ones_total_9(self) -> None:
        result = score_pgsi([1] * 9)
        assert result.total == 9

    def test_all_twos_total_18(self) -> None:
        result = score_pgsi([2] * 9)
        assert result.total == 18

    def test_mixed_total_correct(self) -> None:
        """Mixed endorsements: items 1, 3, 5, 7, 9 = Most of the time
        (2); items 2, 4, 6, 8 = Sometimes (1).  Total = 5*2 + 4*1 =
        14."""
        items = [2, 1, 2, 1, 2, 1, 2, 1, 2]
        result = score_pgsi(items)
        assert result.total == 14


# --------------------------------------------------------------------
# Band classification — four bands, three boundaries.  Pin every
# boundary so a refactor that drifts the <= to < or alters a
# threshold value fails loudly.
# --------------------------------------------------------------------


class TestBandClassification:
    """Pin Ferris & Wynne 2001 band boundaries."""

    def test_total_0_non_problem(self) -> None:
        """ACE 0: non-problem gambler."""
        result = score_pgsi([0] * 9)
        assert result.total == 0
        assert result.severity == "non_problem"

    def test_total_1_low_risk(self) -> None:
        """Just above non-problem."""
        items = [1, 0, 0, 0, 0, 0, 0, 0, 0]
        result = score_pgsi(items)
        assert result.total == 1
        assert result.severity == "low_risk"

    def test_total_2_low_risk(self) -> None:
        """Upper bound of low-risk band."""
        items = [2, 0, 0, 0, 0, 0, 0, 0, 0]
        result = score_pgsi(items)
        assert result.total == 2
        assert result.severity == "low_risk"

    def test_total_3_moderate_risk(self) -> None:
        """Just over low-risk — moderate-risk band starts."""
        items = [3, 0, 0, 0, 0, 0, 0, 0, 0]
        result = score_pgsi(items)
        assert result.total == 3
        assert result.severity == "moderate_risk"

    def test_total_7_moderate_risk(self) -> None:
        """Upper bound of moderate-risk band."""
        items = [3, 3, 1, 0, 0, 0, 0, 0, 0]
        result = score_pgsi(items)
        assert result.total == 7
        assert result.severity == "moderate_risk"

    def test_total_8_problem_gambler(self) -> None:
        """Exactly at Ferris 2001 problem-gambler cutoff.  This is
        the DSM-IV-pathological-gambling concurrent-validity
        operating point (kappa = 0.83)."""
        items = [3, 3, 2, 0, 0, 0, 0, 0, 0]
        result = score_pgsi(items)
        assert result.total == 8
        assert result.severity == "problem_gambler"

    def test_total_27_problem_gambler(self) -> None:
        """Ceiling — maximum problem severity."""
        result = score_pgsi([3] * 9)
        assert result.total == 27
        assert result.severity == "problem_gambler"

    def test_boundary_non_problem_to_low_risk(self) -> None:
        """0 -> 1 transition.  A regression that drifted the 0-band
        upper to 1 would fail this."""
        assert score_pgsi([0] * 9).severity == "non_problem"
        assert (
            score_pgsi([1, 0, 0, 0, 0, 0, 0, 0, 0]).severity == "low_risk"
        )

    def test_boundary_low_risk_to_moderate_risk(self) -> None:
        """2 -> 3 transition."""
        assert (
            score_pgsi([2, 0, 0, 0, 0, 0, 0, 0, 0]).severity == "low_risk"
        )
        assert (
            score_pgsi([3, 0, 0, 0, 0, 0, 0, 0, 0]).severity
            == "moderate_risk"
        )

    def test_boundary_moderate_risk_to_problem_gambler(self) -> None:
        """7 -> 8 transition."""
        assert (
            score_pgsi([3, 3, 1, 0, 0, 0, 0, 0, 0]).severity
            == "moderate_risk"
        )
        assert (
            score_pgsi([3, 3, 2, 0, 0, 0, 0, 0, 0]).severity
            == "problem_gambler"
        )


# --------------------------------------------------------------------
# Direction semantics — each item position adds 3 at max (no reverse
# scoring).
# --------------------------------------------------------------------


class TestDirectionSemantics:
    """No reverse items — each item adds exactly its Likert value."""

    @pytest.mark.parametrize("position", range(9))
    def test_each_item_position_adds_3_at_max(self, position: int) -> None:
        """Endorsing item at position N at max (3) with all others 0
        gives total = 3."""
        items = [0] * 9
        items[position] = 3
        result = score_pgsi(items)
        assert result.total == 3, (
            f"item position {position} did not contribute 3"
        )

    def test_higher_total_means_more_problem_severity(self) -> None:
        """Monotonicity — adding endorsements increases total."""
        totals = [
            score_pgsi([1] * k + [0] * (9 - k)).total for k in range(10)
        ]
        assert totals == list(range(10))


# --------------------------------------------------------------------
# Item-count validation — PGSI is exactly 9 items.  Traps for
# adjacent-count instruments (PHQ-9 also 9; AUDIT 10; GAD-7 7).
# --------------------------------------------------------------------


class TestItemCountValidation:
    """Reject any input without exactly 9 items."""

    def test_empty_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 9 items"):
            score_pgsi([])

    def test_8_items_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 9 items"):
            score_pgsi([1] * 8)

    def test_10_items_rejected(self) -> None:
        """10 items — AUDIT / DAST-10 / PSS-10 adjacent-count trap."""
        with pytest.raises(InvalidResponseError, match="exactly 9 items"):
            score_pgsi([0] * 10)

    def test_7_items_rejected(self) -> None:
        """7 items — GAD-7 / ISI adjacent-count trap."""
        with pytest.raises(InvalidResponseError, match="exactly 9 items"):
            score_pgsi([0] * 7)

    def test_13_items_rejected(self) -> None:
        """13 items — MDQ adjacent trap."""
        with pytest.raises(InvalidResponseError, match="exactly 9 items"):
            score_pgsi([0] * 13)


# --------------------------------------------------------------------
# Item-range validation — 0-3 Likert.  Reject values outside range.
# --------------------------------------------------------------------


class TestItemRangeValidation:
    """Reject items outside the 0-3 Likert range."""

    def test_value_4_rejected(self) -> None:
        """Immediately above Ferris 2001 anchor range."""
        items = [4, 0, 0, 0, 0, 0, 0, 0, 0]
        with pytest.raises(InvalidResponseError, match="must be in 0-3"):
            score_pgsi(items)

    def test_value_negative_rejected(self) -> None:
        items = [-1, 0, 0, 0, 0, 0, 0, 0, 0]
        with pytest.raises(InvalidResponseError, match="must be in 0-3"):
            score_pgsi(items)

    def test_value_7_rejected_at_last_position(self) -> None:
        """End-position — cannot assume first-item-only checks."""
        items = [0, 0, 0, 0, 0, 0, 0, 0, 7]
        with pytest.raises(InvalidResponseError, match="must be in 0-3"):
            score_pgsi(items)

    def test_error_message_names_position(self) -> None:
        """Error message includes the 1-indexed item number."""
        items = [0, 0, 0, 4, 0, 0, 0, 0, 0]
        with pytest.raises(InvalidResponseError, match="item 4"):
            score_pgsi(items)


# --------------------------------------------------------------------
# Bool rejection — CLAUDE.md standing rule.
# --------------------------------------------------------------------


class TestBoolRejection:
    """Reject bool values before int coercion."""

    def test_true_rejected(self) -> None:
        items: list = [True, 0, 0, 0, 0, 0, 0, 0, 0]
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_pgsi(items)

    def test_false_rejected(self) -> None:
        items: list = [False, 0, 0, 0, 0, 0, 0, 0, 0]
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_pgsi(items)

    def test_float_rejected(self) -> None:
        items: list = [1.0, 0, 0, 0, 0, 0, 0, 0, 0]
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_pgsi(items)

    def test_str_rejected(self) -> None:
        items: list = ["1", 0, 0, 0, 0, 0, 0, 0, 0]
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_pgsi(items)

    def test_none_rejected(self) -> None:
        items: list = [None, 0, 0, 0, 0, 0, 0, 0, 0]
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_pgsi(items)


# --------------------------------------------------------------------
# Result shape — frozen dataclass contract.
# --------------------------------------------------------------------


class TestResultShape:
    """PgsiResult dataclass contract."""

    def test_result_is_frozen(self) -> None:
        result = score_pgsi([0] * 9)
        with pytest.raises((AttributeError, Exception)):
            result.total = 999  # type: ignore[misc]

    def test_result_total_is_int(self) -> None:
        result = score_pgsi([1, 2, 3, 0, 1, 2, 3, 0, 1])
        assert isinstance(result.total, int)
        assert result.total == 13

    def test_result_severity_is_str(self) -> None:
        result = score_pgsi([3] * 9)
        assert isinstance(result.severity, str)
        assert result.severity == "problem_gambler"

    def test_result_items_is_tuple(self) -> None:
        result = score_pgsi([1, 2, 3, 0, 1, 2, 3, 0, 1])
        assert isinstance(result.items, tuple)

    def test_result_items_preserves_order(self) -> None:
        raw = [3, 0, 2, 1, 3, 0, 2, 1, 3]
        result = score_pgsi(raw)
        assert result.items == tuple(raw)

    def test_result_items_length_9(self) -> None:
        result = score_pgsi([0] * 9)
        assert len(result.items) == 9

    def test_result_version_pinned(self) -> None:
        result = score_pgsi([0] * 9)
        assert result.instrument_version == "pgsi-1.0.0"

    def test_result_no_positive_screen_field(self) -> None:
        """PGSI is banded, not screen — no positive_screen field."""
        result = score_pgsi([3] * 9)
        assert not hasattr(result, "positive_screen")

    def test_result_no_cutoff_used_field(self) -> None:
        """Banded severity — no single cutoff."""
        result = score_pgsi([3] * 9)
        assert not hasattr(result, "cutoff_used")

    def test_result_no_subscales_field(self) -> None:
        """Ferris 2001 retained unidimensional structure."""
        result = score_pgsi([3] * 9)
        assert not hasattr(result, "subscales")

    def test_result_no_requires_t3_field(self) -> None:
        """No acute-safety item."""
        result = score_pgsi([3] * 9)
        assert not hasattr(result, "requires_t3")

    def test_result_hashable(self) -> None:
        result = score_pgsi([1, 2, 3, 0, 1, 2, 3, 0, 1])
        assert hash(result) is not None


# --------------------------------------------------------------------
# Clinical vignettes — end-to-end patterns across each band.
# --------------------------------------------------------------------


class TestClinicalVignettes:
    """Canonical band patterns."""

    def test_non_problem_vignette(self) -> None:
        """General-population non-problem gambler — no endorsements."""
        result = score_pgsi([0] * 9)
        assert result.total == 0
        assert result.severity == "non_problem"

    def test_low_risk_vignette(self) -> None:
        """Occasional bet-more-than-affordable (Sometimes) — total 1,
        low-risk band; brief-intervention sufficient per Cunningham
        2014."""
        items = [1, 0, 0, 0, 0, 0, 0, 0, 0]
        result = score_pgsi(items)
        assert result.total == 1
        assert result.severity == "low_risk"

    def test_moderate_risk_tolerance_chasing_vignette(self) -> None:
        """Tolerance + chasing-losses endorsements (items 2, 3) at
        Most of the time (2) — DSM-5 disordered-gambling core
        criteria activated.  Total = 4, moderate-risk band."""
        items = [0, 2, 2, 0, 0, 0, 0, 0, 0]
        result = score_pgsi(items)
        assert result.total == 4
        assert result.severity == "moderate_risk"

    def test_problem_gambler_cutoff_vignette(self) -> None:
        """Exactly at the Ferris 2001 >=8 cutoff — DSM-IV concurrent
        validity operating point.  This patient profile indicates
        specialist behavioral-addiction referral."""
        items = [2, 1, 2, 0, 1, 1, 0, 0, 1]
        result = score_pgsi(items)
        assert result.total == 8
        assert result.severity == "problem_gambler"

    def test_severe_problem_gambler_vignette(self) -> None:
        """Full-severity problem gambler — every item Almost always
        (3).  Total 27, indicates naltrexone consideration (Kim 2001;
        Grant 2008)."""
        result = score_pgsi([3] * 9)
        assert result.total == 27
        assert result.severity == "problem_gambler"

    def test_financial_consequence_without_core_loss_of_control(
        self,
    ) -> None:
        """Items 4 (borrow money) + 8 (financial harm) endorsed at
        Sometimes, without tolerance/chasing — total 2, low-risk
        band.  A pattern where harm is present but the behavioral-
        addiction core is not yet entrenched."""
        items = [0, 0, 0, 1, 0, 0, 0, 1, 0]
        result = score_pgsi(items)
        assert result.total == 2
        assert result.severity == "low_risk"


# --------------------------------------------------------------------
# No safety routing — PGSI has NO acute-safety item.
# --------------------------------------------------------------------


class TestNoSafetyRouting:
    """PGSI does not surface any safety routing fields."""

    def test_no_triggering_items_field_on_result(self) -> None:
        result = score_pgsi([3] * 9)
        assert not hasattr(result, "triggering_items")

    def test_no_requires_t3_field_even_at_max(self) -> None:
        """Even at PGSI = 27 (full-severity problem gambler), no
        requires_t3 field on result.  Problem-gambler suicide risk
        (3.4x per Moghaddam 2015) is handled at the PROFILE level
        (PGSI + PHQ-9 + C-SSRS), not via per-PGSI-item T3."""
        result = score_pgsi([3] * 9)
        assert not hasattr(result, "requires_t3")

    def test_guilt_item_9_at_max_no_safety_flag(self) -> None:
        """Item 9 ("felt guilty about the way you gamble") endorsed
        at Almost always is NOT a safety item despite the affective
        word overlap.  Total 3 → moderate-risk band, no safety
        routing."""
        items = [0, 0, 0, 0, 0, 0, 0, 0, 3]
        result = score_pgsi(items)
        assert result.total == 3
        assert result.severity == "moderate_risk"
        assert not hasattr(result, "requires_t3")

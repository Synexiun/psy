"""Unit tests for the ACEs scorer.

Felitti VJ et al. 1998 — Adverse Childhood Experiences Questionnaire.
10 binary items, total 0-10, positive-screen cutoff >= 4.

Tests are organized to pin the clinically-load-bearing contract:

- Constants match Felitti 1998 (ITEM_COUNT=10, ACES_POSITIVE_CUTOFF=4,
  ITEM_MIN/ITEM_MAX = 0/1).
- Binary-only wire: the scorer rejects 2, 3, -1 even though these
  integers are "in range" for a plausible loose range-check
  (0 <= v <= 10).  This is the platform's first binary-only
  instrument; the pin prevents a refactor from loosening to a
  range-check.
- Bool rejection: True/False raise ``InvalidResponseError``, uniform
  with the rest of the psychometric package.
- Unidimensional structure: the result dataclass has NO ``subscales``
  field (Dong 2004 rejected the three-subscale model).
- No severity bands beyond the cutoff (CLAUDE.md "don't hand-roll
  severity thresholds").
- No ``requires_t3`` on the result (retrospective — no acute-safety
  item).
- Retrospective-instrument metadata: the scorer is stateless and
  positional-ordered per Felitti 1998; trajectory-layer one-time-
  measurement handling is upstream.

References
----------
- Felitti VJ et al. 1998 AJPM 14(4):245-258 — primary validation,
  n = 17,337 Kaiser HMO members; cutoff >= 4 established.
- Dong M et al. 2004 Child Abuse Negl 28(7):771-784 — factor
  analysis rejecting three-subscale model.
- Hughes K et al. 2017 Lancet Public Health 2(8):e356-e366 —
  meta-analysis n = 253,719 confirming dose-response.
"""

from __future__ import annotations

import pytest

from discipline.psychometric.scoring.aces import (
    ACES_POSITIVE_CUTOFF,
    AcesResult,
    INSTRUMENT_VERSION,
    ITEM_COUNT,
    ITEM_MAX,
    ITEM_MIN,
    InvalidResponseError,
    score_aces,
)


# --------------------------------------------------------------------
# Constants — pin Felitti 1998 source-of-truth values so a refactor
# cannot silently drift the clinical contract.
# --------------------------------------------------------------------


class TestConstants:
    """Pin published constants from Felitti 1998."""

    def test_item_count_is_10(self) -> None:
        assert ITEM_COUNT == 10

    def test_item_min_is_0(self) -> None:
        assert ITEM_MIN == 0

    def test_item_max_is_1(self) -> None:
        assert ITEM_MAX == 1

    def test_positive_cutoff_is_4(self) -> None:
        """Felitti 1998 §Results: ACE >= 4 = 4.7x alcoholism risk."""
        assert ACES_POSITIVE_CUTOFF == 4

    def test_instrument_version_pinned(self) -> None:
        assert INSTRUMENT_VERSION == "aces-1.0.0"

    def test_no_subscales_constant(self) -> None:
        """Dong 2004 rejected three-subscale model — no ACES_SUBSCALES
        constant should be exported."""
        import discipline.psychometric.scoring.aces as aces_module

        assert not hasattr(aces_module, "ACES_SUBSCALES")

    def test_no_severity_thresholds_constant(self) -> None:
        """No hand-rolled severity bands beyond the >=4 cutoff
        (CLAUDE.md anti-hand-rolled-bands rule)."""
        import discipline.psychometric.scoring.aces as aces_module

        assert not hasattr(aces_module, "ACES_SEVERITY_THRESHOLDS")

    def test_exported_symbols(self) -> None:
        """__all__ pins the public API."""
        import discipline.psychometric.scoring.aces as aces_module

        expected = {
            "ACES_POSITIVE_CUTOFF",
            "AcesResult",
            "INSTRUMENT_VERSION",
            "InvalidResponseError",
            "ITEM_COUNT",
            "ITEM_MAX",
            "ITEM_MIN",
            "Screen",
            "score_aces",
        }
        assert set(aces_module.__all__) == expected


# --------------------------------------------------------------------
# Total correctness — pure sum of 10 binary items, no transforms.
# --------------------------------------------------------------------


class TestTotalCorrectness:
    """Verify total is a straight sum of the 10 binary items."""

    def test_all_zeros_total_zero(self) -> None:
        """ACE = 0: no adversity exposure."""
        result = score_aces([0] * 10)
        assert result.total == 0

    def test_all_ones_total_ten(self) -> None:
        """ACE = 10: maximum adversity — every category endorsed."""
        result = score_aces([1] * 10)
        assert result.total == 10

    def test_mixed_endorsements_total_correct(self) -> None:
        """Mixed: abuse (1,2,3), neglect (4,5) endorsed; household
        dysfunction (6-10) not endorsed → total = 5."""
        result = score_aces([1, 1, 1, 1, 1, 0, 0, 0, 0, 0])
        assert result.total == 5

    def test_only_item_1_endorsed_total_one(self) -> None:
        """Minimal endorsement at item 1 only."""
        result = score_aces([1, 0, 0, 0, 0, 0, 0, 0, 0, 0])
        assert result.total == 1

    def test_only_item_10_endorsed_total_one(self) -> None:
        """Minimal endorsement at item 10 only — rules out any
        implicit position-weighting."""
        result = score_aces([0, 0, 0, 0, 0, 0, 0, 0, 0, 1])
        assert result.total == 1


# --------------------------------------------------------------------
# Cutoff boundary — Felitti 1998 §Results: ACE >= 4 is the operating
# point for elevated adult-health risk.  Pin the boundary so a
# refactor cannot drift the >= to > or drift the threshold value.
# --------------------------------------------------------------------


class TestCutoffBoundary:
    """Pin the >=4 positive-screen cutoff."""

    def test_total_3_is_negative_screen(self) -> None:
        """3 endorsements — below Felitti 1998 cutoff."""
        result = score_aces([1, 1, 1, 0, 0, 0, 0, 0, 0, 0])
        assert result.total == 3
        assert result.positive_screen is False

    def test_total_4_is_positive_screen(self) -> None:
        """4 endorsements — at Felitti 1998 cutoff, positive."""
        result = score_aces([1, 1, 1, 1, 0, 0, 0, 0, 0, 0])
        assert result.total == 4
        assert result.positive_screen is True

    def test_total_5_is_positive_screen(self) -> None:
        """Above cutoff — positive."""
        result = score_aces([1, 1, 1, 1, 1, 0, 0, 0, 0, 0])
        assert result.total == 5
        assert result.positive_screen is True

    def test_total_0_is_negative_screen(self) -> None:
        """No adversity — negative."""
        result = score_aces([0] * 10)
        assert result.total == 0
        assert result.positive_screen is False

    def test_total_10_is_positive_screen(self) -> None:
        """Ceiling — maximum adversity, positive."""
        result = score_aces([1] * 10)
        assert result.total == 10
        assert result.positive_screen is True

    def test_positive_screen_at_cutoff_exactly(self) -> None:
        """The cutoff is inclusive (>=), not strict (>)."""
        for i in range(ACES_POSITIVE_CUTOFF):
            items = [1] * (i + 1) + [0] * (9 - i)
            result = score_aces(items)
            if i + 1 < ACES_POSITIVE_CUTOFF:
                assert result.positive_screen is False, (
                    f"total={i + 1} should be negative"
                )
            else:
                assert result.positive_screen is True, (
                    f"total={i + 1} should be positive"
                )


# --------------------------------------------------------------------
# Direction semantics — higher = more adversity.  Pin each item
# position adds exactly 1 when endorsed.  Binary instrument, so
# this also doubles as a position-independence pin.
# --------------------------------------------------------------------


class TestDirectionSemantics:
    """Each item contributes exactly 1 when endorsed (higher = worse)."""

    @pytest.mark.parametrize("position", range(10))
    def test_each_item_contributes_exactly_1(self, position: int) -> None:
        """Endorsing item at position N gives total = 1."""
        items = [0] * 10
        items[position] = 1
        result = score_aces(items)
        assert result.total == 1, (
            f"item position {position} did not contribute 1"
        )

    def test_higher_total_means_more_adversity(self) -> None:
        """Monotonicity: adding endorsements increases total."""
        results = [score_aces([1] * k + [0] * (10 - k)) for k in range(11)]
        totals = [r.total for r in results]
        assert totals == list(range(11))


# --------------------------------------------------------------------
# Item-count validation — ACEs is exactly 10 items.  Traps for
# adjacent instruments with similar counts (9 items, 11 items).
# --------------------------------------------------------------------


class TestItemCountValidation:
    """Reject any input without exactly 10 items."""

    def test_empty_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 10 items"):
            score_aces([])

    def test_9_items_rejected(self) -> None:
        """Near-miss: 9 endorsements instead of 10."""
        with pytest.raises(InvalidResponseError, match="exactly 10 items"):
            score_aces([1] * 9)

    def test_11_items_rejected(self) -> None:
        """Near-miss: one item too many."""
        with pytest.raises(InvalidResponseError, match="exactly 10 items"):
            score_aces([0] * 11)

    def test_13_items_rejected(self) -> None:
        """Trap: expanded ACE-IQ has ~13 items."""
        with pytest.raises(InvalidResponseError, match="exactly 10 items"):
            score_aces([0] * 13)

    def test_1_item_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 10 items"):
            score_aces([1])


# --------------------------------------------------------------------
# Binary-range validation — the crux novel wire contract for this
# instrument.  Reject integers that are in a plausible range
# (0-10) but not strictly binary (0 or 1).  This prevents a
# silent corruption where a caller sends a count instead of a
# binary indicator.
# --------------------------------------------------------------------


class TestBinaryRangeValidation:
    """Reject non-binary integers even when "in range"."""

    def test_value_2_rejected_at_position_0(self) -> None:
        """The most obvious failure mode: 2 at position 0."""
        items = [2, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        with pytest.raises(InvalidResponseError, match="binary"):
            score_aces(items)

    def test_value_2_rejected_at_position_9(self) -> None:
        """End-position failure — cannot assume first-item-only checks."""
        items = [0, 0, 0, 0, 0, 0, 0, 0, 0, 2]
        with pytest.raises(InvalidResponseError, match="binary"):
            score_aces(items)

    def test_value_3_rejected(self) -> None:
        items = [3, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        with pytest.raises(InvalidResponseError, match="binary"):
            score_aces(items)

    def test_value_10_rejected(self) -> None:
        """Critical: 10 would silently corrupt to a total matching
        the ceiling even with one endorsement under a loose range check."""
        items = [10, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        with pytest.raises(InvalidResponseError, match="binary"):
            score_aces(items)

    def test_negative_rejected(self) -> None:
        items = [-1, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        with pytest.raises(InvalidResponseError, match="binary"):
            score_aces(items)

    def test_error_message_names_position(self) -> None:
        """Error message includes the 1-indexed position for
        clinician-interpretability."""
        items = [0, 0, 2, 0, 0, 0, 0, 0, 0, 0]
        with pytest.raises(InvalidResponseError, match="item 3"):
            score_aces(items)


# --------------------------------------------------------------------
# Type / bool rejection — uniform CLAUDE.md standing rule.  bool
# must be rejected BEFORE int-check (bool is int in Python) so
# True/False cannot pass via silent coercion.
# --------------------------------------------------------------------


class TestBoolRejection:
    """Reject bool at position 0 and position N; reject float & str."""

    def test_true_rejected(self) -> None:
        """True would coerce to 1; reject explicitly."""
        items: list = [True, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_aces(items)

    def test_false_rejected(self) -> None:
        """False would coerce to 0; reject explicitly."""
        items: list = [False, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_aces(items)

    def test_float_rejected(self) -> None:
        """float(1.0) is not int — reject."""
        items: list = [1.0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_aces(items)

    def test_str_rejected(self) -> None:
        """String values rejected."""
        items: list = ["1", 0, 0, 0, 0, 0, 0, 0, 0, 0]
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_aces(items)

    def test_none_rejected(self) -> None:
        items: list = [None, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_aces(items)


# --------------------------------------------------------------------
# Result shape — frozen dataclass contract.  Pin deliberately-
# absent fields to prevent regression drift.
# --------------------------------------------------------------------


class TestResultShape:
    """AcesResult dataclass contract."""

    def test_result_is_frozen(self) -> None:
        """Immutable — cannot drift post-score."""
        result = score_aces([0] * 10)
        with pytest.raises((AttributeError, Exception)):
            result.total = 999  # type: ignore[misc]

    def test_result_total_is_int(self) -> None:
        result = score_aces([1, 0, 1, 0, 1, 0, 0, 0, 0, 0])
        assert isinstance(result.total, int)
        assert result.total == 3

    def test_result_positive_screen_is_bool(self) -> None:
        """Pure bool — not a truthy int."""
        result = score_aces([1] * 4 + [0] * 6)
        assert isinstance(result.positive_screen, bool)
        assert result.positive_screen is True

    def test_result_items_is_tuple(self) -> None:
        """Tuple for hashability; not mutable list."""
        result = score_aces([1, 0, 1, 0, 1, 0, 0, 0, 0, 0])
        assert isinstance(result.items, tuple)

    def test_result_items_preserves_order(self) -> None:
        """items is the verbatim input order — positional per
        Felitti 1998 administration order."""
        raw = [1, 0, 1, 0, 0, 1, 0, 1, 0, 0]
        result = score_aces(raw)
        assert result.items == tuple(raw)

    def test_result_items_length_10(self) -> None:
        """items is always 10-tuple."""
        result = score_aces([0] * 10)
        assert len(result.items) == 10

    def test_result_version_pinned(self) -> None:
        result = score_aces([0] * 10)
        assert result.instrument_version == "aces-1.0.0"

    def test_result_no_severity_field(self) -> None:
        """No severity field — router envelope carries screen."""
        result = score_aces([0] * 10)
        assert not hasattr(result, "severity")

    def test_result_no_subscales_field(self) -> None:
        """Dong 2004 rejected three-subscale model."""
        result = score_aces([0] * 10)
        assert not hasattr(result, "subscales")

    def test_result_no_requires_t3_field(self) -> None:
        """Retrospective instrument — no acute safety item."""
        result = score_aces([0] * 10)
        assert not hasattr(result, "requires_t3")

    def test_result_no_triggering_items_field(self) -> None:
        """No safety-triggering items on this instrument."""
        result = score_aces([0] * 10)
        assert not hasattr(result, "triggering_items")

    def test_result_hashable(self) -> None:
        """Frozen + tuple items → hashable."""
        result = score_aces([1, 0, 1, 0, 1, 0, 0, 0, 0, 0])
        assert hash(result) is not None


# --------------------------------------------------------------------
# Clinical vignettes — end-to-end patterns clinicians recognize.
# --------------------------------------------------------------------


class TestClinicalVignettes:
    """End-to-end patterns that replicate Felitti 1998 table rows."""

    def test_no_adversity_vignette(self) -> None:
        """ACE = 0: no household adversity.  ~36% of Felitti 1998
        n = 17,337."""
        result = score_aces([0] * 10)
        assert result.total == 0
        assert result.positive_screen is False

    def test_severe_adversity_vignette(self) -> None:
        """ACE = 10: the full Felitti 1998 household-dysfunction +
        abuse + neglect pattern.  ~0.5% of the Kaiser sample."""
        result = score_aces([1] * 10)
        assert result.total == 10
        assert result.positive_screen is True

    def test_felitti_sample_mean_vignette(self) -> None:
        """Felitti 1998 overall sample mean was ACE ≈ 1.5;
        a patient reporting emotional abuse + household substance
        abuse = ACE 2 is a below-cutoff but non-zero exposure."""
        items = [1, 0, 0, 0, 0, 0, 1, 0, 0, 0]
        result = score_aces(items)
        assert result.total == 2
        assert result.positive_screen is False

    def test_household_dysfunction_only_vignette(self) -> None:
        """Items 6-10 (household dysfunction) only.  Common
        divorced-parent + incarcerated-relative + substance-abuse
        household pattern."""
        items = [0, 0, 0, 0, 0, 1, 1, 0, 1, 1]
        result = score_aces(items)
        assert result.total == 4
        assert result.positive_screen is True

    def test_abuse_only_vignette(self) -> None:
        """Items 1-3 (abuse) only.  Below cutoff — total = 3."""
        items = [1, 1, 1, 0, 0, 0, 0, 0, 0, 0]
        result = score_aces(items)
        assert result.total == 3
        assert result.positive_screen is False

    def test_at_cutoff_borderline_vignette(self) -> None:
        """Exactly ACE = 4: a common post-TIC-screening borderline
        case.  Felitti 1998 stratification puts this in the
        positive pool."""
        items = [1, 1, 0, 1, 0, 0, 0, 1, 0, 0]
        result = score_aces(items)
        assert result.total == 4
        assert result.positive_screen is True


# --------------------------------------------------------------------
# No safety routing — ACEs is retrospective-only; no acute-safety
# item.  Pin that no item position is flagged as safety-triggering.
# --------------------------------------------------------------------


class TestNoSafetyRouting:
    """No acute-safety item on any position."""

    def test_all_max_no_triggering_items_field(self) -> None:
        """Even at ACE=10, no triggering_items field on result."""
        result = score_aces([1] * 10)
        assert not hasattr(result, "triggering_items")

    def test_all_max_no_requires_t3_field(self) -> None:
        """Even at ACE=10, no requires_t3 field on result.
        Retrospective exposure is dispositional risk, not acute."""
        result = score_aces([1] * 10)
        assert not hasattr(result, "requires_t3")

    def test_child_abuse_items_endorsed_no_safety_flag(self) -> None:
        """Items 1-3 (abuse) are content-sensitive but retrospective.
        Acute-ideation screening stays on C-SSRS / PHQ-9 item 9."""
        items = [1, 1, 1, 0, 0, 0, 0, 0, 0, 0]
        result = score_aces(items)
        assert not hasattr(result, "requires_t3")
        assert not hasattr(result, "triggering_items")

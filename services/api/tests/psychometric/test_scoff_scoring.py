"""Tests for SCOFF scorer — Morgan, Reid & Lacey 1999 eating-disorder screen.

SCOFF is a 5-item binary yes/no screen for anorexia / bulimia
nervosa.  Cutoff >= 2 positive items per Morgan 1999 (sens 100% /
spec 87.5% vs DSM-III-R AN/BN); replicated by Cotton 2003 in
primary care (sens 100% / spec 89.6%) and Solmi 2015 meta-analysis
(pooled AUC 0.89).

Wire envelope matches AUDIT-C / PC-PTSD-5 / SHAPS / ACEs binary-
screen shape: positive_screen + cutoff_used, no bands, no
subscales.

No T3 — item 1 "make yourself Sick" is purging behavior (self-
induced vomiting), NOT self-harm.  Acute-risk screening stays
on C-SSRS / PHQ-9 item 9.
"""

from __future__ import annotations

import pytest

from discipline.psychometric.scoring import scoff
from discipline.psychometric.scoring.scoff import (
    INSTRUMENT_VERSION,
    ITEM_COUNT,
    ITEM_MAX,
    ITEM_MIN,
    SCOFF_POSITIVE_CUTOFF,
    InvalidResponseError,
    ScoffResult,
    score_scoff,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


class TestConstants:
    """Pin the published structure of the SCOFF instrument.

    Any change here is a clinical decision (Morgan 1999 derivation) —
    not an implementation tweak.
    """

    def test_instrument_version(self) -> None:
        assert INSTRUMENT_VERSION == "scoff-1.0.0"

    def test_item_count_is_five(self) -> None:
        assert ITEM_COUNT == 5

    def test_item_min_is_zero(self) -> None:
        assert ITEM_MIN == 0

    def test_item_max_is_one(self) -> None:
        assert ITEM_MAX == 1

    def test_positive_cutoff_is_two(self) -> None:
        # Morgan 1999 §3: operating point >= 2 produces sens 100%
        # / spec 87.5% against DSM-III-R AN/BN.  Solmi 2015 meta-
        # analysis confirmed across 25 studies (n = 26,488).
        # Changing this is a clinical decision.
        assert SCOFF_POSITIVE_CUTOFF == 2

    def test_no_severity_thresholds_exported(self) -> None:
        # SCOFF is a screen, not a severity instrument.  A
        # SCOFF_SEVERITY_THRESHOLDS constant would be a category
        # error — Morgan 1999 explicitly did not publish banded
        # severity.
        assert not hasattr(scoff, "SCOFF_SEVERITY_THRESHOLDS")

    def test_no_subscales_exported(self) -> None:
        # 5 clinical-consensus cues, not factor-partitioned.
        assert not hasattr(scoff, "SCOFF_SUBSCALES")

    def test_no_reverse_items_exported(self) -> None:
        # SCOFF items are uniform-direction yes/no; no reverse-
        # keying.
        assert not hasattr(scoff, "SCOFF_REVERSE_ITEMS")

    def test_public_exports(self) -> None:
        assert set(scoff.__all__) == {
            "INSTRUMENT_VERSION",
            "ITEM_COUNT",
            "ITEM_MAX",
            "ITEM_MIN",
            "InvalidResponseError",
            "SCOFF_POSITIVE_CUTOFF",
            "Screen",
            "ScoffResult",
            "score_scoff",
        }


# ---------------------------------------------------------------------------
# Total correctness
# ---------------------------------------------------------------------------


class TestTotalCorrectness:
    def test_all_zeros_total_zero(self) -> None:
        result = score_scoff([0, 0, 0, 0, 0])
        assert result.total == 0

    def test_all_ones_total_five(self) -> None:
        result = score_scoff([1, 1, 1, 1, 1])
        assert result.total == 5

    def test_single_one_total_one(self) -> None:
        result = score_scoff([1, 0, 0, 0, 0])
        assert result.total == 1

    def test_total_is_positional_count(self) -> None:
        # Positions 2, 4 endorsed -> total 2.
        result = score_scoff([0, 1, 0, 1, 0])
        assert result.total == 2

    def test_total_equals_sum_of_items(self) -> None:
        # Quality check: every permutation must satisfy
        # total == sum(items).
        for s_val in (0, 1):
            for c_val in (0, 1):
                for o_val in (0, 1):
                    for f1_val in (0, 1):
                        for f2_val in (0, 1):
                            items = [s_val, c_val, o_val, f1_val, f2_val]
                            result = score_scoff(items)
                            assert result.total == sum(items)


# ---------------------------------------------------------------------------
# Cutoff / screen classification
# ---------------------------------------------------------------------------


class TestCutoffBoundary:
    """Pin the Morgan 1999 >= 2 operating point."""

    def test_zero_negative(self) -> None:
        result = score_scoff([0, 0, 0, 0, 0])
        assert result.positive_screen is False

    def test_one_still_negative(self) -> None:
        # Morgan 1999 §3 REJECTED the >= 1 threshold (spec 69%).
        # Even though the single-positive case is not zero, it is
        # NOT a positive screen.
        result = score_scoff([1, 0, 0, 0, 0])
        assert result.total == 1
        assert result.positive_screen is False

    def test_two_positive_boundary(self) -> None:
        # Exactly at cutoff — the clinically-validated operating
        # point with sens 100% / spec 87.5% vs DSM-III-R AN/BN.
        result = score_scoff([1, 1, 0, 0, 0])
        assert result.total == 2
        assert result.positive_screen is True

    def test_three_positive(self) -> None:
        result = score_scoff([1, 1, 1, 0, 0])
        assert result.total == 3
        assert result.positive_screen is True

    def test_five_maximum_positive(self) -> None:
        result = score_scoff([1, 1, 1, 1, 1])
        assert result.total == 5
        assert result.positive_screen is True

    def test_any_two_positions_is_positive_screen(self) -> None:
        # The cutoff is COUNT-based, not position-based.  Every
        # pair of positions should produce positive_screen.
        from itertools import combinations

        for pos_a, pos_b in combinations(range(5), 2):
            items = [0] * 5
            items[pos_a] = 1
            items[pos_b] = 1
            result = score_scoff(items)
            assert result.total == 2
            assert result.positive_screen is True, (
                f"positions {pos_a + 1}, {pos_b + 1} did not "
                f"produce positive_screen"
            )


# ---------------------------------------------------------------------------
# Direction semantics — each position contributes identically
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("position", [0, 1, 2, 3, 4])
def test_each_position_contributes_one_at_max(position: int) -> None:
    """Pin the position-agnostic property: each SCOFF item
    contributes exactly 1 to the total when endorsed.  Rules
    out an accidental reverse-keying or position-weighted bug."""
    items = [0] * 5
    items[position] = 1
    result = score_scoff(items)
    assert result.total == 1


# ---------------------------------------------------------------------------
# Item-count validation
# ---------------------------------------------------------------------------


class TestItemCountValidation:
    def test_four_items_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 5"):
            score_scoff([0, 0, 0, 0])

    def test_six_items_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 5"):
            score_scoff([0, 0, 0, 0, 0, 0])

    def test_zero_items_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 5"):
            score_scoff([])

    def test_ten_items_rejected(self) -> None:
        # Trap: someone confuses SCOFF (5) with ACEs (10).
        with pytest.raises(InvalidResponseError, match="exactly 5"):
            score_scoff([0] * 10)

    def test_nine_items_rejected(self) -> None:
        # Trap: someone confuses SCOFF (5) with PHQ-9 (9).
        with pytest.raises(InvalidResponseError, match="exactly 5"):
            score_scoff([0] * 9)


# ---------------------------------------------------------------------------
# Binary range validation — strict 0/1
# ---------------------------------------------------------------------------


class TestBinaryRangeValidation:
    def test_two_rejected(self) -> None:
        # SCOFF is binary, not Likert — a value of 2 is invalid,
        # not "more endorsement".
        with pytest.raises(InvalidResponseError, match="must be 0 or 1"):
            score_scoff([2, 0, 0, 0, 0])

    def test_negative_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be 0 or 1"):
            score_scoff([-1, 0, 0, 0, 0])

    def test_three_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be 0 or 1"):
            score_scoff([0, 3, 0, 0, 0])

    def test_any_position_strict(self) -> None:
        # Every position must enforce 0/1 strictly.
        for position in range(5):
            items = [0] * 5
            items[position] = 2
            with pytest.raises(InvalidResponseError, match="must be 0 or 1"):
                score_scoff(items)

    def test_range_violation_reports_correct_index(self) -> None:
        with pytest.raises(InvalidResponseError, match=r"item 3"):
            score_scoff([0, 0, 99, 0, 0])


# ---------------------------------------------------------------------------
# Bool rejection — CLAUDE.md standing rule
# ---------------------------------------------------------------------------


class TestBoolRejection:
    """CLAUDE.md standing rule: ``bool`` values are rejected at
    the scorer even though ``bool is int`` in Python.  Keeps the
    wire contract explicit: a SCOFF response is a 0/1 int, not a
    flag."""

    def test_true_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_scoff([True, 0, 0, 0, 0])

    def test_false_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_scoff([False, 0, 0, 0, 0])

    def test_bool_in_each_position(self) -> None:
        for position in range(5):
            items: list[object] = [0] * 5
            items[position] = True
            with pytest.raises(InvalidResponseError, match="must be int"):
                score_scoff(items)  # type: ignore[arg-type]

    def test_float_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_scoff([0.0, 0, 0, 0, 0])  # type: ignore[list-item]

    def test_none_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_scoff([None, 0, 0, 0, 0])  # type: ignore[list-item]

    def test_string_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_scoff(["1", 0, 0, 0, 0])  # type: ignore[list-item]


# ---------------------------------------------------------------------------
# Result shape
# ---------------------------------------------------------------------------


class TestResultShape:
    def test_returns_scoff_result(self) -> None:
        result = score_scoff([0, 0, 0, 0, 0])
        assert isinstance(result, ScoffResult)

    def test_total_field_present(self) -> None:
        result = score_scoff([1, 1, 0, 0, 0])
        assert result.total == 2

    def test_positive_screen_field_present(self) -> None:
        result = score_scoff([1, 1, 0, 0, 0])
        assert result.positive_screen is True

    def test_positive_screen_is_bool_not_int(self) -> None:
        # Wire contract: positive_screen is bool, not int.  Pin
        # the exact type so the FHIR exporter does not need to
        # coerce.
        result = score_scoff([1, 1, 0, 0, 0])
        assert isinstance(result.positive_screen, bool)

    def test_instrument_version_field_present(self) -> None:
        result = score_scoff([0, 0, 0, 0, 0])
        assert result.instrument_version == INSTRUMENT_VERSION

    def test_items_stores_raw(self) -> None:
        raw = [1, 0, 1, 0, 1]
        result = score_scoff(raw)
        assert result.items == tuple(raw)

    def test_items_is_tuple(self) -> None:
        result = score_scoff([0, 0, 0, 0, 0])
        assert isinstance(result.items, tuple)

    def test_result_is_frozen(self) -> None:
        result = score_scoff([0, 0, 0, 0, 0])
        with pytest.raises((AttributeError, Exception)):
            result.total = 99  # type: ignore[misc]

    def test_result_is_hashable(self) -> None:
        result = score_scoff([0, 0, 0, 0, 0])
        assert hash(result) == hash(result)

    def test_no_severity_field(self) -> None:
        # SCOFF is a screen, not severity-banded.
        result = score_scoff([0, 0, 0, 0, 0])
        assert not hasattr(result, "severity")

    def test_no_subscales_field(self) -> None:
        result = score_scoff([0, 0, 0, 0, 0])
        assert not hasattr(result, "subscales")

    def test_no_requires_t3_field(self) -> None:
        # No SCOFF item probes suicidality.  Item 1 "make
        # yourself Sick" is purging behavior per Morgan 1999
        # Background §1.  Safety items stay on C-SSRS / PHQ-9
        # item 9.
        result = score_scoff([1, 1, 1, 1, 1])
        assert not hasattr(result, "requires_t3")


# ---------------------------------------------------------------------------
# Clinical vignettes
# ---------------------------------------------------------------------------


class TestClinicalVignettes:
    """Hand-constructed realistic response patterns matching
    clinical presentations from Morgan 1999 / Cotton 2003."""

    def test_typical_bulimia_nervosa_presentation(self) -> None:
        # BN-typical positive pattern: purging (S), loss of
        # control (C), food preoccupation (F2).  Weight loss
        # and body image per individual — often positive.
        # Morgan 1999 derivation sample: BN cases scored 3-5.
        result = score_scoff([1, 1, 0, 1, 1])
        assert result.total == 4
        assert result.positive_screen is True

    def test_typical_anorexia_nervosa_presentation(self) -> None:
        # AN-typical positive pattern: weight loss (O), body
        # image distortion (F1), food preoccupation (F2).
        # Purging varies (restrictive vs binge-purge subtype).
        # Morgan 1999 derivation sample: AN cases scored 3-5.
        result = score_scoff([0, 0, 1, 1, 1])
        assert result.total == 3
        assert result.positive_screen is True

    def test_subthreshold_one_item(self) -> None:
        # Single-item endorsement — Morgan 1999 §3 explicitly
        # negative per the rejected >= 1 threshold.
        result = score_scoff([0, 1, 0, 0, 0])
        assert result.total == 1
        assert result.positive_screen is False

    def test_no_ed_indication(self) -> None:
        # Control-sample typical pattern — no positive items.
        result = score_scoff([0, 0, 0, 0, 0])
        assert result.total == 0
        assert result.positive_screen is False

    def test_severe_ed_all_five(self) -> None:
        # Full positive endorsement — severe/chronic ED
        # presentation.  Count of 5 is not "more severe" than 2
        # in a banded sense (SCOFF is a screen, not severity),
        # but it reinforces the positive screen with higher
        # specificity.
        result = score_scoff([1, 1, 1, 1, 1])
        assert result.total == 5
        assert result.positive_screen is True


# ---------------------------------------------------------------------------
# Safety routing — no T3/T4 triggering from SCOFF
# ---------------------------------------------------------------------------


class TestNoSafetyRouting:
    """SCOFF does NOT probe suicidality.  Morgan 1999 Background
    §1 explicitly defines the mnemonic "Sick" as self-induced
    vomiting (purging behavior), NOT self-harm.  Acute-risk
    screening stays on C-SSRS / PHQ-9 item 9."""

    def test_item_1_sick_does_not_signal_safety(self) -> None:
        # Item 1 endorsement (purging) — no safety attribute.
        result = score_scoff([1, 0, 0, 0, 0])
        assert not hasattr(result, "requires_t3")

    def test_maximum_positive_does_not_signal_safety(self) -> None:
        # Even full-positive SCOFF (severe ED pattern) — no
        # T3 attribute on the scorer result.
        result = score_scoff([1, 1, 1, 1, 1])
        assert result.positive_screen is True
        assert not hasattr(result, "requires_t3")

    def test_positive_screen_no_safety_attribute(self) -> None:
        # Any positive-screen case — SCOFF does not emit T3.
        # Clinical-follow-up pathway is ED-assessment (EDE-Q /
        # EDE interview), not the suicide-response protocol.
        result = score_scoff([1, 1, 0, 0, 0])
        assert result.positive_screen is True
        assert not hasattr(result, "requires_t3")

    def test_every_single_position_no_safety(self) -> None:
        # Position-by-position: no single item produces a
        # safety attribute.
        for position in range(5):
            items = [0] * 5
            items[position] = 1
            result = score_scoff(items)
            assert not hasattr(result, "requires_t3"), (
                f"position {position + 1} unexpectedly set "
                f"requires_t3"
            )

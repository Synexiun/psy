"""Unit tests for _validate_item() and _band_for_total() pure helpers in
discipline.psychometric.scoring.wsas.

_validate_item(index_1, value) → int
  Widest Likert range in the psychometric package: 0-8 (Mundt 2002).
  All prior instruments top out at 0-3, 1-4, or 1-5.  Bool guard applies.
  A response of 9 is explicitly rejected.

_band_for_total(total) → Severity
  WSAS uses a DESCENDING-threshold table (unlike HADS/DASS-21's ascending ≤
  tables).  The first threshold where total >= threshold wins.  Mundt 2002
  cut-points: ≥20 → "severe", ≥10 → "significant", ≥0 → "subclinical".
  This means total=20 is "severe" (not "significant"), and total=10 is
  "significant" (not "subclinical") — the >= semantics put tie-breakers at
  the more severe band.
"""

from __future__ import annotations

import pytest

from discipline.psychometric.scoring.wsas import (
    ITEM_MAX,
    ITEM_MIN,
    WSAS_SEVERITY_THRESHOLDS,
    InvalidResponseError,
    _band_for_total,
    _validate_item,
)


# ---------------------------------------------------------------------------
# _validate_item — accepted inputs (0-8 range)
# ---------------------------------------------------------------------------


class TestValidateItemWsasAccepted:
    def test_zero_accepted(self) -> None:
        assert _validate_item(1, 0) == 0

    def test_eight_accepted(self) -> None:
        assert _validate_item(1, 8) == 8

    def test_four_accepted(self) -> None:
        assert _validate_item(1, 4) == 4

    def test_returns_value_unchanged(self) -> None:
        for v in range(9):
            assert _validate_item(1, v) == v

    def test_item_max_is_8(self) -> None:
        assert ITEM_MAX == 8

    def test_item_min_is_0(self) -> None:
        assert ITEM_MIN == 0


class TestValidateItemWsasBoolRejection:
    def test_true_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_item(1, True)

    def test_false_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_item(1, False)


class TestValidateItemWsasRangeRejection:
    def test_nine_raises(self) -> None:
        # 9 is explicitly out of range per WSAS 0-8 Likert
        with pytest.raises(InvalidResponseError):
            _validate_item(1, 9)

    def test_minus_1_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_item(1, -1)

    def test_100_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_item(1, 100)

    def test_error_mentions_item_index(self) -> None:
        with pytest.raises(InvalidResponseError, match="3"):
            _validate_item(3, 99)


class TestValidateItemWsasTypeRejection:
    def test_string_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_item(1, "5")

    def test_none_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_item(1, None)

    def test_float_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_item(1, 4.0)


# ---------------------------------------------------------------------------
# _band_for_total — Mundt 2002 descending-threshold classification
# Cut-points: ≥20=severe, ≥10=significant, ≥0=subclinical
# ---------------------------------------------------------------------------


class TestBandForTotal:
    def test_score_0_is_subclinical(self) -> None:
        assert _band_for_total(0) == "subclinical"

    def test_score_9_is_subclinical(self) -> None:
        assert _band_for_total(9) == "subclinical"

    def test_score_10_is_significant(self) -> None:
        # Boundary: 10 is "significant" not "subclinical"
        assert _band_for_total(10) == "significant"

    def test_score_19_is_significant(self) -> None:
        assert _band_for_total(19) == "significant"

    def test_score_20_is_severe(self) -> None:
        # Boundary: 20 is "severe" not "significant"
        assert _band_for_total(20) == "severe"

    def test_score_40_is_severe(self) -> None:
        # 40 is maximum (5 items × 8 = 40)
        assert _band_for_total(40) == "severe"

    def test_boundary_9_to_10(self) -> None:
        assert _band_for_total(9) != _band_for_total(10)

    def test_boundary_19_to_20(self) -> None:
        assert _band_for_total(19) != _band_for_total(20)

    def test_descending_table_structure(self) -> None:
        # WSAS thresholds are ordered high→low (unlike HADS ascending ≤ tables)
        thresholds = [t for t, _ in WSAS_SEVERITY_THRESHOLDS]
        assert thresholds == sorted(thresholds, reverse=True)

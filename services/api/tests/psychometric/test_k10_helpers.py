"""Unit tests for _validate_item() and _band_for_total() pure helpers in
discipline.psychometric.scoring.k10.

_validate_item(index_1, value) → int
  K-10 uses a 1-5 Likert ("none of the time" … "all of the time") — this is
  the FIRST instrument in the package with ITEM_MIN = 1 (all others start at
  0).  The minimum possible total is therefore 10 (not 0), which is load-
  bearing for band interpretation.  Bool guard applies; 0 is out of range.

_band_for_total(total) → Severity
  Same descending-threshold table pattern as WSAS.  Andrews & Slade 2001
  cut-points: ≥30 → "very_high", ≥25 → "high", ≥20 → "moderate", ≥10 → "low".
  Four-band scheme (vs WSAS's three, HADS/DASS-21's five).
"""

from __future__ import annotations

import pytest

from discipline.psychometric.scoring.k10 import (
    ITEM_MAX,
    ITEM_MIN,
    K10_SEVERITY_THRESHOLDS,
    InvalidResponseError,
    _band_for_total,
    _validate_item,
)


# ---------------------------------------------------------------------------
# _validate_item — accepted inputs (1-5 range; ITEM_MIN = 1)
# ---------------------------------------------------------------------------


class TestValidateItemK10Accepted:
    def test_one_accepted(self) -> None:
        assert _validate_item(1, 1) == 1

    def test_five_accepted(self) -> None:
        assert _validate_item(1, 5) == 5

    def test_all_valid_range_returned_unchanged(self) -> None:
        for v in range(1, 6):
            assert _validate_item(3, v) == v

    def test_item_min_is_1(self) -> None:
        # Load-bearing: minimum total is 10 × 1 = 10, not 0
        assert ITEM_MIN == 1

    def test_item_max_is_5(self) -> None:
        assert ITEM_MAX == 5


class TestValidateItemK10BoolRejection:
    def test_true_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_item(1, True)

    def test_false_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_item(1, False)


class TestValidateItemK10RangeRejection:
    def test_zero_raises(self) -> None:
        # K-10 starts at 1 — zero is explicitly out of range
        with pytest.raises(InvalidResponseError):
            _validate_item(1, 0)

    def test_six_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_item(1, 6)

    def test_minus_1_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_item(1, -1)

    def test_error_mentions_item_index(self) -> None:
        with pytest.raises(InvalidResponseError, match="7"):
            _validate_item(7, 99)


class TestValidateItemK10TypeRejection:
    def test_string_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_item(1, "3")

    def test_none_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_item(1, None)

    def test_float_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_item(1, 3.0)


# ---------------------------------------------------------------------------
# _band_for_total — Andrews & Slade 2001 four-band classifier
# Cut-points: ≥30=very_high, ≥25=high, ≥20=moderate, ≥10=low
# ---------------------------------------------------------------------------


class TestBandForTotalK10:
    def test_score_10_is_low(self) -> None:
        # 10 is the minimum (10 items × 1)
        assert _band_for_total(10) == "low"

    def test_score_19_is_low(self) -> None:
        assert _band_for_total(19) == "low"

    def test_score_20_is_moderate(self) -> None:
        assert _band_for_total(20) == "moderate"

    def test_score_24_is_moderate(self) -> None:
        assert _band_for_total(24) == "moderate"

    def test_score_25_is_high(self) -> None:
        assert _band_for_total(25) == "high"

    def test_score_29_is_high(self) -> None:
        assert _band_for_total(29) == "high"

    def test_score_30_is_very_high(self) -> None:
        assert _band_for_total(30) == "very_high"

    def test_score_50_is_very_high(self) -> None:
        # 50 is the maximum (10 items × 5)
        assert _band_for_total(50) == "very_high"

    def test_boundary_19_to_20(self) -> None:
        assert _band_for_total(19) != _band_for_total(20)

    def test_boundary_24_to_25(self) -> None:
        assert _band_for_total(24) != _band_for_total(25)

    def test_boundary_29_to_30(self) -> None:
        assert _band_for_total(29) != _band_for_total(30)

    def test_descending_table_structure(self) -> None:
        # Same descending pattern as WSAS
        thresholds = [t for t, _ in K10_SEVERITY_THRESHOLDS]
        assert thresholds == sorted(thresholds, reverse=True)

    def test_four_distinct_bands(self) -> None:
        assert len(K10_SEVERITY_THRESHOLDS) == 4

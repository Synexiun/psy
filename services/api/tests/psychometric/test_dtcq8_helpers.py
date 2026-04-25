"""Unit tests for _validate_item() pure helper in
discipline.psychometric.scoring.dtcq8.

_validate_item(index_1, value) → int
  DTCQ-8 (Drug Taking Confidence Questionnaire, Sklar 1999) uses a 0-100
  percentage scale: "How confident are you that you could resist the urge
  to use?"  This is the widest per-item range in the entire psychometric
  package — all other instruments use ITEM_MAX ≤ 8.

  Validation uses a range check (ITEM_MIN=0 to ITEM_MAX=100).  The bool
  guard applies as everywhere: True/False must be rejected before the int
  isinstance check.

  Boundary semantics:
    0   = "not at all confident" (valid — complete lack of resistance)
    100 = "completely confident" (valid — maximum resistance)
    101 = invalid (no concept of >100% confidence)
"""

from __future__ import annotations

import pytest

from discipline.psychometric.scoring.dtcq8 import (
    ITEM_MAX,
    ITEM_MIN,
    InvalidResponseError,
    _validate_item,
)


class TestDtcq8ItemConstants:
    def test_item_min_is_0(self) -> None:
        assert ITEM_MIN == 0

    def test_item_max_is_100(self) -> None:
        assert ITEM_MAX == 100


class TestValidateItemDtcq8Boundaries:
    def test_zero_accepted(self) -> None:
        assert _validate_item(1, 0) == 0

    def test_100_accepted(self) -> None:
        assert _validate_item(1, 100) == 100

    def test_midpoint_50_accepted(self) -> None:
        assert _validate_item(1, 50) == 50

    def test_returns_value_unchanged(self) -> None:
        for v in (0, 1, 50, 99, 100):
            assert _validate_item(1, v) == v

    def test_101_raises(self) -> None:
        # 101 exceeds the 100% scale — no valid clinical meaning
        with pytest.raises(InvalidResponseError):
            _validate_item(1, 101)

    def test_minus_1_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_item(1, -1)

    def test_error_mentions_item_index(self) -> None:
        with pytest.raises(InvalidResponseError, match="8"):
            _validate_item(8, 200)


class TestValidateItemDtcq8BoolRejection:
    def test_true_raises(self) -> None:
        # True == 1, which is in range, but bool is not int here
        with pytest.raises(InvalidResponseError):
            _validate_item(1, True)

    def test_false_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_item(1, False)


class TestValidateItemDtcq8TypeRejection:
    def test_string_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_item(1, "50")

    def test_none_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_item(1, None)

    def test_float_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_item(1, 50.0)

    def test_float_0_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_item(1, 0.0)

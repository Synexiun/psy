"""Unit tests for _validate_item() pure helper in
discipline.psychometric.scoring.pcptsd5.

_validate_item(index_1, value) → int
  PC-PTSD-5 (Primary Care PTSD Screen for DSM-5, Prins 2016) uses binary
  yes/no scoring: each item is 0 or 1.

  Implementation contrast with ACES:
    PC-PTSD-5 uses a RANGE check (value < ITEM_MIN or value > ITEM_MAX).
    ACES uses an EQUALITY check (value != 0 and value != 1).
    Both produce identical rejection behaviour for integers, but ACES's
    equality check documents the stricter binary-by-design intent.
    PC-PTSD-5's range check reflects binary-by-convention.

  The bool guard applies as everywhere in this package.
  A value of 2 is NOT valid; the instrument has no partial credit.
"""

from __future__ import annotations

import pytest

from discipline.psychometric.scoring.pcptsd5 import (
    ITEM_MAX,
    ITEM_MIN,
    InvalidResponseError,
    _validate_item,
)


class TestPcPtsd5ItemConstants:
    def test_item_min_is_0(self) -> None:
        assert ITEM_MIN == 0

    def test_item_max_is_1(self) -> None:
        assert ITEM_MAX == 1


class TestValidateItemPcPtsd5Accepted:
    def test_zero_accepted(self) -> None:
        assert _validate_item(1, 0) == 0

    def test_one_accepted(self) -> None:
        assert _validate_item(1, 1) == 1

    def test_returns_value_unchanged(self) -> None:
        assert _validate_item(3, 0) == 0
        assert _validate_item(3, 1) == 1


class TestValidateItemPcPtsd5BoolRejection:
    def test_true_raises(self) -> None:
        # bool guard: True == 1 but bool is not int for this contract
        with pytest.raises(InvalidResponseError):
            _validate_item(1, True)

    def test_false_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_item(1, False)


class TestValidateItemPcPtsd5OutOfRange:
    def test_two_raises(self) -> None:
        # 2 is outside the binary range — no partial credit on PC-PTSD-5
        with pytest.raises(InvalidResponseError):
            _validate_item(1, 2)

    def test_minus_1_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_item(1, -1)

    def test_five_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_item(1, 5)

    def test_error_mentions_item_index(self) -> None:
        with pytest.raises(InvalidResponseError, match="5"):
            _validate_item(5, 99)


class TestValidateItemPcPtsd5TypeRejection:
    def test_string_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_item(1, "1")

    def test_none_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_item(1, None)

    def test_float_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_item(1, 0.0)

    def test_float_1_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_item(1, 1.0)

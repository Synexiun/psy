"""Unit tests for _validate_item() pure helper in
discipline.psychometric.scoring.aces.

_validate_item(index_1, value) → int
  ACEs (Adverse Childhood Experiences Scale, Felitti 1998) uses binary
  yes/no scoring: each item is EXACTLY 0 or 1 (not a graded Likert scale).

  Validation uses an exact equality check (``value != 0 and value != 1``),
  not a range check (``ITEM_MIN <= value <= ITEM_MAX``).  This is critical:
  a naive range-check ``[0, 1]`` would also reject values correctly, but the
  intent must be explicit for binary semantics — value 0 and 1 only.

  The same bool-before-int guard applies as all other instruments in this
  package.  A value of 2 is NOT a valid ACE response; it must raise.
"""

from __future__ import annotations

import pytest

from discipline.psychometric.scoring.aces import (
    ITEM_MAX,
    ITEM_MIN,
    InvalidResponseError,
    _validate_item,
)


# ---------------------------------------------------------------------------
# _validate_item — binary (0 or 1 only)
# ---------------------------------------------------------------------------


class TestValidateItemAces:
    def test_zero_accepted(self) -> None:
        assert _validate_item(1, 0) == 0

    def test_one_accepted(self) -> None:
        assert _validate_item(1, 1) == 1

    def test_item_min_is_0(self) -> None:
        assert ITEM_MIN == 0

    def test_item_max_is_1(self) -> None:
        assert ITEM_MAX == 1

    def test_returns_value_unchanged(self) -> None:
        assert _validate_item(5, 0) == 0
        assert _validate_item(5, 1) == 1


class TestValidateItemAcesBoolRejection:
    def test_true_raises(self) -> None:
        # True would pass range check but must be rejected (bool guard)
        with pytest.raises(InvalidResponseError):
            _validate_item(1, True)

    def test_false_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_item(1, False)


class TestValidateItemAcesBinaryExactCheck:
    def test_two_raises(self) -> None:
        # Exact equality check: 2 is NOT a valid binary response
        with pytest.raises(InvalidResponseError):
            _validate_item(1, 2)

    def test_three_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_item(1, 3)

    def test_minus_1_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_item(1, -1)

    def test_10_raises(self) -> None:
        # ACE total is 0-10 but individual items are 0 or 1
        with pytest.raises(InvalidResponseError):
            _validate_item(1, 10)

    def test_error_mentions_item_index(self) -> None:
        with pytest.raises(InvalidResponseError, match="7"):
            _validate_item(7, 5)


class TestValidateItemAcesTypeRejection:
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

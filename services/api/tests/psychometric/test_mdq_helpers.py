"""Unit tests for _validate_concurrent() and _validate_impairment() pure
helpers in discipline.psychometric.scoring.mdq.

_validate_concurrent(value) → bool
  MDQ Part 2 concurrent_symptoms flag MUST be strictly bool.
  This is the inverted pattern from _validate_item — booleans are
  REQUIRED here (Part 2 is a yes/no instrument question); integers 0/1
  are REJECTED to keep the wire-format contract crisp.

_validate_impairment(value) → ImpairmentLevel
  MDQ Part 3 functional_impairment must be one of the four published
  categorical labels: "none" | "minor" | "moderate" | "serious"
  (MDQ_IMPAIRMENT_LEVELS frozenset).  Non-strings and unknown strings
  both raise InvalidResponseError.

_validate_item(index_1, value) → int  [MDQ-specific variant]
  Like HADS _validate_item but restricted to 0-1 range (binary yes/no).
  Bool is rejected (same guard as HADS).
"""

from __future__ import annotations

import pytest

from discipline.psychometric.scoring.mdq import (
    MDQ_IMPAIRMENT_LEVELS,
    InvalidResponseError,
    _validate_concurrent,
    _validate_impairment,
    _validate_item,
)


# ---------------------------------------------------------------------------
# _validate_concurrent — accepted inputs (strictly bool required)
# ---------------------------------------------------------------------------


class TestValidateConcurrentAccepted:
    def test_true_accepted(self) -> None:
        assert _validate_concurrent(True) is True

    def test_false_accepted(self) -> None:
        assert _validate_concurrent(False) is False

    def test_returns_exact_bool_value(self) -> None:
        assert type(_validate_concurrent(True)) is bool
        assert type(_validate_concurrent(False)) is bool


# ---------------------------------------------------------------------------
# _validate_concurrent — int rejection (inverted from _validate_item pattern)
# ---------------------------------------------------------------------------


class TestValidateConcurrentIntRejection:
    def test_int_1_raises(self) -> None:
        # int(1) is truthy but not bool — must be rejected to keep wire contract
        with pytest.raises(InvalidResponseError):
            _validate_concurrent(1)

    def test_int_0_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_concurrent(0)

    def test_int_minus_1_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_concurrent(-1)

    def test_large_int_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_concurrent(42)


# ---------------------------------------------------------------------------
# _validate_concurrent — other type rejection
# ---------------------------------------------------------------------------


class TestValidateConcurrentTypeRejection:
    def test_none_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_concurrent(None)

    def test_string_yes_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_concurrent("yes")

    def test_string_true_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_concurrent("true")

    def test_string_one_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_concurrent("1")

    def test_float_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_concurrent(1.0)

    def test_list_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_concurrent([True])

    def test_dict_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_concurrent({"value": True})

    def test_error_is_invalid_response_error(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_concurrent(0)

    def test_error_mentions_bool(self) -> None:
        with pytest.raises(InvalidResponseError, match="bool"):
            _validate_concurrent(0)


# ---------------------------------------------------------------------------
# _validate_impairment — accepted inputs (four MDQ categorical labels)
# ---------------------------------------------------------------------------


class TestValidateImpairmentAccepted:
    def test_none_label_accepted(self) -> None:
        assert _validate_impairment("none") == "none"

    def test_minor_label_accepted(self) -> None:
        assert _validate_impairment("minor") == "minor"

    def test_moderate_label_accepted(self) -> None:
        assert _validate_impairment("moderate") == "moderate"

    def test_serious_label_accepted(self) -> None:
        assert _validate_impairment("serious") == "serious"

    def test_returns_exact_value_unchanged(self) -> None:
        for label in MDQ_IMPAIRMENT_LEVELS:
            assert _validate_impairment(label) == label

    def test_all_four_levels_in_impairment_levels_frozenset(self) -> None:
        assert MDQ_IMPAIRMENT_LEVELS == {"none", "minor", "moderate", "serious"}


# ---------------------------------------------------------------------------
# _validate_impairment — unknown string rejection
# ---------------------------------------------------------------------------


class TestValidateImpairmentUnknownString:
    def test_empty_string_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_impairment("")

    def test_uppercase_none_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_impairment("None")

    def test_uppercase_serious_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_impairment("SERIOUS")

    def test_unknown_label_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_impairment("severe")

    def test_error_mentions_valid_options(self) -> None:
        # Error message must include sorted valid options per implementation
        with pytest.raises(InvalidResponseError, match="minor"):
            _validate_impairment("extreme")

    def test_partial_match_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_impairment("mod")


# ---------------------------------------------------------------------------
# _validate_impairment — type rejection
# ---------------------------------------------------------------------------


class TestValidateImpairmentTypeRejection:
    def test_none_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_impairment(None)

    def test_int_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_impairment(0)

    def test_bool_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_impairment(True)

    def test_list_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_impairment(["none"])

    def test_float_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_impairment(1.0)

    def test_error_is_invalid_response_error(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_impairment(None)


# ---------------------------------------------------------------------------
# _validate_item — MDQ binary items (0 or 1 only)
# ---------------------------------------------------------------------------


class TestValidateItemMdqAccepted:
    def test_zero_accepted(self) -> None:
        assert _validate_item(1, 0) == 0

    def test_one_accepted(self) -> None:
        assert _validate_item(1, 1) == 1

    def test_returns_value_unchanged(self) -> None:
        assert _validate_item(5, 0) == 0
        assert _validate_item(5, 1) == 1


class TestValidateItemMdqRejected:
    def test_two_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_item(1, 2)

    def test_three_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_item(1, 3)

    def test_minus_one_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_item(1, -1)

    def test_true_raises(self) -> None:
        # bool subtype guard applies here too
        with pytest.raises(InvalidResponseError):
            _validate_item(1, True)

    def test_false_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_item(1, False)

    def test_string_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_item(1, "1")

    def test_none_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_item(1, None)

    def test_error_mentions_item_index(self) -> None:
        with pytest.raises(InvalidResponseError, match="3"):
            _validate_item(3, 99)

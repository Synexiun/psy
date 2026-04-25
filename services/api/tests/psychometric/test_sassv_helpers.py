"""Unit tests for _cutoff_for() and _validate_item() pure helpers in
discipline.psychometric.scoring.sassv.

_cutoff_for(sex) → int
  Maps sex key to the Kwon 2013 SAS-SV positive-screen cutoff:
    "male" → 31, "female" → 33, "unspecified" → 31 (conservative fallback).
  "unspecified" uses the male (LOWER) cutoff for maximum sensitivity —
  same safety-conservatism policy as AUDIT-C and SDS unspecified defaults.

_validate_item(index_1, value) → int
  SAS-SV uses a 1-6 Likert — ITEM_MAX = 6 is the widest scale in the
  psychometric package (prior maximum was WSAS's 0-8, but on a different
  endpoint; this is the first 1-6 scale).
"""

from __future__ import annotations

import pytest

from discipline.psychometric.scoring.sassv import (
    ITEM_MAX,
    ITEM_MIN,
    SAS_SV_CUTOFF_FEMALE,
    SAS_SV_CUTOFF_MALE,
    SAS_SV_CUTOFF_UNSPECIFIED,
    InvalidResponseError,
    _cutoff_for,
    _validate_item,
)


# ---------------------------------------------------------------------------
# _cutoff_for — Kwon 2013 sex-stratified cutoffs
# ---------------------------------------------------------------------------


class TestCutoffForSasSv:
    def test_male_cutoff(self) -> None:
        assert _cutoff_for("male") == SAS_SV_CUTOFF_MALE

    def test_female_cutoff(self) -> None:
        assert _cutoff_for("female") == SAS_SV_CUTOFF_FEMALE

    def test_unspecified_cutoff(self) -> None:
        assert _cutoff_for("unspecified") == SAS_SV_CUTOFF_UNSPECIFIED

    def test_unspecified_equals_male_conservative_fallback(self) -> None:
        # Male cutoff (31) < female cutoff (33) → more sensitive
        assert SAS_SV_CUTOFF_UNSPECIFIED == SAS_SV_CUTOFF_MALE

    def test_female_cutoff_higher_than_male(self) -> None:
        # Kwon 2013 ROC: female threshold is higher
        assert SAS_SV_CUTOFF_FEMALE > SAS_SV_CUTOFF_MALE

    def test_unspecified_is_lower_of_two(self) -> None:
        # Safety-conservatism: use the more sensitive (lower) cutoff
        assert SAS_SV_CUTOFF_UNSPECIFIED == min(SAS_SV_CUTOFF_MALE, SAS_SV_CUTOFF_FEMALE)

    def test_male_cutoff_is_31(self) -> None:
        assert SAS_SV_CUTOFF_MALE == 31

    def test_female_cutoff_is_33(self) -> None:
        assert SAS_SV_CUTOFF_FEMALE == 33

    def test_returns_int(self) -> None:
        for sex in ("male", "female", "unspecified"):
            assert isinstance(_cutoff_for(sex), int)


# ---------------------------------------------------------------------------
# _validate_item — 1-6 Likert (novel ITEM_MAX = 6)
# ---------------------------------------------------------------------------


class TestValidateItemSasSv:
    def test_one_accepted(self) -> None:
        assert _validate_item(1, 1) == 1

    def test_six_accepted(self) -> None:
        assert _validate_item(1, 6) == 6

    def test_all_valid_range_unchanged(self) -> None:
        for v in range(1, 7):
            assert _validate_item(5, v) == v

    def test_item_max_is_6(self) -> None:
        assert ITEM_MAX == 6

    def test_item_min_is_1(self) -> None:
        assert ITEM_MIN == 1

    def test_true_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_item(1, True)

    def test_false_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_item(1, False)

    def test_zero_raises(self) -> None:
        # Scale starts at 1
        with pytest.raises(InvalidResponseError):
            _validate_item(1, 0)

    def test_seven_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_item(1, 7)

    def test_error_mentions_item_index(self) -> None:
        with pytest.raises(InvalidResponseError, match="4"):
            _validate_item(4, 99)

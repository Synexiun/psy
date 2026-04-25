"""Unit tests for _dichotomize() and _validate_item() pure helpers in
discipline.psychometric.scoring.shaps.

_dichotomize(raw) → int
  Converts a 1-4 SHAPS response to a binary 0/1 anhedonia indicator per
  Snaith 1995.  Likert 1 (Strongly Agree) / 2 (Agree) → 0 (hedonic capacity
  present).  Likert 3 (Disagree) / 4 (Strongly Disagree) → 1 (anhedonic).
  Threshold is SHAPS_DICHOTOMIZE_THRESHOLD_INCLUSIVE = 2.  This is the only
  helper in the psychometric package that maps a graded scale to binary.

_validate_item(index_1, value) → int
  SHAPS uses a 1-4 Likert.  Bool rejection applies.
"""

from __future__ import annotations

import pytest

from discipline.psychometric.scoring.shaps import (
    ITEM_MAX,
    ITEM_MIN,
    SHAPS_DICHOTOMIZE_THRESHOLD_INCLUSIVE,
    InvalidResponseError,
    _dichotomize,
    _validate_item,
)


# ---------------------------------------------------------------------------
# _dichotomize — Snaith 1995 binary conversion
# ≤2 (agree/strongly agree) → 0 (hedonic present)
# ≥3 (disagree/strongly disagree) → 1 (anhedonic)
# ---------------------------------------------------------------------------


class TestDichotomize:
    def test_one_is_zero(self) -> None:
        # Strongly Agree = hedonic capacity present
        assert _dichotomize(1) == 0

    def test_two_is_zero(self) -> None:
        # Agree = hedonic capacity present (threshold inclusive)
        assert _dichotomize(2) == 0

    def test_three_is_one(self) -> None:
        # Disagree = anhedonic
        assert _dichotomize(3) == 1

    def test_four_is_one(self) -> None:
        # Strongly Disagree = anhedonic
        assert _dichotomize(4) == 1

    def test_threshold_is_2(self) -> None:
        assert SHAPS_DICHOTOMIZE_THRESHOLD_INCLUSIVE == 2

    def test_returns_only_0_or_1(self) -> None:
        for v in range(1, 5):
            result = _dichotomize(v)
            assert result in (0, 1)

    def test_boundary_at_threshold(self) -> None:
        # At threshold: 0; above threshold: 1
        assert _dichotomize(SHAPS_DICHOTOMIZE_THRESHOLD_INCLUSIVE) == 0
        assert _dichotomize(SHAPS_DICHOTOMIZE_THRESHOLD_INCLUSIVE + 1) == 1

    def test_max_score_across_14_items(self) -> None:
        # All 14 items dichotomized to 1 → total = 14
        assert sum(_dichotomize(4) for _ in range(14)) == 14

    def test_min_score_across_14_items(self) -> None:
        # All 14 items dichotomized to 0 → total = 0
        assert sum(_dichotomize(1) for _ in range(14)) == 0


# ---------------------------------------------------------------------------
# _validate_item — 1-4 Likert
# ---------------------------------------------------------------------------


class TestValidateItemShaps:
    def test_one_accepted(self) -> None:
        assert _validate_item(1, 1) == 1

    def test_four_accepted(self) -> None:
        assert _validate_item(1, 4) == 4

    def test_true_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_item(1, True)

    def test_zero_raises(self) -> None:
        # SHAPS starts at 1
        with pytest.raises(InvalidResponseError):
            _validate_item(1, 0)

    def test_five_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_item(1, 5)

    def test_error_mentions_item_index(self) -> None:
        with pytest.raises(InvalidResponseError, match="6"):
            _validate_item(6, 99)

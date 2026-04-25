"""Unit tests for _classify() and _validate_item() pure helpers in
discipline.psychometric.scoring.pgsi.

_classify(total) → Severity
  PGSI uses an ascending ≤ threshold table (same pattern as HADS).
  Ferris & Wynne 2001 four-band scheme:
    =0 → "non_problem", ≤2 → "low_risk", ≤7 → "moderate_risk",
    ≤27 → "problem_gambler" (maximum 27 = 9 items × 3).
  The threshold table starts at (0, "non_problem") — the only instrument
  in this package with a zero-value first threshold.

_validate_item(index_1, value) → int
  0-3 Likert (same range as HADS).  Bool guard applies.
"""

from __future__ import annotations

import pytest

from discipline.psychometric.scoring.pgsi import (
    ITEM_MAX,
    ITEM_MIN,
    PGSI_SEVERITY_THRESHOLDS,
    InvalidResponseError,
    _classify,
    _validate_item,
)


# ---------------------------------------------------------------------------
# _classify — Ferris & Wynne 2001 four-band gambling classifier
# ---------------------------------------------------------------------------


class TestClassifyPgsi:
    def test_score_0_is_non_problem(self) -> None:
        assert _classify(0) == "non_problem"

    def test_score_1_is_low_risk(self) -> None:
        assert _classify(1) == "low_risk"

    def test_score_2_is_low_risk(self) -> None:
        assert _classify(2) == "low_risk"

    def test_score_3_is_moderate_risk(self) -> None:
        assert _classify(3) == "moderate_risk"

    def test_score_7_is_moderate_risk(self) -> None:
        assert _classify(7) == "moderate_risk"

    def test_score_8_is_problem_gambler(self) -> None:
        assert _classify(8) == "problem_gambler"

    def test_score_27_is_problem_gambler(self) -> None:
        # 27 is the maximum (9 items × 3)
        assert _classify(27) == "problem_gambler"

    def test_zero_threshold_entry(self) -> None:
        # First threshold is (0, "non_problem") — unique in the package
        first_threshold, first_label = PGSI_SEVERITY_THRESHOLDS[0]
        assert first_threshold == 0
        assert first_label == "non_problem"

    def test_boundary_0_to_1(self) -> None:
        assert _classify(0) != _classify(1)

    def test_boundary_2_to_3(self) -> None:
        assert _classify(2) != _classify(3)

    def test_boundary_7_to_8(self) -> None:
        assert _classify(7) != _classify(8)


# ---------------------------------------------------------------------------
# _validate_item — 0-3 Likert
# ---------------------------------------------------------------------------


class TestValidateItemPgsi:
    def test_zero_accepted(self) -> None:
        assert _validate_item(1, 0) == 0

    def test_three_accepted(self) -> None:
        assert _validate_item(1, 3) == 3

    def test_true_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_item(1, True)

    def test_four_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_item(1, 4)

    def test_minus_1_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_item(1, -1)

    def test_error_mentions_item_index(self) -> None:
        with pytest.raises(InvalidResponseError, match="9"):
            _validate_item(9, 99)

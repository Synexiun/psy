"""Unit tests for _classify() and _validate_item() pure helpers in
discipline.psychometric.scoring.audit.

_classify(total) → Band
  AUDIT-full uses Saunders 1993 / WHO 2001 four-zone severity:
    ≤7  → "low_risk"
    ≤15 → "hazardous"
    ≤19 → "harmful"
    >19 → "possible_dependence"   (no upper bound — cascade last branch)
  This is an if-cascade pattern (not a threshold tuple), which is also used
  by PSS-10.  The maximum AUDIT total is 40 (10 items × 4).

_validate_item(index_1, value) → int
  0-4 Likert but NOTE: items 1-8 use 0/1/2/3/4 while items 9 and 10
  have specialized 0/2/4 response scales.  The _validate_item helper
  validates the same 0-4 range regardless of position — the unusual
  item scales are a clinical concern, not a validation concern.
"""

from __future__ import annotations

import pytest

from discipline.psychometric.scoring.audit import (
    AUDIT_HARMFUL_UPPER,
    AUDIT_HAZARDOUS_UPPER,
    AUDIT_LOW_RISK_UPPER,
    ITEM_MAX,
    ITEM_MIN,
    InvalidResponseError,
    _classify,
    _validate_item,
)


# ---------------------------------------------------------------------------
# _classify — Saunders 1993 / WHO 2001 four-zone classifier
# Cut-points: ≤7=low_risk, ≤15=hazardous, ≤19=harmful, >19=possible_dependence
# ---------------------------------------------------------------------------


class TestClassifyAudit:
    def test_score_0_is_low_risk(self) -> None:
        assert _classify(0) == "low_risk"

    def test_score_7_is_low_risk(self) -> None:
        assert _classify(AUDIT_LOW_RISK_UPPER) == "low_risk"

    def test_score_8_is_hazardous(self) -> None:
        assert _classify(AUDIT_LOW_RISK_UPPER + 1) == "hazardous"

    def test_score_15_is_hazardous(self) -> None:
        assert _classify(AUDIT_HAZARDOUS_UPPER) == "hazardous"

    def test_score_16_is_harmful(self) -> None:
        assert _classify(AUDIT_HAZARDOUS_UPPER + 1) == "harmful"

    def test_score_19_is_harmful(self) -> None:
        assert _classify(AUDIT_HARMFUL_UPPER) == "harmful"

    def test_score_20_is_possible_dependence(self) -> None:
        assert _classify(AUDIT_HARMFUL_UPPER + 1) == "possible_dependence"

    def test_score_40_is_possible_dependence(self) -> None:
        # 40 is the maximum (10 items × 4)
        assert _classify(40) == "possible_dependence"

    def test_boundary_7_to_8(self) -> None:
        assert _classify(7) != _classify(8)

    def test_boundary_15_to_16(self) -> None:
        assert _classify(15) != _classify(16)

    def test_boundary_19_to_20(self) -> None:
        assert _classify(19) != _classify(20)

    def test_constants_match_saunders_1993(self) -> None:
        assert AUDIT_LOW_RISK_UPPER == 7
        assert AUDIT_HAZARDOUS_UPPER == 15
        assert AUDIT_HARMFUL_UPPER == 19


# ---------------------------------------------------------------------------
# _validate_item — 0-4 range
# ---------------------------------------------------------------------------


class TestValidateItemAudit:
    def test_zero_accepted(self) -> None:
        assert _validate_item(1, 0) == 0

    def test_four_accepted(self) -> None:
        assert _validate_item(1, 4) == 4

    def test_true_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_item(1, True)

    def test_five_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_item(1, 5)

    def test_minus_1_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            _validate_item(1, -1)

    def test_error_mentions_item_index(self) -> None:
        with pytest.raises(InvalidResponseError, match="10"):
            _validate_item(10, 99)

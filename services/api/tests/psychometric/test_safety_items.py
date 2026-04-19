"""PHQ-9 item-9 → T3 safety-routing tests.

The rule is absolute: any positive value on PHQ-9 item 9 triggers T3.  No
threshold tuning, no calibration.  See Docs/Whitepapers/04_Safety_Framework.md
§Safety items.
"""

from __future__ import annotations

import pytest

from discipline.psychometric.safety_items import SafetyRoutingSignal, evaluate_phq9
from discipline.psychometric.scoring.phq9 import ITEM_COUNT, PHQ9_SAFETY_ITEM_INDEX, score_phq9


def test_item9_zero_returns_none_signal() -> None:
    result = score_phq9([0] * ITEM_COUNT)
    assert evaluate_phq9(result) is None


@pytest.mark.parametrize("item9_value", [1, 2, 3])
def test_any_positive_item9_triggers_t3(item9_value: int) -> None:
    items = [0] * ITEM_COUNT
    items[PHQ9_SAFETY_ITEM_INDEX] = item9_value
    result = score_phq9(items)

    signal = evaluate_phq9(result)

    assert signal is not None
    assert isinstance(signal, SafetyRoutingSignal)
    assert signal.requires_t3 is True
    assert signal.reason == "phq9_item9_positive"
    assert signal.source == "phq9.item9"


def test_t3_signal_fires_even_when_total_is_low() -> None:
    """Zero on all items except item 9 = 1 → total 1, severity 'none',
    but T3 still triggers.  The safety rule is decoupled from severity."""
    items = [0] * ITEM_COUNT
    items[PHQ9_SAFETY_ITEM_INDEX] = 1
    result = score_phq9(items)
    assert result.total == 1
    assert result.severity == "none"

    signal = evaluate_phq9(result)
    assert signal is not None
    assert signal.requires_t3 is True


def test_signal_is_frozen() -> None:
    items = [0] * ITEM_COUNT
    items[PHQ9_SAFETY_ITEM_INDEX] = 2
    signal = evaluate_phq9(score_phq9(items))
    assert signal is not None
    with pytest.raises(AttributeError):
        signal.requires_t3 = False  # type: ignore[misc]

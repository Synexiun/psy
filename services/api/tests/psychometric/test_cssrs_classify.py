"""Unit tests for _classify() pure helper in discipline.psychometric.scoring.cssrs.

_classify(items, *, behavior_within_3mo) → (Risk, bool, tuple[int, ...])
  Posner 2011 triage rules.  Returns (risk_band, requires_t3, triggering_items).

  Item index constants (zero-indexed):
    ITEM_PASSIVE_IDEATION = 0   (item 1 in 1-indexed clinical language)
    ITEM_ACTIVE_IDEATION  = 1   (item 2)
    ITEM_METHOD           = 2   (item 3)
    ITEM_INTENT           = 3   (item 4)
    ITEM_PLAN             = 4   (item 5)
    ITEM_PAST_BEHAVIOR    = 5   (item 6)

  Precedence (highest wins):
    1. Item 4 (INTENT) positive         → acute, requires_t3=True
    2. Item 5 (PLAN) positive           → acute, requires_t3=True
    3. Item 6 (PAST_BEHAVIOR) + behavior_within_3mo=True → acute, requires_t3=True
    4. Item 3 (METHOD) positive         → moderate, requires_t3=False
    5. Item 6 (PAST_BEHAVIOR) + behavior_within_3mo=False → moderate (historic)
    6. Items 1-2 (PASSIVE/ACTIVE) only  → low, requires_t3=False
    7. Nothing positive                 → none, requires_t3=False, ()

  Critical safety contract: requires_t3=True is ONLY set for the "acute" band.
  triggering_items uses 1-indexed item numbers (ITEM_n + 1) matching clinical language.
"""

from __future__ import annotations

import pytest

from discipline.psychometric.scoring.cssrs import (
    ITEM_ACTIVE_IDEATION,
    ITEM_INTENT,
    ITEM_METHOD,
    ITEM_PASSIVE_IDEATION,
    ITEM_PLAN,
    ITEM_PAST_BEHAVIOR,
    _classify,
)

# ---------------------------------------------------------------------------
# Helpers to build 6-item bool tuples
# ---------------------------------------------------------------------------

_NONE: tuple[bool, ...] = (False,) * 6


def _items(**kwargs: bool) -> tuple[bool, ...]:
    """Build a 6-item bool tuple with selected indices set True.
    kwargs keys: passive, active, method, intent, plan, behavior.
    """
    idx = {
        "passive": ITEM_PASSIVE_IDEATION,
        "active": ITEM_ACTIVE_IDEATION,
        "method": ITEM_METHOD,
        "intent": ITEM_INTENT,
        "plan": ITEM_PLAN,
        "behavior": ITEM_PAST_BEHAVIOR,
    }
    result = list(_NONE)
    for name, val in kwargs.items():
        result[idx[name]] = val
    return tuple(result)


# ---------------------------------------------------------------------------
# Baseline — all negative
# ---------------------------------------------------------------------------


class TestClassifyCssrsNone:
    def test_all_false_returns_none(self) -> None:
        risk, t3, triggering = _classify(_NONE, behavior_within_3mo=False)
        assert risk == "none"

    def test_all_false_no_t3(self) -> None:
        _, t3, _ = _classify(_NONE, behavior_within_3mo=False)
        assert t3 is False

    def test_all_false_empty_triggering(self) -> None:
        _, _, triggering = _classify(_NONE, behavior_within_3mo=False)
        assert triggering == ()

    def test_behavior_within_3mo_false_all_negative_is_none(self) -> None:
        # behavior_within_3mo=True with no positive items still → none
        risk, _, _ = _classify(_NONE, behavior_within_3mo=True)
        assert risk == "none"


# ---------------------------------------------------------------------------
# Low risk — passive or active ideation only
# ---------------------------------------------------------------------------


class TestClassifyCssrsLow:
    def test_passive_ideation_only_is_low(self) -> None:
        risk, _, _ = _classify(_items(passive=True), behavior_within_3mo=False)
        assert risk == "low"

    def test_active_ideation_only_is_low(self) -> None:
        risk, _, _ = _classify(_items(active=True), behavior_within_3mo=False)
        assert risk == "low"

    def test_passive_and_active_both_positive_is_low(self) -> None:
        risk, _, _ = _classify(
            _items(passive=True, active=True), behavior_within_3mo=False
        )
        assert risk == "low"

    def test_low_does_not_require_t3(self) -> None:
        _, t3, _ = _classify(_items(passive=True), behavior_within_3mo=False)
        assert t3 is False

    def test_passive_triggering_is_item_1(self) -> None:
        _, _, triggering = _classify(_items(passive=True), behavior_within_3mo=False)
        assert ITEM_PASSIVE_IDEATION + 1 in triggering

    def test_active_triggering_is_item_2(self) -> None:
        _, _, triggering = _classify(_items(active=True), behavior_within_3mo=False)
        assert ITEM_ACTIVE_IDEATION + 1 in triggering

    def test_both_ideation_items_in_triggering(self) -> None:
        _, _, triggering = _classify(
            _items(passive=True, active=True), behavior_within_3mo=False
        )
        assert ITEM_PASSIVE_IDEATION + 1 in triggering
        assert ITEM_ACTIVE_IDEATION + 1 in triggering


# ---------------------------------------------------------------------------
# Moderate risk — method or historic past behavior
# ---------------------------------------------------------------------------


class TestClassifyCssrsModerate:
    def test_method_only_is_moderate(self) -> None:
        risk, _, _ = _classify(_items(method=True), behavior_within_3mo=False)
        assert risk == "moderate"

    def test_past_behavior_historic_is_moderate(self) -> None:
        # behavior_within_3mo=False → historic, not acute
        risk, _, _ = _classify(_items(behavior=True), behavior_within_3mo=False)
        assert risk == "moderate"

    def test_moderate_does_not_require_t3(self) -> None:
        _, t3, _ = _classify(_items(method=True), behavior_within_3mo=False)
        assert t3 is False

    def test_method_triggering_is_item_3(self) -> None:
        _, _, triggering = _classify(_items(method=True), behavior_within_3mo=False)
        assert ITEM_METHOD + 1 in triggering

    def test_past_behavior_historic_triggering_is_item_6(self) -> None:
        _, _, triggering = _classify(_items(behavior=True), behavior_within_3mo=False)
        assert ITEM_PAST_BEHAVIOR + 1 in triggering

    def test_method_and_behavior_historic_both_in_triggering(self) -> None:
        _, _, triggering = _classify(
            _items(method=True, behavior=True), behavior_within_3mo=False
        )
        assert ITEM_METHOD + 1 in triggering
        assert ITEM_PAST_BEHAVIOR + 1 in triggering

    def test_passive_plus_method_is_moderate_not_low(self) -> None:
        # Method outranks ideation-only
        risk, _, _ = _classify(
            _items(passive=True, method=True), behavior_within_3mo=False
        )
        assert risk == "moderate"


# ---------------------------------------------------------------------------
# Acute risk — intent, plan, or recent past behavior
# ---------------------------------------------------------------------------


class TestClassifyCssrsAcute:
    def test_intent_alone_is_acute(self) -> None:
        risk, _, _ = _classify(_items(intent=True), behavior_within_3mo=False)
        assert risk == "acute"

    def test_plan_alone_is_acute(self) -> None:
        risk, _, _ = _classify(_items(plan=True), behavior_within_3mo=False)
        assert risk == "acute"

    def test_past_behavior_recent_is_acute(self) -> None:
        # behavior_within_3mo=True promotes item 6 from moderate to acute
        risk, _, _ = _classify(_items(behavior=True), behavior_within_3mo=True)
        assert risk == "acute"

    def test_acute_requires_t3(self) -> None:
        _, t3, _ = _classify(_items(intent=True), behavior_within_3mo=False)
        assert t3 is True

    def test_plan_requires_t3(self) -> None:
        _, t3, _ = _classify(_items(plan=True), behavior_within_3mo=False)
        assert t3 is True

    def test_recent_behavior_requires_t3(self) -> None:
        _, t3, _ = _classify(_items(behavior=True), behavior_within_3mo=True)
        assert t3 is True

    def test_intent_triggering_is_item_4(self) -> None:
        _, _, triggering = _classify(_items(intent=True), behavior_within_3mo=False)
        assert ITEM_INTENT + 1 in triggering

    def test_plan_triggering_is_item_5(self) -> None:
        _, _, triggering = _classify(_items(plan=True), behavior_within_3mo=False)
        assert ITEM_PLAN + 1 in triggering

    def test_recent_behavior_triggering_is_item_6(self) -> None:
        _, _, triggering = _classify(_items(behavior=True), behavior_within_3mo=True)
        assert ITEM_PAST_BEHAVIOR + 1 in triggering

    def test_intent_and_plan_both_in_triggering(self) -> None:
        _, _, triggering = _classify(
            _items(intent=True, plan=True), behavior_within_3mo=False
        )
        assert ITEM_INTENT + 1 in triggering
        assert ITEM_PLAN + 1 in triggering


# ---------------------------------------------------------------------------
# Precedence — higher rule always wins
# ---------------------------------------------------------------------------


class TestClassifyCssrsPrecedence:
    def test_intent_beats_ideation_only(self) -> None:
        # Items 1+2+4 present — acute outranks low
        risk, t3, _ = _classify(
            _items(passive=True, active=True, intent=True), behavior_within_3mo=False
        )
        assert risk == "acute"
        assert t3 is True

    def test_intent_beats_method(self) -> None:
        # Items 3+4 present — acute outranks moderate
        risk, _, _ = _classify(
            _items(method=True, intent=True), behavior_within_3mo=False
        )
        assert risk == "acute"

    def test_plan_beats_method(self) -> None:
        risk, _, _ = _classify(
            _items(method=True, plan=True), behavior_within_3mo=False
        )
        assert risk == "acute"

    def test_recent_behavior_beats_method(self) -> None:
        risk, _, _ = _classify(
            _items(method=True, behavior=True), behavior_within_3mo=True
        )
        assert risk == "acute"

    def test_method_beats_ideation_only(self) -> None:
        risk, _, _ = _classify(
            _items(passive=True, active=True, method=True), behavior_within_3mo=False
        )
        assert risk == "moderate"

    def test_historic_behavior_beats_ideation_only(self) -> None:
        risk, _, _ = _classify(
            _items(passive=True, behavior=True), behavior_within_3mo=False
        )
        assert risk == "moderate"

    def test_all_positive_recent_is_acute(self) -> None:
        all_positive = (True,) * 6
        risk, t3, _ = _classify(all_positive, behavior_within_3mo=True)
        assert risk == "acute"
        assert t3 is True


# ---------------------------------------------------------------------------
# behavior_within_3mo temporal gate
# ---------------------------------------------------------------------------


class TestClassifyCssrsBehaviorTemporalGate:
    def test_same_items_historic_vs_recent(self) -> None:
        items = _items(behavior=True)
        risk_historic, t3_historic, _ = _classify(items, behavior_within_3mo=False)
        risk_recent, t3_recent, _ = _classify(items, behavior_within_3mo=True)
        assert risk_historic == "moderate"
        assert risk_recent == "acute"
        assert t3_historic is False
        assert t3_recent is True

    def test_behavior_within_3mo_only_affects_item_6(self) -> None:
        # behavior_within_3mo=True on items that don't include item 6 → no change
        for items in [
            _items(passive=True),
            _items(method=True),
            _items(intent=True),
        ]:
            risk_false, _, _ = _classify(items, behavior_within_3mo=False)
            risk_true, _, _ = _classify(items, behavior_within_3mo=True)
            assert risk_false == risk_true

    def test_behavior_historic_not_in_acute_triggering(self) -> None:
        # When behavior_within_3mo=False, item 6 goes to moderate, not acute
        _, t3, _ = _classify(_items(behavior=True), behavior_within_3mo=False)
        assert t3 is False


# ---------------------------------------------------------------------------
# Return type contract
# ---------------------------------------------------------------------------


class TestClassifyCssrsReturnContract:
    def test_returns_3_tuple(self) -> None:
        result = _classify(_NONE, behavior_within_3mo=False)
        assert len(result) == 3

    def test_triggering_is_tuple_not_list(self) -> None:
        _, _, triggering = _classify(_NONE, behavior_within_3mo=False)
        assert isinstance(triggering, tuple)

    def test_triggering_items_are_one_indexed(self) -> None:
        # All triggering item numbers must be ≥ 1 (1-indexed clinical language)
        for items, behavior_3mo in [
            (_items(passive=True), False),
            (_items(method=True), False),
            (_items(intent=True), False),
            (_items(behavior=True), True),
        ]:
            _, _, triggering = _classify(items, behavior_within_3mo=behavior_3mo)
            for item_no in triggering:
                assert item_no >= 1

    def test_none_band_has_no_triggering_items(self) -> None:
        _, _, triggering = _classify(_NONE, behavior_within_3mo=False)
        assert len(triggering) == 0

    def test_requires_t3_is_bool(self) -> None:
        for items, behavior_3mo in [
            (_NONE, False),
            (_items(passive=True), False),
            (_items(intent=True), False),
        ]:
            _, t3, _ = _classify(items, behavior_within_3mo=behavior_3mo)
            assert isinstance(t3, bool)

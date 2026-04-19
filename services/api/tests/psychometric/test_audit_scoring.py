"""AUDIT scoring tests — Saunders 1993 / WHO 2001.

Two load-bearing correctness properties for the full 10-item AUDIT:

1. **Items 9 and 10 use a restricted 0/2/4 response scale.**  Accepting
   values 1 or 3 on these items is a wire-format bug — those values
   are not part of the WHO-published response set and silently
   mis-scoring them would shift a patient's zone classification.
2. **Four-zone classification with inclusive upper bounds** per
   Saunders 1993: low_risk 0-7, hazardous 8-15, harmful 16-19,
   dependence 20-40.  A flipped operator on any boundary would
   mis-route a patient between Zones II/III or Zones III/IV, which
   changes the clinician's recommended action (advice vs. brief
   counseling vs. referral).

Coverage strategy:
- Pin all zone cutoffs against Saunders 1993 / WHO 2001.
- Boundary-test each zone transition both just-below and at-cutoff.
- Exhaustively pin that items 1-8 accept the full 0-4 range.
- Exhaustively pin that items 9-10 reject 1, 3, and out-of-range.
- Input validation: wrong count, wrong type, bool rejection.
- Clinical vignettes a clinician would recognize.
"""

from __future__ import annotations

import pytest

from discipline.psychometric.scoring.audit import (
    AUDIT_HARMFUL_UPPER,
    AUDIT_HAZARDOUS_UPPER,
    AUDIT_LOW_RISK_UPPER,
    AUDIT_TOTAL_MAX,
    AUDIT_TOTAL_MIN,
    INSTRUMENT_VERSION,
    ITEM_COUNT,
    ITEM_MAX,
    ITEM_MIN,
    AuditResult,
    InvalidResponseError,
    RESTRICTED_SCALE_ITEMS_1INDEXED,
    RESTRICTED_SCALE_VALUES,
    score_audit,
)


def _items(base: int = 0, overrides: dict[int, int] | None = None) -> list[int]:
    """Build a 10-item list defaulting to ``base`` for every item.

    ``overrides`` is a 1-indexed dict of positions to specific values
    so test inputs stay readable ("item 9 = 2, rest = 0").  Item-9/10
    values must be in {0, 2, 4} per the instrument's restricted scale;
    the helper trusts callers to respect that.
    """
    out = [base] * ITEM_COUNT
    if overrides:
        for idx_1, value in overrides.items():
            out[idx_1 - 1] = value
    return out


# =============================================================================
# Constants — pinned to Saunders 1993 / WHO 2001
# =============================================================================


class TestConstants:
    def test_item_count_is_ten(self) -> None:
        """Full AUDIT is 10 items; AUDIT-C is a 3-item subset and
        lives in ``scoring/audit_c.py``.  A refactor that collapsed
        them must not drop the item count here."""
        assert ITEM_COUNT == 10

    def test_item_range_is_zero_to_four(self) -> None:
        """0-4 scale for items 1-8; items 9-10 overlay the restricted
        {0, 2, 4} subset."""
        assert ITEM_MIN == 0
        assert ITEM_MAX == 4

    def test_total_range_is_zero_to_forty(self) -> None:
        """Total range bounds pinned as module constants so callers
        (chart axis code, test fixtures) consume one source of truth."""
        assert AUDIT_TOTAL_MIN == 0
        assert AUDIT_TOTAL_MAX == 40

    def test_zone_upper_bounds_match_who_manual(self) -> None:
        """WHO 2001 AUDIT manual zones: 0-7 / 8-15 / 16-19 / 20-40.
        Changing any of these requires clinical sign-off; they should
        never drift as an implementation tweak."""
        assert AUDIT_LOW_RISK_UPPER == 7
        assert AUDIT_HAZARDOUS_UPPER == 15
        assert AUDIT_HARMFUL_UPPER == 19

    def test_zone_bounds_strictly_monotonic(self) -> None:
        """Structural invariant — zones are contiguous and ordered.
        A regression that flipped two bounds would silently skip a zone
        for every patient who landed between them."""
        assert AUDIT_LOW_RISK_UPPER < AUDIT_HAZARDOUS_UPPER
        assert AUDIT_HAZARDOUS_UPPER < AUDIT_HARMFUL_UPPER
        assert AUDIT_HARMFUL_UPPER < AUDIT_TOTAL_MAX

    def test_restricted_items_are_nine_and_ten(self) -> None:
        """Only items 9 and 10 use the 0/2/4 scale per WHO 2001.
        Adding or removing an item from this set is a clinical change."""
        assert RESTRICTED_SCALE_ITEMS_1INDEXED == frozenset({9, 10})

    def test_restricted_values_are_zero_two_four(self) -> None:
        """Published response options for items 9 and 10 are
        'No' (0) / 'Yes, but not in the last year' (2) / 'Yes, during
        the last year' (4).  1 and 3 are not response options."""
        assert RESTRICTED_SCALE_VALUES == frozenset({0, 2, 4})

    def test_instrument_version_stable(self) -> None:
        assert INSTRUMENT_VERSION == "audit-1.0.0"


# =============================================================================
# Zone boundary — low_risk / hazardous transition at total=8
# =============================================================================


class TestLowRiskZone:
    def test_total_zero_is_low_risk(self) -> None:
        r = score_audit(_items(base=0))
        assert r.total == 0
        assert r.band == "low_risk"

    def test_total_seven_is_low_risk(self) -> None:
        """At-cutoff inclusive: total=7 → still Zone I."""
        # Seven 1s on items 1-7, 0 elsewhere → total = 7.
        items = [1, 1, 1, 1, 1, 1, 1, 0, 0, 0]
        r = score_audit(items)
        assert r.total == 7
        assert r.band == "low_risk"

    def test_total_eight_crosses_to_hazardous(self) -> None:
        """Boundary flip at 8: a ``<=`` operator that stayed at
        low_risk would silently under-flag this patient."""
        items = [1, 1, 1, 1, 1, 1, 1, 1, 0, 0]
        r = score_audit(items)
        assert r.total == 8
        assert r.band == "hazardous"


# =============================================================================
# Zone boundary — hazardous / harmful transition at total=16
# =============================================================================


class TestHazardousZone:
    def test_total_fifteen_is_hazardous(self) -> None:
        # Five 3s on items 1-5 = 15.
        items = [3, 3, 3, 3, 3, 0, 0, 0, 0, 0]
        r = score_audit(items)
        assert r.total == 15
        assert r.band == "hazardous"

    def test_total_sixteen_crosses_to_harmful(self) -> None:
        items = [4, 4, 4, 4, 0, 0, 0, 0, 0, 0]
        r = score_audit(items)
        assert r.total == 16
        assert r.band == "harmful"


# =============================================================================
# Zone boundary — harmful / dependence transition at total=20
# =============================================================================


class TestHarmfulZone:
    def test_total_nineteen_is_harmful(self) -> None:
        items = [4, 4, 4, 4, 3, 0, 0, 0, 0, 0]
        r = score_audit(items)
        assert r.total == 19
        assert r.band == "harmful"

    def test_total_twenty_crosses_to_dependence(self) -> None:
        items = [4, 4, 4, 4, 4, 0, 0, 0, 0, 0]
        r = score_audit(items)
        assert r.total == 20
        assert r.band == "dependence"


# =============================================================================
# Dependence zone — top of scale
# =============================================================================


class TestDependenceZone:
    def test_total_forty_is_dependence(self) -> None:
        """Maximum score: items 1-8 all at 4, items 9-10 at 4 (the
        highest restricted-scale value).  Total = 8*4 + 4 + 4 = 40."""
        items = [4, 4, 4, 4, 4, 4, 4, 4, 4, 4]
        r = score_audit(items)
        assert r.total == 40
        assert r.band == "dependence"


# =============================================================================
# Restricted-scale validation (items 9 and 10 only)
# =============================================================================


class TestRestrictedScale:
    @pytest.mark.parametrize("value", [0, 2, 4])
    def test_item_nine_accepts_restricted_values(self, value: int) -> None:
        r = score_audit(_items(overrides={9: value}))
        assert r.total == value
        assert r.items[8] == value

    @pytest.mark.parametrize("value", [0, 2, 4])
    def test_item_ten_accepts_restricted_values(self, value: int) -> None:
        r = score_audit(_items(overrides={10: value}))
        assert r.total == value
        assert r.items[9] == value

    @pytest.mark.parametrize("value", [1, 3])
    def test_item_nine_rejects_in_between_values(self, value: int) -> None:
        """Items 9 and 10 use WHO's 3-point response set (0, 2, 4).
        A wire-format bug sending 1 or 3 must fail — those values
        are not valid responses to 'have you or someone else been
        injured because of your drinking?'"""
        with pytest.raises(InvalidResponseError, match="item 9"):
            score_audit(_items(overrides={9: value}))

    @pytest.mark.parametrize("value", [1, 3])
    def test_item_ten_rejects_in_between_values(self, value: int) -> None:
        with pytest.raises(InvalidResponseError, match="item 10"):
            score_audit(_items(overrides={10: value}))

    @pytest.mark.parametrize("value", [-1, 5, 6])
    def test_item_nine_rejects_out_of_range(self, value: int) -> None:
        with pytest.raises(InvalidResponseError, match="item 9"):
            score_audit(_items(overrides={9: value}))

    @pytest.mark.parametrize("value", [-1, 5, 6])
    def test_item_ten_rejects_out_of_range(self, value: int) -> None:
        with pytest.raises(InvalidResponseError, match="item 10"):
            score_audit(_items(overrides={10: value}))

    def test_error_mentions_restricted_scale(self) -> None:
        """The error message for items 9/10 must explicitly mention
        the {0, 2, 4} set so a client developer debugging a wire-
        format bug understands why 1 is not accepted."""
        with pytest.raises(InvalidResponseError) as exc_info:
            score_audit(_items(overrides={9: 1}))
        msg = str(exc_info.value)
        assert "0, 2, or 4" in msg


# =============================================================================
# Standard 0-4 scale validation (items 1-8)
# =============================================================================


class TestStandardScale:
    @pytest.mark.parametrize("item_idx", [1, 2, 3, 4, 5, 6, 7, 8])
    def test_items_one_through_eight_accept_full_range(
        self, item_idx: int
    ) -> None:
        """Each non-restricted item must accept every value in [0, 4].
        A regression that accidentally restricted any of these to a
        narrower set would silently drop valid responses."""
        for value in range(5):
            r = score_audit(_items(overrides={item_idx: value}))
            assert r.items[item_idx - 1] == value

    @pytest.mark.parametrize("item_idx", [1, 2, 3, 4, 5, 6, 7, 8])
    def test_items_one_through_eight_reject_negative(
        self, item_idx: int
    ) -> None:
        with pytest.raises(InvalidResponseError, match=f"item {item_idx}"):
            score_audit(_items(overrides={item_idx: -1}))

    @pytest.mark.parametrize("item_idx", [1, 2, 3, 4, 5, 6, 7, 8])
    def test_items_one_through_eight_reject_above_four(
        self, item_idx: int
    ) -> None:
        with pytest.raises(InvalidResponseError, match=f"item {item_idx}"):
            score_audit(_items(overrides={item_idx: 5}))


# =============================================================================
# Input validation
# =============================================================================


class TestInputValidation:
    def test_wrong_count_rejected_nine_items(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 10"):
            score_audit([0] * 9)

    def test_wrong_count_rejected_eleven_items(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 10"):
            score_audit([0] * 11)

    def test_empty_list_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 10"):
            score_audit([])

    def test_bool_rejected_on_standard_item(self) -> None:
        """True/False would silently score as 1/0 — for a 0-4 scale
        item that maps to a real clinical response value and is a
        wire-format bug the scorer must refuse."""
        items: list[int] = _items()
        items[0] = True  # type: ignore[list-item]
        with pytest.raises(InvalidResponseError, match="item 1"):
            score_audit(items)

    def test_bool_rejected_on_restricted_item(self) -> None:
        """Even on item 9 where True happens to be a valid integer
        (1) that's NOT in the restricted scale {0, 2, 4}, the bool
        type must be rejected up front for consistency."""
        items: list[int] = _items()
        items[8] = False  # type: ignore[list-item]
        with pytest.raises(InvalidResponseError, match="item 9"):
            score_audit(items)

    def test_string_rejected(self) -> None:
        items: list[int] = _items()
        items[0] = "2"  # type: ignore[list-item]
        with pytest.raises(InvalidResponseError, match="item 1"):
            score_audit(items)

    def test_float_rejected(self) -> None:
        """Floats would silently truncate to int in a naive
        implementation — 2.7 becoming 2 changes the zone boundary."""
        items: list[int] = _items()
        items[0] = 2.5  # type: ignore[list-item]
        with pytest.raises(InvalidResponseError, match="item 1"):
            score_audit(items)

    def test_none_rejected(self) -> None:
        items: list[int] = _items()
        items[0] = None  # type: ignore[list-item]
        with pytest.raises(InvalidResponseError, match="item 1"):
            score_audit(items)


# =============================================================================
# Result shape and immutability
# =============================================================================


class TestResultShape:
    def test_items_echoed_verbatim(self) -> None:
        """The result carries the caller's items unchanged so an
        auditor can re-derive the total and band without trusting the
        stored aggregates."""
        items = [0, 1, 2, 3, 4, 0, 1, 2, 0, 2]
        r = score_audit(items)
        assert r.items == tuple(items)

    def test_items_stored_as_tuple(self) -> None:
        """Tuple keeps the result hashable and immutable.  A list
        field would let a caller mutate stored items after the fact."""
        r = score_audit(_items())
        assert isinstance(r.items, tuple)

    def test_result_is_frozen(self) -> None:
        r = score_audit(_items())
        with pytest.raises(Exception):  # noqa: B017 — FrozenInstanceError
            r.total = 99  # type: ignore[misc]

    def test_instrument_version_in_result(self) -> None:
        r = score_audit(_items())
        assert r.instrument_version == "audit-1.0.0"


# =============================================================================
# Clinical vignettes — a clinician should recognize each of these
# =============================================================================


class TestClinicalVignettes:
    def test_occasional_social_drinker(self) -> None:
        """Monthly drinking (item 1 = 1), 1-2 drinks per occasion
        (item 2 = 0), never heavy (item 3 = 0), no dependence or
        problems.  Total = 1, Zone I."""
        items = [1, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        r = score_audit(items)
        assert r.band == "low_risk"

    def test_hazardous_weekly_binge_pattern(self) -> None:
        """Frequent drinking (item 1 = 3 = 2-3x/week), high quantity
        (item 2 = 3 = 7-9 drinks), weekly heavy sessions (item 3 = 3).
        No dependence items endorsed.  Total = 9, Zone II."""
        items = [3, 3, 3, 0, 0, 0, 0, 0, 0, 0]
        r = score_audit(items)
        assert r.total == 9
        assert r.band == "hazardous"

    def test_harmful_drinking_with_morning_use(self) -> None:
        """Daily drinking (item 1 = 4), high quantity (item 2 = 4),
        monthly loss of control (item 4 = 2), morning drinking
        (item 6 = 2), guilt (item 7 = 2), blackouts (item 8 = 2),
        injury not in last year (item 9 = 2), concern from others
        not in last year (item 10 = 2).  Total = 20, Zone IV."""
        items = [4, 4, 0, 2, 0, 2, 2, 2, 2, 2]
        r = score_audit(items)
        assert r.total == 20
        assert r.band == "dependence"

    def test_clear_dependence_pattern(self) -> None:
        """Daily drinking + daily loss of control + weekly morning
        drinking + frequent blackouts + injury in last year +
        concern from others in last year.  Classic dependence
        presentation."""
        items = [4, 4, 4, 4, 3, 3, 3, 3, 4, 4]
        r = score_audit(items)
        assert r.total == 36
        assert r.band == "dependence"

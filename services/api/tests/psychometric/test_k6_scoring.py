"""Tests for the K6 scorer (Kessler 2003 / NSDUH reference short
form of the Kessler Psychological Distress Scale).

Pins the module constants, total computation, SMI cutoff boundary,
validator envelope (item count, item range, bool rejection, 1-5
range), result shape invariants, and the no-safety-routing invariant.
"""

from __future__ import annotations

import pytest

from discipline.psychometric.scoring.k6 import (
    INSTRUMENT_VERSION,
    ITEM_COUNT,
    ITEM_MAX,
    ITEM_MIN,
    InvalidResponseError,
    K6_POSITIVE_CUTOFF,
    K6Result,
    score_k6,
)


class TestConstants:
    """Pinned module constants — drift here is a clinical change."""

    def test_item_count_is_six(self) -> None:
        assert ITEM_COUNT == 6

    def test_item_floor_is_one(self) -> None:
        """Kessler 2003 uses the same 1-5 coding as K10.  ITEM_MIN=1
        is load-bearing for the ≥13 cutoff calibration — a 0-indexed
        submission would shift totals by 6 and miss the SMI gate."""
        assert ITEM_MIN == 1

    def test_item_ceiling_is_five(self) -> None:
        assert ITEM_MAX == 5

    def test_instrument_version_pinned(self) -> None:
        assert INSTRUMENT_VERSION == "k6-1.0.0"

    def test_cutoff_is_thirteen(self) -> None:
        """Kessler 2003 SMI cutoff is ≥13 (AUC 0.87 against DSM-IV
        SMI)."""
        assert K6_POSITIVE_CUTOFF == 13


class TestTotalCorrectness:
    """Total is the straight sum of items — no reverse scoring."""

    def test_minimum_total_is_six(self) -> None:
        """Every item min is 1, so total min is 6 — NOT 0."""
        r = score_k6([1] * 6)
        assert r.total == 6

    def test_maximum_total_is_thirty(self) -> None:
        r = score_k6([5] * 6)
        assert r.total == 30

    def test_mixed_sum(self) -> None:
        r = score_k6([1, 2, 3, 2, 3, 1])
        assert r.total == 12

    def test_single_high_item(self) -> None:
        r = score_k6([5, 1, 1, 1, 1, 1])
        assert r.total == 10


class TestCutoffBoundary:
    """Kessler 2003 ≥13 gate — flips exactly at 13."""

    def test_total_twelve_is_negative(self) -> None:
        """Below cutoff — negative screen."""
        r = score_k6([2, 2, 2, 2, 2, 2])
        assert r.total == 12
        assert r.positive_screen is False

    def test_total_thirteen_is_positive(self) -> None:
        """Cutoff boundary — total=13 flips to positive SMI screen."""
        r = score_k6([2, 2, 2, 2, 2, 3])
        assert r.total == 13
        assert r.positive_screen is True

    def test_total_fourteen_is_positive(self) -> None:
        r = score_k6([2, 2, 2, 2, 3, 3])
        assert r.total == 14
        assert r.positive_screen is True

    def test_minimum_total_six_is_negative(self) -> None:
        r = score_k6([1] * 6)
        assert r.positive_screen is False

    def test_maximum_total_thirty_is_positive(self) -> None:
        r = score_k6([5] * 6)
        assert r.positive_screen is True

    def test_single_item_cannot_reach_cutoff(self) -> None:
        """Single max'd item (5) plus five minimum (1 each) = 10,
        below cutoff.  A positive K6 requires multi-item distress —
        not just one bad symptom.  Pins the cutoff-as-pattern
        rationale."""
        r = score_k6([5, 1, 1, 1, 1, 1])
        assert r.total == 10
        assert r.positive_screen is False

    def test_two_high_items_reach_cutoff(self) -> None:
        """Two items at 5 plus four items at 1 = 14 — crosses
        cutoff."""
        r = score_k6([5, 5, 1, 1, 1, 1])
        assert r.total == 14
        assert r.positive_screen is True


class TestItemCountValidation:
    """Exact count = 6.  Any other length is a 422, not a silent score."""

    def test_rejects_zero_items(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 6 items"):
            score_k6([])

    def test_rejects_five_items(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 6 items"):
            score_k6([1, 1, 1, 1, 1])

    def test_rejects_seven_items(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 6 items"):
            score_k6([1, 1, 1, 1, 1, 1, 1])

    def test_rejects_ten_items_k10_misroute(self) -> None:
        """10 items is K10 territory — must NOT silently score as K6."""
        with pytest.raises(InvalidResponseError, match="exactly 6 items"):
            score_k6([1] * 10)


class TestItemRangeValidation:
    """Every item must be within [1, 5].  No coercion, no clamping."""

    @pytest.mark.parametrize("bad_value", [-1, 0, 6, 7, 10])
    def test_rejects_out_of_range(self, bad_value: int) -> None:
        with pytest.raises(InvalidResponseError, match="out of range"):
            score_k6([bad_value, 1, 1, 1, 1, 1])

    def test_rejects_zero_not_silently_accepted(self) -> None:
        """LOAD-BEARING — ITEM_MIN=1 matches K10's Kessler coding.
        A 0 would shift totals by 6 and potentially drop a positive
        SMI screen.  Must reject explicitly."""
        with pytest.raises(InvalidResponseError, match="out of range"):
            score_k6([0, 1, 1, 1, 1, 1])

    def test_rejects_negative_at_last_position(self) -> None:
        with pytest.raises(InvalidResponseError, match="item 6"):
            score_k6([1, 1, 1, 1, 1, -1])

    def test_rejects_string_item(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_k6([1, 1, "3", 1, 1, 1])  # type: ignore[list-item]

    def test_rejects_float_item(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_k6([1, 1, 2.5, 1, 1, 1])  # type: ignore[list-item]

    def test_rejects_none_item(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_k6([1, 1, None, 1, 1, 1])  # type: ignore[list-item]


class TestBoolRejection:
    """Uniform with the rest of the package — bool is not a valid
    Likert value, even though ``True == 1`` in Python."""

    def test_rejects_true(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_k6([True, 1, 1, 1, 1, 1])  # type: ignore[list-item]

    def test_rejects_false(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_k6([False, 1, 1, 1, 1, 1])  # type: ignore[list-item]


class TestResultShape:
    """Pin the K6Result dataclass shape — no drift, no surprise fields."""

    def test_result_is_frozen(self) -> None:
        r = score_k6([1, 1, 1, 1, 1, 1])
        with pytest.raises(Exception):  # FrozenInstanceError subclass
            r.total = 99  # type: ignore[misc]

    def test_result_has_no_severity_field(self) -> None:
        """K6 uses cutoff envelope, not banded envelope — no
        ``severity`` attribute on the scorer result.  K10 has banded
        severity; K6 does NOT (Kessler 2003 published only the ≥13
        SMI cutoff, not K10-style bands)."""
        r = score_k6([1, 1, 1, 1, 1, 1])
        assert not hasattr(r, "severity")

    def test_result_has_no_requires_t3_field(self) -> None:
        """K6 has no safety item — no ``requires_t3`` on the result."""
        r = score_k6([5, 5, 5, 5, 5, 5])
        assert not hasattr(r, "requires_t3")

    def test_result_has_no_subscales_field(self) -> None:
        """Kessler 2003 validated unidimensionality — no subscales."""
        r = score_k6([1, 1, 1, 1, 1, 1])
        assert not hasattr(r, "subscales")

    def test_result_carries_instrument_version(self) -> None:
        r = score_k6([1, 1, 1, 1, 1, 1])
        assert r.instrument_version == "k6-1.0.0"

    def test_result_echoes_items_verbatim(self) -> None:
        r = score_k6([1, 2, 3, 4, 5, 1])
        assert r.items == (1, 2, 3, 4, 5, 1)

    def test_result_items_is_tuple(self) -> None:
        r = score_k6([1, 2, 3, 4, 5, 1])
        assert isinstance(r.items, tuple)

    def test_result_is_k6result_instance(self) -> None:
        r = score_k6([1] * 6)
        assert isinstance(r, K6Result)


class TestClinicalVignettes:
    """Realistic patient scenarios pinning clinical interpretation."""

    def test_low_distress_vignette(self) -> None:
        """Patient with mild occasional distress — mostly "a little
        of the time" on a few items.  Below cutoff; distress at
        normal-range levels."""
        r = score_k6([2, 1, 2, 1, 2, 1])
        assert r.total == 9
        assert r.positive_screen is False

    def test_moderate_distress_sub_threshold(self) -> None:
        """Moderate distress — "some of the time" across most items.
        Just below cutoff (12).  Clinician might re-assess at next
        cadence or promote to K10 for banded signal."""
        r = score_k6([2, 2, 2, 2, 2, 2])
        assert r.total == 12
        assert r.positive_screen is False

    def test_smi_threshold_vignette(self) -> None:
        """Patient at the SMI threshold — "some of the time" across
        most items plus one item at "most of the time".  Crosses
        cutoff; flags for full work-up."""
        r = score_k6([2, 2, 2, 2, 2, 3])
        assert r.total == 13
        assert r.positive_screen is True

    def test_high_distress_vignette(self) -> None:
        """Clearly above cutoff — "most of the time" across items.
        Strong distress signal; clinician works up with K10 / PHQ-9 /
        GAD-7 / C-SSRS as indicated."""
        r = score_k6([4, 4, 4, 4, 4, 4])
        assert r.total == 24
        assert r.positive_screen is True

    def test_hopelessness_dominant_vignette(self) -> None:
        """Depressive-dominant profile — items 2 (hopeless) and 4
        (so depressed) at "most of the time"; other items moderate.
        Crosses cutoff.  Though dominated by hopelessness items, NO
        T3 fires — K6 items are affect probes, not intent probes."""
        r = score_k6([2, 4, 2, 4, 2, 2])
        assert r.total == 16
        assert r.positive_screen is True
        assert not hasattr(r, "requires_t3")


class TestNoSafetyRouting:
    """K6 has no suicidality item.  No combination of responses fires
    T3.  The scorer doesn't even expose requires_t3 — this class pins
    the invariant against future accidental addition."""

    def test_all_max_items_do_not_fire_t3(self) -> None:
        r = score_k6([5, 5, 5, 5, 5, 5])
        assert not hasattr(r, "requires_t3")
        assert r.positive_screen is True

    def test_hopelessness_item_alone_does_not_fire_t3(self) -> None:
        """Item 2 (hopeless) maxed — affect probe, not intent probe."""
        r = score_k6([1, 5, 1, 1, 1, 1])
        assert not hasattr(r, "requires_t3")

    def test_worthlessness_item_alone_does_not_fire_t3(self) -> None:
        """Item 6 (worthless) maxed — affect probe, not intent probe."""
        r = score_k6([1, 1, 1, 1, 1, 5])
        assert not hasattr(r, "requires_t3")

    def test_all_three_negative_mood_items_maxed_does_not_fire_t3(
        self,
    ) -> None:
        """All three negative-mood items (2 hopeless, 4 so depressed,
        6 worthless) maxed simultaneously — a strong affect signal,
        but still NOT a suicidality signal.  Acute ideation screening
        is PHQ-9 item 9 / C-SSRS, not K6."""
        r = score_k6([1, 5, 1, 5, 1, 5])
        assert not hasattr(r, "requires_t3")
        assert r.positive_screen is True

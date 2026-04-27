"""Unit tests for pure helpers in discipline.check_in.router.

_intensity_to_state(intensity) → str
  SUDS-calibrated band mapping:
  0–3  → "stable"
  4–6  → "rising_urge"
  7–10 → "peak_urge"
  No overlap, no gap — every integer in [0, 10] maps to exactly one label.

Confidence formula (inline, router.py:234):
  confidence = round(0.70 + 0.03 * min(intensity, 10), 2)
  Range: intensity=0 → 0.70, intensity=10 → 1.00.
  min(…, 10) caps the multiplier so a hypothetical out-of-range value
  never exceeds 1.00.

add_check_in / get_check_ins / reset_check_in_store
  In-memory store backed by a module-level defaultdict.
  get_check_ins returns newest-first (reversed insertion order) and
  returns an empty list for an unknown user without raising KeyError.
  reset_check_in_store() must be called in teardown to prevent state leak.
"""

from __future__ import annotations

import pytest

from discipline.check_in.router import (
    _intensity_to_state,
    add_check_in,
    get_check_ins,
    reset_check_in_store,
)


# ---------------------------------------------------------------------------
# _intensity_to_state — SUDS band mapping
# ---------------------------------------------------------------------------


class TestIntensityToState:
    def test_zero_is_stable(self) -> None:
        assert _intensity_to_state(0) == "stable"

    def test_one_is_stable(self) -> None:
        assert _intensity_to_state(1) == "stable"

    def test_three_is_stable(self) -> None:
        assert _intensity_to_state(3) == "stable"

    def test_four_is_rising_urge(self) -> None:
        assert _intensity_to_state(4) == "rising_urge"

    def test_five_is_rising_urge(self) -> None:
        assert _intensity_to_state(5) == "rising_urge"

    def test_six_is_rising_urge(self) -> None:
        assert _intensity_to_state(6) == "rising_urge"

    def test_seven_is_peak_urge(self) -> None:
        assert _intensity_to_state(7) == "peak_urge"

    def test_eight_is_peak_urge(self) -> None:
        assert _intensity_to_state(8) == "peak_urge"

    def test_ten_is_peak_urge(self) -> None:
        assert _intensity_to_state(10) == "peak_urge"

    def test_all_valid_intensities_return_known_labels(self) -> None:
        known = {"stable", "rising_urge", "peak_urge"}
        for i in range(11):
            assert _intensity_to_state(i) in known

    def test_boundary_3_to_4_transitions(self) -> None:
        assert _intensity_to_state(3) == "stable"
        assert _intensity_to_state(4) == "rising_urge"

    def test_boundary_6_to_7_transitions(self) -> None:
        assert _intensity_to_state(6) == "rising_urge"
        assert _intensity_to_state(7) == "peak_urge"


# ---------------------------------------------------------------------------
# Confidence formula — 0.70 + 0.03 * min(intensity, 10), rounded to 2 dp
# ---------------------------------------------------------------------------


def _confidence(intensity: int) -> float:
    return round(0.70 + 0.03 * min(intensity, 10), 2)


class TestConfidenceFormula:
    def test_intensity_zero_gives_0_70(self) -> None:
        assert _confidence(0) == 0.70

    def test_intensity_one_gives_0_73(self) -> None:
        assert _confidence(1) == 0.73

    def test_intensity_five_gives_0_85(self) -> None:
        assert _confidence(5) == 0.85

    def test_intensity_ten_gives_1_00(self) -> None:
        assert _confidence(10) == 1.00

    def test_cap_means_out_of_range_still_1_00(self) -> None:
        # The field validator blocks >10 in production, but the formula
        # itself caps with min(..., 10) so it can never exceed 1.00.
        assert _confidence(11) == 1.00
        assert _confidence(99) == 1.00

    def test_result_is_two_decimal_places(self) -> None:
        # Every integer in [0, 10] must round cleanly to 2 dp.
        for i in range(11):
            c = _confidence(i)
            assert c == round(c, 2)

    def test_monotonically_non_decreasing(self) -> None:
        prev = _confidence(0)
        for i in range(1, 11):
            curr = _confidence(i)
            assert curr >= prev
            prev = curr

    def test_range_is_0_70_to_1_00(self) -> None:
        values = [_confidence(i) for i in range(11)]
        assert min(values) == 0.70
        assert max(values) == 1.00


# ---------------------------------------------------------------------------
# add_check_in / get_check_ins / reset_check_in_store
# ---------------------------------------------------------------------------


class TestCheckInStore:
    def setup_method(self) -> None:
        reset_check_in_store()

    def teardown_method(self) -> None:
        reset_check_in_store()

    def test_empty_store_returns_empty_list(self) -> None:
        assert get_check_ins("user-unknown", 10) == []

    def test_add_then_get_single_record(self) -> None:
        add_check_in("u1", "sid-1", 5, ["stress"], "2026-01-01T00:00:00Z")
        records = get_check_ins("u1", 10)
        assert len(records) == 1
        assert records[0].session_id == "sid-1"
        assert records[0].intensity == 5

    def test_get_returns_newest_first(self) -> None:
        add_check_in("u1", "sid-old", 3, [], "2026-01-01T00:00:00Z")
        add_check_in("u1", "sid-new", 7, [], "2026-01-02T00:00:00Z")
        records = get_check_ins("u1", 10)
        assert records[0].session_id == "sid-new"
        assert records[1].session_id == "sid-old"

    def test_limit_truncates_to_n_newest(self) -> None:
        for i in range(5):
            add_check_in("u1", f"sid-{i}", i, [], f"2026-01-0{i + 1}T00:00:00Z")
        records = get_check_ins("u1", 3)
        assert len(records) == 3
        # Newest first — the last 3 inserted are i=4,3,2
        assert records[0].session_id == "sid-4"

    def test_limit_equal_to_count_returns_all(self) -> None:
        for i in range(3):
            add_check_in("u1", f"sid-{i}", 1, [], "2026-01-01T00:00:00Z")
        assert len(get_check_ins("u1", 3)) == 3

    def test_limit_larger_than_count_returns_all(self) -> None:
        add_check_in("u1", "sid-only", 2, [], "2026-01-01T00:00:00Z")
        assert len(get_check_ins("u1", 100)) == 1

    def test_trigger_tags_preserved(self) -> None:
        tags = ["boredom", "loneliness"]
        add_check_in("u1", "sid-1", 4, tags, "2026-01-01T00:00:00Z")
        record = get_check_ins("u1", 1)[0]
        assert record.trigger_tags == tags

    def test_checked_in_at_preserved(self) -> None:
        ts = "2026-03-15T14:30:00Z"
        add_check_in("u1", "sid-1", 6, [], ts)
        record = get_check_ins("u1", 1)[0]
        assert record.checked_in_at == ts

    def test_different_users_are_isolated(self) -> None:
        add_check_in("user-a", "sid-a", 1, [], "2026-01-01T00:00:00Z")
        add_check_in("user-b", "sid-b", 9, [], "2026-01-01T00:00:00Z")
        assert get_check_ins("user-a", 10)[0].session_id == "sid-a"
        assert get_check_ins("user-b", 10)[0].session_id == "sid-b"

    def test_reset_clears_all_users(self) -> None:
        add_check_in("user-a", "sid-a", 1, [], "2026-01-01T00:00:00Z")
        add_check_in("user-b", "sid-b", 2, [], "2026-01-01T00:00:00Z")
        reset_check_in_store()
        assert get_check_ins("user-a", 10) == []
        assert get_check_ins("user-b", 10) == []

    def test_store_accumulates_across_adds(self) -> None:
        for i in range(10):
            add_check_in("u1", f"sid-{i}", i % 10, [], "2026-01-01T00:00:00Z")
        assert len(get_check_ins("u1", 100)) == 10

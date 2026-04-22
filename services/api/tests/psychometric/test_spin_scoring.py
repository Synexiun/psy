"""Tests for the SPIN (Social Phobia Inventory) scorer.

Connor KM et al. 2000 British Journal of Psychiatry 176:379-386.
17 items, 0-4 Likert, total 0-68, HIGHER = MORE social anxiety.
Severity bands: none (0-20), mild (21-30), moderate (31-40),
severe (41-50), very_severe (51-68).
Unidimensional (Connor 2000 EFA, Cronbach α = 0.94).
No positive_screen, no subscales.
"""

from __future__ import annotations

import pytest

from discipline.psychometric.scoring.spin import (
    INSTRUMENT_VERSION,
    ITEM_COUNT,
    ITEM_MAX,
    ITEM_MIN,
    SPIN_SEVERITY_THRESHOLDS,
    InvalidResponseError,
    SpinResult,
    score_spin,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _items(total: int) -> list[int]:
    """Construct a valid 17-item list summing to ``total``.

    Distributes evenly; remainder applied to last non-full item.
    """
    if total < 0 or total > 17 * ITEM_MAX:
        raise ValueError(f"Cannot construct SPIN items for total={total}")
    items: list[int] = []
    remaining = total
    for _ in range(ITEM_COUNT):
        v = min(ITEM_MAX, remaining)
        items.append(v)
        remaining -= v
    return items


def _floor_items() -> list[int]:
    return [0] * ITEM_COUNT


def _ceil_items() -> list[int]:
    return [4] * ITEM_COUNT


# ---------------------------------------------------------------------------
# TestConstants
# ---------------------------------------------------------------------------

class TestConstants:
    def test_instrument_version(self) -> None:
        assert INSTRUMENT_VERSION == "spin-1.0.0"

    def test_item_count(self) -> None:
        assert ITEM_COUNT == 17

    def test_item_min(self) -> None:
        assert ITEM_MIN == 0

    def test_item_max(self) -> None:
        assert ITEM_MAX == 4

    def test_severity_thresholds_pinned_to_connor_2000(self) -> None:
        # Connor 2000 Table 4 + Davidson 2004 normative distributions.
        expected = ((20, "none"), (30, "mild"), (40, "moderate"), (50, "severe"), (68, "very_severe"))
        assert expected == SPIN_SEVERITY_THRESHOLDS

    def test_thresholds_cover_full_range(self) -> None:
        # Final upper must equal ITEM_COUNT × ITEM_MAX
        assert SPIN_SEVERITY_THRESHOLDS[-1][0] == ITEM_COUNT * ITEM_MAX

    def test_thresholds_strictly_increasing(self) -> None:
        uppers = [u for u, _ in SPIN_SEVERITY_THRESHOLDS]
        assert uppers == sorted(uppers)

    def test_labels_expected_set(self) -> None:
        labels = {label for _, label in SPIN_SEVERITY_THRESHOLDS}
        assert labels == {"none", "mild", "moderate", "severe", "very_severe"}


# ---------------------------------------------------------------------------
# TestTotalCorrectness
# ---------------------------------------------------------------------------

class TestTotalCorrectness:
    def test_floor_total_is_zero(self) -> None:
        r = score_spin(_floor_items())
        assert r.total == 0

    def test_ceiling_total_is_68(self) -> None:
        r = score_spin(_ceil_items())
        assert r.total == 68

    def test_all_ones_total(self) -> None:
        r = score_spin([1] * ITEM_COUNT)
        assert r.total == 17

    def test_all_twos_total(self) -> None:
        r = score_spin([2] * ITEM_COUNT)
        assert r.total == 34

    def test_all_threes_total(self) -> None:
        r = score_spin([3] * ITEM_COUNT)
        assert r.total == 51

    def test_explicit_mixed_total(self) -> None:
        # Items: 7 × 2 + 5 × 3 + 5 × 1 = 14 + 15 + 5 = 34
        items = [2] * 7 + [3] * 5 + [1] * 5
        assert len(items) == 17
        r = score_spin(items)
        assert r.total == 34

    def test_total_matches_python_sum(self) -> None:
        items = [0, 1, 2, 3, 4, 3, 2, 1, 0, 1, 2, 3, 4, 3, 2, 1, 0]
        assert len(items) == 17
        r = score_spin(items)
        assert r.total == sum(items)

    def test_no_reverse_keying(self) -> None:
        # Increasing all items must increase total linearly.
        r0 = score_spin([0] * ITEM_COUNT)
        r1 = score_spin([1] * ITEM_COUNT)
        assert r1.total == r0.total + ITEM_COUNT


# ---------------------------------------------------------------------------
# TestSeverityBoundaries
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("total,expected_severity", [
    (0, "none"),
    (20, "none"),
    (21, "mild"),
    (30, "mild"),
    (31, "moderate"),
    (40, "moderate"),
    (41, "severe"),
    (50, "severe"),
    (51, "very_severe"),
    (68, "very_severe"),
])
def test_severity_at_each_boundary(total: int, expected_severity: str) -> None:
    items = _items(total)
    r = score_spin(items)
    assert r.total == total
    assert r.severity == expected_severity


class TestSeverityAnchors:
    def test_floor_is_none(self) -> None:
        assert score_spin(_floor_items()).severity == "none"

    def test_ceiling_is_very_severe(self) -> None:
        assert score_spin(_ceil_items()).severity == "very_severe"

    def test_mid_none_is_none(self) -> None:
        # total = 10 → none
        assert score_spin(_items(10)).severity == "none"

    def test_mid_mild_is_mild(self) -> None:
        # total = 25 → mild
        assert score_spin(_items(25)).severity == "mild"

    def test_mid_moderate_is_moderate(self) -> None:
        # total = 35 → moderate
        assert score_spin(_items(35)).severity == "moderate"

    def test_mid_severe_is_severe(self) -> None:
        # total = 45 → severe
        assert score_spin(_items(45)).severity == "severe"

    def test_mid_very_severe_is_very_severe(self) -> None:
        # total = 60 → very_severe
        assert score_spin(_items(60)).severity == "very_severe"

    def test_boundary_20_is_none_not_mild(self) -> None:
        # Connor 2000 uses inclusive upper bounds — 20 is "none"
        assert score_spin(_items(20)).severity == "none"

    def test_boundary_21_is_mild_not_none(self) -> None:
        assert score_spin(_items(21)).severity == "mild"

    def test_boundary_50_is_severe_not_very_severe(self) -> None:
        assert score_spin(_items(50)).severity == "severe"

    def test_boundary_51_is_very_severe_not_severe(self) -> None:
        assert score_spin(_items(51)).severity == "very_severe"


# ---------------------------------------------------------------------------
# TestItemCountValidation
# ---------------------------------------------------------------------------

class TestItemCountValidation:
    def test_too_few_items_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            score_spin([1] * 16)

    def test_too_many_items_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            score_spin([1] * 18)

    def test_empty_raises(self) -> None:
        with pytest.raises(InvalidResponseError):
            score_spin([])

    def test_error_message_mentions_count(self) -> None:
        with pytest.raises(InvalidResponseError, match="17"):
            score_spin([0] * 5)


# ---------------------------------------------------------------------------
# TestItemRangeValidation
# ---------------------------------------------------------------------------

class TestItemRangeValidation:
    def test_negative_item_raises(self) -> None:
        items = [1] * ITEM_COUNT
        items[0] = -1
        with pytest.raises(InvalidResponseError):
            score_spin(items)

    def test_item_above_4_raises(self) -> None:
        items = [1] * ITEM_COUNT
        items[3] = 5
        with pytest.raises(InvalidResponseError):
            score_spin(items)

    def test_middle_item_out_of_range_raises(self) -> None:
        items = [2] * ITEM_COUNT
        items[8] = 99
        with pytest.raises(InvalidResponseError):
            score_spin(items)

    def test_last_item_out_of_range_raises(self) -> None:
        items = [1] * ITEM_COUNT
        items[16] = -2
        with pytest.raises(InvalidResponseError):
            score_spin(items)

    def test_error_message_mentions_item_position(self) -> None:
        items = [0] * ITEM_COUNT
        items[4] = 7
        with pytest.raises(InvalidResponseError, match="5"):  # 1-indexed
            score_spin(items)


# ---------------------------------------------------------------------------
# TestItemTypeValidation
# ---------------------------------------------------------------------------

class TestItemTypeValidation:
    def test_true_raises(self) -> None:
        items: list = [1] * ITEM_COUNT
        items[0] = True
        with pytest.raises(InvalidResponseError):
            score_spin(items)

    def test_false_raises(self) -> None:
        items: list = [2] * ITEM_COUNT
        items[0] = False
        with pytest.raises(InvalidResponseError):
            score_spin(items)

    def test_float_raises(self) -> None:
        items: list = [1] * ITEM_COUNT
        items[2] = 2.0
        with pytest.raises(InvalidResponseError):
            score_spin(items)

    def test_string_raises(self) -> None:
        items: list = [1] * ITEM_COUNT
        items[5] = "3"
        with pytest.raises(InvalidResponseError):
            score_spin(items)

    def test_none_raises(self) -> None:
        items: list = [1] * ITEM_COUNT
        items[11] = None
        with pytest.raises(InvalidResponseError):
            score_spin(items)


# ---------------------------------------------------------------------------
# TestResultTyping
# ---------------------------------------------------------------------------

class TestResultTyping:
    def test_result_is_spin_result(self) -> None:
        r = score_spin(_floor_items())
        assert isinstance(r, SpinResult)

    def test_result_is_frozen(self) -> None:
        r = score_spin(_floor_items())
        with pytest.raises((AttributeError, TypeError)):
            r.total = 99  # type: ignore[misc]

    def test_instrument_version_pinned(self) -> None:
        r = score_spin(_floor_items())
        assert r.instrument_version == INSTRUMENT_VERSION

    def test_items_is_tuple(self) -> None:
        r = score_spin(_floor_items())
        assert isinstance(r.items, tuple)

    def test_items_length_17(self) -> None:
        r = score_spin(_floor_items())
        assert len(r.items) == ITEM_COUNT

    def test_severity_is_string(self) -> None:
        r = score_spin(_floor_items())
        assert isinstance(r.severity, str)

    def test_total_is_int(self) -> None:
        r = score_spin(_floor_items())
        assert isinstance(r.total, int)

    def test_no_subscales_attribute(self) -> None:
        r = score_spin(_floor_items())
        assert not hasattr(r, "subscales")

    def test_no_positive_screen_attribute(self) -> None:
        r = score_spin(_floor_items())
        assert not hasattr(r, "positive_screen")


# ---------------------------------------------------------------------------
# TestClinicalVignettes
# ---------------------------------------------------------------------------

class TestClinicalVignettes:
    def test_healthy_control_no_social_phobia(self) -> None:
        # Community normative — low-fear, low-avoidance, low-arousal.
        # All items 0-1; total ≤ 10 → "none".
        items = [0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 0]
        assert len(items) == 17
        r = score_spin(items)
        assert r.severity == "none"
        assert r.total <= 20

    def test_mild_social_phobia_job_interview_anxiety(self) -> None:
        # Mild fear + some avoidance; total in 21-30 range.
        items = _items(25)
        r = score_spin(items)
        assert r.severity == "mild"

    def test_moderate_social_phobia_public_speaking(self) -> None:
        # Moderate fear, avoidance, physiological arousal; total 31-40.
        items = _items(36)
        r = score_spin(items)
        assert r.severity == "moderate"

    def test_severe_social_phobia_alcohol_self_medication(self) -> None:
        # Buckner 2008: severe social anxiety → alcohol self-medication.
        # Total 41-50 → severe.
        items = _items(46)
        r = score_spin(items)
        assert r.severity == "severe"

    def test_very_severe_social_phobia_ceiling(self) -> None:
        # All items maximum — worst possible presentation.
        r = score_spin(_ceil_items())
        assert r.total == 68
        assert r.severity == "very_severe"

    def test_post_relapse_shame_escalation_pattern(self) -> None:
        # Stewart 1998: fear-of-negative-evaluation → shame →
        # post-relapse escalation; high total expected.
        items = _items(55)
        r = score_spin(items)
        assert r.severity == "very_severe"

    def test_cannabis_self_medication_very_severe(self) -> None:
        # Buckner 2008 cannabis extension: very severe social anxiety
        # → cannabis use for anticipatory fear management.
        items = _items(52)
        r = score_spin(items)
        assert r.severity == "very_severe"

    def test_avoidance_isolation_escalation_severe(self) -> None:
        # Morris 2005: avoidance → social isolation → drinking alone;
        # severe SPIN + AUDIT signal.
        items = _items(43)
        r = score_spin(items)
        assert r.severity == "severe"

    def test_direction_higher_is_more_anxiety(self) -> None:
        # SPIN is in the "HIGHER = worse" direction family.
        r_low = score_spin(_items(10))
        r_high = score_spin(_items(50))
        assert r_high.total > r_low.total

    def test_rci_determinism(self) -> None:
        # Same response set → same total every call (no randomness).
        items = [1, 2, 3, 2, 1, 0, 4, 3, 2, 1, 0, 1, 2, 3, 4, 2, 1]
        assert len(items) == 17
        r1 = score_spin(items)
        r2 = score_spin(items)
        assert r1.total == r2.total
        assert r1.severity == r2.severity

    def test_spin_phq9_depression_comorbidity(self) -> None:
        # Fehm 2005: social anxiety + depression bidirectional loop.
        # SPIN severe → severity consistent.
        items = _items(44)
        r = score_spin(items)
        assert r.severity == "severe"

    def test_spin_adhd_rejection_sensitive(self) -> None:
        # Biederman 2006: ADHD + social anxiety via rejection-sensitive
        # dysphoria; SPIN moderate to severe range.
        items = _items(37)
        r = score_spin(items)
        assert r.severity == "moderate"


# ---------------------------------------------------------------------------
# TestInvariants
# ---------------------------------------------------------------------------

class TestInvariants:
    def test_items_preserved_verbatim(self) -> None:
        raw = [0, 1, 2, 3, 4, 3, 2, 1, 0, 1, 2, 3, 4, 3, 2, 1, 0]
        assert len(raw) == 17
        r = score_spin(raw)
        assert r.items == tuple(raw)

    def test_total_equals_sum_of_items(self) -> None:
        raw = [1, 2, 0, 3, 4, 1, 2, 3, 0, 1, 2, 1, 0, 4, 3, 2, 1]
        assert len(raw) == 17
        r = score_spin(raw)
        assert r.total == sum(raw)

    def test_lower_bound_zero(self) -> None:
        r = score_spin(_floor_items())
        assert r.total == 0

    def test_upper_bound_68(self) -> None:
        r = score_spin(_ceil_items())
        assert r.total == 68

    def test_severity_band_matches_threshold_lookup(self) -> None:
        for total in range(0, 69):
            items = _items(total)
            r = score_spin(items)
            assert r.total == total
            expected: str | None = None
            for upper, label in SPIN_SEVERITY_THRESHOLDS:
                if total <= upper:
                    expected = label
                    break
            assert r.severity == expected


# ---------------------------------------------------------------------------
# TestEdgeCases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_tuple_input_accepted(self) -> None:
        items = tuple([0] * ITEM_COUNT)
        r = score_spin(items)
        assert r.total == 0

    def test_generator_input_accepted(self) -> None:
        r = score_spin(x for x in ([0] * ITEM_COUNT))
        assert r.total == 0

    def test_out_of_range_error_message_cites_bounds(self) -> None:
        items: list = [2] * ITEM_COUNT
        items[6] = 5
        with pytest.raises(InvalidResponseError, match="0-4"):
            score_spin(items)

    def test_complex_object_raises(self) -> None:
        items: list = [1] * ITEM_COUNT
        items[9] = complex(2, 0)
        with pytest.raises(InvalidResponseError):
            score_spin(items)

    def test_does_not_mutate_input(self) -> None:
        original = list(range(ITEM_COUNT))  # [0,1,2,...,16] but max=4 — fix
        # Items within range: repeat 0-4 pattern
        raw = [i % (ITEM_MAX + 1) for i in range(ITEM_COUNT)]
        snapshot = raw[:]
        score_spin(raw)
        assert raw == snapshot

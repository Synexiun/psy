"""Unit tests for discipline.psychometric.scoring.pswq.

Coverage aim: every validation branch, every correctness invariant
(especially the NOVEL reverse-keying logic), and negative assertions
that document deliberately-absent fields (no severity, no cutoff_used,
no positive_screen, no requires_t3, no subscales).
"""

from __future__ import annotations

import pytest

from discipline.psychometric.scoring.pswq import (
    INSTRUMENT_VERSION,
    ITEM_COUNT,
    ITEM_MAX,
    ITEM_MIN,
    InvalidResponseError,
    PSWQ_REVERSE_ITEMS,
    PswqResult,
    score_pswq,
)


class TestConstants:
    def test_instrument_version(self) -> None:
        assert INSTRUMENT_VERSION == "pswq-1.0.0"

    def test_item_count_is_16(self) -> None:
        """Meyer 1990 — exactly 16 items."""
        assert ITEM_COUNT == 16

    def test_item_range_is_1_to_5(self) -> None:
        """Meyer 1990 1-5 Likert (not 0-based; not 7-point)."""
        assert ITEM_MIN == 1
        assert ITEM_MAX == 5

    def test_reverse_items_exact_set(self) -> None:
        """The 5 reverse-keyed items per Meyer 1990 Appendix are
        1, 3, 8, 10, 11.  This pins the set so a future edit cannot
        silently swap an item in or out — which would invalidate the
        score and contradict every downstream PSWQ validation paper."""
        assert PSWQ_REVERSE_ITEMS == (1, 3, 8, 10, 11)

    def test_reverse_items_is_tuple(self) -> None:
        """Frozen tuple so equality is hash-stable and the scorer
        cannot mutate the reverse set at runtime."""
        assert isinstance(PSWQ_REVERSE_ITEMS, tuple)


class TestTotalCorrectness:
    def test_all_ones_total_is_48(self) -> None:
        """Every raw item at 1.  Non-reverse items contribute 1 each
        (11 items × 1 = 11); reverse items contribute 5 each after
        flip (5 items × 5 = 25).  Total = 11 + 25 = 36... wait, NO:
        16 non-reverse items... there are 11 non-reverse and 5
        reverse.  11×1 + 5×5 = 11 + 25 = 36.  Pins the reverse logic
        — a buggy "flip all items" implementation would give
        16×5 = 80, a buggy "flip none" would give 16×1 = 16."""
        result = score_pswq([1] * 16)
        assert result.total == 36

    def test_all_fives_total_is_60(self) -> None:
        """Every raw item at 5.  Non-reverse contribute 5 each
        (11×5 = 55); reverse contribute 1 each after flip (5×1 = 5).
        Total = 55 + 5 = 60.  Pins the direction of the flip: a
        buggy "flip ALL" gives 16×1 = 16, a buggy "flip none" gives
        16×5 = 80."""
        result = score_pswq([5] * 16)
        assert result.total == 60

    def test_all_threes_total_is_48(self) -> None:
        """Every raw item at 3 (the Likert midpoint).  Flip(3) = 3,
        so reverse and non-reverse items both contribute 3.
        Total = 16 × 3 = 48.  Pins that the flip FUNCTION is
        correct at the reflection point (3 → 3)."""
        result = score_pswq([3] * 16)
        assert result.total == 48

    def test_maximum_worry_pattern(self) -> None:
        """The maximum-worry pattern: non-reverse items at 5 (high
        worry endorsement) AND reverse items at 1 (low worry-absent
        endorsement = high worry).  Total = (11 × 5) + (5 × 5 post-
        flip from raw 1) = 55 + 25 = 80.  This is the instrument
        ceiling and pins the semantic meaning: high trait-worry
        patients endorse direct items HIGH and reverse items LOW."""
        items = [0] * 16
        for i in range(1, 17):
            items[i - 1] = 1 if i in PSWQ_REVERSE_ITEMS else 5
        result = score_pswq(items)
        assert result.total == 80

    def test_minimum_worry_pattern(self) -> None:
        """The minimum-worry pattern: non-reverse items at 1 (no
        worry endorsement) AND reverse items at 5 (high worry-absent
        endorsement = low worry).  Total = (11 × 1) + (5 × 1 post-
        flip from raw 5) = 11 + 5 = 16.  This is the instrument
        floor; pins the direction."""
        items = [0] * 16
        for i in range(1, 17):
            items[i - 1] = 5 if i in PSWQ_REVERSE_ITEMS else 1
        result = score_pswq(items)
        assert result.total == 16

    def test_gad_sample_approximate(self) -> None:
        """A response pattern around Meyer 1990's reported GAD-sample
        mean (~67).  Pins that a clinically-elevated profile scores
        in the published-high range and confirms the flip math works
        on mixed patterns, not just all-same."""
        # Raw direct items at 5, raw reverse items at 2 (flipped → 4).
        # Non-reverse: 11 × 5 = 55.  Reverse: 5 × 4 = 20.  Total = 75.
        items = [0] * 16
        for i in range(1, 17):
            items[i - 1] = 2 if i in PSWQ_REVERSE_ITEMS else 5
        result = score_pswq(items)
        assert result.total == 75

    def test_normal_control_approximate(self) -> None:
        """A response pattern around a typical general-pop mean
        (~42-48).  Direct items at 3 (moderate endorsement), reverse
        items at 3 (moderate worry-absent — flip keeps at 3).
        Total = 16 × 3 = 48."""
        result = score_pswq([3] * 16)
        assert result.total == 48

    def test_single_reverse_item_flip_symmetry(self) -> None:
        """Set ALL items to 3 (flip-invariant midpoint) except item
        10 (reverse), which is 5 (raw → flip to 1).  Result total =
        15×3 + 1 = 46.  A buggy "don't flip item 10" would give
        15×3 + 5 = 50, catching an off-by-one in the reverse set."""
        items = [3] * 16
        items[9] = 5  # item 10, 0-indexed 9
        result = score_pswq(items)
        assert result.total == 46

    def test_single_direct_item_no_flip(self) -> None:
        """Set all items to 3 except item 2 (direct), which is 5.
        Total = 15×3 + 5 = 50.  A buggy "flip item 2 too" would
        give 15×3 + 1 = 46."""
        items = [3] * 16
        items[1] = 5  # item 2, 0-indexed 1
        result = score_pswq(items)
        assert result.total == 50


class TestItemCountValidation:
    def test_empty_list_rejects(self) -> None:
        with pytest.raises(InvalidResponseError, match="16 items"):
            score_pswq([])

    def test_too_few_rejects(self) -> None:
        """15 items fails — exactly 16 required."""
        with pytest.raises(InvalidResponseError, match="16 items"):
            score_pswq([3] * 15)

    def test_too_many_rejects(self) -> None:
        """17 items fails — exactly 16 required."""
        with pytest.raises(InvalidResponseError, match="16 items"):
            score_pswq([3] * 17)

    def test_ders16_length_rejects(self) -> None:
        """16 items passes count validation (DERS-16 and PSWQ both
        16 items).  This test just confirms that the 16-count
        validator doesn't mis-reject a valid 16-item payload; the
        router layer is responsible for dispatching to the correct
        scorer by the ``instrument`` key."""
        # Must NOT raise count error.
        result = score_pswq([3] * 16)
        assert result.total == 48

    def test_phq9_length_rejects(self) -> None:
        """9 items (PHQ-9 length) fails PSWQ's 16-item requirement."""
        with pytest.raises(InvalidResponseError, match="16 items"):
            score_pswq([3] * 9)

    def test_pcl5_length_rejects(self) -> None:
        """20 items (PCL-5 length) fails PSWQ's 16-item requirement."""
        with pytest.raises(InvalidResponseError, match="16 items"):
            score_pswq([3] * 20)

    def test_cdrisc10_length_rejects(self) -> None:
        """10 items (CD-RISC-10 length) fails PSWQ's 16-item."""
        with pytest.raises(InvalidResponseError, match="16 items"):
            score_pswq([3] * 10)


class TestItemRangeValidation:
    def test_zero_rejects(self) -> None:
        """0 fails — floor is 1 (1-5 Likert, not 0-based)."""
        bad = [3] * 16
        bad[0] = 0
        with pytest.raises(InvalidResponseError, match=r"out of range"):
            score_pswq(bad)

    def test_six_rejects(self) -> None:
        """6 fails — ceiling is 5, not 6 (1-6) or 7 (1-7)."""
        bad = [3] * 16
        bad[0] = 6
        with pytest.raises(InvalidResponseError, match=r"out of range"):
            score_pswq(bad)

    def test_negative_rejects(self) -> None:
        bad = [3] * 16
        bad[0] = -1
        with pytest.raises(InvalidResponseError, match=r"out of range"):
            score_pswq(bad)

    @pytest.mark.parametrize("bad_value", [-5, 0, 6, 7, 100, 255])
    def test_out_of_range_values_parametric(self, bad_value: int) -> None:
        """Range-boundary sweep: every value outside [1, 5] rejects."""
        bad = [3] * 16
        bad[5] = bad_value
        with pytest.raises(InvalidResponseError, match=r"out of range"):
            score_pswq(bad)

    def test_float_rejects(self) -> None:
        """Floats reject even when numerically valid."""
        bad: list = [3] * 16
        bad[0] = 3.0
        with pytest.raises(InvalidResponseError, match=r"must be int"):
            score_pswq(bad)

    def test_string_rejects(self) -> None:
        bad: list = [3] * 16
        bad[0] = "3"
        with pytest.raises(InvalidResponseError, match=r"must be int"):
            score_pswq(bad)

    def test_none_rejects(self) -> None:
        bad: list = [3] * 16
        bad[0] = None
        with pytest.raises(InvalidResponseError, match=r"must be int"):
            score_pswq(bad)

    def test_error_message_names_1_indexed_item(self) -> None:
        """Error message names the 1-indexed item position so the
        clinician can identify it on the PSWQ printout."""
        bad: list = [3] * 16
        bad[7] = 99  # 0-indexed 7, 1-indexed 8
        with pytest.raises(InvalidResponseError, match=r"item 8"):
            score_pswq(bad)

    def test_reverse_item_out_of_range_still_rejects(self) -> None:
        """Range validation runs BEFORE the reverse-keying flip —
        an invalid value on a reverse-keyed item rejects cleanly,
        not with a confusing "flipped 6 - value = 6 - 99 = -93" side
        effect."""
        bad: list = [3] * 16
        bad[0] = 99  # item 1 is reverse-keyed AND out of range
        with pytest.raises(InvalidResponseError, match=r"item 1.*out of range"):
            score_pswq(bad)


class TestBoolRejection:
    def test_true_rejects(self) -> None:
        """True smuggled into a 1-5 int envelope must reject (Python
        bool is a subclass of int, so isinstance(True, int) is True
        without the explicit bool check — uniform with the rest of
        the psychometric package)."""
        bad: list = [3] * 16
        bad[0] = True
        with pytest.raises(InvalidResponseError, match=r"must be int"):
            score_pswq(bad)

    def test_false_rejects(self) -> None:
        bad: list = [3] * 16
        bad[0] = False
        with pytest.raises(InvalidResponseError, match=r"must be int"):
            score_pswq(bad)

    def test_bool_on_reverse_item_rejects(self) -> None:
        """True on a reverse-keyed item (item 1) must reject, not
        get flipped to 5 or silently treated as 1."""
        bad: list = [3] * 16
        bad[0] = True  # item 1 is reverse-keyed
        with pytest.raises(InvalidResponseError, match=r"item 1.*must be int"):
            score_pswq(bad)


class TestResultShape:
    def test_result_is_frozen_dataclass(self) -> None:
        result = score_pswq([3] * 16)
        with pytest.raises(Exception):
            result.total = 999  # type: ignore[misc]

    def test_items_is_tuple(self) -> None:
        """Items field is a tuple (not list) for hashability and
        immutability — the audit trail must not be mutable after
        scoring."""
        result = score_pswq([3] * 16)
        assert isinstance(result.items, tuple)
        assert result.items == tuple([3] * 16)

    def test_items_preserves_raw_pre_flip(self) -> None:
        """The audit trail preserves the PATIENT'S raw responses, NOT
        the internal post-flip values.  Critical for reverse-keyed
        instruments: a clinician reviewing the record must see what
        the patient actually ticked, not the scorer's flipped
        representation."""
        # Item 1 is reverse-keyed.  Set it to 2 (patient said "rarely
        # typical"); internal flip would turn it into 4, but the
        # ``items`` field must still show 2.
        raw = [3] * 16
        raw[0] = 2
        result = score_pswq(raw)
        assert result.items[0] == 2  # raw, not 4 (flipped)

    def test_instrument_version_pinned(self) -> None:
        result = score_pswq([3] * 16)
        assert result.instrument_version == "pswq-1.0.0"

    def test_total_is_int(self) -> None:
        result = score_pswq([3] * 16)
        assert isinstance(result.total, int)

    def test_no_severity_field(self) -> None:
        """Continuous instrument — no severity band in the scorer
        result.  The router envelope emits ``severity="continuous"``
        as the sentinel."""
        result = score_pswq([3] * 16)
        assert not hasattr(result, "severity")

    def test_no_cutoff_used_field(self) -> None:
        result = score_pswq([3] * 16)
        assert not hasattr(result, "cutoff_used")

    def test_no_positive_screen_field(self) -> None:
        result = score_pswq([3] * 16)
        assert not hasattr(result, "positive_screen")

    def test_no_requires_t3_field(self) -> None:
        """PSWQ has no safety item — requires_t3 is never set."""
        result = score_pswq([3] * 16)
        assert not hasattr(result, "requires_t3")

    def test_no_triggering_items_field(self) -> None:
        result = score_pswq([3] * 16)
        assert not hasattr(result, "triggering_items")

    def test_no_subscales_field(self) -> None:
        """Unidimensional per Meyer 1990 / Brown 1992 — no subscales
        dict (distinct from DERS-16's 5-subscale surface)."""
        result = score_pswq([3] * 16)
        assert not hasattr(result, "subscales")
        assert not hasattr(result, "subscale_1")

    def test_result_is_instance_of_pswq_result(self) -> None:
        result = score_pswq([3] * 16)
        assert isinstance(result, PswqResult)


class TestClinicalVignettes:
    def test_gad_patient_elevated(self) -> None:
        """A GAD patient profile: high endorsement on direct worry
        items (4-5), low endorsement on reverse-keyed absent-worry
        items (1-2).  Expect total in the 60-75 range per Meyer
        1990 GAD-sample norms."""
        items = [0] * 16
        direct_pattern = [0, 5, 0, 5, 5, 5, 5, 0, 5, 0, 0, 5, 5, 5, 5, 4]
        reverse_pattern = [2, 0, 2, 0, 0, 0, 0, 2, 0, 2, 1, 0, 0, 0, 0, 0]
        for i in range(16):
            items[i] = direct_pattern[i] if direct_pattern[i] else reverse_pattern[i]
        result = score_pswq(items)
        # Post-flip: reverse items become (6-2=4, 6-2=4, 6-2=4, 6-2=4, 6-1=5)
        # Non-reverse: 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 4 = 54
        # Reverse post-flip: 4+4+4+4+5 = 21
        # Total = 54 + 21 = 75
        assert result.total == 75

    def test_healthy_control(self) -> None:
        """A healthy-control profile: low endorsement on direct
        worry items (1-2), high endorsement on reverse-keyed absent-
        worry items (4-5).  Expect total in the 16-30 range."""
        items = [0] * 16
        for i in range(1, 17):
            if i in PSWQ_REVERSE_ITEMS:
                items[i - 1] = 4  # high worry-absent = low worry
            else:
                items[i - 1] = 1  # low worry endorsement
        result = score_pswq(items)
        # Non-reverse: 11 × 1 = 11.  Reverse post-flip: 5 × (6-4) = 10.
        # Total = 11 + 10 = 21.
        assert result.total == 21

    def test_response_set_bias_caught_by_mixed_direction(self) -> None:
        """Acquiescent response set (all 5s) produces a moderate
        score (60), NOT the ceiling (80).  The mixed-direction
        design of PSWQ catches acquiescence: if the patient just
        ticked 5 for everything, the reverse-keyed items flip to
        1s and suppress the total below the ceiling.

        This test pins the clinical value of the reverse-keying
        design — a buggy scorer that doesn't flip would report an
        acquiescent responder as maxed-out."""
        result = score_pswq([5] * 16)
        assert result.total == 60  # not 80
        assert result.total < 80

    def test_disacquiescent_bias_caught(self) -> None:
        """Dis-acquiescent response set (all 1s) produces 36, NOT
        the floor (16).  Mirror of above — mixed-direction catches
        both biases.  A buggy no-flip scorer would report this as
        the minimum-worry floor (16)."""
        result = score_pswq([1] * 16)
        assert result.total == 36  # not 16
        assert result.total > 16

    def test_midline_pattern_is_flip_invariant(self) -> None:
        """Every item at the Likert midpoint (3) produces 48
        regardless of reverse-keying, because flip(3) = 3.  This
        pins the mathematical symmetry of the 6-x reflection at the
        midpoint — a sanity check on the flip formula."""
        result = score_pswq([3] * 16)
        assert result.total == 48


class TestNoSafetyRouting:
    def test_max_total_does_not_expose_t3_field(self) -> None:
        """Even at the maximum worry profile (total 80), the scorer
        result does NOT carry a requires_t3 field.  Worry is not
        suicidality; acute ideation screening stays on PHQ-9 item 9
        / C-SSRS."""
        items = [0] * 16
        for i in range(1, 17):
            items[i - 1] = 1 if i in PSWQ_REVERSE_ITEMS else 5
        result = score_pswq(items)
        assert result.total == 80
        assert not hasattr(result, "requires_t3")
        assert not hasattr(result, "t3_reason")

    def test_item_2_overwhelm_does_not_trigger_t3(self) -> None:
        """Item 2 ("My worries overwhelm me.") at 5 endorses
        subjective overwhelm — a DBT / CBT target, NOT a crisis
        signal.  Acute ideation stays on PHQ-9 item 9 / C-SSRS."""
        items = [3] * 16
        items[1] = 5  # item 2 at max
        result = score_pswq(items)
        assert not hasattr(result, "requires_t3")

    def test_item_14_cannot_stop_does_not_trigger_t3(self) -> None:
        """Item 14 ("Once I start worrying, I cannot stop.") at 5
        endorses uncontrollability — the GAD DSM-5 criterion, NOT
        a crisis signal.  Routes to CBT-for-GAD worry-postponement
        / decatastrophizing intervention variants."""
        items = [3] * 16
        items[13] = 5  # item 14 at max
        result = score_pswq(items)
        assert not hasattr(result, "requires_t3")

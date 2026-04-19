"""Scoring-layer tests for WEMWBS (Tennant 2007).

The Warwick-Edinburgh Mental Wellbeing Scale — 14-item self-report
measure of mental wellbeing, 1-5 Likert per item, total 14-70,
HIGHER = MORE WELLBEING.  Unidimensional per Tennant 2007 CFA
(single-factor CFI = 0.93, RMSEA = 0.084).  No reverse-keying —
all items positively worded.  No published clinical cutpoints
(severity = "continuous" sentinel; trajectory layer applies
Jacobson-Truax RCI).

Coverage matrix:
- Constants pinned to Tennant 2007 (item count 14, range 1-5,
  no subscales, instrument_version "wemwbs-1.0.0").
- Total correctness across the ceiling, floor, and representative
  interior values.
- Severity always "continuous" regardless of total.
- Item-count validation (≠ 14 rejected with proper messages).
- Item-range validation (0 and 6 rejected; -1 rejected;
  positional error message names the 1-indexed position).
- Item-type validation (bool rejected BEFORE range check per
  CLAUDE.md standing rule; string and float rejected).
- Result typing — frozen dataclass, tuple-of-int items, preserves
  RAW responses.
- Clinical vignettes (Tennant 2007 population norms; Keyes 2002
  languishing/flourishing framing; Seligman 2011 post-recovery
  monitoring).
"""

from __future__ import annotations

import pytest

from discipline.psychometric.scoring.wemwbs import (
    INSTRUMENT_VERSION,
    ITEM_COUNT,
    ITEM_MAX,
    ITEM_MIN,
    InvalidResponseError,
    WemwbsResult,
    score_wemwbs,
)


class TestConstants:
    """WEMWBS constants pinned to Tennant 2007."""

    def test_item_count_is_fourteen(self) -> None:
        assert ITEM_COUNT == 14

    def test_item_range_is_1_to_5(self) -> None:
        assert ITEM_MIN == 1
        assert ITEM_MAX == 5

    def test_instrument_version_pinned(self) -> None:
        assert INSTRUMENT_VERSION == "wemwbs-1.0.0"


class TestTotalCorrectness:
    """Total is sum of 14 items, range 14-70."""

    def test_all_ones_floor(self) -> None:
        """Minimum endorsement: total = 14 (14 × 1)."""
        result = score_wemwbs([1] * 14)
        assert result.total == 14

    def test_all_fives_ceiling(self) -> None:
        """Maximum endorsement: total = 70 (14 × 5)."""
        result = score_wemwbs([5] * 14)
        assert result.total == 70

    def test_all_threes_midpoint(self) -> None:
        """Midpoint endorsement: total = 42 (14 × 3)."""
        result = score_wemwbs([3] * 14)
        assert result.total == 42

    def test_population_mean_profile_tennant_2007(self) -> None:
        """Tennant 2007 population sample mean 50.7.  Build a
        vector totaling 51 (close to the norm)."""
        items = [4] * 9 + [3] * 5  # 36 + 15 = 51
        result = score_wemwbs(items)
        assert result.total == 51

    def test_asymmetric_vector(self) -> None:
        """Non-uniform responses — confirms linear sum, no
        weighting."""
        items = [1, 5, 1, 5, 1, 5, 1, 5, 1, 5, 1, 5, 1, 5]
        result = score_wemwbs(items)
        assert result.total == sum(items)
        assert result.total == 42


class TestNoReverseKeying:
    """WEMWBS is positively worded throughout — no reverse-keying."""

    def test_ceiling_on_every_item_yields_max(self) -> None:
        """Marsh 1996 method-artifact concern: WEMWBS specifically
        avoids reverse-keyed items.  High raw on every item must
        yield the MAX total (not a mid-range value as would occur
        with balanced positive/negative wording like RSES)."""
        result = score_wemwbs([5] * 14)
        assert result.total == 70

    def test_floor_on_every_item_yields_min(self) -> None:
        result = score_wemwbs([1] * 14)
        assert result.total == 14

    def test_raw_items_preserved_identically(self) -> None:
        """No transformation of raw responses — items field is
        byte-identical to input."""
        raw = [1, 2, 3, 4, 5, 4, 3, 2, 1, 2, 3, 4, 5, 4]
        result = score_wemwbs(raw)
        assert result.items == tuple(raw)


class TestSeverityContinuous:
    """Severity is the ``"continuous"`` sentinel at all totals."""

    @pytest.mark.parametrize("items,expected_total", [
        ([1] * 14, 14),
        ([3] * 14, 42),
        ([5] * 14, 70),
        ([2] * 14, 28),
        ([4] * 14, 56),
    ])
    def test_severity_always_continuous(
        self, items: list[int], expected_total: int
    ) -> None:
        result = score_wemwbs(items)
        assert result.total == expected_total
        assert result.severity == "continuous"

    def test_no_clinical_bands_introduced(self) -> None:
        """Stewart-Brown 2012 preliminary tertile thresholds are
        NOT baked into the scorer.  Severity remains literal
        ``"continuous"`` even at values that would cross those
        thresholds."""
        # Stewart-Brown's preliminary "very low" cutoff was ~40.
        # Our scorer emits "continuous" not "very_low".
        low = score_wemwbs([2] * 14)  # total 28
        mid = score_wemwbs([3] * 14)  # total 42
        high = score_wemwbs([5] * 14)  # total 70
        assert low.severity == "continuous"
        assert mid.severity == "continuous"
        assert high.severity == "continuous"


class TestItemCountValidation:
    """Item-count rejections raise :class:`InvalidResponseError`."""

    def test_short_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="14"):
            score_wemwbs([3] * 13)

    def test_long_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="14"):
            score_wemwbs([3] * 15)

    def test_empty_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="14"):
            score_wemwbs([])

    def test_message_names_wemwbs(self) -> None:
        try:
            score_wemwbs([3] * 10)
        except InvalidResponseError as exc:
            assert "WEMWBS" in str(exc)
            assert "14" in str(exc)
        else:
            pytest.fail("Expected InvalidResponseError")


class TestItemRangeValidation:
    """Item-range rejections raise :class:`InvalidResponseError`."""

    def test_below_range_rejected(self) -> None:
        items = [3] * 14
        items[0] = 0  # Below 1-5 range.
        with pytest.raises(InvalidResponseError, match="1-5"):
            score_wemwbs(items)

    def test_above_range_rejected(self) -> None:
        items = [3] * 14
        items[5] = 6  # Above 1-5 range.
        with pytest.raises(InvalidResponseError, match="1-5"):
            score_wemwbs(items)

    def test_negative_rejected(self) -> None:
        items = [3] * 14
        items[13] = -1
        with pytest.raises(InvalidResponseError, match="1-5"):
            score_wemwbs(items)

    def test_range_message_names_position(self) -> None:
        """Error message identifies the 1-indexed position of
        the offending item so clinicians can locate it in the
        response record."""
        items = [3] * 14
        items[4] = 7
        try:
            score_wemwbs(items)
        except InvalidResponseError as exc:
            assert "5" in str(exc)
            assert "1-5" in str(exc)
        else:
            pytest.fail("Expected InvalidResponseError")

    def test_first_invalid_reported(self) -> None:
        """If multiple items are out of range, the first is
        reported — matches the single-item-at-a-time validation
        pattern across the psychometric module."""
        items = [3] * 14
        items[2] = 0
        items[7] = 6
        with pytest.raises(InvalidResponseError) as exc_info:
            score_wemwbs(items)
        assert "3" in str(exc_info.value)  # 1-indexed position 3


class TestItemTypeValidation:
    """Bool / string / float items raise :class:`InvalidResponseError`."""

    def test_bool_true_rejected(self) -> None:
        """CLAUDE.md standing rule: bool rejected BEFORE the range
        check even though True would coerce to 1 (valid range).
        At the wire layer Pydantic coerces JSON ``true`` → 1 and
        the scorer never sees the bool; here at the scorer level
        we test direct Python invocation with a bool, which MUST
        reject."""
        items: list = [3] * 14
        items[0] = True
        with pytest.raises(InvalidResponseError, match="int"):
            score_wemwbs(items)

    def test_bool_false_rejected(self) -> None:
        items: list = [3] * 14
        items[0] = False
        with pytest.raises(InvalidResponseError, match="int"):
            score_wemwbs(items)

    def test_string_rejected(self) -> None:
        items: list = [3] * 14
        items[0] = "3"
        with pytest.raises(InvalidResponseError, match="int"):
            score_wemwbs(items)

    def test_float_rejected(self) -> None:
        items: list = [3] * 14
        items[0] = 3.0
        with pytest.raises(InvalidResponseError, match="int"):
            score_wemwbs(items)

    def test_none_rejected(self) -> None:
        items: list = [3] * 14
        items[0] = None
        with pytest.raises(InvalidResponseError, match="int"):
            score_wemwbs(items)


class TestResultTyping:
    """Result is a frozen dataclass with the correct field types."""

    def test_returns_wemwbs_result(self) -> None:
        result = score_wemwbs([3] * 14)
        assert isinstance(result, WemwbsResult)

    def test_total_is_int(self) -> None:
        result = score_wemwbs([3] * 14)
        assert isinstance(result.total, int)

    def test_severity_is_continuous_literal(self) -> None:
        result = score_wemwbs([3] * 14)
        assert result.severity == "continuous"

    def test_items_is_tuple_of_ints(self) -> None:
        result = score_wemwbs([2, 3, 4, 1, 5, 3, 2, 4, 5, 1, 3, 2, 4, 5])
        assert isinstance(result.items, tuple)
        assert all(isinstance(item, int) for item in result.items)
        assert len(result.items) == 14

    def test_frozen_dataclass(self) -> None:
        result = score_wemwbs([3] * 14)
        with pytest.raises((AttributeError, TypeError)):
            result.total = 100  # type: ignore[misc]

    def test_instrument_version_default(self) -> None:
        result = score_wemwbs([3] * 14)
        assert result.instrument_version == "wemwbs-1.0.0"

    def test_items_preserve_raw_response(self) -> None:
        """Audit invariance: items field must be byte-identical
        to the raw response (no transformation, no reverse-keying,
        no mutation)."""
        raw = [1, 5, 1, 5, 2, 4, 2, 4, 3, 3, 3, 3, 1, 5]
        result = score_wemwbs(raw)
        assert result.items == tuple(raw)


class TestClinicalVignettes:
    """Clinical scenarios grounded in Tennant 2007 / Keyes 2002."""

    def test_flourishing_profile_seligman_2011(self) -> None:
        """Seligman 2011 flourishing profile — high endorsement
        across all wellbeing items.  Typical post-acute recovery
        ceiling."""
        result = score_wemwbs([5] * 14)
        assert result.total == 70
        assert result.severity == "continuous"

    def test_languishing_profile_keyes_2002(self) -> None:
        """Keyes 2002 languishing profile — uniformly low
        wellbeing endorsement.  The user could be simultaneously
        symptom-absent (PHQ-9 low, GAD-7 low) and yet register
        low WEMWBS; the platform's intervention-matching must
        detect this pattern."""
        result = score_wemwbs([1] * 14)
        assert result.total == 14
        assert result.severity == "continuous"

    def test_population_mean_profile_tennant_2007(self) -> None:
        """Tennant 2007 UK n = 348 population mean = 50.7 (SD
        8.8).  A user at total 51 is at population norm — not a
        clinical flag on its own; the RCI-based trajectory layer
        interprets direction of change rather than absolute
        value."""
        # Build a vector totaling 51.
        items = [4] * 9 + [3] * 5  # 36 + 15 = 51
        result = score_wemwbs(items)
        assert result.total == 51
        assert result.severity == "continuous"

    def test_scottish_population_mean_stewart_brown_2009(self) -> None:
        """Stewart-Brown 2009 Scottish n = 2,073 mean = 51.6
        (SD 8.7) — the two population norms agree within SEM,
        confirming cross-national stability."""
        items = [4] * 10 + [3] * 4  # 40 + 12 = 52
        result = score_wemwbs(items)
        assert result.total == 52

    def test_sub_one_sd_low_wellbeing(self) -> None:
        """One SD below Tennant 2007 mean: 50.7 - 8.8 = 41.9.
        Total 42 is the canonical "low wellbeing" anchor that
        epidemiological literature cites, but the scorer does
        NOT flag it as positive_screen or low_severity — that
        interpretation belongs at the rendering / analytics
        layer, not inside the instrument-scoring primitive."""
        result = score_wemwbs([3] * 14)
        assert result.total == 42
        assert result.severity == "continuous"

    def test_recovery_trajectory_early(self) -> None:
        """Early in recovery — user reports occasional wellbeing
        (item responses around 2-3) with no dominant high
        endorsements.  Jacobson-Truax RCI in the trajectory
        layer will compare to baseline."""
        items = [2, 2, 3, 2, 2, 3, 2, 3, 2, 2, 3, 2, 2, 3]
        result = score_wemwbs(items)
        assert result.total == 33
        assert result.severity == "continuous"

    def test_recovery_trajectory_late(self) -> None:
        """Late in recovery — user reports frequent wellbeing
        (item responses around 4-5).  RCI between early and
        late trajectories is the primary clinical signal."""
        items = [4, 5, 4, 4, 4, 5, 4, 4, 4, 5, 4, 4, 5, 4]
        result = score_wemwbs(items)
        assert result.total == 60
        assert result.severity == "continuous"

    def test_mixed_profile_interest_without_energy(self) -> None:
        """Mixed profile — user high on cognitive-evaluative
        items (items 6, 7, 10, 11) but low on energy and
        affective items (items 3, 5, 14).  Represents the 'I'm
        functioning but exhausted' pattern common in
        burnout-adjacent presentations."""
        items = [3, 4, 2, 3, 2, 5, 5, 4, 3, 5, 5, 3, 4, 2]
        result = score_wemwbs(items)
        assert result.total == 50
        # Despite the internal pattern, severity stays continuous —
        # the scorer doesn't parse profile shapes.
        assert result.severity == "continuous"

    def test_direction_higher_equals_more_wellbeing(self) -> None:
        """Direction guarantee: total 70 > total 14; higher
        number = more wellbeing.  Same direction as WHO-5 / BRS /
        LOT-R / RSES / MAAS / CD-RISC-10; OPPOSITE of PHQ-9 /
        GAD-7."""
        low = score_wemwbs([1] * 14)
        high = score_wemwbs([5] * 14)
        assert low.total < high.total
        assert low.total == 14
        assert high.total == 70

    def test_rci_determinism_identical_input_yields_identical_output(
        self,
    ) -> None:
        """Jacobson-Truax RCI assumes deterministic scoring.
        Identical input must yield identical output (total,
        severity, items, instrument_version)."""
        items = [3, 4, 2, 5, 1, 4, 3, 2, 5, 1, 4, 3, 2, 5]
        a = score_wemwbs(items)
        b = score_wemwbs(items)
        assert a == b

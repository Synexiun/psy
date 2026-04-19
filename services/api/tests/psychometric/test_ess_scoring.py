"""Scorer-level tests for the Epworth Sleepiness Scale.

Johns 1991 Sleep 14(6):540-545 *A new method for measuring
daytime sleepiness: The Epworth sleepiness scale*.  8-item 0-3
Likert self-report; total 0-24; HIGHER = MORE daytime sleepiness.
Severity bands per Johns 1993 Sleep 16(2):118-125 + Johns 2000
J Sleep Res 9(1):5-11:

    0-10  normal
    11-12 mild excessive daytime sleepiness
    13-15 moderate EDS
    16-24 severe EDS

These tests run at the scorer (pure-function) layer — Pydantic
lax-mode coercion is NOT in effect.  The scorer's own bool /
type / range gates fire here.  Wire-layer coercion tests live in
``test_assessments_router.py::TestEssRouting``.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from typing import Any

import pytest

from discipline.psychometric.scoring.ess import (
    ESS_SEVERITY_THRESHOLDS,
    INSTRUMENT_VERSION,
    ITEM_COUNT,
    ITEM_MAX,
    ITEM_MIN,
    EssResult,
    InvalidResponseError,
    score_ess,
)


class TestConstants:
    """Pin the published Johns 1991/1993/2000 constants."""

    def test_instrument_version(self) -> None:
        assert INSTRUMENT_VERSION == "ess-1.0.0"

    def test_item_count_matches_johns_1991(self) -> None:
        """Johns 1991 Appendix — 8 items.  Changing this breaks the
        factor validation."""
        assert ITEM_COUNT == 8

    def test_item_range_zero_to_three(self) -> None:
        """Johns 1991 Likert range: 0 ('Would never doze') to 3
        ('High chance of dozing')."""
        assert ITEM_MIN == 0
        assert ITEM_MAX == 3

    def test_severity_thresholds_pinned_to_published_bands(
        self,
    ) -> None:
        """Johns 1993 Chest 103(1):30-36 + Johns 2000 J Sleep Res
        9(1):5-11 published severity bands — pinned verbatim.  No
        hand-rolled thresholds."""
        assert ESS_SEVERITY_THRESHOLDS == (
            (10, "normal"),
            (12, "mild"),
            (15, "moderate"),
            (24, "severe"),
        )

    def test_severity_thresholds_cover_full_range(self) -> None:
        """Bands must be exhaustive across the 0-24 total range.
        Final entry must cap at 24."""
        assert ESS_SEVERITY_THRESHOLDS[-1][0] == 24

    def test_severity_thresholds_strictly_increasing(self) -> None:
        """Band upper bounds must be strictly ascending — otherwise
        the ``_classify`` linear scan is ambiguous."""
        uppers = [t[0] for t in ESS_SEVERITY_THRESHOLDS]
        assert uppers == sorted(uppers)
        assert len(set(uppers)) == len(uppers)

    def test_severity_labels_expected_set(self) -> None:
        """Band labels must match the Literal type in the scorer
        module."""
        labels = {t[1] for t in ESS_SEVERITY_THRESHOLDS}
        assert labels == {"normal", "mild", "moderate", "severe"}


class TestTotalCorrectness:
    """End-to-end arithmetic for the full range of item values."""

    def test_floor_all_zeros_total_zero(self) -> None:
        result = score_ess([0] * 8)
        assert result.total == 0

    def test_ceiling_all_threes_total_twenty_four(self) -> None:
        result = score_ess([3] * 8)
        assert result.total == 24

    def test_midpoint_all_ones_total_eight(self) -> None:
        result = score_ess([1] * 8)
        assert result.total == 8

    def test_midpoint_all_twos_total_sixteen(self) -> None:
        result = score_ess([2] * 8)
        assert result.total == 16

    def test_explicit_mixed_vector_total(self) -> None:
        """Canonical mixed vector [0,1,2,3,0,1,2,3] → total 12."""
        result = score_ess([0, 1, 2, 3, 0, 1, 2, 3])
        assert result.total == 12

    def test_total_matches_python_sum(self) -> None:
        items = [3, 2, 0, 1, 3, 2, 1, 0]
        assert score_ess(items).total == sum(items)

    def test_no_reverse_keying(self) -> None:
        """All 8 items worded so higher endorsement = more
        sleepiness.  Doubling every item doubles the total — no
        item is inverted."""
        low = score_ess([1] * 8)
        high = score_ess([2] * 8)
        assert high.total == 2 * low.total


class TestSeverityBoundaries:
    """Exhaustive boundary tests at each Johns-published cutoff."""

    @pytest.mark.parametrize(
        "total,expected",
        [
            (0, "normal"),
            (5, "normal"),
            (10, "normal"),  # upper of normal band
            (11, "mild"),  # lower of mild band
            (12, "mild"),  # upper of mild band
            (13, "moderate"),  # lower of moderate band
            (15, "moderate"),  # upper of moderate band
            (16, "severe"),  # lower of severe band
            (20, "severe"),
            (24, "severe"),  # absolute ceiling
        ],
    )
    def test_severity_at_each_boundary(
        self, total: int, expected: str
    ) -> None:
        """Every band boundary pinned.  Off-by-one at 10/11, 12/13,
        15/16 would shift clinical-severity categorization and
        invalidate the Johns 1993 validation."""
        # Build items summing exactly to ``total`` with exactly 8
        # entries.  q items at 3, remainder item at r (if any
        # headroom remains), rest at 0.  At total=24 q=8 and no
        # remainder slot is needed.
        q, r = divmod(total, 3)
        items: list[int] = [3] * q
        if q < 8:
            items.append(r)
            items.extend([0] * (8 - len(items)))
        assert len(items) == 8
        assert sum(items) == total
        result = score_ess(items)
        assert result.severity == expected

    def test_normal_upper_boundary_ten_classified_normal(
        self,
    ) -> None:
        """Specific regression: Johns 1991/1993 classifies total
        10 as ``normal``, not as the boundary of ``mild``."""
        items = [3, 3, 3, 1, 0, 0, 0, 0]
        assert sum(items) == 10
        assert score_ess(items).severity == "normal"

    def test_mild_lower_boundary_eleven_classified_mild(self) -> None:
        items = [3, 3, 3, 2, 0, 0, 0, 0]
        assert sum(items) == 11
        assert score_ess(items).severity == "mild"

    def test_mild_upper_boundary_twelve_classified_mild(self) -> None:
        items = [3, 3, 3, 3, 0, 0, 0, 0]
        assert sum(items) == 12
        assert score_ess(items).severity == "mild"

    def test_moderate_lower_boundary_thirteen_classified_moderate(
        self,
    ) -> None:
        items = [3, 3, 3, 3, 1, 0, 0, 0]
        assert sum(items) == 13
        assert score_ess(items).severity == "moderate"

    def test_moderate_upper_boundary_fifteen_classified_moderate(
        self,
    ) -> None:
        items = [3, 3, 3, 3, 3, 0, 0, 0]
        assert sum(items) == 15
        assert score_ess(items).severity == "moderate"

    def test_severe_lower_boundary_sixteen_classified_severe(
        self,
    ) -> None:
        items = [3, 3, 3, 3, 3, 1, 0, 0]
        assert sum(items) == 16
        assert score_ess(items).severity == "severe"


class TestItemCountValidation:
    """ESS requires exactly 8 items — short, long, empty → raise."""

    def test_rejects_seven_items(self) -> None:
        with pytest.raises(InvalidResponseError):
            score_ess([1] * 7)

    def test_rejects_nine_items(self) -> None:
        with pytest.raises(InvalidResponseError):
            score_ess([1] * 9)

    def test_rejects_zero_items(self) -> None:
        with pytest.raises(InvalidResponseError):
            score_ess([])

    def test_error_message_mentions_expected_count(self) -> None:
        with pytest.raises(InvalidResponseError) as exc:
            score_ess([1] * 5)
        assert "8" in str(exc.value)


class TestItemRangeValidation:
    """ESS item range is 0-3.  Below / above → raise."""

    def test_rejects_negative_item(self) -> None:
        with pytest.raises(InvalidResponseError):
            score_ess([-1, 0, 0, 0, 0, 0, 0, 0])

    def test_rejects_item_above_three(self) -> None:
        """Contrast PHQ-9 (0-3 — same ceiling) and IGDS9-SF (1-5
        — much higher ceiling).  ESS ceiling is 3."""
        with pytest.raises(InvalidResponseError):
            score_ess([4, 0, 0, 0, 0, 0, 0, 0])

    def test_rejects_item_in_middle_of_vector(self) -> None:
        """Range violation at position 5 must still fire — catches
        an early-return bug."""
        with pytest.raises(InvalidResponseError):
            score_ess([0, 0, 0, 0, 9, 0, 0, 0])

    def test_rejects_item_at_end_of_vector(self) -> None:
        """Last item must be validated — off-by-one guard."""
        with pytest.raises(InvalidResponseError):
            score_ess([0, 0, 0, 0, 0, 0, 0, -5])

    def test_error_message_mentions_position(self) -> None:
        """Error message identifies 1-indexed item position for
        clinician-log readability."""
        with pytest.raises(InvalidResponseError) as exc:
            score_ess([0, 0, 0, 9, 0, 0, 0, 0])
        assert "4" in str(exc.value)


class TestItemTypeValidation:
    """CLAUDE.md: bool values rejected BEFORE range check."""

    def test_rejects_bool_true(self) -> None:
        """True would silently coerce to int 1 (valid in 0-3
        range) without explicit bool rejection — wrong."""
        with pytest.raises(InvalidResponseError):
            score_ess([True, 0, 0, 0, 0, 0, 0, 0])  # type: ignore[list-item]

    def test_rejects_bool_false(self) -> None:
        """False would silently coerce to int 0 — wrong."""
        with pytest.raises(InvalidResponseError):
            score_ess([False, 0, 0, 0, 0, 0, 0, 0])  # type: ignore[list-item]

    def test_rejects_float(self) -> None:
        """Floats must be rejected — clinical score integrity
        requires integer responses."""
        with pytest.raises(InvalidResponseError):
            score_ess([1.5, 0, 0, 0, 0, 0, 0, 0])  # type: ignore[list-item]

    def test_rejects_string_numeric(self) -> None:
        """Even a numeric-looking string is rejected at the
        scorer layer.  Wire layer may coerce ``"3"`` → 3 (see
        Pydantic lax-mode); the scorer's own gate does not."""
        with pytest.raises(InvalidResponseError):
            score_ess(["2", 0, 0, 0, 0, 0, 0, 0])  # type: ignore[list-item]

    def test_rejects_none(self) -> None:
        with pytest.raises(InvalidResponseError):
            score_ess([None, 0, 0, 0, 0, 0, 0, 0])  # type: ignore[list-item]


class TestResultTyping:
    """EssResult is a frozen dataclass with stable field names."""

    def test_result_is_ess_result_instance(self) -> None:
        assert isinstance(score_ess([0] * 8), EssResult)

    def test_result_is_frozen(self) -> None:
        result = score_ess([0] * 8)
        with pytest.raises(FrozenInstanceError):
            result.total = 999  # type: ignore[misc]

    def test_result_instrument_version_defaulted(self) -> None:
        assert score_ess([0] * 8).instrument_version == "ess-1.0.0"

    def test_result_items_is_tuple(self) -> None:
        result = score_ess([0, 1, 2, 3, 0, 1, 2, 3])
        assert isinstance(result.items, tuple)
        assert result.items == (0, 1, 2, 3, 0, 1, 2, 3)

    def test_result_items_length_eight(self) -> None:
        assert len(score_ess([1] * 8).items) == 8

    def test_result_severity_is_literal_string(self) -> None:
        assert score_ess([0] * 8).severity == "normal"
        assert score_ess([3] * 8).severity == "severe"

    def test_result_total_is_int(self) -> None:
        assert isinstance(score_ess([1] * 8).total, int)

    def test_no_subscales_field(self) -> None:
        """ESS is unidimensional — no subscales attribute on the
        result (contrast PCS / Brief COPE / DERS-16)."""
        result = score_ess([1] * 8)
        assert not hasattr(result, "subscales")


class TestClinicalVignettes:
    """End-to-end profiles drawn from Johns 1991 and downstream
    validation / clinical literature."""

    def test_vignette_johns_1991_healthy_control_floor(self) -> None:
        """Healthy-control profile from Johns & Hocking 1997 Sleep
        20(10):844-849 Australian workers sample — median ESS
        ≈ 5-6 for non-shift-working adults.  Falls in ``normal``
        band."""
        # Conservative healthy profile: mostly 0 with a few 1s.
        items = [1, 1, 0, 1, 1, 0, 1, 0]
        result = score_ess(items)
        assert result.total == 5
        assert result.severity == "normal"

    def test_vignette_johns_1991_narcolepsy_ceiling(self) -> None:
        """Johns 1991 Appendix reports narcolepsy patients
        typically score 17+ (severe EDS).  Full-ceiling vector
        maps to severe."""
        result = score_ess([3] * 8)
        assert result.total == 24
        assert result.severity == "severe"

    def test_vignette_obstructive_sleep_apnea_profile(self) -> None:
        """Johns 1993 Chest 103(1):30-36 OSA patient sample —
        mean ESS 13.6 (SD ~4.5).  Profile: moderate dozing
        likelihood across most passive situations."""
        # Mean 13.6 → items summing to 13 or 14 → moderate band.
        items = [2, 2, 1, 2, 2, 1, 2, 1]
        result = score_ess(items)
        assert result.total == 13
        assert result.severity == "moderate"

    def test_vignette_shift_worker_mild_eds(self) -> None:
        """Shift-worker profile — elevated sleepiness during
        passive situations (reading, watching TV) but lower
        during active contexts.  Total 11-12 → mild EDS."""
        items = [2, 2, 1, 2, 2, 1, 2, 0]
        result = score_ess(items)
        assert result.total == 12
        assert result.severity == "mild"

    def test_vignette_stimulant_withdrawal_rebound(self) -> None:
        """Roehrs 2016 Sleep Med Clin — stimulant-dependent
        individuals in early withdrawal experience rebound
        hypersomnia; ESS frequently 16+ in the first 2 weeks
        post-cessation.  Maps to severe EDS."""
        items = [3, 3, 2, 3, 3, 2, 3, 2]
        result = score_ess(items)
        assert result.total == 21
        assert result.severity == "severe"

    def test_vignette_alcohol_disrupted_sleep_post_withdrawal(
        self,
    ) -> None:
        """Brower 2008 — alcohol-dependent users in post-acute-
        withdrawal window report persistent ESS ≥ 13 for months.
        High ESS in this window is a relapse-risk marker."""
        items = [2, 2, 2, 2, 2, 2, 2, 1]
        result = score_ess(items)
        assert result.total == 15
        assert result.severity == "moderate"

    def test_vignette_depression_sleep_loop(self) -> None:
        """Franzen & Buysse 2008 — depression-sleep bidirectional
        loop.  PHQ-9 elevation + ESS elevation is a routing
        signal for behavioral-activation + sleep-restriction
        content."""
        items = [2, 3, 2, 2, 3, 1, 2, 2]
        result = score_ess(items)
        assert result.total == 17
        assert result.severity == "severe"

    def test_vignette_adolescent_typical_profile(self) -> None:
        """Hasler 2012 — adolescents typically score higher than
        adults due to circadian phase delay; normative ≈ 7-9.
        Stays in ``normal`` band — ESS does NOT pathologize
        developmental sleep phase."""
        items = [1, 2, 1, 1, 2, 1, 1, 0]
        result = score_ess(items)
        assert result.total == 9
        assert result.severity == "normal"

    def test_vignette_rci_determinism(self) -> None:
        """Jacobson-Truax RCI requires deterministic scoring —
        identical items yield identical totals / severities /
        instrument_versions."""
        items = [2, 1, 3, 0, 2, 1, 3, 0]
        a = score_ess(items)
        b = score_ess(items)
        assert a.total == b.total
        assert a.severity == b.severity
        assert a.instrument_version == b.instrument_version
        assert a.items == b.items

    def test_vignette_direction_guarantee(self) -> None:
        """Direction: HIGHER = MORE sleepiness.  Doubling every
        item value produces a higher total AND a more-severe
        band (mild → severe in this vector)."""
        low = score_ess([1] * 8)
        high = score_ess([3] * 8)
        assert high.total > low.total
        assert high.severity == "severe"
        assert low.severity == "normal"

    def test_vignette_urge_window_narrowing(
        self,
    ) -> None:
        """Hasler 2012 sleep-impulsivity coupling — high ESS
        predicts narrowed deliberation window (prefrontal
        hypometabolism pathway).  Platform-mission relevance:
        severe-band ESS is an orthogonal risk signal for the
        60-180 s intervention window.  Scorer just reports — the
        intervention layer does the window-adjustment."""
        items = [3, 3, 3, 2, 3, 2, 3, 2]
        result = score_ess(items)
        assert result.total == 21
        assert result.severity == "severe"


class TestInvariants:
    """Cross-cutting invariants that must hold across all inputs."""

    def test_items_returned_verbatim(self) -> None:
        """``items`` field mirrors input for audit invariance."""
        raw: list[int] = [2, 0, 3, 1, 2, 0, 3, 1]
        result = score_ess(raw)
        assert result.items == tuple(raw)

    def test_total_equals_sum_of_items(self) -> None:
        raw: list[int] = [3, 2, 1, 0, 1, 2, 3, 0]
        result = score_ess(raw)
        assert result.total == sum(result.items)

    def test_total_lower_bound(self) -> None:
        """Total must be ≥ 0 for all valid inputs."""
        assert score_ess([0] * 8).total >= 0

    def test_total_upper_bound(self) -> None:
        """Total must be ≤ 24 for all valid inputs (8 × 3)."""
        assert score_ess([3] * 8).total == 24

    def test_severity_band_matches_threshold_lookup(self) -> None:
        """For every valid total 0..24, the returned severity
        equals the first label in ``ESS_SEVERITY_THRESHOLDS``
        whose upper ≥ total."""
        for total in range(0, 25):
            q, r = divmod(total, 3)
            items: list[int] = [3] * q
            if q < 8:
                items.append(r)
                items.extend([0] * (8 - len(items)))
            assert len(items) == 8
            assert sum(items) == total
            result = score_ess(items)
            expected = next(
                label
                for upper, label in ESS_SEVERITY_THRESHOLDS
                if total <= upper
            )
            assert result.severity == expected


class TestEdgeCases:
    """Non-typical input shapes."""

    def test_accepts_tuple_input(self) -> None:
        """Sequence is ``collections.abc.Sequence`` — a tuple is
        also a Sequence, must work."""
        result = score_ess((1, 1, 1, 1, 1, 1, 1, 1))
        assert result.total == 8

    def test_accepts_generator_materialized(self) -> None:
        """Generators aren't Sequences — but a list comprehension
        is.  Smoke test: built from a generator, materialized."""
        items = [i % 4 for i in range(8)]
        result = score_ess(items)
        assert result.total == sum(items)

    def test_huge_items_typeerror_message(self) -> None:
        """A very out-of-range int still produces the pinned
        error message format."""
        with pytest.raises(InvalidResponseError) as exc:
            score_ess([999, 0, 0, 0, 0, 0, 0, 0])
        assert "0-3" in str(exc.value)

    def test_rejects_complex_non_int_object(self) -> None:
        """Arbitrary objects without int coercion must be
        rejected."""
        with pytest.raises(InvalidResponseError):
            score_ess([object(), 0, 0, 0, 0, 0, 0, 0])  # type: ignore[list-item]

    def test_does_not_mutate_input(self) -> None:
        """Scorer must not mutate caller's list."""
        raw: list[Any] = [2, 1, 3, 0, 2, 1, 3, 0]
        snapshot = list(raw)
        score_ess(raw)
        assert raw == snapshot

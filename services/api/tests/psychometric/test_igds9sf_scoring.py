"""Scoring-layer tests for IGDS9-SF (Pontes & Griffiths 2015).

The Internet Gaming Disorder Scale Short Form — 9-item self-report
screen for Internet Gaming Disorder mapping 1:1 to DSM-5 Section
III proposed IGD criteria.  Each item is a 1-5 frequency Likert;
total range 9-45 (HIGHER = MORE SEVERITY).  Unidimensional per
Pontes 2015 CFA (reconfirmed Pontes 2019 cross-national sample,
n = 6,773).  No reverse-keying — all items positively worded.

Why ``severity="continuous"`` WITH ``positive_screen``:

Pontes 2015 published a formal diagnostic threshold (the 5-item
DSM-5-aligned criterion: ≥ 5 of 9 items endorsed at "Often" (4)
or "Very Often" (5)) but did NOT publish total-based severity
bands.  Király 2017's alternative total cutoff ≥ 21 is a
research-convention tool, not the primary published scheme.  The
scorer therefore:

- emits ``positive_screen`` boolean (primary diagnostic signal)
- emits ``cutoff_used = 5`` (items-endorsed threshold, not total)
- emits ``endorsed_item_count`` (raw count for clinician display)
- emits ``severity = "continuous"`` (sentinel — no total bands)

Coverage matrix:
- Constants pinned to Pontes 2015 (item count 9, range 1-5,
  positive-item-count 5, endorsement-threshold 4, instrument_version
  "igds9sf-1.0.0").
- Total correctness across the ceiling, floor, and representative
  interior values.
- Endorsed-item-count correctness at boundary endorsement levels.
- Positive-screen boundary semantics: exactly 5 items at 4 → True;
  4 items at 4 → False; 9 items at 5 → True; all 3s (endorsed 0) →
  False; mix patterns.
- Severity always "continuous" regardless of total or
  positive_screen result.
- Item-count validation (≠ 9 rejected with proper messages).
- Item-range validation (0 and 6 rejected; -1 rejected; positional
  error message names the 1-indexed position).
- Item-type validation (bool rejected BEFORE range check per
  CLAUDE.md standing rule; string, float, None rejected).
- Result typing — frozen dataclass, tuple-of-int items, preserves
  RAW responses, default instrument_version populated.
- Clinical vignettes (DSM-5 Section III threshold; ICD-11 Gaming
  Disorder profile; escape-motivated gaming per criterion 8;
  functional impairment per criterion 9; RCI determinism;
  direction guarantee).
"""

from __future__ import annotations

import pytest

from discipline.psychometric.scoring.igds9sf import (
    IGDS9SF_ENDORSEMENT_THRESHOLD,
    IGDS9SF_POSITIVE_ITEM_COUNT,
    INSTRUMENT_VERSION,
    ITEM_COUNT,
    ITEM_MAX,
    ITEM_MIN,
    Igds9SfResult,
    InvalidResponseError,
    score_igds9sf,
)


class TestConstants:
    """IGDS9-SF constants pinned to Pontes 2015."""

    def test_item_count_is_nine(self) -> None:
        """DSM-5 Section III lists 9 proposed IGD criteria; Pontes
        2015 instrument has exactly one item per criterion."""
        assert ITEM_COUNT == 9

    def test_item_range_is_1_to_5(self) -> None:
        assert ITEM_MIN == 1
        assert ITEM_MAX == 5

    def test_positive_item_count_is_five(self) -> None:
        """DSM-5 Section III requires endorsement of 5 or more of
        the 9 criteria for an IGD presumptive diagnosis.  This
        constant MUST stay at 5; changing it invalidates Pontes
        2015 validation."""
        assert IGDS9SF_POSITIVE_ITEM_COUNT == 5

    def test_endorsement_threshold_is_four(self) -> None:
        """Pontes 2015 operationalizes "endorsed" as "Often" (4) or
        "Very Often" (5) on the 5-point Likert — threshold = 4."""
        assert IGDS9SF_ENDORSEMENT_THRESHOLD == 4

    def test_instrument_version_pinned(self) -> None:
        assert INSTRUMENT_VERSION == "igds9sf-1.0.0"


class TestTotalCorrectness:
    """Total is sum of 9 items, range 9-45."""

    def test_all_ones_floor(self) -> None:
        """Minimum endorsement: total = 9 (9 × 1)."""
        result = score_igds9sf([1] * 9)
        assert result.total == 9

    def test_all_fives_ceiling(self) -> None:
        """Maximum endorsement: total = 45 (9 × 5)."""
        result = score_igds9sf([5] * 9)
        assert result.total == 45

    def test_all_threes_midpoint(self) -> None:
        """Midpoint endorsement: total = 27 (9 × 3)."""
        result = score_igds9sf([3] * 9)
        assert result.total == 27

    def test_representative_interior_value(self) -> None:
        """Mixed profile totaling 30 — a value Király 2017 would
        still flag below their ≥ 21 research cutoff but below the
        Pontes 2015 5-item criterion if the items-at-≥ 4 count is
        low."""
        items = [4, 3, 4, 3, 3, 4, 3, 3, 3]  # 30
        result = score_igds9sf(items)
        assert result.total == 30

    def test_asymmetric_vector(self) -> None:
        """Non-uniform responses — confirms linear sum, no
        weighting."""
        items = [1, 5, 2, 4, 3, 5, 1, 4, 2]
        result = score_igds9sf(items)
        assert result.total == sum(items)
        assert result.total == 27


class TestNoReverseKeying:
    """IGDS9-SF is positively worded throughout — no reverse-keying."""

    def test_ceiling_on_every_item_yields_max(self) -> None:
        """All items worded so higher endorsement = more
        pathological gaming.  Ceiling on every item → total 45,
        not a mid-range value."""
        result = score_igds9sf([5] * 9)
        assert result.total == 45

    def test_floor_on_every_item_yields_min(self) -> None:
        result = score_igds9sf([1] * 9)
        assert result.total == 9

    def test_raw_items_preserved_identically(self) -> None:
        """No transformation of raw responses — items field is
        byte-identical to input."""
        raw = [1, 2, 3, 4, 5, 4, 3, 2, 1]
        result = score_igds9sf(raw)
        assert result.items == tuple(raw)


class TestSeverityContinuous:
    """Severity is the ``"continuous"`` sentinel at all totals."""

    @pytest.mark.parametrize("items,expected_total", [
        ([1] * 9, 9),
        ([2] * 9, 18),
        ([3] * 9, 27),
        ([4] * 9, 36),
        ([5] * 9, 45),
    ])
    def test_severity_always_continuous(
        self, items: list[int], expected_total: int
    ) -> None:
        result = score_igds9sf(items)
        assert result.total == expected_total
        assert result.severity == "continuous"

    def test_no_clinical_bands_introduced(self) -> None:
        """Király 2017 proposed ≥ 21 as a TOTAL-based research
        cutoff.  Our scorer does NOT bake that in — severity remains
        literal ``"continuous"`` even at values that would cross
        that threshold (positive_screen carries the primary
        diagnostic signal)."""
        below_kiraly = score_igds9sf([2] * 9)  # total 18
        at_kiraly = score_igds9sf([3] * 7 + [1, 1])  # total 23
        above_kiraly = score_igds9sf([3] * 9)  # total 27
        assert below_kiraly.severity == "continuous"
        assert at_kiraly.severity == "continuous"
        assert above_kiraly.severity == "continuous"

    def test_severity_continuous_even_when_positive_screen(self) -> None:
        """Severity stays ``"continuous"`` even when the user
        meets the Pontes 2015 5-item criterion.  positive_screen is
        the diagnostic signal; severity is not reparameterized."""
        # 5 items at 4 triggers positive_screen True.
        result = score_igds9sf([4, 4, 4, 4, 4, 1, 1, 1, 1])
        assert result.positive_screen is True
        assert result.severity == "continuous"

    def test_severity_continuous_when_not_positive_screen(self) -> None:
        """Severity stays ``"continuous"`` when positive_screen is
        False."""
        result = score_igds9sf([3] * 9)  # 0 items at ≥ 4
        assert result.positive_screen is False
        assert result.severity == "continuous"


class TestEndorsedItemCount:
    """Endorsed item count = number of items at ≥ "Often" (4)."""

    def test_zero_endorsements_when_all_below_threshold(self) -> None:
        """All items at 3 ("Sometimes") — below the "Often" (4)
        endorsement threshold.  Endorsed count = 0."""
        result = score_igds9sf([3] * 9)
        assert result.endorsed_item_count == 0

    def test_all_nine_endorsed_at_ceiling(self) -> None:
        """All items at 5 ("Very Often") — every item endorsed.
        Count = 9."""
        result = score_igds9sf([5] * 9)
        assert result.endorsed_item_count == 9

    def test_all_nine_endorsed_at_often(self) -> None:
        """All items at 4 ("Often") — all meet the endorsement
        threshold.  Count = 9."""
        result = score_igds9sf([4] * 9)
        assert result.endorsed_item_count == 9

    def test_five_items_endorsed_exactly(self) -> None:
        """Exactly 5 items at 4 — meets Pontes 2015 threshold at
        the boundary."""
        result = score_igds9sf([4, 4, 4, 4, 4, 3, 3, 3, 3])
        assert result.endorsed_item_count == 5

    def test_four_items_endorsed_below_boundary(self) -> None:
        """4 items at 4 — JUST below the 5-item criterion."""
        result = score_igds9sf([4, 4, 4, 4, 3, 3, 3, 3, 3])
        assert result.endorsed_item_count == 4

    def test_mixed_four_and_five_endorsements(self) -> None:
        """Mix of "Often" and "Very Often" both count as
        endorsed."""
        result = score_igds9sf([4, 5, 4, 5, 4, 1, 1, 1, 1])
        assert result.endorsed_item_count == 5

    def test_threshold_is_four_not_three(self) -> None:
        """A 3 ("Sometimes") does NOT count as endorsed.  Pontes
        2015 operationalizes endorsed = "Often" or "Very Often"
        (≥ 4), not ≥ "Sometimes"."""
        items = [3] * 9  # All "Sometimes".
        result = score_igds9sf(items)
        assert result.endorsed_item_count == 0
        assert result.total == 27  # High total but no endorsement.

    def test_threshold_inclusive_at_four(self) -> None:
        """Value of 4 is endorsed (inclusive); value of 3 is not."""
        # Single item at 4, rest at 3.
        result = score_igds9sf([4] + [3] * 8)
        assert result.endorsed_item_count == 1


class TestPositiveScreenBoundary:
    """Pontes 2015 5-item criterion boundary semantics."""

    def test_exactly_five_endorsed_triggers_positive(self) -> None:
        """Canonical boundary: exactly 5 items at "Often" (4) →
        positive_screen True."""
        result = score_igds9sf([4, 4, 4, 4, 4, 1, 1, 1, 1])
        assert result.endorsed_item_count == 5
        assert result.positive_screen is True
        assert result.cutoff_used == 5

    def test_four_endorsed_does_not_trigger(self) -> None:
        """JUST below the boundary: 4 items at "Often" →
        positive_screen False.  Proves the threshold is ≥ 5, not
        ≥ 4."""
        result = score_igds9sf([4, 4, 4, 4, 1, 1, 1, 1, 1])
        assert result.endorsed_item_count == 4
        assert result.positive_screen is False
        assert result.cutoff_used == 5

    def test_all_nine_at_ceiling_triggers_positive(self) -> None:
        """Ceiling case: all 9 items at "Very Often" (5) →
        positive_screen True; endorsed_item_count = 9."""
        result = score_igds9sf([5] * 9)
        assert result.endorsed_item_count == 9
        assert result.positive_screen is True

    def test_all_nine_at_sometimes_does_not_trigger(self) -> None:
        """All items at "Sometimes" (3) — no endorsements (3 < 4);
        positive_screen False even though total 27 sits above
        Király 2017's ≥ 21 research cutoff.  Demonstrates that we
        use the 5-item criterion, NOT a total cutoff."""
        result = score_igds9sf([3] * 9)
        assert result.total == 27
        assert result.endorsed_item_count == 0
        assert result.positive_screen is False

    def test_five_at_very_often_triggers_positive(self) -> None:
        """5 items at "Very Often" (5) → positive_screen True."""
        result = score_igds9sf([5, 5, 5, 5, 5, 1, 1, 1, 1])
        assert result.endorsed_item_count == 5
        assert result.positive_screen is True

    def test_mixed_four_and_five_at_threshold(self) -> None:
        """Mix of 4s and 5s totaling exactly 5 items at ≥ 4 →
        positive_screen True."""
        result = score_igds9sf([4, 5, 4, 5, 4, 1, 1, 1, 1])
        assert result.endorsed_item_count == 5
        assert result.positive_screen is True

    def test_six_endorsed_clearly_positive(self) -> None:
        """6 items endorsed — above boundary; positive_screen
        True."""
        result = score_igds9sf([4] * 6 + [1] * 3)
        assert result.endorsed_item_count == 6
        assert result.positive_screen is True

    def test_all_at_three_just_below_endorsement_threshold(self) -> None:
        """3 < 4, so none endorsed; positive_screen False
        regardless of high total."""
        result = score_igds9sf([3] * 9)
        assert result.positive_screen is False

    def test_zero_endorsed_not_positive(self) -> None:
        """Floor case: all items at 1 ("Never") — no endorsements;
        positive_screen False."""
        result = score_igds9sf([1] * 9)
        assert result.endorsed_item_count == 0
        assert result.positive_screen is False

    def test_cutoff_used_always_five(self) -> None:
        """cutoff_used is always the item count (5), not the
        endorsement threshold (4).  Surfacing this lets the client
        render "positive at ≥ 5 items endorsed"."""
        high = score_igds9sf([5] * 9)
        low = score_igds9sf([1] * 9)
        mid = score_igds9sf([3] * 9)
        assert high.cutoff_used == 5
        assert low.cutoff_used == 5
        assert mid.cutoff_used == 5


class TestItemCountValidation:
    """Item-count rejections raise :class:`InvalidResponseError`."""

    def test_short_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="9"):
            score_igds9sf([3] * 8)

    def test_long_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="9"):
            score_igds9sf([3] * 10)

    def test_empty_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="9"):
            score_igds9sf([])

    def test_message_names_igds9sf(self) -> None:
        try:
            score_igds9sf([3] * 5)
        except InvalidResponseError as exc:
            assert "IGDS9-SF" in str(exc)
            assert "9" in str(exc)
        else:
            pytest.fail("Expected InvalidResponseError")


class TestItemRangeValidation:
    """Item-range rejections raise :class:`InvalidResponseError`."""

    def test_below_range_rejected(self) -> None:
        items = [3] * 9
        items[0] = 0  # Below 1-5 range.
        with pytest.raises(InvalidResponseError, match="1-5"):
            score_igds9sf(items)

    def test_above_range_rejected(self) -> None:
        items = [3] * 9
        items[5] = 6  # Above 1-5 range.
        with pytest.raises(InvalidResponseError, match="1-5"):
            score_igds9sf(items)

    def test_negative_rejected(self) -> None:
        items = [3] * 9
        items[8] = -1
        with pytest.raises(InvalidResponseError, match="1-5"):
            score_igds9sf(items)

    def test_way_above_range_rejected(self) -> None:
        """Even a value that might be a typo for a 10-point
        instrument (e.g., 10) is rejected at the 1-5 range."""
        items = [3] * 9
        items[3] = 10
        with pytest.raises(InvalidResponseError, match="1-5"):
            score_igds9sf(items)

    def test_range_message_names_position(self) -> None:
        """Error message identifies the 1-indexed position of the
        offending item so clinicians can locate it in the response
        record."""
        items = [3] * 9
        items[4] = 7
        try:
            score_igds9sf(items)
        except InvalidResponseError as exc:
            assert "5" in str(exc)  # 1-indexed position 5.
            assert "1-5" in str(exc)
        else:
            pytest.fail("Expected InvalidResponseError")

    def test_first_invalid_reported(self) -> None:
        """If multiple items are out of range, the first is
        reported — matches the single-item-at-a-time validation
        pattern across the psychometric module."""
        items = [3] * 9
        items[2] = 0
        items[6] = 6
        with pytest.raises(InvalidResponseError) as exc_info:
            score_igds9sf(items)
        assert "3" in str(exc_info.value)  # 1-indexed position 3.


class TestItemTypeValidation:
    """Bool / string / float items raise :class:`InvalidResponseError`."""

    def test_bool_true_rejected(self) -> None:
        """CLAUDE.md standing rule: bool rejected BEFORE the range
        check even though True would coerce to 1 (valid range).
        At the wire layer Pydantic coerces JSON ``true`` → 1 and
        the scorer never sees the bool; here at the scorer level
        we test direct Python invocation with a bool, which MUST
        reject."""
        items: list = [3] * 9
        items[0] = True
        with pytest.raises(InvalidResponseError, match="int"):
            score_igds9sf(items)

    def test_bool_false_rejected(self) -> None:
        items: list = [3] * 9
        items[0] = False
        with pytest.raises(InvalidResponseError, match="int"):
            score_igds9sf(items)

    def test_string_rejected(self) -> None:
        items: list = [3] * 9
        items[0] = "3"
        with pytest.raises(InvalidResponseError, match="int"):
            score_igds9sf(items)

    def test_float_rejected(self) -> None:
        items: list = [3] * 9
        items[0] = 3.0
        with pytest.raises(InvalidResponseError, match="int"):
            score_igds9sf(items)

    def test_none_rejected(self) -> None:
        items: list = [3] * 9
        items[0] = None
        with pytest.raises(InvalidResponseError, match="int"):
            score_igds9sf(items)


class TestResultTyping:
    """Result is a frozen dataclass with the correct field types."""

    def test_returns_igds9sf_result(self) -> None:
        result = score_igds9sf([3] * 9)
        assert isinstance(result, Igds9SfResult)

    def test_total_is_int(self) -> None:
        result = score_igds9sf([3] * 9)
        assert isinstance(result.total, int)

    def test_severity_is_continuous_literal(self) -> None:
        result = score_igds9sf([3] * 9)
        assert result.severity == "continuous"

    def test_positive_screen_is_bool(self) -> None:
        result = score_igds9sf([3] * 9)
        assert isinstance(result.positive_screen, bool)

    def test_cutoff_used_is_int(self) -> None:
        result = score_igds9sf([3] * 9)
        assert isinstance(result.cutoff_used, int)
        assert result.cutoff_used == 5

    def test_endorsed_item_count_is_int(self) -> None:
        result = score_igds9sf([4, 4, 4, 4, 4, 1, 1, 1, 1])
        assert isinstance(result.endorsed_item_count, int)
        assert result.endorsed_item_count == 5

    def test_items_is_tuple_of_ints(self) -> None:
        result = score_igds9sf([2, 3, 4, 1, 5, 3, 2, 4, 5])
        assert isinstance(result.items, tuple)
        assert all(isinstance(item, int) for item in result.items)
        assert len(result.items) == 9

    def test_frozen_dataclass(self) -> None:
        result = score_igds9sf([3] * 9)
        with pytest.raises((AttributeError, TypeError)):
            result.total = 100  # type: ignore[misc]

    def test_instrument_version_default(self) -> None:
        result = score_igds9sf([3] * 9)
        assert result.instrument_version == "igds9sf-1.0.0"

    def test_items_preserve_raw_response(self) -> None:
        """Audit invariance: items field must be byte-identical to
        the raw response (no transformation, no reverse-keying, no
        mutation)."""
        raw = [1, 5, 2, 4, 3, 5, 1, 4, 2]
        result = score_igds9sf(raw)
        assert result.items == tuple(raw)


class TestClinicalVignettes:
    """Clinical scenarios grounded in Pontes 2015 / DSM-5 / ICD-11."""

    def test_dsm5_section_iii_threshold_boundary(self) -> None:
        """Canonical DSM-5 Section III IGD case: user endorses
        exactly 5 of 9 criteria at "Often" — meets the presumptive
        diagnostic threshold.  This is the boundary between IGD-
        presumptive and sub-threshold gaming concern."""
        # Items: preoccupation, withdrawal, tolerance, loss of
        # control, escape — the first five DSM-5 criteria at "Often",
        # rest at "Never".
        items = [4, 4, 4, 4, 4, 1, 1, 1, 1]
        result = score_igds9sf(items)
        assert result.total == 24
        assert result.endorsed_item_count == 5
        assert result.positive_screen is True
        assert result.severity == "continuous"

    def test_subthreshold_gaming_concern(self) -> None:
        """User endorses 3 items at "Often" — concerning but below
        Pontes 2015 threshold.  Platform's trajectory layer would
        flag rising trend even though absolute positive_screen is
        False; this is the T1 preventive window."""
        items = [4, 4, 4, 2, 2, 2, 2, 2, 2]
        result = score_igds9sf(items)
        assert result.endorsed_item_count == 3
        assert result.positive_screen is False

    def test_icd11_gaming_disorder_profile(self) -> None:
        """ICD-11 Gaming Disorder (6C51) clinical profile: user
        endorses all 9 DSM-5 criteria at "Very Often" — consistent
        with the ICD-11 impaired-control + prioritization +
        continuation-despite-consequences triad, and far above the
        Pontes 2015 5-item threshold."""
        result = score_igds9sf([5] * 9)
        assert result.total == 45
        assert result.endorsed_item_count == 9
        assert result.positive_screen is True

    def test_escape_motivated_gaming_item_8(self) -> None:
        """Kiraly 2015 profile: user high on item 8 (escape / mood
        modification) with moderate endorsement elsewhere.  In this
        profile gaming is secondary to depression/loneliness;
        intervention-matching layer routes depression-primary CBT.
        Scorer still reports positive_screen per the objective
        5-item criterion."""
        # Items 1-5 and 8 at "Often"; 6, 7, 9 at "Sometimes".
        items = [4, 4, 4, 4, 4, 3, 3, 4, 3]
        result = score_igds9sf(items)
        assert result.endorsed_item_count == 6
        assert result.positive_screen is True
        assert result.severity == "continuous"

    def test_functional_impairment_profile_item_9(self) -> None:
        """Profile: user endorses item 9 (jeopardized relationships
        / opportunities) at "Very Often" with other items mid-range.
        Item 9 endorsement with WSAS elevation flags for clinician
        review regardless of total."""
        items = [3, 3, 3, 4, 4, 4, 3, 4, 5]
        result = score_igds9sf(items)
        assert result.endorsed_item_count == 5
        assert result.positive_screen is True
        # Raw preserved — clinician can inspect item 9 value.
        assert result.items[8] == 5

    def test_floor_profile_no_gaming_concern(self) -> None:
        """Floor case: user reports "Never" on every item — no
        gaming-disorder signal.  Floor baseline for a user who does
        not game compulsively."""
        result = score_igds9sf([1] * 9)
        assert result.total == 9
        assert result.endorsed_item_count == 0
        assert result.positive_screen is False

    def test_never_endorses_past_sometimes(self) -> None:
        """User reports "Sometimes" (3) on every item — elevated
        total (27) but 0 items at endorsement threshold; Pontes
        2015 criterion correctly distinguishes FREQUENCY of
        endorsement from COUNT of meaningfully-endorsed items."""
        result = score_igds9sf([3] * 9)
        assert result.total == 27
        assert result.endorsed_item_count == 0
        assert result.positive_screen is False

    def test_kiraly_2017_alternative_cutoff_not_applied(self) -> None:
        """Király 2017 proposed total ≥ 21 as a research-convention
        cutoff.  Our scorer does NOT apply that — a user at total
        21 with all items at ~2-3 has 0 items at ≥ 4;
        positive_screen False even though total clears Király's
        research threshold."""
        items = [2, 3, 2, 3, 2, 3, 2, 2, 2]  # total 21
        result = score_igds9sf(items)
        assert result.total == 21
        assert result.endorsed_item_count == 0
        assert result.positive_screen is False

    def test_direction_higher_equals_more_severity(self) -> None:
        """Direction guarantee: total 45 > total 9; higher number =
        more gaming-disorder severity.  Same direction as PHQ-9 /
        GAD-7 / AUDIT / DUDIT / FTND / PSS-10; OPPOSITE of WHO-5 /
        BRS / LOT-R / RSES / MAAS / CD-RISC-10 / WEMWBS."""
        low = score_igds9sf([1] * 9)
        high = score_igds9sf([5] * 9)
        assert low.total < high.total
        assert low.total == 9
        assert high.total == 45
        # Positive-screen direction: high endorsement → True.
        assert low.positive_screen is False
        assert high.positive_screen is True

    def test_rci_determinism_identical_input_yields_identical_output(
        self,
    ) -> None:
        """Jacobson-Truax RCI assumes deterministic scoring.
        Identical input must yield identical output (total,
        severity, positive_screen, cutoff_used, endorsed_item_count,
        items, instrument_version)."""
        items = [4, 3, 5, 2, 4, 3, 5, 2, 4]
        a = score_igds9sf(items)
        b = score_igds9sf(items)
        assert a == b

    def test_poly_addiction_profile(self) -> None:
        """IGDS9-SF positive + substance-addiction positive profile:
        user endorses 7 gaming criteria at "Often"/"Very Often".
        High positive_screen signal supports behavioral-addiction
        intervention track (MBRP — Bowen 2014).  Scorer just
        reports; intervention layer decides routing."""
        items = [4, 5, 4, 5, 4, 3, 5, 4, 2]
        result = score_igds9sf(items)
        assert result.endorsed_item_count == 7
        assert result.positive_screen is True

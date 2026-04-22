"""Scorer tests for SWLS (Diener 1985 Satisfaction With Life Scale).

Pins the Diener 1985 / Pavot & Diener 1993 invariants:

- 5 items, each 1-7 Likert, NO reverse keying.
- Total 5-35, straight sum, HIGHER = MORE satisfied.
- Severity = ``"continuous"`` — Pavot 1993 interpretive bands
  (extremely dissatisfied 5-9, extremely satisfied 31-35, etc.)
  are NOT collapsed into envelope bands; they stay at the
  clinician-UI renderer layer per CLAUDE.md non-negotiable #9.
- No subscales (unidimensional factor structure).
- Bool rejection at the scorer (CLAUDE.md standing rule).
- Strict 1-7 range — 0 is rejected (unlike CIUS 0-4 where 0 is
  valid).

These tests cover:
- Constants (ITEM_COUNT, ITEM_MIN, ITEM_MAX, SWLS_REVERSE_ITEMS).
- Total correctness at all-v constant vectors and Pavot 1993 band
  boundaries.
- Severity always ``"continuous"`` (no band collapse).
- No reverse-keying invariance (every item raised contributes
  linearly to the total).
- Acquiescence signature: linear ``total = 5v``.
- Item count, value, and type validation.
- Bool rejection invariant (direct-Python-call defence).
- Clinical vignettes mirroring the Pavot 1993 bands and the
  Moos 2005 delayed-relapse / ACT-values-clarification profiles
  described in the module docstring.
"""

from __future__ import annotations

import pytest

from discipline.psychometric.scoring.swls import (
    INSTRUMENT_VERSION,
    ITEM_COUNT,
    ITEM_MAX,
    ITEM_MIN,
    SWLS_REVERSE_ITEMS,
    InvalidResponseError,
    SwlsResult,
    score_swls,
)


class TestConstants:
    """Pin the Diener 1985 scale constants against primary source."""

    def test_instrument_version_pinned(self) -> None:
        """Version string is the canonical sprint-72 release tag;
        any bump propagates to the router header, the FHIR export
        layer, and the trajectory-RCI calculation."""
        assert INSTRUMENT_VERSION == "swls-1.0.0"

    def test_item_count_pinned(self) -> None:
        """Diener 1985 Table 1 — 5 items, retained through Pavot
        1993 and Pavot 2008 validations."""
        assert ITEM_COUNT == 5

    def test_item_min_pinned(self) -> None:
        """Diener 1985 §Methods — 1 = Strongly Disagree."""
        assert ITEM_MIN == 1

    def test_item_max_pinned(self) -> None:
        """Diener 1985 §Methods — 7 = Strongly Agree."""
        assert ITEM_MAX == 7

    def test_no_reverse_items(self) -> None:
        """Diener 1985 / Pavot 1993: NO reverse-keyed items.  All
        five items worded in the "higher = more satisfied"
        direction.  Empty tuple is the pinned sentinel documenting
        this design decision."""
        assert SWLS_REVERSE_ITEMS == ()


class TestTotalCorrectness:
    """Pin that the total is a straight sum across all 1-7 values."""

    def test_all_minimum_sums_to_five(self) -> None:
        """All items at 1 (Strongly Disagree) — total = 5, the
        Pavot 1993 "Extremely dissatisfied" floor."""
        result = score_swls([1, 1, 1, 1, 1])
        assert result.total == 5

    def test_all_maximum_sums_to_thirty_five(self) -> None:
        """All items at 7 (Strongly Agree) — total = 35, the
        Pavot 1993 "Extremely satisfied" ceiling."""
        result = score_swls([7, 7, 7, 7, 7])
        assert result.total == 35

    def test_neutral_midpoint_sums_to_twenty(self) -> None:
        """All items at 4 (Neither Agree nor Disagree) — total = 20,
        Pavot 1993's single-value "Neutral" point."""
        result = score_swls([4, 4, 4, 4, 4])
        assert result.total == 20

    def test_pavot_satisfied_band_example(self) -> None:
        """Raw [5, 5, 6, 6, 6] = 28, within Pavot 1993 "Satisfied"
        band (26-30)."""
        result = score_swls([5, 5, 6, 6, 6])
        assert result.total == 28

    def test_pavot_slightly_dissatisfied_band_example(self) -> None:
        """Raw [3, 4, 3, 4, 3] = 17, within Pavot 1993 "Slightly
        dissatisfied" band (15-19)."""
        result = score_swls([3, 4, 3, 4, 3])
        assert result.total == 17

    def test_asymmetric_response_sums_correctly(self) -> None:
        """Mixed response [1, 4, 5, 7, 3] = 20."""
        result = score_swls([1, 4, 5, 7, 3])
        assert result.total == 20


class TestSeverityAlwaysContinuous:
    """Severity is always ``"continuous"`` — Pavot 1993 bands do
    NOT collapse the envelope."""

    @pytest.mark.parametrize(
        "items",
        [
            [1, 1, 1, 1, 1],
            [2, 2, 2, 2, 2],
            [3, 3, 3, 3, 3],
            [4, 4, 4, 4, 4],
            [5, 5, 5, 5, 5],
            [6, 6, 6, 6, 6],
            [7, 7, 7, 7, 7],
            [6, 7, 7, 6, 7],
            [5, 5, 6, 6, 6],
            [1, 2, 1, 2, 2],
        ],
    )
    def test_severity_is_continuous_everywhere(
        self, items: list[int]
    ) -> None:
        """No matter where the total falls in 5-35, severity is
        always ``"continuous"``."""
        result = score_swls(items)
        assert result.severity == "continuous"


class TestNoReverseKeying:
    """Pin the no-reverse-keying invariance: raising any single
    item from 1 to 7 raises the total by exactly 6."""

    @pytest.mark.parametrize("position", [0, 1, 2, 3, 4])
    def test_raising_any_item_raises_total_linearly(
        self, position: int
    ) -> None:
        """For each 0-indexed position, raising the item from 1 to
        7 while holding others at 1 produces a total of 11 (4 × 1 +
        7).  Linear contribution confirms no reverse-keying."""
        items = [1, 1, 1, 1, 1]
        items[position] = 7
        result = score_swls(items)
        assert result.total == 11

    @pytest.mark.parametrize("position", [0, 1, 2, 3, 4])
    def test_dropping_any_item_lowers_total_linearly(
        self, position: int
    ) -> None:
        """For each 0-indexed position, dropping the item from 7 to
        1 while holding others at 7 produces a total of 29 (4 × 7 +
        1).  Linear contribution in both directions."""
        items = [7, 7, 7, 7, 7]
        items[position] = 1
        result = score_swls(items)
        assert result.total == 29


class TestAcquiescenceSignature:
    """Pin the linear ``total = 5v`` acquiescence formula across
    all seven constant-response levels."""

    @pytest.mark.parametrize(
        "v, expected",
        [
            (1, 5),
            (2, 10),
            (3, 15),
            (4, 20),
            (5, 25),
            (6, 30),
            (7, 35),
        ],
    )
    def test_all_same_value_yields_five_v(
        self, v: int, expected: int
    ) -> None:
        """Linear formula ``total = 5v`` for any all-v constant
        vector.  Gap between v=1 and v=7 is 30, the full 5-35
        range (100%).  Matches UCLA-3 / CIUS 100%-of-range
        endpoint-exposure profile."""
        result = score_swls([v] * 5)
        assert result.total == expected

    def test_acquiescence_gap_is_thirty(self) -> None:
        """Pin the endpoint exposure: all-7s minus all-1s = 30,
        the full 5-35 range (100%).  Informs acquiescence-bias
        discount at the analytics-layer, should the platform ever
        implement one."""
        low = score_swls([1, 1, 1, 1, 1])
        high = score_swls([7, 7, 7, 7, 7])
        assert high.total - low.total == 30


class TestItemsPreserveRaw:
    """Pin that the ``items`` field preserves raw responses in
    administration order, with no reverse-keying transformation
    applied (there is no reverse-keying)."""

    def test_items_tuple_preserved(self) -> None:
        """Raw input round-trips identically to the items field
        for audit invariance."""
        raw = [1, 3, 5, 7, 4]
        result = score_swls(raw)
        assert result.items == tuple(raw)

    def test_items_is_tuple_not_list(self) -> None:
        """Frozen dataclass immutability requires tuple items; a
        mutable list would allow downstream mutation of audit
        state."""
        result = score_swls([2, 3, 4, 5, 6])
        assert isinstance(result.items, tuple)


class TestItemCountValidation:
    """Pin that exactly 5 items are required; other counts raise."""

    @pytest.mark.parametrize("count", [0, 1, 2, 3, 4, 6, 7, 10, 20])
    def test_rejects_wrong_item_count(self, count: int) -> None:
        """Any count other than 5 raises InvalidResponseError."""
        with pytest.raises(InvalidResponseError):
            score_swls([4] * count)


class TestItemValueValidation:
    """Pin the strict 1-7 range at the scorer."""

    @pytest.mark.parametrize("bad_value", [0, -1, -7, 8, 9, 10, 100])
    def test_rejects_out_of_range_values(self, bad_value: int) -> None:
        """0 and negatives are below-range (Diener 1985 starts at
        1); 8 and above are above-range (Diener 1985 ends at 7).
        Each raises InvalidResponseError."""
        items = [4, 4, 4, 4, 4]
        items[0] = bad_value
        with pytest.raises(InvalidResponseError):
            score_swls(items)

    def test_zero_rejected_even_though_plausible_scale(self) -> None:
        """Some life-satisfaction scales use 0-6 or 0-10 anchors;
        SWLS is 1-7 and 0 must be rejected.  Guards against
        accidental 0-based-Likert submission."""
        with pytest.raises(InvalidResponseError):
            score_swls([0, 4, 4, 4, 4])


class TestItemTypeValidation:
    """Pin the bool-rejection invariant (CLAUDE.md standing rule)."""

    @pytest.mark.parametrize("bad_value", ["4", 4.0, 4.5, None, [4]])
    def test_rejects_non_int_types(self, bad_value: object) -> None:
        """String / float / None / list item values all raise
        InvalidResponseError.  A float 4.0 is rejected even though
        numerically equal to int 4 — the platform contract is
        strict int-ness."""
        items: list[object] = [4, 4, 4, 4, 4]
        items[0] = bad_value
        with pytest.raises(InvalidResponseError):
            score_swls(items)  # type: ignore[arg-type]

    def test_rejects_true_despite_being_in_range(self) -> None:
        """Python's ``True == 1`` coercion means ``True`` would
        pass the 1-7 range check if not caught by the pre-range
        bool guard.  LOAD-BEARING test: direct-Python-call defence
        against silent bool-is-int confusion.

        Note: under the HTTP/Pydantic wire layer, JSON ``true``
        round-trips as int 1 BEFORE reaching the scorer, so this
        guard only fires for direct Python callers (internal
        services, batch scoring, tests)."""
        with pytest.raises(InvalidResponseError):
            score_swls([True, 4, 4, 4, 4])  # type: ignore[list-item]

    def test_rejects_false_despite_numerical_equivalence(self) -> None:
        """``False == 0`` in Python.  SWLS rejects 0 at the range
        check AND rejects False at the bool check — both guards
        apply.  The bool guard precedes the range guard so False
        is rejected with the bool-specific error message."""
        with pytest.raises(InvalidResponseError):
            score_swls([False, 4, 4, 4, 4])  # type: ignore[list-item]


class TestInvalidResponseErrorIdentity:
    """Pin that the exception is a ValueError subclass for HTTP
    422 translation at the router layer."""

    def test_exception_subclass_of_valueerror(self) -> None:
        """Router unified exception tuple in ``router.py`` catches
        ``InvalidResponseError`` across all scorers; ValueError
        subclass identity is the invariant that keeps the tuple
        mechanism sound."""
        assert issubclass(InvalidResponseError, ValueError)


class TestResultTyping:
    """Pin the frozen dataclass envelope shape."""

    def test_result_is_frozen_dataclass(self) -> None:
        """SwlsResult is frozen to prevent downstream mutation of
        audit-invariant fields (total, items, severity,
        instrument_version)."""
        result = score_swls([4, 4, 4, 4, 4])
        with pytest.raises(Exception):
            result.total = 0  # type: ignore[misc]

    def test_result_carries_instrument_version(self) -> None:
        """The instrument_version field flows to FHIR export and
        trajectory-RCI layers unchanged."""
        result = score_swls([4, 4, 4, 4, 4])
        assert result.instrument_version == INSTRUMENT_VERSION

    def test_result_has_no_subscales_field(self) -> None:
        """Diener 1985 / Pavot 1993 confirmed unidimensional;
        SwlsResult has no subscales field (cannot getattr)."""
        result = score_swls([4, 4, 4, 4, 4])
        assert not hasattr(result, "subscales")
        assert not hasattr(result, "cognitive_sum")
        assert not hasattr(result, "affective_sum")

    def test_result_has_no_positive_screen_field(self) -> None:
        """SWLS is not a screen — Pavot 1993's Neutral band at
        exactly 20 resists binary dichotomization, so the envelope
        MUST NOT carry positive_screen."""
        result = score_swls([4, 4, 4, 4, 4])
        assert not hasattr(result, "positive_screen")

    def test_result_has_no_requires_t3_field(self) -> None:
        """No SWLS item probes suicidality; acute-risk screening
        stays on C-SSRS / PHQ-9 item 9."""
        result = score_swls([4, 4, 4, 4, 4])
        assert not hasattr(result, "requires_t3")


class TestClinicalVignettes:
    """Vignettes pinning the Pavot 1993 interpretive bands and
    the module-docstring profile pairings."""

    def test_vignette_extremely_dissatisfied_floor(self) -> None:
        """Pavot 1993 "Extremely dissatisfied" floor (5-9).  Raw
        [1, 1, 1, 1, 1] = 5.  Clinically the severe-depression-
        with-pervasive-dissatisfaction profile."""
        result = score_swls([1, 1, 1, 1, 1])
        assert result.total == 5
        assert result.severity == "continuous"

    def test_vignette_dissatisfied_band(self) -> None:
        """Pavot 1993 "Dissatisfied" band (10-14).  Raw
        [2, 3, 3, 2, 2] = 12."""
        result = score_swls([2, 3, 3, 2, 2])
        assert result.total == 12

    def test_vignette_slightly_dissatisfied_band(self) -> None:
        """Pavot 1993 "Slightly dissatisfied" band (15-19).  Raw
        [3, 4, 3, 4, 3] = 17.  Early-recovery profile where
        cognitive evaluation still lags affective improvement —
        Moos 2005 delayed-relapse-risk window."""
        result = score_swls([3, 4, 3, 4, 3])
        assert result.total == 17

    def test_vignette_pavot_neutral_single_value(self) -> None:
        """Pavot 1993 "Neutral" point at exactly 20.  Raw
        [4, 4, 4, 4, 4] = 20.  Pavot 1993 treated this as a
        single-value band, not collapsed into dissatisfied or
        satisfied bands — the platform preserves this as a
        continuous value, not a band."""
        result = score_swls([4, 4, 4, 4, 4])
        assert result.total == 20
        assert result.severity == "continuous"

    def test_vignette_slightly_satisfied_band(self) -> None:
        """Pavot 1993 "Slightly satisfied" band (21-25).  Raw
        [4, 5, 4, 5, 4] = 22."""
        result = score_swls([4, 5, 4, 5, 4])
        assert result.total == 22

    def test_vignette_satisfied_band(self) -> None:
        """Pavot 1993 "Satisfied" band (26-30).  Raw
        [5, 6, 5, 6, 6] = 28.  Stable-recovery profile — Moos 2005
        long-horizon-remission predictor at this range in 1-3
        years post-treatment."""
        result = score_swls([5, 6, 5, 6, 6])
        assert result.total == 28

    def test_vignette_extremely_satisfied_ceiling(self) -> None:
        """Pavot 1993 "Extremely satisfied" ceiling (31-35).  Raw
        [7, 7, 7, 7, 7] = 35."""
        result = score_swls([7, 7, 7, 7, 7])
        assert result.total == 35

    def test_vignette_moos_delayed_relapse_profile(self) -> None:
        """Moos 2005 delayed-relapse signature: improved affective
        wellbeing (WHO-5 would be high) with persistent low
        cognitive satisfaction.  SWLS = 13 ("Dissatisfied" band)
        in a client 18 months post-AUD-treatment with good mood
        but "this isn't the life I want" cognitive profile.  Raw
        [2, 3, 3, 3, 2] = 13."""
        result = score_swls([2, 3, 3, 3, 2])
        assert result.total == 13
        assert result.severity == "continuous"

    def test_vignette_wrong_life_profile_item4_and_5_low(
        self,
    ) -> None:
        """Hayes 2006 ACT values-clarification indication: the
        "wrong-life" profile features low item-4 (important things
        attained) and low item-5 (would change nothing).  Present-
        state items (1-3) may be neutral.  Raw [4, 4, 4, 2, 1] = 15,
        the Pavot 1993 "Slightly dissatisfied" floor.  Flags for
        values-mapping intervention, not further affect-work."""
        result = score_swls([4, 4, 4, 2, 1])
        assert result.total == 15
        assert result.severity == "continuous"

    def test_vignette_cbt_responder_trajectory(self) -> None:
        """12-week CBT + behavioral-activation responder signature:
        pre-treatment [2, 2, 3, 2, 2] = 11 ("Dissatisfied"), post-
        treatment [5, 5, 5, 4, 4] = 23 ("Slightly satisfied").
        Delta 12 is substantially above the Jacobson 1991 RCI MCID
        (≈6 points derived from α ≈ 0.87 and Pavot 2008 SD ≈ 6.6);
        documents reliable clinical change in the trajectory
        layer."""
        pre = score_swls([2, 2, 3, 2, 2])
        post = score_swls([5, 5, 5, 4, 4])
        assert pre.total == 11
        assert post.total == 23
        assert post.total - pre.total == 12

    def test_vignette_hopelessness_dissociation_low_swls_low_lotr(
        self,
    ) -> None:
        """Beck 1985 hopelessness-suicide-risk profile: persistently
        low SWLS paired (at the clinician-UI layer) with low LOT-R.
        SWLS = 7 ("Extremely dissatisfied") signals the "my life
        isn't good" cognitive half of the profile.  The ASSESSMENT
        itself MUST NOT set T3 — that stays on C-SSRS / PHQ-9
        item 9 — but the low-SWLS × low-LOT-R profile prompts
        clinician-UI C-SSRS follow-up."""
        result = score_swls([1, 2, 2, 1, 1])
        assert result.total == 7
        assert result.severity == "continuous"
        assert not hasattr(result, "requires_t3")

    def test_vignette_improving_life_evaluation(self) -> None:
        """6-month trajectory from acute-relapse-aftermath (low 8)
        to stabilizing baseline (slightly satisfied 22).  Delta
        14 on the 5-35 range (47% of range) — unambiguous clinical
        improvement signal at the trajectory layer."""
        pre = score_swls([1, 2, 2, 2, 1])
        post = score_swls([4, 5, 4, 5, 4])
        assert pre.total == 8
        assert post.total == 22
        assert post.total - pre.total == 14


class TestResultInstanceShape:
    """Pin the positional fields present on SwlsResult."""

    def test_result_has_total_severity_items(self) -> None:
        result = score_swls([4, 4, 4, 4, 4])
        assert isinstance(result, SwlsResult)
        assert isinstance(result.total, int)
        assert result.severity == "continuous"
        assert len(result.items) == 5
        assert all(isinstance(v, int) for v in result.items)

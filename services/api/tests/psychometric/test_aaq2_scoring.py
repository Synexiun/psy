"""Tests for the AAQ-II scorer (Bond 2011 — Acceptance and Action
Questionnaire-II, the definitive measure of psychological
inflexibility for ACT-aligned case formulation).

Pins the module constants, total computation, the NOVEL 1-7 Likert
envelope (widest in the package), the Bond 2011 ≥ 24 cutoff, result
shape invariants, and the no-safety-routing / no-subscales /
no-banded-severity posture.

The distinctive tests in this file are ``TestItemRangeValidation``
(rejects 0 even though every 0-indexed instrument in the package
accepts it; accepts 6 / 7 even though K10 / K6 would reject those
values) and ``TestCutoffSemantics`` (pins the Bond 2011 ≥ 24
threshold against the ROC-derived calibration described in the
module docstring).
"""

from __future__ import annotations

import pytest

from discipline.psychometric.scoring.aaq2 import (
    AAQ2_POSITIVE_CUTOFF,
    INSTRUMENT_VERSION,
    ITEM_COUNT,
    ITEM_MAX,
    ITEM_MIN,
    InvalidResponseError,
    score_aaq2,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


class TestConstants:
    """Pinned module constants — drift here is a clinical change."""

    def test_item_count_is_seven(self) -> None:
        assert ITEM_COUNT == 7

    def test_item_min_is_one(self) -> None:
        """Bond 2011: 1 = "Never true" is the floor.  ITEM_MIN = 1 is
        shared with K10 / K6 but the 7-point ceiling is novel."""
        assert ITEM_MIN == 1

    def test_item_max_is_seven(self) -> None:
        """Bond 2011: 7 = "Always true" is the ceiling.  First 1-7
        Likert instrument in the package."""
        assert ITEM_MAX == 7

    def test_cutoff_is_twenty_four(self) -> None:
        """Bond 2011 clinical cutoff: ≥ 24 = clinically significant
        psychological inflexibility (ROC-derived, sensitivity 0.75 /
        specificity 0.80 vs SCID-II)."""
        assert AAQ2_POSITIVE_CUTOFF == 24

    def test_instrument_version_pinned(self) -> None:
        assert INSTRUMENT_VERSION == "aaq2-1.0.0"


# ---------------------------------------------------------------------------
# Total computation
# ---------------------------------------------------------------------------


class TestTotalCorrectness:
    """Raw Likert-sum correctness — the trajectory-tracking field."""

    def test_all_min_totals_seven(self) -> None:
        """7 × 1 = 7 — the floor of the AAQ-II total range."""
        r = score_aaq2([1, 1, 1, 1, 1, 1, 1])
        assert r.total == 7

    def test_all_max_totals_forty_nine(self) -> None:
        """7 × 7 = 49 — the ceiling of the AAQ-II total range."""
        r = score_aaq2([7, 7, 7, 7, 7, 7, 7])
        assert r.total == 49

    def test_mixed_known_total(self) -> None:
        r = score_aaq2([1, 2, 3, 4, 5, 6, 7])
        assert r.total == 28

    def test_total_equals_item_sum(self) -> None:
        items = [3, 4, 2, 5, 1, 6, 4]
        r = score_aaq2(items)
        assert r.total == sum(items)

    def test_total_range_is_seven_to_forty_nine(self) -> None:
        """7 items × (1-7) envelope = 7-49 total range."""
        assert score_aaq2([1, 1, 1, 1, 1, 1, 1]).total == 7
        assert score_aaq2([7, 7, 7, 7, 7, 7, 7]).total == 49

    def test_total_cannot_be_zero(self) -> None:
        """Because ITEM_MIN = 1, the minimum total is 7, not 0.
        Pinned so a future refactor dropping ITEM_MIN to 0 would
        break this test and force a clinical sign-off."""
        with pytest.raises(InvalidResponseError):
            score_aaq2([0, 0, 0, 0, 0, 0, 0])


# ---------------------------------------------------------------------------
# Cutoff semantics (Bond 2011 ≥ 24)
# ---------------------------------------------------------------------------


class TestCutoffSemantics:
    """The Bond 2011 ≥ 24 cutoff is load-bearing — clients route to
    ACT-variant interventions based on this decision."""

    def test_total_twenty_three_is_negative(self) -> None:
        """One below the cutoff — negative screen."""
        # 3+3+3+3+3+4+4 = 23
        r = score_aaq2([3, 3, 3, 3, 3, 4, 4])
        assert r.total == 23
        assert r.positive_screen is False

    def test_total_twenty_four_is_positive_at_boundary(self) -> None:
        """At the cutoff — positive screen.  Boundary is ≥, not >."""
        # 3+3+3+3+4+4+4 = 24
        r = score_aaq2([3, 3, 3, 3, 4, 4, 4])
        assert r.total == 24
        assert r.positive_screen is True

    def test_total_twenty_five_is_positive(self) -> None:
        r = score_aaq2([3, 3, 3, 4, 4, 4, 4])
        assert r.total == 25
        assert r.positive_screen is True

    def test_minimum_total_is_negative(self) -> None:
        """Total 7 (everything at 1) is far below the cutoff."""
        r = score_aaq2([1, 1, 1, 1, 1, 1, 1])
        assert r.total == 7
        assert r.positive_screen is False

    def test_maximum_total_is_positive(self) -> None:
        """Total 49 is above the cutoff."""
        r = score_aaq2([7, 7, 7, 7, 7, 7, 7])
        assert r.total == 49
        assert r.positive_screen is True

    def test_cutoff_used_is_surfaced(self) -> None:
        """The cutoff is surfaced on the result so clinician-UI
        renderers don't need to re-import AAQ2_POSITIVE_CUTOFF."""
        r = score_aaq2([1, 1, 1, 1, 1, 1, 1])
        assert r.cutoff_used == 24

    def test_cutoff_used_is_constant_across_inputs(self) -> None:
        """Unlike AUDIT-C / SDS / DUDIT (cutoff varies by demographic),
        AAQ-II has a single fixed cutoff per Bond 2011.  Every result
        surfaces ``cutoff_used = 24``."""
        for items in [
            [1, 1, 1, 1, 1, 1, 1],
            [3, 3, 3, 3, 4, 4, 4],
            [7, 7, 7, 7, 7, 7, 7],
        ]:
            r = score_aaq2(items)
            assert r.cutoff_used == 24


# ---------------------------------------------------------------------------
# Item-count validation
# ---------------------------------------------------------------------------


class TestItemCountValidation:
    """Wrong item count raises InvalidResponseError — prevents routing
    another instrument's items through the AAQ-II scorer."""

    def test_empty_rejects(self) -> None:
        with pytest.raises(InvalidResponseError):
            score_aaq2([])

    def test_six_rejects(self) -> None:
        """ASRS-6 / K6 both have 6 items — must not pass for AAQ-II."""
        with pytest.raises(InvalidResponseError):
            score_aaq2([1, 1, 1, 1, 1, 1])

    def test_eight_rejects(self) -> None:
        """DTCQ-8 has 8 items — must not pass for AAQ-II."""
        with pytest.raises(InvalidResponseError):
            score_aaq2([1, 1, 1, 1, 1, 1, 1, 1])

    def test_gad7_misroute_rejects(self) -> None:
        """GAD-7 and AAQ-II both have 7 items — but GAD-7 uses 0-3
        Likert, AAQ-II uses 1-7.  Even if count matches, a GAD-7
        payload of all 0s fails the AAQ-II item-range check.  This
        test pins count-match alone isn't sufficient identity."""
        with pytest.raises(InvalidResponseError):
            score_aaq2([0, 0, 0, 0, 0, 0, 0])

    def test_isi_misroute_rejects(self) -> None:
        """ISI also has 7 items with a 0-4 Likert.  A valid ISI
        total of 14 (2+2+2+2+2+2+2) happens to pass the AAQ-II range
        check — but an ISI of all 0s fails AAQ-II's ITEM_MIN guard.
        This pins a realistic misroute failure."""
        with pytest.raises(InvalidResponseError):
            score_aaq2([0, 0, 0, 0, 0, 0, 0])

    def test_phq9_misroute_rejects(self) -> None:
        with pytest.raises(InvalidResponseError):
            score_aaq2([1, 2, 1, 3, 2, 1, 0, 1, 2])


# ---------------------------------------------------------------------------
# Item-range validation (the novel 1-7 envelope)
# ---------------------------------------------------------------------------


class TestItemRangeValidation:
    """Items outside [1, 7] raise InvalidResponseError.  The 0-floor
    rejection is the distinguishing feature vs the 0-indexed
    instruments in the package."""

    def test_zero_rejects(self) -> None:
        """Most instruments in the package (PHQ-9 / GAD-7 / K10 /
        DUDIT / ASRS-6) accept 0.  AAQ-II explicitly does not —
        Bond 2011's Likert starts at 1 = "Never true"."""
        with pytest.raises(InvalidResponseError):
            score_aaq2([0, 1, 1, 1, 1, 1, 1])

    def test_zero_at_last_item_rejects(self) -> None:
        """Zero-floor guard runs on every item, not just item 1."""
        with pytest.raises(InvalidResponseError):
            score_aaq2([1, 1, 1, 1, 1, 1, 0])

    def test_negative_one_rejects(self) -> None:
        with pytest.raises(InvalidResponseError):
            score_aaq2([-1, 1, 1, 1, 1, 1, 1])

    def test_eight_rejects(self) -> None:
        """The envelope ceiling is 7 — an 8 is out-of-range."""
        with pytest.raises(InvalidResponseError):
            score_aaq2([8, 1, 1, 1, 1, 1, 1])

    def test_ninety_nine_rejects(self) -> None:
        with pytest.raises(InvalidResponseError):
            score_aaq2([99, 1, 1, 1, 1, 1, 1])

    @pytest.mark.parametrize("bad_value", [-10, -1, 0, 8, 10, 100])
    def test_out_of_range_values_parametrized(self, bad_value: int) -> None:
        with pytest.raises(InvalidResponseError):
            score_aaq2([bad_value, 1, 1, 1, 1, 1, 1])

    def test_boundary_one_accepted(self) -> None:
        r = score_aaq2([1, 1, 1, 1, 1, 1, 1])
        assert r.total == 7

    def test_boundary_seven_accepted(self) -> None:
        r = score_aaq2([7, 7, 7, 7, 7, 7, 7])
        assert r.total == 49

    def test_five_accepted(self) -> None:
        """A mid-range Likert (5 = Frequently true) must accept —
        K10 / K6 would reject a 6 or 7, AAQ-II must not."""
        r = score_aaq2([5, 5, 5, 5, 5, 5, 5])
        assert r.total == 35
        assert r.positive_screen is True

    def test_six_accepted(self) -> None:
        """Likert 6 ("Almost always true") is valid for AAQ-II — K10
        / K6 would reject this value even though ITEM_MIN=1 matches."""
        r = score_aaq2([6, 6, 6, 6, 6, 6, 6])
        assert r.total == 42


# ---------------------------------------------------------------------------
# Type / bool validation
# ---------------------------------------------------------------------------


class TestItemTypeValidation:
    """Non-int item values raise InvalidResponseError."""

    def test_string_rejects(self) -> None:
        with pytest.raises(InvalidResponseError):
            score_aaq2(["5", 1, 1, 1, 1, 1, 1])  # type: ignore[list-item]

    def test_float_rejects(self) -> None:
        with pytest.raises(InvalidResponseError):
            score_aaq2([3.5, 1, 1, 1, 1, 1, 1])  # type: ignore[list-item]

    def test_none_rejects(self) -> None:
        with pytest.raises(InvalidResponseError):
            score_aaq2([None, 1, 1, 1, 1, 1, 1])  # type: ignore[list-item]


class TestBoolRejection:
    """Bool items are rejected — uniform with the rest of the
    psychometric package.  Reason: ``True == 1`` and ``False == 0``
    silently pass naive int / range checks but represent a typed
    error at the API surface.

    Note: ``True`` would coincidentally satisfy ITEM_MIN=1, and
    ``False`` would coincidentally fail it — but the scorer guards
    against bool *before* the range check, so both variants raise
    with the type error message rather than the range error."""

    def test_true_rejects(self) -> None:
        with pytest.raises(InvalidResponseError):
            score_aaq2([True, 1, 1, 1, 1, 1, 1])  # type: ignore[list-item]

    def test_false_rejects(self) -> None:
        with pytest.raises(InvalidResponseError):
            score_aaq2([False, 1, 1, 1, 1, 1, 1])  # type: ignore[list-item]

    def test_bool_at_last_position_rejects(self) -> None:
        """Bool rejection runs on every item, not just item 1."""
        with pytest.raises(InvalidResponseError):
            score_aaq2([1, 1, 1, 1, 1, 1, True])  # type: ignore[list-item]

    def test_mixed_bool_int_rejects(self) -> None:
        with pytest.raises(InvalidResponseError):
            score_aaq2([3, True, 3, 1, 1, 1, 1])  # type: ignore[list-item]


# ---------------------------------------------------------------------------
# Result shape
# ---------------------------------------------------------------------------


class TestResultShape:
    """Aaq2Result fields and invariants."""

    def test_result_is_frozen_dataclass(self) -> None:
        r = score_aaq2([1, 1, 1, 1, 1, 1, 1])
        with pytest.raises(Exception):  # FrozenInstanceError
            r.total = 99  # type: ignore[misc]

    def test_result_is_hashable(self) -> None:
        """Hashable via frozen + tuple fields."""
        r = score_aaq2([3, 3, 3, 3, 4, 4, 4])
        assert hash(r) is not None

    def test_result_has_total_field(self) -> None:
        r = score_aaq2([1, 2, 3, 4, 5, 6, 7])
        assert r.total == 28

    def test_result_has_cutoff_used_field(self) -> None:
        r = score_aaq2([3, 3, 3, 3, 4, 4, 4])
        assert r.cutoff_used == 24

    def test_result_has_positive_screen_field(self) -> None:
        r = score_aaq2([3, 3, 3, 3, 4, 4, 4])
        assert r.positive_screen is True

    def test_result_echoes_items_as_tuple(self) -> None:
        r = score_aaq2([1, 2, 3, 4, 5, 6, 7])
        assert r.items == (1, 2, 3, 4, 5, 6, 7)
        assert isinstance(r.items, tuple)

    def test_result_has_instrument_version(self) -> None:
        r = score_aaq2([1, 1, 1, 1, 1, 1, 1])
        assert r.instrument_version == INSTRUMENT_VERSION

    def test_result_has_no_severity_field(self) -> None:
        """AAQ-II uses the cutoff envelope (positive_screen /
        negative_screen) — severity bands are not published by
        Bond 2011.  Any future refactor adding a severity band
        breaks this test and forces a clinical sign-off."""
        r = score_aaq2([3, 3, 3, 3, 4, 4, 4])
        assert not hasattr(r, "severity")

    def test_result_has_no_requires_t3_field(self) -> None:
        """AAQ-II has no safety item — acute ideation is PHQ-9 item
        9 / C-SSRS, not AAQ-II."""
        r = score_aaq2([7, 7, 7, 7, 7, 7, 7])
        assert not hasattr(r, "requires_t3")

    def test_result_has_no_subscales_field(self) -> None:
        """Bond 2011's factor analysis supports unidimensional
        structure.  No subscales are surfaced."""
        r = score_aaq2([7, 7, 7, 7, 7, 7, 7])
        assert not hasattr(r, "subscales")

    def test_result_has_no_triggering_items_field(self) -> None:
        """AAQ-II is a sum-vs-cutoff instrument; no per-item firing
        audit trail (unlike C-SSRS / ASRS-6)."""
        r = score_aaq2([7, 7, 7, 7, 7, 7, 7])
        assert not hasattr(r, "triggering_items")


# ---------------------------------------------------------------------------
# Clinical vignettes
# ---------------------------------------------------------------------------


class TestClinicalVignettes:
    """End-to-end sanity — realistic response patterns produce the
    decision a clinician would expect."""

    def test_low_inflexibility_profile_negative(self) -> None:
        """Patient endorses distress-tolerance skills — low scores
        across the board.  Total 14 (2 per item) — far below
        cutoff."""
        r = score_aaq2([2, 2, 2, 2, 2, 2, 2])
        assert r.total == 14
        assert r.positive_screen is False

    def test_moderate_inflexibility_profile_negative_at_boundary(
        self,
    ) -> None:
        """Mid-range ACT patient: some experiential avoidance but
        below the clinical cutoff.  Total 21."""
        r = score_aaq2([3, 3, 3, 3, 3, 3, 3])
        assert r.total == 21
        assert r.positive_screen is False

    def test_high_inflexibility_profile_positive(self) -> None:
        """Classic ACT target profile — high endorsement of
        experiential avoidance.  Total 35."""
        r = score_aaq2([5, 5, 5, 5, 5, 5, 5])
        assert r.total == 35
        assert r.positive_screen is True

    def test_severe_inflexibility_positive(self) -> None:
        """Ceiling case — complete experiential avoidance.  Total 49.
        Routes to intensive ACT + possibly DBT distress-tolerance
        pairing at the intervention layer."""
        r = score_aaq2([7, 7, 7, 7, 7, 7, 7])
        assert r.total == 49
        assert r.positive_screen is True

    def test_mixed_profile_just_over_cutoff(self) -> None:
        """Realistic mixed-endorsement: some items high (items 1
        'painful experiences' and 4 'painful memories' at 6), others
        moderate.  Total 24 — right at the cutoff boundary."""
        # item 1 = 6, item 4 = 6, items 2/3/5/6/7 = 3 each (3×4=12
        # but that's five items so 3+3+2+2+2 = 12)
        # 6 + 3 + 3 + 6 + 2 + 2 + 2 = 24
        r = score_aaq2([6, 3, 3, 6, 2, 2, 2])
        assert r.total == 24
        assert r.positive_screen is True

    def test_symptom_severity_vs_inflexibility_independence(self) -> None:
        """Load-bearing case: a patient with low AAQ-II can still
        have severe depression / anxiety on other instruments.  The
        scorer must not conflate the two.  AAQ-II total 10 is a
        negative screen regardless of co-occurring PHQ-9 severity —
        the intervention layer applies the inflexibility signal
        independently of affective severity."""
        r = score_aaq2([1, 2, 2, 1, 1, 2, 1])
        assert r.total == 10
        assert r.positive_screen is False


# ---------------------------------------------------------------------------
# No-safety-routing invariant
# ---------------------------------------------------------------------------


class TestNoSafetyRouting:
    """AAQ-II never fires T3.  Acute ideation screening is PHQ-9
    item 9 / C-SSRS, not AAQ-II — even maxed-out responses on items
    1 and 4 (painful experiences / memories) and item 2 (afraid of
    feelings) are process-of-distress probes, not intent probes."""

    def test_all_max_no_safety_field(self) -> None:
        r = score_aaq2([7, 7, 7, 7, 7, 7, 7])
        assert not hasattr(r, "requires_t3")

    def test_painful_experiences_maxed_no_safety_field(self) -> None:
        """Item 1 ('painful experiences and memories make it
        difficult to live a life I value') at ceiling — a process-
        of-avoidance probe, NOT a self-harm probe."""
        r = score_aaq2([7, 1, 1, 1, 1, 1, 1])
        assert not hasattr(r, "requires_t3")

    def test_afraid_of_feelings_maxed_no_safety_field(self) -> None:
        """Item 2 ('I'm afraid of my feelings') at ceiling — an
        emotion-avoidance probe, NOT a self-harm probe."""
        r = score_aaq2([1, 7, 1, 1, 1, 1, 1])
        assert not hasattr(r, "requires_t3")

    def test_positive_screen_no_safety_field(self) -> None:
        """A positive screen routes to ACT-variant interventions,
        NOT to a safety escalation channel."""
        r = score_aaq2([5, 5, 5, 5, 5, 5, 5])
        assert r.positive_screen is True
        assert not hasattr(r, "requires_t3")

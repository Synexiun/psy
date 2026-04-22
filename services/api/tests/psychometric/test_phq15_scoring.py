"""PHQ-15 scoring tests — Kroenke 2002.

Three load-bearing correctness properties for the 15-item PHQ-15:

1. **Severity bands are Kroenke-2002 boundaries.**  The published
   cutoffs are 4/5 (minimal→low), 9/10 (low→medium), 14/15
   (medium→high).  A fence-post regression at any of these three
   boundaries would mis-classify clinical-decision-point patients.
2. **Item range is 0-2, not 0-3 (PHQ-9) or 0-4 (GAD-7 / ISI).**
   Kroenke 2002 chose a tighter Likert scale because the
   bothered-at-all step is the clinically meaningful unit for
   somatic symptoms.  A copy-paste bug that reused the 0-4
   validator from ISI would silently accept invalid 3s and 4s
   as real item values, inflating totals and pushing patients
   into higher bands.
3. **Exactly 15 items.**  Item 4 is sex-specific (menstrual
   cramps/periods) and is coded 0 by male respondents per the
   Kroenke 2002 convention — but the scorer always takes 15
   items; sex-awareness lives in the clinician-UI layer that
   submits the pre-coded 15-tuple.

Coverage strategy:
- Pin all three band boundaries (4/5, 9/10, 14/15).
- Pin item-range ceiling (reject 3 — the "almost looks like PHQ-9"
  case).
- Item-count validation.
- Bool rejection.
- Clinical vignettes — minimal somatization, somatization-dominant
  presentation (high band), male-respondent item 4 = 0 handling.
- No safety routing.
"""

from __future__ import annotations

import pytest

from discipline.psychometric.scoring.phq15 import (
    INSTRUMENT_VERSION,
    ITEM_COUNT,
    ITEM_MAX,
    ITEM_MIN,
    PHQ15_SEVERITY_THRESHOLDS,
    InvalidResponseError,
    score_phq15,
)


def _zeros() -> list[int]:
    return [0] * ITEM_COUNT


class TestConstants:
    """Pin published constants so drift from Kroenke 2002 is caught."""

    def test_item_count_is_fifteen(self) -> None:
        assert ITEM_COUNT == 15

    def test_item_range_is_zero_to_two(self) -> None:
        """0-2 Likert — tighter than PHQ-9 (0-3) and ISI / GAD-7
        (0-4).  A refactor that widened this range would silently
        accept malformed submissions and inflate severity."""
        assert ITEM_MIN == 0
        assert ITEM_MAX == 2

    def test_severity_thresholds_match_kroenke_2002(self) -> None:
        """Kroenke 2002 §Results — cutoffs 4/9/14 across the four
        bands.  Any change is a clinical change."""
        assert PHQ15_SEVERITY_THRESHOLDS == (
            (4, "minimal"),
            (9, "low"),
            (14, "medium"),
            (30, "high"),
        )

    def test_instrument_version_pinned(self) -> None:
        assert INSTRUMENT_VERSION == "phq15-1.0.0"


class TestTotalCorrectness:
    """Straight 0-30 sum (no reverse-coding)."""

    def test_zero_is_minimum(self) -> None:
        result = score_phq15(_zeros())
        assert result.total == 0

    def test_max_is_thirty(self) -> None:
        """15 items × max 2 = 30."""
        result = score_phq15([2] * ITEM_COUNT)
        assert result.total == 30

    def test_mixed_sum(self) -> None:
        """Arbitrary mix — verifies the total is a plain sum."""
        items = [2, 1, 0, 2, 1, 0, 2, 1, 0, 2, 1, 0, 2, 1, 0]
        result = score_phq15(items)
        assert result.total == sum(items)


class TestSeverityBandBoundaries:
    """All three published Kroenke-2002 band boundaries pinned with
    just-below / at-boundary pairs so fence-post regressions are
    caught at every clinical decision point."""

    def test_total_zero_is_minimal(self) -> None:
        """Total 0 → minimal band (lower edge of the first band)."""
        result = score_phq15(_zeros())
        assert result.total == 0
        assert result.severity == "minimal"

    def test_total_four_is_minimal(self) -> None:
        """Total 4 → last value of minimal band.  A ``< 4`` bug
        would push this into low band and over-identify."""
        items = _zeros()
        items[0] = 2
        items[1] = 2  # 2+2 = 4
        result = score_phq15(items)
        assert result.total == 4
        assert result.severity == "minimal"

    def test_total_five_is_low(self) -> None:
        """Total 5 → first value of low band (the minimal→low
        transition).  A ``<= 4`` off-by-one would leave this
        misclassified as minimal."""
        items = _zeros()
        items[0] = 2
        items[1] = 2
        items[2] = 1  # 2+2+1 = 5
        result = score_phq15(items)
        assert result.total == 5
        assert result.severity == "low"

    def test_total_nine_is_low(self) -> None:
        """Total 9 → last value of low band."""
        items = _zeros()
        for i in range(4):
            items[i] = 2
        items[4] = 1  # 4×2 + 1 = 9
        result = score_phq15(items)
        assert result.total == 9
        assert result.severity == "low"

    def test_total_ten_is_medium(self) -> None:
        """Total 10 → first value of medium band (the low→medium
        transition).  Kroenke 2002 cites this as a practical
        clinical-referral threshold — mis-classifying here would
        suppress a flag that a clinician-UI reads to escalate
        somatic-work-up recommendations."""
        items = _zeros()
        for i in range(5):
            items[i] = 2  # 5×2 = 10
        result = score_phq15(items)
        assert result.total == 10
        assert result.severity == "medium"

    def test_total_fourteen_is_medium(self) -> None:
        """Total 14 → last value of medium band."""
        items = _zeros()
        for i in range(7):
            items[i] = 2  # 7×2 = 14
        result = score_phq15(items)
        assert result.total == 14
        assert result.severity == "medium"

    def test_total_fifteen_is_high(self) -> None:
        """Total 15 → first value of high band (the medium→high
        transition).  The high band is the clinician-UI's
        'somatization-dominant — route to interoceptive-exposure /
        somatic-awareness work' trigger; the boundary must match
        Kroenke 2002 exactly."""
        items = _zeros()
        for i in range(7):
            items[i] = 2
        items[7] = 1  # 7×2 + 1 = 15
        result = score_phq15(items)
        assert result.total == 15
        assert result.severity == "high"

    def test_total_thirty_is_high(self) -> None:
        """Total 30 (maximum) → high band."""
        result = score_phq15([2] * ITEM_COUNT)
        assert result.total == 30
        assert result.severity == "high"


class TestItemCountValidation:
    """Exactly 15 items required."""

    def test_rejects_fourteen_items(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 15 items"):
            score_phq15([0] * 14)

    def test_rejects_sixteen_items(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 15 items"):
            score_phq15([0] * 16)

    def test_rejects_empty(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 15 items"):
            score_phq15([])


class TestItemRangeValidation:
    """Items must be in [0, 2] — tighter than other PHQ instruments."""

    @pytest.mark.parametrize("bad_value", [-1, 3, 4, 10])
    def test_rejects_out_of_range(self, bad_value: int) -> None:
        """3 is a particularly important reject case: PHQ-9 is 0-3,
        so a copy-paste regression from the PHQ-9 validator would
        silently accept 3 as valid and inflate PHQ-15 totals past
        the Kroenke-2002 published ceiling of 30."""
        items = _zeros()
        items[7] = bad_value
        with pytest.raises(InvalidResponseError, match="out of range"):
            score_phq15(items)

    def test_error_names_one_indexed_item(self) -> None:
        """Error messages use 1-indexed item numbers to match the
        PHQ-15 instrument document."""
        items = _zeros()
        items[5] = 99  # item 6 (index 5) — chest pain
        with pytest.raises(InvalidResponseError, match="PHQ-15 item 6"):
            score_phq15(items)

    def test_rejects_string_item(self) -> None:
        items = _zeros()
        items[0] = "2"  # type: ignore[call-overload]
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_phq15(items)

    def test_rejects_float_item(self) -> None:
        items = _zeros()
        items[0] = 2.0  # type: ignore[call-overload]
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_phq15(items)


class TestBoolRejection:
    """Bool items rejected even though True/False map to valid 1/0.
    Rationale: uniform wire contract across the psychometric package
    (same policy as MDQ, ISI, PCL-5, PC-PTSD-5, OCI-R).
    """

    def test_rejects_true_item(self) -> None:
        items = _zeros()
        items[0] = True  # type: ignore[call-overload]
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_phq15(items)

    def test_rejects_false_item(self) -> None:
        items = _zeros()
        items[0] = False  # type: ignore[call-overload]
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_phq15(items)


class TestResultShape:
    """Phq15Result carries the fields the router + trajectory layer
    need."""

    def test_result_is_frozen(self) -> None:
        result = score_phq15(_zeros())
        with pytest.raises(Exception):  # FrozenInstanceError subclass
            result.total = 99  # type: ignore[misc]

    def test_items_are_tuple(self) -> None:
        """Tuple so Phq15Result is hashable and the stored repository
        record is immutable."""
        items = [1, 2, 0, 1, 2, 0, 1, 2, 0, 1, 2, 0, 1, 2, 0]
        result = score_phq15(items)
        assert isinstance(result.items, tuple)
        assert result.items == tuple(items)

    def test_result_echoes_instrument_version(self) -> None:
        result = score_phq15(_zeros())
        assert result.instrument_version == INSTRUMENT_VERSION

    def test_no_requires_t3_field(self) -> None:
        """PHQ-15 has no suicidality item.  The result dataclass
        deliberately omits requires_t3 so downstream routing cannot
        accidentally escalate a high-somatization patient into T3.
        Item 6 (chest pain) + item 8 (fainting) are surfaced by the
        clinician-UI layer as medical-evaluation signals, NOT as
        crisis-path triggers.  Co-administer PHQ-9 / C-SSRS for
        suicidality differential."""
        result = score_phq15([2] * ITEM_COUNT)
        assert not hasattr(result, "requires_t3")


class TestClinicalVignettes:
    """Named patterns a clinician would recognize."""

    def test_minimal_somatization_presentation(self) -> None:
        """All items 0 → minimal band.  The baseline case —
        healthy-somatic patient with no bodily-complaint burden."""
        result = score_phq15(_zeros())
        assert result.total == 0
        assert result.severity == "minimal"

    def test_somatization_dominant_high_band(self) -> None:
        """Classic somatization-dominant presentation — multiple
        bodily complaints at moderate intensity.  Clinically
        routes to interoceptive-exposure / somatic-awareness work
        rather than cognitive restructuring."""
        # All 15 items at 2 → total 30 → high
        result = score_phq15([2] * ITEM_COUNT)
        assert result.total == 30
        assert result.severity == "high"

    def test_male_respondent_item_4_zero(self) -> None:
        """Per Kroenke 2002 convention, male respondents code item 4
        (menstrual cramps/periods) as 0.  The scorer is sex-blind —
        it takes 15 pre-coded items and sums them.  The effective
        ceiling for a male respondent is 28 (14 items × 2), not 30;
        the same bands still apply.  Pin that a male submission
        with 0 at item 4 scores and classifies correctly."""
        # Male respondent with moderate pain/fatigue — item 4 = 0,
        # other items varied.  Build to land in the medium band:
        # items 1 (stomach) = 2, 2 (back) = 2, 3 (limbs) = 2, 4 = 0,
        # 5 (headache) = 2, 6 (chest) = 1, 7 (dizzy) = 1, others 0.
        items = [2, 2, 2, 0, 2, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0]
        result = score_phq15(items)
        assert result.items[3] == 0  # item 4 (index 3) is zero
        assert result.total == 10
        assert result.severity == "medium"

    def test_border_boundary_between_low_and_medium(self) -> None:
        """A common clinical pattern — somatic burden around the
        low→medium transition, where the band label drives whether
        the clinician adds somatic-focused work to the treatment
        plan.  Pin that the boundary resolves predictably."""
        # Total 9 → low; total 10 → medium.
        items_low = _zeros()
        for i in range(4):
            items_low[i] = 2
        items_low[4] = 1  # = 9
        assert score_phq15(items_low).severity == "low"

        items_medium = _zeros()
        for i in range(5):
            items_medium[i] = 2  # = 10
        assert score_phq15(items_medium).severity == "medium"


class TestNoSafetyRouting:
    """PHQ-15 has no direct suicidality item.  Item 6 (chest pain)
    and item 8 (fainting spells) are medical-urgency markers but
    are NOT crisis-routing signals in the platform's T3 sense.  The
    scorer must not expose anything the router could mistake for a
    T3 trigger.
    """

    def test_max_total_has_no_safety_field(self) -> None:
        result = score_phq15([2] * ITEM_COUNT)
        assert not hasattr(result, "requires_t3")
        assert not hasattr(result, "t3_reason")
        assert not hasattr(result, "safety_item_positive")
        assert not hasattr(result, "triggering_items")

    def test_chest_pain_max_has_no_safety_field(self) -> None:
        """Even when item 6 (chest pain) is maxed out (the item most
        likely to be mistaken for a safety-routing trigger), the
        result carries no safety-routing fields.  A renderer that
        keyed off item 6 > threshold to escalate would misroute
        medical signals into the safety stream — crossing the
        boundary between medical urgency and psychiatric crisis."""
        items = _zeros()
        items[5] = 2  # item 6 (chest pain) max
        result = score_phq15(items)
        assert not hasattr(result, "requires_t3")
        assert not hasattr(result, "t3_reason")

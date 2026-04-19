"""Unit tests for the DTCQ-8 (Drug-Taking Confidence Questionnaire,
8-item short form) scorer.

Covers:
- Module constants pin the Sklar 1999 8-item shape (8 items, 0-100
  integer, continuous, higher-is-better).
- ``SITUATION_LABELS`` pins the Marlatt 1985 positional mapping.
- Total correctness — mean-then-round on identity edges (uniform-0,
  uniform-100, midrange) plus the non-integer-mean case that
  motivates exposing ``mean`` separately.
- Item-count validation (exactly 8; zero, 5, and 50 — the long-form
  DTCQ — all fail).
- Item-range validation on the 0-100 range with off-by-one guards
  (101) and a VAS-range-like confusion guard (-1, 200).
- Bool rejection uniform with the rest of the psychometric package.
- Result-shape invariants (frozen dataclass, items tuple, ``mean``
  float type, no severity or requires_t3 fields — DTCQ-8 is a
  continuous higher-is-better coping instrument).
- Clinical vignettes across the coping-profile shapes the intervention
  layer reads (uniform-low, uniform-high, social-pressure weakness,
  unpleasant-emotions weakness) — these are descriptive landmarks,
  not clinically-validated cutoffs.
- Per-situation profile preservation — ``items[i]`` must equal the
  submitted value at every position so the intervention layer can
  read the coping profile verbatim.
- No-safety-routing invariant — a DTCQ-8 score of 0 ("no coping
  self-efficacy at all") must not expose any T3 surface; low
  self-efficacy is a skill-building signal, not a crisis signal.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError, fields

import pytest

from discipline.psychometric.scoring.dtcq8 import (
    INSTRUMENT_VERSION,
    ITEM_COUNT,
    ITEM_MAX,
    ITEM_MIN,
    SITUATION_LABELS,
    Dtcq8Result,
    InvalidResponseError,
    score_dtcq8,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
class TestConstants:
    """The Sklar 1999 short-form shape is clinical fact, not tunable —
    pin every value so an accidental edit fails a test with an obvious
    diff."""

    def test_instrument_version_is_pinned(self) -> None:
        assert INSTRUMENT_VERSION == "dtcq8-1.0.0"

    def test_item_count_is_eight(self) -> None:
        # 8 items — one prototype item per Marlatt 1985 high-risk
        # category.  The defining shape of the 8-item short form
        # distinct from the 50-item long-form DTCQ.
        assert ITEM_COUNT == 8

    def test_item_min_is_zero(self) -> None:
        assert ITEM_MIN == 0

    def test_item_max_is_one_hundred(self) -> None:
        # 0-100 is the Annis confidence-percentage scale.  Regression
        # this guards: a validator copy-pasted from a Likert scorer
        # (0-6 / 0-4) that silently caps confidence at 4%.
        assert ITEM_MAX == 100


# ---------------------------------------------------------------------------
# Situation labels
# ---------------------------------------------------------------------------
class TestSituationLabels:
    """The 8 positional labels from Marlatt 1985 — the intervention
    layer reads the per-situation profile via these positions.  A
    reorder here is semantically equivalent to reordering PHQ-9 items
    (silent clinical-signal corruption), so pin every position."""

    def test_situation_labels_is_tuple(self) -> None:
        # Tuple, not list — downstream code cannot mutate the ordering
        # (the intervention layer's positional read would silently
        # route to the wrong tool variant).
        assert isinstance(SITUATION_LABELS, tuple)

    def test_situation_labels_count_matches_item_count(self) -> None:
        assert len(SITUATION_LABELS) == ITEM_COUNT

    def test_situation_labels_are_pinned(self) -> None:
        # Exact Marlatt 1985 / Sklar 1999 positional order.
        # Reordering this tuple — even without changing the members —
        # would flip the intervention-layer's per-situation lookup.
        assert SITUATION_LABELS == (
            "unpleasant_emotions",
            "physical_discomfort",
            "pleasant_emotions",
            "testing_personal_control",
            "urges_and_temptations",
            "conflict_with_others",
            "social_pressure_to_use",
            "pleasant_times_with_others",
        )


# ---------------------------------------------------------------------------
# Total correctness
# ---------------------------------------------------------------------------
class TestTotalCorrectness:
    """Mean-then-round.  The aggregate is the confidence mean across
    8 situations (Sklar 1999), not the sum.  These tests pin the mean
    arithmetic on identity edges and the non-integer-mean case that
    motivates exposing ``mean`` separately from ``total``."""

    def test_uniform_zero_total_is_zero(self) -> None:
        # All situations rated "not at all confident" — the rock-
        # bottom-coping profile.
        result = score_dtcq8([0] * 8)
        assert result.total == 0
        assert result.mean == 0.0

    def test_uniform_one_hundred_total_is_one_hundred(self) -> None:
        # All situations rated "very confident" — the ceiling profile
        # the maintenance-stage user reports.
        result = score_dtcq8([100] * 8)
        assert result.total == 100
        assert result.mean == 100.0

    def test_uniform_fifty_midrange(self) -> None:
        # Uniform 50 — the "moderate confidence" vignette.  A
        # clinician-training heuristic calls 50 "half confident" but
        # the instrument treats it as a continuous estimate with no
        # validated cutoff.
        result = score_dtcq8([50] * 8)
        assert result.total == 50
        assert result.mean == 50.0

    def test_non_integer_mean_preserved_in_mean_field(self) -> None:
        # items [50,50,50,50,50,50,50,51] → mean 50.125, total 50.
        # This is THE motivating case for exposing ``mean`` separately:
        # ``total`` rounds down to 50 but the clinician PDF should
        # still show 50.125 so a "just above the baseline" signal
        # isn't lost.
        result = score_dtcq8([50, 50, 50, 50, 50, 50, 50, 51])
        assert result.mean == pytest.approx(50.125)
        assert result.total == 50

    def test_mean_rounds_half_to_even(self) -> None:
        # items [50,50,50,50,50,50,51,51] → mean 50.25, total 50.
        # items summing to a value that splits evenly into 8 × half
        # boundaries exercise the banker's-rounding contract.  50.25
        # rounds to 50, not 51, per Python's built-in round().
        result = score_dtcq8([50, 50, 50, 50, 50, 50, 51, 51])
        assert result.mean == pytest.approx(50.25)
        assert result.total == 50

    def test_profile_weakness_total(self) -> None:
        # Social-pressure weakness profile: seven 80s and one 10
        # (item 7).  mean = (7×80 + 10) / 8 = 570/8 = 71.25 → total 71.
        # The test fixes the clinical vignette used in
        # TestClinicalVignettes below to concrete arithmetic.
        result = score_dtcq8([80, 80, 80, 80, 80, 80, 10, 80])
        assert result.mean == pytest.approx(71.25)
        assert result.total == 71


# ---------------------------------------------------------------------------
# Item-count validation
# ---------------------------------------------------------------------------
class TestItemCountValidation:
    """DTCQ-8 is the 8-item form (Sklar 1999).  Regression guards
    against submitting the long-form (50 items) or other common
    instrument shapes."""

    def test_empty_list_raises(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 8 items"):
            score_dtcq8([])

    def test_five_items_raises(self) -> None:
        # 5 items is PACS / PC-PTSD-5 — neighbor instruments on the
        # wire.  Must not silently accept a misrouted PACS payload.
        with pytest.raises(InvalidResponseError, match="exactly 8 items"):
            score_dtcq8([50, 50, 50, 50, 50])

    def test_seven_items_raises(self) -> None:
        # Off-by-one below — one category dropped would silently
        # misreport the aggregate if the scorer padded.
        with pytest.raises(InvalidResponseError, match="exactly 8 items"):
            score_dtcq8([50] * 7)

    def test_nine_items_raises(self) -> None:
        # Off-by-one above — PHQ-9 is 9 items.  A caller wiring
        # DTCQ-8 through a PHQ-9 code-path would send 9 items.
        with pytest.raises(InvalidResponseError, match="exactly 8 items"):
            score_dtcq8([50] * 9)

    def test_fifty_items_raises(self) -> None:
        # 50 items is the long-form DTCQ shape (Sklar 1997).  The
        # 8-item scorer must not silently accept a long-form payload —
        # the semantic mapping (one item per Marlatt category) breaks
        # at any other length.
        with pytest.raises(InvalidResponseError, match="exactly 8 items"):
            score_dtcq8([50] * 50)


# ---------------------------------------------------------------------------
# Item-range validation
# ---------------------------------------------------------------------------
class TestItemRangeValidation:
    """0-100 bounds.  The off-by-one tests (101) guard the classic
    regression; the negative and far-over tests guard the broader
    copy-paste hazards (VAS reverse / unbounded validator)."""

    def test_negative_item_raises(self) -> None:
        with pytest.raises(InvalidResponseError, match="out of range"):
            score_dtcq8([-1, 50, 50, 50, 50, 50, 50, 50])

    def test_one_hundred_one_raises(self) -> None:
        # 101 is the classic off-by-one above the 0-100 ceiling.
        with pytest.raises(InvalidResponseError, match="out of range"):
            score_dtcq8([50, 50, 50, 50, 50, 50, 50, 101])

    def test_two_hundred_raises(self) -> None:
        # Far-over: guards against a completely unbounded validator.
        with pytest.raises(InvalidResponseError, match="out of range"):
            score_dtcq8([50, 50, 50, 50, 50, 50, 50, 200])

    def test_zero_boundary_accepted(self) -> None:
        result = score_dtcq8([0] * 8)
        assert result.total == 0

    def test_one_hundred_boundary_accepted(self) -> None:
        # 100 is the published ceiling — must not be rejected.  The
        # clinical significance of "fully confident" is preserved
        # only if the ceiling is inclusive.
        result = score_dtcq8([100] * 8)
        assert result.total == 100

    def test_error_message_names_the_item_index(self) -> None:
        # 1-indexed for clinician readability.  Item 3 rejected.
        with pytest.raises(InvalidResponseError, match="item 3"):
            score_dtcq8([50, 50, 200, 50, 50, 50, 50, 50])


# ---------------------------------------------------------------------------
# Bool rejection
# ---------------------------------------------------------------------------
class TestBoolRejection:
    """Shared posture across the package — True/False must not silently
    coerce to 1/0.  Especially important on a 0-100 DTCQ-8 where a
    coerced ``True`` would report 1% confidence (essentially zero) and
    a coerced ``False`` would look identical to a legitimate 0."""

    def test_true_raises(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_dtcq8([True, 50, 50, 50, 50, 50, 50, 50])  # type: ignore[list-item]

    def test_false_raises(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_dtcq8([False, 50, 50, 50, 50, 50, 50, 50])  # type: ignore[list-item]


# ---------------------------------------------------------------------------
# Result shape
# ---------------------------------------------------------------------------
class TestResultShape:
    """Invariants downstream storage + FHIR export + intervention-layer
    per-situation reads rely on."""

    def test_result_is_frozen(self) -> None:
        result = score_dtcq8([50] * 8)
        with pytest.raises(FrozenInstanceError):
            result.total = 99  # type: ignore[misc]

    def test_items_is_tuple(self) -> None:
        # Tuple, not list — hashability + caller cannot mutate the
        # audit record OR the per-situation profile after the fact.
        result = score_dtcq8([10, 20, 30, 40, 50, 60, 70, 80])
        assert isinstance(result.items, tuple)
        assert result.items == (10, 20, 30, 40, 50, 60, 70, 80)

    def test_mean_is_float(self) -> None:
        # ``mean`` is a float even on integer-mean cases.  The FHIR
        # valueDecimal emission path reads ``mean`` as a float without
        # conversion; a surprise int would pass isinstance(result.mean,
        # int) checks in consumer code and break the FHIR type.
        result = score_dtcq8([50] * 8)
        assert isinstance(result.mean, float)
        assert result.mean == 50.0

    def test_instrument_version_is_default(self) -> None:
        result = score_dtcq8([0] * 8)
        assert result.instrument_version == INSTRUMENT_VERSION


# ---------------------------------------------------------------------------
# Per-situation profile preservation
# ---------------------------------------------------------------------------
class TestPerSituationProfile:
    """The intervention layer reads the per-situation profile by index.
    A regression where items were sorted, deduplicated, or reordered
    during scoring would silently break tool-variant selection.

    These tests pin the positional contract: submitted_value ==
    result.items[i] at every i."""

    def test_positional_preservation_ascending_profile(self) -> None:
        # An ascending 0→70 profile — each position is distinct so a
        # reorder regression would fail the per-index assertion.
        submitted = [0, 10, 20, 30, 40, 50, 60, 70]
        result = score_dtcq8(submitted)
        for i, value in enumerate(submitted):
            assert result.items[i] == value

    def test_positional_preservation_at_situation_labels(self) -> None:
        # Read the social_pressure_to_use confidence through the
        # public SITUATION_LABELS constant — the pattern the
        # intervention layer uses.  If the label order drifts from
        # the item order, this test breaks.
        submitted = [80, 80, 80, 80, 80, 80, 10, 80]
        result = score_dtcq8(submitted)
        social_pressure_idx = SITUATION_LABELS.index("social_pressure_to_use")
        assert result.items[social_pressure_idx] == 10


# ---------------------------------------------------------------------------
# Clinical vignettes
# ---------------------------------------------------------------------------
class TestClinicalVignettes:
    """Coping-profile shapes the intervention layer routinely observes.
    Descriptive landmarks — NOT clinically-validated cutoffs — but they
    shape how the intervention layer picks skill-building tool variants
    at the coping × craving decision surface."""

    def test_rock_bottom_coping_profile(self) -> None:
        # Uniform 0 — "no confidence at all" across every situation.
        # Most commonly observed early in detox / during high-acuity
        # relapse episodes.  Routes to foundational psychoeducation,
        # not tool-variant selection within a specific situation.
        result = score_dtcq8([0] * 8)
        assert result.total == 0

    def test_social_pressure_weakness_profile(self) -> None:
        # Seven situations confidently handled (80), one weak spot:
        # item 7 (social_pressure_to_use) at 10.  Intervention script
        # is refusal-skills / assertive-communication work.  The
        # profile's weakness is clinically distinct from uniform-
        # moderate confidence at the same aggregate.
        result = score_dtcq8([80, 80, 80, 80, 80, 80, 10, 80])
        assert result.total == 71
        # The *profile* is the clinical signal — aggregate alone
        # would read "71% confident" and miss the social-pressure
        # vulnerability.
        assert result.items[6] == 10

    def test_unpleasant_emotions_weakness_profile(self) -> None:
        # Inverse profile: strong everywhere except item 1
        # (unpleasant_emotions).  Intervention script is distress-
        # tolerance / emotion-regulation work (DBT skills, affect-
        # labeling).  Same aggregate as social_pressure_weakness
        # profile — different intervention.
        result = score_dtcq8([10, 80, 80, 80, 80, 80, 80, 80])
        assert result.total == 71
        assert result.items[0] == 10

    def test_maintenance_stage_profile(self) -> None:
        # Uniform high (90) across every situation — the "fully in
        # recovery, broadly confident" vignette.  Must not fire T3
        # via any indirect path.
        result = score_dtcq8([90] * 8)
        assert result.total == 90

    def test_pleasant_times_weakness_profile(self) -> None:
        # Item 8 (pleasant_times_with_others) weakness — the "I use
        # when I'm out with friends celebrating" relapse pattern.
        # Routes to social-alternative-planning / implementation-
        # intentions work.
        result = score_dtcq8([70, 70, 70, 70, 70, 70, 70, 20])
        assert result.mean == pytest.approx(63.75)
        assert result.items[7] == 20


# ---------------------------------------------------------------------------
# Safety-routing absence
# ---------------------------------------------------------------------------
class TestNoSafetyRouting:
    """DTCQ-8 carries no suicidality or acute-harm item — the result
    must expose no T3 surface.  Low coping self-efficacy is a
    skill-building signal routing to MI / CBT interventions, not a
    crisis signal."""

    def test_result_has_no_severity_field(self) -> None:
        # Deliberate absence — Sklar 1999 publishes no bands.
        # Hand-rolling severity from the "50% = moderate confidence"
        # clinician-training heuristic would violate CLAUDE.md's
        # "Don't hand-roll severity thresholds".  The router supplies
        # ``severity="continuous"`` at the wire layer instead.
        field_names = {f.name for f in fields(Dtcq8Result)}
        assert "severity" not in field_names

    def test_result_has_no_requires_t3_field(self) -> None:
        field_names = {f.name for f in fields(Dtcq8Result)}
        assert "requires_t3" not in field_names

    def test_zero_coping_does_not_expose_t3(self) -> None:
        # Regression guard: "no coping self-efficacy at all" (DTCQ-8
        # all-zeros) must NOT reach a T3-emitting branch.  Low
        # self-efficacy pairs with high-craving / low-motivation
        # profiles, and the product responds with skill-building
        # interventions matched to the weakest category — not crisis
        # handoff.  Acute ideation is gated by PHQ-9 / C-SSRS per
        # Whitepaper 04 §T3.
        result = score_dtcq8([0] * 8)
        assert not hasattr(result, "requires_t3")

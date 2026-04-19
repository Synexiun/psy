"""Unit tests for the PACS (Penn Alcohol Craving Scale) scorer.

Covers:
- Module constants pin to Flannery 1999 (5 items, 0-6 Likert, 0-30 total).
- Total correctness on identity edges (all-zero, all-max, mixed).
- Item-count and item-range validation.
- Bool rejection uniform with the rest of the psychometric package.
- Result-shape invariants (frozen dataclass, items tuple, no severity
  or requires_t3 fields — PACS is a continuous-severity instrument).
- Clinical vignettes covering the craving phenomenology Flannery 1999
  validates (frequency / intensity / duration / resistance / overall).
- No-safety-routing invariant — craving is a pre-behavior signal the
  platform intervenes on in the 60-180s urge-to-action window; it is
  not a T3 crisis marker.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError, fields

import pytest

from discipline.psychometric.scoring.pacs import (
    INSTRUMENT_VERSION,
    ITEM_COUNT,
    ITEM_MAX,
    ITEM_MIN,
    InvalidResponseError,
    PacsResult,
    score_pacs,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
class TestConstants:
    """The Flannery 1999 numerics are clinical facts, not tunables — pin them
    as constants so an accidental edit fails a test with an obvious diff."""

    def test_instrument_version_is_pinned(self) -> None:
        assert INSTRUMENT_VERSION == "pacs-1.0.0"

    def test_item_count_is_five(self) -> None:
        assert ITEM_COUNT == 5

    def test_item_min_is_zero(self) -> None:
        assert ITEM_MIN == 0

    def test_item_max_is_six(self) -> None:
        # PACS uses 0-6 Likert — wider than PHQ-9 (0-3), GAD-7 / ISI
        # (0-4), and PHQ-15 (0-2).  The regression this guards is
        # copy-pasting a narrower validator into the scorer.
        assert ITEM_MAX == 6


# ---------------------------------------------------------------------------
# Total correctness
# ---------------------------------------------------------------------------
class TestTotalCorrectness:
    """Flannery 1999 straight-sum scoring — no reverse coding, no subscale
    partitioning."""

    def test_all_zero_items_total_zero(self) -> None:
        result = score_pacs([0, 0, 0, 0, 0])
        assert result.total == 0

    def test_all_max_items_total_thirty(self) -> None:
        # 5 × 6 = 30 — the Flannery 1999 ceiling.
        result = score_pacs([6, 6, 6, 6, 6])
        assert result.total == 30

    def test_mixed_items_straight_sum(self) -> None:
        # 1 + 3 + 5 + 2 + 4 = 15 — a mid-range profile.
        result = score_pacs([1, 3, 5, 2, 4])
        assert result.total == 15


# ---------------------------------------------------------------------------
# Item-count validation
# ---------------------------------------------------------------------------
class TestItemCountValidation:
    """Off-by-one items are the most common wire-format bug; test both
    directions."""

    def test_four_items_raises(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 5 items"):
            score_pacs([0, 0, 0, 0])

    def test_six_items_raises(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 5 items"):
            score_pacs([0, 0, 0, 0, 0, 0])

    def test_empty_list_raises(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 5 items"):
            score_pacs([])


# ---------------------------------------------------------------------------
# Item-range validation
# ---------------------------------------------------------------------------
class TestItemRangeValidation:
    """0-6 Likert bounds.  The max-side test (7) is the regression guard
    against copy-pasting a 0-5 validator from an older instrument."""

    def test_negative_item_raises(self) -> None:
        with pytest.raises(InvalidResponseError, match="out of range"):
            score_pacs([-1, 0, 0, 0, 0])

    def test_item_seven_raises(self) -> None:
        # 7 is the off-by-one above the Flannery 1999 ceiling — the
        # classic "they used 1-7 in the UI" bug.
        with pytest.raises(InvalidResponseError, match="out of range"):
            score_pacs([7, 0, 0, 0, 0])

    def test_item_one_hundred_raises(self) -> None:
        with pytest.raises(InvalidResponseError, match="out of range"):
            score_pacs([0, 0, 100, 0, 0])

    def test_item_value_six_is_accepted(self) -> None:
        # 6 is the published max — must not be rejected.
        result = score_pacs([6, 0, 0, 0, 0])
        assert result.total == 6

    def test_item_value_zero_is_accepted(self) -> None:
        result = score_pacs([0, 0, 0, 0, 0])
        assert result.total == 0

    def test_error_message_names_the_item_index(self) -> None:
        # 1-indexed for clinician readability — item 3 (duration).
        with pytest.raises(InvalidResponseError, match="item 3"):
            score_pacs([0, 0, 7, 0, 0])


# ---------------------------------------------------------------------------
# Bool rejection
# ---------------------------------------------------------------------------
class TestBoolRejection:
    """Shared posture across the package — True/False must not silently
    coerce to 1/0 on a Likert instrument.  Uniform with phq15.py, ocir.py,
    pcl5.py, isi.py, pcptsd5.py, mdq.py."""

    def test_true_raises(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_pacs([True, 0, 0, 0, 0])  # type: ignore[list-item]

    def test_false_raises(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_pacs([0, False, 0, 0, 0])  # type: ignore[list-item]


# ---------------------------------------------------------------------------
# Result shape
# ---------------------------------------------------------------------------
class TestResultShape:
    """Invariants that downstream storage + FHIR export rely on."""

    def test_result_is_frozen(self) -> None:
        result = score_pacs([1, 2, 3, 4, 5])
        with pytest.raises(FrozenInstanceError):
            result.total = 99  # type: ignore[misc]

    def test_items_is_tuple(self) -> None:
        # Tuple, not list — hashability + caller can't mutate the
        # audit record after the fact.
        result = score_pacs([0, 1, 2, 3, 4])
        assert isinstance(result.items, tuple)
        assert result.items == (0, 1, 2, 3, 4)

    def test_instrument_version_is_default(self) -> None:
        result = score_pacs([0, 0, 0, 0, 0])
        assert result.instrument_version == INSTRUMENT_VERSION

    def test_result_has_no_severity_field(self) -> None:
        # Deliberate absence — Flannery 1999 publishes no bands.
        # Hand-rolling a "severity" on the scorer would violate
        # CLAUDE.md's "Don't hand-roll severity thresholds".  The router
        # supplies ``severity="continuous"`` at the wire layer instead.
        field_names = {f.name for f in fields(PacsResult)}
        assert "severity" not in field_names


# ---------------------------------------------------------------------------
# Clinical vignettes
# ---------------------------------------------------------------------------
class TestClinicalVignettes:
    """Phenomenological profiles Flannery 1999 validates."""

    def test_cue_free_week_is_low_total(self) -> None:
        # Post-detox, in-program, no triggers — low scores across
        # frequency, intensity, duration.  Total 3 is the kind of
        # week the product wants to amplify.
        result = score_pacs([1, 1, 1, 0, 0])
        assert result.total == 3

    def test_high_craving_week_is_high_total(self) -> None:
        # Trigger-rich week: thoughts often (5), strong urges (5),
        # much time spent (4), high difficulty resisting (5), overall
        # high craving (5).  Total 24 — the signal the urge-to-action
        # intervention window targets.
        result = score_pacs([5, 5, 4, 5, 5])
        assert result.total == 24

    def test_resistance_dominant_profile(self) -> None:
        # Low frequency / intensity but high resistance difficulty —
        # the "I only thought about it once but I almost acted on it"
        # pattern.  The continuous-severity envelope preserves this
        # signal where a banded classifier would flatten it.
        result = score_pacs([1, 2, 1, 6, 2])
        assert result.total == 12

    def test_ceiling_profile(self) -> None:
        # All six on every item — acute craving crisis.  Still produces
        # a valid result (no T3 fire — PACS does not fire T3); the
        # *trajectory* consumer is responsible for escalation gating.
        result = score_pacs([6, 6, 6, 6, 6])
        assert result.total == 30


# ---------------------------------------------------------------------------
# Safety-routing absence
# ---------------------------------------------------------------------------
class TestNoSafetyRouting:
    """PACS carries no suicidality or acute-harm item — the result must
    expose no T3 surface, and a ceiling score must not fire T3 via any
    indirect path."""

    def test_result_has_no_requires_t3_field(self) -> None:
        field_names = {f.name for f in fields(PacsResult)}
        assert "requires_t3" not in field_names

    def test_ceiling_profile_does_not_expose_t3(self) -> None:
        # Regression guard: a maximum-craving week must not reach a
        # T3-emitting branch.  T3 is reserved for active suicidality
        # per Whitepaper 04 §T3.
        result = score_pacs([6, 6, 6, 6, 6])
        assert not hasattr(result, "requires_t3")

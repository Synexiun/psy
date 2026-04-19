"""Unit tests for the Craving VAS (Visual Analog Scale) scorer.

Covers:
- Module constants pin the Sayette 2000 VAS shape (1 item, 0-100, continuous).
- Total correctness on identity edges (0, 100, midrange).
- Item-count validation (exactly 1 item — both zero and >1 fail).
- Item-range validation on the full 0-100 pseudo-continuous range.
- Bool rejection uniform with the rest of the psychometric package.
- Result-shape invariants (frozen dataclass, items tuple, no severity
  or requires_t3 fields — VAS is a continuous-severity instrument).
- Clinical vignettes spanning the EMA use case the urge-to-action
  intervention layer targets.
- No-safety-routing invariant — peak craving (VAS = 100) must not
  expose any T3 surface; acute suicidality is gated by PHQ-9 / C-SSRS.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError, fields

import pytest

from discipline.psychometric.scoring.craving_vas import (
    INSTRUMENT_VERSION,
    ITEM_COUNT,
    ITEM_MAX,
    ITEM_MIN,
    CravingVasResult,
    InvalidResponseError,
    score_craving_vas,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
class TestConstants:
    """The Sayette 2000 VAS shape is clinical fact, not tunable — pin every
    value so an accidental edit fails a test with an obvious diff."""

    def test_instrument_version_is_pinned(self) -> None:
        assert INSTRUMENT_VERSION == "craving_vas-1.0.0"

    def test_item_count_is_one(self) -> None:
        # Single-item EMA instrument — the defining shape.  If this
        # regresses to 2+, callers submitting a legitimate 1-element
        # VAS payload will be rejected.
        assert ITEM_COUNT == 1

    def test_item_min_is_zero(self) -> None:
        assert ITEM_MIN == 0

    def test_item_max_is_one_hundred(self) -> None:
        # VAS uses a 0-100 integer range — NOT a Likert anchor.  Every
        # other instrument in the package has a small anchor set (0-3,
        # 0-4, 0-6, 1-4, 0-2).  The regression this guards is a
        # validator pattern copy-pasted from a Likert scorer that caps
        # at a lower anchor.
        assert ITEM_MAX == 100


# ---------------------------------------------------------------------------
# Total correctness
# ---------------------------------------------------------------------------
class TestTotalCorrectness:
    """Straight pass-through — ``total == items[0]``.  No math to validate
    for the scoring rule itself, but the invariant needs its own tests so
    a future refactor (e.g. averaging, rescaling) that breaks the
    pass-through surfaces immediately."""

    def test_zero_item_total_is_zero(self) -> None:
        result = score_craving_vas([0])
        assert result.total == 0

    def test_max_item_total_is_one_hundred(self) -> None:
        result = score_craving_vas([100])
        assert result.total == 100

    def test_midrange_item_total(self) -> None:
        # 50 — mid-session craving, intervention-window-typical.
        result = score_craving_vas([50])
        assert result.total == 50


# ---------------------------------------------------------------------------
# Item-count validation
# ---------------------------------------------------------------------------
class TestItemCountValidation:
    """VAS is single-item by design.  Both zero and >1 must raise with
    an error message that identifies the expected count."""

    def test_empty_list_raises(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 1 item"):
            score_craving_vas([])

    def test_two_items_raises(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 1 item"):
            score_craving_vas([50, 50])

    def test_five_items_raises(self) -> None:
        # 5 items is the PACS shape — the VAS scorer must not silently
        # accept a misrouted PACS payload.
        with pytest.raises(InvalidResponseError, match="exactly 1 item"):
            score_craving_vas([1, 2, 3, 4, 5])


# ---------------------------------------------------------------------------
# Item-range validation
# ---------------------------------------------------------------------------
class TestItemRangeValidation:
    """0-100 bounds.  The off-by-one tests (101) guard the most likely
    regression — a validator copy-pasted from a 0-99 scale or a 1-100
    scale."""

    def test_negative_item_raises(self) -> None:
        with pytest.raises(InvalidResponseError, match="out of range"):
            score_craving_vas([-1])

    def test_one_hundred_one_raises(self) -> None:
        # 101 is the classic off-by-one above the VAS ceiling.
        with pytest.raises(InvalidResponseError, match="out of range"):
            score_craving_vas([101])

    def test_one_thousand_raises(self) -> None:
        # Far-over: guards against a completely unbounded validator.
        with pytest.raises(InvalidResponseError, match="out of range"):
            score_craving_vas([1000])

    def test_zero_boundary_accepted(self) -> None:
        result = score_craving_vas([0])
        assert result.total == 0

    def test_one_hundred_boundary_accepted(self) -> None:
        # 100 is the published max — must not be rejected.  The clinical
        # significance of "peak craving I have ever felt" is preserved
        # only if the ceiling is inclusive.
        result = score_craving_vas([100])
        assert result.total == 100

    def test_error_message_names_the_item_index(self) -> None:
        # 1-indexed for clinician readability.  Only one item exists,
        # so the index is always 1.
        with pytest.raises(InvalidResponseError, match="item 1"):
            score_craving_vas([101])


# ---------------------------------------------------------------------------
# Bool rejection
# ---------------------------------------------------------------------------
class TestBoolRejection:
    """Shared posture across the package — True/False must not silently
    coerce to 1/0.  Especially important on a 0-100 VAS where a coerced
    ``True`` would report a craving of 1 (effectively "none") and a
    coerced ``False`` would look identical to a legitimate 0."""

    def test_true_raises(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_craving_vas([True])  # type: ignore[list-item]

    def test_false_raises(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_craving_vas([False])  # type: ignore[list-item]


# ---------------------------------------------------------------------------
# Result shape
# ---------------------------------------------------------------------------
class TestResultShape:
    """Invariants downstream storage + FHIR export rely on."""

    def test_result_is_frozen(self) -> None:
        result = score_craving_vas([50])
        with pytest.raises(FrozenInstanceError):
            result.total = 99  # type: ignore[misc]

    def test_items_is_tuple(self) -> None:
        # Tuple, not list — hashability + caller can't mutate the
        # audit record after the fact.
        result = score_craving_vas([42])
        assert isinstance(result.items, tuple)
        assert result.items == (42,)

    def test_instrument_version_is_default(self) -> None:
        result = score_craving_vas([0])
        assert result.instrument_version == INSTRUMENT_VERSION


# ---------------------------------------------------------------------------
# Clinical vignettes
# ---------------------------------------------------------------------------
class TestClinicalVignettes:
    """Phenomenological profiles the EMA layer routinely observes — a
    ground-truth sanity check that the scorer preserves the raw signal
    without any transformation."""

    def test_post_detox_in_program_no_trigger(self) -> None:
        # Early morning, safe environment, no cues.  VAS = 5 — the kind
        # of baseline the intervention layer wants to hold.
        result = score_craving_vas([5])
        assert result.total == 5

    def test_trigger_peak_at_cue_exposure(self) -> None:
        # User encountered a strong cue (a bar, an ex, a payday).  VAS
        # = 85 — the urge-to-action window the intervention is about
        # to fire into.
        result = score_craving_vas([85])
        assert result.total == 85

    def test_post_intervention_reduction(self) -> None:
        # Post-intervention re-prompt: the within-episode Δ is pre 85
        # → post 40 = a 45-point drop.  This test pins only the post
        # value; the pre/post Δ is computed at the bandit layer.
        result = score_craving_vas([40])
        assert result.total == 40

    def test_ceiling_peak_craving(self) -> None:
        # "The strongest craving I have ever felt."  VAS = 100 is a
        # valid score (not an error), and must not fire T3 via any
        # indirect path — see TestNoSafetyRouting below.
        result = score_craving_vas([100])
        assert result.total == 100


# ---------------------------------------------------------------------------
# Safety-routing absence
# ---------------------------------------------------------------------------
class TestNoSafetyRouting:
    """Craving VAS carries no suicidality or acute-harm item — the result
    must expose no T3 surface, and a ceiling score must not fire T3 via
    any indirect path."""

    def test_result_has_no_severity_field(self) -> None:
        # Deliberate absence — Sayette 2000 publishes no VAS bands.
        # Hand-rolling severity would violate CLAUDE.md's
        # "Don't hand-roll severity thresholds".  The router supplies
        # ``severity="continuous"`` at the wire layer instead.
        field_names = {f.name for f in fields(CravingVasResult)}
        assert "severity" not in field_names

    def test_result_has_no_requires_t3_field(self) -> None:
        field_names = {f.name for f in fields(CravingVasResult)}
        assert "requires_t3" not in field_names

    def test_ceiling_profile_does_not_expose_t3(self) -> None:
        # Regression guard: "strongest craving I have ever felt" must
        # not reach a T3-emitting branch.  T3 is reserved for active
        # suicidality per Whitepaper 04 §T3; acute ideation goes
        # through PHQ-9 / C-SSRS, not VAS.
        result = score_craving_vas([100])
        assert not hasattr(result, "requires_t3")

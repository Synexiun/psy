"""Unit tests for the Readiness Ruler scorer.

Covers:
- Module constants pin the Rollnick 1999 / Heather 2008 shape
  (1 item, 0-10 integer, continuous).
- Total correctness on identity edges (0, 10, midrange).
- Item-count validation (exactly 1 item — both zero and >1 fail).
- Item-range validation on the 0-10 range with off-by-one guards.
- Bool rejection uniform with the rest of the psychometric package.
- Result-shape invariants (frozen dataclass, items tuple, no severity
  or requires_t3 fields — Ruler is a continuous-severity instrument
  with higher-is-better direction semantics).
- Clinical vignettes across the MI stages-of-change pedagogical
  anchors (pre-contemplation / contemplation / action).
- No-safety-routing invariant — a Ruler score of 0 ("not ready at
  all") must not expose any T3 surface; low motivation is an MI
  intervention signal, not a crisis signal.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError, fields

import pytest

from discipline.psychometric.scoring.readiness_ruler import (
    INSTRUMENT_VERSION,
    ITEM_COUNT,
    ITEM_MAX,
    ITEM_MIN,
    InvalidResponseError,
    ReadinessRulerResult,
    score_readiness_ruler,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
class TestConstants:
    """The Heather 2008 validation pinned the 0-10 range against longer
    instruments.  Rescaling to 0-5 or 0-100 would invalidate the
    correlations, so the constants are clinical facts — not tunables."""

    def test_instrument_version_is_pinned(self) -> None:
        assert INSTRUMENT_VERSION == "readiness_ruler-1.0.0"

    def test_item_count_is_one(self) -> None:
        # Single-item MI instrument — the defining shape.  Matches the
        # Craving VAS shape introduced in Sprint 36.
        assert ITEM_COUNT == 1

    def test_item_min_is_zero(self) -> None:
        assert ITEM_MIN == 0

    def test_item_max_is_ten(self) -> None:
        # 0-10 is the Heather 2008 form.  The regression this guards is
        # copy-pasting the Craving VAS validator (0-100) or a 0-point
        # Likert (0-4).  Either would silently misreport the ready
        # state when Heather 2008 cutoffs were compared.
        assert ITEM_MAX == 10


# ---------------------------------------------------------------------------
# Total correctness
# ---------------------------------------------------------------------------
class TestTotalCorrectness:
    """Straight pass-through — ``total == items[0]``.  No math to
    validate for the rule itself, but the invariant needs explicit
    tests so a future refactor (e.g. percentile conversion, midpoint-
    shifted scaling) that breaks the pass-through surfaces
    immediately."""

    def test_zero_item_total_is_zero(self) -> None:
        # Not ready at all — pre-contemplation stage per the MI
        # pedagogical anchors (not a clinically-validated cutoff).
        result = score_readiness_ruler([0])
        assert result.total == 0

    def test_max_item_total_is_ten(self) -> None:
        # Completely ready — deep action/maintenance stage.
        result = score_readiness_ruler([10])
        assert result.total == 10

    def test_midrange_item_total(self) -> None:
        # 5 — contemplation / preparation midpoint; the most common
        # response in routine brief-intervention settings.
        result = score_readiness_ruler([5])
        assert result.total == 5


# ---------------------------------------------------------------------------
# Item-count validation
# ---------------------------------------------------------------------------
class TestItemCountValidation:
    """Ruler is single-item by design.  Both zero and >1 must raise
    with an error message that identifies the expected count."""

    def test_empty_list_raises(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 1 item"):
            score_readiness_ruler([])

    def test_two_items_raises(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 1 item"):
            score_readiness_ruler([5, 5])

    def test_sixteen_items_raises(self) -> None:
        # 16 items is the URICA short-form shape — the Ruler scorer
        # must not silently accept a misrouted URICA payload when
        # URICA ships.
        with pytest.raises(InvalidResponseError, match="exactly 1 item"):
            score_readiness_ruler([2] * 16)


# ---------------------------------------------------------------------------
# Item-range validation
# ---------------------------------------------------------------------------
class TestItemRangeValidation:
    """0-10 bounds.  The off-by-one tests (11) guard the most likely
    regression — a validator copy-pasted from a 0-100 scale (VAS) or
    a 1-10 scale."""

    def test_negative_item_raises(self) -> None:
        with pytest.raises(InvalidResponseError, match="out of range"):
            score_readiness_ruler([-1])

    def test_eleven_raises(self) -> None:
        # 11 is the classic off-by-one above the Heather 2008 ceiling.
        with pytest.raises(InvalidResponseError, match="out of range"):
            score_readiness_ruler([11])

    def test_one_hundred_raises(self) -> None:
        # Guards against a validator inherited from Craving VAS
        # (0-100) — a caller switching from VAS to Ruler but
        # forgetting to rescale would submit 100 and expect success.
        with pytest.raises(InvalidResponseError, match="out of range"):
            score_readiness_ruler([100])

    def test_zero_boundary_accepted(self) -> None:
        result = score_readiness_ruler([0])
        assert result.total == 0

    def test_ten_boundary_accepted(self) -> None:
        # 10 is the published ceiling — must not be rejected.  The
        # clinical significance of "completely ready" is preserved
        # only if the ceiling is inclusive.
        result = score_readiness_ruler([10])
        assert result.total == 10

    def test_error_message_names_the_item_index(self) -> None:
        # 1-indexed for clinician readability.  Only one item exists.
        with pytest.raises(InvalidResponseError, match="item 1"):
            score_readiness_ruler([11])


# ---------------------------------------------------------------------------
# Bool rejection
# ---------------------------------------------------------------------------
class TestBoolRejection:
    """Shared posture across the package — True/False must not silently
    coerce to 1/0.  Especially important on a 0-10 Ruler where a
    coerced ``True`` would report readiness of 1 ("barely ready") —
    the pre-contemplation stage — and a coerced ``False`` would look
    identical to a legitimate 0."""

    def test_true_raises(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_readiness_ruler([True])  # type: ignore[list-item]

    def test_false_raises(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_readiness_ruler([False])  # type: ignore[list-item]


# ---------------------------------------------------------------------------
# Result shape
# ---------------------------------------------------------------------------
class TestResultShape:
    """Invariants downstream storage + FHIR export rely on."""

    def test_result_is_frozen(self) -> None:
        result = score_readiness_ruler([5])
        with pytest.raises(FrozenInstanceError):
            result.total = 99  # type: ignore[misc]

    def test_items_is_tuple(self) -> None:
        # Tuple, not list — hashability + caller can't mutate the
        # audit record after the fact.
        result = score_readiness_ruler([7])
        assert isinstance(result.items, tuple)
        assert result.items == (7,)

    def test_instrument_version_is_default(self) -> None:
        result = score_readiness_ruler([0])
        assert result.instrument_version == INSTRUMENT_VERSION


# ---------------------------------------------------------------------------
# Clinical vignettes
# ---------------------------------------------------------------------------
class TestClinicalVignettes:
    """Phenomenological profiles mapping to the MI stages-of-change
    pedagogical anchors.  These are descriptive landmarks — NOT
    clinically-validated cutoffs — but they shape how the
    intervention layer picks tools at the motivation × craving
    decision surface."""

    def test_precontemplation_stance(self) -> None:
        # "I don't see why I should change."  Ruler 1 — MI script is
        # decisional-balance elicitation, NOT action planning.
        result = score_readiness_ruler([1])
        assert result.total == 1

    def test_contemplation_stance(self) -> None:
        # "I'm thinking about it."  Ruler 5 — MI script is
        # change-talk amplification.
        result = score_readiness_ruler([5])
        assert result.total == 5

    def test_action_stance(self) -> None:
        # "I'm ready — I just need help making the plan stick."  Ruler
        # 9 — MI script is implementation intentions.
        result = score_readiness_ruler([9])
        assert result.total == 9

    def test_ceiling_maintenance_stance(self) -> None:
        # "Fully committed, I know what I'm doing."  Ruler 10 — the
        # maintenance stage.  Must not fire T3 via any indirect path.
        result = score_readiness_ruler([10])
        assert result.total == 10


# ---------------------------------------------------------------------------
# Safety-routing absence
# ---------------------------------------------------------------------------
class TestNoSafetyRouting:
    """Readiness Ruler carries no suicidality or acute-harm item — the
    result must expose no T3 surface.  A score of 0 ("not ready at
    all") is a motivation signal routing to MI-scripted interventions,
    not a crisis signal."""

    def test_result_has_no_severity_field(self) -> None:
        # Deliberate absence — Heather 2008 publishes no bands.
        # The MI stages-of-change anchors are pedagogical, not
        # clinically-validated cutoffs; hand-rolling bands from
        # them would violate CLAUDE.md's "Don't hand-roll severity
        # thresholds".  The router supplies
        # ``severity="continuous"`` at the wire layer instead.
        field_names = {f.name for f in fields(ReadinessRulerResult)}
        assert "severity" not in field_names

    def test_result_has_no_requires_t3_field(self) -> None:
        field_names = {f.name for f in fields(ReadinessRulerResult)}
        assert "requires_t3" not in field_names

    def test_zero_ready_does_not_expose_t3(self) -> None:
        # Regression guard: "not ready at all" (Ruler 0) must NOT
        # reach a T3-emitting branch.  Low motivation pairs with
        # low-agency mood profiles, and the product responds with
        # MI-scripted interventions rather than crisis handoff.
        # Acute ideation is gated by PHQ-9 / C-SSRS per Whitepaper
        # 04 §T3.
        result = score_readiness_ruler([0])
        assert not hasattr(result, "requires_t3")

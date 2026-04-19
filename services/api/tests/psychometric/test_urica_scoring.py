"""Unit tests for the URICA short (16-item University of Rhode Island
Change Assessment) scorer.

Covers:
- Module constants pin the DiClemente & Hughes 1990 16-item shape
  (16 items, 1-5 Likert, 4 subscales of 4 items).
- Subscale slot constants pin the positional stage-attribution
  mapping — a reorder regression would silently swap stage labels.
- SUBSCALE_LABELS tuple pins the public stage-label order.
- Each subscale sum correct on identity edges (uniform-low per
  subscale, uniform-high per subscale).
- Readiness composite correct across stage-profile vignettes —
  pure-PC, pure-action, balanced, and the zero-crossing case.
- Signed-total contract — URICA is the first instrument in the
  package whose ``total`` can be negative; pin the negative-
  Readiness case explicitly.
- Item-count validation (16 exactly; 32 — the original URICA long
  form — must fail).
- Item-range validation on the 1-5 range (NOT 0-4!) with off-by-one
  guards at both ends (0 and 6).
- Bool rejection uniform with the rest of the psychometric package.
- Result-shape invariants (frozen dataclass, items tuple, all four
  subscale fields present, no severity / requires_t3 fields).
- Clinical vignettes per stage — pure precontemplator, pure
  contemplator, deep-action, maintenance-with-relapse-warning.
- No-safety-routing invariant — negative Readiness (pre-
  contemplation-dominant) must not expose any T3 surface; low
  readiness is an MI signal, not a crisis signal.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError, fields

import pytest

from discipline.psychometric.scoring.urica import (
    INSTRUMENT_VERSION,
    ITEM_COUNT,
    ITEM_MAX,
    ITEM_MIN,
    SUBSCALE_ACTION_SLOTS,
    SUBSCALE_CONTEMPLATION_SLOTS,
    SUBSCALE_LABELS,
    SUBSCALE_MAINTENANCE_SLOTS,
    SUBSCALE_PRECONTEMPLATION_SLOTS,
    SUBSCALE_SIZE,
    InvalidResponseError,
    UricaResult,
    score_urica,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
class TestConstants:
    """The DiClemente & Hughes 1990 16-item short-form shape is
    clinical fact, not tunable.  Pin every value."""

    def test_instrument_version_is_pinned(self) -> None:
        assert INSTRUMENT_VERSION == "urica-1.0.0"

    def test_item_count_is_sixteen(self) -> None:
        # 16 items — 4 per subscale × 4 subscales.  The defining shape
        # distinguishing the short form from the 32-item original.
        assert ITEM_COUNT == 16

    def test_item_min_is_one(self) -> None:
        # URICA is 1-5 Likert (strongly disagree → strongly agree), NOT
        # 0-based.  Second 1-based instrument after BIS-11.  Regression
        # this guards: a validator copy-pasted from a 0-based Likert
        # scorer (PHQ-9 / GAD-7 / PSS-10) that silently treats 0 as
        # valid and misreports every subscale at the same rate.
        assert ITEM_MIN == 1

    def test_item_max_is_five(self) -> None:
        assert ITEM_MAX == 5

    def test_subscale_size_is_four(self) -> None:
        # 4 items per subscale is the short-form contract.  A regression
        # that shifted subscale sizing would silently break the
        # Readiness composite arithmetic.
        assert SUBSCALE_SIZE == 4


# ---------------------------------------------------------------------------
# Subscale slot constants
# ---------------------------------------------------------------------------
class TestSubscaleSlots:
    """Positional stage-attribution constants.  A reorder here is
    clinically equivalent to swapping the stage labels of the user's
    responses — the intervention layer reading the per-subscale
    profile would then route every response to the wrong stage
    script."""

    def test_slots_are_tuples(self) -> None:
        # Tuples (not range / list) — immutable at import time so
        # downstream code cannot mutate the stage attribution.
        assert isinstance(SUBSCALE_PRECONTEMPLATION_SLOTS, tuple)
        assert isinstance(SUBSCALE_CONTEMPLATION_SLOTS, tuple)
        assert isinstance(SUBSCALE_ACTION_SLOTS, tuple)
        assert isinstance(SUBSCALE_MAINTENANCE_SLOTS, tuple)

    def test_precontemplation_slots_are_zero_to_three(self) -> None:
        # Items 1-4 (0-indexed 0-3) per DiClemente & Hughes 1990
        # administration order.
        assert SUBSCALE_PRECONTEMPLATION_SLOTS == (0, 1, 2, 3)

    def test_contemplation_slots_are_four_to_seven(self) -> None:
        assert SUBSCALE_CONTEMPLATION_SLOTS == (4, 5, 6, 7)

    def test_action_slots_are_eight_to_eleven(self) -> None:
        assert SUBSCALE_ACTION_SLOTS == (8, 9, 10, 11)

    def test_maintenance_slots_are_twelve_to_fifteen(self) -> None:
        assert SUBSCALE_MAINTENANCE_SLOTS == (12, 13, 14, 15)

    def test_slots_partition_full_item_range(self) -> None:
        # Union of all four subscales must cover every item index
        # exactly once — no gaps, no overlaps.  A regression that
        # reused a slot or skipped one would silently drop (or
        # double-count) a subscale contribution to Readiness.
        all_slots = (
            SUBSCALE_PRECONTEMPLATION_SLOTS
            + SUBSCALE_CONTEMPLATION_SLOTS
            + SUBSCALE_ACTION_SLOTS
            + SUBSCALE_MAINTENANCE_SLOTS
        )
        assert sorted(all_slots) == list(range(ITEM_COUNT))


class TestSubscaleLabels:
    """Public label tuple — matches DTCQ-8's SITUATION_LABELS pattern.
    The FHIR exporter and intervention layer read subscale names
    through this constant; a reorder or typo here would silently
    misattribute every exported stage score."""

    def test_labels_is_tuple(self) -> None:
        assert isinstance(SUBSCALE_LABELS, tuple)

    def test_labels_pinned(self) -> None:
        # Order matches the administration order — Precontemplation
        # first, Maintenance last, per DiClemente & Hughes 1990.
        assert SUBSCALE_LABELS == (
            "precontemplation",
            "contemplation",
            "action",
            "maintenance",
        )

    def test_labels_match_dataclass_fields(self) -> None:
        # Every label must correspond to a dataclass field on
        # UricaResult — a divergence would mean the FHIR exporter
        # can't find a subscale score by its label.
        field_names = {f.name for f in fields(UricaResult)}
        for label in SUBSCALE_LABELS:
            assert label in field_names, f"missing field for {label}"


# ---------------------------------------------------------------------------
# Subscale correctness
# ---------------------------------------------------------------------------
class TestSubscaleCorrectness:
    """Per-subscale arithmetic — straight sum of the 4 Likert responses
    in each subscale's positional slots."""

    def test_uniform_one_gives_minimum_subscales(self) -> None:
        # All items at Likert 1 → each subscale = 4 (floor).
        result = score_urica([1] * 16)
        assert result.precontemplation == 4
        assert result.contemplation == 4
        assert result.action == 4
        assert result.maintenance == 4

    def test_uniform_five_gives_maximum_subscales(self) -> None:
        # All items at Likert 5 → each subscale = 20 (ceiling).
        result = score_urica([5] * 16)
        assert result.precontemplation == 20
        assert result.contemplation == 20
        assert result.action == 20
        assert result.maintenance == 20

    def test_precontemplation_only_elevated(self) -> None:
        # Items 1-4 at 5, rest at 1 → PC = 20, others = 4.  Pure
        # precontemplator profile.
        result = score_urica([5, 5, 5, 5] + [1] * 12)
        assert result.precontemplation == 20
        assert result.contemplation == 4
        assert result.action == 4
        assert result.maintenance == 4

    def test_action_only_elevated(self) -> None:
        # Items 9-12 at 5, rest at 1 → Action = 20, others = 4.  Deep
        # action-stage profile.
        result = score_urica([1] * 8 + [5, 5, 5, 5] + [1] * 4)
        assert result.precontemplation == 4
        assert result.contemplation == 4
        assert result.action == 20
        assert result.maintenance == 4


# ---------------------------------------------------------------------------
# Readiness composite correctness
# ---------------------------------------------------------------------------
class TestReadinessComposite:
    """Readiness = C + A + M − PC per DiClemente & Hughes 1990 /
    Project MATCH 1997.  These tests pin the signed-int arithmetic
    on identity edges AND on the zero-crossing case — URICA is the
    package's first signed-total instrument, so the signed
    arithmetic has its own test surface."""

    def test_uniform_one_gives_minimum_positive_readiness(self) -> None:
        # All items at 1 → PC = C = A = M = 4.
        # Readiness = 4 + 4 + 4 - 4 = +8.  NOT the minimum — the
        # minimum requires PC peaked while others floored.
        result = score_urica([1] * 16)
        assert result.total == 8

    def test_uniform_five_gives_maximum_positive_readiness(self) -> None:
        # All items at 5 → PC = C = A = M = 20.
        # Readiness = 20 + 20 + 20 - 20 = +40.  NOT +56 — the
        # maximum requires others peaked while PC floored.
        result = score_urica([5] * 16)
        assert result.total == 40

    def test_pure_precontemplation_gives_minimum_readiness(self) -> None:
        # PC peaked (20), others floored (4).
        # Readiness = 4 + 4 + 4 - 20 = -8.  The signed-minimum
        # "rock-bottom precontemplation" profile.  URICA's first
        # clinically-interpretable negative total — a regression
        # that clamped totals to 0+ would silently lose this signal.
        items = [5, 5, 5, 5] + [1] * 12
        result = score_urica(items)
        assert result.total == -8

    def test_pure_action_maintenance_gives_maximum_readiness(self) -> None:
        # Others peaked (20 each), PC floored (4).
        # Readiness = 20 + 20 + 20 - 4 = +56.  The signed-maximum
        # "deep action / maintenance, minimal precontemplation"
        # profile — the therapeutic-progress ceiling.
        items = [1, 1, 1, 1] + [5] * 12
        result = score_urica(items)
        assert result.total == 56

    def test_balanced_profile_gives_positive_readiness(self) -> None:
        # PC = C = A = M = 12 (all items at 3, the Likert midpoint).
        # Readiness = 12 + 12 + 12 - 12 = +24.  The "balanced but
        # non-committal" profile.
        result = score_urica([3] * 16)
        assert result.total == 24
        assert result.precontemplation == 12
        assert result.contemplation == 12
        assert result.action == 12
        assert result.maintenance == 12

    def test_zero_crossing_case(self) -> None:
        # Construct a profile that crosses zero exactly.
        # PC = 16 (4 × 4), C = A = M = 4 + 4 + ... let's pick the
        # values: PC = 4,4,4,4 (sum 16).  C = 2,2,2,2 (sum 8).
        # A = 2,2,2,2 (sum 8).  M = 2,2,2,2 (sum 8).
        # Readiness = 8 + 8 + 8 - 16 = 8.  Adjust: PC = 5,5,5,5 (20),
        # C = 3,3,3,3 (12), A = 2,2,2,2 (8), M = 5,5,5,5 (20).
        # Readiness = 12 + 8 + 20 - 20 = 20.  Reset.
        # Want Readiness == 0.  PC = C + A + M.
        # PC = 16, C = 5, A = 5, M = 6 → C+A+M = 16, Readiness = 0.
        # But each subscale must be 4-20, so min per subscale is 4.
        # So smallest C + A + M is 12 (all floor).  Then PC must be 12.
        # PC subscale sum = 12 → each PC item = 3.
        items = [3, 3, 3, 3] + [1] * 12
        result = score_urica(items)
        assert result.precontemplation == 12
        assert result.contemplation == 4
        assert result.action == 4
        assert result.maintenance == 4
        # Readiness = 4 + 4 + 4 - 12 = 0 exactly.  The zero-crossing
        # is a clinically salient transition and must be reachable
        # by a legitimate Likert profile.
        assert result.total == 0


# ---------------------------------------------------------------------------
# Item-count validation
# ---------------------------------------------------------------------------
class TestItemCountValidation:
    """URICA short is the 16-item form.  Regression guards against
    submitting the original 32-item URICA or neighbor instruments."""

    def test_empty_list_raises(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 16 items"):
            score_urica([])

    def test_fifteen_items_raises(self) -> None:
        # Off-by-one below.
        with pytest.raises(InvalidResponseError, match="exactly 16 items"):
            score_urica([3] * 15)

    def test_seventeen_items_raises(self) -> None:
        # Off-by-one above.
        with pytest.raises(InvalidResponseError, match="exactly 16 items"):
            score_urica([3] * 17)

    def test_thirty_two_items_long_form_raises(self) -> None:
        # 32 items is the original McConnaughy 1983 URICA shape.
        # The short-form dispatch must not silently accept the long
        # form — the positional slot mapping assumes 4-item subscales,
        # and 8-item long-form subscales would quietly collapse into
        # an aliased short-form profile.
        with pytest.raises(InvalidResponseError, match="exactly 16 items"):
            score_urica([3] * 32)

    def test_eight_items_raises(self) -> None:
        # 8 items is the DTCQ-8 shape — must not silently accept a
        # misrouted DTCQ-8 payload on the same Likert scale (though
        # DTCQ-8 is 0-100 not 1-5, so the range validator would
        # also catch it; the count check fires first).
        with pytest.raises(InvalidResponseError, match="exactly 16 items"):
            score_urica([3] * 8)


# ---------------------------------------------------------------------------
# Item-range validation
# ---------------------------------------------------------------------------
class TestItemRangeValidation:
    """1-5 bounds.  The critical off-by-one here is ``0`` — URICA is
    1-based (unlike every 0-based Likert instrument in the package
    except BIS-11), so a validator that silently accepts 0 would
    under-count every subscale."""

    def test_zero_raises_because_scale_is_one_based(self) -> None:
        # THE load-bearing regression test.  A copy-paste from PHQ-9
        # / GAD-7 / PSS-10 would silently accept 0 and produce
        # understated subscale sums (since 0 < 4 items can add to 0
        # in the PC subscale, turning a Readiness of +8 into +16 on
        # identical response intent).
        with pytest.raises(InvalidResponseError, match="out of range"):
            score_urica([0] * 16)

    def test_negative_raises(self) -> None:
        with pytest.raises(InvalidResponseError, match="out of range"):
            score_urica([-1] + [3] * 15)

    def test_six_raises(self) -> None:
        # Off-by-one above the 5-ceiling.  Would over-count every
        # subscale if silently accepted.
        with pytest.raises(InvalidResponseError, match="out of range"):
            score_urica([3] * 15 + [6])

    def test_one_hundred_raises(self) -> None:
        # Far-over: guards against a validator inherited from
        # Craving VAS / DTCQ-8 (0-100 scales).
        with pytest.raises(InvalidResponseError, match="out of range"):
            score_urica([3] * 15 + [100])

    def test_one_boundary_accepted(self) -> None:
        result = score_urica([1] * 16)
        assert result.precontemplation == 4

    def test_five_boundary_accepted(self) -> None:
        # 5 is the published ceiling ("Strongly Agree") — must not
        # be rejected.  Ceiling exclusion would silently clip every
        # high-endorsement profile.
        result = score_urica([5] * 16)
        assert result.precontemplation == 20

    def test_error_message_names_the_item_index(self) -> None:
        # 1-indexed for clinician readability.  Item 9 (first Action
        # item) rejected.
        items = [3] * 8 + [6] + [3] * 7
        with pytest.raises(InvalidResponseError, match="item 9"):
            score_urica(items)


# ---------------------------------------------------------------------------
# Bool rejection
# ---------------------------------------------------------------------------
class TestBoolRejection:
    """Shared posture across the package — True/False must not silently
    coerce to 1/0.  On URICA's 1-5 scale, ``True`` (coerced to 1) is
    at the scale floor and would misreport strong disagreement, while
    ``False`` (coerced to 0) would fail range validation instead of
    surfacing the wire-format error.  Catching the bool at the type
    check produces the more diagnostic message."""

    def test_true_raises(self) -> None:
        items: list[int] = [3] * 15 + [True]  # type: ignore[list-item]
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_urica(items)

    def test_false_raises(self) -> None:
        items: list[int] = [False] + [3] * 15  # type: ignore[list-item]
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_urica(items)


# ---------------------------------------------------------------------------
# Result shape
# ---------------------------------------------------------------------------
class TestResultShape:
    """Invariants downstream storage + FHIR component export + the
    intervention-layer per-subscale profile reads rely on."""

    def test_result_is_frozen(self) -> None:
        result = score_urica([3] * 16)
        with pytest.raises(FrozenInstanceError):
            result.total = 99  # type: ignore[misc]

    def test_items_is_tuple(self) -> None:
        # Tuple, not list — hashability + caller cannot mutate the
        # audit record after the fact.
        result = score_urica(list(range(1, 6)) * 3 + [1])
        assert isinstance(result.items, tuple)
        assert len(result.items) == 16

    def test_subscales_are_ints(self) -> None:
        # Not floats — URICA subscale sums are integer-native.  A
        # surprise float would pass isinstance(x, int) checks in
        # consumer code and break FHIR valueInteger components.
        result = score_urica([3] * 16)
        assert isinstance(result.precontemplation, int)
        assert isinstance(result.contemplation, int)
        assert isinstance(result.action, int)
        assert isinstance(result.maintenance, int)

    def test_total_is_int_even_when_negative(self) -> None:
        # Signed-int total — a regression that clamped to a non-
        # negative type (e.g. ``max(0, signed_readiness)``) would
        # silently zero-out every pre-contemplation-dominant profile.
        items = [5, 5, 5, 5] + [1] * 12
        result = score_urica(items)
        assert isinstance(result.total, int)
        assert result.total == -8
        assert result.total < 0

    def test_instrument_version_is_default(self) -> None:
        result = score_urica([3] * 16)
        assert result.instrument_version == INSTRUMENT_VERSION


# ---------------------------------------------------------------------------
# Clinical vignettes
# ---------------------------------------------------------------------------
class TestClinicalVignettes:
    """Stage-profile shapes the intervention layer routinely observes.
    Descriptive landmarks — NOT clinically-validated cutoffs, but the
    profile-vs-aggregate distinction is exactly the point (two profiles
    with the same Readiness can route to different interventions)."""

    def test_pure_precontemplator_profile(self) -> None:
        # "I don't have a problem, why am I even here?"  PC peaked,
        # all others floored.  Intervention script is empathic
        # reflection of ambivalence + decisional-balance elicitation
        # — NOT action planning, which would be misattuned to the
        # user's stage.
        items = [5, 5, 5, 5] + [1] * 12
        result = score_urica(items)
        assert result.precontemplation == 20
        assert result.total == -8

    def test_pure_contemplator_profile(self) -> None:
        # "I'm thinking about changing but not ready to act."  C
        # peaked, others floored.  Intervention script is change-
        # talk amplification + self-efficacy building.
        items = [1] * 4 + [5, 5, 5, 5] + [1] * 8
        result = score_urica(items)
        assert result.contemplation == 20
        assert result.total == 20 + 4 + 4 - 4  # 24

    def test_deep_action_profile(self) -> None:
        # "I'm doing the work right now."  A peaked, M high, others
        # floored.  Intervention script is implementation-
        # intentions consolidation + relapse-prevention planning.
        items = [1] * 4 + [1] * 4 + [5, 5, 5, 5] + [4, 4, 4, 4]
        result = score_urica(items)
        assert result.action == 20
        assert result.maintenance == 16
        # Readiness = 4 + 20 + 16 - 4 = 36
        assert result.total == 36

    def test_maintenance_with_relapse_warning_profile(self) -> None:
        # M high but PC creeping back — the classic relapse-warning
        # signature the trajectory layer flags.  An isolated single-
        # reading can't flag the rising-PC pattern (needs a prior
        # reading), but the profile shape is legitimate and this
        # test pins the arithmetic.  M = 20, PC = 12 (3-3-3-3), C = 8
        # (2-2-2-2), A = 8 (2-2-2-2).
        items = [3, 3, 3, 3] + [2, 2, 2, 2] + [2, 2, 2, 2] + [5, 5, 5, 5]
        result = score_urica(items)
        assert result.maintenance == 20
        assert result.precontemplation == 12
        # Readiness = 8 + 8 + 20 - 12 = 24
        assert result.total == 24


# ---------------------------------------------------------------------------
# Safety-routing absence
# ---------------------------------------------------------------------------
class TestNoSafetyRouting:
    """URICA carries no suicidality or acute-harm item — the result
    must expose no T3 surface.  Negative Readiness (pre-contemplation-
    dominant) is a motivation signal routing to MI-scripted
    interventions, not a crisis signal."""

    def test_result_has_no_severity_field(self) -> None:
        # Deliberate absence — DiClemente & Hughes 1990 publishes no
        # bands; URICA is treated cluster-analytically, not cutoff-
        # categorically.  Hand-rolling bands would violate
        # CLAUDE.md's "Don't hand-roll severity thresholds".
        field_names = {f.name for f in fields(UricaResult)}
        assert "severity" not in field_names

    def test_result_has_no_requires_t3_field(self) -> None:
        field_names = {f.name for f in fields(UricaResult)}
        assert "requires_t3" not in field_names

    def test_negative_readiness_does_not_expose_t3(self) -> None:
        # Regression guard: pure-precontemplation (most-negative
        # Readiness) must NOT reach a T3-emitting branch.  Low
        # readiness pairs with low-agency mood profiles, and the
        # product responds with MI-scripted interventions rather
        # than crisis handoff.  Acute ideation is gated by PHQ-9 /
        # C-SSRS per Whitepaper 04 §T3.
        items = [5, 5, 5, 5] + [1] * 12
        result = score_urica(items)
        assert result.total == -8
        assert not hasattr(result, "requires_t3")

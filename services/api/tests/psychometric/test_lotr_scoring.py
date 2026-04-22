"""Unit tests for LOT-R (Life Orientation Test Revised).

Pins the Scheier, Carver & Bridges (1994) scoring contract:

- 10-item 0-4 Likert payload; 6 scored items (positions 1, 3, 4, 7,
  9, 10) and 4 filler items (positions 2, 5, 6, 8).  The fillers are
  present on the patient-facing form to obscure the optimism
  construct from demand characteristics; they are validated for
  type/range but excluded from the sum.
- Reverse-keying on items 3, 7, 9 (pessimism-worded).  Scorer
  applies arithmetic-reflection flip ``4 - raw`` before summing.
- Range 0-24, higher is better (more dispositional optimism).
- No severity bands — Scheier 1994 did not publish cross-calibrated
  clinical cuts.  LOT-R ships as a continuous dimensional measure
  uniform with PACS / Craving VAS / DERS-16 / CD-RISC-10 / PSWQ.
- No T3 escalation — no safety item in the instrument.
- ``items`` field preserves all 10 raw pre-flip responses (including
  the 4 filler values) for auditability.

Novel patterns under test:
1. **Filler-item exclusion** — first instrument in the package with
   items on the form that do not contribute to the score.  The
   filler-exclusion invariant is asserted in TestFillerPositionsExcluded
   by holding scored positions constant and varying filler positions
   across the full [0, 4] range.
2. **Reverse-keying reuse** — the arithmetic-reflection idiom from
   PSWQ is reused on a different Likert envelope (0-4 here vs 1-5
   there).  The mid-line-invariance property (all-2s → 12) and
   response-set acquiescence catch (all-4s → 12 not 24) verify the
   flip fires correctly on this envelope.
"""

from __future__ import annotations

import pytest

from discipline.psychometric.scoring.lotr import (
    INSTRUMENT_VERSION,
    ITEM_COUNT,
    ITEM_MAX,
    ITEM_MIN,
    LOTR_FILLER_POSITIONS,
    LOTR_REVERSE_ITEMS,
    LOTR_SCORED_POSITIONS,
    InvalidResponseError,
    LotrResult,
    score_lotr,
)

# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------


def _build(
    scored_values: dict[int, int],
    *,
    filler_fill: int = 2,
) -> list[int]:
    """Build a 10-item payload with explicit scored positions and a
    uniform filler fill.  Non-specified scored positions default to
    the filler_fill as well (for convenience in one-off tests)."""
    out = [filler_fill] * ITEM_COUNT
    for pos, val in scored_values.items():
        out[pos - 1] = val
    return out


# ---------------------------------------------------------------------------
# TestConstants — frozen contract pins
# ---------------------------------------------------------------------------


class TestConstants:

    def test_instrument_version(self) -> None:
        assert INSTRUMENT_VERSION == "lotr-1.0.0"

    def test_item_count(self) -> None:
        assert ITEM_COUNT == 10

    def test_item_min(self) -> None:
        assert ITEM_MIN == 0

    def test_item_max(self) -> None:
        assert ITEM_MAX == 4

    def test_scored_positions_frozen(self) -> None:
        """Scheier 1994 kept items 1, 3, 4, 7, 9, 10 from the original
        LOT after refactor-analysis dropped optimism-adjacent fillers."""
        assert LOTR_SCORED_POSITIONS == (1, 3, 4, 7, 9, 10)
        assert isinstance(LOTR_SCORED_POSITIONS, tuple)

    def test_filler_positions_frozen(self) -> None:
        """Items 2, 5, 6, 8 are the 4 filler items kept on the form
        for demand-characteristic camouflage; not summed into total."""
        assert LOTR_FILLER_POSITIONS == (2, 5, 6, 8)
        assert isinstance(LOTR_FILLER_POSITIONS, tuple)

    def test_reverse_positions_frozen(self) -> None:
        """Items 3, 7, 9 are pessimism-worded; flipped before sum."""
        assert LOTR_REVERSE_ITEMS == (3, 7, 9)
        assert isinstance(LOTR_REVERSE_ITEMS, tuple)

    def test_scored_and_filler_partition_all_positions(self) -> None:
        """Every position 1..10 is either scored or filler; no overlap."""
        combined = set(LOTR_SCORED_POSITIONS) | set(LOTR_FILLER_POSITIONS)
        assert combined == set(range(1, ITEM_COUNT + 1))
        assert (
            set(LOTR_SCORED_POSITIONS) & set(LOTR_FILLER_POSITIONS) == set()
        )

    def test_reverse_items_are_scored_items(self) -> None:
        """Reverse-keying only makes sense on scored items."""
        assert set(LOTR_REVERSE_ITEMS).issubset(set(LOTR_SCORED_POSITIONS))


# ---------------------------------------------------------------------------
# TestTotalCorrectness — arithmetic pins on the scorer
# ---------------------------------------------------------------------------


class TestTotalCorrectness:

    def test_all_zeros_yields_twelve(self) -> None:
        """All items 0.  Scored: 1,3,4,7,9,10 raw 0,0,0,0,0,0; reverse
        flips items 3, 7, 9 from 0 → 4.  Sum = 0+4+0+4+4+0 = 12."""
        r = score_lotr([0] * 10)
        assert r.total == 12

    def test_all_fours_yields_twelve(self) -> None:
        """All items 4.  Scored raw 4,4,4,4,4,4; reverse flips items 3,
        7, 9 from 4 → 0.  Sum = 4+0+4+0+0+4 = 12.  Catches response-set
        acquiescence — someone who checks "strongly agree" for every
        item gets the midline, not the maximum."""
        r = score_lotr([4] * 10)
        assert r.total == 12

    def test_all_twos_yields_twelve(self) -> None:
        """Midline responses — all items 2.  Reverse-flip of 2 is 2
        (arithmetic reflection around the midpoint).  Sum = 6 × 2 = 12.
        Flip-invariance at midline."""
        r = score_lotr([2] * 10)
        assert r.total == 12

    def test_all_ones_symmetric_to_all_threes(self) -> None:
        """All 1s: direct items contribute 1; reverse items flip to 3.
        Sum = 3×1 + 3×3 = 12.  All 3s: direct contribute 3; reverse
        flip to 1.  Sum = 3×3 + 3×1 = 12.  Response-set detection both
        directions."""
        assert score_lotr([1] * 10).total == 12
        assert score_lotr([3] * 10).total == 12

    def test_maximum_optimism_profile_yields_24(self) -> None:
        """Direct items (1, 4, 10) = 4; reverse items (3, 7, 9) = 0
        (patient strongly disagrees with pessimism-worded items).
        Post-flip every scored item = 4.  Sum = 6 × 4 = 24.  Fillers
        at mid so they do not affect."""
        raw = _build(
            {1: 4, 3: 0, 4: 4, 7: 0, 9: 0, 10: 4}, filler_fill=2,
        )
        assert score_lotr(raw).total == 24

    def test_minimum_optimism_profile_yields_zero(self) -> None:
        """Direct items (1, 4, 10) = 0; reverse items (3, 7, 9) = 4
        (patient strongly agrees with pessimism-worded items).  Post-
        flip every scored item = 0.  Sum = 0.  Fillers at mid do not
        affect."""
        raw = _build(
            {1: 0, 3: 4, 4: 0, 7: 4, 9: 4, 10: 0}, filler_fill=2,
        )
        assert score_lotr(raw).total == 0

    def test_moderate_optimist(self) -> None:
        """Direct items = 3, reverse items = 1.  Post-flip every scored
        item = 3.  Sum = 18."""
        raw = _build(
            {1: 3, 3: 1, 4: 3, 7: 1, 9: 1, 10: 3}, filler_fill=2,
        )
        assert score_lotr(raw).total == 18

    def test_moderate_pessimist(self) -> None:
        """Direct items = 1, reverse items = 3.  Post-flip every scored
        item = 1.  Sum = 6."""
        raw = _build(
            {1: 1, 3: 3, 4: 1, 7: 3, 9: 3, 10: 1}, filler_fill=2,
        )
        assert score_lotr(raw).total == 6

    def test_asymmetric_profile_arithmetic(self) -> None:
        """Mixed profile — pin a specific non-uniform sum.  Item 1=4,
        3=1, 4=2, 7=3, 9=2, 10=1.  Contributions: 4, (4-1)=3, 2,
        (4-3)=1, (4-2)=2, 1.  Sum = 13."""
        raw = _build(
            {1: 4, 3: 1, 4: 2, 7: 3, 9: 2, 10: 1}, filler_fill=0,
        )
        assert score_lotr(raw).total == 13


# ---------------------------------------------------------------------------
# TestFillerPositionsExcluded — the novel invariant
# ---------------------------------------------------------------------------


class TestFillerPositionsExcluded:

    def test_filler_sweep_does_not_change_total(self) -> None:
        """Holding all 6 scored items at max-optimism (24), sweep the
        fillers across all [0, 4] values; total stays 24."""
        scored_max = {1: 4, 3: 0, 4: 4, 7: 0, 9: 0, 10: 4}
        totals = set()
        for fill in range(ITEM_MIN, ITEM_MAX + 1):
            raw = _build(scored_max, filler_fill=fill)
            totals.add(score_lotr(raw).total)
        assert totals == {24}

    def test_filler_sweep_at_minimum_profile(self) -> None:
        """Same invariant at the minimum-optimism scored profile."""
        scored_min = {1: 0, 3: 4, 4: 0, 7: 4, 9: 4, 10: 0}
        totals = set()
        for fill in range(ITEM_MIN, ITEM_MAX + 1):
            raw = _build(scored_min, filler_fill=fill)
            totals.add(score_lotr(raw).total)
        assert totals == {0}

    @pytest.mark.parametrize("filler_pos", [2, 5, 6, 8])
    def test_individual_filler_position_does_not_contribute(
        self, filler_pos: int,
    ) -> None:
        """Toggle a single filler position from 0 to 4; total does not
        change.  Parametrized across each of the 4 filler positions."""
        scored = _build(
            {1: 3, 3: 1, 4: 3, 7: 1, 9: 1, 10: 3}, filler_fill=0,
        )
        baseline = score_lotr(scored).total

        toggled = list(scored)
        toggled[filler_pos - 1] = 4
        assert score_lotr(toggled).total == baseline

    def test_all_fillers_extreme_with_scored_midline(self) -> None:
        """Fillers at 4, scored items at 2.  If fillers were being
        summed, total would exceed 12.  Expected: post-flip all scored
        contribute 2.  Sum = 12.  Confirms fillers silent."""
        raw = [2] * 10
        for pos in LOTR_FILLER_POSITIONS:
            raw[pos - 1] = 4
        assert score_lotr(raw).total == 12

    def test_single_scored_item_toggle_does_change_total(self) -> None:
        """Complement check — scored items DO contribute.  Baseline all
        0s (→ 12).  Toggle item 1 from 0 → 4: adds 4 (direct item),
        total = 16.  This rules out a false-positive where the scorer
        simply returns a constant."""
        baseline = score_lotr([0] * 10).total
        assert baseline == 12

        toggled = [0] * 10
        toggled[0] = 4  # item 1, direct
        assert score_lotr(toggled).total == 16

    def test_reverse_scored_item_toggle_flips_direction(self) -> None:
        """Complement check on reverse item.  Baseline all 0s (→ 12).
        Toggle item 3 (reverse) from 0 → 4: contribution was (4-0)=4,
        becomes (4-4)=0; total decreases by 4 to 8."""
        baseline = score_lotr([0] * 10).total
        assert baseline == 12

        toggled = [0] * 10
        toggled[2] = 4  # item 3, reverse
        assert score_lotr(toggled).total == 8


# ---------------------------------------------------------------------------
# TestItemCountValidation — misroute guards
# ---------------------------------------------------------------------------


class TestItemCountValidation:

    def test_rejects_zero_items(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 10"):
            score_lotr([])

    def test_rejects_one_item(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 10"):
            score_lotr([2])

    def test_rejects_six_items_only_scored_positions(self) -> None:
        """Someone who pre-strips fillers and sends only the 6 scored
        items should be rejected — the wire contract requires 10."""
        with pytest.raises(InvalidResponseError, match="exactly 10"):
            score_lotr([2, 2, 2, 2, 2, 2])

    def test_rejects_nine_items(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 10"):
            score_lotr([2] * 9)

    def test_rejects_eleven_items(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 10"):
            score_lotr([2] * 11)

    def test_rejects_pswq_misroute(self) -> None:
        """PSWQ is 16 items; must not silently accept."""
        with pytest.raises(InvalidResponseError, match="exactly 10"):
            score_lotr([3] * 16)

    def test_rejects_ders16_misroute(self) -> None:
        """DERS-16 is 16 items."""
        with pytest.raises(InvalidResponseError, match="exactly 10"):
            score_lotr([1] * 16)

    def test_rejects_pcl5_misroute(self) -> None:
        """PCL-5 is 20 items."""
        with pytest.raises(InvalidResponseError, match="exactly 10"):
            score_lotr([0] * 20)


# ---------------------------------------------------------------------------
# TestItemRangeValidation — 0-4 floor/ceiling
# ---------------------------------------------------------------------------


class TestItemRangeValidation:

    @pytest.mark.parametrize("bad_value", [-5, -1, 5, 6, 100, 255])
    def test_rejects_out_of_range(self, bad_value: int) -> None:
        raw = [2] * 10
        raw[0] = bad_value  # item 1
        with pytest.raises(InvalidResponseError, match="out of range"):
            score_lotr(raw)

    def test_rejects_out_of_range_at_filler_position(self) -> None:
        """Filler positions are validated identically — a value outside
        [0, 4] at a filler position is a wire violation even though
        that position won't be summed."""
        raw = [2] * 10
        raw[1] = 7  # item 2, filler
        with pytest.raises(InvalidResponseError, match="item 2"):
            score_lotr(raw)

    def test_rejects_out_of_range_at_reverse_position(self) -> None:
        """Reverse-keyed items validated pre-flip."""
        raw = [2] * 10
        raw[2] = 10  # item 3, reverse
        with pytest.raises(InvalidResponseError, match="item 3"):
            score_lotr(raw)

    def test_rejects_float(self) -> None:
        raw: list[object] = [2] * 10
        raw[0] = 2.5
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_lotr(raw)  # type: ignore[arg-type]

    def test_rejects_string(self) -> None:
        raw: list[object] = [2] * 10
        raw[0] = "2"
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_lotr(raw)  # type: ignore[arg-type]

    def test_rejects_none(self) -> None:
        raw: list[object] = [2] * 10
        raw[5] = None
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_lotr(raw)  # type: ignore[arg-type]

    def test_error_message_uses_one_indexed_position(self) -> None:
        """Clinicians and wire-format docs use 1-indexed item numbers
        (item 1, item 2, ..., item 10).  The error message must match."""
        raw = [2] * 10
        raw[9] = 99  # item 10 (1-indexed) = position 9 in list
        with pytest.raises(InvalidResponseError, match="item 10"):
            score_lotr(raw)

    def test_floor_boundary_accepts_zero(self) -> None:
        """0 is in range — must accept."""
        r = score_lotr([0] * 10)
        assert r.total == 12

    def test_ceiling_boundary_accepts_four(self) -> None:
        """4 is in range — must accept."""
        r = score_lotr([4] * 10)
        assert r.total == 12


# ---------------------------------------------------------------------------
# TestBoolRejection — bool is an int subclass; must be rejected
# ---------------------------------------------------------------------------


class TestBoolRejection:

    def test_rejects_bool_true_at_scored_position(self) -> None:
        raw: list[object] = [2] * 10
        raw[0] = True  # item 1, scored-direct
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_lotr(raw)  # type: ignore[arg-type]

    def test_rejects_bool_false_at_filler_position(self) -> None:
        raw: list[object] = [2] * 10
        raw[1] = False  # item 2, filler
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_lotr(raw)  # type: ignore[arg-type]

    def test_rejects_bool_at_reverse_position(self) -> None:
        raw: list[object] = [2] * 10
        raw[6] = True  # item 7, scored-reverse
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_lotr(raw)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# TestResultShape — envelope contract pins
# ---------------------------------------------------------------------------


class TestResultShape:

    def test_returns_lotrresult_instance(self) -> None:
        r = score_lotr([2] * 10)
        assert isinstance(r, LotrResult)

    def test_instrument_version_populated(self) -> None:
        r = score_lotr([2] * 10)
        assert r.instrument_version == INSTRUMENT_VERSION

    def test_items_preserves_all_ten_raw_responses(self) -> None:
        """Audit-trail invariant: the patient saw 10 items on the form,
        all 10 raw responses must be in the result — INCLUDING the 4
        filler values and the pre-flip raw value for reverse items."""
        raw = [4, 0, 4, 0, 1, 2, 4, 3, 0, 4]
        r = score_lotr(raw)
        assert r.items == tuple(raw)

    def test_items_is_tuple(self) -> None:
        """Frozen-tuple invariant for hashability and non-mutation."""
        r = score_lotr([2] * 10)
        assert isinstance(r.items, tuple)

    def test_items_preserves_reverse_items_pre_flip(self) -> None:
        """Reverse-keying is an internal scoring detail; ``items``
        must not surface flipped values.  Raw 4 at position 3
        (reverse) must appear in items as 4, not 0."""
        raw = [2, 2, 4, 2, 2, 2, 4, 2, 4, 2]
        r = score_lotr(raw)
        assert r.items[2] == 4  # item 3 pre-flip
        assert r.items[6] == 4  # item 7 pre-flip
        assert r.items[8] == 4  # item 9 pre-flip

    def test_no_severity_field(self) -> None:
        """Continuous instrument — no severity band.  Emitted as
        sentinel ``severity="continuous"`` at router level, not here."""
        r = score_lotr([2] * 10)
        assert not hasattr(r, "severity")

    def test_no_cutoff_used_field(self) -> None:
        """Continuous — no cutoff shape."""
        r = score_lotr([2] * 10)
        assert not hasattr(r, "cutoff_used")

    def test_no_positive_screen_field(self) -> None:
        """Continuous — no screen shape."""
        r = score_lotr([2] * 10)
        assert not hasattr(r, "positive_screen")

    def test_no_requires_t3_field(self) -> None:
        """LOT-R has no safety item."""
        r = score_lotr([2] * 10)
        assert not hasattr(r, "requires_t3")

    def test_no_subscales_field(self) -> None:
        """Scheier 1994 sustained unidimensional structure.  We ship
        unidimensional; Chang 1997 two-factor split is sample-specific
        and deliberately rejected."""
        r = score_lotr([2] * 10)
        assert not hasattr(r, "subscales")

    def test_result_is_frozen(self) -> None:
        r = score_lotr([2] * 10)
        with pytest.raises(Exception):  # FrozenInstanceError
            r.total = 99  # type: ignore[misc]

    def test_result_is_hashable(self) -> None:
        """Frozen + tuple fields → hashable → usable in sets/dict keys."""
        r = score_lotr([2] * 10)
        hash(r)

    def test_total_is_int(self) -> None:
        r = score_lotr([1, 2, 3, 2, 1, 2, 3, 2, 3, 1])
        assert isinstance(r.total, int)


# ---------------------------------------------------------------------------
# TestClinicalVignettes — response-pattern pins
# ---------------------------------------------------------------------------


class TestClinicalVignettes:

    def test_optimist_profile_near_ceiling(self) -> None:
        """Self-described optimistic patient: strong-agrees with the
        direct items, strong-disagrees with the pessimism-worded
        reverse items.  Fillers at moderate agree (3).  Expected: 24."""
        raw = _build(
            {1: 4, 3: 0, 4: 4, 7: 0, 9: 0, 10: 4}, filler_fill=3,
        )
        assert score_lotr(raw).total == 24

    def test_pessimist_profile_near_floor(self) -> None:
        """Depressed patient with low future-expectancy: disagrees
        with direct optimism items, agrees with pessimism-worded
        reverse items.  Expected: 0."""
        raw = _build(
            {1: 0, 3: 4, 4: 0, 7: 4, 9: 4, 10: 0}, filler_fill=1,
        )
        assert score_lotr(raw).total == 0

    def test_acquiescence_bias_caught(self) -> None:
        """Response-set bias: patient strong-agrees with everything
        (all 4s).  A naive sum would give 24 × 1.67 = 40 (or 24 if
        capped to scored-only).  Mixed-direction wording catches the
        bias: sum = 12 (midline).  A clinician reading 12 on a mixed-
        direction instrument knows to flag response-set bias."""
        r = score_lotr([4] * 10)
        assert r.total == 12
        assert r.total != 24  # not the maximum
        assert r.total != 0   # not the minimum

    def test_dis_acquiescence_bias_caught(self) -> None:
        """Opposite response set: patient strong-disagrees with
        everything (all 0s).  Also flattens to midline (12)."""
        r = score_lotr([0] * 10)
        assert r.total == 12

    def test_midline_flip_invariance(self) -> None:
        """Response-set midline (all 2s) lands at 12 — confirms
        arithmetic-reflection symmetry around the midpoint."""
        r = score_lotr([2] * 10)
        assert r.total == 12

    def test_slight_optimistic_tilt(self) -> None:
        """Patient slightly agrees with direct (2 → 3 on items 1, 4,
        10), slightly disagrees with reverse (2 → 1 on items 3, 7, 9).
        Contributions: 3, (4-1)=3, 3, (4-1)=3, (4-1)=3, 3 = 18.  A
        ~1-point shift from midline per scored item."""
        raw = _build(
            {1: 3, 3: 1, 4: 3, 7: 1, 9: 1, 10: 3}, filler_fill=2,
        )
        assert score_lotr(raw).total == 18


# ---------------------------------------------------------------------------
# TestNoSafetyRouting — T3 never fires from LOT-R alone
# ---------------------------------------------------------------------------


class TestNoSafetyRouting:

    def test_no_requires_t3_at_floor(self) -> None:
        """Minimum optimism (0) is a strong prior for outcome-
        expectancy scaffolding but NOT itself a crisis gate — acute
        ideation screening is PHQ-9 item 9 / C-SSRS, not LOT-R."""
        raw = _build(
            {1: 0, 3: 4, 4: 0, 7: 4, 9: 4, 10: 0}, filler_fill=0,
        )
        r = score_lotr(raw)
        assert not hasattr(r, "requires_t3")
        assert r.total == 0

    def test_no_requires_t3_at_midline(self) -> None:
        r = score_lotr([2] * 10)
        assert not hasattr(r, "requires_t3")
        assert r.total == 12

    def test_no_requires_t3_at_ceiling(self) -> None:
        raw = _build(
            {1: 4, 3: 0, 4: 4, 7: 0, 9: 0, 10: 4}, filler_fill=4,
        )
        r = score_lotr(raw)
        assert not hasattr(r, "requires_t3")
        assert r.total == 24

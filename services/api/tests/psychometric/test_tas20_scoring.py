"""Unit tests for TAS-20 (Toronto Alexithymia Scale, Bagby 1994).

Pins the Bagby, Parker & Taylor (1994) scoring contract:

- 20-item 1-5 Likert payload, three-factor subscale structure:
  DIF (7 items: 1, 3, 6, 7, 9, 13, 14), DDF (5 items: 2, 4, 11, 12,
  17), EOT (8 items: 5, 8, 10, 15, 16, 18, 19, 20).
- Reverse-keying on items 4, 5, 10, 18, 19 (alexithymia-absent
  wording).  Scorer applies the arithmetic-reflection idiom reused
  from PSWQ / LOT-R: ``flipped = 6 - raw``.
- Post-flip total range 20-100.  Higher is worse (more alexithymia).
- Subscale totals computed from POST-flip values so within-subscale
  reverse items contribute in the alexithymia direction.
- Bagby 1994 cutoffs (replicated Taylor 1997, cross-calibrated
  against structured clinical interview): ≤51 non_alexithymic,
  52-60 possible_alexithymia, ≥61 alexithymic.
- No T3 — the 20 items probe emotion-identification / description
  / externally-oriented cognition; none probe suicidality.
- ``items`` field preserves the patient's RAW pre-flip responses
  for auditability.

Novel patterns under test:
1. **Re-introduces banded classification** after 5 consecutive
   continuous-sentinel sprints (WSAS, DERS-16, CD-RISC-10, PSWQ,
   LOT-R).  The midline-lands-in-possible-band property (raw all
   3s → total 60 → possible_alexithymia) is deliberately pinned
   — it is a clinical property of Bagby's threshold placement, not
   an off-by-one defect.
2. **Subscale post-flip invariant** — the EOT subscale contains
   4 reverse items (5, 10, 18, 19) out of 8; if the scorer
   computed the subscale sum from RAW values the EOT total would
   be higher-is-better while the other subscales are higher-is-
   worse.  Tests pin that all three subscales contribute in the
   alexithymia direction.
3. **Banded + subscales envelope** — TAS-20 has both severity bands
   AND subscale totals, a shape distinct from DERS-16 (continuous
   + subscales) and AUDIT (banded, no subscales).
"""

from __future__ import annotations

import pytest

from discipline.psychometric.scoring.tas20 import (
    INSTRUMENT_VERSION,
    ITEM_COUNT,
    ITEM_MAX,
    ITEM_MIN,
    TAS20_NON_ALEXITHYMIC_UPPER,
    TAS20_POSSIBLE_UPPER,
    TAS20_REVERSE_ITEMS,
    TAS20_SUBSCALES,
    TAS20_TOTAL_MAX,
    TAS20_TOTAL_MIN,
    InvalidResponseError,
    Tas20Result,
    score_tas20,
)

# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------


def _make(
    *, direct: int = 3, reverse: int = 3,
) -> list[int]:
    """Build a 20-item list with distinct direct vs reverse values.

    This helper exists to make "maximum alexithymia" / "minimum
    alexithymia" / direction-mixed patterns readable in tests.
    """
    out = []
    for i in range(1, ITEM_COUNT + 1):
        if i in TAS20_REVERSE_ITEMS:
            out.append(reverse)
        else:
            out.append(direct)
    return out


# ---------------------------------------------------------------------------
# TestConstants
# ---------------------------------------------------------------------------


class TestConstants:

    def test_instrument_version(self) -> None:
        assert INSTRUMENT_VERSION == "tas20-1.0.0"

    def test_item_count(self) -> None:
        assert ITEM_COUNT == 20

    def test_item_min_max(self) -> None:
        assert ITEM_MIN == 1
        assert ITEM_MAX == 5

    def test_total_bounds_consistent(self) -> None:
        """Post-flip floor 20 (every item at 1) and ceiling 100
        (every item at 5).  Pinned as module constants."""
        assert TAS20_TOTAL_MIN == 20
        assert TAS20_TOTAL_MAX == 100

    def test_subscale_assignments_frozen(self) -> None:
        """Bagby 1994 three-factor CFA item assignments."""
        assert TAS20_SUBSCALES["dif"] == (1, 3, 6, 7, 9, 13, 14)
        assert TAS20_SUBSCALES["ddf"] == (2, 4, 11, 12, 17)
        assert TAS20_SUBSCALES["eot"] == (5, 8, 10, 15, 16, 18, 19, 20)

    def test_subscales_partition_all_items(self) -> None:
        """Every item 1..20 belongs to exactly one subscale — the
        three factors together cover the full instrument without
        overlap."""
        combined: list[int] = []
        for positions in TAS20_SUBSCALES.values():
            combined.extend(positions)
        assert sorted(combined) == list(range(1, ITEM_COUNT + 1))
        # No duplicates.
        assert len(combined) == len(set(combined))

    def test_reverse_items_frozen(self) -> None:
        """Bagby 1994 reverse-keyed items."""
        assert TAS20_REVERSE_ITEMS == (4, 5, 10, 18, 19)

    def test_band_cutoffs_frozen(self) -> None:
        """Bagby 1994 published cutoffs — non-alexithymic ≤51,
        possible 52-60, alexithymic ≥61.  Do NOT hand-roll these."""
        assert TAS20_NON_ALEXITHYMIC_UPPER == 51
        assert TAS20_POSSIBLE_UPPER == 60


# ---------------------------------------------------------------------------
# TestTotalCorrectness
# ---------------------------------------------------------------------------


class TestTotalCorrectness:

    def test_all_raw_ones_total_40(self) -> None:
        """Every raw item at 1.  Direct 15 × 1 = 15; reverse 5 ×
        (6-1)=5 = 25.  Total = 40."""
        assert score_tas20([1] * 20).total == 40

    def test_all_raw_threes_total_60_midline(self) -> None:
        """Every raw item at 3 — midline.  Flip-invariant because
        6-3=3.  Total = 20 × 3 = 60.  Lands exactly on the upper
        edge of the "possible alexithymia" band."""
        assert score_tas20([3] * 20).total == 60

    def test_all_raw_fives_total_80(self) -> None:
        """Every raw item at 5.  Direct 15 × 5 = 75; reverse 5 ×
        (6-5)=1 = 5.  Total = 80.  Acquiescence catch — strong-
        agrees everywhere → alexithymic band (80 > 61), not
        ceiling 100."""
        assert score_tas20([5] * 20).total == 80

    def test_minimum_alexithymia_pattern_floor(self) -> None:
        """Minimum-alexithymia pattern: direct=1, reverse=5.  Post-
        flip every item = 1.  Total = 20 (instrument floor)."""
        assert score_tas20(_make(direct=1, reverse=5)).total == 20

    def test_maximum_alexithymia_pattern_ceiling(self) -> None:
        """Maximum-alexithymia pattern: direct=5, reverse=1.  Post-
        flip every item = 5.  Total = 100 (instrument ceiling)."""
        assert score_tas20(_make(direct=5, reverse=1)).total == 100

    def test_total_in_valid_range_for_all_inputs(self) -> None:
        """Across several inputs, total stays in [20, 100]."""
        for raw in (
            [1] * 20,
            [2] * 20,
            [3] * 20,
            [4] * 20,
            [5] * 20,
            [1, 2, 3, 4, 5] * 4,
            _make(direct=1, reverse=5),
            _make(direct=5, reverse=1),
        ):
            r = score_tas20(raw)
            assert TAS20_TOTAL_MIN <= r.total <= TAS20_TOTAL_MAX

    def test_reverse_keying_single_item_flip_symmetry(self) -> None:
        """Toggle only item 4 (reverse) from 1 to 5.  Post-flip
        contribution moves from (6-1)=5 to (6-5)=1 — a swing of -4
        at that position.  Baseline: all raw=1 → 40.  After
        toggle: 40 - 4 = 36."""
        baseline = score_tas20([1] * 20).total
        assert baseline == 40

        toggled = [1] * 20
        toggled[3] = 5  # item 4 (reverse)
        assert score_tas20(toggled).total == 36

    def test_non_reverse_item_toggle_direct_contribution(self) -> None:
        """Toggle only item 1 (direct, DIF subscale) from 1 to 5.
        Post-flip contribution moves from 1 to 5 — a swing of +4.
        Baseline 40 + 4 = 44."""
        baseline = score_tas20([1] * 20).total
        toggled = [1] * 20
        toggled[0] = 5  # item 1 (direct)
        assert score_tas20(toggled).total == 44

    def test_asymmetric_profile_pinned(self) -> None:
        """Mixed profile — pin a specific non-uniform sum.
        Pattern: direct items at 4, reverse items at 2.  Post-flip:
        direct 15 × 4 = 60; reverse 5 × (6-2)=4 = 20.  Total = 80."""
        raw = _make(direct=4, reverse=2)
        assert score_tas20(raw).total == 80

    def test_clinical_midline_boundary_arithmetic(self) -> None:
        """Raw all 3s = 60 lands at the upper boundary of the
        possible-alexithymia band.  Dropping a single direct item
        from 3 to 2 shifts total to 59 (non-alexithymic boundary
        region)."""
        raw = [3] * 20
        raw[0] = 2  # item 1 (direct, DIF)
        assert score_tas20(raw).total == 59


# ---------------------------------------------------------------------------
# TestSubscaleAssignments
# ---------------------------------------------------------------------------


class TestSubscaleAssignments:

    def test_dif_subscale_all_raw_threes_is_21(self) -> None:
        """DIF has 7 items, no reverse.  All raw 3 → subscale 21."""
        r = score_tas20([3] * 20)
        assert r.subscale_dif == 21

    def test_ddf_subscale_all_raw_threes_is_15(self) -> None:
        """DDF has 5 items, item 4 reverse.  All raw 3 → post-flip
        also 3 at every position → subscale 15."""
        r = score_tas20([3] * 20)
        assert r.subscale_ddf == 15

    def test_eot_subscale_all_raw_threes_is_24(self) -> None:
        """EOT has 8 items, items 5, 10, 18, 19 reverse.  All raw
        3 → post-flip also 3 → subscale 24."""
        r = score_tas20([3] * 20)
        assert r.subscale_eot == 24

    def test_subscales_sum_to_total(self) -> None:
        """Subscales are a full partition — their sum equals the
        post-flip total.  Holds for any valid input."""
        for raw in (
            [1] * 20,
            [2] * 20,
            [3] * 20,
            [4] * 20,
            [5] * 20,
            _make(direct=1, reverse=5),
            _make(direct=5, reverse=1),
            [1, 2, 3, 4, 5] * 4,
        ):
            r = score_tas20(raw)
            assert r.subscale_dif + r.subscale_ddf + r.subscale_eot == r.total

    def test_eot_subscale_post_flip_not_raw(self) -> None:
        """Critical invariant: EOT contains 4 reverse items (5, 10,
        18, 19).  If the scorer summed RAW values the EOT subscale
        would move in the alexithymia-ABSENT direction.  Test: all
        raw = 5 should give EOT = 4 direct × 5 + 4 reverse × (6-5)=1
        = 20 + 4 = 24, NOT 40 (the raw sum)."""
        r = score_tas20([5] * 20)
        assert r.subscale_eot == 24
        assert r.subscale_eot != 40

    def test_ddf_subscale_post_flip_not_raw(self) -> None:
        """DDF contains 1 reverse item (item 4).  All raw = 5 →
        DDF = 4 direct × 5 + 1 reverse × (6-5)=1 = 21, NOT 25."""
        r = score_tas20([5] * 20)
        assert r.subscale_ddf == 21

    def test_dif_subscale_no_reverse(self) -> None:
        """DIF has no reverse items, so raw=post-flip.  All raw 5
        → DIF 35 (ceiling)."""
        r = score_tas20([5] * 20)
        assert r.subscale_dif == 35

    def test_subscale_ranges_at_floor_and_ceiling(self) -> None:
        """DIF range 7-35, DDF 5-25, EOT 8-40.  Min-alexithymia
        pattern (direct=1, reverse=5) → every post-flip value 1 →
        subscales at their floors."""
        min_alex = score_tas20(_make(direct=1, reverse=5))
        assert min_alex.subscale_dif == 7
        assert min_alex.subscale_ddf == 5
        assert min_alex.subscale_eot == 8

        max_alex = score_tas20(_make(direct=5, reverse=1))
        assert max_alex.subscale_dif == 35
        assert max_alex.subscale_ddf == 25
        assert max_alex.subscale_eot == 40


# ---------------------------------------------------------------------------
# TestBandClassification
# ---------------------------------------------------------------------------


class TestBandClassification:

    def test_band_at_floor(self) -> None:
        """Total 20 (floor) → non_alexithymic."""
        assert score_tas20(_make(direct=1, reverse=5)).band == "non_alexithymic"

    def test_band_at_51_upper_non_alexithymic(self) -> None:
        """Total 51 is the upper boundary of the non_alexithymic
        band."""
        # Build a total of exactly 51 post-flip.  All direct=1 (15
        # items contribute 15), reverse=3 (5 items × (6-3)=3 = 15).
        # Subtotal = 30.  Need +21 to hit 51.  Increase 7 DIF items
        # (1, 3, 6, 7, 9, 13, 14) from 1 to 4.  Each adds +3.
        # 7 × 3 = 21.  Total = 30 + 21 = 51.
        raw = [1] * 20
        # DIF: items 1, 3, 6, 7, 9, 13, 14 → set to 4
        for pos in (1, 3, 6, 7, 9, 13, 14):
            raw[pos - 1] = 4
        # Reverse items 4, 5, 10, 18, 19 → set to 3 (post-flip 3)
        for pos in TAS20_REVERSE_ITEMS:
            raw[pos - 1] = 3
        r = score_tas20(raw)
        assert r.total == 51
        assert r.band == "non_alexithymic"

    def test_band_at_52_lower_possible(self) -> None:
        """Total 52 → possible_alexithymia (above the 51 upper)."""
        # Take the 51-total configuration and nudge one DIF item
        # from 4 to 5 (adds +1).
        raw = [1] * 20
        for pos in (1, 3, 6, 7, 9, 13, 14):
            raw[pos - 1] = 4
        for pos in TAS20_REVERSE_ITEMS:
            raw[pos - 1] = 3
        raw[0] = 5  # item 1 goes from 4 to 5: +1
        r = score_tas20(raw)
        assert r.total == 52
        assert r.band == "possible_alexithymia"

    def test_band_at_60_upper_possible(self) -> None:
        """Total 60 → possible_alexithymia (upper edge).  Raw all
        3s is the canonical example."""
        r = score_tas20([3] * 20)
        assert r.total == 60
        assert r.band == "possible_alexithymia"

    def test_band_at_61_lower_alexithymic(self) -> None:
        """Total 61 → alexithymic (above the 60 upper)."""
        raw = [3] * 20
        raw[0] = 4  # item 1 (direct): +1 → total 61
        r = score_tas20(raw)
        assert r.total == 61
        assert r.band == "alexithymic"

    def test_band_at_ceiling(self) -> None:
        """Total 100 (ceiling) → alexithymic."""
        r = score_tas20(_make(direct=5, reverse=1))
        assert r.total == 100
        assert r.band == "alexithymic"

    def test_all_ones_non_alexithymic(self) -> None:
        """Raw all 1s → total 40 → non_alexithymic."""
        assert score_tas20([1] * 20).band == "non_alexithymic"

    def test_all_fives_alexithymic(self) -> None:
        """Raw all 5s → total 80 → alexithymic (acquiescence catch
        still lands in the clinical band because 80 > 61)."""
        assert score_tas20([5] * 20).band == "alexithymic"

    def test_midline_lands_in_possible_band(self) -> None:
        """Raw all 3s (midline) → total 60 → possible_alexithymia.
        This is a DELIBERATE clinical property of Bagby's cutoff
        placement — a midline responder's "neither agree nor
        disagree" on alexithymia-identifying statements is itself
        evidence of poor emotional self-knowledge.  Do NOT 'fix'
        this by shifting the cutoff."""
        r = score_tas20([3] * 20)
        assert r.band == "possible_alexithymia"

    def test_band_monotonic_in_total(self) -> None:
        """Band classification is monotonic in the total — walking
        from floor to ceiling, the band sequence is
        non_alexithymic → possible_alexithymia → alexithymic with
        no regressions."""
        last_rank = 0
        rank_map = {
            "non_alexithymic": 0,
            "possible_alexithymia": 1,
            "alexithymic": 2,
        }
        for total_target in [20, 40, 51, 52, 60, 61, 80, 100]:
            # Build an input that lands on the target total.  Use
            # all ones plus incremental direct-item increases.
            raw = [1] * 20
            # Reverse items contribute (6-1)=5 each → 25.  Direct
            # items contribute 1 each → 15.  Base = 40.
            # Need (target - 40) more from direct-item increases.
            needed = total_target - 40
            if needed > 0:
                direct_positions = [
                    i for i in range(1, 21) if i not in TAS20_REVERSE_ITEMS
                ]
                # Each direct item can go from 1 to 5, adding up to 4.
                remaining = needed
                idx = 0
                while remaining > 0 and idx < len(direct_positions):
                    pos = direct_positions[idx]
                    add = min(4, remaining)
                    raw[pos - 1] = 1 + add
                    remaining -= add
                    idx += 1
            elif needed < 0:
                # Below 40 — drop reverse items (their post-flip
                # value decreases when raw increases).
                rev = list(TAS20_REVERSE_ITEMS)
                remaining = -needed
                idx = 0
                while remaining > 0 and idx < len(rev):
                    pos = rev[idx]
                    add = min(4, remaining)
                    raw[pos - 1] = 1 + add  # post-flip decreases
                    remaining -= add
                    idx += 1
            r = score_tas20(raw)
            rank = rank_map[r.band]
            assert rank >= last_rank, (
                f"band regressed at total={r.total}: rank {rank} "
                f"< last {last_rank}"
            )
            last_rank = rank


# ---------------------------------------------------------------------------
# TestItemCountValidation
# ---------------------------------------------------------------------------


class TestItemCountValidation:

    def test_rejects_zero_items(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 20"):
            score_tas20([])

    def test_rejects_nineteen_items(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 20"):
            score_tas20([3] * 19)

    def test_rejects_twentyone_items(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 20"):
            score_tas20([3] * 21)

    def test_rejects_pcl5_count_misroute(self) -> None:
        """PCL-5 is also 20 items — but with a 0-4 envelope.  If
        the router dispatched PCL-5 to TAS-20 by count, the 0
        floor would crash here.  Test: all 0s fails on range, not
        count — but all 1s would pass count and give a valid TAS-20
        total that's structurally wrong.  The router's instrument-
        key dispatch is the real guard; we just confirm the scorer
        won't silently accept 0 items."""
        with pytest.raises(InvalidResponseError, match="out of range"):
            score_tas20([0] * 20)

    def test_rejects_pswq_misroute(self) -> None:
        """PSWQ is 16 items."""
        with pytest.raises(InvalidResponseError, match="exactly 20"):
            score_tas20([3] * 16)

    def test_rejects_cdrisc10_misroute(self) -> None:
        """CD-RISC-10 is 10 items."""
        with pytest.raises(InvalidResponseError, match="exactly 20"):
            score_tas20([3] * 10)


# ---------------------------------------------------------------------------
# TestItemRangeValidation
# ---------------------------------------------------------------------------


class TestItemRangeValidation:

    @pytest.mark.parametrize("bad_value", [-5, -1, 0, 6, 7, 100, 255])
    def test_rejects_out_of_range(self, bad_value: int) -> None:
        raw = [3] * 20
        raw[0] = bad_value
        with pytest.raises(InvalidResponseError, match="out of range"):
            score_tas20(raw)

    def test_rejects_out_of_range_at_reverse_position(self) -> None:
        """Reverse-keyed items validated pre-flip against the raw
        range [1, 5]."""
        raw = [3] * 20
        raw[3] = 10  # item 4, reverse
        with pytest.raises(InvalidResponseError, match="item 4"):
            score_tas20(raw)

    def test_rejects_float(self) -> None:
        raw: list[object] = [3] * 20
        raw[0] = 2.5
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_tas20(raw)  # type: ignore[arg-type]

    def test_rejects_string(self) -> None:
        raw: list[object] = [3] * 20
        raw[0] = "3"
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_tas20(raw)  # type: ignore[arg-type]

    def test_rejects_none(self) -> None:
        raw: list[object] = [3] * 20
        raw[10] = None
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_tas20(raw)  # type: ignore[arg-type]

    def test_error_message_uses_one_indexed_position(self) -> None:
        raw = [3] * 20
        raw[19] = 99  # item 20 (1-indexed) = position 19 in list
        with pytest.raises(InvalidResponseError, match="item 20"):
            score_tas20(raw)

    def test_floor_boundary_accepts_one(self) -> None:
        r = score_tas20([1] * 20)
        assert r.total == 40

    def test_ceiling_boundary_accepts_five(self) -> None:
        r = score_tas20([5] * 20)
        assert r.total == 80


# ---------------------------------------------------------------------------
# TestBoolRejection
# ---------------------------------------------------------------------------


class TestBoolRejection:

    def test_rejects_bool_true_at_direct_position(self) -> None:
        raw: list[object] = [3] * 20
        raw[0] = True
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_tas20(raw)  # type: ignore[arg-type]

    def test_rejects_bool_false_at_reverse_position(self) -> None:
        raw: list[object] = [3] * 20
        raw[3] = False  # item 4, reverse
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_tas20(raw)  # type: ignore[arg-type]

    def test_rejects_bool_at_last_item(self) -> None:
        raw: list[object] = [3] * 20
        raw[19] = True
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_tas20(raw)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# TestResultShape
# ---------------------------------------------------------------------------


class TestResultShape:

    def test_returns_tas20result_instance(self) -> None:
        r = score_tas20([3] * 20)
        assert isinstance(r, Tas20Result)

    def test_instrument_version_populated(self) -> None:
        r = score_tas20([3] * 20)
        assert r.instrument_version == INSTRUMENT_VERSION

    def test_items_preserves_all_raw_pre_flip(self) -> None:
        """Audit-trail invariant: ``items`` is the RAW 20-tuple
        including pre-flip values for the 5 reverse items."""
        raw = [1, 2, 3, 4, 5, 1, 2, 3, 4, 5, 1, 2, 3, 4, 5, 1, 2, 3, 4, 5]
        r = score_tas20(raw)
        assert r.items == tuple(raw)

    def test_items_is_tuple(self) -> None:
        r = score_tas20([3] * 20)
        assert isinstance(r.items, tuple)

    def test_items_reverse_item_raw_preserved(self) -> None:
        """Item 4 is reverse-keyed.  A raw value of 5 must appear
        in items as 5, NOT as 1 (the post-flip value)."""
        raw = [3] * 20
        raw[3] = 5  # item 4
        r = score_tas20(raw)
        assert r.items[3] == 5

    def test_no_cutoff_used_field(self) -> None:
        """TAS-20 has three bands, not a single binary cutoff."""
        r = score_tas20([3] * 20)
        assert not hasattr(r, "cutoff_used")

    def test_no_positive_screen_field(self) -> None:
        r = score_tas20([3] * 20)
        assert not hasattr(r, "positive_screen")

    def test_no_requires_t3_field(self) -> None:
        """TAS-20 has no safety item."""
        r = score_tas20([3] * 20)
        assert not hasattr(r, "requires_t3")

    def test_has_band_field(self) -> None:
        r = score_tas20([3] * 20)
        assert r.band in (
            "non_alexithymic",
            "possible_alexithymia",
            "alexithymic",
        )

    def test_has_three_subscale_fields(self) -> None:
        r = score_tas20([3] * 20)
        assert isinstance(r.subscale_dif, int)
        assert isinstance(r.subscale_ddf, int)
        assert isinstance(r.subscale_eot, int)

    def test_result_is_frozen(self) -> None:
        r = score_tas20([3] * 20)
        with pytest.raises(Exception):  # FrozenInstanceError
            r.total = 99  # type: ignore[misc]

    def test_result_is_hashable(self) -> None:
        """Frozen + tuple fields → hashable."""
        r = score_tas20([3] * 20)
        hash(r)

    def test_total_is_int(self) -> None:
        r = score_tas20([2, 3, 4, 1, 2, 3, 4, 5, 1, 2, 3, 4, 5, 1, 2, 3, 4, 5, 1, 2])
        assert isinstance(r.total, int)


# ---------------------------------------------------------------------------
# TestClinicalVignettes
# ---------------------------------------------------------------------------


class TestClinicalVignettes:

    def test_clearly_alexithymic_profile(self) -> None:
        """Strong-agrees with DIF items (confused about emotions),
        strong-agrees with DDF items (difficulty describing), and
        endorses EOT (prefers external focus).  Direct items at 5,
        reverse items at 1 → total 100, alexithymic band."""
        r = score_tas20(_make(direct=5, reverse=1))
        assert r.band == "alexithymic"
        assert r.total == 100

    def test_clearly_non_alexithymic_profile(self) -> None:
        """Strong-disagrees with DIF/DDF/EOT direct items,
        strong-agrees with reverse items (healthy emotion-
        communication).  Total 20 → non_alexithymic."""
        r = score_tas20(_make(direct=1, reverse=5))
        assert r.band == "non_alexithymic"
        assert r.total == 20

    def test_borderline_possible_band_profile(self) -> None:
        """A patient who endorses most items neutrally — the
        "possible alexithymia" middle band is the clinical
        borderline group that benefits most from affect-labeling
        intervention."""
        r = score_tas20([3] * 20)
        assert r.band == "possible_alexithymia"
        assert 52 <= r.total <= 60

    def test_dif_dominant_profile(self) -> None:
        """DIF-dominant: high DIF subscale relative to DDF/EOT.
        Clinically: "I can't tell what I'm feeling" — routes to
        emotion-identification training specifically (before
        describing-to-others work)."""
        raw = [1] * 20
        # Set all DIF items (1, 3, 6, 7, 9, 13, 14) to 5.
        for pos in (1, 3, 6, 7, 9, 13, 14):
            raw[pos - 1] = 5
        r = score_tas20(raw)
        # DIF at 35 (ceiling), DDF at floor, EOT at floor.
        assert r.subscale_dif == 35
        assert r.subscale_dif > r.subscale_ddf
        assert r.subscale_dif > r.subscale_eot

    def test_response_set_acquiescence_still_classifies_cleanly(self) -> None:
        """Acquiescence response set (all raw = 5) lands at 80,
        well into the alexithymic band — the mixed-direction
        wording catches the bias (80 not 100), but the clinical
        classification is still "alexithymic" because 80 > 61.
        Test pins this is NOT a false-positive artifact: the
        reverse-keying design does not under-call alexithymia when
        the responder is actually alexithymic AND acquiescent."""
        r = score_tas20([5] * 20)
        assert r.band == "alexithymic"
        assert r.total == 80
        assert r.total != 100  # reverse-keying did fire


# ---------------------------------------------------------------------------
# TestNoSafetyRouting
# ---------------------------------------------------------------------------


class TestNoSafetyRouting:

    def test_no_requires_t3_at_floor(self) -> None:
        r = score_tas20(_make(direct=1, reverse=5))
        assert not hasattr(r, "requires_t3")

    def test_no_requires_t3_at_ceiling(self) -> None:
        r = score_tas20(_make(direct=5, reverse=1))
        assert not hasattr(r, "requires_t3")

    def test_no_requires_t3_at_clinical_threshold(self) -> None:
        """A total of 61 (alexithymic clinical threshold) is a
        referral signal for affect-labeling / emotion-regulation-
        therapy work, NOT a crisis signal.  Acute ideation
        screening stays on PHQ-9 item 9 / C-SSRS."""
        raw = [3] * 20
        raw[0] = 4
        r = score_tas20(raw)
        assert r.band == "alexithymic"
        assert not hasattr(r, "requires_t3")

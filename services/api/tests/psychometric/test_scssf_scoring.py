"""Unit tests for SCS-SF scorer (Raes 2011).

The SCS-SF is structurally the most asymmetric scorer in the
psychometric package.  Two distinct scoring conventions live in
the same instrument:

 1. TOTAL is computed POST-FLIP (6 reverse items arithmetically
    reflected) — aggregate reads in the self-compassion direction.
 2. SUBSCALES are computed on RAW values (native construct
    direction) — ``self_judgment`` reads as "how much self-judgment
    does this patient endorse", NOT as the reversed lack-of-self-
    judgment value.

This asymmetry is deliberate per Raes 2011 / Neff 2016 scoring
methodology and preserves the clinically meaningful positive /
negative construct dyad structure (SK vs SJ, CH vs I, M vs OI).
These tests pin the asymmetry explicitly so a future refactor
cannot silently "normalize" subscales to post-flip (which would
break the dyad-reading pattern clinicians expect).

Additional invariants pinned:
- 6-subscale partition: every item in exactly one subscale.
- Reverse items are the 6 uncompassionate-direction items
  (1, 4, 8, 9, 11, 12).
- Arithmetic reflection is ``6 - raw`` on the 1-5 envelope.
- Compassionate self-responding = SK + CH + M (items 2, 3, 5, 6, 7, 10);
  this sum equals the post-flip total minus the post-flip sum of the
  uncompassionate items.
- Bool rejection at the scorer contract.
"""

from __future__ import annotations

import pytest

from discipline.psychometric.scoring.scssf import (
    INSTRUMENT_VERSION,
    ITEM_COUNT,
    ITEM_MAX,
    ITEM_MIN,
    SCSSF_REVERSE_ITEMS,
    SCSSF_SUBSCALES,
    SCSSF_TOTAL_MAX,
    SCSSF_TOTAL_MIN,
    InvalidResponseError,
    ScsSfResult,
    score_scssf,
)


class TestConstants:
    """Pin the Raes 2011 instrument constants."""

    def test_instrument_version_pinned(self) -> None:
        assert INSTRUMENT_VERSION == "scssf-1.0.0"

    def test_item_count_is_twelve(self) -> None:
        assert ITEM_COUNT == 12

    def test_item_min_is_one(self) -> None:
        # 1-5 Likert anchored at "almost never" = 1, NOT 0.
        assert ITEM_MIN == 1

    def test_item_max_is_five(self) -> None:
        assert ITEM_MAX == 5

    def test_total_min_is_twelve(self) -> None:
        # 12 items × 1 = 12 (floor; post-flip lowest value is 1).
        assert SCSSF_TOTAL_MIN == 12

    def test_total_max_is_sixty(self) -> None:
        # 12 items × 5 = 60 (ceiling; post-flip highest value is 5).
        assert SCSSF_TOTAL_MAX == 60

    def test_six_subscales(self) -> None:
        assert len(SCSSF_SUBSCALES) == 6

    def test_each_subscale_has_two_items(self) -> None:
        for name, positions in SCSSF_SUBSCALES.items():
            assert len(positions) == 2, f"subscale {name} has wrong n"

    def test_subscale_partition_covers_all_items_once(self) -> None:
        """The 6 subscales partition the 12 items exactly.

        Every item appears in exactly one subscale.  A refactor
        that duplicated an item across subscales (or forgot one)
        would fail this invariant.  Stronger than the per-subscale
        length checks above.
        """
        all_positions: list[int] = []
        for positions in SCSSF_SUBSCALES.values():
            all_positions.extend(positions)
        assert sorted(all_positions) == list(range(1, ITEM_COUNT + 1))

    def test_reverse_items_are_the_six_uncompassionate_positions(self) -> None:
        # Uncompassionate subscales are SJ (11, 12), I (4, 8),
        # OI (1, 9) — 6 items total.  Pins that only these items
        # are reverse-keyed (not the positive-direction 6 items).
        expected = sorted(
            SCSSF_SUBSCALES["self_judgment"]
            + SCSSF_SUBSCALES["isolation"]
            + SCSSF_SUBSCALES["over_identification"]
        )
        assert sorted(SCSSF_REVERSE_ITEMS) == expected

    def test_reverse_items_are_exactly_six(self) -> None:
        # Six positive + six negative — the instrument is balanced
        # by design (Neff 2003 original intent), preserved in the
        # 12-item short form (Raes 2011).
        assert len(SCSSF_REVERSE_ITEMS) == 6

    def test_self_kindness_positions_raes_2011(self) -> None:
        assert SCSSF_SUBSCALES["self_kindness"] == (2, 6)

    def test_self_judgment_positions_raes_2011(self) -> None:
        assert SCSSF_SUBSCALES["self_judgment"] == (11, 12)

    def test_common_humanity_positions_raes_2011(self) -> None:
        assert SCSSF_SUBSCALES["common_humanity"] == (5, 10)

    def test_isolation_positions_raes_2011(self) -> None:
        assert SCSSF_SUBSCALES["isolation"] == (4, 8)

    def test_mindfulness_positions_raes_2011(self) -> None:
        assert SCSSF_SUBSCALES["mindfulness"] == (3, 7)

    def test_over_identification_positions_raes_2011(self) -> None:
        assert SCSSF_SUBSCALES["over_identification"] == (1, 9)


class TestTotalCorrectness:
    """Pin the post-flip total arithmetic."""

    def test_all_ones_raw_post_flip_total(self) -> None:
        """Every item at 1 → positive items stay 1, negative items
        flip to 5.  Total = 6×1 + 6×5 = 36."""
        result = score_scssf([1] * 12)
        assert result.total == 36

    def test_all_fives_raw_post_flip_total(self) -> None:
        """Every item at 5 → positive items stay 5, negative items
        flip to 1.  Total = 6×5 + 6×1 = 36 (same!).

        Clinically: a "yes to everything" acquiescent responder
        lands at EXACTLY the midpoint of the self-compassion total
        because their positive and negative endorsements cancel.
        This is a built-in acquiescence catch at the instrument
        level — a key reason the instrument balances positive and
        negative items.
        """
        result = score_scssf([5] * 12)
        assert result.total == 36

    def test_all_threes_raw_post_flip_total(self) -> None:
        """Every item at 3 (midline) → post-flip all 3s.  Total
        = 12 × 3 = 36.  Midline flip-invariance."""
        result = score_scssf([3] * 12)
        assert result.total == 36

    def test_maximum_self_compassion_total(self) -> None:
        """Positive items at 5, negative items at 1.  Post-flip
        all 5s.  Total = 60 — the instrument ceiling."""
        items = [0] * 12
        for pos in SCSSF_SUBSCALES["self_kindness"]:
            items[pos - 1] = 5
        for pos in SCSSF_SUBSCALES["common_humanity"]:
            items[pos - 1] = 5
        for pos in SCSSF_SUBSCALES["mindfulness"]:
            items[pos - 1] = 5
        for pos in SCSSF_REVERSE_ITEMS:
            items[pos - 1] = 1
        result = score_scssf(items)
        assert result.total == 60

    def test_minimum_self_compassion_total(self) -> None:
        """Positive items at 1, negative items at 5.  Post-flip
        all 1s.  Total = 12 — the instrument floor."""
        items = [0] * 12
        for pos in SCSSF_SUBSCALES["self_kindness"]:
            items[pos - 1] = 1
        for pos in SCSSF_SUBSCALES["common_humanity"]:
            items[pos - 1] = 1
        for pos in SCSSF_SUBSCALES["mindfulness"]:
            items[pos - 1] = 1
        for pos in SCSSF_REVERSE_ITEMS:
            items[pos - 1] = 5
        result = score_scssf(items)
        assert result.total == 12

    def test_total_is_int_type(self) -> None:
        result = score_scssf([3] * 12)
        assert isinstance(result.total, int)

    def test_reverse_flip_uses_arithmetic_reflection(self) -> None:
        """Every reverse item satisfies ``flipped = 6 - raw``.

        Verified indirectly: set all positive items to 3 (stay 3)
        and all reverse items to 2 (flip to 4).  Total = 6×3 +
        6×4 = 42.
        """
        items = [0] * 12
        positive_positions = (
            SCSSF_SUBSCALES["self_kindness"]
            + SCSSF_SUBSCALES["common_humanity"]
            + SCSSF_SUBSCALES["mindfulness"]
        )
        for pos in positive_positions:
            items[pos - 1] = 3
        for pos in SCSSF_REVERSE_ITEMS:
            items[pos - 1] = 2  # flip to 4
        result = score_scssf(items)
        # 6 positive at 3 + 6 reverse flipped to 4 = 18 + 24 = 42.
        assert result.total == 42

    def test_total_equal_for_symmetric_acquiescence_pattern(self) -> None:
        """Acquiescence invariance: all-1s and all-5s both produce
        total=36 because positive and negative endorsements
        balance exactly."""
        assert score_scssf([1] * 12).total == score_scssf([5] * 12).total

    def test_single_positive_item_bump_raises_total_by_one(self) -> None:
        """Bumping a POSITIVE item by 1 raises total by 1 (no flip)."""
        baseline = score_scssf([3] * 12)
        items = [3] * 12
        # Item 2 is Self-Kindness (positive direction).
        items[1] = 4
        result = score_scssf(items)
        assert result.total - baseline.total == 1

    def test_single_reverse_item_bump_lowers_total_by_one(self) -> None:
        """Bumping a REVERSE item by 1 (raw) LOWERS total by 1
        because the flip: raw 3 → flip 3; raw 4 → flip 2.  A
        clinically critical behavior — endorsing self-judgment
        more strongly must move the compassion total DOWN, not
        up.  A refactor that accidentally dropped the flip would
        break this test.
        """
        baseline = score_scssf([3] * 12)
        items = [3] * 12
        # Item 11 is Self-Judgment (reverse direction).
        items[10] = 4
        result = score_scssf(items)
        assert result.total - baseline.total == -1


class TestSubscaleAssignments:
    """Pin Raes 2011 subscale assignments per item (RAW, not post-flip)."""

    def test_subscales_are_raw_not_post_flip(self) -> None:
        """The central asymmetry test: subscales report raw values.

        Set item 11 (Self-Judgment reverse item) to raw 5.
        If subscales were post-flip, ``subscale_self_judgment``
        would include the flipped value (1).  We assert it uses
        raw (5) — matching the native construct direction.
        """
        items = [3] * 12
        items[10] = 5  # item 11 raw=5
        items[11] = 3  # item 12 raw=3
        result = score_scssf(items)
        # SJ is items (11, 12).  Raw sum = 5 + 3 = 8.  If subscales
        # were post-flipped, SJ sum would be (6-5) + (6-3) = 4.
        assert result.subscale_self_judgment == 8
        # NOT post-flipped — this is the pin.
        assert result.subscale_self_judgment != 4

    def test_self_kindness_raw_sum(self) -> None:
        """Items 2, 6 at raw 4, 5 → SK sum = 9 (raw, positive
        direction — no flip regardless of post-flip or not)."""
        items = [3] * 12
        items[1] = 4   # item 2
        items[5] = 5   # item 6
        result = score_scssf(items)
        assert result.subscale_self_kindness == 9

    def test_common_humanity_raw_sum(self) -> None:
        """Items 5, 10 at raw 2, 3 → CH sum = 5."""
        items = [3] * 12
        items[4] = 2   # item 5
        items[9] = 3   # item 10
        result = score_scssf(items)
        assert result.subscale_common_humanity == 5

    def test_mindfulness_raw_sum(self) -> None:
        """Items 3, 7 at raw 1, 5 → M sum = 6."""
        items = [3] * 12
        items[2] = 1   # item 3
        items[6] = 5   # item 7
        result = score_scssf(items)
        assert result.subscale_mindfulness == 6

    def test_isolation_raw_sum(self) -> None:
        """Items 4, 8 at raw 5, 4 → I sum = 9 (NOT 2+3=5 flipped)."""
        items = [3] * 12
        items[3] = 5   # item 4
        items[7] = 4   # item 8
        result = score_scssf(items)
        assert result.subscale_isolation == 9

    def test_over_identification_raw_sum(self) -> None:
        """Items 1, 9 at raw 4, 5 → OI sum = 9 (NOT 2+1=3 flipped)."""
        items = [3] * 12
        items[0] = 4   # item 1
        items[8] = 5   # item 9
        result = score_scssf(items)
        assert result.subscale_over_identification == 9

    def test_subscale_range_per_subscale_is_two_to_ten(self) -> None:
        """2 items × 1-5 Likert → subscale range 2-10."""
        all_ones = score_scssf([1] * 12)
        all_fives = score_scssf([5] * 12)
        for sub in (
            all_ones.subscale_self_kindness,
            all_ones.subscale_self_judgment,
            all_ones.subscale_common_humanity,
            all_ones.subscale_isolation,
            all_ones.subscale_mindfulness,
            all_ones.subscale_over_identification,
        ):
            assert sub == 2
        for sub in (
            all_fives.subscale_self_kindness,
            all_fives.subscale_self_judgment,
            all_fives.subscale_common_humanity,
            all_fives.subscale_isolation,
            all_fives.subscale_mindfulness,
            all_fives.subscale_over_identification,
        ):
            assert sub == 10

    def test_subscale_bumps_do_not_leak_across(self) -> None:
        """Bumping an SK item affects SK only — not SJ / CH / I / M / OI."""
        baseline = score_scssf([3] * 12)
        # Item 2 (SK) bump.
        items = [3] * 12
        items[1] = 5
        result = score_scssf(items)
        assert result.subscale_self_kindness == baseline.subscale_self_kindness + 2
        assert result.subscale_self_judgment == baseline.subscale_self_judgment
        assert result.subscale_common_humanity == baseline.subscale_common_humanity
        assert result.subscale_isolation == baseline.subscale_isolation
        assert result.subscale_mindfulness == baseline.subscale_mindfulness
        assert (
            result.subscale_over_identification
            == baseline.subscale_over_identification
        )


class TestItemCountValidation:
    """Reject inputs with the wrong number of items."""

    def test_eleven_items_raises(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 12 items"):
            score_scssf([3] * 11)

    def test_thirteen_items_raises(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 12 items"):
            score_scssf([3] * 13)

    def test_empty_items_raises(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 12 items"):
            score_scssf([])

    def test_twenty_items_raises(self) -> None:
        # TAS-20-shaped input rejected — dispatch / scorer contract
        # not confused between sibling subscale-bearing instruments.
        with pytest.raises(InvalidResponseError, match="exactly 12 items"):
            score_scssf([3] * 20)

    def test_ten_items_raises(self) -> None:
        # ERQ-shaped input rejected.
        with pytest.raises(InvalidResponseError, match="exactly 12 items"):
            score_scssf([3] * 10)

    def test_count_error_names_received_count(self) -> None:
        with pytest.raises(InvalidResponseError, match="got 5"):
            score_scssf([3] * 5)


class TestItemRangeValidation:
    """Reject items outside the 1-5 Likert envelope."""

    def test_zero_rejects_below_floor(self) -> None:
        with pytest.raises(InvalidResponseError, match=r"out of range"):
            score_scssf([0] + [3] * 11)

    def test_six_rejects_above_ceiling(self) -> None:
        with pytest.raises(InvalidResponseError, match=r"out of range"):
            score_scssf([6] + [3] * 11)

    def test_negative_rejects(self) -> None:
        with pytest.raises(InvalidResponseError, match=r"out of range"):
            score_scssf([-1] + [3] * 11)

    def test_seven_rejects(self) -> None:
        # 7 is valid for ERQ but NOT for SCS-SF — different envelopes.
        with pytest.raises(InvalidResponseError, match=r"out of range"):
            score_scssf([7] + [3] * 11)

    def test_one_accepts_floor(self) -> None:
        score_scssf([1] * 12)

    def test_five_accepts_ceiling(self) -> None:
        score_scssf([5] * 12)

    def test_range_error_names_item_position(self) -> None:
        with pytest.raises(InvalidResponseError, match="item 3"):
            score_scssf([3, 3, 99, 3, 3, 3, 3, 3, 3, 3, 3, 3])

    def test_mid_sequence_out_of_range_detected(self) -> None:
        items = [3] * 12
        items[11] = 0
        with pytest.raises(InvalidResponseError, match="item 12"):
            score_scssf(items)


class TestBoolRejection:
    """Reject bool values even though Python bool is an int subclass."""

    def test_true_rejects(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_scssf([True] + [3] * 11)

    def test_false_rejects(self) -> None:
        # False == 0; bool check must fire before range check.
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_scssf([False] + [3] * 11)

    def test_mixed_bool_in_sequence_rejects(self) -> None:
        items = [3] * 12
        items[5] = True  # type: ignore[assignment]
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_scssf(items)


class TestResultShape:
    """Pin the ScsSfResult dataclass contract."""

    def test_result_is_scssf_result(self) -> None:
        assert isinstance(score_scssf([3] * 12), ScsSfResult)

    def test_result_has_total_field(self) -> None:
        assert hasattr(score_scssf([3] * 12), "total")

    def test_result_has_all_six_subscales(self) -> None:
        result = score_scssf([3] * 12)
        for name in (
            "subscale_self_kindness",
            "subscale_self_judgment",
            "subscale_common_humanity",
            "subscale_isolation",
            "subscale_mindfulness",
            "subscale_over_identification",
        ):
            assert hasattr(result, name)

    def test_result_has_items_field(self) -> None:
        assert hasattr(score_scssf([3] * 12), "items")

    def test_instrument_version_pinned_on_result(self) -> None:
        result = score_scssf([3] * 12)
        assert result.instrument_version == "scssf-1.0.0"

    def test_result_is_frozen(self) -> None:
        result = score_scssf([3] * 12)
        with pytest.raises(Exception):  # FrozenInstanceError
            result.total = 99  # type: ignore[misc]

    def test_items_field_is_tuple(self) -> None:
        assert isinstance(score_scssf([3] * 12).items, tuple)

    def test_items_preserves_input_verbatim(self) -> None:
        """Audit invariant: ``items`` holds the RAW pre-flip values,
        NOT the post-flip.  A clinician reviewing the record sees
        exactly what the patient ticked.
        """
        raw = [5, 3, 3, 5, 3, 3, 3, 5, 5, 3, 5, 5]
        result = score_scssf(raw)
        assert result.items == tuple(raw)
        # Spot-check: item 11 (raw=5, reverse) is stored as 5,
        # not as post-flipped 1.
        assert result.items[10] == 5

    def test_no_severity_field(self) -> None:
        # Continuous-sentinel: no severity at the scorer level.
        result = score_scssf([3] * 12)
        assert not hasattr(result, "severity")
        assert not hasattr(result, "band")

    def test_no_requires_t3_field(self) -> None:
        result = score_scssf([3] * 12)
        assert not hasattr(result, "requires_t3")

    def test_no_cutoff_used_field(self) -> None:
        result = score_scssf([3] * 12)
        assert not hasattr(result, "cutoff_used")


class TestClinicalVignettes:
    """Plausible clinical response patterns preserved end-to-end."""

    def test_high_self_compassion_protective_profile(self) -> None:
        """Positive items at 5, negative items at 1 → max total 60
        with high SK / CH / M subscales (10 each) and low SJ / I /
        OI subscales (2 each).  The protective profile — Aldao
        2010, MacBeth 2012 — correlates with lower depression /
        anxiety / stress."""
        items = [0] * 12
        for pos in SCSSF_SUBSCALES["self_kindness"]:
            items[pos - 1] = 5
        for pos in SCSSF_SUBSCALES["common_humanity"]:
            items[pos - 1] = 5
        for pos in SCSSF_SUBSCALES["mindfulness"]:
            items[pos - 1] = 5
        for pos in SCSSF_REVERSE_ITEMS:
            items[pos - 1] = 1
        result = score_scssf(items)
        assert result.total == 60
        assert result.subscale_self_kindness == 10
        assert result.subscale_common_humanity == 10
        assert result.subscale_mindfulness == 10
        assert result.subscale_self_judgment == 2
        assert result.subscale_isolation == 2
        assert result.subscale_over_identification == 2

    def test_low_self_compassion_relapse_risk_profile(self) -> None:
        """Positive items at 1, negative items at 5 → min total 12
        with high SJ / I / OI subscales (10 each) and low SK / CH /
        M subscales (2 each).  The relapse-risk profile — Tangney
        2011, Brooks 2012 — identified for compassion-focused
        routing in the intervention layer."""
        items = [0] * 12
        for pos in SCSSF_SUBSCALES["self_kindness"]:
            items[pos - 1] = 1
        for pos in SCSSF_SUBSCALES["common_humanity"]:
            items[pos - 1] = 1
        for pos in SCSSF_SUBSCALES["mindfulness"]:
            items[pos - 1] = 1
        for pos in SCSSF_REVERSE_ITEMS:
            items[pos - 1] = 5
        result = score_scssf(items)
        assert result.total == 12
        assert result.subscale_self_kindness == 2
        assert result.subscale_common_humanity == 2
        assert result.subscale_mindfulness == 2
        assert result.subscale_self_judgment == 10
        assert result.subscale_isolation == 10
        assert result.subscale_over_identification == 10

    def test_high_functioning_but_miserable_profile(self) -> None:
        """High SK AND high SJ — positive self-beliefs coexisting
        with harsh self-criticism.  This dyad imbalance is what
        CFT specifically targets; the 6-subscale wire exposure is
        what lets the clinician read it directly.  If subscales
        were post-flipped, this profile would collapse to "medium"
        on every subscale and the clinical pattern would be
        invisible."""
        items = [3] * 12
        # Self-Kindness (items 2, 6) — high.
        items[1] = 5
        items[5] = 5
        # Self-Judgment (items 11, 12) — also high.
        items[10] = 5
        items[11] = 5
        result = score_scssf(items)
        assert result.subscale_self_kindness == 10
        assert result.subscale_self_judgment == 10  # both high (RAW)
        # Total pulls DOWN because reverse-flipping SJ pulls out the
        # high SJ endorsement → (SK at 5 + SJ reverse at 1).
        #   Item 2 = 5, Item 6 = 5         → SK 10
        #   Item 11 raw=5 flip=1, Item 12 raw=5 flip=1 → SJ flipped 2
        #   Other 8 items at 3 (4 positive stay, 4 reverse flip 3→3).
        # Total: 5+5 (SK) + 1+1 (SJ flip) + 8×3 (others) = 10 + 2 + 24 = 36.
        assert result.total == 36

    def test_midline_neutral_profile(self) -> None:
        """All-3s neutral → every subscale at 6, total at 36.
        Useful baseline for clinical comparison."""
        result = score_scssf([3] * 12)
        assert result.total == 36
        assert result.subscale_self_kindness == 6
        assert result.subscale_self_judgment == 6
        assert result.subscale_common_humanity == 6
        assert result.subscale_isolation == 6
        assert result.subscale_mindfulness == 6
        assert result.subscale_over_identification == 6

    def test_acquiescence_pattern_detected_via_subscale_inconsistency(
        self,
    ) -> None:
        """All-5s → SK=10, CH=10, M=10, SJ=10, I=10, OI=10.
        Clinically impossible dyad (endorsing both self-kindness
        AND self-judgment at maximum).  Total collapses to 36
        (midline) despite every subscale at 10 — a pattern the
        clinician-UI layer can flag as acquiescence bias.  This
        is a product of the balanced positive/negative-item
        design in Raes 2011; the subscale-RAW exposure makes the
        bias visible to the clinician, where a post-flipped
        subscale report would hide it (everything 6/10)."""
        result = score_scssf([5] * 12)
        assert result.total == 36  # acquiescence cancels
        assert result.subscale_self_kindness == 10
        assert result.subscale_self_judgment == 10
        assert result.subscale_common_humanity == 10
        assert result.subscale_isolation == 10
        assert result.subscale_mindfulness == 10
        assert result.subscale_over_identification == 10


class TestNoSafetyRouting:
    """SCS-SF has no safety item — nothing ever routes to T3/T4."""

    def test_minimum_total_emits_no_requires_t3(self) -> None:
        """Even floor total does not carry a safety-escalation bit."""
        items = [0] * 12
        for pos in SCSSF_SUBSCALES["self_kindness"]:
            items[pos - 1] = 1
        for pos in SCSSF_SUBSCALES["common_humanity"]:
            items[pos - 1] = 1
        for pos in SCSSF_SUBSCALES["mindfulness"]:
            items[pos - 1] = 1
        for pos in SCSSF_REVERSE_ITEMS:
            items[pos - 1] = 5
        result = score_scssf(items)
        assert not hasattr(result, "requires_t3")
        assert not hasattr(result, "triggering_items")

    def test_all_fives_emits_no_requires_t3(self) -> None:
        result = score_scssf([5] * 12)
        assert not hasattr(result, "requires_t3")

    def test_no_triggering_items_field(self) -> None:
        result = score_scssf([3] * 12)
        assert not hasattr(result, "triggering_items")

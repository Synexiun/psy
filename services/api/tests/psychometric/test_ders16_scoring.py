"""DERS-16 scoring tests — Bjureberg 2016.

Four load-bearing correctness properties for the 16-item DERS-16:

1. **No severity bands emitted.**  Bjureberg 2016 published no banded
   thresholds; downstream literature (Fowler 2014, Hallion 2018) proposes
   sample-specific cutoffs that are not cross-calibrated.  Per CLAUDE.md
   "don't hand-roll severity thresholds", the scorer ships as a
   continuous dimensional measure — the result dataclass deliberately
   omits the ``severity`` / ``cutoff_used`` / ``positive_screen`` fields.
   The router emits ``severity="continuous"`` as a sentinel (uniform
   with Craving VAS / PACS).
2. **Subscale boundaries map INTERLEAVED items with ASYMMETRIC ranges.**
   Unlike OCI-R's symmetric 6×3 grid, DERS-16's subscales have
   different item counts per Bjureberg 2016 Table 2:
     - nonacceptance = (9, 10, 13)      range 3-15
     - goals = (3, 7, 15)               range 3-15
     - impulse = (4, 8, 11)             range 3-15
     - strategies = (5, 6, 12, 14, 16)  range 5-25  ← widest
     - clarity = (1, 2)                 range 2-10  ← narrowest
   Each subscale test endorses only those positions and verifies the
   other four subscales stay at their minimum.  A refactor that rotated
   subscale rows or shifted an item (e.g. item 16 from strategies to
   clarity) would break the DBT skill-module routing silently.
3. **Exactly 16 items, each 1-5 Likert.**  Minimum 16 (not 0) because
   the lowest Likert response is 1 ("almost never"), not 0 — same floor
   semantic as K10 / K6 / AAQ-II.
4. **No safety routing.**  DERS-16 has no direct suicidality item.
   Items 4 and 8 ("out of control") probe impulse-control loss but not
   acute intent; the scorer must not expose anything the router could
   mistake for a T3 trigger.

Coverage strategy:
- Pin the 5-subscale map with asymmetric item counts.
- Single-subscale endorsement tests isolating the interleaved positions.
- Invariant: five subscale sums equal the total.
- Item-count and item-range validation (1-5 Likert).
- Bool rejection.
- Clinical vignettes — impulse-dominant (BPD-like), strategies-dominant
  (depressive ruminative), clarity-dominant (alexithymic) presentations
  that drive DBT skill-module selection.
- No severity / cutoff / safety fields.
"""

from __future__ import annotations

import pytest

from discipline.psychometric.scoring.ders16 import (
    DERS16_SUBSCALES,
    INSTRUMENT_VERSION,
    ITEM_COUNT,
    ITEM_MAX,
    ITEM_MIN,
    Ders16Result,
    InvalidResponseError,
    score_ders16,
)


def _baseline() -> list[int]:
    """Return a 16-item list at the Likert floor (1 = 'almost never').

    Uniform with K10 / K6 / AAQ-II — DERS-16's minimum is 16, not 0,
    because item floor is 1.
    """
    return [ITEM_MIN] * ITEM_COUNT


def _endorse_at(positions_1: list[int], level: int = ITEM_MAX) -> list[int]:
    """Build a 16-item list with the given 1-indexed positions set to
    ``level`` and the rest at the floor (1 = "almost never").

    Used to isolate subscale-specific endorsements so subscale-boundary
    tests don't accidentally leak responses across the interleaved
    subscale positions.
    """
    if not (ITEM_MIN <= level <= ITEM_MAX):
        raise ValueError(f"level must be in [{ITEM_MIN}, {ITEM_MAX}]")
    items = _baseline()
    for pos in positions_1:
        items[pos - 1] = level
    return items


class TestConstants:
    """Pin published constants so a drift from Bjureberg 2016 is caught."""

    def test_item_count_is_sixteen(self) -> None:
        assert ITEM_COUNT == 16

    def test_item_range_is_one_to_five(self) -> None:
        """Bjureberg 2016 §Method — 1-5 Likert ('Almost never' to
        'Almost always').  Item floor is 1, not 0 — different from
        PHQ-9 / GAD-7 (0-3), matches K10 / K6 / AAQ-II (1-5 / 1-7)."""
        assert ITEM_MIN == 1
        assert ITEM_MAX == 5

    def test_instrument_version_pinned(self) -> None:
        assert INSTRUMENT_VERSION == "ders16-1.0.0"

    def test_subscales_match_bjureberg_2016_table_2(self) -> None:
        """Five subscales per Bjureberg 2016 Table 2, 1-indexed
        positions.  Pinned verbatim from the paper — a refactor that
        rotated rows or reassigned items would break the validated
        confirmatory-factor structure and break DBT skill-module
        routing silently."""
        assert DERS16_SUBSCALES == {
            "nonacceptance": (9, 10, 13),
            "goals": (3, 7, 15),
            "impulse": (4, 8, 11),
            "strategies": (5, 6, 12, 14, 16),
            "clarity": (1, 2),
        }

    def test_subscale_item_counts_per_paper(self) -> None:
        """Asymmetric item counts: 3/3/3/5/2 summing to 16.  Important
        because downstream subscale-comparison logic must divide by
        item count, not compare raw totals."""
        assert len(DERS16_SUBSCALES["nonacceptance"]) == 3
        assert len(DERS16_SUBSCALES["goals"]) == 3
        assert len(DERS16_SUBSCALES["impulse"]) == 3
        assert len(DERS16_SUBSCALES["strategies"]) == 5
        assert len(DERS16_SUBSCALES["clarity"]) == 2

    def test_subscales_cover_all_sixteen_items_exactly_once(self) -> None:
        """Invariant: every 1-16 position appears in exactly one
        subscale.  A refactor that double-counted (put item 7 in
        both goals and strategies) or dropped an item would break
        the total-equals-sum-of-subscales invariant."""
        all_positions = [
            pos for positions in DERS16_SUBSCALES.values() for pos in positions
        ]
        assert sorted(all_positions) == list(range(1, ITEM_COUNT + 1))


class TestTotalCorrectness:
    """Straight 16-80 sum (no reverse-coding — Bjureberg 2016 pruned
    all awareness-subscale reverse-keyed items)."""

    def test_all_floor_is_sixteen(self) -> None:
        """Minimum total is 16, not 0 — 16 items × floor 1."""
        result = score_ders16(_baseline())
        assert result.total == 16

    def test_all_ceiling_is_eighty(self) -> None:
        """Maximum total is 80 — 16 items × ceiling 5."""
        result = score_ders16([ITEM_MAX] * ITEM_COUNT)
        assert result.total == 80

    def test_mixed_sum(self) -> None:
        """Arbitrary mix — verifies the total is a plain sum."""
        items = [1, 2, 3, 4, 5, 1, 2, 3, 4, 5, 1, 2, 3, 4, 5, 1]
        result = score_ders16(items)
        assert result.total == sum(items)

    def test_all_threes_is_forty_eight(self) -> None:
        """All items at the midpoint (3 = 'about half the time') →
        total 48, a plausible 'moderate dysregulation' presentation."""
        result = score_ders16([3] * ITEM_COUNT)
        assert result.total == 48

    def test_single_item_change_propagates(self) -> None:
        """Moving one item from 1 → 5 changes total by 4.  Pins that
        the sum is element-wise, not something clever like an average
        or weighted-combine."""
        baseline = score_ders16(_baseline())
        items = _baseline()
        items[0] = 5
        bumped = score_ders16(items)
        assert bumped.total == baseline.total + 4


class TestSubscaleBoundaries:
    """Each subscale must map to its correct INTERLEAVED 1-indexed
    positions with its correct item count.  Asymmetric design (3/3/3/5/2)
    means subscale totals have different ranges — downstream comparison
    logic must normalize by item count before comparing subscales.

    Every subscale test endorses exactly its positions at ceiling and
    verifies the other four subscales stay at their floor.
    """

    def test_nonacceptance_items_nine_ten_thirteen(self) -> None:
        """Endorse only items 9, 10, 13 at max → nonacceptance = 15
        (3×5), others at floor."""
        result = score_ders16(_endorse_at([9, 10, 13]))
        assert result.subscale_nonacceptance == 15
        assert result.subscale_goals == 3  # 3 items at floor 1
        assert result.subscale_impulse == 3
        assert result.subscale_strategies == 5  # 5 items at floor 1
        assert result.subscale_clarity == 2  # 2 items at floor 1

    def test_goals_items_three_seven_fifteen(self) -> None:
        """Endorse only items 3, 7, 15 → goals = 15, others at floor.
        Goals subscale measures goal-directed-behavior-difficulty-when-
        upset — clinically maps to DBT's emotion-surf and
        mindfulness-of-current-activity skills."""
        result = score_ders16(_endorse_at([3, 7, 15]))
        assert result.subscale_nonacceptance == 3
        assert result.subscale_goals == 15
        assert result.subscale_impulse == 3
        assert result.subscale_strategies == 5
        assert result.subscale_clarity == 2

    def test_impulse_items_four_eight_eleven(self) -> None:
        """Endorse only items 4, 8, 11 → impulse = 15, others at floor.
        Impulse subscale measures behavior-control-loss-when-upset —
        clinically maps to DBT's distress-tolerance skills (TIP, STOP,
        self-soothe) and is the strongest BPD-pattern signal."""
        result = score_ders16(_endorse_at([4, 8, 11]))
        assert result.subscale_nonacceptance == 3
        assert result.subscale_goals == 3
        assert result.subscale_impulse == 15
        assert result.subscale_strategies == 5
        assert result.subscale_clarity == 2

    def test_strategies_items_five_six_twelve_fourteen_sixteen(self) -> None:
        """Endorse only items 5, 6, 12, 14, 16 → strategies = 25
        (5×5 — the WIDEST subscale range), others at floor.  Strategies
        subscale measures regulation-hopelessness — clinically maps to
        DBT's cope-ahead, opposite-action, and mastery-activity skills,
        and is a strong depressive-rumination signal."""
        result = score_ders16(_endorse_at([5, 6, 12, 14, 16]))
        assert result.subscale_nonacceptance == 3
        assert result.subscale_goals == 3
        assert result.subscale_impulse == 3
        assert result.subscale_strategies == 25
        assert result.subscale_clarity == 2

    def test_clarity_items_one_two(self) -> None:
        """Endorse only items 1, 2 → clarity = 10 (2×5 — the NARROWEST
        subscale range), others at floor.  Clarity subscale measures
        emotional-labeling-difficulty — clinically maps to DBT's
        observe/describe skills and is the alexithymic-pattern signal."""
        result = score_ders16(_endorse_at([1, 2]))
        assert result.subscale_nonacceptance == 3
        assert result.subscale_goals == 3
        assert result.subscale_impulse == 3
        assert result.subscale_strategies == 5
        assert result.subscale_clarity == 10

    def test_subscale_sum_equals_total(self) -> None:
        """The five subscales sum to the total.  A refactor that
        double-counted an item (put item 7 in both goals and
        strategies) or dropped an item (left item 16 out of all
        subscales) would break this invariant."""
        items = [1, 2, 3, 4, 5, 1, 2, 3, 4, 5, 1, 2, 3, 4, 5, 1]
        result = score_ders16(items)
        subscale_sum = (
            result.subscale_nonacceptance
            + result.subscale_goals
            + result.subscale_impulse
            + result.subscale_strategies
            + result.subscale_clarity
        )
        assert subscale_sum == result.total

    def test_subscale_ranges_at_floor(self) -> None:
        """All items at floor — each subscale equals its item count
        (item count × 1).  Pins the asymmetric-range design."""
        result = score_ders16(_baseline())
        assert result.subscale_nonacceptance == 3  # 3 items × 1
        assert result.subscale_goals == 3
        assert result.subscale_impulse == 3
        assert result.subscale_strategies == 5  # 5 items × 1
        assert result.subscale_clarity == 2  # 2 items × 1

    def test_subscale_ranges_at_ceiling(self) -> None:
        """All items at ceiling — each subscale equals item count × 5.
        Pins the asymmetric maxima: 15/15/15/25/10."""
        result = score_ders16([ITEM_MAX] * ITEM_COUNT)
        assert result.subscale_nonacceptance == 15  # 3 × 5
        assert result.subscale_goals == 15
        assert result.subscale_impulse == 15
        assert result.subscale_strategies == 25  # 5 × 5
        assert result.subscale_clarity == 10  # 2 × 5


class TestItemCountValidation:
    """Exactly 16 items required.  Misroutes from neighboring
    instruments (PHQ-9 at 9, GAD-7 at 7, AAQ-II at 7, WSAS at 5,
    K10 at 10, ASRS-6 at 6, OCI-R at 18) must fail loudly."""

    def test_rejects_fifteen_items(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 16 items"):
            score_ders16([3] * 15)

    def test_rejects_seventeen_items(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 16 items"):
            score_ders16([3] * 17)

    def test_rejects_empty(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 16 items"):
            score_ders16([])

    def test_rejects_phq9_count(self) -> None:
        """9-item payload from PHQ-9 misroute should fail cleanly."""
        with pytest.raises(InvalidResponseError, match="exactly 16 items"):
            score_ders16([3] * 9)

    def test_rejects_aaq2_count(self) -> None:
        """7-item payload from AAQ-II misroute should fail cleanly.
        AAQ-II and DERS-16 are both process-target instruments, so
        a dispatch-level bug that routed AAQ-II items to DERS-16
        must surface — it would otherwise silently score a 7-item
        ACT payload as a truncated DERS-16."""
        with pytest.raises(InvalidResponseError, match="exactly 16 items"):
            score_ders16([3] * 7)

    def test_rejects_wsas_count(self) -> None:
        """5-item payload from WSAS misroute should fail cleanly."""
        with pytest.raises(InvalidResponseError, match="exactly 16 items"):
            score_ders16([3] * 5)

    def test_rejects_ocir_count(self) -> None:
        """18-item payload from OCI-R misroute should fail cleanly.
        OCI-R and DERS-16 are the two largest subscale instruments
        in the package — a dispatch swap is the most plausible
        mis-routing risk."""
        with pytest.raises(InvalidResponseError, match="exactly 16 items"):
            score_ders16([3] * 18)


class TestItemRangeValidation:
    """Items must be in [1, 5]."""

    @pytest.mark.parametrize("bad_value", [-1, 0, 6, 7, 100, 255])
    def test_rejects_out_of_range(self, bad_value: int) -> None:
        items = _baseline()
        items[9] = bad_value
        with pytest.raises(InvalidResponseError, match="out of range"):
            score_ders16(items)

    def test_rejects_zero_item(self) -> None:
        """0 is below the Likert floor — important to reject because
        0 is the floor for PHQ-9/GAD-7/OCI-R/K10 items.  A client that
        submitted a 0-4 payload (from a PHQ-9-like UI) instead of a
        1-5 payload should fail loudly, not silently under-score."""
        items = _baseline()
        items[0] = 0
        with pytest.raises(InvalidResponseError, match="out of range"):
            score_ders16(items)

    def test_rejects_six_item(self) -> None:
        """6 is above the Likert ceiling.  Important to reject because
        6 is a valid item for AAQ-II (1-7 range) — a client that
        submitted AAQ-II-like items into a DERS-16 dispatch would
        fail here, not silently over-score."""
        items = _baseline()
        items[0] = 6
        with pytest.raises(InvalidResponseError, match="out of range"):
            score_ders16(items)

    def test_error_names_one_indexed_item(self) -> None:
        """Error messages use 1-indexed item numbers to match the
        DERS-16 instrument document a clinician would reference."""
        items = _baseline()
        items[15] = 99  # item 16 (last item, strategies subscale)
        with pytest.raises(InvalidResponseError, match="DERS-16 item 16"):
            score_ders16(items)

    def test_rejects_string_item(self) -> None:
        items = _baseline()
        items[0] = "4"  # type: ignore[call-overload]
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_ders16(items)

    def test_rejects_float_item(self) -> None:
        items = _baseline()
        items[0] = 4.0  # type: ignore[call-overload]
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_ders16(items)

    def test_rejects_none_item(self) -> None:
        items = _baseline()
        items[0] = None  # type: ignore[call-overload]
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_ders16(items)


class TestBoolRejection:
    """Bool items rejected even though True/False map to valid 1/0.
    Rationale: uniform wire contract across the psychometric package
    (same policy as MDQ, PCL-5, PC-PTSD-5, ISI, OCI-R, K10, K6, SDS,
    AAQ-II, WSAS, etc.).
    """

    def test_rejects_true_item(self) -> None:
        items = _baseline()
        items[0] = True  # type: ignore[call-overload]
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_ders16(items)

    def test_rejects_false_item(self) -> None:
        items = _baseline()
        items[0] = False  # type: ignore[call-overload]
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_ders16(items)

    def test_rejects_true_at_last_position(self) -> None:
        """Guard against an off-by-one in the bool check that only
        catches position 0.  Item 16 is the last item — a boolean
        reaching it should still be rejected."""
        items = _baseline()
        items[15] = True  # type: ignore[call-overload]
        with pytest.raises(InvalidResponseError, match="DERS-16 item 16"):
            score_ders16(items)

    def test_rejects_mixed_bool_and_int(self) -> None:
        """Only one bool in an otherwise-valid payload is enough to
        reject — validates that bool rejection is per-item, not
        whole-payload."""
        items = _baseline()
        items[5] = True  # type: ignore[call-overload]
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_ders16(items)


class TestResultShape:
    """Ders16Result carries the fields the router envelope needs and
    deliberately OMITS fields that would falsely imply banded severity,
    a cutoff decision, or a safety trigger.
    """

    def test_result_is_frozen(self) -> None:
        result = score_ders16(_baseline())
        with pytest.raises(Exception):  # FrozenInstanceError subclass
            result.total = 99  # type: ignore[misc]

    def test_items_are_tuple(self) -> None:
        """Tuple so Ders16Result is hashable and the stored repository
        record is immutable."""
        items = [1, 2, 3, 4, 5, 1, 2, 3, 4, 5, 1, 2, 3, 4, 5, 1]
        result = score_ders16(items)
        assert isinstance(result.items, tuple)
        assert result.items == tuple(items)

    def test_result_echoes_instrument_version(self) -> None:
        result = score_ders16(_baseline())
        assert result.instrument_version == INSTRUMENT_VERSION

    def test_no_severity_field(self) -> None:
        """Bjureberg 2016 published no banded thresholds.  The scorer
        must NOT emit a ``severity`` field — the router attaches the
        ``"continuous"`` sentinel at the envelope layer (uniform with
        Craving VAS / PACS).  A scorer that hand-rolled bands would
        violate CLAUDE.md's 'don't hand-roll severity thresholds' rule."""
        result = score_ders16([ITEM_MAX] * ITEM_COUNT)
        assert not hasattr(result, "severity")

    def test_no_cutoff_used_field(self) -> None:
        """Continuous instrument — no cutoff shape.  The result must
        not expose a ``cutoff_used`` field because that is the wire
        marker for cutoff-envelope instruments (AAQ-II, ASRS-6, etc.),
        which DERS-16 is not.  A renderer that keyed off this field
        to display a positive-screen badge would over-fire."""
        result = score_ders16([ITEM_MAX] * ITEM_COUNT)
        assert not hasattr(result, "cutoff_used")

    def test_no_positive_screen_field(self) -> None:
        """Continuous instrument — no screen decision.  The result must
        not expose a ``positive_screen`` boolean because the instrument
        does not implement a binary decision gate."""
        result = score_ders16([ITEM_MAX] * ITEM_COUNT)
        assert not hasattr(result, "positive_screen")

    def test_no_requires_t3_field(self) -> None:
        """DERS-16 has no safety item.  The result dataclass deliberately
        omits requires_t3 so downstream routing cannot accidentally
        escalate a high-dysregulation patient into T3.  Acute ideation
        screening is PHQ-9 item 9 / C-SSRS, not DERS-16."""
        result = score_ders16([ITEM_MAX] * ITEM_COUNT)
        assert not hasattr(result, "requires_t3")

    def test_no_triggering_items_field(self) -> None:
        """DERS-16 has no safety items, so there is no ``triggering_items``
        list to surface on the envelope (unlike PHQ-9 which surfaces
        positive item 9 here)."""
        result = score_ders16([ITEM_MAX] * ITEM_COUNT)
        assert not hasattr(result, "triggering_items")

    def test_all_five_subscale_fields_present(self) -> None:
        """The 5-key subscale output is load-bearing for the router's
        subscales dict.  A refactor that dropped a subscale field would
        surface as missing wire keys, not a crash."""
        result = score_ders16(_baseline())
        assert hasattr(result, "subscale_nonacceptance")
        assert hasattr(result, "subscale_goals")
        assert hasattr(result, "subscale_impulse")
        assert hasattr(result, "subscale_strategies")
        assert hasattr(result, "subscale_clarity")

    def test_result_is_ders16_result_type(self) -> None:
        result = score_ders16(_baseline())
        assert isinstance(result, Ders16Result)

    def test_total_is_int(self) -> None:
        result = score_ders16(_baseline())
        assert isinstance(result.total, int)
        assert not isinstance(result.total, bool)


class TestClinicalVignettes:
    """Named patterns a clinician would recognize.  Subscale dominance
    drives DBT skill-module selection per Linehan 1993 — the intervention
    layer reads the 5-tuple profile (not just the aggregate total) to
    pick the skill-building tool variant matched to the weakest
    regulatory capacity.
    """

    def test_impulse_dominant_presentation(self) -> None:
        """Classic BPD-pattern dysregulation — impulse subscale elevated,
        others modest.  Clinically indicates DBT distress-tolerance
        skills (TIP, STOP, self-soothe, radical acceptance) as the
        first-line intervention tool variant."""
        # Impulse (4, 8, 11) at 5; others at floor 1
        items = _endorse_at([4, 8, 11], level=5)
        result = score_ders16(items)
        assert result.subscale_impulse == 15  # 3 × 5
        assert result.subscale_impulse > result.subscale_nonacceptance
        assert result.subscale_impulse > result.subscale_goals
        # Note: strategies subscale at floor = 5, impulse at max = 15
        assert result.subscale_impulse > result.subscale_strategies
        assert result.subscale_impulse > result.subscale_clarity

    def test_strategies_dominant_presentation(self) -> None:
        """Depressive-ruminative pattern — strategies subscale elevated
        (regulation-hopelessness).  Clinically indicates DBT's cope-ahead,
        opposite-action, and mastery-activity skills; also signals
        behavioral-activation CBT as adjunctive."""
        # Strategies (5, 6, 12, 14, 16) at 5; others at floor 1
        items = _endorse_at([5, 6, 12, 14, 16], level=5)
        result = score_ders16(items)
        assert result.subscale_strategies == 25  # 5 × 5 — widest range
        assert result.subscale_strategies > result.subscale_nonacceptance
        assert result.subscale_strategies > result.subscale_goals
        assert result.subscale_strategies > result.subscale_impulse
        assert result.subscale_strategies > result.subscale_clarity

    def test_clarity_dominant_presentation(self) -> None:
        """Alexithymic pattern — clarity subscale elevated (difficulty
        labeling emotions).  Clinically indicates DBT's observe/describe
        mindfulness skills and emotion-naming interoceptive work."""
        # Clarity (1, 2) at 5; others at floor 1
        items = _endorse_at([1, 2], level=5)
        result = score_ders16(items)
        assert result.subscale_clarity == 10  # 2 × 5 — narrowest range
        # Clarity max is 10, impulse/goals/nonacceptance floor is 3,
        # strategies floor is 5.  Normalize by item count to compare:
        # clarity per-item = 5, impulse/goals/nonacceptance per-item = 1,
        # strategies per-item = 1.
        assert result.subscale_clarity > result.subscale_nonacceptance
        assert result.subscale_clarity > result.subscale_goals
        assert result.subscale_clarity > result.subscale_impulse
        assert result.subscale_clarity > result.subscale_strategies

    def test_nonacceptance_dominant_presentation(self) -> None:
        """Self-critical / shame-laden pattern — nonacceptance subscale
        elevated.  Clinically indicates DBT's self-compassion /
        non-judgmental-stance skills; common in trauma-exposed
        populations where PCL-5 co-elevates."""
        items = _endorse_at([9, 10, 13], level=5)
        result = score_ders16(items)
        assert result.subscale_nonacceptance == 15
        assert result.subscale_nonacceptance > result.subscale_goals
        assert result.subscale_nonacceptance > result.subscale_impulse
        assert result.subscale_nonacceptance > result.subscale_strategies
        assert result.subscale_nonacceptance > result.subscale_clarity

    def test_goals_dominant_presentation(self) -> None:
        """Executive-function-interference pattern — goals subscale
        elevated.  Clinically indicates DBT's wise-mind /
        mindfulness-of-current-activity skills."""
        items = _endorse_at([3, 7, 15], level=5)
        result = score_ders16(items)
        assert result.subscale_goals == 15
        assert result.subscale_goals > result.subscale_nonacceptance
        assert result.subscale_goals > result.subscale_impulse
        assert result.subscale_goals > result.subscale_strategies
        assert result.subscale_goals > result.subscale_clarity

    def test_uniform_moderate_pattern(self) -> None:
        """Uniform moderate dysregulation across all subscales (all
        items at 3 = 'about half the time').  Common outcome-tracking
        baseline — clinically indicates broad DBT skill-curriculum
        rather than targeted module emphasis."""
        result = score_ders16([3] * ITEM_COUNT)
        assert result.total == 48
        # Each subscale at item_count × 3:
        assert result.subscale_nonacceptance == 9  # 3 × 3
        assert result.subscale_goals == 9
        assert result.subscale_impulse == 9
        assert result.subscale_strategies == 15  # 5 × 3
        assert result.subscale_clarity == 6  # 2 × 3

    def test_full_dysregulation_profile(self) -> None:
        """All 16 items endorsed at ceiling 5 → total 80, every subscale
        at max.  Defining case for outcome-tracking baseline in severe
        emotion-dysregulation presentations."""
        result = score_ders16([ITEM_MAX] * ITEM_COUNT)
        assert result.total == 80
        assert result.subscale_nonacceptance == 15  # 3 × 5
        assert result.subscale_goals == 15
        assert result.subscale_impulse == 15
        assert result.subscale_strategies == 25  # 5 × 5
        assert result.subscale_clarity == 10  # 2 × 5

    def test_minimum_dysregulation_profile(self) -> None:
        """All 16 items at floor 1 → total 16, every subscale at its
        minimum.  Healthy-baseline case — scorer must not over-fire
        a bands-adjacent field here."""
        result = score_ders16(_baseline())
        assert result.total == 16
        assert result.subscale_nonacceptance == 3
        assert result.subscale_goals == 3
        assert result.subscale_impulse == 3
        assert result.subscale_strategies == 5
        assert result.subscale_clarity == 2
        # Explicit re-assertion: no bands, no screen, no safety.
        assert not hasattr(result, "severity")
        assert not hasattr(result, "positive_screen")
        assert not hasattr(result, "requires_t3")


class TestNoSafetyRouting:
    """DERS-16 has no direct suicidality / self-harm item.  Items 4 and 8
    ("out of control") probe impulse-control loss, item 14 ("feel very
    bad about myself") probes self-critical affect, but none probe
    acute intent.  The scorer must not expose anything the router could
    mistake for a T3 trigger — acute-ideation screening routes through
    PHQ-9 item 9 / C-SSRS, not DERS-16.
    """

    def test_max_total_has_no_safety_field(self) -> None:
        result = score_ders16([ITEM_MAX] * ITEM_COUNT)
        assert not hasattr(result, "requires_t3")
        assert not hasattr(result, "t3_reason")
        assert not hasattr(result, "safety_item_positive")
        assert not hasattr(result, "triggering_items")

    def test_impulse_max_has_no_safety_field(self) -> None:
        """Even when the impulse subscale is maxed out (the one that
        probes 'out of control' and is the strongest BPD-pattern signal),
        the result carries no safety-routing fields.  A renderer that
        tried to key off impulse > threshold to escalate to T3 would
        over-fire and desensitize the safety queue."""
        result = score_ders16(_endorse_at([4, 8, 11], level=5))
        assert not hasattr(result, "requires_t3")
        assert not hasattr(result, "t3_reason")

    def test_self_critical_items_have_no_safety_field(self) -> None:
        """Items 9, 10, 13, 14 probe self-critical / shame affect.
        These superficially resemble hopelessness content but do NOT
        probe acute intent — the scorer must not escalate here."""
        # Endorse items 9, 10, 13, 14 at max
        result = score_ders16(_endorse_at([9, 10, 13, 14], level=5))
        assert not hasattr(result, "requires_t3")
        assert not hasattr(result, "t3_reason")

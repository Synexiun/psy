"""Tests for RSES scorer — Rosenberg 1965 Self-Esteem Scale.

RSES is a 10-item 0-3 Likert self-report measure of global
self-esteem.  Rosenberg 1965 Society and the Adolescent Self-
Image (Princeton University Press) — the most widely-used
psychological instrument (>100k citations).  Gray-Little 1997
IRT meta-analysis confirmed unidimensional factor structure;
Schmitt & Allik 2005 cross-national n = 16,998 confirmed
factorial invariance across 53 nations.

Scoring:
- 5 reverse-keyed items (2, 5, 6, 8, 9) — negatively worded.
- Total = sum of post-flip values, 0-30.
- Higher = more self-esteem.
- No published clinical cutpoints; severity = "continuous".
- ``items`` field preserves raw pre-flip per audit invariance.

No T3 — RSES measures self-esteem, not suicidality.  Item 9
"inclined to feel that I am a failure" is a self-concept item
per Rosenberg 1965 derivation, NOT ideation.  Acute-risk stays
on C-SSRS / PHQ-9 item 9.
"""

from __future__ import annotations

import pytest

from discipline.psychometric.scoring import rses
from discipline.psychometric.scoring.rses import (
    INSTRUMENT_VERSION,
    ITEM_COUNT,
    ITEM_MAX,
    ITEM_MIN,
    RSES_REVERSE_ITEMS,
    InvalidResponseError,
    RsesResult,
    score_rses,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


class TestConstants:
    """Pin the published structure of the Rosenberg 1965 RSES.

    Any change here is a clinical decision — Rosenberg 1965
    derivation / Gray-Little 1997 IRT / Schmitt & Allik 2005
    cross-cultural invariance.  NOT an implementation tweak.
    """

    def test_instrument_version(self) -> None:
        assert INSTRUMENT_VERSION == "rses-1.0.0"

    def test_item_count_is_ten(self) -> None:
        assert ITEM_COUNT == 10

    def test_item_min_is_zero(self) -> None:
        # Gray-Little 1997 §1 modern anchoring convention:
        # 0-3 scale ("strongly disagree" -> "strongly agree").
        assert ITEM_MIN == 0

    def test_item_max_is_three(self) -> None:
        assert ITEM_MAX == 3

    def test_reverse_items_per_rosenberg_1965(self) -> None:
        # Items 2, 5, 6, 8, 9 are negatively worded ("At times
        # I think I am no good at all", "I feel I do not have
        # much to be proud of", "I certainly feel useless at
        # times", "I wish I could have more respect for
        # myself", "All in all, I am inclined to feel that I
        # am a failure").  Changing this tuple invalidates
        # the Rosenberg 1965 factor-analytic derivation.
        assert RSES_REVERSE_ITEMS == (2, 5, 6, 8, 9)

    def test_five_reverse_items(self) -> None:
        # Balanced 5 reverse + 5 positive per Rosenberg 1965
        # derivation.  Method-effect reduction (Marsh 1996).
        assert len(RSES_REVERSE_ITEMS) == 5

    def test_reverse_items_within_bounds(self) -> None:
        for i in RSES_REVERSE_ITEMS:
            assert 1 <= i <= ITEM_COUNT

    def test_no_severity_thresholds_exported(self) -> None:
        # Rosenberg 1965 did not publish clinical cutpoints.
        # Schmitt & Allik 2005 cross-national means (M = 21.3,
        # SD = 5.5 on 0-30 scale) are descriptive, not clinical
        # bands.  A ``RSES_SEVERITY_THRESHOLDS`` constant would
        # violate CLAUDE.md (no hand-rolled bands).
        assert not hasattr(rses, "RSES_SEVERITY_THRESHOLDS")

    def test_no_subscales_exported(self) -> None:
        # Gray-Little 1997 IRT confirmed unidimensional
        # structure.  Tomas 1999 / Marsh 1996 two-factor
        # proposals are method-artifact (positive-negative
        # wording bias), not substantive subscales.
        assert not hasattr(rses, "RSES_SUBSCALES")

    def test_no_positive_cutoff_exported(self) -> None:
        # RSES is not a screen.
        assert not hasattr(rses, "RSES_POSITIVE_CUTOFF")

    def test_public_exports(self) -> None:
        assert set(rses.__all__) == {
            "INSTRUMENT_VERSION",
            "ITEM_COUNT",
            "ITEM_MAX",
            "ITEM_MIN",
            "InvalidResponseError",
            "RSES_REVERSE_ITEMS",
            "RsesResult",
            "Severity",
            "score_rses",
        }


# ---------------------------------------------------------------------------
# Total correctness — reverse-keying pinned
# ---------------------------------------------------------------------------


class TestTotalCorrectness:
    """Pin the reverse-keying arithmetic.  RSES inherits the
    PGSI / BRS / TAS-20 / PSWQ / LOT-R reverse-keying idiom —
    (ITEM_MIN + ITEM_MAX) - raw = 3 - raw applied only at the
    5 reverse positions."""

    def test_all_zeros_acquiescence_control(self) -> None:
        # Pure "strongly disagree" on all 10 items.  Raw = 0.
        # Post-flip: positively-keyed items (1, 3, 4, 7, 10)
        # stay 0; reverse-keyed items (2, 5, 6, 8, 9) flip to
        # 3.  Total = 5 * 0 + 5 * 3 = 15.
        result = score_rses([0] * 10)
        assert result.total == 15

    def test_all_threes_acquiescence_control(self) -> None:
        # Pure "strongly agree" on all 10 items.  Raw = 3.
        # Post-flip: positively-keyed items stay 3; reverse-
        # keyed items flip to 0.  Total = 5 * 3 + 5 * 0 = 15.
        # Pin: acquiescent-positive AND acquiescent-negative
        # response styles both produce the SAME total.  This is
        # the balanced-wording signature of a proper reverse-
        # keyed instrument and is the canonical method-effect
        # test (Marsh 1996).
        result = score_rses([3] * 10)
        assert result.total == 15

    def test_all_ones_middle_lower(self) -> None:
        # "Disagree" on all items.  Positively-keyed = 1,
        # reverse-keyed = 3 - 1 = 2.  Total = 5 * 1 + 5 * 2 = 15.
        # Note: a uniformly "disagreeing" respondent produces a
        # middling total on RSES because half the items are
        # reverse-keyed.
        result = score_rses([1] * 10)
        assert result.total == 15

    def test_all_twos_middle_upper(self) -> None:
        # "Agree" on all items.  Positively-keyed = 2, reverse-
        # keyed = 3 - 2 = 1.  Total = 5 * 2 + 5 * 1 = 15.
        result = score_rses([2] * 10)
        assert result.total == 15

    def test_maximum_self_esteem_pattern(self) -> None:
        # Maximum self-esteem: "strongly agree" on positive
        # items (1, 3, 4, 7, 10) and "strongly disagree" on
        # reverse items (2, 5, 6, 8, 9).  All post-flip = 3.
        # Total = 30.
        items = [3, 0, 3, 3, 0, 0, 3, 0, 0, 3]
        result = score_rses(items)
        assert result.total == 30

    def test_minimum_self_esteem_pattern(self) -> None:
        # Minimum self-esteem: "strongly disagree" on positive
        # items and "strongly agree" on reverse items.  All
        # post-flip = 0.  Total = 0.
        items = [0, 3, 0, 0, 3, 3, 0, 3, 3, 0]
        result = score_rses(items)
        assert result.total == 0

    def test_reverse_keying_applied_at_position_2(self) -> None:
        # Isolated test: only position 2 (reverse) is 3, rest 0.
        # Position 2 post-flip = 0.  Position 1 etc are 0.  Others
        # reverse positions (5, 6, 8, 9) are 0 raw -> 3 post-flip.
        # Total = 0 + 0 + 0 + 0 + 3 + 3 + 0 + 3 + 3 + 0 = 12.
        items = [0, 3, 0, 0, 0, 0, 0, 0, 0, 0]
        result = score_rses(items)
        assert result.total == 12

    def test_reverse_keying_not_applied_at_position_1(self) -> None:
        # Isolated test: only position 1 (positive-keyed) is 3,
        # rest 0.  Position 1 post-flip = 3.  Reverse positions
        # (2, 5, 6, 8, 9) all raw 0 -> 3 post-flip each.
        # Total = 3 + 3 + 0 + 0 + 3 + 3 + 0 + 3 + 3 + 0 = 18.
        items = [3, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        result = score_rses(items)
        assert result.total == 18

    def test_total_in_domain_across_exhaustive_search(self) -> None:
        # Spot-check: every configuration must produce total in
        # [0, 30].  Exhaustive search over 4^10 = 1,048,576 is
        # too slow; sample the extremes + several intermediate
        # profiles.
        for raw in (
            [0] * 10,
            [3] * 10,
            [3, 0, 3, 3, 0, 0, 3, 0, 0, 3],
            [0, 3, 0, 0, 3, 3, 0, 3, 3, 0],
            [1, 2, 1, 1, 2, 2, 1, 2, 2, 1],
            [2, 1, 2, 2, 1, 1, 2, 1, 1, 2],
        ):
            result = score_rses(raw)
            assert 0 <= result.total <= 30


# ---------------------------------------------------------------------------
# Reverse-keying direction — parametrized
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "position_1, raw, expected_post_flip",
    [
        # Positively-keyed positions: raw == post-flip.
        (1, 0, 0), (1, 1, 1), (1, 2, 2), (1, 3, 3),
        (3, 0, 0), (3, 1, 1), (3, 2, 2), (3, 3, 3),
        (4, 0, 0), (4, 1, 1), (4, 2, 2), (4, 3, 3),
        (7, 0, 0), (7, 1, 1), (7, 2, 2), (7, 3, 3),
        (10, 0, 0), (10, 1, 1), (10, 2, 2), (10, 3, 3),
        # Reverse-keyed positions: post-flip = 3 - raw.
        (2, 0, 3), (2, 1, 2), (2, 2, 1), (2, 3, 0),
        (5, 0, 3), (5, 1, 2), (5, 2, 1), (5, 3, 0),
        (6, 0, 3), (6, 1, 2), (6, 2, 1), (6, 3, 0),
        (8, 0, 3), (8, 1, 2), (8, 2, 1), (8, 3, 0),
        (9, 0, 3), (9, 1, 2), (9, 2, 1), (9, 3, 0),
    ],
)
def test_position_direction_mapping(
    position_1: int, raw: int, expected_post_flip: int
) -> None:
    """Pin the exact per-position, per-value post-flip
    mapping.  Set position to raw; fix all other positions
    such that their contributions are easy to subtract.

    Reference pattern: all other positions set to 0 (raw).
    Positively-keyed other positions contribute 0 each.
    Reverse-keyed other positions contribute 3 each.
    """
    items = [0] * 10
    items[position_1 - 1] = raw
    result = score_rses(items)

    # Baseline total with all items = 0: 5 * 0 + 5 * 3 = 15.
    # Perturbation effect at position_1:
    #   - If position_1 is positive-keyed, post-flip at raw
    #     minus 0 = raw.  Total = 15 + raw.
    #   - If position_1 is reverse-keyed, post-flip = 3 - raw,
    #     minus baseline 3 = -raw.  Total = 15 - raw.
    if position_1 in RSES_REVERSE_ITEMS:
        expected_total = 15 - raw
    else:
        expected_total = 15 + raw
    assert result.total == expected_total, (
        f"position {position_1} raw {raw}: expected total "
        f"{expected_total}, got {result.total}"
    )
    # Additional check: items field preserves raw pre-flip.
    assert result.items[position_1 - 1] == raw
    # Indirect pin of post-flip direction:
    if position_1 in RSES_REVERSE_ITEMS:
        # raw 3 -> post-flip 0, raw 0 -> post-flip 3.
        assert expected_post_flip == ITEM_MAX - raw
    else:
        assert expected_post_flip == raw


# ---------------------------------------------------------------------------
# Item-count validation
# ---------------------------------------------------------------------------


class TestItemCountValidation:
    def test_nine_items_rejected(self) -> None:
        # Trap: someone confuses RSES (10) with PHQ-9 (9).
        with pytest.raises(InvalidResponseError, match="exactly 10"):
            score_rses([0] * 9)

    def test_eleven_items_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 10"):
            score_rses([0] * 11)

    def test_zero_items_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 10"):
            score_rses([])

    def test_five_items_rejected(self) -> None:
        # Trap: someone submits only the 5 positive items or 5
        # reverse items.
        with pytest.raises(InvalidResponseError, match="exactly 10"):
            score_rses([0] * 5)

    def test_twenty_items_rejected(self) -> None:
        # Trap: someone doubles up thinking RSES is a 20-item
        # scale (confusing with PCL-5 / TAS-20).
        with pytest.raises(InvalidResponseError, match="exactly 10"):
            score_rses([0] * 20)


# ---------------------------------------------------------------------------
# Item-range validation — strict 0-3 Likert
# ---------------------------------------------------------------------------


class TestItemRangeValidation:
    def test_four_rejected(self) -> None:
        # Trap: someone uses the 1-4 Likert variant on a 0-3
        # scorer.  Must fail loud.
        with pytest.raises(InvalidResponseError, match="0-3"):
            score_rses([4, 0, 0, 0, 0, 0, 0, 0, 0, 0])

    def test_negative_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="0-3"):
            score_rses([-1, 0, 0, 0, 0, 0, 0, 0, 0, 0])

    def test_large_positive_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="0-3"):
            score_rses([99, 0, 0, 0, 0, 0, 0, 0, 0, 0])

    def test_range_violation_reports_correct_index(self) -> None:
        # Position-5 violation must report "item 5" (1-indexed).
        with pytest.raises(InvalidResponseError, match=r"item 5"):
            score_rses([0, 0, 0, 0, 9, 0, 0, 0, 0, 0])

    def test_every_position_strict(self) -> None:
        for position in range(10):
            items = [0] * 10
            items[position] = 4
            with pytest.raises(InvalidResponseError, match="0-3"):
                score_rses(items)

    def test_boundary_zero_accepted(self) -> None:
        score_rses([0] * 10)

    def test_boundary_three_accepted(self) -> None:
        score_rses([3] * 10)


# ---------------------------------------------------------------------------
# Bool rejection — CLAUDE.md standing rule
# ---------------------------------------------------------------------------


class TestBoolRejection:
    def test_true_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_rses([True, 0, 0, 0, 0, 0, 0, 0, 0, 0])

    def test_false_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_rses([False, 0, 0, 0, 0, 0, 0, 0, 0, 0])

    def test_bool_in_each_position(self) -> None:
        for position in range(10):
            items: list[object] = [0] * 10
            items[position] = True
            with pytest.raises(InvalidResponseError, match="must be int"):
                score_rses(items)  # type: ignore[arg-type]

    def test_float_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_rses(
                [0.0, 0, 0, 0, 0, 0, 0, 0, 0, 0]  # type: ignore[list-item]
            )

    def test_none_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_rses(
                [None, 0, 0, 0, 0, 0, 0, 0, 0, 0]  # type: ignore[list-item]
            )

    def test_string_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_rses(
                ["0", 0, 0, 0, 0, 0, 0, 0, 0, 0]  # type: ignore[list-item]
            )


# ---------------------------------------------------------------------------
# Result shape
# ---------------------------------------------------------------------------


class TestResultShape:
    def test_returns_rses_result(self) -> None:
        result = score_rses([0] * 10)
        assert isinstance(result, RsesResult)

    def test_total_field_present(self) -> None:
        result = score_rses([3, 0, 3, 3, 0, 0, 3, 0, 0, 3])
        assert result.total == 30

    def test_total_is_int(self) -> None:
        result = score_rses([3] * 10)
        assert isinstance(result.total, int)
        assert not isinstance(result.total, bool)

    def test_severity_is_continuous(self) -> None:
        # Rosenberg 1965 did not publish bands.  severity is
        # the "continuous" sentinel — uniform with PACS / VAS /
        # Ruler / DTCQ-8 / DERS-16 / CD-RISC-10 / PSWQ / LOT-R /
        # PANAS-10.
        result = score_rses([3] * 10)
        assert result.severity == "continuous"

    def test_items_stores_raw_pre_flip(self) -> None:
        # Pin the audit invariance — items field is RAW,
        # NOT post-flip.
        raw = [3, 3, 0, 2, 3, 3, 1, 3, 3, 0]
        result = score_rses(raw)
        assert result.items == tuple(raw)

    def test_items_is_tuple(self) -> None:
        result = score_rses([0] * 10)
        assert isinstance(result.items, tuple)

    def test_items_length_is_ten(self) -> None:
        result = score_rses([0] * 10)
        assert len(result.items) == 10

    def test_instrument_version_field(self) -> None:
        result = score_rses([0] * 10)
        assert result.instrument_version == INSTRUMENT_VERSION

    def test_result_is_frozen(self) -> None:
        result = score_rses([0] * 10)
        with pytest.raises((AttributeError, Exception)):
            result.total = 99  # type: ignore[misc]

    def test_result_is_hashable(self) -> None:
        result = score_rses([0] * 10)
        assert hash(result) == hash(result)

    def test_no_subscales_field(self) -> None:
        # Gray-Little 1997 IRT — unidimensional.
        result = score_rses([0] * 10)
        assert not hasattr(result, "subscales")

    def test_no_positive_screen_field(self) -> None:
        # RSES is not a screen.
        result = score_rses([0] * 10)
        assert not hasattr(result, "positive_screen")

    def test_no_cutoff_used_field(self) -> None:
        result = score_rses([0] * 10)
        assert not hasattr(result, "cutoff_used")

    def test_no_requires_t3_field(self) -> None:
        # Item 9 "inclined to feel that I am a failure" is a
        # self-concept item, NOT suicidal ideation.  No T3.
        result = score_rses([0, 3, 0, 0, 3, 3, 0, 3, 3, 0])
        assert not hasattr(result, "requires_t3")


# ---------------------------------------------------------------------------
# Clinical vignettes
# ---------------------------------------------------------------------------


class TestClinicalVignettes:
    """Response patterns drawn from Rosenberg 1965 / Schmitt &
    Allik 2005 / clinical relapse-prevention literature."""

    def test_high_self_esteem_flourishing(self) -> None:
        # "Strongly agree" on positive items, "strongly
        # disagree" on reverse items.  Maximum flourishing
        # self-concept.  Schmitt & Allik 2005: US mean 22.2,
        # total 30 is ~1.4 SD above international mean
        # (21.3 ± 5.5).
        items = [3, 0, 3, 3, 0, 0, 3, 0, 0, 3]
        result = score_rses(items)
        assert result.total == 30

    def test_low_self_esteem_abstinence_violation(self) -> None:
        # Classic AVE (Marlatt 1985) signature: the patient has
        # internalized failure attributions.  Post-lapse
        # self-esteem is at floor.  Intervention: self-
        # compassion-based work (Neff 2003) or Gilbert 2010
        # CFT.
        items = [0, 3, 0, 0, 3, 3, 0, 3, 3, 0]
        result = score_rses(items)
        assert result.total == 0

    def test_moderate_mild_impairment(self) -> None:
        # "Disagree" on positive, "agree" on reverse — a
        # consistently low-but-not-floor pattern.  Post-flip
        # positives all 1; post-flip reverse items all 1 (3-2=1).
        # Total = 10.
        items = [1, 2, 1, 1, 2, 2, 1, 2, 2, 1]
        result = score_rses(items)
        assert result.total == 10

    def test_moderate_mild_positive(self) -> None:
        # Inverse: "agree" on positive, "disagree" on reverse.
        # Post-flip positives all 2; post-flip reverse items
        # all 2.  Total = 20.
        items = [2, 1, 2, 2, 1, 1, 2, 1, 1, 2]
        result = score_rses(items)
        assert result.total == 20

    def test_schmitt_allik_international_mean(self) -> None:
        # Schmitt & Allik 2005 cross-national grand M = 21.3
        # on the 0-30 scale (SD = 5.5).  A respondent at this
        # mean pattern is the normative reference point.
        # Construct a pattern producing total ~ 21:
        # positives at (3, 3, 2, 2, 2) = 12; reverse raw at
        # (1, 1, 2, 1, 1) -> post-flip (2, 2, 1, 2, 2) = 9.
        # Total = 21.
        items = [3, 1, 3, 2, 1, 2, 2, 1, 1, 2]
        result = score_rses(items)
        assert result.total == 21

    def test_acquiescent_positive_response_style(self) -> None:
        # "Strongly agree" to EVERYTHING (including reverse-
        # keyed items).  Without reverse-keying, this would
        # produce a spuriously-high total; with reverse-keying,
        # the balanced-wording design produces a middling 15.
        # This is the canonical method-effect check (Marsh 1996).
        result = score_rses([3] * 10)
        assert result.total == 15

    def test_acquiescent_negative_response_style(self) -> None:
        # Symmetrically: "strongly disagree" to everything.
        # Also produces 15.  Marsh 1996 / Gray-Little 1997:
        # the balanced-wording design ensures acquiescent
        # response styles produce SCORES AT THE MIDPOINT, not
        # artificially high/low.
        result = score_rses([0] * 10)
        assert result.total == 15


# ---------------------------------------------------------------------------
# Safety routing — no T3/T4 triggering from RSES
# ---------------------------------------------------------------------------


class TestNoSafetyRouting:
    """RSES measures self-esteem, not suicidality.  Item 9
    "All in all, I am inclined to feel that I am a failure" is
    a SELF-CONCEPT item per Rosenberg 1965 derivation, NOT an
    ideation item.  Acute-risk stays on C-SSRS / PHQ-9 item 9."""

    def test_item_9_failure_does_not_signal_safety(self) -> None:
        # Maximum endorsement of item 9 alone — no safety
        # attribute.
        items = [0] * 10
        items[8] = 3  # item 9, 0-indexed 8
        result = score_rses(items)
        assert not hasattr(result, "requires_t3")

    def test_item_6_useless_does_not_signal_safety(self) -> None:
        # Maximum endorsement of item 6 "I certainly feel
        # useless at times" alone — no safety attribute.
        items = [0] * 10
        items[5] = 3  # item 6, 0-indexed 5
        result = score_rses(items)
        assert not hasattr(result, "requires_t3")

    def test_floor_total_does_not_signal_safety(self) -> None:
        # Total 0 (all reverse items at max, all positives at
        # min) — severe low self-esteem but NOT an acute-risk
        # signal.  A clinician reading RSES 0 should pair it
        # with a safety screen, but the RSES itself does not
        # emit T3.
        items = [0, 3, 0, 0, 3, 3, 0, 3, 3, 0]
        result = score_rses(items)
        assert result.total == 0
        assert not hasattr(result, "requires_t3")

    def test_every_single_position_no_safety(self) -> None:
        # Position-by-position: no single item produces a
        # safety attribute regardless of response.
        for position in range(10):
            for value in (0, 1, 2, 3):
                items = [0] * 10
                items[position] = value
                result = score_rses(items)
                assert not hasattr(result, "requires_t3"), (
                    f"position {position + 1} value {value} "
                    f"unexpectedly set requires_t3"
                )

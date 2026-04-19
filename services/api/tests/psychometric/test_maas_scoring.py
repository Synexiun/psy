"""Unit tests for the MAAS scorer (Brown & Ryan 2003).

Covers:
- Constants (count, range, no subscale dict pin, no reverse pin).
- Total correctness (midline, max, min, arithmetic sum invariance).
- Direction semantics (higher = more mindful, produced by item-wording
  × Likert-anchoring combination).
- Item count validation (wrong-length rejection).
- Item range validation (0, 7, negatives).
- Bool rejection (CLAUDE.md standing rule).
- Result shape (dataclass frozen / field types / version pin / NO
  subscale map).
- Clinical vignettes (highly-mindful, automatic-pilot, moderately-
  mindful, Brown 2003 community mean, MBSR pre-post sensitivity).
- No safety routing (no triggering-items concept).
"""

from __future__ import annotations

import pytest

from discipline.psychometric.scoring.maas import (
    INSTRUMENT_VERSION,
    InvalidResponseError,
    ITEM_COUNT,
    ITEM_MAX,
    ITEM_MIN,
    MaasResult,
    score_maas,
)


class TestConstants:
    """Pin scale constants — changing any of these without an
    instrument-version bump invalidates the audit trail and
    silently shifts the published-literature comparison baseline."""

    def test_item_count_is_fifteen(self) -> None:
        assert ITEM_COUNT == 15

    def test_item_min_is_one(self) -> None:
        # Brown & Ryan 2003 anchors: 1 = almost always (mindless).
        # A refactor shifting floor to 0 would silently bias every
        # total downward by 15 points and make the published Brown
        # 2003 community mean (≈ 4.1 × 15 = 61.5 on sum scale)
        # impossible to compare to.
        assert ITEM_MIN == 1

    def test_item_max_is_six(self) -> None:
        # Brown & Ryan 2003 anchors: 6 = almost never (mindless).
        # A refactor to 1-5 or 1-7 would render the instrument's
        # published norms uninterpretable.
        assert ITEM_MAX == 6

    def test_instrument_version_pinned(self) -> None:
        assert INSTRUMENT_VERSION == "maas-1.0.0"

    def test_no_subscale_constant_exported(self) -> None:
        # Pin the unidimensional contract at the module level —
        # Brown & Ryan 2003, Carlson & Brown 2005, MacKillop 2007
        # confirmed single-factor.  A refactor introducing a
        # SUBSCALES dict without a version bump would be a
        # psychometric fabrication.
        from discipline.psychometric.scoring import maas

        assert not hasattr(maas, "MAAS_SUBSCALES")


class TestTotalCorrectness:
    """Pin arithmetic correctness of the total field."""

    def test_min_total_is_fifteen(self) -> None:
        # All 1s (almost always mindless) — minimum score means
        # LEAST mindful, not "missing data".  The anchoring gives
        # total=15 the semantic meaning of "pervasive automatic
        # pilot".
        result = score_maas([1] * 15)
        assert result.total == 15

    def test_max_total_is_ninety(self) -> None:
        # All 6s (almost never mindless) — maximum score means
        # MOST mindful (present-moment attention default).
        result = score_maas([6] * 15)
        assert result.total == 90

    def test_midline_all_threes(self) -> None:
        # All 3s — 45.  Approximately 3.0 on the Brown & Ryan mean
        # metric; roughly 1 SD below the Brown 2003 community mean.
        result = score_maas([3] * 15)
        assert result.total == 45

    def test_midline_all_fours(self) -> None:
        # All 4s — 60.  Near Brown & Ryan 2003 Study 3 community
        # sample mean (≈ 61.5 on sum metric, ≈ 4.1 on mean metric).
        result = score_maas([4] * 15)
        assert result.total == 60

    def test_total_is_arithmetic_sum(self) -> None:
        items = [1, 2, 3, 4, 5, 6, 1, 2, 3, 4, 5, 6, 1, 2, 3]
        expected = sum(items)
        result = score_maas(items)
        assert result.total == expected

    def test_mbsr_pre_post_delta_representable(self) -> None:
        # Carmody & Baer 2008 MBSR pre ≈ 3.8, post ≈ 4.3 on mean
        # metric → pre-sum ≈ 57, post-sum ≈ 64.5.  Delta of 7.5
        # points on the sum metric is the empirical sensitivity-
        # to-change benchmark.  Pin that both endpoints are
        # representable as valid scores.
        pre_approx = [4] * 12 + [3] * 3  # sum = 57
        post_approx = [4] * 8 + [5] * 7  # sum = 67
        pre_result = score_maas(pre_approx)
        post_result = score_maas(post_approx)
        assert pre_result.total == 57
        assert post_result.total == 67
        # Post > Pre — the directional signature of mindfulness
        # increase.
        assert post_result.total > pre_result.total


class TestDirectionSemantics:
    """Pin the counterintuitive direction rule: all 15 items are
    worded in the MINDLESSNESS direction, so the total is summed
    AS-IS with higher = more mindful.  No flip arithmetic is needed
    — the item wording × Likert anchoring jointly produce the
    correct direction.  A future refactor that "cleaned up" by
    adding a reverse-keying step would DOUBLE-INVERT the score."""

    def test_all_sixes_means_most_mindful(self) -> None:
        # "Almost never [mindless]" answered to every item — the
        # dispositionally-most-mindful respondent.
        result = score_maas([6] * 15)
        assert result.total == 90

    def test_all_ones_means_least_mindful(self) -> None:
        # "Almost always [mindless]" answered to every item — the
        # dispositionally-least-mindful (automatic-pilot) respondent.
        result = score_maas([1] * 15)
        assert result.total == 15

    def test_higher_total_is_more_mindful(self) -> None:
        low = score_maas([2] * 15)
        mid = score_maas([4] * 15)
        high = score_maas([6] * 15)
        # A regression that introduced a spurious reverse-keying
        # step would invert this ordering — pin it.
        assert low.total < mid.total < high.total

    def test_no_reverse_items_by_position(self) -> None:
        # Each item, taken in isolation at max endorsement, should
        # push the total UP, not down.  This catches a refactor
        # that silently introduced per-item reverse-keying for
        # some subset of items.
        baseline = score_maas([1] * 15)  # total = 15
        for pos in range(15):
            items = [1] * 15
            items[pos] = 6
            result = score_maas(items)
            assert result.total == baseline.total + 5, (
                f"Position {pos + 1}: item at max should raise "
                f"total by 5 (not be reverse-keyed)."
            )


class TestItemCountValidation:
    """Pin count-mismatch rejection."""

    def test_zero_items_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 15"):
            score_maas([])

    def test_fourteen_items_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 15"):
            score_maas([1] * 14)

    def test_sixteen_items_rejected(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 15"):
            score_maas([1] * 16)

    def test_five_items_rejected(self) -> None:
        # MAAS-5 is a widely-used short form (derived from Osman
        # 2016 IRT analysis).  Accepting 5 items here would
        # silently score the MAAS-5 using the MAAS-15 endpoint,
        # producing a score 10 points below the real MAAS-15
        # value.
        with pytest.raises(InvalidResponseError, match="exactly 15"):
            score_maas([1] * 5)

    def test_twenty_items_rejected(self) -> None:
        # Longer-than-expected submission.
        with pytest.raises(InvalidResponseError, match="exactly 15"):
            score_maas([1] * 20)


class TestItemRangeValidation:
    """Pin out-of-range item rejection."""

    def test_zero_rejected(self) -> None:
        # 0 is the floor on PHQ-9 / GAD-7 (0-3 Likert) but NOT on
        # MAAS (1-6 Likert).  Catches reflexive 0-indexed mistakes.
        items = [0] + [1] * 14
        with pytest.raises(InvalidResponseError, match="out of range"):
            score_maas(items)

    def test_seven_rejected(self) -> None:
        # 7 is accepted by ERQ (1-7) but NOT MAAS (1-6).
        items = [7] + [1] * 14
        with pytest.raises(InvalidResponseError, match="out of range"):
            score_maas(items)

    def test_five_accepted(self) -> None:
        # 5 is the ceiling on SCS-SF but is INSIDE range for MAAS.
        score_maas([5] * 15)

    def test_negative_rejected(self) -> None:
        items = [-1] + [1] * 14
        with pytest.raises(InvalidResponseError, match="out of range"):
            score_maas(items)

    def test_large_positive_rejected(self) -> None:
        items = [1] * 14 + [100]
        with pytest.raises(InvalidResponseError, match="out of range"):
            score_maas(items)

    def test_range_error_names_item_position(self) -> None:
        items = [1, 1, 1, 1, 1, 1, 1, 99, 1, 1, 1, 1, 1, 1, 1]
        with pytest.raises(InvalidResponseError, match="item 8"):
            score_maas(items)

    def test_range_error_reports_offending_value(self) -> None:
        items = [1] * 14 + [42]
        with pytest.raises(InvalidResponseError, match="42"):
            score_maas(items)

    def test_boundary_one_accepted(self) -> None:
        # 1 is the floor; must be accepted.
        score_maas([1] * 15)

    def test_boundary_six_accepted(self) -> None:
        # 6 is the ceiling; must be accepted.
        score_maas([6] * 15)


class TestBoolRejection:
    """Pin CLAUDE.md standing rule: bool is not int for psychometric
    items."""

    def test_true_rejected(self) -> None:
        items: list[object] = [True] + [1] * 14
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_maas(items)  # type: ignore[arg-type]

    def test_false_rejected(self) -> None:
        # False == 0 numerically; bool rejection comes BEFORE the
        # range check, so the error says "must be int" not "out of
        # range" — diagnostically more informative.
        items: list[object] = [False] + [1] * 14
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_maas(items)  # type: ignore[arg-type]

    def test_bool_in_middle_rejected(self) -> None:
        items: list[object] = (
            [1, 2, 3, 4, 5, 6, True, 2, 3, 4, 5, 6, 1, 2, 3]
        )
        with pytest.raises(InvalidResponseError, match="item 7"):
            score_maas(items)  # type: ignore[arg-type]


class TestResultShape:
    """Pin the dataclass shape and immutability — including the
    ABSENCE of subscale / severity fields (unidimensional
    continuous contract)."""

    def test_returns_maas_result_instance(self) -> None:
        result = score_maas([1] * 15)
        assert isinstance(result, MaasResult)

    def test_result_is_frozen(self) -> None:
        result = score_maas([1] * 15)
        with pytest.raises((AttributeError, Exception)):
            result.total = 999  # type: ignore[misc]

    def test_total_is_int(self) -> None:
        result = score_maas([1, 2, 3, 4, 5, 6, 1, 2, 3, 4, 5, 6, 1, 2, 3])
        assert isinstance(result.total, int)

    def test_items_is_tuple(self) -> None:
        result = score_maas([3] * 15)
        assert isinstance(result.items, tuple)

    def test_items_length_is_fifteen(self) -> None:
        result = score_maas([1] * 15)
        assert len(result.items) == 15

    def test_items_preserves_input(self) -> None:
        raw = [1, 2, 3, 4, 5, 6, 1, 2, 3, 4, 5, 6, 1, 2, 3]
        result = score_maas(raw)
        assert list(result.items) == raw

    def test_instrument_version_default_populated(self) -> None:
        result = score_maas([1] * 15)
        assert result.instrument_version == "maas-1.0.0"

    def test_result_is_hashable(self) -> None:
        result = score_maas([1] * 15)
        hash(result)

    def test_no_subscale_field(self) -> None:
        # Pin the unidimensional construct on the dataclass itself.
        # A regression that added a subscale field would be caught
        # here before the wire shape drifts.
        result = score_maas([1] * 15)
        fields = set(result.__dataclass_fields__.keys())
        assert "subscales" not in fields
        assert "subscale_brooding" not in fields
        assert "subscale_reflection" not in fields
        assert "subscale_attention" not in fields  # common alt-name

    def test_no_severity_field(self) -> None:
        # Brown & Ryan 2003 published no bands; pin no severity
        # field on the dataclass.  Continuous-sentinel handling
        # happens at the router layer.
        result = score_maas([1] * 15)
        fields = set(result.__dataclass_fields__.keys())
        assert "severity" not in fields
        assert "band" not in fields

    def test_no_safety_field(self) -> None:
        # MAAS carries no imminent-harm signal.
        result = score_maas([6] * 15)
        fields = set(result.__dataclass_fields__.keys())
        assert "requires_t3" not in fields
        assert "safety_flag" not in fields
        assert "triggering_items" not in fields


class TestClinicalVignettes:
    """End-to-end clinical scenarios pinning score-semantic
    interpretation."""

    def test_automatic_pilot_profile(self) -> None:
        # Dispositionally low-MAAS — "I find myself doing things
        # without paying attention" endorsed at almost-always
        # across the board.  The prototypical low-mindfulness
        # profile that routes to attention-training tools BEFORE
        # any cognitive or exposure work.
        result = score_maas([1] * 15)
        assert result.total == 15

    def test_highly_mindful_profile(self) -> None:
        # Dispositionally high-MAAS — "I find myself doing things
        # without paying attention" denied at almost-never across
        # the board.  Low-intervention-need pattern; mindfulness
        # tools would be maintenance / reinforcement rather than
        # primary treatment.
        result = score_maas([6] * 15)
        assert result.total == 90

    def test_brown_2003_community_mean(self) -> None:
        # Brown & Ryan 2003 Study 3 community sample: mean ≈ 4.1
        # (SD ≈ 0.7) on the mean-metric scale.  Sum-metric
        # equivalent ≈ 61.5.  Approximate with all-4s (sum = 60)
        # as the community-mean-adjacent profile.
        items = [4] * 15
        result = score_maas(items)
        assert result.total == 60
        # The platform renderer divides by 15 for the mean-metric
        # comparison; 60 / 15 = 4.0 ≈ Brown 2003 community mean.

    def test_mbrp_pre_post_trajectory(self) -> None:
        # Bowen 2014 RCT: MBRP participants showed MAAS increase
        # from baseline to 6-month follow-up.  Pin that a plausible
        # pre-MBRP pattern and a plausible post-MBRP pattern are
        # both representable and orderable.
        pre_items = [3] * 15  # sum 45 — SUD-sample-adjacent low
        post_items = [5] * 15  # sum 75 — post-MBRP-adjacent
        pre = score_maas(pre_items)
        post = score_maas(post_items)
        assert pre.total == 45
        assert post.total == 75
        # MBRP effect sign: post > pre.
        assert post.total - pre.total == 30

    def test_mixed_awareness_profile(self) -> None:
        # Intermittent mindfulness — some items high (present),
        # some low (automatic pilot).  The "skill available but
        # not automatic under stress" profile that routes to
        # implementation-intention / cued-practice tools rather
        # than basic attention training.
        items = [5, 2, 5, 2, 5, 2, 5, 2, 5, 2, 5, 2, 5, 2, 5]
        result = score_maas(items)
        # 8 × 5 = 40; 7 × 2 = 14; total = 54.
        assert result.total == 54


class TestNoSafetyRouting:
    """Pin that MAAS carries no safety-item concept.  Low
    mindfulness is not acute-risk signal — that stays on C-SSRS /
    PHQ-9 item 9."""

    def test_floor_all_ones_no_safety_field(self) -> None:
        # Even at floor (total 15), no safety flag surfaces.
        # Rationale: a dispositionally mindless patient is
        # clinically meaningful but not imminently unsafe.
        result = score_maas([1] * 15)
        fields = set(result.__dataclass_fields__.keys())
        assert "requires_t3" not in fields
        assert "safety_flag" not in fields

    def test_no_triggering_items_concept(self) -> None:
        # Unlike C-SSRS, there is no subset of MAAS items whose
        # endorsement constitutes an imminent-harm signal.
        result = score_maas([1] * 15)
        fields = set(result.__dataclass_fields__.keys())
        assert "triggering_items" not in fields

    def test_no_severity_field_even_at_floor(self) -> None:
        # Brown & Ryan 2003 published no severity bands; the
        # scorer must NOT invent any, even at the lowest
        # possible total.
        result = score_maas([1] * 15)
        fields = set(result.__dataclass_fields__.keys())
        assert "severity" not in fields

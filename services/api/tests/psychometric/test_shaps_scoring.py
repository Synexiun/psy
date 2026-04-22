"""SHAPS scoring tests — Snaith 1995 / Franken 2007.

Four load-bearing correctness properties for the 14-item SHAPS:

1. **Dichotomization is the scoring convention.**  Raw 1-4 Likert
   responses are dichotomized per Snaith 1995 (1-2 → 0, 3-4 → 1)
   BEFORE summation.  Every prior instrument on the platform
   stores ``sum(raw)``, ``sum(reverse(raw))``, ``mean(raw)``, or a
   cutoff on one of those.  SHAPS is the first with a
   non-identity transform inside the summation; a regression that
   silently stored the raw sum (14-56) instead of the dichotomized
   sum (0-14) would break FHIR export, the positive-screen cutoff,
   and cross-sample comparability with every published SHAPS
   trial.  Three dichotomization tests pin the per-value mapping
   (1→0, 2→0, 3→1, 4→1) and the cutoff-boundary tests pin the
   integer sum behavior.

2. **Cutoff is ``>= 3``, not ``> 3`` or ``> 2``.**  Snaith 1995
   §Results selected 3 as the operating point; Franken 2007
   confirmed it against MINI depression (sensitivity 0.77,
   specificity 0.82).  Boundary tests pin 2/3 and 3/4 explicitly
   — total=2 must be negative_screen, total=3 must be positive.
   A fence-post regression at this line would either miss
   clinically positive patients or fire on normal community
   controls.

3. **Higher-is-worse direction (same as PHQ-9/GAD-7/PSS-10).**
   More anhedonic = higher score.  All-agreement (raw [1]*14,
   most hedonically intact response) MUST score 0.  All-disagree
   (raw [4]*14, most anhedonic response) MUST score 14.  A
   silent direction flip would register treatment gains as
   anhedonia worsening and vice-versa.

4. **Raw items are preserved verbatim — NOT the dichotomized
   values.**  The ``items`` tuple carries the 1-4 Likert values
   the respondent actually submitted, not the 0/1 dichotomization.
   This is load-bearing for FHIR export (surfaces the raw
   response), clinician-PDF precision (discriminates a user who
   answered Strongly Disagree to all vs Disagree to all — both
   dichotomize to 14 but represent different phenomenology), and
   recovery of the Franken 2007 continuous-scoring alternative.

Coverage strategy:
- Pin the 2/3 cutoff boundary.
- Pin per-Likert-value dichotomization (1→0, 2→0, 3→1, 4→1).
- Full-range totals: all-1 = 0, all-4 = 14, mixed patterns.
- Item-count and item-range validation (13/15/10-item traps,
  0/5 scale-boundary traps).
- Bool rejection.
- Result shape — raw items preserved, dichotomized values not
  stored separately.
- Clinical vignettes — healthy community response, severe
  anhedonia, Snaith 1995 community-control mean, Franken 2007
  SUD-sample mean, exact-at-cutoff borderline case.
- No safety routing.
"""

from __future__ import annotations

import pytest

from discipline.psychometric.scoring.shaps import (
    INSTRUMENT_VERSION,
    ITEM_COUNT,
    ITEM_MAX,
    ITEM_MIN,
    SHAPS_DICHOTOMIZE_THRESHOLD_INCLUSIVE,
    SHAPS_POSITIVE_CUTOFF,
    InvalidResponseError,
    score_shaps,
)


def _all(level: int) -> list[int]:
    """14-item list with every position at ``level``."""
    return [level] * ITEM_COUNT


def _mixed(anhedonic_positions_1: list[int]) -> list[int]:
    """Build a response with the given 1-indexed positions set to 4
    (Strongly Disagree = anhedonic) and all others set to 1 (Strongly
    Agree = hedonic)."""
    items = [1] * ITEM_COUNT
    for pos in anhedonic_positions_1:
        items[pos - 1] = 4
    return items


class TestConstants:
    """Pin published constants so drift from Snaith 1995 is caught."""

    def test_instrument_version_pinned(self) -> None:
        assert INSTRUMENT_VERSION == "shaps-1.0.0"

    def test_item_count_is_14(self) -> None:
        assert ITEM_COUNT == 14

    def test_item_range_1_to_4(self) -> None:
        assert ITEM_MIN == 1
        assert ITEM_MAX == 4

    def test_positive_cutoff_is_3_snaith_1995(self) -> None:
        """Snaith 1995 §Results published >= 3 operating point."""
        assert SHAPS_POSITIVE_CUTOFF == 3

    def test_dichotomize_threshold_inclusive_is_2(self) -> None:
        """Snaith 1995 specifies raw 1-2 → 0, raw 3-4 → 1."""
        assert SHAPS_DICHOTOMIZE_THRESHOLD_INCLUSIVE == 2

    def test_no_subscales_constant_exported(self) -> None:
        """SHAPS is unidimensional (Franken 2007 PCA, Leventhal 2006
        CFA, Nakonezny 2010 IRT).  Absence of a ``SHAPS_SUBSCALES``
        constant at module level is a psychometric commitment — if
        someone later adds one, this pin breaks and forces a review.
        """
        import discipline.psychometric.scoring.shaps as shaps_module

        assert not hasattr(shaps_module, "SHAPS_SUBSCALES")


class TestDichotomization:
    """Pin the 1-2 → 0, 3-4 → 1 per-item mapping per Snaith 1995."""

    def test_likert_1_dichotomizes_to_0(self) -> None:
        """Strongly Agree on every item → 0 anhedonic items."""
        result = score_shaps(_all(1))
        assert result.total == 0

    def test_likert_2_dichotomizes_to_0(self) -> None:
        """Agree on every item → 0 anhedonic items.

        This is the non-trivial dichotomization pin — raw 2 is
        NOT the midpoint of 1-4, but per Snaith 1995 it scores
        with 1 (not with 3).  A naive ``round(raw / 4)`` or
        ``raw > 2`` implementation would diverge here.
        """
        result = score_shaps(_all(2))
        assert result.total == 0

    def test_likert_3_dichotomizes_to_1(self) -> None:
        """Disagree on every item → 14 anhedonic items."""
        result = score_shaps(_all(3))
        assert result.total == 14

    def test_likert_4_dichotomizes_to_1(self) -> None:
        """Strongly Disagree on every item → 14 anhedonic items."""
        result = score_shaps(_all(4))
        assert result.total == 14

    def test_mixed_2s_and_3s_splits_at_threshold(self) -> None:
        """Seven items at 2 + seven at 3 → 7 anhedonic (threshold
        splits the Likert at the 2/3 boundary)."""
        items = [2] * 7 + [3] * 7
        result = score_shaps(items)
        assert result.total == 7


class TestTotalCorrectness:
    """Integer-sum arithmetic on the dichotomized per-item values."""

    def test_all_strongly_agree_total_is_0(self) -> None:
        """Most hedonically intact possible response → 0."""
        result = score_shaps(_all(1))
        assert result.total == 0
        assert result.positive_screen is False

    def test_all_strongly_disagree_total_is_14(self) -> None:
        """Most anhedonic possible response → 14 (maximum)."""
        result = score_shaps(_all(4))
        assert result.total == 14
        assert result.positive_screen is True

    def test_single_anhedonic_item_scores_1(self) -> None:
        result = score_shaps(_mixed([1]))
        assert result.total == 1

    def test_two_anhedonic_items_score_2(self) -> None:
        result = score_shaps(_mixed([1, 2]))
        assert result.total == 2

    def test_position_invariance_same_count_same_total(self) -> None:
        """Five anhedonic items at positions 1-5 vs positions 10-14
        must produce the same total.  Catches a regression that
        weighted items by position."""
        a = score_shaps(_mixed([1, 2, 3, 4, 5]))
        b = score_shaps(_mixed([10, 11, 12, 13, 14]))
        assert a.total == b.total == 5


class TestCutoffBoundary:
    """Snaith 1995 ≥3 cutoff: 2 negative, 3 positive."""

    def test_total_0_is_negative_screen(self) -> None:
        result = score_shaps(_all(1))
        assert result.positive_screen is False

    def test_total_1_is_negative_screen(self) -> None:
        result = score_shaps(_mixed([1]))
        assert result.total == 1
        assert result.positive_screen is False

    def test_total_2_is_negative_screen(self) -> None:
        """Below-cutoff boundary — MUST NOT trigger positive screen."""
        result = score_shaps(_mixed([1, 2]))
        assert result.total == 2
        assert result.positive_screen is False

    def test_total_3_is_positive_screen(self) -> None:
        """At-cutoff boundary — MUST trigger positive screen.  This
        is the exact operating point Snaith 1995 §Results specifies;
        a fence-post regression here misses the clinical threshold."""
        result = score_shaps(_mixed([1, 2, 3]))
        assert result.total == 3
        assert result.positive_screen is True

    def test_total_4_is_positive_screen(self) -> None:
        result = score_shaps(_mixed([1, 2, 3, 4]))
        assert result.total == 4
        assert result.positive_screen is True

    def test_total_14_is_positive_screen(self) -> None:
        """Maximum total — severe anhedonia."""
        result = score_shaps(_all(4))
        assert result.total == 14
        assert result.positive_screen is True


class TestDirectionSemantics:
    """Higher-is-worse direction pinned per-item.

    Each test endorses only one item (setting raw=4 / Strongly
    Disagree) and verifies that item pushes the total UP by
    exactly 1.  Catches a refactor that silently added reverse-
    keying for a subset of items.
    """

    @pytest.mark.parametrize("position_1", list(range(1, 15)))
    def test_each_item_at_max_anhedonic_adds_1_to_total(
        self, position_1: int
    ) -> None:
        baseline = score_shaps(_all(1))
        endorsed = score_shaps(_mixed([position_1]))
        assert endorsed.total - baseline.total == 1, (
            f"item {position_1} at Strongly Disagree must add exactly 1 "
            f"to total (got {endorsed.total - baseline.total})"
        )


class TestItemCountValidation:
    """Exactly 14 items — mismatches are validation errors, not
    partial scores."""

    def test_rejects_0_items(self) -> None:
        with pytest.raises(InvalidResponseError, match="requires exactly 14"):
            score_shaps([])

    def test_rejects_13_items(self) -> None:
        """One short — could happen via client submitting partial
        response.  Must reject, not score as if item 14 == 0."""
        with pytest.raises(InvalidResponseError, match="requires exactly 14"):
            score_shaps([1] * 13)

    def test_rejects_15_items(self) -> None:
        """One too many — could happen from client mis-padding or a
        MAAS (15-item) payload mis-routed to SHAPS.  Must reject."""
        with pytest.raises(InvalidResponseError, match="requires exactly 14"):
            score_shaps([1] * 15)

    def test_rejects_10_items(self) -> None:
        """RRS-10 / PSS-10 / DAST-10 / DTCQ-8 / AUDIT payloads are
        all plausible near-neighbors that could mis-route.  Must
        reject."""
        with pytest.raises(InvalidResponseError, match="requires exactly 14"):
            score_shaps([1] * 10)

    def test_rejects_7_items(self) -> None:
        """GAD-7 / ISI / AAQ-II payload width — catches a wider
        mis-routing scenario."""
        with pytest.raises(InvalidResponseError, match="requires exactly 14"):
            score_shaps([1] * 7)


class TestItemRangeValidation:
    """Each item must be 1-4 Likert."""

    def test_rejects_0(self) -> None:
        """0 is a valid value in PHQ-9 / GAD-7 / OCI-R — catches a
        client that normalized to 0-3 by mistake."""
        items = _all(1)
        items[0] = 0
        with pytest.raises(InvalidResponseError, match="out of range"):
            score_shaps(items)

    def test_rejects_5(self) -> None:
        """5 is valid in SCS-SF / DERS-16 / K6 — catches 1-5
        normalization mis-route."""
        items = _all(1)
        items[0] = 5
        with pytest.raises(InvalidResponseError, match="out of range"):
            score_shaps(items)

    def test_rejects_7(self) -> None:
        """7 is valid in ERQ (1-7) — catches ERQ normalization
        mis-route."""
        items = _all(1)
        items[13] = 7
        with pytest.raises(InvalidResponseError, match="out of range"):
            score_shaps(items)

    def test_rejects_negative(self) -> None:
        items = _all(1)
        items[0] = -1
        with pytest.raises(InvalidResponseError, match="out of range"):
            score_shaps(items)

    def test_error_message_names_offending_item_number(self) -> None:
        """The 1-indexed item number appears in the message so a
        clinician can locate the faulty response against the Snaith
        1995 administration document."""
        items = _all(1)
        items[7] = 9
        with pytest.raises(InvalidResponseError, match="item 8"):
            score_shaps(items)

    def test_accepts_all_valid_boundary_values(self) -> None:
        """Exercises both endpoints of the 1-4 range at once."""
        result = score_shaps([1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2])
        # Dichotomized: [0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0] = 6
        assert result.total == 6


class TestBoolRejection:
    """CLAUDE.md standing rule — bools are not ints for psychometric
    items.  ``True`` / ``False`` must be explicitly rejected."""

    def test_rejects_true(self) -> None:
        items: list[int] = _all(1)
        items[0] = True  # type: ignore[assignment]
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_shaps(items)

    def test_rejects_false(self) -> None:
        items: list[int] = _all(1)
        items[0] = False  # type: ignore[assignment]
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_shaps(items)

    def test_rejects_bool_in_middle_position(self) -> None:
        """Ensures per-item validation runs across the full list, not
        only position 0."""
        items: list[int] = _all(1)
        items[7] = True  # type: ignore[assignment]
        with pytest.raises(InvalidResponseError, match="item 8"):
            score_shaps(items)


class TestResultShape:
    """ShapsResult dataclass field contract.

    The raw 1-4 response is preserved verbatim in ``items``; the
    dichotomized 0/1 values are a scoring implementation detail
    and are NOT stored separately.  FHIR export and the clinician
    PDF both read ``items`` to surface the raw response."""

    def test_result_is_frozen_dataclass(self) -> None:
        result = score_shaps(_all(1))
        with pytest.raises(Exception):  # FrozenInstanceError subclass
            result.total = 99  # type: ignore[misc]

    def test_result_is_hashable(self) -> None:
        """Frozen + tuple items → hashable.  Allows set/dict keying
        at the trajectory layer when deduplicating identical
        responses."""
        result = score_shaps(_all(1))
        hash(result)

    def test_items_is_tuple_not_list(self) -> None:
        """Tuple preserves immutability; a list field would allow
        downstream mutation that breaks the dataclass's frozen
        contract."""
        result = score_shaps(_all(1))
        assert isinstance(result.items, tuple)

    def test_items_preserves_raw_1_to_4_values(self) -> None:
        """Load-bearing — items must NOT be the dichotomized 0/1
        values.  A user who answered Strongly Disagree (4) to every
        item is phenomenologically distinct from one who answered
        Disagree (3); both dichotomize to 14 but have different
        clinical trajectories (Franken 2007 discusses this in the
        continuous-scoring rationale)."""
        raw = [1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2]
        result = score_shaps(raw)
        assert result.items == tuple(raw)

    def test_items_preserves_raw_even_when_total_is_max(self) -> None:
        """All-4 and all-3 both dichotomize to 14, so this pin
        distinguishes them in the stored ``items`` tuple."""
        all_3 = score_shaps(_all(3))
        all_4 = score_shaps(_all(4))
        assert all_3.total == all_4.total == 14
        assert all_3.items != all_4.items
        assert all_3.items == (3,) * 14
        assert all_4.items == (4,) * 14

    def test_instrument_version_field_is_pinned(self) -> None:
        result = score_shaps(_all(1))
        assert result.instrument_version == INSTRUMENT_VERSION

    def test_positive_screen_is_bool_not_string(self) -> None:
        """The router envelope converts the bool to the
        positive_screen / negative_screen string; the scorer emits
        a bool so downstream math is Pythonic (``if result
        .positive_screen:`` not ``if result.positive_screen ==
        "positive_screen":``)."""
        result = score_shaps(_all(4))
        assert isinstance(result.positive_screen, bool)

    def test_severity_field_absent(self) -> None:
        """SHAPS has positive_screen semantics (cutoff-based) not
        banded severity.  A regression that added a severity field
        on the dataclass would duplicate wire state already carried
        by positive_screen + the router's envelope string."""
        result = score_shaps(_all(1))
        assert not hasattr(result, "severity")

    def test_subscales_field_absent(self) -> None:
        """Unidimensional per Franken 2007 / Leventhal 2006 /
        Nakonezny 2010 — no subscale fields on the dataclass."""
        result = score_shaps(_all(1))
        assert not hasattr(result, "subscale_hedonic")
        assert not hasattr(result, "subscales")

    def test_safety_item_positive_field_absent(self) -> None:
        """SHAPS has no safety item — unlike PHQ-9's
        ``safety_item_positive`` field, SHAPS result dataclass
        should not carry a parallel pin."""
        result = score_shaps(_all(1))
        assert not hasattr(result, "safety_item_positive")

    def test_requires_t3_field_absent(self) -> None:
        """The router hard-codes requires_t3=False for SHAPS; the
        scorer dataclass should NOT carry a requires_t3 field that
        could lead a future refactor to think the scorer is
        authoritative for T3 routing."""
        result = score_shaps(_all(1))
        assert not hasattr(result, "requires_t3")


class TestClinicalVignettes:
    """Scenario-based end-to-end tests grounded in published samples.

    These are not arithmetic tests — they verify that realistic
    respondent profiles produce the clinically-expected classification.
    """

    def test_healthy_community_response_is_negative_screen(self) -> None:
        """Snaith 1995 §Results community-control mean was 0.2
        (dichotomized), SD 0.7 — the modal response was 0.  A
        person who strongly agrees or agrees with every hedonic
        item represents the upper tail of hedonic intactness."""
        result = score_shaps([2, 1, 2, 1, 1, 2, 1, 2, 2, 1, 1, 2, 1, 2])
        assert result.total == 0
        assert result.positive_screen is False

    def test_severe_anhedonia_is_maximum_positive(self) -> None:
        """A patient in major depression with severe anhedonic
        presentation scores at ceiling (14) — Snaith 1995 §Results
        depressive-outpatient subsample mean 5.8, SD 3.6; ceiling
        responses are clinically observed at the severe tail."""
        result = score_shaps(_all(4))
        assert result.total == 14
        assert result.positive_screen is True

    def test_snaith_1995_community_mean_is_negative(self) -> None:
        """Snaith 1995 reports community-control mean 0.2 (SD 0.7).
        A respondent scoring exactly 1 (one item at Disagree, rest
        at Agree) sits at roughly the 75th percentile of community
        controls and remains BELOW cutoff."""
        result = score_shaps(_mixed([7]))
        assert result.total == 1
        assert result.positive_screen is False

    def test_franken_2007_sud_sample_mean_is_positive(self) -> None:
        """Franken 2007 Table 2 — substance-dependent outpatient
        sample mean SHAPS was 3.5 (SD 3.1).  A patient scoring 4
        is near the sample mean and MUST positive-screen."""
        result = score_shaps(_mixed([1, 3, 7, 11]))
        assert result.total == 4
        assert result.positive_screen is True

    def test_borderline_at_cutoff_is_positive(self) -> None:
        """Exactly at the Snaith 1995 ≥3 cutoff — this is the
        clinically-ambiguous boundary that must still trigger
        positive_screen per the published operating point."""
        result = score_shaps(_mixed([3, 9, 14]))
        assert result.total == 3
        assert result.positive_screen is True

    def test_paws_signature_anhedonia_with_preserved_attention(self) -> None:
        """Post-acute-withdrawal profile: moderate-to-severe
        anhedonia (Koob 2008 opponent-process residual).  A SHAPS
        of 6 is characteristic of the abstinent-SUD population in
        the first 3 months of recovery (Martinotti 2008)."""
        result = score_shaps(_mixed([1, 3, 5, 7, 9, 11]))
        assert result.total == 6
        assert result.positive_screen is True


class TestNoSafetyRouting:
    """SHAPS has no safety item — the dataclass must not carry a
    safety field, and no response pattern must raise a safety signal.

    Anhedonia is a well-documented INDIRECT risk factor (Fawcett
    1990 long-term suicide prediction), but the phenomenological
    closeness is handled at the PROFILE level (SHAPS + PHQ-9 +
    C-SSRS) not via per-item SHAPS content.  Acute ideation
    screening stays on C-SSRS / PHQ-9 item 9 per the uniform
    convention.
    """

    def test_maximum_anhedonia_does_not_emit_safety_signal(self) -> None:
        """All-4 response — the clinically most severe SHAPS
        response.  MUST NOT emit any safety-item-positive indicator;
        that phenomenology is probed by C-SSRS."""
        result = score_shaps(_all(4))
        assert not hasattr(result, "safety_item_positive")
        assert not hasattr(result, "requires_t3")

    def test_positive_screen_does_not_imply_safety_flag(self) -> None:
        """Any positive_screen — even at the maximum — is a
        clinical-signal flag, NOT a crisis flag.  The router
        hard-codes requires_t3=False."""
        result = score_shaps(_all(4))
        assert result.positive_screen is True
        assert not hasattr(result, "requires_t3")

    def test_minimum_response_is_clean(self) -> None:
        """Minimum possible response (all Strongly Agree) — no
        anhedonia signal, no safety signal."""
        result = score_shaps(_all(1))
        assert result.total == 0
        assert result.positive_screen is False

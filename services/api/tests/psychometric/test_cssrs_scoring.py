"""C-SSRS Screen scoring tests — Posner et al. 2008/2011.

The C-SSRS Screen is a triage instrument: every test below pins a
specific routing decision in the Posner triage table.  A regression
at any of these points changes which patients get T3-routed, which
has direct safety consequences (under-flag misses crisis cases;
over-flag desensitizes the crisis team).

Coverage strategy:
- Every item, in isolation, with every plausible recency state.
- Every precedence rule (severity-ordered classifier, not first-match).
- The disjunctive escalation contract: any of items 4/5/(6+recent)
  must independently fire T3.
- The "historic past behavior is moderate, not none" branch — added
  to fix a clinical gap where item 6 alone would have classified
  a patient with a prior attempt as 'no risk'.
"""

from __future__ import annotations

import pytest

from discipline.psychometric.scoring.cssrs import (
    INSTRUMENT_VERSION,
    ITEM_ACTIVE_IDEATION,
    ITEM_COUNT,
    ITEM_INTENT,
    ITEM_METHOD,
    ITEM_PASSIVE_IDEATION,
    ITEM_PAST_BEHAVIOR,
    ITEM_PLAN,
    CssrsResult,
    InvalidResponseError,
    score_cssrs_screen,
)


# Helpful literal: an all-negative response is the baseline against
# which every positive-item test sets exactly one bit.  Using a named
# constant makes the intent of each test obvious at a glance.
ALL_NEGATIVE = [False, False, False, False, False, False]


def _with_item(index: int, value: bool = True) -> list[bool]:
    """Return a 6-bool list with exactly one position set."""
    items = list(ALL_NEGATIVE)
    items[index] = value
    return items


# =============================================================================
# Constants — pinned to the published instrument
# =============================================================================


class TestConstants:
    def test_item_count_is_six(self) -> None:
        """The Screen has exactly 6 items per Posner 2011 — changing
        this changes the instrument identity."""
        assert ITEM_COUNT == 6

    def test_instrument_version_stable(self) -> None:
        assert INSTRUMENT_VERSION == "cssrs-screen-1.0.0"

    def test_item_position_constants_are_zero_indexed(self) -> None:
        """Internal positions are 0-indexed for clean array access;
        the docstring + UI use 1-indexed labels.  Pinning the order
        catches an accidental reshuffle."""
        assert ITEM_PASSIVE_IDEATION == 0
        assert ITEM_ACTIVE_IDEATION == 1
        assert ITEM_METHOD == 2
        assert ITEM_INTENT == 3
        assert ITEM_PLAN == 4
        assert ITEM_PAST_BEHAVIOR == 5


# =============================================================================
# None — no positives anywhere
# =============================================================================


class TestNoneRisk:
    def test_all_negative_is_none_risk(self) -> None:
        """Baseline: a clean screen yields 'none' band, no T3, empty
        triggering tuple, positive_count=0."""
        result = score_cssrs_screen(ALL_NEGATIVE)
        assert result.risk == "none"
        assert result.requires_t3 is False
        assert result.triggering_items == ()
        assert result.positive_count == 0

    def test_all_negative_with_recency_flag_still_none(self) -> None:
        """``behavior_within_3mo=True`` is a no-op when item 6 is
        negative — it modulates item 6, doesn't independently raise
        the band."""
        result = score_cssrs_screen(ALL_NEGATIVE, behavior_within_3mo=True)
        assert result.risk == "none"
        assert result.requires_t3 is False


# =============================================================================
# Low — passive / active ideation only (items 1-2)
# =============================================================================


class TestLowRisk:
    def test_only_item_1_is_low(self) -> None:
        """Passive ideation alone ('wished I were dead') → low band,
        clinician check-in.  This is the most common positive screen
        and should NOT escalate."""
        result = score_cssrs_screen(_with_item(ITEM_PASSIVE_IDEATION))
        assert result.risk == "low"
        assert result.requires_t3 is False
        assert result.triggering_items == (1,)
        assert result.positive_count == 1

    def test_only_item_2_is_low(self) -> None:
        """Active ideation without method ('thoughts of killing
        myself, no plan') → low band per Posner 2011 triage."""
        result = score_cssrs_screen(_with_item(ITEM_ACTIVE_IDEATION))
        assert result.risk == "low"
        assert result.requires_t3 is False
        assert result.triggering_items == (2,)

    def test_items_1_and_2_both_low(self) -> None:
        """Both passive and active ideation positive, no method/
        intent/plan/behavior → still low (not moderate).  Both items
        appear in triggering_items in 1-indexed order."""
        items = list(ALL_NEGATIVE)
        items[ITEM_PASSIVE_IDEATION] = True
        items[ITEM_ACTIVE_IDEATION] = True
        result = score_cssrs_screen(items)
        assert result.risk == "low"
        assert result.triggering_items == (1, 2)
        assert result.positive_count == 2


# =============================================================================
# Moderate — item 3 (method) OR item 6 historic
# =============================================================================


class TestModerateRisk:
    def test_only_item_3_is_moderate(self) -> None:
        """Active ideation with method ('thinking about how I might
        do this') but no intent/plan → moderate, supportive
        intervention.  Does NOT trigger T3."""
        result = score_cssrs_screen(_with_item(ITEM_METHOD))
        assert result.risk == "moderate"
        assert result.requires_t3 is False
        assert result.triggering_items == (3,)

    def test_only_item_6_historic_is_moderate(self) -> None:
        """Past suicidal behavior, NOT within 3 months → moderate.
        This is the clinical-gap fix: prior to this branch, an
        otherwise-asymptomatic patient with a years-old attempt
        would have been classified 'none', which understates their
        longitudinal risk.  Posner 2011 §Discussion treats lifetime
        history as a persistent risk factor."""
        result = score_cssrs_screen(
            _with_item(ITEM_PAST_BEHAVIOR), behavior_within_3mo=False
        )
        assert result.risk == "moderate"
        assert result.requires_t3 is False
        assert result.triggering_items == (6,)

    def test_item_6_historic_with_default_recency_is_moderate(self) -> None:
        """The default ``behavior_within_3mo=False`` should produce
        the same outcome as explicitly passing False — 'no recency
        context supplied' is treated as historic."""
        result = score_cssrs_screen(_with_item(ITEM_PAST_BEHAVIOR))
        assert result.risk == "moderate"
        assert result.requires_t3 is False
        assert result.triggering_items == (6,)

    def test_items_3_and_6_historic_both_moderate(self) -> None:
        """Both moderate-band items positive at once → still
        moderate (no escalation path here), and both appear in
        triggering_items in numerical order."""
        items = list(ALL_NEGATIVE)
        items[ITEM_METHOD] = True
        items[ITEM_PAST_BEHAVIOR] = True
        result = score_cssrs_screen(items, behavior_within_3mo=False)
        assert result.risk == "moderate"
        assert result.triggering_items == (3, 6)

    def test_low_items_plus_method_is_moderate_not_low(self) -> None:
        """Severity-precedence test: items 1+2+3 positive →
        moderate (driven by item 3), NOT low.  A 'first-match'
        classifier that returned at the first true item would
        mis-bucket this case."""
        items = list(ALL_NEGATIVE)
        items[ITEM_PASSIVE_IDEATION] = True
        items[ITEM_ACTIVE_IDEATION] = True
        items[ITEM_METHOD] = True
        result = score_cssrs_screen(items)
        assert result.risk == "moderate"
        # triggering_items reports what drove the band, not all
        # positive items — items 1-2 are positive but did not
        # determine the band.
        assert result.triggering_items == (3,)
        assert result.positive_count == 3


# =============================================================================
# Acute — items 4, 5, or 6+recent
# =============================================================================


class TestAcuteRisk:
    def test_only_item_4_is_acute_t3(self) -> None:
        """Active ideation with intent → acute T3.  Threshold below
        which a person should not leave unsupervised."""
        result = score_cssrs_screen(_with_item(ITEM_INTENT))
        assert result.risk == "acute"
        assert result.requires_t3 is True
        assert result.triggering_items == (4,)

    def test_only_item_5_is_acute_t3(self) -> None:
        """Active ideation with specific plan and intent → acute
        T3.  This is the highest-severity ideation item."""
        result = score_cssrs_screen(_with_item(ITEM_PLAN))
        assert result.risk == "acute"
        assert result.requires_t3 is True
        assert result.triggering_items == (5,)

    def test_only_item_6_recent_is_acute_t3(self) -> None:
        """Past behavior WITHIN the past 3 months → acute T3.
        Recent behavior is the strongest single predictor of
        near-term re-attempt per Posner 2011."""
        result = score_cssrs_screen(
            _with_item(ITEM_PAST_BEHAVIOR), behavior_within_3mo=True
        )
        assert result.risk == "acute"
        assert result.requires_t3 is True
        assert result.triggering_items == (6,)

    def test_items_4_and_5_both_in_triggering(self) -> None:
        """Disjunctive contract — both intent AND plan positive,
        both surface in triggering_items in 1-indexed order.  This
        is what an audit reviewer needs to see."""
        items = list(ALL_NEGATIVE)
        items[ITEM_INTENT] = True
        items[ITEM_PLAN] = True
        result = score_cssrs_screen(items)
        assert result.risk == "acute"
        assert result.requires_t3 is True
        assert result.triggering_items == (4, 5)

    def test_items_4_5_and_6_recent_all_in_triggering(self) -> None:
        """Worst-case scenario: every acute item positive AND recent
        behavior — all three appear in triggering_items."""
        items = list(ALL_NEGATIVE)
        items[ITEM_INTENT] = True
        items[ITEM_PLAN] = True
        items[ITEM_PAST_BEHAVIOR] = True
        result = score_cssrs_screen(items, behavior_within_3mo=True)
        assert result.risk == "acute"
        assert result.requires_t3 is True
        assert result.triggering_items == (4, 5, 6)
        assert result.positive_count == 3

    def test_low_items_plus_intent_is_acute_not_low(self) -> None:
        """Precedence: items 1+2+4 positive → acute (not low).
        A naive classifier that short-circuits on the first match
        in 1-2-3-4 order would mis-bucket this as low."""
        items = list(ALL_NEGATIVE)
        items[ITEM_PASSIVE_IDEATION] = True
        items[ITEM_ACTIVE_IDEATION] = True
        items[ITEM_INTENT] = True
        result = score_cssrs_screen(items)
        assert result.risk == "acute"
        assert result.requires_t3 is True
        assert result.triggering_items == (4,)
        assert result.positive_count == 3

    def test_method_plus_plan_is_acute_not_moderate(self) -> None:
        """Items 3+5 positive → acute (not moderate).  Item 5 wins
        precedence; item 3 is dropped from triggering because it
        didn't determine the band."""
        items = list(ALL_NEGATIVE)
        items[ITEM_METHOD] = True
        items[ITEM_PLAN] = True
        result = score_cssrs_screen(items)
        assert result.risk == "acute"
        assert result.triggering_items == (5,)


# =============================================================================
# Disjunctive escalation — the load-bearing safety contract
# =============================================================================


class TestDisjunctiveEscalation:
    """Items 4 OR 5 OR (6+recent) — any single one fires T3.  A
    refactor that joined them with ``and`` would silently suppress
    the majority of acute cases.  Each path is pinned independently."""

    def test_intent_alone_fires_t3(self) -> None:
        result = score_cssrs_screen(_with_item(ITEM_INTENT))
        assert result.requires_t3 is True

    def test_plan_alone_fires_t3(self) -> None:
        result = score_cssrs_screen(_with_item(ITEM_PLAN))
        assert result.requires_t3 is True

    def test_recent_behavior_alone_fires_t3(self) -> None:
        result = score_cssrs_screen(
            _with_item(ITEM_PAST_BEHAVIOR), behavior_within_3mo=True
        )
        assert result.requires_t3 is True

    def test_no_acute_items_does_not_fire_t3(self) -> None:
        """Negative control: items 1+2+3 positive (low → moderate
        bands) → never T3, even with all three on."""
        items = list(ALL_NEGATIVE)
        items[ITEM_PASSIVE_IDEATION] = True
        items[ITEM_ACTIVE_IDEATION] = True
        items[ITEM_METHOD] = True
        result = score_cssrs_screen(items)
        assert result.requires_t3 is False


# =============================================================================
# behavior_within_3mo — the recency input
# =============================================================================


class TestBehaviorRecency:
    def test_default_is_false(self) -> None:
        """The default treats item 6 as historic.  This is the
        safer default in the absence of recency context — an
        omitted kwarg should not over-trigger T3 on long-past
        behavior."""
        result = score_cssrs_screen(_with_item(ITEM_PAST_BEHAVIOR))
        # Default is False → moderate, not acute
        assert result.risk == "moderate"
        assert result.behavior_within_3mo is False

    def test_recency_true_escalates_item_6(self) -> None:
        """The same item 6 positive becomes acute when the caller
        supplies ``behavior_within_3mo=True``.  This is the entire
        point of the recency parameter."""
        items_neg = score_cssrs_screen(
            _with_item(ITEM_PAST_BEHAVIOR), behavior_within_3mo=False
        )
        items_pos = score_cssrs_screen(
            _with_item(ITEM_PAST_BEHAVIOR), behavior_within_3mo=True
        )
        assert items_neg.risk == "moderate"
        assert items_pos.risk == "acute"
        assert items_neg.requires_t3 is False
        assert items_pos.requires_t3 is True

    def test_recency_echoed_in_result(self) -> None:
        """Audit traceability: the recency input is pinned in the
        result so a downstream auditor can see the exact decision
        inputs that produced the band."""
        result = score_cssrs_screen(
            _with_item(ITEM_PAST_BEHAVIOR), behavior_within_3mo=True
        )
        assert result.behavior_within_3mo is True

    def test_recency_only_modulates_item_6(self) -> None:
        """``behavior_within_3mo=True`` does NOT change items 1-5's
        contribution — it only gates whether item 6 raises to acute.
        This isolates the recency parameter's effect."""
        # Item 3 alone → moderate, irrespective of recency flag
        a = score_cssrs_screen(_with_item(ITEM_METHOD), behavior_within_3mo=False)
        b = score_cssrs_screen(_with_item(ITEM_METHOD), behavior_within_3mo=True)
        assert a.risk == "moderate"
        assert b.risk == "moderate"
        assert a.requires_t3 == b.requires_t3 == False  # noqa: E712


# =============================================================================
# Triggering items — 1-indexed for clinician/UI alignment
# =============================================================================


class TestTriggeringItems:
    def test_triggering_items_are_one_indexed(self) -> None:
        """Items in the result are 1-indexed (matching the published
        item numbering 1-6) even though internal positions are
        0-indexed.  Confused indexing here would mis-attribute
        which question drove the escalation in audit logs."""
        result = score_cssrs_screen(_with_item(ITEM_INTENT))
        # ITEM_INTENT is position 3 internally; emerges as 4 in result.
        assert result.triggering_items == (4,)

    def test_triggering_items_are_in_ascending_order(self) -> None:
        """When multiple items fire, they appear in numerical order
        — clinician-facing audit needs predictable ordering."""
        items = list(ALL_NEGATIVE)
        items[ITEM_INTENT] = True
        items[ITEM_PLAN] = True
        items[ITEM_PAST_BEHAVIOR] = True
        result = score_cssrs_screen(items, behavior_within_3mo=True)
        assert result.triggering_items == (4, 5, 6)

    def test_triggering_items_empty_when_none_band(self) -> None:
        result = score_cssrs_screen(ALL_NEGATIVE)
        assert result.triggering_items == ()

    def test_triggering_items_only_band_drivers(self) -> None:
        """Only items that determined the band are listed — not all
        positive items.  Items 1+2 positive alongside item 4 →
        triggering_items=(4,) because items 1-2 didn't drive the
        acute classification."""
        items = list(ALL_NEGATIVE)
        items[ITEM_PASSIVE_IDEATION] = True
        items[ITEM_ACTIVE_IDEATION] = True
        items[ITEM_INTENT] = True
        result = score_cssrs_screen(items)
        assert result.triggering_items == (4,)


# =============================================================================
# Validation
# =============================================================================


class TestValidation:
    def test_too_few_items_raises(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 6 items"):
            score_cssrs_screen([False, False, False, False, False])

    def test_too_many_items_raises(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 6 items"):
            score_cssrs_screen([False] * 7)

    def test_zero_items_raises(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 6 items"):
            score_cssrs_screen([])

    def test_count_in_error_message(self) -> None:
        """The error reports the actual count received — diagnostic
        for the caller who got the item count wrong."""
        with pytest.raises(InvalidResponseError, match="got 4"):
            score_cssrs_screen([False, False, False, False])


# =============================================================================
# Coercion — non-bool truthy/falsy values normalize to bool
# =============================================================================


class TestCoercion:
    def test_int_zero_one_coerce_to_bool(self) -> None:
        """The published instrument is yes/no; the wire layer often
        sends 0/1.  ``bool(v)`` coercion keeps the scorer's domain
        bool while accepting common transport encodings."""
        result = score_cssrs_screen([0, 0, 0, 0, 0, 0])
        assert result.risk == "none"
        assert all(isinstance(v, bool) for v in result.items)

    def test_int_one_in_intent_position_fires_t3(self) -> None:
        """0/1 transport encoding still produces correct triage."""
        result = score_cssrs_screen([0, 0, 0, 1, 0, 0])
        assert result.risk == "acute"
        assert result.requires_t3 is True

    def test_items_stored_as_bool_not_int(self) -> None:
        """After coercion the stored tuple is all-bool — not a mix.
        Downstream serializers can rely on the type."""
        result = score_cssrs_screen([1, 0, 1, 0, 1, 0])
        for v in result.items:
            assert type(v) is bool


# =============================================================================
# Result shape
# =============================================================================


class TestResultShape:
    def test_result_is_frozen(self) -> None:
        """``CssrsResult`` is immutable so a downstream consumer
        can't accidentally mutate the audit record after the fact."""
        result = score_cssrs_screen(ALL_NEGATIVE)
        with pytest.raises(Exception):  # FrozenInstanceError
            result.risk = "acute"  # type: ignore[misc]

    def test_items_is_tuple(self) -> None:
        result = score_cssrs_screen(ALL_NEGATIVE)
        assert isinstance(result.items, tuple)

    def test_triggering_items_is_tuple(self) -> None:
        result = score_cssrs_screen(_with_item(ITEM_INTENT))
        assert isinstance(result.triggering_items, tuple)

    def test_items_echoed_verbatim(self) -> None:
        """The stored items match the input (after bool coercion).
        Audit needs the inputs that produced the band."""
        items = [True, False, True, False, True, False]
        result = score_cssrs_screen(items)
        assert result.items == tuple(items)

    def test_positive_count_matches_items(self) -> None:
        """``positive_count`` is the sum of True values — useful for
        tracking change over time independently of the risk band."""
        items = [True, True, False, True, False, True]
        result = score_cssrs_screen(items, behavior_within_3mo=True)
        assert result.positive_count == 4

    def test_instrument_version_in_result(self) -> None:
        result = score_cssrs_screen(ALL_NEGATIVE)
        assert result.instrument_version == INSTRUMENT_VERSION

    def test_result_type(self) -> None:
        result = score_cssrs_screen(ALL_NEGATIVE)
        assert isinstance(result, CssrsResult)


# =============================================================================
# Realistic clinical scenarios — pinning end-to-end behavior
# =============================================================================


class TestClinicalScenarios:
    """End-to-end pinning of the most-reported screen patterns.
    These read like patient vignettes; if any of these diverge from
    the documented Posner triage, that's the regression to catch."""

    def test_passive_only_check_in_next_visit(self) -> None:
        """'Wished I were dead, no thoughts of acting' → low, no T3."""
        items = [True, False, False, False, False, False]
        result = score_cssrs_screen(items)
        assert result.risk == "low"
        assert result.requires_t3 is False

    def test_active_with_method_no_intent(self) -> None:
        """'Thoughts of killing myself, thinking about how, no
        intent or plan' → moderate, no T3."""
        items = [True, True, True, False, False, False]
        result = score_cssrs_screen(items)
        assert result.risk == "moderate"
        assert result.requires_t3 is False
        # Item 3 is the band driver.
        assert result.triggering_items == (3,)

    def test_full_ideation_chain_fires_t3(self) -> None:
        """'Wished dead, thoughts of killing self, with method, with
        intent' → acute T3.  This is the canonical emergent pattern
        the Screen is designed to flag."""
        items = [True, True, True, True, False, False]
        result = score_cssrs_screen(items)
        assert result.risk == "acute"
        assert result.requires_t3 is True
        assert result.triggering_items == (4,)

    def test_recent_attempt_with_otherwise_clean_screen(self) -> None:
        """'Took an overdose 6 weeks ago' but currently denies any
        ideation → still acute T3 because recent behavior is the
        strongest predictor.  This is the key 'no current ideation
        but still in danger' case."""
        items = [False, False, False, False, False, True]
        result = score_cssrs_screen(items, behavior_within_3mo=True)
        assert result.risk == "acute"
        assert result.requires_t3 is True
        assert result.triggering_items == (6,)

    def test_distant_attempt_with_otherwise_clean_screen(self) -> None:
        """'Took an overdose 8 years ago, no recent ideation' →
        moderate (NOT none, NOT acute).  This is the historic-
        behavior gap-fix path."""
        items = [False, False, False, False, False, True]
        result = score_cssrs_screen(items, behavior_within_3mo=False)
        assert result.risk == "moderate"
        assert result.requires_t3 is False
        assert result.triggering_items == (6,)

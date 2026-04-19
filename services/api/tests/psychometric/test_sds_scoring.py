"""Tests for the SDS scorer (Gossop 1995 + per-substance follow-up
validation).

These tests pin the module constants, the total computation, the
substance-adaptive cutoff semantics, the validator envelope (item
count, item range, bool rejection), and the no-safety-routing invariant.
"""

from __future__ import annotations

import pytest

from discipline.psychometric.scoring.sds import (
    INSTRUMENT_VERSION,
    ITEM_COUNT,
    ITEM_MAX,
    ITEM_MIN,
    InvalidResponseError,
    SDS_CUTOFFS,
    SDS_CUTOFF_AMPHETAMINE,
    SDS_CUTOFF_CANNABIS,
    SDS_CUTOFF_COCAINE,
    SDS_CUTOFF_HEROIN,
    SDS_CUTOFF_UNSPECIFIED,
    SdsResult,
    score_sds,
)


class TestConstants:
    """Pinned module constants — drift here is a clinical change."""

    def test_item_count_is_five(self) -> None:
        assert ITEM_COUNT == 5

    def test_item_floor_is_zero(self) -> None:
        assert ITEM_MIN == 0

    def test_item_ceiling_is_three(self) -> None:
        assert ITEM_MAX == 3

    def test_instrument_version_pinned(self) -> None:
        assert INSTRUMENT_VERSION == "sds-1.0.0"

    def test_heroin_cutoff_is_five(self) -> None:
        """Gossop 1995 — heroin cutoff ≥5."""
        assert SDS_CUTOFF_HEROIN == 5

    def test_cannabis_cutoff_is_three(self) -> None:
        """Martin 2006 / Swift 1998 — cannabis cutoff ≥3."""
        assert SDS_CUTOFF_CANNABIS == 3

    def test_cocaine_cutoff_is_three(self) -> None:
        """Kaye & Darke 2002/2004 — cocaine cutoff ≥3."""
        assert SDS_CUTOFF_COCAINE == 3

    def test_amphetamine_cutoff_is_four(self) -> None:
        """Topp & Mattick 1997 — amphetamine cutoff ≥4."""
        assert SDS_CUTOFF_AMPHETAMINE == 4

    def test_unspecified_cutoff_matches_lowest(self) -> None:
        """Conservative default: unspecified → lowest published cutoff
        (cannabis/cocaine = 3).  Pins the safety-posture rationale."""
        assert SDS_CUTOFF_UNSPECIFIED == 3
        assert SDS_CUTOFF_UNSPECIFIED == min(
            SDS_CUTOFF_HEROIN,
            SDS_CUTOFF_CANNABIS,
            SDS_CUTOFF_COCAINE,
            SDS_CUTOFF_AMPHETAMINE,
        )

    def test_cutoffs_table_exposes_all_substances(self) -> None:
        """SDS_CUTOFFS must cover every Substance Literal value."""
        assert set(SDS_CUTOFFS.keys()) == {
            "heroin",
            "cannabis",
            "cocaine",
            "amphetamine",
            "unspecified",
        }


class TestTotalCorrectness:
    """Total is the straight sum of items — no reverse scoring."""

    def test_all_zeros_total_is_zero(self) -> None:
        r = score_sds([0, 0, 0, 0, 0])
        assert r.total == 0

    def test_all_threes_total_is_fifteen(self) -> None:
        r = score_sds([3, 3, 3, 3, 3])
        assert r.total == 15

    def test_mixed_sum(self) -> None:
        r = score_sds([1, 2, 3, 0, 1])
        assert r.total == 7

    def test_single_high_item(self) -> None:
        r = score_sds([3, 0, 0, 0, 0])
        assert r.total == 3


class TestSubstanceCutoffs:
    """Each named substance applies its published cutoff; positive_screen
    flips exactly at ``total >= cutoff``."""

    def test_heroin_four_is_negative(self) -> None:
        """Heroin cutoff is ≥5; total=4 is below, negative screen."""
        r = score_sds([1, 1, 1, 1, 0], substance="heroin")
        assert r.total == 4
        assert r.cutoff_used == 5
        assert r.positive_screen is False

    def test_heroin_five_is_positive(self) -> None:
        """Heroin cutoff is ≥5; total=5 flips to positive."""
        r = score_sds([1, 1, 1, 1, 1], substance="heroin")
        assert r.total == 5
        assert r.cutoff_used == 5
        assert r.positive_screen is True

    def test_cannabis_two_is_negative(self) -> None:
        """Cannabis cutoff is ≥3; total=2 is below, negative screen."""
        r = score_sds([1, 1, 0, 0, 0], substance="cannabis")
        assert r.total == 2
        assert r.cutoff_used == 3
        assert r.positive_screen is False

    def test_cannabis_three_is_positive(self) -> None:
        """Cannabis cutoff is ≥3; total=3 flips to positive."""
        r = score_sds([1, 1, 1, 0, 0], substance="cannabis")
        assert r.total == 3
        assert r.cutoff_used == 3
        assert r.positive_screen is True

    def test_cocaine_two_is_negative(self) -> None:
        r = score_sds([1, 1, 0, 0, 0], substance="cocaine")
        assert r.total == 2
        assert r.cutoff_used == 3
        assert r.positive_screen is False

    def test_cocaine_three_is_positive(self) -> None:
        r = score_sds([1, 1, 1, 0, 0], substance="cocaine")
        assert r.total == 3
        assert r.cutoff_used == 3
        assert r.positive_screen is True

    def test_amphetamine_three_is_negative(self) -> None:
        """Amphetamine cutoff is ≥4; total=3 is below, negative screen.
        This is a load-bearing distinction — amphetamine is the only
        substance in the default catalog where the cutoff sits
        BETWEEN the cannabis (3) and heroin (5) thresholds."""
        r = score_sds([1, 1, 1, 0, 0], substance="amphetamine")
        assert r.total == 3
        assert r.cutoff_used == 4
        assert r.positive_screen is False

    def test_amphetamine_four_is_positive(self) -> None:
        r = score_sds([1, 1, 1, 1, 0], substance="amphetamine")
        assert r.total == 4
        assert r.cutoff_used == 4
        assert r.positive_screen is True

    def test_unspecified_uses_lowest_cutoff(self) -> None:
        """Unspecified substance → ≥3 (lowest published).  Safety-
        conservative default — same posture as AUDIT-C sex='unspecified'."""
        r = score_sds([1, 1, 1, 0, 0], substance="unspecified")
        assert r.total == 3
        assert r.cutoff_used == 3
        assert r.positive_screen is True

    def test_unspecified_is_default_when_not_passed(self) -> None:
        """Callers that omit substance get the conservative default."""
        r = score_sds([1, 1, 1, 0, 0])
        assert r.substance == "unspecified"
        assert r.cutoff_used == 3

    def test_same_total_differs_across_substances(self) -> None:
        """Total=4: negative for heroin (≥5), positive for
        cannabis/cocaine/unspecified (≥3), positive for amphetamine
        (≥4).  This is the whole point of the substance-adaptive
        envelope — the same psychometric signal carries different
        clinical meaning depending on what the patient is using."""
        items = [1, 1, 1, 1, 0]
        assert score_sds(items, substance="heroin").positive_screen is False
        assert score_sds(items, substance="cannabis").positive_screen is True
        assert score_sds(items, substance="cocaine").positive_screen is True
        assert (
            score_sds(items, substance="amphetamine").positive_screen is True
        )
        assert (
            score_sds(items, substance="unspecified").positive_screen is True
        )


class TestItemCountValidation:
    """Exact count = 5.  Any other length is a 422, not a silent score."""

    def test_rejects_zero_items(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 5 items"):
            score_sds([])

    def test_rejects_four_items(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 5 items"):
            score_sds([0, 0, 0, 0])

    def test_rejects_six_items(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 5 items"):
            score_sds([0, 0, 0, 0, 0, 0])

    def test_rejects_three_items_like_auditc_misroute(self) -> None:
        """A 3-item AUDIT-C submission misrouted to SDS must 422, not
        silently return a total=sum(3 items)."""
        with pytest.raises(InvalidResponseError, match="exactly 5 items"):
            score_sds([2, 2, 2])


class TestItemRangeValidation:
    """Every item must be within [0, 3].  No coercion, no clamping."""

    @pytest.mark.parametrize("bad_value", [-1, 4, 5, 10])
    def test_rejects_out_of_range(self, bad_value: int) -> None:
        with pytest.raises(InvalidResponseError, match="out of range"):
            score_sds([bad_value, 0, 0, 0, 0])

    def test_rejects_negative_at_last_position(self) -> None:
        with pytest.raises(InvalidResponseError, match="item 5"):
            score_sds([0, 0, 0, 0, -1])

    def test_rejects_string_item(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_sds([0, 0, "2", 0, 0])  # type: ignore[list-item]

    def test_rejects_float_item(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_sds([0, 0, 2.5, 0, 0])  # type: ignore[list-item]

    def test_rejects_none_item(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_sds([0, 0, None, 0, 0])  # type: ignore[list-item]


class TestBoolRejection:
    """Uniform with the rest of the package — bool is not a valid
    Likert value, even though ``True == 1`` in Python."""

    def test_rejects_true(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_sds([True, 0, 0, 0, 0])  # type: ignore[list-item]

    def test_rejects_false(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_sds([False, 0, 0, 0, 0])  # type: ignore[list-item]

    def test_rejects_mixed_bool_int(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_sds([1, 2, True, 0, 0])  # type: ignore[list-item]


class TestResultShape:
    """Pin the SdsResult dataclass shape — no drift, no surprise fields."""

    def test_result_is_frozen(self) -> None:
        r = score_sds([1, 1, 1, 0, 0])
        with pytest.raises(Exception):  # FrozenInstanceError subclass
            r.total = 99  # type: ignore[misc]

    def test_result_has_no_severity_field(self) -> None:
        """SDS uses cutoff envelope, not banded envelope — no
        ``severity`` attribute on the scorer result."""
        r = score_sds([1, 1, 1, 0, 0])
        assert not hasattr(r, "severity")

    def test_result_has_no_requires_t3_field(self) -> None:
        """SDS has no safety item — no ``requires_t3`` on the result."""
        r = score_sds([3, 3, 3, 3, 3])
        assert not hasattr(r, "requires_t3")

    def test_result_has_no_subscales_field(self) -> None:
        """Gossop 1995 validated unidimensionality — no subscales."""
        r = score_sds([1, 1, 1, 0, 0])
        assert not hasattr(r, "subscales")

    def test_result_carries_instrument_version(self) -> None:
        r = score_sds([0, 0, 0, 0, 0])
        assert r.instrument_version == "sds-1.0.0"

    def test_result_echoes_items_verbatim(self) -> None:
        r = score_sds([0, 1, 2, 3, 1])
        assert r.items == (0, 1, 2, 3, 1)

    def test_result_items_is_tuple(self) -> None:
        """Items must be a tuple (hashable, immutable), not a list."""
        r = score_sds([0, 1, 2, 3, 1])
        assert isinstance(r.items, tuple)

    def test_result_echoes_substance(self) -> None:
        """Substance echoed for audit traceability."""
        r = score_sds([1, 1, 1, 1, 1], substance="heroin")
        assert r.substance == "heroin"

    def test_result_is_sdsresult_instance(self) -> None:
        r = score_sds([0, 0, 0, 0, 0])
        assert isinstance(r, SdsResult)


class TestClinicalVignettes:
    """Realistic patient scenarios pinning clinical interpretation."""

    def test_cannabis_user_low_psychological_dependence(self) -> None:
        """Frequent cannabis use but not psychologically captive.
        Total=2, cutoff ≥3 → negative screen.  Clinician reads this
        as "use without dependence" — a different treatment path
        from use-with-dependence."""
        r = score_sds([0, 0, 1, 0, 1], substance="cannabis")
        assert r.total == 2
        assert r.positive_screen is False

    def test_cannabis_user_high_psychological_dependence(self) -> None:
        """Occasional cannabis use but strongly captive.
        Items 1 (out of control) and 5 (difficult to stop) maxed;
        clear psychological-dependence profile even if use is not
        heavy.  This is the DAST-low / SDS-high pattern SDS is
        designed to surface."""
        r = score_sds([3, 1, 2, 2, 3], substance="cannabis")
        assert r.total == 11
        assert r.positive_screen is True

    def test_heroin_user_borderline(self) -> None:
        """Heroin user at total=4 — below the Gossop 1995 cutoff.
        Would be POSITIVE for every other substance in the catalog,
        NEGATIVE for heroin.  This is the substance-adaptive point."""
        r = score_sds([1, 1, 1, 1, 0], substance="heroin")
        assert r.total == 4
        assert r.positive_screen is False

    def test_heroin_user_max_score(self) -> None:
        """Maximum SDS=15 — unambiguous psychological dependence
        regardless of substance."""
        r = score_sds([3, 3, 3, 3, 3], substance="heroin")
        assert r.total == 15
        assert r.positive_screen is True

    def test_amphetamine_between_thresholds(self) -> None:
        """Amphetamine cutoff 4 sits between cannabis/cocaine (3)
        and heroin (5) — total=3 is the vignette that exercises this
        middle-threshold band."""
        r = score_sds([1, 1, 1, 0, 0], substance="amphetamine")
        assert r.total == 3
        assert r.positive_screen is False

    def test_unspecified_captures_early_dependence(self) -> None:
        """Conservative default catches low-level dependence signal
        when the clinician hasn't yet pinned the substance (e.g.,
        multi-substance user being worked up).  Same total=3 would
        be positive."""
        r = score_sds([0, 1, 1, 1, 0], substance="unspecified")
        assert r.total == 3
        assert r.positive_screen is True


class TestNoSafetyRouting:
    """SDS has no suicidality item.  No combination of responses fires
    T3.  The scorer doesn't even expose requires_t3 — this class pins
    the invariant against future accidental addition."""

    def test_all_max_items_do_not_fire_t3(self) -> None:
        r = score_sds([3, 3, 3, 3, 3], substance="heroin")
        assert not hasattr(r, "requires_t3")
        assert r.positive_screen is True

    def test_item_1_out_of_control_is_not_safety_item(self) -> None:
        """Item 1 ("out of control") probes loss-of-control cognition,
        not suicidality.  Maxing it alone does not elevate safety."""
        r = score_sds([3, 0, 0, 0, 0], substance="cannabis")
        assert not hasattr(r, "requires_t3")

    def test_item_4_wish_could_stop_is_not_safety_item(self) -> None:
        """Item 4 ("wish could stop") probes motivation toward
        abstinence, not suicidality.  Maxing it alone does not
        elevate safety."""
        r = score_sds([0, 0, 0, 3, 0], substance="cannabis")
        assert not hasattr(r, "requires_t3")

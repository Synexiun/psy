"""Tests for the DUDIT scorer (Berman, Bergman, Palmstierna, Schlyter
2005 — Drug Use Disorders Identification Test).

Pins the module constants, total computation, sex-keyed cutoff
selection, the NOVEL non-uniform per-index validator (items 1-9 are
0-4 Likert, items 10-11 are {0, 2, 4} trinary), result shape
invariants, and the no-safety-routing invariant.
"""

from __future__ import annotations

import pytest

from discipline.psychometric.scoring.dudit import (
    DUDIT_CUTOFF_FEMALE,
    DUDIT_CUTOFF_MALE,
    DUDIT_CUTOFF_UNSPECIFIED,
    DuditResult,
    INSTRUMENT_VERSION,
    ITEM_COUNT,
    InvalidResponseError,
    LIKERT_ITEM_MAX,
    LIKERT_ITEM_MIN,
    TRINARY_ITEM_INDICES_1,
    TRINARY_VALUES,
    score_dudit,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


class TestConstants:
    """Pinned module constants — drift here is a clinical change."""

    def test_item_count_is_eleven(self) -> None:
        assert ITEM_COUNT == 11

    def test_likert_floor_is_zero(self) -> None:
        """DUDIT coding puts "Never" at 0 — a total of 0 is a genuine
        negative response, not a coding artifact.  ITEM_MIN=0 is
        different from K10/K6 (which use 1-5) — no cross-instrument
        coding confusion."""
        assert LIKERT_ITEM_MIN == 0

    def test_likert_ceiling_is_four(self) -> None:
        assert LIKERT_ITEM_MAX == 4

    def test_trinary_values_are_zero_two_four(self) -> None:
        """Items 10-11 accept only 0/2/4 — a response of 1 or 3 on
        these items is rejected even though it sits within the
        numerical envelope 0-4."""
        assert TRINARY_VALUES == frozenset({0, 2, 4})

    def test_trinary_indices_are_ten_and_eleven(self) -> None:
        """Exactly the last two items take the trinary envelope."""
        assert TRINARY_ITEM_INDICES_1 == frozenset({10, 11})

    def test_male_cutoff_is_six(self) -> None:
        """Berman 2005: ≥6 for men (sensitivity 0.90, specificity 0.88
        vs DSM-IV drug abuse/dependence)."""
        assert DUDIT_CUTOFF_MALE == 6

    def test_female_cutoff_is_two(self) -> None:
        """Berman 2005: ≥2 for women — the 3× asymmetry vs male
        cutoff reflects population-distribution differences in drug
        use patterns, not tolerance or metabolism alone."""
        assert DUDIT_CUTOFF_FEMALE == 2

    def test_unspecified_cutoff_matches_female(self) -> None:
        """Safety-conservatism convention — unspecified sex defaults
        to the lower (more sensitive) cutoff.  Same convention as
        AUDIT-C."""
        assert DUDIT_CUTOFF_UNSPECIFIED == DUDIT_CUTOFF_FEMALE

    def test_instrument_version_pinned(self) -> None:
        assert INSTRUMENT_VERSION == "dudit-1.0.0"


# ---------------------------------------------------------------------------
# Total correctness
# ---------------------------------------------------------------------------


class TestTotalCorrectness:
    """Total is the straight sum — items 1-9 contribute 0-36, items
    10-11 contribute 0-8, range 0-44."""

    def test_minimum_total_is_zero(self) -> None:
        """Every item's lowest valid value is 0 — total min is 0."""
        r = score_dudit([0] * 11)
        assert r.total == 0

    def test_maximum_total_is_forty_four(self) -> None:
        """Items 1-9 maxed (9×4=36) plus items 10-11 maxed (2×4=8) = 44."""
        r = score_dudit([4] * 9 + [4, 4])
        assert r.total == 44

    def test_likert_items_only(self) -> None:
        """Items 10-11 at 0 — total is pure Likert sum."""
        r = score_dudit([2, 3, 2, 1, 4, 2, 3, 1, 2, 0, 0])
        assert r.total == 20

    def test_trinary_items_only(self) -> None:
        """All Likert items 0, items 10-11 at 4 — total = 8."""
        r = score_dudit([0] * 9 + [4, 4])
        assert r.total == 8

    def test_mixed_sum(self) -> None:
        r = score_dudit([1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 0])
        assert r.total == 11

    def test_trinary_two_values(self) -> None:
        """Trinary item at 2 (yes but not last year) counts as 2."""
        r = score_dudit([0] * 9 + [2, 2])
        assert r.total == 4


# ---------------------------------------------------------------------------
# Sex-keyed cutoff selection
# ---------------------------------------------------------------------------


class TestSexCutoffs:
    """Cutoff keyed by sex per Berman 2005 — the load-bearing clinical
    decision lives here."""

    def test_male_positive_at_six(self) -> None:
        r = score_dudit([1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0], sex="male")
        assert r.total == 6
        assert r.cutoff_used == 6
        assert r.positive_screen is True

    def test_male_negative_at_five(self) -> None:
        r = score_dudit([1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0], sex="male")
        assert r.total == 5
        assert r.cutoff_used == 6
        assert r.positive_screen is False

    def test_female_positive_at_two(self) -> None:
        r = score_dudit([1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0], sex="female")
        assert r.total == 2
        assert r.cutoff_used == 2
        assert r.positive_screen is True

    def test_female_negative_at_one(self) -> None:
        r = score_dudit([1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], sex="female")
        assert r.total == 1
        assert r.cutoff_used == 2
        assert r.positive_screen is False

    def test_unspecified_uses_female_cutoff(self) -> None:
        """Safety-conservatism — same as AUDIT-C."""
        r = score_dudit([1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0], sex="unspecified")
        assert r.cutoff_used == 2
        assert r.positive_screen is True

    def test_sex_defaults_to_unspecified(self) -> None:
        """Omitting sex lands on the conservative female cutoff."""
        r = score_dudit([1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0])
        assert r.sex == "unspecified"
        assert r.cutoff_used == 2
        assert r.positive_screen is True

    def test_same_total_differs_across_sexes(self) -> None:
        """Total 4 — below male cutoff (6), above female cutoff (2).
        This is the load-bearing wire shape for sex-keyed cutoffs.
        The scorer must produce opposite positive_screen values for
        the same total depending on sex."""
        items = [1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0]
        m = score_dudit(items, sex="male")
        f = score_dudit(items, sex="female")
        assert m.total == f.total == 4
        assert m.positive_screen is False
        assert f.positive_screen is True

    def test_sex_echoed_in_result(self) -> None:
        r = score_dudit([0] * 11, sex="male")
        assert r.sex == "male"

    def test_male_at_cutoff_boundary_positive(self) -> None:
        """Boundary — total=6 flips male to positive."""
        r = score_dudit([2, 2, 2, 0, 0, 0, 0, 0, 0, 0, 0], sex="male")
        assert r.total == 6
        assert r.positive_screen is True

    def test_female_at_cutoff_boundary_positive(self) -> None:
        r = score_dudit([2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], sex="female")
        assert r.total == 2
        assert r.positive_screen is True


# ---------------------------------------------------------------------------
# Item-count validation
# ---------------------------------------------------------------------------


class TestItemCountValidation:
    """Exact count = 11.  Any other length is a 422, not a silent score."""

    def test_rejects_zero_items(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 11 items"):
            score_dudit([])

    def test_rejects_ten_items(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 11 items"):
            score_dudit([0] * 10)

    def test_rejects_twelve_items(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 11 items"):
            score_dudit([0] * 12)

    def test_rejects_three_items_auditc_misroute(self) -> None:
        """3 items is AUDIT-C territory — must NOT silently score as DUDIT."""
        with pytest.raises(InvalidResponseError, match="exactly 11 items"):
            score_dudit([0, 0, 0])

    def test_rejects_five_items_sds_misroute(self) -> None:
        """5 items is SDS territory — must NOT silently score as DUDIT."""
        with pytest.raises(InvalidResponseError, match="exactly 11 items"):
            score_dudit([0, 0, 0, 0, 0])


# ---------------------------------------------------------------------------
# Item-range validation — the NOVEL non-uniform validator
# ---------------------------------------------------------------------------


class TestLikertItemRange:
    """Items 1-9 must be within [0, 4].  No coercion, no clamping."""

    @pytest.mark.parametrize("bad_value", [-1, 5, 6, 10])
    def test_rejects_out_of_range_likert(self, bad_value: int) -> None:
        with pytest.raises(InvalidResponseError, match="out of range"):
            score_dudit([bad_value] + [0] * 10)

    def test_rejects_negative_at_last_likert_position(self) -> None:
        """Item 9 is the last Likert slot."""
        with pytest.raises(InvalidResponseError, match="item 9"):
            score_dudit([0] * 8 + [-1, 0, 0])

    def test_rejects_five_at_likert_item(self) -> None:
        """5 is the canonical 'off by one' for a 0-4 Likert."""
        with pytest.raises(InvalidResponseError, match="item 1"):
            score_dudit([5] + [0] * 10)


class TestTrinaryItemRange:
    """Items 10-11 must be within {0, 2, 4}.  Values 1 or 3 are
    rejected even though they fall within 0-4.  This is the novel
    validator shape of DUDIT."""

    def test_rejects_one_at_item_ten(self) -> None:
        """1 is within 0-4 but NOT in the trinary set — must reject."""
        with pytest.raises(InvalidResponseError, match="item 10"):
            score_dudit([0] * 9 + [1, 0])

    def test_rejects_three_at_item_ten(self) -> None:
        """3 is within 0-4 but NOT in the trinary set."""
        with pytest.raises(InvalidResponseError, match="item 10"):
            score_dudit([0] * 9 + [3, 0])

    def test_rejects_one_at_item_eleven(self) -> None:
        with pytest.raises(InvalidResponseError, match="item 11"):
            score_dudit([0] * 10 + [1])

    def test_rejects_three_at_item_eleven(self) -> None:
        with pytest.raises(InvalidResponseError, match="item 11"):
            score_dudit([0] * 10 + [3])

    def test_rejects_five_at_trinary_item(self) -> None:
        """5 is out-of-range in both validators — must reject at
        trinary position with the trinary message."""
        with pytest.raises(InvalidResponseError, match="item 10"):
            score_dudit([0] * 9 + [5, 0])

    def test_rejects_negative_at_trinary_item(self) -> None:
        with pytest.raises(InvalidResponseError, match="item 10"):
            score_dudit([0] * 9 + [-1, 0])

    def test_trinary_message_mentions_values(self) -> None:
        """Error message names the legal values so a clinician
        reading the error understands the yes/not-last-year/last-year
        semantic."""
        with pytest.raises(InvalidResponseError, match="0, 2, or 4"):
            score_dudit([0] * 9 + [1, 0])

    def test_accepts_zero_at_trinary(self) -> None:
        """Zero is legal — the 'No' response."""
        r = score_dudit([0] * 9 + [0, 0])
        assert r.total == 0

    def test_accepts_two_at_trinary(self) -> None:
        """Two is legal — 'Yes, but not in the last year'."""
        r = score_dudit([0] * 9 + [2, 0])
        assert r.total == 2

    def test_accepts_four_at_trinary(self) -> None:
        """Four is legal — 'Yes, during the last year'."""
        r = score_dudit([0] * 9 + [4, 0])
        assert r.total == 4


class TestItemTypeValidation:
    """Item values must be plain int."""

    def test_rejects_string_item(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_dudit([1, 1, "2", 1, 0, 0, 0, 0, 0, 0, 0])  # type: ignore[list-item]

    def test_rejects_float_item(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_dudit([1, 1, 2.5, 1, 0, 0, 0, 0, 0, 0, 0])  # type: ignore[list-item]

    def test_rejects_none_item(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_dudit([1, 1, None, 1, 0, 0, 0, 0, 0, 0, 0])  # type: ignore[list-item]

    def test_rejects_string_at_trinary_item(self) -> None:
        """Non-int values must be rejected BEFORE the trinary check —
        a caller submitting ``"0"`` should see the type error, not
        the trinary error."""
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_dudit([0] * 9 + ["0", 0])  # type: ignore[list-item]


class TestBoolRejection:
    """Uniform with the rest of the package — bool is not a valid
    item value, even though ``True == 1`` and ``False == 0`` in Python."""

    def test_rejects_true_at_likert_item(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_dudit([True, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])  # type: ignore[list-item]

    def test_rejects_false_at_likert_item(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_dudit([False, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])  # type: ignore[list-item]

    def test_rejects_true_at_trinary_item(self) -> None:
        """``True == 1`` would falsely pass a trinary-values check if
        the type guard wasn't first — pins ordering."""
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_dudit([0] * 9 + [True, 0])  # type: ignore[list-item]

    def test_rejects_false_at_trinary_item(self) -> None:
        """``False == 0`` is in the trinary set — but bool must still
        be rejected before the trinary check runs."""
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_dudit([0] * 9 + [False, 0])  # type: ignore[list-item]


# ---------------------------------------------------------------------------
# Result shape
# ---------------------------------------------------------------------------


class TestResultShape:
    """Pin the DuditResult dataclass shape — no drift, no surprise
    fields."""

    def test_result_is_frozen(self) -> None:
        r = score_dudit([0] * 11)
        with pytest.raises(Exception):  # FrozenInstanceError subclass
            r.total = 99  # type: ignore[misc]

    def test_result_has_no_severity_field(self) -> None:
        """DUDIT uses cutoff envelope, not banded envelope — no
        ``severity`` attribute on the scorer result.  Berman 2005 did
        not publish a banded severity scale."""
        r = score_dudit([0] * 11)
        assert not hasattr(r, "severity")

    def test_result_has_no_requires_t3_field(self) -> None:
        """DUDIT has no safety item — no ``requires_t3`` on the result."""
        r = score_dudit([4] * 9 + [4, 4])
        assert not hasattr(r, "requires_t3")

    def test_result_has_no_subscales_field(self) -> None:
        """Berman 2003 validated DUDIT as unidimensional at the
        screening-score level — no wire-exposed subscales."""
        r = score_dudit([0] * 11)
        assert not hasattr(r, "subscales")

    def test_result_carries_instrument_version(self) -> None:
        r = score_dudit([0] * 11)
        assert r.instrument_version == "dudit-1.0.0"

    def test_result_carries_cutoff_used(self) -> None:
        r = score_dudit([0] * 11, sex="male")
        assert r.cutoff_used == 6

    def test_result_carries_sex(self) -> None:
        r = score_dudit([0] * 11, sex="female")
        assert r.sex == "female"

    def test_result_echoes_items_verbatim(self) -> None:
        r = score_dudit([1, 2, 3, 4, 0, 1, 2, 3, 4, 2, 4])
        assert r.items == (1, 2, 3, 4, 0, 1, 2, 3, 4, 2, 4)

    def test_result_items_is_tuple(self) -> None:
        r = score_dudit([0] * 11)
        assert isinstance(r.items, tuple)

    def test_result_is_duditresult_instance(self) -> None:
        r = score_dudit([0] * 11)
        assert isinstance(r, DuditResult)


# ---------------------------------------------------------------------------
# Clinical vignettes
# ---------------------------------------------------------------------------


class TestClinicalVignettes:
    """Realistic patient scenarios pinning clinical interpretation."""

    def test_abstinent_vignette(self) -> None:
        """Patient who doesn't use drugs — every item at 0, total 0."""
        r = score_dudit([0] * 11, sex="unspecified")
        assert r.total == 0
        assert r.positive_screen is False

    def test_low_use_male_below_cutoff(self) -> None:
        """Male patient with occasional cannabis use, no consequences.
        Total 3 — below male cutoff (6) but would be positive for a
        female patient.  Pins the sex-keyed asymmetry clinically."""
        r = score_dudit([2, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0], sex="male")
        assert r.total == 3
        assert r.positive_screen is False

    def test_low_use_female_above_cutoff(self) -> None:
        """Same response pattern as the low-use-male vignette but
        scored as a female patient — positive screen.  This is the
        load-bearing sex-keyed clinical decision."""
        r = score_dudit([2, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0], sex="female")
        assert r.total == 3
        assert r.positive_screen is True

    def test_problem_drug_use_male(self) -> None:
        """Male patient with weekly use, loss of control, and one
        historical consequence.  Total 10 — positive screen."""
        r = score_dudit([3, 1, 2, 1, 1, 0, 0, 0, 0, 2, 0], sex="male")
        assert r.total == 10
        assert r.positive_screen is True

    def test_severe_use_vignette(self) -> None:
        """Daily use, loss of control, morning-after use, consequences
        in the last year.  Total high — positive screen for both
        sexes."""
        r = score_dudit([4, 2, 3, 3, 3, 2, 2, 2, 2, 4, 4], sex="male")
        assert r.total == 31
        assert r.positive_screen is True

    def test_historical_only_consequences(self) -> None:
        """Patient with historical drug consequences (items 10-11 at 2 —
        'yes but not in the last year') but no current use.  Items 1-9
        all at 0; items 10-11 at 2 each → total = 4.  Positive for a
        female, negative for a male — clinical judgement call on
        follow-up."""
        r_m = score_dudit([0] * 9 + [2, 2], sex="male")
        r_f = score_dudit([0] * 9 + [2, 2], sex="female")
        assert r_m.total == r_f.total == 4
        assert r_m.positive_screen is False
        assert r_f.positive_screen is True


# ---------------------------------------------------------------------------
# No safety routing — invariant pin
# ---------------------------------------------------------------------------


class TestNoSafetyRouting:
    """DUDIT has no suicidality item.  No combination of responses
    fires T3.  The scorer doesn't even expose requires_t3 — this
    class pins the invariant against future accidental addition."""

    def test_all_max_items_do_not_fire_t3(self) -> None:
        r = score_dudit([4] * 9 + [4, 4], sex="male")
        assert not hasattr(r, "requires_t3")
        assert r.positive_screen is True

    def test_loss_of_control_items_alone_do_not_fire_t3(self) -> None:
        """Items 4 (heavily influenced), 5 (irresistible longing), 6
        (can't stop) maxed — loss-of-control signal, not intent."""
        r = score_dudit([0, 0, 0, 4, 4, 4, 0, 0, 0, 0, 0], sex="female")
        assert not hasattr(r, "requires_t3")

    def test_self_harm_consequence_item_does_not_fire_t3(self) -> None:
        """Item 10 probes 'have you or anyone else been hurt' — but
        the hurt can be physical, mental, social, or legal; this is
        NOT a suicidality item.  Routing T3 off DUDIT item 10 would
        be a false positive against the acute-ideation workflow."""
        r = score_dudit([0] * 9 + [4, 0], sex="female")
        assert not hasattr(r, "requires_t3")
        assert r.positive_screen is True

    def test_third_party_concern_item_does_not_fire_t3(self) -> None:
        """Item 11 is a clinician-concern item — still not
        suicidality."""
        r = score_dudit([0] * 9 + [0, 4], sex="female")
        assert not hasattr(r, "requires_t3")

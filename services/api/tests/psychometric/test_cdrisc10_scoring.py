"""CD-RISC-10 scoring tests — Campbell-Sills & Stein 2007.

Four load-bearing correctness properties for the 10-item CD-RISC-10:

1. **Higher-is-better directionality.**  Unlike PHQ-9 / GAD-7 / DERS-16
   / PCL-5 / OCI-R / K10 / WSAS (higher = worse), CD-RISC-10 is in the
   positive-resilience direction uniform with WHO-5 / DTCQ-8 /
   Readiness Ruler.  A floor score (0) is the most concerning outcome;
   a ceiling score (40) is the best outcome.  Dashboards and
   trajectory renderers that reuse higher-is-worse visual language
   would misread this instrument.
2. **No severity bands emitted.**  Campbell-Sills & Stein 2007
   reported general-population means (31.8 ± 5.4) but NO
   cross-calibrated banded thresholds.  Connor & Davidson 2003
   reported cuts for the 25-item scale that do not translate
   linearly to the 10-item form.  Per CLAUDE.md "don't hand-roll
   severity thresholds", the scorer ships as a continuous dimensional
   measure — the dataclass deliberately omits ``severity`` /
   ``cutoff_used`` / ``positive_screen`` fields.  The router emits
   ``severity="continuous"`` as a sentinel.
3. **Exactly 10 items, each 0-4 Likert.**  Minimum 0 (not 1) because
   the lowest Likert response is 0 ("not true at all") — same floor
   semantic as PHQ-9 / GAD-7 / OCI-R / AUDIT / DAST-10, distinct from
   K10 / K6 / AAQ-II / DERS-16 which floor at 1.
4. **Unidimensional — no subscales.**  Campbell-Sills & Stein 2007
   CFA validated the single-factor structure; the original 25-item's
   five-factor split was explicitly rejected for the 10-item form.
   The result dataclass emits no subscale fields.

Coverage strategy:
- Pin the constants (item count, range, instrument version).
- Total-correctness tests across floor / ceiling / midpoint / mixed.
- Item-count validation (10) including misroute checks against PHQ-9,
  GAD-7, WSAS, DERS-16 item counts.
- Item-range validation (0-4) including PHQ-9-adjacent 5 rejection
  (PHQ-15 floors 0-3; CD-RISC-10 and OCI-R ceil at 4).
- Bool rejection.
- Clinical vignettes — high-resilience floor/ceiling/general-pop-mean
  patterns that drive intervention-scaffolding decisions.
- No severity / cutoff / subscales / safety fields.
"""

from __future__ import annotations

import pytest

from discipline.psychometric.scoring.cdrisc10 import (
    INSTRUMENT_VERSION,
    ITEM_COUNT,
    ITEM_MAX,
    ITEM_MIN,
    Cdrisc10Result,
    InvalidResponseError,
    score_cdrisc10,
)


def _floor() -> list[int]:
    """Return a 10-item list at the Likert floor (0 = 'not true at
    all').  CD-RISC-10 minimum total is 0 (lowest resilience)."""
    return [ITEM_MIN] * ITEM_COUNT


def _ceiling() -> list[int]:
    """Return a 10-item list at the Likert ceiling (4 = 'true nearly
    all the time').  CD-RISC-10 maximum total is 40 (highest
    resilience)."""
    return [ITEM_MAX] * ITEM_COUNT


class TestConstants:
    """Pin published constants so a drift from Campbell-Sills & Stein
    2007 is caught."""

    def test_item_count_is_ten(self) -> None:
        assert ITEM_COUNT == 10

    def test_item_range_is_zero_to_four(self) -> None:
        """Campbell-Sills & Stein 2007 used Connor 2003's original
        0-4 Likert ('not true at all' to 'true nearly all the time').
        Distinct from DERS-16's 1-5 floor."""
        assert ITEM_MIN == 0
        assert ITEM_MAX == 4

    def test_instrument_version_pinned(self) -> None:
        assert INSTRUMENT_VERSION == "cdrisc10-1.0.0"


class TestTotalCorrectness:
    """Straight 0-40 sum (no reverse-coding — all items positively
    worded per Campbell-Sills & Stein 2007)."""

    def test_floor_is_zero(self) -> None:
        """Minimum total is 0 — 10 items × floor 0.  This is the
        LOWEST resilience score, i.e. the worst outcome on this
        instrument (direction-reversal from PHQ-9 / GAD-7 / DERS-16
        etc. where 0 is best)."""
        result = score_cdrisc10(_floor())
        assert result.total == 0

    def test_ceiling_is_forty(self) -> None:
        """Maximum total is 40 — 10 items × ceiling 4.  This is the
        HIGHEST resilience score, i.e. the best outcome."""
        result = score_cdrisc10(_ceiling())
        assert result.total == 40

    def test_mixed_sum(self) -> None:
        """Arbitrary mix — verifies the total is a plain sum."""
        items = [0, 1, 2, 3, 4, 0, 1, 2, 3, 4]
        result = score_cdrisc10(items)
        assert result.total == sum(items)

    def test_near_general_population_mean(self) -> None:
        """Campbell-Sills & Stein 2007 reported U.S. general-adult mean
        of 31.8 ± 5.4 (N=764).  A score at the mean is the reference
        point for 'below-population' clinical flagging."""
        # 9 items at 3, 1 item at 5 not possible (ceiling 4).
        # Use 8 × 3 + 2 × 4 = 32, at the mean.
        items = [3, 3, 3, 3, 3, 3, 3, 3, 4, 4]
        result = score_cdrisc10(items)
        assert result.total == 32

    def test_single_item_change_propagates(self) -> None:
        """Moving one item from 0 → 4 changes total by 4.  Pins the
        sum is element-wise."""
        baseline = score_cdrisc10(_floor())
        items = _floor()
        items[0] = 4
        bumped = score_cdrisc10(items)
        assert bumped.total == baseline.total + 4


class TestItemCountValidation:
    """Exactly 10 items required.  Misroutes from neighboring
    instruments (PHQ-9 at 9, GAD-7 at 7, WSAS at 5, DERS-16 at 16,
    OCI-R at 18, AUDIT at 10 — exact same count!) must fail loudly."""

    def test_rejects_nine_items(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 10 items"):
            score_cdrisc10([3] * 9)

    def test_rejects_eleven_items(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 10 items"):
            score_cdrisc10([3] * 11)

    def test_rejects_empty(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 10 items"):
            score_cdrisc10([])

    def test_rejects_ders16_count(self) -> None:
        """16-item payload from DERS-16 misroute should fail cleanly.
        CD-RISC-10 and DERS-16 both measure process-level constructs;
        a dispatch swap is a plausible mis-routing risk."""
        with pytest.raises(InvalidResponseError, match="exactly 10 items"):
            score_cdrisc10([3] * 16)

    def test_rejects_phq9_count(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 10 items"):
            score_cdrisc10([3] * 9)

    def test_rejects_wsas_count(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 10 items"):
            score_cdrisc10([3] * 5)


class TestItemRangeValidation:
    """Items must be in [0, 4]."""

    @pytest.mark.parametrize("bad_value", [-1, -5, 5, 6, 100, 255])
    def test_rejects_out_of_range(self, bad_value: int) -> None:
        items = _floor()
        items[5] = bad_value
        with pytest.raises(InvalidResponseError, match="out of range"):
            score_cdrisc10(items)

    def test_rejects_five_item(self) -> None:
        """5 is above the Likert ceiling.  Distinct from DERS-16 and
        K10 where 5 is valid (1-5 range); a client that submitted
        DERS-16-like items into a CD-RISC-10 dispatch would fail
        here, not silently over-score."""
        items = _floor()
        items[0] = 5
        with pytest.raises(InvalidResponseError, match="out of range"):
            score_cdrisc10(items)

    def test_rejects_negative_one_item(self) -> None:
        items = _floor()
        items[0] = -1
        with pytest.raises(InvalidResponseError, match="out of range"):
            score_cdrisc10(items)

    def test_error_names_one_indexed_item(self) -> None:
        """Error messages use 1-indexed item numbers to match the
        CD-RISC-10 instrument document."""
        items = _floor()
        items[9] = 99  # item 10 (last item)
        with pytest.raises(InvalidResponseError, match="CD-RISC-10 item 10"):
            score_cdrisc10(items)

    def test_rejects_string_item(self) -> None:
        items = _floor()
        items[0] = "3"  # type: ignore[call-overload]
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_cdrisc10(items)

    def test_rejects_float_item(self) -> None:
        items = _floor()
        items[0] = 3.0  # type: ignore[call-overload]
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_cdrisc10(items)

    def test_rejects_none_item(self) -> None:
        items = _floor()
        items[0] = None  # type: ignore[call-overload]
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_cdrisc10(items)


class TestBoolRejection:
    """Bool items rejected even though True/False map to valid 1/0.
    Rationale: uniform wire contract across the psychometric package.
    """

    def test_rejects_true_item(self) -> None:
        items = _floor()
        items[0] = True  # type: ignore[call-overload]
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_cdrisc10(items)

    def test_rejects_false_item(self) -> None:
        items = _floor()
        items[0] = False  # type: ignore[call-overload]
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_cdrisc10(items)

    def test_rejects_true_at_last_position(self) -> None:
        """Guard against off-by-one in bool check — item 10 is last."""
        items = _floor()
        items[9] = True  # type: ignore[call-overload]
        with pytest.raises(InvalidResponseError, match="CD-RISC-10 item 10"):
            score_cdrisc10(items)


class TestResultShape:
    """Cdrisc10Result carries the fields the router envelope needs and
    deliberately OMITS fields that would falsely imply banded severity,
    a cutoff decision, subscales, or a safety trigger.
    """

    def test_result_is_frozen(self) -> None:
        result = score_cdrisc10(_floor())
        with pytest.raises(Exception):  # FrozenInstanceError subclass
            result.total = 99  # type: ignore[misc]

    def test_items_are_tuple(self) -> None:
        items = [0, 1, 2, 3, 4, 0, 1, 2, 3, 4]
        result = score_cdrisc10(items)
        assert isinstance(result.items, tuple)
        assert result.items == tuple(items)

    def test_result_echoes_instrument_version(self) -> None:
        result = score_cdrisc10(_floor())
        assert result.instrument_version == INSTRUMENT_VERSION

    def test_no_severity_field(self) -> None:
        """Campbell-Sills & Stein 2007 published no bands.  The scorer
        must NOT emit ``severity`` — the router attaches the
        ``"continuous"`` sentinel at the envelope layer."""
        result = score_cdrisc10(_ceiling())
        assert not hasattr(result, "severity")

    def test_no_cutoff_used_field(self) -> None:
        """Continuous instrument — no cutoff shape."""
        result = score_cdrisc10(_ceiling())
        assert not hasattr(result, "cutoff_used")

    def test_no_positive_screen_field(self) -> None:
        """Continuous instrument — no screen decision."""
        result = score_cdrisc10(_ceiling())
        assert not hasattr(result, "positive_screen")

    def test_no_requires_t3_field(self) -> None:
        """No safety item — scorer must not expose T3 routing."""
        result = score_cdrisc10(_ceiling())
        assert not hasattr(result, "requires_t3")

    def test_no_triggering_items_field(self) -> None:
        result = score_cdrisc10(_ceiling())
        assert not hasattr(result, "triggering_items")

    def test_no_subscales_fields(self) -> None:
        """Campbell-Sills & Stein 2007 CFA: unidimensional.  The
        original 25-item's five-factor split was explicitly rejected
        for the 10-item form — the scorer exposes no subscale_*
        fields."""
        result = score_cdrisc10(_ceiling())
        for attr_name in (
            "subscale_adaptability",
            "subscale_persistence",
            "subscale_control",
            "subscale_spirituality",
            "subscale_competence",
            "subscales",
        ):
            assert not hasattr(result, attr_name), (
                f"CD-RISC-10 exposed unexpected subscale field "
                f"{attr_name!r} — Campbell-Sills & Stein 2007 "
                f"validates unidimensional structure"
            )

    def test_result_is_cdrisc10_result_type(self) -> None:
        result = score_cdrisc10(_floor())
        assert isinstance(result, Cdrisc10Result)

    def test_total_is_int(self) -> None:
        result = score_cdrisc10(_floor())
        assert isinstance(result.total, int)
        assert not isinstance(result.total, bool)


class TestClinicalVignettes:
    """Named patterns a clinician would recognize.  Total-level
    interpretation per Campbell-Sills & Stein 2007 general-population
    norms (mean 31.8 ± 5.4).
    """

    def test_minimum_resilience(self) -> None:
        """All items at 0 — total 0, the floor of the resilience
        construct.  This is the MOST concerning outcome (direction-
        reversed from symptom measures).  Clinically indicates
        heavy intervention scaffolding and longer-horizon work,
        not a crisis gate."""
        result = score_cdrisc10(_floor())
        assert result.total == 0

    def test_maximum_resilience(self) -> None:
        """All items at 4 — total 40, the ceiling.  This is the BEST
        outcome on the instrument.  Useful as a pre-recovery baseline
        when the patient rebuilds resilience and as a ceiling-effect
        sanity check on the trajectory layer."""
        result = score_cdrisc10(_ceiling())
        assert result.total == 40

    def test_below_general_population_mean(self) -> None:
        """Total 25, ~1 SD below the Campbell-Sills & Stein 2007
        general-population mean of 31.8 ± 5.4.  The clinician UI
        layer can surface this as a 'below general-population
        resilience' flag (NOT a classification, NOT a gate) to inform
        intervention-scaffolding intensity.  Pinned here as a named
        clinical vignette so a future regression that accidentally
        hand-rolled severity bands would surface explicitly."""
        items = [2, 2, 3, 2, 3, 2, 3, 2, 3, 3]
        result = score_cdrisc10(items)
        assert result.total == 25

    def test_at_general_population_mean(self) -> None:
        """Total 32, at the Campbell-Sills & Stein 2007 mean.
        Reference 'typical-resilience' profile."""
        items = [3, 3, 3, 3, 3, 3, 3, 3, 4, 4]
        result = score_cdrisc10(items)
        assert result.total == 32

    def test_above_general_population_mean(self) -> None:
        """Total 38, ~1 SD above the mean.  High-resilience profile;
        common in actively-recovering patients weeks into a coherent
        therapeutic arc."""
        items = [4, 4, 4, 3, 4, 4, 4, 4, 3, 4]
        result = score_cdrisc10(items)
        assert result.total == 38

    def test_mixed_moderate_pattern(self) -> None:
        """Uniform moderate endorsement (all items at 2 — 'sometimes
        true') — total 20, midpoint of the scale."""
        items = [2] * 10
        result = score_cdrisc10(items)
        assert result.total == 20


class TestNoSafetyRouting:
    """CD-RISC-10 has no direct suicidality / self-harm item.  Item
    10 ("can handle unpleasant or painful feelings like sadness, fear,
    and anger") probes distress-tolerance capacity — the INVERSE of
    what a crisis item probes (not 'do you want to end it', but 'can
    you hold the feelings without reaction').  The scorer must not
    expose anything the router could mistake for a T3 trigger.
    """

    def test_floor_has_no_safety_field(self) -> None:
        """Even the lowest-resilience outcome (total 0) carries no
        safety-routing fields.  A naive renderer that tried to key
        off 'total == 0 → escalate' would over-fire and desensitize
        the safety queue — low resilience is a scaffolding signal,
        not a crisis signal."""
        result = score_cdrisc10(_floor())
        assert not hasattr(result, "requires_t3")
        assert not hasattr(result, "t3_reason")
        assert not hasattr(result, "safety_item_positive")
        assert not hasattr(result, "triggering_items")

    def test_max_has_no_safety_field(self) -> None:
        result = score_cdrisc10(_ceiling())
        assert not hasattr(result, "requires_t3")

    def test_item_ten_alone_has_no_safety_field(self) -> None:
        """Item 10 probes distress-tolerance; even if it alone is at
        floor (patient reports no capacity to handle painful feelings),
        the scorer does NOT escalate.  Low CD-RISC-10 item 10 in
        isolation is an intervention-selection signal (DBT distress-
        tolerance skills), not a crisis signal.  Acute ideation
        screening is on PHQ-9 item 9 / C-SSRS."""
        items = [4, 4, 4, 4, 4, 4, 4, 4, 4, 0]  # only item 10 at floor
        result = score_cdrisc10(items)
        assert not hasattr(result, "requires_t3")

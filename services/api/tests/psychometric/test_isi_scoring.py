"""ISI scoring tests — Bastien 2001 / Morin 2011.

Two load-bearing correctness properties for the 7-item ISI:

1. **Four-band severity classification.**  Bastien 2001 Table 2
   fixes exactly four severity bands with specific upper bounds:
   0-7 none, 8-14 subthreshold, 15-21 moderate, 22-28 severe.  A
   fence-post mistake (``<`` vs ``<=``) at any band boundary would
   misclassify precisely the patients where clinical decision-making
   matters most — the boundary tests pin every cutover point
   explicitly.
2. **7 items, each 0-4 Likert.**  Total range is 0-28 — any item
   value outside ``[0, 4]`` is a validation error, not a silent
   clamp.  PHQ-9 uses 0-3 and PSS-10 uses 0-4 reverse-coded; ISI's
   0-4 uniform direction is distinct from both and must be tested
   independently to avoid a copy-paste regression.

Coverage strategy:
- Pin every severity-band boundary: 7/8, 14/15, 21/22.
- Pin zero and max total.
- Exhaustively pin item validation at each position (bool, out-of-
  range, non-int).
- Item-count validation (6, 8, empty).
- Result shape: frozen, tuple items, no safety-routing fields.
- Clinical vignettes at each band — a clinician's mental model
  should match the scorer output.
"""

from __future__ import annotations

import pytest

from discipline.psychometric.scoring.isi import (
    INSTRUMENT_VERSION,
    ISI_SEVERITY_THRESHOLDS,
    ITEM_COUNT,
    ITEM_MAX,
    ITEM_MIN,
    InvalidResponseError,
    IsiResult,
    score_isi,
)


def _items_with_total(total: int) -> list[int]:
    """Build a 7-item list that sums to ``total``.

    ISI is a straight sum, so position doesn't affect the score.
    Fill items 1..7 with ``4``s until we've accumulated most of the
    total, then pad the remainder onto a single item and zero out
    the rest — keeps the helper readable and lets each test write
    ``_items_with_total(15)`` rather than an inline 7-item list.
    """
    if total < 0 or total > ITEM_COUNT * ITEM_MAX:
        raise ValueError(
            f"total must be in [0, {ITEM_COUNT * ITEM_MAX}], got {total}"
        )
    items = [0] * ITEM_COUNT
    remaining = total
    for i in range(ITEM_COUNT):
        allocation = min(ITEM_MAX, remaining)
        items[i] = allocation
        remaining -= allocation
        if remaining == 0:
            break
    return items


class TestConstants:
    """Pin published constants so a drift from Bastien 2001 is caught."""

    def test_item_count_is_seven(self) -> None:
        assert ITEM_COUNT == 7

    def test_item_range_is_zero_to_four(self) -> None:
        assert ITEM_MIN == 0
        assert ITEM_MAX == 4

    def test_severity_thresholds_match_bastien_2001(self) -> None:
        """The four published bands (Bastien 2001 Table 2).  A change
        to any upper bound is a clinical change and must cite a
        replacement paper, not be a silent refactor."""
        assert ISI_SEVERITY_THRESHOLDS == (
            (7, "none"),
            (14, "subthreshold"),
            (21, "moderate"),
            (28, "severe"),
        )

    def test_instrument_version_pinned(self) -> None:
        assert INSTRUMENT_VERSION == "isi-1.0.0"


class TestSeverityBoundaries:
    """Every band boundary pinned just-below and at-cutoff so a
    fence-post regression is caught immediately."""

    def test_zero_total_is_none(self) -> None:
        result = score_isi([0, 0, 0, 0, 0, 0, 0])
        assert result.total == 0
        assert result.severity == "none"

    def test_total_seven_is_upper_none(self) -> None:
        """Upper bound of the ``none`` band.  A ``<`` bug would push
        this to subthreshold."""
        result = score_isi(_items_with_total(7))
        assert result.total == 7
        assert result.severity == "none"

    def test_total_eight_is_lower_subthreshold(self) -> None:
        """First total in the subthreshold band.  A ``<=`` bug on the
        upper bound of ``none`` would leave this mis-classified as
        ``none`` and under-identify an entire clinical population."""
        result = score_isi(_items_with_total(8))
        assert result.total == 8
        assert result.severity == "subthreshold"

    def test_total_fourteen_is_upper_subthreshold(self) -> None:
        result = score_isi(_items_with_total(14))
        assert result.total == 14
        assert result.severity == "subthreshold"

    def test_total_fifteen_is_lower_moderate(self) -> None:
        """The clinical-referral threshold in the community
        validation.  Morin 2011 uses ``>= 15`` as the moderate-or-
        severe gate; a boundary bug here would miss every
        moderate-category patient."""
        result = score_isi(_items_with_total(15))
        assert result.total == 15
        assert result.severity == "moderate"

    def test_total_twenty_one_is_upper_moderate(self) -> None:
        result = score_isi(_items_with_total(21))
        assert result.total == 21
        assert result.severity == "moderate"

    def test_total_twenty_two_is_lower_severe(self) -> None:
        result = score_isi(_items_with_total(22))
        assert result.total == 22
        assert result.severity == "severe"

    def test_total_twenty_eight_is_upper_severe(self) -> None:
        """Maximum possible ISI total — all 7 items at 4."""
        result = score_isi([4, 4, 4, 4, 4, 4, 4])
        assert result.total == 28
        assert result.severity == "severe"


class TestSumCorrectness:
    """The straight-sum operation — no reverse-coding, no weighting."""

    def test_sum_matches_items(self) -> None:
        """ISI items are not reverse-coded (unlike PSS-10 items 4/5/7/8).
        A regression that imported PSS-10's reverse step would produce
        a systematically lower total."""
        result = score_isi([3, 2, 4, 1, 0, 2, 3])
        assert result.total == 15

    def test_symmetry_across_item_positions(self) -> None:
        """Item position doesn't affect the sum — ISI treats all 7
        items equally.  A bug that weighted items 4-7 (the impact
        items) differently from items 1-3 (the sleep-problem items)
        would fail this."""
        a = score_isi([4, 4, 4, 0, 0, 0, 0])
        b = score_isi([0, 0, 0, 0, 4, 4, 4])
        assert a.total == b.total == 12


class TestItemCountValidation:
    """Exactly 7 items required."""

    def test_rejects_six_items(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 7 items"):
            score_isi([0, 0, 0, 0, 0, 0])

    def test_rejects_eight_items(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 7 items"):
            score_isi([0, 0, 0, 0, 0, 0, 0, 0])

    def test_rejects_empty(self) -> None:
        with pytest.raises(InvalidResponseError, match="exactly 7 items"):
            score_isi([])


class TestItemRangeValidation:
    """Items must be in [0, 4] — no Likert-scale shift, no clamp."""

    @pytest.mark.parametrize("bad_value", [-1, 5, 10, 100])
    def test_rejects_out_of_range(self, bad_value: int) -> None:
        items = [0, 0, 0, bad_value, 0, 0, 0]
        with pytest.raises(InvalidResponseError, match="out of range"):
            score_isi(items)

    def test_error_message_names_the_item(self) -> None:
        """Error messages name the 1-indexed item number so clinicians
        map errors to the Bastien 2001 item wording."""
        with pytest.raises(InvalidResponseError, match="ISI item 4"):
            score_isi([0, 0, 0, 99, 0, 0, 0])

    def test_rejects_string_item(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_isi([0, 0, "2", 0, 0, 0, 0])  # type: ignore[list-item]

    def test_rejects_float_item(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_isi([0, 0, 2.0, 0, 0, 0, 0])  # type: ignore[list-item]

    def test_rejects_none_item(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_isi([0, 0, None, 0, 0, 0, 0])  # type: ignore[list-item]


class TestBoolRejection:
    """Bool items rejected even though True/False map to valid 1/0
    values.  Rationale: uniform wire contract across the psychometric
    package.  See scoring/isi.py module docstring.
    """

    def test_rejects_true_item(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_isi([True, 0, 0, 0, 0, 0, 0])  # type: ignore[list-item]

    def test_rejects_false_item(self) -> None:
        with pytest.raises(InvalidResponseError, match="must be int"):
            score_isi([0, 0, 0, False, 0, 0, 0])  # type: ignore[list-item]


class TestResultShape:
    """IsiResult carries the fields the router needs."""

    def test_result_is_frozen(self) -> None:
        result = score_isi([0, 0, 0, 0, 0, 0, 0])
        with pytest.raises(Exception):  # FrozenInstanceError subclass
            result.total = 99  # type: ignore[misc]

    def test_items_are_tuple(self) -> None:
        """Tuple (not list) so IsiResult is hashable and the stored
        repository record is immutable."""
        result = score_isi([1, 2, 3, 4, 0, 1, 2])
        assert isinstance(result.items, tuple)
        assert result.items == (1, 2, 3, 4, 0, 1, 2)

    def test_result_echoes_instrument_version(self) -> None:
        result = score_isi([0, 0, 0, 0, 0, 0, 0])
        assert result.instrument_version == INSTRUMENT_VERSION

    def test_no_requires_t3_field(self) -> None:
        """ISI has no safety item.  The result dataclass deliberately
        omits requires_t3 so downstream routing cannot accidentally
        escalate a severe-insomnia patient into the T3 crisis pathway
        — which would be clinically wrong."""
        result = score_isi([4, 4, 4, 4, 4, 4, 4])
        assert not hasattr(result, "requires_t3")

    def test_no_safety_item_positive_field(self) -> None:
        """PHQ-9 surfaces safety_item_positive because item 9 is a
        suicidality probe.  ISI has no such item; the field must
        not exist on the result."""
        result = score_isi([4, 4, 4, 4, 4, 4, 4])
        assert not hasattr(result, "safety_item_positive")


class TestClinicalVignettes:
    """Named patterns a clinician would recognize."""

    def test_good_sleeper(self) -> None:
        """Patient reports minimal sleep disturbance.  No clinical
        concern — the ``none`` band is exactly this cohort."""
        result = score_isi([1, 0, 0, 0, 0, 1, 0])
        assert result.total == 2
        assert result.severity == "none"

    def test_subthreshold_insomnia(self) -> None:
        """Mild-to-moderate symptoms without functional impairment.
        Bastien 2001 identifies this band as the watch-list group —
        monitor but do not refer."""
        result = score_isi([2, 2, 1, 2, 1, 2, 2])
        assert result.total == 12
        assert result.severity == "subthreshold"

    def test_moderate_clinical_insomnia(self) -> None:
        """Patient reports sleep disturbance AND functional impact
        (items 5/6/7 elevated).  Morin 2011 cutoff for clinical
        referral — route to CBT-I / sleep-medicine consult."""
        result = score_isi([3, 3, 2, 2, 3, 3, 3])
        assert result.total == 19
        assert result.severity == "moderate"

    def test_severe_clinical_insomnia(self) -> None:
        """Patient reports the full symptom cluster with severe
        functional impact.  Urgent CBT-I referral — also a strong
        relapse-risk marker per
        Docs/Whitepapers/02_Clinical_Evidence_Base.md §sleep."""
        result = score_isi([4, 4, 4, 4, 4, 4, 4])
        assert result.total == 28
        assert result.severity == "severe"


class TestNoSafetyRouting:
    """ISI is a CBT-I / sleep-medicine referral signal, not a crisis
    signal.  The scorer must not expose anything a downstream router
    could mistake for a T3 trigger.  The T3 pathway is reserved for
    active suicidality per Docs/Whitepapers/04_Safety_Framework.md §T3.
    """

    def test_max_total_has_no_safety_field(self) -> None:
        result = score_isi([4, 4, 4, 4, 4, 4, 4])
        assert not hasattr(result, "requires_t3")
        assert not hasattr(result, "t3_reason")
        assert not hasattr(result, "triggering_items")
        assert not hasattr(result, "safety_item_positive")

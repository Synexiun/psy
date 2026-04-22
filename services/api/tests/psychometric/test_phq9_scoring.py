"""PHQ-9 scoring fidelity tests.

Source: Kroenke, Spitzer & Williams (2001).  The PHQ-9: Validity of a brief
depression severity measure.  J Gen Intern Med 16(9), 606–613.  Table 3
(severity bands) is the authoritative reference for the boundary tests below.

A failing test in this file is a CLINICAL defect, not a code bug.  Do not
"fix" it by editing expected values.
"""

from __future__ import annotations

import pytest

from discipline.psychometric.scoring.phq9 import (
    INSTRUMENT_VERSION,
    ITEM_COUNT,
    ITEM_MAX,
    ITEM_MIN,
    PHQ9_SAFETY_ITEM_INDEX,
    PHQ9_SEVERITY_THRESHOLDS,
    InvalidResponseError,
    score_phq9,
)

# ---- Severity band boundaries (Kroenke 2001 Table 3) -----------------------


@pytest.mark.parametrize(
    ("total", "expected"),
    [
        (0, "none"),
        (4, "none"),            # upper bound of "none"
        (5, "mild"),            # lower bound of "mild"
        (9, "mild"),            # upper bound of "mild"
        (10, "moderate"),       # lower bound of "moderate"
        (14, "moderate"),       # upper bound of "moderate"
        (15, "moderately_severe"),
        (19, "moderately_severe"),
        (20, "severe"),
        (27, "severe"),         # theoretical maximum
    ],
)
def test_severity_bands_match_kroenke_2001_table3(total: int, expected: str) -> None:
    items = _items_summing_to(total)
    result = score_phq9(items)
    assert result.total == total
    assert result.severity == expected


def test_severity_thresholds_constant_matches_expected_ordering() -> None:
    """The tuple order is load-bearing — _classify walks it in order."""
    uppers = [u for u, _ in PHQ9_SEVERITY_THRESHOLDS]
    assert uppers == sorted(uppers)
    assert uppers[-1] == 27  # full theoretical scale


# ---- Item 9 safety flag (Docs/Whitepapers/04_Safety_Framework.md §T4) -----


@pytest.mark.parametrize("item9_value", [1, 2, 3])
def test_safety_item_positive_when_item9_nonzero(item9_value: int) -> None:
    items = [0] * ITEM_COUNT
    items[PHQ9_SAFETY_ITEM_INDEX] = item9_value
    result = score_phq9(items)
    assert result.safety_item_positive is True


def test_safety_item_zero_when_item9_zero() -> None:
    result = score_phq9([0] * ITEM_COUNT)
    assert result.safety_item_positive is False


def test_safety_item_index_is_zero_indexed_nine() -> None:
    """Item 9 in clinical language = index 8 in Python."""
    assert PHQ9_SAFETY_ITEM_INDEX == 8


# ---- Validation (no partial scoring on error) ------------------------------


@pytest.mark.parametrize("length", [0, 1, 8, 10, 18])
def test_wrong_item_count_raises(length: int) -> None:
    with pytest.raises(InvalidResponseError, match="exactly 9 items"):
        score_phq9([0] * length)


@pytest.mark.parametrize("bad_value", [-1, 4, 5, 100])
def test_item_value_out_of_range_raises(bad_value: int) -> None:
    items = [0] * ITEM_COUNT
    items[3] = bad_value
    with pytest.raises(InvalidResponseError, match="item 4 out of range"):
        score_phq9(items)


def test_item_value_out_of_range_reports_one_indexed_position() -> None:
    """Error messages use clinical (1-indexed) item numbering."""
    items = [0] * ITEM_COUNT
    items[8] = 99
    with pytest.raises(InvalidResponseError) as exc_info:
        score_phq9(items)
    assert "item 9" in str(exc_info.value)


# ---- Result dataclass invariants ------------------------------------------


def test_result_is_frozen() -> None:
    result = score_phq9([0] * ITEM_COUNT)
    with pytest.raises(AttributeError):
        result.total = 99  # type: ignore[misc]


def test_result_echoes_items_as_tuple() -> None:
    raw = [1, 2, 3, 0, 1, 2, 3, 0, 1]
    result = score_phq9(raw)
    assert result.items == tuple(raw)
    assert isinstance(result.items, tuple)


def test_instrument_version_is_pinned() -> None:
    """Version string is written to audit + analytics; downstream consumers
    key on it for back-compat with re-scored assessments."""
    result = score_phq9([0] * ITEM_COUNT)
    assert result.instrument_version == INSTRUMENT_VERSION
    assert INSTRUMENT_VERSION.startswith("phq9-")


def test_maximum_possible_total_is_27() -> None:
    result = score_phq9([3] * ITEM_COUNT)
    assert result.total == 27
    assert result.severity == "severe"
    assert result.safety_item_positive is True


def test_constants_match_clinical_scale() -> None:
    assert ITEM_COUNT == 9
    assert (ITEM_MIN, ITEM_MAX) == (0, 3)


# ---- Helpers ----------------------------------------------------------------


def _items_summing_to(total: int) -> list[int]:
    """Build a valid PHQ-9 item vector that sums to ``total``.

    Greedy fill across all 9 items.  Severity-band tests only inspect the
    total + classification, so whether item 9 happens to be non-zero in the
    constructed vector is immaterial — safety-flag behavior is tested
    separately with explicit item-9 values.
    """
    if total < 0 or total > 27:
        raise AssertionError("test builder called with impossible total")
    items = [0] * ITEM_COUNT
    remainder = total
    for idx in range(ITEM_COUNT):
        bump = min(3, remainder)
        items[idx] = bump
        remainder -= bump
    return items

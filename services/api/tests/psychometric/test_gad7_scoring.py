"""GAD-7 scoring fidelity tests.

Source: Spitzer, Kroenke, Williams & Löwe (2006).  A brief measure for
assessing generalized anxiety disorder: the GAD-7.  Arch Intern Med 166(10),
1092–1097.  Severity bands 0–4 / 5–9 / 10–14 / 15–21 are the authoritative
reference for the boundary tests below.
"""

from __future__ import annotations

import pytest

from discipline.psychometric.scoring.gad7 import (
    GAD7_SEVERITY_THRESHOLDS,
    INSTRUMENT_VERSION,
    ITEM_COUNT,
    ITEM_MAX,
    ITEM_MIN,
    InvalidResponseError,
    score_gad7,
)

# ---- Severity band boundaries (Spitzer 2006) -------------------------------


@pytest.mark.parametrize(
    ("total", "expected"),
    [
        (0, "none"),
        (4, "none"),        # upper bound of "none / minimal"
        (5, "mild"),        # lower bound of "mild"
        (9, "mild"),        # upper bound of "mild"
        (10, "moderate"),
        (14, "moderate"),
        (15, "severe"),     # lower bound of "severe"
        (21, "severe"),     # theoretical maximum
    ],
)
def test_severity_bands_match_spitzer_2006(total: int, expected: str) -> None:
    items = _items_summing_to(total)
    result = score_gad7(items)
    assert result.total == total
    assert result.severity == expected


def test_severity_thresholds_cover_full_scale() -> None:
    uppers = [u for u, _ in GAD7_SEVERITY_THRESHOLDS]
    assert uppers == sorted(uppers)
    assert uppers[-1] == 21  # full theoretical scale


# ---- Validation ------------------------------------------------------------


@pytest.mark.parametrize("length", [0, 1, 6, 8, 9])
def test_wrong_item_count_raises(length: int) -> None:
    with pytest.raises(InvalidResponseError, match="exactly 7 items"):
        score_gad7([0] * length)


@pytest.mark.parametrize("bad_value", [-1, 4, 100])
def test_item_value_out_of_range_raises(bad_value: int) -> None:
    items = [0] * ITEM_COUNT
    items[2] = bad_value
    with pytest.raises(InvalidResponseError, match="item 3 out of range"):
        score_gad7(items)


# ---- Result dataclass invariants ------------------------------------------


def test_result_is_frozen() -> None:
    result = score_gad7([0] * ITEM_COUNT)
    with pytest.raises(AttributeError):
        result.total = 99  # type: ignore[misc]


def test_result_echoes_items_as_tuple() -> None:
    raw = [3, 2, 1, 0, 1, 2, 3]
    result = score_gad7(raw)
    assert result.items == tuple(raw)


def test_instrument_version_is_pinned() -> None:
    result = score_gad7([0] * ITEM_COUNT)
    assert result.instrument_version == INSTRUMENT_VERSION
    assert INSTRUMENT_VERSION.startswith("gad7-")


def test_maximum_possible_total_is_21() -> None:
    result = score_gad7([3] * ITEM_COUNT)
    assert result.total == 21
    assert result.severity == "severe"


def test_minimum_possible_total_is_0() -> None:
    result = score_gad7([0] * ITEM_COUNT)
    assert result.total == 0
    assert result.severity == "none"


def test_constants_match_clinical_scale() -> None:
    assert ITEM_COUNT == 7
    assert (ITEM_MIN, ITEM_MAX) == (0, 3)


# ---- Helpers ---------------------------------------------------------------


def _items_summing_to(total: int) -> list[int]:
    if total < 0 or total > 21:
        raise AssertionError("test builder called with impossible total")
    items = [0] * ITEM_COUNT
    remainder = total
    idx = 0
    while remainder > 0:
        bump = min(3, remainder)
        items[idx] += bump
        remainder -= bump
        idx += 1
    return items

"""Unit tests for pure helpers in discipline.psychometric.router.

_rci_score_for(record) → float
  WHO-5 uses record.index (0-100 scale) not record.total (0-25 raw).
  The published RCI threshold for WHO-5 (17 points) is on the index
  scale.  Passing the raw total (÷4 smaller) would silently compress
  every delta and misclassify clinically meaningful changes as
  no_reliable_change.  All other instruments use record.total directly.

_normalize_instrument_name(raw) → str
  Maps hyphenated web-app names ("phq-9", "gad-7", "who-5", "audit-c")
  to scorer-canonical keys ("phq9", "gad7", "who5", "audit_c").
  The function is the single source-of-truth for this translation; a
  gap here means a client name silently falls through to _stub_band.

_validate_item_count(payload) → None (raises HTTPException 422)
  Enforces per-instrument item count at the router boundary, one layer
  before the scorer raises InvalidResponseError.  Same end behavior,
  but more diagnostic: the error code is "validation.item_count" and
  the message names the expected count.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from discipline.psychometric.repository import AssessmentRecord
from discipline.psychometric.router import (
    _normalize_instrument_name,
    _rci_score_for,
    _validate_item_count,
)

_NOW = datetime(2026, 1, 15, 12, 0, 0, tzinfo=UTC)


def _record(instrument: str, total: int, index: int | None = None) -> AssessmentRecord:
    return AssessmentRecord(
        assessment_id="x",
        user_id="u1",
        instrument=instrument,
        total=total,
        severity="mild",
        requires_t3=False,
        raw_items=(0,) * 9,
        created_at=_NOW,
        index=index,
    )


# ---------------------------------------------------------------------------
# _rci_score_for — WHO-5 index vs raw total
# ---------------------------------------------------------------------------


class TestRciScoreFor:
    def test_phq9_uses_total(self) -> None:
        record = _record("phq9", total=14)
        assert _rci_score_for(record) == 14.0

    def test_gad7_uses_total(self) -> None:
        record = _record("gad7", total=10)
        assert _rci_score_for(record) == 10.0

    def test_pss10_uses_total(self) -> None:
        record = _record("pss10", total=20)
        assert _rci_score_for(record) == 20.0

    def test_audit_c_uses_total(self) -> None:
        record = _record("audit_c", total=5)
        assert _rci_score_for(record) == 5.0

    def test_who5_uses_index_not_total(self) -> None:
        # WHO-5 raw total 15 (0-25) → index 60 (0-100)
        # RCI threshold is on the index scale (17 points)
        record = _record("who5", total=15, index=60)
        assert _rci_score_for(record) == 60.0

    def test_who5_index_not_total_prevents_4x_compression(self) -> None:
        # Using total=15 would give 15.0 — far below the 17-point threshold
        # Using index=60 gives 60.0 — clearly above
        record = _record("who5", total=15, index=60)
        result = _rci_score_for(record)
        assert result != float(record.total)
        assert result == float(record.index)

    def test_who5_with_no_index_falls_back_to_total(self) -> None:
        # If index is None, fall back to total rather than raising
        record = _record("who5", total=20, index=None)
        assert _rci_score_for(record) == 20.0

    def test_returns_float(self) -> None:
        assert isinstance(_rci_score_for(_record("phq9", total=5)), float)


# ---------------------------------------------------------------------------
# _normalize_instrument_name — web-app hyphenated → scorer canonical
# ---------------------------------------------------------------------------


class TestNormalizeInstrumentName:
    def test_phq_9_maps_to_phq9(self) -> None:
        assert _normalize_instrument_name("phq-9") == "phq9"

    def test_gad_7_maps_to_gad7(self) -> None:
        assert _normalize_instrument_name("gad-7") == "gad7"

    def test_who_5_maps_to_who5(self) -> None:
        assert _normalize_instrument_name("who-5") == "who5"

    def test_audit_c_hyphen_maps_to_audit_c_underscore(self) -> None:
        assert _normalize_instrument_name("audit-c") == "audit_c"

    def test_pss_10_maps_to_pss10(self) -> None:
        assert _normalize_instrument_name("pss-10") == "pss10"

    def test_dast_10_maps_to_dast10(self) -> None:
        assert _normalize_instrument_name("dast-10") == "dast10"

    def test_canonical_name_passes_through(self) -> None:
        assert _normalize_instrument_name("phq9") == "phq9"

    def test_unknown_name_passes_through_lowercased(self) -> None:
        assert _normalize_instrument_name("AUDIT") == "audit"

    def test_leading_trailing_whitespace_stripped(self) -> None:
        assert _normalize_instrument_name("  phq-9  ") == "phq9"

    def test_uppercase_hyphenated_normalized(self) -> None:
        assert _normalize_instrument_name("PHQ-9") == "phq9"


# ---------------------------------------------------------------------------
# _validate_item_count — 422 enforcement at router boundary
# ---------------------------------------------------------------------------


def _assessment_request(instrument: str, item_count: int) -> MagicMock:
    req = MagicMock()
    req.instrument = instrument
    req.items = list(range(item_count))
    return req


class TestValidateItemCount:
    def test_correct_phq9_count_does_not_raise(self) -> None:
        _validate_item_count(_assessment_request("phq9", 9))

    def test_correct_gad7_count_does_not_raise(self) -> None:
        _validate_item_count(_assessment_request("gad7", 7))

    def test_wrong_count_raises_422(self) -> None:
        with pytest.raises(HTTPException) as exc_info:
            _validate_item_count(_assessment_request("phq9", 8))
        assert exc_info.value.status_code == 422

    def test_error_detail_has_item_count_code(self) -> None:
        with pytest.raises(HTTPException) as exc_info:
            _validate_item_count(_assessment_request("gad7", 5))
        detail = exc_info.value.detail
        assert detail["code"] == "validation.item_count"

    def test_error_message_names_instrument(self) -> None:
        with pytest.raises(HTTPException) as exc_info:
            _validate_item_count(_assessment_request("phq9", 8))
        assert "phq9" in exc_info.value.detail["message"]

    def test_error_message_names_expected_count(self) -> None:
        with pytest.raises(HTTPException) as exc_info:
            _validate_item_count(_assessment_request("phq9", 8))
        assert "9" in exc_info.value.detail["message"]

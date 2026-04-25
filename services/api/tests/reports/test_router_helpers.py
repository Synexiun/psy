"""Unit tests for _render_record_as_observation(), _parse_assessment_sessions(),
and _parse_check_ins() pure helpers in discipline.reports.router.

_render_record_as_observation(record) → dict
  Dispatches C-SSRS records to render_cssrs_bundle (categorical FHIR path)
  and all other instruments to render_bundle (numeric valueInteger path).
  Key safety contract: the C-SSRS dispatch must never use the numeric path,
  or the risk level would be silently rendered as an integer observation.

_parse_assessment_sessions(user_id, raw) → list[AssessmentSession]
  Naive datetime tolerance: a UTC-naive ISO-8601 string is accepted and
  coerced to UTC (adds tzinfo=UTC), unlike _ensure_utc in user_export which
  rejects non-UTC datetimes.  This prevents a surprise 422 from callers
  that emit naive UTC strings.

_parse_check_ins(user_id, raw) → list[UrgeCheckInRecord]
  Same naive datetime tolerance as _parse_assessment_sessions.
  Intensity must be in 0-10 range; out-of-range raises ValueError wrapped
  as "check_ins[i] is malformed".
"""

from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest

from discipline.psychometric.repository import AssessmentRecord
from discipline.reports.router import (
    _parse_assessment_sessions,
    _parse_check_ins,
    _render_record_as_observation,
)

_NOW_UTC = datetime(2026, 1, 15, 12, 0, 0, tzinfo=UTC)


def _phq9_record(**overrides: object) -> AssessmentRecord:
    defaults: dict[str, object] = dict(
        assessment_id="aaa-111",
        user_id="user-1",
        instrument="phq9",
        total=14,
        severity="moderate",
        requires_t3=False,
        raw_items=(0, 1, 2, 1, 2, 1, 2, 1, 2),
        created_at=_NOW_UTC,
    )
    defaults.update(overrides)
    return AssessmentRecord(**defaults)  # type: ignore[arg-type]


def _cssrs_record(**overrides: object) -> AssessmentRecord:
    defaults: dict[str, object] = dict(
        assessment_id="bbb-222",
        user_id="user-1",
        instrument="cssrs",
        total=0,
        severity="low",
        requires_t3=False,
        raw_items=(True, False, False, False, False, False),
        created_at=_NOW_UTC,
        triggering_items=(1, 2),
    )
    defaults.update(overrides)
    return AssessmentRecord(**defaults)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# _render_record_as_observation — dispatch logic
# ---------------------------------------------------------------------------


class TestRenderRecordAsObservationDispatch:
    def test_non_cssrs_returns_dict(self) -> None:
        result = _render_record_as_observation(_phq9_record())
        assert isinstance(result, dict)

    def test_cssrs_returns_dict(self) -> None:
        result = _render_record_as_observation(_cssrs_record())
        assert isinstance(result, dict)

    def test_non_cssrs_uses_numeric_path(self) -> None:
        # Numeric path does NOT use valueCodeableConcept (that's C-SSRS only)
        result = _render_record_as_observation(_phq9_record())
        serialized = json.dumps(result)
        assert "valueCodeableConcept" not in serialized

    def test_cssrs_uses_categorical_path(self) -> None:
        # Categorical path uses valueCodeableConcept (not valueInteger)
        result = _render_record_as_observation(_cssrs_record())
        serialized = json.dumps(result)
        assert "valueCodeableConcept" in serialized

    def test_cssrs_and_non_cssrs_produce_different_fhir_shapes(self) -> None:
        phq9_result = _render_record_as_observation(_phq9_record())
        cssrs_result = _render_record_as_observation(_cssrs_record())
        assert phq9_result != cssrs_result

    def test_unknown_instrument_raises_unsupported(self) -> None:
        from discipline.reports.fhir_observation import UnsupportedInstrumentError
        with pytest.raises(UnsupportedInstrumentError):
            _render_record_as_observation(_phq9_record(instrument="unknown_xyz"))

    def test_cssrs_unknown_severity_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="known risk level"):
            _render_record_as_observation(_cssrs_record(severity="catastrophic"))

    def test_cssrs_all_valid_risk_levels_accepted(self) -> None:
        for level in ("none", "low", "moderate", "acute"):
            result = _render_record_as_observation(_cssrs_record(severity=level))
            assert isinstance(result, dict)

    def test_cssrs_none_triggering_items_normalised_to_empty_tuple(self) -> None:
        # triggering_items=None on record → empty tuple passed to render_cssrs_bundle
        result = _render_record_as_observation(_cssrs_record(triggering_items=None))
        assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# _parse_assessment_sessions — datetime parsing and naive-UTC tolerance
# ---------------------------------------------------------------------------


def _session_entry(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "instrument": "phq9",
        "total_score": 7,
        "administered_at": "2026-01-15T12:00:00+00:00",
        "safety_item_positive": False,
    }
    base.update(overrides)
    return base


class TestParseAssessmentSessions:
    def test_returns_list(self) -> None:
        result = _parse_assessment_sessions("u1", [_session_entry()])
        assert isinstance(result, list)
        assert len(result) == 1

    def test_empty_raw_returns_empty_list(self) -> None:
        assert _parse_assessment_sessions("u1", []) == []

    def test_user_id_propagated(self) -> None:
        result = _parse_assessment_sessions("u-abc", [_session_entry()])
        assert result[0].user_id == "u-abc"

    def test_instrument_propagated(self) -> None:
        result = _parse_assessment_sessions("u1", [_session_entry(instrument="gad7")])
        assert result[0].instrument == "gad7"

    def test_total_score_propagated(self) -> None:
        result = _parse_assessment_sessions("u1", [_session_entry(total_score=21)])
        assert result[0].total_score == 21

    def test_zulu_suffix_accepted(self) -> None:
        entry = _session_entry(administered_at="2026-01-15T12:00:00Z")
        result = _parse_assessment_sessions("u1", [entry])
        assert result[0].administered_at.tzinfo is not None

    def test_offset_string_accepted(self) -> None:
        entry = _session_entry(administered_at="2026-01-15T12:00:00+00:00")
        result = _parse_assessment_sessions("u1", [entry])
        assert result[0].administered_at.tzinfo is not None

    def test_naive_string_coerced_to_utc(self) -> None:
        # Naive ISO string: no +00:00 or Z — treated as UTC, not rejected
        entry = _session_entry(administered_at="2026-01-15T12:00:00")
        result = _parse_assessment_sessions("u1", [entry])
        assert result[0].administered_at.tzinfo == UTC

    def test_datetime_object_accepted(self) -> None:
        entry = _session_entry(administered_at=_NOW_UTC)
        result = _parse_assessment_sessions("u1", [entry])
        assert result[0].administered_at == _NOW_UTC

    def test_naive_datetime_object_coerced_to_utc(self) -> None:
        naive_dt = datetime(2026, 1, 15, 12, 0, 0)
        entry = _session_entry(administered_at=naive_dt)
        result = _parse_assessment_sessions("u1", [entry])
        assert result[0].administered_at.tzinfo == UTC

    def test_safety_item_positive_defaults_to_false(self) -> None:
        entry: dict[str, object] = {
            "instrument": "phq9",
            "total_score": 7,
            "administered_at": "2026-01-15T12:00:00Z",
        }
        result = _parse_assessment_sessions("u1", [entry])
        assert result[0].safety_item_positive is False

    def test_missing_instrument_raises_value_error(self) -> None:
        bad: dict[str, object] = {
            "total_score": 7,
            "administered_at": "2026-01-15T12:00:00Z",
        }
        with pytest.raises(ValueError, match=r"sessions\[0\]"):
            _parse_assessment_sessions("u1", [bad])

    def test_invalid_administered_at_type_raises_value_error(self) -> None:
        entry = _session_entry(administered_at=12345)
        with pytest.raises(ValueError, match=r"sessions\[0\]"):
            _parse_assessment_sessions("u1", [entry])

    def test_multiple_entries_parsed(self) -> None:
        raw = [_session_entry(instrument="phq9"), _session_entry(instrument="gad7")]
        result = _parse_assessment_sessions("u1", raw)
        assert len(result) == 2
        assert result[0].instrument == "phq9"
        assert result[1].instrument == "gad7"


# ---------------------------------------------------------------------------
# _parse_check_ins — datetime parsing and intensity validation
# ---------------------------------------------------------------------------


def _checkin_entry(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "intensity": 5,
        "checked_in_at": "2026-01-15T12:00:00+00:00",
    }
    base.update(overrides)
    return base


class TestParseCheckIns:
    def test_returns_list(self) -> None:
        result = _parse_check_ins("u1", [_checkin_entry()])
        assert isinstance(result, list)
        assert len(result) == 1

    def test_empty_raw_returns_empty_list(self) -> None:
        assert _parse_check_ins("u1", []) == []

    def test_user_id_propagated(self) -> None:
        result = _parse_check_ins("u-abc", [_checkin_entry()])
        assert result[0].user_id == "u-abc"

    def test_intensity_propagated(self) -> None:
        result = _parse_check_ins("u1", [_checkin_entry(intensity=8)])
        assert result[0].intensity == 8

    def test_intensity_zero_accepted(self) -> None:
        result = _parse_check_ins("u1", [_checkin_entry(intensity=0)])
        assert result[0].intensity == 0

    def test_intensity_10_accepted(self) -> None:
        result = _parse_check_ins("u1", [_checkin_entry(intensity=10)])
        assert result[0].intensity == 10

    def test_intensity_11_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match=r"check_ins\[0\]"):
            _parse_check_ins("u1", [_checkin_entry(intensity=11)])

    def test_intensity_minus_1_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match=r"check_ins\[0\]"):
            _parse_check_ins("u1", [_checkin_entry(intensity=-1)])

    def test_naive_string_coerced_to_utc(self) -> None:
        # Same naive-UTC tolerance as _parse_assessment_sessions
        entry = _checkin_entry(checked_in_at="2026-01-15T12:00:00")
        result = _parse_check_ins("u1", [entry])
        assert result[0].checked_in_at.tzinfo == UTC

    def test_zulu_suffix_accepted(self) -> None:
        entry = _checkin_entry(checked_in_at="2026-01-15T12:00:00Z")
        result = _parse_check_ins("u1", [entry])
        assert result[0].checked_in_at.tzinfo is not None

    def test_missing_intensity_raises_value_error(self) -> None:
        bad: dict[str, object] = {"checked_in_at": "2026-01-15T12:00:00Z"}
        with pytest.raises(ValueError, match=r"check_ins\[0\]"):
            _parse_check_ins("u1", [bad])

    def test_error_index_identifies_malformed_entry(self) -> None:
        good = _checkin_entry()
        bad = _checkin_entry(intensity=99)
        with pytest.raises(ValueError, match=r"check_ins\[1\]"):
            _parse_check_ins("u1", [good, bad])

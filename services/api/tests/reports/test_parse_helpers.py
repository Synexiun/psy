"""Unit tests for _parse_assessment_sessions() and _parse_check_ins() pure
helpers in discipline.reports.router.

Both functions convert wire-format dicts (from HTTP request payloads) into
typed dataclasses, applying two shared invariants:

1. Naive datetime → UTC: a datetime that has no tzinfo is silently treated as
   UTC rather than rejected, so callers that produce naive UTC strings don't
   get a surprise 422.
2. "Z" suffix → "+00:00": ISO-8601 strings ending in "Z" are normalised before
   calling datetime.fromisoformat(), working around Python <3.11 behaviour.
3. Malformed entries raise ValueError with a 0-indexed position in the message
   so the caller can locate the bad record.

_parse_check_ins additionally validates that intensity is 0–10; values outside
that range raise ValueError.
"""

from __future__ import annotations

from datetime import UTC, datetime, timezone

import pytest

from discipline.reports.router import _parse_assessment_sessions, _parse_check_ins


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_UID = "user_abc"

# A well-formed assessment session dict
def _session(
    instrument: str = "phq9",
    total_score: int = 8,
    administered_at: str | datetime = "2026-04-25T10:00:00Z",
    safety_item_positive: bool = False,
) -> dict:
    return {
        "instrument": instrument,
        "total_score": total_score,
        "administered_at": administered_at,
        "safety_item_positive": safety_item_positive,
    }


# A well-formed check-in dict
def _check_in(
    intensity: int = 5,
    checked_in_at: str | datetime = "2026-04-25T10:00:00Z",
) -> dict:
    return {"intensity": intensity, "checked_in_at": checked_in_at}


# ---------------------------------------------------------------------------
# _parse_assessment_sessions — happy path
# ---------------------------------------------------------------------------


class TestParseAssessmentSessionsHappyPath:
    def test_returns_empty_list_for_empty_input(self) -> None:
        assert _parse_assessment_sessions(_UID, []) == []

    def test_single_session_parsed(self) -> None:
        result = _parse_assessment_sessions(_UID, [_session()])
        assert len(result) == 1

    def test_user_id_propagated(self) -> None:
        result = _parse_assessment_sessions(_UID, [_session()])
        assert result[0].user_id == _UID

    def test_instrument_preserved(self) -> None:
        result = _parse_assessment_sessions(_UID, [_session(instrument="gad7")])
        assert result[0].instrument == "gad7"

    def test_total_score_preserved(self) -> None:
        result = _parse_assessment_sessions(_UID, [_session(total_score=14)])
        assert result[0].total_score == 14

    def test_safety_positive_flag_true(self) -> None:
        result = _parse_assessment_sessions(
            _UID, [_session(safety_item_positive=True)]
        )
        assert result[0].safety_item_positive is True

    def test_safety_positive_flag_false_by_default(self) -> None:
        entry = {
            "instrument": "phq9",
            "total_score": 5,
            "administered_at": "2026-04-25T10:00:00Z",
        }
        result = _parse_assessment_sessions(_UID, [entry])
        assert result[0].safety_item_positive is False

    def test_multiple_sessions_all_parsed(self) -> None:
        entries = [
            _session(instrument="phq9", total_score=4),
            _session(instrument="gad7", total_score=9),
            _session(instrument="who5", total_score=18),
        ]
        result = _parse_assessment_sessions(_UID, entries)
        assert len(result) == 3
        assert result[1].instrument == "gad7"


# ---------------------------------------------------------------------------
# _parse_assessment_sessions — datetime handling
# ---------------------------------------------------------------------------


class TestParseAssessmentSessionsDatetime:
    def test_z_suffix_string_parsed_as_utc(self) -> None:
        result = _parse_assessment_sessions(
            _UID, [_session(administered_at="2026-04-25T10:00:00Z")]
        )
        dt = result[0].administered_at
        assert dt.tzinfo is not None
        assert dt.utctimetuple() == datetime(2026, 4, 25, 10, 0, 0, tzinfo=UTC).utctimetuple()

    def test_plus00_00_suffix_parsed(self) -> None:
        result = _parse_assessment_sessions(
            _UID, [_session(administered_at="2026-04-25T10:00:00+00:00")]
        )
        assert result[0].administered_at.tzinfo is not None

    def test_naive_string_treated_as_utc(self) -> None:
        result = _parse_assessment_sessions(
            _UID, [_session(administered_at="2026-04-25T10:00:00")]
        )
        dt = result[0].administered_at
        assert dt.tzinfo == UTC

    def test_datetime_object_passthrough(self) -> None:
        dt_obj = datetime(2026, 4, 25, 10, 0, 0, tzinfo=UTC)
        result = _parse_assessment_sessions(
            _UID, [_session(administered_at=dt_obj)]
        )
        assert result[0].administered_at == dt_obj

    def test_naive_datetime_object_treated_as_utc(self) -> None:
        naive = datetime(2026, 4, 25, 10, 0, 0)
        result = _parse_assessment_sessions(_UID, [_session(administered_at=naive)])
        assert result[0].administered_at.tzinfo == UTC

    def test_result_datetime_is_timezone_aware(self) -> None:
        result = _parse_assessment_sessions(
            _UID, [_session(administered_at="2026-04-25T10:00:00Z")]
        )
        assert result[0].administered_at.tzinfo is not None


# ---------------------------------------------------------------------------
# _parse_assessment_sessions — malformed entries
# ---------------------------------------------------------------------------


class TestParseAssessmentSessionsMalformed:
    def test_missing_instrument_key_raises(self) -> None:
        entry = {"total_score": 5, "administered_at": "2026-04-25T10:00:00Z"}
        with pytest.raises(ValueError):
            _parse_assessment_sessions(_UID, [entry])

    def test_missing_total_score_raises(self) -> None:
        entry = {"instrument": "phq9", "administered_at": "2026-04-25T10:00:00Z"}
        with pytest.raises(ValueError):
            _parse_assessment_sessions(_UID, [entry])

    def test_missing_administered_at_raises(self) -> None:
        entry = {"instrument": "phq9", "total_score": 5}
        with pytest.raises(ValueError):
            _parse_assessment_sessions(_UID, [entry])

    def test_error_message_contains_index(self) -> None:
        good = _session()
        bad = {"instrument": "phq9", "total_score": 5}  # missing administered_at
        with pytest.raises(ValueError, match=r"sessions\[1\]"):
            _parse_assessment_sessions(_UID, [good, bad])

    def test_first_bad_entry_index_zero(self) -> None:
        with pytest.raises(ValueError, match=r"sessions\[0\]"):
            _parse_assessment_sessions(_UID, [{"instrument": "phq9"}])

    def test_invalid_administered_at_type_raises(self) -> None:
        entry = {"instrument": "phq9", "total_score": 5, "administered_at": 12345}
        with pytest.raises(ValueError):
            _parse_assessment_sessions(_UID, [entry])


# ---------------------------------------------------------------------------
# _parse_check_ins — happy path
# ---------------------------------------------------------------------------


class TestParseCheckInsHappyPath:
    def test_returns_empty_list_for_empty_input(self) -> None:
        assert _parse_check_ins(_UID, []) == []

    def test_single_check_in_parsed(self) -> None:
        result = _parse_check_ins(_UID, [_check_in()])
        assert len(result) == 1

    def test_user_id_propagated(self) -> None:
        result = _parse_check_ins(_UID, [_check_in()])
        assert result[0].user_id == _UID

    def test_intensity_preserved(self) -> None:
        result = _parse_check_ins(_UID, [_check_in(intensity=7)])
        assert result[0].intensity == 7

    def test_intensity_zero_accepted(self) -> None:
        result = _parse_check_ins(_UID, [_check_in(intensity=0)])
        assert result[0].intensity == 0

    def test_intensity_ten_accepted(self) -> None:
        result = _parse_check_ins(_UID, [_check_in(intensity=10)])
        assert result[0].intensity == 10

    def test_multiple_check_ins_all_parsed(self) -> None:
        entries = [_check_in(intensity=3), _check_in(intensity=7), _check_in(intensity=9)]
        result = _parse_check_ins(_UID, entries)
        assert len(result) == 3
        assert result[1].intensity == 7


# ---------------------------------------------------------------------------
# _parse_check_ins — datetime handling
# ---------------------------------------------------------------------------


class TestParseCheckInsDatetime:
    def test_z_suffix_string_parsed_as_utc(self) -> None:
        result = _parse_check_ins(
            _UID, [_check_in(checked_in_at="2026-04-25T10:00:00Z")]
        )
        assert result[0].checked_in_at.tzinfo is not None

    def test_naive_string_treated_as_utc(self) -> None:
        result = _parse_check_ins(
            _UID, [_check_in(checked_in_at="2026-04-25T10:00:00")]
        )
        assert result[0].checked_in_at.tzinfo == UTC

    def test_datetime_object_passthrough(self) -> None:
        dt_obj = datetime(2026, 4, 25, 10, 0, 0, tzinfo=UTC)
        result = _parse_check_ins(_UID, [_check_in(checked_in_at=dt_obj)])
        assert result[0].checked_in_at == dt_obj

    def test_result_checked_in_at_is_timezone_aware(self) -> None:
        result = _parse_check_ins(
            _UID, [_check_in(checked_in_at="2026-04-25T10:00:00Z")]
        )
        assert result[0].checked_in_at.tzinfo is not None


# ---------------------------------------------------------------------------
# _parse_check_ins — intensity range validation
# ---------------------------------------------------------------------------


class TestParseCheckInsIntensityRange:
    def test_intensity_11_raises(self) -> None:
        with pytest.raises(ValueError):
            _parse_check_ins(_UID, [_check_in(intensity=11)])

    def test_intensity_negative_raises(self) -> None:
        with pytest.raises(ValueError):
            _parse_check_ins(_UID, [_check_in(intensity=-1)])

    def test_error_message_mentions_range(self) -> None:
        with pytest.raises(ValueError, match=r"0.10"):
            _parse_check_ins(_UID, [_check_in(intensity=100)])


# ---------------------------------------------------------------------------
# _parse_check_ins — malformed entries
# ---------------------------------------------------------------------------


class TestParseCheckInsMalformed:
    def test_missing_intensity_key_raises(self) -> None:
        entry = {"checked_in_at": "2026-04-25T10:00:00Z"}
        with pytest.raises(ValueError):
            _parse_check_ins(_UID, [entry])

    def test_missing_checked_in_at_raises(self) -> None:
        entry = {"intensity": 5}
        with pytest.raises(ValueError):
            _parse_check_ins(_UID, [entry])

    def test_error_message_contains_index(self) -> None:
        good = _check_in()
        bad = {"intensity": 5}  # missing checked_in_at
        with pytest.raises(ValueError, match=r"check_ins\[1\]"):
            _parse_check_ins(_UID, [good, bad])

    def test_first_bad_entry_index_zero(self) -> None:
        with pytest.raises(ValueError, match=r"check_ins\[0\]"):
            _parse_check_ins(_UID, [{"intensity": 5}])

    def test_invalid_checked_in_at_type_raises(self) -> None:
        entry = {"intensity": 5, "checked_in_at": 99999}
        with pytest.raises(ValueError):
            _parse_check_ins(_UID, [entry])

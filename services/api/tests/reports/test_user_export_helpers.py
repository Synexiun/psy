"""Unit tests for _ensure_utc(), _iso_utc(), and _is_empty_payload() pure
helpers in discipline.reports.user_export.

_ensure_utc(dt, field_name) → datetime
  Validates that a datetime is both timezone-aware AND UTC.  Naive datetimes
  and non-UTC offsets raise NonUtcTimestampError.  This is load-bearing: the
  archive serialization always emits "Z"-suffixed strings; a naive or off-UTC
  datetime would produce a string without the Z designator, which a client
  parser could silently mis-classify.

_iso_utc(dt) → str
  Renders a UTC datetime as "YYYY-MM-DDTHH:MM:SSZ".  Always uses "Z" (not
  "+00:00") for byte-identical output across Python versions.

_is_empty_payload(payload) → bool
  True iff every data-bearing section (profile, psychometric_scores,
  intervention_events, resilience_streak, safety_events, consents) is empty.
  Metadata fields (user_id, requested_at, generated_at, locale) do NOT count
  towards emptiness — a user with no records still has those populated.
"""

from __future__ import annotations

from datetime import UTC, datetime, timezone, timedelta

import pytest

from discipline.reports.user_export import (
    NonUtcTimestampError,
    UserExportPayload,
    _ensure_utc,
    _is_empty_payload,
    _iso_utc,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_NOW_UTC = datetime(2026, 4, 25, 12, 0, 0, tzinfo=UTC)


def _empty_payload(**overrides) -> UserExportPayload:
    base = dict(
        user_id="user_abc",
        requested_at=_NOW_UTC,
        generated_at=_NOW_UTC,
        locale="en",
    )
    base.update(overrides)
    return UserExportPayload(**base)


# ---------------------------------------------------------------------------
# _ensure_utc — accepted inputs
# ---------------------------------------------------------------------------


class TestEnsureUtcAccepted:
    def test_utc_aware_datetime_returned_unchanged(self) -> None:
        result = _ensure_utc(_NOW_UTC, field_name="requested_at")
        assert result == _NOW_UTC

    def test_returns_same_datetime_object_identity(self) -> None:
        result = _ensure_utc(_NOW_UTC, field_name="generated_at")
        assert result is _NOW_UTC

    def test_result_is_timezone_aware(self) -> None:
        result = _ensure_utc(_NOW_UTC, field_name="f")
        assert result.tzinfo is not None


# ---------------------------------------------------------------------------
# _ensure_utc — naive datetimes rejected
# ---------------------------------------------------------------------------


class TestEnsureUtcNaiveRejected:
    def test_naive_datetime_raises(self) -> None:
        naive = datetime(2026, 4, 25, 12, 0, 0)
        with pytest.raises(NonUtcTimestampError):
            _ensure_utc(naive, field_name="requested_at")

    def test_naive_error_mentions_field_name(self) -> None:
        naive = datetime(2026, 4, 25, 12, 0, 0)
        with pytest.raises(NonUtcTimestampError, match="requested_at"):
            _ensure_utc(naive, field_name="requested_at")

    def test_error_is_subclass_of_value_error(self) -> None:
        naive = datetime(2026, 4, 25, 12, 0, 0)
        with pytest.raises(ValueError):
            _ensure_utc(naive, field_name="f")


# ---------------------------------------------------------------------------
# _ensure_utc — non-UTC offsets rejected
# ---------------------------------------------------------------------------


class TestEnsureUtcNonUtcRejected:
    def test_plus_five_offset_raises(self) -> None:
        east5 = datetime(2026, 4, 25, 17, 0, 0, tzinfo=timezone(timedelta(hours=5)))
        with pytest.raises(NonUtcTimestampError):
            _ensure_utc(east5, field_name="generated_at")

    def test_minus_five_offset_raises(self) -> None:
        west5 = datetime(2026, 4, 25, 7, 0, 0, tzinfo=timezone(timedelta(hours=-5)))
        with pytest.raises(NonUtcTimestampError):
            _ensure_utc(west5, field_name="f")

    def test_non_utc_error_mentions_field_name(self) -> None:
        east = datetime(2026, 4, 25, 12, 0, 0, tzinfo=timezone(timedelta(hours=3)))
        with pytest.raises(NonUtcTimestampError, match="generated_at"):
            _ensure_utc(east, field_name="generated_at")


# ---------------------------------------------------------------------------
# _iso_utc — output format
# ---------------------------------------------------------------------------


class TestIsoUtcFormat:
    def test_utc_datetime_renders_with_z_suffix(self) -> None:
        result = _iso_utc(_NOW_UTC)
        assert result.endswith("Z")

    def test_format_is_yyyy_mm_ddTHH_MM_SSZ(self) -> None:
        dt = datetime(2026, 4, 25, 10, 30, 15, tzinfo=UTC)
        assert _iso_utc(dt) == "2026-04-25T10:30:15Z"

    def test_does_not_use_plus00_00_form(self) -> None:
        result = _iso_utc(_NOW_UTC)
        assert "+00:00" not in result

    def test_midnight_rendered_correctly(self) -> None:
        dt = datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC)
        assert _iso_utc(dt) == "2026-01-01T00:00:00Z"

    def test_end_of_day_rendered_correctly(self) -> None:
        dt = datetime(2026, 12, 31, 23, 59, 59, tzinfo=UTC)
        assert _iso_utc(dt) == "2026-12-31T23:59:59Z"

    def test_non_utc_offset_converted_to_utc(self) -> None:
        east5 = datetime(2026, 4, 25, 17, 0, 0, tzinfo=timezone(timedelta(hours=5)))
        # 17:00+05 == 12:00 UTC
        result = _iso_utc(east5)
        assert result == "2026-04-25T12:00:00Z"

    def test_result_is_always_20_chars(self) -> None:
        # "2026-04-25T10:00:00Z" = 20 characters
        result = _iso_utc(_NOW_UTC)
        assert len(result) == 20


# ---------------------------------------------------------------------------
# _is_empty_payload — fully empty
# ---------------------------------------------------------------------------


class TestIsEmptyPayloadFullyEmpty:
    def test_default_payload_is_empty(self) -> None:
        payload = _empty_payload()
        assert _is_empty_payload(payload) is True

    def test_explicit_empty_sections_is_empty(self) -> None:
        payload = _empty_payload(
            profile={},
            psychometric_scores=[],
            intervention_events=[],
            resilience_streak={},
            safety_events=[],
            consents=[],
        )
        assert _is_empty_payload(payload) is True


# ---------------------------------------------------------------------------
# _is_empty_payload — metadata fields do NOT count
# ---------------------------------------------------------------------------


class TestIsEmptyPayloadMetadataIgnored:
    def test_user_id_does_not_affect_emptiness(self) -> None:
        payload = _empty_payload(user_id="important_user")
        assert _is_empty_payload(payload) is True

    def test_locale_does_not_affect_emptiness(self) -> None:
        payload = _empty_payload(locale="ar")
        assert _is_empty_payload(payload) is True


# ---------------------------------------------------------------------------
# _is_empty_payload — any populated section makes it non-empty
# ---------------------------------------------------------------------------


class TestIsEmptyPayloadNonEmpty:
    def test_profile_populated_is_not_empty(self) -> None:
        payload = _empty_payload(profile={"name": "Alice"})
        assert _is_empty_payload(payload) is False

    def test_psychometric_scores_populated_is_not_empty(self) -> None:
        payload = _empty_payload(psychometric_scores=[{"phq9": 8}])
        assert _is_empty_payload(payload) is False

    def test_intervention_events_populated_is_not_empty(self) -> None:
        payload = _empty_payload(intervention_events=[{"tool": "box_breathing"}])
        assert _is_empty_payload(payload) is False

    def test_resilience_streak_populated_is_not_empty(self) -> None:
        payload = _empty_payload(resilience_streak={"days": 30})
        assert _is_empty_payload(payload) is False

    def test_safety_events_populated_is_not_empty(self) -> None:
        payload = _empty_payload(safety_events=[{"type": "t3_escalation"}])
        assert _is_empty_payload(payload) is False

    def test_consents_populated_is_not_empty(self) -> None:
        payload = _empty_payload(consents=[{"type": "data_processing"}])
        assert _is_empty_payload(payload) is False

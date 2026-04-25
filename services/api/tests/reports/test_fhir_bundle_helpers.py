"""Unit tests for _format_iso8601_z() and _new_urn_uuid() pure helpers in
discipline.reports.fhir_bundle.

_format_iso8601_z(dt) → str
  Rejects naive datetimes (ValueError).
  Converts to UTC and formats as "YYYY-MM-DDTHH:MM:SSZ".
  Contract is identical to _iso_utc in user_export; both surfaces must
  emit Z-suffix timestamps for FHIR R4 compliance (section 2.24 of the
  FHIR spec requires timezone designator on dateTime values).

_new_urn_uuid() → str
  Returns "urn:uuid:<uuid4>".  FHIR R4 Bundle entries use URN-based
  fullUrls to avoid absolute URL construction during offline / export
  scenarios.  The "urn:uuid:" prefix is a FHIR R4 spec requirement.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime, timezone, timedelta

import pytest

from discipline.reports.fhir_bundle import _format_iso8601_z, _new_urn_uuid

_NOW = datetime(2026, 3, 15, 9, 30, 0, tzinfo=UTC)
_NAIVE = datetime(2026, 3, 15, 9, 30, 0)

_URN_UUID_RE = re.compile(
    r"^urn:uuid:[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)


# ---------------------------------------------------------------------------
# _format_iso8601_z — FHIR R4 timestamp format
# ---------------------------------------------------------------------------


class TestFormatIso8601Z:
    def test_utc_datetime_ends_with_z(self) -> None:
        result = _format_iso8601_z(_NOW)
        assert result.endswith("Z")

    def test_format_is_iso8601(self) -> None:
        result = _format_iso8601_z(_NOW)
        assert result == "2026-03-15T09:30:00Z"

    def test_no_plus_offset_in_output(self) -> None:
        assert "+00:00" not in _format_iso8601_z(_NOW)

    def test_naive_raises_value_error(self) -> None:
        with pytest.raises(ValueError):
            _format_iso8601_z(_NAIVE)

    def test_naive_error_message_mentions_timezone(self) -> None:
        with pytest.raises(ValueError, match="[Tt]imezone"):
            _format_iso8601_z(_NAIVE)

    def test_non_utc_offset_converted(self) -> None:
        eastern = datetime(2026, 3, 15, 4, 30, 0, tzinfo=timezone(timedelta(hours=-5)))
        # 04:30-05:00 = 09:30 UTC
        assert _format_iso8601_z(eastern) == "2026-03-15T09:30:00Z"

    def test_result_length_is_20(self) -> None:
        assert len(_format_iso8601_z(_NOW)) == 20


# ---------------------------------------------------------------------------
# _new_urn_uuid — FHIR R4 fullUrl format
# ---------------------------------------------------------------------------


class TestNewUrnUuid:
    def test_starts_with_urn_uuid_prefix(self) -> None:
        assert _new_urn_uuid().startswith("urn:uuid:")

    def test_matches_urn_uuid4_pattern(self) -> None:
        result = _new_urn_uuid()
        assert _URN_UUID_RE.match(result), f"'{result}' does not match urn:uuid:v4 pattern"

    def test_returns_string(self) -> None:
        assert isinstance(_new_urn_uuid(), str)

    def test_each_call_returns_unique_value(self) -> None:
        results = {_new_urn_uuid() for _ in range(10)}
        assert len(results) == 10

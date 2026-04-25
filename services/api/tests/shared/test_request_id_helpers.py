"""Unit tests for _parse_or_generate() pure helper in
discipline.shared.middleware.request_id.

_parse_or_generate(header_value) → str
  Validates a caller-supplied request ID or generates a UUID v4.

  Validation rules (BOTH must pass to accept the supplied value):
    1. header_value is not falsy (empty string, None → generate)
    2. len(header_value) ≤ 64 characters
    3. Matches ^[a-zA-Z0-9\\-]+$ (alphanumeric + hyphens only)

  Any failure → generate a fresh UUID4 string.
  The UUID output is always a valid 36-character UUID string.

  Security rationale: request IDs appear in log entries.  Accepting
  arbitrary characters (spaces, slashes, quotes) would allow a caller
  to inject log noise or break log parsers.
"""

from __future__ import annotations

import re
import uuid

from discipline.shared.middleware.request_id import _parse_or_generate

_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)


def _is_uuid4(s: str) -> bool:
    return bool(_UUID_RE.match(s))


# ---------------------------------------------------------------------------
# Valid inputs — supplied value returned unchanged
# ---------------------------------------------------------------------------


class TestParseOrGenerateAccepted:
    def test_plain_uuid_accepted(self) -> None:
        val = "abc-1234-XYZ"
        assert _parse_or_generate(val) == val

    def test_alphanumeric_only_accepted(self) -> None:
        val = "requestABC123"
        assert _parse_or_generate(val) == val

    def test_hyphens_accepted(self) -> None:
        val = "req-id-001"
        assert _parse_or_generate(val) == val

    def test_exactly_64_chars_accepted(self) -> None:
        val = "a" * 64
        assert _parse_or_generate(val) == val

    def test_single_char_accepted(self) -> None:
        assert _parse_or_generate("a") == "a"

    def test_returns_string(self) -> None:
        assert isinstance(_parse_or_generate("valid-id"), str)


# ---------------------------------------------------------------------------
# Invalid inputs — UUID4 generated
# ---------------------------------------------------------------------------


class TestParseOrGenerateGenerates:
    def test_none_generates_uuid(self) -> None:
        result = _parse_or_generate(None)
        assert _is_uuid4(result)

    def test_empty_string_generates_uuid(self) -> None:
        result = _parse_or_generate("")
        assert _is_uuid4(result)

    def test_65_chars_generates_uuid(self) -> None:
        result = _parse_or_generate("a" * 65)
        assert _is_uuid4(result)

    def test_space_in_value_generates_uuid(self) -> None:
        result = _parse_or_generate("req id")
        assert _is_uuid4(result)

    def test_slash_in_value_generates_uuid(self) -> None:
        result = _parse_or_generate("req/id")
        assert _is_uuid4(result)

    def test_underscore_in_value_generates_uuid(self) -> None:
        # Underscores are NOT in the allowed set
        result = _parse_or_generate("req_id")
        assert _is_uuid4(result)

    def test_dot_in_value_generates_uuid(self) -> None:
        result = _parse_or_generate("req.id")
        assert _is_uuid4(result)

    def test_generated_uuid_is_always_36_chars(self) -> None:
        for _ in range(5):
            result = _parse_or_generate(None)
            assert len(result) == 36

    def test_generated_values_are_unique(self) -> None:
        results = {_parse_or_generate(None) for _ in range(10)}
        assert len(results) == 10

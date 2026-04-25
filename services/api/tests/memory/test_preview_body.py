"""Unit tests for the _preview_body() pure helper in discipline.memory.router.

_preview_body(body, limit=200) truncates body to `limit` characters.
When len(body) > limit, returns body[:limit-1] + "…" (1 Unicode ellipsis char).
When len(body) <= limit, returns body unchanged.

Key invariants:
- Strings at or below the limit are returned verbatim
- The truncated form is exactly `limit` characters long (not limit+1)
- The ellipsis character used is U+2026 (HORIZONTAL ELLIPSIS), not "..."
- The custom limit parameter is respected
- Empty string is handled
- Unicode characters count as 1 towards the length (Python str length)
"""

from __future__ import annotations

import pytest

from discipline.memory.router import _preview_body


# ---------------------------------------------------------------------------
# Below-limit (passthrough)
# ---------------------------------------------------------------------------


class TestPreviewBodyPassthrough:
    def test_empty_string_returned_unchanged(self) -> None:
        assert _preview_body("") == ""

    def test_single_char_returned_unchanged(self) -> None:
        assert _preview_body("x") == "x"

    def test_exactly_limit_chars_not_truncated(self) -> None:
        body = "a" * 200
        result = _preview_body(body)
        assert result == body
        assert len(result) == 200

    def test_one_below_limit_not_truncated(self) -> None:
        body = "a" * 199
        result = _preview_body(body)
        assert result == body
        assert len(result) == 199


# ---------------------------------------------------------------------------
# Above-limit (truncation)
# ---------------------------------------------------------------------------


class TestPreviewBodyTruncation:
    def test_one_above_limit_truncated(self) -> None:
        body = "a" * 201
        result = _preview_body(body)
        assert result == "a" * 199 + "…"
        assert len(result) == 200

    def test_truncated_result_is_exactly_limit_chars(self) -> None:
        body = "x" * 500
        result = _preview_body(body)
        assert len(result) == 200

    def test_truncated_result_ends_with_ellipsis(self) -> None:
        body = "Hello world " * 20  # 240 chars
        result = _preview_body(body)
        assert result.endswith("…")

    def test_truncated_body_uses_unicode_ellipsis_not_three_dots(self) -> None:
        body = "a" * 201
        result = _preview_body(body)
        assert result[-1] == "…"   # U+2026
        assert result[-1] != "."   # not a period

    def test_first_limit_minus_one_chars_preserved(self) -> None:
        body = "abcde" * 50  # 250 chars, well above limit
        result = _preview_body(body)
        assert result[:-1] == body[:199]


# ---------------------------------------------------------------------------
# Custom limit
# ---------------------------------------------------------------------------


class TestPreviewBodyCustomLimit:
    def test_limit_10_on_short_string_passthrough(self) -> None:
        assert _preview_body("hello", limit=10) == "hello"

    def test_limit_10_on_exactly_10_chars_passthrough(self) -> None:
        body = "0123456789"
        assert _preview_body(body, limit=10) == body

    def test_limit_10_on_11_chars_truncates(self) -> None:
        body = "01234567890"  # 11 chars
        result = _preview_body(body, limit=10)
        assert len(result) == 10
        assert result == "012345678…"

    def test_limit_5_truncates_correctly(self) -> None:
        body = "abcdef"  # 6 chars
        result = _preview_body(body, limit=5)
        assert result == "abcd…"
        assert len(result) == 5


# ---------------------------------------------------------------------------
# Unicode / multi-byte content
# ---------------------------------------------------------------------------


class TestPreviewBodyUnicode:
    def test_unicode_chars_counted_as_one_each(self) -> None:
        body = "أ" * 201  # Arabic letter alef, 2 bytes each in UTF-8
        result = _preview_body(body)
        assert len(result) == 200

    def test_unicode_content_preserved_in_truncated_prefix(self) -> None:
        body = "日" * 201  # CJK, 3 bytes each in UTF-8
        result = _preview_body(body)
        assert result[:-1] == "日" * 199
        assert result[-1] == "…"

    def test_emoji_counted_as_one_char(self) -> None:
        body = "😊" * 201  # 4 bytes each in UTF-8
        result = _preview_body(body)
        assert len(result) == 200

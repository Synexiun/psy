"""Unit tests for _slug_from_filename() and _title_from_body() pure helpers
in discipline.content.help.

_slug_from_filename(name) → str | None
  Matches filenames of the form "NN_slug.md" (two leading digits, underscore,
  slug, .md extension).  Returns the slug portion on match, None otherwise.
  Pattern: ``r"^\d{2}_(.+)\.md$"``

_title_from_body(body, slug) → str
  Extracts the first level-1 Markdown heading ("# Title") from body text.
  Falls back to the slug with underscores replaced by spaces, title-cased,
  when no heading is found.  Pattern: ``r"^#\s+(.+)$"`` (multiline).
"""

from __future__ import annotations

import pytest

from discipline.content.help import _slug_from_filename, _title_from_body


# ---------------------------------------------------------------------------
# _slug_from_filename — accepted filenames
# ---------------------------------------------------------------------------


class TestSlugFromFilenameAccepted:
    def test_two_digit_prefix_returns_slug(self) -> None:
        assert _slug_from_filename("01_getting_started.md") == "getting_started"

    def test_two_digit_prefix_with_higher_number(self) -> None:
        assert _slug_from_filename("12_crisis_support.md") == "crisis_support"

    def test_two_digit_99(self) -> None:
        assert _slug_from_filename("99_last_article.md") == "last_article"

    def test_single_word_slug(self) -> None:
        assert _slug_from_filename("03_privacy.md") == "privacy"

    def test_slug_with_multiple_underscores(self) -> None:
        assert _slug_from_filename("05_privacy_and_data.md") == "privacy_and_data"

    def test_slug_preserved_exactly(self) -> None:
        assert _slug_from_filename("07_relapse_prevention_basics.md") == "relapse_prevention_basics"


# ---------------------------------------------------------------------------
# _slug_from_filename — rejected filenames
# ---------------------------------------------------------------------------


class TestSlugFromFilenameRejected:
    def test_readme_returns_none(self) -> None:
        assert _slug_from_filename("README.md") is None

    def test_no_numeric_prefix_returns_none(self) -> None:
        assert _slug_from_filename("getting_started.md") is None

    def test_single_digit_prefix_returns_none(self) -> None:
        # Pattern requires exactly two digits
        assert _slug_from_filename("1_article.md") is None

    def test_three_digit_prefix_returns_none(self) -> None:
        assert _slug_from_filename("001_article.md") is None

    def test_wrong_extension_returns_none(self) -> None:
        assert _slug_from_filename("01_article.txt") is None

    def test_no_extension_returns_none(self) -> None:
        assert _slug_from_filename("01_article") is None

    def test_empty_string_returns_none(self) -> None:
        assert _slug_from_filename("") is None

    def test_letters_prefix_returns_none(self) -> None:
        assert _slug_from_filename("ab_article.md") is None

    def test_trailing_content_after_md_returns_none(self) -> None:
        # Regex requires $ at end — extra suffix fails
        assert _slug_from_filename("01_article.md.bak") is None


# ---------------------------------------------------------------------------
# _title_from_body — heading extraction
# ---------------------------------------------------------------------------


class TestTitleFromBodyHeadingFound:
    def test_h1_heading_extracted(self) -> None:
        body = "# Getting Started\n\nSome content here."
        assert _title_from_body(body, "getting_started") == "Getting Started"

    def test_h1_heading_stripped(self) -> None:
        body = "#  Spaces Around Title  \n\nContent"
        assert _title_from_body(body, "slug") == "Spaces Around Title"

    def test_first_heading_returned_when_multiple(self) -> None:
        body = "# First Heading\n\n## Second Heading\n\n# Third Heading"
        result = _title_from_body(body, "slug")
        assert result == "First Heading"

    def test_heading_mid_document(self) -> None:
        body = "Some text.\n\n# Mid Document Title\n\nMore text."
        assert _title_from_body(body, "fallback") == "Mid Document Title"

    def test_heading_not_h2(self) -> None:
        # ## is h2 — should not match
        body = "## Not a Title\n\n# Real Title"
        assert _title_from_body(body, "slug") == "Real Title"


# ---------------------------------------------------------------------------
# _title_from_body — slug fallback (no heading found)
# ---------------------------------------------------------------------------


class TestTitleFromBodyFallback:
    def test_no_heading_falls_back_to_slug(self) -> None:
        body = "Some content without a heading."
        result = _title_from_body(body, "getting_started")
        assert result == "Getting Started"

    def test_underscores_replaced_by_spaces(self) -> None:
        result = _title_from_body("", "privacy_and_data")
        assert "_" not in result

    def test_fallback_is_title_cased(self) -> None:
        result = _title_from_body("", "crisis_support_basics")
        assert result == "Crisis Support Basics"

    def test_empty_body_uses_slug(self) -> None:
        result = _title_from_body("", "article_name")
        assert result == "Article Name"

    def test_h2_only_body_falls_back(self) -> None:
        # Only ## (h2) — pattern requires exactly one # before space
        body = "## Section Heading\n\nContent"
        result = _title_from_body(body, "my_article")
        assert result == "My Article"

    def test_single_word_slug_title_cased(self) -> None:
        result = _title_from_body("", "privacy")
        assert result == "Privacy"

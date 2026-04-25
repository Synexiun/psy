"""Unit tests for discipline.content.help — the in-process help article loader.

Covers:
- article_slugs() returns a non-empty sorted list
- slug derivation from NN_slug.md filenames
- title extraction from first # Heading in markdown body
- get_article returns HelpArticle for known slugs
- get_article returns None for unknown slugs
- get_article returns en body for non-en locale (no-MT rule)
- locale stamp is set to requested locale on fallback
- list_articles returns all articles sorted by slug
- list_articles returns correct locale stamp for non-en
- HelpArticle is a frozen dataclass
- updated_at is a YYYY-MM-DD ISO date string
"""

from __future__ import annotations

import asyncio
import re

import pytest

from discipline.content.help import (
    HelpArticle,
    article_slugs,
    get_article,
    list_articles,
)


# ---------------------------------------------------------------------------
# article_slugs
# ---------------------------------------------------------------------------


class TestArticleSlugs:
    def test_returns_non_empty_list(self) -> None:
        slugs = article_slugs()
        assert isinstance(slugs, list)
        assert len(slugs) > 0

    def test_returns_sorted_list(self) -> None:
        slugs = article_slugs()
        assert slugs == sorted(slugs)

    def test_known_slug_present(self) -> None:
        assert "getting_started" in article_slugs()

    def test_all_slugs_are_strings(self) -> None:
        for slug in article_slugs():
            assert isinstance(slug, str)

    def test_slugs_have_no_numeric_prefix(self) -> None:
        """Filename prefix '00_' must be stripped; slugs start with a letter."""
        for slug in article_slugs():
            assert not re.match(r"^\d", slug), f"slug {slug!r} starts with a digit"

    def test_slugs_have_no_md_extension(self) -> None:
        for slug in article_slugs():
            assert not slug.endswith(".md"), f"slug {slug!r} has .md extension"

    def test_sixteen_articles_loaded(self) -> None:
        """Docs/Help/ ships with 16 articles (00–15).  If this changes update here."""
        assert len(article_slugs()) == 16


# ---------------------------------------------------------------------------
# get_article — en locale
# ---------------------------------------------------------------------------


class TestGetArticleEn:
    @pytest.mark.asyncio
    async def test_returns_help_article_for_known_slug(self) -> None:
        article = await get_article("getting_started", "en")
        assert isinstance(article, HelpArticle)

    @pytest.mark.asyncio
    async def test_returns_none_for_unknown_slug(self) -> None:
        result = await get_article("totally_nonexistent_slug_xyz", "en")
        assert result is None

    @pytest.mark.asyncio
    async def test_slug_field_matches_request(self) -> None:
        article = await get_article("getting_started", "en")
        assert article is not None
        assert article.slug == "getting_started"

    @pytest.mark.asyncio
    async def test_locale_is_en(self) -> None:
        article = await get_article("getting_started", "en")
        assert article is not None
        assert article.locale == "en"

    @pytest.mark.asyncio
    async def test_title_is_non_empty_string(self) -> None:
        article = await get_article("getting_started", "en")
        assert article is not None
        assert isinstance(article.title, str)
        assert article.title.strip() != ""

    @pytest.mark.asyncio
    async def test_body_md_contains_markdown_heading(self) -> None:
        article = await get_article("getting_started", "en")
        assert article is not None
        assert "#" in article.body_md

    @pytest.mark.asyncio
    async def test_updated_at_is_iso_date(self) -> None:
        article = await get_article("getting_started", "en")
        assert article is not None
        assert re.match(r"^\d{4}-\d{2}-\d{2}$", article.updated_at), (
            f"updated_at {article.updated_at!r} is not YYYY-MM-DD"
        )

    @pytest.mark.asyncio
    async def test_all_slugs_resolve(self) -> None:
        for slug in article_slugs():
            result = await get_article(slug, "en")
            assert result is not None, f"slug {slug!r} returned None"


# ---------------------------------------------------------------------------
# get_article — non-en locale fallback (CLAUDE.md no-MT rule)
# ---------------------------------------------------------------------------


class TestGetArticleLocaleFallback:
    @pytest.mark.asyncio
    async def test_fr_locale_returns_en_body(self) -> None:
        en = await get_article("getting_started", "en")
        fr = await get_article("getting_started", "fr")
        assert en is not None and fr is not None
        assert fr.body_md == en.body_md

    @pytest.mark.asyncio
    async def test_fr_locale_stamps_fr_on_article(self) -> None:
        fr = await get_article("getting_started", "fr")
        assert fr is not None
        assert fr.locale == "fr"

    @pytest.mark.asyncio
    async def test_ar_locale_returns_en_body(self) -> None:
        en = await get_article("getting_started", "en")
        ar = await get_article("getting_started", "ar")
        assert en is not None and ar is not None
        assert ar.body_md == en.body_md

    @pytest.mark.asyncio
    async def test_ar_locale_stamps_ar_on_article(self) -> None:
        ar = await get_article("getting_started", "ar")
        assert ar is not None
        assert ar.locale == "ar"

    @pytest.mark.asyncio
    async def test_fa_locale_stamps_fa_on_article(self) -> None:
        fa = await get_article("getting_started", "fa")
        assert fa is not None
        assert fa.locale == "fa"

    @pytest.mark.asyncio
    async def test_non_en_unknown_slug_returns_none(self) -> None:
        result = await get_article("unknown_slug_xyz", "fr")
        assert result is None


# ---------------------------------------------------------------------------
# list_articles
# ---------------------------------------------------------------------------


class TestListArticles:
    @pytest.mark.asyncio
    async def test_returns_all_articles(self) -> None:
        articles = await list_articles("en")
        assert len(articles) == len(article_slugs())

    @pytest.mark.asyncio
    async def test_sorted_by_slug(self) -> None:
        articles = await list_articles("en")
        slugs = [a.slug for a in articles]
        assert slugs == sorted(slugs)

    @pytest.mark.asyncio
    async def test_all_have_en_locale(self) -> None:
        articles = await list_articles("en")
        for a in articles:
            assert a.locale == "en"

    @pytest.mark.asyncio
    async def test_fr_locale_stamps_fr_on_all(self) -> None:
        articles = await list_articles("fr")
        for a in articles:
            assert a.locale == "fr"

    @pytest.mark.asyncio
    async def test_all_have_title(self) -> None:
        articles = await list_articles("en")
        for a in articles:
            assert a.title.strip() != "", f"article {a.slug!r} has empty title"

    @pytest.mark.asyncio
    async def test_all_have_body_md(self) -> None:
        articles = await list_articles("en")
        for a in articles:
            assert len(a.body_md) > 0, f"article {a.slug!r} has empty body"


# ---------------------------------------------------------------------------
# HelpArticle frozen dataclass
# ---------------------------------------------------------------------------


class TestHelpArticleFrozen:
    @pytest.mark.asyncio
    async def test_article_is_frozen(self) -> None:
        article = await get_article("getting_started", "en")
        assert article is not None
        with pytest.raises((AttributeError, TypeError)):
            article.slug = "mutated"  # type: ignore[misc]

    def test_can_construct_directly(self) -> None:
        a = HelpArticle(
            slug="test",
            title="Test",
            body_md="# Test",
            locale="en",
            updated_at="2026-04-25",
        )
        assert a.slug == "test"

"""Per-locale help article loader.

Help articles are authored in ``Docs/Help/`` (English source-of-truth) and
loaded at import time into an in-process index.  The index is keyed by
``(slug, locale)``; the ``en`` fallback is used when a translation is not yet
available (CLAUDE.md no-MT rule: never machine-translate clinical content).

Slug derivation: filenames ``NN_slug_with_underscores.md`` → slug is the part
after the two-digit prefix and underscore, e.g. ``00_getting_started.md``
→ ``getting_started``.

Title derivation: the first ``# Title`` heading in the markdown body.

CLAUDE.md rule: do NOT import this module into ``apps/web-crisis``.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from discipline.shared.i18n import Locale

# Resolve Docs/Help relative to this file's location in the monorepo.
# Path: services/api/src/discipline/content/help.py
#       → ../../../../.. → repo root
#       → Docs/Help
_REPO_ROOT = Path(__file__).parents[5]
_HELP_DIR = _REPO_ROOT / "Docs" / "Help"

_UPDATED_AT_FALLBACK = "2026-04-25"
_FILENAME_RE = re.compile(r"^\d{2}_(.+)\.md$")
_HEADING_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)


@dataclass(frozen=True)
class HelpArticle:
    slug: str
    title: str
    body_md: str
    locale: Locale
    updated_at: str


def _slug_from_filename(name: str) -> str | None:
    m = _FILENAME_RE.match(name)
    return m.group(1) if m else None


def _title_from_body(body: str, slug: str) -> str:
    m = _HEADING_RE.search(body)
    return m.group(1).strip() if m else slug.replace("_", " ").title()


def _load_en_articles() -> dict[str, HelpArticle]:
    """Load all English help articles from Docs/Help/ at import time."""
    index: dict[str, HelpArticle] = {}
    if not _HELP_DIR.exists():
        return index
    for path in sorted(_HELP_DIR.glob("*.md")):
        if path.name == "README.md":
            continue
        slug = _slug_from_filename(path.name)
        if slug is None:
            continue
        body = path.read_text(encoding="utf-8")
        title = _title_from_body(body, slug)
        mtime = os.path.getmtime(path)
        from datetime import date, timezone
        from datetime import datetime as dt

        updated_at = dt.fromtimestamp(mtime, tz=timezone.utc).date().isoformat()
        index[slug] = HelpArticle(
            slug=slug,
            title=title,
            body_md=body,
            locale=cast(Locale, "en"),
            updated_at=updated_at,
        )
    return index


# Single in-process index keyed by slug (en source-of-truth only for now).
# Translation overlays will be added when fr/ar/fa are reviewed and released.
_EN_INDEX: dict[str, HelpArticle] = _load_en_articles()


async def get_article(slug: str, locale: Locale) -> HelpArticle | None:
    """Return the help article for *slug*, falling back to English if the
    requested locale is not yet available (CLAUDE.md no-MT rule).

    Returns ``None`` if the slug does not exist in any locale.
    """
    # Locale-specific overlay would be checked here when translations ship.
    # For now all articles are served from the en index with locale stamped.
    article = _EN_INDEX.get(slug)
    if article is None:
        return None
    if locale == "en":
        return article
    # Fall back to en, stamping the requested locale so callers can render
    # the locale UI frame correctly while the body is English.
    return HelpArticle(
        slug=article.slug,
        title=article.title,
        body_md=article.body_md,
        locale=locale,
        updated_at=article.updated_at,
    )


async def list_articles(locale: Locale) -> list[HelpArticle]:
    """Return all help articles sorted by slug, falling back to English."""
    articles = []
    for slug in sorted(_EN_INDEX):
        article = await get_article(slug, locale)
        if article is not None:
            articles.append(article)
    return articles


def article_slugs() -> list[str]:
    """Return all available slug IDs (useful for generateStaticParams / sitemaps)."""
    return sorted(_EN_INDEX.keys())


__all__ = ["HelpArticle", "article_slugs", "get_article", "list_articles"]

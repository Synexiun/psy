"""Per-locale help article loader.

The help articles are authored under ``Docs/Help/`` and bundled into the
service at build time as structured JSON (one file per locale).  This module
exposes the lookup by slug (e.g. ``how_it_works``, ``urge_surfing``).
"""

from __future__ import annotations

from dataclasses import dataclass

from discipline.shared.i18n import Locale


@dataclass(frozen=True)
class HelpArticle:
    slug: str
    title: str
    body_md: str
    locale: Locale
    updated_at: str


async def get_article(_slug: str, _locale: Locale) -> HelpArticle | None:
    """Stub.  Wire to the bundled JSON loader in a later milestone."""
    raise NotImplementedError


async def list_articles(_locale: Locale) -> list[HelpArticle]:
    """Stub."""
    raise NotImplementedError


__all__ = ["HelpArticle", "get_article", "list_articles"]

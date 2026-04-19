"""Content HTTP surface — safety directory, help articles, intervention scripts."""

from __future__ import annotations

from fastapi import APIRouter, Header

from discipline.shared.i18n import negotiate_locale

from .safety_directory import resolve

router = APIRouter(prefix="/content", tags=["content"])


@router.get("/safety-directory/{country}")
async def safety_directory(
    country: str,
    accept_language: str | None = Header(default=None, alias="Accept-Language"),
) -> dict[str, object]:
    locale = negotiate_locale(None, accept_language)
    entry = resolve(country, locale)
    return {
        "country": entry.country,
        "locale": entry.locale,
        "emergency": {"label": entry.emergency_label, "number": entry.emergency_number},
        "hotlines": [
            {
                "id": h.id,
                "name": h.name,
                "number": h.number,
                "sms": h.sms,
                "web": h.web,
                "hours": h.hours,
                "cost": h.cost,
                "verified_at": h.verified_at,
            }
            for h in entry.hotlines
        ],
    }


@router.get("/help/{slug}")
async def help_article(slug: str) -> dict[str, str]:
    """Stub."""
    return {"status": "not_implemented", "slug": slug}

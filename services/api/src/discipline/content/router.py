"""Content HTTP surface — safety directory, help articles, intervention scripts,
and crisis resources.

The crisis resources endpoint (GET /v1/crisis/resources) must be:
- PUBLIC (no auth required) — reachable when Clerk is mid-outage or the
  user's session is invalid.  This mirrors the CLAUDE.md Rule #1 contract:
  crisis paths are never auth-gated.
- DETERMINISTIC — no LLM, no DB round-trip.  Returns a static payload so
  the endpoint is effectively a typed alias for the inlined COPY dict that
  the ``apps/web-crisis`` static export already embeds.
- UNLIMITED rate — the rate-limit middleware whitelist includes /v1/crisis/*.

"""

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


# =============================================================================
# Crisis resources router
#
# Separate APIRouter (no prefix here) so it mounts at /v1/crisis/resources
# when registered with app.include_router(crisis_router, prefix="/v1").
#
# CRITICAL (CLAUDE.md Rule #1):
# - No auth dependency.
# - No LLM calls.
# - No DB calls — payload is a deterministic static dict.
# - Never feature-flagged.
# The rate-limit middleware already whitelists /v1/crisis/* as UNLIMITED.
# =============================================================================

from pydantic import BaseModel  # noqa: E402


class CrisisHotline(BaseModel):
    """A single crisis hotline entry."""

    name: str
    number: str
    sms: str | None = None
    web: str | None = None
    available: str = "24/7"


class CrisisResourcesResponse(BaseModel):
    """Deterministic crisis resources payload.

    This mirrors the inlined COPY dict in ``apps/web-crisis/src/lib/locale.ts``
    for the ``en`` locale.  The response intentionally does NOT vary by locale
    or user — any personalisation would introduce a DB round-trip and break the
    determinism guarantee.  Locale-specific hotlines are served by
    ``GET /v1/content/safety-directory/{country}`` instead.
    """

    emergency_number: str
    text_line: str | None
    hotlines: list[CrisisHotline]
    # Inline coping anchors — static, evidence-based, no LLM
    coping_steps: list[str]


# Static payload — edit with clinical QA sign-off only.
_CRISIS_RESOURCES = CrisisResourcesResponse(
    emergency_number="911",
    text_line="988",
    hotlines=[
        CrisisHotline(
            name="988 Suicide & Crisis Lifeline",
            number="988",
            sms="988",
            web="https://988lifeline.org",
            available="24/7",
        ),
        CrisisHotline(
            name="Crisis Text Line",
            number="",
            sms="HOME to 741741",
            web="https://www.crisistextline.org",
            available="24/7",
        ),
        CrisisHotline(
            name="SAMHSA National Helpline",
            number="1-800-662-4357",
            sms=None,
            web="https://www.samhsa.gov/find-help/national-helpline",
            available="24/7",
        ),
    ],
    coping_steps=[
        "Take one slow breath — in for 4 counts, out for 6.",
        "Name five things you can see around you right now.",
        "You are safe in this moment. The urge will pass.",
        "Reach out to someone you trust, or call/text the lifeline above.",
    ],
)

crisis_router = APIRouter(tags=["crisis"])


@crisis_router.get(
    "/crisis/resources",
    response_model=CrisisResourcesResponse,
    # No auth — this must be reachable without a valid session.
)
async def crisis_resources() -> CrisisResourcesResponse:
    """Return static crisis resources (hotlines + coping anchors).

    This endpoint is deterministic, requires no authentication, and
    makes no LLM or database calls.  It mirrors the inlined COPY dict
    in the ``apps/web-crisis`` static export so the web-app can surface
    a consistent set of resources without importing from the crisis
    surface.

    CLAUDE.md Rule #1: crisis paths are never auth-gated, never LLM-
    backed, and never feature-flagged.  This endpoint is an in-process
    constant lookup.

    # TODO: when the safety-directory module carries a "global default"
    # entry, delegate to it here so hotline numbers stay in one
    # source of truth.  Until then this static dict is the ground truth.
    """
    return _CRISIS_RESOURCES

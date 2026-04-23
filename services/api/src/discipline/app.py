from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from discipline import __version__

# Routers are imported from each module.
# Modules are added incrementally as features land.
from discipline.admin.router import router as admin_router
from discipline.analytics.router import router as analytics_router
from discipline.clinical.router import router as clinical_router
from discipline.config import get_settings
from discipline.content.router import router as content_router
from discipline.content.safety_directory import (
    MirrorDriftError,
    check_freshness,
    verify_mirror_parity,
)
from discipline.identity.router import router as identity_router
from discipline.intervention.router import router as intervention_router
from discipline.memory.router import router as memory_router
from discipline.signal.router import router as signal_router
from discipline.compliance.router import router as compliance_router
from discipline.billing.router import router as billing_router
from discipline.enterprise.router import router as enterprise_router
from discipline.notifications.router import router as notifications_router
from discipline.pattern.router import router as pattern_router
from discipline.psychometric.router import router as psychometric_router
from discipline.reports.router import router as reports_router
from discipline.resilience.router import router as resilience_router
from discipline.shared.db import _get_engine
from discipline.shared.http import PhiBoundaryMiddleware
from discipline.shared.i18n import SUPPORTED_LOCALES
from discipline.shared.i18n.package_catalog import (
    is_locale_releasable,
    load_catalog,
)
from discipline.shared.logging import configure_logging
from discipline.shared.redis_client import get_redis_client, reset_pool
from discipline.shared.tracing import configure_tracing


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings.log_level)
    configure_tracing(settings.otel_service_name, settings.otel_endpoint)

    # Eagerly initialize singletons so failures surface at startup
    # rather than on the first request.
    _ = get_redis_client()
    _ = _get_engine()

    yield

    # Graceful shutdown: close shared pools so uvicorn workers don't
    # leak connections on reload / scale-in.
    reset_pool()
    engine = _get_engine()
    await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Discipline OS API",
        version=__version__,
        lifespan=lifespan,
        docs_url="/internal/docs" if get_settings().env != "prod" else None,
    )

    # PHI boundary middleware (CLAUDE.md Rule #11): endpoints opt-in via
    # ``Depends(mark_phi_boundary)``; this middleware appends the
    # ``X-Phi-Boundary: 1`` header to the response on the way out.
    app.add_middleware(PhiBoundaryMiddleware)

    @app.get("/health", tags=["system"])
    async def health() -> JSONResponse:
        """Operational health check.

        Verifies PostgreSQL and Redis connectivity.  Returns 503 if
        either dependency is unreachable so the load balancer can
        shift traffic away from an unhealthy task.
        """
        checks: dict[str, str] = {}
        status_code = 200

        # Redis check
        try:
            redis_client = get_redis_client()
            redis_client.ping()
            checks["redis"] = "ok"
        except Exception as exc:
            checks["redis"] = f"error: {exc}"
            status_code = 503

        # PostgreSQL check
        try:
            from sqlalchemy import text
            engine = _get_engine()
            async with engine.connect() as conn:
                result = await conn.execute(text("SELECT 1"))
                _ = result.scalar()
            checks["postgres"] = "ok"
        except Exception as exc:
            checks["postgres"] = f"error: {exc}"
            status_code = 503

        return JSONResponse(
            {"status": "ok" if status_code == 200 else "degraded", "checks": checks, "version": __version__},
            status_code=status_code,
        )

    @app.get("/system/locale-status", tags=["system"])
    async def locale_status() -> JSONResponse:
        """Release-gate view of i18n catalog status (CLAUDE.md Rule #8).

        The deploy pipeline queries this endpoint before shipping a locale
        live — a locale reported as ``draft`` is refused regardless of
        whether the catalog file exists, because ``draft`` means "no
        clinical native-reviewer sign-off yet".

        No auth: this is an operational surface exposing non-PHI
        governance state (status enum, review date, reviewer name).
        """
        releasable: list[str] = []
        draft: list[str] = []
        details: dict[str, dict[str, object]] = {}
        for locale in SUPPORTED_LOCALES:
            catalog = load_catalog(locale)
            details[locale] = {
                "status": catalog.meta.status.value,
                "direction": catalog.meta.direction,
                "reviewed_by": catalog.meta.reviewed_by,
                "reviewed_at": catalog.meta.reviewed_at,
            }
            if is_locale_releasable(locale):
                releasable.append(locale)
            else:
                draft.append(locale)
        return JSONResponse(
            {
                "releasable": releasable,
                "draft": draft,
                "details": details,
            }
        )

    @app.get("/system/safety-directory-status", tags=["system"])
    async def safety_directory_status() -> JSONResponse:
        """Release-gate view of safety-directory freshness + mirror parity.

        CLAUDE.md Rule #10 — the safety directory has a 90-day
        ``reviewWindowDays``; entries older than the window block their
        country-locale.  CI calls this endpoint before each deploy and
        fails the build if ``blocked_locales`` is non-empty or
        ``mirror_parity_ok`` is False.

        Runtime resolution (``resolve()``) keeps serving stale entries —
        showing a slightly outdated hotline is safer than showing
        nothing on a crisis path.  This endpoint exists separately so
        the gate is operational/CI, not user-visible.

        No auth: operational governance surface, no PHI.

        Response shape:
        - ``stale_entries``: list of ``{country, locale, hotline_id,
          verified_at, days_stale}`` — each entry that breached the
          freshness window.
        - ``blocked_locales``: list of ``country/locale`` strings —
          country-locale pairs with at least one stale hotline.
        - ``mirror_parity_ok``: bool — True when api copy and package
          copy of hotlines.json have identical sha256.
        - ``mirror_drift_detail``: nullable string — human-readable
          drift explanation when parity fails (paths + sha prefixes).
        """
        stale = check_freshness()
        blocked: set[str] = {f"{s.country}/{s.locale}" for s in stale}
        try:
            verify_mirror_parity()
            parity_ok = True
            drift_detail: str | None = None
        except MirrorDriftError as exc:
            parity_ok = False
            drift_detail = str(exc)
        except FileNotFoundError as exc:
            # Package mirror missing on disk (e.g. dev environment without
            # the workspace) — treat as parity failure but distinguish in
            # the detail string so ops can tell "drift" from "missing".
            parity_ok = False
            drift_detail = f"mirror file not found: {exc}"

        return JSONResponse(
            {
                "stale_entries": [
                    {
                        "country": s.country,
                        "locale": s.locale,
                        "hotline_id": s.hotline_id,
                        "verified_at": s.verified_at.isoformat(),
                        "days_stale": s.days_stale,
                    }
                    for s in stale
                ],
                "blocked_locales": sorted(blocked),
                "mirror_parity_ok": parity_ok,
                "mirror_drift_detail": drift_detail,
            }
        )

    app.include_router(identity_router, prefix="/v1")
    app.include_router(intervention_router, prefix="/v1")
    app.include_router(clinical_router, prefix="/v1")
    app.include_router(resilience_router, prefix="/v1")
    app.include_router(psychometric_router, prefix="/v1")
    app.include_router(analytics_router, prefix="/v1")
    app.include_router(reports_router, prefix="/v1")
    app.include_router(content_router, prefix="/v1")
    app.include_router(memory_router, prefix="/v1")
    app.include_router(signal_router, prefix="/v1")
    app.include_router(compliance_router, prefix="/v1")
    app.include_router(notifications_router, prefix="/v1")
    app.include_router(pattern_router, prefix="/v1")
    app.include_router(billing_router, prefix="/v1")
    app.include_router(enterprise_router, prefix="/v1")
    app.include_router(admin_router, prefix="/v1")

    return app


app = create_app()

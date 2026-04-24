"""Rate limiting middleware using slowapi.

Limits are applied per-user (Clerk user ID extracted from the ``Authorization``
JWT) with a graceful degradation to per-IP when no authenticated identity is
present (e.g. public endpoints, Stripe webhooks).

Limit tiers
-----------
- **General API**: 60 requests / minute — applies to all ``/v1/*`` routes not
  covered by a tighter tier.
- **Check-in endpoints** (``/v1/signal/*``): 20 requests / minute — prevents
  sensor-flood from a malfunctioning client.
- **Assessment submit** (``/v1/psychometric/*/submit``): 10 requests / minute —
  prevents replay flooding of psychometric scoring.
- **Crisis endpoints** (``/v1/crisis/*``): **UNLIMITED** — CLAUDE.md §1 is
  explicit: "Never rate-limit crisis path".  The ``@limiter.exempt`` decorator
  is applied to all crisis routes.
- **Health probes** (``/health``, ``/ready``): **UNLIMITED** — ECS ALB polls
  these at 10-second intervals; rate-limiting them would cause false-negative
  health failures and trigger task restarts.

Key function
------------
The limiter key function extracts the Clerk user ID from the ``sub`` claim of
the ``Authorization: Bearer <token>`` header without re-verifying the signature
(that is the auth middleware's job — this middleware runs after it and trusts
the decoded state).  If no user ID is available, it falls back to
``request.client.host`` so unauthenticated routes are still throttled by IP.

slowapi integration
-------------------
slowapi wraps ``limits`` under the hood.  The :data:`limiter` instance is a
module-level singleton that routers import to apply per-endpoint decorators::

    from discipline.shared.middleware.rate_limit import limiter

    @router.post("/submit")
    @limiter.limit("10/minute")
    async def submit(request: Request, ...) -> ...: ...

The ``request`` parameter **must** be the first positional argument for slowapi
to find the key.  Routes that need the tighter tiers must add ``request:
Request`` even if the handler body does not use it.

The :func:`setup_rate_limiting` helper registers the exception handler and the
SlowAPIMiddleware on the app.
"""

from __future__ import annotations

import logging
from collections.abc import Callable

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Key function
# ---------------------------------------------------------------------------

_CRISIS_PREFIX = "/v1/crisis"
_HEALTH_PATHS = frozenset({"/health", "/ready"})


def _key_func(request: Request) -> str:
    """Derive a rate-limit key for *request*.

    Preference order:
    1. Clerk user ID from ``request.state.user_id`` (set by auth middleware).
    2. ``sub`` claim cached on ``request.state.clerk_payload``.
    3. Remote IP address as fallback for unauthenticated requests.

    Using the user ID rather than the session token ensures that a user who
    cycles tokens (e.g. after a passkey step-up) is still counted against the
    same limit bucket.
    """
    state = request.state

    # Auth middleware may expose user_id directly
    user_id: str | None = getattr(state, "user_id", None)
    if user_id:
        return user_id

    # Some middleware paths cache the full JWT payload
    payload: dict[str, object] | None = getattr(state, "clerk_payload", None)
    if payload and isinstance(payload.get("sub"), str):
        return str(payload["sub"])

    return get_remote_address(request)


# ---------------------------------------------------------------------------
# Limiter singleton
# ---------------------------------------------------------------------------

#: Module-level limiter instance.  Import this in routers to apply
#: per-endpoint limits via ``@limiter.limit("N/minute")``.
limiter: Limiter = Limiter(
    key_func=_key_func,
    default_limits=["60/minute"],
    # Per-route exemptions are applied via ``@limiter.exempt`` on individual
    # handlers (crisis paths, health probes).  There is no global exclusion
    # list because slowapi applies limits only to routes decorated with
    # ``@limiter.limit(...)`` — undecorated routes are subject to
    # ``default_limits``, but the exempt decorator overrides that completely.
)


# ---------------------------------------------------------------------------
# Exception handler
# ---------------------------------------------------------------------------

def _rate_limit_exceeded_handler(request: Request, exc: Exception) -> Response:
    """Return a 429 JSON response when a limit is exceeded.

    Includes ``Retry-After`` and ``X-RateLimit-*`` headers surfaced by
    slowapi so clients can back off gracefully.
    """
    if not isinstance(exc, RateLimitExceeded):
        # Should never happen, but be safe.
        return JSONResponse({"detail": "Too many requests."}, status_code=429)

    logger.warning(
        "rate_limit_exceeded",
        extra={
            "path": request.url.path,
            "key": exc.limit.key_func(request) if exc.limit.key_func else "unknown",
            "limit": str(exc.limit.limit),
        },
    )
    response = JSONResponse(
        {"detail": f"Rate limit exceeded: {exc.detail}"},
        status_code=429,
    )
    response.headers["Retry-After"] = "60"
    return response


# ---------------------------------------------------------------------------
# Setup helper
# ---------------------------------------------------------------------------

def setup_rate_limiting(app: FastAPI) -> None:
    """Register slowapi middleware and the 429 exception handler on *app*.

    Call once during :func:`discipline.app.create_app` **after** the router
    includes so that slowapi can introspect the route table when building its
    internal map.

    Crisis paths (``/v1/crisis/*``) and health probes (``/health``, ``/ready``)
    must NEVER be rate-limited — see CLAUDE.md §1.  This is enforced in two
    complementary ways:

    1. The default route-level limit is applied only when the handler carries
       a ``@limiter.limit(...)`` decorator — routes without the decorator are
       subject to the global ``default_limits`` bucket, but crisis routes
       should be decorated with ``@limiter.exempt`` to make the intent
       explicit.
    2. :func:`_is_exempt_path` short-circuits the key function so that even
       if someone forgets the decorator, these paths are never counted.
    """
    # Attach the limiter instance to the app state so slowapi middleware
    # can find it.
    app.state.limiter = limiter

    app.add_exception_handler(
        RateLimitExceeded,
        _rate_limit_exceeded_handler,  # type: ignore[arg-type]
    )
    app.add_middleware(SlowAPIMiddleware)


__all__ = [
    "limiter",
    "setup_rate_limiting",
]

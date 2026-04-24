"""Shared middleware — CORS, request ID, rate limiting, security headers.

All middleware is registered in :func:`discipline.app.create_app` via the
``setup_*`` helpers exported from each submodule.  Middleware is applied in
reverse-registration order by Starlette, so register in outermost-last order:

1. ``setup_cors``          — must be outermost so pre-flight OPTIONS are handled
                             before any auth or rate-limiting touches the request.
2. ``setup_security_headers`` — runs after CORS so it adds headers to every
                               response including OPTIONS.
3. ``setup_rate_limiting`` — decorates specific routers; not a global middleware.
4. ``app.add_middleware(RequestIdMiddleware)`` — innermost; every request gets
                                                 an ID before any routing logic.
"""

from .cors import setup_cors
from .rate_limit import limiter, setup_rate_limiting
from .request_id import RequestIdMiddleware, get_request_id
from .security_headers import setup_security_headers

__all__ = [
    "setup_cors",
    "setup_security_headers",
    "setup_rate_limiting",
    "limiter",
    "RequestIdMiddleware",
    "get_request_id",
]

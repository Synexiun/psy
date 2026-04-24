"""Security response-headers middleware.

Adds a baseline set of security headers to every API response.  The choices
follow OWASP recommendations for REST APIs and are aligned with the CSP
strategy described in ``Docs/Technicals/16_Web_Application.md``.

Header rationale
----------------
``X-Content-Type-Options: nosniff``
    Prevents browsers from MIME-sniffing a response away from the declared
    Content-Type.  Especially relevant for JSON API responses that may be
    embedded in a ``<script>`` tag by a malicious page.

``X-Frame-Options: DENY``
    The API does not serve HTML and must never be framed.  Blocks clickjacking
    attempts that embed API response URLs in iframes.

``X-XSS-Protection: 0``
    The legacy XSS auditor in older browsers is itself a source of
    vulnerabilities (information disclosure, bypass via injection).  Setting it
    to ``0`` disables the auditor per OWASP 2023 guidance.  Modern browsers
    rely on CSP instead.

``Strict-Transport-Security: max-age=31536000; includeSubDomains``
    Forces HTTPS for 1 year including all subdomains once a browser has
    visited any API endpoint.  The ``preload`` directive is intentionally
    omitted because the API sits behind an ALB and domain-preload registration
    requires careful coordination with the marketing site.

``Referrer-Policy: strict-origin-when-cross-origin``
    Sends the origin only (no path) for cross-origin requests so that API
    paths (which may contain user IDs or session tokens) are not leaked in the
    ``Referer`` header to third-party origins.

``Cache-Control: no-store``
    Default for API responses: instructs caches at every layer (browser,
    CDN, ALB) not to store the response body.  PHI-bearing routes already
    set this explicitly; the middleware is a belt-and-suspenders fallback.
    Individual routes may override with a more permissive directive (e.g.
    ``public, max-age=3600`` for a public catalog endpoint).

Note: ``Content-Security-Policy`` is deliberately omitted here.  The API
returns JSON, not HTML; a CSP header on JSON responses provides no protection
and would create false confidence.  CSP belongs on the web-app surfaces
(``apps/web-*``), not on the API.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from starlette.types import ASGIApp

_SECURITY_HEADERS: dict[str, str] = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "0",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Cache-Control": "no-store",
}


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Append security headers to every response.

    Headers are applied unconditionally — the middleware has no knowledge of
    route semantics.  Routes that require a different ``Cache-Control``
    directive should set it after calling ``call_next``; the later
    ``response.headers`` assignment will overwrite the middleware-set value
    because Starlette processes headers in insertion order and ``call_next``
    runs the endpoint before the middleware can inspect the response.

    Actually the middleware runs *after* the endpoint returns, so any
    header set by the endpoint or an inner middleware takes precedence over
    what this middleware writes — which means an endpoint can intentionally
    override ``Cache-Control`` by setting its own value in the ``Response``
    object before returning.
    """

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        response = await call_next(request)
        for header, value in _SECURITY_HEADERS.items():
            # Only set the header if the endpoint hasn't already set it,
            # so that routes which intentionally override (e.g. a public
            # catalog with a longer max-age) are not silently clobbered.
            if header not in response.headers:
                response.headers[header] = value
        return response


def setup_security_headers(app: FastAPI) -> None:
    """Register :class:`SecurityHeadersMiddleware` on *app*.

    Call once during :func:`discipline.app.create_app`.
    """
    app.add_middleware(SecurityHeadersMiddleware)


__all__ = [
    "SecurityHeadersMiddleware",
    "setup_security_headers",
]

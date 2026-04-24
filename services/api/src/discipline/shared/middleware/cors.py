"""CORS middleware configuration.

Allowed origins are the five local dev ports plus any origins supplied via the
``ALLOWED_ORIGINS`` environment variable (comma-separated).  The variable is
intended for staging and production, e.g.:

    ALLOWED_ORIGINS=https://app.disciplineos.com,https://clinician.disciplineos.com

Design notes
------------
- ``allow_credentials=True`` is required because the web-app, web-clinician, and
  web-enterprise surfaces all send ``Authorization`` headers and Clerk session
  cookies.
- ``*`` is never used as the origin when ``allow_credentials=True`` — browsers
  reject it with a CORS error, and it would be a security violation regardless
  (CLAUDE.md §"Non-negotiable rules").
- The ``X-Request-ID`` and ``Accept-Language`` request headers are explicitly
  listed so pre-flight checks pass for clients that add them.
"""

from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

_DEV_ORIGINS: list[str] = [
    "http://localhost:3010",  # web-marketing
    "http://localhost:3020",  # web-app
    "http://localhost:3030",  # web-clinician
    "http://localhost:3040",  # web-enterprise
    "http://localhost:3050",  # web-crisis
]

_ALLOWED_METHODS: list[str] = [
    "GET",
    "POST",
    "PUT",
    "DELETE",
    "OPTIONS",
    "PATCH",
]

_ALLOWED_HEADERS: list[str] = [
    "Authorization",
    "Content-Type",
    "X-Request-ID",
    "Accept-Language",
]


def _get_allowed_origins() -> list[str]:
    """Return the combined list of allowed origins.

    Always includes the five local dev ports.  Any additional origins
    specified in ``ALLOWED_ORIGINS`` (comma-separated) are appended —
    empty strings produced by trailing commas are silently filtered.
    """
    extra = os.environ.get("ALLOWED_ORIGINS", "")
    extra_origins = [o.strip() for o in extra.split(",") if o.strip()]
    return _DEV_ORIGINS + extra_origins


def setup_cors(app: FastAPI) -> None:
    """Register :class:`CORSMiddleware` on *app*.

    Call once during application factory (``create_app``), before any
    route-level middleware is added, so pre-flight ``OPTIONS`` requests are
    resolved at the CORS layer before auth or rate-limiting is consulted.
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_get_allowed_origins(),
        allow_credentials=True,
        allow_methods=_ALLOWED_METHODS,
        allow_headers=_ALLOWED_HEADERS,
    )


__all__ = ["setup_cors"]

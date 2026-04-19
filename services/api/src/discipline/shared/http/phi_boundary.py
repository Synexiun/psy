"""PHI boundary marker + middleware (CLAUDE.md Rule #11).

Every response that carries PHI must include ``X-Phi-Boundary: 1`` so the
log correlator can cross-reference the audit stream with the app stream,
and downstream CSP / egress enforcers can refuse to cache / relay the
response.

Design:

- :func:`mark_phi_boundary` is a FastAPI dependency that attaches a flag
  to the request state.  Endpoints that touch PHI opt in by declaring
  ``dependencies=[Depends(mark_phi_boundary)]`` on their route.  The
  dependency exists purely for its side effect; its return value is
  ignored.

- :class:`PhiBoundaryMiddleware` reads the flag after the endpoint has
  produced a response and appends the header.  The middleware has no
  knowledge of which routes are PHI — it trusts the per-route opt-in.
  This keeps the policy co-located with the route (so a reader can grep
  for PHI surfaces by searching for ``mark_phi_boundary``) while keeping
  the header-setting centralized so an endpoint can't forget.

Why not tag-based detection (``tags=["phi"]``):
- Tags are documentation, not semantics.  They don't flow into request
  state; the middleware would need to walk FastAPI's route table to map
  URL → tag on every request.
- A route can be re-tagged by a cosmetic edit, silently dropping the
  header.  Explicit dependency makes the PHI opt-in impossible to remove
  without a code change a human will notice.

Why middleware + dependency instead of inline header-setting:
- An endpoint that forgets to set the header silently violates Rule #11.
  With the dependency + middleware split, forgetting the dependency makes
  it obvious in review ("why isn't this PHI route marked?"), and
  forgetting the header is no longer possible — the middleware always
  appends it when the flag is set.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from starlette.types import ASGIApp

PHI_BOUNDARY_HEADER: str = "X-Phi-Boundary"
PHI_BOUNDARY_VALUE: str = "1"
_STATE_FLAG: str = "is_phi_boundary"


def mark_phi_boundary(request: Request) -> None:
    """FastAPI dependency that marks a request as PHI-touching.

    Apply via::

        from fastapi import APIRouter, Depends
        from discipline.shared.http import mark_phi_boundary

        router = APIRouter()

        @router.get("/patient/{id}", dependencies=[Depends(mark_phi_boundary)])
        async def read_patient(id: str) -> PatientOut: ...

    The dependency has no return value of interest — it only sets the
    request-state flag that :class:`PhiBoundaryMiddleware` reads on the
    way out.
    """
    request.state.is_phi_boundary = True


class PhiBoundaryMiddleware(BaseHTTPMiddleware):
    """Append ``X-Phi-Boundary: 1`` to responses from PHI-marked routes.

    The middleware is a thin wrapper around :class:`BaseHTTPMiddleware`.
    Register it via ``app.add_middleware(PhiBoundaryMiddleware)`` once in
    :func:`discipline.app.create_app`.
    """

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        response = await call_next(request)
        if getattr(request.state, _STATE_FLAG, False):
            response.headers[PHI_BOUNDARY_HEADER] = PHI_BOUNDARY_VALUE
        return response


__all__ = [
    "PHI_BOUNDARY_HEADER",
    "PHI_BOUNDARY_VALUE",
    "PhiBoundaryMiddleware",
    "mark_phi_boundary",
]

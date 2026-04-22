"""PHI boundary middleware tests (CLAUDE.md Rule #11).

Contract the middleware enforces:
- Routes that declare ``Depends(mark_phi_boundary)`` respond with
  ``X-Phi-Boundary: 1``.
- Routes that do NOT declare it receive no such header.
- The flag is per-request; one request's marking must not leak to
  another request.
- Error responses (HTTPException) from a PHI route still carry the
  header — a clinician hitting a 422 on a PHI route still had their
  request enter the boundary.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

import pytest
from fastapi import Depends, FastAPI, HTTPException
from fastapi.testclient import TestClient

from discipline.shared.http import PhiBoundaryMiddleware, mark_phi_boundary
from discipline.shared.http.phi_boundary import (
    PHI_BOUNDARY_HEADER,
    PHI_BOUNDARY_VALUE,
)

# ---- Fixtures --------------------------------------------------------------


def _app_with_routes() -> FastAPI:
    """Build a tiny app exercising both marked and unmarked routes."""
    app = FastAPI()
    app.add_middleware(PhiBoundaryMiddleware)

    @app.get("/public")
    async def public() -> dict[str, str]:
        return {"hello": "world"}

    @app.get("/phi", dependencies=[Depends(mark_phi_boundary)])
    async def phi() -> dict[str, str]:
        return {"patient_id": "xyz"}

    @app.get("/phi-error", dependencies=[Depends(mark_phi_boundary)])
    async def phi_error() -> dict[str, str]:
        raise HTTPException(status_code=422, detail="nope")

    @app.get("/phi-500", dependencies=[Depends(mark_phi_boundary)])
    async def phi_500() -> dict[str, str]:
        raise HTTPException(status_code=500, detail="boom")

    return app


@pytest.fixture
def client() -> TestClient:
    return TestClient(_app_with_routes())


# =============================================================================
# Header presence / absence
# =============================================================================


class TestHeaderPresence:
    def test_unmarked_route_omits_header(self, client: TestClient) -> None:
        resp = client.get("/public")
        assert resp.status_code == 200
        assert PHI_BOUNDARY_HEADER not in resp.headers

    def test_marked_route_sets_header(self, client: TestClient) -> None:
        resp = client.get("/phi")
        assert resp.status_code == 200
        assert resp.headers.get(PHI_BOUNDARY_HEADER) == PHI_BOUNDARY_VALUE

    def test_header_value_is_exactly_one(self, client: TestClient) -> None:
        """Pinned: the value is the string ``1``.  If we ever change it to
        ``"yes"`` or ``"true"``, downstream CSP / log-correlator code that
        compares the header value will silently stop recognizing PHI
        responses."""
        resp = client.get("/phi")
        assert resp.headers[PHI_BOUNDARY_HEADER] == "1"

    def test_marked_route_with_422_still_sets_header(
        self, client: TestClient
    ) -> None:
        """A clinician hitting a validation error on a PHI route still had
        their request enter the boundary.  The audit trail must reflect
        that; the header makes it visible to the log correlator even on
        error responses."""
        resp = client.get("/phi-error")
        assert resp.status_code == 422
        assert resp.headers.get(PHI_BOUNDARY_HEADER) == PHI_BOUNDARY_VALUE

    def test_marked_route_with_500_still_sets_header(
        self, client: TestClient
    ) -> None:
        resp = client.get("/phi-500")
        assert resp.status_code == 500
        assert resp.headers.get(PHI_BOUNDARY_HEADER) == PHI_BOUNDARY_VALUE


# =============================================================================
# Per-request isolation
# =============================================================================


class TestPerRequestIsolation:
    def test_marking_does_not_leak_between_requests(
        self, client: TestClient
    ) -> None:
        """A marked request must NOT cause a subsequent unmarked request
        to also get the header — the flag is per-request, not per-app."""
        marked_resp = client.get("/phi")
        assert marked_resp.headers.get(PHI_BOUNDARY_HEADER) == PHI_BOUNDARY_VALUE

        unmarked_resp = client.get("/public")
        assert PHI_BOUNDARY_HEADER not in unmarked_resp.headers

    def test_many_alternating_requests(self, client: TestClient) -> None:
        """Stress-test the per-request boundary over a series of rapid
        alternating calls."""
        for _ in range(5):
            assert (
                client.get("/phi").headers.get(PHI_BOUNDARY_HEADER)
                == PHI_BOUNDARY_VALUE
            )
            assert PHI_BOUNDARY_HEADER not in client.get("/public").headers


# =============================================================================
# Integration with the real clinician endpoint
# =============================================================================


class TestLiveClinicianBundleRoute:
    """Regression guard: the production clinician-bundle endpoint must
    still carry the header after the refactor to dependency-based opt-in.
    This test exists separately from the unit test above to catch
    accidental removal of the ``Depends(mark_phi_boundary)`` line."""

    def test_clinician_bundle_response_has_phi_header(self) -> None:
        from discipline.app import create_app

        app = create_app()
        client = TestClient(app)
        resp = client.post(
            "/v1/reports/fhir/clinician-bundle",
            json={
                "clinician_id": "clin-001",
                "patient_id": "pt-001",
                "observations": [
                    {
                        "patient_reference": "Patient/test-001",
                        "instrument": "phq9",
                        "score": 5,
                        "effective": "2026-04-18T12:00:00+00:00",
                    }
                ],
                "bundle_type": "collection",
            },
        )
        assert resp.status_code == 200
        assert resp.headers.get(PHI_BOUNDARY_HEADER) == PHI_BOUNDARY_VALUE

    @patch("discipline.app.get_redis_client")
    @patch("discipline.app._get_engine")
    def test_health_endpoint_does_not_have_phi_header(
        self,
        mock_get_engine: Any,
        mock_get_redis: Any,
    ) -> None:
        """Regression guard in the other direction: a non-PHI route must
        not get the header, or the boundary marker loses its meaning."""
        from unittest.mock import AsyncMock, MagicMock

        from discipline.app import create_app

        mock_get_redis.return_value = MagicMock()
        mock_conn = AsyncMock()
        # scalar() is synchronous on SQLAlchemy Result; use a plain Mock for it
        mock_result = MagicMock()
        mock_result.scalar.return_value = 1
        mock_conn.execute.return_value = mock_result
        mock_engine = MagicMock()
        mock_engine.connect.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_engine.connect.return_value.__aexit__ = AsyncMock(return_value=False)
        mock_get_engine.return_value = mock_engine

        app = create_app()
        client = TestClient(app)
        resp = client.get("/health")
        assert resp.status_code == 200
        assert PHI_BOUNDARY_HEADER not in resp.headers

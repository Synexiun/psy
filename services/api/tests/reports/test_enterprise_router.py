"""Enterprise engagement endpoint tests.

This route is the wire-facing application of the k-anonymity primitive
from ``discipline.reports.enterprise``.  The primitive's semantics are
unit-tested separately in ``test_enterprise.py``; this file covers the
HTTP surface — the wire contract, suppression visibility, and the
absence of PHI-surface markers (aggregate data only per CLAUDE.md).

Why a separate file:
- ``test_enterprise.py`` is pure-Python unit coverage of the primitive.
- This file is integration — it goes through FastAPI + Pydantic +
  PhiBoundaryMiddleware to verify the end-to-end contract.  The
  duplication is intentional; a primitive test passing while the HTTP
  surface regresses is exactly the failure mode we want to catch.
"""

from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient

from discipline.app import create_app
from discipline.reports.enterprise import K_ANONYMITY_THRESHOLD
from discipline.shared.http.phi_boundary import PHI_BOUNDARY_HEADER

# ---- Fixtures --------------------------------------------------------------


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


def _snapshot_payload(
    *,
    org_id: str = "org-acme",
    active: int = 25,
    tools: int = 60,
    wellbeing: float = 68.0,
    n_active: int = 20,
    n_wellbeing: int = 18,
) -> dict[str, Any]:
    """Default payload represents a healthy, k-sufficient org.

    Individual tests override specific fields to exercise edge cases
    (sub-k cohorts, zeros, negative inputs, etc.)."""
    return {
        "org_id": org_id,
        "active_members_count_7d": active,
        "tools_used_count_7d": tools,
        "wellbeing_index_mean": wellbeing,
        "n_active_members_7d": n_active,
        "n_wellbeing_reporters": n_wellbeing,
    }


# =============================================================================
# Happy path — k-sufficient cohort renders all fields
# =============================================================================


class TestHappyPath:
    def test_k_sufficient_returns_all_fields(self, client: TestClient) -> None:
        """With n_active = 20 and n_wellbeing = 18 (both >> 5), every
        cell renders with its raw value intact."""
        resp = client.post(
            "/v1/reports/enterprise/engagement",
            json=_snapshot_payload(),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["org_id"] == "org-acme"
        assert body["active_members_7d"] == 25
        assert body["tools_used_7d"] == 60
        assert body["wellbeing_index"] == 68.0

    def test_threshold_reported_in_response(self, client: TestClient) -> None:
        """Clients need to know the threshold to render suppressed cells
        with the correct legend ('< 5 users' vs just 'insufficient data').
        Exposing it in the response avoids a separate discovery call."""
        resp = client.post(
            "/v1/reports/enterprise/engagement", json=_snapshot_payload()
        )
        assert resp.status_code == 200
        assert resp.json()["k_anonymity_threshold"] == K_ANONYMITY_THRESHOLD
        assert resp.json()["k_anonymity_threshold"] == 5

    def test_exactly_at_threshold_renders(self, client: TestClient) -> None:
        """n == k is not suppressed — the gate is ``>=``, not ``>``."""
        resp = client.post(
            "/v1/reports/enterprise/engagement",
            json=_snapshot_payload(
                n_active=K_ANONYMITY_THRESHOLD, n_wellbeing=K_ANONYMITY_THRESHOLD
            ),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["active_members_7d"] is not None
        assert body["wellbeing_index"] is not None


# =============================================================================
# Suppression — sub-k cohorts render as JSON null
# =============================================================================


class TestSuppression:
    def test_small_org_suppresses_all_fields(self, client: TestClient) -> None:
        """A 3-member org: everything under k, everything None.  JSON
        serializes Python None as ``null`` — dashboards render that as
        'insufficient data'."""
        resp = client.post(
            "/v1/reports/enterprise/engagement",
            json=_snapshot_payload(n_active=3, n_wellbeing=3),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["active_members_7d"] is None
        assert body["tools_used_7d"] is None
        assert body["wellbeing_index"] is None
        # org_id is metadata, not a suppressible cell — it must remain.
        assert body["org_id"] == "org-acme"

    def test_partial_suppression_wellbeing_only(self, client: TestClient) -> None:
        """20 active members but only 3 filled out WHO-5 this window —
        activity cells render, wellbeing suppressed.  This is the most
        common real-world mixed state."""
        resp = client.post(
            "/v1/reports/enterprise/engagement",
            json=_snapshot_payload(n_active=20, n_wellbeing=3),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["active_members_7d"] == 25
        assert body["tools_used_7d"] == 60
        assert body["wellbeing_index"] is None

    def test_zero_values_at_sufficient_cohort_preserved(
        self, client: TestClient
    ) -> None:
        """A legitimate zero (100-person org, nobody used any tool this
        week) must render as ``0``, not ``null``.  The distinction is
        load-bearing: zero-is-information, null-is-suppression."""
        resp = client.post(
            "/v1/reports/enterprise/engagement",
            json=_snapshot_payload(
                active=0,
                tools=0,
                wellbeing=0.0,
                n_active=100,
                n_wellbeing=100,
            ),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["active_members_7d"] == 0
        assert body["tools_used_7d"] == 0
        assert body["wellbeing_index"] == 0.0


# =============================================================================
# Non-PHI surface — no X-Phi-Boundary header, no audit emission
# =============================================================================


class TestNotPhiSurface:
    def test_response_does_not_carry_phi_boundary_header(
        self, client: TestClient
    ) -> None:
        """Rule #11 applies to PHI routes.  This route renders k-anonymous
        aggregates, not identifiable PHI — the header being absent is the
        signal to downstream correlators that this response is safe to
        ship to enterprise admins."""
        resp = client.post(
            "/v1/reports/enterprise/engagement", json=_snapshot_payload()
        )
        assert resp.status_code == 200
        assert PHI_BOUNDARY_HEADER not in resp.headers

    def test_suppression_response_still_not_phi(self, client: TestClient) -> None:
        """Even when all cells are suppressed, the route isn't PHI — a
        suppression is the absence of data, which is itself non-PHI."""
        resp = client.post(
            "/v1/reports/enterprise/engagement",
            json=_snapshot_payload(n_active=2, n_wellbeing=2),
        )
        assert resp.status_code == 200
        assert PHI_BOUNDARY_HEADER not in resp.headers


# =============================================================================
# Validation — negative inputs, missing fields, wrong types
# =============================================================================


class TestValidation:
    def test_missing_org_id_rejected(self, client: TestClient) -> None:
        payload = _snapshot_payload()
        del payload["org_id"]
        resp = client.post("/v1/reports/enterprise/engagement", json=payload)
        assert resp.status_code == 422

    def test_empty_org_id_rejected(self, client: TestClient) -> None:
        """org_id with zero length fails Pydantic ``min_length=1`` — an
        empty string here would make the aggregate meaningless (which
        org?) and possibly leak across tenants if a downstream cache
        keys on it."""
        resp = client.post(
            "/v1/reports/enterprise/engagement",
            json=_snapshot_payload(org_id=""),
        )
        assert resp.status_code == 422

    def test_negative_active_count_rejected(self, client: TestClient) -> None:
        resp = client.post(
            "/v1/reports/enterprise/engagement",
            json=_snapshot_payload(active=-1),
        )
        assert resp.status_code == 422

    def test_negative_cohort_size_rejected(self, client: TestClient) -> None:
        """n < 0 is caught at Pydantic ``ge=0`` before the primitive ever
        sees it — the primitive would raise ``InvalidCohortSizeError``
        which would become a 500; catching it at the wire layer as 422
        is a cleaner error surface."""
        resp = client.post(
            "/v1/reports/enterprise/engagement",
            json=_snapshot_payload(n_active=-1),
        )
        assert resp.status_code == 422

    def test_wellbeing_above_scale_max_rejected(self, client: TestClient) -> None:
        """WHO-5 percentage is bounded [0, 100].  A value of 150 is a
        caller bug — probably a raw score passed in instead of the
        WHO-5 Index (the ``* 4`` conversion was skipped, or applied
        twice).  Either way, reject at the wire."""
        resp = client.post(
            "/v1/reports/enterprise/engagement",
            json=_snapshot_payload(wellbeing=150.0),
        )
        assert resp.status_code == 422

    def test_missing_cohort_field_rejected(self, client: TestClient) -> None:
        """n_wellbeing_reporters is required — a snapshot without it
        cannot be suppressed correctly."""
        payload = _snapshot_payload()
        del payload["n_wellbeing_reporters"]
        resp = client.post("/v1/reports/enterprise/engagement", json=payload)
        assert resp.status_code == 422


# =============================================================================
# Method contract — POST only (snapshot is a body, not a resource URL)
# =============================================================================


class TestMethodContract:
    def test_get_not_allowed(self, client: TestClient) -> None:
        """GET on this path returns 405 — the snapshot payload has six
        numeric fields which fit poorly in a querystring, and the semantic
        is 'submit a snapshot for rendering', not 'read a resource'."""
        resp = client.get("/v1/reports/enterprise/engagement")
        assert resp.status_code == 405

    def test_content_type_is_json(self, client: TestClient) -> None:
        resp = client.post(
            "/v1/reports/enterprise/engagement", json=_snapshot_payload()
        )
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("application/json")

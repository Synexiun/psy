"""``POST /v1/assessments/trajectory`` endpoint tests.

The trajectory endpoint surfaces the reliable-change-index (RCI)
computation per Jacobson & Truax 1991.  These tests pin:
- Per-instrument RCI thresholds from
  ``Docs/Whitepapers/02_Clinical_Evidence_Base.md``.
- Boundary cases at the threshold (at-cutoff is improvement, not
  no_reliable_change — the threshold is the lower bound of 'reliable').
- Direction inversion for WHO-5 (the only higher-is-better
  instrument).
- Graceful handling of unknown instruments and missing baselines
  (HTTP 200 + ``insufficient_data``, not 422).
- The thresholds table endpoint returns the canonical dict used by
  the computation — single source of truth.
"""

from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient

from discipline.app import create_app
from discipline.psychometric.trajectories import RCI_THRESHOLDS


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


def _post_trajectory(
    client: TestClient,
    *,
    instrument: str,
    current: float,
    baseline: float | None = None,
) -> Any:
    body: dict[str, Any] = {"instrument": instrument, "current": current}
    if baseline is not None:
        body["baseline"] = baseline
    return client.post("/v1/assessments/trajectory", json=body)


# =============================================================================
# Lower-is-better instruments — improvement direction is delta < 0
# =============================================================================


class TestPhq9Trajectory:
    """PHQ-9 RCI threshold = 5.2 (Kroenke 2001 / Whitepapers 02)."""

    def test_improvement_below_baseline(self, client: TestClient) -> None:
        """Total dropped from 18 to 12 (delta -6, |Δ|=6 ≥ 5.2) →
        improvement.  This is the canonical 'patient is getting
        better' rendering."""
        resp = _post_trajectory(client, instrument="phq9", current=12, baseline=18)
        assert resp.status_code == 200
        body = resp.json()
        assert body["instrument"] == "phq9"
        assert body["delta"] == -6
        assert body["rci_threshold"] == 5.2
        assert body["direction"] == "improvement"

    def test_deterioration_above_baseline(self, client: TestClient) -> None:
        """Total climbed from 12 to 18 (delta +6) → deterioration."""
        resp = _post_trajectory(client, instrument="phq9", current=18, baseline=12)
        body = resp.json()
        assert body["delta"] == 6
        assert body["direction"] == "deterioration"

    def test_no_reliable_change_just_below_threshold(
        self, client: TestClient
    ) -> None:
        """|Δ|=5 < 5.2 → no_reliable_change.  This is the noise band
        where day-to-day variability dominates true change."""
        resp = _post_trajectory(client, instrument="phq9", current=13, baseline=18)
        body = resp.json()
        assert abs(body["delta"]) == 5
        assert body["direction"] == "no_reliable_change"

    def test_at_threshold_is_improvement(self, client: TestClient) -> None:
        """|Δ|=5.2 exactly → improvement.  The threshold is the
        inclusive lower bound of 'reliable' per Jacobson & Truax;
        a strict ``>`` here would push at-cutoff cases to
        no_reliable_change, which understates real treatment effects."""
        resp = _post_trajectory(client, instrument="phq9", current=12.8, baseline=18)
        body = resp.json()
        assert body["delta"] == pytest.approx(-5.2)
        assert body["direction"] == "improvement"


class TestGad7Trajectory:
    """GAD-7 RCI threshold = 4.6 (Spitzer 2006 / Whitepapers 02)."""

    def test_improvement(self, client: TestClient) -> None:
        resp = _post_trajectory(client, instrument="gad7", current=8, baseline=14)
        body = resp.json()
        assert body["delta"] == -6
        assert body["rci_threshold"] == 4.6
        assert body["direction"] == "improvement"

    def test_just_below_threshold_no_change(self, client: TestClient) -> None:
        """|Δ|=4.5 < 4.6 → no_reliable_change."""
        resp = _post_trajectory(client, instrument="gad7", current=9.5, baseline=14)
        body = resp.json()
        assert body["delta"] == pytest.approx(-4.5)
        assert body["direction"] == "no_reliable_change"


class TestPss10Trajectory:
    """PSS-10 RCI threshold = 7.8."""

    def test_improvement(self, client: TestClient) -> None:
        resp = _post_trajectory(client, instrument="pss10", current=14, baseline=24)
        body = resp.json()
        assert body["delta"] == -10
        assert body["rci_threshold"] == 7.8
        assert body["direction"] == "improvement"

    def test_deterioration(self, client: TestClient) -> None:
        resp = _post_trajectory(client, instrument="pss10", current=24, baseline=14)
        body = resp.json()
        assert body["delta"] == 10
        assert body["direction"] == "deterioration"


class TestAuditCTrajectory:
    """AUDIT-C RCI threshold = 2."""

    def test_improvement_at_threshold(self, client: TestClient) -> None:
        """|Δ|=2 (exactly threshold) → improvement.  AUDIT-C has the
        smallest absolute threshold (2 points on a 12-point scale),
        which makes the at-threshold case especially important to
        pin."""
        resp = _post_trajectory(client, instrument="audit_c", current=4, baseline=6)
        body = resp.json()
        assert body["delta"] == -2
        assert body["direction"] == "improvement"

    def test_deterioration_at_threshold(self, client: TestClient) -> None:
        resp = _post_trajectory(client, instrument="audit_c", current=6, baseline=4)
        body = resp.json()
        assert body["delta"] == 2
        assert body["direction"] == "deterioration"


# =============================================================================
# Higher-is-better instrument — direction inverts for WHO-5
# =============================================================================


class TestWho5Trajectory:
    """WHO-5 RCI threshold = 17.  Unique among the supported set in
    that HIGHER is better — the direction logic must invert here."""

    def test_improvement_with_positive_delta(self, client: TestClient) -> None:
        """Index rose from 40 to 60 (delta +20) → improvement.
        Same numeric delta on PHQ-9 would be deterioration.  Direction
        renderers must use the ``direction`` string, not the ``delta``
        sign."""
        resp = _post_trajectory(client, instrument="who5", current=60, baseline=40)
        body = resp.json()
        assert body["delta"] == 20
        assert body["rci_threshold"] == 17.0
        assert body["direction"] == "improvement"

    def test_deterioration_with_negative_delta(self, client: TestClient) -> None:
        """Index fell from 60 to 40 (delta -20) → deterioration."""
        resp = _post_trajectory(client, instrument="who5", current=40, baseline=60)
        body = resp.json()
        assert body["delta"] == -20
        assert body["direction"] == "deterioration"

    def test_at_threshold_is_improvement(self, client: TestClient) -> None:
        """|Δ|=17 exactly with positive sign → improvement (WHO-5)."""
        resp = _post_trajectory(client, instrument="who5", current=57, baseline=40)
        body = resp.json()
        assert body["delta"] == 17
        assert body["direction"] == "improvement"

    def test_just_below_threshold_no_change(self, client: TestClient) -> None:
        resp = _post_trajectory(client, instrument="who5", current=56, baseline=40)
        body = resp.json()
        assert body["delta"] == 16
        assert body["direction"] == "no_reliable_change"


# =============================================================================
# Insufficient data — graceful failure modes
# =============================================================================


class TestInsufficientData:
    def test_missing_baseline_returns_insufficient_data(
        self, client: TestClient
    ) -> None:
        """No baseline supplied → ``insufficient_data`` with HTTP 200.
        This is a SUCCESSFUL query — the renderer needs to know the
        threshold (to display 'collect another reading') but cannot
        compute a delta yet."""
        resp = _post_trajectory(client, instrument="phq9", current=12)
        assert resp.status_code == 200
        body = resp.json()
        assert body["baseline"] is None
        assert body["delta"] is None
        assert body["direction"] == "insufficient_data"
        assert body["rci_threshold"] == 5.2  # threshold still echoed

    def test_explicit_null_baseline_returns_insufficient_data(
        self, client: TestClient
    ) -> None:
        """An explicit JSON ``null`` for baseline behaves like an
        omitted field."""
        resp = client.post(
            "/v1/assessments/trajectory",
            json={"instrument": "phq9", "current": 12, "baseline": None},
        )
        body = resp.json()
        assert body["direction"] == "insufficient_data"

    def test_unknown_instrument_returns_insufficient_data(
        self, client: TestClient
    ) -> None:
        """An instrument we have no validated RCI threshold for →
        ``insufficient_data``.  HTTP 200, NOT 422.  This is the
        graceful-degradation contract: a renderer that asks about
        'beck_depression' (which we don't yet have) gets a typed
        'we don't compute that' response, not a hard error."""
        resp = _post_trajectory(
            client, instrument="beck_depression", current=12, baseline=18
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["direction"] == "insufficient_data"
        assert body["rci_threshold"] is None
        assert body["delta"] is None  # no comparison possible without threshold

    def test_unknown_instrument_with_no_baseline(
        self, client: TestClient
    ) -> None:
        """Both unknown instrument AND no baseline → still 200,
        insufficient_data.  Compound failure modes don't 422."""
        resp = _post_trajectory(client, instrument="totally_made_up", current=10)
        assert resp.status_code == 200
        assert resp.json()["direction"] == "insufficient_data"


# =============================================================================
# Instrument-name normalization
# =============================================================================


class TestNormalization:
    def test_uppercase_instrument_normalized(self, client: TestClient) -> None:
        """The endpoint lowercases the instrument so callers don't
        have to know the canonical casing.  'PHQ9' should resolve
        the same as 'phq9'."""
        resp = _post_trajectory(client, instrument="PHQ9", current=12, baseline=18)
        body = resp.json()
        assert body["instrument"] == "phq9"
        assert body["direction"] == "improvement"

    def test_whitespace_stripped(self, client: TestClient) -> None:
        """Leading/trailing whitespace stripped — defensive against
        sloppy callers."""
        resp = _post_trajectory(client, instrument="  phq9  ", current=12, baseline=18)
        body = resp.json()
        assert body["instrument"] == "phq9"
        assert body["direction"] == "improvement"


# =============================================================================
# Thresholds endpoint
# =============================================================================


class TestThresholdsEndpoint:
    def test_returns_full_threshold_table(self, client: TestClient) -> None:
        """``GET /v1/assessments/trajectory/thresholds`` returns every
        instrument's |Δ| threshold.  Useful for UI tooltips."""
        resp = client.get("/v1/assessments/trajectory/thresholds")
        assert resp.status_code == 200
        body = resp.json()
        assert body == {
            "phq9": 5.2,
            "gad7": 4.6,
            "who5": 17.0,
            "pss10": 7.8,
            "audit_c": 2.0,
        }

    def test_thresholds_match_computation_source(
        self, client: TestClient
    ) -> None:
        """The exposed thresholds are exactly what the computation
        endpoint uses — pinning that the API and library share one
        source of truth.  A future refactor that introduced a parallel
        copy would be caught here."""
        resp = client.get("/v1/assessments/trajectory/thresholds")
        assert resp.json() == dict(RCI_THRESHOLDS)


# =============================================================================
# Response shape
# =============================================================================


class TestResponseShape:
    def test_required_fields_always_present(self, client: TestClient) -> None:
        """Every trajectory response carries the same six keys.  A
        renderer can rely on every field always being present (even
        if some are ``null``)."""
        resp = _post_trajectory(client, instrument="phq9", current=12, baseline=18)
        body = resp.json()
        required = {
            "instrument",
            "current",
            "baseline",
            "delta",
            "rci_threshold",
            "direction",
        }
        assert set(body.keys()) == required

    def test_required_fields_present_on_insufficient_data(
        self, client: TestClient
    ) -> None:
        """Even on the insufficient_data path, all keys are present
        (some null).  This keeps client rendering branchless."""
        resp = _post_trajectory(client, instrument="phq9", current=12)
        body = resp.json()
        required = {
            "instrument",
            "current",
            "baseline",
            "delta",
            "rci_threshold",
            "direction",
        }
        assert set(body.keys()) == required

    def test_current_echoed_verbatim(self, client: TestClient) -> None:
        resp = _post_trajectory(client, instrument="phq9", current=12.5, baseline=18)
        assert resp.json()["current"] == 12.5

    def test_baseline_echoed_verbatim(self, client: TestClient) -> None:
        resp = _post_trajectory(client, instrument="phq9", current=12, baseline=18.5)
        assert resp.json()["baseline"] == 18.5


# =============================================================================
# Validation — fields the route DOES enforce
# =============================================================================


class TestValidation:
    def test_missing_current_422(self, client: TestClient) -> None:
        """``current`` is required — Pydantic rejects without it."""
        resp = client.post(
            "/v1/assessments/trajectory",
            json={"instrument": "phq9"},
        )
        assert resp.status_code == 422

    def test_missing_instrument_422(self, client: TestClient) -> None:
        resp = client.post(
            "/v1/assessments/trajectory",
            json={"current": 12},
        )
        assert resp.status_code == 422

    def test_non_numeric_current_422(self, client: TestClient) -> None:
        resp = client.post(
            "/v1/assessments/trajectory",
            json={"instrument": "phq9", "current": "not-a-number"},
        )
        assert resp.status_code == 422

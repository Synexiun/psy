"""Analytics HTTP router integration tests.

These go through the full FastAPI stack (request validation, response
serialization) to ensure the pure service layer is correctly wired.  The
composition rules themselves are exhaustively tested in
``test_framing_rules.py`` and ``test_weekly_reflection.py``; these tests
cover the HTTP-specific concerns: status codes, response shape, query
validation, and the safety-routed=200 contract.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from discipline.app import create_app


def _client() -> TestClient:
    return TestClient(create_app())


# =============================================================================
# POST /v1/insights/weekly/compose
# =============================================================================


class TestWeeklyCompose:
    _URL = "/v1/insights/weekly/compose"

    def _valid_payload(self, **overrides: object) -> dict[str, object]:
        base: dict[str, object] = {
            "user_id": "user_001",
            "week_ending": "2026-04-18",
            "phq9_current": 8,
            "phq9_baseline": 14,
            "gad7_current": 6,
            "gad7_baseline": 9,
            "who5_current": 60.0,
            "who5_baseline": 40.0,
            "resilience_days": 42,
            "days_clean": 14,
            "n_checkins_7d": 5,
            "safety_positive_this_week": False,
        }
        base.update(overrides)
        return base

    def test_happy_path_returns_200(self) -> None:
        response = _client().post(self._URL, json=self._valid_payload())
        assert response.status_code == 200

    def test_happy_path_has_every_framed_field(self) -> None:
        body = _client().post(self._URL, json=self._valid_payload()).json()
        assert body["safety_routed"] is False
        assert body["severity_phq9"]["display"] == "mild"
        assert body["trend_phq9"]["direction_label"] == "softer"
        assert body["resilience"]["display"].startswith("42 urges handled")

    def test_safety_positive_returns_200_with_flag(self) -> None:
        """Safety-positive is a domain signal, NOT a validation error.  The
        client inspects safety_routed and renders T3 handoff instead of the
        reflection.  HTTP 200 is the right status."""
        response = _client().post(
            self._URL,
            json=self._valid_payload(safety_positive_this_week=True),
        )
        assert response.status_code == 200
        body = response.json()
        assert body["safety_routed"] is True
        assert body["severity_phq9"] is None
        assert body["trend_phq9"] is None
        assert body["resilience"] is None

    def test_missing_phq9_current_omits_phq9_fields(self) -> None:
        body = (
            _client()
            .post(self._URL, json=self._valid_payload(phq9_current=None))
            .json()
        )
        assert body["severity_phq9"] is None
        assert body["trend_phq9"] is None
        assert body["severity_gad7"] is not None

    def test_phq9_current_out_of_range_rejected(self) -> None:
        """pydantic validation rejects scores outside the PHQ-9 range."""
        response = _client().post(
            self._URL,
            json=self._valid_payload(phq9_current=28),
        )
        assert response.status_code == 422

    def test_sparse_week_suppresses_all_trends(self) -> None:
        body = (
            _client()
            .post(self._URL, json=self._valid_payload(n_checkins_7d=1))
            .json()
        )
        for trend_key in ("trend_phq9", "trend_gad7", "trend_who5"):
            assert body[trend_key]["suppressed_reason"] == "insufficient_data"
        # But snapshot severity and resilience are preserved
        assert body["severity_phq9"] is not None
        assert body["resilience"] is not None


# =============================================================================
# GET /v1/insights/trajectory
# =============================================================================


class TestTrajectoryEndpoint:
    _URL = "/v1/insights/trajectory"

    def test_phq9_improvement_frames_as_softer(self) -> None:
        response = _client().get(
            self._URL,
            params={"instrument": "phq9", "current": 3, "baseline": 12},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["direction_label"] == "softer"

    def test_missing_baseline_returns_insufficient_data(self) -> None:
        response = _client().get(
            self._URL, params={"instrument": "phq9", "current": 5}
        )
        body = response.json()
        assert body["suppressed_reason"] == "insufficient_data"
        assert body["direction_label"] is None

    def test_sparse_checkins_suppress_direction(self) -> None:
        response = _client().get(
            self._URL,
            params={
                "instrument": "phq9",
                "current": 3,
                "baseline": 12,
                "n_checkins_7d": 1,
            },
        )
        body = response.json()
        assert body["suppressed_reason"] == "insufficient_data"

    def test_unknown_instrument_returns_422(self) -> None:
        response = _client().get(
            self._URL,
            params={"instrument": "madeup", "current": 5, "baseline": 3},
        )
        assert response.status_code == 422
        assert response.json()["detail"]["code"] == "validation.unknown_instrument"

    def test_missing_required_query_param_returns_422(self) -> None:
        """``instrument`` is required."""
        response = _client().get(self._URL, params={"current": 5})
        assert response.status_code == 422

    def test_negative_current_rejected(self) -> None:
        response = _client().get(
            self._URL, params={"instrument": "phq9", "current": -1}
        )
        assert response.status_code == 422

    def test_response_includes_narrative(self) -> None:
        body = (
            _client()
            .get(
                self._URL,
                params={"instrument": "phq9", "current": 3, "baseline": 12},
            )
            .json()
        )
        # Narrative text contains the approved lexicon
        assert "softer" in body["narrative"]


# =============================================================================
# GET /v1/insights/resilience
# =============================================================================


class TestResilienceEndpoint:
    _URL = "/v1/insights/resilience"

    def test_happy_path(self) -> None:
        response = _client().get(
            self._URL, params={"resilience_days": 10, "days_clean": 3}
        )
        assert response.status_code == 200
        body = response.json()
        assert body["resilience_days"] == 10
        assert body["days_clean"] == 3
        assert "10" in body["display"]
        assert "3 days clean" in body["display"]

    def test_both_fields_required(self) -> None:
        """P2: resilience never appears without days-clean.  The endpoint
        refuses to accept only one of the two."""
        missing_days_clean = _client().get(
            self._URL, params={"resilience_days": 10}
        )
        assert missing_days_clean.status_code == 422

        missing_resilience = _client().get(
            self._URL, params={"days_clean": 3}
        )
        assert missing_resilience.status_code == 422

    def test_negative_values_rejected(self) -> None:
        response = _client().get(
            self._URL, params={"resilience_days": -1, "days_clean": 0}
        )
        assert response.status_code == 422

    def test_zero_days_clean_still_returns_200(self) -> None:
        """First day / post-reset — still a valid response with tone=neutral."""
        body = (
            _client()
            .get(self._URL, params={"resilience_days": 5, "days_clean": 0})
            .json()
        )
        assert body["tone"] == "neutral"
        assert "0 days clean" in body["display"]


# =============================================================================
# Stubs remain stubs
# =============================================================================


class TestStubEndpoints:
    """GET /weekly and /patterns are pending repository wiring.  They return
    the documented stub shape so CI catches accidental endpoint removal."""

    def test_get_weekly_is_stub(self) -> None:
        body = _client().get("/v1/insights/weekly").json()
        assert body == {"status": "not_implemented"}

    def test_get_patterns_is_stub(self) -> None:
        body = _client().get("/v1/insights/patterns").json()
        assert body == {"status": "not_implemented"}

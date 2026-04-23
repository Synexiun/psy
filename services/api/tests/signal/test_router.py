"""Signal router tests.

Covers signal window ingest, deduplication, state estimate lifecycle,
and device capabilities.
"""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from discipline.app import create_app
from discipline.signal.repository import reset_signal_repositories


@pytest.fixture(autouse=True)
def _clear_signal() -> None:
    reset_signal_repositories()


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


_USER_HEADER = {"X-User-Id": "user_sig_001"}
_USER_HEADER_B = {"X-User-Id": "user_sig_002"}


# =============================================================================
# Signal window ingest
# =============================================================================


class TestSignalWindowIngest:
    def test_ingest_returns_201(self, client: TestClient) -> None:
        response = client.post(
            "/v1/signals/windows",
            json={
                "window_start": "2026-04-22T10:00:00Z",
                "window_end": "2026-04-22T10:05:00Z",
                "source": "healthkit",
                "samples": [{"timestamp": "2026-04-22T10:00:00Z", "value": 72.0, "unit": "bpm"}],
            },
            headers=_USER_HEADER,
        )
        assert response.status_code == 201

    def test_ingest_response_has_window_id(self, client: TestClient) -> None:
        body = client.post(
            "/v1/signals/windows",
            json={
                "window_start": "2026-04-22T10:00:00Z",
                "window_end": "2026-04-22T10:05:00Z",
                "source": "healthkit",
                "samples": [],
            },
            headers=_USER_HEADER,
        ).json()
        assert "window_id" in body
        uuid.UUID(body["window_id"])

    def test_ingest_preserves_window_times(self, client: TestClient) -> None:
        body = client.post(
            "/v1/signals/windows",
            json={
                "window_start": "2026-04-22T10:00:00Z",
                "window_end": "2026-04-22T10:05:00Z",
                "source": "watch",
                "samples": [],
            },
            headers=_USER_HEADER,
        ).json()
        assert body["window_start"] == "2026-04-22T10:00:00Z"
        assert body["window_end"] == "2026-04-22T10:05:00Z"

    def test_ingest_invalid_source_returns_422(self, client: TestClient) -> None:
        response = client.post(
            "/v1/signals/windows",
            json={
                "window_start": "2026-04-22T10:00:00Z",
                "window_end": "2026-04-22T10:05:00Z",
                "source": "unknown_source",
                "samples": [],
            },
            headers=_USER_HEADER,
        )
        assert response.status_code == 422

    def test_ingest_deduplicates_identical_samples(self, client: TestClient) -> None:
        payload = {
            "window_start": "2026-04-22T10:00:00Z",
            "window_end": "2026-04-22T10:05:00Z",
            "source": "healthkit",
            "samples": [{"timestamp": "2026-04-22T10:00:00Z", "value": 72.0}],
        }
        r1 = client.post("/v1/signals/windows", json=payload, headers=_USER_HEADER).json()
        r2 = client.post("/v1/signals/windows", json=payload, headers=_USER_HEADER).json()
        assert r1["window_id"] == r2["window_id"]

    def test_ingest_different_samples_different_window(self, client: TestClient) -> None:
        payload1 = {
            "window_start": "2026-04-22T10:00:00Z",
            "window_end": "2026-04-22T10:05:00Z",
            "source": "healthkit",
            "samples": [{"timestamp": "2026-04-22T10:00:00Z", "value": 72.0}],
        }
        payload2 = {
            "window_start": "2026-04-22T10:00:00Z",
            "window_end": "2026-04-22T10:05:00Z",
            "source": "healthkit",
            "samples": [{"timestamp": "2026-04-22T10:00:00Z", "value": 75.0}],
        }
        r1 = client.post("/v1/signals/windows", json=payload1, headers=_USER_HEADER).json()
        r2 = client.post("/v1/signals/windows", json=payload2, headers=_USER_HEADER).json()
        assert r1["window_id"] != r2["window_id"]

    def test_ingest_missing_window_start_returns_422(self, client: TestClient) -> None:
        response = client.post(
            "/v1/signals/windows",
            json={"window_end": "2026-04-22T10:05:00Z", "source": "healthkit", "samples": []},
            headers=_USER_HEADER,
        )
        assert response.status_code == 422

    def test_ingest_missing_window_end_returns_422(self, client: TestClient) -> None:
        response = client.post(
            "/v1/signals/windows",
            json={"window_start": "2026-04-22T10:00:00Z", "source": "healthkit", "samples": []},
            headers=_USER_HEADER,
        )
        assert response.status_code == 422

    def test_ingest_all_valid_sources_accepted(self, client: TestClient) -> None:
        for source in ("healthkit", "health_connect", "manual_checkin", "watch"):
            response = client.post(
                "/v1/signals/windows",
                json={
                    "window_start": "2026-04-22T10:00:00Z",
                    "window_end": "2026-04-22T10:05:00Z",
                    "source": source,
                    "samples": [],
                },
                headers=_USER_HEADER,
            )
            assert response.status_code == 201, f"source={source} should be accepted"


# =============================================================================
# State estimate creation
# =============================================================================


class TestStateEstimateCreate:
    def test_create_returns_201(self, client: TestClient) -> None:
        response = client.post(
            "/v1/signals/state",
            json={
                "state_label": "rising_urge",
                "confidence": 0.85,
                "model_version": "state-v1.2.0",
                "inferred_at": "2026-04-22T10:00:00Z",
            },
            headers=_USER_HEADER,
        )
        assert response.status_code == 201

    def test_create_response_has_estimate_id(self, client: TestClient) -> None:
        body = client.post(
            "/v1/signals/state",
            json={
                "state_label": "stable",
                "confidence": 0.92,
                "model_version": "state-v1.2.0",
                "inferred_at": "2026-04-22T10:00:00Z",
            },
            headers=_USER_HEADER,
        ).json()
        assert "estimate_id" in body
        uuid.UUID(body["estimate_id"])

    def test_create_invalid_state_label_returns_422(self, client: TestClient) -> None:
        response = client.post(
            "/v1/signals/state",
            json={
                "state_label": "unknown",
                "confidence": 0.5,
                "model_version": "v1",
                "inferred_at": "2026-04-22T10:00:00Z",
            },
            headers=_USER_HEADER,
        )
        assert response.status_code == 422

    def test_create_confidence_below_range_returns_422(self, client: TestClient) -> None:
        response = client.post(
            "/v1/signals/state",
            json={
                "state_label": "stable",
                "confidence": -0.1,
                "model_version": "v1",
                "inferred_at": "2026-04-22T10:00:00Z",
            },
            headers=_USER_HEADER,
        )
        assert response.status_code == 422

    def test_create_confidence_above_range_returns_422(self, client: TestClient) -> None:
        response = client.post(
            "/v1/signals/state",
            json={
                "state_label": "stable",
                "confidence": 1.1,
                "model_version": "v1",
                "inferred_at": "2026-04-22T10:00:00Z",
            },
            headers=_USER_HEADER,
        )
        assert response.status_code == 422

    def test_create_boundary_confidence_accepted(self, client: TestClient) -> None:
        for confidence in (0.0, 1.0):
            response = client.post(
                "/v1/signals/state",
                json={
                    "state_label": "baseline",
                    "confidence": confidence,
                    "model_version": "v1",
                    "inferred_at": "2026-04-22T10:00:00Z",
                },
                headers=_USER_HEADER,
            )
            assert response.status_code == 201, f"confidence={confidence} should be accepted"

    def test_create_all_valid_state_labels_accepted(self, client: TestClient) -> None:
        for label in ("stable", "rising_urge", "peak_urge", "post_urge", "baseline"):
            response = client.post(
                "/v1/signals/state",
                json={
                    "state_label": label,
                    "confidence": 0.75,
                    "model_version": "v1",
                    "inferred_at": "2026-04-22T10:00:00Z",
                },
                headers={"X-User-Id": f"user_{label}"},
            )
            assert response.status_code == 201, f"state_label={label} should be accepted"


# =============================================================================
# State estimate retrieval
# =============================================================================


class TestStateEstimateGet:
    def test_get_latest_returns_200(self, client: TestClient) -> None:
        client.post(
            "/v1/signals/state",
            json={
                "state_label": "rising_urge",
                "confidence": 0.85,
                "model_version": "v1",
                "inferred_at": "2026-04-22T10:00:00Z",
            },
            headers=_USER_HEADER,
        )
        response = client.get("/v1/signals/state", headers=_USER_HEADER)
        assert response.status_code == 200

    def test_get_latest_returns_most_recent(self, client: TestClient) -> None:
        client.post(
            "/v1/signals/state",
            json={
                "state_label": "stable",
                "confidence": 0.5,
                "model_version": "v1",
                "inferred_at": "2026-04-22T09:00:00Z",
            },
            headers=_USER_HEADER,
        )
        client.post(
            "/v1/signals/state",
            json={
                "state_label": "peak_urge",
                "confidence": 0.9,
                "model_version": "v1",
                "inferred_at": "2026-04-22T10:00:00Z",
            },
            headers=_USER_HEADER,
        )
        body = client.get("/v1/signals/state", headers=_USER_HEADER).json()
        assert body["state_label"] == "peak_urge"
        assert body["confidence"] == 0.9

    def test_get_not_found_returns_404(self, client: TestClient) -> None:
        response = client.get("/v1/signals/state", headers=_USER_HEADER)
        assert response.status_code == 404
        assert response.json()["detail"] == "state_estimate.not_found"

    def test_get_user_isolation(self, client: TestClient) -> None:
        client.post(
            "/v1/signals/state",
            json={
                "state_label": "stable",
                "confidence": 0.8,
                "model_version": "v1",
                "inferred_at": "2026-04-22T10:00:00Z",
            },
            headers=_USER_HEADER,
        )
        response = client.get("/v1/signals/state", headers=_USER_HEADER_B)
        assert response.status_code == 404


# =============================================================================
# Device capabilities
# =============================================================================


class TestDeviceCapabilities:
    def test_get_returns_200(self, client: TestClient) -> None:
        response = client.get("/v1/signals/device-capabilities", headers=_USER_HEADER)
        assert response.status_code == 200

    def test_get_returns_all_capabilities_true(self, client: TestClient) -> None:
        body = client.get("/v1/signals/device-capabilities", headers=_USER_HEADER).json()
        assert body["heart_rate"] is True
        assert body["hrv"] is True
        assert body["accelerometer"] is True
        assert body["sleep"] is True
        assert body["audio_journal"] is True

    def test_get_shape_is_stable(self, client: TestClient) -> None:
        body = client.get("/v1/signals/device-capabilities", headers=_USER_HEADER).json()
        assert set(body.keys()) == {
            "heart_rate",
            "hrv",
            "accelerometer",
            "sleep",
            "audio_journal",
        }

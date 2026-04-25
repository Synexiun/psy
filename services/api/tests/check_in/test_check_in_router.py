"""Check-in router tests.

Covers:
- POST /v1/check-in returns 201 with session_id and received_at
- GET /v1/check-in/history returns 200 with items list
- After POST, GET /v1/check-in/history returns the submitted check-in
- limit parameter works correctly
- User isolation (user A's history not visible to user B)
- Signal processing pipeline: SignalWindowRepository + StateEstimateRepository wired
- Intensity → state label mapping (deterministic, no LLM)
- Safety stream event emitted for intensity >= 8
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from discipline.app import create_app
from discipline.check_in.router import _intensity_to_state, reset_check_in_store
from discipline.shared.middleware.rate_limit import limiter
from discipline.signal.repository import reset_signal_repositories


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture(autouse=True)
def _clear_store() -> None:
    """Reset all in-memory stores and rate limiter before every test."""
    reset_check_in_store()
    reset_signal_repositories()
    limiter._storage.reset()


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


_USER_A = {"X-User-Id": "user_test_001"}
_USER_B = {"X-User-Id": "user_test_002"}

_URL_CHECKIN = "/v1/check-in"
_URL_HISTORY = "/v1/check-in/history"


def _valid_check_in(**overrides):
    base = {
        "intensity": 5,
        "trigger_tags": ["stress", "boredom"],
    }
    base.update(overrides)
    return base


# =============================================================================
# POST /v1/check-in
# =============================================================================


class TestSubmitCheckIn:
    def test_returns_201(self, client: TestClient) -> None:
        response = client.post(_URL_CHECKIN, json=_valid_check_in(), headers=_USER_A)
        assert response.status_code == 201

    def test_response_has_session_id(self, client: TestClient) -> None:
        response = client.post(_URL_CHECKIN, json=_valid_check_in(), headers=_USER_A)
        body = response.json()
        assert "session_id" in body
        assert isinstance(body["session_id"], str)
        assert len(body["session_id"]) > 0

    def test_response_has_received_at(self, client: TestClient) -> None:
        response = client.post(_URL_CHECKIN, json=_valid_check_in(), headers=_USER_A)
        body = response.json()
        assert "received_at" in body
        assert isinstance(body["received_at"], str)
        # Should be a parseable ISO-8601 timestamp
        from datetime import datetime
        datetime.fromisoformat(body["received_at"])

    def test_response_has_state_updated(self, client: TestClient) -> None:
        response = client.post(_URL_CHECKIN, json=_valid_check_in(), headers=_USER_A)
        body = response.json()
        assert body["state_updated"] is True

    def test_intensity_boundary_zero(self, client: TestClient) -> None:
        response = client.post(
            _URL_CHECKIN, json=_valid_check_in(intensity=0), headers=_USER_A
        )
        assert response.status_code == 201

    def test_intensity_boundary_ten(self, client: TestClient) -> None:
        response = client.post(
            _URL_CHECKIN, json=_valid_check_in(intensity=10), headers=_USER_A
        )
        assert response.status_code == 201

    def test_intensity_above_max_rejected(self, client: TestClient) -> None:
        response = client.post(
            _URL_CHECKIN, json=_valid_check_in(intensity=11), headers=_USER_A
        )
        assert response.status_code == 422

    def test_intensity_below_min_rejected(self, client: TestClient) -> None:
        response = client.post(
            _URL_CHECKIN, json=_valid_check_in(intensity=-1), headers=_USER_A
        )
        assert response.status_code == 422

    def test_empty_trigger_tags_accepted(self, client: TestClient) -> None:
        response = client.post(
            _URL_CHECKIN, json=_valid_check_in(trigger_tags=[]), headers=_USER_A
        )
        assert response.status_code == 201

    def test_optional_notes_accepted(self, client: TestClient) -> None:
        response = client.post(
            _URL_CHECKIN,
            json=_valid_check_in(notes="Feeling overwhelmed"),
            headers=_USER_A,
        )
        assert response.status_code == 201

    def test_notes_over_max_length_rejected(self, client: TestClient) -> None:
        long_note = "x" * 281
        response = client.post(
            _URL_CHECKIN, json=_valid_check_in(notes=long_note), headers=_USER_A
        )
        assert response.status_code == 422

    def test_custom_checked_in_at_accepted(self, client: TestClient) -> None:
        response = client.post(
            _URL_CHECKIN,
            json=_valid_check_in(checked_in_at="2026-04-20T14:30:00Z"),
            headers=_USER_A,
        )
        assert response.status_code == 201

    def test_each_submission_has_unique_session_id(self, client: TestClient) -> None:
        r1 = client.post(_URL_CHECKIN, json=_valid_check_in(), headers=_USER_A)
        r2 = client.post(_URL_CHECKIN, json=_valid_check_in(), headers=_USER_A)
        assert r1.json()["session_id"] != r2.json()["session_id"]


# =============================================================================
# GET /v1/check-in/history
# =============================================================================


class TestGetCheckInHistory:
    def test_returns_200(self, client: TestClient) -> None:
        response = client.get(_URL_HISTORY, headers=_USER_A)
        assert response.status_code == 200

    def test_empty_history_returns_empty_items(self, client: TestClient) -> None:
        response = client.get(_URL_HISTORY, headers=_USER_A)
        body = response.json()
        assert body["items"] == []
        assert body["total"] == 0

    def test_response_shape(self, client: TestClient) -> None:
        response = client.get(_URL_HISTORY, headers=_USER_A)
        body = response.json()
        assert "items" in body
        assert "total" in body
        assert isinstance(body["items"], list)
        assert isinstance(body["total"], int)


# =============================================================================
# POST then GET — round-trip
# =============================================================================


class TestCheckInRoundTrip:
    def test_post_then_history_contains_checkin(self, client: TestClient) -> None:
        post_resp = client.post(_URL_CHECKIN, json=_valid_check_in(), headers=_USER_A)
        assert post_resp.status_code == 201
        session_id = post_resp.json()["session_id"]

        hist_resp = client.get(_URL_HISTORY, headers=_USER_A)
        assert hist_resp.status_code == 200
        body = hist_resp.json()
        assert body["total"] == 1
        assert len(body["items"]) == 1

        item = body["items"][0]
        assert item["session_id"] == session_id
        assert item["intensity"] == 5
        assert item["trigger_tags"] == ["stress", "boredom"]

    def test_history_item_has_checked_in_at(self, client: TestClient) -> None:
        ts = "2026-04-20T14:30:00+00:00"
        client.post(
            _URL_CHECKIN,
            json=_valid_check_in(checked_in_at=ts),
            headers=_USER_A,
        )
        body = client.get(_URL_HISTORY, headers=_USER_A).json()
        assert body["items"][0]["checked_in_at"] == ts

    def test_multiple_posts_all_appear_in_history(self, client: TestClient) -> None:
        for intensity in [2, 5, 8]:
            client.post(
                _URL_CHECKIN, json=_valid_check_in(intensity=intensity), headers=_USER_A
            )

        body = client.get(_URL_HISTORY, headers=_USER_A).json()
        assert body["total"] == 3
        assert len(body["items"]) == 3

    def test_history_is_newest_first(self, client: TestClient) -> None:
        for intensity in [1, 2, 3]:
            client.post(
                _URL_CHECKIN, json=_valid_check_in(intensity=intensity), headers=_USER_A
            )

        body = client.get(_URL_HISTORY, headers=_USER_A).json()
        intensities = [item["intensity"] for item in body["items"]]
        assert intensities == [3, 2, 1]


# =============================================================================
# limit parameter
# =============================================================================


class TestCheckInHistoryLimit:
    def test_limit_default_is_20(self, client: TestClient) -> None:
        for i in range(25):
            client.post(
                _URL_CHECKIN, json=_valid_check_in(intensity=i % 11), headers=_USER_A
            )

        body = client.get(_URL_HISTORY, headers=_USER_A).json()
        assert body["total"] == 25
        assert len(body["items"]) == 20

    def test_limit_parameter_respected(self, client: TestClient) -> None:
        for i in range(10):
            client.post(
                _URL_CHECKIN, json=_valid_check_in(intensity=i % 11), headers=_USER_A
            )

        body = client.get(_URL_HISTORY + "?limit=3", headers=_USER_A).json()
        assert body["total"] == 10
        assert len(body["items"]) == 3

    def test_limit_returns_most_recent(self, client: TestClient) -> None:
        for intensity in [1, 2, 3, 4, 5]:
            client.post(
                _URL_CHECKIN, json=_valid_check_in(intensity=intensity), headers=_USER_A
            )

        body = client.get(_URL_HISTORY + "?limit=2", headers=_USER_A).json()
        intensities = [item["intensity"] for item in body["items"]]
        assert intensities == [5, 4]

    def test_limit_1_accepted(self, client: TestClient) -> None:
        client.post(_URL_CHECKIN, json=_valid_check_in(), headers=_USER_A)
        body = client.get(_URL_HISTORY + "?limit=1", headers=_USER_A).json()
        assert len(body["items"]) == 1

    def test_limit_100_accepted(self, client: TestClient) -> None:
        response = client.get(_URL_HISTORY + "?limit=100", headers=_USER_A)
        assert response.status_code == 200

    def test_limit_0_rejected(self, client: TestClient) -> None:
        response = client.get(_URL_HISTORY + "?limit=0", headers=_USER_A)
        assert response.status_code == 422

    def test_limit_101_rejected(self, client: TestClient) -> None:
        response = client.get(_URL_HISTORY + "?limit=101", headers=_USER_A)
        assert response.status_code == 422

    def test_limit_less_than_total_returns_correct_count(self, client: TestClient) -> None:
        for i in range(5):
            client.post(
                _URL_CHECKIN, json=_valid_check_in(intensity=i % 11), headers=_USER_A
            )

        body = client.get(_URL_HISTORY + "?limit=3", headers=_USER_A).json()
        assert len(body["items"]) == 3

    def test_limit_greater_than_total_returns_all(self, client: TestClient) -> None:
        for i in range(3):
            client.post(
                _URL_CHECKIN, json=_valid_check_in(intensity=i % 11), headers=_USER_A
            )

        body = client.get(_URL_HISTORY + "?limit=50", headers=_USER_A).json()
        assert len(body["items"]) == 3


# =============================================================================
# User isolation
# =============================================================================


class TestUserIsolation:
    def test_user_a_history_not_visible_to_user_b(self, client: TestClient) -> None:
        client.post(_URL_CHECKIN, json=_valid_check_in(intensity=7), headers=_USER_A)

        body_b = client.get(_URL_HISTORY, headers=_USER_B).json()
        assert body_b["total"] == 0
        assert body_b["items"] == []

    def test_user_b_history_not_visible_to_user_a(self, client: TestClient) -> None:
        client.post(_URL_CHECKIN, json=_valid_check_in(intensity=3), headers=_USER_B)

        body_a = client.get(_URL_HISTORY, headers=_USER_A).json()
        assert body_a["total"] == 0
        assert body_a["items"] == []

    def test_both_users_see_only_their_own_data(self, client: TestClient) -> None:
        client.post(_URL_CHECKIN, json=_valid_check_in(intensity=2), headers=_USER_A)
        client.post(_URL_CHECKIN, json=_valid_check_in(intensity=9), headers=_USER_B)
        client.post(_URL_CHECKIN, json=_valid_check_in(intensity=4), headers=_USER_A)

        body_a = client.get(_URL_HISTORY, headers=_USER_A).json()
        body_b = client.get(_URL_HISTORY, headers=_USER_B).json()

        assert body_a["total"] == 2
        assert body_b["total"] == 1

        intensities_a = {item["intensity"] for item in body_a["items"]}
        intensities_b = {item["intensity"] for item in body_b["items"]}

        assert 9 not in intensities_a
        assert 2 not in intensities_b
        assert 4 not in intensities_b

    def test_default_user_id_isolated_from_explicit_user(self, client: TestClient) -> None:
        """Requests without X-User-Id default to test_user_001; must not bleed into named users."""
        client.post(_URL_CHECKIN, json=_valid_check_in())  # no header → test_user_001

        body = client.get(_URL_HISTORY, headers=_USER_A).json()
        # _USER_A is "user_test_001", distinct from the default "test_user_001"
        assert body["total"] == 0


# =============================================================================
# Intensity → state label mapping (deterministic — no LLM, Rule 1)
# =============================================================================


class TestIntensityToState:
    def test_zero_is_stable(self) -> None:
        assert _intensity_to_state(0) == "stable"

    def test_three_is_stable(self) -> None:
        assert _intensity_to_state(3) == "stable"

    def test_four_is_rising_urge(self) -> None:
        assert _intensity_to_state(4) == "rising_urge"

    def test_six_is_rising_urge(self) -> None:
        assert _intensity_to_state(6) == "rising_urge"

    def test_seven_is_peak_urge(self) -> None:
        assert _intensity_to_state(7) == "peak_urge"

    def test_eight_is_peak_urge(self) -> None:
        assert _intensity_to_state(8) == "peak_urge"

    def test_ten_is_peak_urge(self) -> None:
        assert _intensity_to_state(10) == "peak_urge"

    def test_boundary_three_to_four(self) -> None:
        """3 → stable, 4 → rising_urge — boundary must be sharp."""
        assert _intensity_to_state(3) != _intensity_to_state(4)

    def test_boundary_six_to_seven(self) -> None:
        """6 → rising_urge, 7 → peak_urge — boundary must be sharp."""
        assert _intensity_to_state(6) != _intensity_to_state(7)


# =============================================================================
# Signal processing pipeline — SignalWindowRepository + StateEstimateRepository
# =============================================================================


class TestSignalPipeline:
    def test_check_in_writes_signal_window(self, client: TestClient) -> None:
        """After a check-in, a SignalWindowRecord must exist in the repository."""
        from discipline.signal.repository import get_signal_window_repository

        client.post(_URL_CHECKIN, json=_valid_check_in(intensity=5), headers=_USER_A)

        # The in-memory repo should have received exactly one window.
        repo = get_signal_window_repository()
        # Access private state for assertion — acceptable for unit tests.
        assert len(repo._windows) == 1

    def test_check_in_writes_state_estimate(self, client: TestClient) -> None:
        """After a check-in, a StateEstimateRecord must exist in the repository."""
        from discipline.signal.repository import get_state_estimate_repository

        client.post(_URL_CHECKIN, json=_valid_check_in(intensity=5), headers=_USER_A)

        repo = get_state_estimate_repository()
        assert len(repo._estimates) == 1

    def test_state_estimate_label_matches_intensity(self, client: TestClient) -> None:
        """The persisted state label must match the deterministic intensity band."""
        from discipline.signal.repository import get_state_estimate_repository

        client.post(_URL_CHECKIN, json=_valid_check_in(intensity=2), headers=_USER_A)

        repo = get_state_estimate_repository()
        record = next(iter(repo._estimates.values()))
        assert record.state_label == "stable"

    def test_rising_urge_label_stored(self, client: TestClient) -> None:
        from discipline.signal.repository import get_state_estimate_repository

        client.post(_URL_CHECKIN, json=_valid_check_in(intensity=5), headers=_USER_A)

        repo = get_state_estimate_repository()
        record = next(iter(repo._estimates.values()))
        assert record.state_label == "rising_urge"

    def test_peak_urge_label_stored(self, client: TestClient) -> None:
        from discipline.signal.repository import get_state_estimate_repository

        client.post(_URL_CHECKIN, json=_valid_check_in(intensity=9), headers=_USER_A)

        repo = get_state_estimate_repository()
        record = next(iter(repo._estimates.values()))
        assert record.state_label == "peak_urge"

    def test_signal_window_source_is_manual_checkin(self, client: TestClient) -> None:
        from discipline.signal.repository import get_signal_window_repository

        client.post(_URL_CHECKIN, json=_valid_check_in(intensity=4), headers=_USER_A)

        repo = get_signal_window_repository()
        record = next(iter(repo._windows.values()))
        assert record.source == "manual_checkin"

    def test_state_estimate_model_version(self, client: TestClient) -> None:
        from discipline.signal.repository import get_state_estimate_repository

        client.post(_URL_CHECKIN, json=_valid_check_in(intensity=7), headers=_USER_A)

        repo = get_state_estimate_repository()
        record = next(iter(repo._estimates.values()))
        assert record.model_version == "check-in-intensity-v1"

    def test_state_updated_true_when_pipeline_succeeds(self, client: TestClient) -> None:
        body = client.post(
            _URL_CHECKIN, json=_valid_check_in(intensity=6), headers=_USER_A
        ).json()
        assert body["state_updated"] is True

    def test_two_check_ins_create_two_windows(self, client: TestClient) -> None:
        from discipline.signal.repository import get_signal_window_repository

        client.post(_URL_CHECKIN, json=_valid_check_in(intensity=3), headers=_USER_A)
        client.post(_URL_CHECKIN, json=_valid_check_in(intensity=7), headers=_USER_A)

        repo = get_signal_window_repository()
        assert len(repo._windows) == 2

    def test_signal_window_user_id_matches_header(self, client: TestClient) -> None:
        from discipline.signal.repository import get_signal_window_repository

        client.post(_URL_CHECKIN, json=_valid_check_in(intensity=5), headers=_USER_A)

        repo = get_signal_window_repository()
        record = next(iter(repo._windows.values()))
        assert record.user_id == "user_test_001"

    def test_pipeline_error_does_not_break_response(self, client: TestClient) -> None:
        """If the signal repo raises, the endpoint still returns 201 (graceful degradation)."""
        with patch(
            "discipline.check_in.router.get_signal_window_repository"
        ) as mock_repo_factory:
            mock_repo = MagicMock()
            mock_repo.create.side_effect = RuntimeError("db unavailable")
            mock_repo_factory.return_value = mock_repo

            response = client.post(
                _URL_CHECKIN, json=_valid_check_in(intensity=5), headers=_USER_A
            )

        assert response.status_code == 201
        assert response.json()["state_updated"] is False


# =============================================================================
# Safety stream events — high intensity
# =============================================================================


class TestSafetyStreamEvents:
    def test_intensity_8_emits_safety_event(self, client: TestClient) -> None:
        """Intensity >= 8 must emit a safety-stream warning event."""
        with patch(
            "discipline.check_in.router.get_stream_logger"
        ) as mock_get_logger:
            mock_safety_logger = MagicMock()
            mock_get_logger.return_value = mock_safety_logger

            client.post(_URL_CHECKIN, json=_valid_check_in(intensity=8), headers=_USER_A)

            mock_get_logger.assert_called_once()
            mock_safety_logger.warning.assert_called_once()

    def test_safety_event_name_is_check_in_high_intensity(self, client: TestClient) -> None:
        with patch(
            "discipline.check_in.router.get_stream_logger"
        ) as mock_get_logger:
            mock_safety_logger = MagicMock()
            mock_get_logger.return_value = mock_safety_logger

            client.post(_URL_CHECKIN, json=_valid_check_in(intensity=9), headers=_USER_A)

            call_args = mock_safety_logger.warning.call_args
            event_name = call_args.args[0] if call_args.args else call_args[0][0]
            assert event_name == "check_in.high_intensity"

    def test_safety_event_includes_intensity(self, client: TestClient) -> None:
        with patch(
            "discipline.check_in.router.get_stream_logger"
        ) as mock_get_logger:
            mock_safety_logger = MagicMock()
            mock_get_logger.return_value = mock_safety_logger

            client.post(_URL_CHECKIN, json=_valid_check_in(intensity=10), headers=_USER_A)

            call_kwargs = mock_safety_logger.warning.call_args.kwargs
            assert call_kwargs.get("intensity") == 10

    def test_intensity_7_does_not_emit_safety_event(self, client: TestClient) -> None:
        """Intensity 7 is peak_urge but below the safety-stream threshold of 8."""
        with patch(
            "discipline.check_in.router.get_stream_logger"
        ) as mock_get_logger:
            mock_safety_logger = MagicMock()
            mock_get_logger.return_value = mock_safety_logger

            client.post(_URL_CHECKIN, json=_valid_check_in(intensity=7), headers=_USER_A)

            mock_get_logger.assert_not_called()

    def test_intensity_0_does_not_emit_safety_event(self, client: TestClient) -> None:
        with patch(
            "discipline.check_in.router.get_stream_logger"
        ) as mock_get_logger:
            mock_safety_logger = MagicMock()
            mock_get_logger.return_value = mock_safety_logger

            client.post(_URL_CHECKIN, json=_valid_check_in(intensity=0), headers=_USER_A)

            mock_get_logger.assert_not_called()

    def test_safety_event_uses_safety_stream(self, client: TestClient) -> None:
        """get_stream_logger must be called with LogStream.SAFETY (not AUDIT or APP)."""
        from discipline.shared.logging import LogStream

        with patch(
            "discipline.check_in.router.get_stream_logger"
        ) as mock_get_logger:
            mock_get_logger.return_value = MagicMock()
            client.post(_URL_CHECKIN, json=_valid_check_in(intensity=8), headers=_USER_A)
            mock_get_logger.assert_called_once_with(LogStream.SAFETY)

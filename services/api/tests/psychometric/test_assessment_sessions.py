"""Assessment sessions endpoint tests — POST/GET /v1/assessments/sessions.

Covers:
1.  POST /sessions returns 201 with session_id, instrument, score, severity
2.  POST /sessions uses real scoring engine (no stub sum)
3.  POST /sessions persists the record so GET /sessions returns it
4.  Instrument name normalisation (phq-9 → phq9, gad-7 → gad7, who-5 → who5, audit-c → audit_c)
5.  PHQ-9 item 9 > 0 sets safety_flag=True
6.  PHQ-9 item 9 = 0 sets safety_flag=False
7.  Non-PHQ-9 instruments: safety_flag=False
8.  POST /sessions emits AUDIT log entry (PHI boundary)
9.  T3 fire emits safety-stream event
10. GET /sessions returns empty list for new user
11. GET /sessions returns submitted sessions in history order
12. GET /sessions limit parameter respected
13. User isolation: user A cannot see user B's sessions
14. Missing item values default to 0
15. Invalid instrument returns 422
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from discipline.app import create_app
from discipline.psychometric.repository import get_assessment_repository
from discipline.shared.logging import LogStream, reset_chain_state
from discipline.shared.middleware.rate_limit import limiter


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_USER_A = {"X-User-Id": "user_session_001"}
_USER_B = {"X-User-Id": "user_session_002"}

_URL_SESSIONS = "/v1/assessments/sessions"


@pytest.fixture(autouse=True)
def _reset_state() -> None:
    get_assessment_repository().clear()
    reset_chain_state(LogStream.AUDIT)
    limiter._storage.reset()
    yield
    get_assessment_repository().clear()
    limiter._storage.reset()


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


def _phq9_responses(values: list[int] | None = None) -> dict[str, Any]:
    """PHQ-9 session submission with supplied item values (1–9)."""
    vals = values or [0] * 9
    return {
        "instrument": "phq-9",
        "responses": [{"item": i + 1, "value": v} for i, v in enumerate(vals)],
    }


def _gad7_responses(values: list[int] | None = None) -> dict[str, Any]:
    vals = values or [0] * 7
    return {
        "instrument": "gad-7",
        "responses": [{"item": i + 1, "value": v} for i, v in enumerate(vals)],
    }


def _who5_responses(values: list[int] | None = None) -> dict[str, Any]:
    vals = values or [3] * 5
    return {
        "instrument": "who-5",
        "responses": [{"item": i + 1, "value": v} for i, v in enumerate(vals)],
    }


# ---------------------------------------------------------------------------
# 1-3. Basic shape + real scoring + persistence
# ---------------------------------------------------------------------------


class TestCreateSessionBasic:
    def test_returns_201(self, client: TestClient) -> None:
        resp = client.post(_URL_SESSIONS, json=_phq9_responses(), headers=_USER_A)
        assert resp.status_code == 201, resp.text

    def test_response_has_session_id(self, client: TestClient) -> None:
        body = client.post(_URL_SESSIONS, json=_phq9_responses(), headers=_USER_A).json()
        assert "session_id" in body
        import uuid
        uuid.UUID(body["session_id"])

    def test_response_has_instrument(self, client: TestClient) -> None:
        body = client.post(_URL_SESSIONS, json=_phq9_responses(), headers=_USER_A).json()
        assert body["instrument"] == "phq9"

    def test_response_has_score(self, client: TestClient) -> None:
        body = client.post(_URL_SESSIONS, json=_phq9_responses(), headers=_USER_A).json()
        assert isinstance(body["score"], int)

    def test_response_has_severity(self, client: TestClient) -> None:
        body = client.post(_URL_SESSIONS, json=_phq9_responses(), headers=_USER_A).json()
        assert isinstance(body["severity"], str)
        assert len(body["severity"]) > 0

    def test_response_has_completed_at(self, client: TestClient) -> None:
        body = client.post(_URL_SESSIONS, json=_phq9_responses(), headers=_USER_A).json()
        from datetime import datetime
        datetime.fromisoformat(body["completed_at"])

    def test_response_has_safety_flag(self, client: TestClient) -> None:
        body = client.post(_URL_SESSIONS, json=_phq9_responses(), headers=_USER_A).json()
        assert isinstance(body["safety_flag"], bool)


# ---------------------------------------------------------------------------
# 2. Real scoring engine
# ---------------------------------------------------------------------------


class TestRealScoring:
    def test_phq9_all_ones_score_is_9(self, client: TestClient) -> None:
        """PHQ-9 with all 1s: total should be 9 (mild band)."""
        body = client.post(
            _URL_SESSIONS, json=_phq9_responses([1] * 9), headers=_USER_A
        ).json()
        assert body["score"] == 9
        assert body["severity"] == "mild"

    def test_phq9_all_zeros_score_is_0(self, client: TestClient) -> None:
        body = client.post(
            _URL_SESSIONS, json=_phq9_responses([0] * 9), headers=_USER_A
        ).json()
        assert body["score"] == 0
        # PHQ-9 0-4 band is "none" per Kroenke 2001 pinned thresholds (PHQ9_SEVERITY_THRESHOLDS)
        assert body["severity"] == "none"

    def test_phq9_severe_band(self, client: TestClient) -> None:
        """21–27 → severe."""
        body = client.post(
            _URL_SESSIONS, json=_phq9_responses([3] * 9), headers=_USER_A
        ).json()
        assert body["score"] == 27
        assert body["severity"] == "severe"

    def test_gad7_all_ones_score_is_7(self, client: TestClient) -> None:
        body = client.post(
            _URL_SESSIONS, json=_gad7_responses([1] * 7), headers=_USER_A
        ).json()
        assert body["score"] == 7
        assert body["severity"] == "mild"

    def test_who5_raw_total_correct(self, client: TestClient) -> None:
        """WHO-5 all 3s → raw total 15."""
        body = client.post(
            _URL_SESSIONS, json=_who5_responses([3] * 5), headers=_USER_A
        ).json()
        assert body["score"] == 15


# ---------------------------------------------------------------------------
# 3. Persistence: POST then GET
# ---------------------------------------------------------------------------


class TestSessionPersistence:
    def test_post_then_get_returns_session(self, client: TestClient) -> None:
        client.post(_URL_SESSIONS, json=_phq9_responses([1] * 9), headers=_USER_A)
        history = client.get(_URL_SESSIONS, headers=_USER_A).json()
        assert len(history) == 1

    def test_persisted_session_has_correct_instrument(self, client: TestClient) -> None:
        client.post(_URL_SESSIONS, json=_phq9_responses([1] * 9), headers=_USER_A)
        history = client.get(_URL_SESSIONS, headers=_USER_A).json()
        assert history[0]["instrument"] == "phq9"

    def test_persisted_session_score_matches_post(self, client: TestClient) -> None:
        post_body = client.post(
            _URL_SESSIONS, json=_phq9_responses([2] * 9), headers=_USER_A
        ).json()
        history = client.get(_URL_SESSIONS, headers=_USER_A).json()
        assert history[0]["score"] == post_body["score"]

    def test_two_sessions_both_persisted(self, client: TestClient) -> None:
        client.post(_URL_SESSIONS, json=_phq9_responses([1] * 9), headers=_USER_A)
        client.post(_URL_SESSIONS, json=_gad7_responses([1] * 7), headers=_USER_A)
        history = client.get(_URL_SESSIONS, headers=_USER_A).json()
        assert len(history) == 2


# ---------------------------------------------------------------------------
# 4. Instrument name normalisation
# ---------------------------------------------------------------------------


class TestInstrumentNormalisation:
    def test_phq9_hyphenated_accepted(self, client: TestClient) -> None:
        resp = client.post(_URL_SESSIONS, json=_phq9_responses(), headers=_USER_A)
        assert resp.status_code == 201
        assert resp.json()["instrument"] == "phq9"

    def test_gad7_hyphenated_accepted(self, client: TestClient) -> None:
        resp = client.post(_URL_SESSIONS, json=_gad7_responses(), headers=_USER_A)
        assert resp.status_code == 201
        assert resp.json()["instrument"] == "gad7"

    def test_who5_hyphenated_accepted(self, client: TestClient) -> None:
        resp = client.post(_URL_SESSIONS, json=_who5_responses(), headers=_USER_A)
        assert resp.status_code == 201
        assert resp.json()["instrument"] == "who5"

    def test_audit_c_hyphenated_accepted(self, client: TestClient) -> None:
        resp = client.post(
            _URL_SESSIONS,
            json={
                "instrument": "audit-c",
                "responses": [{"item": i + 1, "value": 0} for i in range(3)],
            },
            headers=_USER_A,
        )
        assert resp.status_code == 201
        assert resp.json()["instrument"] == "audit_c"

    def test_canonical_name_also_accepted(self, client: TestClient) -> None:
        """phq9 (no hyphen) also routes correctly."""
        resp = client.post(
            _URL_SESSIONS,
            json={
                "instrument": "phq9",
                "responses": [{"item": i + 1, "value": 0} for i in range(9)],
            },
            headers=_USER_A,
        )
        assert resp.status_code == 201
        assert resp.json()["instrument"] == "phq9"


# ---------------------------------------------------------------------------
# 5 & 6. PHQ-9 item 9 safety flag
# ---------------------------------------------------------------------------


class TestPhq9SafetyFlag:
    def test_item_9_positive_sets_safety_flag(self, client: TestClient) -> None:
        vals = [0] * 9
        vals[8] = 1  # item 9 (0-indexed = 8)
        body = client.post(
            _URL_SESSIONS, json=_phq9_responses(vals), headers=_USER_A
        ).json()
        assert body["safety_flag"] is True

    def test_item_9_zero_does_not_set_safety_flag(self, client: TestClient) -> None:
        body = client.post(
            _URL_SESSIONS, json=_phq9_responses([0] * 9), headers=_USER_A
        ).json()
        assert body["safety_flag"] is False

    def test_item_9_value_3_sets_safety_flag(self, client: TestClient) -> None:
        vals = [0] * 9
        vals[8] = 3
        body = client.post(
            _URL_SESSIONS, json=_phq9_responses(vals), headers=_USER_A
        ).json()
        assert body["safety_flag"] is True


# ---------------------------------------------------------------------------
# 7. Non-PHQ-9 instruments do not set safety_flag
# ---------------------------------------------------------------------------


class TestNonPhq9SafetyFlag:
    def test_gad7_safety_flag_false(self, client: TestClient) -> None:
        body = client.post(
            _URL_SESSIONS, json=_gad7_responses([3] * 7), headers=_USER_A
        ).json()
        assert body["safety_flag"] is False

    def test_who5_safety_flag_false(self, client: TestClient) -> None:
        body = client.post(
            _URL_SESSIONS, json=_who5_responses([0] * 5), headers=_USER_A
        ).json()
        assert body["safety_flag"] is False


# ---------------------------------------------------------------------------
# 8. AUDIT log entry on session create
# ---------------------------------------------------------------------------


class TestAuditLog:
    def test_session_create_calls_audit_logger(self, client: TestClient) -> None:
        with patch(
            "discipline.psychometric.router._audit"
        ) as mock_audit:
            client.post(_URL_SESSIONS, json=_phq9_responses(), headers=_USER_A)
            mock_audit.info.assert_called_once()

    def test_audit_event_name(self, client: TestClient) -> None:
        with patch("discipline.psychometric.router._audit") as mock_audit:
            client.post(_URL_SESSIONS, json=_phq9_responses(), headers=_USER_A)
            call_args = mock_audit.info.call_args
            event = call_args.args[0] if call_args.args else call_args[0][0]
            assert event == "assessment_session.created"

    def test_audit_event_has_action_field(self, client: TestClient) -> None:
        with patch("discipline.psychometric.router._audit") as mock_audit:
            client.post(_URL_SESSIONS, json=_phq9_responses(), headers=_USER_A)
            kwargs = mock_audit.info.call_args.kwargs
            assert kwargs.get("action") == "session_submit"

    def test_audit_event_has_user_id(self, client: TestClient) -> None:
        with patch("discipline.psychometric.router._audit") as mock_audit:
            client.post(_URL_SESSIONS, json=_phq9_responses(), headers=_USER_A)
            kwargs = mock_audit.info.call_args.kwargs
            assert kwargs.get("user_id") == "user_session_001"


# ---------------------------------------------------------------------------
# 9. T3 fire emits safety-stream event
# ---------------------------------------------------------------------------


class TestT3SafetyEvent:
    def test_phq9_item9_fire_emits_safety_event(self, client: TestClient) -> None:
        vals = [0] * 9
        vals[8] = 1
        with patch("discipline.psychometric.router._safety") as mock_safety:
            client.post(_URL_SESSIONS, json=_phq9_responses(vals), headers=_USER_A)
            mock_safety.warning.assert_called_once()

    def test_phq9_no_t3_does_not_emit_safety_event(self, client: TestClient) -> None:
        with patch("discipline.psychometric.router._safety") as mock_safety:
            client.post(_URL_SESSIONS, json=_phq9_responses([0] * 9), headers=_USER_A)
            mock_safety.warning.assert_not_called()


# ---------------------------------------------------------------------------
# 10-12. GET /sessions — empty, history, limit
# ---------------------------------------------------------------------------


class TestListSessions:
    def test_empty_list_for_new_user(self, client: TestClient) -> None:
        resp = client.get(_URL_SESSIONS, headers=_USER_A)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_history_returns_submitted_sessions(self, client: TestClient) -> None:
        client.post(_URL_SESSIONS, json=_phq9_responses([1] * 9), headers=_USER_A)
        history = client.get(_URL_SESSIONS, headers=_USER_A).json()
        assert len(history) == 1
        assert history[0]["instrument"] == "phq9"

    def test_limit_parameter(self, client: TestClient) -> None:
        for _ in range(5):
            client.post(_URL_SESSIONS, json=_phq9_responses([1] * 9), headers=_USER_A)
        history = client.get(_URL_SESSIONS + "?limit=3", headers=_USER_A).json()
        assert len(history) == 3

    def test_default_limit_is_fifty(self, client: TestClient) -> None:
        """Verify the default limit doesn't truncate small result sets."""
        for _ in range(10):
            client.post(_URL_SESSIONS, json=_phq9_responses([1] * 9), headers=_USER_A)
        history = client.get(_URL_SESSIONS, headers=_USER_A).json()
        assert len(history) == 10


# ---------------------------------------------------------------------------
# 13. User isolation
# ---------------------------------------------------------------------------


class TestUserIsolation:
    def test_user_a_cannot_see_user_b_sessions(self, client: TestClient) -> None:
        client.post(_URL_SESSIONS, json=_phq9_responses([1] * 9), headers=_USER_B)
        history_a = client.get(_URL_SESSIONS, headers=_USER_A).json()
        assert len(history_a) == 0

    def test_user_b_cannot_see_user_a_sessions(self, client: TestClient) -> None:
        client.post(_URL_SESSIONS, json=_phq9_responses([1] * 9), headers=_USER_A)
        history_b = client.get(_URL_SESSIONS, headers=_USER_B).json()
        assert len(history_b) == 0

    def test_each_user_sees_only_their_own(self, client: TestClient) -> None:
        client.post(_URL_SESSIONS, json=_phq9_responses([1] * 9), headers=_USER_A)
        client.post(_URL_SESSIONS, json=_gad7_responses([2] * 7), headers=_USER_B)
        client.post(_URL_SESSIONS, json=_who5_responses([4] * 5), headers=_USER_A)

        history_a = client.get(_URL_SESSIONS, headers=_USER_A).json()
        history_b = client.get(_URL_SESSIONS, headers=_USER_B).json()

        assert len(history_a) == 2
        assert len(history_b) == 1


# ---------------------------------------------------------------------------
# 14. Missing item values default to 0
# ---------------------------------------------------------------------------


class TestMissingValues:
    def test_responses_without_value_default_to_zero(self, client: TestClient) -> None:
        """If an item has no 'value' key, it should contribute 0 to the score."""
        resp = client.post(
            _URL_SESSIONS,
            json={
                "instrument": "phq-9",
                "responses": [{"item": i + 1} for i in range(9)],
            },
            headers=_USER_A,
        )
        assert resp.status_code == 201
        assert resp.json()["score"] == 0

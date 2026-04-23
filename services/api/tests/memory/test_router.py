"""Memory router tests.

Covers journal CRUD and voice session lifecycle.
"""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from discipline.app import create_app
from discipline.memory.repository import reset_memory_repositories


@pytest.fixture(autouse=True)
def _clear_memory() -> None:
    reset_memory_repositories()


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


_USER_HEADER = {"X-User-Id": "user_mem_001"}
_USER_HEADER_B = {"X-User-Id": "user_mem_002"}


# =============================================================================
# Journal creation
# =============================================================================


class TestJournalCreate:
    def test_create_returns_201(self, client: TestClient) -> None:
        response = client.post(
            "/v1/journals",
            json={"body": "Today was hard but I made it."},
            headers=_USER_HEADER,
        )
        assert response.status_code == 201

    def test_create_response_has_journal_id(self, client: TestClient) -> None:
        body = client.post(
            "/v1/journals",
            json={"body": "Entry one."},
            headers=_USER_HEADER,
        ).json()
        assert "journal_id" in body
        uuid.UUID(body["journal_id"])

    def test_create_with_title(self, client: TestClient) -> None:
        body = client.post(
            "/v1/journals",
            json={"title": "Morning reflection", "body": "Text here."},
            headers=_USER_HEADER,
        ).json()
        assert body["title"] == "Morning reflection"

    def test_create_with_mood_score(self, client: TestClient) -> None:
        body = client.post(
            "/v1/journals",
            json={"body": "Feeling okay.", "mood_score": 6},
            headers=_USER_HEADER,
        ).json()
        assert body["mood_score"] == 6

    def test_create_body_is_encrypted_in_response(self, client: TestClient) -> None:
        body = client.post(
            "/v1/journals",
            json={"body": "Secret thoughts."},
            headers=_USER_HEADER,
        ).json()
        assert body["body_encrypted"] != "Secret thoughts."
        assert isinstance(body["body_encrypted"], str)

    def test_create_missing_body_returns_422(self, client: TestClient) -> None:
        response = client.post("/v1/journals", json={}, headers=_USER_HEADER)
        assert response.status_code == 422

    def test_create_empty_body_returns_422(self, client: TestClient) -> None:
        response = client.post(
            "/v1/journals",
            json={"body": ""},
            headers=_USER_HEADER,
        )
        assert response.status_code == 422

    def test_create_mood_score_below_range_returns_422(self, client: TestClient) -> None:
        response = client.post(
            "/v1/journals",
            json={"body": "Text", "mood_score": -1},
            headers=_USER_HEADER,
        )
        assert response.status_code == 422

    def test_create_mood_score_above_range_returns_422(self, client: TestClient) -> None:
        response = client.post(
            "/v1/journals",
            json={"body": "Text", "mood_score": 11},
            headers=_USER_HEADER,
        )
        assert response.status_code == 422

    def test_create_boundary_mood_scores_accepted(self, client: TestClient) -> None:
        for score in (0, 10):
            response = client.post(
                "/v1/journals",
                json={"body": "Text", "mood_score": score},
                headers=_USER_HEADER,
            )
            assert response.status_code == 201, f"mood_score={score} should be accepted"

    def test_create_without_user_header_uses_fallback(self, client: TestClient) -> None:
        response = client.post("/v1/journals", json={"body": "Anonymous."})
        assert response.status_code == 201
        body = response.json()
        assert body["user_id"] == "test_user_001"


# =============================================================================
# Journal listing
# =============================================================================


class TestJournalList:
    def test_list_empty_returns_empty_items(self, client: TestClient) -> None:
        body = client.get("/v1/journals", headers=_USER_HEADER).json()
        assert body["items"] == []
        assert body["total"] == 0

    def test_list_returns_created_entries(self, client: TestClient) -> None:
        client.post("/v1/journals", json={"body": "A"}, headers=_USER_HEADER)
        client.post("/v1/journals", json={"body": "B"}, headers=_USER_HEADER)
        body = client.get("/v1/journals", headers=_USER_HEADER).json()
        assert body["total"] == 2

    def test_list_is_newest_first(self, client: TestClient) -> None:
        r1 = client.post("/v1/journals", json={"body": "First"}, headers=_USER_HEADER).json()
        r2 = client.post("/v1/journals", json={"body": "Second"}, headers=_USER_HEADER).json()
        items = client.get("/v1/journals", headers=_USER_HEADER).json()["items"]
        assert items[0]["journal_id"] == r2["journal_id"]
        assert items[1]["journal_id"] == r1["journal_id"]

    def test_list_respects_user_isolation(self, client: TestClient) -> None:
        client.post("/v1/journals", json={"body": "Mine"}, headers=_USER_HEADER)
        client.post("/v1/journals", json={"body": "Yours"}, headers=_USER_HEADER_B)
        body = client.get("/v1/journals", headers=_USER_HEADER).json()
        assert body["total"] == 1
        assert body["items"][0]["body_preview"] != "Yours"

    def test_list_item_has_preview_not_full_body(self, client: TestClient) -> None:
        client.post("/v1/journals", json={"body": "A" * 500}, headers=_USER_HEADER)
        items = client.get("/v1/journals", headers=_USER_HEADER).json()["items"]
        assert len(items[0]["body_preview"]) < 500

    def test_list_limit_parameter(self, client: TestClient) -> None:
        for i in range(5):
            client.post("/v1/journals", json={"body": str(i)}, headers=_USER_HEADER)
        body = client.get("/v1/journals?limit=2", headers=_USER_HEADER).json()
        assert body["total"] == 2


# =============================================================================
# Journal detail
# =============================================================================


class TestJournalDetail:
    def test_get_existing_returns_200(self, client: TestClient) -> None:
        created = client.post(
            "/v1/journals",
            json={"body": "Detail test."},
            headers=_USER_HEADER,
        ).json()
        response = client.get(f"/v1/journals/{created['journal_id']}", headers=_USER_HEADER)
        assert response.status_code == 200

    def test_get_returns_full_encrypted_body(self, client: TestClient) -> None:
        created = client.post(
            "/v1/journals",
            json={"body": "Secret detail."},
            headers=_USER_HEADER,
        ).json()
        detail = client.get(
            f"/v1/journals/{created['journal_id']}",
            headers=_USER_HEADER,
        ).json()
        assert detail["body_encrypted"] == created["body_encrypted"]

    def test_get_not_found_returns_404(self, client: TestClient) -> None:
        response = client.get(f"/v1/journals/{uuid.uuid4()}", headers=_USER_HEADER)
        assert response.status_code == 404
        assert response.json()["detail"] == "journal.not_found"

    def test_get_cross_user_isolation(self, client: TestClient) -> None:
        created = client.post(
            "/v1/journals",
            json={"body": "Private."},
            headers=_USER_HEADER,
        ).json()
        response = client.get(
            f"/v1/journals/{created['journal_id']}",
            headers=_USER_HEADER_B,
        )
        assert response.status_code == 404


# =============================================================================
# Voice session creation
# =============================================================================


class TestVoiceSessionCreate:
    def test_create_returns_201(self, client: TestClient) -> None:
        response = client.post("/v1/voice/sessions", headers=_USER_HEADER)
        assert response.status_code == 201

    def test_create_response_has_session_id(self, client: TestClient) -> None:
        body = client.post("/v1/voice/sessions", headers=_USER_HEADER).json()
        assert "session_id" in body
        uuid.UUID(body["session_id"])

    def test_create_status_is_recording(self, client: TestClient) -> None:
        body = client.post("/v1/voice/sessions", headers=_USER_HEADER).json()
        assert body["status"] == "recording"

    def test_create_has_hard_delete_at(self, client: TestClient) -> None:
        body = client.post("/v1/voice/sessions", headers=_USER_HEADER).json()
        assert "hard_delete_at" in body
        assert isinstance(body["hard_delete_at"], str)

    def test_create_hard_delete_is_72h_from_now(self, client: TestClient) -> None:
        from datetime import UTC, datetime, timedelta

        body = client.post("/v1/voice/sessions", headers=_USER_HEADER).json()
        hard_delete = datetime.fromisoformat(body["hard_delete_at"])
        created = datetime.fromisoformat(body["created_at"])
        delta = hard_delete - created
        assert timedelta(hours=71) < delta < timedelta(hours=73)


# =============================================================================
# Voice session finalize
# =============================================================================


class TestVoiceSessionFinalize:
    def test_finalize_returns_200(self, client: TestClient) -> None:
        session = client.post("/v1/voice/sessions", headers=_USER_HEADER).json()
        response = client.post(
            f"/v1/voice/sessions/{session['session_id']}/finalize",
            json={"s3_key": "voices/user1/test.webm"},
            headers=_USER_HEADER,
        )
        assert response.status_code == 200

    def test_finalize_updates_status(self, client: TestClient) -> None:
        session = client.post("/v1/voice/sessions", headers=_USER_HEADER).json()
        body = client.post(
            f"/v1/voice/sessions/{session['session_id']}/finalize",
            json={"s3_key": "voices/user1/test.webm"},
            headers=_USER_HEADER,
        ).json()
        assert body["status"] == "uploaded"

    def test_finalize_sets_s3_key(self, client: TestClient) -> None:
        session = client.post("/v1/voice/sessions", headers=_USER_HEADER).json()
        body = client.post(
            f"/v1/voice/sessions/{session['session_id']}/finalize",
            json={"s3_key": "voices/user1/test.webm"},
            headers=_USER_HEADER,
        ).json()
        assert body["s3_key"] == "voices/user1/test.webm"

    def test_finalize_sets_duration(self, client: TestClient) -> None:
        session = client.post("/v1/voice/sessions", headers=_USER_HEADER).json()
        body = client.post(
            f"/v1/voice/sessions/{session['session_id']}/finalize",
            json={"s3_key": "voices/user1/test.webm", "duration_seconds": 120},
            headers=_USER_HEADER,
        ).json()
        assert body["duration_seconds"] == 120

    def test_finalize_missing_s3_key_returns_422(self, client: TestClient) -> None:
        session = client.post("/v1/voice/sessions", headers=_USER_HEADER).json()
        response = client.post(
            f"/v1/voice/sessions/{session['session_id']}/finalize",
            json={},
            headers=_USER_HEADER,
        )
        assert response.status_code == 422

    def test_finalize_not_found_returns_404(self, client: TestClient) -> None:
        response = client.post(
            f"/v1/voice/sessions/{uuid.uuid4()}/finalize",
            json={"s3_key": "x"},
            headers=_USER_HEADER,
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "voice_session.not_found"

    def test_finalize_cross_user_isolation(self, client: TestClient) -> None:
        session = client.post("/v1/voice/sessions", headers=_USER_HEADER).json()
        response = client.post(
            f"/v1/voice/sessions/{session['session_id']}/finalize",
            json={"s3_key": "x"},
            headers=_USER_HEADER_B,
        )
        assert response.status_code == 404


# =============================================================================
# Voice session detail
# =============================================================================


class TestVoiceSessionDetail:
    def test_get_existing_returns_200(self, client: TestClient) -> None:
        created = client.post("/v1/voice/sessions", headers=_USER_HEADER).json()
        response = client.get(
            f"/v1/voice/sessions/{created['session_id']}",
            headers=_USER_HEADER,
        )
        assert response.status_code == 200

    def test_get_not_found_returns_404(self, client: TestClient) -> None:
        response = client.get(f"/v1/voice/sessions/{uuid.uuid4()}", headers=_USER_HEADER)
        assert response.status_code == 404
        assert response.json()["detail"] == "voice_session.not_found"

    def test_get_cross_user_isolation(self, client: TestClient) -> None:
        created = client.post("/v1/voice/sessions", headers=_USER_HEADER).json()
        response = client.get(
            f"/v1/voice/sessions/{created['session_id']}",
            headers=_USER_HEADER_B,
        )
        assert response.status_code == 404

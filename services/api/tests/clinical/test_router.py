"""Clinical router tests.

Covers relapse reporting, compassion response determinism, retrieval,
and review workflow.
"""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from discipline.app import create_app
from discipline.clinical.repository import reset_relapse_repository


@pytest.fixture(autouse=True)
def _clear_relapses() -> None:
    reset_relapse_repository()


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


_USER_HEADER = {"X-User-Id": "user_clin_001"}
_USER_HEADER_B = {"X-User-Id": "user_clin_002"}
_URL = "/v1/relapses"


# =============================================================================
# Relapse creation
# =============================================================================


class TestRelapseCreate:
    def test_create_returns_201(self, client: TestClient) -> None:
        response = client.post(
            _URL,
            json={
                "occurred_at": "2026-04-22T10:00:00Z",
                "behavior": "alcohol",
                "severity": 3,
            },
            headers={**_USER_HEADER, "Idempotency-Key": "ik-1"},
        )
        assert response.status_code == 201

    def test_create_response_has_relapse_id(self, client: TestClient) -> None:
        body = client.post(
            _URL,
            json={
                "occurred_at": "2026-04-22T10:00:00Z",
                "behavior": "alcohol",
                "severity": 3,
            },
            headers={**_USER_HEADER, "Idempotency-Key": "ik-2"},
        ).json()
        assert "relapse_id" in body
        uuid.UUID(body["relapse_id"])

    def test_create_has_compassion_message(self, client: TestClient) -> None:
        body = client.post(
            _URL,
            json={
                "occurred_at": "2026-04-22T10:00:00Z",
                "behavior": "alcohol",
                "severity": 3,
            },
            headers={**_USER_HEADER, "Idempotency-Key": "ik-3"},
        ).json()
        assert "compassion_message" in body
        assert isinstance(body["compassion_message"], str)
        assert len(body["compassion_message"]) > 0

    def test_create_no_shame_language(self, client: TestClient) -> None:
        """AGENTS.md Rule #4: no shame-adjacent copy."""
        body = client.post(
            _URL,
            json={
                "occurred_at": "2026-04-22T10:00:00Z",
                "behavior": "alcohol",
                "severity": 3,
            },
            headers={**_USER_HEADER, "Idempotency-Key": "ik-4"},
        ).json()
        message = body["compassion_message"].lower()
        assert "failed" not in message
        assert "reset" not in message

    def test_create_resilience_preserved_flag(self, client: TestClient) -> None:
        body = client.post(
            _URL,
            json={
                "occurred_at": "2026-04-22T10:00:00Z",
                "behavior": "alcohol",
                "severity": 3,
            },
            headers={**_USER_HEADER, "Idempotency-Key": "ik-5"},
        ).json()
        assert body["resilience_preserved"] is True

    def test_create_next_steps_present(self, client: TestClient) -> None:
        body = client.post(
            _URL,
            json={
                "occurred_at": "2026-04-22T10:00:00Z",
                "behavior": "alcohol",
                "severity": 3,
            },
            headers={**_USER_HEADER, "Idempotency-Key": "ik-6"},
        ).json()
        assert "next_steps" in body
        assert isinstance(body["next_steps"], list)
        assert len(body["next_steps"]) > 0

    def test_create_high_severity_more_steps(self, client: TestClient) -> None:
        low = client.post(
            _URL,
            json={
                "occurred_at": "2026-04-22T10:00:00Z",
                "behavior": "alcohol",
                "severity": 1,
            },
            headers={**_USER_HEADER, "Idempotency-Key": "ik-7"},
        ).json()
        high = client.post(
            _URL,
            json={
                "occurred_at": "2026-04-22T11:00:00Z",
                "behavior": "alcohol",
                "severity": 5,
            },
            headers={**_USER_HEADER, "Idempotency-Key": "ik-8"},
        ).json()
        assert len(high["next_steps"]) >= len(low["next_steps"])

    def test_create_missing_idempotency_key_returns_422(self, client: TestClient) -> None:
        response = client.post(
            _URL,
            json={
                "occurred_at": "2026-04-22T10:00:00Z",
                "behavior": "alcohol",
                "severity": 3,
            },
            headers=_USER_HEADER,
        )
        assert response.status_code == 422

    def test_create_severity_below_range_returns_422(self, client: TestClient) -> None:
        response = client.post(
            _URL,
            json={
                "occurred_at": "2026-04-22T10:00:00Z",
                "behavior": "alcohol",
                "severity": 0,
            },
            headers={**_USER_HEADER, "Idempotency-Key": "ik-9"},
        )
        assert response.status_code == 422

    def test_create_severity_above_range_returns_422(self, client: TestClient) -> None:
        response = client.post(
            _URL,
            json={
                "occurred_at": "2026-04-22T10:00:00Z",
                "behavior": "alcohol",
                "severity": 6,
            },
            headers={**_USER_HEADER, "Idempotency-Key": "ik-10"},
        )
        assert response.status_code == 422

    def test_create_deterministic_compassion_message(self, client: TestClient) -> None:
        """Same input → same compassion message (deterministic)."""
        payload = {
            "occurred_at": "2026-04-22T10:00:00Z",
            "behavior": "alcohol",
            "severity": 3,
        }
        r1 = client.post(_URL, json=payload, headers={**_USER_HEADER, "Idempotency-Key": "ik-d1"}).json()
        r2 = client.post(_URL, json=payload, headers={**_USER_HEADER, "Idempotency-Key": "ik-d2"}).json()
        assert r1["compassion_message"] == r2["compassion_message"]


# =============================================================================
# Relapse retrieval
# =============================================================================


class TestRelapseGet:
    def test_get_existing_returns_200(self, client: TestClient) -> None:
        created = client.post(
            _URL,
            json={
                "occurred_at": "2026-04-22T10:00:00Z",
                "behavior": "alcohol",
                "severity": 3,
            },
            headers={**_USER_HEADER, "Idempotency-Key": "ik-g1"},
        ).json()
        response = client.get(f"{_URL}/{created['relapse_id']}", headers=_USER_HEADER)
        assert response.status_code == 200

    def test_get_returns_same_compassion_message(self, client: TestClient) -> None:
        created = client.post(
            _URL,
            json={
                "occurred_at": "2026-04-22T10:00:00Z",
                "behavior": "alcohol",
                "severity": 3,
            },
            headers={**_USER_HEADER, "Idempotency-Key": "ik-g2"},
        ).json()
        detail = client.get(f"{_URL}/{created['relapse_id']}", headers=_USER_HEADER).json()
        assert detail["compassion_message"] == created["compassion_message"]

    def test_get_not_found_returns_404(self, client: TestClient) -> None:
        response = client.get(f"{_URL}/{uuid.uuid4()}", headers=_USER_HEADER)
        assert response.status_code == 404
        assert response.json()["detail"] == "relapse.not_found"

    def test_get_cross_user_isolation(self, client: TestClient) -> None:
        created = client.post(
            _URL,
            json={
                "occurred_at": "2026-04-22T10:00:00Z",
                "behavior": "alcohol",
                "severity": 3,
            },
            headers={**_USER_HEADER, "Idempotency-Key": "ik-g3"},
        ).json()
        response = client.get(f"{_URL}/{created['relapse_id']}", headers=_USER_HEADER_B)
        assert response.status_code == 404


# =============================================================================
# Relapse review
# =============================================================================


class TestRelapseReview:
    def test_review_returns_200(self, client: TestClient) -> None:
        created = client.post(
            _URL,
            json={
                "occurred_at": "2026-04-22T10:00:00Z",
                "behavior": "alcohol",
                "severity": 3,
            },
            headers={**_USER_HEADER, "Idempotency-Key": "ik-r1"},
        ).json()
        response = client.post(
            f"{_URL}/{created['relapse_id']}/review",
            json={"reviewed_by": "Dr. Smith"},
            headers=_USER_HEADER,
        )
        assert response.status_code == 200

    def test_review_sets_reviewed_true(self, client: TestClient) -> None:
        created = client.post(
            _URL,
            json={
                "occurred_at": "2026-04-22T10:00:00Z",
                "behavior": "alcohol",
                "severity": 3,
            },
            headers={**_USER_HEADER, "Idempotency-Key": "ik-r2"},
        ).json()
        body = client.post(
            f"{_URL}/{created['relapse_id']}/review",
            json={"reviewed_by": "Dr. Smith"},
            headers=_USER_HEADER,
        ).json()
        assert body["reviewed"] is True

    def test_review_sets_reviewed_by(self, client: TestClient) -> None:
        created = client.post(
            _URL,
            json={
                "occurred_at": "2026-04-22T10:00:00Z",
                "behavior": "alcohol",
                "severity": 3,
            },
            headers={**_USER_HEADER, "Idempotency-Key": "ik-r3"},
        ).json()
        body = client.post(
            f"{_URL}/{created['relapse_id']}/review",
            json={"reviewed_by": "Dr. Smith"},
            headers=_USER_HEADER,
        ).json()
        assert body["reviewed_by"] == "Dr. Smith"

    def test_review_sets_reviewed_at(self, client: TestClient) -> None:
        created = client.post(
            _URL,
            json={
                "occurred_at": "2026-04-22T10:00:00Z",
                "behavior": "alcohol",
                "severity": 3,
            },
            headers={**_USER_HEADER, "Idempotency-Key": "ik-r4"},
        ).json()
        body = client.post(
            f"{_URL}/{created['relapse_id']}/review",
            json={"reviewed_by": "Dr. Smith"},
            headers=_USER_HEADER,
        ).json()
        assert body["reviewed_at"] is not None
        assert isinstance(body["reviewed_at"], str)

    def test_review_not_found_returns_404(self, client: TestClient) -> None:
        response = client.post(
            f"{_URL}/{uuid.uuid4()}/review",
            json={"reviewed_by": "Dr. Smith"},
            headers=_USER_HEADER,
        )
        assert response.status_code == 404

    def test_review_cross_user_isolation(self, client: TestClient) -> None:
        created = client.post(
            _URL,
            json={
                "occurred_at": "2026-04-22T10:00:00Z",
                "behavior": "alcohol",
                "severity": 3,
            },
            headers={**_USER_HEADER, "Idempotency-Key": "ik-r5"},
        ).json()
        response = client.post(
            f"{_URL}/{created['relapse_id']}/review",
            json={"reviewed_by": "Dr. Smith"},
            headers=_USER_HEADER_B,
        )
        assert response.status_code == 404

    def test_review_missing_reviewed_by_returns_422(self, client: TestClient) -> None:
        created = client.post(
            _URL,
            json={
                "occurred_at": "2026-04-22T10:00:00Z",
                "behavior": "alcohol",
                "severity": 3,
            },
            headers={**_USER_HEADER, "Idempotency-Key": "ik-r6"},
        ).json()
        response = client.post(
            f"{_URL}/{created['relapse_id']}/review",
            json={},
            headers=_USER_HEADER,
        )
        assert response.status_code == 422

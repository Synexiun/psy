"""``POST /v1/admin/audit/verify`` endpoint tests.

The endpoint wraps :func:`discipline.shared.logging.streams.verify_chain`
in an admin-gated HTTP surface.  These tests pin:

- **Auth gate** — missing / wrong ``X-Admin-Token`` → 403.
- **Happy path** — valid chain → ``valid: true``, ``broken_indices: []``.
- **Tamper detection** — altered record → ``valid: false`` with index
  pointing at the offending record.
- **Edge cases** — empty records, single record, extra fields tolerated.
- **Response shape** — ``total_records``, ``verified_at`` UTC ISO 8601.
"""

from __future__ import annotations

import os
from typing import Any

import pytest
from fastapi.testclient import TestClient

from discipline.app import create_app
from discipline.shared.logging import (
    LogStream,
    compute_chain_hash,
    reset_chain_state,
)
from discipline.shared.logging.streams import GENESIS_SENTINEL, _record_for_chain


# ---- Fixtures --------------------------------------------------------------


@pytest.fixture(autouse=True)
def _isolated_chain_state() -> None:
    """Fresh chain state per test (matches the streams-level test file)."""
    reset_chain_state()
    yield
    reset_chain_state()


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


@pytest.fixture
def admin_headers() -> dict[str, str]:
    token = os.environ.get("ADMIN_API_TOKEN", "dev-admin-token")
    return {"X-Admin-Token": token}


# ---- Helpers --------------------------------------------------------------


def _build_valid_chain(events: list[tuple[str, str]]) -> list[dict[str, Any]]:
    """Build a valid HMAC-Merkle chain by re-using the pure chain math.

    Each input is ``(timestamp, event)``; the returned records carry
    the correct ``prev_hash`` and ``chain_hash`` so :func:`verify_chain`
    should report zero broken indices.
    """
    records: list[dict[str, Any]] = []
    prev = GENESIS_SENTINEL
    for timestamp, event in events:
        record = {"timestamp": timestamp, "event": event}
        record_str = _record_for_chain(record)
        chain_hash = compute_chain_hash(prev, record_str)
        records.append(
            {
                "timestamp": timestamp,
                "event": event,
                "prev_hash": prev,
                "chain_hash": chain_hash,
            }
        )
        prev = chain_hash
    return records


# ---- Auth gate ------------------------------------------------------------


class TestAuthGate:
    def test_missing_token_returns_403(self, client: TestClient) -> None:
        resp = client.post("/v1/admin/audit/verify", json={"records": []})
        assert resp.status_code == 403
        assert resp.json()["detail"]["code"] == "auth.admin_required"

    def test_wrong_token_returns_403(self, client: TestClient) -> None:
        resp = client.post(
            "/v1/admin/audit/verify",
            json={"records": []},
            headers={"X-Admin-Token": "nope"},
        )
        assert resp.status_code == 403
        assert resp.json()["detail"]["code"] == "auth.admin_forbidden"


# ---- Happy path -----------------------------------------------------------


class TestValidChain:
    def test_single_record_valid_chain(
        self, client: TestClient, admin_headers: dict[str, str]
    ) -> None:
        records = _build_valid_chain(
            [("2026-04-18T12:00:00Z", "phi.access.attempt")]
        )
        resp = client.post(
            "/v1/admin/audit/verify",
            json={"records": records},
            headers=admin_headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["valid"] is True
        assert body["total_records"] == 1
        assert body["broken_indices"] == []

    def test_multi_record_valid_chain(
        self, client: TestClient, admin_headers: dict[str, str]
    ) -> None:
        records = _build_valid_chain(
            [
                ("2026-04-18T12:00:00Z", "phi.access.attempt"),
                ("2026-04-18T12:00:01Z", "phi.access.ok"),
                ("2026-04-18T12:00:02Z", "phi.access.attempt"),
                ("2026-04-18T12:00:03Z", "phi.access.ok"),
            ]
        )
        resp = client.post(
            "/v1/admin/audit/verify",
            json={"records": records},
            headers=admin_headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["valid"] is True
        assert body["total_records"] == 4
        assert body["broken_indices"] == []


# ---- Tamper detection -----------------------------------------------------


class TestTamperDetection:
    def test_altered_event_field_detected(
        self, client: TestClient, admin_headers: dict[str, str]
    ) -> None:
        """If an auditor replays records whose ``event`` was altered,
        the replay re-derives a different chain_hash than declared, so
        the record index surfaces in ``broken_indices``.  This is the
        core tamper-evidence guarantee of Rule #6."""
        records = _build_valid_chain(
            [
                ("2026-04-18T12:00:00Z", "phi.access.attempt"),
                ("2026-04-18T12:00:01Z", "phi.access.ok"),
                ("2026-04-18T12:00:02Z", "phi.access.attempt"),
            ]
        )
        # Tamper index 1 — alter the event name but leave hashes in place.
        records[1]["event"] = "phi.access.deleted"

        resp = client.post(
            "/v1/admin/audit/verify",
            json={"records": records},
            headers=admin_headers,
        )
        body = resp.json()
        assert body["valid"] is False
        assert 1 in body["broken_indices"]

    def test_altered_chain_hash_detected(
        self, client: TestClient, admin_headers: dict[str, str]
    ) -> None:
        """Overwriting the declared chain_hash with garbage must break
        verification at that index."""
        records = _build_valid_chain(
            [
                ("2026-04-18T12:00:00Z", "a"),
                ("2026-04-18T12:00:01Z", "b"),
            ]
        )
        records[0]["chain_hash"] = "deadbeef" * 8

        resp = client.post(
            "/v1/admin/audit/verify",
            json={"records": records},
            headers=admin_headers,
        )
        body = resp.json()
        assert body["valid"] is False
        assert 0 in body["broken_indices"]

    def test_altered_prev_hash_detected(
        self, client: TestClient, admin_headers: dict[str, str]
    ) -> None:
        records = _build_valid_chain(
            [
                ("2026-04-18T12:00:00Z", "a"),
                ("2026-04-18T12:00:01Z", "b"),
            ]
        )
        # A prev_hash not matching the previous record's chain_hash breaks
        # the link even if the current chain_hash happens to look valid.
        records[1]["prev_hash"] = "cafebabe" * 8

        resp = client.post(
            "/v1/admin/audit/verify",
            json={"records": records},
            headers=admin_headers,
        )
        body = resp.json()
        assert body["valid"] is False
        assert 1 in body["broken_indices"]


# ---- Edge cases -----------------------------------------------------------


class TestEdgeCases:
    def test_empty_records_list_is_vacuously_valid(
        self, client: TestClient, admin_headers: dict[str, str]
    ) -> None:
        """No records → nothing to verify → vacuously valid.  This is
        the right answer for a caller asking 'is this empty archive
        intact' — the answer is yes, there's nothing to tamper with."""
        resp = client.post(
            "/v1/admin/audit/verify",
            json={"records": []},
            headers=admin_headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["valid"] is True
        assert body["total_records"] == 0
        assert body["broken_indices"] == []

    def test_extra_fields_on_record_tolerated(
        self, client: TestClient, admin_headers: dict[str, str]
    ) -> None:
        """Real audit records carry extra fields (actor_id, subject_id,
        resource, …).  ``AuditRecord.model_config.extra='allow'`` must
        let them pass through without 422ing.  The chain math only
        hashes over timestamp+event anyway."""
        records = _build_valid_chain(
            [("2026-04-18T12:00:00Z", "phi.access.attempt")]
        )
        records[0]["actor_id"] = "clinician_001"
        records[0]["subject_id"] = "patient_abc"
        records[0]["resource"] = "fhir.bundle"

        resp = client.post(
            "/v1/admin/audit/verify",
            json={"records": records},
            headers=admin_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["valid"] is True

    def test_missing_required_field_rejected(
        self, client: TestClient, admin_headers: dict[str, str]
    ) -> None:
        """Records missing ``chain_hash`` cannot be verified — 422 with
        field-level detail rather than silently returning 'valid: false'."""
        resp = client.post(
            "/v1/admin/audit/verify",
            json={
                "records": [
                    {
                        "timestamp": "2026-04-18T12:00:00Z",
                        "event": "x",
                        "prev_hash": "abc",
                        # chain_hash deliberately missing
                    }
                ]
            },
            headers=admin_headers,
        )
        assert resp.status_code == 422


# ---- Response shape -------------------------------------------------------


class TestResponseShape:
    def test_response_contains_all_expected_keys(
        self, client: TestClient, admin_headers: dict[str, str]
    ) -> None:
        records = _build_valid_chain([("2026-04-18T12:00:00Z", "x")])
        resp = client.post(
            "/v1/admin/audit/verify",
            json={"records": records},
            headers=admin_headers,
        )
        body = resp.json()
        assert set(body.keys()) == {
            "valid",
            "total_records",
            "broken_indices",
            "verified_at",
        }

    def test_verified_at_is_iso_utc(
        self, client: TestClient, admin_headers: dict[str, str]
    ) -> None:
        resp = client.post(
            "/v1/admin/audit/verify",
            json={"records": []},
            headers=admin_headers,
        )
        verified_at = resp.json()["verified_at"]
        # FastAPI/Pydantic serializes tz-aware datetime as ISO 8601;
        # the tz marker is ``+00:00`` or ``Z`` depending on config.
        assert "T" in verified_at
        assert verified_at.endswith(("Z", "+00:00"))


# ---- Independence from live stream state ----------------------------------


class TestStatelessReplay:
    def test_endpoint_does_not_mutate_live_chain_state(
        self,
        client: TestClient,
        admin_headers: dict[str, str],
    ) -> None:
        """Verification is replay-only — calling the endpoint must NOT
        advance the in-memory Merkle state of either live stream.  A
        regression that leaked through and advanced the state would
        corrupt subsequent real emissions by producing wrong prev_hash
        values for the next audit write."""
        from discipline.shared.logging.streams import _MERKLE_CHAIN_STATE

        assert _MERKLE_CHAIN_STATE.get(LogStream.AUDIT) is None
        records = _build_valid_chain(
            [
                ("2026-04-18T12:00:00Z", "x"),
                ("2026-04-18T12:00:01Z", "y"),
            ]
        )
        client.post(
            "/v1/admin/audit/verify",
            json={"records": records},
            headers=admin_headers,
        )
        # After verification, the live state must still be untouched.
        assert _MERKLE_CHAIN_STATE.get(LogStream.AUDIT) is None

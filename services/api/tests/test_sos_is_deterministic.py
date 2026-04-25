"""T3 crisis flow invariants.

These tests encode NON-NEGOTIABLE clinical rules. They must never be skipped,
weakened, or made flaky.

CLAUDE.md Rule 1:
  T3/T4 crisis flows are deterministic. Never call the LLM in a crisis path.
  Never rely on a network round-trip to render crisis UI. Never feature-flag
  crisis behavior.

CLAUDE.md Rule: 100% branch coverage on T3 flows.

See Docs/Technicals/06_ML_AI_Architecture.md §9.2.
See Docs/Whitepapers/04_Safety_Framework.md §T3/T4.
"""

from __future__ import annotations

import re
import uuid

from fastapi.testclient import TestClient

from discipline.app import create_app


def _client() -> TestClient:
    return TestClient(create_app())


# ---------------------------------------------------------------------------
# Status code and baseline structure
# ---------------------------------------------------------------------------


def test_sos_returns_201() -> None:
    response = _client().post("/v1/sos", headers={"Idempotency-Key": "test-key-1"})
    assert response.status_code == 201, response.text


def test_sos_returns_json() -> None:
    response = _client().post("/v1/sos", headers={"Idempotency-Key": "test-key-json"})
    body = response.json()
    assert isinstance(body, dict)


def test_sos_has_payload_key() -> None:
    body = _client().post("/v1/sos", headers={"Idempotency-Key": "k"}).json()
    assert "payload" in body


def test_sos_has_urge_id() -> None:
    body = _client().post("/v1/sos", headers={"Idempotency-Key": "k"}).json()
    assert "urge_id" in body


def test_sos_has_intervention_id() -> None:
    body = _client().post("/v1/sos", headers={"Idempotency-Key": "k"}).json()
    assert "intervention_id" in body


def test_sos_urge_id_is_valid_uuid() -> None:
    body = _client().post("/v1/sos", headers={"Idempotency-Key": "k"}).json()
    uuid.UUID(body["urge_id"])


def test_sos_intervention_id_is_valid_uuid() -> None:
    body = _client().post("/v1/sos", headers={"Idempotency-Key": "k"}).json()
    uuid.UUID(body["intervention_id"])


# ---------------------------------------------------------------------------
# Payload content — deterministic clinical requirements
# ---------------------------------------------------------------------------


def test_sos_ui_template_is_crisis_flow_v3() -> None:
    """UI template must be pinned. Mobile uses this string to pick the crisis renderer."""
    body = _client().post("/v1/sos", headers={"Idempotency-Key": "k"}).json()
    assert body["payload"]["ui_template"] == "crisis_flow_v3"


def test_sos_tools_hardcoded_contains_urge_surf() -> None:
    body = _client().post("/v1/sos", headers={"Idempotency-Key": "k"}).json()
    assert "urge_surf" in body["payload"]["tools_hardcoded"]


def test_sos_tools_hardcoded_contains_tipp_60s() -> None:
    body = _client().post("/v1/sos", headers={"Idempotency-Key": "k"}).json()
    assert "tipp_60s" in body["payload"]["tools_hardcoded"]


def test_sos_tools_hardcoded_contains_call_support() -> None:
    """Crisis flow must always include a human-connection option."""
    body = _client().post("/v1/sos", headers={"Idempotency-Key": "k"}).json()
    assert "call_support" in body["payload"]["tools_hardcoded"]


def test_sos_local_hotline_is_988() -> None:
    """988 is the US Suicide and Crisis Lifeline — must be present and correct."""
    body = _client().post("/v1/sos", headers={"Idempotency-Key": "k"}).json()
    assert body["payload"]["local_hotline"] == "988"


def test_sos_tools_hardcoded_is_a_list() -> None:
    body = _client().post("/v1/sos", headers={"Idempotency-Key": "k"}).json()
    assert isinstance(body["payload"]["tools_hardcoded"], list)


def test_sos_tools_hardcoded_not_empty() -> None:
    body = _client().post("/v1/sos", headers={"Idempotency-Key": "k"}).json()
    assert len(body["payload"]["tools_hardcoded"]) > 0


# ---------------------------------------------------------------------------
# Determinism: identical structure across calls (offline-cache contract)
# ---------------------------------------------------------------------------


def test_sos_payload_structure_stable_across_calls() -> None:
    """Crisis payload must be reliably identical in structure — mobile caches
    this exact shape on device and relies on it for offline crisis rendering.
    """
    c = _client()
    r1 = c.post("/v1/sos", headers={"Idempotency-Key": "k1"}).json()
    r2 = c.post("/v1/sos", headers={"Idempotency-Key": "k2"}).json()
    assert r1["payload"].keys() == r2["payload"].keys()


def test_sos_tools_hardcoded_identical_across_calls() -> None:
    c = _client()
    r1 = c.post("/v1/sos", headers={"Idempotency-Key": "k1"}).json()
    r2 = c.post("/v1/sos", headers={"Idempotency-Key": "k2"}).json()
    assert r1["payload"]["tools_hardcoded"] == r2["payload"]["tools_hardcoded"]


def test_sos_ui_template_identical_across_calls() -> None:
    c = _client()
    r1 = c.post("/v1/sos", headers={"Idempotency-Key": "k1"}).json()
    r2 = c.post("/v1/sos", headers={"Idempotency-Key": "k2"}).json()
    assert r1["payload"]["ui_template"] == r2["payload"]["ui_template"]


def test_sos_hotline_identical_across_calls() -> None:
    c = _client()
    r1 = c.post("/v1/sos", headers={"Idempotency-Key": "k1"}).json()
    r2 = c.post("/v1/sos", headers={"Idempotency-Key": "k2"}).json()
    assert r1["payload"]["local_hotline"] == r2["payload"]["local_hotline"]


def test_sos_urge_id_differs_across_calls() -> None:
    """Each SOS call generates a fresh UUID — never reuse the same urge_id."""
    c = _client()
    r1 = c.post("/v1/sos", headers={"Idempotency-Key": "k1"}).json()
    r2 = c.post("/v1/sos", headers={"Idempotency-Key": "k2"}).json()
    assert r1["urge_id"] != r2["urge_id"]


# ---------------------------------------------------------------------------
# Required header: Idempotency-Key
# ---------------------------------------------------------------------------


def test_sos_requires_idempotency_key() -> None:
    """Missing Idempotency-Key must be rejected — prevents duplicate crisis activations."""
    response = _client().post("/v1/sos")
    assert response.status_code == 422


def test_sos_accepts_any_non_empty_idempotency_key() -> None:
    c = _client()
    assert c.post("/v1/sos", headers={"Idempotency-Key": "abc"}).status_code == 201
    assert c.post("/v1/sos", headers={"Idempotency-Key": str(uuid.uuid4())}).status_code == 201

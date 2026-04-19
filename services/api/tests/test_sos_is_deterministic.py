"""T3 crisis flow invariants.

These tests encode non-negotiable clinical rules. They must never be skipped,
weakened, or flaky. See Docs/Technicals/06_ML_AI_Architecture.md §9.2.
"""

from fastapi.testclient import TestClient

from discipline.app import create_app


def test_sos_returns_deterministic_payload() -> None:
    client = TestClient(create_app())
    response = client.post("/v1/sos", headers={"Idempotency-Key": "test-key-1"})

    assert response.status_code == 201
    body = response.json()

    assert body["payload"]["ui_template"] == "crisis_flow_v3"
    assert "urge_surf" in body["payload"]["tools_hardcoded"]
    assert "tipp_60s" in body["payload"]["tools_hardcoded"]
    assert body["payload"]["local_hotline"] == "988"


def test_sos_payload_shape_is_stable_across_calls() -> None:
    """Crisis payload must be reliably identical in structure — mobile caches
    this exact shape on device and relies on it for offline crisis rendering.
    """
    client = TestClient(create_app())
    r1 = client.post("/v1/sos", headers={"Idempotency-Key": "k1"}).json()
    r2 = client.post("/v1/sos", headers={"Idempotency-Key": "k2"}).json()
    assert r1["payload"].keys() == r2["payload"].keys()
    assert r1["payload"]["tools_hardcoded"] == r2["payload"]["tools_hardcoded"]

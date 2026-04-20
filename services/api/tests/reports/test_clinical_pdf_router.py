"""Clinical PDF report router tests.

``POST /v1/reports/clinical/pdf`` is a 501 stub that will eventually queue a
PDF export job.  These tests verify the contract while the stub is in place so
a future implementation doesn't silently diverge from the declared shape.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from discipline.app import create_app


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


_URL = "/v1/reports/clinical/pdf"


class TestClinicalPdfEndpoint:
    def test_returns_501(self, client: TestClient) -> None:
        """Stub contract: endpoint is not yet implemented → 501."""
        response = client.post(_URL)
        assert response.status_code == 501

    def test_response_body_has_code_field(self, client: TestClient) -> None:
        """FastAPI wraps HTTPException detail in {'detail': ...}."""
        body = client.post(_URL).json()
        assert "detail" in body
        assert "code" in body["detail"]

    def test_code_is_not_implemented(self, client: TestClient) -> None:
        body = client.post(_URL).json()
        assert body["detail"]["code"] == "not_implemented"

    def test_post_with_empty_body_still_returns_501(self, client: TestClient) -> None:
        response = client.post(_URL, json={})
        assert response.status_code == 501

    def test_post_with_arbitrary_body_returns_501(self, client: TestClient) -> None:
        """Stub rejects all payloads — implementation details are not wired yet."""
        response = client.post(_URL, json={"patient_id": "abc", "range_days": 90})
        assert response.status_code == 501

    def test_response_is_stable_across_calls(self, client: TestClient) -> None:
        b1 = client.post(_URL).json()
        b2 = client.post(_URL).json()
        assert b1["detail"]["code"] == b2["detail"]["code"]

"""Enterprise router tests — org provisioning, clinician links, aggregate reports.

Covers organization lifecycle, clinician-patient invite/consent/revoke,
k-anonymity floor on reports, and user isolation.
"""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from discipline.app import create_app
from discipline.enterprise.repository import reset_enterprise_repositories


@pytest.fixture(autouse=True)
def _clear_enterprise() -> None:
    reset_enterprise_repositories()


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


_CLINICIAN_HEADER = {"X-User-Id": "user_clin_001"}
_PATIENT_HEADER = {"X-User-Id": "user_pat_001"}
_OTHER_HEADER = {"X-User-Id": "user_other_001"}

_URL_ORGS = "/v1/enterprise/orgs"
_URL_LINKS = "/v1/enterprise/clinician-links"
_URL_REPORTS = "/v1/enterprise/reports/monthly"


def _provision_org(client: TestClient, **overrides) -> dict:
    payload = {"name": "Test Org", "slug": "test-org", "tier": "standard"}
    payload.update(overrides)
    return client.post(_URL_ORGS, json=payload, headers=_CLINICIAN_HEADER).json()


def _create_link(client: TestClient, org_id: str, patient_user_id: str) -> dict:
    return client.post(
        _URL_LINKS,
        json={"org_id": org_id, "patient_user_id": patient_user_id},
        headers=_CLINICIAN_HEADER,
    ).json()


# =============================================================================
# Organization provisioning
# =============================================================================


class TestOrgProvision:
    def test_provision_returns_201(self, client: TestClient) -> None:
        response = client.post(
            _URL_ORGS,
            json={"name": "Test Org", "slug": "test-org"},
            headers=_CLINICIAN_HEADER,
        )
        assert response.status_code == 201

    def test_provision_response_has_org_id(self, client: TestClient) -> None:
        body = client.post(
            _URL_ORGS,
            json={"name": "Test Org", "slug": "test-org"},
            headers=_CLINICIAN_HEADER,
        ).json()
        assert "org_id" in body
        uuid.UUID(body["org_id"])

    def test_provision_persists_name_and_slug(self, client: TestClient) -> None:
        body = client.post(
            _URL_ORGS,
            json={"name": "Acme Health", "slug": "acme-health"},
            headers=_CLINICIAN_HEADER,
        ).json()
        assert body["name"] == "Acme Health"
        assert body["slug"] == "acme-health"

    def test_provision_defaults_to_standard_tier(self, client: TestClient) -> None:
        body = client.post(
            _URL_ORGS,
            json={"name": "Test Org", "slug": "test-org"},
            headers=_CLINICIAN_HEADER,
        ).json()
        assert body["tier"] == "standard"

    def test_provision_all_valid_tiers_accepted(self, client: TestClient) -> None:
        for tier in ("pilot", "standard", "enterprise"):
            reset_enterprise_repositories()
            response = client.post(
                _URL_ORGS,
                json={"name": "Test Org", "slug": f"test-org-{tier}", "tier": tier},
                headers=_CLINICIAN_HEADER,
            )
            assert response.status_code == 201, f"tier={tier} failed"

    def test_provision_invalid_tier_returns_422(self, client: TestClient) -> None:
        response = client.post(
            _URL_ORGS,
            json={"name": "Test Org", "slug": "test-org", "tier": "invalid"},
            headers=_CLINICIAN_HEADER,
        )
        assert response.status_code == 422

    def test_provision_missing_name_returns_422(self, client: TestClient) -> None:
        response = client.post(
            _URL_ORGS,
            json={"slug": "test-org"},
            headers=_CLINICIAN_HEADER,
        )
        assert response.status_code == 422

    def test_provision_defaults_to_active_status(self, client: TestClient) -> None:
        body = client.post(
            _URL_ORGS,
            json={"name": "Test Org", "slug": "test-org"},
            headers=_CLINICIAN_HEADER,
        ).json()
        assert body["status"] == "active"


# =============================================================================
# Organization retrieval
# =============================================================================


class TestOrgGet:
    def test_get_returns_200(self, client: TestClient) -> None:
        org = _provision_org(client)
        response = client.get(f"{_URL_ORGS}/{org['org_id']}", headers=_CLINICIAN_HEADER)
        assert response.status_code == 200

    def test_get_returns_same_org(self, client: TestClient) -> None:
        org = _provision_org(client)
        body = client.get(f"{_URL_ORGS}/{org['org_id']}", headers=_CLINICIAN_HEADER).json()
        assert body["org_id"] == org["org_id"]
        assert body["name"] == org["name"]

    def test_get_unknown_returns_404(self, client: TestClient) -> None:
        response = client.get(
            f"{_URL_ORGS}/00000000-0000-0000-0000-000000000000",
            headers=_CLINICIAN_HEADER,
        )
        assert response.status_code == 404


# =============================================================================
# Clinician link invite
# =============================================================================


class TestClinicianLinkInvite:
    def test_invite_returns_201(self, client: TestClient) -> None:
        org = _provision_org(client)
        response = client.post(
            _URL_LINKS,
            json={"org_id": org["org_id"], "patient_user_id": "user_pat_001"},
            headers=_CLINICIAN_HEADER,
        )
        assert response.status_code == 201

    def test_invite_response_has_link_id(self, client: TestClient) -> None:
        org = _provision_org(client)
        body = client.post(
            _URL_LINKS,
            json={"org_id": org["org_id"], "patient_user_id": "user_pat_001"},
            headers=_CLINICIAN_HEADER,
        ).json()
        assert "link_id" in body
        uuid.UUID(body["link_id"])

    def test_invite_defaults_to_pending(self, client: TestClient) -> None:
        org = _provision_org(client)
        body = client.post(
            _URL_LINKS,
            json={"org_id": org["org_id"], "patient_user_id": "user_pat_001"},
            headers=_CLINICIAN_HEADER,
        ).json()
        assert body["status"] == "pending"
        assert body["consented_at"] is None

    def test_invite_records_clinician_as_caller(self, client: TestClient) -> None:
        org = _provision_org(client)
        body = client.post(
            _URL_LINKS,
            json={"org_id": org["org_id"], "patient_user_id": "user_pat_001"},
            headers=_CLINICIAN_HEADER,
        ).json()
        assert body["clinician_user_id"] == "user_clin_001"

    def test_invite_missing_org_id_returns_422(self, client: TestClient) -> None:
        response = client.post(
            _URL_LINKS,
            json={"patient_user_id": "user_pat_001"},
            headers=_CLINICIAN_HEADER,
        )
        assert response.status_code == 422


# =============================================================================
# Clinician link consent
# =============================================================================


class TestClinicianLinkConsent:
    def test_consent_returns_200(self, client: TestClient) -> None:
        org = _provision_org(client)
        link = _create_link(client, org["org_id"], "user_pat_001")
        response = client.post(
            f"{_URL_LINKS}/{link['link_id']}/consent",
            headers=_PATIENT_HEADER,
        )
        assert response.status_code == 200

    def test_consent_sets_status_to_active(self, client: TestClient) -> None:
        org = _provision_org(client)
        link = _create_link(client, org["org_id"], "user_pat_001")
        body = client.post(
            f"{_URL_LINKS}/{link['link_id']}/consent",
            headers=_PATIENT_HEADER,
        ).json()
        assert body["status"] == "active"
        assert body["consented_at"] is not None

    def test_consent_wrong_patient_returns_404(self, client: TestClient) -> None:
        org = _provision_org(client)
        link = _create_link(client, org["org_id"], "user_pat_001")
        response = client.post(
            f"{_URL_LINKS}/{link['link_id']}/consent",
            headers=_OTHER_HEADER,
        )
        assert response.status_code == 404

    def test_consent_unknown_link_returns_404(self, client: TestClient) -> None:
        response = client.post(
            f"{_URL_LINKS}/00000000-0000-0000-0000-000000000000/consent",
            headers=_PATIENT_HEADER,
        )
        assert response.status_code == 404


# =============================================================================
# Clinician link revoke
# =============================================================================


class TestClinicianLinkRevoke:
    def test_revoke_by_clinician_returns_200(self, client: TestClient) -> None:
        org = _provision_org(client)
        link = _create_link(client, org["org_id"], "user_pat_001")
        response = client.post(
            f"{_URL_LINKS}/{link['link_id']}/revoke",
            headers=_CLINICIAN_HEADER,
        )
        assert response.status_code == 200

    def test_revoke_by_patient_returns_200(self, client: TestClient) -> None:
        org = _provision_org(client)
        link = _create_link(client, org["org_id"], "user_pat_001")
        # First consent
        client.post(f"{_URL_LINKS}/{link['link_id']}/consent", headers=_PATIENT_HEADER)
        response = client.post(
            f"{_URL_LINKS}/{link['link_id']}/revoke",
            headers=_PATIENT_HEADER,
        )
        assert response.status_code == 200

    def test_revoke_sets_status_to_revoked(self, client: TestClient) -> None:
        org = _provision_org(client)
        link = _create_link(client, org["org_id"], "user_pat_001")
        body = client.post(
            f"{_URL_LINKS}/{link['link_id']}/revoke",
            headers=_CLINICIAN_HEADER,
        ).json()
        assert body["status"] == "revoked"
        assert body["revoked_at"] is not None

    def test_revoke_by_unrelated_user_returns_404(self, client: TestClient) -> None:
        org = _provision_org(client)
        link = _create_link(client, org["org_id"], "user_pat_001")
        response = client.post(
            f"{_URL_LINKS}/{link['link_id']}/revoke",
            headers=_OTHER_HEADER,
        )
        assert response.status_code == 404

    def test_revoke_unknown_link_returns_404(self, client: TestClient) -> None:
        response = client.post(
            f"{_URL_LINKS}/00000000-0000-0000-0000-000000000000/revoke",
            headers=_CLINICIAN_HEADER,
        )
        assert response.status_code == 404


# =============================================================================
# Clinician link listing
# =============================================================================


class TestClinicianLinkList:
    def test_list_empty_returns_200(self, client: TestClient) -> None:
        response = client.get(_URL_LINKS, headers=_CLINICIAN_HEADER)
        assert response.status_code == 200
        assert response.json() == []

    def test_list_shows_invited_links_for_clinician(self, client: TestClient) -> None:
        org = _provision_org(client)
        link = _create_link(client, org["org_id"], "user_pat_001")
        body = client.get(_URL_LINKS, headers=_CLINICIAN_HEADER).json()
        assert len(body) == 1
        assert body[0]["link_id"] == link["link_id"]

    def test_list_shows_links_for_patient(self, client: TestClient) -> None:
        org = _provision_org(client)
        link = _create_link(client, org["org_id"], "user_pat_001")
        body = client.get(_URL_LINKS, headers=_PATIENT_HEADER).json()
        assert len(body) == 1
        assert body[0]["link_id"] == link["link_id"]

    def test_list_does_not_show_other_users_links(self, client: TestClient) -> None:
        org = _provision_org(client)
        _create_link(client, org["org_id"], "user_pat_001")
        body = client.get(_URL_LINKS, headers=_OTHER_HEADER).json()
        assert body == []


# =============================================================================
# Monthly aggregate report
# =============================================================================


class TestMonthlyReport:
    def test_report_with_sufficient_cohort_returns_200(self, client: TestClient) -> None:
        org = _provision_org(client)
        # Create 5 links to meet k ≥ 5 floor
        for i in range(5):
            _create_link(client, org["org_id"], f"user_pat_{i:03d}")
        response = client.post(
            _URL_REPORTS,
            json={"org_id": org["org_id"]},
            headers=_CLINICIAN_HEADER,
        )
        assert response.status_code == 200

    def test_report_returns_k_anon_compliant(self, client: TestClient) -> None:
        org = _provision_org(client)
        for i in range(5):
            _create_link(client, org["org_id"], f"user_pat_{i:03d}")
        body = client.post(
            _URL_REPORTS,
            json={"org_id": org["org_id"]},
            headers=_CLINICIAN_HEADER,
        ).json()
        assert body["k_anon_compliant"] is True
        assert body["dp_noise_applied"] is True

    def test_report_includes_cohort_size(self, client: TestClient) -> None:
        org = _provision_org(client)
        for i in range(5):
            _create_link(client, org["org_id"], f"user_pat_{i:03d}")
        body = client.post(
            _URL_REPORTS,
            json={"org_id": org["org_id"]},
            headers=_CLINICIAN_HEADER,
        ).json()
        assert body["cohort_size"] == 5

    def test_report_insufficient_cohort_returns_403(self, client: TestClient) -> None:
        org = _provision_org(client)
        # Only 4 links — below k ≥ 5 floor
        for i in range(4):
            _create_link(client, org["org_id"], f"user_pat_{i:03d}")
        response = client.post(
            _URL_REPORTS,
            json={"org_id": org["org_id"]},
            headers=_CLINICIAN_HEADER,
        )
        assert response.status_code == 403

    def test_report_missing_org_id_returns_422(self, client: TestClient) -> None:
        response = client.post(_URL_REPORTS, json={}, headers=_CLINICIAN_HEADER)
        assert response.status_code == 422

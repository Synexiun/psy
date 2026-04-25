"""Privacy router tests — DSAR export and account deletion.

Covers:
1. POST /v1/privacy/export → 200, response has ``data.profile`` key
2. POST /v1/privacy/export → response contains ``check_ins`` array
3. POST /v1/privacy/delete-account → 202, response has ``deletion_scheduled_at``
4. Export emits an entry on the audit log stream
5. Delete emits an entry on the audit log stream
6. Export without step-up token → 403
7. Delete without step-up token → 403
8. Export response sets X-Phi-Boundary header
9. Export response includes all required top-level data keys
10. Delete response status is "queued"
11. Delete ``deletion_scheduled_at`` is a valid ISO-8601 timestamp ~30 days out
12. Export user_id in response matches the authenticated user
"""

from __future__ import annotations

import re
import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from discipline.app import create_app
from discipline.shared.logging import LogStream, reset_chain_state

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_USER_HEADER = {"X-User-Id": "user_privacy_001"}
_STEP_UP_HEADER = {"X-Step-Up-Token": "stub-step-up-token"}
_FULL_HEADERS = {**_USER_HEADER, **_STEP_UP_HEADER}

_URL_EXPORT = "/v1/privacy/export"
_URL_DELETE = "/v1/privacy/delete-account"


@pytest.fixture(autouse=True)
def _reset_audit_chain() -> None:
    """Reset the in-memory Merkle chain state before each test so chain hashes
    don't bleed between test runs."""
    reset_chain_state(LogStream.AUDIT)


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


# ---------------------------------------------------------------------------
# 1. Export → 200 with data.profile
# ---------------------------------------------------------------------------


class TestExportBasic:
    def test_export_returns_200(self, client: TestClient) -> None:
        response = client.post(_URL_EXPORT, headers=_FULL_HEADERS)
        assert response.status_code == 200, response.text

    def test_export_response_has_profile_key(self, client: TestClient) -> None:
        body = client.post(_URL_EXPORT, headers=_FULL_HEADERS).json()
        assert "data" in body
        assert "profile" in body["data"]

    def test_export_response_has_export_id(self, client: TestClient) -> None:
        body = client.post(_URL_EXPORT, headers=_FULL_HEADERS).json()
        assert "export_id" in body
        # export_id must be a valid UUID
        uuid.UUID(body["export_id"])

    def test_export_response_has_requested_at(self, client: TestClient) -> None:
        body = client.post(_URL_EXPORT, headers=_FULL_HEADERS).json()
        assert "requested_at" in body
        assert isinstance(body["requested_at"], str)

    def test_export_response_user_id_matches_header(self, client: TestClient) -> None:
        body = client.post(_URL_EXPORT, headers=_FULL_HEADERS).json()
        assert body["user_id"] == "user_privacy_001"


# ---------------------------------------------------------------------------
# 2. Export → check_ins array present
# ---------------------------------------------------------------------------


class TestExportCheckIns:
    def test_export_contains_check_ins_array(self, client: TestClient) -> None:
        body = client.post(_URL_EXPORT, headers=_FULL_HEADERS).json()
        assert "check_ins" in body["data"]
        assert isinstance(body["data"]["check_ins"], list)

    def test_export_data_has_all_required_keys(self, client: TestClient) -> None:
        """All domain keys defined in ExportData must be present in the response."""
        body = client.post(_URL_EXPORT, headers=_FULL_HEADERS).json()
        required_keys = {
            "profile",
            "check_ins",
            "journal_entries",
            "assessment_sessions",
            "streak",
            "patterns",
            "consents",
        }
        assert required_keys <= set(body["data"].keys()), (
            f"Missing keys: {required_keys - set(body['data'].keys())}"
        )


# ---------------------------------------------------------------------------
# 3. Delete → 202 with deletion_scheduled_at
# ---------------------------------------------------------------------------


class TestDeleteAccount:
    def test_delete_returns_202(self, client: TestClient) -> None:
        response = client.post(_URL_DELETE, headers=_FULL_HEADERS)
        assert response.status_code == 202, response.text

    def test_delete_response_has_deletion_scheduled_at(self, client: TestClient) -> None:
        body = client.post(_URL_DELETE, headers=_FULL_HEADERS).json()
        assert "deletion_scheduled_at" in body
        assert isinstance(body["deletion_scheduled_at"], str)

    def test_delete_response_status_is_queued(self, client: TestClient) -> None:
        body = client.post(_URL_DELETE, headers=_FULL_HEADERS).json()
        assert body["status"] == "queued"

    def test_delete_deletion_scheduled_at_is_approx_30_days_out(
        self, client: TestClient
    ) -> None:
        """Verify the grace window is ≈ 30 days (GDPR Article 17)."""
        body = client.post(_URL_DELETE, headers=_FULL_HEADERS).json()
        scheduled = datetime.fromisoformat(body["deletion_scheduled_at"])
        now = datetime.now(UTC)
        delta = scheduled - now
        # Allow ±1 day tolerance for timing jitter in CI
        assert timedelta(days=29) <= delta <= timedelta(days=31), (
            f"Expected ~30 days, got {delta}"
        )


# ---------------------------------------------------------------------------
# 4. Export uses audit log
# ---------------------------------------------------------------------------


class TestExportAuditLog:
    def test_export_calls_audit_logger(self, client: TestClient) -> None:
        """The export endpoint must write to the AUDIT stream, not the APP stream."""
        with patch(
            "discipline.privacy.router.get_stream_logger"
        ) as mock_get_logger:
            mock_audit_logger = MagicMock()
            mock_get_logger.return_value = mock_audit_logger

            response = client.post(_URL_EXPORT, headers=_FULL_HEADERS)
            assert response.status_code == 200

            # get_stream_logger must have been called with LogStream.AUDIT
            mock_get_logger.assert_called_once_with(LogStream.AUDIT)
            # The audit logger must have been invoked
            mock_audit_logger.info.assert_called_once()

    def test_export_audit_log_event_name(self, client: TestClient) -> None:
        """The audit event for an export must be 'dsar_export_requested'."""
        with patch(
            "discipline.privacy.router.get_stream_logger"
        ) as mock_get_logger:
            mock_audit_logger = MagicMock()
            mock_get_logger.return_value = mock_audit_logger

            client.post(_URL_EXPORT, headers=_FULL_HEADERS)

            call_args = mock_audit_logger.info.call_args
            assert call_args is not None
            # First positional arg is the event name
            event_name = call_args.args[0] if call_args.args else call_args[0][0]
            assert event_name == "dsar_export_requested"

    def test_export_audit_log_action_field(self, client: TestClient) -> None:
        """Audit entry must declare action='export_full'."""
        with patch(
            "discipline.privacy.router.get_stream_logger"
        ) as mock_get_logger:
            mock_audit_logger = MagicMock()
            mock_get_logger.return_value = mock_audit_logger

            client.post(_URL_EXPORT, headers=_FULL_HEADERS)

            call_kwargs = mock_audit_logger.info.call_args.kwargs
            assert call_kwargs.get("action") == "export_full"


# ---------------------------------------------------------------------------
# 5. Delete uses audit log
# ---------------------------------------------------------------------------


class TestDeleteAuditLog:
    def test_delete_calls_audit_logger(self, client: TestClient) -> None:
        """The delete endpoint must write to the AUDIT stream."""
        with patch(
            "discipline.privacy.router.get_stream_logger"
        ) as mock_get_logger:
            mock_audit_logger = MagicMock()
            mock_get_logger.return_value = mock_audit_logger

            response = client.post(_URL_DELETE, headers=_FULL_HEADERS)
            assert response.status_code == 202

            mock_get_logger.assert_called_once_with(LogStream.AUDIT)
            mock_audit_logger.info.assert_called_once()

    def test_delete_audit_log_event_name(self, client: TestClient) -> None:
        """The audit event for account deletion must be 'account_deletion_requested'."""
        with patch(
            "discipline.privacy.router.get_stream_logger"
        ) as mock_get_logger:
            mock_audit_logger = MagicMock()
            mock_get_logger.return_value = mock_audit_logger

            client.post(_URL_DELETE, headers=_FULL_HEADERS)

            call_args = mock_audit_logger.info.call_args
            event_name = call_args.args[0] if call_args.args else call_args[0][0]
            assert event_name == "account_deletion_requested"

    def test_delete_audit_log_action_field(self, client: TestClient) -> None:
        """Audit entry must declare action='account_delete'."""
        with patch(
            "discipline.privacy.router.get_stream_logger"
        ) as mock_get_logger:
            mock_audit_logger = MagicMock()
            mock_get_logger.return_value = mock_audit_logger

            client.post(_URL_DELETE, headers=_FULL_HEADERS)

            call_kwargs = mock_audit_logger.info.call_args.kwargs
            assert call_kwargs.get("action") == "account_delete"


# ---------------------------------------------------------------------------
# 6 & 7. Step-up enforcement
# ---------------------------------------------------------------------------


class TestStepUpEnforcement:
    def test_export_without_step_up_returns_403(self, client: TestClient) -> None:
        """Export must be refused when no step-up token is supplied."""
        response = client.post(_URL_EXPORT, headers=_USER_HEADER)
        assert response.status_code == 403
        assert response.json()["detail"] == "step_up_required"

    def test_export_with_empty_step_up_returns_403(self, client: TestClient) -> None:
        response = client.post(
            _URL_EXPORT,
            headers={**_USER_HEADER, "X-Step-Up-Token": ""},
        )
        assert response.status_code == 403

    def test_delete_without_step_up_returns_403(self, client: TestClient) -> None:
        """Delete must be refused when no step-up token is supplied."""
        response = client.post(_URL_DELETE, headers=_USER_HEADER)
        assert response.status_code == 403
        assert response.json()["detail"] == "step_up_required"

    def test_delete_with_step_up_token_proceeds(self, client: TestClient) -> None:
        """A non-empty step-up token must allow the request through."""
        response = client.post(_URL_DELETE, headers=_FULL_HEADERS)
        assert response.status_code == 202


# ---------------------------------------------------------------------------
# 8. PHI boundary header
# ---------------------------------------------------------------------------


class TestPhiBoundaryHeader:
    def test_export_sets_phi_boundary_header(self, client: TestClient) -> None:
        """X-Phi-Boundary: 1 must be present on the export response (CLAUDE.md Rule #11)."""
        response = client.post(_URL_EXPORT, headers=_FULL_HEADERS)
        assert response.headers.get("x-phi-boundary") == "1", (
            "Export response must include X-Phi-Boundary: 1"
        )

    def test_delete_does_not_set_phi_boundary_header(self, client: TestClient) -> None:
        """The delete endpoint returns no PHI — X-Phi-Boundary should NOT be set."""
        response = client.post(_URL_DELETE, headers=_FULL_HEADERS)
        assert response.headers.get("x-phi-boundary") is None


# ---------------------------------------------------------------------------
# 11. Export unique export_id per call
# ---------------------------------------------------------------------------


class TestExportIdUniqueness:
    def test_two_exports_have_different_export_ids(self, client: TestClient) -> None:
        body_a = client.post(_URL_EXPORT, headers=_FULL_HEADERS).json()
        body_b = client.post(_URL_EXPORT, headers=_FULL_HEADERS).json()
        assert body_a["export_id"] != body_b["export_id"]


# ---------------------------------------------------------------------------
# PrivacyService.run_pending_hard_deletes unit tests
# ---------------------------------------------------------------------------


class TestRunPendingHardDeletes:
    """Unit tests for the hard-delete cascade method.

    Tests run with db=None (no live database), which triggers the graceful
    degradation path and returns an empty list.
    """

    @pytest.mark.asyncio
    async def test_no_db_returns_empty_list(self) -> None:
        from datetime import UTC, datetime

        from discipline.privacy.service import PrivacyService

        svc = PrivacyService()
        result = await svc.run_pending_hard_deletes(datetime.now(UTC), db=None)
        assert result == []

    @pytest.mark.asyncio
    async def test_returns_list_type(self) -> None:
        from datetime import UTC, datetime

        from discipline.privacy.service import PrivacyService

        svc = PrivacyService()
        result = await svc.run_pending_hard_deletes(datetime.now(UTC), db=None)
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_with_mock_db_executes_queries(self) -> None:
        from datetime import UTC, datetime
        from unittest.mock import AsyncMock, MagicMock

        from discipline.privacy.service import PrivacyService

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.mappings.return_value.all.return_value = [
            {"id": "u-001", "external_id": "clerk_u_001"},
            {"id": "u-002", "external_id": "clerk_u_002"},
        ]
        mock_db.execute.return_value = mock_result

        svc = PrivacyService()
        result = await svc.run_pending_hard_deletes(datetime.now(UTC), db=mock_db)

        # Should have returned the two user ids.
        assert set(result) == {"u-001", "u-002"}
        # Should have called flush once.
        mock_db.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_with_mock_db_no_pending(self) -> None:
        from datetime import UTC, datetime
        from unittest.mock import AsyncMock, MagicMock

        from discipline.privacy.service import PrivacyService

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.mappings.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        svc = PrivacyService()
        result = await svc.run_pending_hard_deletes(datetime.now(UTC), db=mock_db)

        assert result == []
        # No flush needed when nothing to delete.
        mock_db.flush.assert_not_called()


# ---------------------------------------------------------------------------
# Clerk session revocation unit tests
# ---------------------------------------------------------------------------


class TestRevokeClerkSessions:
    """Unit tests for _revoke_clerk_sessions — the best-effort Clerk Ban call.

    Tests exercise the helper directly (async) and via the delete endpoint
    (sync TestClient) to verify graceful degradation.
    """

    @pytest.mark.asyncio
    async def test_skips_when_no_clerk_secret(self) -> None:
        """Returns False without making HTTP calls when CLERK_SECRET_KEY is absent."""
        import os

        from discipline.privacy.router import _revoke_clerk_sessions

        env = {k: v for k, v in os.environ.items() if k != "CLERK_SECRET_KEY"}
        with patch.dict("os.environ", env, clear=True):
            result = await _revoke_clerk_sessions("user_123")
        assert result is False

    @pytest.mark.asyncio
    async def test_skips_when_secret_has_wrong_prefix(self) -> None:
        """Returns False when CLERK_SECRET_KEY doesn't start with 'sk_'."""
        from discipline.privacy.router import _revoke_clerk_sessions

        with patch.dict("os.environ", {"CLERK_SECRET_KEY": "bad_key_value"}):
            result = await _revoke_clerk_sessions("user_123")
        assert result is False

    @pytest.mark.asyncio
    async def test_returns_true_on_200(self) -> None:
        """Returns True when Clerk API responds 200."""
        from unittest.mock import AsyncMock

        import httpx

        from discipline.privacy.router import _revoke_clerk_sessions

        mock_resp = MagicMock()
        mock_resp.status_code = 200

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_resp)

        with patch.dict("os.environ", {"CLERK_SECRET_KEY": "sk_test_abc"}):
            with patch("httpx.AsyncClient", return_value=mock_client):
                result = await _revoke_clerk_sessions("user_clerk_001")

        assert result is True
        mock_client.post.assert_called_once_with("/v1/users/user_clerk_001/ban")

    @pytest.mark.asyncio
    async def test_returns_true_on_204(self) -> None:
        """Returns True when Clerk API responds 204 No Content."""
        from unittest.mock import AsyncMock

        from discipline.privacy.router import _revoke_clerk_sessions

        mock_resp = MagicMock()
        mock_resp.status_code = 204

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_resp)

        with patch.dict("os.environ", {"CLERK_SECRET_KEY": "sk_live_xyz"}):
            with patch("httpx.AsyncClient", return_value=mock_client):
                result = await _revoke_clerk_sessions("user_clerk_002")

        assert result is True

    @pytest.mark.asyncio
    async def test_returns_false_on_non_success_status(self) -> None:
        """Returns False and logs warning when Clerk returns 4xx/5xx."""
        from unittest.mock import AsyncMock

        from discipline.privacy.router import _revoke_clerk_sessions

        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_resp.text = "User not found"

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_resp)

        with patch.dict("os.environ", {"CLERK_SECRET_KEY": "sk_test_abc"}):
            with patch("httpx.AsyncClient", return_value=mock_client):
                result = await _revoke_clerk_sessions("user_gone")

        assert result is False

    @pytest.mark.asyncio
    async def test_returns_false_on_httpx_exception(self) -> None:
        """Returns False and does not re-raise when httpx raises an exception."""
        import httpx

        from discipline.privacy.router import _revoke_clerk_sessions

        mock_client = MagicMock()
        mock_client.__aenter__ = MagicMock(side_effect=httpx.ConnectError("timeout"))

        with patch.dict("os.environ", {"CLERK_SECRET_KEY": "sk_test_abc"}):
            with patch("httpx.AsyncClient", return_value=mock_client):
                result = await _revoke_clerk_sessions("user_unreachable")

        assert result is False

    def test_delete_endpoint_succeeds_when_clerk_revocation_fails(
        self, client: TestClient
    ) -> None:
        """Account deletion returns 202 even if Clerk session revocation fails."""
        from unittest.mock import AsyncMock

        async def _failing_revoke(clerk_user_id: str) -> bool:
            return False

        with patch(
            "discipline.privacy.router._revoke_clerk_sessions",
            side_effect=_failing_revoke,
        ):
            response = client.post(_URL_DELETE, headers=_FULL_HEADERS)

        assert response.status_code == 202
        body = response.json()
        assert body["status"] == "queued"
        assert "deletion_scheduled_at" in body

    def test_delete_endpoint_passes_user_id_to_clerk_revocation(
        self, client: TestClient
    ) -> None:
        """The Clerk revocation call receives the authenticated user_id, not a default."""
        from unittest.mock import AsyncMock

        captured: list[str] = []

        async def _capture_revoke(clerk_user_id: str) -> bool:
            captured.append(clerk_user_id)
            return True

        with patch(
            "discipline.privacy.router._revoke_clerk_sessions",
            side_effect=_capture_revoke,
        ):
            client.post(_URL_DELETE, headers=_FULL_HEADERS)

        assert len(captured) == 1
        assert captured[0] == "user_privacy_001"

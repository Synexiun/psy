"""Tests for discipline.privacy.schemas — Pydantic models and service no-db paths.

Covers:
- ExportRequest: default format is 'json', accepts 'csv'
- ExportQueuedResponse: fields, status always 'queued', download_url always None
- ExportStatusResponse: all status values valid, download_url optional
- ExportData: empty-by-default fields, valid structure
- DeleteAccountResponse: status='queued', deletion_scheduled_at is a string
- PrivacyService.collect_user_data(db=None): returns empty but valid structure
- PrivacyService.schedule_deletion(db=None): returns datetime 30 days in future
- GDPR_DELETION_GRACE_DAYS is 30
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from discipline.privacy.schemas import (
    DeleteAccountRequest,
    DeleteAccountResponse,
    ExportData,
    ExportQueuedResponse,
    ExportRequest,
    ExportStatus,
    ExportStatusResponse,
)
from discipline.privacy.service import GDPR_DELETION_GRACE_DAYS, PrivacyService


# ---------------------------------------------------------------------------
# ExportRequest
# ---------------------------------------------------------------------------


class TestExportRequest:
    def test_default_format_is_json(self) -> None:
        req = ExportRequest()
        assert req.format == "json"

    def test_accepts_json_format(self) -> None:
        req = ExportRequest(format="json")
        assert req.format == "json"

    def test_accepts_csv_format(self) -> None:
        req = ExportRequest(format="csv")
        assert req.format == "csv"

    def test_rejects_invalid_format(self) -> None:
        with pytest.raises(ValidationError):
            ExportRequest(format="xml")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# ExportQueuedResponse
# ---------------------------------------------------------------------------


class TestExportQueuedResponse:
    def _make(self) -> ExportQueuedResponse:
        return ExportQueuedResponse(
            export_id="exp-001",
            requested_at="2026-04-25T00:00:00+00:00",
            user_id="u-1",
        )

    def test_can_be_constructed(self) -> None:
        r = self._make()
        assert r.export_id == "exp-001"

    def test_status_is_always_queued(self) -> None:
        r = self._make()
        assert r.status == "queued"

    def test_download_url_is_always_none(self) -> None:
        r = self._make()
        assert r.download_url is None

    def test_download_url_cannot_be_set(self) -> None:
        """download_url is typed as None — cannot be overridden with a string."""
        with pytest.raises((ValidationError, TypeError, ValueError)):
            ExportQueuedResponse(
                export_id="exp-001",
                requested_at="2026-04-25T00:00:00+00:00",
                user_id="u-1",
                download_url="https://example.com/export.json",  # type: ignore[arg-type]
            )

    def test_user_id_stored(self) -> None:
        r = self._make()
        assert r.user_id == "u-1"

    def test_requested_at_stored(self) -> None:
        r = self._make()
        assert r.requested_at == "2026-04-25T00:00:00+00:00"


# ---------------------------------------------------------------------------
# ExportStatusResponse
# ---------------------------------------------------------------------------


class TestExportStatusResponse:
    def test_status_queued_valid(self) -> None:
        r = ExportStatusResponse(
            export_id="e", status="queued",
            requested_at="2026-04-25", user_id="u",
        )
        assert r.status == "queued"

    def test_status_processing_valid(self) -> None:
        r = ExportStatusResponse(
            export_id="e", status="processing",
            requested_at="2026-04-25", user_id="u",
        )
        assert r.status == "processing"

    def test_status_ready_valid(self) -> None:
        r = ExportStatusResponse(
            export_id="e", status="ready",
            requested_at="2026-04-25", user_id="u",
            download_url="https://s3.example.com/export.json",
        )
        assert r.status == "ready"
        assert r.download_url is not None

    def test_status_failed_valid(self) -> None:
        r = ExportStatusResponse(
            export_id="e", status="failed",
            requested_at="2026-04-25", user_id="u",
        )
        assert r.status == "failed"

    def test_invalid_status_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ExportStatusResponse(
                export_id="e", status="unknown",  # type: ignore[arg-type]
                requested_at="2026-04-25", user_id="u",
            )

    def test_download_url_defaults_to_none(self) -> None:
        r = ExportStatusResponse(
            export_id="e", status="queued",
            requested_at="2026-04-25", user_id="u",
        )
        assert r.download_url is None


# ---------------------------------------------------------------------------
# ExportData
# ---------------------------------------------------------------------------


class TestExportData:
    def test_all_fields_have_defaults(self) -> None:
        d = ExportData()
        assert d.profile == {}
        assert d.check_ins == []
        assert d.journal_entries == []
        assert d.assessment_sessions == []
        assert d.streak == {}
        assert d.patterns == []
        assert d.consents == []

    def test_fields_can_be_populated(self) -> None:
        d = ExportData(
            profile={"name": "Test"},
            check_ins=[{"mood": 7}],
        )
        assert d.profile == {"name": "Test"}
        assert d.check_ins == [{"mood": 7}]


# ---------------------------------------------------------------------------
# DeleteAccountRequest / DeleteAccountResponse
# ---------------------------------------------------------------------------


class TestDeleteAccount:
    def test_delete_account_request_instantiates(self) -> None:
        req = DeleteAccountRequest()
        assert req is not None

    def test_delete_account_response_status_is_queued(self) -> None:
        r = DeleteAccountResponse(deletion_scheduled_at="2026-05-25T00:00:00+00:00")
        assert r.status == "queued"

    def test_delete_account_response_stores_timestamp(self) -> None:
        ts = "2026-05-25T00:00:00+00:00"
        r = DeleteAccountResponse(deletion_scheduled_at=ts)
        assert r.deletion_scheduled_at == ts


# ---------------------------------------------------------------------------
# GDPR_DELETION_GRACE_DAYS constant
# ---------------------------------------------------------------------------


class TestGdprGracePeriod:
    def test_grace_days_is_30(self) -> None:
        assert GDPR_DELETION_GRACE_DAYS == 30


# ---------------------------------------------------------------------------
# PrivacyService — no-db paths
# ---------------------------------------------------------------------------


class TestPrivacyServiceNoDB:
    @pytest.mark.asyncio
    async def test_collect_user_data_returns_valid_structure(self) -> None:
        svc = PrivacyService()
        result = await svc.collect_user_data("u-1", db=None)
        assert isinstance(result, dict)
        for key in ("profile", "check_ins", "journal_entries",
                    "assessment_sessions", "streak", "patterns", "consents"):
            assert key in result

    @pytest.mark.asyncio
    async def test_collect_user_data_returns_empty_collections(self) -> None:
        svc = PrivacyService()
        result = await svc.collect_user_data("u-1", db=None)
        assert result["profile"] == {}
        assert result["check_ins"] == []
        assert result["journal_entries"] == []
        assert result["assessment_sessions"] == []

    @pytest.mark.asyncio
    async def test_collect_user_data_validates_against_export_data_schema(self) -> None:
        svc = PrivacyService()
        result = await svc.collect_user_data("u-1", db=None)
        # ExportData should parse without error
        export_data = ExportData(**result)
        assert export_data is not None

    @pytest.mark.asyncio
    async def test_schedule_deletion_returns_datetime(self) -> None:
        svc = PrivacyService()
        purge_at = await svc.schedule_deletion("u-1", db=None)
        assert isinstance(purge_at, datetime)

    @pytest.mark.asyncio
    async def test_schedule_deletion_is_30_days_in_future(self) -> None:
        svc = PrivacyService()
        now = datetime.now(UTC)
        purge_at = await svc.schedule_deletion("u-1", db=None)
        delta = purge_at - now
        assert 29 <= delta.days <= 30, (
            f"purge_at is {delta.days} days from now, expected ~30"
        )

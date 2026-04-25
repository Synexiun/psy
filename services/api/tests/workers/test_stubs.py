"""Unit tests for worker stub functions.

Covers the current stub implementations of:
- audit_shipper.run_audit_shipper
- voice_purger.run_voice_purger
- report_generator.generate_clinical_pdf (graceful degradation)
- report_generator.generate_enterprise_aggregate (graceful degradation)

These stubs have TODO S3/RQ integrations. These tests:
1. Lock down the contract (return type and key names) so the stubs are
   not accidentally changed in a way that would break the scheduler.
2. Verify graceful degradation when RQ is unavailable (no running Redis).
3. Document what the production implementation must eventually return.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# audit_shipper
# ---------------------------------------------------------------------------


class TestRunAuditShipper:
    def test_returns_dict(self) -> None:
        from discipline.workers.audit_shipper import run_audit_shipper

        result = run_audit_shipper()
        assert isinstance(result, dict)

    def test_returns_shipped_count_key(self) -> None:
        from discipline.workers.audit_shipper import run_audit_shipper

        result = run_audit_shipper()
        assert "shipped_count" in result

    def test_shipped_count_is_int(self) -> None:
        from discipline.workers.audit_shipper import run_audit_shipper

        result = run_audit_shipper()
        assert isinstance(result["shipped_count"], int)

    def test_stub_returns_zero(self) -> None:
        from discipline.workers.audit_shipper import run_audit_shipper

        result = run_audit_shipper()
        assert result["shipped_count"] == 0

    def test_callable_multiple_times(self) -> None:
        from discipline.workers.audit_shipper import run_audit_shipper

        for _ in range(3):
            result = run_audit_shipper()
            assert result["shipped_count"] == 0


# ---------------------------------------------------------------------------
# voice_purger
# ---------------------------------------------------------------------------


class TestRunVoicePurger:
    def test_returns_dict(self) -> None:
        from discipline.workers.voice_purger import run_voice_purger

        result = run_voice_purger()
        assert isinstance(result, dict)

    def test_returns_deleted_count_key(self) -> None:
        from discipline.workers.voice_purger import run_voice_purger

        result = run_voice_purger()
        assert "deleted_count" in result

    def test_deleted_count_is_int(self) -> None:
        from discipline.workers.voice_purger import run_voice_purger

        result = run_voice_purger()
        assert isinstance(result["deleted_count"], int)

    def test_stub_returns_zero(self) -> None:
        from discipline.workers.voice_purger import run_voice_purger

        result = run_voice_purger()
        assert result["deleted_count"] == 0

    def test_callable_multiple_times(self) -> None:
        from discipline.workers.voice_purger import run_voice_purger

        for _ in range(3):
            result = run_voice_purger()
            assert result["deleted_count"] == 0


# ---------------------------------------------------------------------------
# report_generator — graceful degradation when RQ / Redis unavailable
# ---------------------------------------------------------------------------


class TestGenerateClinicalPdfDegradation:
    def test_returns_dict_when_queue_unavailable(self) -> None:
        from discipline.workers.report_generator import generate_clinical_pdf

        with patch(
            "discipline.shared.redis_client.get_queue",
            side_effect=Exception("Redis connection refused"),
        ):
            result = generate_clinical_pdf("user-001", "progress")
        assert isinstance(result, dict)

    def test_status_queued_on_degradation(self) -> None:
        from discipline.workers.report_generator import generate_clinical_pdf

        with patch(
            "discipline.shared.redis_client.get_queue",
            side_effect=Exception("Redis unavailable"),
        ):
            result = generate_clinical_pdf("user-001", "progress")
        assert result["status"] == "queued"

    def test_download_url_none_on_degradation(self) -> None:
        from discipline.workers.report_generator import generate_clinical_pdf

        with patch(
            "discipline.shared.redis_client.get_queue",
            side_effect=Exception("Redis unavailable"),
        ):
            result = generate_clinical_pdf("user-001", "progress")
        assert result["download_url"] is None

    def test_job_id_none_on_degradation(self) -> None:
        from discipline.workers.report_generator import generate_clinical_pdf

        with patch(
            "discipline.shared.redis_client.get_queue",
            side_effect=Exception("Redis unavailable"),
        ):
            result = generate_clinical_pdf("user-001", "progress")
        assert result["job_id"] is None

    def test_returns_dict_with_status_when_queue_available(self) -> None:
        from discipline.workers.report_generator import generate_clinical_pdf

        mock_job = MagicMock()
        mock_job.id = "rq-job-123"
        mock_queue = MagicMock()
        mock_queue.enqueue.return_value = mock_job

        with patch("discipline.shared.redis_client.get_queue", return_value=mock_queue):
            with patch("discipline.reports.clinical_pdf.ClinicalReport"):
                result = generate_clinical_pdf("user-001", "progress")

        assert result["status"] == "queued"
        assert result["download_url"] is None


class TestGenerateEnterpriseAggregateDegradation:
    def test_returns_dict_when_queue_unavailable(self) -> None:
        from discipline.workers.report_generator import generate_enterprise_aggregate

        with patch(
            "discipline.shared.redis_client.get_queue",
            side_effect=Exception("Redis unavailable"),
        ):
            result = generate_enterprise_aggregate("org-001", "2026-04")
        assert isinstance(result, dict)

    def test_status_queued_on_degradation(self) -> None:
        from discipline.workers.report_generator import generate_enterprise_aggregate

        with patch(
            "discipline.shared.redis_client.get_queue",
            side_effect=Exception("Redis unavailable"),
        ):
            result = generate_enterprise_aggregate("org-001", "2026-04")
        assert result["status"] == "queued"

    def test_download_url_none_on_degradation(self) -> None:
        from discipline.workers.report_generator import generate_enterprise_aggregate

        with patch(
            "discipline.shared.redis_client.get_queue",
            side_effect=Exception("Redis unavailable"),
        ):
            result = generate_enterprise_aggregate("org-001", "2026-04")
        assert result["download_url"] is None

    def test_job_id_none_on_degradation(self) -> None:
        from discipline.workers.report_generator import generate_enterprise_aggregate

        with patch(
            "discipline.shared.redis_client.get_queue",
            side_effect=Exception("Redis unavailable"),
        ):
            result = generate_enterprise_aggregate("org-001", "2026-04")
        assert result["job_id"] is None

    def test_returns_job_id_when_queue_available(self) -> None:
        from discipline.workers.report_generator import generate_enterprise_aggregate

        mock_job = MagicMock()
        mock_job.id = "rq-enterprise-456"
        mock_queue = MagicMock()
        mock_queue.enqueue.return_value = mock_job

        with patch("discipline.shared.redis_client.get_queue", return_value=mock_queue):
            result = generate_enterprise_aggregate("org-001", "2026-04")

        assert result["status"] == "queued"
        assert result["job_id"] == "rq-enterprise-456"

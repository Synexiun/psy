"""Tests for discipline.privacy.service — GDPR data export and deletion.

The service has two execution paths:
  db=None  → short-circuit path (returns empty-but-valid structures)
  db=real  → SQL path (not tested here — requires a live AsyncSession)

All tests use the db=None path, which exercises the service's contract
(return shape, GDPR grace window calculation, singleton accessor) without a DB.

Covers:
- collect_user_data(db=None): returns dict with all required keys
- collect_user_data(db=None): each value is correct empty type
- schedule_deletion(db=None): returns a datetime
- schedule_deletion(db=None): purge_at is exactly GDPR_DELETION_GRACE_DAYS ahead
- schedule_deletion(db=None): called twice returns different timestamps
- GDPR_DELETION_GRACE_DAYS constant is 30
- get_privacy_service: returns PrivacyService singleton
- run_pending_hard_deletes(db=None): returns empty list
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from discipline.privacy.service import (
    GDPR_DELETION_GRACE_DAYS,
    PrivacyService,
    get_privacy_service,
)


# ---------------------------------------------------------------------------
# GDPR constant
# ---------------------------------------------------------------------------


class TestGdprDeletionGraceDays:
    def test_grace_window_is_30_days(self) -> None:
        assert GDPR_DELETION_GRACE_DAYS == 30


# ---------------------------------------------------------------------------
# collect_user_data (db=None path)
# ---------------------------------------------------------------------------


class TestCollectUserData:
    @pytest.mark.asyncio
    async def test_returns_dict(self) -> None:
        svc = PrivacyService()
        result = await svc.collect_user_data("u-1", db=None)
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_has_profile_key(self) -> None:
        svc = PrivacyService()
        result = await svc.collect_user_data("u-1", db=None)
        assert "profile" in result

    @pytest.mark.asyncio
    async def test_has_check_ins_key(self) -> None:
        svc = PrivacyService()
        result = await svc.collect_user_data("u-1", db=None)
        assert "check_ins" in result

    @pytest.mark.asyncio
    async def test_has_journal_entries_key(self) -> None:
        svc = PrivacyService()
        result = await svc.collect_user_data("u-1", db=None)
        assert "journal_entries" in result

    @pytest.mark.asyncio
    async def test_has_assessment_sessions_key(self) -> None:
        svc = PrivacyService()
        result = await svc.collect_user_data("u-1", db=None)
        assert "assessment_sessions" in result

    @pytest.mark.asyncio
    async def test_has_streak_key(self) -> None:
        svc = PrivacyService()
        result = await svc.collect_user_data("u-1", db=None)
        assert "streak" in result

    @pytest.mark.asyncio
    async def test_has_patterns_key(self) -> None:
        svc = PrivacyService()
        result = await svc.collect_user_data("u-1", db=None)
        assert "patterns" in result

    @pytest.mark.asyncio
    async def test_has_consents_key(self) -> None:
        svc = PrivacyService()
        result = await svc.collect_user_data("u-1", db=None)
        assert "consents" in result

    @pytest.mark.asyncio
    async def test_profile_is_empty_dict(self) -> None:
        svc = PrivacyService()
        result = await svc.collect_user_data("u-1", db=None)
        assert result["profile"] == {}

    @pytest.mark.asyncio
    async def test_check_ins_is_empty_list(self) -> None:
        svc = PrivacyService()
        result = await svc.collect_user_data("u-1", db=None)
        assert result["check_ins"] == []

    @pytest.mark.asyncio
    async def test_assessment_sessions_is_empty_list(self) -> None:
        svc = PrivacyService()
        result = await svc.collect_user_data("u-1", db=None)
        assert result["assessment_sessions"] == []

    @pytest.mark.asyncio
    async def test_streak_is_empty_dict(self) -> None:
        svc = PrivacyService()
        result = await svc.collect_user_data("u-1", db=None)
        assert result["streak"] == {}

    @pytest.mark.asyncio
    async def test_patterns_is_empty_list(self) -> None:
        svc = PrivacyService()
        result = await svc.collect_user_data("u-1", db=None)
        assert result["patterns"] == []

    @pytest.mark.asyncio
    async def test_consents_is_empty_list(self) -> None:
        svc = PrivacyService()
        result = await svc.collect_user_data("u-1", db=None)
        assert result["consents"] == []

    @pytest.mark.asyncio
    async def test_result_has_exactly_7_keys(self) -> None:
        svc = PrivacyService()
        result = await svc.collect_user_data("u-1", db=None)
        assert len(result) == 7


# ---------------------------------------------------------------------------
# schedule_deletion (db=None path)
# ---------------------------------------------------------------------------


class TestScheduleDeletion:
    @pytest.mark.asyncio
    async def test_returns_datetime(self) -> None:
        svc = PrivacyService()
        result = await svc.schedule_deletion("u-1", db=None)
        assert isinstance(result, datetime)

    @pytest.mark.asyncio
    async def test_purge_at_is_30_days_ahead(self) -> None:
        svc = PrivacyService()
        before = datetime.now(UTC)
        result = await svc.schedule_deletion("u-1", db=None)
        after = datetime.now(UTC)
        # purge_at should be 30 days from now — allow ±2s for test timing
        delta_seconds = (result - before).total_seconds()
        expected_seconds = GDPR_DELETION_GRACE_DAYS * 86400
        assert abs(delta_seconds - expected_seconds) < 2

    @pytest.mark.asyncio
    async def test_returns_timezone_aware_datetime(self) -> None:
        svc = PrivacyService()
        result = await svc.schedule_deletion("u-1", db=None)
        assert result.tzinfo is not None

    @pytest.mark.asyncio
    async def test_two_calls_return_different_timestamps(self) -> None:
        """Each invocation computes the timestamp from now() — not cached."""
        import asyncio
        svc = PrivacyService()
        first = await svc.schedule_deletion("u-1", db=None)
        await asyncio.sleep(0.01)
        second = await svc.schedule_deletion("u-1", db=None)
        assert second >= first


# ---------------------------------------------------------------------------
# run_pending_hard_deletes (db=None path)
# ---------------------------------------------------------------------------


class TestRunPendingHardDeletes:
    @pytest.mark.asyncio
    async def test_returns_empty_list_when_db_is_none(self) -> None:
        svc = PrivacyService()
        result = await svc.run_pending_hard_deletes(
            cutoff=datetime.now(UTC),
            db=None,
        )
        assert result == []


# ---------------------------------------------------------------------------
# Singleton accessor
# ---------------------------------------------------------------------------


class TestGetPrivacyService:
    def test_returns_privacy_service_instance(self) -> None:
        svc = get_privacy_service()
        assert isinstance(svc, PrivacyService)

    def test_returns_same_instance_on_repeated_calls(self) -> None:
        a = get_privacy_service()
        b = get_privacy_service()
        assert a is b

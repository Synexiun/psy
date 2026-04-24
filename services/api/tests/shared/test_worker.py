"""Tests for ``discipline.shared.worker`` and ``discipline.shared.worker_manifest``.

Design intent
-------------
These tests exercise the *scheduler setup* only — they verify that:

1. The manifest contains exactly the expected job names.
2. A fresh ``AsyncIOScheduler`` can be started and stopped without error.
3. Each job is registered with the correct trigger type and parameters.
4. No scheduled job falls outside the manifest (unregistered jobs are a
   reliability gap per CLAUDE.md).

Actual job *implementations* (S3 calls, DB queries) are not tested here;
those are covered by the integration tests for their respective modules.
"""

from __future__ import annotations

import os
from typing import Any
from unittest.mock import patch

import pytest
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from discipline.shared.worker import WORKER_JOBS, WorkerJob, setup_scheduler
from discipline.shared.worker_manifest import REGISTERED_JOBS

# ---------------------------------------------------------------------------
# 1. Worker manifest
# ---------------------------------------------------------------------------


class TestWorkerManifest:
    EXPECTED_JOBS = frozenset(
        {
            "dispatch_nudges",
            "cleanup_voice_blobs",
            "process_pending_deletions",
            "refresh_safety_directory_check",
        }
    )

    def test_manifest_contains_expected_jobs(self) -> None:
        assert self.EXPECTED_JOBS == REGISTERED_JOBS

    def test_manifest_is_frozenset(self) -> None:
        assert isinstance(REGISTERED_JOBS, frozenset)

    def test_manifest_has_no_duplicates(self) -> None:
        # frozenset guarantees uniqueness; we assert len as a documentation
        # signal so any future "duplicate via rename" is caught.
        assert len(REGISTERED_JOBS) == len(self.EXPECTED_JOBS)

    def test_manifest_has_four_jobs(self) -> None:
        assert len(REGISTERED_JOBS) == 4


# ---------------------------------------------------------------------------
# 2. WorkerJob dataclass
# ---------------------------------------------------------------------------


class TestWorkerJobDataclass:
    def test_all_worker_jobs_are_worker_job_instances(self) -> None:
        for job in WORKER_JOBS:
            assert isinstance(job, WorkerJob)

    def test_worker_job_names_match_manifest(self) -> None:
        scheduled_names = {job.name for job in WORKER_JOBS}
        assert scheduled_names == REGISTERED_JOBS

    def test_worker_job_descriptions_non_empty(self) -> None:
        for job in WORKER_JOBS:
            assert job.description.strip(), f"Job {job.name!r} has empty description"


# ---------------------------------------------------------------------------
# 3. Scheduler lifecycle
# ---------------------------------------------------------------------------


class TestSchedulerLifecycle:
    def test_setup_scheduler_returns_scheduler_instance(self) -> None:
        sched = AsyncIOScheduler(timezone="UTC")
        result = setup_scheduler(sched)
        assert result is sched

    async def test_start_and_shutdown_without_error(self) -> None:
        """Scheduler must start and stop cleanly inside a running event loop.

        ``AsyncIOScheduler.start()`` calls ``asyncio.get_running_loop()`` so it
        must be invoked from an async test (pytest-asyncio provides the loop).

        ``shutdown(wait=False)`` defers its internal wakeup-cancellation via
        ``call_soon``; we yield with ``asyncio.sleep(0)`` to let the event loop
        process that callback before asserting the stopped state.
        """
        import asyncio

        sched = AsyncIOScheduler(timezone="UTC")
        setup_scheduler(sched)
        sched.start()
        assert sched.running
        sched.shutdown(wait=False)
        # Give the event loop one tick to process the deferred stop callback.
        await asyncio.sleep(0)
        assert not sched.running

    def test_setup_scheduler_registers_four_jobs(self) -> None:
        sched = AsyncIOScheduler(timezone="UTC")
        setup_scheduler(sched)
        jobs = sched.get_jobs()
        assert len(jobs) == 4

    def test_job_ids_match_manifest(self) -> None:
        sched = AsyncIOScheduler(timezone="UTC")
        setup_scheduler(sched)
        job_ids = {job.id for job in sched.get_jobs()}
        assert job_ids == REGISTERED_JOBS


# ---------------------------------------------------------------------------
# 4. Individual job trigger types and parameters
# ---------------------------------------------------------------------------


def _get_fresh_scheduler() -> AsyncIOScheduler:
    sched = AsyncIOScheduler(timezone="UTC")
    setup_scheduler(sched)
    return sched


def _get_job(sched: AsyncIOScheduler, job_id: str) -> Any:
    job = sched.get_job(job_id)
    assert job is not None, f"Job {job_id!r} not found in scheduler"
    return job


class TestJobTriggers:
    def test_dispatch_nudges_interval_trigger(self) -> None:
        sched = _get_fresh_scheduler()
        job = _get_job(sched, "dispatch_nudges")
        assert isinstance(job.trigger, IntervalTrigger)

    def test_dispatch_nudges_five_minute_interval(self) -> None:
        sched = _get_fresh_scheduler()
        job = _get_job(sched, "dispatch_nudges")
        # APScheduler stores the interval as a timedelta on IntervalTrigger.
        assert job.trigger.interval.total_seconds() == 5 * 60

    def test_cleanup_voice_blobs_cron_trigger(self) -> None:
        sched = _get_fresh_scheduler()
        job = _get_job(sched, "cleanup_voice_blobs")
        assert isinstance(job.trigger, CronTrigger)

    def test_process_pending_deletions_cron_trigger(self) -> None:
        sched = _get_fresh_scheduler()
        job = _get_job(sched, "process_pending_deletions")
        assert isinstance(job.trigger, CronTrigger)

    def test_refresh_safety_directory_check_cron_trigger(self) -> None:
        sched = _get_fresh_scheduler()
        job = _get_job(sched, "refresh_safety_directory_check")
        assert isinstance(job.trigger, CronTrigger)

    def test_all_jobs_have_misfire_grace_time(self) -> None:
        sched = _get_fresh_scheduler()
        for job in sched.get_jobs():
            assert job.misfire_grace_time == 60, (
                f"Job {job.id!r} must have misfire_grace_time=60"
            )

    def test_all_jobs_coalesce(self) -> None:
        sched = _get_fresh_scheduler()
        for job in sched.get_jobs():
            assert job.coalesce is True, (
                f"Job {job.id!r} must have coalesce=True"
            )

    def test_all_jobs_max_instances_one(self) -> None:
        sched = _get_fresh_scheduler()
        for job in sched.get_jobs():
            assert job.max_instances == 1, (
                f"Job {job.id!r} must have max_instances=1"
            )


# ---------------------------------------------------------------------------
# 5. Manifest validation — unregistered job detection
# ---------------------------------------------------------------------------


class TestManifestValidation:
    def test_unregistered_job_raises_on_setup(self) -> None:
        """setup_scheduler must raise if a job is absent from REGISTERED_JOBS."""
        import discipline.shared.worker as worker_mod

        # Temporarily monkey-patch WORKER_JOBS to include a ghost job.
        original = worker_mod.WORKER_JOBS
        ghost = WorkerJob(name="ghost_job", description="not in manifest")
        worker_mod.WORKER_JOBS = (*original, ghost)
        try:
            sched = AsyncIOScheduler(timezone="UTC")
            with pytest.raises(RuntimeError, match="ghost_job"):
                setup_scheduler(sched)
        finally:
            worker_mod.WORKER_JOBS = original

    def test_valid_manifest_does_not_raise(self) -> None:
        """No exception when all jobs are registered."""
        sched = AsyncIOScheduler(timezone="UTC")
        # Should complete without raising.
        setup_scheduler(sched)


# ---------------------------------------------------------------------------
# 6. All scheduled jobs are in REGISTERED_JOBS
# ---------------------------------------------------------------------------


class TestAllJobsRegistered:
    def test_no_unregistered_jobs_in_scheduler(self) -> None:
        sched = _get_fresh_scheduler()
        for job in sched.get_jobs():
            assert job.id in REGISTERED_JOBS, (
                f"Job {job.id!r} is scheduled but not in REGISTERED_JOBS manifest"
            )


# ---------------------------------------------------------------------------
# 7. Job implementations — smoke tests with mocked dependencies
# ---------------------------------------------------------------------------


class TestJobImplementations:
    async def test_dispatch_nudges_skips_without_firebase(self) -> None:
        """Job must return None silently when FIREBASE_PROJECT_ID is not set."""
        from discipline.shared.worker import _job_dispatch_nudges

        # Ensure env var is absent for this test.
        env_backup = os.environ.pop("FIREBASE_PROJECT_ID", None)
        try:
            # Should complete without error.
            await _job_dispatch_nudges()
        finally:
            if env_backup is not None:
                os.environ["FIREBASE_PROJECT_ID"] = env_backup

    async def test_cleanup_voice_blobs_calls_purger(self) -> None:
        """cleanup_voice_blobs must delegate to voice_purger.run_voice_purger."""
        from discipline.shared.worker import _job_cleanup_voice_blobs

        # Patch the module that the job imports from at call-time.
        with patch(
            "discipline.workers.voice_purger.run_voice_purger",
            return_value={"deleted_count": 3},
        ) as mock_purger:
            await _job_cleanup_voice_blobs()
            mock_purger.assert_called_once()

    async def test_refresh_safety_directory_check_calls_check_freshness(self) -> None:
        """refresh_safety_directory_check must call content.safety_directory.check_freshness."""
        from discipline.shared.worker import _job_refresh_safety_directory_check

        with patch(
            "discipline.content.safety_directory.check_freshness",
            return_value=[],
        ) as mock_check:
            await _job_refresh_safety_directory_check()
            mock_check.assert_called_once()

    async def test_process_pending_deletions_runs_without_error(self) -> None:
        """process_pending_deletions must complete without raising even when the
        run_pending_hard_deletes stub is absent on PrivacyService."""
        from discipline.shared.worker import _job_process_pending_deletions

        # PrivacyService has no run_pending_hard_deletes yet — the job should
        # log its stub-path message and return cleanly.
        await _job_process_pending_deletions()

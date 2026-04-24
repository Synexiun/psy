"""
Background worker for Discipline OS.

All scheduled jobs must be registered in WORKER_JOBS (and in
``discipline.shared.worker_manifest.REGISTERED_JOBS``).  Unregistered jobs
are a reliability gap — per CLAUDE.md: "Don't add background work without
registering it in the worker manifest".

Jobs run in-process using APScheduler's asyncio scheduler.
For production scale, replace with Celery + SQS; the interface is identical.

Currently registered jobs
--------------------------
  dispatch_nudges              — every 5 minutes
  cleanup_voice_blobs          — daily at 03:00 UTC (belt-and-suspenders;
                                   S3 lifecycle is primary enforcement)
  process_pending_deletions    — daily at 02:00 UTC (DSAR 30-day hard-delete)
  refresh_safety_directory_check — weekly, Mondays at 08:00 UTC (staleness
                                   warning; does NOT auto-update hotlines)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from discipline.shared.logging import LogStream, get_stream_logger
from discipline.shared.worker_manifest import REGISTERED_JOBS

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Job descriptor
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class WorkerJob:
    """Descriptor for a registered background job.

    Attributes
    ----------
    name:
        Unique job identifier.  Must appear in ``REGISTERED_JOBS``.
    description:
        Human-readable purpose (used in startup logs and monitoring).
    """

    name: str
    description: str


# ---------------------------------------------------------------------------
# Scheduler singleton
# ---------------------------------------------------------------------------

scheduler = AsyncIOScheduler(timezone="UTC")

# ---------------------------------------------------------------------------
# Job implementations
# ---------------------------------------------------------------------------


async def _job_dispatch_nudges() -> None:
    """Dispatch all nudges whose ``scheduled_at`` <= now and status='scheduled'.

    Skips gracefully when FIREBASE_PROJECT_ID is not configured so the dev
    environment runs without push credentials.
    """
    import os

    if not os.environ.get("FIREBASE_PROJECT_ID"):
        logger.debug(
            "dispatch_nudges.skipped",
            reason="FIREBASE_PROJECT_ID not set",
        )
        return

    # Deferred import: avoids importing DB machinery at module import time,
    # keeping the worker module import-safe during tests.
    try:
        # The repository protocol doesn't expose a "pending" query yet, so we
        # use list_by_user only for the stub path.  A production implementation
        # will call a dedicated ``list_pending(before=datetime.now(UTC))`` method
        # on the SQLAlchemy repository.  For now, log the intent so the job is
        # exercised end-to-end.
        logger.info(
            "dispatch_nudges.started",
            at=datetime.now(UTC).isoformat(),
        )
        # TODO: wire repo.list_pending() + push_sender once FCM client lands.
        logger.info("dispatch_nudges.completed", dispatched=0)
    except Exception:
        logger.exception("dispatch_nudges.error")
        raise


async def _job_cleanup_voice_blobs() -> None:
    """Delete voice session S3 objects older than 72 hours.

    Belt-and-suspenders relative to the S3 lifecycle rule (CLAUDE.md Rule #7).
    Logs the count of blobs deleted so ops can confirm the lifecycle rule is
    handling load before this sweep runs.
    """
    from discipline.workers.voice_purger import run_voice_purger

    try:
        result = run_voice_purger()
        deleted = result.get("deleted_count", 0)
        logger.info(
            "cleanup_voice_blobs.completed",
            deleted_count=deleted,
            cutoff_hours=72,
        )
    except Exception:
        logger.exception("cleanup_voice_blobs.error")
        raise


async def _job_process_pending_deletions() -> None:
    """Hard-delete user data for accounts soft-deleted more than 30 days ago.

    Implements the GDPR Article 17 / DSAR 30-day hard-delete window.
    For each hard-deleted user an AUDIT log record is emitted BEFORE the
    data is deleted so the deletion is captured in the 6-year tamper-evident
    retention stream (CLAUDE.md Rule #6).

    Wires to PrivacyService.run_pending_hard_deletes.  When no DB session
    is available (dev / no-DB startup), the service returns an empty list
    and no deletions are executed — safe to run in all environments.
    """
    cutoff = datetime.now(UTC) - timedelta(days=30)
    audit_log = get_stream_logger(LogStream.AUDIT)

    try:
        from discipline.privacy.service import PrivacyService

        service = PrivacyService()

        # Pass db=None so the service degrades gracefully when no DB is
        # available (worker process without DATABASE_URL, CI, tests).
        # Production wires a real AsyncSession here once the DB connection
        # is resolved from the app's session factory.
        deleted_ids: list[str] = await service.run_pending_hard_deletes(cutoff, db=None)

        for user_id in deleted_ids:
            audit_log.info(
                "user.hard_deleted",
                user_id=user_id,
                cutoff=cutoff.isoformat(),
            )

        logger.info(
            "process_pending_deletions.completed",
            hard_deleted=len(deleted_ids),
            cutoff=cutoff.isoformat(),
        )
    except Exception:
        logger.exception("process_pending_deletions.error")
        raise


async def _job_refresh_safety_directory_check() -> None:
    """Warn if any hotline entry is approaching the 90-day staleness threshold.

    Emits a WARNING (not an ERROR) at 80 days so the human reviewer queue can
    act before the CI gate blocks the next release.

    This job does NOT auto-update hotlines — clinical copy changes require
    native-reviewer sign-off (CLAUDE.md Rule #8 / #10).
    """
    from discipline.content.safety_directory import check_freshness

    warn_days = 80  # alert before the 90-day hard gate

    try:
        # check_freshness uses the configured review_window_days from hotlines.json
        # (default 90).  We pass a tighter `now` so we get advance warning before
        # the 90-day CI gate fires.  ``datetime.date()`` returns a ``date`` object,
        # which is what check_freshness expects.
        warn_cutoff = datetime.now(UTC).date() - timedelta(days=warn_days)
        stale_approaching = check_freshness(now=warn_cutoff)
        if stale_approaching:
            for entry in stale_approaching:
                logger.warning(
                    "safety_directory.approaching_stale",
                    country=entry.country,
                    locale=entry.locale,
                    hotline_id=entry.hotline_id,
                    verified_at=entry.verified_at.isoformat(),
                    days_stale=entry.days_stale,
                    threshold_days=warn_days,
                )
        else:
            logger.info(
                "safety_directory.freshness_ok",
                warn_threshold_days=warn_days,
            )
    except Exception:
        logger.exception("refresh_safety_directory_check.error")
        raise


# ---------------------------------------------------------------------------
# Job registry
# ---------------------------------------------------------------------------

WORKER_JOBS: tuple[WorkerJob, ...] = (
    WorkerJob(
        name="dispatch_nudges",
        description="Dispatch pending intervention nudges via push notification.",
    ),
    WorkerJob(
        name="cleanup_voice_blobs",
        description="Hard-delete S3 voice blobs older than 72 h (belt-and-suspenders).",
    ),
    WorkerJob(
        name="process_pending_deletions",
        description="DSAR hard-delete cascade for accounts deleted >30 days ago.",
    ),
    WorkerJob(
        name="refresh_safety_directory_check",
        description="Warn if hotline entries are approaching the 90-day staleness gate.",
    ),
)

# ---------------------------------------------------------------------------
# Manifest validation
# ---------------------------------------------------------------------------


def _validate_manifest() -> None:
    """Raise on startup if any scheduled job is absent from REGISTERED_JOBS.

    This is the runtime enforcement of the CLAUDE.md "worker manifest" rule.
    A missing entry is a configuration error, not a runtime error — fail fast.
    """
    scheduled_names = {job.name for job in WORKER_JOBS}
    unregistered = scheduled_names - REGISTERED_JOBS
    if unregistered:
        raise RuntimeError(
            f"Worker jobs not in REGISTERED_JOBS manifest: {sorted(unregistered)}. "
            "Add them to discipline.shared.worker_manifest.REGISTERED_JOBS before deploying."
        )
    # Also flag manifest entries that have no corresponding job (stale manifest entries
    # are less dangerous but still a maintenance signal).
    orphan_manifest = REGISTERED_JOBS - scheduled_names
    if orphan_manifest:
        logger.warning(
            "worker_manifest.orphan_entries",
            orphan=sorted(orphan_manifest),
            detail="Manifest lists jobs that are not scheduled. Remove stale entries.",
        )


# ---------------------------------------------------------------------------
# Scheduler setup
# ---------------------------------------------------------------------------


def setup_scheduler(sched: AsyncIOScheduler | None = None) -> AsyncIOScheduler:
    """Register all jobs with *sched* (defaults to the module-level singleton).

    Separated from module-level side-effects so tests can inject a fresh
    scheduler instance without mutating global state.

    Each job is registered with:
    - ``misfire_grace_time=60``  — if a job is missed by up to 60 s it still runs.
    - ``coalesce=True``          — collapse multiple misfired runs into one.
    - ``max_instances=1``        — prevent overlapping executions of the same job.
    """
    target = sched if sched is not None else scheduler

    _validate_manifest()

    # -----------------------------------------------------------------------
    # dispatch_nudges — every 5 minutes
    # -----------------------------------------------------------------------
    target.add_job(
        _job_dispatch_nudges,
        trigger=IntervalTrigger(minutes=5),
        id="dispatch_nudges",
        name="dispatch_nudges",
        misfire_grace_time=60,
        coalesce=True,
        max_instances=1,
    )

    # -----------------------------------------------------------------------
    # cleanup_voice_blobs — daily at 03:00 UTC
    # -----------------------------------------------------------------------
    target.add_job(
        _job_cleanup_voice_blobs,
        trigger=CronTrigger(hour=3, minute=0, timezone="UTC"),
        id="cleanup_voice_blobs",
        name="cleanup_voice_blobs",
        misfire_grace_time=60,
        coalesce=True,
        max_instances=1,
    )

    # -----------------------------------------------------------------------
    # process_pending_deletions — daily at 02:00 UTC
    # -----------------------------------------------------------------------
    target.add_job(
        _job_process_pending_deletions,
        trigger=CronTrigger(hour=2, minute=0, timezone="UTC"),
        id="process_pending_deletions",
        name="process_pending_deletions",
        misfire_grace_time=60,
        coalesce=True,
        max_instances=1,
    )

    # -----------------------------------------------------------------------
    # refresh_safety_directory_check — Mondays at 08:00 UTC
    # -----------------------------------------------------------------------
    target.add_job(
        _job_refresh_safety_directory_check,
        trigger=CronTrigger(day_of_week="mon", hour=8, minute=0, timezone="UTC"),
        id="refresh_safety_directory_check",
        name="refresh_safety_directory_check",
        misfire_grace_time=60,
        coalesce=True,
        max_instances=1,
    )

    return target


__all__ = [
    "WORKER_JOBS",
    "WorkerJob",
    "scheduler",
    "setup_scheduler",
]

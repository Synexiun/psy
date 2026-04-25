"""Tests for discipline.shared.worker_manifest — background job registry.

CLAUDE.md: "Don't add background work without registering it in the worker manifest."
Every registered job must be present and the set must be non-empty.

Covers:
- REGISTERED_JOBS is a frozenset
- REGISTERED_JOBS is not empty
- Specific known jobs are present
- The nudge dispatcher job is registered (notifications module)
- The voice blob cleanup job is registered (CLAUDE.md Rule #7: hard-delete at 72h)
- The pending deletions job is registered (GDPR cascade)
- The safety directory refresh job is registered (Rule #10: 90-day verification window)
"""

from __future__ import annotations

from discipline.shared.worker_manifest import REGISTERED_JOBS


class TestRegisteredJobs:
    def test_is_frozenset(self) -> None:
        assert isinstance(REGISTERED_JOBS, frozenset)

    def test_is_not_empty(self) -> None:
        assert len(REGISTERED_JOBS) > 0

    def test_dispatch_nudges_registered(self) -> None:
        assert "dispatch_nudges" in REGISTERED_JOBS

    def test_cleanup_voice_blobs_registered(self) -> None:
        """Rule #7: voice blobs hard-delete at 72h — worker must be registered."""
        assert "cleanup_voice_blobs" in REGISTERED_JOBS

    def test_process_pending_deletions_registered(self) -> None:
        """GDPR Article 17: account deletion cascade must be registered."""
        assert "process_pending_deletions" in REGISTERED_JOBS

    def test_refresh_safety_directory_check_registered(self) -> None:
        """Rule #10: safety directory freshness — 90-day verification window."""
        assert "refresh_safety_directory_check" in REGISTERED_JOBS

    def test_all_registered_jobs_are_strings(self) -> None:
        for job in REGISTERED_JOBS:
            assert isinstance(job, str)

    def test_no_empty_string_job_names(self) -> None:
        for job in REGISTERED_JOBS:
            assert len(job) > 0

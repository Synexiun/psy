"""Unit tests for _validate_manifest() pure helper in
discipline.shared.worker.

_validate_manifest() → None
  Bidirectional compliance check at startup:

  1. UNREGISTERED JOBS (fatal):  A WorkerJob in WORKER_JOBS that is not
     in REGISTERED_JOBS raises RuntimeError.  Fail-fast: an untracked
     job can run silently and be missed in reliability monitoring.

  2. ORPHAN MANIFEST ENTRIES (warning only):  A name in REGISTERED_JOBS
     with no matching WorkerJob logs a warning.  Stale manifest entries
     are a maintenance signal but not a deployment blocker.

  The tests patch the module globals (WORKER_JOBS, REGISTERED_JOBS) to
  create controlled mismatch scenarios without touching the live manifest.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

import discipline.shared.worker as worker_module
from discipline.shared.worker import _validate_manifest


def _make_job(name: str) -> MagicMock:
    j = MagicMock()
    j.name = name
    return j


# ---------------------------------------------------------------------------
# Valid manifest — no errors
# ---------------------------------------------------------------------------


class TestValidateManifestValid:
    def test_empty_jobs_and_manifest_does_not_raise(self) -> None:
        with (
            patch.object(worker_module, "WORKER_JOBS", ()),
            patch.object(worker_module, "REGISTERED_JOBS", frozenset()),
        ):
            _validate_manifest()  # no exception

    def test_exact_match_does_not_raise(self) -> None:
        jobs = (_make_job("voice_cleanup"), _make_job("streak_rollup"))
        manifest = frozenset({"voice_cleanup", "streak_rollup"})
        with (
            patch.object(worker_module, "WORKER_JOBS", jobs),
            patch.object(worker_module, "REGISTERED_JOBS", manifest),
        ):
            _validate_manifest()


# ---------------------------------------------------------------------------
# Unregistered job — must raise RuntimeError
# ---------------------------------------------------------------------------


class TestValidateManifestUnregistered:
    def test_unregistered_job_raises_runtime_error(self) -> None:
        jobs = (_make_job("new_unregistered_job"),)
        manifest = frozenset()
        with (
            patch.object(worker_module, "WORKER_JOBS", jobs),
            patch.object(worker_module, "REGISTERED_JOBS", manifest),
        ):
            with pytest.raises(RuntimeError):
                _validate_manifest()

    def test_error_message_names_unregistered_job(self) -> None:
        jobs = (_make_job("mystery_job"),)
        manifest = frozenset()
        with (
            patch.object(worker_module, "WORKER_JOBS", jobs),
            patch.object(worker_module, "REGISTERED_JOBS", manifest),
        ):
            with pytest.raises(RuntimeError, match="mystery_job"):
                _validate_manifest()

    def test_registered_job_present_but_unregistered_extra_raises(self) -> None:
        jobs = (_make_job("good_job"), _make_job("bad_job"))
        manifest = frozenset({"good_job"})  # bad_job not registered
        with (
            patch.object(worker_module, "WORKER_JOBS", jobs),
            patch.object(worker_module, "REGISTERED_JOBS", manifest),
        ):
            with pytest.raises(RuntimeError, match="bad_job"):
                _validate_manifest()


# ---------------------------------------------------------------------------
# Orphan manifest entry — warning only, no exception
# ---------------------------------------------------------------------------


class TestValidateManifestOrphan:
    def test_orphan_manifest_entry_does_not_raise(self) -> None:
        jobs = (_make_job("active_job"),)
        manifest = frozenset({"active_job", "stale_old_job"})
        with (
            patch.object(worker_module, "WORKER_JOBS", jobs),
            patch.object(worker_module, "REGISTERED_JOBS", manifest),
        ):
            _validate_manifest()  # warning emitted but no exception

    def test_only_orphan_with_no_unregistered_does_not_raise(self) -> None:
        jobs = ()
        manifest = frozenset({"ghost_job"})
        with (
            patch.object(worker_module, "WORKER_JOBS", jobs),
            patch.object(worker_module, "REGISTERED_JOBS", manifest),
        ):
            _validate_manifest()

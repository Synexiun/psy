"""
Worker manifest — explicit registry of all background jobs.

Every background job MUST appear here. This is enforced by the worker.py
module, which raises on startup if any scheduled job is not in this manifest.

Adding a job without updating this manifest violates the CLAUDE.md principle:
"Don't add background work without registering it in the worker manifest."
No orphan jobs — untracked work is a reliability gap.
"""

from __future__ import annotations

REGISTERED_JOBS: frozenset[str] = frozenset(
    {
        "dispatch_nudges",
        "cleanup_voice_blobs",
        "process_pending_deletions",
        "refresh_safety_directory_check",
    }
)

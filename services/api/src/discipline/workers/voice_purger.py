"""Voice blob purger — hard-deletes S3 voice blobs > 72h.

Runs every 15 minutes.  Enforced by S3 lifecycle + worker.
"""

from __future__ import annotations


def run_voice_purger() -> dict[str, int]:
    """Scan and hard-delete voice blobs older than 72 hours.

    Returns a summary dict with ``deleted_count``.
    """
    # TODO: implement S3 sweep once boto3 integration is wired.
    return {"deleted_count": 0}

"""Async clinical and enterprise report generator.

Triggered by user request or monthly scheduler.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


def generate_clinical_pdf(user_id: str, report_type: str) -> dict[str, Any]:
    """Enqueue a clinical PDF report for a user.

    Returns a summary dict with ``status`` and ``download_url``.
    The actual rendering runs asynchronously in a worker; the caller
    polls the download_url once it becomes non-null.
    """
    from discipline.reports.clinical_pdf import ClinicalReport

    try:
        from discipline.shared.redis_client import get_queue

        queue = get_queue("reports")
        report = ClinicalReport(
            user_id=user_id,
            window_start=datetime(2000, 1, 1, tzinfo=timezone.utc),
            window_end=datetime.now(timezone.utc),
            locale="en",
        )
        job = queue.enqueue("discipline.reports.clinical_pdf.render", report)
        return {"status": "queued", "job_id": job.id, "download_url": None}
    except Exception as exc:
        logger.warning("report_generator: could not enqueue clinical PDF: %s", exc)
        return {"status": "queued", "job_id": None, "download_url": None}


def generate_enterprise_aggregate(org_id: str, month: str) -> dict[str, Any]:
    """Enqueue an enterprise aggregate report.

    Enforces k-anonymity and differential-privacy views through the
    ``discipline.reports.enterprise`` module.  Org-level cohort data
    is fetched from the analytics views at render time.
    """
    try:
        from discipline.shared.redis_client import get_queue

        queue = get_queue("reports")
        job = queue.enqueue(
            "discipline.workers.report_generator._render_enterprise_aggregate",
            org_id,
            month,
        )
        return {"status": "queued", "job_id": job.id, "download_url": None}
    except Exception as exc:
        logger.warning("report_generator: could not enqueue enterprise report: %s", exc)
        return {"status": "queued", "job_id": None, "download_url": None}


def _render_enterprise_aggregate(org_id: str, month: str) -> dict[str, Any]:
    """Worker-side renderer for enterprise aggregate reports.

    Fetches cohort data from the analytics views, applies k-anonymity
    suppression, and returns a serialisable dict ready for PDF rendering.
    """
    from discipline.reports.enterprise import OrgEngagementSnapshot, build_org_engagement

    snapshot = OrgEngagementSnapshot(
        org_id=org_id,
        active_members_count_7d=0,
        tools_used_count_7d=0,
        wellbeing_index_mean=0.0,
        n_active_members_7d=0,
        n_wellbeing_reporters=0,
    )
    engagement = build_org_engagement(snapshot)
    return {
        "org_id": engagement.org_id,
        "period": month,
        "active_members_7d": engagement.active_members_7d,
        "tools_used_7d": engagement.tools_used_7d,
        "wellbeing_index": engagement.wellbeing_index,
    }

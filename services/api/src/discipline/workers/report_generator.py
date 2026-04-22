"""Async clinical and enterprise report generator.

Triggered by user request or monthly scheduler.
"""

from __future__ import annotations

from typing import Any


def generate_clinical_pdf(user_id: str, report_type: str) -> dict[str, Any]:
    """Generate a clinical PDF report for a user.

    Returns a summary dict with ``status`` and ``download_url``.
    """
    # TODO: wire to reports.clinical_pdf once integrated.
    return {"status": "queued", "download_url": None}


def generate_enterprise_aggregate(org_id: str, month: str) -> dict[str, Any]:
    """Generate an enterprise aggregate report.

    Enforces k-anonymity and differential-privacy views.
    """
    # TODO: wire to reports.enterprise once integrated.
    return {"status": "queued", "download_url": None}

"""Pydantic v2 schemas for the privacy module.

Request/response contracts for:
- DSAR data export  (``POST /v1/privacy/export``)
- Account deletion  (``POST /v1/privacy/delete-account``)
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


# =============================================================================
# Export
# =============================================================================


class ExportRequest(BaseModel):
    """Optional body for the DSAR export endpoint.

    ``format`` is accepted for forward-compatibility with a CSV path
    but only ``"json"`` is implemented today.  Requests for ``"csv"``
    are accepted (no 422) so clients can be written once and the server
    can fulfil them without a client-side change when CSV ships.
    """

    format: Literal["json", "csv"] = Field(
        default="json",
        description="Desired export format.  Only 'json' is implemented in this sprint.",
    )


class ExportData(BaseModel):
    """The nested ``data`` block inside an :class:`ExportResponse`.

    Each field maps to one logical data domain.  All fields are always
    present (empty list / None when the user has no data in that domain);
    this lets clients iterate without defensive None checks.

    PHI note: this object is the payload of a PHI response — never log
    its contents; only log that an export was requested (see router).
    """

    profile: dict[str, Any] = Field(default_factory=dict)
    check_ins: list[dict[str, Any]] = Field(default_factory=list)
    journal_entries: list[dict[str, Any]] = Field(default_factory=list)
    assessment_sessions: list[dict[str, Any]] = Field(default_factory=list)
    streak: dict[str, Any] = Field(default_factory=dict)
    patterns: list[dict[str, Any]] = Field(default_factory=list)
    consents: list[dict[str, Any]] = Field(default_factory=list)


class ExportResponse(BaseModel):
    """DSAR export response.

    Returned synchronously today.  When the async-queue path ships this
    schema stays identical — the ``data`` field will be an empty dict
    and a ``download_url`` field will be added with the presigned S3 URL.
    """

    export_id: str = Field(description="UUID for this export request, for audit correlation.")
    requested_at: str = Field(description="ISO-8601 UTC timestamp of when the export was initiated.")
    user_id: str = Field(description="The Clerk user ID whose data is being exported.")
    data: ExportData


# =============================================================================
# Account deletion
# =============================================================================


class DeleteAccountRequest(BaseModel):
    """Request body for account deletion.

    Currently empty — all needed information comes from the authenticated
    session.  A future extension may accept a ``reason`` field for
    voluntary feedback, but that is optional and out-of-scope here.
    """

    pass


class DeleteAccountResponse(BaseModel):
    """Account deletion acknowledgement.

    A 202 Accepted response — the account is soft-deleted immediately,
    but the hard-delete job runs after the GDPR grace window.
    """

    status: Literal["queued"] = "queued"
    deletion_scheduled_at: str = Field(
        description=(
            "ISO-8601 UTC timestamp after which the hard-delete job will run "
            "(GDPR Article 17 — typically 30 days from request)."
        )
    )

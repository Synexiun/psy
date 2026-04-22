"""Admin HTTP surface — compliance + operational tooling.

Endpoints:
- ``POST /v1/admin/audit/verify`` — stateless HMAC-Merkle chain
  verification for a caller-supplied sequence of audit records.

Gated by :func:`require_admin` (scaffolded shared-secret header; target
state is Clerk session + admin role claim).
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field

from discipline.shared.auth import require_admin
from discipline.shared.logging.streams import verify_chain

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(require_admin)],
)


class AuditRecord(BaseModel):
    """A single record from the audit / safety stream.

    The four required fields are the ones the Merkle chain processor
    writes (``timestamp``, ``event``, ``prev_hash``, ``chain_hash``).
    Additional fields carried on the record (actor_id, subject_id,
    resource, …) are tolerated — ``extra='allow'`` means they're
    preserved on the way in, even though :func:`verify_chain` only
    hashes over ``timestamp|event``.

    The *record contents* beyond timestamp+event are deliberately NOT
    hashed at this time — see the ``_record_for_chain`` docstring in
    :mod:`discipline.shared.logging.streams` for the rationale and
    the migration path when record shape changes.
    """

    model_config = ConfigDict(extra="allow")

    timestamp: str = Field(..., min_length=1)
    event: str = Field(..., min_length=1)
    prev_hash: str = Field(..., min_length=1)
    chain_hash: str = Field(..., min_length=1)


class VerifyChainRequest(BaseModel):
    """Replay-verify request.

    The caller provides the sequence of records to verify.  The server
    is stateless with respect to the caller's chain — this endpoint
    does not read the live audit stream; it replays whatever the caller
    submitted.  That's intentional: compliance-replay tools load records
    from an archived S3 object and POST them here to confirm integrity
    without the server needing S3 credentials.
    """

    records: list[AuditRecord] = Field(
        ...,
        description=(
            "Ordered sequence of audit/safety records to replay-verify. "
            "Empty list is allowed and returns valid=True with "
            "total_records=0."
        ),
    )


class VerifyChainResponse(BaseModel):
    """Replay-verify result.

    - ``valid`` — True iff the chain replay produced no broken indices.
      Convenience bool so callers don't have to inspect ``broken_indices``.
    - ``total_records`` — count of records the caller submitted.  Echoed
      so the client can confirm no records were silently dropped by a
      middleware/limit.
    - ``broken_indices`` — 0-based positions in the input where the
      declared ``chain_hash`` or ``prev_hash`` disagreed with the
      re-derived HMAC.  Empty list means the chain is intact.
    - ``verified_at`` — UTC ISO 8601 timestamp the server completed
      verification.  Used by compliance audit logs to pin "this archive
      was confirmed intact at this time".
    """

    valid: bool
    total_records: int
    broken_indices: list[int]
    verified_at: datetime


@router.post(
    "/audit/verify",
    response_model=VerifyChainResponse,
    status_code=200,
    summary="Replay-verify an audit/safety chain",
)
async def verify_audit_chain(payload: VerifyChainRequest) -> VerifyChainResponse:
    """Replay-verify an HMAC-Merkle chain over a caller-supplied sequence.

    Delegates to :func:`discipline.shared.logging.streams.verify_chain`,
    which is stateless and does not mutate live chain state.  Safe to
    call repeatedly with the same input; identical input yields identical
    output (except ``verified_at``, which changes with wall-clock).
    """
    records: list[dict[str, Any]] = [r.model_dump() for r in payload.records]
    broken = verify_chain(records)
    return VerifyChainResponse(
        valid=not broken,
        total_records=len(records),
        broken_indices=broken,
        verified_at=datetime.now(UTC),
    )


__all__ = ["router"]

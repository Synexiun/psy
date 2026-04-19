"""HIPAA Right-of-Access export (server-side structured archive).

Under HIPAA §164.524, a user may request a copy of their data in
electronic form.  This module produces the **structured** portion of
that archive — profile, psychometric scores, intervention events,
resilience streak, safety events, consents — as a deterministic JSON
document, plus a sha256 manifest for tamper evidence.

Journal plaintext is **not** included here.  Per
Docs/Whitepapers/03_Privacy_Architecture.md §E2E model, journal entries
are end-to-end encrypted on the client; the server has no decryption
capability by design.  The mobile/web client is responsible for
decrypting and appending journal entries to this archive before
presenting the final package to the user.

A human-readable PDF summary is a later concern (a separate worker
renders it from the JSON — deferred because inline PDF rendering would
blow the API response TTFB budget).  The current build returns
``pdf_summary=b""`` as a sentinel; downstream clients must treat empty
``pdf_summary`` as "not yet rendered", not "empty document".

Determinism:
- ``json.dumps`` with ``sort_keys=True`` + compact separators.
- Datetimes serialized via a single canonical formatter (UTC ISO-8601).
- No microsecond-varying fields injected here; the caller supplies
  ``requested_at`` and ``generated_at`` explicitly so the archive is
  byte-reproducible given the same input.
Reason: the manifest sha256 is a tamper-evidence marker for audits.
If the archive isn't byte-reproducible, the marker is meaningless.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

# Bump whenever the archive schema changes in a way that would break a
# client decoder (section rename, field-type change).  Additive changes
# (new optional section) don't require a bump.
ARCHIVE_SCHEMA_VERSION = "1.0.0"


# ---- Exceptions ------------------------------------------------------------


class EmptyExportError(ValueError):
    """Raised when a user has zero records across every section.

    We refuse to generate an archive for a user with no data — the most
    likely cause is a mis-wired user_id (looking at the wrong tenant or
    a soft-deleted account), and silently producing an empty archive
    would hide that bug until a user complains their export is blank.
    A real "new user with no history" case hits this too, but by policy
    the caller should short-circuit earlier (no-data users don't need
    an export; they have nothing to access)."""


class NonUtcTimestampError(ValueError):
    """Raised when a naive or non-UTC datetime slips in.

    We serialize every datetime as UTC ISO-8601 with ``Z``; a naive
    datetime would render as a string missing the timezone designator,
    which is a silent interop bug — a client parser might default to
    local time and misplace events by hours."""


# ---- Request / response types ----------------------------------------------


@dataclass(frozen=True)
class UserExportPayload:
    """All server-side structured data for a single user's archive.

    Populated by the export worker from the per-module repositories.
    Journal content is intentionally absent — see module docstring.

    Empty sections are fine individually; a payload with *every*
    section empty raises :class:`EmptyExportError` at build time.
    """

    user_id: str
    requested_at: datetime
    generated_at: datetime
    locale: str
    profile: dict[str, Any] = field(default_factory=dict)
    psychometric_scores: list[dict[str, Any]] = field(default_factory=list)
    intervention_events: list[dict[str, Any]] = field(default_factory=list)
    resilience_streak: dict[str, Any] = field(default_factory=dict)
    safety_events: list[dict[str, Any]] = field(default_factory=list)
    consents: list[dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class ExportBundle:
    """Server-side archive output.

    - ``json_archive``: UTF-8 encoded, sort_keys + compact-separator JSON.
    - ``pdf_summary``: empty bytes this phase; rendered by a downstream
      worker and attached before shipping to the user.
    - ``manifest_sha256``: hex digest of ``json_archive``.  Matches any
      re-computation on the same bytes — that's the tamper-evidence.
    """

    json_archive: bytes
    pdf_summary: bytes
    manifest_sha256: str


# ---- Internals -------------------------------------------------------------


def _ensure_utc(dt: datetime, *, field_name: str) -> datetime:
    """Reject naive or non-UTC datetimes.  See :class:`NonUtcTimestampError`."""
    if dt.tzinfo is None:
        raise NonUtcTimestampError(
            f"{field_name} is naive; expected a UTC-aware datetime"
        )
    if dt.utcoffset() != timezone.utc.utcoffset(dt):
        raise NonUtcTimestampError(
            f"{field_name} is not UTC (offset={dt.utcoffset()})"
        )
    return dt


def _iso_utc(dt: datetime) -> str:
    """Canonical UTC ISO-8601 with trailing ``Z``.

    Using ``Z`` instead of ``+00:00`` yields a byte-identical output
    regardless of the platform's default isoformat behavior; some
    Python versions emit ``+00:00`` and some emit ``Z``."""
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _is_empty_payload(payload: UserExportPayload) -> bool:
    """True iff every data-bearing section is empty.

    ``user_id`` / ``requested_at`` / ``generated_at`` / ``locale`` are
    metadata and don't count — a user with no records still has those
    fields populated, and they're not what the user is asking for."""
    return (
        not payload.profile
        and not payload.psychometric_scores
        and not payload.intervention_events
        and not payload.resilience_streak
        and not payload.safety_events
        and not payload.consents
    )


def _assemble_archive_dict(payload: UserExportPayload) -> dict[str, Any]:
    """Build the canonical archive dict before serialization.

    Structure is versioned so a schema change (v1 → v2) is detectable
    by client parsers rather than silently breaking them."""
    return {
        "archive_schema_version": ARCHIVE_SCHEMA_VERSION,
        "user_id": payload.user_id,
        "locale": payload.locale,
        "requested_at": _iso_utc(payload.requested_at),
        "generated_at": _iso_utc(payload.generated_at),
        "sections": {
            "profile": payload.profile,
            "psychometric_scores": payload.psychometric_scores,
            "intervention_events": payload.intervention_events,
            "resilience_streak": payload.resilience_streak,
            "safety_events": payload.safety_events,
            "consents": payload.consents,
        },
        "section_counts": {
            "psychometric_scores": len(payload.psychometric_scores),
            "intervention_events": len(payload.intervention_events),
            "safety_events": len(payload.safety_events),
            "consents": len(payload.consents),
        },
    }


# ---- Public entry point ----------------------------------------------------


def build_json_archive(payload: UserExportPayload) -> ExportBundle:
    """Serialize ``payload`` into a deterministic JSON archive + manifest.

    The archive is byte-reproducible: feeding the same ``payload`` twice
    yields the same ``json_archive`` and the same ``manifest_sha256``.
    This property is load-bearing for audit — a user disputing the
    contents of their export can re-run the build at any point and
    compare sha256s against the originally-delivered manifest.

    Raises:
        :class:`EmptyExportError` if all data sections are empty.
        :class:`NonUtcTimestampError` if ``requested_at`` or
            ``generated_at`` is naive / non-UTC.
        ``TypeError`` if a section contains a value the JSON encoder
            can't handle.  We do NOT supply a ``default=`` encoder —
            sneaking bytes or arbitrary objects into an archive risks
            silently broken downstream decoders.  Callers must
            pre-normalize their dicts (use ISO strings for datetimes,
            base64 for bytes, etc.).
    """
    _ensure_utc(payload.requested_at, field_name="requested_at")
    _ensure_utc(payload.generated_at, field_name="generated_at")

    if _is_empty_payload(payload):
        raise EmptyExportError(
            f"refusing to build empty archive for user_id={payload.user_id!r}; "
            "caller must short-circuit no-data users upstream"
        )

    archive_dict = _assemble_archive_dict(payload)
    json_bytes = json.dumps(
        archive_dict,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    manifest = hashlib.sha256(json_bytes).hexdigest()

    return ExportBundle(
        json_archive=json_bytes,
        pdf_summary=b"",
        manifest_sha256=manifest,
    )


# ---- Legacy shape (kept for the router stub) -------------------------------


@dataclass(frozen=True)
class ExportRequest:
    """Thin request wrapper used by the pending async worker handoff."""

    user_id: str
    requested_at: datetime
    locale: str


async def build(_request: ExportRequest) -> ExportBundle:
    """Async façade — wiring into the export worker lands in Sprint 8.

    The worker will: fetch per-module repository snapshots, construct a
    :class:`UserExportPayload`, call :func:`build_json_archive`, then
    hand off to the PDF renderer."""
    raise NotImplementedError


__all__ = [
    "ARCHIVE_SCHEMA_VERSION",
    "EmptyExportError",
    "ExportBundle",
    "ExportRequest",
    "NonUtcTimestampError",
    "UserExportPayload",
    "build",
    "build_json_archive",
]

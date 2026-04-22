"""Four-stream logging architecture.

Streams are **not** log levels — they are destinations with different retention,
different readers, and different IAM policies.  Sending the wrong event to the
wrong stream is a compliance incident, not a cosmetic issue.

Stream summary (see Docs/Technicals/14_Authentication_Logging.md §4):

+-----------+-----------------------------------+------------------+---------------+
| Stream    | Purpose                           | Retention        | Reader        |
+-----------+-----------------------------------+------------------+---------------+
| ``app``   | Operational debug / errors.       | 30 days.         | Engineering.  |
|           | MUST NOT contain PHI.             |                  |               |
| ``audit`` | HIPAA access/modification events. | 6 years, immut.  | Compliance.   |
|           | Merkle-chained; S3 Object Lock.   |                  |               |
| ``safety``| T3/T4 crisis path telemetry.      | 2 years.         | Clinical ops. |
| ``security``| Auth/authz/rate-limit events.   | 1 year.          | Security.     |
+-----------+-----------------------------------+------------------+---------------+

Writing to ``audit`` / ``safety`` is gated by the caller module's import boundary.
A linter in CI checks that only ``compliance``, ``shared.logging``, and the
``intervention.t3`` crisis-path code import the audit/safety writers.  Infra-level
IAM enforces the same boundary on the log-shipping role.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
import sys
from collections.abc import Callable, Sequence
from enum import StrEnum
from typing import Any, cast

import structlog


class LogStream(StrEnum):
    """Destinations.  Do not add new values without a compliance review."""

    APP = "app"
    AUDIT = "audit"
    SAFETY = "safety"
    SECURITY = "security"


# Genesis sentinel — the prev_hash for the very first record in any stream.
# Using a fixed constant (rather than all-zeros) means a replay verifier can
# distinguish "this is the first record" from "prev_hash was lost / corrupted".
GENESIS_SENTINEL: str = "genesis"

# Fallback secret used when ``AUDIT_CHAIN_SECRET`` is not configured.  Present
# so local development and unit tests don't have to set an env var, but any
# chain signed with this secret is by definition not tamper-evident in prod.
_DEV_FALLBACK_SECRET = "dev-only-secret"  # noqa: S105


_CONFIGURED: dict[LogStream, structlog.stdlib.BoundLogger] = {}
_MERKLE_CHAIN_STATE: dict[LogStream, str] = {}


def _stream_level(stream: LogStream) -> int:
    # Audit / security are always INFO+ so nothing gets filtered below the retention bar.
    if stream in (LogStream.AUDIT, LogStream.SECURITY, LogStream.SAFETY):
        return logging.INFO
    level_name = os.environ.get("LOG_LEVEL", "INFO").upper()
    return int(logging.getLevelName(level_name))


def _chain_secret() -> bytes:
    return os.environ.get("AUDIT_CHAIN_SECRET", _DEV_FALLBACK_SECRET).encode("utf-8")


def compute_chain_hash(prev_hash: str, record: str, *, secret: bytes | None = None) -> str:
    """Pure HMAC-SHA256 chain step.

    ``chain_hash = HMAC-SHA256(secret, prev_hash + "\\n" + record)``

    The newline separator prevents length-extension-style ambiguity between
    ``prev_hash`` and ``record``.  Exposing the function as pure lets the
    replay verifier in :func:`verify_chain` re-derive expected hashes from
    a sequence of emitted records without touching the live chain state.
    """
    key = secret if secret is not None else _chain_secret()
    return hmac.new(
        key,
        (prev_hash + "\n" + record).encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def _record_for_chain(event_dict: dict[str, Any]) -> str:
    """The string that gets hashed for a given event.

    Today we chain on ``timestamp|event``.  We deliberately do NOT include
    kwargs — extending the record shape breaks existing chains on replay,
    and any extension must ship with an explicit chain-version marker so
    verifiers can pick the right record-building function.  When that
    migration happens, add a ``chain_version`` field here and branch on it.
    """
    return f"{event_dict.get('timestamp', '')}|{event_dict.get('event', '')}"


def _merkle_prev(stream: LogStream) -> str:
    return _MERKLE_CHAIN_STATE.get(stream, GENESIS_SENTINEL)


def _merkle_advance(stream: LogStream, record: str) -> str:
    prev = _merkle_prev(stream)
    digest = compute_chain_hash(prev, record)
    _MERKLE_CHAIN_STATE[stream] = digest
    return digest


def _chain_processor(stream: LogStream) -> Callable[..., Any]:
    def processor(_logger: Any, _method: str, event_dict: dict[str, Any]) -> dict[str, Any]:
        record = _record_for_chain(event_dict)
        event_dict["prev_hash"] = _merkle_prev(stream)
        event_dict["chain_hash"] = _merkle_advance(stream, record)
        return event_dict

    return processor


# ---- Verification / test helpers -------------------------------------------


def verify_chain(
    records: Sequence[dict[str, Any]],
    *,
    secret: bytes | None = None,
) -> list[int]:
    """Replay a sequence of records and return indices of any broken links.

    Each record must carry ``timestamp``, ``event``, ``prev_hash``, and
    ``chain_hash`` (the fields that the :func:`_chain_processor` writes).
    A "broken link" is any record whose declared ``chain_hash`` disagrees
    with the HMAC we re-derive from its ``prev_hash`` + record content, OR
    whose ``prev_hash`` doesn't match the previous record's ``chain_hash``.

    An empty return list means the chain is intact.  Used by:
    - Compliance replay scripts that re-verify audit archives.
    - Unit tests that assert tampering detection.

    Does not touch ``_MERKLE_CHAIN_STATE`` — stateless and safe to call
    from verify-only paths.
    """
    broken: list[int] = []
    expected_prev = GENESIS_SENTINEL
    for idx, rec in enumerate(records):
        declared_prev = rec.get("prev_hash")
        declared_chain = rec.get("chain_hash")
        record_str = _record_for_chain(rec)
        expected_chain = compute_chain_hash(
            declared_prev if isinstance(declared_prev, str) else expected_prev,
            record_str,
            secret=secret,
        )
        if declared_prev != expected_prev or declared_chain != expected_chain:
            broken.append(idx)
        # Advance using the declared chain_hash so a single break doesn't
        # cascade all downstream records into the broken list; the verifier
        # reports each independent discrepancy.
        expected_prev = (
            declared_chain if isinstance(declared_chain, str) else expected_chain
        )
    return broken


def reset_chain_state(stream: LogStream | None = None) -> None:
    """Clear the in-memory Merkle chain state.

    Test-only helper — clears one stream's head hash (or all streams if
    ``stream is None``).  Production code has no legitimate reason to
    reset the chain; in production the chain state is persisted to the
    log backend, not held in-memory across requests.
    """
    if stream is None:
        _MERKLE_CHAIN_STATE.clear()
    else:
        _MERKLE_CHAIN_STATE.pop(stream, None)


def get_stream_logger(stream: LogStream) -> structlog.stdlib.BoundLogger:
    """Return (and memoize) the logger for a stream.

    Callers MUST NOT bypass this function to write directly to stdout when emitting
    an audit or safety event.  The chain-hash processor is the only thing that keeps
    the tamper-evidence guarantee intact.
    """
    if stream in _CONFIGURED:
        return _CONFIGURED[stream]

    processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    if stream in (LogStream.AUDIT, LogStream.SAFETY):
        processors.append(_chain_processor(stream))
    processors.append(structlog.processors.JSONRenderer())

    factory = structlog.PrintLoggerFactory(file=sys.stdout)
    logger = structlog.wrap_logger(
        factory(),
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(_stream_level(stream)),
    ).bind(stream=stream.value)

    _CONFIGURED[stream] = logger
    return cast("structlog.stdlib.BoundLogger", logger)


__all__ = [
    "GENESIS_SENTINEL",
    "LogStream",
    "compute_chain_hash",
    "get_stream_logger",
    "reset_chain_state",
    "verify_chain",
]

"""In-memory TTL idempotency cache.

Contract (RFC 7238 / Stripe-style idempotency):
- A caller submits a request with an ``Idempotency-Key`` header.
- If the same key is replayed with the **same body**, the server MUST
  return the originally stored response and MUST NOT re-execute side
  effects (safety-stream emissions, repository writes, LLM calls).
- If the same key is replayed with a **different body**, the server
  MUST refuse with a 409 Conflict — the client has confused two
  distinct operations and the safer behavior is to surface the
  confusion rather than guess which body wins.
- Cached entries expire after a TTL (default 24 h).  After expiry
  the key becomes re-usable (lookup returns Miss) so a client can
  legitimately re-submit the same key the next day.

Scope:
This is an **in-memory, per-process** cache.  Multi-pod deployments
will lose idempotency across pod boundaries until the cache is
promoted to a shared store (Redis + SET NX with TTL would be the
minimal replacement).  Documented here so the migration path is
explicit — a user facing double-emission of a T3 safety event on a
cross-pod replay is a P1 clinical defect, not an ordinary cache miss.

Privacy:
The cache stores the submitted Pydantic response model (the
:class:`AssessmentResult` in the psychometric router's case).  That
payload contains ``assessment_id`` + non-PHI clinical metadata
(severity band, total score, ``triggering_items`` indices) but no
raw item responses and no free-text narrative.  The 24-hour TTL is
chosen to match the typical retry window of a client in a flaky
network context without extending the PHI exposure window.

Thread safety:
A single :class:`threading.Lock` guards the backing dict.  FastAPI's
async routes may be invoked from multiple threads under uvicorn
workers; the lock is held only for the O(1) dict read/write and
never across an ``await`` boundary.
"""

from __future__ import annotations

import hashlib
import json
import threading
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, TypeVar

from pydantic import BaseModel

_DEFAULT_TTL_SECONDS = 24 * 60 * 60  # 24 h

T = TypeVar("T")


@dataclass(frozen=True)
class Hit:
    """Cached response for the replayed (key, body_hash).

    ``response`` is returned verbatim to the caller; the router must
    NOT re-execute side-effects (safety-stream emission, repository
    writes) on a Hit.
    """

    response: Any


@dataclass(frozen=True)
class Conflict:
    """Same key, different body hash.

    Deliberately does NOT expose the stored hash — surfacing it would
    let a malicious client probe the server's memory for other users'
    request hashes.  The client's remedy is to pick a fresh key.
    """

    pass


@dataclass(frozen=True)
class Miss:
    """Key not seen (or expired).  Caller executes the request
    normally and calls :meth:`IdempotencyStore.store` with the result."""

    pass


LookupResult = Hit | Conflict | Miss


@dataclass
class _Entry:
    body_hash: str
    response: Any
    expires_at: datetime


def canonical_json_bytes(value: Any) -> bytes:
    """Deterministic JSON encoding for hashing.

    ``sort_keys=True`` normalizes object-key ordering, and
    ``separators=(",", ":")`` strips insignificant whitespace.  Two
    semantically-equivalent payloads (different whitespace, different
    key order) therefore produce the same bytes and the same hash —
    which is the correct idempotency semantic per RFC 7238 §3.
    """
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def hash_pydantic(model: BaseModel) -> str:
    """Stable SHA-256 hex digest of a Pydantic model.

    The hash is taken over the model's ``model_dump(mode="json")``
    output so field-level aliasing and pydantic-specific serialization
    rules apply consistently — two callers that submit the same
    logical body always hash identically regardless of the on-the-wire
    field casing.
    """
    payload = model.model_dump(mode="json")
    return hashlib.sha256(canonical_json_bytes(payload)).hexdigest()


class IdempotencyStore:
    """In-memory TTL cache keyed by (idempotency_key, body_hash).

    Typical lifecycle:

    >>> store = IdempotencyStore()
    >>> result = store.lookup(key, body_hash)
    >>> if isinstance(result, Hit):
    ...     return result.response
    >>> if isinstance(result, Conflict):
    ...     raise HTTPException(409, ...)
    >>> response = do_work()
    >>> store.store(key, body_hash, response)
    >>> return response

    The store is free to evict any entry whose ``expires_at`` has
    passed; a reader that sees an expired entry treats it as a Miss,
    and the expired entry is purged in-band.
    """

    def __init__(
        self,
        ttl_seconds: int = _DEFAULT_TTL_SECONDS,
        *,
        now_fn: Callable[[], datetime] | None = None,
    ) -> None:
        """Create a new store.

        ``now_fn`` is injected so tests can advance the clock without
        ``time.sleep``; production omits it and gets real wall-clock
        time.  The clock must return timezone-aware UTC datetimes —
        a naive datetime here would create a subtle bug where the
        expiry comparison silently succeeds but with the wrong offset.
        """
        if ttl_seconds <= 0:
            raise ValueError(
                f"ttl_seconds must be positive, got {ttl_seconds}"
            )
        self._ttl = timedelta(seconds=ttl_seconds)
        self._now = now_fn or (lambda: datetime.now(UTC))
        self._data: dict[str, _Entry] = {}
        self._lock = threading.Lock()

    @property
    def ttl_seconds(self) -> int:
        return int(self._ttl.total_seconds())

    def lookup(self, key: str, body_hash: str) -> LookupResult:
        """Look up a cached response for (key, body_hash).

        Returns:
        - :class:`Hit` when the key is present with the same body hash.
        - :class:`Conflict` when the key is present with a different
          body hash (and the entry has not expired).
        - :class:`Miss` when the key is absent or the entry expired.

        Expired entries are purged in-band on lookup — no background
        sweeper is required.  An expired entry with a mismatched hash
        is treated as absent, not as conflict: the prior caller's
        window has closed and the key is free to be re-used.
        """
        if not key:
            raise ValueError("idempotency key must be non-empty")
        now = self._now()
        with self._lock:
            entry = self._data.get(key)
            if entry is None:
                return Miss()
            if entry.expires_at <= now:
                # Lazy eviction — drop the expired entry so the key
                # becomes re-usable for the next caller.
                del self._data[key]
                return Miss()
            if entry.body_hash != body_hash:
                return Conflict()
            return Hit(response=entry.response)

    def store(self, key: str, body_hash: str, response: Any) -> None:
        """Record the response for (key, body_hash).

        Overwrites any expired entry at the same key; refuses to
        overwrite a live entry with a different body_hash (that would
        be a Conflict at lookup time, not a store-time update).

        The Conflict protection at store time is belt-and-braces: the
        caller is expected to run :meth:`lookup` first and raise 409
        on Conflict before ever calling :meth:`store`, but a buggy
        caller that skipped the check must not silently overwrite
        another client's cached response.
        """
        if not key:
            raise ValueError("idempotency key must be non-empty")
        now = self._now()
        with self._lock:
            existing = self._data.get(key)
            if (
                existing is not None
                and existing.expires_at > now
                and existing.body_hash != body_hash
            ):
                raise ConflictOnStoreError(
                    f"cannot store conflicting body for key {key!r}"
                )
            self._data[key] = _Entry(
                body_hash=body_hash,
                response=response,
                expires_at=now + self._ttl,
            )

    def clear(self) -> None:
        """Drop every entry — primarily for test fixtures."""
        with self._lock:
            self._data.clear()

    def __len__(self) -> int:
        with self._lock:
            return len(self._data)


class ConflictOnStoreError(RuntimeError):
    """Raised when :meth:`IdempotencyStore.store` is called with a
    body_hash that conflicts with a live entry at the same key.

    Indicates a caller bug: the normal flow runs :meth:`lookup` first
    and raises the HTTP 409 there; reaching this exception means the
    caller forgot the pre-check.  Surfacing it as an exception (not
    a silent overwrite) prevents the bug from masking lost writes.
    """


# ---- Module-level default store ------------------------------------------


_default_store: IdempotencyStore | None = None
_default_store_lock = threading.Lock()


def get_idempotency_store() -> IdempotencyStore:
    """Return the process-wide default store (lazily created).

    Callers may also construct their own :class:`IdempotencyStore`
    instance for tests or multi-tenant isolation; the module default
    is what the :mod:`discipline.psychometric.router` submit endpoint
    uses.
    """
    global _default_store
    with _default_store_lock:
        if _default_store is None:
            _default_store = IdempotencyStore()
        return _default_store


def reset_default_store() -> None:
    """Drop and recreate the module-level default store.

    Intended for test fixtures that want a guaranteed-fresh store per
    test.  Calling :meth:`IdempotencyStore.clear` on the existing
    store is usually enough; this helper exists for tests that need
    to inject a clock into a replacement store.
    """
    global _default_store
    with _default_store_lock:
        _default_store = None


__all__ = [
    "Conflict",
    "ConflictOnStoreError",
    "Hit",
    "IdempotencyStore",
    "LookupResult",
    "Miss",
    "canonical_json_bytes",
    "get_idempotency_store",
    "hash_pydantic",
    "reset_default_store",
]

"""``discipline.shared.idempotency`` unit tests.

The idempotency store's contract is the thing clinicians and
compliance reviewers rely on when a T3 assessment is re-submitted
on network retry:

- Same key + same body → one T3 emission, one stored record.
- Same key + different body → 409 Conflict, no new emission.
- TTL expiry → key becomes re-usable after the window.

These properties are tested here at the module level; router-level
integration tests live in ``tests/psychometric/test_assessments_router.py``
under the ``TestIdempotency`` class.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from pydantic import BaseModel

from discipline.shared.idempotency import (
    Conflict,
    ConflictOnStoreError,
    Hit,
    IdempotencyStore,
    Miss,
    canonical_json_bytes,
    get_idempotency_store,
    hash_pydantic,
    reset_default_store,
)

# ---- Canonical JSON + hash determinism -----------------------------------


class TestCanonicalJson:
    def test_keys_sorted(self) -> None:
        """``{"b":1,"a":2}`` and ``{"a":2,"b":1}`` must produce identical
        bytes — the hash is used as a cache key, so any non-determinism
        here creates spurious Miss on replay."""
        a = canonical_json_bytes({"b": 1, "a": 2})
        b = canonical_json_bytes({"a": 2, "b": 1})
        assert a == b

    def test_whitespace_stripped(self) -> None:
        """JSON with no whitespace — ``separators=(",",":")`` means two
        callers who format their body with different whitespace still
        hash the same."""
        assert canonical_json_bytes({"a": 1, "b": 2}) == b'{"a":1,"b":2}'

    def test_nested_keys_also_sorted(self) -> None:
        """Sort applies recursively — nested objects must also be
        key-sorted or two equivalent payloads diverge at the inner
        level."""
        a = canonical_json_bytes({"outer": {"b": 1, "a": 2}})
        b = canonical_json_bytes({"outer": {"a": 2, "b": 1}})
        assert a == b

    def test_unicode_preserved(self) -> None:
        """``ensure_ascii=False`` keeps non-ASCII characters unescaped
        so locale-varying bodies (e.g. ar/fa ``user_id``) hash the
        same byte-for-byte as their native representation."""
        raw = canonical_json_bytes({"name": "علي"})
        assert "علي" in raw.decode("utf-8")


class TestHashPydantic:
    def test_same_model_same_hash(self) -> None:
        class M(BaseModel):
            a: int
            b: str

        m1 = M(a=1, b="x")
        m2 = M(a=1, b="x")
        assert hash_pydantic(m1) == hash_pydantic(m2)

    def test_different_field_values_differ(self) -> None:
        class M(BaseModel):
            a: int

        assert hash_pydantic(M(a=1)) != hash_pydantic(M(a=2))

    def test_hash_is_hex_sha256(self) -> None:
        """64 hex chars = 256-bit SHA-256 digest.  A regression to a
        different algorithm (MD5, blake2) would still look 'like a
        hash' — this test pins the length."""

        class M(BaseModel):
            a: int

        digest = hash_pydantic(M(a=1))
        assert len(digest) == 64
        assert all(c in "0123456789abcdef" for c in digest)


# ---- Core lookup/store contract ------------------------------------------


def _fixed_clock(value: datetime) -> Any:
    """Return a clock function that always yields ``value``.

    Separate helper so tests can mutate a cell across timestep-advancing
    tests without a mutable closure."""
    return lambda: value


class TestLookup:
    def test_missing_key_returns_miss(self) -> None:
        store = IdempotencyStore()
        assert isinstance(store.lookup("never-seen", "hash-a"), Miss)

    def test_stored_key_same_hash_returns_hit(self) -> None:
        store = IdempotencyStore()
        store.store("k1", "hash-a", {"result": 42})
        result = store.lookup("k1", "hash-a")
        assert isinstance(result, Hit)
        assert result.response == {"result": 42}

    def test_stored_key_different_hash_returns_conflict(self) -> None:
        """Same key + different body hash = Conflict — the 409 signal."""
        store = IdempotencyStore()
        store.store("k1", "hash-a", {"result": 1})
        assert isinstance(store.lookup("k1", "hash-b"), Conflict)

    def test_conflict_does_not_expose_stored_hash(self) -> None:
        """Conflict carries no data — a side-channel that exposed the
        stored body hash would let a probing client enumerate other
        users' request hashes at the same key."""
        store = IdempotencyStore()
        store.store("k1", "hash-a", {"result": 1})
        result = store.lookup("k1", "hash-b")
        assert isinstance(result, Conflict)
        # The dataclass has no fields; can't read the hash off it.
        assert not hasattr(result, "body_hash")
        assert not hasattr(result, "stored_hash")

    def test_empty_key_raises(self) -> None:
        """An empty idempotency key is a client bug — surfacing it
        here prevents a malformed client from poisoning the cache
        under the empty-string key."""
        store = IdempotencyStore()
        with pytest.raises(ValueError, match="non-empty"):
            store.lookup("", "hash-a")


class TestStore:
    def test_store_then_lookup_round_trip(self) -> None:
        store = IdempotencyStore()
        response = {"assessment_id": "abc", "total": 5}
        store.store("k1", "hash-a", response)
        result = store.lookup("k1", "hash-a")
        assert isinstance(result, Hit)
        assert result.response is response  # identity, not just equality

    def test_store_overwrites_expired_entry(self) -> None:
        """An expired entry is effectively gone — the next store under
        the same key must succeed even with a different body hash."""
        clock = _fixed_clock(datetime(2026, 4, 18, tzinfo=UTC))
        store = IdempotencyStore(ttl_seconds=60, now_fn=clock)
        store.store("k1", "hash-a", "first")
        # Advance past expiry.
        store._now = _fixed_clock(  # type: ignore[method-assign]
            datetime(2026, 4, 18, 0, 2, tzinfo=UTC)
        )
        # Same key, different hash — must succeed (not ConflictOnStoreError).
        store.store("k1", "hash-b", "second")
        result = store.lookup("k1", "hash-b")
        assert isinstance(result, Hit)
        assert result.response == "second"

    def test_store_with_conflicting_hash_on_live_entry_raises(self) -> None:
        """Belt-and-braces — callers that skipped the pre-lookup MUST
        NOT overwrite a live entry.  The exception here exposes the
        caller bug rather than silently losing the earlier response."""
        store = IdempotencyStore()
        store.store("k1", "hash-a", "first")
        with pytest.raises(ConflictOnStoreError):
            store.store("k1", "hash-b", "second")
        # Original entry untouched.
        result = store.lookup("k1", "hash-a")
        assert isinstance(result, Hit)
        assert result.response == "first"

    def test_store_with_same_hash_refreshes_response(self) -> None:
        """Idempotent over the same (key, hash) — storing twice with
        the same hash is a no-op from the caller's perspective.  We
        still overwrite the stored response (e.g. the router's retry
        might have produced a fresh AssessmentResult instance)."""
        store = IdempotencyStore()
        store.store("k1", "hash-a", "v1")
        store.store("k1", "hash-a", "v2")
        result = store.lookup("k1", "hash-a")
        assert isinstance(result, Hit)
        assert result.response == "v2"

    def test_empty_key_raises(self) -> None:
        store = IdempotencyStore()
        with pytest.raises(ValueError, match="non-empty"):
            store.store("", "hash-a", "v")


# ---- TTL expiry ----------------------------------------------------------


class TestTtlExpiry:
    def test_entry_returns_hit_before_expiry(self) -> None:
        start = datetime(2026, 4, 18, 12, 0, 0, tzinfo=UTC)
        store = IdempotencyStore(ttl_seconds=60, now_fn=_fixed_clock(start))
        store.store("k1", "hash-a", "ok")
        # 59 s later — still within TTL.
        store._now = _fixed_clock(start + timedelta(seconds=59))  # type: ignore[method-assign]
        assert isinstance(store.lookup("k1", "hash-a"), Hit)

    def test_entry_returns_miss_after_expiry(self) -> None:
        start = datetime(2026, 4, 18, 12, 0, 0, tzinfo=UTC)
        store = IdempotencyStore(ttl_seconds=60, now_fn=_fixed_clock(start))
        store.store("k1", "hash-a", "ok")
        # 61 s later — past TTL.
        store._now = _fixed_clock(start + timedelta(seconds=61))  # type: ignore[method-assign]
        assert isinstance(store.lookup("k1", "hash-a"), Miss)

    def test_expired_entry_evicted_in_band(self) -> None:
        """Lookup of an expired entry purges it.  Pins that we don't
        accumulate expired entries forever."""
        start = datetime(2026, 4, 18, 12, 0, 0, tzinfo=UTC)
        store = IdempotencyStore(ttl_seconds=60, now_fn=_fixed_clock(start))
        store.store("k1", "hash-a", "ok")
        assert len(store) == 1
        store._now = _fixed_clock(start + timedelta(seconds=61))  # type: ignore[method-assign]
        store.lookup("k1", "hash-a")
        assert len(store) == 0

    def test_expired_entry_then_different_hash_is_miss_not_conflict(self) -> None:
        """After expiry the key is re-usable — a different body hash
        at the same key is a fresh request, not a Conflict."""
        start = datetime(2026, 4, 18, 12, 0, 0, tzinfo=UTC)
        store = IdempotencyStore(ttl_seconds=60, now_fn=_fixed_clock(start))
        store.store("k1", "hash-a", "first")
        store._now = _fixed_clock(start + timedelta(seconds=120))  # type: ignore[method-assign]
        assert isinstance(store.lookup("k1", "hash-b"), Miss)

    def test_default_ttl_is_24_hours(self) -> None:
        """24-hour default matches CLAUDE.md §'how to make changes' —
        the retry window for a flaky client connection without
        extending PHI exposure."""
        store = IdempotencyStore()
        assert store.ttl_seconds == 24 * 60 * 60

    def test_zero_ttl_rejected(self) -> None:
        """TTL of 0 would make every entry expire immediately — a
        cache that always misses.  Surfaces the misconfiguration."""
        with pytest.raises(ValueError, match="positive"):
            IdempotencyStore(ttl_seconds=0)

    def test_negative_ttl_rejected(self) -> None:
        with pytest.raises(ValueError, match="positive"):
            IdempotencyStore(ttl_seconds=-1)


# ---- Clear + length ------------------------------------------------------


class TestClear:
    def test_clear_empties_store(self) -> None:
        store = IdempotencyStore()
        store.store("k1", "h1", "a")
        store.store("k2", "h2", "b")
        assert len(store) == 2
        store.clear()
        assert len(store) == 0
        assert isinstance(store.lookup("k1", "h1"), Miss)


# ---- Module-level default store ------------------------------------------


class TestDefaultStore:
    def test_get_returns_singleton(self) -> None:
        a = get_idempotency_store()
        b = get_idempotency_store()
        assert a is b

    def test_reset_replaces_singleton(self) -> None:
        a = get_idempotency_store()
        reset_default_store()
        b = get_idempotency_store()
        assert a is not b

    def test_reset_drops_all_entries(self) -> None:
        get_idempotency_store().store("k1", "h1", "ok")
        reset_default_store()
        assert len(get_idempotency_store()) == 0


# ---- Multi-key isolation -------------------------------------------------


class TestMultiKeyIsolation:
    def test_different_keys_dont_collide(self) -> None:
        """Two independent keys must never see each other's entries."""
        store = IdempotencyStore()
        store.store("k1", "h1", "v1")
        store.store("k2", "h1", "v2")  # same body hash, different key
        r1 = store.lookup("k1", "h1")
        r2 = store.lookup("k2", "h1")
        assert isinstance(r1, Hit) and r1.response == "v1"
        assert isinstance(r2, Hit) and r2.response == "v2"

    def test_same_body_different_key_not_a_conflict(self) -> None:
        """Body hash alone doesn't identify an operation — the
        (key, body_hash) tuple does.  Two independent clients may
        submit semantically identical bodies under different keys."""
        store = IdempotencyStore()
        store.store("k1", "h1", "first")
        assert isinstance(store.lookup("k2", "h1"), Miss)

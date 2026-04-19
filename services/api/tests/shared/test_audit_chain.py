"""Merkle-chained audit log tests (CLAUDE.md Rule #6).

The audit stream's tamper-evidence is load-bearing for HIPAA: if any
record is altered or dropped, every subsequent record's ``chain_hash``
stops matching the expected HMAC.  These tests exercise that property
and pin the semantics so a refactor can't silently weaken the chain.

Test structure mirrors the three layers of the system:
- **Pure chain math** — :func:`compute_chain_hash`, :func:`verify_chain`
- **Stream isolation** — audit + safety streams advance independently
- **Integration** — the structlog processor writes the expected fields
"""

from __future__ import annotations

import hashlib
import hmac
from typing import Any

import pytest

from discipline.shared.logging import (
    GENESIS_SENTINEL,
    LogStream,
    compute_chain_hash,
    get_stream_logger,
    reset_chain_state,
    verify_chain,
)
from discipline.shared.logging.streams import _chain_processor, _record_for_chain


# ---- Fixtures --------------------------------------------------------------


@pytest.fixture(autouse=True)
def _isolated_chain_state() -> None:
    """Clear the in-memory Merkle state between tests so one test's chain
    doesn't bleed into the next.  In production the state is persisted;
    in tests we want fresh start + isolation."""
    reset_chain_state()
    yield
    reset_chain_state()


def _make_record(timestamp: str, event: str) -> dict[str, Any]:
    return {"timestamp": timestamp, "event": event}


# =============================================================================
# Pure chain math
# =============================================================================


class TestComputeChainHash:
    def test_deterministic_for_same_inputs(self) -> None:
        """Given identical (prev_hash, record, secret), the output is
        identical — this is table-stakes for HMAC but pinning it here
        prevents a future "optimization" that introduces nondeterminism."""
        a = compute_chain_hash("abc", "2026-04-18T12:00:00Z|phi.access", secret=b"s")
        b = compute_chain_hash("abc", "2026-04-18T12:00:00Z|phi.access", secret=b"s")
        assert a == b

    def test_different_secret_different_hash(self) -> None:
        """Changing the secret must change every downstream hash — this is
        what makes the chain tamper-evident without shared secrets."""
        a = compute_chain_hash("abc", "x", secret=b"s1")
        b = compute_chain_hash("abc", "x", secret=b"s2")
        assert a != b

    def test_different_prev_hash_different_chain_hash(self) -> None:
        a = compute_chain_hash("prev-a", "x", secret=b"s")
        b = compute_chain_hash("prev-b", "x", secret=b"s")
        assert a != b

    def test_different_record_different_chain_hash(self) -> None:
        a = compute_chain_hash("abc", "record-a", secret=b"s")
        b = compute_chain_hash("abc", "record-b", secret=b"s")
        assert a != b

    def test_matches_reference_hmac(self) -> None:
        """Lock the exact algorithm.  If this assertion breaks, the chain
        format has changed — every existing archive is now unverifiable
        and a migration with a chain-version marker is required."""
        secret = b"test-secret"
        prev = "genesis"
        record = "2026-04-18T12:00:00Z|phi.access"
        expected = hmac.new(
            secret, (prev + "\n" + record).encode("utf-8"), hashlib.sha256
        ).hexdigest()
        assert compute_chain_hash(prev, record, secret=secret) == expected

    def test_genesis_sentinel_is_the_string_genesis(self) -> None:
        """The sentinel value is not all-zeros; it's the literal word
        ``genesis``.  Pinned so a replay verifier expecting one doesn't
        silently accept the other."""
        assert GENESIS_SENTINEL == "genesis"


# =============================================================================
# verify_chain replay
# =============================================================================


class TestVerifyChain:
    def test_empty_chain_is_valid(self) -> None:
        """No records means no broken links — a fresh audit stream verifies
        clean before any events arrive."""
        assert verify_chain([]) == []

    def test_single_record_chain_validates(self) -> None:
        """One valid record chained off genesis.  Baseline for replay."""
        secret = b"s"
        rec = _make_record("2026-04-18T00:00:00Z", "phi.access.ok")
        record_str = _record_for_chain(rec)
        rec["prev_hash"] = GENESIS_SENTINEL
        rec["chain_hash"] = compute_chain_hash(GENESIS_SENTINEL, record_str, secret=secret)
        assert verify_chain([rec], secret=secret) == []

    def test_multi_record_valid_chain(self) -> None:
        """Three consecutive records, each properly chained, all verify."""
        secret = b"s"
        records: list[dict[str, Any]] = []
        prev = GENESIS_SENTINEL
        for i in range(3):
            rec = _make_record(f"2026-04-18T00:0{i}:00Z", f"event.{i}")
            record_str = _record_for_chain(rec)
            rec["prev_hash"] = prev
            rec["chain_hash"] = compute_chain_hash(prev, record_str, secret=secret)
            records.append(rec)
            prev = rec["chain_hash"]
        assert verify_chain(records, secret=secret) == []

    def test_tampered_record_content_detected(self) -> None:
        """Flipping the event string of a record must break that record's
        chain_hash — this is the core tamper-evidence guarantee."""
        secret = b"s"
        records: list[dict[str, Any]] = []
        prev = GENESIS_SENTINEL
        for i in range(3):
            rec = _make_record(f"2026-04-18T00:0{i}:00Z", f"event.{i}")
            rec["prev_hash"] = prev
            rec["chain_hash"] = compute_chain_hash(
                prev, _record_for_chain(rec), secret=secret
            )
            records.append(rec)
            prev = rec["chain_hash"]
        # Attacker edits the middle record's event.
        records[1]["event"] = "event.1.TAMPERED"
        broken = verify_chain(records, secret=secret)
        assert 1 in broken

    def test_tampered_prev_hash_detected(self) -> None:
        """A dropped record is detectable because its neighbor's
        prev_hash no longer matches."""
        secret = b"s"
        records: list[dict[str, Any]] = []
        prev = GENESIS_SENTINEL
        for i in range(2):
            rec = _make_record(f"2026-04-18T00:0{i}:00Z", f"event.{i}")
            rec["prev_hash"] = prev
            rec["chain_hash"] = compute_chain_hash(
                prev, _record_for_chain(rec), secret=secret
            )
            records.append(rec)
            prev = rec["chain_hash"]
        # Tamper: overwrite prev_hash on record[1].
        records[1]["prev_hash"] = "fabricated-prev"
        broken = verify_chain(records, secret=secret)
        assert 1 in broken

    def test_wrong_secret_breaks_every_record(self) -> None:
        """A verifier using the wrong secret sees every record as broken —
        because HMAC with a different key produces different hashes.
        This is what catches an adversary who rebuilds a chain with their
        own secret after deleting originals."""
        good_secret = b"production-secret"
        bad_secret = b"attacker-secret"
        records: list[dict[str, Any]] = []
        prev = GENESIS_SENTINEL
        for i in range(3):
            rec = _make_record(f"t{i}", f"e.{i}")
            rec["prev_hash"] = prev
            rec["chain_hash"] = compute_chain_hash(
                prev, _record_for_chain(rec), secret=good_secret
            )
            records.append(rec)
            prev = rec["chain_hash"]
        broken = verify_chain(records, secret=bad_secret)
        assert broken == [0, 1, 2]


# =============================================================================
# Stream isolation
# =============================================================================


class TestStreamIsolation:
    def test_audit_and_safety_chains_are_independent(self) -> None:
        """Writing to the audit stream must NOT advance the safety
        stream's chain, or a busy audit load could mask a dropped safety
        event during replay."""
        reset_chain_state()
        audit_proc = _chain_processor(LogStream.AUDIT)
        safety_proc = _chain_processor(LogStream.SAFETY)

        audit_rec1 = {"timestamp": "t1", "event": "audit.1"}
        audit_proc(None, "info", audit_rec1)
        safety_rec1 = {"timestamp": "t1", "event": "safety.1"}
        safety_proc(None, "info", safety_rec1)

        # Both should start from genesis independently.
        assert audit_rec1["prev_hash"] == GENESIS_SENTINEL
        assert safety_rec1["prev_hash"] == GENESIS_SENTINEL
        # And produce different chain_hashes (different record content,
        # same prev — so chain_hash must differ).
        assert audit_rec1["chain_hash"] != safety_rec1["chain_hash"]

    def test_second_audit_event_chains_off_first(self) -> None:
        reset_chain_state()
        audit_proc = _chain_processor(LogStream.AUDIT)
        rec1 = {"timestamp": "t1", "event": "a"}
        audit_proc(None, "info", rec1)
        rec2 = {"timestamp": "t2", "event": "b"}
        audit_proc(None, "info", rec2)
        assert rec2["prev_hash"] == rec1["chain_hash"]


# =============================================================================
# Stream level floors
# =============================================================================


class TestStreamLevels:
    """Audit, safety, and security streams must always run at INFO+ so no
    events fall below the retention bar.  A misconfiguration that set
    LOG_LEVEL=ERROR must not silently drop audit INFOs."""

    def test_audit_logger_emits_info(self) -> None:
        reset_chain_state()
        logger = get_stream_logger(LogStream.AUDIT)
        # Calling info should not raise; if the filter level were too high
        # structlog would no-op but the processor wouldn't have run — we
        # can detect that by re-reading the chain state.
        logger.info("audit.probe")
        # Reset and re-probe: the state must have advanced.
        from discipline.shared.logging.streams import _MERKLE_CHAIN_STATE

        assert LogStream.AUDIT in _MERKLE_CHAIN_STATE

    def test_safety_logger_emits_info(self) -> None:
        reset_chain_state()
        logger = get_stream_logger(LogStream.SAFETY)
        logger.info("safety.probe")
        from discipline.shared.logging.streams import _MERKLE_CHAIN_STATE

        assert LogStream.SAFETY in _MERKLE_CHAIN_STATE


# =============================================================================
# reset_chain_state helper
# =============================================================================


class TestResetChainState:
    def test_reset_all_clears_every_stream(self) -> None:
        audit_proc = _chain_processor(LogStream.AUDIT)
        safety_proc = _chain_processor(LogStream.SAFETY)
        audit_proc(None, "info", {"timestamp": "t", "event": "a"})
        safety_proc(None, "info", {"timestamp": "t", "event": "s"})

        from discipline.shared.logging.streams import _MERKLE_CHAIN_STATE

        assert len(_MERKLE_CHAIN_STATE) >= 2

        reset_chain_state()
        assert _MERKLE_CHAIN_STATE == {}

    def test_reset_single_stream_leaves_others(self) -> None:
        reset_chain_state()
        audit_proc = _chain_processor(LogStream.AUDIT)
        safety_proc = _chain_processor(LogStream.SAFETY)
        audit_proc(None, "info", {"timestamp": "t", "event": "a"})
        safety_proc(None, "info", {"timestamp": "t", "event": "s"})

        reset_chain_state(LogStream.AUDIT)

        from discipline.shared.logging.streams import _MERKLE_CHAIN_STATE

        assert LogStream.AUDIT not in _MERKLE_CHAIN_STATE
        assert LogStream.SAFETY in _MERKLE_CHAIN_STATE


# =============================================================================
# End-to-end: emit 3 events, verify as a chain
# =============================================================================


class TestEndToEndChain:
    def test_three_emits_produce_verifiable_chain(self) -> None:
        """Drive the processor directly (not through structlog) to capture
        records and then run verify_chain over them.  The chain must
        verify clean."""
        reset_chain_state()
        audit_proc = _chain_processor(LogStream.AUDIT)
        records: list[dict[str, Any]] = []
        for i in range(3):
            rec = {"timestamp": f"2026-04-18T00:0{i}:00Z", "event": f"phi.access.{i}"}
            audit_proc(None, "info", rec)
            records.append(rec)

        # Replay with the same secret (set by conftest) — chain intact.
        broken = verify_chain(records)
        assert broken == []

    def test_tampering_post_emit_detected_by_verifier(self) -> None:
        reset_chain_state()
        audit_proc = _chain_processor(LogStream.AUDIT)
        records: list[dict[str, Any]] = []
        for i in range(3):
            rec = {"timestamp": f"t{i}", "event": f"e.{i}"}
            audit_proc(None, "info", rec)
            records.append(rec)

        # Attacker modifies record[1]'s event AFTER emit.
        records[1]["event"] = "e.1.ALTERED"
        broken = verify_chain(records)
        assert 1 in broken

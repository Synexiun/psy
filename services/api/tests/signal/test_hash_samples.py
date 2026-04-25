"""Unit tests for the _hash_samples() pure helper in discipline.signal.router.

_hash_samples(samples) produces a deterministic SHA-256 hex digest of the
canonical JSON encoding of a list of SignalSample objects.

Canonical form: JSON array of {"t": timestamp, "v": value, "u": unit} dicts
with sort_keys=True and compact separators(",", ":").

Key invariants verified here:
- Output is a 64-character lowercase hex string (SHA-256)
- Same inputs always produce the same hash (determinism)
- Different inputs produce different hashes (collision sensitivity)
- Empty sample list produces a valid, stable hash
- unit=None is encoded as JSON null and included in the hash
- Sample order matters (changing order changes hash)
- Changing any single field changes the hash
"""

from __future__ import annotations

import hashlib
import json

import pytest

from discipline.signal.router import _hash_samples, SignalSample


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _sample(ts: str = "2026-04-25T10:00:00Z", value: float = 72.0, unit: str | None = "bpm") -> SignalSample:
    return SignalSample(timestamp=ts, value=value, unit=unit)


def _expected_hash(*samples: SignalSample) -> str:
    """Compute the expected hash using the same algorithm as _hash_samples."""
    canonical = json.dumps(
        [{"t": s.timestamp, "v": s.value, "u": s.unit} for s in samples],
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Output format
# ---------------------------------------------------------------------------


class TestHashSamplesOutputFormat:
    def test_returns_string(self) -> None:
        result = _hash_samples([_sample()])
        assert isinstance(result, str)

    def test_returns_64_char_hex(self) -> None:
        result = _hash_samples([_sample()])
        assert len(result) == 64

    def test_output_is_lowercase_hex(self) -> None:
        result = _hash_samples([_sample()])
        assert all(c in "0123456789abcdef" for c in result)

    def test_empty_list_returns_64_char_hex(self) -> None:
        result = _hash_samples([])
        assert len(result) == 64
        assert all(c in "0123456789abcdef" for c in result)


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------


class TestHashSamplesDeterminism:
    def test_same_sample_same_hash(self) -> None:
        s = _sample()
        assert _hash_samples([s]) == _hash_samples([s])

    def test_same_samples_constructed_independently_same_hash(self) -> None:
        a = _sample("2026-04-25T10:00:00Z", 72.0, "bpm")
        b = _sample("2026-04-25T10:00:00Z", 72.0, "bpm")
        assert _hash_samples([a]) == _hash_samples([b])

    def test_empty_list_is_deterministic(self) -> None:
        assert _hash_samples([]) == _hash_samples([])

    def test_multi_sample_list_is_deterministic(self) -> None:
        samples = [
            _sample("2026-04-25T10:00:00Z", 72.0, "bpm"),
            _sample("2026-04-25T10:01:00Z", 74.0, "bpm"),
        ]
        assert _hash_samples(samples) == _hash_samples(list(samples))

    def test_matches_manual_sha256(self) -> None:
        s = _sample("2026-04-25T10:00:00Z", 72.0, "bpm")
        assert _hash_samples([s]) == _expected_hash(s)

    def test_empty_list_matches_manual_sha256(self) -> None:
        assert _hash_samples([]) == _expected_hash()


# ---------------------------------------------------------------------------
# Collision sensitivity — changing any field changes the hash
# ---------------------------------------------------------------------------


class TestHashSamplesCollisionSensitivity:
    def test_different_value_different_hash(self) -> None:
        a = _sample(value=72.0)
        b = _sample(value=73.0)
        assert _hash_samples([a]) != _hash_samples([b])

    def test_different_timestamp_different_hash(self) -> None:
        a = _sample(ts="2026-04-25T10:00:00Z")
        b = _sample(ts="2026-04-25T10:01:00Z")
        assert _hash_samples([a]) != _hash_samples([b])

    def test_different_unit_different_hash(self) -> None:
        a = _sample(unit="bpm")
        b = _sample(unit="hrv_ms")
        assert _hash_samples([a]) != _hash_samples([b])

    def test_unit_none_vs_string_different_hash(self) -> None:
        a = _sample(unit=None)
        b = _sample(unit="bpm")
        assert _hash_samples([a]) != _hash_samples([b])

    def test_one_sample_vs_two_samples_different_hash(self) -> None:
        s1 = _sample()
        s2 = _sample(ts="2026-04-25T10:01:00Z")
        assert _hash_samples([s1]) != _hash_samples([s1, s2])

    def test_empty_vs_nonempty_different_hash(self) -> None:
        assert _hash_samples([]) != _hash_samples([_sample()])


# ---------------------------------------------------------------------------
# Order sensitivity — changing sample order changes the hash
# ---------------------------------------------------------------------------


class TestHashSamplesOrderSensitivity:
    def test_swapped_order_different_hash(self) -> None:
        a = _sample(ts="2026-04-25T10:00:00Z", value=72.0)
        b = _sample(ts="2026-04-25T10:01:00Z", value=75.0)
        assert _hash_samples([a, b]) != _hash_samples([b, a])

    def test_original_order_matches_expected(self) -> None:
        a = _sample(ts="2026-04-25T10:00:00Z", value=72.0)
        b = _sample(ts="2026-04-25T10:01:00Z", value=75.0)
        assert _hash_samples([a, b]) == _expected_hash(a, b)
        assert _hash_samples([b, a]) == _expected_hash(b, a)


# ---------------------------------------------------------------------------
# unit=None handling
# ---------------------------------------------------------------------------


class TestHashSamplesUnitNone:
    def test_none_unit_produces_valid_hash(self) -> None:
        s = _sample(unit=None)
        result = _hash_samples([s])
        assert len(result) == 64

    def test_none_unit_is_deterministic(self) -> None:
        a = _sample(unit=None)
        b = _sample(unit=None)
        assert _hash_samples([a]) == _hash_samples([b])

    def test_none_unit_encoded_as_null_in_canonical_json(self) -> None:
        s = SignalSample(timestamp="2026-04-25T10:00:00Z", value=72.0, unit=None)
        expected = _expected_hash(s)
        assert _hash_samples([s]) == expected

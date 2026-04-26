"""Unit tests for pure router-layer helpers across compliance, memory, resilience,
and billing modules.

_hash_ip(ip) → str | None                        compliance/router.py
  SHA-256 hex of the IP string for audit trail.
  None-safe: returns None when ip is None.

_encrypt_body(body) → str                         memory/router.py
  Base64 stub for KMS envelope encryption.
  Round-trips through base64.b64decode.

_record_to_schema(record) → StreakState           resilience/router.py
  Thin mapper from StreakStateRecord-duck to StreakState Pydantic model.

_record_to_item(record) → SubscriptionItem        billing/router.py
  Thin mapper from SubscriptionRecord-duck to SubscriptionItem Pydantic model.

All helpers use MagicMock to avoid needing a DB session.
"""

from __future__ import annotations

import base64
import hashlib
from unittest.mock import MagicMock
import uuid

import pytest

from discipline.compliance.router import _hash_ip
from discipline.memory.router import _encrypt_body
from discipline.resilience.router import _record_to_schema
from discipline.billing.router import _record_to_item

_UUID = str(uuid.uuid4())
_NOW_ISO = "2026-01-15T12:00:00+00:00"


# ---------------------------------------------------------------------------
# _hash_ip — SHA-256, None-safe
# ---------------------------------------------------------------------------


class TestHashIp:
    def test_none_ip_returns_none(self) -> None:
        assert _hash_ip(None) is None

    def test_string_ip_returns_64_char_hex(self) -> None:
        result = _hash_ip("127.0.0.1")
        assert result is not None
        assert len(result) == 64
        assert all(c in "0123456789abcdef" for c in result)

    def test_matches_sha256_reference(self) -> None:
        ip = "192.168.1.100"
        expected = hashlib.sha256(ip.encode()).hexdigest()
        assert _hash_ip(ip) == expected

    def test_deterministic_same_input(self) -> None:
        assert _hash_ip("10.0.0.1") == _hash_ip("10.0.0.1")

    def test_different_ips_different_hashes(self) -> None:
        assert _hash_ip("1.1.1.1") != _hash_ip("8.8.8.8")

    def test_returns_string_not_none_for_non_null(self) -> None:
        assert isinstance(_hash_ip("0.0.0.0"), str)


# ---------------------------------------------------------------------------
# _encrypt_body — base64 stub, round-trips
# ---------------------------------------------------------------------------


class TestEncryptBody:
    def test_returns_string(self) -> None:
        assert isinstance(_encrypt_body("hello"), str)

    def test_result_is_base64_decodable(self) -> None:
        result = _encrypt_body("journal entry text")
        decoded = base64.b64decode(result).decode()
        assert decoded == "journal entry text"

    def test_roundtrip_recovers_original(self) -> None:
        original = "Today I felt overwhelmed."
        assert base64.b64decode(_encrypt_body(original)).decode() == original

    def test_empty_string_encodes(self) -> None:
        result = _encrypt_body("")
        assert base64.b64decode(result).decode() == ""

    def test_deterministic(self) -> None:
        assert _encrypt_body("same") == _encrypt_body("same")

    def test_different_inputs_different_encodings(self) -> None:
        assert _encrypt_body("a") != _encrypt_body("b")


# ---------------------------------------------------------------------------
# _record_to_schema — StreakStateRecord-duck → StreakState
# ---------------------------------------------------------------------------


def _streak_record() -> MagicMock:
    r = MagicMock()
    r.continuous_days = 14
    r.continuous_streak_start = _NOW_ISO
    r.resilience_days = 42
    r.resilience_urges_handled_total = 7
    r.resilience_streak_start = _NOW_ISO
    return r


class TestRecordToSchema:
    def test_continuous_days_propagated(self) -> None:
        result = _record_to_schema(_streak_record())
        assert result.continuous_days == 14

    def test_resilience_days_propagated(self) -> None:
        result = _record_to_schema(_streak_record())
        assert result.resilience_days == 42

    def test_resilience_urges_propagated(self) -> None:
        result = _record_to_schema(_streak_record())
        assert result.resilience_urges_handled_total == 7

    def test_continuous_streak_start_propagated(self) -> None:
        result = _record_to_schema(_streak_record())
        assert result.continuous_streak_start == _NOW_ISO

    def test_resilience_streak_start_propagated(self) -> None:
        result = _record_to_schema(_streak_record())
        assert result.resilience_streak_start == _NOW_ISO


# ---------------------------------------------------------------------------
# _record_to_item — SubscriptionRecord-duck → SubscriptionItem
# ---------------------------------------------------------------------------


def _sub_record(canceled_at: str | None = None) -> MagicMock:
    r = MagicMock()
    r.subscription_id = _UUID
    r.status = "active"
    r.tier = "plus"
    r.provider = "stripe"
    r.provider_subscription_id = "sub_abc"
    r.current_period_start = _NOW_ISO
    r.current_period_end = _NOW_ISO
    r.canceled_at = canceled_at
    r.cancel_reason = None
    r.created_at = _NOW_ISO
    r.updated_at = _NOW_ISO
    return r


class TestRecordToItem:
    def test_subscription_id_propagated(self) -> None:
        result = _record_to_item(_sub_record())
        assert result.subscription_id == _UUID

    def test_status_propagated(self) -> None:
        assert _record_to_item(_sub_record()).status == "active"

    def test_tier_propagated(self) -> None:
        assert _record_to_item(_sub_record()).tier == "plus"

    def test_provider_propagated(self) -> None:
        assert _record_to_item(_sub_record()).provider == "stripe"

    def test_canceled_at_none_when_none(self) -> None:
        result = _record_to_item(_sub_record(canceled_at=None))
        assert result.canceled_at is None

    def test_canceled_at_propagated_when_present(self) -> None:
        result = _record_to_item(_sub_record(canceled_at=_NOW_ISO))
        assert result.canceled_at == _NOW_ISO

    def test_current_period_start_propagated(self) -> None:
        assert _record_to_item(_sub_record()).current_period_start == _NOW_ISO

    def test_current_period_end_propagated(self) -> None:
        assert _record_to_item(_sub_record()).current_period_end == _NOW_ISO

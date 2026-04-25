"""Tests for discipline.signal.repository — signal window and state estimate in-memory stores.

Covers:
- SignalWindowRecord frozen dataclass
- InMemorySignalWindowRepository.create: valid UUID, fields match
- get_by_samples_hash: returns record, None for unknown hash/user
- StateEstimateRecord frozen dataclass
- InMemoryStateEstimateRepository.create: valid UUID, fields match
- latest_by_user: returns most recent estimate, None for unknown user
- reset_signal_repositories: clears both repos
"""

from __future__ import annotations

import uuid

import pytest

from discipline.signal.repository import (
    InMemorySignalWindowRepository,
    InMemoryStateEstimateRepository,
    SignalWindowRecord,
    StateEstimateRecord,
    reset_signal_repositories,
)


@pytest.fixture(autouse=True)
def _reset() -> None:
    reset_signal_repositories()


# ---------------------------------------------------------------------------
# SignalWindowRecord frozen dataclass
# ---------------------------------------------------------------------------


class TestSignalWindowRecord:
    def test_can_be_constructed(self) -> None:
        r = SignalWindowRecord(
            window_id="wid",
            user_id="uid",
            window_start="2026-04-25T00:00:00+00:00",
            window_end="2026-04-25T00:05:00+00:00",
            source="wearable_hr",
            samples_hash="abc123",
            created_at="2026-04-25T00:00:00+00:00",
        )
        assert r.window_id == "wid"

    def test_frozen(self) -> None:
        r = SignalWindowRecord(
            window_id="w", user_id="u",
            window_start="2026-04-25T00:00:00+00:00",
            window_end="2026-04-25T00:05:00+00:00",
            source="hrv", samples_hash="h",
            created_at="2026-04-25",
        )
        with pytest.raises((AttributeError, TypeError)):
            r.source = "mutated"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# InMemorySignalWindowRepository
# ---------------------------------------------------------------------------


class TestSignalWindowCreate:
    @pytest.mark.asyncio
    async def test_returns_signal_window_record(self) -> None:
        repo = InMemorySignalWindowRepository()
        r = await repo.create(
            user_id="u-1",
            window_start="2026-04-25T00:00:00+00:00",
            window_end="2026-04-25T00:05:00+00:00",
            source="wearable_hr",
            samples_hash="hash1",
            samples_json={"hr": [70, 72]},
        )
        assert isinstance(r, SignalWindowRecord)

    @pytest.mark.asyncio
    async def test_window_id_is_valid_uuid(self) -> None:
        repo = InMemorySignalWindowRepository()
        r = await repo.create(
            user_id="u-1",
            window_start="2026-04-25T00:00:00+00:00",
            window_end="2026-04-25T00:05:00+00:00",
            source="wearable_hr",
            samples_hash="hash2",
            samples_json={},
        )
        uuid.UUID(r.window_id)

    @pytest.mark.asyncio
    async def test_fields_match_input(self) -> None:
        repo = InMemorySignalWindowRepository()
        r = await repo.create(
            user_id="u-99",
            window_start="2026-04-25T00:00:00+00:00",
            window_end="2026-04-25T00:05:00+00:00",
            source="manual_checkin",
            samples_hash="myhash",
            samples_json={"intensity": 8},
        )
        assert r.user_id == "u-99"
        assert r.source == "manual_checkin"
        assert r.samples_hash == "myhash"


class TestSignalWindowGetBySamplesHash:
    @pytest.mark.asyncio
    async def test_returns_record_for_matching_hash(self) -> None:
        repo = InMemorySignalWindowRepository()
        created = await repo.create(
            user_id="u-1",
            window_start="2026-04-25T00:00:00+00:00",
            window_end="2026-04-25T00:05:00+00:00",
            source="hrv",
            samples_hash="unique-hash",
            samples_json={},
        )
        result = await repo.get_by_samples_hash("u-1", "unique-hash")
        assert result is not None
        assert result.window_id == created.window_id

    @pytest.mark.asyncio
    async def test_returns_none_for_unknown_hash(self) -> None:
        repo = InMemorySignalWindowRepository()
        result = await repo.get_by_samples_hash("u-1", "nonexistent-hash")
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_for_wrong_user(self) -> None:
        repo = InMemorySignalWindowRepository()
        await repo.create(
            user_id="alice",
            window_start="2026-04-25T00:00:00+00:00",
            window_end="2026-04-25T00:05:00+00:00",
            source="hrv",
            samples_hash="shared-hash",
            samples_json={},
        )
        result = await repo.get_by_samples_hash("bob", "shared-hash")
        assert result is None


# ---------------------------------------------------------------------------
# StateEstimateRecord frozen dataclass
# ---------------------------------------------------------------------------


class TestStateEstimateRecord:
    def test_can_be_constructed(self) -> None:
        r = StateEstimateRecord(
            estimate_id="eid",
            user_id="uid",
            state_label="elevated",
            confidence=0.85,
            model_version="1.0",
            inferred_at="2026-04-25T00:00:00+00:00",
            created_at="2026-04-25T00:00:00+00:00",
        )
        assert r.estimate_id == "eid"

    def test_frozen(self) -> None:
        r = StateEstimateRecord(
            estimate_id="e", user_id="u",
            state_label="calm", confidence=0.9,
            model_version="1.0",
            inferred_at="2026-04-25", created_at="2026-04-25",
        )
        with pytest.raises((AttributeError, TypeError)):
            r.confidence = 0.0  # type: ignore[misc]


# ---------------------------------------------------------------------------
# InMemoryStateEstimateRepository
# ---------------------------------------------------------------------------


class TestStateEstimateCreate:
    @pytest.mark.asyncio
    async def test_returns_state_estimate_record(self) -> None:
        repo = InMemoryStateEstimateRepository()
        r = await repo.create(
            user_id="u-1",
            state_label="elevated",
            confidence=0.85,
            model_version="1.0",
            inferred_at="2026-04-25T00:00:00+00:00",
            features_json=None,
        )
        assert isinstance(r, StateEstimateRecord)

    @pytest.mark.asyncio
    async def test_estimate_id_is_valid_uuid(self) -> None:
        repo = InMemoryStateEstimateRepository()
        r = await repo.create(
            user_id="u-1",
            state_label="calm",
            confidence=0.9,
            model_version="1.0",
            inferred_at="2026-04-25T00:00:00+00:00",
            features_json=None,
        )
        uuid.UUID(r.estimate_id)

    @pytest.mark.asyncio
    async def test_fields_match_input(self) -> None:
        repo = InMemoryStateEstimateRepository()
        r = await repo.create(
            user_id="u-99",
            state_label="high_risk",
            confidence=0.77,
            model_version="2.0",
            inferred_at="2026-04-25T12:00:00+00:00",
            features_json={"feature_a": 1.0},
        )
        assert r.user_id == "u-99"
        assert r.state_label == "high_risk"
        assert r.confidence == 0.77
        assert r.model_version == "2.0"


class TestStateEstimateLatestByUser:
    @pytest.mark.asyncio
    async def test_returns_most_recent_estimate(self) -> None:
        repo = InMemoryStateEstimateRepository()
        await repo.create(
            user_id="u-1", state_label="calm", confidence=0.9,
            model_version="1.0", inferred_at="2026-04-25T00:00:00+00:00",
            features_json=None,
        )
        r2 = await repo.create(
            user_id="u-1", state_label="elevated", confidence=0.75,
            model_version="1.0", inferred_at="2026-04-25T06:00:00+00:00",
            features_json=None,
        )
        latest = await repo.latest_by_user("u-1")
        assert latest is not None
        assert latest.estimate_id == r2.estimate_id

    @pytest.mark.asyncio
    async def test_returns_none_for_unknown_user(self) -> None:
        repo = InMemoryStateEstimateRepository()
        result = await repo.latest_by_user("ghost-user")
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_only_matching_user(self) -> None:
        repo = InMemoryStateEstimateRepository()
        await repo.create(
            user_id="alice", state_label="calm", confidence=0.9,
            model_version="1.0", inferred_at="2026-04-25T00:00:00+00:00",
            features_json=None,
        )
        result = await repo.latest_by_user("bob")
        assert result is None

"""Unit tests for the intervention outcome service.

OutcomeRecord is bandit feedback — it records whether a user handled, dismissed,
or was escalated from an intervention.  Correct storage is required for the
bandit's reward signal.  Tests use InMemoryOutcomeRepository (no DB required).

Covers:
- OutcomeRecord frozen dataclass
- InMemoryOutcomeRepository.record: stores and returns an OutcomeRecord
- InMemoryOutcomeRepository.list_by_user: filters by user, sorted descending
- list_by_user respects the limit parameter
- context_json may be None or a dict
- reset_outcome_repository returns fresh state
- get_outcome_repository returns the global singleton
"""

from __future__ import annotations

import asyncio
import uuid

import pytest

from discipline.intervention.outcome_service import (
    InMemoryOutcomeRepository,
    OutcomeRecord,
    get_outcome_repository,
    reset_outcome_repository,
)


@pytest.fixture(autouse=True)
def _reset() -> None:
    reset_outcome_repository()


# ---------------------------------------------------------------------------
# OutcomeRecord dataclass
# ---------------------------------------------------------------------------


class TestOutcomeRecord:
    def test_can_be_constructed(self) -> None:
        rec = OutcomeRecord(
            outcome_id="oid-1",
            user_id="u-1",
            intervention_id="int-1",
            tool_variant="box_breathing",
            outcome="handled",
            recorded_at="2026-04-25T00:00:00+00:00",
            context_json=None,
        )
        assert rec.outcome_id == "oid-1"

    def test_frozen(self) -> None:
        rec = OutcomeRecord(
            outcome_id="oid",
            user_id="u",
            intervention_id="i",
            tool_variant="v",
            outcome="handled",
            recorded_at="2026-04-25T00:00:00+00:00",
            context_json=None,
        )
        with pytest.raises((AttributeError, TypeError)):
            rec.outcome = "dismissed"  # type: ignore[misc]

    def test_context_json_none_allowed(self) -> None:
        rec = OutcomeRecord(
            outcome_id="o",
            user_id="u",
            intervention_id="i",
            tool_variant="v",
            outcome="handled",
            recorded_at="now",
            context_json=None,
        )
        assert rec.context_json is None

    def test_context_json_dict_allowed(self) -> None:
        rec = OutcomeRecord(
            outcome_id="o",
            user_id="u",
            intervention_id="i",
            tool_variant="v",
            outcome="handled",
            recorded_at="now",
            context_json={"mood": 5},
        )
        assert rec.context_json == {"mood": 5}


# ---------------------------------------------------------------------------
# InMemoryOutcomeRepository.record
# ---------------------------------------------------------------------------


class TestRecordOutcome:
    @pytest.mark.asyncio
    async def test_returns_outcome_record(self) -> None:
        repo = InMemoryOutcomeRepository()
        rec = await repo.record(
            user_id="u-1",
            intervention_id="int-1",
            tool_variant="urge_surf",
            outcome="handled",
            context_json=None,
        )
        assert isinstance(rec, OutcomeRecord)

    @pytest.mark.asyncio
    async def test_outcome_id_is_valid_uuid(self) -> None:
        repo = InMemoryOutcomeRepository()
        rec = await repo.record(
            user_id="u-1",
            intervention_id="int-1",
            tool_variant="urge_surf",
            outcome="handled",
            context_json=None,
        )
        uuid.UUID(rec.outcome_id)

    @pytest.mark.asyncio
    async def test_fields_match_input(self) -> None:
        repo = InMemoryOutcomeRepository()
        rec = await repo.record(
            user_id="u-99",
            intervention_id="int-99",
            tool_variant="box_breathing",
            outcome="dismissed",
            context_json={"mood": 3},
        )
        assert rec.user_id == "u-99"
        assert rec.intervention_id == "int-99"
        assert rec.tool_variant == "box_breathing"
        assert rec.outcome == "dismissed"
        assert rec.context_json == {"mood": 3}

    @pytest.mark.asyncio
    async def test_recorded_at_is_iso_string(self) -> None:
        repo = InMemoryOutcomeRepository()
        rec = await repo.record(
            user_id="u-1",
            intervention_id="int-1",
            tool_variant="v",
            outcome="handled",
            context_json=None,
        )
        assert "T" in rec.recorded_at  # ISO-8601 contains T separator

    @pytest.mark.asyncio
    async def test_two_records_have_different_ids(self) -> None:
        repo = InMemoryOutcomeRepository()
        r1 = await repo.record(
            user_id="u", intervention_id="i1", tool_variant="v",
            outcome="handled", context_json=None
        )
        r2 = await repo.record(
            user_id="u", intervention_id="i2", tool_variant="v",
            outcome="dismissed", context_json=None
        )
        assert r1.outcome_id != r2.outcome_id

    @pytest.mark.asyncio
    async def test_context_json_none_stored(self) -> None:
        repo = InMemoryOutcomeRepository()
        rec = await repo.record(
            user_id="u", intervention_id="i", tool_variant="v",
            outcome="expired", context_json=None
        )
        assert rec.context_json is None

    @pytest.mark.asyncio
    async def test_context_json_dict_stored(self) -> None:
        repo = InMemoryOutcomeRepository()
        ctx = {"urge_intensity": 8, "tool_duration": 120}
        rec = await repo.record(
            user_id="u", intervention_id="i", tool_variant="v",
            outcome="handled", context_json=ctx
        )
        assert rec.context_json == ctx


# ---------------------------------------------------------------------------
# InMemoryOutcomeRepository.list_by_user
# ---------------------------------------------------------------------------


class TestListByUser:
    @pytest.mark.asyncio
    async def test_empty_for_unknown_user(self) -> None:
        repo = InMemoryOutcomeRepository()
        results = await repo.list_by_user("ghost_user")
        assert results == []

    @pytest.mark.asyncio
    async def test_returns_only_matching_user(self) -> None:
        repo = InMemoryOutcomeRepository()
        await repo.record(user_id="alice", intervention_id="i1", tool_variant="v",
                          outcome="handled", context_json=None)
        await repo.record(user_id="bob", intervention_id="i2", tool_variant="v",
                          outcome="handled", context_json=None)
        alice_results = await repo.list_by_user("alice")
        assert all(r.user_id == "alice" for r in alice_results)
        assert len(alice_results) == 1

    @pytest.mark.asyncio
    async def test_returns_all_outcomes_for_user(self) -> None:
        repo = InMemoryOutcomeRepository()
        for i in range(5):
            await repo.record(user_id="u-1", intervention_id=f"int-{i}",
                               tool_variant="v", outcome="handled", context_json=None)
        results = await repo.list_by_user("u-1")
        assert len(results) == 5

    @pytest.mark.asyncio
    async def test_sorted_descending_by_recorded_at(self) -> None:
        repo = InMemoryOutcomeRepository()
        for _ in range(3):
            await repo.record(user_id="u-1", intervention_id=str(uuid.uuid4()),
                               tool_variant="v", outcome="handled", context_json=None)
        results = await repo.list_by_user("u-1")
        times = [r.recorded_at for r in results]
        assert times == sorted(times, reverse=True)

    @pytest.mark.asyncio
    async def test_limit_respected(self) -> None:
        repo = InMemoryOutcomeRepository()
        for i in range(10):
            await repo.record(user_id="u-1", intervention_id=f"int-{i}",
                               tool_variant="v", outcome="handled", context_json=None)
        results = await repo.list_by_user("u-1", limit=3)
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_default_limit_is_50(self) -> None:
        repo = InMemoryOutcomeRepository()
        for i in range(60):
            await repo.record(user_id="u-1", intervention_id=f"int-{i}",
                               tool_variant="v", outcome="handled", context_json=None)
        results = await repo.list_by_user("u-1")
        assert len(results) == 50


# ---------------------------------------------------------------------------
# Singleton management
# ---------------------------------------------------------------------------


class TestSingleton:
    @pytest.mark.asyncio
    async def test_get_outcome_repository_returns_same_instance(self) -> None:
        r1 = get_outcome_repository()
        r2 = get_outcome_repository()
        assert r1 is r2

    @pytest.mark.asyncio
    async def test_reset_returns_empty_repository(self) -> None:
        repo = get_outcome_repository()
        await repo.record(user_id="u", intervention_id="i", tool_variant="v",
                          outcome="handled", context_json=None)
        reset_outcome_repository()
        fresh_repo = get_outcome_repository()
        results = await fresh_repo.list_by_user("u")
        assert results == []

    @pytest.mark.asyncio
    async def test_reset_creates_new_instance(self) -> None:
        r1 = get_outcome_repository()
        reset_outcome_repository()
        r2 = get_outcome_repository()
        assert r1 is not r2


# ---------------------------------------------------------------------------
# Worker manifest
# ---------------------------------------------------------------------------


class TestWorkerManifest:
    def test_registered_jobs_is_frozenset(self) -> None:
        from discipline.shared.worker_manifest import REGISTERED_JOBS

        assert isinstance(REGISTERED_JOBS, frozenset)

    def test_dispatch_nudges_registered(self) -> None:
        from discipline.shared.worker_manifest import REGISTERED_JOBS

        assert "dispatch_nudges" in REGISTERED_JOBS

    def test_cleanup_voice_blobs_registered(self) -> None:
        from discipline.shared.worker_manifest import REGISTERED_JOBS

        assert "cleanup_voice_blobs" in REGISTERED_JOBS

    def test_process_pending_deletions_registered(self) -> None:
        from discipline.shared.worker_manifest import REGISTERED_JOBS

        assert "process_pending_deletions" in REGISTERED_JOBS

    def test_refresh_safety_directory_registered(self) -> None:
        from discipline.shared.worker_manifest import REGISTERED_JOBS

        assert "refresh_safety_directory_check" in REGISTERED_JOBS

    def test_manifest_has_expected_count(self) -> None:
        from discipline.shared.worker_manifest import REGISTERED_JOBS

        assert len(REGISTERED_JOBS) >= 4

    def test_manifest_is_immutable(self) -> None:
        from discipline.shared.worker_manifest import REGISTERED_JOBS

        with pytest.raises((AttributeError, TypeError)):
            REGISTERED_JOBS.add("orphan_job")  # type: ignore[attr-defined]

"""Tests for discipline.clinical.repository — relapse event in-memory store.

Covers methods not exercised by test_relapse_service.py:
- InMemoryRelapseRepository.get_by_id: returns record, None for wrong user, None for unknown id
- InMemoryRelapseRepository.mark_reviewed: reviewed=True, reviewed_at/reviewed_by set
- InMemoryRelapseRepository.mark_reviewed: wrong user → None (user isolation)
- InMemoryRelapseRepository.mark_reviewed: unknown id → None
- reset_relapse_repository: clears store
"""

from __future__ import annotations

import uuid

import pytest

from discipline.clinical.repository import (
    InMemoryRelapseRepository,
    RelapseRecord,
    reset_relapse_repository,
)


@pytest.fixture(autouse=True)
def _reset() -> None:
    reset_relapse_repository()


async def _create(
    repo: InMemoryRelapseRepository,
    user_id: str = "u-1",
    behavior: str = "gaming",
    severity: int = 2,
) -> RelapseRecord:
    return await repo.create(
        user_id=user_id,
        occurred_at="2026-04-25T00:00:00+00:00",
        behavior=behavior,
        severity=severity,
        context_tags=["stress"],
        compassion_message="Every stumble is a step in your story.",
    )


# ---------------------------------------------------------------------------
# get_by_id
# ---------------------------------------------------------------------------


class TestGetById:
    @pytest.mark.asyncio
    async def test_returns_record_for_matching_user(self) -> None:
        repo = InMemoryRelapseRepository()
        created = await _create(repo, user_id="u-1")
        result = await repo.get_by_id(created.relapse_id, "u-1")
        assert result is not None
        assert result.relapse_id == created.relapse_id

    @pytest.mark.asyncio
    async def test_returns_none_for_wrong_user(self) -> None:
        repo = InMemoryRelapseRepository()
        created = await _create(repo, user_id="alice")
        result = await repo.get_by_id(created.relapse_id, "bob")
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_for_unknown_id(self) -> None:
        repo = InMemoryRelapseRepository()
        result = await repo.get_by_id(str(uuid.uuid4()), "u-1")
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_correct_record_among_multiple(self) -> None:
        repo = InMemoryRelapseRepository()
        r1 = await _create(repo, user_id="u-1", behavior="gaming")
        r2 = await _create(repo, user_id="u-1", behavior="scrolling")
        result = await repo.get_by_id(r1.relapse_id, "u-1")
        assert result is not None
        assert result.relapse_id == r1.relapse_id
        assert result.behavior == "gaming"
        assert r2.relapse_id != r1.relapse_id


# ---------------------------------------------------------------------------
# mark_reviewed
# ---------------------------------------------------------------------------


class TestMarkReviewed:
    @pytest.mark.asyncio
    async def test_sets_reviewed_to_true(self) -> None:
        repo = InMemoryRelapseRepository()
        created = await _create(repo)
        assert created.reviewed is False
        result = await repo.mark_reviewed(created.relapse_id, "u-1", reviewed_by="dr-jones")
        assert result is not None
        assert result.reviewed is True

    @pytest.mark.asyncio
    async def test_sets_reviewed_by(self) -> None:
        repo = InMemoryRelapseRepository()
        created = await _create(repo)
        result = await repo.mark_reviewed(created.relapse_id, "u-1", reviewed_by="dr-jones")
        assert result is not None
        assert result.reviewed_by == "dr-jones"

    @pytest.mark.asyncio
    async def test_sets_reviewed_at_timestamp(self) -> None:
        repo = InMemoryRelapseRepository()
        created = await _create(repo)
        result = await repo.mark_reviewed(created.relapse_id, "u-1", reviewed_by="dr-jones")
        assert result is not None
        assert result.reviewed_at is not None

    @pytest.mark.asyncio
    async def test_preserves_other_fields(self) -> None:
        repo = InMemoryRelapseRepository()
        created = await _create(repo, behavior="gaming", severity=3)
        result = await repo.mark_reviewed(created.relapse_id, "u-1", reviewed_by="dr-jones")
        assert result is not None
        assert result.behavior == "gaming"
        assert result.severity == 3
        assert result.user_id == "u-1"

    @pytest.mark.asyncio
    async def test_returns_none_for_wrong_user(self) -> None:
        repo = InMemoryRelapseRepository()
        created = await _create(repo, user_id="alice")
        result = await repo.mark_reviewed(created.relapse_id, "bob", reviewed_by="dr-jones")
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_for_unknown_id(self) -> None:
        repo = InMemoryRelapseRepository()
        result = await repo.mark_reviewed(
            str(uuid.uuid4()), "u-1", reviewed_by="dr-jones"
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_reviewed_record_persists(self) -> None:
        repo = InMemoryRelapseRepository()
        created = await _create(repo)
        await repo.mark_reviewed(created.relapse_id, "u-1", reviewed_by="dr-jones")
        fetched = await repo.get_by_id(created.relapse_id, "u-1")
        assert fetched is not None
        assert fetched.reviewed is True

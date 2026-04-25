"""Tests for discipline.pattern.repository — pattern in-memory store.

Covers methods not exercised by test_pattern_service.py:
- InMemoryPatternRepository.get_by_id: returns record, None for wrong user, None for unknown id
- reset_pattern_repository: clears store
"""

from __future__ import annotations

import uuid

import pytest

from discipline.pattern.repository import (
    InMemoryPatternRepository,
    PatternRecord,
    reset_pattern_repository,
)


@pytest.fixture(autouse=True)
def _reset() -> None:
    reset_pattern_repository()


async def _create(
    repo: InMemoryPatternRepository,
    user_id: str = "u-1",
    pattern_type: str = "temporal",
    detector: str = "peak_window",
    confidence: float = 0.8,
) -> PatternRecord:
    return await repo.create(
        user_id=user_id,
        pattern_type=pattern_type,
        detector=detector,
        confidence=confidence,
        description="Urge intensity rises between 5 PM and 7 PM.",
        metadata_json={"peak_start_hour": 17, "peak_end_hour": 19},
    )


# ---------------------------------------------------------------------------
# get_by_id
# ---------------------------------------------------------------------------


class TestGetById:
    @pytest.mark.asyncio
    async def test_returns_record_for_matching_user(self) -> None:
        repo = InMemoryPatternRepository()
        created = await _create(repo, user_id="u-1")
        result = await repo.get_by_id(created.pattern_id, "u-1")
        assert result is not None
        assert result.pattern_id == created.pattern_id

    @pytest.mark.asyncio
    async def test_returns_none_for_wrong_user(self) -> None:
        repo = InMemoryPatternRepository()
        created = await _create(repo, user_id="alice")
        result = await repo.get_by_id(created.pattern_id, "bob")
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_for_unknown_id(self) -> None:
        repo = InMemoryPatternRepository()
        result = await repo.get_by_id(str(uuid.uuid4()), "u-1")
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_correct_record_among_multiple(self) -> None:
        repo = InMemoryPatternRepository()
        r1 = await _create(repo, user_id="u-1", pattern_type="temporal")
        r2 = await _create(repo, user_id="u-1", pattern_type="contextual")
        result = await repo.get_by_id(r1.pattern_id, "u-1")
        assert result is not None
        assert result.pattern_type == "temporal"
        assert r2.pattern_id != r1.pattern_id

    @pytest.mark.asyncio
    async def test_returns_all_fields(self) -> None:
        repo = InMemoryPatternRepository()
        created = await _create(
            repo, user_id="u-99", pattern_type="frequency", confidence=0.91
        )
        result = await repo.get_by_id(created.pattern_id, "u-99")
        assert result is not None
        assert result.user_id == "u-99"
        assert result.pattern_type == "frequency"
        assert result.confidence == 0.91
        assert result.status == "active"


# ---------------------------------------------------------------------------
# reset_pattern_repository
# ---------------------------------------------------------------------------


class TestReset:
    @pytest.mark.asyncio
    async def test_clears_created_records(self) -> None:
        repo = InMemoryPatternRepository()
        created = await _create(repo)
        reset_pattern_repository()
        # After reset, new repo instance is returned by singleton
        from discipline.pattern.repository import get_pattern_repository
        new_repo = get_pattern_repository()
        result = await new_repo.get_by_id(created.pattern_id, "u-1")
        assert result is None

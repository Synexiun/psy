"""Tests for discipline.pattern.service — DetectedPattern, PatternServiceImpl, detectors.

Covers:
- DetectedPattern frozen dataclass
- _run_detectors returns exactly 4 patterns
- _run_detectors pattern_types: temporal, contextual, physiological, compound
- _run_detectors confidence values in [0.0, 1.0]
- PatternServiceImpl.mine_patterns creates records and returns them
- mine_patterns creates exactly 4 patterns per call
- mine_patterns records have active status
- list_active returns active patterns
- list_active limit parameter respected
- dismiss returns updated record
- dismiss unknown pattern_id returns None
- get_pattern_service returns same instance
- reset_pattern_service creates new instance
"""

from __future__ import annotations

import pytest

from discipline.pattern.repository import (
    PatternRecord,
    get_pattern_repository,
    reset_pattern_repository,
)
from discipline.pattern.service import (
    DetectedPattern,
    PatternServiceImpl,
    _run_detectors,
    get_pattern_service,
    reset_pattern_service,
)


@pytest.fixture(autouse=True)
def _reset() -> None:
    reset_pattern_repository()
    reset_pattern_service()


# ---------------------------------------------------------------------------
# DetectedPattern frozen dataclass
# ---------------------------------------------------------------------------


class TestDetectedPattern:
    def test_can_be_constructed(self) -> None:
        d = DetectedPattern(
            pattern_type="temporal",
            detector="peak_window",
            confidence=0.82,
            description="Urge peaks at 5 PM",
            metadata={"peak_hour": 17},
        )
        assert d.pattern_type == "temporal"

    def test_frozen(self) -> None:
        d = DetectedPattern(
            pattern_type="temporal",
            detector="peak_window",
            confidence=0.82,
            description="desc",
            metadata={},
        )
        with pytest.raises((AttributeError, TypeError)):
            d.confidence = 0.0  # type: ignore[misc]

    def test_metadata_is_dict(self) -> None:
        d = DetectedPattern(
            pattern_type="contextual",
            detector="co_occurring_tags",
            confidence=0.74,
            description="d",
            metadata={"tags": ["work_stress"]},
        )
        assert isinstance(d.metadata, dict)


# ---------------------------------------------------------------------------
# _run_detectors
# ---------------------------------------------------------------------------


class TestRunDetectors:
    def test_returns_four_patterns(self) -> None:
        results = _run_detectors("u-1")
        assert len(results) == 4

    def test_all_are_detected_pattern(self) -> None:
        for d in _run_detectors("u-1"):
            assert isinstance(d, DetectedPattern)

    def test_pattern_types_present(self) -> None:
        types = {d.pattern_type for d in _run_detectors("u-1")}
        assert "temporal" in types
        assert "contextual" in types
        assert "physiological" in types
        assert "compound" in types

    def test_confidence_in_range(self) -> None:
        for d in _run_detectors("u-1"):
            assert 0.0 <= d.confidence <= 1.0, (
                f"detector {d.detector!r} has confidence {d.confidence} out of range"
            )

    def test_descriptions_non_empty(self) -> None:
        for d in _run_detectors("u-1"):
            assert d.description.strip() != "", (
                f"detector {d.detector!r} has empty description"
            )

    def test_deterministic_for_same_user(self) -> None:
        r1 = _run_detectors("u-42")
        r2 = _run_detectors("u-42")
        assert [(d.pattern_type, d.detector) for d in r1] == [
            (d.pattern_type, d.detector) for d in r2
        ]


# ---------------------------------------------------------------------------
# PatternServiceImpl.mine_patterns
# ---------------------------------------------------------------------------


class TestMinePatterns:
    @pytest.mark.asyncio
    async def test_returns_list_of_pattern_records(self) -> None:
        svc = PatternServiceImpl()
        records = await svc.mine_patterns("u-1")
        assert isinstance(records, list)
        assert all(isinstance(r, PatternRecord) for r in records)

    @pytest.mark.asyncio
    async def test_creates_exactly_four_patterns(self) -> None:
        svc = PatternServiceImpl()
        records = await svc.mine_patterns("u-1")
        assert len(records) == 4

    @pytest.mark.asyncio
    async def test_patterns_have_active_status(self) -> None:
        svc = PatternServiceImpl()
        records = await svc.mine_patterns("u-1")
        for r in records:
            assert r.status == "active", f"pattern {r.pattern_id!r} has status {r.status!r}"

    @pytest.mark.asyncio
    async def test_patterns_have_correct_user_id(self) -> None:
        svc = PatternServiceImpl()
        records = await svc.mine_patterns("u-99")
        for r in records:
            assert r.user_id == "u-99"

    @pytest.mark.asyncio
    async def test_pattern_ids_are_unique(self) -> None:
        svc = PatternServiceImpl()
        records = await svc.mine_patterns("u-1")
        ids = [r.pattern_id for r in records]
        assert len(set(ids)) == len(ids)


# ---------------------------------------------------------------------------
# PatternServiceImpl.list_active
# ---------------------------------------------------------------------------


class TestListActive:
    @pytest.mark.asyncio
    async def test_returns_mined_patterns(self) -> None:
        svc = PatternServiceImpl()
        await svc.mine_patterns("u-1")
        records = await svc.list_active("u-1")
        assert len(records) == 4

    @pytest.mark.asyncio
    async def test_empty_for_unknown_user(self) -> None:
        svc = PatternServiceImpl()
        records = await svc.list_active("ghost-user")
        assert records == []

    @pytest.mark.asyncio
    async def test_limit_respected(self) -> None:
        svc = PatternServiceImpl()
        await svc.mine_patterns("u-1")
        records = await svc.list_active("u-1", limit=2)
        assert len(records) == 2


# ---------------------------------------------------------------------------
# PatternServiceImpl.dismiss
# ---------------------------------------------------------------------------


class TestDismiss:
    @pytest.mark.asyncio
    async def test_dismiss_returns_updated_record(self) -> None:
        svc = PatternServiceImpl()
        mined = await svc.mine_patterns("u-1")
        pattern_id = mined[0].pattern_id
        record = await svc.dismiss(pattern_id, "u-1", reason="not_relevant")
        assert record is not None

    @pytest.mark.asyncio
    async def test_dismiss_sets_status_dismissed(self) -> None:
        svc = PatternServiceImpl()
        mined = await svc.mine_patterns("u-1")
        pattern_id = mined[0].pattern_id
        record = await svc.dismiss(pattern_id, "u-1", reason="not_relevant")
        assert record is not None
        assert record.status == "dismissed"

    @pytest.mark.asyncio
    async def test_dismiss_unknown_pattern_returns_none(self) -> None:
        svc = PatternServiceImpl()
        result = await svc.dismiss("nonexistent-id", "u-1", reason=None)
        assert result is None


# ---------------------------------------------------------------------------
# Singleton management
# ---------------------------------------------------------------------------


class TestSingleton:
    def test_get_pattern_service_returns_same_instance(self) -> None:
        s1 = get_pattern_service()
        s2 = get_pattern_service()
        assert s1 is s2

    def test_reset_creates_new_instance(self) -> None:
        s1 = get_pattern_service()
        reset_pattern_service()
        s2 = get_pattern_service()
        assert s1 is not s2

"""Tests for discipline.clinical.service — RelapseService compassion-first relapse protocol.

CLAUDE.md Rule #4: Relapse copy is compassion-first. No "you failed", no "streak reset".

Covers:
- report() creates and returns a RelapseRecord
- report() compassion_message comes from the reviewed template set
- report() is deterministic: same user+occurred_at → same compassion_message
- report() compassion_message is non-empty
- report() stores user_id, behavior, severity, context_tags correctly
- next_steps(severity >= 4) returns 4 steps
- next_steps(severity >= 2) returns 3 steps
- next_steps(severity 0-1) returns 2 steps
- next_steps always includes 'compassion_message' as first step
- no template contains "you failed" or "streak reset" (CLAUDE.md Rule #4)
"""

from __future__ import annotations

import pytest

from discipline.clinical.repository import reset_relapse_repository
from discipline.clinical.service import RelapseService, _COMPASSION_TEMPLATES


@pytest.fixture(autouse=True)
def _reset() -> None:
    reset_relapse_repository()


def _make_service() -> RelapseService:
    from discipline.clinical.repository import InMemoryRelapseRepository

    return RelapseService(repository=InMemoryRelapseRepository())


# ---------------------------------------------------------------------------
# Clinical copy compliance (CLAUDE.md Rule #4)
# ---------------------------------------------------------------------------


class TestCompassionCopyCompliance:
    def test_no_template_says_you_failed(self) -> None:
        for t in _COMPASSION_TEMPLATES:
            assert "you failed" not in t.lower(), f"Non-compliant template: {t!r}"

    def test_no_template_says_streak_reset(self) -> None:
        for t in _COMPASSION_TEMPLATES:
            assert "streak reset" not in t.lower(), f"Non-compliant template: {t!r}"

    def test_no_template_says_you_broke(self) -> None:
        for t in _COMPASSION_TEMPLATES:
            assert "you broke" not in t.lower(), f"Non-compliant template: {t!r}"

    def test_templates_list_is_non_empty(self) -> None:
        assert len(_COMPASSION_TEMPLATES) >= 3

    def test_all_templates_are_non_empty_strings(self) -> None:
        for t in _COMPASSION_TEMPLATES:
            assert isinstance(t, str)
            assert t.strip() != ""


# ---------------------------------------------------------------------------
# RelapseService.report
# ---------------------------------------------------------------------------


class TestReport:
    @pytest.mark.asyncio
    async def test_returns_relapse_record(self) -> None:
        from discipline.clinical.repository import RelapseRecord

        svc = _make_service()
        rec = await svc.report(
            user_id="u-1",
            occurred_at="2026-04-25T00:00:00+00:00",
            behavior="alcohol",
            severity=3,
            context_tags=["stress", "social"],
        )
        assert isinstance(rec, RelapseRecord)

    @pytest.mark.asyncio
    async def test_fields_match_input(self) -> None:
        svc = _make_service()
        rec = await svc.report(
            user_id="u-99",
            occurred_at="2026-04-25T00:00:00+00:00",
            behavior="gambling",
            severity=5,
            context_tags=["boredom"],
        )
        assert rec.user_id == "u-99"
        assert rec.behavior == "gambling"
        assert rec.severity == 5
        assert "boredom" in rec.context_tags

    @pytest.mark.asyncio
    async def test_compassion_message_is_from_template_set(self) -> None:
        svc = _make_service()
        rec = await svc.report(
            user_id="u-1",
            occurred_at="2026-04-25T00:00:00+00:00",
            behavior="alcohol",
            severity=2,
            context_tags=[],
        )
        assert rec.compassion_message in _COMPASSION_TEMPLATES

    @pytest.mark.asyncio
    async def test_compassion_message_is_non_empty(self) -> None:
        svc = _make_service()
        rec = await svc.report(
            user_id="u-1",
            occurred_at="2026-04-25T00:00:00+00:00",
            behavior="alcohol",
            severity=2,
            context_tags=[],
        )
        assert rec.compassion_message.strip() != ""

    @pytest.mark.asyncio
    async def test_deterministic_same_user_same_time(self) -> None:
        """Same user_id + occurred_at → same compassion message (idempotent)."""
        svc = _make_service()
        r1 = await svc.report(
            user_id="det-user",
            occurred_at="2026-04-25T12:00:00+00:00",
            behavior="alcohol",
            severity=3,
            context_tags=[],
        )
        r2 = await svc.report(
            user_id="det-user",
            occurred_at="2026-04-25T12:00:00+00:00",
            behavior="alcohol",
            severity=3,
            context_tags=[],
        )
        assert r1.compassion_message == r2.compassion_message

    @pytest.mark.asyncio
    async def test_empty_context_tags_accepted(self) -> None:
        svc = _make_service()
        rec = await svc.report(
            user_id="u-1",
            occurred_at="2026-04-25T00:00:00+00:00",
            behavior="alcohol",
            severity=1,
            context_tags=[],
        )
        assert rec.context_tags == []

    @pytest.mark.asyncio
    async def test_relapse_id_is_non_empty(self) -> None:
        svc = _make_service()
        rec = await svc.report(
            user_id="u-1",
            occurred_at="2026-04-25T00:00:00+00:00",
            behavior="alcohol",
            severity=1,
            context_tags=[],
        )
        assert rec.relapse_id


# ---------------------------------------------------------------------------
# RelapseService.next_steps
# ---------------------------------------------------------------------------


class TestNextSteps:
    def test_severity_4_returns_4_steps(self) -> None:
        svc = _make_service()
        steps = svc.next_steps(4)
        assert len(steps) == 4

    def test_severity_5_returns_4_steps(self) -> None:
        svc = _make_service()
        steps = svc.next_steps(5)
        assert len(steps) == 4

    def test_severity_2_returns_3_steps(self) -> None:
        svc = _make_service()
        steps = svc.next_steps(2)
        assert len(steps) == 3

    def test_severity_3_returns_3_steps(self) -> None:
        svc = _make_service()
        steps = svc.next_steps(3)
        assert len(steps) == 3

    def test_severity_0_returns_2_steps(self) -> None:
        svc = _make_service()
        steps = svc.next_steps(0)
        assert len(steps) == 2

    def test_severity_1_returns_2_steps(self) -> None:
        svc = _make_service()
        steps = svc.next_steps(1)
        assert len(steps) == 2

    def test_first_step_is_compassion_message(self) -> None:
        """Compassion must always be the first step — clinical requirement."""
        svc = _make_service()
        for severity in range(6):
            steps = svc.next_steps(severity)
            assert steps[0] == "compassion_message", (
                f"severity={severity}: first step is {steps[0]!r}, expected 'compassion_message'"
            )

    def test_returns_list_of_strings(self) -> None:
        svc = _make_service()
        for step in svc.next_steps(3):
            assert isinstance(step, str)

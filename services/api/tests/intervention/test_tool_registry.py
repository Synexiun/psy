"""Unit tests for ToolRegistry — static coping tool variant catalogue.

Clinical compliance (CLAUDE.md §intervention coverage requirement):
- All variants must be offline-capable (CLAUDE.md Rule 3: no network-dep for tools)
- No variant should require location (privacy constraint)
- All variants must have non-empty name, category, description
- The registry must be immutable from the test perspective
- Clinical-category tools (crisis, mindfulness) must be offline-capable

These are deterministic, no-DB, no-network tests.
"""

from __future__ import annotations

import pytest

from discipline.intervention.tool_registry import ToolRegistry, ToolVariant


# ---------------------------------------------------------------------------
# ToolVariant dataclass
# ---------------------------------------------------------------------------


class TestToolVariant:
    def test_frozen(self) -> None:
        variant = ToolRegistry.get_tool("box_breathing")
        assert variant is not None
        with pytest.raises((AttributeError, TypeError)):
            variant.name = "hacked"  # type: ignore[misc]

    def test_equality_by_value(self) -> None:
        t1 = ToolVariant(
            variant="v",
            name="V",
            category="cat",
            duration_seconds=60,
            description="desc",
            offline_capable=True,
            requires_audio=False,
            requires_location=False,
        )
        t2 = ToolVariant(
            variant="v",
            name="V",
            category="cat",
            duration_seconds=60,
            description="desc",
            offline_capable=True,
            requires_audio=False,
            requires_location=False,
        )
        assert t1 == t2


# ---------------------------------------------------------------------------
# ToolRegistry.list_tools
# ---------------------------------------------------------------------------


class TestListTools:
    def test_returns_list(self) -> None:
        result = ToolRegistry.list_tools()
        assert isinstance(result, list)

    def test_minimum_8_tools(self) -> None:
        assert len(ToolRegistry.list_tools()) >= 8

    def test_each_element_is_tool_variant(self) -> None:
        for tool in ToolRegistry.list_tools():
            assert isinstance(tool, ToolVariant)

    def test_all_have_non_empty_variant(self) -> None:
        for tool in ToolRegistry.list_tools():
            assert tool.variant, f"Empty variant: {tool}"

    def test_all_have_non_empty_name(self) -> None:
        for tool in ToolRegistry.list_tools():
            assert tool.name, f"Empty name: {tool.variant}"

    def test_all_have_non_empty_category(self) -> None:
        for tool in ToolRegistry.list_tools():
            assert tool.category, f"Empty category: {tool.variant}"

    def test_all_have_non_empty_description(self) -> None:
        for tool in ToolRegistry.list_tools():
            assert tool.description, f"Empty description: {tool.variant}"

    def test_variant_ids_are_unique(self) -> None:
        ids = [t.variant for t in ToolRegistry.list_tools()]
        assert len(ids) == len(set(ids)), "Duplicate variant IDs found"


# ---------------------------------------------------------------------------
# ToolRegistry.get_tool
# ---------------------------------------------------------------------------


class TestGetTool:
    def test_returns_none_for_unknown_variant(self) -> None:
        assert ToolRegistry.get_tool("nonexistent_xyz") is None

    def test_returns_correct_tool_for_box_breathing(self) -> None:
        tool = ToolRegistry.get_tool("box_breathing")
        assert tool is not None
        assert tool.variant == "box_breathing"

    def test_returns_correct_tool_for_urge_surf(self) -> None:
        tool = ToolRegistry.get_tool("urge_surf")
        assert tool is not None
        assert tool.variant == "urge_surf"

    def test_every_listed_tool_is_retrievable_by_variant(self) -> None:
        for tool in ToolRegistry.list_tools():
            found = ToolRegistry.get_tool(tool.variant)
            assert found is not None
            assert found.variant == tool.variant

    def test_returns_none_for_empty_string(self) -> None:
        assert ToolRegistry.get_tool("") is None


# ---------------------------------------------------------------------------
# ToolRegistry.variants
# ---------------------------------------------------------------------------


class TestVariants:
    def test_returns_list_of_strings(self) -> None:
        result = ToolRegistry.variants()
        assert all(isinstance(v, str) for v in result)

    def test_count_matches_list_tools(self) -> None:
        assert len(ToolRegistry.variants()) == len(ToolRegistry.list_tools())

    def test_all_variants_are_non_empty(self) -> None:
        for v in ToolRegistry.variants():
            assert v, "Empty variant ID"


# ---------------------------------------------------------------------------
# Clinical compliance: offline capability (CLAUDE.md — offline contract)
# ---------------------------------------------------------------------------


class TestOfflineCapability:
    def test_all_tools_are_offline_capable(self) -> None:
        """Every registered tool must work without a network connection.

        CLAUDE.md Rule: every tool variant in the ToolRegistry must render
        correctly offline.  No tool variant should rely on a network round-trip.
        """
        for tool in ToolRegistry.list_tools():
            assert tool.offline_capable, (
                f"Tool '{tool.variant}' is not offline-capable — "
                "violates CLAUDE.md 'deterministic fallback' requirement"
            )

    def test_no_tool_requires_location(self) -> None:
        """Privacy constraint: no coping tool should request the user's location."""
        for tool in ToolRegistry.list_tools():
            assert not tool.requires_location, (
                f"Tool '{tool.variant}' requires location — privacy violation"
            )


# ---------------------------------------------------------------------------
# Known tools: spot-check key clinical entries
# ---------------------------------------------------------------------------


class TestKnownTools:
    def test_box_breathing_category_is_breathing(self) -> None:
        tool = ToolRegistry.get_tool("box_breathing")
        assert tool is not None
        assert tool.category == "breathing"

    def test_grounding_5_4_3_2_1_registered(self) -> None:
        tool = ToolRegistry.get_tool("grounding_5_4_3_2_1")
        assert tool is not None

    def test_grounding_description_mentions_senses(self) -> None:
        tool = ToolRegistry.get_tool("grounding_5_4_3_2_1")
        assert tool is not None
        # CLAUDE.md: 5-4-3-2-1 grounding must cover 5 senses
        description_lower = tool.description.lower()
        assert any(sense in description_lower for sense in ("see", "feel", "hear", "smell", "taste"))

    def test_tipp_60s_is_crisis_category(self) -> None:
        tool = ToolRegistry.get_tool("tipp_60s")
        assert tool is not None
        assert tool.category == "crisis"

    def test_call_support_has_no_duration(self) -> None:
        """call_support has no fixed duration — it's open-ended."""
        tool = ToolRegistry.get_tool("call_support")
        assert tool is not None
        assert tool.duration_seconds is None

    def test_self_compassion_break_requires_audio(self) -> None:
        tool = ToolRegistry.get_tool("self_compassion_break")
        assert tool is not None
        assert tool.requires_audio is True

    def test_urge_surf_5min_requires_audio(self) -> None:
        tool = ToolRegistry.get_tool("urge_surf_5min")
        assert tool is not None
        assert tool.requires_audio is True

    def test_values_reminder_no_audio(self) -> None:
        tool = ToolRegistry.get_tool("values_reminder")
        assert tool is not None
        assert tool.requires_audio is False

    def test_box_breathing_duration_is_180s(self) -> None:
        """Box breathing is a 3-minute (180s) exercise."""
        tool = ToolRegistry.get_tool("box_breathing")
        assert tool is not None
        assert tool.duration_seconds == 180


# ---------------------------------------------------------------------------
# Analytics + content stubs: contract tests
# ---------------------------------------------------------------------------


class TestAnalyticsRollupContract:
    """DailyRollup dataclass shape tests — no DB required."""

    def test_daily_rollup_can_be_constructed(self) -> None:
        from datetime import date

        from discipline.analytics.rollups import DailyRollup

        rollup = DailyRollup(
            user_id="u-001",
            day=date(2026, 4, 1),
            urges_logged=3,
            urges_handled=2,
            tools_used=1,
            mood_mean=6.5,
            sleep_hours=7.0,
            wellbeing_state="stable",
        )
        assert rollup.user_id == "u-001"
        assert rollup.rollup_version == "1.0.0"

    def test_build_for_user_stub_raises_not_implemented(self) -> None:
        import asyncio
        from datetime import date

        from discipline.analytics.rollups import build_for_user

        with pytest.raises(NotImplementedError):
            asyncio.run(
                build_for_user("u-001", date(2026, 4, 1))
            )


class TestInterventionContentContract:
    """Script dataclass shape tests — no DB required."""

    def test_script_can_be_constructed(self) -> None:
        from discipline.content.intervention_content import Script

        script = Script(
            tool="box_breathing",
            locale="en",
            steps=("Inhale for 4", "Hold for 4", "Exhale for 4", "Hold for 4"),
            version="1.0.0",
        )
        assert script.tool == "box_breathing"
        assert len(script.steps) == 4

    def test_get_script_stub_raises_not_implemented(self) -> None:
        import asyncio

        from discipline.content.intervention_content import get_script

        with pytest.raises(NotImplementedError):
            asyncio.run(
                get_script("box_breathing", "en")
            )

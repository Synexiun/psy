"""Tool registry — deterministic coping tool variants.

Every tool variant in the registry must render correctly offline.
No tool variant is added without a deterministic fallback.

See Docs/Technicals/05_Backend_Services.md §3.4 for the full registry spec.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True, slots=True)
class ToolVariant:
    """A single coping tool variant."""

    variant: str
    name: str
    category: str
    duration_seconds: int | None
    description: str
    offline_capable: bool
    requires_audio: bool
    requires_location: bool


class ToolRegistry:
    """Static registry of deterministic coping tools.

    Tools are referenced by ``variant`` string across mobile, web, and
    backend.  The registry is version-pinned — adding a variant requires
    a code change and clinical QA sign-off.
    """

    _TOOLS: ClassVar[dict[str, ToolVariant]] = {
        "urge_surf": ToolVariant(
            variant="urge_surf",
            name="Urge Surfing",
            category="mindfulness",
            duration_seconds=300,
            description="Ride the wave of the urge without acting on it.",
            offline_capable=True,
            requires_audio=False,
            requires_location=False,
        ),
        "urge_surf_5min": ToolVariant(
            variant="urge_surf_5min",
            name="Urge Surfing (5 min)",
            category="mindfulness",
            duration_seconds=300,
            description="Five-minute guided urge surf.",
            offline_capable=True,
            requires_audio=True,
            requires_location=False,
        ),
        "tipp_60s": ToolVariant(
            variant="tipp_60s",
            name="TIPP Skill (60 sec)",
            category="crisis",
            duration_seconds=60,
            description="Temperature, Intense exercise, Paced breathing, Paired muscle relaxation.",
            offline_capable=True,
            requires_audio=False,
            requires_location=False,
        ),
        "call_support": ToolVariant(
            variant="call_support",
            name="Call Support",
            category="social",
            duration_seconds=None,
            description="Reach out to a trusted contact or hotline.",
            offline_capable=True,
            requires_audio=False,
            requires_location=False,
        ),
        "box_breathing": ToolVariant(
            variant="box_breathing",
            name="Box Breathing",
            category="breathing",
            duration_seconds=180,
            description="4-4-4-4 rhythmic breathing pattern.",
            offline_capable=True,
            requires_audio=False,
            requires_location=False,
        ),
        "grounding_5_4_3_2_1": ToolVariant(
            variant="grounding_5_4_3_2_1",
            name="5-4-3-2-1 Grounding",
            category="grounding",
            duration_seconds=120,
            description="Name 5 things you see, 4 you feel, 3 you hear, 2 you smell, 1 you taste.",
            offline_capable=True,
            requires_audio=False,
            requires_location=False,
        ),
        "self_compassion_break": ToolVariant(
            variant="self_compassion_break",
            name="Self-Compassion Break",
            category="compassion",
            duration_seconds=300,
            description="A guided pause to offer yourself kindness.",
            offline_capable=True,
            requires_audio=True,
            requires_location=False,
        ),
        "values_reminder": ToolVariant(
            variant="values_reminder",
            name="Values Reminder",
            category="values",
            duration_seconds=60,
            description="Review your top values and why they matter.",
            offline_capable=True,
            requires_audio=False,
            requires_location=False,
        ),
    }

    @classmethod
    def list_tools(cls) -> list[ToolVariant]:
        """Return all registered tool variants."""
        return list(cls._TOOLS.values())

    @classmethod
    def get_tool(cls, variant: str) -> ToolVariant | None:
        """Look up a tool by variant string."""
        return cls._TOOLS.get(variant)

    @classmethod
    def variants(cls) -> list[str]:
        """Return all variant IDs."""
        return list(cls._TOOLS.keys())

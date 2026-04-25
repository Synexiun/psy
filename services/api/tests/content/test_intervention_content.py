"""Tests for discipline.content.intervention_content — Script dataclass and stub guard.

Covers:
- Script can be constructed with all fields
- Script is a frozen dataclass
- Script.steps is a tuple of strings
- get_script raises NotImplementedError (stub contract — must never call LLM)
- __all__ exports are present
"""

from __future__ import annotations

import pytest

from discipline.content.intervention_content import Script, get_script


class TestScript:
    def test_can_be_constructed(self) -> None:
        s = Script(
            tool="box_breathing",
            locale="en",
            steps=("Breathe in for 4s", "Hold for 4s", "Breathe out for 4s", "Hold for 4s"),
            version="1.0.0",
        )
        assert s.tool == "box_breathing"

    def test_frozen(self) -> None:
        s = Script(
            tool="urge_surf",
            locale="en",
            steps=("Step 1",),
            version="1.0.0",
        )
        with pytest.raises((AttributeError, TypeError)):
            s.tool = "mutated"  # type: ignore[misc]

    def test_steps_is_tuple(self) -> None:
        s = Script(
            tool="tipp",
            locale="en",
            steps=("Step A", "Step B"),
            version="1.0.0",
        )
        assert isinstance(s.steps, tuple)

    def test_steps_elements_are_strings(self) -> None:
        s = Script(
            tool="tipp",
            locale="en",
            steps=("Step A", "Step B"),
            version="1.0.0",
        )
        for step in s.steps:
            assert isinstance(step, str)

    def test_locale_stored(self) -> None:
        s = Script(
            tool="box_breathing",
            locale="fr",
            steps=("Respirez",),
            version="1.0.0",
        )
        assert s.locale == "fr"

    def test_version_stored(self) -> None:
        s = Script(
            tool="box_breathing",
            locale="en",
            steps=("Step 1",),
            version="2.0.0",
        )
        assert s.version == "2.0.0"

    def test_empty_steps_tuple_allowed(self) -> None:
        s = Script(tool="t", locale="en", steps=(), version="1.0.0")
        assert s.steps == ()


class TestGetScript:
    @pytest.mark.asyncio
    async def test_raises_not_implemented(self) -> None:
        """Stub contract: real implementation requires clinical QA sign-off.
        Must never delegate to an LLM — see intervention_content module docstring."""
        with pytest.raises(NotImplementedError):
            await get_script("box_breathing", "en")

    @pytest.mark.asyncio
    async def test_raises_for_any_locale(self) -> None:
        for locale in ("en", "fr", "ar", "fa"):
            with pytest.raises(NotImplementedError):
                await get_script("urge_surf", locale)  # type: ignore[arg-type]


class TestModule:
    def test_script_in_all(self) -> None:
        from discipline.content import intervention_content

        assert "Script" in intervention_content.__all__

    def test_get_script_in_all(self) -> None:
        from discipline.content import intervention_content

        assert "get_script" in intervention_content.__all__

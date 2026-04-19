"""Per-locale intervention scripts (coping-tool copy).

All strings are clinical-QA-signed templates.  NEVER call an LLM to generate or
rephrase intervention content — see Docs/Technicals/05_Backend_Services.md §3.12.
"""

from __future__ import annotations

from dataclasses import dataclass

from discipline.shared.i18n import Locale


@dataclass(frozen=True)
class Script:
    tool: str
    locale: Locale
    steps: tuple[str, ...]
    version: str


async def get_script(_tool: str, _locale: Locale) -> Script | None:
    raise NotImplementedError


__all__ = ["Script", "get_script"]

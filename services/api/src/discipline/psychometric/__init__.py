"""Psychometric module — validated instruments, deterministic scoring, trajectories.

Authority chain:
- Scoring functions are **pure** and **version-pinned**.  A change to a scoring
  formula bumps the instrument version, which is written to every stored score.
- Reference values come from the original validation publications; see
  Docs/Whitepapers/02_Clinical_Evidence_Base.md for the citation table.
- Safety-relevant items (PHQ-9 item 9, C-SSRS) route into the T3/T4 safety path
  via :mod:`discipline.psychometric.safety_items`; LLMs NEVER participate.
"""

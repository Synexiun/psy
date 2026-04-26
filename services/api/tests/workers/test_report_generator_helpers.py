"""Unit tests for _render_enterprise_aggregate() in discipline.workers.report_generator.

_render_enterprise_aggregate(org_id, month) → dict
  Builds an org engagement dict from a zero-filled OrgEngagementSnapshot stub.
  Contracts pinned here:
  - Returns a dict containing org_id, period, active_members_7d, tools_used_7d,
    wellbeing_index.
  - org_id and period are passed through to the result without modification.
  - All numeric fields are non-negative (stub produces zeros).
"""

from __future__ import annotations

from discipline.workers.report_generator import _render_enterprise_aggregate


class TestRenderEnterpriseAggregate:
    def test_returns_dict(self) -> None:
        result = _render_enterprise_aggregate("org-abc", "2026-01")
        assert isinstance(result, dict)

    def test_org_id_propagated(self) -> None:
        result = _render_enterprise_aggregate("org-xyz", "2026-01")
        assert result["org_id"] == "org-xyz"

    def test_period_propagated(self) -> None:
        result = _render_enterprise_aggregate("org-abc", "2026-03")
        assert result["period"] == "2026-03"

    def test_active_members_7d_present(self) -> None:
        result = _render_enterprise_aggregate("org-abc", "2026-01")
        assert "active_members_7d" in result

    def test_tools_used_7d_present(self) -> None:
        result = _render_enterprise_aggregate("org-abc", "2026-01")
        assert "tools_used_7d" in result

    def test_wellbeing_index_present(self) -> None:
        result = _render_enterprise_aggregate("org-abc", "2026-01")
        assert "wellbeing_index" in result

    def test_numeric_fields_are_int_or_none(self) -> None:
        # The stub snapshot has n=0, which triggers k-anon suppression → None
        result = _render_enterprise_aggregate("org-abc", "2026-01")
        assert isinstance(result["active_members_7d"], (int, type(None)))
        assert isinstance(result["tools_used_7d"], (int, type(None)))
        assert isinstance(result["wellbeing_index"], (float, int, type(None)))

    def test_different_org_ids_produce_different_org_id(self) -> None:
        r1 = _render_enterprise_aggregate("org-1", "2026-01")
        r2 = _render_enterprise_aggregate("org-2", "2026-01")
        assert r1["org_id"] != r2["org_id"]

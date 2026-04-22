"""Enterprise k-anonymity primitive tests.

CLAUDE.md: enterprise aggregates are k ≥ 5 only.  These tests are load-
bearing for privacy — a silent weakening of the threshold would leak
individual user signals into the enterprise dashboard.
"""

from __future__ import annotations

import pytest

from discipline.reports.enterprise import (
    K_ANONYMITY_THRESHOLD,
    InvalidCohortSizeError,
    OrgEngagement,
    OrgEngagementSnapshot,
    build_org_engagement,
    suppress_below_k,
)

# =============================================================================
# The threshold itself
# =============================================================================


class TestThreshold:
    def test_threshold_is_five(self) -> None:
        """Pinned: the k-anonymity threshold is 5.  Any change requires a
        DPIA + compliance review — this assertion forces that conversation
        into code review rather than letting it slide as a casual edit."""
        assert K_ANONYMITY_THRESHOLD == 5


# =============================================================================
# suppress_below_k boundary semantics
# =============================================================================


class TestSuppressBelowK:
    @pytest.mark.parametrize("n", [0, 1, 2, 3, 4])
    def test_below_threshold_suppressed(self, n: int) -> None:
        """Cohort sizes 0..4 must be suppressed (return None).  This is the
        primary guarantee of the function."""
        assert suppress_below_k(42, n) is None

    def test_exactly_at_threshold_not_suppressed(self) -> None:
        """Boundary: n == k passes through.  The threshold is ``>=``, not
        ``>``.  If this ever flips to strict ``>``, every current dashboard
        cell at exactly 5 users suddenly disappears — which is a visible
        regression for enterprise customers."""
        assert suppress_below_k(42, K_ANONYMITY_THRESHOLD) == 42

    @pytest.mark.parametrize("n", [5, 6, 10, 1000])
    def test_above_threshold_not_suppressed(self, n: int) -> None:
        assert suppress_below_k(42, n) == 42

    def test_float_values_pass_through(self) -> None:
        """WHO-5 mean is a float; suppression must preserve the type."""
        result = suppress_below_k(68.4, 10)
        assert result == 68.4

    def test_zero_value_at_sufficient_cohort_is_not_suppressed(self) -> None:
        """A legitimate zero count (nobody used tool X this week) at a
        sufficient cohort size (100 members in the org) is information,
        not a privacy risk.  It must NOT be suppressed — returning None
        here would lie to the dashboard."""
        assert suppress_below_k(0, 100) == 0

    def test_negative_cohort_size_raises(self) -> None:
        with pytest.raises(InvalidCohortSizeError, match="non-negative"):
            suppress_below_k(42, -1)

    def test_custom_k_override(self) -> None:
        """Callers can tighten the floor (e.g. a PII-sensitive cell with
        k=10), never loosen it."""
        assert suppress_below_k(42, 8, k=10) is None
        assert suppress_below_k(42, 10, k=10) == 42


# =============================================================================
# build_org_engagement composition
# =============================================================================


class TestBuildOrgEngagement:
    def _snapshot(
        self,
        *,
        n_active: int = 20,
        n_wellbeing: int = 20,
        active: int = 15,
        tools: int = 40,
        wellbeing: float = 68.0,
    ) -> OrgEngagementSnapshot:
        return OrgEngagementSnapshot(
            org_id="org-test",
            active_members_count_7d=active,
            tools_used_count_7d=tools,
            wellbeing_index_mean=wellbeing,
            n_active_members_7d=n_active,
            n_wellbeing_reporters=n_wellbeing,
        )

    def test_all_fields_present_when_cohort_is_sufficient(self) -> None:
        engagement = build_org_engagement(self._snapshot())
        assert engagement.active_members_7d == 15
        assert engagement.tools_used_7d == 40
        assert engagement.wellbeing_index == 68.0

    def test_small_org_suppresses_all_fields(self) -> None:
        """An org with 3 members — everything suppressed.  Dashboard
        renders 'insufficient data' for each cell."""
        engagement = build_org_engagement(
            self._snapshot(n_active=3, n_wellbeing=3)
        )
        assert engagement.active_members_7d is None
        assert engagement.tools_used_7d is None
        assert engagement.wellbeing_index is None

    def test_wellbeing_suppressed_while_activity_not(self) -> None:
        """Plausible scenario: 20 active members but only 3 answered WHO-5
        this week.  Activity cells render; wellbeing suppressed."""
        engagement = build_org_engagement(
            self._snapshot(n_active=20, n_wellbeing=3)
        )
        assert engagement.active_members_7d is not None
        assert engagement.tools_used_7d is not None
        assert engagement.wellbeing_index is None

    def test_org_id_preserved(self) -> None:
        engagement = build_org_engagement(
            self._snapshot()
        )
        assert engagement.org_id == "org-test"

    def test_suppressed_cells_distinguishable_from_zero(self) -> None:
        """A zero count at a sufficient cohort is NOT the same as
        suppression.  The wire format (None vs 0) distinguishes them;
        dashboards must render them differently."""
        engagement = build_org_engagement(
            self._snapshot(active=0, tools=0, wellbeing=0.0)
        )
        # n_active is 20 (sufficient), so zeros pass through as zeros.
        assert engagement.active_members_7d == 0
        assert engagement.tools_used_7d == 0
        assert engagement.wellbeing_index == 0.0


# =============================================================================
# Type stability / wire contract
# =============================================================================


class TestOrgEngagementShape:
    def test_is_frozen_dataclass(self) -> None:
        """Frozen so the render boundary's output can't be mutated after
        suppression (no accidental post-hoc de-suppression)."""
        engagement = build_org_engagement(
            OrgEngagementSnapshot(
                org_id="o",
                active_members_count_7d=1,
                tools_used_count_7d=1,
                wellbeing_index_mean=1.0,
                n_active_members_7d=10,
                n_wellbeing_reporters=10,
            )
        )
        with pytest.raises(Exception):  # dataclasses.FrozenInstanceError
            engagement.active_members_7d = 999  # type: ignore[misc]

    def test_optional_types_preserved(self) -> None:
        engagement = OrgEngagement(
            org_id="o",
            active_members_7d=None,
            tools_used_7d=None,
            wellbeing_index=None,
        )
        assert engagement.active_members_7d is None

"""Unit tests for _cutoff_for() pure helper in
discipline.psychometric.scoring.sds.

_cutoff_for(substance) → int
  Maps a substance key to the published SDS positive-screen cutoff:
    "heroin" → 5, "cannabis" → 3, "cocaine" → 3,
    "amphetamine" → 4, "unspecified" → 3 (safety-conservative fallback).
  "unspecified" uses the LOWEST published cutoff (cannabis/cocaine) to
  maximize sensitivity — same safety posture as AUDIT-C's unspecified-sex
  falling back to the female (lower) cutoff.
"""

from __future__ import annotations

from discipline.psychometric.scoring.sds import (
    SDS_CUTOFF_AMPHETAMINE,
    SDS_CUTOFF_CANNABIS,
    SDS_CUTOFF_COCAINE,
    SDS_CUTOFF_HEROIN,
    SDS_CUTOFF_UNSPECIFIED,
    SDS_CUTOFFS,
    _cutoff_for,
)


# ---------------------------------------------------------------------------
# _cutoff_for — published per-substance cutoffs
# ---------------------------------------------------------------------------


class TestCutoffForSds:
    def test_heroin_cutoff(self) -> None:
        assert _cutoff_for("heroin") == SDS_CUTOFF_HEROIN

    def test_cannabis_cutoff(self) -> None:
        assert _cutoff_for("cannabis") == SDS_CUTOFF_CANNABIS

    def test_cocaine_cutoff(self) -> None:
        assert _cutoff_for("cocaine") == SDS_CUTOFF_COCAINE

    def test_amphetamine_cutoff(self) -> None:
        assert _cutoff_for("amphetamine") == SDS_CUTOFF_AMPHETAMINE

    def test_unspecified_cutoff(self) -> None:
        assert _cutoff_for("unspecified") == SDS_CUTOFF_UNSPECIFIED

    def test_unspecified_is_lowest_published_cutoff(self) -> None:
        # Safety-conservatism: unspecified must use the most sensitive cutoff
        specified_cutoffs = [
            SDS_CUTOFF_HEROIN,
            SDS_CUTOFF_CANNABIS,
            SDS_CUTOFF_COCAINE,
            SDS_CUTOFF_AMPHETAMINE,
        ]
        assert SDS_CUTOFF_UNSPECIFIED == min(specified_cutoffs)

    def test_heroin_cutoff_is_highest(self) -> None:
        # Opioid dependence has the highest validated cutoff
        assert SDS_CUTOFF_HEROIN == 5
        other = [SDS_CUTOFF_CANNABIS, SDS_CUTOFF_COCAINE, SDS_CUTOFF_AMPHETAMINE]
        assert SDS_CUTOFF_HEROIN > max(other)

    def test_all_substances_in_cutoffs_dict(self) -> None:
        for substance in ("heroin", "cannabis", "cocaine", "amphetamine", "unspecified"):
            assert substance in SDS_CUTOFFS

    def test_cutoff_returns_int(self) -> None:
        for substance in ("heroin", "cannabis", "cocaine", "amphetamine", "unspecified"):
            assert isinstance(_cutoff_for(substance), int)

    def test_all_cutoffs_are_positive(self) -> None:
        for substance in SDS_CUTOFFS:
            assert _cutoff_for(substance) > 0

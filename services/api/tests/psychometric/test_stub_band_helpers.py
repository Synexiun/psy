"""Unit tests for _stub_band() and _normalize_instrument_name() pure helpers.

Both functions live in discipline.psychometric.router and are used by the
POST /v1/assessments/sessions endpoint.

_stub_band(instrument, score) → severity band string
  Applies published clinical thresholds (Kroenke 2001, Spitzer 2006, WHO 1998,
  Cohen 1983) to map a raw score to a severity label.  The thresholds are
  duplicated from the scoring modules intentionally — tests here pin the
  duplication so drift between _stub_band and the scorer is caught immediately.

_normalize_instrument_name(raw) → canonical scorer key
  Maps hyphenated web-app names ("phq-9", "gad-7") to underscore/digit names
  ("phq9", "gad7").  Unknown names pass through unchanged (lowercased/stripped).
"""

from __future__ import annotations

import pytest

from discipline.psychometric.router import _normalize_instrument_name, _stub_band


# ---------------------------------------------------------------------------
# PHQ-9 bands (Kroenke, Spitzer & Williams 2001)
# ---------------------------------------------------------------------------


class TestStubBandPHQ9:
    def test_score_0_is_minimal(self) -> None:
        assert _stub_band("phq-9", 0) == "minimal"

    def test_score_4_is_minimal(self) -> None:
        assert _stub_band("phq-9", 4) == "minimal"

    def test_score_5_is_mild(self) -> None:
        assert _stub_band("phq-9", 5) == "mild"

    def test_score_9_is_mild(self) -> None:
        assert _stub_band("phq-9", 9) == "mild"

    def test_score_10_is_moderate(self) -> None:
        assert _stub_band("phq-9", 10) == "moderate"

    def test_score_14_is_moderate(self) -> None:
        assert _stub_band("phq-9", 14) == "moderate"

    def test_score_15_is_moderately_severe(self) -> None:
        assert _stub_band("phq-9", 15) == "moderately_severe"

    def test_score_19_is_moderately_severe(self) -> None:
        assert _stub_band("phq-9", 19) == "moderately_severe"

    def test_score_20_is_severe(self) -> None:
        assert _stub_band("phq-9", 20) == "severe"

    def test_score_27_is_severe(self) -> None:
        assert _stub_band("phq-9", 27) == "severe"

    def test_boundary_4_to_5(self) -> None:
        assert _stub_band("phq-9", 4) != _stub_band("phq-9", 5)

    def test_boundary_9_to_10(self) -> None:
        assert _stub_band("phq-9", 9) != _stub_band("phq-9", 10)

    def test_boundary_14_to_15(self) -> None:
        assert _stub_band("phq-9", 14) != _stub_band("phq-9", 15)

    def test_boundary_19_to_20(self) -> None:
        assert _stub_band("phq-9", 19) != _stub_band("phq-9", 20)


# ---------------------------------------------------------------------------
# GAD-7 bands (Spitzer et al. 2006)
# ---------------------------------------------------------------------------


class TestStubBandGAD7:
    def test_score_0_is_minimal(self) -> None:
        assert _stub_band("gad-7", 0) == "minimal"

    def test_score_4_is_minimal(self) -> None:
        assert _stub_band("gad-7", 4) == "minimal"

    def test_score_5_is_mild(self) -> None:
        assert _stub_band("gad-7", 5) == "mild"

    def test_score_9_is_mild(self) -> None:
        assert _stub_band("gad-7", 9) == "mild"

    def test_score_10_is_moderate(self) -> None:
        assert _stub_band("gad-7", 10) == "moderate"

    def test_score_14_is_moderate(self) -> None:
        assert _stub_band("gad-7", 14) == "moderate"

    def test_score_15_is_severe(self) -> None:
        assert _stub_band("gad-7", 15) == "severe"

    def test_score_21_is_severe(self) -> None:
        assert _stub_band("gad-7", 21) == "severe"

    def test_boundary_9_to_10(self) -> None:
        assert _stub_band("gad-7", 9) != _stub_band("gad-7", 10)

    def test_boundary_14_to_15(self) -> None:
        assert _stub_band("gad-7", 14) != _stub_band("gad-7", 15)


# ---------------------------------------------------------------------------
# WHO-5 bands (WHO 1998) — raw × 4 = percentage
# ---------------------------------------------------------------------------


class TestStubBandWHO5:
    def test_raw_0_pct_0_is_poor(self) -> None:
        assert _stub_band("who-5", 0) == "poor"

    def test_raw_6_pct_24_is_poor(self) -> None:
        assert _stub_band("who-5", 6) == "poor"

    def test_raw_7_pct_28_is_low(self) -> None:
        assert _stub_band("who-5", 7) == "low"

    def test_raw_12_pct_48_is_low(self) -> None:
        assert _stub_band("who-5", 12) == "low"

    def test_raw_13_pct_52_is_moderate(self) -> None:
        assert _stub_band("who-5", 13) == "moderate"

    def test_raw_17_pct_68_is_moderate(self) -> None:
        assert _stub_band("who-5", 17) == "moderate"

    def test_raw_18_pct_72_is_good(self) -> None:
        assert _stub_band("who-5", 18) == "good"

    def test_raw_25_pct_100_is_good(self) -> None:
        assert _stub_band("who-5", 25) == "good"

    def test_boundary_poor_to_low(self) -> None:
        assert _stub_band("who-5", 6) != _stub_band("who-5", 7)

    def test_boundary_low_to_moderate(self) -> None:
        assert _stub_band("who-5", 12) != _stub_band("who-5", 13)

    def test_boundary_moderate_to_good(self) -> None:
        assert _stub_band("who-5", 17) != _stub_band("who-5", 18)


# ---------------------------------------------------------------------------
# PSS-10 bands (Cohen 1983)
# ---------------------------------------------------------------------------


class TestStubBandPSS10:
    def test_score_0_is_low(self) -> None:
        assert _stub_band("pss-10", 0) == "low"

    def test_score_13_is_low(self) -> None:
        assert _stub_band("pss-10", 13) == "low"

    def test_score_14_is_moderate(self) -> None:
        assert _stub_band("pss-10", 14) == "moderate"

    def test_score_26_is_moderate(self) -> None:
        assert _stub_band("pss-10", 26) == "moderate"

    def test_score_27_is_high(self) -> None:
        assert _stub_band("pss-10", 27) == "high"

    def test_score_40_is_high(self) -> None:
        assert _stub_band("pss-10", 40) == "high"

    def test_boundary_13_to_14(self) -> None:
        assert _stub_band("pss-10", 13) != _stub_band("pss-10", 14)

    def test_boundary_26_to_27(self) -> None:
        assert _stub_band("pss-10", 26) != _stub_band("pss-10", 27)


# ---------------------------------------------------------------------------
# Unknown / fallthrough instruments
# ---------------------------------------------------------------------------


class TestStubBandUnknown:
    def test_unknown_instrument_returns_scored(self) -> None:
        assert _stub_band("audit", 10) == "scored"

    def test_completely_unknown_returns_scored(self) -> None:
        assert _stub_band("xyz", 5) == "scored"

    def test_empty_instrument_returns_scored(self) -> None:
        assert _stub_band("", 0) == "scored"


# ---------------------------------------------------------------------------
# _normalize_instrument_name — web-app → scorer key mapping
# ---------------------------------------------------------------------------


class TestNormalizeInstrumentName:
    def test_phq9_hyphenated_to_underscore(self) -> None:
        assert _normalize_instrument_name("phq-9") == "phq9"

    def test_gad7_hyphenated_to_underscore(self) -> None:
        assert _normalize_instrument_name("gad-7") == "gad7"

    def test_who5_hyphenated_to_underscore(self) -> None:
        assert _normalize_instrument_name("who-5") == "who5"

    def test_audit_c_hyphenated_to_underscore(self) -> None:
        assert _normalize_instrument_name("audit-c") == "audit_c"

    def test_pss10_hyphenated_to_underscore(self) -> None:
        assert _normalize_instrument_name("pss-10") == "pss10"

    def test_dast10_hyphenated_to_underscore(self) -> None:
        assert _normalize_instrument_name("dast-10") == "dast10"

    def test_already_canonical_passes_through(self) -> None:
        assert _normalize_instrument_name("phq9") == "phq9"

    def test_unknown_name_passes_through_lowercased(self) -> None:
        assert _normalize_instrument_name("AUDIT") == "audit"

    def test_unknown_name_stripped(self) -> None:
        assert _normalize_instrument_name("  gad7  ") == "gad7"

    def test_uppercase_hyphenated_normalised(self) -> None:
        assert _normalize_instrument_name("PHQ-9") == "phq9"

    def test_completely_unknown_returns_lowercased(self) -> None:
        assert _normalize_instrument_name("CUSTOM-SCALE") == "custom-scale"

"""Unit tests for _run_detectors() in discipline.pattern.service.

_run_detectors(user_id) → list[DetectedPattern]
  Deterministic stub that returns four structurally valid patterns (one per
  detector type) regardless of the user_id argument.  Contracts pinned here:
  - Always returns exactly 4 patterns.
  - Each of the four pattern_type values is present exactly once.
  - All confidence values are in [0, 1].
  - Every DetectedPattern has a non-empty description and a non-empty metadata dict.
  - Return type is list[DetectedPattern] (not a generator or tuple).
"""

from __future__ import annotations

from discipline.pattern.service import DetectedPattern, _run_detectors

_EXPECTED_TYPES = {"temporal", "contextual", "physiological", "compound"}


class TestRunDetectorsContract:
    def test_returns_exactly_four_patterns(self) -> None:
        result = _run_detectors("user-abc")
        assert len(result) == 4

    def test_all_four_pattern_types_present(self) -> None:
        result = _run_detectors("user-abc")
        types = {p.pattern_type for p in result}
        assert types == _EXPECTED_TYPES

    def test_result_is_list(self) -> None:
        assert isinstance(_run_detectors("user-abc"), list)

    def test_all_elements_are_detected_pattern(self) -> None:
        for p in _run_detectors("user-abc"):
            assert isinstance(p, DetectedPattern)

    def test_all_confidences_in_unit_interval(self) -> None:
        for p in _run_detectors("user-abc"):
            assert 0.0 <= p.confidence <= 1.0, f"{p.pattern_type}: confidence={p.confidence}"

    def test_all_descriptions_non_empty(self) -> None:
        for p in _run_detectors("user-abc"):
            assert isinstance(p.description, str) and len(p.description) > 0

    def test_all_metadata_dicts_non_empty(self) -> None:
        for p in _run_detectors("user-abc"):
            assert isinstance(p.metadata, dict) and len(p.metadata) > 0

    def test_user_id_does_not_affect_output(self) -> None:
        r1 = _run_detectors("user-1")
        r2 = _run_detectors("user-2")
        assert [p.pattern_type for p in r1] == [p.pattern_type for p in r2]

    def test_temporal_pattern_has_expected_detector(self) -> None:
        result = _run_detectors("u")
        temporal = next(p for p in result if p.pattern_type == "temporal")
        assert temporal.detector == "peak_window"

    def test_contextual_pattern_has_expected_detector(self) -> None:
        result = _run_detectors("u")
        contextual = next(p for p in result if p.pattern_type == "contextual")
        assert contextual.detector == "co_occurring_tags"

    def test_physiological_pattern_has_expected_detector(self) -> None:
        result = _run_detectors("u")
        physio = next(p for p in result if p.pattern_type == "physiological")
        assert physio.detector == "hrv_dip"

    def test_compound_pattern_has_expected_detector(self) -> None:
        result = _run_detectors("u")
        compound = next(p for p in result if p.pattern_type == "compound")
        assert compound.detector == "chained_signals"

    def test_deterministic_on_repeated_calls(self) -> None:
        r1 = _run_detectors("user-abc")
        r2 = _run_detectors("user-abc")
        for p1, p2 in zip(r1, r2):
            assert p1 == p2

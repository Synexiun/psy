"""Unit tests for _assessment_observation() and _urge_observation() pure
helpers in discipline.reports.fhir_export.

_assessment_observation(session) → dict | None
  Returns None (soft-skip) when the instrument has no pinned LOINC code.
  This is intentionally different from the clinician-surface router which
  raises UnsupportedInstrumentError: patient self-export must not fail
  just because one instrument isn't LOINC-mapped yet.
  For mapped instruments: delegates to render_bundle (numeric path).

_urge_observation(check_in) → dict
  Uses the Discipline OS proprietary code system (not LOINC) because no
  published LOINC code covers a 0-10 self-reported urge intensity.
  Key contract: resourceType = "Observation", valueInteger = intensity,
  effectiveDateTime ends with "Z", category uses "survey" code.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest

from discipline.reports.fhir_export import (
    DISCIPLINEOS_CODE_SYSTEM,
    AssessmentSession,
    UrgeCheckInRecord,
    _assessment_observation,
    _urge_observation,
)

_NOW = datetime(2026, 1, 15, 12, 0, 0, tzinfo=UTC)


def _session(instrument: str = "phq9", **overrides: object) -> AssessmentSession:
    defaults = dict(
        user_id="u1",
        instrument=instrument,
        total_score=10,
        administered_at=_NOW,
        safety_item_positive=False,
    )
    defaults.update(overrides)
    return AssessmentSession(**defaults)  # type: ignore[arg-type]


def _checkin(intensity: int = 5, **overrides: object) -> UrgeCheckInRecord:
    defaults = dict(user_id="u1", intensity=intensity, checked_in_at=_NOW)
    defaults.update(overrides)
    return UrgeCheckInRecord(**defaults)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# _assessment_observation — None for unmapped instruments
# ---------------------------------------------------------------------------


class TestAssessmentObservation:
    def test_known_instrument_returns_dict(self) -> None:
        result = _assessment_observation(_session("phq9"))
        assert isinstance(result, dict)

    def test_unknown_instrument_returns_none(self) -> None:
        # Soft-skip: patient export must not fail on unmapped instruments
        result = _assessment_observation(_session("unknown_xyz_instrument"))
        assert result is None

    def test_known_instrument_is_fhir_observation(self) -> None:
        result = _assessment_observation(_session("phq9"))
        assert result is not None
        assert result.get("resourceType") == "Observation"

    def test_unknown_instrument_is_not_unsupported_error(self) -> None:
        # Must return None, not raise UnsupportedInstrumentError
        result = _assessment_observation(_session("hypothetical"))
        assert result is None

    def test_gad7_returns_observation(self) -> None:
        result = _assessment_observation(_session("gad7"))
        assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# _urge_observation — proprietary code system, Z-suffix, valueInteger
# ---------------------------------------------------------------------------


class TestUrgeObservation:
    def test_returns_dict(self) -> None:
        assert isinstance(_urge_observation(_checkin()), dict)

    def test_resource_type_is_observation(self) -> None:
        result = _urge_observation(_checkin())
        assert result["resourceType"] == "Observation"

    def test_status_is_final(self) -> None:
        result = _urge_observation(_checkin())
        assert result["status"] == "final"

    def test_value_integer_matches_intensity(self) -> None:
        result = _urge_observation(_checkin(intensity=7))
        assert result["valueInteger"] == 7

    def test_intensity_zero_allowed(self) -> None:
        result = _urge_observation(_checkin(intensity=0))
        assert result["valueInteger"] == 0

    def test_intensity_10_allowed(self) -> None:
        result = _urge_observation(_checkin(intensity=10))
        assert result["valueInteger"] == 10

    def test_effective_datetime_has_z_suffix(self) -> None:
        result = _urge_observation(_checkin())
        assert str(result["effectiveDateTime"]).endswith("Z")

    def test_uses_disciplineos_code_system_not_loinc(self) -> None:
        # Proprietary system because no LOINC code covers urge intensity
        serialized = json.dumps(_urge_observation(_checkin()))
        assert DISCIPLINEOS_CODE_SYSTEM in serialized
        assert "loinc.org" not in serialized

    def test_category_uses_survey_code(self) -> None:
        result = _urge_observation(_checkin())
        serialized = json.dumps(result)
        assert '"survey"' in serialized

    def test_non_utc_datetime_converted_to_z(self) -> None:
        from datetime import timezone, timedelta
        eastern = datetime(2026, 1, 15, 7, 0, 0, tzinfo=timezone(timedelta(hours=-5)))
        result = _urge_observation(_checkin(checked_in_at=eastern))
        # 07:00-05:00 = 12:00 UTC
        assert result["effectiveDateTime"] == "2026-01-15T12:00:00Z"

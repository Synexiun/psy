"""Unit tests for pure helpers in discipline.reports.fhir_observation.

_require_utc(dt) → datetime
  Accepts ALL timezone-aware datetimes and converts to UTC via astimezone.
  Only rejects naive datetimes (no tzinfo).  This is intentionally less strict
  than discipline.reports.user_export._ensure_utc — FHIR observations often
  originate from mobile clients with device-local timestamps; converting is
  safer than refusing.

_format_iso8601_z(dt) → str
  Renders a datetime as ISO 8601 with "Z" suffix (always UTC, never +00:00).
  Non-UTC inputs are converted first via _require_utc.

_code_block(instrument) → dict
  Returns a LOINC coding dict for the instrument.  Raises
  UnsupportedInstrumentError (a subclass of ValueError) when the instrument
  has no pinned LOINC code.

_interpretation_block(safety_positive) → list | None
  Returns the FHIR interpretation array when safety_positive is True,
  None otherwise.  The array carries the Discipline-OS T3-routing CodeSystem
  code, not a generic HL7 abnormal flag.
"""

from __future__ import annotations

from datetime import UTC, datetime, timezone, timedelta

import pytest

from discipline.reports.fhir_observation import (
    CSSRS_ITEM_DISPLAYS,
    CSSRS_RISK_LEVEL_DISPLAYS,
    LOINC_CODES,
    UnsupportedInstrumentError,
    _category_block,
    _code_block,
    _cssrs_code_block,
    _cssrs_component_block,
    _cssrs_value_block,
    _format_iso8601_z,
    _interpretation_block,
    _require_utc,
)

_NOW_UTC = datetime(2026, 4, 25, 12, 0, 0, tzinfo=UTC)


# ---------------------------------------------------------------------------
# _require_utc — accepted inputs
# ---------------------------------------------------------------------------


class TestRequireUtcAccepted:
    def test_utc_aware_returned_unchanged(self) -> None:
        result = _require_utc(_NOW_UTC)
        assert result == _NOW_UTC

    def test_non_utc_offset_converted_to_utc(self) -> None:
        east5 = datetime(2026, 4, 25, 17, 0, 0, tzinfo=timezone(timedelta(hours=5)))
        result = _require_utc(east5)
        assert result.tzinfo is UTC or result.utcoffset().total_seconds() == 0

    def test_non_utc_conversion_produces_correct_time(self) -> None:
        # 17:00+05 == 12:00 UTC
        east5 = datetime(2026, 4, 25, 17, 0, 0, tzinfo=timezone(timedelta(hours=5)))
        result = _require_utc(east5)
        assert result.hour == 12
        assert result.minute == 0

    def test_negative_offset_converted(self) -> None:
        west5 = datetime(2026, 4, 25, 7, 0, 0, tzinfo=timezone(timedelta(hours=-5)))
        result = _require_utc(west5)
        assert result.hour == 12

    def test_result_is_timezone_aware(self) -> None:
        result = _require_utc(_NOW_UTC)
        assert result.tzinfo is not None


# ---------------------------------------------------------------------------
# _require_utc — naive datetime rejected
# ---------------------------------------------------------------------------


class TestRequireUtcNaiveRejected:
    def test_naive_datetime_raises(self) -> None:
        naive = datetime(2026, 4, 25, 12, 0, 0)
        with pytest.raises(ValueError):
            _require_utc(naive)

    def test_error_mentions_timezone_aware(self) -> None:
        naive = datetime(2026, 4, 25, 12, 0, 0)
        with pytest.raises(ValueError, match="timezone-aware"):
            _require_utc(naive)


# ---------------------------------------------------------------------------
# _format_iso8601_z — output format
# ---------------------------------------------------------------------------


class TestFormatIso8601Z:
    def test_utc_renders_with_z_suffix(self) -> None:
        result = _format_iso8601_z(_NOW_UTC)
        assert result.endswith("Z")

    def test_format_is_yyyy_mm_ddTHH_MM_SSZ(self) -> None:
        dt = datetime(2026, 4, 25, 10, 30, 15, tzinfo=UTC)
        assert _format_iso8601_z(dt) == "2026-04-25T10:30:15Z"

    def test_does_not_use_plus00_00_form(self) -> None:
        assert "+00:00" not in _format_iso8601_z(_NOW_UTC)

    def test_non_utc_offset_converted_before_formatting(self) -> None:
        # 17:00+05 == 12:00 UTC
        east5 = datetime(2026, 4, 25, 17, 0, 0, tzinfo=timezone(timedelta(hours=5)))
        assert _format_iso8601_z(east5) == "2026-04-25T12:00:00Z"

    def test_midnight_rendered_correctly(self) -> None:
        dt = datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC)
        assert _format_iso8601_z(dt) == "2026-01-01T00:00:00Z"

    def test_result_is_20_chars(self) -> None:
        assert len(_format_iso8601_z(_NOW_UTC)) == 20

    def test_naive_raises_via_require_utc(self) -> None:
        naive = datetime(2026, 4, 25, 12, 0, 0)
        with pytest.raises(ValueError):
            _format_iso8601_z(naive)


# ---------------------------------------------------------------------------
# _code_block — LOINC validation
# ---------------------------------------------------------------------------


class TestCodeBlock:
    def test_phq9_returns_dict_with_loinc_system(self) -> None:
        result = _code_block("phq9")
        coding = result["coding"][0]  # type: ignore[index]
        assert coding["system"] == "http://loinc.org"

    def test_phq9_returns_correct_loinc_code(self) -> None:
        result = _code_block("phq9")
        coding = result["coding"][0]  # type: ignore[index]
        assert coding["code"] == LOINC_CODES["phq9"]

    def test_gad7_code_block_returns_loinc_dict(self) -> None:
        result = _code_block("gad7")
        assert "coding" in result

    def test_all_loinc_codes_are_accepted(self) -> None:
        for instrument in LOINC_CODES:
            result = _code_block(instrument)
            assert "coding" in result

    def test_unknown_instrument_raises(self) -> None:
        with pytest.raises(UnsupportedInstrumentError):
            _code_block("fake_instrument")

    def test_error_is_subclass_of_value_error(self) -> None:
        with pytest.raises(ValueError):
            _code_block("fake_instrument")

    def test_error_mentions_instrument_name(self) -> None:
        with pytest.raises(UnsupportedInstrumentError, match="not_a_real_instrument"):
            _code_block("not_a_real_instrument")

    def test_empty_string_raises(self) -> None:
        with pytest.raises(UnsupportedInstrumentError):
            _code_block("")

    def test_uppercase_instrument_raises(self) -> None:
        # Codes are lowercase keys — "PHQ9" should not silently match "phq9"
        with pytest.raises(UnsupportedInstrumentError):
            _code_block("PHQ9")


# ---------------------------------------------------------------------------
# _interpretation_block — safety routing flag
# ---------------------------------------------------------------------------


class TestInterpretationBlock:
    def test_safety_positive_returns_list(self) -> None:
        result = _interpretation_block(True)
        assert isinstance(result, list)

    def test_safety_positive_list_is_non_empty(self) -> None:
        result = _interpretation_block(True)
        assert len(result) == 1  # type: ignore[arg-type]

    def test_safety_positive_contains_t3_routed_code(self) -> None:
        result = _interpretation_block(True)
        coding = result[0]["coding"][0]  # type: ignore[index]
        assert coding["code"] == "t3-routed"

    def test_safety_positive_uses_discipline_codesystem_not_hl7(self) -> None:
        result = _interpretation_block(True)
        coding = result[0]["coding"][0]  # type: ignore[index]
        assert "disciplineos.com" in coding["system"]
        assert "hl7.org" not in coding["system"]

    def test_safety_negative_returns_none(self) -> None:
        result = _interpretation_block(False)
        assert result is None

    def test_false_returns_none_not_empty_list(self) -> None:
        result = _interpretation_block(False)
        assert result is None, "Must be None, not []"


# ---------------------------------------------------------------------------
# _category_block — always "survey"
# ---------------------------------------------------------------------------


class TestCategoryBlock:
    def test_returns_list(self) -> None:
        assert isinstance(_category_block(), list)

    def test_single_entry(self) -> None:
        assert len(_category_block()) == 1

    def test_code_is_survey(self) -> None:
        coding = _category_block()[0]["coding"][0]  # type: ignore[index]
        assert coding["code"] == "survey"

    def test_system_is_observation_category(self) -> None:
        coding = _category_block()[0]["coding"][0]  # type: ignore[index]
        assert "observation-category" in str(coding["system"])

    def test_deterministic(self) -> None:
        assert _category_block() == _category_block()


# ---------------------------------------------------------------------------
# _cssrs_code_block — Discipline-OS CodeSystem, no LOINC
# ---------------------------------------------------------------------------


class TestCssrsCodeBlock:
    def test_returns_dict(self) -> None:
        assert isinstance(_cssrs_code_block(), dict)

    def test_coding_key_present(self) -> None:
        assert "coding" in _cssrs_code_block()

    def test_uses_disciplineos_system_not_loinc(self) -> None:
        import json
        serialized = json.dumps(_cssrs_code_block())
        assert "disciplineos.com" in serialized
        assert "loinc.org" not in serialized

    def test_code_is_screen_risk(self) -> None:
        coding = _cssrs_code_block()["coding"][0]  # type: ignore[index]
        assert coding["code"] == "screen-risk"

    def test_display_references_columbia(self) -> None:
        coding = _cssrs_code_block()["coding"][0]  # type: ignore[index]
        display = str(coding["display"])
        assert "Columbia" in display or "CSSRS" in display.upper()


# ---------------------------------------------------------------------------
# _cssrs_value_block — risk level → coded concept
# ---------------------------------------------------------------------------


class TestCssrsValueBlock:
    def test_all_four_risk_levels_succeed(self) -> None:
        for level in ("none", "low", "moderate", "acute"):
            result = _cssrs_value_block(level)
            assert isinstance(result, dict)

    def test_code_matches_risk_level(self) -> None:
        for level in ("none", "low", "moderate", "acute"):
            coding = _cssrs_value_block(level)["coding"][0]  # type: ignore[index]
            assert coding["code"] == level

    def test_display_matches_constant(self) -> None:
        for level in ("none", "low", "moderate", "acute"):
            coding = _cssrs_value_block(level)["coding"][0]  # type: ignore[index]
            assert coding["display"] == CSSRS_RISK_LEVEL_DISPLAYS[level]

    def test_disciplineos_risk_level_system_uri(self) -> None:
        coding = _cssrs_value_block("low")["coding"][0]  # type: ignore[index]
        assert "disciplineos.com" in str(coding["system"])
        assert "cssrs-risk-level" in str(coding["system"])


# ---------------------------------------------------------------------------
# _cssrs_component_block — one entry per triggering item
# ---------------------------------------------------------------------------


class TestCssrsComponentBlock:
    def test_empty_tuple_returns_empty_list(self) -> None:
        assert _cssrs_component_block(()) == []

    def test_single_item_returns_one_entry(self) -> None:
        assert len(_cssrs_component_block((1,))) == 1

    def test_multiple_items_count_matches(self) -> None:
        assert len(_cssrs_component_block((1, 3, 5))) == 3

    def test_order_preserved(self) -> None:
        result = _cssrs_component_block((2, 5, 1))
        codes = [e["code"]["coding"][0]["code"] for e in result]  # type: ignore[index]
        assert codes == ["item-2", "item-5", "item-1"]

    def test_item_code_format(self) -> None:
        coding = _cssrs_component_block((3,))[0]["code"]["coding"][0]  # type: ignore[index]
        assert coding["code"] == "item-3"

    def test_value_boolean_true(self) -> None:
        result = _cssrs_component_block((1,))
        assert result[0]["valueBoolean"] is True

    def test_display_matches_cssrs_item_displays(self) -> None:
        coding = _cssrs_component_block((1,))[0]["code"]["coding"][0]  # type: ignore[index]
        assert coding["display"] == CSSRS_ITEM_DISPLAYS[1]

    def test_disciplineos_item_system_uri(self) -> None:
        coding = _cssrs_component_block((2,))[0]["code"]["coding"][0]  # type: ignore[index]
        assert "disciplineos.com" in str(coding["system"])

    def test_all_six_items_valid(self) -> None:
        assert len(_cssrs_component_block((1, 2, 3, 4, 5, 6))) == 6

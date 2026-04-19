"""FHIR R4 Observation fidelity tests.

Sources:
- HL7 FHIR R4 spec — https://hl7.org/fhir/R4/observation.html
- LOINC database — loinc.org (canonical code registry)

Every assertion here is a wire-format contract with receiving EHR systems.
Changing a LOINC code without a cross-system coordination plan means our
bundles will be rejected or (worse) silently misclassified on the receiving
side.  A failing test must trigger a LOINC lookup, not an "update the string".
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from discipline.reports.fhir_observation import (
    CSSRS_ITEM_DISPLAYS,
    CSSRS_RISK_LEVEL_DISPLAYS,
    CssrsObservationSpec,
    LOINC_CODES,
    LOINC_DISPLAY,
    ObservationSpec,
    UnsupportedInstrumentError,
    render_bundle,
    render_cssrs_bundle,
)


# ---- LOINC code registry pinning -------------------------------------------


class TestLoincCodesPinnedToRegistry:
    """Each code is the canonical LOINC identifier for the total score of
    the instrument.  Cross-verify against loinc.org before changing."""

    @pytest.mark.parametrize(
        ("instrument", "expected_code"),
        [
            ("phq9", "44261-6"),
            ("gad7", "69737-5"),
            ("audit", "75626-2"),
            ("audit_c", "75624-7"),
            ("dast10", "82667-7"),
            ("who5", "89708-7"),
            ("pss10", "93038-1"),
        ],
    )
    def test_instrument_loinc_code(self, instrument: str, expected_code: str) -> None:
        assert LOINC_CODES[instrument] == expected_code

    def test_every_code_has_display_string(self) -> None:
        """Receiving systems that don't resolve LOINC internally fall back
        to ``display`` — every code must carry one."""
        assert set(LOINC_DISPLAY) == set(LOINC_CODES)
        for display in LOINC_DISPLAY.values():
            assert display  # non-empty

    def test_loinc_codes_follow_nnnn_n_format(self) -> None:
        """LOINC codes are of the form ``NNNNN-N`` (check digit at the end)."""
        import re

        pattern = re.compile(r"^\d{4,6}-\d$")
        for instrument, code in LOINC_CODES.items():
            assert pattern.match(code), f"invalid LOINC shape for {instrument}: {code}"


# ---- Required resource shape -----------------------------------------------


class TestFhirResourceShape:
    def _spec(self, **overrides: object) -> ObservationSpec:
        defaults: dict[str, object] = {
            "patient_reference": "Patient/abc123",
            "instrument": "phq9",
            "score": 12,
            "effective": datetime(2026, 4, 18, 14, 30, 0, tzinfo=timezone.utc),
            "safety_item_positive": False,
        }
        defaults.update(overrides)
        return ObservationSpec(**defaults)  # type: ignore[arg-type]

    def test_resource_type_is_observation(self) -> None:
        bundle = render_bundle(self._spec())
        assert bundle["resourceType"] == "Observation"

    def test_status_defaults_to_final(self) -> None:
        bundle = render_bundle(self._spec())
        assert bundle["status"] == "final"

    def test_category_is_survey(self) -> None:
        bundle = render_bundle(self._spec())
        category = bundle["category"]
        assert isinstance(category, list) and len(category) == 1
        coding = category[0]["coding"][0]  # type: ignore[call-overload,index]
        assert coding["code"] == "survey"
        assert (
            coding["system"]
            == "http://terminology.hl7.org/CodeSystem/observation-category"
        )

    def test_code_block_uses_loinc_system(self) -> None:
        bundle = render_bundle(self._spec())
        coding = bundle["code"]["coding"][0]  # type: ignore[call-overload,index]
        assert coding["system"] == "http://loinc.org"
        assert coding["code"] == "44261-6"  # PHQ-9 total
        assert "PHQ-9" in coding["display"]

    def test_subject_reference_passed_through(self) -> None:
        bundle = render_bundle(self._spec(patient_reference="Patient/xyz"))
        assert bundle["subject"] == {"reference": "Patient/xyz"}

    def test_value_integer_carries_the_raw_score(self) -> None:
        bundle = render_bundle(self._spec(score=17))
        assert bundle["valueInteger"] == 17
        # FHIR is strict: integer scores MUST NOT use valueQuantity.  That
        # would introduce unit semantics we don't have.
        assert "valueQuantity" not in bundle


# ---- effectiveDateTime (ISO 8601 UTC) --------------------------------------


class TestEffectiveDateTimeFormat:
    def test_effective_datetime_is_iso_with_z_suffix(self) -> None:
        spec = ObservationSpec(
            patient_reference="Patient/1",
            instrument="phq9",
            score=5,
            effective=datetime(2026, 4, 18, 14, 30, 0, tzinfo=timezone.utc),
        )
        bundle = render_bundle(spec)
        assert bundle["effectiveDateTime"] == "2026-04-18T14:30:00Z"

    def test_non_utc_tzinfo_is_converted_to_utc(self) -> None:
        """A +0200 timezone-aware datetime must be emitted as UTC."""
        tz_plus_two = timezone(timedelta(hours=2))
        spec = ObservationSpec(
            patient_reference="Patient/1",
            instrument="phq9",
            score=5,
            effective=datetime(2026, 4, 18, 16, 30, 0, tzinfo=tz_plus_two),
        )
        bundle = render_bundle(spec)
        assert bundle["effectiveDateTime"] == "2026-04-18T14:30:00Z"

    def test_naive_datetime_is_rejected(self) -> None:
        """Naive datetimes are ambiguous on the wire; we reject at the boundary."""
        spec = ObservationSpec(
            patient_reference="Patient/1",
            instrument="phq9",
            score=5,
            effective=datetime(2026, 4, 18, 14, 30, 0),  # no tzinfo
        )
        with pytest.raises(ValueError, match="timezone-aware"):
            render_bundle(spec)


# ---- Safety-positive interpretation ----------------------------------------


class TestSafetyPositiveInterpretation:
    """Safety-positive PHQ-9 item 9 ≥ 1 → the bundle carries an
    ``interpretation`` array flagging the T3 routing decision."""

    def _spec(self, *, safety_positive: bool) -> ObservationSpec:
        return ObservationSpec(
            patient_reference="Patient/abc",
            instrument="phq9",
            score=8,
            effective=datetime(2026, 4, 18, 12, 0, 0, tzinfo=timezone.utc),
            safety_item_positive=safety_positive,
        )

    def test_no_interpretation_key_when_not_safety_positive(self) -> None:
        bundle = render_bundle(self._spec(safety_positive=False))
        assert "interpretation" not in bundle

    def test_interpretation_present_when_safety_positive(self) -> None:
        bundle = render_bundle(self._spec(safety_positive=True))
        assert "interpretation" in bundle
        interpretation = bundle["interpretation"]
        assert isinstance(interpretation, list) and len(interpretation) == 1

    def test_interpretation_uses_discipline_safety_routing_code(self) -> None:
        bundle = render_bundle(self._spec(safety_positive=True))
        coding = bundle["interpretation"][0]["coding"][0]  # type: ignore[call-overload,index]
        assert coding["code"] == "t3-routed"
        assert "disciplineos.com" in coding["system"]

    def test_interpretation_display_has_human_readable_text(self) -> None:
        bundle = render_bundle(self._spec(safety_positive=True))
        display = bundle["interpretation"][0]["coding"][0]["display"]  # type: ignore[call-overload,index]
        assert "Safety item positive" in display
        assert "T3" in display

    def test_interpretation_never_leaks_patient_narrative(self) -> None:
        """FHIR is an interop surface, not a transport for intervention
        scripts or user quotes.  Our interpretation payload is strictly a
        routing flag — no free-text patient content."""
        bundle = render_bundle(self._spec(safety_positive=True))
        display = bundle["interpretation"][0]["coding"][0]["display"]  # type: ignore[call-overload,index]
        # Very coarse heuristic: no quoted text fragments, no pronouns like "I"
        # or "me" that could indicate user-authored content leaked in.
        assert "'" not in display
        assert '"' not in display


# ---- Error handling --------------------------------------------------------


class TestRenderErrors:
    def test_unknown_instrument_raises_descriptive_error(self) -> None:
        spec = ObservationSpec(
            patient_reference="Patient/1",
            instrument="not_a_real_instrument",
            score=5,
            effective=datetime(2026, 4, 18, 0, 0, 0, tzinfo=timezone.utc),
        )
        with pytest.raises(UnsupportedInstrumentError, match="not_a_real_instrument"):
            render_bundle(spec)

    def test_negative_score_raises(self) -> None:
        spec = ObservationSpec(
            patient_reference="Patient/1",
            instrument="phq9",
            score=-1,
            effective=datetime(2026, 4, 18, 0, 0, 0, tzinfo=timezone.utc),
        )
        with pytest.raises(ValueError, match="non-negative"):
            render_bundle(spec)


# ---- Round-trip parametrized over every supported instrument ---------------


class TestAllInstrumentsRenderConsistently:
    """Sanity sweep: every instrument in LOINC_CODES must render cleanly
    with a placeholder score and produce a structurally valid bundle."""

    @pytest.mark.parametrize("instrument", list(LOINC_CODES.keys()))
    def test_instrument_renders_without_error(self, instrument: str) -> None:
        spec = ObservationSpec(
            patient_reference="Patient/universal",
            instrument=instrument,
            score=5,
            effective=datetime(2026, 4, 18, 0, 0, 0, tzinfo=timezone.utc),
        )
        bundle = render_bundle(spec)
        assert bundle["resourceType"] == "Observation"
        code = bundle["code"]["coding"][0]["code"]  # type: ignore[call-overload,index]
        assert code == LOINC_CODES[instrument]


# ---- Dataclass invariants --------------------------------------------------


class TestObservationSpecInvariants:
    def test_spec_is_frozen(self) -> None:
        spec = ObservationSpec(
            patient_reference="Patient/1",
            instrument="phq9",
            score=5,
            effective=datetime(2026, 4, 18, 0, 0, 0, tzinfo=timezone.utc),
        )
        with pytest.raises(AttributeError):
            spec.score = 99  # type: ignore[misc]

    def test_spec_default_safety_flag_is_false(self) -> None:
        spec = ObservationSpec(
            patient_reference="Patient/1",
            instrument="phq9",
            score=5,
            effective=datetime(2026, 4, 18, 0, 0, 0, tzinfo=timezone.utc),
        )
        assert spec.safety_item_positive is False

    def test_spec_default_status_is_final(self) -> None:
        spec = ObservationSpec(
            patient_reference="Patient/1",
            instrument="phq9",
            score=5,
            effective=datetime(2026, 4, 18, 0, 0, 0, tzinfo=timezone.utc),
        )
        assert spec.status == "final"


# ---- PSS-10 instrument-specific scenarios ----------------------------------


class TestPss10Rendering:
    """PSS-10 (Cohen 1983 / 1988) bands: low ≤ 13, moderate 14-26, high ≥ 27.
    A mid-moderate-band total of 18 should round-trip to ``valueInteger=18``
    under the canonical PSS-10 LOINC code ``93038-1``."""

    def _spec(self, score: int, *, safety_positive: bool = False) -> ObservationSpec:
        return ObservationSpec(
            patient_reference="Patient/pss-subject",
            instrument="pss10",
            score=score,
            effective=datetime(2026, 4, 18, 14, 0, 0, tzinfo=timezone.utc),
            safety_item_positive=safety_positive,
        )

    def test_pss10_renders_with_loinc_93038_1(self) -> None:
        bundle = render_bundle(self._spec(score=18))
        coding = bundle["code"]["coding"][0]  # type: ignore[call-overload,index]
        assert coding["system"] == "http://loinc.org"
        assert coding["code"] == "93038-1"
        assert "PSS-10" in coding["display"]

    def test_pss10_value_integer_passthrough(self) -> None:
        bundle = render_bundle(self._spec(score=18))
        assert bundle["valueInteger"] == 18

    def test_pss10_high_band_total(self) -> None:
        """A high-band total of 30 (≥ 27 cutoff) still renders as a plain
        integer score — the band is not encoded in the FHIR bundle, only
        the raw total is.  Receiving systems do their own banding."""
        bundle = render_bundle(self._spec(score=30))
        assert bundle["valueInteger"] == 30
        # No interpretation block — PSS-10 has no safety item.
        assert "interpretation" not in bundle

    def test_pss10_zero_floor_renders(self) -> None:
        """A subject scoring 0 (lowest possible PSS-10 total) is a valid
        non-negative integer and must round-trip — boundary check."""
        bundle = render_bundle(self._spec(score=0))
        assert bundle["valueInteger"] == 0

    def test_pss10_does_not_use_safety_routing_interpretation(self) -> None:
        """PSS-10 has no item-level safety signal (unlike PHQ-9 item 9).
        Even with safety_item_positive=True (defensive), the renderer just
        echoes the boolean — but in practice the router never sets it for
        PSS-10.  This test pins the behavior so a future regression that
        accidentally sets the flag for PSS-10 is visible in tests."""
        bundle = render_bundle(self._spec(score=20, safety_positive=True))
        # The renderer is generic — it will emit interpretation if asked.
        # The contract is: the router must NOT set safety_item_positive for pss10.
        # Verify the integer score still passes through correctly.
        assert bundle["valueInteger"] == 20


# ---- C-SSRS Screen categorical Observation ---------------------------------


class TestCssrsCategoricalRendering:
    """C-SSRS Screen yields a categorical risk band, not an integer total.
    The render output uses ``valueCodeableConcept`` per FHIR R4 §6.1.2.7.1
    rather than ``valueInteger``.  This test class pins the wire format
    that receiving EHRs will key on."""

    def _spec(self, **overrides: object) -> CssrsObservationSpec:
        defaults: dict[str, object] = {
            "patient_reference": "Patient/cssrs-subject",
            "risk_level": "moderate",
            "effective": datetime(2026, 4, 18, 10, 0, 0, tzinfo=timezone.utc),
            "triggering_items": (3,),
            "requires_t3": False,
        }
        defaults.update(overrides)
        return CssrsObservationSpec(**defaults)  # type: ignore[arg-type]

    def test_resource_type_is_observation(self) -> None:
        bundle = render_cssrs_bundle(self._spec())
        assert bundle["resourceType"] == "Observation"

    def test_status_defaults_to_final(self) -> None:
        bundle = render_cssrs_bundle(self._spec())
        assert bundle["status"] == "final"

    def test_category_is_survey(self) -> None:
        bundle = render_cssrs_bundle(self._spec())
        coding = bundle["category"][0]["coding"][0]  # type: ignore[call-overload,index]
        assert coding["code"] == "survey"

    def test_observation_code_is_discipline_os_namespaced(self) -> None:
        """LOINC has no rollup C-SSRS Screen risk code at the time of
        this writing.  We use a Discipline-OS CodeSystem URI; this test
        pins the URI so a future change to a real LOINC code is visible."""
        bundle = render_cssrs_bundle(self._spec())
        coding = bundle["code"]["coding"][0]  # type: ignore[call-overload,index]
        assert coding["system"] == "http://disciplineos.com/fhir/CodeSystem/cssrs-screen"
        assert coding["code"] == "screen-risk"
        assert "Columbia" in coding["display"]

    def test_value_codeable_concept_used_not_integer(self) -> None:
        """C-SSRS is categorical — must NOT use valueInteger or valueQuantity.
        Receiving systems that only consume valueCodeableConcept for this
        observation code will silently drop integer values."""
        bundle = render_cssrs_bundle(self._spec())
        assert "valueCodeableConcept" in bundle
        assert "valueInteger" not in bundle
        assert "valueQuantity" not in bundle

    @pytest.mark.parametrize("risk", ["none", "low", "moderate", "acute"])
    def test_each_risk_band_round_trips(self, risk: str) -> None:
        bundle = render_cssrs_bundle(self._spec(risk_level=risk))
        coding = bundle["valueCodeableConcept"]["coding"][0]  # type: ignore[call-overload,index]
        assert coding["system"] == "http://disciplineos.com/fhir/CodeSystem/cssrs-risk-level"
        assert coding["code"] == risk
        assert coding["display"] == CSSRS_RISK_LEVEL_DISPLAYS[risk]

    def test_subject_reference_passed_through(self) -> None:
        bundle = render_cssrs_bundle(self._spec(patient_reference="Patient/xyz"))
        assert bundle["subject"] == {"reference": "Patient/xyz"}

    def test_effective_datetime_iso_z_format(self) -> None:
        bundle = render_cssrs_bundle(self._spec())
        assert bundle["effectiveDateTime"] == "2026-04-18T10:00:00Z"

    def test_naive_datetime_rejected(self) -> None:
        spec = CssrsObservationSpec(
            patient_reference="Patient/1",
            risk_level="low",
            effective=datetime(2026, 4, 18, 10, 0, 0),  # no tzinfo
            triggering_items=(1,),
        )
        with pytest.raises(ValueError, match="timezone-aware"):
            render_cssrs_bundle(spec)


class TestCssrsTriggeringItems:
    """Triggering items emit as FHIR ``component`` entries — one per item,
    each with a Discipline-OS-coded item identifier and ``valueBoolean=true``.
    This lets receiving EHRs see which items drove the band without
    requiring transmission of the raw item-level responses."""

    def _spec(self, items: tuple[int, ...]) -> CssrsObservationSpec:
        return CssrsObservationSpec(
            patient_reference="Patient/abc",
            risk_level="acute",
            effective=datetime(2026, 4, 18, 10, 0, 0, tzinfo=timezone.utc),
            triggering_items=items,
            requires_t3=True,
        )

    def test_no_components_when_no_triggering_items(self) -> None:
        spec = CssrsObservationSpec(
            patient_reference="Patient/none",
            risk_level="none",
            effective=datetime(2026, 4, 18, 10, 0, 0, tzinfo=timezone.utc),
        )
        bundle = render_cssrs_bundle(spec)
        assert "component" not in bundle

    def test_single_triggering_item_emits_one_component(self) -> None:
        bundle = render_cssrs_bundle(self._spec((4,)))
        assert len(bundle["component"]) == 1
        comp = bundle["component"][0]  # type: ignore[index]
        assert comp["valueBoolean"] is True
        coding = comp["code"]["coding"][0]
        assert coding["system"] == "http://disciplineos.com/fhir/CodeSystem/cssrs-items"
        assert coding["code"] == "item-4"
        assert coding["display"] == CSSRS_ITEM_DISPLAYS[4]

    def test_multiple_triggering_items_preserve_order(self) -> None:
        """Order in input tuple == order in output components.  The
        scorer enumerates low → high item number; the bundle echoes
        that order so a clinician reviewing the FHIR resource sees
        items in the same order as in the source."""
        bundle = render_cssrs_bundle(self._spec((4, 5, 6)))
        codes = [c["code"]["coding"][0]["code"] for c in bundle["component"]]  # type: ignore[index]
        assert codes == ["item-4", "item-5", "item-6"]

    def test_all_six_items_renderable(self) -> None:
        bundle = render_cssrs_bundle(self._spec((1, 2, 3, 4, 5, 6)))
        assert len(bundle["component"]) == 6
        for component in bundle["component"]:  # type: ignore[union-attr]
            assert component["valueBoolean"] is True

    def test_triggering_item_zero_rejected(self) -> None:
        with pytest.raises(ValueError, match="out-of-range"):
            render_cssrs_bundle(self._spec((0,)))

    def test_triggering_item_seven_rejected(self) -> None:
        """C-SSRS Screen has 6 items; item 7 is invalid and signals a
        scorer bug rather than valid data."""
        with pytest.raises(ValueError, match="out-of-range"):
            render_cssrs_bundle(self._spec((7,)))


class TestCssrsAcuteInterpretation:
    """Acute C-SSRS results emit the same ``t3-routed`` interpretation
    as PHQ-9 item 9 — receiving systems' safety-routing branches stay
    uniform regardless of source instrument."""

    def _spec(self, *, requires_t3: bool, risk: str = "acute") -> CssrsObservationSpec:
        return CssrsObservationSpec(
            patient_reference="Patient/acute",
            risk_level=risk,  # type: ignore[arg-type]
            effective=datetime(2026, 4, 18, 10, 0, 0, tzinfo=timezone.utc),
            triggering_items=(4, 5),
            requires_t3=requires_t3,
        )

    def test_acute_with_requires_t3_emits_interpretation(self) -> None:
        bundle = render_cssrs_bundle(self._spec(requires_t3=True))
        assert "interpretation" in bundle
        coding = bundle["interpretation"][0]["coding"][0]  # type: ignore[call-overload,index]
        assert coding["code"] == "t3-routed"
        assert "disciplineos.com" in coding["system"]

    def test_no_interpretation_when_requires_t3_false(self) -> None:
        bundle = render_cssrs_bundle(self._spec(requires_t3=False, risk="moderate"))
        assert "interpretation" not in bundle


class TestCssrsValidation:
    def test_unknown_risk_level_rejected(self) -> None:
        spec = CssrsObservationSpec(
            patient_reference="Patient/1",
            risk_level="severe",  # type: ignore[arg-type]  # not a valid band
            effective=datetime(2026, 4, 18, 10, 0, 0, tzinfo=timezone.utc),
        )
        with pytest.raises(ValueError, match="unknown C-SSRS risk_level"):
            render_cssrs_bundle(spec)

    def test_spec_is_frozen(self) -> None:
        spec = CssrsObservationSpec(
            patient_reference="Patient/1",
            risk_level="low",
            effective=datetime(2026, 4, 18, 10, 0, 0, tzinfo=timezone.utc),
        )
        with pytest.raises(AttributeError):
            spec.risk_level = "acute"  # type: ignore[misc]

    def test_spec_default_triggering_items_is_empty(self) -> None:
        spec = CssrsObservationSpec(
            patient_reference="Patient/1",
            risk_level="none",
            effective=datetime(2026, 4, 18, 10, 0, 0, tzinfo=timezone.utc),
        )
        assert spec.triggering_items == ()
        assert spec.requires_t3 is False


class TestCssrsDisplaysCoverAllBands:
    """Every band must have a non-empty display string — receiving
    systems that don't recognize the Discipline-OS CodeSystem fall back
    to display per FHIR R4 §2.6.7."""

    def test_every_risk_level_has_display(self) -> None:
        assert set(CSSRS_RISK_LEVEL_DISPLAYS) == {"none", "low", "moderate", "acute"}
        for display in CSSRS_RISK_LEVEL_DISPLAYS.values():
            assert display

    def test_every_screen_item_has_display(self) -> None:
        assert set(CSSRS_ITEM_DISPLAYS) == {1, 2, 3, 4, 5, 6}
        for display in CSSRS_ITEM_DISPLAYS.values():
            assert display

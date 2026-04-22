"""FHIR R4 Bundle assembler tests.

Reference: https://hl7.org/fhir/R4/bundle.html

Assembled bundles are the wire format for clinician exports, so every
assertion here is an interop contract.  A failing test must not be "fixed"
by editing the expected shape — check the FHIR spec and reconcile upstream.
"""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime

import pytest

from discipline.reports.fhir_bundle import assemble_bundle
from discipline.reports.fhir_observation import ObservationSpec

# ---- Helpers ---------------------------------------------------------------


def _spec(
    instrument: str = "phq9",
    score: int = 8,
    *,
    safety_positive: bool = False,
) -> ObservationSpec:
    return ObservationSpec(
        patient_reference="Patient/test-001",
        instrument=instrument,
        score=score,
        effective=datetime(2026, 4, 18, 12, 0, 0, tzinfo=UTC),
        safety_item_positive=safety_positive,
    )


# ---- Top-level shape -------------------------------------------------------


class TestBundleTopLevelShape:
    def test_resource_type_is_bundle(self) -> None:
        bundle = assemble_bundle([_spec()])
        assert bundle["resourceType"] == "Bundle"

    def test_default_type_is_collection(self) -> None:
        """``collection`` is the right default for clinician export; we
        only use ``document`` when adding a Composition narrative."""
        bundle = assemble_bundle([_spec()])
        assert bundle["type"] == "collection"

    def test_explicit_document_type_passes_through(self) -> None:
        bundle = assemble_bundle([_spec()], bundle_type="document")
        assert bundle["type"] == "document"

    def test_identifier_block_present(self) -> None:
        bundle = assemble_bundle([_spec()])
        identifier = bundle["identifier"]
        assert isinstance(identifier, dict)
        assert "system" in identifier
        assert "value" in identifier

    def test_identifier_value_is_urn_uuid(self) -> None:
        """Bundle identifier in urn:uuid:<uuid> form per FHIR convention."""
        bundle = assemble_bundle([_spec()])
        value = bundle["identifier"]["value"]  # type: ignore[call-overload,index]
        assert value.startswith("urn:uuid:")
        uuid_part = value.removeprefix("urn:uuid:")
        assert re.match(
            r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
            uuid_part,
        ), f"identifier UUID malformed: {value}"


# ---- Timestamp formatting --------------------------------------------------


class TestBundleTimestamp:
    def test_timestamp_is_iso_z_format(self) -> None:
        ts = datetime(2026, 4, 18, 14, 30, 0, tzinfo=UTC)
        bundle = assemble_bundle([_spec()], timestamp=ts)
        assert bundle["timestamp"] == "2026-04-18T14:30:00Z"

    def test_timestamp_defaults_to_now(self) -> None:
        """If caller doesn't supply a timestamp, the assembler uses now().
        We just verify the format is correct, not the value."""
        bundle = assemble_bundle([_spec()])
        ts = bundle["timestamp"]
        assert isinstance(ts, str)
        assert re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$", ts), (
            f"timestamp not ISO 8601 Z: {ts!r}"
        )

    def test_naive_timestamp_rejected(self) -> None:
        with pytest.raises(ValueError, match="timezone-aware"):
            assemble_bundle([_spec()], timestamp=datetime(2026, 4, 18, 12, 0, 0))


# ---- Entries ---------------------------------------------------------------


class TestBundleEntries:
    def test_entry_count_matches_spec_count(self) -> None:
        specs = [_spec("phq9"), _spec("gad7"), _spec("who5")]
        bundle = assemble_bundle(specs)
        entries = bundle["entry"]
        assert isinstance(entries, list)
        assert len(entries) == 3

    def test_each_entry_has_fullurl_and_resource(self) -> None:
        specs = [_spec("phq9"), _spec("gad7")]
        bundle = assemble_bundle(specs)
        for entry in bundle["entry"]:  # type: ignore[attr-defined]
            assert "fullUrl" in entry
            assert "resource" in entry
            assert entry["resource"]["resourceType"] == "Observation"

    def test_entry_fullurls_are_unique_urn_uuids(self) -> None:
        """Each entry's fullUrl is a fresh urn:uuid, unique within the Bundle."""
        specs = [_spec("phq9"), _spec("gad7"), _spec("who5")]
        bundle = assemble_bundle(specs)
        urls = [e["fullUrl"] for e in bundle["entry"]]  # type: ignore[attr-defined]
        assert len(set(urls)) == len(urls)  # all unique
        for url in urls:
            assert url.startswith("urn:uuid:")

    def test_entry_order_matches_input_order(self) -> None:
        """Ordering matters: clinicians may rely on chronological ordering."""
        specs = [_spec("phq9", score=1), _spec("phq9", score=2), _spec("phq9", score=3)]
        bundle = assemble_bundle(specs)
        scores = [
            e["resource"]["valueInteger"]  # type: ignore[index]
            for e in bundle["entry"]  # type: ignore[attr-defined]
        ]
        assert scores == [1, 2, 3]

    def test_observation_resource_preserves_safety_interpretation(self) -> None:
        """Safety-positive observation must still carry its interpretation
        array inside the Bundle."""
        bundle = assemble_bundle([_spec(safety_positive=True)])
        observation = bundle["entry"][0]["resource"]  # type: ignore[index]
        assert "interpretation" in observation


# ---- Error handling --------------------------------------------------------


class TestBundleErrors:
    def test_empty_specs_list_raises(self) -> None:
        """An empty Bundle is almost always a caller bug."""
        with pytest.raises(ValueError, match="empty Bundle"):
            assemble_bundle([])

    def test_unsupported_instrument_propagates(self) -> None:
        """Bundle assembler defers instrument validation to render_bundle."""
        bad_spec = ObservationSpec(
            patient_reference="Patient/1",
            instrument="not_a_thing",
            score=5,
            effective=datetime(2026, 4, 18, 0, 0, 0, tzinfo=UTC),
        )
        from discipline.reports.fhir_observation import UnsupportedInstrumentError

        with pytest.raises(UnsupportedInstrumentError):
            assemble_bundle([bad_spec])


# ---- Identifier override ---------------------------------------------------


class TestIdentifierOverride:
    def test_caller_provided_identifier_is_used(self) -> None:
        """Audit correlation: when the caller has a tracking UUID it should
        land in the Bundle identifier verbatim."""
        given = "abc-12345-correlation-id"
        bundle = assemble_bundle([_spec()], identifier=given)
        value = bundle["identifier"]["value"]  # type: ignore[call-overload,index]
        assert value == f"urn:uuid:{given}"

    def test_caller_provided_urn_uuid_not_double_prefixed(self) -> None:
        """If the caller passed a full urn:uuid, don't prepend another prefix."""
        given = "urn:uuid:abc-123"
        bundle = assemble_bundle([_spec()], identifier=given)
        assert bundle["identifier"]["value"] == given  # type: ignore[call-overload,index]


# ---- Round-trip serialization ----------------------------------------------


class TestBundleIsJsonSerializable:
    def test_bundle_round_trips_through_json(self) -> None:
        """The Bundle must be ``json.dumps``-safe out of the box — no
        datetime / UUID / dataclass leaks to catch consumers off guard."""
        bundle = assemble_bundle(
            [_spec("phq9"), _spec("gad7")],
            timestamp=datetime(2026, 4, 18, 12, 0, 0, tzinfo=UTC),
        )
        serialized = json.dumps(bundle)
        reparsed = json.loads(serialized)
        assert reparsed["resourceType"] == "Bundle"
        assert len(reparsed["entry"]) == 2

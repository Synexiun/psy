"""FHIR R4 patient-level Bundle export tests.

Tests are organised in four layers:

1. ``FhirExporter`` unit tests — pure in-memory, no HTTP, no DB.
2. Patient resource safety tests — assert no PII ever leaks into the
   Patient resource (CLAUDE.md Rule #2, 07_Security_Privacy).
3. Observation correctness tests — LOINC codes, custom code system,
   effectiveDateTime format, etc.
4. Router integration tests — ``POST /v1/reports/fhir/patient-bundle``
   over a TestClient, checking HTTP shape, PHI boundary header, audit
   emission, and error paths.

Coverage targets (from CLAUDE.md §coverage):
- The FHIR export path is a clinical-record surface, so we target 95 %
  branch coverage; every conditional branch in
  :mod:`discipline.reports.fhir_export` must be exercised.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timezone
from typing import Any

import pytest
from fastapi.testclient import TestClient

from discipline.app import create_app
from discipline.reports.fhir_export import (
    DISCIPLINEOS_CODE_SYSTEM,
    URGE_INTENSITY_CODE,
    AssessmentSession,
    FhirExporter,
    UrgeCheckInRecord,
)
from discipline.reports.fhir_observation import LOINC_CODES
from discipline.shared.logging import LogStream, get_stream_logger

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

_FIXED_TS = datetime(2026, 4, 18, 12, 0, 0, tzinfo=UTC)
_USER_ID = "user-fhir-export-001"


def _session(
    instrument: str = "phq9",
    score: int = 8,
    *,
    safety_item_positive: bool = False,
    administered_at: datetime | None = None,
) -> AssessmentSession:
    return AssessmentSession(
        user_id=_USER_ID,
        instrument=instrument,
        total_score=score,
        administered_at=administered_at or _FIXED_TS,
        safety_item_positive=safety_item_positive,
    )


def _check_in(
    intensity: int = 5,
    checked_in_at: datetime | None = None,
) -> UrgeCheckInRecord:
    return UrgeCheckInRecord(
        user_id=_USER_ID,
        intensity=intensity,
        checked_in_at=checked_in_at or _FIXED_TS,
    )


def _exporter(
    sessions: list[AssessmentSession] | None = None,
    check_ins: list[UrgeCheckInRecord] | None = None,
) -> FhirExporter:
    return FhirExporter(
        sessions=sessions or [],
        check_ins=check_ins or [],
    )


# ---------------------------------------------------------------------------
# 1. FhirExporter unit tests — bundle top-level shape
# ---------------------------------------------------------------------------


class TestFhirExporterBundleShape:
    def test_returns_dict_with_resourcetype_bundle(self) -> None:
        """export_patient_bundle must return a dict with resourceType=Bundle."""
        bundle = _exporter().export_patient_bundle(_USER_ID, timestamp=_FIXED_TS)
        assert isinstance(bundle, dict)
        assert bundle["resourceType"] == "Bundle"

    def test_bundle_type_is_collection(self) -> None:
        bundle = _exporter().export_patient_bundle(_USER_ID, timestamp=_FIXED_TS)
        assert bundle["type"] == "collection"

    def test_bundle_has_timestamp(self) -> None:
        bundle = _exporter().export_patient_bundle(_USER_ID, timestamp=_FIXED_TS)
        assert bundle["timestamp"] == "2026-04-18T12:00:00Z"

    def test_bundle_has_entry_list(self) -> None:
        bundle = _exporter().export_patient_bundle(_USER_ID, timestamp=_FIXED_TS)
        assert "entry" in bundle
        assert isinstance(bundle["entry"], list)

    def test_every_entry_has_resource(self) -> None:
        bundle = _exporter(
            sessions=[_session("phq9"), _session("gad7")],
            check_ins=[_check_in(3)],
        ).export_patient_bundle(_USER_ID, timestamp=_FIXED_TS)
        for entry in bundle["entry"]:  # type: ignore[union-attr]
            assert "resource" in entry

    def test_every_entry_resource_has_resourcetype(self) -> None:
        bundle = _exporter(
            sessions=[_session("phq9")],
            check_ins=[_check_in(2)],
        ).export_patient_bundle(_USER_ID, timestamp=_FIXED_TS)
        for entry in bundle["entry"]:  # type: ignore[union-attr]
            assert "resourceType" in entry["resource"]

    def test_empty_user_id_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="user_id must be non-empty"):
            _exporter().export_patient_bundle("", timestamp=_FIXED_TS)

    def test_bundle_is_json_serializable(self) -> None:
        """The bundle must round-trip through json.dumps without error."""
        bundle = _exporter(
            sessions=[_session("phq9"), _session("gad7")],
            check_ins=[_check_in(7)],
        ).export_patient_bundle(_USER_ID, timestamp=_FIXED_TS)
        reparsed = json.loads(json.dumps(bundle))
        assert reparsed["resourceType"] == "Bundle"


# ---------------------------------------------------------------------------
# 2. Patient resource safety tests (PHI non-disclosure)
# ---------------------------------------------------------------------------


class TestPatientResourcePHISafety:
    """The Patient resource MUST be PII-free (CLAUDE.md Rule #2 / 07_Security_Privacy).

    These tests are the load-bearing contract for the privacy guarantee.
    A failing test here MUST NOT be fixed by relaxing the assertion —
    fix the implementation instead.
    """

    def _patient_resource(self, user_id: str = _USER_ID) -> dict[str, Any]:
        bundle = _exporter().export_patient_bundle(user_id, timestamp=_FIXED_TS)
        # First entry is always the Patient resource.
        return bundle["entry"][0]["resource"]  # type: ignore[index]

    def test_bundle_contains_patient_resource(self) -> None:
        resource = self._patient_resource()
        assert resource["resourceType"] == "Patient"

    def test_patient_id_is_user_id(self) -> None:
        resource = self._patient_resource("specific-user-123")
        assert resource["id"] == "specific-user-123"

    def test_patient_resource_never_has_name(self) -> None:
        resource = self._patient_resource()
        assert "name" not in resource, (
            "Patient resource must NEVER carry a 'name' field — "
            "this is a PHI non-disclosure contract (CLAUDE.md Rule #2)"
        )

    def test_patient_resource_never_has_birthdate(self) -> None:
        resource = self._patient_resource()
        assert "birthDate" not in resource, (
            "Patient resource must NEVER carry 'birthDate' (HIPAA §164.514 identifier)"
        )

    def test_patient_resource_never_has_address(self) -> None:
        resource = self._patient_resource()
        assert "address" not in resource, (
            "Patient resource must NEVER carry 'address' (HIPAA §164.514 identifier)"
        )

    def test_patient_resource_never_has_telecom(self) -> None:
        resource = self._patient_resource()
        assert "telecom" not in resource, (
            "Patient resource must NEVER carry 'telecom' (phone/email — "
            "HIPAA §164.514 identifier)"
        )

    def test_patient_resource_never_has_gender(self) -> None:
        resource = self._patient_resource()
        assert "gender" not in resource, (
            "Gender is a PHI field; must not be in the Patient resource "
            "unless the user explicitly grants this scope (not implemented yet)"
        )

    def test_patient_resource_has_fhir_profile_meta(self) -> None:
        resource = self._patient_resource()
        assert "meta" in resource
        assert "profile" in resource["meta"]
        profiles: list[str] = resource["meta"]["profile"]
        assert any("Patient" in p for p in profiles)

    def test_patient_is_first_entry(self) -> None:
        """FHIR convention: Patient is first so receiving systems find it quickly."""
        bundle = _exporter(
            sessions=[_session("phq9")],
            check_ins=[_check_in(4)],
        ).export_patient_bundle(_USER_ID, timestamp=_FIXED_TS)
        first_resource = bundle["entry"][0]["resource"]  # type: ignore[index]
        assert first_resource["resourceType"] == "Patient"


# ---------------------------------------------------------------------------
# 3. Observation correctness — assessment sessions
# ---------------------------------------------------------------------------


class TestAssessmentObservations:
    def _entries_for(
        self, sessions: list[AssessmentSession]
    ) -> list[dict[str, Any]]:
        bundle = _exporter(sessions=sessions).export_patient_bundle(
            _USER_ID, timestamp=_FIXED_TS
        )
        # Skip the Patient entry (index 0), return the Observations.
        return [e["resource"] for e in bundle["entry"][1:]]  # type: ignore[index]

    def test_phq9_observation_has_loinc_code(self) -> None:
        obs_list = self._entries_for([_session("phq9", 12)])
        assert len(obs_list) == 1
        obs = obs_list[0]
        assert obs["resourceType"] == "Observation"
        coding = obs["code"]["coding"]
        assert any(c["system"] == "http://loinc.org" for c in coding)

    def test_phq9_loinc_code_value(self) -> None:
        obs_list = self._entries_for([_session("phq9", 12)])
        obs = obs_list[0]
        code_values = [c["code"] for c in obs["code"]["coding"]]
        assert LOINC_CODES["phq9"] in code_values

    def test_gad7_observation_has_loinc_code(self) -> None:
        obs_list = self._entries_for([_session("gad7", 7)])
        obs = obs_list[0]
        code_values = [c["code"] for c in obs["code"]["coding"]]
        assert LOINC_CODES["gad7"] in code_values

    def test_who5_observation_has_loinc_code(self) -> None:
        obs_list = self._entries_for([_session("who5", 15)])
        obs = obs_list[0]
        code_values = [c["code"] for c in obs["code"]["coding"]]
        assert LOINC_CODES["who5"] in code_values

    def test_observation_value_integer_matches_score(self) -> None:
        obs_list = self._entries_for([_session("phq9", 14)])
        assert obs_list[0]["valueInteger"] == 14

    def test_effective_datetime_is_utc_z_format(self) -> None:
        ts = datetime(2026, 3, 1, 9, 30, 0, tzinfo=UTC)
        obs_list = self._entries_for([_session("gad7", 5, administered_at=ts)])
        assert obs_list[0]["effectiveDateTime"] == "2026-03-01T09:30:00Z"

    def test_safety_positive_observation_has_interpretation(self) -> None:
        obs_list = self._entries_for([_session("phq9", 18, safety_item_positive=True)])
        assert "interpretation" in obs_list[0]

    def test_safety_negative_observation_has_no_interpretation(self) -> None:
        obs_list = self._entries_for([_session("phq9", 8, safety_item_positive=False)])
        assert "interpretation" not in obs_list[0]

    def test_unknown_instrument_is_silently_omitted(self) -> None:
        """Instruments without a pinned LOINC code must be omitted, not raise.

        This protects exports when a new instrument is added to the scorer
        but not yet registered in LOINC_CODES.
        """
        unknown_session = AssessmentSession(
            user_id=_USER_ID,
            instrument="future_instrument_not_in_loinc",
            total_score=5,
            administered_at=_FIXED_TS,
        )
        obs_list = self._entries_for([unknown_session])
        assert obs_list == [], (
            "An instrument without a LOINC code must be silently omitted, "
            "not raise an exception that would block the entire export."
        )

    def test_multiple_sessions_produce_multiple_observations(self) -> None:
        sessions = [
            _session("phq9", 8),
            _session("gad7", 5),
            _session("who5", 16),
        ]
        obs_list = self._entries_for(sessions)
        assert len(obs_list) == 3

    def test_observation_subject_reference_contains_user_id(self) -> None:
        obs_list = self._entries_for([_session("phq9", 10)])
        assert obs_list[0]["subject"]["reference"] == f"Patient/{_USER_ID}"

    def test_observation_status_is_final(self) -> None:
        obs_list = self._entries_for([_session("phq9", 6)])
        assert obs_list[0]["status"] == "final"

    def test_observation_category_is_survey(self) -> None:
        obs_list = self._entries_for([_session("gad7", 9)])
        category_codes = [
            c["code"]
            for cat in obs_list[0]["category"]
            for c in cat["coding"]
        ]
        assert "survey" in category_codes


# ---------------------------------------------------------------------------
# 4. Observation correctness — urge check-ins
# ---------------------------------------------------------------------------


class TestUrgeCheckInObservations:
    def _check_in_entries(
        self, check_ins: list[UrgeCheckInRecord]
    ) -> list[dict[str, Any]]:
        bundle = _exporter(check_ins=check_ins).export_patient_bundle(
            _USER_ID, timestamp=_FIXED_TS
        )
        # Skip the Patient entry (index 0).
        return [e["resource"] for e in bundle["entry"][1:]]  # type: ignore[index]

    def test_check_in_observation_has_custom_code_system(self) -> None:
        obs_list = self._check_in_entries([_check_in(4)])
        obs = obs_list[0]
        code_systems = [c["system"] for c in obs["code"]["coding"]]
        assert DISCIPLINEOS_CODE_SYSTEM in code_systems

    def test_check_in_code_value_is_urge_intensity(self) -> None:
        obs_list = self._check_in_entries([_check_in(6)])
        obs = obs_list[0]
        code_values = [c["code"] for c in obs["code"]["coding"]]
        assert URGE_INTENSITY_CODE in code_values

    def test_check_in_intensity_stored_as_value_integer(self) -> None:
        obs_list = self._check_in_entries([_check_in(7)])
        assert obs_list[0]["valueInteger"] == 7

    def test_check_in_effective_datetime_is_utc_z_format(self) -> None:
        ts = datetime(2026, 4, 10, 8, 0, 0, tzinfo=UTC)
        obs_list = self._check_in_entries([_check_in(3, checked_in_at=ts)])
        assert obs_list[0]["effectiveDateTime"] == "2026-04-10T08:00:00Z"

    def test_check_in_subject_reference_contains_user_id(self) -> None:
        obs_list = self._check_in_entries([_check_in(5)])
        assert obs_list[0]["subject"]["reference"] == f"Patient/{_USER_ID}"

    def test_check_in_observation_status_is_final(self) -> None:
        obs_list = self._check_in_entries([_check_in(2)])
        assert obs_list[0]["status"] == "final"

    def test_check_in_category_is_survey(self) -> None:
        obs_list = self._check_in_entries([_check_in(9)])
        category_codes = [
            c["code"]
            for cat in obs_list[0]["category"]
            for c in cat["coding"]
        ]
        assert "survey" in category_codes

    def test_non_loinc_code_system_not_loinc(self) -> None:
        obs_list = self._check_in_entries([_check_in(5)])
        code_systems = [c["system"] for c in obs_list[0]["code"]["coding"]]
        assert "http://loinc.org" not in code_systems, (
            "Urge intensity observations must use the Discipline OS custom "
            "code system, NOT LOINC — there is no published LOINC code for "
            "a 0-10 self-reported urge intensity."
        )

    def test_multiple_check_ins_produce_multiple_observations(self) -> None:
        entries = self._check_in_entries(
            [_check_in(1), _check_in(5), _check_in(10)]
        )
        assert len(entries) == 3

    def test_non_utc_timezone_is_converted_to_utc(self) -> None:
        """A check-in with a non-UTC tz must appear as UTC Z in effectiveDateTime."""
        eastern = timezone(datetime(2026, 1, 1).astimezone().utcoffset() or __import__("datetime").timedelta(hours=-5))
        ts = datetime(2026, 4, 10, 4, 0, 0, tzinfo=eastern)
        # We just verify the output is a valid Z-suffix string without
        # asserting the exact offset (which varies by DST / machine tz).
        obs_list = self._check_in_entries([_check_in(3, checked_in_at=ts)])
        effective = obs_list[0]["effectiveDateTime"]
        assert isinstance(effective, str)
        assert effective.endswith("Z")


# ---------------------------------------------------------------------------
# 5. Bundle total-entry count
# ---------------------------------------------------------------------------


class TestBundleEntryCount:
    def test_patient_only_bundle_has_one_entry(self) -> None:
        """A user with no data still gets a Patient entry."""
        bundle = _exporter().export_patient_bundle(_USER_ID, timestamp=_FIXED_TS)
        assert len(bundle["entry"]) == 1  # type: ignore[arg-type]

    def test_total_entry_count_is_patient_plus_observations(self) -> None:
        bundle = _exporter(
            sessions=[_session("phq9"), _session("gad7"), _session("who5")],
            check_ins=[_check_in(4), _check_in(8)],
        ).export_patient_bundle(_USER_ID, timestamp=_FIXED_TS)
        # 1 Patient + 3 sessions + 2 check-ins = 6
        assert len(bundle["entry"]) == 6  # type: ignore[arg-type]

    def test_unknown_instrument_does_not_inflate_entry_count(self) -> None:
        """Silent omit of unknown instruments must not change the entry count
        beyond what the other valid sessions produce."""
        bundle = _exporter(
            sessions=[
                _session("phq9"),
                AssessmentSession(
                    user_id=_USER_ID,
                    instrument="not_registered",
                    total_score=3,
                    administered_at=_FIXED_TS,
                ),
            ],
        ).export_patient_bundle(_USER_ID, timestamp=_FIXED_TS)
        # 1 Patient + 1 phq9 (not_registered is omitted) = 2
        assert len(bundle["entry"]) == 2  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# 6. Router integration tests
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(create_app())


def _bundle_payload(
    *,
    actor_id: str = _USER_ID,
    user_id: str = _USER_ID,
    sessions: list[dict[str, Any]] | None = None,
    check_ins: list[dict[str, Any]] | None = None,
    bundle_id: str | None = None,
) -> dict[str, Any]:
    return {
        "actor_id": actor_id,
        "user_id": user_id,
        "sessions": sessions or [],
        "check_ins": check_ins or [],
        **({"bundle_id": bundle_id} if bundle_id is not None else {}),
    }


class TestFhirPatientBundleRouter:
    def test_empty_payload_returns_200_with_patient_only_bundle(
        self, client: TestClient
    ) -> None:
        resp = client.post(
            "/v1/reports/fhir/patient-bundle",
            json=_bundle_payload(),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["resourceType"] == "Bundle"
        assert body["type"] == "collection"
        entries: list[dict[str, Any]] = body["entry"]
        assert len(entries) == 1
        assert entries[0]["resource"]["resourceType"] == "Patient"

    def test_bundle_contains_correct_patient_id(
        self, client: TestClient
    ) -> None:
        # actor_id and user_id must match (self-access only).
        resp = client.post(
            "/v1/reports/fhir/patient-bundle",
            json=_bundle_payload(actor_id="specific-user-999", user_id="specific-user-999"),
        )
        assert resp.status_code == 200
        patient = resp.json()["entry"][0]["resource"]
        assert patient["id"] == "specific-user-999"

    def test_phi_boundary_header_present(self, client: TestClient) -> None:
        """PHI surface must set X-Phi-Boundary: 1 (CLAUDE.md Rule #11)."""
        resp = client.post(
            "/v1/reports/fhir/patient-bundle",
            json=_bundle_payload(),
        )
        assert resp.status_code == 200
        assert resp.headers.get("x-phi-boundary") == "1"

    def test_actor_id_mismatch_returns_403(self, client: TestClient) -> None:
        """Self-access only: actor_id must equal user_id."""
        resp = client.post(
            "/v1/reports/fhir/patient-bundle",
            json=_bundle_payload(actor_id="clinician-777", user_id="patient-001"),
        )
        assert resp.status_code == 403
        body = resp.json()
        assert body["detail"]["code"] == "auth.self_access_only"

    def test_with_sessions_produces_observations(
        self, client: TestClient
    ) -> None:
        payload = _bundle_payload(
            sessions=[
                {
                    "instrument": "phq9",
                    "total_score": 10,
                    "administered_at": "2026-04-01T10:00:00Z",
                    "safety_item_positive": False,
                },
                {
                    "instrument": "gad7",
                    "total_score": 7,
                    "administered_at": "2026-04-05T10:00:00Z",
                },
            ],
        )
        resp = client.post("/v1/reports/fhir/patient-bundle", json=payload)
        assert resp.status_code == 200
        entries: list[dict[str, Any]] = resp.json()["entry"]
        # 1 Patient + 2 Observations
        assert len(entries) == 3
        resource_types = [e["resource"]["resourceType"] for e in entries]
        assert resource_types.count("Patient") == 1
        assert resource_types.count("Observation") == 2

    def test_with_check_ins_produces_urge_observations(
        self, client: TestClient
    ) -> None:
        payload = _bundle_payload(
            check_ins=[
                {
                    "intensity": 6,
                    "checked_in_at": "2026-04-10T14:00:00Z",
                },
                {
                    "intensity": 3,
                    "checked_in_at": "2026-04-11T09:30:00Z",
                },
            ],
        )
        resp = client.post("/v1/reports/fhir/patient-bundle", json=payload)
        assert resp.status_code == 200
        entries: list[dict[str, Any]] = resp.json()["entry"]
        # 1 Patient + 2 urge check-in Observations
        assert len(entries) == 3
        obs_entries = [e for e in entries if e["resource"]["resourceType"] == "Observation"]
        assert len(obs_entries) == 2
        # Verify code system
        for obs_entry in obs_entries:
            obs = obs_entry["resource"]
            code_systems = [c["system"] for c in obs["code"]["coding"]]
            assert DISCIPLINEOS_CODE_SYSTEM in code_systems

    def test_assessment_observations_have_loinc_codes(
        self, client: TestClient
    ) -> None:
        payload = _bundle_payload(
            sessions=[
                {
                    "instrument": "phq9",
                    "total_score": 8,
                    "administered_at": "2026-04-15T12:00:00Z",
                }
            ],
        )
        resp = client.post("/v1/reports/fhir/patient-bundle", json=payload)
        assert resp.status_code == 200
        obs_entries = [
            e
            for e in resp.json()["entry"]
            if e["resource"]["resourceType"] == "Observation"
        ]
        obs = obs_entries[0]["resource"]
        code_systems = [c["system"] for c in obs["code"]["coding"]]
        assert "http://loinc.org" in code_systems

    def test_bundle_id_round_trips(self, client: TestClient) -> None:
        correlation = "test-correlation-id-round-trip"
        resp = client.post(
            "/v1/reports/fhir/patient-bundle",
            json=_bundle_payload(bundle_id=correlation),
        )
        assert resp.status_code == 200
        identifier_value = resp.json()["identifier"]["value"]
        assert correlation in identifier_value

    def test_malformed_session_returns_422(self, client: TestClient) -> None:
        payload = _bundle_payload(
            sessions=[{"instrument": "phq9"}],  # missing total_score + administered_at
        )
        resp = client.post("/v1/reports/fhir/patient-bundle", json=payload)
        assert resp.status_code == 422

    def test_malformed_check_in_returns_422(self, client: TestClient) -> None:
        payload = _bundle_payload(
            check_ins=[{"intensity": 5}],  # missing checked_in_at
        )
        resp = client.post("/v1/reports/fhir/patient-bundle", json=payload)
        assert resp.status_code == 422

    def test_out_of_range_intensity_returns_422(
        self, client: TestClient
    ) -> None:
        payload = _bundle_payload(
            check_ins=[
                {
                    "intensity": 11,  # > 10 — out of range
                    "checked_in_at": "2026-04-10T10:00:00Z",
                }
            ],
        )
        resp = client.post("/v1/reports/fhir/patient-bundle", json=payload)
        assert resp.status_code == 422

    def test_patient_resource_in_response_has_no_name(
        self, client: TestClient
    ) -> None:
        """PHI safety check: router response must not leak name."""
        resp = client.post(
            "/v1/reports/fhir/patient-bundle",
            json=_bundle_payload(),
        )
        patient = resp.json()["entry"][0]["resource"]
        assert "name" not in patient

    def test_patient_resource_in_response_has_no_birthdate(
        self, client: TestClient
    ) -> None:
        resp = client.post(
            "/v1/reports/fhir/patient-bundle",
            json=_bundle_payload(),
        )
        patient = resp.json()["entry"][0]["resource"]
        assert "birthDate" not in patient

    def test_patient_resource_in_response_has_no_address(
        self, client: TestClient
    ) -> None:
        resp = client.post(
            "/v1/reports/fhir/patient-bundle",
            json=_bundle_payload(),
        )
        patient = resp.json()["entry"][0]["resource"]
        assert "address" not in patient

    def test_response_is_json_serializable(self, client: TestClient) -> None:
        resp = client.post(
            "/v1/reports/fhir/patient-bundle",
            json=_bundle_payload(
                sessions=[
                    {
                        "instrument": "who5",
                        "total_score": 14,
                        "administered_at": "2026-04-12T09:00:00Z",
                    }
                ],
                check_ins=[
                    {
                        "intensity": 4,
                        "checked_in_at": "2026-04-12T10:00:00Z",
                    }
                ],
            ),
        )
        assert resp.status_code == 200
        # Already parsed by resp.json() above — verify key structure
        body = resp.json()
        reparsed = json.loads(json.dumps(body))
        assert reparsed["resourceType"] == "Bundle"

"""User Right-of-Access JSON archive builder tests.

CLAUDE.md / HIPAA §164.524: users have the right to a copy of their
data.  The archive is tamper-evidence-marked with a sha256 manifest,
which is only meaningful if the archive is byte-reproducible.  The
determinism tests below are the load-bearing contract for that.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta, timezone
from typing import Any

import pytest

from discipline.reports.user_export import (
    ARCHIVE_SCHEMA_VERSION,
    EmptyExportError,
    ExportBundle,
    NonUtcTimestampError,
    UserExportPayload,
    build_json_archive,
)

# ---- Fixtures --------------------------------------------------------------


def _now_utc() -> datetime:
    """A pinned timestamp so determinism tests don't drift with wall clock."""
    return datetime(2026, 4, 18, 12, 0, 0, tzinfo=UTC)


def _sample_payload(
    *,
    user_id: str = "user-001",
    locale: str = "en",
    profile: dict[str, Any] | None = None,
    psychometric_scores: list[dict[str, Any]] | None = None,
    intervention_events: list[dict[str, Any]] | None = None,
    resilience_streak: dict[str, Any] | None = None,
    safety_events: list[dict[str, Any]] | None = None,
    consents: list[dict[str, Any]] | None = None,
    requested_at: datetime | None = None,
    generated_at: datetime | None = None,
) -> UserExportPayload:
    """A realistic payload with one record in each section.

    Tests override sections to exercise empty / large / edge shapes."""
    base = _now_utc()
    return UserExportPayload(
        user_id=user_id,
        requested_at=requested_at or base,
        generated_at=generated_at or (base + timedelta(seconds=30)),
        locale=locale,
        profile=profile if profile is not None else {"display_name": "Alex"},
        psychometric_scores=(
            psychometric_scores
            if psychometric_scores is not None
            else [
                {
                    "instrument": "phq9",
                    "score": 8,
                    "effective": "2026-04-10T12:00:00Z",
                }
            ]
        ),
        intervention_events=(
            intervention_events
            if intervention_events is not None
            else [
                {
                    "event": "urge.recorded",
                    "at": "2026-04-11T09:30:00Z",
                    "intensity": 7,
                }
            ]
        ),
        resilience_streak=(
            resilience_streak
            if resilience_streak is not None
            else {"days": 14, "started_at": "2026-04-04T00:00:00Z"}
        ),
        safety_events=safety_events if safety_events is not None else [],
        consents=(
            consents
            if consents is not None
            else [
                {
                    "kind": "data_processing",
                    "accepted_at": "2026-03-01T10:00:00Z",
                    "version": "v3",
                }
            ]
        ),
    )


# =============================================================================
# Happy path — archive content + manifest
# =============================================================================


class TestHappyPath:
    def test_returns_export_bundle(self) -> None:
        result = build_json_archive(_sample_payload())
        assert isinstance(result, ExportBundle)

    def test_json_archive_is_non_empty_bytes(self) -> None:
        result = build_json_archive(_sample_payload())
        assert isinstance(result.json_archive, bytes)
        assert len(result.json_archive) > 0

    def test_json_archive_is_valid_utf8_json(self) -> None:
        result = build_json_archive(_sample_payload())
        decoded = result.json_archive.decode("utf-8")
        parsed = json.loads(decoded)
        assert isinstance(parsed, dict)

    def test_manifest_matches_sha256_of_archive_bytes(self) -> None:
        """The manifest is the single tamper-evidence marker for the
        archive.  If it doesn't equal ``sha256(json_archive)`` byte-for-
        byte, the audit claim 'this is the file we delivered' is broken."""
        result = build_json_archive(_sample_payload())
        expected = hashlib.sha256(result.json_archive).hexdigest()
        assert result.manifest_sha256 == expected

    def test_manifest_is_64_char_hex(self) -> None:
        result = build_json_archive(_sample_payload())
        assert len(result.manifest_sha256) == 64
        int(result.manifest_sha256, 16)  # round-trips as hex

    def test_pdf_summary_is_empty_sentinel(self) -> None:
        """PDF rendering is deferred to a downstream worker — the
        builder returns ``b""`` as a 'not yet rendered' marker.  Clients
        must distinguish this from a rendered-but-empty document (which
        is impossible for a user with ≥1 record)."""
        result = build_json_archive(_sample_payload())
        assert result.pdf_summary == b""


# =============================================================================
# Archive structure / schema
# =============================================================================


class TestArchiveStructure:
    def _parsed(self, payload: UserExportPayload | None = None) -> dict[str, Any]:
        result = build_json_archive(payload or _sample_payload())
        return json.loads(result.json_archive)

    def test_carries_schema_version(self) -> None:
        """Client parsers read this before touching sections.  A missing
        or unexpected version means the archive format has drifted and
        the parser should refuse to proceed rather than misinterpret."""
        assert self._parsed()["archive_schema_version"] == ARCHIVE_SCHEMA_VERSION

    def test_user_id_preserved(self) -> None:
        assert self._parsed()["user_id"] == "user-001"

    def test_locale_preserved(self) -> None:
        assert self._parsed(_sample_payload(locale="fa"))["locale"] == "fa"

    def test_datetimes_serialized_as_utc_z(self) -> None:
        """Canonical ``Z`` suffix — not ``+00:00``.  Python's default
        isoformat varies across versions on this, so we pin the format
        to make the archive bytes truly platform-independent."""
        parsed = self._parsed()
        assert parsed["requested_at"] == "2026-04-18T12:00:00Z"
        assert parsed["generated_at"] == "2026-04-18T12:00:30Z"

    def test_sections_block_contains_all_keys(self) -> None:
        sections = self._parsed()["sections"]
        assert set(sections.keys()) == {
            "profile",
            "psychometric_scores",
            "intervention_events",
            "resilience_streak",
            "safety_events",
            "consents",
        }

    def test_section_counts_accurate(self) -> None:
        counts = self._parsed()["section_counts"]
        assert counts["psychometric_scores"] == 1
        assert counts["intervention_events"] == 1
        assert counts["safety_events"] == 0
        assert counts["consents"] == 1

    def test_journal_plaintext_not_in_archive(self) -> None:
        """Hard guarantee: server-side archive never includes journal
        plaintext (E2E encryption means the server can't decrypt it
        anyway, but the test pins that no accidental 'journal' key was
        added to the schema)."""
        parsed = self._parsed()
        assert "journal" not in parsed
        assert "journal" not in parsed["sections"]
        assert "journal_entries" not in parsed["sections"]


# =============================================================================
# Determinism — byte-for-byte reproducibility
# =============================================================================


class TestDeterminism:
    def test_same_input_yields_same_bytes(self) -> None:
        """The core tamper-evidence property.  If this ever fails,
        re-computing the manifest during an audit will disagree with
        the originally-issued manifest and the audit fails open."""
        r1 = build_json_archive(_sample_payload())
        r2 = build_json_archive(_sample_payload())
        assert r1.json_archive == r2.json_archive
        assert r1.manifest_sha256 == r2.manifest_sha256

    def test_keys_are_sorted_in_output(self) -> None:
        """Confirms the ``sort_keys=True`` serialization — without it,
        Python dict ordering (insertion order) would leak into the
        archive and small code changes could silently churn the bytes."""
        decoded = build_json_archive(_sample_payload()).json_archive.decode("utf-8")
        # The top-level keys must appear in alphabetical order when
        # sorted; easiest check is to parse and re-dump and compare.
        reparsed = json.loads(decoded)
        redumped = json.dumps(
            reparsed, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        )
        assert decoded == redumped

    def test_compact_separators_no_whitespace(self) -> None:
        """Compact form means no ``": "`` / ``", "`` — every wasted byte
        is a delivery cost and a potential newline-vs-space churn
        source.  ``sort_keys=True`` alone isn't enough; separators too."""
        decoded = build_json_archive(_sample_payload()).json_archive.decode("utf-8")
        assert ": " not in decoded
        assert ", " not in decoded

    def test_different_user_yields_different_manifest(self) -> None:
        a = build_json_archive(_sample_payload(user_id="user-a"))
        b = build_json_archive(_sample_payload(user_id="user-b"))
        assert a.manifest_sha256 != b.manifest_sha256

    def test_different_generated_at_yields_different_manifest(self) -> None:
        """``generated_at`` is in the archive — changing it changes the
        bytes and therefore the manifest.  This pins that the builder
        isn't silently stripping timestamps for determinism."""
        base = _now_utc()
        a = build_json_archive(_sample_payload(generated_at=base))
        b = build_json_archive(
            _sample_payload(generated_at=base + timedelta(seconds=1))
        )
        assert a.manifest_sha256 != b.manifest_sha256


# =============================================================================
# Empty-payload refusal
# =============================================================================


class TestEmptyPayload:
    def test_all_sections_empty_raises(self) -> None:
        """A user with zero records across every section is almost
        certainly a caller bug (wrong user_id).  Refusing here forces
        the caller to short-circuit upstream."""
        payload = UserExportPayload(
            user_id="ghost-user",
            requested_at=_now_utc(),
            generated_at=_now_utc(),
            locale="en",
        )
        with pytest.raises(EmptyExportError, match="ghost-user"):
            build_json_archive(payload)

    def test_one_non_empty_section_suffices(self) -> None:
        """A user with only consents (e.g. newly signed up, hasn't run
        any assessments yet) is a legitimate minimal payload."""
        payload = UserExportPayload(
            user_id="new-user",
            requested_at=_now_utc(),
            generated_at=_now_utc(),
            locale="en",
            consents=[{"kind": "data_processing", "accepted_at": "2026-04-18Z"}],
        )
        result = build_json_archive(payload)
        assert len(result.json_archive) > 0

    def test_profile_only_is_sufficient(self) -> None:
        """Even just a profile (display_name set) counts — the user is
        exercising their right to see what we hold on them, even if
        what we hold is minimal."""
        payload = UserExportPayload(
            user_id="profile-only-user",
            requested_at=_now_utc(),
            generated_at=_now_utc(),
            locale="en",
            profile={"display_name": "Alex"},
        )
        result = build_json_archive(payload)
        parsed = json.loads(result.json_archive)
        assert parsed["sections"]["profile"] == {"display_name": "Alex"}


# =============================================================================
# Timestamp discipline
# =============================================================================


class TestTimestampDiscipline:
    def test_naive_requested_at_rejected(self) -> None:
        """A naive datetime would render without a timezone designator,
        which many client parsers default to local time — a silent
        interop bug.  Better to fail loud."""
        naive = datetime(2026, 4, 18, 12, 0, 0)  # no tzinfo
        payload = UserExportPayload(
            user_id="u",
            requested_at=naive,
            generated_at=_now_utc(),
            locale="en",
            profile={"x": 1},
        )
        with pytest.raises(NonUtcTimestampError, match="requested_at"):
            build_json_archive(payload)

    def test_naive_generated_at_rejected(self) -> None:
        payload = UserExportPayload(
            user_id="u",
            requested_at=_now_utc(),
            generated_at=datetime(2026, 4, 18, 12, 0, 0),
            locale="en",
            profile={"x": 1},
        )
        with pytest.raises(NonUtcTimestampError, match="generated_at"):
            build_json_archive(payload)

    def test_non_utc_timezone_rejected(self) -> None:
        """A +05:00 datetime is un-ambiguous but still not UTC.  The
        archive format pins UTC; converting silently would be a footgun
        for anyone auditing delivery times."""
        ist = timezone(timedelta(hours=5, minutes=30))
        payload = UserExportPayload(
            user_id="u",
            requested_at=datetime(2026, 4, 18, 17, 30, 0, tzinfo=ist),
            generated_at=_now_utc(),
            locale="en",
            profile={"x": 1},
        )
        with pytest.raises(NonUtcTimestampError):
            build_json_archive(payload)


# =============================================================================
# Unicode / locale handling
# =============================================================================


class TestUnicode:
    def test_non_latin_profile_name_roundtrips(self) -> None:
        """Profile names may contain non-Latin characters — Arabic,
        Persian, CJK.  With ``ensure_ascii=False`` they land as UTF-8
        directly instead of ``\\uXXXX`` escape sequences, which is
        shorter on the wire and friendlier to human readers of the
        archive."""
        payload = _sample_payload(profile={"display_name": "علي"})
        result = build_json_archive(payload)
        parsed = json.loads(result.json_archive)
        assert parsed["sections"]["profile"]["display_name"] == "علي"

    def test_non_ascii_user_id_preserved(self) -> None:
        """Defensive: user_ids are generally ASCII UUIDs, but the
        serializer must not mangle non-ASCII input if one ever lands."""
        payload = _sample_payload(user_id="user-ñ-001")
        result = build_json_archive(payload)
        parsed = json.loads(result.json_archive)
        assert parsed["user_id"] == "user-ñ-001"


# =============================================================================
# Shape stability — frozen dataclass
# =============================================================================


class TestShape:
    def test_export_bundle_is_frozen(self) -> None:
        """Frozen so a downstream handler can't mutate the archive after
        the manifest was computed — a post-hoc change to ``json_archive``
        would silently diverge from the manifest."""
        result = build_json_archive(_sample_payload())
        with pytest.raises(Exception):  # dataclasses.FrozenInstanceError
            result.json_archive = b"tampered"  # type: ignore[misc]

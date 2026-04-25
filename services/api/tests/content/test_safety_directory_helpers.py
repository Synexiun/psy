"""Unit tests for _parse_meta() and _parse_directory() pure helpers in
discipline.content.safety_directory.

_parse_meta(raw_meta) → DirectoryMeta
  Parses the _meta block from the hotlines.json dict.
  Fields: schemaVersion (str), lastReviewedAt (ISO date str → date),
  reviewWindowDays (int), reviewedBy (str).

_parse_directory(raw) → tuple[CountryDirectory, ...]
  Parses the entries array from the raw hotlines.json dict.
  Each entry becomes a CountryDirectory with a tuple of Hotlines.
  Optional hotline fields (number, sms, web) default to None when absent.
"""

from __future__ import annotations

from datetime import date

import pytest

from discipline.content.safety_directory import (
    CountryDirectory,
    DirectoryMeta,
    Hotline,
    _parse_directory,
    _parse_meta,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _meta_raw(**overrides) -> dict:
    base = {
        "schemaVersion": "1.0",
        "lastReviewedAt": "2026-04-01",
        "reviewWindowDays": 90,
        "reviewedBy": "Safety Team",
    }
    base.update(overrides)
    return base


def _hotline_raw(**overrides) -> dict:
    base = {
        "id": "us-en-988",
        "name": "988 Suicide & Crisis Lifeline",
        "number": "988",
        "hours": "24/7",
        "cost": "free",
        "verifiedAt": "2026-03-01",
    }
    base.update(overrides)
    return base


def _entry_raw(**overrides) -> dict:
    base = {
        "country": "US",
        "locale": "en",
        "emergency": {"label": "Emergency", "number": "911"},
        "hotlines": [_hotline_raw()],
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# _parse_meta — field parsing
# ---------------------------------------------------------------------------


class TestParseMetaFields:
    def test_schema_version_parsed(self) -> None:
        result = _parse_meta(_meta_raw(schemaVersion="2.1"))
        assert result.schema_version == "2.1"

    def test_last_reviewed_at_parsed_as_date(self) -> None:
        result = _parse_meta(_meta_raw(lastReviewedAt="2026-04-01"))
        assert result.last_reviewed_at == date(2026, 4, 1)

    def test_review_window_days_parsed_as_int(self) -> None:
        result = _parse_meta(_meta_raw(reviewWindowDays=90))
        assert result.review_window_days == 90

    def test_reviewed_by_parsed(self) -> None:
        result = _parse_meta(_meta_raw(reviewedBy="Dr. Smith"))
        assert result.reviewed_by == "Dr. Smith"

    def test_result_is_directory_meta_instance(self) -> None:
        result = _parse_meta(_meta_raw())
        assert isinstance(result, DirectoryMeta)

    def test_last_reviewed_at_is_date_not_string(self) -> None:
        result = _parse_meta(_meta_raw())
        assert isinstance(result.last_reviewed_at, date)

    def test_review_window_days_string_coerced_to_int(self) -> None:
        # int("90") = 90 — the raw JSON might have numeric but we ensure int type
        result = _parse_meta(_meta_raw(reviewWindowDays="90"))
        assert result.review_window_days == 90


# ---------------------------------------------------------------------------
# _parse_directory — empty entries
# ---------------------------------------------------------------------------


class TestParseDirectoryEmpty:
    def test_empty_entries_returns_empty_tuple(self) -> None:
        result = _parse_directory({"entries": []})
        assert result == ()

    def test_missing_entries_key_returns_empty_tuple(self) -> None:
        result = _parse_directory({})
        assert result == ()

    def test_result_is_tuple_not_list(self) -> None:
        result = _parse_directory({"entries": []})
        assert isinstance(result, tuple)


# ---------------------------------------------------------------------------
# _parse_directory — single entry
# ---------------------------------------------------------------------------


class TestParseDirectorySingleEntry:
    def test_country_parsed(self) -> None:
        raw = {"entries": [_entry_raw(country="US")]}
        result = _parse_directory(raw)
        assert result[0].country == "US"

    def test_locale_parsed(self) -> None:
        raw = {"entries": [_entry_raw(locale="en")]}
        result = _parse_directory(raw)
        assert result[0].locale == "en"

    def test_emergency_label_parsed(self) -> None:
        raw = {"entries": [_entry_raw(emergency={"label": "Emergency", "number": "911"})]}
        result = _parse_directory(raw)
        assert result[0].emergency_label == "Emergency"

    def test_emergency_number_parsed(self) -> None:
        raw = {"entries": [_entry_raw()]}
        result = _parse_directory(raw)
        assert result[0].emergency_number == "911"

    def test_result_is_country_directory_instance(self) -> None:
        raw = {"entries": [_entry_raw()]}
        result = _parse_directory(raw)
        assert isinstance(result[0], CountryDirectory)

    def test_hotlines_is_tuple(self) -> None:
        raw = {"entries": [_entry_raw()]}
        result = _parse_directory(raw)
        assert isinstance(result[0].hotlines, tuple)


# ---------------------------------------------------------------------------
# _parse_directory — hotline field parsing
# ---------------------------------------------------------------------------


class TestParseDirectoryHotlineFields:
    def _single_hotline(self, **kwargs) -> Hotline:
        raw = {"entries": [_entry_raw(hotlines=[_hotline_raw(**kwargs)])]}
        return _parse_directory(raw)[0].hotlines[0]

    def test_id_parsed(self) -> None:
        hotline = self._single_hotline(id="ca-en-crisis")
        assert hotline.id == "ca-en-crisis"

    def test_name_parsed(self) -> None:
        hotline = self._single_hotline(name="Crisis Line")
        assert hotline.name == "Crisis Line"

    def test_number_parsed(self) -> None:
        hotline = self._single_hotline(number="1-800-123-4567")
        assert hotline.number == "1-800-123-4567"

    def test_hours_parsed(self) -> None:
        hotline = self._single_hotline(hours="24/7")
        assert hotline.hours == "24/7"

    def test_cost_parsed(self) -> None:
        hotline = self._single_hotline(cost="free")
        assert hotline.cost == "free"

    def test_verified_at_preserved_as_string(self) -> None:
        hotline = self._single_hotline(verifiedAt="2026-03-01")
        assert hotline.verified_at == "2026-03-01"

    def test_result_is_hotline_instance(self) -> None:
        hotline = self._single_hotline()
        assert isinstance(hotline, Hotline)


# ---------------------------------------------------------------------------
# _parse_directory — optional hotline fields default to None
# ---------------------------------------------------------------------------


class TestParseDirectoryOptionalHotlineFields:
    def _hotline_without(self, *fields: str) -> Hotline:
        raw = _hotline_raw()
        for f in fields:
            raw.pop(f, None)
        parsed = {"entries": [_entry_raw(hotlines=[raw])]}
        return _parse_directory(parsed)[0].hotlines[0]

    def test_missing_number_defaults_to_none(self) -> None:
        hotline = self._hotline_without("number")
        assert hotline.number is None

    def test_missing_sms_defaults_to_none(self) -> None:
        hotline = self._hotline_without("sms")
        assert hotline.sms is None

    def test_missing_web_defaults_to_none(self) -> None:
        hotline = self._hotline_without("web")
        assert hotline.web is None

    def test_sms_present_when_provided(self) -> None:
        raw = {"entries": [_entry_raw(hotlines=[_hotline_raw(sms="741741")])]}
        hotline = _parse_directory(raw)[0].hotlines[0]
        assert hotline.sms == "741741"


# ---------------------------------------------------------------------------
# _parse_directory — multiple entries and hotlines
# ---------------------------------------------------------------------------


class TestParseDirectoryMultiple:
    def test_two_entries_parsed(self) -> None:
        raw = {
            "entries": [
                _entry_raw(country="US", locale="en"),
                _entry_raw(country="CA", locale="fr"),
            ]
        }
        result = _parse_directory(raw)
        assert len(result) == 2

    def test_order_preserved(self) -> None:
        raw = {
            "entries": [
                _entry_raw(country="US", locale="en"),
                _entry_raw(country="CA", locale="fr"),
            ]
        }
        result = _parse_directory(raw)
        assert result[0].country == "US"
        assert result[1].country == "CA"

    def test_multiple_hotlines_in_entry(self) -> None:
        raw = {
            "entries": [
                _entry_raw(
                    hotlines=[
                        _hotline_raw(id="line-1"),
                        _hotline_raw(id="line-2"),
                    ]
                )
            ]
        }
        result = _parse_directory(raw)
        assert len(result[0].hotlines) == 2
        assert result[0].hotlines[0].id == "line-1"
        assert result[0].hotlines[1].id == "line-2"

    def test_empty_hotlines_list_gives_empty_tuple(self) -> None:
        raw = {"entries": [_entry_raw(hotlines=[])]}
        result = _parse_directory(raw)
        assert result[0].hotlines == ()

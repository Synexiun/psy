"""System endpoint tests — operational / CI gates.

``GET /system/locale-status`` — i18n catalog release gate.
``GET /system/safety-directory-status`` — safety directory freshness + mirror parity.

These endpoints are queried by CI before each deploy; a failing test here means
the release-gate surface is broken, not just a service feature.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from discipline.app import create_app


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


# =============================================================================
# GET /system/locale-status
# =============================================================================


class TestLocaleStatusEndpoint:
    _URL = "/system/locale-status"

    def test_returns_200(self, client: TestClient) -> None:
        response = client.get(self._URL)
        assert response.status_code == 200

    def test_response_has_top_level_keys(self, client: TestClient) -> None:
        body = client.get(self._URL).json()
        assert "releasable" in body
        assert "draft" in body
        assert "details" in body

    def test_releasable_is_list(self, client: TestClient) -> None:
        body = client.get(self._URL).json()
        assert isinstance(body["releasable"], list)

    def test_draft_is_list(self, client: TestClient) -> None:
        body = client.get(self._URL).json()
        assert isinstance(body["draft"], list)

    def test_details_is_dict(self, client: TestClient) -> None:
        body = client.get(self._URL).json()
        assert isinstance(body["details"], dict)

    def test_en_is_releasable(self, client: TestClient) -> None:
        """English is the source-of-truth catalog (status='source') and must
        always appear in 'releasable'."""
        body = client.get(self._URL).json()
        assert "en" in body["releasable"]

    def test_en_not_in_draft(self, client: TestClient) -> None:
        body = client.get(self._URL).json()
        assert "en" not in body["draft"]

    def test_fr_ar_fa_are_draft(self, client: TestClient) -> None:
        """CLAUDE.md Rule #8: fr/ar/fa catalogs are currently draft and
        must not ship until native clinical review sets them to 'released'."""
        body = client.get(self._URL).json()
        for locale in ("fr", "ar", "fa"):
            assert locale in body["draft"], f"{locale} should be in draft"

    def test_fr_ar_fa_not_in_releasable(self, client: TestClient) -> None:
        body = client.get(self._URL).json()
        for locale in ("fr", "ar", "fa"):
            assert locale not in body["releasable"], f"{locale} must not be releasable yet"

    def test_releasable_and_draft_are_disjoint(self, client: TestClient) -> None:
        body = client.get(self._URL).json()
        overlap = set(body["releasable"]) & set(body["draft"])
        assert overlap == set(), f"locales in both releasable and draft: {overlap}"

    def test_details_has_entry_for_each_locale(self, client: TestClient) -> None:
        body = client.get(self._URL).json()
        all_locales = set(body["releasable"]) | set(body["draft"])
        for locale in all_locales:
            assert locale in body["details"], f"details missing entry for {locale}"

    def test_detail_entry_has_required_fields(self, client: TestClient) -> None:
        body = client.get(self._URL).json()
        for locale, detail in body["details"].items():
            assert "status" in detail, f"details[{locale}] missing 'status'"
            assert "direction" in detail, f"details[{locale}] missing 'direction'"

    def test_en_detail_status_is_source(self, client: TestClient) -> None:
        body = client.get(self._URL).json()
        assert body["details"]["en"]["status"] == "source"

    def test_en_direction_is_ltr(self, client: TestClient) -> None:
        body = client.get(self._URL).json()
        assert body["details"]["en"]["direction"] == "ltr"

    def test_ar_direction_is_rtl(self, client: TestClient) -> None:
        """Arabic is RTL — CLAUDE.md specifies Arabic and Persian are RTL."""
        body = client.get(self._URL).json()
        assert body["details"]["ar"]["direction"] == "rtl"

    def test_fa_direction_is_rtl(self, client: TestClient) -> None:
        """Persian (Farsi) is RTL."""
        body = client.get(self._URL).json()
        assert body["details"]["fa"]["direction"] == "rtl"

    def test_all_detail_statuses_are_valid_strings(self, client: TestClient) -> None:
        valid_statuses = {"source", "released", "draft"}
        body = client.get(self._URL).json()
        for locale, detail in body["details"].items():
            assert detail["status"] in valid_statuses, (
                f"details[{locale}].status={detail['status']!r} is not a valid catalog status"
            )


# =============================================================================
# GET /system/safety-directory-status
# =============================================================================


class TestSafetyDirectoryStatusEndpoint:
    _URL = "/system/safety-directory-status"

    def test_returns_200(self, client: TestClient) -> None:
        response = client.get(self._URL)
        assert response.status_code == 200

    def test_response_has_top_level_keys(self, client: TestClient) -> None:
        body = client.get(self._URL).json()
        assert "stale_entries" in body
        assert "blocked_locales" in body
        assert "mirror_parity_ok" in body
        assert "mirror_drift_detail" in body

    def test_stale_entries_is_list(self, client: TestClient) -> None:
        body = client.get(self._URL).json()
        assert isinstance(body["stale_entries"], list)

    def test_blocked_locales_is_list(self, client: TestClient) -> None:
        body = client.get(self._URL).json()
        assert isinstance(body["blocked_locales"], list)

    def test_mirror_parity_ok_is_bool(self, client: TestClient) -> None:
        body = client.get(self._URL).json()
        assert isinstance(body["mirror_parity_ok"], bool)

    def test_mirror_drift_detail_is_string_or_null(self, client: TestClient) -> None:
        body = client.get(self._URL).json()
        val = body["mirror_drift_detail"]
        assert val is None or isinstance(val, str)

    def test_stale_entry_shape_when_present(self, client: TestClient) -> None:
        """If there are stale entries, each must carry the required fields."""
        body = client.get(self._URL).json()
        for entry in body["stale_entries"]:
            assert "country" in entry
            assert "locale" in entry
            assert "hotline_id" in entry
            assert "verified_at" in entry
            assert "days_stale" in entry

    def test_blocked_locales_format(self, client: TestClient) -> None:
        """Blocked locales are 'COUNTRY/locale' strings (e.g. 'US/en')."""
        body = client.get(self._URL).json()
        for entry in body["blocked_locales"]:
            assert "/" in entry, f"blocked_locales entry {entry!r} not in COUNTRY/locale format"

    def test_stale_days_non_negative_when_present(self, client: TestClient) -> None:
        body = client.get(self._URL).json()
        for entry in body["stale_entries"]:
            assert entry["days_stale"] >= 0

    def test_response_is_stable_across_calls(self, client: TestClient) -> None:
        """The safety directory is static on disk; two consecutive GETs
        return the same freshness state."""
        b1 = client.get(self._URL).json()
        b2 = client.get(self._URL).json()
        assert b1["mirror_parity_ok"] == b2["mirror_parity_ok"]
        assert set(b1["blocked_locales"]) == set(b2["blocked_locales"])

    def test_drift_detail_null_when_parity_ok(self, client: TestClient) -> None:
        """When mirror_parity_ok is True, drift_detail has no information
        to convey and should be null."""
        body = client.get(self._URL).json()
        if body["mirror_parity_ok"]:
            assert body["mirror_drift_detail"] is None

    def test_drift_detail_present_when_parity_fails(self, client: TestClient) -> None:
        """When mirror_parity_ok is False, drift_detail must be a non-empty
        string so ops can diagnose the mismatch."""
        body = client.get(self._URL).json()
        if not body["mirror_parity_ok"]:
            detail = body["mirror_drift_detail"]
            assert isinstance(detail, str) and len(detail) > 0

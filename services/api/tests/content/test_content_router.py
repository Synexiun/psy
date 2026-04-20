"""HTTP surface tests for the content router.

Covers:
- GET /v1/content/safety-directory/{country} — locale-negotiated crisis directory
- GET /v1/content/help/{slug} — help article stub

The pure safety-directory module is tested exhaustively in test_safety_directory.py.
These tests verify the wiring between the HTTP layer, locale negotiation, and the
directory resolver.  A failure here means the integration is broken, not the
individual components.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from discipline.app import create_app


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


# =============================================================================
# GET /v1/content/safety-directory/{country}
# =============================================================================


class TestSafetyDirectoryEndpoint:
    _BASE_URL = "/v1/content/safety-directory"

    def test_us_en_returns_200(self, client: TestClient) -> None:
        response = client.get(f"{self._BASE_URL}/US")
        assert response.status_code == 200

    def test_response_has_expected_top_level_keys(self, client: TestClient) -> None:
        body = client.get(f"{self._BASE_URL}/US").json()
        assert "country" in body
        assert "locale" in body
        assert "emergency" in body
        assert "hotlines" in body

    def test_emergency_has_label_and_number(self, client: TestClient) -> None:
        body = client.get(f"{self._BASE_URL}/US").json()
        emergency = body["emergency"]
        assert "label" in emergency
        assert "number" in emergency
        assert isinstance(emergency["label"], str)
        assert isinstance(emergency["number"], str)

    def test_hotlines_is_non_empty_list(self, client: TestClient) -> None:
        body = client.get(f"{self._BASE_URL}/US").json()
        assert isinstance(body["hotlines"], list)
        assert len(body["hotlines"]) > 0

    def test_hotline_entry_has_required_fields(self, client: TestClient) -> None:
        body = client.get(f"{self._BASE_URL}/US").json()
        hotline = body["hotlines"][0]
        assert "id" in hotline
        assert "name" in hotline
        assert "verified_at" in hotline

    def test_us_country_echoed_in_response(self, client: TestClient) -> None:
        body = client.get(f"{self._BASE_URL}/US").json()
        assert body["country"] == "US"

    def test_us_defaults_to_en_locale(self, client: TestClient) -> None:
        """No Accept-Language header → negotiate_locale falls back to 'en'."""
        body = client.get(f"{self._BASE_URL}/US").json()
        assert body["locale"] == "en"

    def test_case_insensitive_country_code(self, client: TestClient) -> None:
        """Both 'us' and 'US' should resolve to the US entry."""
        body_upper = client.get(f"{self._BASE_URL}/US").json()
        body_lower = client.get(f"{self._BASE_URL}/us").json()
        assert body_upper["country"] == body_lower["country"]
        assert body_upper["locale"] == body_lower["locale"]

    def test_uk_returns_en_directory(self, client: TestClient) -> None:
        body = client.get(f"{self._BASE_URL}/UK").json()
        assert body["country"] == "UK"
        assert body["locale"] == "en"

    def test_ca_with_accept_language_fr_returns_fr_entry(
        self, client: TestClient
    ) -> None:
        """Canada has both en and fr entries.  Accept-Language: fr should
        match the French directory entry via locale negotiation → fr."""
        body = client.get(
            f"{self._BASE_URL}/CA",
            headers={"Accept-Language": "fr"},
        ).json()
        assert body["country"] == "CA"
        assert body["locale"] == "fr"

    def test_ca_without_language_header_returns_en_entry(
        self, client: TestClient
    ) -> None:
        """No Accept-Language → default locale 'en' → CA/en entry."""
        body = client.get(f"{self._BASE_URL}/CA").json()
        assert body["country"] == "CA"
        assert body["locale"] == "en"

    def test_fr_with_accept_language_fr_returns_french_entry(
        self, client: TestClient
    ) -> None:
        body = client.get(
            f"{self._BASE_URL}/FR",
            headers={"Accept-Language": "fr"},
        ).json()
        assert body["country"] == "FR"
        assert body["locale"] == "fr"

    def test_unknown_country_falls_back_to_us_en(self, client: TestClient) -> None:
        """resolve() fallback chain ends at US/en — no 4xx for unknown country."""
        body = client.get(f"{self._BASE_URL}/XZ").json()
        assert body["country"] == "US"
        assert body["locale"] == "en"

    def test_ar_country_with_accept_language_ar(self, client: TestClient) -> None:
        body = client.get(
            f"{self._BASE_URL}/SA",
            headers={"Accept-Language": "ar"},
        ).json()
        assert body["country"] == "SA"
        assert body["locale"] == "ar"

    def test_ir_with_accept_language_fa(self, client: TestClient) -> None:
        body = client.get(
            f"{self._BASE_URL}/IR",
            headers={"Accept-Language": "fa"},
        ).json()
        assert body["country"] == "IR"
        assert body["locale"] == "fa"

    def test_accept_language_regional_variant_collapses_to_primary(
        self, client: TestClient
    ) -> None:
        """'fr-CA' primary tag is 'fr' — negotiate_locale strips the subtag."""
        body = client.get(
            f"{self._BASE_URL}/CA",
            headers={"Accept-Language": "fr-CA"},
        ).json()
        assert body["locale"] == "fr"

    def test_accept_language_unsupported_locale_falls_back_to_en(
        self, client: TestClient
    ) -> None:
        """'de' is not a supported locale; negotiation falls back to 'en'."""
        body = client.get(
            f"{self._BASE_URL}/US",
            headers={"Accept-Language": "de"},
        ).json()
        assert body["locale"] == "en"

    def test_hotline_number_or_sms_present(self, client: TestClient) -> None:
        """Every hotline must have at least a number or an SMS short-code
        so the crisis page can render a contact option."""
        body = client.get(f"{self._BASE_URL}/US").json()
        for hotline in body["hotlines"]:
            has_contact = (hotline.get("number") is not None) or (
                hotline.get("sms") is not None
            )
            assert has_contact, f"hotline {hotline['id']!r} has no number and no sms"


# =============================================================================
# GET /v1/content/help/{slug}
# =============================================================================


class TestHelpArticleEndpoint:
    _BASE_URL = "/v1/content/help"

    def test_any_slug_returns_200(self, client: TestClient) -> None:
        response = client.get(f"{self._BASE_URL}/getting-started")
        assert response.status_code == 200

    def test_response_has_status_field(self, client: TestClient) -> None:
        body = client.get(f"{self._BASE_URL}/getting-started").json()
        assert "status" in body

    def test_status_is_not_implemented(self, client: TestClient) -> None:
        """Stub contract: the field value is 'not_implemented' until the
        help-article repository is wired."""
        body = client.get(f"{self._BASE_URL}/any-slug").json()
        assert body["status"] == "not_implemented"

    def test_slug_echoed_in_response(self, client: TestClient) -> None:
        """The slug is echoed so the client knows which article was requested
        (useful for logging when the stub is replaced with a real loader)."""
        slug = "relapse-compassion-guide"
        body = client.get(f"{self._BASE_URL}/{slug}").json()
        assert body["slug"] == slug

    def test_different_slugs_each_return_200(self, client: TestClient) -> None:
        for slug in ("onboarding", "urge-surfing", "support"):
            resp = client.get(f"{self._BASE_URL}/{slug}")
            assert resp.status_code == 200, f"slug={slug!r} returned {resp.status_code}"

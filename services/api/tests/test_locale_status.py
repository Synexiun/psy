"""``/system/locale-status`` release-gate endpoint tests.

This endpoint is consumed by the deploy pipeline: if a locale appears in
``draft``, the pipeline refuses to ship that locale.  The shape of the
response is therefore a release-contract — a reshape breaks CI on every
consuming deploy.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from discipline.app import create_app


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


def test_endpoint_returns_200(client: TestClient) -> None:
    resp = client.get("/system/locale-status")
    assert resp.status_code == 200


def test_response_shape(client: TestClient) -> None:
    """Wire-contract: ``releasable``, ``draft``, ``details`` keys."""
    body = client.get("/system/locale-status").json()
    assert set(body.keys()) == {"releasable", "draft", "details"}
    assert isinstance(body["releasable"], list)
    assert isinstance(body["draft"], list)
    assert isinstance(body["details"], dict)


def test_en_is_releasable(client: TestClient) -> None:
    """English is source-of-truth and must always be releasable."""
    body = client.get("/system/locale-status").json()
    assert "en" in body["releasable"]


def test_current_draft_locales_flagged(client: TestClient) -> None:
    """As of 2026-04-18, fr/ar/fa are draft.  When clinical review flips
    a locale to ``released``, update this test in the same PR."""
    body = client.get("/system/locale-status").json()
    assert "fr" in body["draft"]
    assert "ar" in body["draft"]
    assert "fa" in body["draft"]


def test_no_locale_in_both_lists(client: TestClient) -> None:
    """Releasable and draft are disjoint — a locale is one or the other."""
    body = client.get("/system/locale-status").json()
    assert not set(body["releasable"]) & set(body["draft"])


def test_all_supported_locales_appear(client: TestClient) -> None:
    """Every supported locale must appear in exactly one of the two lists
    or the deploy pipeline can't tell whether the locale is safe to ship."""
    body = client.get("/system/locale-status").json()
    covered = set(body["releasable"]) | set(body["draft"])
    assert covered == {"en", "fr", "ar", "fa"}


def test_details_for_en_has_source_status(client: TestClient) -> None:
    body = client.get("/system/locale-status").json()
    en = body["details"]["en"]
    assert en["status"] == "source"
    assert en["direction"] == "ltr"
    assert en["reviewed_by"] == "source-of-truth"


def test_details_for_rtl_locales_declare_direction(client: TestClient) -> None:
    body = client.get("/system/locale-status").json()
    assert body["details"]["ar"]["direction"] == "rtl"
    assert body["details"]["fa"]["direction"] == "rtl"


def test_draft_locales_have_null_reviewer(client: TestClient) -> None:
    """A draft locale has no reviewer — the null signal is what the deploy
    pipeline uses to refuse the locale."""
    body = client.get("/system/locale-status").json()
    for locale in ("fr", "ar", "fa"):
        assert body["details"][locale]["reviewed_by"] is None
        assert body["details"][locale]["status"] == "draft"


def test_endpoint_has_no_auth(client: TestClient) -> None:
    """The release-gate reaches this endpoint unauthenticated; a regression
    here would break every deploy."""
    resp = client.get("/system/locale-status")
    assert resp.status_code == 200
    # And explicitly: no request headers were provided

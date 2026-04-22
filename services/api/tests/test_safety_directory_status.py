"""``/system/safety-directory-status`` release-gate endpoint tests.

CLAUDE.md Rule #10: a hotline whose ``verifiedAt`` is older than the
90-day window blocks the country-locale.  This endpoint is consumed by
the deploy pipeline; the response shape is therefore a release contract.

A reshape (renaming ``stale_entries`` to ``stale``, dropping the
``mirror_drift_detail`` field, etc.) breaks every consuming CI job.
"""

from __future__ import annotations

from datetime import date

import pytest
from fastapi.testclient import TestClient

from discipline.app import create_app
from discipline.content.safety_directory import (
    MirrorDriftError,
)

# ---- Fixtures --------------------------------------------------------------


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


# =============================================================================
# Response shape (wire contract — CI depends on this)
# =============================================================================


class TestResponseShape:
    def test_endpoint_returns_200(self, client: TestClient) -> None:
        resp = client.get("/system/safety-directory-status")
        assert resp.status_code == 200

    def test_top_level_keys_exact(self, client: TestClient) -> None:
        """Pinned set of keys.  Adding a key is fine (additive change),
        but renaming or removing one is a CI-breaking event — the deploy
        pipeline reads each by name."""
        body = client.get("/system/safety-directory-status").json()
        assert set(body.keys()) == {
            "stale_entries",
            "blocked_locales",
            "mirror_parity_ok",
            "mirror_drift_detail",
        }

    def test_stale_entries_is_list(self, client: TestClient) -> None:
        body = client.get("/system/safety-directory-status").json()
        assert isinstance(body["stale_entries"], list)

    def test_blocked_locales_is_list(self, client: TestClient) -> None:
        body = client.get("/system/safety-directory-status").json()
        assert isinstance(body["blocked_locales"], list)

    def test_mirror_parity_is_bool(self, client: TestClient) -> None:
        body = client.get("/system/safety-directory-status").json()
        assert isinstance(body["mirror_parity_ok"], bool)


# =============================================================================
# Currently-fresh directory state
# =============================================================================


class TestLiveDirectoryFreshness:
    """The on-disk hotlines.json (verified 2026-04-01) is well within
    the 90-day window as of the test reference date 2026-04-18, so the
    live directory must report no stale entries.

    If a future change to the data file breaks this, the test fails
    loudly — which is the desired behavior; a stale on-disk hotline
    means deploys should be blocked anyway."""

    def test_no_stale_entries_for_current_data(self, client: TestClient) -> None:
        body = client.get("/system/safety-directory-status").json()
        assert body["stale_entries"] == []

    def test_no_blocked_locales_for_current_data(self, client: TestClient) -> None:
        body = client.get("/system/safety-directory-status").json()
        assert body["blocked_locales"] == []


# =============================================================================
# Mirror parity reporting
# =============================================================================


class TestMirrorParity:
    """The package and api copies of ``hotlines.json`` must be byte-for-
    byte identical.  In a healthy checkout they are; the endpoint
    surfaces this for CI to enforce."""

    def test_parity_ok_in_clean_checkout(self, client: TestClient) -> None:
        body = client.get("/system/safety-directory-status").json()
        assert body["mirror_parity_ok"] is True
        assert body["mirror_drift_detail"] is None

    def test_drift_surfaces_via_monkeypatch(
        self,
        monkeypatch: pytest.MonkeyPatch,
        client: TestClient,
    ) -> None:
        """Inject a fake parity failure to confirm the endpoint surfaces
        the drift detail rather than blowing up.  We monkeypatch the
        symbol the app's route imports — ``app.verify_mirror_parity``
        — not the source module, because the route captured the
        function reference at import time."""
        from discipline import app as app_module

        def _raise_drift() -> None:
            raise MirrorDriftError(
                "fake drift: package=abc123… api=def456…"
            )

        monkeypatch.setattr(app_module, "verify_mirror_parity", _raise_drift)
        body = client.get("/system/safety-directory-status").json()
        assert body["mirror_parity_ok"] is False
        assert body["mirror_drift_detail"] is not None
        assert "fake drift" in body["mirror_drift_detail"]

    def test_missing_mirror_distinguishable_from_drift(
        self,
        monkeypatch: pytest.MonkeyPatch,
        client: TestClient,
    ) -> None:
        """A missing mirror file is reported separately from a content
        drift.  Ops needs to be able to tell 'workspace not checked out
        on the box' from 'someone edited one copy and forgot the
        other.'"""
        from discipline import app as app_module

        def _raise_missing() -> None:
            raise FileNotFoundError(
                "[Errno 2] No such file: 'packages/safety-directory/src/hotlines.json'"
            )

        monkeypatch.setattr(app_module, "verify_mirror_parity", _raise_missing)
        body = client.get("/system/safety-directory-status").json()
        assert body["mirror_parity_ok"] is False
        assert "not found" in body["mirror_drift_detail"]


# =============================================================================
# Stale entry surfacing — injected via monkeypatch
# =============================================================================


class TestStaleEntrySurfacing:
    """Use a synthetic stale entry so we don't need to backdate the real
    JSON.  Patch ``check_freshness`` to return a known StaleEntry tuple
    and verify the wire format mirrors it."""

    def test_stale_entry_appears_in_response(
        self,
        monkeypatch: pytest.MonkeyPatch,
        client: TestClient,
    ) -> None:
        from discipline import app as app_module
        from discipline.content.safety_directory import StaleEntry

        cutoff = date(2026, 1, 18)
        verified = date(2025, 10, 1)
        stale = StaleEntry(
            country="ZZ",
            locale="en",
            hotline_id="zz-fake-001",
            verified_at=verified,
            review_cutoff=cutoff,
            days_stale=(cutoff - verified).days,
        )
        monkeypatch.setattr(
            app_module, "check_freshness", lambda: (stale,)
        )

        body = client.get("/system/safety-directory-status").json()
        assert len(body["stale_entries"]) == 1
        entry = body["stale_entries"][0]
        assert entry["country"] == "ZZ"
        assert entry["locale"] == "en"
        assert entry["hotline_id"] == "zz-fake-001"
        assert entry["verified_at"] == "2025-10-01"
        assert entry["days_stale"] == (cutoff - verified).days

    def test_stale_entry_blocks_locale(
        self,
        monkeypatch: pytest.MonkeyPatch,
        client: TestClient,
    ) -> None:
        """A stale hotline contributes its country/locale to
        ``blocked_locales``.  CI fails on a non-empty blocked list."""
        from discipline import app as app_module
        from discipline.content.safety_directory import StaleEntry

        stale = StaleEntry(
            country="DE",
            locale="en",
            hotline_id="de-old",
            verified_at=date(2025, 1, 1),
            review_cutoff=date(2026, 1, 18),
            days_stale=382,
        )
        monkeypatch.setattr(app_module, "check_freshness", lambda: (stale,))

        body = client.get("/system/safety-directory-status").json()
        assert body["blocked_locales"] == ["DE/en"]

    def test_multiple_stale_entries_dedup_locale(
        self,
        monkeypatch: pytest.MonkeyPatch,
        client: TestClient,
    ) -> None:
        """Two stale hotlines in the same country/locale produce ONE
        blocked-locale entry.  Without dedup, CI would over-report."""
        from discipline import app as app_module
        from discipline.content.safety_directory import StaleEntry

        stale1 = StaleEntry(
            country="FR",
            locale="fr",
            hotline_id="fr-1",
            verified_at=date(2025, 1, 1),
            review_cutoff=date(2026, 1, 18),
            days_stale=382,
        )
        stale2 = StaleEntry(
            country="FR",
            locale="fr",
            hotline_id="fr-2",
            verified_at=date(2025, 1, 5),
            review_cutoff=date(2026, 1, 18),
            days_stale=378,
        )
        monkeypatch.setattr(
            app_module, "check_freshness", lambda: (stale1, stale2)
        )

        body = client.get("/system/safety-directory-status").json()
        assert body["blocked_locales"] == ["FR/fr"]
        assert len(body["stale_entries"]) == 2

    def test_blocked_locales_sorted_for_stable_diff(
        self,
        monkeypatch: pytest.MonkeyPatch,
        client: TestClient,
    ) -> None:
        """Sorted output makes CI diffs stable — a flapping unsorted
        list would force ops to re-read the entire field every time
        instead of just glancing at the first new entry."""
        from discipline import app as app_module
        from discipline.content.safety_directory import StaleEntry

        cutoff = date(2026, 1, 18)
        entries = (
            StaleEntry("US", "en", "h1", date(2025, 1, 1), cutoff, 382),
            StaleEntry("DE", "en", "h2", date(2025, 1, 1), cutoff, 382),
            StaleEntry("FR", "fr", "h3", date(2025, 1, 1), cutoff, 382),
        )
        monkeypatch.setattr(app_module, "check_freshness", lambda: entries)

        body = client.get("/system/safety-directory-status").json()
        assert body["blocked_locales"] == ["DE/en", "FR/fr", "US/en"]


# =============================================================================
# Operational accessibility (no auth, no PHI)
# =============================================================================


class TestOperationalSurface:
    def test_no_phi_boundary_header(self, client: TestClient) -> None:
        """This is governance state, not user data — no PHI header."""
        from discipline.shared.http.phi_boundary import PHI_BOUNDARY_HEADER

        resp = client.get("/system/safety-directory-status")
        assert PHI_BOUNDARY_HEADER not in resp.headers

    def test_endpoint_is_unauthenticated(self, client: TestClient) -> None:
        """No Authorization header sent — must still return 200.  CI runs
        unauthenticated and would break if this required auth."""
        resp = client.get("/system/safety-directory-status")
        assert resp.status_code == 200

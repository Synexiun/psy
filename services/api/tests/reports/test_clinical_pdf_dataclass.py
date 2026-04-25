"""Unit tests for ClinicalReport frozen dataclass and render stub.

clinical_pdf.py has a router test (test_clinical_pdf_router.py) that verifies
the 501 HTTP contract, but the ClinicalReport dataclass itself has no direct
unit coverage.  These tests pin:

- Frozen dataclass construction and field access.
- Default version field ("1.0.0").
- Immutability — mutations raise FrozenInstanceError.
- render() is a stub that raises NotImplementedError.

The ``version`` field pins the PDF archive schema version at the dataclass
level.  A blind rename or version bump here would fail the test before it
reaches the PDF renderer.
"""

from __future__ import annotations

import asyncio
import dataclasses
from datetime import UTC, datetime

import pytest

from discipline.reports.clinical_pdf import ClinicalReport, render


# ---- Helpers ---------------------------------------------------------------


def _make_report(**kwargs: object) -> ClinicalReport:
    defaults: dict[str, object] = {
        "user_id": "user-001",
        "window_start": datetime(2026, 4, 1, 0, 0, 0, tzinfo=UTC),
        "window_end": datetime(2026, 4, 30, 23, 59, 59, tzinfo=UTC),
        "locale": "en",
    }
    defaults.update(kwargs)
    return ClinicalReport(**defaults)  # type: ignore[arg-type]


# ---- Construction ----------------------------------------------------------


class TestConstruction:
    def test_required_fields_accepted(self) -> None:
        r = _make_report()
        assert r.user_id == "user-001"

    def test_window_start_stored(self) -> None:
        dt = datetime(2026, 3, 1, tzinfo=UTC)
        r = _make_report(window_start=dt)
        assert r.window_start == dt

    def test_window_end_stored(self) -> None:
        dt = datetime(2026, 3, 31, tzinfo=UTC)
        r = _make_report(window_end=dt)
        assert r.window_end == dt

    def test_locale_stored(self) -> None:
        r = _make_report(locale="fa")
        assert r.locale == "fa"

    def test_default_version_is_1_0_0(self) -> None:
        """Pinned: archive schema version must be '1.0.0' until the PDF
        format changes in a breaking way.  A silent version bump here
        would break client decoders that key on the version field."""
        r = _make_report()
        assert r.version == "1.0.0"

    def test_explicit_version_override(self) -> None:
        r = _make_report(version="2.0.0")
        assert r.version == "2.0.0"


# ---- Frozen / immutability -------------------------------------------------


class TestFrozen:
    def test_is_dataclass(self) -> None:
        assert dataclasses.is_dataclass(ClinicalReport)

    def test_mutation_raises(self) -> None:
        """Frozen so a downstream handler can't mutate the report metadata
        after construction — a post-hoc locale change would desync the
        rendered PDF from the audit record."""
        r = _make_report()
        with pytest.raises(Exception):  # dataclasses.FrozenInstanceError
            r.user_id = "different-user"  # type: ignore[misc]

    def test_version_mutation_raises(self) -> None:
        r = _make_report()
        with pytest.raises(Exception):
            r.version = "9.9.9"  # type: ignore[misc]

    def test_locale_mutation_raises(self) -> None:
        r = _make_report()
        with pytest.raises(Exception):
            r.locale = "fr"  # type: ignore[misc]

    def test_equality_by_value(self) -> None:
        """Frozen dataclasses compare by field values, not identity."""
        dt_start = datetime(2026, 4, 1, tzinfo=UTC)
        dt_end = datetime(2026, 4, 30, tzinfo=UTC)
        a = ClinicalReport(
            user_id="u", window_start=dt_start, window_end=dt_end, locale="en"
        )
        b = ClinicalReport(
            user_id="u", window_start=dt_start, window_end=dt_end, locale="en"
        )
        assert a == b

    def test_different_user_id_not_equal(self) -> None:
        dt_start = datetime(2026, 4, 1, tzinfo=UTC)
        dt_end = datetime(2026, 4, 30, tzinfo=UTC)
        a = ClinicalReport(
            user_id="user-a", window_start=dt_start, window_end=dt_end, locale="en"
        )
        b = ClinicalReport(
            user_id="user-b", window_start=dt_start, window_end=dt_end, locale="en"
        )
        assert a != b


# ---- render stub -----------------------------------------------------------


class TestRenderStub:
    def test_render_raises_not_implemented(self) -> None:
        """Stub contract: render() is not yet wired to the PDF renderer.
        Any call must raise NotImplementedError so callers know the
        feature is pending, not silently returning empty bytes."""
        r = _make_report()
        with pytest.raises(NotImplementedError):
            asyncio.run(render(r))

    def test_render_is_async(self) -> None:
        """render() is declared async — callers must await it.  A sync
        implementation would break the async worker that calls it."""
        import asyncio
        r = _make_report()
        coro = render(r)
        # Cancel to avoid UnraisableExceptionWarning from an un-awaited coroutine.
        try:
            asyncio.run(coro)
        except NotImplementedError:
            pass

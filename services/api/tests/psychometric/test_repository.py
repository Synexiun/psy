"""``discipline.psychometric.repository`` unit tests.

The repository is the persistence boundary for submitted assessments
— the ``/history`` timeline reads through it and Sprint 24's single
FHIR-Observation GET looks up records by id.  Tested here at the
module level; router-level integration tests live in
``tests/psychometric/test_assessments_router.py`` under the
``TestHistoryEndpoint`` class.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from discipline.psychometric.repository import (
    AssessmentRecord,
    InMemoryAssessmentRepository,
    get_assessment_repository,
    reset_assessment_repository,
)


def _record(
    *,
    assessment_id: str = "a1",
    user_id: str = "user-1",
    instrument: str = "phq9",
    total: int = 10,
    severity: str = "moderate",
    requires_t3: bool = False,
    raw_items: tuple[int, ...] = (1, 1, 1, 1, 1, 1, 1, 1, 1),
    created_at: datetime | None = None,
    **overrides: object,
) -> AssessmentRecord:
    """Build a minimally-valid AssessmentRecord for tests.

    Helper avoids repeating the full constructor signature in every
    test.  ``created_at`` defaults to a fixed timestamp so tests that
    don't care about ordering still produce deterministic records."""
    base: dict[str, object] = dict(
        assessment_id=assessment_id,
        user_id=user_id,
        instrument=instrument,
        total=total,
        severity=severity,
        requires_t3=requires_t3,
        raw_items=raw_items,
        created_at=created_at or datetime(2026, 4, 18, tzinfo=timezone.utc),
    )
    base.update(overrides)
    return AssessmentRecord(**base)  # type: ignore[arg-type]


# ---- AssessmentRecord shape ---------------------------------------------


class TestAssessmentRecord:
    def test_is_frozen(self) -> None:
        """A frozen dataclass protects against accidental mutation of
        a record after it's handed to a reader — e.g. a chart renderer
        sorting the list in place must not corrupt the stored copy."""
        r = _record()
        with pytest.raises(Exception):  # noqa: B017 — FrozenInstanceError
            r.total = 99  # type: ignore[misc]

    def test_raw_items_is_tuple(self) -> None:
        """Tuple (not list) keeps the record hashable and truly
        immutable.  A list field would let a caller mutate
        ``record.raw_items`` from the outside."""
        r = _record(raw_items=(1, 2, 3))
        assert isinstance(r.raw_items, tuple)

    def test_optional_fields_default_to_none(self) -> None:
        r = _record()
        assert r.t3_reason is None
        assert r.index is None
        assert r.cutoff_used is None
        assert r.positive_screen is None
        assert r.triggering_items is None
        assert r.sex is None
        assert r.behavior_within_3mo is None


# ---- Save + history core contract ---------------------------------------


class TestSave:
    def test_save_round_trip(self) -> None:
        repo = InMemoryAssessmentRepository()
        r = _record()
        repo.save(r)
        assert len(repo) == 1
        assert repo.history_for("user-1") == [r]

    def test_save_rejects_empty_user_id(self) -> None:
        """An empty user_id would silently vanish into the defaultdict's
        empty-string bucket — refuse it at the boundary."""
        repo = InMemoryAssessmentRepository()
        with pytest.raises(ValueError, match="non-empty"):
            repo.save(_record(user_id=""))

    def test_save_duplicate_assessment_id_overwrites(self) -> None:
        """Same assessment_id under the same user replaces the prior
        entry — the by-user list must not show the record twice."""
        repo = InMemoryAssessmentRepository()
        r1 = _record(assessment_id="a1", total=1)
        r2 = _record(assessment_id="a1", total=9)
        repo.save(r1)
        repo.save(r2)
        history = repo.history_for("user-1")
        assert len(history) == 1
        assert history[0].total == 9

    def test_save_duplicate_across_users_overwrites(self) -> None:
        """Even more defensive — a duplicate assessment_id that arrives
        under a different user_id should overwrite (assessment_id is a
        globally unique UUID; two users sharing one means a bug)."""
        repo = InMemoryAssessmentRepository()
        r1 = _record(assessment_id="a1", user_id="user-A")
        r2 = _record(assessment_id="a1", user_id="user-B")
        repo.save(r1)
        repo.save(r2)
        # Original user's history is now empty.
        assert repo.history_for("user-A") == []
        assert repo.history_for("user-B") == [r2]


class TestHistoryFor:
    def test_empty_for_unknown_user(self) -> None:
        """Unknown user_id returns empty list — and MUST NOT create a
        side-effect entry in the defaultdict (leaks memory over time
        with probing attackers enumerating user ids)."""
        repo = InMemoryAssessmentRepository()
        assert repo.history_for("ghost") == []
        # Private check that we didn't poison the dict.
        assert "ghost" not in repo._by_user  # type: ignore[attr-defined]

    def test_newest_first(self) -> None:
        """Sort order matters — the UI renders a top-to-bottom timeline
        where the most recent assessment is at the top."""
        repo = InMemoryAssessmentRepository()
        t1 = datetime(2026, 4, 18, 10, 0, tzinfo=timezone.utc)
        t2 = datetime(2026, 4, 18, 12, 0, tzinfo=timezone.utc)
        t3 = datetime(2026, 4, 18, 14, 0, tzinfo=timezone.utc)
        repo.save(_record(assessment_id="a", created_at=t1))
        repo.save(_record(assessment_id="c", created_at=t3))
        repo.save(_record(assessment_id="b", created_at=t2))
        history = repo.history_for("user-1")
        assert [r.assessment_id for r in history] == ["c", "b", "a"]

    def test_respects_limit(self) -> None:
        repo = InMemoryAssessmentRepository()
        base = datetime(2026, 4, 18, tzinfo=timezone.utc)
        for i in range(10):
            repo.save(
                _record(
                    assessment_id=f"a{i}",
                    created_at=base + timedelta(seconds=i),
                )
            )
        history = repo.history_for("user-1", limit=3)
        assert len(history) == 3
        # Must be the 3 newest.
        assert [r.assessment_id for r in history] == ["a9", "a8", "a7"]

    def test_default_limit_is_50(self) -> None:
        """50 records spans roughly a year of weekly check-ins — the
        default lets the UI render without paginating in the common
        case.  A regression to a smaller default would silently hide
        history."""
        repo = InMemoryAssessmentRepository()
        base = datetime(2026, 4, 18, tzinfo=timezone.utc)
        for i in range(60):
            repo.save(
                _record(
                    assessment_id=f"a{i}",
                    created_at=base + timedelta(seconds=i),
                )
            )
        history = repo.history_for("user-1")
        assert len(history) == 50

    def test_rejects_empty_user_id(self) -> None:
        repo = InMemoryAssessmentRepository()
        with pytest.raises(ValueError, match="non-empty"):
            repo.history_for("")

    def test_rejects_zero_limit(self) -> None:
        repo = InMemoryAssessmentRepository()
        with pytest.raises(ValueError, match="positive"):
            repo.history_for("user-1", limit=0)

    def test_rejects_negative_limit(self) -> None:
        repo = InMemoryAssessmentRepository()
        with pytest.raises(ValueError, match="positive"):
            repo.history_for("user-1", limit=-1)


class TestCountFor:
    def test_counts_all_not_just_page(self) -> None:
        """``count_for`` returns the absolute count, not ``min(total,
        limit)`` — the UI uses it to decide whether to show a 'load
        older' control, which needs the true total."""
        repo = InMemoryAssessmentRepository()
        base = datetime(2026, 4, 18, tzinfo=timezone.utc)
        for i in range(75):
            repo.save(
                _record(
                    assessment_id=f"a{i}",
                    created_at=base + timedelta(seconds=i),
                )
            )
        assert repo.count_for("user-1") == 75

    def test_unknown_user_is_zero(self) -> None:
        repo = InMemoryAssessmentRepository()
        assert repo.count_for("ghost") == 0

    def test_rejects_empty_user_id(self) -> None:
        repo = InMemoryAssessmentRepository()
        with pytest.raises(ValueError, match="non-empty"):
            repo.count_for("")


class TestGetById:
    def test_round_trip(self) -> None:
        repo = InMemoryAssessmentRepository()
        r = _record(assessment_id="a1")
        repo.save(r)
        assert repo.get_by_id("a1") == r

    def test_missing_returns_none(self) -> None:
        """None rather than raising — the HTTP layer translates to
        a clean 404 without needing an exception catch."""
        repo = InMemoryAssessmentRepository()
        assert repo.get_by_id("never-seen") is None

    def test_rejects_empty_id(self) -> None:
        repo = InMemoryAssessmentRepository()
        with pytest.raises(ValueError, match="non-empty"):
            repo.get_by_id("")

    def test_get_does_not_enforce_user_scope(self) -> None:
        """Callers that expose get_by_id over HTTP MUST authorize
        separately.  This test pins the library contract — the repo
        itself returns whatever is stored, and the clinician-portal /
        patient-portal authorization happens at the HTTP layer."""
        repo = InMemoryAssessmentRepository()
        r = _record(user_id="user-A")
        repo.save(r)
        assert repo.get_by_id(r.assessment_id) == r


# ---- Multi-user isolation -----------------------------------------------


class TestMultiUserIsolation:
    def test_users_see_only_their_own_records(self) -> None:
        repo = InMemoryAssessmentRepository()
        repo.save(_record(assessment_id="a1", user_id="user-A"))
        repo.save(_record(assessment_id="b1", user_id="user-B"))
        repo.save(_record(assessment_id="a2", user_id="user-A"))
        a_history = repo.history_for("user-A")
        b_history = repo.history_for("user-B")
        assert {r.assessment_id for r in a_history} == {"a1", "a2"}
        assert {r.assessment_id for r in b_history} == {"b1"}

    def test_counts_are_per_user(self) -> None:
        repo = InMemoryAssessmentRepository()
        repo.save(_record(assessment_id="a1", user_id="user-A"))
        repo.save(_record(assessment_id="a2", user_id="user-A"))
        repo.save(_record(assessment_id="b1", user_id="user-B"))
        assert repo.count_for("user-A") == 2
        assert repo.count_for("user-B") == 1


# ---- Clear + length ------------------------------------------------------


class TestClear:
    def test_clear_empties_repo(self) -> None:
        repo = InMemoryAssessmentRepository()
        repo.save(_record(assessment_id="a1", user_id="user-A"))
        repo.save(_record(assessment_id="b1", user_id="user-B"))
        assert len(repo) == 2
        repo.clear()
        assert len(repo) == 0
        assert repo.history_for("user-A") == []
        assert repo.get_by_id("a1") is None


# ---- Module-level default repository ------------------------------------


class TestDefaultRepo:
    def test_get_returns_singleton(self) -> None:
        a = get_assessment_repository()
        b = get_assessment_repository()
        assert a is b

    def test_reset_replaces_singleton(self) -> None:
        a = get_assessment_repository()
        reset_assessment_repository()
        b = get_assessment_repository()
        assert a is not b

    def test_reset_drops_all_entries(self) -> None:
        get_assessment_repository().save(_record())
        reset_assessment_repository()
        assert len(get_assessment_repository()) == 0


# ---- Clock injection -----------------------------------------------------


class TestClockInjection:
    def test_now_returns_injected_clock(self) -> None:
        """``repo.now()`` returns the clock the router uses to stamp
        records.  Tests that pin creation times use this to feed the
        repo a fixed timestamp without monkey-patching ``datetime``."""
        fixed = datetime(2026, 1, 1, tzinfo=timezone.utc)
        repo = InMemoryAssessmentRepository(now_fn=lambda: fixed)
        assert repo.now() == fixed

"""In-memory repository for submitted psychometric assessments.

Contract:
- Each successful ``POST /v1/assessments`` with a ``user_id`` persists
  one :class:`AssessmentRecord` — the full event (score envelope plus
  the raw item responses that produced it).
- ``history_for(user_id)`` returns that user's records newest-first,
  capped at ``limit``.  Other users' records are unreachable — the
  user_id key is the isolation boundary.
- ``get_by_id(assessment_id)`` returns the single record without a
  user scope; callers that expose this over an HTTP surface must
  authorize separately (see the clinician-portal PHI boundary).

Scope:
This is an **in-memory, per-process** store.  A production deployment
will move this to PostgreSQL (the ``psychometric`` module owns its
own tables per the CLAUDE.md cross-module rule).  The move-to-Postgres
delta is bounded by this interface — callers see ``save`` / ``history_for``
and never read ``_data`` directly, so the swap is a file-level change.

Privacy:
Records contain ``raw_items`` (PHI — the caller's literal answers on
a validated clinical instrument).  The in-memory store has no
persistence-to-disk and evaporates on process restart, which is the
reason the 24-hour idempotency TTL is tolerable: we never want raw
item responses to outlive the submitting session across a redeploy.
When the repository is promoted to Postgres, the retention policy
must be explicit in the data model doc; a silent 'records live
forever' would be a DPIA violation.

Thread safety:
A single :class:`threading.Lock` guards the backing dict.  FastAPI's
async routes may be invoked from multiple threads under uvicorn
workers; the lock is held only for O(1) dict operations and the
short append to a per-user list, never across an ``await`` boundary.
"""

from __future__ import annotations

import threading
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

__all__ = [
    "AssessmentRecord",
    "InMemoryAssessmentRepository",
    "get_assessment_repository",
    "reset_assessment_repository",
]


@dataclass(frozen=True)
class AssessmentRecord:
    """Immutable record of one submitted assessment.

    All fields mirror the scoring result envelope, plus the raw request
    context needed to re-render the event as a FHIR Observation later
    without consulting a second source of truth.

    ``raw_items`` and the per-instrument context fields (``sex``,
    ``behavior_within_3mo``, ``concurrent_symptoms``,
    ``functional_impairment``) are retained so the Sprint 24
    single-Observation GET can reconstruct the full event; the
    ``/history`` endpoint does NOT expose ``raw_items`` — that's a
    PHI-boundary response-shape choice, not a storage choice.

    Tuple (not list) for ``raw_items`` and ``triggering_items`` so the
    record stays hashable and genuinely immutable — a mutable list
    field on a frozen dataclass is a common footgun.
    """

    assessment_id: str
    user_id: str
    instrument: str
    total: int
    severity: str
    requires_t3: bool
    raw_items: tuple[int, ...]
    created_at: datetime
    t3_reason: str | None = None
    index: int | None = None
    cutoff_used: int | None = None
    positive_screen: bool | None = None
    triggering_items: tuple[int, ...] | None = None
    # Multi-subscale profile surfacing — URICA-first (precontemplation /
    # contemplation / action / maintenance), reusable for PCL-5 clusters,
    # OCI-R subtypes, and BIS-11 factors without schema churn.  Stored as
    # a plain ``dict`` rather than a frozen mapping because the router
    # constructs the mapping fresh per dispatch; mutating the stored
    # dict from a caller would be a policy violation, not a mechanical
    # one — matching the raw_items convention (tuple for genuine
    # immutability) vs triggering_items (also tuple) is deliberately
    # relaxed here since the subscale map is a computed projection, not
    # raw user input.
    subscales: dict[str, int] | None = None
    instrument_version: str | None = None
    sex: str | None = None
    behavior_within_3mo: bool | None = None
    # MDQ Part 2 — yes/no concurrent-symptoms gate.  Stored verbatim so a
    # clinician reviewing the record can re-derive the positive_screen
    # decision without trusting the aggregate.
    concurrent_symptoms: bool | None = None
    # MDQ Part 3 — one of "none"/"minor"/"moderate"/"serious".  Stored as
    # the canonical categorical label (not a bool collapsed on the
    # moderate-or-serious gate) so a future FHIR re-render can preserve
    # the full ordinal distinction.
    functional_impairment: str | None = None
    # SDS — the substance key used to select the Gossop 1995 /
    # follow-up-literature cutoff.  Stored verbatim so a clinician
    # reviewing the record can re-derive the positive_screen decision
    # without trusting the aggregate.  Non-SDS records leave this
    # ``None``.
    substance: str | None = None


class InMemoryAssessmentRepository:
    """Per-user timeline of submitted assessments.

    Typical lifecycle:

    >>> repo = InMemoryAssessmentRepository()
    >>> repo.save(record)
    >>> history = repo.history_for("user-123", limit=50)
    >>> record = repo.get_by_id(assessment_id)
    """

    def __init__(
        self, *, now_fn: Callable[[], datetime] | None = None
    ) -> None:
        self._now = now_fn or (lambda: datetime.now(UTC))
        self._by_user: dict[str, list[AssessmentRecord]] = defaultdict(list)
        self._by_id: dict[str, AssessmentRecord] = {}
        self._lock = threading.Lock()

    def now(self) -> datetime:
        """Expose the injected clock so the router can stamp records
        with the same timestamp the repo would use — lets tests pin
        the creation moment deterministically without monkey-patching
        ``datetime.now``."""
        return self._now()

    def save(self, record: AssessmentRecord) -> None:
        """Persist a record.

        Duplicate ``assessment_id`` overwrites the prior entry — in
        the in-memory world this is a defensive no-op because
        ``assessment_id`` is a UUID generated per dispatch and
        collisions would indicate a much bigger bug.  The overwrite
        semantic means a deliberate replay (e.g. a test harness)
        doesn't accumulate phantom entries in the by-user list.
        """
        if not record.user_id:
            raise ValueError("AssessmentRecord.user_id must be non-empty")
        with self._lock:
            existing = self._by_id.get(record.assessment_id)
            if existing is not None:
                # Defensive overwrite — remove the stale entry from the
                # by-user list so the timeline doesn't show the same
                # assessment twice.
                user_list = self._by_user.get(existing.user_id)
                if user_list is not None:
                    self._by_user[existing.user_id] = [
                        r for r in user_list
                        if r.assessment_id != record.assessment_id
                    ]
            self._by_user[record.user_id].append(record)
            self._by_id[record.assessment_id] = record

    def history_for(
        self, user_id: str, *, limit: int = 50
    ) -> list[AssessmentRecord]:
        """Return the user's records newest-first, capped at ``limit``.

        ``limit`` defaults to 50 — enough to render a year of weekly
        check-ins without paginating.  Callers that need more should
        pass a higher limit explicitly; a future Postgres
        implementation will want cursor pagination instead.

        Cross-user isolation is enforced here: an unknown ``user_id``
        returns an empty list, never the defaultdict's side-effect of
        creating a new entry (we take the list under the lock but do
        not modify ``_by_user`` — ``dict.get`` instead of ``__getitem__``).
        """
        if not user_id:
            raise ValueError("user_id must be non-empty")
        if limit <= 0:
            raise ValueError(f"limit must be positive, got {limit}")
        with self._lock:
            records = list(self._by_user.get(user_id, ()))
        records.sort(key=lambda r: r.created_at, reverse=True)
        return records[:limit]

    def count_for(self, user_id: str) -> int:
        """Return the total number of records for ``user_id``.

        Used by the ``/history`` endpoint to surface 'showing N of
        total' pagination metadata without fetching a full list when
        the caller only needs the count.  Unknown users return 0.
        """
        if not user_id:
            raise ValueError("user_id must be non-empty")
        with self._lock:
            return len(self._by_user.get(user_id, ()))

    def get_by_id(self, assessment_id: str) -> AssessmentRecord | None:
        """Look up a single record by ``assessment_id``.

        Returns ``None`` if not found.  This does NOT enforce user
        scope — the caller is expected to authorize before calling
        (clinician access, patient-portal same-user check, etc.).
        The missing-record result is ``None`` rather than raising so
        the HTTP layer can translate it to a clean 404 without
        catching an exception type.
        """
        if not assessment_id:
            raise ValueError("assessment_id must be non-empty")
        with self._lock:
            return self._by_id.get(assessment_id)

    def clear(self) -> None:
        """Drop every record — primarily for test fixtures."""
        with self._lock:
            self._by_user.clear()
            self._by_id.clear()

    def __len__(self) -> int:
        with self._lock:
            return len(self._by_id)


# ---- Module-level default repository -------------------------------------


_default_repo: InMemoryAssessmentRepository | None = None
_default_repo_lock = threading.Lock()


def get_assessment_repository() -> InMemoryAssessmentRepository:
    """Return the process-wide default repository (lazily created).

    The psychometric router uses this module default.  Tests that want
    a fresh repo per test call :func:`reset_assessment_repository`
    before each run — or use the router's autouse fixture which does
    this automatically.
    """
    global _default_repo
    with _default_repo_lock:
        if _default_repo is None:
            _default_repo = InMemoryAssessmentRepository()
        return _default_repo


def reset_assessment_repository() -> None:
    """Drop and recreate the module-level default repository."""
    global _default_repo
    with _default_repo_lock:
        _default_repo = None

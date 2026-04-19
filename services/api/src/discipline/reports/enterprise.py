"""Enterprise aggregates — k-anonymous, DP-noised.

The k-anonymity floor (k ≥ 5) is enforced here at the rendering boundary.
Any cell whose underlying cohort size is < k must return ``None`` so the
enterprise dashboard shows "insufficient data" instead of a reconstructable
per-user signal.

Layering:

- :func:`suppress_below_k` — the pure primitive.  Given a value and its
  backing cohort size ``n``, returns the value if ``n >= k`` else ``None``.
  This is the single source of truth for the k threshold; every caller
  must route its cells through it (no ad-hoc ``if n >= 5`` checks).

- :class:`OrgEngagementSnapshot` — raw (un-suppressed) input counts.
  Upstream SQL reads from the k-anonymity-enforcing ``analytics_org_*``
  views and populates this.  The snapshot is a transient — it never
  leaves the service process.

- :func:`build_org_engagement` — applies :func:`suppress_below_k` to each
  cell of the snapshot and returns an :class:`OrgEngagement` suitable for
  the wire.

Differential-privacy noise (Laplace/Gaussian) can be added on top later
by composing a noise function over the :class:`OrgEngagement` result.
Noise is NOT a substitute for k-anonymity — it's defense-in-depth, and
must be applied AFTER suppression so suppressed cells stay suppressed.

References:
- CLAUDE.md §"What this project is": ``web-enterprise`` — aggregate-only,
  k ≥ 5.
- Docs/Whitepapers/03_Privacy_Architecture.md §Analytics DP budget.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeVar

# The k-anonymity threshold.  Changing this value is a privacy-policy
# decision — do NOT adjust without a DPIA + compliance review.  Pinned
# as a module constant so every caller routes through the same value.
K_ANONYMITY_THRESHOLD: int = 5


# Generic type for the value being suppressed.  Supports int / float and
# any wrapper type a caller might pass (e.g. a tagged numeric).
T = TypeVar("T")


# ---- Exceptions ------------------------------------------------------------


class InvalidCohortSizeError(ValueError):
    """Raised when a negative cohort size is supplied.  A negative cohort
    size is always a caller bug — counts can never be negative, so we
    fail fast rather than silently suppressing the cell."""


# ---- Core primitive --------------------------------------------------------


def suppress_below_k(value: T, n: int, *, k: int = K_ANONYMITY_THRESHOLD) -> T | None:
    """Return ``value`` if the backing cohort is at least ``k``, else ``None``.

    This is the k-anonymity gate for enterprise aggregate rendering.  A
    cell whose backing cohort size is under the floor leaks too much
    about individual users, so we replace it with ``None``.

    ``n`` must be non-negative; a negative cohort is always a caller bug
    (you can't have -3 users) and we raise rather than silently suppressing.

    ``k`` defaults to :data:`K_ANONYMITY_THRESHOLD` but is overridable for
    tests and for the rare scenario where a specific dashboard requires
    a stricter floor (never looser — there's no use case for k < 5 here).
    """
    if n < 0:
        raise InvalidCohortSizeError(
            f"cohort size n must be non-negative, got {n}"
        )
    if n < k:
        return None
    return value


# ---- Snapshot + wire types -------------------------------------------------


@dataclass(frozen=True)
class OrgEngagementSnapshot:
    """Raw aggregate counts for an org, prior to k-anonymity suppression.

    Populated from the k-anonymity-enforcing SQL views (which themselves
    gate on cohort size), but we re-apply :func:`suppress_below_k` at the
    render boundary as defense-in-depth — an SQL view change or a future
    direct-query path must not be able to leak a sub-k cell.

    Field semantics:
    - ``n_active_members_7d`` is the cohort size for both
      ``active_members_count_7d`` and ``tools_used_count_7d`` cells.
    - ``n_wellbeing_reporters`` is the cohort that responded to WHO-5
      this window, used for the ``wellbeing_index_mean`` cell.
    """

    org_id: str
    active_members_count_7d: int
    tools_used_count_7d: int
    wellbeing_index_mean: float
    n_active_members_7d: int
    n_wellbeing_reporters: int


@dataclass(frozen=True)
class OrgEngagement:
    """Wire-format engagement view for an org.  ``None`` on a field means
    the underlying cohort was sub-k and the cell is suppressed.  Clients
    must render suppressed cells as "insufficient data", not 0."""

    org_id: str
    active_members_7d: int | None
    tools_used_7d: int | None
    wellbeing_index: float | None


# ---- Rendering -------------------------------------------------------------


def build_org_engagement(snapshot: OrgEngagementSnapshot) -> OrgEngagement:
    """Apply the k-anonymity gate to each cell of the snapshot.

    This is the *only* place where un-suppressed counts become a wire
    response.  Every code path that produces :class:`OrgEngagement` goes
    through here.
    """
    return OrgEngagement(
        org_id=snapshot.org_id,
        active_members_7d=suppress_below_k(
            snapshot.active_members_count_7d,
            snapshot.n_active_members_7d,
        ),
        tools_used_7d=suppress_below_k(
            snapshot.tools_used_count_7d,
            snapshot.n_active_members_7d,
        ),
        wellbeing_index=suppress_below_k(
            snapshot.wellbeing_index_mean,
            snapshot.n_wellbeing_reporters,
        ),
    )


async def engagement_for_org(_org_id: str) -> OrgEngagement:
    """Stub — production implementation reads from the k-anonymity SQL
    view and calls :func:`build_org_engagement`.  Wired in the HTTP
    sprint once the repository layer exists."""
    raise NotImplementedError


__all__ = [
    "InvalidCohortSizeError",
    "K_ANONYMITY_THRESHOLD",
    "OrgEngagement",
    "OrgEngagementSnapshot",
    "build_org_engagement",
    "engagement_for_org",
    "suppress_below_k",
]

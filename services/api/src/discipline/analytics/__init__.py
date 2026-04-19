"""Analytics module — user insights & protectively-framed trajectories.

Boundary:
- User-facing: framed per rules P1–P6 (:mod:`.framing`).  Never shows raw scores
  without context; never uses language that could shame the user; separates trend
  from today's state.
- Aggregate / enterprise-facing: see :mod:`discipline.reports.enterprise` — the
  k-anonymity floor (k ≥ 5) is enforced at the SQL view layer, not here.
"""

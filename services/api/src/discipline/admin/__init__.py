"""Admin HTTP surfaces — compliance + operational tooling.

Every endpoint in this module is gated by :func:`discipline.shared.auth.require_admin`.
The module imports nothing from user-facing surfaces; it is safe to deploy
with admin endpoints disabled (by routing the ``/v1/admin`` path to a 404
at the edge).
"""

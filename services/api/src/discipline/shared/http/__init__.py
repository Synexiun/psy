"""Shared HTTP primitives — middleware, marker dependencies, shared clients.

Modules here are cross-cutting concerns that every router may compose
into its request pipeline: PHI boundary marking, egress-allowed HTTP
clients, tracing headers, etc.
"""

from .phi_boundary import PhiBoundaryMiddleware, mark_phi_boundary

__all__ = ["PhiBoundaryMiddleware", "mark_phi_boundary"]

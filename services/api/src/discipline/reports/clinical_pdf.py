"""Clinical PDF generator — reproducible, signed.

Reproducibility:
- Pinned font subset bundled with the service (no network font fetch).
- Fixed page dimensions, fixed metadata, deterministic byte order.
- The byte-identical output is tested in the `reports` fidelity suite — a change
  to any rendering module that shifts bytes fails CI and requires a version bump.

Signing:
- Ed25519 signature over the rendered byte stream, written as a PDF-level
  metadata entry; verification uses the published public key in
  Docs/Technicals/07_Security_Privacy.md §Report signing.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ClinicalReport:
    user_id: str
    window_start: datetime
    window_end: datetime
    locale: str
    version: str = "1.0.0"


async def render(report: ClinicalReport) -> bytes:
    """Stub.  Wire to the pinned PDF renderer in a later milestone."""
    raise NotImplementedError


__all__ = ["ClinicalReport", "render"]

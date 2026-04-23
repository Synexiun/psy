"""Signal module SQLAlchemy models.

Tables:
- ``signal_windows`` — ingested signal batches (hypertable candidate)
- ``state_estimates`` — ML state classifier outputs

See Docs/Technicals/02_Data_Model.md §3.3 for full schema.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from discipline.shared.models import Base


class SignalWindow(Base):
    """A batch of signal samples from a device window."""

    __tablename__ = "signal_windows"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    window_start: Mapped[datetime] = mapped_column(
        nullable=False,
        comment="Start of the signal window (UTC)",
    )
    window_end: Mapped[datetime] = mapped_column(
        nullable=False,
        comment="End of the signal window (UTC)",
    )
    source: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        comment="healthkit | health_connect | manual_checkin | watch",
    )
    samples_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="SHA-256 hex of canonical sample JSON for deduplication",
    )
    samples_json: Mapped[dict[str, object]] = mapped_column(
        JSONB,
        nullable=False,
        comment="Opaque sample payload — raw values never leave device in prod",
    )
    created_at: Mapped[datetime] = mapped_column(
        server_default=text("now()"),
        nullable=False,
    )


class StateEstimate(Base):
    """Output of the on-device (or server-fallback) state classifier."""

    __tablename__ = "state_estimates"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    state_label: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        comment="stable | rising_urge | peak_urge | post_urge | baseline",
    )
    confidence: Mapped[float] = mapped_column(
        nullable=False,
        comment="Classifier confidence 0.0–1.0",
    )
    model_version: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        comment="Model tag for reproducibility and audit",
    )
    features_json: Mapped[dict[str, object] | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Feature vector that produced this estimate (optional)",
    )
    inferred_at: Mapped[datetime] = mapped_column(
        nullable=False,
        comment="Wall-clock time the estimate was produced",
    )
    created_at: Mapped[datetime] = mapped_column(
        server_default=text("now()"),
        nullable=False,
    )

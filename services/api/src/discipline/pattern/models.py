"""Pattern module SQLAlchemy models.

Tables:
- ``patterns`` — detected behavioral patterns per user

See Docs/Technicals/02_Data_Model.md §3.7 for full schema.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from discipline.shared.models import Base


class Pattern(Base):
    """A detected behavioral pattern for a user."""

    __tablename__ = "patterns"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    pattern_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        comment="temporal | contextual | physiological | compound",
    )
    detector: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="Detector that produced this pattern",
    )
    confidence: Mapped[float] = mapped_column(
        nullable=False,
        comment="Detector confidence 0.0–1.0",
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Human-readable pattern summary",
    )
    metadata_json: Mapped[dict[str, object]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        comment="Structured detector output (peak hours, tags, thresholds, etc.)",
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="active",
        comment="active | dismissed | expired",
    )
    dismissed_at: Mapped[datetime | None] = mapped_column(
        nullable=True,
    )
    dismiss_reason: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        server_default=text("now()"),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=text("now()"),
        onupdate=text("now()"),
        nullable=False,
    )

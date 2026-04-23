"""Clinical module SQLAlchemy models.

Tables:
- ``relapse_events`` — user relapse reports

See Docs/Technicals/02_Data_Model.md §3.5 for full schema.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from discipline.shared.models import Base


class RelapseEvent(Base):
    """A user-reported relapse event."""

    __tablename__ = "relapse_events"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    occurred_at: Mapped[datetime] = mapped_column(
        nullable=False,
    )
    behavior: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
    )
    severity: Mapped[int] = mapped_column(
        nullable=False,
        comment="1–5 self-reported severity",
    )
    context_tags = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        comment="JSON array of context tags",
    )
    compassion_message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Deterministic compassion-first response copy",
    )
    reviewed: Mapped[bool] = mapped_column(
        nullable=False,
        default=False,
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(
        nullable=True,
    )
    reviewed_by: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        server_default=text("now()"),
        nullable=False,
    )

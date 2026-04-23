"""Resilience module SQLAlchemy models.

Tables:
- ``streak_states`` — user streak state (continuous + resilience)

See Docs/Technicals/02_Data_Model.md §3.8 for full schema.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String, text
from sqlalchemy.orm import Mapped, mapped_column

from discipline.shared.models import Base


class StreakStateModel(Base):
    """User streak state.

    ``resilience_days`` is monotonically non-decreasing per AGENTS.md
    Rule #3.  A DB trigger enforces this; application code must never
    attempt to decrement it.
    """

    __tablename__ = "streak_states"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    continuous_days: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
    )
    continuous_streak_start: Mapped[datetime | None] = mapped_column(
        nullable=True,
    )
    resilience_days: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
    )
    resilience_urges_handled_total: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
    )
    resilience_streak_start: Mapped[datetime] = mapped_column(
        server_default=text("now()"),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=text("now()"),
        onupdate=text("now()"),
        nullable=False,
    )

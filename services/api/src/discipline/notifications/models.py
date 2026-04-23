"""Notifications module SQLAlchemy models.

Tables:
- ``nudges`` — scheduled intervention nudges
- ``push_tokens`` — device push notification tokens

See Docs/Technicals/02_Data_Model.md for full schema.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String, text
from sqlalchemy.orm import Mapped, mapped_column

from discipline.shared.models import Base


class Nudge(Base):
    """A scheduled intervention nudge."""

    __tablename__ = "nudges"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    nudge_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        comment="check_in | tool_suggestion | crisis_follow_up | weekly_reflection",
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="scheduled",
        comment="scheduled | sent | dismissed | expired",
    )
    scheduled_at: Mapped[datetime] = mapped_column(
        nullable=False,
    )
    sent_at: Mapped[datetime | None] = mapped_column(
        nullable=True,
    )
    tool_variant: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )
    message_copy: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        server_default=text("now()"),
        nullable=False,
    )


class PushToken(Base):
    """Device push notification token."""

    __tablename__ = "push_tokens"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    platform: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        comment="ios | android | web",
    )
    token_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="SHA-256 of the raw push token",
    )
    token_encrypted: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
        comment="KMS-wrapped token ciphertext",
    )
    created_at: Mapped[datetime] = mapped_column(
        server_default=text("now()"),
        nullable=False,
    )
    last_valid_at: Mapped[datetime | None] = mapped_column(
        nullable=True,
    )

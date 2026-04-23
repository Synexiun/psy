"""Memory module SQLAlchemy models.

Tables:
- ``journals`` — user journal entries with encrypted body
- ``voice_sessions`` — voice session metadata + transcription state

See Docs/Technicals/02_Data_Model.md §3.6 for full schema.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from discipline.shared.models import Base


class Journal(Base):
    """User journal entry."""

    __tablename__ = "journals"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    body_encrypted: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="KMS-wrapped journal body ciphertext (base64)",
    )
    mood_score: Mapped[int | None] = mapped_column(
        nullable=True,
        comment="Optional 0–10 mood score attached at write time",
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


class VoiceSession(Base):
    """Voice session metadata."""

    __tablename__ = "voice_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="recording",
        comment="recording | uploaded | transcribed | failed",
    )
    duration_seconds: Mapped[int | None] = mapped_column(
        nullable=True,
    )
    s3_key: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
        comment="S3 object key for the voice blob",
    )
    transcription: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Whisper transcription text (stored encrypted at rest via SSE-S3)",
    )
    created_at: Mapped[datetime] = mapped_column(
        server_default=text("now()"),
        nullable=False,
    )
    finalized_at: Mapped[datetime | None] = mapped_column(
        nullable=True,
    )
    hard_delete_at: Mapped[datetime] = mapped_column(
        nullable=False,
        comment="72-hour hard-delete deadline per AGENTS.md Rule #7",
    )

"""Identity module SQLAlchemy models.

Tables:
- ``users`` — core user account (maps to Clerk external_id)
- ``user_profiles`` — clinical profile, PHI-isolated from users

See Docs/Technicals/02_Data_Model.md §3.1-3.2 for full schema.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String, text
from sqlalchemy.orm import Mapped, mapped_column

from discipline.shared.models import Base


class User(Base):
    """Core user account."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    external_id: Mapped[str] = mapped_column(
        String,
        unique=True,
        nullable=False,
        comment="Clerk user ID",
    )
    email_hash: Mapped[str] = mapped_column(
        String,
        nullable=False,
        comment="SHA-256 hex for lookup (not the raw email)",
    )
    email_encrypted: Mapped[str] = mapped_column(
        String,
        nullable=False,
        comment="KMS-wrapped email ciphertext (base64)",
    )
    handle: Mapped[str | None] = mapped_column(
        String,
        unique=True,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        server_default=text("now()"),
        nullable=False,
    )
    last_active_at: Mapped[datetime | None] = mapped_column(
        nullable=True,
    )
    timezone: Mapped[str] = mapped_column(
        String,
        nullable=False,
        default="UTC",
    )
    locale: Mapped[str] = mapped_column(
        String,
        nullable=False,
        default="en",
    )
    calendar_preference: Mapped[str] = mapped_column(
        String,
        nullable=False,
        default="gregorian",
    )
    digit_preference: Mapped[str] = mapped_column(
        String,
        nullable=False,
        default="auto",
    )
    app_lock_enabled: Mapped[bool] = mapped_column(
        nullable=False,
        default=False,
    )
    alt_icon_enabled: Mapped[bool] = mapped_column(
        nullable=False,
        default=False,
    )
    mfa_enrolled: Mapped[bool] = mapped_column(
        nullable=False,
        default=False,
    )
    consent_version: Mapped[str] = mapped_column(
        String,
        nullable=False,
        default="0.0.0",
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        nullable=True,
    )
    purge_scheduled_at: Mapped[datetime | None] = mapped_column(
        nullable=True,
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} external_id={self.external_id}>"


class UserProfile(Base):
    """Clinical profile — kept separate from users to isolate PHI access."""

    __tablename__ = "user_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    target_behaviors: Mapped[str] = mapped_column(
        String,
        nullable=False,
        default="",
        comment="Comma-separated enum: alcohol,cannabis,porn,binge_eating,doomscroll,custom",
    )
    baseline_severity: Mapped[int | None] = mapped_column(
        nullable=True,
        comment="1-10 self-rated",
    )
    clinical_referral: Mapped[bool] = mapped_column(
        nullable=False,
        default=False,
    )
    ema_frequency: Mapped[str] = mapped_column(
        String,
        nullable=False,
        default="twice_daily",
    )
    crisis_contact_json: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
        comment="KMS-wrapped JSON: name/phone/relationship",
    )
    local_hotline_country: Mapped[str] = mapped_column(
        String,
        nullable=False,
        default="US",
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=text("now()"),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<UserProfile user_id={self.user_id}>"

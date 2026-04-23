"""Compliance module SQLAlchemy models.

Tables:
- ``consents`` — user consent records with versioning
- ``quick_erase_requests`` — queued quick-erase jobs

See Docs/Technicals/02_Data_Model.md §3.10 for full schema.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String, text
from sqlalchemy.orm import Mapped, mapped_column

from discipline.shared.models import Base


class Consent(Base):
    """A user consent record."""

    __tablename__ = "consents"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    consent_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="terms_of_service | privacy_policy | clinical_data | marketing",
    )
    version: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        comment="Semantic version of the consent document",
    )
    granted_at: Mapped[datetime] = mapped_column(
        server_default=text("now()"),
        nullable=False,
    )
    ip_address_hash: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        comment="SHA-256 of the IP address at time of grant",
    )


class QuickEraseRequest(Base):
    """Queued quick-erase request."""

    __tablename__ = "quick_erase_requests"

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
        default="pending",
        comment="pending | processing | completed | failed",
    )
    requested_at: Mapped[datetime] = mapped_column(
        server_default=text("now()"),
        nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        nullable=True,
    )
    error_detail: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
    )

"""Enterprise module SQLAlchemy models.

Tables:
- ``organizations`` — B2B customer orgs
- ``clinician_links`` — clinician-patient consent links

See Docs/Technicals/02_Data_Model.md §3.9 for full schema.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String, text
from sqlalchemy.orm import Mapped, mapped_column

from discipline.shared.models import Base


class Organization(Base):
    """B2B customer organization."""

    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    slug: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        unique=True,
        index=True,
    )
    tier: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="standard",
        comment="pilot | standard | enterprise",
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="active",
        comment="active | suspended | archived",
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


class ClinicianLink(Base):
    """Clinician-patient consent link within an organization."""

    __tablename__ = "clinician_links"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    org_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    clinician_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    patient_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="pending",
        comment="pending | active | revoked",
    )
    invited_at: Mapped[datetime] = mapped_column(
        server_default=text("now()"),
        nullable=False,
    )
    consented_at: Mapped[datetime | None] = mapped_column(
        nullable=True,
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
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

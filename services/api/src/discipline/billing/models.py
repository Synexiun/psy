"""Billing module SQLAlchemy models.

Tables:
- ``subscriptions`` — user subscription state

See Docs/Technicals/02_Data_Model.md §3.2 for full schema.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String, text
from sqlalchemy.orm import Mapped, mapped_column

from discipline.shared.models import Base


class Subscription(Base):
    """User subscription record."""

    __tablename__ = "subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        unique=True,
        comment="One active subscription per user",
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="active",
        comment="active | canceled | expired | grace_period",
    )
    tier: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        comment="free | plus | pro | enterprise",
    )
    provider: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        comment="stripe | apple_iap | google_iap",
    )
    provider_subscription_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="External provider subscription identifier",
    )
    current_period_start: Mapped[datetime] = mapped_column(
        nullable=False,
        comment="Start of current billing period (UTC)",
    )
    current_period_end: Mapped[datetime] = mapped_column(
        nullable=False,
        comment="End of current billing period (UTC)",
    )
    canceled_at: Mapped[datetime | None] = mapped_column(
        nullable=True,
    )
    cancel_reason: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Optional free-text reason for cancellation",
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

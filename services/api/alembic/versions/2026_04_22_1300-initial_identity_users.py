"""initial identity users

Revision ID: 001
Revises:
Create Date: 2026-04-22 13:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("external_id", sa.String(), nullable=False, comment="Clerk user ID"),
        sa.Column("email_hash", sa.String(), nullable=False, comment="SHA-256 hex for lookup"),
        sa.Column("email_encrypted", sa.String(), nullable=False, comment="KMS-wrapped email ciphertext"),
        sa.Column("handle", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("last_active_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("timezone", sa.String(), nullable=False, server_default="UTC"),
        sa.Column("locale", sa.String(), nullable=False, server_default="en"),
        sa.Column("calendar_preference", sa.String(), nullable=False, server_default="gregorian"),
        sa.Column("digit_preference", sa.String(), nullable=False, server_default="auto"),
        sa.Column("app_lock_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("alt_icon_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("mfa_enrolled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("consent_version", sa.String(), nullable=False, server_default="0.0.0"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("purge_scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("external_id"),
        sa.UniqueConstraint("handle"),
    )
    op.create_index("idx_users_external", "users", ["external_id"], unique=False)
    op.create_index("idx_users_email_hash", "users", ["email_hash"], unique=False)
    op.create_index(
        "idx_users_deleted",
        "users",
        ["deleted_at"],
        unique=False,
        postgresql_where=sa.text("deleted_at IS NOT NULL"),
    )
    op.create_index("idx_users_locale", "users", ["locale"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_users_locale", table_name="users")
    op.drop_index("idx_users_deleted", table_name="users")
    op.drop_index("idx_users_email_hash", table_name="users")
    op.drop_index("idx_users_external", table_name="users")
    op.drop_table("users")

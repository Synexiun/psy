"""add nudges and push_tokens

Revision ID: 008
Revises: 007
Create Date: 2026-04-22 20:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "008"
down_revision: str | None = "007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "nudges",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False, comment="Foreign key to users.id"),
        sa.Column("nudge_type", sa.String(32), nullable=False, comment="check_in | tool_suggestion | crisis_follow_up | weekly_reflection"),
        sa.Column("status", sa.String(32), nullable=False, server_default="scheduled", comment="scheduled | sent | dismissed | expired"),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("tool_variant", sa.String(64), nullable=True),
        sa.Column("message_copy", sa.String(512), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_nudges_user_id", "nudges", ["user_id"], unique=False)
    op.create_index("idx_nudges_scheduled_at", "nudges", ["scheduled_at"], unique=False)
    op.create_index("idx_nudges_status", "nudges", ["status"], unique=False)

    op.create_table(
        "push_tokens",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False, comment="Foreign key to users.id"),
        sa.Column("platform", sa.String(16), nullable=False, comment="ios | android | web"),
        sa.Column("token_hash", sa.String(64), nullable=False, comment="SHA-256 of the raw push token"),
        sa.Column("token_encrypted", sa.String(512), nullable=False, comment="KMS-wrapped token ciphertext"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("last_valid_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_push_tokens_user_id", "push_tokens", ["user_id"], unique=False)
    op.create_index("idx_push_tokens_platform", "push_tokens", ["platform"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_push_tokens_platform", table_name="push_tokens")
    op.drop_index("idx_push_tokens_user_id", table_name="push_tokens")
    op.drop_table("push_tokens")
    op.drop_index("idx_nudges_status", table_name="nudges")
    op.drop_index("idx_nudges_scheduled_at", table_name="nudges")
    op.drop_index("idx_nudges_user_id", table_name="nudges")
    op.drop_table("nudges")

"""add relapse_events

Revision ID: 007
Revises: 006
Create Date: 2026-04-22 19:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "007"
down_revision: str | None = "006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "relapse_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False, comment="Foreign key to users.id"),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("behavior", sa.String(128), nullable=False),
        sa.Column("severity", sa.SmallInteger(), nullable=False, comment="1–5 self-reported severity"),
        sa.Column("context_tags", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("compassion_message", sa.Text(), nullable=False, comment="Deterministic compassion-first response copy"),
        sa.Column("reviewed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewed_by", sa.String(128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_relapse_events_user_id", "relapse_events", ["user_id"], unique=False)
    op.create_index("idx_relapse_events_occurred_at", "relapse_events", ["occurred_at"], unique=False)
    op.create_index("idx_relapse_events_reviewed", "relapse_events", ["reviewed"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_relapse_events_reviewed", table_name="relapse_events")
    op.drop_index("idx_relapse_events_occurred_at", table_name="relapse_events")
    op.drop_index("idx_relapse_events_user_id", table_name="relapse_events")
    op.drop_table("relapse_events")

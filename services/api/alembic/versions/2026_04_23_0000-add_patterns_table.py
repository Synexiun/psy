"""add patterns table

Revision ID: 009
Revises: 008
Create Date: 2026-04-23 00:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "009"
down_revision: str | None = "008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "patterns",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False, comment="Foreign key to users.id"),
        sa.Column("pattern_type", sa.String(32), nullable=False, comment="temporal | contextual | physiological | compound"),
        sa.Column("detector", sa.String(64), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("metadata_json", sa.dialects.postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("status", sa.String(32), nullable=False, server_default="active", comment="active | dismissed | expired"),
        sa.Column("dismissed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("dismiss_reason", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_patterns_user_id", "patterns", ["user_id"], unique=False)
    op.create_index("idx_patterns_status", "patterns", ["status"], unique=False)
    op.create_index("idx_patterns_type", "patterns", ["pattern_type"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_patterns_type", table_name="patterns")
    op.drop_index("idx_patterns_status", table_name="patterns")
    op.drop_index("idx_patterns_user_id", table_name="patterns")
    op.drop_table("patterns")

"""add streak_states

Revision ID: 006
Revises: 005
Create Date: 2026-04-22 18:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "006"
down_revision: str | None = "005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "streak_states",
        sa.Column("user_id", sa.Uuid(), nullable=False, comment="Foreign key to users.id"),
        sa.Column("continuous_days", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("continuous_streak_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resilience_days", sa.Integer(), nullable=False, server_default="0", comment="Monotonically non-decreasing per AGENTS.md Rule #3"),
        sa.Column("resilience_urges_handled_total", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("resilience_streak_start", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id"),
    )
    op.create_index("idx_streak_states_user_id", "streak_states", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_streak_states_user_id", table_name="streak_states")
    op.drop_table("streak_states")

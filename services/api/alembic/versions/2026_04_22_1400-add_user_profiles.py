"""add user_profiles

Revision ID: 002
Revises: 001
Create Date: 2026-04-22 14:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: str | None = "001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "user_profiles",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("target_behaviors", sa.String(), nullable=False, server_default=""),
        sa.Column("baseline_severity", sa.SmallInteger(), nullable=True),
        sa.Column("clinical_referral", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("ema_frequency", sa.String(), nullable=False, server_default="twice_daily"),
        sa.Column("crisis_contact_json", sa.String(), nullable=True),
        sa.Column("local_hotline_country", sa.String(), nullable=False, server_default="US"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id"),
    )


def downgrade() -> None:
    op.drop_table("user_profiles")

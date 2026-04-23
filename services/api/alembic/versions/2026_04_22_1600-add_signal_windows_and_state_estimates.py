"""add signal_windows and state_estimates

Revision ID: 004
Revises: 003
Create Date: 2026-04-22 16:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "004"
down_revision: str | None = "003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "signal_windows",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False, comment="Foreign key to users.id"),
        sa.Column("window_start", sa.DateTime(timezone=True), nullable=False, comment="Start of the signal window (UTC)"),
        sa.Column("window_end", sa.DateTime(timezone=True), nullable=False, comment="End of the signal window (UTC)"),
        sa.Column("source", sa.String(32), nullable=False, comment="healthkit | health_connect | manual_checkin | watch"),
        sa.Column("samples_hash", sa.String(64), nullable=False, comment="SHA-256 hex of canonical sample JSON for deduplication"),
        sa.Column("samples_json", postgresql.JSONB(), nullable=False, comment="Opaque sample payload"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_signal_windows_user_id", "signal_windows", ["user_id"], unique=False)
    op.create_index("idx_signal_windows_source", "signal_windows", ["source"], unique=False)
    op.create_index("idx_signal_windows_created_at", "signal_windows", ["created_at"], unique=False)

    op.create_table(
        "state_estimates",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False, comment="Foreign key to users.id"),
        sa.Column("state_label", sa.String(32), nullable=False, comment="stable | rising_urge | peak_urge | post_urge | baseline"),
        sa.Column("confidence", sa.Float(), nullable=False, comment="Classifier confidence 0.0–1.0"),
        sa.Column("model_version", sa.String(32), nullable=False, comment="Model tag for reproducibility and audit"),
        sa.Column("features_json", postgresql.JSONB(), nullable=True, comment="Feature vector that produced this estimate (optional)"),
        sa.Column("inferred_at", sa.DateTime(timezone=True), nullable=False, comment="Wall-clock time the estimate was produced"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_state_estimates_user_id", "state_estimates", ["user_id"], unique=False)
    op.create_index("idx_state_estimates_inferred_at", "state_estimates", ["inferred_at"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_state_estimates_inferred_at", table_name="state_estimates")
    op.drop_index("idx_state_estimates_user_id", table_name="state_estimates")
    op.drop_table("state_estimates")
    op.drop_index("idx_signal_windows_created_at", table_name="signal_windows")
    op.drop_index("idx_signal_windows_source", table_name="signal_windows")
    op.drop_index("idx_signal_windows_user_id", table_name="signal_windows")
    op.drop_table("signal_windows")

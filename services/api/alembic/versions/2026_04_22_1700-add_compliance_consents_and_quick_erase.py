"""add compliance consents and quick_erase

Revision ID: 005
Revises: 004
Create Date: 2026-04-22 17:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "005"
down_revision: str | None = "004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "consents",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False, comment="Foreign key to users.id"),
        sa.Column("consent_type", sa.String(64), nullable=False, comment="terms_of_service | privacy_policy | clinical_data | marketing"),
        sa.Column("version", sa.String(32), nullable=False, comment="Semantic version of the consent document"),
        sa.Column("granted_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("ip_address_hash", sa.String(64), nullable=True, comment="SHA-256 of the IP address at time of grant"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_consents_user_id", "consents", ["user_id"], unique=False)
    op.create_index("idx_consents_user_type", "consents", ["user_id", "consent_type"], unique=False)
    op.create_index("idx_consents_granted_at", "consents", ["granted_at"], unique=False)

    op.create_table(
        "quick_erase_requests",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False, comment="Foreign key to users.id"),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending", comment="pending | processing | completed | failed"),
        sa.Column("requested_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_detail", sa.String(512), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_quick_erase_user_id", "quick_erase_requests", ["user_id"], unique=False)
    op.create_index("idx_quick_erase_status", "quick_erase_requests", ["status"], unique=False)
    op.create_index("idx_quick_erase_requested_at", "quick_erase_requests", ["requested_at"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_quick_erase_requested_at", table_name="quick_erase_requests")
    op.drop_index("idx_quick_erase_status", table_name="quick_erase_requests")
    op.drop_index("idx_quick_erase_user_id", table_name="quick_erase_requests")
    op.drop_table("quick_erase_requests")
    op.drop_index("idx_consents_granted_at", table_name="consents")
    op.drop_index("idx_consents_user_type", table_name="consents")
    op.drop_index("idx_consents_user_id", table_name="consents")
    op.drop_table("consents")

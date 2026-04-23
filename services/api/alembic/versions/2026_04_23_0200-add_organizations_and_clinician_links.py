"""add organizations and clinician_links

Revision ID: 011
Revises: 010
Create Date: 2026-04-23 02:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "011"
down_revision: str | None = "010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "organizations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(128), nullable=False, unique=True),
        sa.Column("tier", sa.String(32), nullable=False, server_default="standard", comment="pilot | standard | enterprise"),
        sa.Column("status", sa.String(32), nullable=False, server_default="active", comment="active | suspended | archived"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_organizations_slug", "organizations", ["slug"], unique=True)
    op.create_index("idx_organizations_status", "organizations", ["status"], unique=False)

    op.create_table(
        "clinician_links",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("org_id", sa.Uuid(), nullable=False, comment="Foreign key to organizations.id"),
        sa.Column("clinician_user_id", sa.Uuid(), nullable=False, comment="Foreign key to users.id"),
        sa.Column("patient_user_id", sa.Uuid(), nullable=False, comment="Foreign key to users.id"),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending", comment="pending | active | revoked"),
        sa.Column("invited_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("consented_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["clinician_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["patient_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_clinician_links_org_id", "clinician_links", ["org_id"], unique=False)
    op.create_index("idx_clinician_links_clinician", "clinician_links", ["clinician_user_id"], unique=False)
    op.create_index("idx_clinician_links_patient", "clinician_links", ["patient_user_id"], unique=False)
    op.create_index("idx_clinician_links_status", "clinician_links", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_clinician_links_status", table_name="clinician_links")
    op.drop_index("idx_clinician_links_patient", table_name="clinician_links")
    op.drop_index("idx_clinician_links_clinician", table_name="clinician_links")
    op.drop_index("idx_clinician_links_org_id", table_name="clinician_links")
    op.drop_table("clinician_links")
    op.drop_index("idx_organizations_status", table_name="organizations")
    op.drop_index("idx_organizations_slug", table_name="organizations")
    op.drop_table("organizations")

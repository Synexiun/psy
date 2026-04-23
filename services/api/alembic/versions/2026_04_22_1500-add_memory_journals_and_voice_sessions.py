"""add memory journals and voice_sessions

Revision ID: 003
Revises: 002
Create Date: 2026-04-22 15:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "003"
down_revision: str | None = "002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "journals",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False, comment="Foreign key to users.id"),
        sa.Column("title", sa.String(255), nullable=True),
        sa.Column("body_encrypted", sa.Text(), nullable=False, comment="KMS-wrapped journal body ciphertext (base64)"),
        sa.Column("mood_score", sa.SmallInteger(), nullable=True, comment="Optional 0–10 mood score attached at write time"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_journals_user_id", "journals", ["user_id"], unique=False)
    op.create_index("idx_journals_created_at", "journals", ["created_at"], unique=False)

    op.create_table(
        "voice_sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False, comment="Foreign key to users.id"),
        sa.Column("status", sa.String(32), nullable=False, server_default="recording", comment="recording | uploaded | transcribed | failed"),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("s3_key", sa.String(512), nullable=True, comment="S3 object key for the voice blob"),
        sa.Column("transcription", sa.Text(), nullable=True, comment="Whisper transcription text (stored encrypted at rest via SSE-S3)"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("finalized_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("hard_delete_at", sa.DateTime(timezone=True), nullable=False, comment="72-hour hard-delete deadline per AGENTS.md Rule #7"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_voice_sessions_user_id", "voice_sessions", ["user_id"], unique=False)
    op.create_index("idx_voice_sessions_hard_delete_at", "voice_sessions", ["hard_delete_at"], unique=False)
    op.create_index(
        "idx_voice_sessions_status",
        "voice_sessions",
        ["status"],
        unique=False,
        postgresql_where=sa.text("status IN ('recording', 'uploaded')"),
    )


def downgrade() -> None:
    op.drop_index("idx_voice_sessions_status", table_name="voice_sessions")
    op.drop_index("idx_voice_sessions_hard_delete_at", table_name="voice_sessions")
    op.drop_index("idx_voice_sessions_user_id", table_name="voice_sessions")
    op.drop_table("voice_sessions")
    op.drop_index("idx_journals_created_at", table_name="journals")
    op.drop_index("idx_journals_user_id", table_name="journals")
    op.drop_table("journals")

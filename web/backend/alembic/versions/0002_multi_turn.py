"""multi turn conversation tables

Revision ID: 0002_multi_turn
Revises: 0001_initial
Create Date: 2026-04-26
"""

import sqlalchemy as sa
from alembic import op

revision = "0002_multi_turn"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "session_messages",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("session_id", sa.String(), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("kind", sa.String(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["gen_sessions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_session_messages_session_id", "session_messages", ["session_id"])
    op.create_index("ix_session_messages_session_created", "session_messages", ["session_id", "created_at"])

    op.create_table(
        "parse_revisions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("session_id", sa.String(), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("parsed_data", sa.Text(), nullable=False),
        sa.Column("missing_info", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["gen_sessions.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_id", "revision", name="uq_parse_revisions_session_revision"),
    )
    op.create_index("ix_parse_revisions_session_id", "parse_revisions", ["session_id"])


def downgrade() -> None:
    op.drop_index("ix_parse_revisions_session_id", table_name="parse_revisions")
    op.drop_table("parse_revisions")
    op.drop_index("ix_session_messages_session_created", table_name="session_messages")
    op.drop_index("ix_session_messages_session_id", table_name="session_messages")
    op.drop_table("session_messages")

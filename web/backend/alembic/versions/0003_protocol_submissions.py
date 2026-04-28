"""protocol submissions table

Revision ID: 0003_protocol_submissions
Revises: 0002_multi_turn
Create Date: 2026-04-27
"""

import sqlalchemy as sa
from alembic import op

revision = "0003_protocol_submissions"
down_revision = "0002_multi_turn"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "protocol_submissions",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("session_id", sa.String(), nullable=True),
        sa.Column("submitter_id", sa.Integer(), nullable=False),
        sa.Column("source_type", sa.String(), nullable=False),
        sa.Column("raw_content", sa.Text(), nullable=False),
        sa.Column("filename", sa.String(), nullable=True),
        sa.Column("brand", sa.String(), nullable=True),
        sa.Column("model_name", sa.String(), nullable=True),
        sa.Column("extracted_protocol", sa.Text(), nullable=True),
        sa.Column("review_status", sa.String(), nullable=False, server_default="pending_review"),
        sa.Column("reviewer_id", sa.Integer(), nullable=True),
        sa.Column("reviewer_note", sa.Text(), nullable=True),
        sa.Column("approved_protocol_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.ForeignKeyConstraint(["approved_protocol_id"], ["protocols.id"]),
        sa.ForeignKeyConstraint(["reviewer_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["session_id"], ["gen_sessions.id"]),
        sa.ForeignKeyConstraint(["submitter_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_protocol_submissions_session_id", "protocol_submissions", ["session_id"])


def downgrade() -> None:
    op.drop_index("ix_protocol_submissions_session_id", table_name="protocol_submissions")
    op.drop_table("protocol_submissions")

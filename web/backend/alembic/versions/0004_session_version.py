"""gen_sessions optimistic-lock version column

Revision ID: 0004_session_version
Revises: 0003_protocol_submissions
Create Date: 2026-04-27
"""

import sqlalchemy as sa
from alembic import op

revision = "0004_session_version"
down_revision = "0003_protocol_submissions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "gen_sessions",
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
    )


def downgrade() -> None:
    op.drop_column("gen_sessions", "version")

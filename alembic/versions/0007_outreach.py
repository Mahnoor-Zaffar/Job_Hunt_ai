"""Create outreach table for cold email tracking

Revision ID: 0007_outreach
Revises: 0006_add_missing_app_cols
Create Date: 2026-07-30

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0007_outreach"
down_revision: str | None = "0006_add_missing_app_cols"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "outreach",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("application_id", sa.Uuid(), nullable=True),
        sa.Column("job_id", sa.Uuid(), nullable=False),
        sa.Column("recipient_email", sa.String(255), nullable=False),
        sa.Column("recipient_name", sa.String(255), nullable=True),
        sa.Column("subject", sa.String(500), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("sent_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"],),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"],),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"],),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_outreach_user_id", "outreach", ["user_id"])
    op.create_index("ix_outreach_status", "outreach", ["status"])


def downgrade() -> None:
    op.drop_table("outreach")

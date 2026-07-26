"""Add missing rejection_reason and follow_up_at columns

Revision ID: 0006_add_missing_app_cols
Revises: 0005_career_profile
Create Date: 2026-07-26

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0006_add_missing_app_cols"
down_revision: str | None = "0005_career_profile"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("applications", sa.Column("rejection_reason", sa.Text(), nullable=True))
    op.add_column("applications", sa.Column("follow_up_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("applications", "follow_up_at")
    op.drop_column("applications", "rejection_reason")

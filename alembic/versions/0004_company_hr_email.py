"""Add HR email fields to companies + auto_watched to watchlists

Revision ID: 0004_company_hr_email
Revises: 0003_domain_tables
Create Date: 2026-07-26

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0004_company_hr_email"
down_revision: str | None = "0003_domain_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("companies", sa.Column("hr_email", sa.String(255), nullable=True))
    op.add_column("companies", sa.Column("hr_email_confidence", sa.Integer(), nullable=True))
    op.add_column("companies", sa.Column("hr_email_source", sa.String(30), nullable=True))
    op.add_column("companies", sa.Column("hr_email_verified_at", sa.DateTime(), nullable=True))
    op.add_column(
        "company_watchlists", sa.Column("auto_watched", sa.Boolean(), nullable=False, server_default="false")
    )


def downgrade() -> None:
    op.drop_column("company_watchlists", "auto_watched")
    op.drop_column("companies", "hr_email_verified_at")
    op.drop_column("companies", "hr_email_source")
    op.drop_column("companies", "hr_email_confidence")
    op.drop_column("companies", "hr_email")

"""Create career_profiles table for personalized job ranking

Revision ID: 0005_career_profile
Revises: 0004_company_hr_email
Create Date: 2026-07-26

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0005_career_profile"
down_revision: str | None = "0004_company_hr_email"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "career_profiles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("skills", sa.ARRAY(sa.String()), nullable=True),
        sa.Column("experience_level", sa.String(20), nullable=False, server_default="mid"),
        sa.Column("years_experience", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("target_roles", sa.ARRAY(sa.String()), nullable=True),
        sa.Column("preferred_locations", sa.ARRAY(sa.String()), nullable=True),
        sa.Column("remote_preference", sa.String(20), nullable=False, server_default="no_preference"),
        sa.Column("preferred_salary_min", sa.Float(), nullable=True),
        sa.Column("preferred_companies", sa.ARRAY(sa.String()), nullable=True),
        sa.Column("tech_stack", sa.ARRAY(sa.String()), nullable=True),
        sa.Column("learning_goals", sa.ARRAY(sa.String()), nullable=True),
        sa.Column("resume_text", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"],),
    )
    op.create_index("ix_career_profiles_user_id", "career_profiles", ["user_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_career_profiles_user_id", table_name="career_profiles")
    op.drop_table("career_profiles")

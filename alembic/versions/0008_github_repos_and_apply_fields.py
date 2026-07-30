"""Add github_repos table and application auto-apply fields

Revision ID: 0008_github_repos_and_apply_fields
Revises: 0007_outreach
Create Date: 2026-07-30

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0008_github_repos_and_apply_fields"
down_revision: str | None = "0007_outreach"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "github_repos",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("repo_name", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("language", sa.String(100), nullable=True),
        sa.Column("topics", sa.ARRAY(sa.String()), nullable=True),
        sa.Column("readme_text", sa.Text(), nullable=True),
        sa.Column("stars", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("forks", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
    )
    op.create_index("ix_github_repos_user_id", "github_repos", ["user_id"])
    op.create_index("ix_github_repos_full_name", "github_repos", ["full_name"], unique=True)

    op.add_column("applications", sa.Column("cover_letter_text", sa.Text(), nullable=True))
    op.add_column("applications", sa.Column("matched_github_repo", sa.String(500), nullable=True))
    op.add_column("applications", sa.Column("before_screenshot", sa.String(500), nullable=True))
    op.add_column("applications", sa.Column("after_screenshot", sa.String(500), nullable=True))
    op.add_column("applications", sa.Column("is_auto_generated", sa.Boolean(), nullable=False, server_default="false"))


def downgrade() -> None:
    op.drop_column("applications", "is_auto_generated")
    op.drop_column("applications", "after_screenshot")
    op.drop_column("applications", "before_screenshot")
    op.drop_column("applications", "matched_github_repo")
    op.drop_column("applications", "cover_letter_text")
    op.drop_index("ix_github_repos_full_name", table_name="github_repos")
    op.drop_index("ix_github_repos_user_id", table_name="github_repos")
    op.drop_table("github_repos")

"""create all domain tables

Revision ID: 0003_domain_tables
Revises: 0002_create_jobs_table
Create Date: 2026-07-15

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0003_domain_tables"
down_revision: str | None = "0002_create_jobs_table"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Company
    op.create_table(
        "companies",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("website", sa.String(500), nullable=True),
        sa.Column("logo_url", sa.String(500), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("industry", sa.String(100), nullable=True),
        sa.Column("size", sa.String(50), nullable=True),
        sa.Column("headquarters", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_companies_name", "companies", ["name"], unique=True)

    # Resume
    op.create_table(
        "resumes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("file_path", sa.String(500), nullable=False),
        sa.Column("file_type", sa.String(20), nullable=False),
        sa.Column("parsed_text", sa.Text(), nullable=True),
        sa.Column("extracted_skills", sa.JSON(), nullable=True),
        sa.Column("total_experience_years", sa.Integer(), nullable=True),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_resumes_user_id", "resumes", ["user_id"])

    # ResumeVersion
    op.create_table(
        "resume_versions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("resume_id", sa.Uuid(), sa.ForeignKey("resumes.id"), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("file_path", sa.String(500), nullable=False),
        sa.Column("change_summary", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_resume_versions_resume_id", "resume_versions", ["resume_id"])

    # Application
    op.create_table(
        "applications",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("job_id", sa.Uuid(), sa.ForeignKey("jobs.id"), nullable=False),
        sa.Column("resume_id", sa.Uuid(), sa.ForeignKey("resumes.id"), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="draft"),
        sa.Column("applied_at", sa.DateTime(), nullable=True),
        sa.Column("cover_letter", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("match_score", sa.Float(), nullable=True),
        sa.Column("interview_date", sa.DateTime(), nullable=True),
        sa.Column("feedback", sa.Text(), nullable=True),
        sa.Column("is_submitted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_applications_user_id", "applications", ["user_id"])
    op.create_index("ix_applications_job_id", "applications", ["job_id"])
    op.create_index("ix_applications_status", "applications", ["status"])

    # Technology
    op.create_table(
        "technologies",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("category", sa.String(50), nullable=True),
        sa.Column("version", sa.String(50), nullable=True),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_technologies_name", "technologies", ["name"], unique=True)

    # JobTechnology (association table)
    op.create_table(
        "job_technologies",
        sa.Column(
            "job_id", sa.Uuid(), sa.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "technology_id",
            sa.Uuid(),
            sa.ForeignKey("technologies.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("job_id", "technology_id"),
    )

    # CompanyWatchlist
    op.create_table(
        "company_watchlists",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("company_name", sa.String(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("notify_on_new_jobs", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_company_watchlists_user_id", "company_watchlists", ["user_id"])
    op.create_index("ix_company_watchlists_company_name", "company_watchlists", ["company_name"])

    # Notification
    op.create_table(
        "notifications",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("read_at", sa.DateTime(), nullable=True),
        sa.Column("job_id", sa.Uuid(), sa.ForeignKey("jobs.id"), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("sent_via", sa.String(20), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])

    # ATSPlatform
    op.create_table(
        "ats_platforms",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(50), nullable=False),
        sa.Column("display_name", sa.String(100), nullable=False),
        sa.Column("base_url_pattern", sa.String(500), nullable=True),
        sa.Column("api_base_url", sa.String(500), nullable=True),
        sa.Column("adapter_module", sa.String(255), nullable=False),
        sa.Column("adapter_class", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("requires_api_key", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("supports_json_api", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ats_platforms_name", "ats_platforms", ["name"], unique=True)

    # Location
    op.create_table(
        "locations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("city", sa.String(100), nullable=False),
        sa.Column("country", sa.String(100), nullable=False),
        sa.Column("region", sa.String(100), nullable=True),
        sa.Column("country_code", sa.String(5), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("is_supported", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_remote", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_locations_city", "locations", ["city"])
    op.create_index("ix_locations_country", "locations", ["country"])

    # ScrapeLog
    op.create_table(
        "scrape_logs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("source", sa.String(50), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="running"),
        sa.Column("jobs_discovered", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("jobs_new", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("jobs_duplicate", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("jobs_skipped", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("duration_seconds", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_scrape_logs_source", "scrape_logs", ["source"])

    # Settings
    op.create_table(
        "settings",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("key", sa.String(100), nullable=False),
        sa.Column("value", sa.Text(), nullable=True),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("is_encrypted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_settings_user_id", "settings", ["user_id"])
    op.create_index("ix_settings_key", "settings", ["key"])

    # Add remote_type and company_id columns to existing jobs table
    op.add_column(
        "jobs", sa.Column("remote_type", sa.String(20), nullable=False, server_default="onsite")
    )
    op.add_column(
        "jobs", sa.Column("company_id", sa.Uuid(), sa.ForeignKey("companies.id"), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("jobs", "company_id")
    op.drop_column("jobs", "remote_type")
    op.drop_table("settings")
    op.drop_table("scrape_logs")
    op.drop_table("locations")
    op.drop_table("ats_platforms")
    op.drop_table("notifications")
    op.drop_table("company_watchlists")
    op.drop_table("job_technologies")
    op.drop_table("technologies")
    op.drop_table("applications")
    op.drop_table("resume_versions")
    op.drop_table("resumes")
    op.drop_table("companies")

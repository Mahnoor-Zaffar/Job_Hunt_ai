import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import BaseModel


class Job(BaseModel):
    __tablename__ = "jobs"

    title: Mapped[str] = mapped_column(String(255), index=True)
    company: Mapped[str] = mapped_column(String(255), index=True)
    company_url: Mapped[str | None] = mapped_column(String(500))
    company_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("companies.id"), nullable=True)

    location: Mapped[str] = mapped_column(String(255))
    city: Mapped[str | None] = mapped_column(String(100))
    country: Mapped[str | None] = mapped_column(String(100))
    is_remote: Mapped[bool] = mapped_column(Boolean, default=False)
    remote_type: Mapped[str] = mapped_column(String(20), default="onsite")

    description: Mapped[str | None] = mapped_column(Text)
    requirements: Mapped[str | None] = mapped_column(Text)

    url: Mapped[str] = mapped_column(String(2048))
    apply_url: Mapped[str | None] = mapped_column(String(2048))

    source: Mapped[str] = mapped_column(String(50), index=True)
    source_id: Mapped[str] = mapped_column(String(255))

    salary_min: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    salary_max: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    currency: Mapped[str | None] = mapped_column(String(10))

    employment_type: Mapped[str | None] = mapped_column(String(50))
    experience_level: Mapped[str | None] = mapped_column(String(50))

    skills: Mapped[list[str] | None] = mapped_column(JSON)

    posted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False))

    fingerprint: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(20), default="active")

    raw_data: Mapped[dict[str, Any] | None] = mapped_column(JSON)

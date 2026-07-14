from datetime import datetime
from decimal import Decimal

from backend.schemas.base import BaseSchema, TimestampSchema


class JobResponse(TimestampSchema):
    title: str
    company: str
    company_url: str | None = None
    location: str
    city: str | None = None
    country: str | None = None
    is_remote: bool = False
    description: str | None = None
    requirements: str | None = None
    url: str
    apply_url: str | None = None
    source: str
    source_id: str
    salary_min: Decimal | None = None
    salary_max: Decimal | None = None
    currency: str | None = None
    employment_type: str | None = None
    experience_level: str | None = None
    skills: list[str] | None = None
    posted_at: datetime | None = None
    expires_at: datetime | None = None
    fingerprint: str
    status: str = "active"


class JobSearchParams(BaseSchema):
    title: str | None = None
    company: str | None = None
    location: str | None = None
    city: str | None = None
    country: str | None = None
    is_remote: bool | None = None
    source: str | None = None
    employment_type: str | None = None
    experience_level: str | None = None
    salary_min: Decimal | None = None
    salary_max: Decimal | None = None
    status: str | None = None
    skills: str | None = None
    page: int = 1
    per_page: int = 50

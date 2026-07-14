from datetime import datetime
from typing import Literal

from backend.schemas.base import BaseSchema

RemoteType = Literal["remote", "hybrid", "onsite"]


class RawJob(BaseSchema):
    """Raw job data as extracted from a source before any cleaning."""

    title: str
    company: str
    company_url: str | None = None
    location: str | None = None
    description: str | None = None
    url: str
    apply_url: str | None = None
    source: str
    source_id: str
    salary_min: float | None = None
    salary_max: float | None = None
    currency: str | None = None
    employment_type: str | None = None
    experience_level: str | None = None
    skills: list[str] | None = None
    requirements: str | None = None
    posted_at: datetime | None = None
    expires_at: datetime | None = None
    remote_type: RemoteType = "onsite"
    is_remote: bool = False
    city: str | None = None
    country: str | None = None


class NormalizedJob(BaseSchema):
    """Canonical job representation after normalisation, ready for storage.

    Every scraper produces this same type regardless of source format.
    No downstream consumer should need to know where the job originated.
    """

    title: str
    company: str
    company_url: str | None = None
    location: str
    description: str | None = None
    url: str
    apply_url: str | None = None
    source: str
    source_id: str
    salary_min: float | None = None
    salary_max: float | None = None
    currency: str | None = None
    employment_type: str | None = None
    experience_level: str | None = None
    skills: list[str] | None = None
    requirements: str | None = None
    posted_at: datetime | None = None
    expires_at: datetime | None = None
    remote_type: RemoteType = "onsite"
    is_remote: bool
    city: str | None = None
    country: str | None = None
    fingerprint: str


class ValidationResult(BaseSchema):
    """Result of validating a single ``NormalizedJob``."""

    is_valid: bool
    errors: list[str]
    warnings: list[str]


class ScraperResult(BaseSchema):
    """Execution result of a single scraper run."""

    source: str
    success: bool
    jobs_found: int
    duration_seconds: float
    error: str | None = None


class ExecutionSummary(BaseSchema):
    """Aggregated result of a full scraping cycle across all enabled scrapers."""

    total_scrapers: int
    succeeded: int
    failed: int
    total_jobs: int
    duration_seconds: float
    results: list[ScraperResult]

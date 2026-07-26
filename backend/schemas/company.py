from datetime import datetime

from backend.schemas.base import BaseSchema, TimestampSchema


class CompanyResponse(TimestampSchema):
    name: str
    website: str | None = None
    logo_url: str | None = None
    description: str | None = None
    industry: str | None = None
    size: str | None = None
    headquarters: str | None = None
    is_active: bool = True
    hr_email: str | None = None
    hr_email_confidence: int | None = None
    hr_email_source: str | None = None
    hr_email_verified_at: datetime | None = None


class CompanyListResponse(BaseSchema):
    items: list[CompanyResponse]
    total: int


class SyncCompaniesResponse(BaseSchema):
    synced: int
    message: str


class EmailVerificationStatusResponse(BaseSchema):
    verified: int
    unverified: int
    total: int

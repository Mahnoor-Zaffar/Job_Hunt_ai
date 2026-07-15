"""Typed service interfaces using :class:`typing.Protocol`.

Each protocol defines the minimal contract a service must fulfil.
Concrete implementations inherit from both the protocol and
:class:`BaseService`.

These protocols are used primarily for dependency injection and
testing — consumers depend on the protocol, not the implementation.
"""

import uuid
from typing import Any, Protocol

from backend.models.application import Application
from backend.models.company import Company
from backend.models.job import Job
from backend.models.notification import Notification
from backend.models.resume import Resume


class JobServiceProtocol(Protocol):
    async def mark_applied(self, job_id: uuid.UUID) -> Job | None: ...
    async def mark_saved(self, job_id: uuid.UUID) -> Job | None: ...
    async def mark_expired(self, job_id: uuid.UUID) -> Job | None: ...
    async def find_duplicates(self, fingerprint: str) -> list[Job]: ...
    async def expire_old_jobs(self) -> int: ...
    async def get_stats(self) -> dict[str, int]: ...


class CompanyServiceProtocol(Protocol):
    async def get_or_create(self, name: str) -> Company: ...
    async def get_active_companies(self, skip: int = 0, limit: int = 50) -> list[Company]: ...
    async def find_by_name(self, name: str) -> Company | None: ...
    async def deactivate(self, company_name: str) -> Company | None: ...
    async def update_metadata(
        self,
        name: str,
        *,
        website: str | None = None,
        description: str | None = None,
        industry: str | None = None,
    ) -> Company | None: ...


class ResumeServiceProtocol(Protocol):
    async def get_user_resumes(self, user_id: uuid.UUID) -> list[Resume]: ...
    async def get_primary_resume(self, user_id: uuid.UUID) -> Resume | None: ...
    async def set_primary(self, resume_id: uuid.UUID) -> Resume | None: ...
    async def create_resume(
        self,
        user_id: uuid.UUID,
        name: str,
        file_path: str,
        file_type: str,
        *,
        parsed_text: str | None = None,
    ) -> Resume: ...
    async def update_text(self, resume_id: uuid.UUID, parsed_text: str) -> Resume | None: ...


class SearchServiceProtocol(Protocol):
    async def search(
        self,
        *,
        title: str | None = None,
        company: str | None = None,
        location: str | None = None,
        city: str | None = None,
        country: str | None = None,
        is_remote: bool | None = None,
        source: str | None = None,
        employment_type: str | None = None,
        experience_level: str | None = None,
        salary_min: float | None = None,
        salary_max: float | None = None,
        status: str | None = "active",
        technologies: list[str] | None = None,
        skip: int = 0,
        limit: int = 50,
        embedding: list[float] | None = None,
    ) -> list[Job]: ...
    async def search_by_keyword(
        self, keyword: str, skip: int = 0, limit: int = 50
    ) -> list[Job]: ...


class ApplicationServiceProtocol(Protocol):
    async def apply(
        self,
        user_id: uuid.UUID,
        job_id: uuid.UUID,
        *,
        resume_id: uuid.UUID | None = None,
        cover_letter: str | None = None,
    ) -> Application: ...
    async def submit(self, application_id: uuid.UUID) -> Application | None: ...
    async def update_status(self, application_id: uuid.UUID, status: str) -> Application | None: ...
    async def get_user_applications(
        self, user_id: uuid.UUID, skip: int = 0, limit: int = 50
    ) -> list[Application]: ...
    async def get_by_status(
        self, status: str, skip: int = 0, limit: int = 50
    ) -> list[Application]: ...


class NotificationServiceProtocol(Protocol):
    async def create(
        self,
        user_id: uuid.UUID,
        type_: str,
        title: str,
        message: str,
        *,
        job_id: uuid.UUID | None = None,
        metadata_json: str | None = None,
        sent_via: str | None = None,
    ) -> Notification: ...
    async def get_unread(self, user_id: uuid.UUID) -> list[Notification]: ...
    async def get_all(
        self, user_id: uuid.UUID, skip: int = 0, limit: int = 50
    ) -> list[Notification]: ...
    async def mark_read(self, notification_id: uuid.UUID) -> Notification | None: ...
    async def mark_all_read(self, user_id: uuid.UUID) -> int: ...


class AnalyticsServiceProtocol(Protocol):
    async def get_dashboard_stats(self) -> dict[str, Any]: ...
    async def get_jobs_by_source(self) -> list[dict[str, Any]]: ...
    async def get_applications_by_status(self) -> list[dict[str, Any]]: ...


class SettingsServiceProtocol(Protocol):
    async def get(self, user_id: uuid.UUID, key: str, default: str | None = None) -> str | None: ...
    async def set(self, user_id: uuid.UUID, key: str, value: str) -> None: ...
    async def get_all(self, user_id: uuid.UUID) -> dict[str, str]: ...

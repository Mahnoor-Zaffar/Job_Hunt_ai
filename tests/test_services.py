"""Tests for business services with mocked repositories."""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.models.application import Application
from backend.models.company import Company
from backend.models.job import Job
from backend.models.notification import Notification
from backend.models.resume import Resume
from backend.repositories.application import ApplicationRepository
from backend.repositories.company import CompanyRepository
from backend.repositories.infrastructure import (
    ScrapeLogRepository,
    SettingsRepository,
)
from backend.repositories.job import JobRepository
from backend.repositories.notification import NotificationRepository
from backend.repositories.resume import ResumeRepository
from backend.services.analytics import AnalyticsService
from backend.services.application import ApplicationService
from backend.services.base import (
    DuplicateError,
    NotFoundError,
    ServiceError,
    ValidationError,
)
from backend.services.company import CompanyService
from backend.services.job import JobService
from backend.services.notification import NotificationService
from backend.services.resume import ResumeService
from backend.services.search import SearchService
from backend.services.settings import SettingsService


def _mock_repo(spec: type) -> MagicMock:
    repo = AsyncMock(spec=spec)
    repo.session = AsyncMock()
    repo.session.flush = AsyncMock()
    return repo


class TestJobService:
    @pytest.mark.asyncio
    async def test_mark_applied(self) -> None:
        job_id = uuid.uuid4()
        job = Job(
            title="Dev",
            company="Co",
            location="Remote",
            url="https://x.com/j/1",
            source="test",
            source_id="1",
            fingerprint="abc",
            status="active",
        )
        repo = _mock_repo(JobRepository)
        repo.get_by_id = AsyncMock(return_value=job)
        service = JobService(repo)
        result = await service.mark_applied(job_id)
        assert result is not None
        assert result.status == "applied"

    @pytest.mark.asyncio
    async def test_mark_applied_not_found(self) -> None:
        repo = _mock_repo(JobRepository)
        repo.get_by_id = AsyncMock(return_value=None)
        service = JobService(repo)
        result = await service.mark_applied(uuid.uuid4())
        assert result is None


class TestCompanyService:
    @pytest.mark.asyncio
    async def test_get_or_create_new(self) -> None:
        company = Company(name="NewCo")
        repo = _mock_repo(CompanyRepository)
        repo.get_or_create = AsyncMock(return_value=company)
        service = CompanyService(repo)
        result = await service.get_or_create("NewCo")
        assert result.name == "NewCo"

    @pytest.mark.asyncio
    async def test_deactivate(self) -> None:
        company = Company(name="OldCo", is_active=True)
        repo = _mock_repo(CompanyRepository)
        repo.get_by_name = AsyncMock(return_value=company)
        service = CompanyService(repo)
        result = await service.deactivate("OldCo")
        assert result is not None
        assert result.is_active is False


class TestApplicationService:
    @pytest.mark.asyncio
    async def test_submit_application(self) -> None:
        app = Application(user_id=uuid.uuid4(), job_id=uuid.uuid4(), status="draft")
        repo = _mock_repo(ApplicationRepository)
        repo.get_by_id = AsyncMock(return_value=app)
        service = ApplicationService(repo)
        result = await service.submit(app.id)
        assert result is not None
        assert result.status == "submitted"
        assert result.is_submitted is True
        assert result.applied_at is not None

    @pytest.mark.asyncio
    async def test_update_status_invalid(self) -> None:
        repo = _mock_repo(ApplicationRepository)
        service = ApplicationService(repo)
        with pytest.raises(ValidationError):
            await service.update_status(uuid.uuid4(), "imaginary_status")

    @pytest.mark.asyncio
    async def test_apply_creates_new(self) -> None:
        user_id = uuid.uuid4()
        job_id = uuid.uuid4()
        repo = _mock_repo(ApplicationRepository)
        repo.get_by_job_and_user = AsyncMock(return_value=None)
        repo.create = AsyncMock(return_value=Application(user_id=user_id, job_id=job_id))
        service = ApplicationService(repo)
        result = await service.apply(user_id, job_id)
        assert result.user_id == user_id
        assert result.job_id == job_id
        assert result.status == "draft"

    @pytest.mark.asyncio
    async def test_apply_returns_existing(self) -> None:
        user_id = uuid.uuid4()
        job_id = uuid.uuid4()
        existing = Application(user_id=user_id, job_id=job_id)
        repo = _mock_repo(ApplicationRepository)
        repo.get_by_job_and_user = AsyncMock(return_value=existing)
        service = ApplicationService(repo)
        result = await service.apply(user_id, job_id)
        assert result is existing


class TestNotificationService:
    @pytest.mark.asyncio
    async def test_create_notification(self) -> None:
        user_id = uuid.uuid4()
        repo = _mock_repo(NotificationRepository)
        repo.create = AsyncMock(
            return_value=Notification(
                user_id=user_id, type="new_job", title="Test", message="Test msg"
            )
        )
        service = NotificationService(repo)
        result = await service.create(user_id, "new_job", "Test", "Test msg")
        assert result.type == "new_job"
        assert result.title == "Test"


class TestResumeService:
    @pytest.mark.asyncio
    async def test_set_primary(self) -> None:
        user_id = uuid.uuid4()
        r1 = Resume(user_id=user_id, name="A", file_path="/a.pdf", file_type="pdf", is_primary=True)
        r2 = Resume(
            user_id=user_id, name="B", file_path="/b.pdf", file_type="pdf", is_primary=False
        )
        repo = _mock_repo(ResumeRepository)
        repo.get_by_id = AsyncMock(return_value=r2)
        repo.get_by_user = AsyncMock(return_value=[r1, r2])
        service = ResumeService(repo)
        result = await service.set_primary(r2.id)
        assert result is not None
        assert r2.is_primary is True
        assert r1.is_primary is False


class TestSearchService:
    @pytest.mark.asyncio
    async def test_search_basic(self) -> None:
        job = Job(
            title="Python Dev",
            company="Co",
            location="Remote",
            url="https://x.com",
            source="test",
            source_id="x",
            fingerprint="fp",
            skills=["Python", "Docker"],
        )
        repo = _mock_repo(JobRepository)
        repo.search = AsyncMock(return_value=[job])
        service = SearchService(repo)
        results = await service.search(title="Python")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_search_tech_filter(self) -> None:
        job_py = Job(
            title="Python Dev",
            company="Co",
            location="Remote",
            url="https://x.com",
            source="test",
            source_id="p",
            fingerprint="fp1",
            skills=["Python"],
        )
        job_go = Job(
            title="Go Dev",
            company="Co",
            location="Remote",
            url="https://x.com",
            source="test",
            source_id="g",
            fingerprint="fp2",
            skills=["Go"],
        )
        repo = _mock_repo(JobRepository)
        repo.search = AsyncMock(return_value=[job_py, job_go])
        service = SearchService(repo)
        results = await service.search(technologies=["Python"])
        assert len(results) == 1
        assert results[0].title == "Python Dev"


class TestAnalyticsService:
    @pytest.mark.asyncio
    async def test_get_dashboard_stats(self) -> None:
        job_repo = _mock_repo(JobRepository)
        job_repo.count_active = AsyncMock(return_value=42)
        app_repo = _mock_repo(ApplicationRepository)
        log_repo = _mock_repo(ScrapeLogRepository)
        service = AnalyticsService(job_repo, app_repo, log_repo)
        stats = await service.get_dashboard_stats()
        assert stats["total_jobs"] == 42
        assert stats["active_jobs"] == 42

    @pytest.mark.asyncio
    async def test_get_jobs_by_source(self) -> None:
        job_repo = _mock_repo(JobRepository)
        job_repo.session.execute = AsyncMock(
            return_value=MockResult([("rozee", 15), ("remoteok", 8)])
        )
        app_repo = _mock_repo(ApplicationRepository)
        log_repo = _mock_repo(ScrapeLogRepository)
        service = AnalyticsService(job_repo, app_repo, log_repo)
        result = await service.get_jobs_by_source()
        assert len(result) == 2
        assert result[0] == {"source": "rozee", "count": 15}

    @pytest.mark.asyncio
    async def test_get_full_dashboard(self) -> None:
        job_repo = _mock_repo(JobRepository)
        job_repo.count_active = AsyncMock(return_value=10)
        job_repo.session.execute = AsyncMock(return_value=MockResult([]))
        app_repo = _mock_repo(ApplicationRepository)
        app_repo.session.execute = AsyncMock(return_value=MockResult([]))
        log_repo = _mock_repo(ScrapeLogRepository)
        log_repo.get_recent = AsyncMock(return_value=[])
        service = AnalyticsService(job_repo, app_repo, log_repo)
        dashboard = await service.get_full_dashboard()
        assert "stats" in dashboard
        assert "jobs_by_source" in dashboard
        assert "applications_by_status" in dashboard
        assert "recent_scrapes" in dashboard

    @pytest.mark.asyncio
    async def test_get_applications_by_status(self) -> None:
        job_repo = _mock_repo(JobRepository)
        app_repo = _mock_repo(ApplicationRepository)
        app_repo.session.execute = AsyncMock(
            return_value=MockResult([("draft", 5), ("submitted", 3)])
        )
        log_repo = _mock_repo(ScrapeLogRepository)
        service = AnalyticsService(job_repo, app_repo, log_repo)
        result = await service.get_applications_by_status()
        assert len(result) == 2


class TestSettingsService:
    @pytest.mark.asyncio
    async def test_get_value(self) -> None:
        repo = _mock_repo(SettingsRepository)
        repo.get_value = AsyncMock(return_value="enabled")
        service = SettingsService(repo)
        result = await service.get(uuid.uuid4(), "notifications.telegram")
        assert result == "enabled"

    @pytest.mark.asyncio
    async def test_get_with_default(self) -> None:
        async def get_value(_user_id, _key, default=None):
            return default

        repo = _mock_repo(SettingsRepository)
        repo.get_value = get_value
        service = SettingsService(repo)
        result = await service.get(uuid.uuid4(), "missing_key", default="nope")
        assert result == "nope"

    @pytest.mark.asyncio
    async def test_set_value(self) -> None:
        repo = _mock_repo(SettingsRepository)
        repo.set_value = AsyncMock()
        service = SettingsService(repo)
        await service.set(uuid.uuid4(), "theme", "dark")
        repo.set_value.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_all(self) -> None:
        from backend.models.settings import Settings

        s1 = Settings(user_id=uuid.uuid4(), key="k1", value="v1")
        s2 = Settings(user_id=uuid.uuid4(), key="k2", value="v2")
        repo = _mock_repo(SettingsRepository)
        repo.get_all_for_user = AsyncMock(return_value=[s1, s2])
        service = SettingsService(repo)
        result = await service.get_all(uuid.uuid4())
        assert result == {"k1": "v1", "k2": "v2"}

    @pytest.mark.asyncio
    async def test_delete_existing(self) -> None:
        from backend.models.settings import Settings

        repo = _mock_repo(SettingsRepository)
        repo.get_by_user_and_key = AsyncMock(
            return_value=Settings(user_id=uuid.uuid4(), key="x", value="y")
        )
        service = SettingsService(repo)
        result = await service.delete(uuid.uuid4(), "x")
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_missing(self) -> None:
        repo = _mock_repo(SettingsRepository)
        repo.get_by_user_and_key = AsyncMock(return_value=None)
        service = SettingsService(repo)
        result = await service.delete(uuid.uuid4(), "nope")
        assert result is False


class TestServiceExceptions:
    def test_not_found_error(self) -> None:
        exc = NotFoundError(entity="Job", entity_id="abc-123")
        assert exc.entity == "Job"
        assert exc.entity_id == "abc-123"
        assert isinstance(exc, ServiceError)

    def test_duplicate_error(self) -> None:
        exc = DuplicateError(entity="User", field="email", value="dup@test.com")
        assert exc.entity == "User"
        assert isinstance(exc, ServiceError)

    def test_validation_error(self) -> None:
        exc = ValidationError("Field X is required")
        assert isinstance(exc, ServiceError)

    def test_service_error_base(self) -> None:
        exc = ServiceError("generic", entity="Thing", entity_id="1")
        assert exc.entity == "Thing"
        assert str(exc) == "generic"


class MockResult:
    def __init__(self, rows: list) -> None:
        self._rows = rows

    def __iter__(self) -> iter:
        return iter(self._rows)

    def scalars(self):
        return MockScalars(self._rows)

    def scalar_one_or_none(self):
        return self._rows[0] if self._rows else None

    def scalar_one(self):
        if not self._rows:
            raise ValueError("No rows")
        return self._rows[0]

    def all(self):
        return self._rows


class MockScalars:
    def __init__(self, rows: list) -> None:
        self._rows = rows

    def __iter__(self) -> iter:
        return iter(self._rows)

    def all(self) -> list:
        return self._rows

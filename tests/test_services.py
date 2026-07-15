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
from backend.repositories.job import JobRepository
from backend.repositories.notification import NotificationRepository
from backend.repositories.resume import ResumeRepository
from backend.services.application import ApplicationService
from backend.services.company import CompanyService
from backend.services.job import JobService
from backend.services.notification import NotificationService
from backend.services.resume import ResumeService
from backend.services.search import SearchService


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
        with pytest.raises(ValueError, match="Invalid application status"):
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

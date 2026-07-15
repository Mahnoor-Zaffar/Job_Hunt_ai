"""Edge case and failure scenario tests."""

import uuid
from unittest.mock import AsyncMock

import pytest

from backend.models.application import Application
from backend.models.job import Job
from backend.repositories.application import ApplicationRepository
from backend.repositories.company import CompanyRepository
from backend.repositories.job import JobRepository
from backend.repositories.resume import ResumeRepository
from backend.services.application import ApplicationService
from backend.services.base import NotFoundError, ValidationError
from backend.services.company import CompanyService
from backend.services.job import JobService
from backend.services.resume import ResumeService
from backend.services.search import SearchService


def _mock_repo(spec: type) -> AsyncMock:
    repo = AsyncMock(spec=spec)
    repo.session = AsyncMock()
    repo.session.flush = AsyncMock()
    return repo


class TestEdgeCases:
    @pytest.mark.asyncio
    async def test_job_service_mark_applied_nonexistent(self) -> None:
        repo = _mock_repo(JobRepository)
        repo.get_by_id = AsyncMock(return_value=None)
        svc = JobService(repo)
        result = await svc.mark_applied(uuid.uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_company_deactivate_nonexistent(self) -> None:
        repo = _mock_repo(CompanyRepository)
        repo.get_by_name = AsyncMock(return_value=None)
        svc = CompanyService(repo)
        result = await svc.deactivate("NoSuchCo")
        assert result is None

    @pytest.mark.asyncio
    async def test_resume_set_primary_nonexistent(self) -> None:
        repo = _mock_repo(ResumeRepository)
        repo.get_by_id = AsyncMock(return_value=None)
        svc = ResumeService(repo)
        result = await svc.set_primary(uuid.uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_application_reject_nonexistent(self) -> None:
        repo = _mock_repo(ApplicationRepository)
        repo.get_by_id = AsyncMock(return_value=None)
        svc = ApplicationService(repo)
        result = await svc.reject(uuid.uuid4(), "not a fit")
        assert result is None

    @pytest.mark.asyncio
    async def test_application_schedule_interview_nonexistent(self) -> None:
        from datetime import UTC, datetime

        repo = _mock_repo(ApplicationRepository)
        repo.get_by_id = AsyncMock(return_value=None)
        svc = ApplicationService(repo)
        result = await svc.schedule_interview(uuid.uuid4(), datetime.now(UTC))
        assert result is None

    @pytest.mark.asyncio
    async def test_search_empty_filters(self) -> None:
        job = Job(
            title="Dev",
            company="Co",
            location="Remote",
            url="https://x.com",
            source="test",
            source_id="x",
            fingerprint="fp",
            skills=["Python"],
        )
        repo = _mock_repo(JobRepository)
        repo.search = AsyncMock(return_value=[job])
        svc = SearchService(repo)
        results = await svc.search(status="active")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_search_pagination(self) -> None:
        job = Job(
            title="Dev",
            company="Co",
            location="Remote",
            url="https://x.com",
            source="test",
            source_id="p",
            fingerprint="fp",
        )
        repo = _mock_repo(JobRepository)
        repo.search = AsyncMock(return_value=[job])
        svc = SearchService(repo)

        page1 = await svc.search(skip=0, limit=1, status="active")
        assert len(page1) == 1

        repo.search = AsyncMock(return_value=[])
        page2 = await svc.search(skip=1, limit=1, status="active")
        assert len(page2) == 0

    @pytest.mark.asyncio
    async def test_application_update_status_nonexistent(self) -> None:
        repo = _mock_repo(ApplicationRepository)
        repo.get_by_id = AsyncMock(return_value=None)
        svc = ApplicationService(repo)
        result = await svc.update_status(uuid.uuid4(), "submitted")
        assert result is None

    @pytest.mark.asyncio
    async def test_application_offer_nonexistent(self) -> None:
        repo = _mock_repo(ApplicationRepository)
        repo.get_by_id = AsyncMock(return_value=None)
        svc = ApplicationService(repo)
        result = await svc.record_offer(uuid.uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_application_follow_up_nonexistent(self) -> None:
        from datetime import UTC, datetime

        repo = _mock_repo(ApplicationRepository)
        repo.get_by_id = AsyncMock(return_value=None)
        svc = ApplicationService(repo)
        result = await svc.set_follow_up(uuid.uuid4(), datetime.now(UTC))
        assert result is None

    def test_validation_error_message(self) -> None:
        exc = ValidationError("field X required")
        assert str(exc) == "field X required"
        assert isinstance(exc, NotFoundError) is False

    def test_not_found_error_message(self) -> None:
        exc = NotFoundError(entity="User", entity_id="42")
        assert "User" in str(exc)
        assert "42" in str(exc)

    @pytest.mark.asyncio
    async def test_duplicate_application_returns_existing(self) -> None:
        user_id = uuid.uuid4()
        job_id = uuid.uuid4()
        existing = Application(user_id=user_id, job_id=job_id)
        repo = _mock_repo(ApplicationRepository)
        repo.get_by_job_and_user = AsyncMock(return_value=existing)
        svc = ApplicationService(repo)
        result = await svc.apply(user_id, job_id)
        assert result is existing  # same object returned

    @pytest.mark.asyncio
    async def test_job_service_ensure_company_no_repo(self) -> None:
        repo = _mock_repo(JobRepository)
        svc = JobService(repo, company_repo=None)
        await svc.ensure_company_exists("Acme")
        # Should not raise — gracefully skipped

    @pytest.mark.asyncio
    async def test_resume_service_create_without_version_repo(self) -> None:
        repo = _mock_repo(ResumeRepository)
        svc = ResumeService(repo, version_repo=None)
        assert svc is not None  # should init fine

    @pytest.mark.asyncio
    async def test_search_zero_results(self) -> None:
        repo = _mock_repo(JobRepository)
        repo.search = AsyncMock(return_value=[])
        svc = SearchService(repo)
        results = await svc.search(status="active")
        assert results == []

    @pytest.mark.asyncio
    async def test_search_salary_boundary(self) -> None:
        job = Job(
            title="Dev",
            company="Co",
            location="Remote",
            url="https://x.com",
            source="test",
            source_id="x",
            fingerprint="fp",
            skills=["Python"],
        )
        repo = _mock_repo(JobRepository)
        repo.search = AsyncMock(return_value=[job])
        svc = SearchService(repo)
        results = await svc.search(salary_min=0, salary_max=999999)
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_application_get_due_follow_ups_empty(self) -> None:
        repo = _mock_repo(ApplicationRepository)
        repo.get_by_status = AsyncMock(return_value=[])
        svc = ApplicationService(repo)
        results = await svc.get_due_follow_ups()
        assert results == []

    @pytest.mark.asyncio
    async def test_application_get_interviews_empty(self) -> None:
        repo = _mock_repo(ApplicationRepository)
        repo.get_by_user = AsyncMock(return_value=[])
        svc = ApplicationService(repo)
        results = await svc.get_interviews(uuid.uuid4())
        assert results == []


class TestFailureScenarios:
    @pytest.mark.asyncio
    async def test_repo_exception_propagates(self) -> None:
        repo = _mock_repo(JobRepository)
        repo.get_by_id = AsyncMock(side_effect=RuntimeError("DB down"))
        svc = JobService(repo)
        with pytest.raises(RuntimeError, match="DB down"):
            await svc.mark_applied(uuid.uuid4())

    @pytest.mark.asyncio
    async def test_company_get_or_create_new(self) -> None:
        company = Job(
            title="T",
            company="C",
            location="L",
            url="u",
            source="s",
            source_id="si",
            fingerprint="f",
        )
        repo = _mock_repo(CompanyRepository)
        repo.get_or_create = AsyncMock(return_value=company)
        svc = CompanyService(repo)
        result = await svc.get_or_create("NewCo")
        assert result is not None

    @pytest.mark.asyncio
    async def test_company_update_metadata_nonexistent(self) -> None:
        repo = _mock_repo(CompanyRepository)
        repo.get_by_name = AsyncMock(return_value=None)
        svc = CompanyService(repo)
        result = await svc.update_metadata("NoCo", website="https://noco.com")
        assert result is None

    @pytest.mark.asyncio
    async def test_resume_update_text_nonexistent(self) -> None:
        repo = _mock_repo(ResumeRepository)
        repo.get_by_id = AsyncMock(return_value=None)
        svc = ResumeService(repo)
        result = await svc.update_text(uuid.uuid4(), "new text")
        assert result is None

"""Tests for domain models — instantiation and field defaults."""

import uuid
from datetime import UTC, datetime

from backend.models.application import Application
from backend.models.company import Company
from backend.models.job import Job
from backend.models.location import Location
from backend.models.notification import Notification
from backend.models.platform import ATSPlatform
from backend.models.resume import Resume, ResumeVersion
from backend.models.scrape_log import ScrapeLog
from backend.models.settings import Settings
from backend.models.technology import Technology, job_technology
from backend.models.user import User
from backend.models.watchlist import CompanyWatchlist


class TestJobModel:
    def test_create_minimal_job(self) -> None:
        job = Job(
            title="Software Engineer",
            company="Acme",
            location="Islamabad, Pakistan",
            url="https://example.com/job/1",
            source="test",
            source_id="test-1",
            fingerprint="abc123def456",
        )
        assert job.title == "Software Engineer"
        assert job.company == "Acme"
        assert job.status == "active"
        assert job.remote_type == "onsite"
        assert job.is_remote is False
        assert job.skills is None
        assert job.company_id is None

    def test_remote_type_maps(self) -> None:
        job = Job(
            title="Dev",
            company="Co",
            location="Remote",
            url="https://example.com/job/2",
            source="test",
            source_id="test-2",
            fingerprint="def456abc",
            is_remote=True,
            remote_type="remote",
        )
        assert job.remote_type == "remote"
        assert job.is_remote is True


class TestCompanyModel:
    def test_create_company(self) -> None:
        company = Company(name="Acme Inc")
        assert company.name == "Acme Inc"
        assert company.is_active is True
        assert company.website is None

    def test_company_with_metadata(self) -> None:
        company = Company(
            name="Acme",
            website="https://acme.com",
            industry="Technology",
            size="100-500",
        )
        assert company.website == "https://acme.com"
        assert company.industry == "Technology"


class TestApplicationModel:
    def test_create_application(self) -> None:
        app = Application(
            user_id=uuid.uuid4(),
            job_id=uuid.uuid4(),
        )
        assert app.status == "draft"
        assert app.is_submitted is False
        assert app.applied_at is None


class TestTechnologyModel:
    def test_create_technology(self) -> None:
        tech = Technology(name="Python", category="Language")
        assert tech.name == "Python"
        assert tech.category == "Language"
        assert tech.is_active is True

    def test_job_technology_table_exists(self) -> None:
        assert job_technology is not None


class TestNotificationModel:
    def test_create_notification(self) -> None:
        n = Notification(
            user_id=uuid.uuid4(),
            type="new_job",
            title="New Job Alert",
            message="A new Python job was found",
        )
        assert n.type == "new_job"
        assert n.is_read is False
        assert n.read_at is None


class TestResumeModel:
    def test_create_resume(self) -> None:
        r = Resume(
            user_id=uuid.uuid4(),
            name="My Resume",
            file_path="/uploads/resume.pdf",
            file_type="pdf",
        )
        assert r.name == "My Resume"
        assert r.is_primary is False

    def test_resume_version(self) -> None:
        rv = ResumeVersion(
            resume_id=uuid.uuid4(),
            version_number=1,
            file_path="/uploads/v1.pdf",
        )
        assert rv.version_number == 1


class TestWatchlistModel:
    def test_create_watchlist(self) -> None:
        cw = CompanyWatchlist(
            user_id=uuid.uuid4(),
            company_name="Spotify",
        )
        assert cw.company_name == "Spotify"
        assert cw.notify_on_new_jobs is True
        assert cw.is_active is True


class TestPlatformModel:
    def test_create_platform(self) -> None:
        plat = ATSPlatform(
            name="greenhouse",
            display_name="Greenhouse",
            adapter_module="backend.scrapers.ats.greenhouse",
            adapter_class="GreenhouseAdapter",
        )
        assert plat.name == "greenhouse"
        assert plat.supports_json_api is True


class TestLocationModel:
    def test_create_location(self) -> None:
        loc = Location(
            city="Islamabad",
            country="Pakistan",
            is_supported=True,
        )
        assert loc.city == "Islamabad"
        assert loc.is_supported is True
        assert loc.is_remote is False


class TestScrapeLogModel:
    def test_create_log(self) -> None:
        log = ScrapeLog(
            source="rozee",
            status="success",
            jobs_discovered=25,
            jobs_new=10,
            duration_seconds=3.5,
            started_at=datetime.now(UTC),
        )
        assert log.source == "rozee"
        assert log.jobs_discovered == 25
        assert log.jobs_new == 10


class TestSettingsModel:
    def test_create_setting(self) -> None:
        s = Settings(
            user_id=uuid.uuid4(),
            key="notifications.telegram",
            value="enabled",
        )
        assert s.key == "notifications.telegram"
        assert s.value == "enabled"
        assert s.is_encrypted is False


class TestUserModel:
    def test_create_user(self) -> None:
        user = User(
            email="test@example.com",
            name="Test User",
            hashed_password="abc123",
        )
        assert user.email == "test@example.com"
        assert user.is_active is True

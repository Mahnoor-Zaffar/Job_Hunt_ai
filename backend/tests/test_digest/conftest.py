import pytest
from pathlib import Path
from datetime import datetime, timezone

from backend.services.digest.config import DigestConfig
from backend.services.digest.models import NormalizedJob


@pytest.fixture
def config() -> DigestConfig:
    config_dir = (
        Path(__file__).resolve().parent.parent.parent / "config" / "rules"
    )
    return DigestConfig(config_dir)


@pytest.fixture
def job_backend_engineer() -> NormalizedJob:
    return NormalizedJob(
        id="1",
        title="Backend Engineer",
        company="Tech Co",
        location="Remote",
        is_remote=True,
        remote_type="remote",
        description="We are looking for a backend engineer with Python, FastAPI, and PostgreSQL experience.",
        skills=["python", "fastapi", "postgresql", "docker"],
        url="https://example.com/jobs/1",
        apply_url="https://example.com/apply/1",
        source="remoteok",
        source_id="remoteok-1",
        employment_type="full time",
        experience_level="senior",
        posted_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def job_frontend_react() -> NormalizedJob:
    return NormalizedJob(
        id="2",
        title="Frontend Developer",
        company="Web Inc",
        location="Remote",
        is_remote=True,
        remote_type="remote",
        description="React, Next.js, TypeScript frontend role.",
        skills=["react", "next.js", "typescript", "tailwind"],
        url="https://example.com/jobs/2",
        apply_url="https://example.com/apply/2",
        source="remotive",
        source_id="remotive-1",
        employment_type="full time",
        experience_level="mid",
        posted_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def job_fullstack() -> NormalizedJob:
    return NormalizedJob(
        id="3",
        title="Full Stack Developer",
        company="Startup XYZ",
        location="San Francisco",
        description="Full stack role with React and Node.js.",
        skills=["react", "node.js", "python", "postgresql"],
        url="https://example.com/jobs/3",
        source="hn_hiring",
        source_id="hn-1",
        employment_type="full time",
        posted_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def job_sales() -> NormalizedJob:
    return NormalizedJob(
        id="4",
        title="Sales Representative",
        company="Sales Co",
        location="New York",
        description="Selling our product to enterprise customers.",
        url="https://example.com/jobs/4",
        source="remoteok",
        source_id="remoteok-4",
        posted_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def job_intern() -> NormalizedJob:
    return NormalizedJob(
        id="5",
        title="Software Engineer Intern",
        company="Big Corp",
        location="Remote",
        is_remote=True,
        remote_type="remote",
        description="Summer internship for software engineers.",
        skills=["python", "react"],
        url="https://example.com/jobs/5",
        source="remoteok",
        source_id="remoteok-5",
        employment_type="intern",
        experience_level="internship",
        posted_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def job_software_engineer_with_tech() -> NormalizedJob:
    return NormalizedJob(
        id="6",
        title="Software Engineer",
        company="Tech Giant",
        location="Remote",
        is_remote=True,
        remote_type="remote",
        description="Backend role using Python, Django, and PostgreSQL. Must know Docker and AWS.",
        skills=["python", "django", "postgresql", "docker", "aws"],
        url="https://example.com/jobs/6",
        apply_url="https://example.com/apply/6",
        source="remoteok",
        source_id="remoteok-6",
        employment_type="full time",
        experience_level="senior",
        posted_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def job_software_engineer_no_tech() -> NormalizedJob:
    return NormalizedJob(
        id="7",
        title="Software Engineer",
        company="Traditional Corp",
        location="New York",
        description="General software engineering role maintaining legacy systems.",
        skills=["java", "c#", "sql"],
        url="https://example.com/jobs/7",
        source="remoteok",
        source_id="remoteok-7",
        employment_type="full time",
        posted_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def job_ai_engineer() -> NormalizedJob:
    return NormalizedJob(
        id="8",
        title="AI Engineer",
        company="AI Lab",
        location="Remote",
        is_remote=True,
        remote_type="remote",
        description="Building RAG systems with LangChain and OpenAI. LLM experience required.",
        skills=["python", "langchain", "openai", "rag", "vector database"],
        url="https://example.com/jobs/8",
        source="remoteok",
        source_id="remoteok-8",
        employment_type="full time",
        experience_level="senior",
        posted_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def job_devops() -> NormalizedJob:
    return NormalizedJob(
        id="9",
        title="DevOps Engineer",
        company="Cloud Co",
        location="Remote",
        is_remote=True,
        remote_type="remote",
        description="Kubernetes, Docker, Terraform, AWS CI/CD pipelines.",
        skills=["kubernetes", "docker", "terraform", "aws", "ci/cd"],
        url="https://example.com/jobs/9",
        source="built_in",
        source_id="builtin-1",
        employment_type="full time",
        experience_level="senior",
        posted_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def job_duplicate() -> NormalizedJob:
    return NormalizedJob(
        id="10",
        title="Backend Engineer",
        company="Tech Co",
        location="Remote",
        is_remote=True,
        remote_type="remote",
        description="We are looking for a backend engineer with Python, FastAPI, and PostgreSQL experience.",
        skills=["python", "fastapi", "postgresql", "docker"],
        url="https://example.com/jobs/1",
        apply_url="https://example.com/apply/1",
        source="remoteok",
        source_id="remoteok-dup",
        employment_type="full time",
        experience_level="senior",
        posted_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def all_jobs(
    job_backend_engineer,
    job_frontend_react,
    job_fullstack,
    job_sales,
    job_intern,
    job_software_engineer_with_tech,
    job_software_engineer_no_tech,
    job_ai_engineer,
    job_devops,
    job_duplicate,
):
    return [
        job_backend_engineer,
        job_frontend_react,
        job_fullstack,
        job_sales,
        job_intern,
        job_software_engineer_with_tech,
        job_software_engineer_no_tech,
        job_ai_engineer,
        job_devops,
        job_duplicate,
    ]

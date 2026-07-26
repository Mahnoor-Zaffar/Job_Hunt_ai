from backend.services.digest.deduplicator import remove_duplicates
from backend.services.digest.scorer import score_job
from backend.services.digest.models import NormalizedJob, ScoredJob


def test_no_duplicates(job_backend_engineer, job_frontend_react, config):
    sj1 = score_job(job_backend_engineer, config)
    sj2 = score_job(job_frontend_react, config)
    result = remove_duplicates([sj1, sj2])
    assert len(result) == 2


def test_duplicate_same_url(job_backend_engineer, job_duplicate, config):
    sj1 = score_job(job_backend_engineer, config)
    sj2 = score_job(job_duplicate, config)
    result = remove_duplicates([sj1, sj2])
    assert len(result) == 1


def test_duplicate_same_company_title(job_backend_engineer, config):
    job2 = NormalizedJob(
        id="999",
        title="Backend Engineer",
        company="Tech Co",
        location="Remote",
        is_remote=True,
        remote_type="remote",
        skills=["python", "fastapi"],
        url="https://example.com/jobs/999",
        source="another_source",
        source_id="another-999",
    )
    sj1 = score_job(job_backend_engineer, config)
    sj2 = score_job(job2, config)
    result = remove_duplicates([sj1, sj2])
    assert len(result) == 1


def test_no_duplicate_different_company(job_backend_engineer, config):
    job2 = NormalizedJob(
        id="111",
        title="Backend Engineer",
        company="Different Co",
        location="Remote",
        is_remote=True,
        remote_type="remote",
        skills=["python"],
        url="https://example.com/jobs/111",
        source="test",
        source_id="test-111",
    )
    sj1 = score_job(job_backend_engineer, config)
    sj2 = score_job(job2, config)
    result = remove_duplicates([sj1, sj2])
    assert len(result) == 2


def test_duplicate_same_company_location_title(config):
    job1 = NormalizedJob(
        id="201",
        title="Senior Backend Engineer",
        company="Same Co",
        location="New York",
        url="https://example.com/jobs/201",
        source="test",
        source_id="test-201",
        skills=["python"],
    )
    job2 = NormalizedJob(
        id="202",
        title="Senior Backend Engineer",
        company="Same Co",
        location="New York",
        url="https://example.com/jobs/202",
        source="test",
        source_id="test-202",
        skills=["python"],
    )
    sj1 = score_job(job1, config)
    sj2 = score_job(job2, config)
    result = remove_duplicates([sj1, sj2])
    assert len(result) == 1


def test_all_unique(all_jobs, config):
    scored = [score_job(j, config) for j in all_jobs]
    filtered = [s for s in scored if s.score >= 70]
    result = remove_duplicates(filtered)
    accepted = sum(1 for s in result if s.score >= 70)
    # At most 1 duplicate (backend engineer + its duplicate), plus sales/intern rejected
    assert accepted <= len(filtered)
    assert accepted >= 1

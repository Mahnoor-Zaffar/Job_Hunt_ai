from backend.services.digest.categorizer import assign_categories
from backend.services.digest.scorer import score_job


def test_assign_backend(job_backend_engineer, config):
    sj = score_job(job_backend_engineer, config)
    groups = assign_categories([sj], config)
    assert len(groups) >= 1
    backend_groups = [g for g in groups if g.category_key == "backend"]
    assert len(backend_groups) == 1
    assert len(backend_groups[0].jobs) == 1


def test_assign_frontend(job_frontend_react, config):
    sj = score_job(job_frontend_react, config)
    groups = assign_categories([sj], config)
    frontend_groups = [g for g in groups if g.category_key == "frontend"]
    assert len(frontend_groups) == 1


def test_assign_ai(job_ai_engineer, config):
    sj = score_job(job_ai_engineer, config)
    groups = assign_categories([sj], config)
    ai_groups = [g for g in groups if g.category_key == "ai"]
    assert len(ai_groups) == 1


def test_assign_devops(job_devops, config):
    sj = score_job(job_devops, config)
    groups = assign_categories([sj], config)
    devops_groups = [g for g in groups if g.category_key == "devops"]
    assert len(devops_groups) == 1


def test_multiple_categories(all_jobs, config):
    scored = [score_job(j, config) for j in all_jobs]
    filtered = [s for s in scored if s.score >= 70]
    groups = assign_categories(filtered, config)
    assert len(groups) >= 1
    for g in groups:
        assert len(g.jobs) > 0
        assert g.category_label != ""


def test_empty_input(config):
    groups = assign_categories([], config)
    assert len(groups) == 0


def test_no_scored_jobs(config):
    from backend.services.digest.models import ScoredJob, NormalizedJob
    job = NormalizedJob(id="x", title="x", company="x", location="x", url="x", source="x", source_id="x")
    sj = ScoredJob(job=job, score=0, category=None)
    groups = assign_categories([sj], config)
    assert len(groups) == 0


def test_max_per_category(config):
    from backend.services.digest.models import NormalizedJob, ScoredJob as SJ
    jobs = []
    for i in range(15):
        job = NormalizedJob(
            id=f"max-{i}",
            title="Backend Engineer",
            company=f"Company {i}",
            location="Remote",
            skills=["python", "fastapi"],
            url=f"https://example.com/jobs/{i}",
            source="test",
            source_id=f"test-max-{i}",
            is_remote=True,
            remote_type="remote",
        )
        sj = score_job(job, config)
        if sj.score >= 70:
            jobs.append(sj)
    groups = assign_categories(jobs, config)
    backend = [g for g in groups if g.category_key == "backend"]
    if backend:
        assert len(backend[0].jobs) <= config.max_per_category


def test_category_order(job_backend_engineer, job_frontend_react, job_ai_engineer, job_devops, config):
    scored = [score_job(j, config) for j in [job_backend_engineer, job_frontend_react, job_ai_engineer, job_devops]]
    filtered = [s for s in scored if s.score >= 70]
    groups = assign_categories(filtered, config)
    keys = [g.category_key for g in groups]
    assert "backend" in keys
    assert "frontend" in keys
    assert "ai" in keys
    assert "devops" in keys

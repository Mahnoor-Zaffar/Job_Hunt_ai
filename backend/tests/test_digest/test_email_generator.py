from backend.services.digest.email_generator import generate_email_html, generate_email_text, _format_salary, _format_posted, _format_location
from backend.services.digest.models import CategoryGroup, ScoredJob, NormalizedJob


def test_generate_email_html_with_categories(job_backend_engineer, config):
    from backend.services.digest.scorer import score_job
    sj = score_job(job_backend_engineer, config)
    group = CategoryGroup(category_key="backend", category_label="Backend Engineering", jobs=[sj])
    html = generate_email_html([group], config)
    assert "<!DOCTYPE html>" in html
    assert "Daily Job Digest" in html
    assert "Backend Engineering" in html
    assert job_backend_engineer.title in html
    assert job_backend_engineer.company in html
    assert "Apply" in html


def test_generate_email_html_empty(config):
    html = generate_email_html([], config)
    assert "<!DOCTYPE html>" in html
    assert "No matching jobs" in html


def test_generate_email_html_with_stats(job_backend_engineer, config):
    from backend.services.digest.scorer import score_job
    sj = score_job(job_backend_engineer, config)
    group = CategoryGroup(category_key="backend", category_label="Backend Engineering", jobs=[sj])
    stats = {"total_scraped": 100, "accepted": 10, "rejected": 90, "duplicates_removed": 5}
    html = generate_email_html([group], config, stats)
    assert "100" in html
    assert "10" in html


def test_generate_email_text(job_backend_engineer, config):
    from backend.services.digest.scorer import score_job
    sj = score_job(job_backend_engineer, config)
    group = CategoryGroup(category_key="backend", category_label="Backend Engineering", jobs=[sj])
    text = generate_email_text([group], config)
    assert "Daily Job Digest" in text
    assert "Backend Engineering" in text
    assert job_backend_engineer.title in text


def test_multiple_categories_html(job_backend_engineer, job_frontend_react, config):
    from backend.services.digest.scorer import score_job
    sj1 = score_job(job_backend_engineer, config)
    sj2 = score_job(job_frontend_react, config)
    groups = [
        CategoryGroup(category_key="backend", category_label="Backend Engineering", jobs=[sj1]),
        CategoryGroup(category_key="frontend", category_label="Frontend Engineering", jobs=[sj2]),
    ]
    html = generate_email_html(groups, config)
    assert "Backend Engineering" in html
    assert "Frontend Engineering" in html
    assert job_backend_engineer.title in html
    assert job_frontend_react.title in html


def test_format_salary():
    from decimal import Decimal
    assert _format_salary(Decimal("100000"), Decimal("150000"), "USD") == "$100,000 - $150,000"
    assert _format_salary(Decimal("80000"), None, "USD") == "From $80,000"
    assert _format_salary(None, Decimal("120000"), "USD") == "Up to $120,000"
    assert _format_salary(None, None, None) == ""


def test_format_posted():
    from datetime import datetime, timezone, timedelta
    now = datetime.now(timezone.utc)
    assert _format_posted(now) == "Just now"
    assert _format_posted(now - timedelta(hours=5)) == "5h ago"
    assert _format_posted(now - timedelta(days=2)) == "2 days ago"
    assert _format_posted(now - timedelta(days=60)) is not None


def test_format_location_remote():
    job = NormalizedJob(id="1", title="E", company="C", location="Remote", is_remote=True, remote_type="remote", url="x", source="x", source_id="x")
    assert "Remote" in _format_location(job)


def test_format_location_city_country():
    job = NormalizedJob(id="1", title="E", company="C", location="San Francisco, USA", city="San Francisco", country="USA", url="x", source="x", source_id="x")
    formatted = _format_location(job)
    assert "San Francisco" in formatted
    assert "USA" in formatted

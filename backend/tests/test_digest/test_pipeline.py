from backend.services.digest.pipeline import run_pipeline, generate_email


def test_pipeline_with_mixed_jobs(all_jobs, config):
    result = run_pipeline(all_jobs, config)
    assert result.total_scraped == len(all_jobs)
    assert result.accepted >= 1
    assert result.rejected >= 1
    assert result.processing_duration_ms > 0
    assert result.acceptance_rate > 0


def test_pipeline_deduplication(all_jobs, config):
    result = run_pipeline(all_jobs, config)
    assert result.duplicates_removed >= 1


def test_pipeline_categories(all_jobs, config):
    result = run_pipeline(all_jobs, config)
    assert len(result.categories) >= 1
    for group in result.categories:
        assert len(group.jobs) > 0
        assert group.category_key != ""
        assert group.category_label != ""


def test_pipeline_no_matching_jobs(config):
    from backend.services.digest.models import NormalizedJob
    jobs = [
        NormalizedJob(id="r1", title="Sales Manager", company="Co", location="NYC", url="x", source="x", source_id="x"),
        NormalizedJob(id="r2", title="Marketing Lead", company="Co", location="NYC", url="x", source="x", source_id="x"),
    ]
    result = run_pipeline(jobs, config)
    assert result.accepted == 0
    assert result.rejected >= 2
    assert len(result.categories) == 0 or sum(len(g.jobs) for g in result.categories) == 0


def test_pipeline_empty_input(config):
    result = run_pipeline([], config)
    assert result.total_scraped == 0
    assert result.accepted == 0
    assert result.rejected == 0
    assert len(result.categories) == 0


def test_generate_email_from_result(all_jobs, config):
    result = run_pipeline(all_jobs, config)
    html, text = generate_email(result, config)
    assert html is not None
    assert text is not None
    assert "<!DOCTYPE html>" in html
    assert "Daily Job Digest" in html


def test_pipeline_stats(all_jobs, config):
    result = run_pipeline(all_jobs, config)
    assert result.per_category_stats is not None
    total_in_categories = sum(result.per_category_stats.values())
    total_in_groups = sum(len(g.jobs) for g in result.categories)
    assert total_in_categories == total_in_groups


def test_pipeline_max_total(all_jobs, config):
    result = run_pipeline(all_jobs, config, max_total=3)
    total = sum(len(g.jobs) for g in result.categories)
    assert total <= 3


def test_pipeline_min_confidence_high(all_jobs, config):
    result = run_pipeline(all_jobs, config, min_confidence="high")
    for g in result.categories:
        for sj in g.jobs:
            assert sj.confidence == "high"


def test_pipeline_acceptance_rate(all_jobs, config):
    result = run_pipeline(all_jobs, config)
    if result.total_scraped > 0:
        expected_rate = (result.accepted / result.total_scraped) * 100
        assert abs(result.acceptance_rate - expected_rate) < 0.01


def test_pipeline_explanations_are_internal(all_jobs, config):
    result = run_pipeline(all_jobs, config)
    for exp in result.explanations:
        assert hasattr(exp, "result")
        assert hasattr(exp, "reason")


def test_confidence_distribution(all_jobs, config):
    result = run_pipeline(all_jobs, config)
    for g in result.categories:
        for sj in g.jobs:
            assert sj.confidence in ("high", "medium", "low")

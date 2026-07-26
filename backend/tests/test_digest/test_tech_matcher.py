from backend.services.digest.tech_matcher import find_matched_technologies, find_all_technologies, has_any_technology


def test_find_backend_technologies(job_backend_engineer, config):
    matched = find_matched_technologies(job_backend_engineer, "backend", config)
    assert "python" in matched
    assert "fastapi" in matched
    assert "postgresql" in matched
    assert "docker" not in matched  # docker is in devops domain, not backend


def test_find_frontend_technologies(job_frontend_react, config):
    matched = find_matched_technologies(job_frontend_react, "frontend", config)
    assert "react" in matched
    assert "next.js" in matched
    assert "typescript" in matched


def test_find_devops_technologies(job_devops, config):
    matched = find_matched_technologies(job_devops, "devops", config)
    assert "kubernetes" in matched
    assert "docker" in matched
    assert "terraform" in matched
    assert "aws" in matched
    assert "ci/cd" in matched


def test_find_ai_technologies(job_ai_engineer, config):
    matched = find_matched_technologies(job_ai_engineer, "ai", config)
    assert "langchain" in matched
    assert "openai" in matched
    assert "rag" in matched
    assert "vector database" in matched


def test_find_all_technologies(job_backend_engineer, config):
    all_tech = find_all_technologies(job_backend_engineer, config)
    assert "backend" in all_tech
    assert "python" in all_tech["backend"]
    assert "fastapi" in all_tech["backend"]


def test_has_any_technology_true(job_software_engineer_with_tech, config):
    assert has_any_technology(job_software_engineer_with_tech, config) is True


def test_has_any_technology_false(job_sales, config):
    assert has_any_technology(job_sales, config) is False


def test_no_match_for_empty_skills(config):
    from backend.services.digest.models import NormalizedJob
    job = NormalizedJob(
        id="99",
        title="Random Job",
        company="Co",
        location="NYC",
        url="https://example.com",
        source="test",
        source_id="test",
    )
    matched = find_matched_technologies(job, "backend", config)
    assert matched == []


def test_match_from_description(job_software_engineer_no_tech, config):
    matched = find_matched_technologies(job_software_engineer_no_tech, "backend", config)
    assert matched == []


def test_match_from_requirements(config):
    from backend.services.digest.models import NormalizedJob
    job = NormalizedJob(
        id="200",
        title="Python Developer",
        company="Co",
        location="Remote",
        requirements="Must have Python, FastAPI, and PostgreSQL experience.",
        url="https://example.com",
        source="test",
        source_id="test-200",
    )
    matched = find_matched_technologies(job, "backend", config)
    assert "python" in matched
    assert "fastapi" in matched
    assert "postgresql" in matched


def test_domain_specific_ai_tech(config):
    from backend.services.digest.models import NormalizedJob
    job = NormalizedJob(
        id="201",
        title="ML Engineer",
        company="AI Co",
        location="Remote",
        description="Using PyTorch and Hugging Face Transformers for NLP.",
        skills=["pytorch", "transformers"],
        url="https://example.com",
        source="test",
        source_id="test-201",
    )
    ai_matches = find_matched_technologies(job, "ai", config)
    ml_matches = find_matched_technologies(job, "ml", config)
    assert "pytorch" in ml_matches or "hugging face" in ml_matches or "transformers" in ml_matches
    assert len(ai_matches) == 0

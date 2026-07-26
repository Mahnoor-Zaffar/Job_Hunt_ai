from backend.services.digest.classifier import classify_job


def test_backend_engineer_accepted(job_backend_engineer, config):
    result = classify_job(job_backend_engineer, config)
    assert result.accepted is True
    assert result.category == "backend"
    assert result.confidence == "high"
    assert result.matched_title == "backend engineer"
    assert len(result.matched_technologies) > 0


def test_frontend_accepted(job_frontend_react, config):
    result = classify_job(job_frontend_react, config)
    assert result.accepted is True
    assert result.category == "frontend"
    assert result.confidence == "high"
    assert "frontend" in result.reason.lower()


def test_fullstack_accepted(job_fullstack, config):
    result = classify_job(job_fullstack, config)
    assert result.accepted is True
    assert result.confidence == "high"
    assert result.category == "fullstack"


def test_ai_engineer_accepted(job_ai_engineer, config):
    result = classify_job(job_ai_engineer, config)
    assert result.accepted is True
    assert result.category == "ai"
    assert result.confidence == "high"


def test_devops_accepted(job_devops, config):
    result = classify_job(job_devops, config)
    assert result.accepted is True
    assert result.category == "devops"
    assert result.confidence == "high"


def test_sales_rejected(job_sales, config):
    result = classify_job(job_sales, config)
    assert result.accepted is False
    assert result.confidence == "low"


def test_intern_rejected(job_intern, config):
    result = classify_job(job_intern, config)
    assert result.accepted is False
    assert result.confidence == "low"


def test_software_engineer_with_tech_medium(job_software_engineer_with_tech, config):
    result = classify_job(job_software_engineer_with_tech, config)
    assert result.accepted is True
    assert result.confidence == "medium"
    assert result.category is not None
    assert len(result.matched_technologies) > 0


def test_software_engineer_no_tech_rejected(job_software_engineer_no_tech, config):
    result = classify_job(job_software_engineer_no_tech, config)
    assert result.accepted is False
    assert result.confidence == "low"


def test_rejected_blockchain(config):
    from backend.services.digest.models import NormalizedJob
    job = NormalizedJob(
        id="100", title="Blockchain Developer", company="Crypto Co",
        location="Remote", url="https://example.com",
        source="test", source_id="test-100",
    )
    result = classify_job(job, config)
    assert result.accepted is False


def test_nestjs_developer(config):
    from backend.services.digest.models import NormalizedJob
    job = NormalizedJob(
        id="300", title="NestJS Developer", company="Tech Co",
        location="Remote",
        skills=["nestjs", "node.js", "typescript"],
        url="https://example.com", source="test", source_id="test-300",
    )
    result = classify_job(job, config)
    assert result.accepted is True
    assert result.confidence == "high"
    assert result.category == "backend"


def test_llm_engineer(config):
    from backend.services.digest.models import NormalizedJob
    job = NormalizedJob(
        id="400", title="LLM Engineer", company="AI Lab",
        location="Remote", is_remote=True, remote_type="remote",
        description="Building LLM applications with LangChain and RAG.",
        skills=["python", "langchain", "gpt", "rag"],
        url="https://example.com", source="test", source_id="test-400",
    )
    result = classify_job(job, config)
    assert result.accepted is True
    assert result.confidence == "high"
    assert result.category == "llm"
    assert "llm" in result.reason.lower()


def test_prompt_engineer(config):
    from backend.services.digest.models import NormalizedJob
    job = NormalizedJob(
        id="401", title="Prompt Engineer", company="AI Co",
        location="Remote",
        skills=["prompt engineering", "gpt", "langchain"],
        url="https://example.com", source="test", source_id="test-401",
    )
    result = classify_job(job, config)
    assert result.accepted is True
    assert result.category == "llm"


def test_generative_ai_engineer_with_ai_tech(config):
    from backend.services.digest.models import NormalizedJob
    job = NormalizedJob(
        id="402", title="Generative AI Engineer", company="AI Lab",
        location="Remote",
        description="Building AI agents with LangChain and OpenAI.",
        skills=["openai", "langchain", "agents"],
        url="https://example.com", source="test", source_id="test-402",
    )
    result = classify_job(job, config)
    assert result.accepted is True
    assert result.category in ("ai", "llm")


def test_ai_developer(config):
    from backend.services.digest.models import NormalizedJob
    job = NormalizedJob(
        id="403", title="AI Developer", company="AI Co",
        location="Remote",
        skills=["openai", "python"],
        url="https://example.com", source="test", source_id="test-403",
    )
    result = classify_job(job, config)
    assert result.accepted is True
    assert result.confidence == "high"


def test_ai_platform_engineer(config):
    from backend.services.digest.models import NormalizedJob
    job = NormalizedJob(
        id="404", title="AI Platform Engineer", company="Platform Co",
        location="Remote",
        skills=["llm", "langchain", "vector database"],
        url="https://example.com", source="test", source_id="test-404",
    )
    result = classify_job(job, config)
    assert result.accepted is True
    assert result.category == "llm"


def test_python_developer(config):
    from backend.services.digest.models import NormalizedJob
    job = NormalizedJob(
        id="500", title="Python Developer", company="Dev Co",
        location="Remote",
        description="Building APIs with FastAPI and PostgreSQL.",
        skills=["python", "fastapi", "postgresql"],
        url="https://example.com", source="test", source_id="test-500",
    )
    result = classify_job(job, config)
    assert result.accepted is True
    assert result.confidence == "high"


def test_output_format(job_backend_engineer, config):
    result = classify_job(job_backend_engineer, config)
    assert hasattr(result, "accepted")
    assert hasattr(result, "category")
    assert hasattr(result, "confidence")
    assert hasattr(result, "matched_title")
    assert hasattr(result, "matched_technologies")
    assert hasattr(result, "reason")
    assert isinstance(result.matched_technologies, list)
    assert result.confidence in ("high", "medium", "low")


def test_rejected_reason_contains_explanation(job_sales, config):
    result = classify_job(job_sales, config)
    assert result.reason is not None
    assert len(result.reason) > 0


def test_empty_skills_no_tech(config):
    from backend.services.digest.models import NormalizedJob
    job = NormalizedJob(
        id="600", title="Software Engineer", company="Generic Co",
        location="NYC",
        description="General engineering role.",
        url="https://example.com", source="test", source_id="test-600",
    )
    result = classify_job(job, config)
    assert result.accepted is False
    assert result.confidence == "low"

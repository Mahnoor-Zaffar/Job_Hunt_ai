from backend.services.digest.title_matcher import match_title, _title_matches
from backend.services.digest.models import MatchResult


def test_explicit_backend_engineer(job_backend_engineer, config):
    exp = match_title(job_backend_engineer, config)
    assert exp.result == MatchResult.ACCEPTED
    assert exp.matched_title == "backend engineer"
    assert "Matched explicit accepted title" in exp.reason


def test_explicit_frontend_developer(job_frontend_react, config):
    exp = match_title(job_frontend_react, config)
    assert exp.result == MatchResult.ACCEPTED
    assert exp.matched_title == "frontend developer"


def test_explicit_fullstack(job_fullstack, config):
    exp = match_title(job_fullstack, config)
    assert exp.result == MatchResult.ACCEPTED
    assert "full stack developer" in exp.matched_title


def test_explicit_ai_engineer(job_ai_engineer, config):
    exp = match_title(job_ai_engineer, config)
    assert exp.result == MatchResult.ACCEPTED
    assert exp.matched_title == "ai engineer"


def test_explicit_devops(job_devops, config):
    exp = match_title(job_devops, config)
    assert exp.result == MatchResult.ACCEPTED
    assert exp.matched_title == "devops engineer"


def test_rejected_sales(job_sales, config):
    exp = match_title(job_sales, config)
    assert exp.result == MatchResult.REJECTED_KEYWORD
    assert "sales" in exp.reason


def test_rejected_intern(job_intern, config):
    exp = match_title(job_intern, config)
    assert exp.result == MatchResult.REJECTED_INTERNSHIP


def test_related_software_engineer_with_tech(job_software_engineer_with_tech, config):
    exp = match_title(job_software_engineer_with_tech, config)
    assert exp.result == MatchResult.ACCEPTED
    assert exp.matched_title == "software engineer"
    assert "related" in exp.reason


def test_rejected_unknown_title(config):
    from backend.services.digest.models import NormalizedJob
    job = NormalizedJob(
        id="99",
        title="Chief Happiness Officer",
        company="Fun Co",
        location="Remote",
        url="https://example.com/jobs/99",
        source="test",
        source_id="test-99",
    )
    exp = match_title(job, config)
    assert exp.result == MatchResult.REJECTED_TITLE


def test_rejected_blockchain(config):
    from backend.services.digest.models import NormalizedJob
    job = NormalizedJob(
        id="100",
        title="Blockchain Developer",
        company="Crypto Co",
        location="Remote",
        url="https://example.com",
        source="test",
        source_id="test-100",
    )
    exp = match_title(job, config)
    assert exp.result == MatchResult.REJECTED_KEYWORD


def test_rejected_wordpress(config):
    from backend.services.digest.models import NormalizedJob
    job = NormalizedJob(
        id="101",
        title="WordPress Developer",
        company="Agency",
        location="Remote",
        url="https://example.com",
        source="test",
        source_id="test-101",
    )
    exp = match_title(job, config)
    assert exp.result == MatchResult.REJECTED_KEYWORD


def test_rejected_hr(config):
    from backend.services.digest.models import NormalizedJob
    job = NormalizedJob(
        id="102",
        title="HR Manager",
        company="Corp",
        location="NYC",
        url="https://example.com",
        source="test",
        source_id="test-102",
    )
    exp = match_title(job, config)
    assert exp.result == MatchResult.REJECTED_KEYWORD


def test_rejected_recruiter(config):
    from backend.services.digest.models import NormalizedJob
    job = NormalizedJob(
        id="103",
        title="Technical Recruiter",
        company="Agency",
        location="Remote",
        url="https://example.com",
        source="test",
        source_id="test-103",
    )
    exp = match_title(job, config)
    assert exp.result == MatchResult.REJECTED_KEYWORD


def test_rejected_qa_tester(config):
    from backend.services.digest.models import NormalizedJob
    job = NormalizedJob(
        id="104",
        title="QA Tester",
        company="Tech Co",
        location="Remote",
        url="https://example.com",
        source="test",
        source_id="test-104",
    )
    exp = match_title(job, config)
    assert exp.result == MatchResult.REJECTED_KEYWORD


def test_related_sde(config):
    from backend.services.digest.models import NormalizedJob
    job = NormalizedJob(
        id="105",
        title="SDE II",
        company="Amazon",
        location="Seattle",
        url="https://example.com",
        source="test",
        source_id="test-105",
    )
    exp = match_title(job, config)
    assert exp.result == MatchResult.ACCEPTED
    assert exp.matched_title == "sde"


def test_title_matches():
    assert _title_matches("backend engineer", "backend engineer") is True
    assert _title_matches("senior backend engineer", "backend engineer") is True
    assert _title_matches("backend engineer ii", "backend engineer") is True
    assert _title_matches("frontend developer", "frontend developer") is True
    assert _title_matches("senior frontend engineer", "frontend engineer") is True
    assert _title_matches("full stack developer", "full stack developer") is True


def test_title_no_match():
    assert _title_matches("sales representative", "backend engineer") is False
    assert _title_matches("marketing manager", "react developer") is False


def test_variant_sre(config):
    from backend.services.digest.models import NormalizedJob
    job = NormalizedJob(
        id="106",
        title="SRE",
        company="Cloud Co",
        location="Remote",
        url="https://example.com",
        source="test",
        source_id="test-106",
    )
    exp = match_title(job, config)
    assert exp.result == MatchResult.ACCEPTED

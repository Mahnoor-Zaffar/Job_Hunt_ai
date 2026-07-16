"""Tests for the intelligence layer — scoring, embeddings, resume parsing."""

import pytest

from backend.ai.intelligence.embeddings import EmbeddingService
from backend.ai.intelligence.matching import MatchingEngine
from backend.ai.intelligence.resume import ResumeIntelligence
from backend.ai.intelligence.scoring import FactorScorer, MatchResult
from backend.models.job import Job

SAMPLE_RESUME = """
John Doe
john@example.com
+1-555-0123
Islamabad, Pakistan

SUMMARY
Senior backend engineer with 8 years of experience building scalable systems.

SKILLS
Python, FastAPI, Docker, Kubernetes, PostgreSQL, Redis, AWS, GraphQL, TypeScript, React

EXPERIENCE
Senior Software Engineer at Acme Corp (2020 - Present)
- Led migration to microservices architecture
- Built real-time data pipeline processing 1M events/day

Backend Engineer at StartupCo (2017 - 2020)
- Designed REST APIs serving 100K users
- Implemented CI/CD pipeline with GitHub Actions

EDUCATION
B.Sc. Computer Science from NUST (2017)

CERTIFICATIONS
AWS Solutions Architect
Kubernetes Administrator (CKA)

PROJECTS
Open source contributions to FastAPI framework
"""


class TestFactorScorer:
    @pytest.fixture
    def scorer(self) -> FactorScorer:
        return FactorScorer()

    def test_perfect_skills_match(self, scorer: FactorScorer) -> None:
        job = Job(
            title="Backend Engineer",
            company="Acme",
            location="Islamabad",
            url="https://x.com",
            source="test",
            source_id="t1",
            fingerprint="fp1",
            skills=["Python", "Docker", "PostgreSQL"],
            experience_level="senior",
        )
        engine = MatchingEngine(scorer=scorer)
        result = engine.match(
            candidate_skills=["Python", "Docker", "PostgreSQL", "AWS"],
            job=job,
            candidate_experience_years=8,
            candidate_location="Islamabad",
        )
        assert result.overall_score > 0.7
        assert "python" in result.skills_matched
        assert result.deterministic is True

    def test_no_skills_match(self, scorer: FactorScorer) -> None:
        job = Job(
            title="Backend Engineer",
            company="Acme",
            location="Islamabad",
            url="https://x.com",
            source="test",
            source_id="t1",
            fingerprint="fp2",
            skills=["Python", "Docker", "PostgreSQL"],
        )
        engine = MatchingEngine(scorer=scorer)
        result = engine.match(
            candidate_skills=["Java", "Spring", "Oracle"],
            job=job,
        )
        assert result.overall_score < 0.6
        assert len(result.skills_matched) == 0
        assert len(result.skills_missing) > 0

    def test_location_match(self, scorer: FactorScorer) -> None:
        job = Job(
            title="Engineer",
            company="Co",
            location="Islamabad, Pakistan",
            url="https://x.com",
            source="test",
            source_id="t1",
            fingerprint="fp3",
        )
        engine = MatchingEngine(scorer=scorer)
        result = engine.match(
            candidate_skills=["Python"],
            job=job,
            candidate_location="Islamabad, Pakistan",
        )
        assert result.factor_scores["location"] == 1.0

    def test_remote_preference(self, scorer: FactorScorer) -> None:
        job = Job(
            title="Engineer",
            company="Co",
            location="Remote",
            url="https://x.com",
            source="test",
            source_id="t1",
            fingerprint="fp4",
            is_remote=True,
        )
        engine = MatchingEngine(scorer=scorer)
        result = engine.match(
            candidate_skills=["Python"],
            job=job,
            candidate_remote=True,
        )
        assert result.factor_scores["remote_preference"] == 1.0

    def test_match_result_has_structure(self, scorer: FactorScorer) -> None:
        job = Job(
            title="Engineer",
            company="Co",
            location="Remote",
            url="https://x.com",
            source="test",
            source_id="t1",
            fingerprint="fp5",
            skills=["Python", "AWS"],
        )
        engine = MatchingEngine(scorer=scorer)
        result = engine.match(
            candidate_skills=["Python", "Docker"],
            job=job,
            candidate_experience_years=5,
            candidate_location="Islamabad",
            candidate_remote=True,
        )
        assert isinstance(result, MatchResult)
        assert 0.0 <= result.overall_score <= 1.0
        assert result.factor_scores
        assert isinstance(result.strengths, list)
        assert isinstance(result.weaknesses, list)
        assert isinstance(result.recommendations, list)

    def test_batch_matching_sorts(self, scorer: FactorScorer) -> None:
        jobs = [
            Job(
                title="Python Dev",
                company="A",
                location="Remote",
                url="u",
                source="s",
                source_id="1",
                fingerprint="a",
                skills=["Python", "Docker"],
            ),
            Job(
                title="Java Dev",
                company="B",
                location="Remote",
                url="u",
                source="s",
                source_id="2",
                fingerprint="b",
                skills=["Java", "Spring"],
            ),
            Job(
                title="Go Dev",
                company="C",
                location="Remote",
                url="u",
                source="s",
                source_id="3",
                fingerprint="c",
                skills=["Go", "K8s"],
            ),
        ]
        engine = MatchingEngine(scorer=scorer)
        results = engine.match_batch(
            candidate_skills=["Python", "Docker", "FastAPI"],
            jobs=jobs,
            candidate_experience_years=5,
        )
        assert len(results) == 3
        assert results[0][1].overall_score >= results[1][1].overall_score


class TestResumeIntelligence:
    @pytest.fixture
    def parser(self) -> ResumeIntelligence:
        return ResumeIntelligence()

    def test_parse_sections(self, parser: ResumeIntelligence) -> None:
        result = parser.parse(SAMPLE_RESUME)
        assert result.full_name
        assert result.email == "john@example.com"
        assert len(result.skills) > 0
        assert "Python" in result.skills
        assert len(result.experience) > 0
        assert len(result.education) > 0
        assert len(result.certifications) > 0

    def test_parse_empty(self, parser: ResumeIntelligence) -> None:
        result = parser.parse("")
        assert result.full_name == ""
        assert result.skills == []
        assert result.experience == []

    def test_parse_skills_only(self, parser: ResumeIntelligence) -> None:
        result = parser.parse("SKILLS\nPython, Docker, Kubernetes")
        assert "Python" in result.skills

    def test_parse_contact_info(self, parser: ResumeIntelligence) -> None:
        result = parser.parse("Jane Smith\njane@test.com\n+92-300-1234567\nLahore")
        assert result.email == "jane@test.com"
        assert "Lahore" in result.location

    def test_estimate_experience(self, parser: ResumeIntelligence) -> None:
        result = parser.parse(SAMPLE_RESUME)
        assert result.total_experience_years is not None
        assert result.total_experience_years > 0


class TestEmbeddingService:
    def test_embed_returns_vector(self) -> None:
        svc = EmbeddingService()
        vec = svc.embed("Software Engineer with Python experience")
        assert len(vec) > 0
        assert isinstance(vec[0], float)

    def test_similarity_same_text(self) -> None:
        svc = EmbeddingService()
        v = svc.embed("Python developer")
        assert svc.similarity(v, v) > 0.99

    def test_similarity_different_text(self) -> None:
        svc = EmbeddingService()
        a = svc.embed("Python developer")
        b = svc.embed("Java developer")
        score = svc.similarity(a, b)
        assert 0.0 <= score <= 1.0

    def test_embed_batch(self) -> None:
        svc = EmbeddingService()
        vecs = svc.embed_batch(["Python", "Java", "Go"])
        assert len(vecs) == 3
        assert len(vecs[0]) > 0

    def test_embed_job(self) -> None:
        svc = EmbeddingService()
        v = svc.embed_job("Engineer", "Acme", "Build APIs", ["Python", "FastAPI"])
        assert len(v) > 0

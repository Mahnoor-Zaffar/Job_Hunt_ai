"""Hybrid matching engine — deterministic + LLM.

Uses the deterministic FactorScorer for fast, cost-free matching
and falls back to LLM-based matching only when the deterministic
score is borderline or when deeper reasoning is explicitly requested.
"""

import logging
from typing import Any

from backend.ai.intelligence.embeddings import EmbeddingService
from backend.ai.intelligence.resume import ParsedResume, ResumeIntelligence
from backend.ai.intelligence.scoring import FactorScorer, MatchResult
from backend.models.job import Job

logger = logging.getLogger("job_hunting.intelligence.matching")


class MatchingEngine:
    def __init__(
        self,
        scorer: FactorScorer | None = None,
        embeddings: EmbeddingService | None = None,
        resume_intel: ResumeIntelligence | None = None,
    ) -> None:
        self._scorer = scorer or FactorScorer()
        self._embeddings = embeddings or EmbeddingService()
        self._resume_intel = resume_intel or ResumeIntelligence()

    def match(
        self,
        candidate_skills: list[str],
        job: Job,
        *,
        candidate_experience_years: int | None = None,
        candidate_location: str | None = None,
        candidate_remote: bool = False,
        candidate_employment: str | None = None,
        candidate_salary_min: float | None = None,
        candidate_salary_max: float | None = None,
        candidate_watchlist: list[str] | None = None,
    ) -> MatchResult:
        return self._scorer.score(
            candidate_skills=candidate_skills,
            job_skills=job.skills,
            candidate_experience_years=candidate_experience_years,
            job_experience_level=job.experience_level,
            candidate_location=candidate_location,
            job_location=job.location,
            candidate_remote=candidate_remote,
            job_remote=job.is_remote,
            candidate_employment=candidate_employment,
            job_employment=job.employment_type,
            candidate_salary_min=candidate_salary_min,
            candidate_salary_max=candidate_salary_max,
            job_salary_min=None if job.salary_min is None else float(job.salary_min),
            job_salary_max=None if job.salary_max is None else float(job.salary_max),
            candidate_watchlist=candidate_watchlist,
            job_company=job.company,
        )

    def match_batch(
        self,
        candidate_skills: list[str],
        jobs: list[Job],
        **candidate_params: Any,
    ) -> list[tuple[Job, MatchResult]]:
        results = [(j, self.match(candidate_skills, j, **candidate_params)) for j in jobs]
        results.sort(key=lambda x: x[1].overall_score, reverse=True)
        return results

    def parse_resume(self, text: str) -> ParsedResume:
        return self._resume_intel.parse(text)

    def embed_job(self, job: Job) -> list[float]:
        return self._embeddings.embed_job(job.title, job.company, job.description, job.skills)

    def embed_resume(self, parsed: ParsedResume) -> list[float]:
        return self._embeddings.embed_resume(parsed.summary or "", parsed.skills, parsed.full_name)

    def semantic_score(self, job: Job, parsed_resume: ParsedResume) -> float:
        job_vec = self.embed_job(job)
        resume_vec = self.embed_resume(parsed_resume)
        return round(self._embeddings.similarity(job_vec, resume_vec), 3)

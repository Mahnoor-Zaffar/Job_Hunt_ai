"""Semantic job matching using OpenRouter.

Compares a candidate's resume/skills against job descriptions and
returns a match score with detailed reasoning.  Designed to be
replaced or augmented by local embedding-based matching via
sentence-transformers when installed.
"""

import json as json_mod
import logging
import re
from typing import Any

from backend.ai.client import OpenRouterClient
from backend.models.job import Job

logger = logging.getLogger("job_hunting.ai.matching")

MATCHING_PROMPT = """Compare the candidate profile against this job description.
Return ONLY valid JSON with these keys:
- match_score: float between 0.0 and 1.0 (0=no match, 1=perfect)
- skills_match: list of skills that match between candidate and job
- skills_missing: list of required skills the candidate lacks
- strengths: list of strings explaining why the candidate is a good fit
- weaknesses: list of strings explaining gaps
- fit_summary: one-sentence summary of the match

Candidate Profile:
{candidate_profile}

Job Description:
{job_description}

Job Title: {job_title}
Company: {company}
Required Skills: {skills}"""


class JobMatcher:
    """Matches candidates to jobs using LLM-based comparison."""

    def __init__(self, client: OpenRouterClient | None = None) -> None:
        self._client = client or OpenRouterClient()

    async def match(
        self,
        candidate_profile: str,
        job: Job,
    ) -> dict[str, Any]:
        prompt = MATCHING_PROMPT.format(
            candidate_profile=candidate_profile[:4000],
            job_description=(job.description or "")[:4000],
            job_title=job.title,
            company=job.company,
            skills=", ".join(job.skills) if job.skills else "Not specified",
        )
        response = await self._client.chat(
            [{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=1024,
        )
        return self._extract_json(response)

    async def match_batch(
        self,
        candidate_profile: str,
        jobs: list[Job],
    ) -> list[tuple[Job, dict[str, Any]]]:
        results: list[tuple[Job, dict[str, Any]]] = []
        for job in jobs:
            try:
                match_result = await self.match(candidate_profile, job)
                results.append((job, match_result))
            except Exception:
                logger.exception("Match failed for job %s", job.id)
                results.append((job, {"match_score": 0.0, "error": "matching failed"}))
        results.sort(key=lambda x: float(x[1].get("match_score", 0)), reverse=True)
        return results

    def _extract_json(self, text: str) -> dict[str, Any]:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                result = json_mod.loads(match.group(0))
                return result  # type: ignore[no-any-return]
            except json_mod.JSONDecodeError:
                pass
        return {"match_score": 0.0, "raw_response": text}

    async def close(self) -> None:
        await self._client.close()

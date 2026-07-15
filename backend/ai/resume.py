"""AI-powered resume parsing and optimisation.

Resume parsing uses OpenRouter to extract structured data from
unstructured resume text (PDF content, plain text, etc.).

Resume optimisation tailors a resume to a specific job description by
rewriting bullet points and emphasising relevant skills.
"""

import json as json_mod
import logging
import re
from typing import Any

from backend.ai.client import OpenRouterClient

logger = logging.getLogger("job_hunting.ai.resume")

RESUME_EXTRACTION_PROMPT = """Extract structured data from this resume. Return ONLY valid JSON with these keys:
- full_name: string
- email: string
- phone: string | null
- location: string | null
- summary: string | null
- skills: list of strings
- experiences: list of {title: string, company: string, dates: string, highlights: list of strings}
- education: list of {degree: string, school: string, year: string | null}
- certifications: list of strings
- languages: list of strings

Resume text:
{resume_text}"""

RESUME_OPTIMISATION_PROMPT = """Rewrite the following resume bullet points to better match this job description.
Focus on highlighting skills and experiences that are most relevant.

Job Description:
{job_description}

Current Resume Content:
{resume_text}

Return ONLY the rewritten resume content with bullet points. Do NOT invent qualifications the candidate doesn't have.
Do NOT include explanations — just the rewritten resume text."""


class ResumeParser:
    """Extracts structured data from resume text using OpenRouter."""

    def __init__(self, client: OpenRouterClient | None = None) -> None:
        self._client = client or OpenRouterClient()

    async def parse(self, resume_text: str) -> dict[str, Any]:
        prompt = RESUME_EXTRACTION_PROMPT.format(resume_text=resume_text[:8000])
        response = await self._client.chat(
            [{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=2048,
        )
        return self._extract_json(response)

    async def optimise(self, resume_text: str, job_description: str) -> str:
        prompt = RESUME_OPTIMISATION_PROMPT.format(
            resume_text=resume_text[:6000],
            job_description=job_description[:4000],
        )
        return await self._client.chat(
            [{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=2048,
        )

    def _extract_json(self, text: str) -> dict[str, Any]:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                result = json_mod.loads(match.group(0))
                return result  # type: ignore[no-any-return]
            except json_mod.JSONDecodeError:
                pass
        return {"raw_response": text}

    async def close(self) -> None:
        await self._client.close()

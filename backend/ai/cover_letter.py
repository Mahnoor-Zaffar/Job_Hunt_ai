"""Cover letter generation using OpenRouter.

Generates tailored cover letters based on a candidate's resume and
a specific job description.  The output is professional, concise,
and customised to the opportunity.
"""

import logging

from backend.ai.client import OpenRouterClient

logger = logging.getLogger("job_hunting.ai.cover_letter")

COVER_LETTER_PROMPT = """Write a professional cover letter for the following job application.
The cover letter should be concise (200-400 words), highlight relevant experience,
and express genuine interest in the role and company.

Job Title: {job_title}
Company: {company}
Job Description:
{job_description}

Candidate Profile:
{candidate_profile}

Additional Notes: {notes}

Write the cover letter. Use a professional tone. Address it to "Hiring Manager".
Format with a salutation, 2-3 body paragraphs that connect the candidate's experience
to the job requirements, and a closing. Do NOT include placeholders — use the actual
candidate information provided."""


class CoverLetterGenerator:
    """Generates tailored cover letters using LLM."""

    def __init__(self, client: OpenRouterClient | None = None) -> None:
        self._client = client or OpenRouterClient()

    async def generate(
        self,
        job_title: str,
        company: str,
        job_description: str,
        candidate_profile: str,
        *,
        notes: str = "",
    ) -> str:
        prompt = COVER_LETTER_PROMPT.format(
            job_title=job_title,
            company=company,
            job_description=job_description[:4000],
            candidate_profile=candidate_profile[:4000],
            notes=notes or "No additional notes.",
        )
        return await self._client.chat(
            [{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1024,
        )

    async def close(self) -> None:
        await self._client.close()

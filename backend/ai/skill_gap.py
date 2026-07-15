"""Skill gap analysis using OpenRouter.

Compares a candidate's current skills against a target role's
requirements and identifies what's missing, what to prioritise,
and generates a learning roadmap.
"""

import json as json_mod
import logging
import re
from typing import Any

from backend.ai.client import OpenRouterClient

logger = logging.getLogger("job_hunting.ai.skill_gap")

SKILL_GAP_PROMPT = """Analyse the skill gap between this candidate and the target job.
Return ONLY valid JSON with these keys:

- matching_skills: list of skills the candidate already has that match
- missing_skills: list of skills the candidate needs to acquire
- partial_skills: list of skills where candidate has some but not full proficiency
- priority_order: list of skills ordered by importance to learn first
- estimated_timeframe: rough estimate (e.g., "2-3 months")
- learning_resources: list of 3-5 suggested resources (courses, books, projects)
- summary: one-paragraph summary of the skill gap

Current Skills: {current_skills}

Target Role: {target_role}
Required Skills from Job: {required_skills}
Job Description:
{job_description}"""


class SkillGapAnalyser:
    """Analyzes skill gaps and recommends learning paths."""

    def __init__(self, client: OpenRouterClient | None = None) -> None:
        self._client = client or OpenRouterClient()

    async def analyse(
        self,
        current_skills: list[str],
        target_role: str,
        required_skills: list[str],
        job_description: str = "",
    ) -> dict[str, Any]:
        prompt = SKILL_GAP_PROMPT.format(
            current_skills=", ".join(current_skills) if current_skills else "Not specified",
            target_role=target_role,
            required_skills=", ".join(required_skills) if required_skills else "Not specified",
            job_description=job_description[:3000],
        )
        response = await self._client.chat(
            [{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1024,
        )
        return self._extract_json(response)

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

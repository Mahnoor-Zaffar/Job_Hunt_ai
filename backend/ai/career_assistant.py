"""Career Assistant — AI-powered job search companion.

Provides resume optimization, cover letters, interview preparation,
application assistance, and career insights — all powered by the
underlying AI platform with structured outputs and validation.
"""

import logging
from typing import Any

from backend.ai.context.builders import build_job_context
from backend.ai.services.ai_service import AIService
from backend.models.job import Job

logger = logging.getLogger("job_hunting.ai.career_assistant")


class CareerAssistant:
    """AI career assistant powered by the platform layer."""

    def __init__(self, ai_service: AIService | None = None) -> None:
        self._ai = ai_service or AIService()

    # -- Resume Optimization -------------------------------------------------

    async def rewrite_bullets(self, bullets: str) -> str:
        result = await self._ai.generate_text(
            "resume.rewrite_bullets",
            {"bullets": bullets[:3000]},
            temperature=0.5,
        )
        return result

    async def suggest_keywords(self, job_description: str, current_skills: str) -> list[str]:
        result = await self._ai.generate_json(
            "resume.suggest_keywords",
            {
                "job_description": job_description[:3000],
                "current_skills": current_skills,
            },
            required_keys=["keywords"],
        )
        result_data = result.get("keywords", [])
        return result_data  # type: ignore[no-any-return]

    async def optimise_resume(self, resume_text: str, job: Job) -> str:
        job_ctx = build_job_context(job)
        result = await self._ai.generate_text(
            "resume.optimise",
            {"resume_text": resume_text[:4000], "job_description": job_ctx[:4000]},
            temperature=0.5,
        )
        return result

    # -- Cover Letters -------------------------------------------------------

    async def generate_cover_letter(
        self,
        job: Job,
        candidate_profile: str,
        notes: str = "",
    ) -> str:
        return await self._ai.generate_text(
            "cover_letter.generate",
            {
                "job_title": job.title,
                "company": job.company,
                "job_description": (job.description or "")[:4000],
                "candidate_profile": candidate_profile[:4000],
                "notes": notes or "No additional notes.",
            },
            temperature=0.7,
        )

    # -- Interview Preparation -----------------------------------------------

    async def technical_questions(self, job: Job) -> list[dict[str, Any]]:
        result = await self._ai.generate_json(
            "interview.technical",
            {
                "job_title": job.title,
                "job_description": (job.description or "")[:3000],
                "skills": ", ".join(job.skills) if job.skills else "Not specified",
            },
            required_keys=["questions"],
        )
        result_data = result.get("questions", [])
        return result_data  # type: ignore[no-any-return]

    async def behavioral_questions(self, job: Job) -> list[dict[str, Any]]:
        result = await self._ai.generate_json(
            "interview.behavioral",
            {
                "job_title": job.title,
                "company": job.company,
                "experience_level": job.experience_level or "mid",
            },
            required_keys=["questions"],
        )
        result_data = result.get("questions", [])
        return result_data  # type: ignore[no-any-return]

    async def company_questions(self, company: str) -> list[dict[str, Any]]:
        result = await self._ai.generate_json(
            "interview.company",
            {"company": company},
            required_keys=["questions"],
        )
        result_data = result.get("questions", [])
        return result_data  # type: ignore[no-any-return]

    async def follow_up_questions(self, job: Job) -> list[dict[str, Any]]:
        result = await self._ai.generate_json(
            "interview.follow_up",
            {"job_title": job.title, "company": job.company},
            required_keys=["questions"],
        )
        result_data = result.get("questions", [])
        return result_data  # type: ignore[no-any-return]

    async def full_interview_prep(self, job: Job) -> dict[str, Any]:
        import asyncio

        results = await asyncio.gather(
            self.technical_questions(job),
            self.behavioral_questions(job),
            self.company_questions(job.company),
            self.follow_up_questions(job),
        )
        return {
            "technical": results[0],
            "behavioral": results[1],
            "company_specific": results[2],
            "questions_to_ask": results[3],
        }

    # -- Application Assistance ----------------------------------------------

    async def short_answer(self, question: str, candidate_profile: str, job: Job) -> str:
        return await self._ai.generate_text(
            "application.short_answer",
            {
                "question": question,
                "candidate_profile": candidate_profile[:2000],
                "job_title": job.title,
                "company": job.company,
            },
            temperature=0.5,
        )

    async def motivation_statement(self, job: Job, candidate_profile: str) -> str:
        return await self._ai.generate_text(
            "application.motivation",
            {
                "company": job.company,
                "job_title": job.title,
                "job_description": (job.description or "")[:3000],
                "candidate_profile": candidate_profile[:3000],
            },
            temperature=0.7,
        )

    async def salary_guidance(
        self,
        job_title: str,
        location: str,
        experience_level: str,
        skills: str,
    ) -> dict[str, Any]:
        result = await self._ai.generate_json(
            "application.salary",
            {
                "job_title": job_title,
                "location": location,
                "experience_level": experience_level,
                "skills": skills,
            },
            required_keys=["talking_points"],
        )
        return result

    async def relocation_response(
        self,
        job_location: str,
        candidate_location: str,
        remote_status: str,
    ) -> str:
        return await self._ai.generate_text(
            "application.relocation",
            {
                "job_location": job_location,
                "candidate_location": candidate_location,
                "remote_status": remote_status,
            },
            temperature=0.5,
        )

    # -- Career Insights -----------------------------------------------------

    async def job_summary(self, job: Job) -> list[str]:
        result = await self._ai.generate_json(
            "career.job_summary",
            {
                "job_title": job.title,
                "company": job.company,
                "job_description": (job.description or "")[:3000],
            },
            required_keys=["summary"],
        )
        result_data = result.get("summary", [])
        return result_data  # type: ignore[no-any-return]

    async def company_summary(self, company_name: str) -> str:
        return await self._ai.generate_text(
            "career.company_summary",
            {"company_name": company_name},
            temperature=0.5,
        )

    async def technology_demand(self, technologies: list[str]) -> list[dict[str, Any]]:
        result = await self._ai.generate_json(
            "career.tech_demand",
            {"technologies": ", ".join(technologies)},
            required_keys=["technologies"],
        )
        result_data = result.get("technologies", [])
        return result_data  # type: ignore[no-any-return]

    # -- Skill Gap Analysis -------------------------------------------------

    async def skill_gap_analysis(
        self,
        current_skills: list[str],
        job: Job,
    ) -> dict[str, Any]:
        return await self._ai.generate_json(
            "skill_gap.analyse",
            {
                "current_skills": ", ".join(current_skills) if current_skills else "None",
                "target_role": job.title,
                "required_skills": ", ".join(job.skills) if job.skills else "Not specified",
                "job_description": (job.description or "")[:3000],
            },
            required_keys=["missing_skills", "priority_order"],
        )

    # -- Utilities -----------------------------------------------------------

    def get_stats(self) -> dict[str, Any]:
        return self._ai.get_stats()

    async def close(self) -> None:
        await self._ai.close()

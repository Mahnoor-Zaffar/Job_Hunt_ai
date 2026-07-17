"""Career enhancement features — company research, contact discovery,
application emails, interview story bank, scam detection, negotiation.
"""

import logging
from typing import Any

from backend.ai.services.ai_service import AIService
from backend.models.job import Job

logger = logging.getLogger("job_hunting.career_enhancements")


class CareerEnhancer:
    def __init__(self, ai_service: AIService | None = None) -> None:
        self._ai = ai_service or AIService()

    async def detect_archetype(self, job: Job) -> dict[str, Any]:
        return await self._ai.generate_json(
            "career.archetype",
            {
                "job_title": job.title,
                "company": job.company,
                "description": (job.description or "")[:3000],
                "skills": ", ".join(job.skills) if job.skills else "",
            },
            model="anthropic/claude-3.5-sonnet",
            required_keys=["archetype", "confidence", "sub_archetype"],
        )

    async def full_evaluation(
        self, job: Job, cv_text: str, candidate_profile: str = ""
    ) -> dict[str, Any]:
        return await self._ai.generate_json(
            "career.full_eval",
            {
                "job_title": job.title,
                "company": job.company,
                "location": job.location,
                "description": (job.description or "")[:4000],
                "skills": ", ".join(job.skills) if job.skills else "",
                "cv_text": cv_text[:4000],
                "candidate_profile": candidate_profile[:2000],
            },
            model="anthropic/claude-3.5-sonnet",
            required_keys=["overall_score", "block_a", "block_b", "block_c", "block_d", "block_e", "block_f"],
        )

    async def company_deep_research(self, company_name: str) -> dict[str, Any]:
        return await self._ai.generate_json(
            "career.company_research",
            {"company_name": company_name},
            model="anthropic/claude-3.5-sonnet",
            required_keys=["ai_strategy", "engineering_culture", "recent_moves"],
        )

    async def contact_discovery(
        self, company_name: str, job_title: str = "", job_id: str = ""
    ) -> dict[str, Any]:
        result = await self._ai.generate_json(
            "career.contact_discovery",
            {"company_name": company_name, "job_title": job_title},
            model="anthropic/claude-3.5-sonnet",
            required_keys=["likely_roles", "linkedin_search_tips"],
        )
        result["hiring_manager_message"] = await self._linkedin_draft(
            company_name, job_title, "hiring_manager", result
        )
        result["recruiter_message"] = await self._linkedin_draft(
            company_name, job_title, "recruiter", result
        )
        return result

    async def _linkedin_draft(
        self, company: str, role: str, contact_type: str, context: dict[str, Any]
    ) -> str:
        return await self._ai.generate_text(
            "career.linkedin_message",
            {
                "company": company,
                "role": role,
                "contact_type": contact_type,
                "context": str(context.get("likely_roles", ""))[:500],
            },
            temperature=0.7,
            max_tokens=400,
        )

    async def application_email(
        self,
        job: Job,
        email_type: str,
        candidate_profile: str,
    ) -> dict[str, str]:
        text = await self._ai.generate_text(
            "career.app_email",
            {
                "company": job.company,
                "job_title": job.title,
                "email_type": email_type,
                "candidate_profile": candidate_profile[:2000],
                "job_description": (job.description or "")[:2000],
            },
            temperature=0.5,
            max_tokens=800,
        )
        lines = text.split("\n")
        subject = ""
        body_lines: list[str] = []
        for line in lines:
            if line.lower().startswith("subject:"):
                subject = line.split(":", 1)[1].strip()
            else:
                body_lines.append(line)
        return {"subject": subject or f"Application: {job.title} at {job.company}", "body": "\n".join(body_lines).strip()}

    async def interview_story_bank(
        self, candidate_profile: str, job: Job
    ) -> dict[str, Any]:
        return await self._ai.generate_json(
            "career.story_bank",
            {
                "candidate_profile": candidate_profile[:3000],
                "job_title": job.title,
                "company": job.company,
            },
            model="anthropic/claude-3.5-sonnet",
            required_keys=["stories"],
        )

    async def scam_check(self, job: Job) -> dict[str, Any]:
        return await self._ai.generate_json(
            "career.scam_check",
            {
                "job_title": job.title,
                "company": job.company,
                "description": (job.description or "")[:3000],
            },
            model="anthropic/claude-3.5-sonnet",
            required_keys=["risk_score", "red_flags"],
        )

    async def negotiation_script(
        self, job: Job, candidate_skills: list[str], target_salary: str = ""
    ) -> dict[str, Any]:
        return await self._ai.generate_json(
            "career.negotiation",
            {
                "job_title": job.title,
                "company": job.company,
                "skills": ", ".join(candidate_skills) if candidate_skills else "Not specified",
                "target_salary": target_salary or "Market rate",
            },
            model="anthropic/claude-3.5-sonnet",
            required_keys=["talking_points", "scripts"],
        )

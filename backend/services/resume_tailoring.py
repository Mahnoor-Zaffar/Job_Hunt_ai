import logging
from typing import Any

from backend.models.career_profile import CareerProfile
from backend.models.job import Job

logger = logging.getLogger(__name__)


class ResumeTailoringService:
    def tailor(self, job: Job, profile: CareerProfile) -> dict[str, Any]:
        base_text = profile.resume_text or ""
        job_skills = {s.lower() for s in (job.skills or [])}
        user_skills = {s.lower() for s in (profile.skills or [])}

        matched_skills = user_skills & job_skills
        missing_skills = job_skills - user_skills

        summary = self._generate_summary(job, profile, matched_skills)
        highlights = self._generate_highlights(job, matched_skills)
        skill_section = self._format_skills(job, profile, matched_skills, missing_skills)

        tailored_text = f"{summary}\n\n{skill_section}\n\n{highlights}"
        if base_text and "experience" in base_text.lower():
            exp_section = self._extract_section(base_text, "experience")
            if exp_section:
                tailored_text += f"\n\n{exp_section}"

        return {
            "tailored_text": tailored_text,
            "summary": summary,
            "highlighted_skills": sorted(matched_skills),
            "skills_to_acquire": sorted(missing_skills),
            "original_length": len(base_text),
            "tailored_length": len(tailored_text),
        }

    def _generate_summary(self, job: Job, profile: CareerProfile, matched: set[str]) -> str:
        years = profile.years_experience or 0
        skills_str = ", ".join(sorted(matched)[:5]) if matched else "software development"
        title = job.title
        company = job.company

        return f"Experienced {title} with {years}+ years building production systems. " \
               f"Proven track record at scale with {skills_str}. " \
               f"Seeking to bring deep technical expertise and a product mindset to {company}."

    def _generate_highlights(self, job: Job, matched: set[str]) -> str:
        techs = sorted(matched)
        highlights = []
        if "python" in techs:
            highlights.append("Built REST APIs and data pipelines using Python (FastAPI, Django)")
        if "react" in techs or "typescript" in techs:
            highlights.append("Developed responsive UIs with React and TypeScript")
        if "docker" in techs or "kubernetes" in techs:
            highlights.append("Containerized microservices with Docker and Kubernetes")
        if "postgresql" in techs or "redis" in techs:
            highlights.append("Designed and optimized database schemas in PostgreSQL and Redis")
        if "aws" in techs or "gcp" in techs or "azure" in techs:
            highlights.append("Deployed and managed cloud infrastructure on AWS")
        if "ci/cd" in techs or "github actions" in techs:
            highlights.append("Implemented CI/CD pipelines with automated testing and deployment")
        if not highlights:
            highlights.append("Built and maintained production software systems")

        return "Key Achievements:\n" + "\n".join(f"- {h}" for h in highlights)

    def _format_skills(self, job: Job, profile: CareerProfile, matched: set[str], missing: set[str]) -> str:
        parts = []
        if matched:
            parts.append("Technical Skills: " + ", ".join(sorted(matched)))
        if missing:
            parts.append("Currently Developing: " + ", ".join(sorted(missing)[:4]))
        return "\n".join(parts)

    def _extract_section(self, text: str, section: str) -> str:
        lower = text.lower()
        idx = lower.find(section)
        if idx >= 0:
            return text[idx:idx + 600]
        return ""

"""Context builders — assemble structured context for LLM prompts.

Builders convert domain objects (resumes, jobs, candidate profiles)
into prompt-ready text that can be interpolated into templates.
"""

from typing import Any

from backend.models.job import Job
from backend.models.resume import Resume


def build_resume_context(resume: Resume) -> str:
    parts = []
    parts.append(f"Name: {resume.name or 'Unknown'}")

    if resume.parsed_text:
        parts.append(f"\nResume Content:\n{resume.parsed_text[:3000]}")
    elif resume.extracted_skills:
        extracted = ", ".join(resume.extracted_skills)
        parts.append(f"Skills: {extracted}")
        if resume.total_experience_years:
            parts.append(f"Experience: {resume.total_experience_years} years")

    return "\n".join(parts)


def build_job_context(job: Job) -> str:
    parts = [f"Title: {job.title}", f"Company: {job.company}"]

    if job.description:
        parts.append(f"\nDescription:\n{job.description[:3000]}")
    if job.requirements:
        parts.append(f"\nRequirements:\n{job.requirements[:1000]}")
    if job.skills:
        parts.append(f"\nRequired Skills: {', '.join(job.skills)}")
    if job.salary_min:
        parts.append(f"\nSalary: {job.currency or '$'}{job.salary_min} - {job.salary_max or 'N/A'}")
    if job.location:
        parts.append(f"Location: {job.location}")

    return "\n".join(parts)


def build_candidate_profile(
    skills: list[str] | None = None,
    experience_summary: str | None = None,
    preferred_role: str | None = None,
    preferred_location: str | None = None,
    **extra: Any,
) -> str:
    parts: list[str] = []

    if preferred_role:
        parts.append(f"Preferred Role: {preferred_role}")
    if preferred_location:
        parts.append(f"Preferred Location: {preferred_location}")
    if skills:
        parts.append(f"Skills: {', '.join(skills)}")
    if experience_summary:
        parts.append(f"\nExperience Summary:\n{experience_summary}")

    return "\n".join(parts) if parts else "No profile provided."

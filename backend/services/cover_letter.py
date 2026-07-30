from __future__ import annotations

import re
from typing import Any

from backend.models.github_repo import GitHubRepo
from backend.models.job import Job
from backend.services.project_matcher import get_matching_open_source, match_best_repo


def generate_cover_letter(
    job: Job,
    github_repos: list[GitHubRepo],
    profile: dict[str, Any] | None = None,
) -> str:
    title = job.title or "this position"
    company = job.company or "your team"
    description = (job.description or "")[:2000]

    best_repo = match_best_repo(github_repos, title, description)
    os_contributions = get_matching_open_source(github_repos)

    skills_text = _extract_skills(profile)
    company_reason = _derive_company_reason(company, description)

    letter = f"""Dear Hiring Team,

I am writing to express my interest in the {title} position at {company}.
As a self-taught backend engineer with 4 years of experience building
AI-powered applications and scalable APIs in {skills_text}, I bring a
proven ability to learn independently and deliver production systems
from scratch.

One achievement I am particularly proud of is Tayari.ai — an AI-powered
interview platform I architected from the ground up. Built with FastAPI,
Next.js, PostgreSQL, Redis, Supabase, and OpenAI APIs, it orchestrates
end-to-end technical interviews with modular authentication, evaluation
pipelines, and real-time AI feedback. This project reflects my ability
to design complex backend systems and integrate modern LLM technologies
— skills directly relevant to this role.
"""

    if os_contributions:
        names = ", ".join(os_contributions)
        letter += f"""
I have also contributed to open-source projects including {names},
demonstrating my commitment to collaborative engineering and code quality.
"""

    if best_repo and best_repo.repo_name.lower() not in ("tayari.ai", "tayari-ai", "tayari_ai", "tayariai"):
        letter += _build_repo_section(best_repo)

    letter += f"""
I am drawn to {company} because {company_reason}

I would welcome the opportunity to discuss how my experience with AI
systems, backend infrastructure, and product-minded engineering aligns
with {company}'s needs.

You can find my work at github.com/Mahnoor-Zaffar and my professional
background at linkedin.com/in/mahnoor-zaffar.

Best regards,
Mahnoor Zaffar
1999mahnoor@gmail.com | +92 334 0136203
github.com/Mahnoor-Zaffar | linkedin.com/in/mahnoor-zaffar
"""

    return letter.strip()


def _extract_skills(profile: dict[str, Any] | None) -> str:
    if profile and profile.get("skills"):
        skills = [s for s in profile["skills"] if isinstance(s, str)]
        return ", ".join(skills[:6])
    return "Python, FastAPI, Next.js, and TypeScript"


def _derive_company_reason(company: str, description: str) -> str:
    desc_lower = description.lower()
    if "ai" in desc_lower or "machine learning" in desc_lower:
        return f"{company} is pushing the boundaries of AI technology, and I am excited by the prospect of contributing to meaningful, intelligent products."
    if "infrastructure" in desc_lower or "platform" in desc_lower:
        return f"{company}'s focus on scalable infrastructure aligns with my passion for building robust, maintainable backend systems."
    if "remote" in desc_lower:
        return f"{company}'s remote-first culture aligns with how I work best — asynchronously, with ownership and clear communication."
    return f"I admire {company}'s work in the technology space and am excited by the opportunity to contribute to a team building impactful products."


def _build_repo_section(repo: GitHubRepo) -> str:
    name = repo.repo_name
    desc = repo.description or "a personal project"
    lang = repo.language or "modern technologies"
    readme_excerpt = ""
    if repo.readme_text:
        cleaned = re.sub(r"[#*\n\r`]", " ", repo.readme_text[:500])
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        if len(cleaned) > 40:
            readme_excerpt = f" In this project, {cleaned[:180]}."

    return f"""
On GitHub, my project {name} ({desc}) showcases my {lang} expertise.{readme_excerpt}
"""

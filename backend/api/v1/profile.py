"""CareerProfile API — get, update, regenerate, and auto-populate."""

import asyncio
import os
import re
import uuid
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.session import get_db, get_session_factory
from backend.repositories.career_profile import CareerProfileRepository
from backend.repositories.infrastructure import (
    CompanyWatchlistRepository,
    SettingsRepository,
)
from backend.services.career_profile import CareerProfileService

router = APIRouter(prefix="/profile", tags=["profile"])

_POPULATE_TASKS: dict[str, dict[str, Any]] = {}


class CareerProfileResponse(BaseModel):
    id: str
    user_id: str
    skills: list[str] = []
    experience_level: str = "mid"
    years_experience: int = 0
    target_roles: list[str] = []
    preferred_locations: list[str] = []
    remote_preference: str = "no_preference"
    preferred_salary_min: float | None = None
    preferred_companies: list[str] = []
    tech_stack: list[str] = []
    learning_goals: list[str] = []
    resume_text: str | None = None

    class Config:
        from_attributes = True


class CareerProfileUpdate(BaseModel):
    skills: list[str] | None = None
    experience_level: str | None = None
    years_experience: int | None = None
    target_roles: list[str] | None = None
    preferred_locations: list[str] | None = None
    remote_preference: str | None = None
    preferred_salary_min: float | None = None
    preferred_companies: list[str] | None = None
    tech_stack: list[str] | None = None
    learning_goals: list[str] | None = None
    resume_text: str | None = None


class PopulateStatusResponse(BaseModel):
    task_id: str
    status: str
    step: str | None = None
    message: str | None = None
    error: str | None = None


def _to_response(p: object) -> CareerProfileResponse:
    return CareerProfileResponse(
        id=str(p.id),
        user_id=str(p.user_id),
        skills=list(p.skills or []),
        experience_level=p.experience_level,
        years_experience=p.years_experience,
        target_roles=list(p.target_roles or []),
        preferred_locations=list(p.preferred_locations or []),
        remote_preference=p.remote_preference,
        preferred_salary_min=p.preferred_salary_min,
        preferred_companies=list(p.preferred_companies or []),
        tech_stack=list(p.tech_stack or []),
        learning_goals=list(p.learning_goals or []),
        resume_text=p.resume_text,
    )


@router.get("", response_model=CareerProfileResponse)
async def get_profile(
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Query(..., description="User ID"),
) -> CareerProfileResponse:
    repo = CareerProfileRepository(db)
    svc = CareerProfileService(repo)
    profile = await svc.get(user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Career profile not found")
    return _to_response(profile)


@router.put("", response_model=CareerProfileResponse)
async def update_profile(
    body: CareerProfileUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Query(..., description="User ID"),
) -> CareerProfileResponse:
    repo = CareerProfileRepository(db)
    svc = CareerProfileService(repo)
    data = body.model_dump(exclude_none=True)
    profile = await svc.create_or_update(user_id, data)
    return _to_response(profile)


@router.post("/regenerate", response_model=CareerProfileResponse)
async def regenerate_skills(
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Query(..., description="User ID"),
) -> CareerProfileResponse:
    repo = CareerProfileRepository(db)
    svc = CareerProfileService(repo)
    try:
        profile = await svc.regenerate_skills(user_id)
        return _to_response(profile)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/populate")
async def populate_profile(
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Query(..., description="User ID"),
) -> PopulateStatusResponse:
    task_id = f"pop_{uuid.uuid4().hex[:6]}"
    _POPULATE_TASKS[task_id] = {"status": "pending", "step": "initializing"}

    # Read all pre-task data synchronously (within request context)
    settings_repo = SettingsRepository(db)
    skills_str = await settings_repo.get_value(user_id, "alert.skills", "")
    alert_skills = [s.strip() for s in skills_str.split(",") if s.strip()]

    watchlist_repo = CompanyWatchlistRepository(db)
    watchlist = await watchlist_repo.get_by_user(user_id)
    watched_companies = [w.company_name for w in watchlist if w.is_active]

    resume_text, parsed_info = await _parse_resume_pdf()

    async def _run() -> None:
        try:
            _POPULATE_TASKS[task_id]["status"] = "running"

            data: dict[str, Any] = {
                "skills": alert_skills,
                "tech_stack": alert_skills,
                "remote_preference": "remote",
                "preferred_companies": watched_companies[:50],
            }

            if resume_text:
                _POPULATE_TASKS[task_id]["step"] = "processing resume"
                data["resume_text"] = resume_text

                all_skills = list(dict.fromkeys(alert_skills + parsed_info.get("skills", [])))
                data["skills"] = all_skills
                data["tech_stack"] = all_skills

                years = parsed_info.get("years_experience")
                if years:
                    data["years_experience"] = years
                    data["experience_level"] = "senior" if years >= 5 else "mid" if years >= 2 else "junior"

                roles = parsed_info.get("target_roles")
                if roles:
                    data["target_roles"] = roles

            _POPULATE_TASKS[task_id]["step"] = "saving profile"

            async with get_session_factory()() as session:
                repo = CareerProfileRepository(session)
                svc = CareerProfileService(repo)
                await svc.create_or_update(user_id, data)
                await session.commit()

            _POPULATE_TASKS[task_id].update(
                status="success",
                step="completed",
                message=f"Profile populated with {len(data.get('skills', []))} skills, {len(data.get('target_roles', []))} target roles, {len(data.get('preferred_companies', []))} preferred companies",
            )

        except Exception as exc:
            _POPULATE_TASKS[task_id].update(
                status="failed",
                step="error",
                error=str(exc),
            )

    _POPULATE_TASKS[task_id]["task"] = asyncio.create_task(_run())
    _POPULATE_TASKS[task_id]["status"] = "pending"

    return PopulateStatusResponse(task_id=task_id, status="pending", step="initializing")


@router.get("/populate/status", response_model=PopulateStatusResponse)
async def populate_status(
    task_id: str = Query(..., description="Task ID from /populate"),
) -> PopulateStatusResponse:
    task = _POPULATE_TASKS.get(task_id)
    if task is None:
        return PopulateStatusResponse(task_id=task_id, status="not_found")
    return PopulateStatusResponse(
        task_id=task_id,
        status=task.get("status", "unknown"),
        step=task.get("step"),
        message=task.get("message"),
        error=task.get("error"),
    )


async def _parse_resume_pdf() -> tuple[str | None, dict[str, Any]]:
    output_dir = Path(__file__).resolve().parents[3] / "output"
    pdf_files = sorted(output_dir.glob("*.pdf"), key=os.path.getmtime, reverse=True)
    if not pdf_files:
        return None, {}

    pdf_path = pdf_files[0]

    try:
        import fitz

        doc = fitz.open(str(pdf_path))
        text = "".join(page.get_text() for page in doc)
        doc.close()
        text = text.strip()
    except Exception:
        return None, {}

    if not text:
        return text, {}

    info: dict[str, Any] = {}

    try:
        from backend.ai.intelligence.resume import ResumeIntelligence
        from backend.scrapers.technologies.extractor import TechnologyExtractor

        parser = ResumeIntelligence(TechnologyExtractor())
        parsed = parser.parse(text)
        info["skills"] = parsed.skills
        info["years_experience"] = parsed.total_experience_years

        roles = _infer_target_roles(text, parsed)
        info["target_roles"] = roles

    except Exception:
        info["skills"] = _simple_skill_extract(text)
        info["target_roles"] = _infer_target_roles(text)

    return text, info


def _infer_target_roles(text: str, parsed: object | None = None) -> list[str]:
    roles = []
    text_lower = text.lower()
    patterns = [
        (r"\bbackend\s*(?:engineer|developer)\b", "Backend Engineer"),
        (r"\bfrontend\s*(?:engineer|developer)\b", "Frontend Engineer"),
        (r"\bfull.?stack\s*(?:engineer|developer)?\b", "Full Stack Developer"),
        (r"\bdata\s*(?:scientist|engineer|analyst)\b", "Data Scientist"),
        (r"\bdevops\s*(?:engineer)?\b", "DevOps Engineer"),
        (r"\bml\s*(?:engineer)?\b|\bmachine learning\s*(?:engineer)?\b", "ML Engineer"),
        (r"\bpython\s*(?:developer|engineer)\b", "Python Developer"),
        (r"\bsoftware\s*(?:engineer|developer)\b", "Software Engineer"),
        (r"\bai\s*(?:engineer)?\b|\bartificial intelligence\b", "AI Engineer"),
        (r"\bsre\b|\bsite reliability\b", "SRE"),
        (r"\bcloud\s*(?:engineer|architect)\b", "Cloud Engineer"),
        (r"\bsecurity\s*(?:engineer|analyst)\b", "Security Engineer"),
        (r"\bsystems\s*(?:engineer|administrator)\b", "Systems Engineer"),
        (r"\b(?:qa|quality assurance|test)\s*(?:engineer|analyst)\b", "QA Engineer"),
        (r"\bproduct\s*manager\b", "Product Manager"),
        (r"\bplatform\s*(?:engineer)?\b", "Platform Engineer"),
        (r"\bdata\s*engineer\b", "Data Engineer"),
    ]
    seen = set()
    for pattern, role in patterns:
        if re.search(pattern, text_lower) and role not in seen:
            roles.append(role)
            seen.add(role)
    return roles


def _simple_skill_extract(text: str) -> list[str]:
    common_tech = [
        "python", "javascript", "typescript", "java", "go", "rust", "c++", "ruby",
        "react", "angular", "vue", "node.js", "express.js", "django", "flask", "fastapi",
        "docker", "kubernetes", "aws", "gcp", "azure", "terraform", "ansible",
        "postgresql", "mysql", "mongodb", "redis", "sqlite", "elasticsearch",
        "graphql", "rest", "grpc", "websocket", "kafka", "rabbitmq",
        "git", "ci/cd", "jenkins", "github actions", "pytest", "jest",
        "machine learning", "deep learning", "nlp", "llm", "langchain", "pytorch", "tensorflow",
        "sql", "nosql", "linux", "bash", "nginx", "html", "css", "tailwind",
    ]
    text_lower = text.lower()
    found = set()
    for tech in common_tech:
        if tech in text_lower:
            found.add(tech.title() if " " not in tech else tech)
    return sorted(found)

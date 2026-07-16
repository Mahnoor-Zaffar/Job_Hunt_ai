"""Career assistant API — resume, cover letter, interview, application, insights."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import Field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.ai.career_assistant import CareerAssistant
from backend.config.settings import get_settings
from backend.database.session import get_db
from backend.models.job import Job
from backend.repositories.job import JobRepository
from backend.schemas.base import BaseSchema

router = APIRouter(prefix="/career", tags=["career"])


def _check_api_key() -> None:
    settings = get_settings()
    if not settings.OPENROUTER_API_KEY or settings.OPENROUTER_API_KEY == "your-openrouter-api-key":
        raise HTTPException(
            status_code=503,
            detail="AI features require an OpenRouter API key. Set OPENROUTER_API_KEY in your .env file.",
        )


# -- Request/Response schemas -----------------------------------------------


class BulletsRequest(BaseSchema):
    bullets: str


class BulletsResponse(BaseSchema):
    rewritten: str


class KeywordsRequest(BaseSchema):
    job_description: str
    current_skills: str = ""


class KeywordsResponse(BaseSchema):
    keywords: list[str] = Field(default_factory=list)


class CoverLetterRequest(BaseSchema):
    job_id: str
    candidate_profile: str
    notes: str = ""


class CoverLetterResponse(BaseSchema):
    cover_letter: str


class InterviewPrepResponse(BaseSchema):
    technical: list[dict[str, Any]] = Field(default_factory=list)
    behavioral: list[dict[str, Any]] = Field(default_factory=list)
    company_specific: list[dict[str, Any]] = Field(default_factory=list)
    questions_to_ask: list[dict[str, Any]] = Field(default_factory=list)


class ShortAnswerRequest(BaseSchema):
    question: str
    candidate_profile: str
    job_id: str


class ShortAnswerResponse(BaseSchema):
    answer: str


class MotivationRequest(BaseSchema):
    candidate_profile: str
    job_id: str


class MotivationResponse(BaseSchema):
    statement: str


class SalaryGuidanceRequest(BaseSchema):
    job_title: str
    location: str
    experience_level: str
    skills: str = ""


class SalaryGuidanceResponse(BaseSchema):
    data: dict[str, Any] = Field(default_factory=dict)


class RelocationRequest(BaseSchema):
    job_location: str
    candidate_location: str
    remote_status: str = "onsite"


class RelocationResponse(BaseSchema):
    response: str


class JobSummaryResponse(BaseSchema):
    summary: list[str] = Field(default_factory=list)


class CompanySummaryResponse(BaseSchema):
    summary: str


class TechDemandResponse(BaseSchema):
    technologies: list[dict[str, Any]] = Field(default_factory=list)


class SkillGapRequest(BaseSchema):
    current_skills: list[str] = Field(default_factory=list)
    job_id: str


class SkillGapResponse(BaseSchema):
    data: dict[str, Any] = Field(default_factory=dict)


# -- Helpers ----------------------------------------------------------------


async def _get_job(db: AsyncSession, job_id: str) -> Job:
    try:
        jid = uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID") from None
    repo = JobRepository(db)
    job = await repo.get_by_id(jid)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


_assistant = CareerAssistant()

_need_key = Depends(_check_api_key)


# -- Resume Optimization ----------------------------------------------------


@router.post("/resume/rewrite-bullets", response_model=BulletsResponse)
async def rewrite_bullets(body: BulletsRequest, _need_key: None = _need_key) -> BulletsResponse:
    result = await _assistant.rewrite_bullets(body.bullets)
    return BulletsResponse(rewritten=result)


@router.post("/resume/suggest-keywords", response_model=KeywordsResponse)
async def suggest_keywords(body: KeywordsRequest, _need_key: None = _need_key) -> KeywordsResponse:
    keywords = await _assistant.suggest_keywords(body.job_description, body.current_skills)
    return KeywordsResponse(keywords=keywords)


@router.post("/resume/optimise", response_model=BulletsResponse)
async def optimise_resume(_need_key: None = _need_key,
    resume_text: str = Query(..., description="Resume text to optimise"),
    job_id: str = Query(..., description="Target job ID"),
    db: AsyncSession = Depends(get_db),
) -> BulletsResponse:
    job = await _get_job(db, job_id)
    result = await _assistant.optimise_resume(resume_text, job)
    return BulletsResponse(rewritten=result)


# -- Cover Letter -----------------------------------------------------------


@router.post("/cover-letter", response_model=CoverLetterResponse)
async def generate_cover_letter(
    body: CoverLetterRequest,
    _need_key: None = _need_key,
    db: AsyncSession = Depends(get_db),
) -> CoverLetterResponse:
    job = await _get_job(db, body.job_id)
    result = await _assistant.generate_cover_letter(job, body.candidate_profile, body.notes)
    return CoverLetterResponse(cover_letter=result)


# -- Interview Preparation --------------------------------------------------


@router.get("/interview/prep/{job_id}", response_model=InterviewPrepResponse)
async def interview_prep(
    job_id: str,
    _need_key: None = _need_key,
    db: AsyncSession = Depends(get_db),
) -> InterviewPrepResponse:
    job = await _get_job(db, job_id)
    result = await _assistant.full_interview_prep(job)
    return InterviewPrepResponse(**result)


# -- Application Assistance -------------------------------------------------


@router.post("/application/short-answer", response_model=ShortAnswerResponse)
async def short_answer(
    body: ShortAnswerRequest,
    _need_key: None = _need_key,
    db: AsyncSession = Depends(get_db),
) -> ShortAnswerResponse:
    job = await _get_job(db, body.job_id)
    result = await _assistant.short_answer(body.question, body.candidate_profile, job)
    return ShortAnswerResponse(answer=result)


@router.post("/application/motivation", response_model=MotivationResponse)
async def motivation_statement(
    body: MotivationRequest,
    _need_key: None = _need_key,
    db: AsyncSession = Depends(get_db),
) -> MotivationResponse:
    job = await _get_job(db, body.job_id)
    result = await _assistant.motivation_statement(job, body.candidate_profile)
    return MotivationResponse(statement=result)


@router.post("/application/salary-guidance", response_model=SalaryGuidanceResponse)
async def salary_guidance(body: SalaryGuidanceRequest, _need_key: None = _need_key) -> SalaryGuidanceResponse:
    result = await _assistant.salary_guidance(
        body.job_title, body.location, body.experience_level, body.skills
    )
    return SalaryGuidanceResponse(data=result)


@router.post("/application/relocation", response_model=RelocationResponse)
async def relocation_response(body: RelocationRequest, _need_key: None = _need_key) -> RelocationResponse:
    result = await _assistant.relocation_response(
        body.job_location, body.candidate_location, body.remote_status
    )
    return RelocationResponse(response=result)


# -- Career Insights --------------------------------------------------------


@router.get("/insights/job/{job_id}", response_model=JobSummaryResponse)
async def job_summary(
    job_id: str,
    _need_key: None = _need_key,
    db: AsyncSession = Depends(get_db),
) -> JobSummaryResponse:
    job = await _get_job(db, job_id)
    result = await _assistant.job_summary(job)
    return JobSummaryResponse(summary=result)


@router.get("/insights/company/{company_name}", response_model=CompanySummaryResponse)
async def company_summary(company_name: str, _need_key: None = _need_key) -> CompanySummaryResponse:
    result = await _assistant.company_summary(company_name)
    return CompanySummaryResponse(summary=result)


@router.post("/insights/tech-demand", response_model=TechDemandResponse)
async def tech_demand(_need_key: None = _need_key,
    technologies: list[str] = Query(..., description="Technologies to analyze"),
) -> TechDemandResponse:
    result = await _assistant.technology_demand(technologies)
    return TechDemandResponse(technologies=result)


# -- Skill Gap --------------------------------------------------------------


@router.post("/skill-gap", response_model=SkillGapResponse)
async def skill_gap(
    body: SkillGapRequest,
    _need_key: None = _need_key,
    db: AsyncSession = Depends(get_db),
) -> SkillGapResponse:
    job = await _get_job(db, body.job_id)
    result = await _assistant.skill_gap_analysis(body.current_skills, job)
    return SkillGapResponse(data=result)

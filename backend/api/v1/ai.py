from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import Field

from backend.ai.cover_letter import CoverLetterGenerator
from backend.ai.matching import JobMatcher
from backend.ai.resume import ResumeParser
from backend.ai.skill_gap import SkillGapAnalyser
from backend.schemas.base import BaseSchema

router = APIRouter(prefix="/ai", tags=["ai"])


class ResumeParseRequest(BaseSchema):
    resume_text: str


class ResumeParseResponse(BaseSchema):
    data: dict[str, Any] = Field(default_factory=dict)


class ResumeOptimiseRequest(BaseSchema):
    resume_text: str
    job_description: str


class ResumeOptimiseResponse(BaseSchema):
    optimised_text: str


class JobMatchRequest(BaseSchema):
    candidate_profile: str
    job_ids: list[str] = Field(default_factory=list)


class MatchResult(BaseSchema):
    job_id: str
    match_score: float
    skills_match: list[str] = Field(default_factory=list)
    skills_missing: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    fit_summary: str = ""


class JobMatchResponse(BaseSchema):
    results: list[MatchResult] = Field(default_factory=list)


class CoverLetterRequest(BaseSchema):
    job_title: str
    company: str
    job_description: str
    candidate_profile: str
    notes: str = ""


class CoverLetterResponse(BaseSchema):
    cover_letter: str


class SkillGapRequest(BaseSchema):
    current_skills: list[str] = Field(default_factory=list)
    target_role: str
    required_skills: list[str] = Field(default_factory=list)
    job_description: str = ""


class SkillGapResponse(BaseSchema):
    data: dict[str, Any] = Field(default_factory=dict)


@router.post("/resume/parse", response_model=ResumeParseResponse)
async def parse_resume(body: ResumeParseRequest) -> ResumeParseResponse:
    parser = ResumeParser()
    try:
        result = await parser.parse(body.resume_text)
        return ResumeParseResponse(data=result)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/resume/optimise", response_model=ResumeOptimiseResponse)
async def optimise_resume(body: ResumeOptimiseRequest) -> ResumeOptimiseResponse:
    parser = ResumeParser()
    try:
        result = await parser.optimise(body.resume_text, body.job_description)
        return ResumeOptimiseResponse(optimised_text=result)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/match", response_model=JobMatchResponse)
async def match_jobs(body: JobMatchRequest) -> JobMatchResponse:
    import uuid

    from backend.database.session import get_session_factory
    from backend.repositories.job import JobRepository

    matcher = JobMatcher()
    factory = get_session_factory()
    results: list[MatchResult] = []

    async with factory() as session:
        repo = JobRepository(session)
        for job_id_str in body.job_ids[:20]:
            try:
                job_id = uuid.UUID(job_id_str)
                job = await repo.get_by_id(job_id)
                if job is None:
                    continue
                match = await matcher.match(body.candidate_profile, job)
                results.append(
                    MatchResult(
                        job_id=str(job.id),
                        match_score=float(match.get("match_score", 0)),
                        skills_match=match.get("skills_match", []) or [],
                        skills_missing=match.get("skills_missing", []) or [],
                        strengths=match.get("strengths", []) or [],
                        weaknesses=match.get("weaknesses", []) or [],
                        fit_summary=match.get("fit_summary", ""),
                    )
                )
            except Exception:
                continue

    return JobMatchResponse(results=sorted(results, key=lambda r: r.match_score, reverse=True))


@router.post("/cover-letter", response_model=CoverLetterResponse)
async def generate_cover_letter(body: CoverLetterRequest) -> CoverLetterResponse:
    generator = CoverLetterGenerator()
    try:
        result = await generator.generate(
            job_title=body.job_title,
            company=body.company,
            job_description=body.job_description,
            candidate_profile=body.candidate_profile,
            notes=body.notes,
        )
        return CoverLetterResponse(cover_letter=result)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/skill-gap", response_model=SkillGapResponse)
async def analyse_skill_gap(body: SkillGapRequest) -> SkillGapResponse:
    analyser = SkillGapAnalyser()
    try:
        result = await analyser.analyse(
            current_skills=body.current_skills,
            target_role=body.target_role,
            required_skills=body.required_skills,
            job_description=body.job_description,
        )
        return SkillGapResponse(data=result)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

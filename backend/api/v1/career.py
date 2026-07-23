"""Career assistant API — resume, cover letter, interview, application, insights."""

import re
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import Field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.ai.career_assistant import CareerAssistant
from backend.ai.career_enhancements import CareerEnhancer
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
_enhancer = CareerEnhancer()

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
async def optimise_resume(
    _need_key: None = _need_key,
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
async def salary_guidance(
    body: SalaryGuidanceRequest, _need_key: None = _need_key
) -> SalaryGuidanceResponse:
    result = await _assistant.salary_guidance(
        body.job_title, body.location, body.experience_level, body.skills
    )
    return SalaryGuidanceResponse(data=result)


@router.post("/application/relocation", response_model=RelocationResponse)
async def relocation_response(
    body: RelocationRequest, _need_key: None = _need_key
) -> RelocationResponse:
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
async def tech_demand(
    _need_key: None = _need_key,
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


# -- Career Enhancements ----------------------------------------------------


class CompanyResearchResponse(BaseSchema):
    data: dict[str, Any] = Field(default_factory=dict)


class ContactDiscoveryResponse(BaseSchema):
    data: dict[str, Any] = Field(default_factory=dict)


class AppEmailRequest(BaseSchema):
    job_id: str
    email_type: str = "cold"
    candidate_profile: str = ""


class AppEmailResponse(BaseSchema):
    subject: str
    body: str


class StoryBankResponse(BaseSchema):
    data: dict[str, Any] = Field(default_factory=dict)


class ScamCheckResponse(BaseSchema):
    data: dict[str, Any] = Field(default_factory=dict)


class NegotiationResponse(BaseSchema):
    data: dict[str, Any] = Field(default_factory=dict)


class StartupEmailsResponse(BaseSchema):
    companies: list[dict[str, Any]] = Field(default_factory=list)
    stats: dict[str, Any] = Field(default_factory=dict)


class EmailHRRequest(BaseSchema):
    job_id: str
    candidate_name: str = "[Your Name]"
    candidate_email: str = "[Your Email]"
    candidate_phone: str = "[Your Phone]"


class EmailHRResponse(BaseSchema):
    emails_found: list[dict[str, Any]] = Field(default_factory=list)
    generated_email: dict[str, str] = Field(default_factory=dict)


@router.post("/email-hr", response_model=EmailHRResponse)
async def email_hr(
    body: EmailHRRequest, _need_key: None = _need_key, db: AsyncSession = Depends(get_db)
) -> EmailHRResponse:
    job = await _get_job(db, body.job_id)

    # Scrape emails
    from playwright.async_api import async_playwright

    from backend.automation.email_scraper import EmailScraper

    emails_found: list[dict[str, Any]] = []
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            scraper = EmailScraper(page)
            results = await scraper.find_emails(
                job_url=job.apply_url or job.url,
                company_name=job.company,
                company_url=job.company_url or "",
            )
            emails_found = [
                {
                    "email": r.email,
                    "priority": r.priority,
                    "priority_label": r.priority_label,
                    "source": r.source,
                }
                for r in results[:5]
            ]
            await browser.close()
    except Exception:
        # Fallback: generate likely emails from company domain
        domain = ""
        if job.company_url:
            with __import__("contextlib").suppress(Exception):
                domain = (
                    __import__("urllib.parse").urlparse(job.company_url).netloc.replace("www.", "")
                )
        if not domain and job.company:
            clean = re.sub(r"[^a-z0-9]", "", job.company.lower())[:20]
            domain = f"{clean}.com"

        if domain:
            emails_found = [
                {
                    "email": f"hr@{domain}",
                    "priority": 3,
                    "priority_label": "HR Department",
                    "source": "domain_guess",
                },
                {
                    "email": f"careers@{domain}",
                    "priority": 3,
                    "priority_label": "Jobs/Careers",
                    "source": "domain_guess",
                },
                {
                    "email": f"recruiting@{domain}",
                    "priority": 3,
                    "priority_label": "Jobs/Careers",
                    "source": "domain_guess",
                },
                {
                    "email": f"jobs@{domain}",
                    "priority": 3,
                    "priority_label": "Jobs/Careers",
                    "source": "domain_guess",
                },
                {
                    "email": f"info@{domain}",
                    "priority": 5,
                    "priority_label": "Generic",
                    "source": "domain_guess",
                },
            ]
        else:
            emails_found = [
                {
                    "email": "No domain found — try the company website",
                    "priority": 5,
                    "priority_label": "Not Found",
                    "source": "error",
                }
            ]

    # Generate email
    primary_email = next(
        (e["email"] for e in emails_found if e.get("priority", 5) <= 3),
        emails_found[0]["email"] if emails_found else "",
    )
    team_name = (
        primary_email.split("@")[0].replace(".", " ").title()
        if "@" in primary_email
        else "Hiring Team"
    )

    skills_str = ", ".join(job.skills[:8]) if job.skills else "relevant technologies"

    subject = f"Application: {job.title} — {body.candidate_name}"
    email_body = f"""Hi {team_name},

I came across the {job.title} role at {job.company} and wanted to reach out directly.

With experience in {skills_str}, I believe I can contribute to your team. I've been following {job.company}'s work and I'm excited about the opportunity to help build impactful solutions.

I've attached my resume for your review. I'd love to schedule a call to discuss how my background aligns with what you're looking for.

Best regards,
{body.candidate_name}
{body.candidate_email}
{body.candidate_phone}"""

    return EmailHRResponse(
        emails_found=emails_found,
        generated_email={"subject": subject, "body": email_body},
    )


@router.get("/research/company/{company_name}", response_model=CompanyResearchResponse)
async def company_research(
    company_name: str, _need_key: None = _need_key
) -> CompanyResearchResponse:
    result = await _enhancer.company_deep_research(company_name)
    return CompanyResearchResponse(data=result)


@router.get("/contacts/{company_name}", response_model=ContactDiscoveryResponse)
async def contact_discovery(
    company_name: str,
    job_title: str = "",
    _need_key: None = _need_key,
) -> ContactDiscoveryResponse:
    result = await _enhancer.contact_discovery(company_name, job_title)
    return ContactDiscoveryResponse(data=result)


@router.post("/email/application", response_model=AppEmailResponse)
async def application_email(
    body: AppEmailRequest,
    _need_key: None = _need_key,
    db: AsyncSession = Depends(get_db),
) -> AppEmailResponse:
    job = await _get_job(db, body.job_id)
    result = await _enhancer.application_email(job, body.email_type, body.candidate_profile)
    return AppEmailResponse(**result)


@router.post("/stories", response_model=StoryBankResponse)
async def story_bank(
    candidate_profile: str = Query(..., description="Your career profile"),
    job_id: str = Query(..., description="Target job ID"),
    _need_key: None = _need_key,
    db: AsyncSession = Depends(get_db),
) -> StoryBankResponse:
    job = await _get_job(db, job_id)
    result = await _enhancer.interview_story_bank(candidate_profile, job)
    return StoryBankResponse(data=result)


@router.get("/scam-check/{job_id}", response_model=ScamCheckResponse)
async def scam_check(
    job_id: str,
    _need_key: None = _need_key,
    db: AsyncSession = Depends(get_db),
) -> ScamCheckResponse:
    job = await _get_job(db, job_id)
    result = await _enhancer.scam_check(job)
    return ScamCheckResponse(data=result)


@router.post("/negotiation/{job_id}", response_model=NegotiationResponse)
async def negotiation(
    job_id: str,
    candidate_skills: list[str] = Query(default_factory=list),
    target_salary: str = Query(""),
    _need_key: None = _need_key,
    db: AsyncSession = Depends(get_db),
) -> NegotiationResponse:
    job = await _get_job(db, job_id)
    result = await _enhancer.negotiation_script(job, candidate_skills, target_salary)
    return NegotiationResponse(data=result)


class ArchetypeResponse(BaseSchema):
    data: dict[str, Any] = Field(default_factory=dict)


class EvalRequest(BaseSchema):
    job_id: str
    cv_text: str
    candidate_profile: str = ""


class EvalResponse(BaseSchema):
    data: dict[str, Any] = Field(default_factory=dict)


class CVGenerateRequest(BaseSchema):
    full_name: str = "John Doe"
    email: str = "john@example.com"
    phone: str = ""
    location: str = ""
    summary: str = ""
    skills: list[str] = Field(default_factory=list)
    experience: list[dict[str, Any]] = Field(default_factory=list)
    education: list[dict[str, Any]] = Field(default_factory=list)
    linkedin: str = ""
    projects: list[str] | None = None
    certifications: list[str] | None = None
    job_id: str | None = None


class CVGenerateResponse(BaseSchema):
    download_url: str
    filename: str


@router.post("/generate-cv", response_model=CVGenerateResponse)
async def generate_cv(body: CVGenerateRequest, _need_key: None = _need_key) -> CVGenerateResponse:
    from backend.ai.pdf_generator import CVGenerator

    keyword_skills = None
    if body.job_id:
        try:
            import uuid as uuid_mod

            from backend.database.session import get_session_factory
            from backend.repositories.job import JobRepository

            factory = get_session_factory()
            async with factory() as session:
                repo = JobRepository(session)
                job = await repo.get_by_id(uuid_mod.UUID(body.job_id))
                if job and job.skills:
                    keyword_skills = job.skills
        except Exception:
            pass

    gen = CVGenerator()
    html = gen.generate_html(
        full_name=body.full_name,
        email=body.email,
        phone=body.phone,
        location=body.location,
        summary=body.summary,
        skills=body.skills,
        experience=body.experience,
        education=body.education,
        linkedin=body.linkedin,
        projects=body.projects,
        certifications=body.certifications,
        keyword_skills=keyword_skills,
    )

    import os
    import time

    os.makedirs("output", exist_ok=True)
    filename = f"cv_{int(time.time())}.pdf"
    output_path = f"output/{filename}"

    await gen.generate_pdf(html, output_path)

    return CVGenerateResponse(
        download_url=f"/api/v1/career/download-cv/{filename}", filename=filename
    )


@router.get("/download-cv/{filename}")
async def download_cv(filename: str) -> FileResponse:
    path = f"output/{filename}"
    if not __import__("os").path.exists(path):
        raise HTTPException(status_code=404, detail="CV not found")
    return FileResponse(path, media_type="application/pdf", filename=filename)


@router.get("/archetype/{job_id}", response_model=ArchetypeResponse)
async def detect_archetype(
    job_id: str,
    _need_key: None = _need_key,
    db: AsyncSession = Depends(get_db),
) -> ArchetypeResponse:
    job = await _get_job(db, job_id)
    result = await _enhancer.detect_archetype(job)
    return ArchetypeResponse(data=result)


@router.post("/evaluate", response_model=EvalResponse)
async def full_evaluation(
    body: EvalRequest,
    _need_key: None = _need_key,
    db: AsyncSession = Depends(get_db),
) -> EvalResponse:
    job = await _get_job(db, body.job_id)
    result = await _enhancer.full_evaluation(job, body.cv_text, body.candidate_profile)
    return EvalResponse(data=result)


@router.post("/startup-emails", response_model=StartupEmailsResponse)
async def find_startup_emails(_need_key: None = _need_key) -> StartupEmailsResponse:
    from playwright.async_api import async_playwright

    from backend.automation.startup_finder import StartupFinder

    stats: dict[str, Any] = {}
    companies_data: list[dict[str, Any]] = []

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            finder = StartupFinder(page)
            results = await finder.discover(max_companies=80, scan_depth=3)

            stats = {
                "total_companies": len(results),
                "tier1_hiring_remote": sum(1 for c in results if c.tier == "Tier 1"),
                "tier2_hiring_onsite": sum(1 for c in results if c.tier == "Tier 2"),
                "emails_found": sum(1 for c in results if c.emails),
            }

            for c in results:
                companies_data.append(
                    {
                        "name": c.name,
                        "website": c.website,
                        "city": c.city,
                        "tier": c.tier,
                        "hiring": c.hiring,
                        "remote": c.remote,
                        "roles_found": c.roles_found,
                        "requirements": c.requirements[:300],
                        "emails": c.emails,
                        "email_keywords": c.email_keywords,
                        "industry": c.industry,
                        "size": c.size,
                        "linkedin": c.linkedin,
                        "scanned": c.scanned,
                    }
                )

            await browser.close()
    except Exception as exc:
        stats = {"error": str(exc), "total_companies": 0}

    return StartupEmailsResponse(companies=companies_data, stats=stats)

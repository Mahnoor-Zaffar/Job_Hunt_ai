"""Career assistant API — resume, cover letter, interview, application, insights."""

import asyncio
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


class VerifyStatusResponse(BaseSchema):
    task_id: str
    status: str  # running | completed | error
    progress: int = 0
    total: int = 0
    companies: list[dict[str, Any]] = Field(default_factory=list)
    stats: dict[str, Any] = Field(default_factory=dict)


class VerifyStartRequest(BaseSchema):
    companies: list[dict[str, Any]]


class StartupPersonalizeRequest(BaseSchema):
    company_name: str
    industry: str = ""
    city: str = ""
    size: str = ""
    role: str = "Full-Stack Developer"
    remote: str = "Remote"
    candidate_profile: str = ""


class StartupPersonalizeResponse(BaseSchema):
    subject: str
    body: str


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


@router.post("/startup-email/personalize", response_model=StartupPersonalizeResponse)
async def personalize_startup_email(
    body: StartupPersonalizeRequest, _need_key: None = _need_key
) -> StartupPersonalizeResponse:
    result = await _enhancer.startup_cold_email(
        company_name=body.company_name,
        industry=body.industry,
        city=body.city,
        size=body.size,
        candidate_profile=body.candidate_profile,
        role=body.role,
        remote=body.remote,
    )
    return StartupPersonalizeResponse(**result)


@router.post("/startup-emails", response_model=StartupEmailsResponse)
async def find_startup_emails(
    _need_key: None = _need_key,
    verify: bool = Query(False, description="Validate HR emails via MX + website scraping"),
) -> StartupEmailsResponse:
    from backend.automation.startup_finder import CompanyResult

    known: list[tuple[str, str, str, str, str, str]] = [
        ("DealCart", "dealcart.pk", "Karachi", "E-commerce", "10-25", "dealcart"),
        ("PriceOye", "priceoye.pk", "Islamabad", "E-commerce", "30-50", "priceoye"),
        ("Markaz", "markaz.app", "Islamabad", "E-commerce", "20-40", "markazapp"),
        ("Byte", "byte.pk", "Lahore", "E-commerce", "10-25", "bytepk"),
        ("Tajir", "tajir.com", "Lahore", "E-commerce", "30-60", "tajir"),
        ("Krave Mart", "kravemart.com", "Karachi", "E-commerce", "50-80", "kravemart"),
        ("Sastaticket", "sastaticket.pk", "Karachi", "Travel", "30-50", "sastaticketpk"),
        ("Rider", "rider.pk", "Karachi", "E-commerce", "40-70", "riderpk"),
        ("CreditBook", "creditbook.pk", "Karachi", "Fintech", "40-60", "creditbookpk"),
        ("Udhaar App", "udhaar.app", "Karachi", "Fintech", "20-40", "udhaarapp"),
        ("QistBazaar", "qistbazaar.pk", "Karachi", "Fintech", "20-40", "qistbazaar"),
        ("Haball", "haball.com", "Karachi", "Fintech", "20-40", "haball"),
        ("AdalFi", "adalfi.com", "Lahore", "Fintech", "15-30", "adalfi"),
        ("Aamarpay", "aamarpay.com", "Karachi", "Fintech", "15-30", "aamarpay"),
        ("Mahaana Wealth", "mahaana.com", "Islamabad", "Fintech", "10-20", "mahaanawith"),
        ("SadaPay", "sadapay.co", "Islamabad", "Fintech", "50-80", "sadapay"),
        ("NayaPay", "nayapay.com", "Islamabad", "Fintech", "80-120", "nayapay"),
        ("Abhi", "abhi.com.pk", "Karachi", "Fintech", "60-100", "abhi-pk"),
        ("QisstPay", "qisstpay.com", "Islamabad", "Fintech", "30-50", "qisstpay"),
        ("OneLoad", "oneload.com", "Islamabad", "Fintech", "30-50", "oneload"),
        ("Elphinstone", "elphinstone.co", "Karachi", "Fintech", "10-20", "elphinstonefin"),
        ("Tag", "tag.co", "Karachi", "Fintech", "20-40", "tagpk"),
        ("Dbank", "dbank.pk", "Lahore", "Fintech", "40-60", "dbank-pk"),
        ("Marham", "marham.pk", "Lahore", "HealthTech", "30-50", "marhampk"),
        ("Oladoc", "oladoc.com", "Lahore", "HealthTech", "40-60", "oladoc"),
        ("MedIQ", "mediq.com.pk", "Lahore", "HealthTech", "20-40", "mediqpk"),
        ("Xylexa", "xylexa.com", "Karachi", "HealthTech", "10-20", "xylexa"),
        ("MedznMore", "medznmore.com", "Karachi", "HealthTech", "15-30", "medznmore"),
        ("Sehat Kahani", "sehatkahani.com", "Karachi", "HealthTech", "30-50", "sehat-kahani"),
        ("Maqsad", "maqsad.pk", "Karachi", "EdTech", "30-60", "maqsadpk"),
        ("Edkasa", "edkasa.com", "Lahore", "EdTech", "15-30", "edkasa"),
        ("Myco", "myco.io", "Karachi", "EdTech", "20-40", "mycoapp"),
        ("Atomcamp", "atomcamp.com", "Islamabad", "EdTech", "15-30", "atomcamp"),
        ("Knowledge Platform", "knowledgeplatform.com", "Islamabad", "EdTech", "40-60", "knowledge-platform"),
        ("Hunarza", "hunarza.com", "Karachi", "EdTech", "5-15", "hunarza"),
        ("Revora AI", "revora.ai", "Karachi", "AI/ML", "10-20", "revoraai"),
        ("Oware", "oware.tech", "Karachi", "AI/ML", "10-20", "owaretech"),
        ("Uplift AI", "upliftaiorg", "Karachi", "Voice AI", "10-20", "upliftaiorg"),
        ("Zypl AI", "zypl.ai", "Karachi", "AI/ML", "15-30", "zyplai"),
        ("Vyro AI", "vyro.ai", "Karachi", "AI/ML", "30-50", "vyroai"),
        ("Vector AI", "vector-ai.co", "Sialkot", "AI/ML", "10-20", "vectoraico"),
        ("Dastgyr", "dastgyr.com", "Karachi", "B2B Commerce", "60-100", "dastgyr"),
        ("Savyour", "savyour.com", "Karachi", "B2B Commerce", "20-40", "savyourpk"),
        ("Zaraye", "zaraye.pk", "Karachi", "B2B Marketplace", "15-25", "zarayepk"),
        ("Retailo", "retailo.com", "Karachi", "B2B Commerce", "60-100", "retailo"),
        ("Bazaar Technologies", "bazaar.tech", "Karachi", "B2B Commerce", "80-120", "bazaar-technologies"),
        ("PostEx", "postex.pk", "Karachi", "Logistics", "50-80", "postexpk"),
        ("Truck It In", "truckitin.com", "Karachi", "Logistics", "30-50", "truckitin"),
        ("Trukkr", "trukkr.com", "Karachi", "Logistics", "10-20", "trukkr"),
        ("BridgeLinx", "bridgelinx.com", "Karachi", "Logistics", "30-50", "bridgelinx"),
        ("Cheetay", "cheetay.pk", "Karachi", "Logistics", "40-60", "cheetaypk"),
        ("Rover", "rover.pk", "Lahore", "Logistics", "20-40", "roverpk"),
        ("Convo", "convoz.com", "Lahore", "SaaS", "40-60", "convoz"),
        ("COLABS", "colabs.pk", "Lahore", "SaaS", "20-40", "colabspk"),
        ("Ease", "ease.xyz", "Karachi", "SaaS", "10-20", "easexyz"),
        ("SMMGuro", "smmguro.com", "Karachi", "SaaS", "15-30", "smmguro"),
        ("EventMobi", "eventmobi.com", "Lahore", "SaaS", "50-80", "eventmobi"),
        ("BusCaro", "buscaro.com", "Karachi", "Mobility", "20-40", "buscaro"),
        ("Bookme", "bookme.pk", "Islamabad", "Travel", "40-60", "bookmepk"),
        ("Bykea", "bykea.com", "Karachi", "Mobility", "60-100", "bykea"),
        ("CarFirst", "carfirst.com", "Karachi", "Auto", "40-60", "carfirstpk"),
        ("Gaadi", "gaadi.pk", "Lahore", "Auto", "15-25", "gaadipk"),
        ("Zyp Technologies", "zyp.tech", "Karachi", "EV", "20-40", "zyptech"),
        ("E-Vehicle", "e-vehicle.pk", "Lahore", "EV", "10-20", "evehiclepk"),
        ("Roomy", "roomy.pk", "Karachi", "PropTech", "10-20", "roomypk"),
        ("Haveli", "haveli.pk", "Lahore", "PropTech", "10-20", "havelipk"),
        ("VaporVM", "vaporvm.com", "Lahore", "Cloud", "30-50", "vaporvm"),
        ("TekRevol", "tekrevol.com", "Lahore", "Software", "60-100", "tekrevol"),
        ("BitSol", "bitsol.com", "Lahore", "Software", "20-40", "bitsol"),
        ("MyAdvo", "myadvo.pk", "Karachi", "LegalTech", "10-20", "myadvo"),
        ("Olive Planet", "oliveplanet.com", "Karachi", "CleanTech", "10-20", "oliveplanet"),
        ("Shopy", "shopy.pk", "Lahore", "E-commerce", "10-20", "shopy"),
        ("Zameen Alert", "zameenalert.com", "Lahore", "PropTech", "5-15", "zameenalrt"),
        ("TaxCorp", "taxcorp.pk", "Karachi", "Fintech", "10-20", "taxcorp"),
        ("PakWheels", "pakwheels.com", "Karachi", "Auto", "80-150", "pakwheels"),
        ("FoodPanda Pakistan", "foodpanda.pk", "Karachi", "FoodTech", "100-200", "foodpanda-pakistan"),
        ("Youth Club", "youthclub.pk", "Karachi", "EdTech", "15-25", "youthclubpk"),
        ("Techling", "techling.pk", "Lahore", "Software", "10-20", "techlingpk"),
        ("Zindigi", "zindigi.com", "Islamabad", "Fintech", "100-300", "zindigi"),
        # -- Additional curated entries --
        ("Keenu", "keenu.pk", "Lahore", "Fintech", "10-30", "keenu"),
        ("Dukan", "dukan.pk", "Karachi", "Fintech", "20-40", "dukanpk"),
        ("PayFast", "payfast.pk", "Karachi", "Fintech", "10-20", "payfast"),
        ("FinPocket", "finpocket.com.pk", "Karachi", "Fintech", "10-20", "finpocket"),
        ("KalPay", "kalpay.com", "Islamabad", "Fintech", "15-30", "kalpay"),
        ("MicroFi", "microfi.app", "Islamabad", "Fintech", "5-15", "microfi"),
        ("Bachat App", "bachat.app", "Karachi", "Fintech", "10-20", "bachatapp"),
        ("Fauree", "fauree.io", "Karachi", "Fintech", "11-50", "fauree"),
        ("Sarmaaya", "sarmaaya.pk", "Karachi", "Fintech", "10-20", "sarmaaya"),
        ("Easypaisa", "easypaisa.com.pk", "Karachi", "Fintech", "200-500", "easypaisa"),
        ("JazzCash", "jazzcash.com.pk", "Islamabad", "Fintech", "200-500", "jazzcash"),
        ("Shopsy", "shopsy.pk", "Lahore", "E-commerce", "15-30", "shopsy"),
        ("Telemart", "telemart.pk", "Lahore", "E-commerce", "20-40", "telemartpk"),
        ("iShopping.pk", "ishopping.pk", "Karachi", "E-commerce", "20-40", "ishoppingpk"),
        ("GharPar", "gharpar.pk", "Karachi", "E-commerce", "5-15", "gharpar"),
        ("Nearpeer", "nearpeer.org", "Lahore", "EdTech", "30-60", "nearpeer"),
        ("Sabaq.pk", "sabaq.pk", "Islamabad", "EdTech", "10-20", "sabaqpk"),
        ("EduMate", "edumate.pk", "Karachi", "EdTech", "5-15", "edumate"),
        ("Taleemabad", "taleemabad.com", "Islamabad", "EdTech", "15-30", "taleemabad"),
        ("DigiSkills", "digiskills.pk", "Islamabad", "EdTech", "20-40", "digiskills"),
        ("LearnOBots", "learnobots.com", "Lahore", "EdTech", "10-20", "learnobots"),
        ("WonderTree", "wondertree.co", "Karachi", "HealthTech", "10-20", "wondertree"),
        ("Dawaai", "dawaai.pk", "Karachi", "HealthTech", "30-60", "dawaai"),
        ("HealthWire", "healthwire.pk", "Karachi", "HealthTech", "20-40", "healthwire"),
        ("DoctorsHood", "doctorshood.com", "Lahore", "HealthTech", "10-20", "doctorshood"),
        ("Finja", "finja.pk", "Lahore", "Fintech", "40-60", "finjapk"),
        ("Careem", "careem.com", "Karachi", "Mobility", "500+", "careem"),
        ("Airlift", "airlift.pk", "Lahore", "Logistics", "30-50", "airliftpk"),
        ("Leopards Courier", "leopardscourier.com", "Karachi", "Logistics", "500-1000", "leopardscourier"),
        ("TCS", "tcs.com.pk", "Karachi", "Logistics", "1000-5000", "tcs-pakistan"),
        ("Call Courier", "callcourier.com.pk", "Karachi", "Logistics", "100-200", "callcourier"),
        ("Metric", "metricapp.co", "Islamabad", "AI/ML", "10-20", "metricapp"),
        ("Data Darbar", "datadarbar.ai", "Islamabad", "AI/ML", "10-20", "datadarbar"),
        ("ZahanatAI", "zahanatai.com", "Karachi", "AI/ML", "5-15", "zahanatai"),
        ("Systems Limited", "systemsltd.com", "Karachi", "SaaS", "2000+", "systemsltd"),
        ("Arbisoft", "arbisoft.com", "Lahore", "SaaS", "500+", "arbisoft"),
        ("Contour Software", "contoursoftware.com", "Karachi", "SaaS", "300+", "contoursoftware"),
        ("Folio3", "folio3.com", "Karachi", "SaaS", "300+", "folio3"),
        ("10Pearls", "10pearls.com", "Karachi", "SaaS", "1400+", "10pearls"),
        ("LetTech", "lettech.pk", "Peshawar", "SaaS", "10-20", "lettech"),
        ("Agrilift", "agrilift.pk", "Karachi", "AgriTech", "10-20", "agriliftpk"),
        ("Tazah", "tazah.pk", "Karachi", "AgriTech", "20-40", "tazahpk"),
        ("Zameen.com", "zameen.com", "Lahore", "PropTech", "200-500", "zameen"),
        ("Ghar47", "ghar47.com", "Islamabad", "PropTech", "20-40", "ghar47"),
        ("Shadiyana", "shadiyana.pk", "Karachi", "WeddingTech", "10-20", "shadiyana"),
        ("Game District", "gamedistrict.com", "Karachi", "Gaming", "50-100", "gamedistrict"),
        ("GenITeam", "geniteam.com", "Islamabad", "Gaming", "50-100", "geniteam"),
        ("SolarMax", "solarmax.pk", "Lahore", "CleanTech", "10-20", "solarmaxpk"),
    ]

    companies_data: list[dict[str, Any]] = []
    for name, domain, city, industry, size, linkedin_slug in known:
        emails = [
            {"email": f"hr@{domain}", "priority": 2, "label": "HR Department"},
            {"email": f"careers@{domain}", "priority": 3, "label": "Jobs/Careers"},
            {"email": f"jobs@{domain}", "priority": 3, "label": "Jobs/Careers"},
        ]
        companies_data.append(
            {
                "name": name,
                "website": f"https://{domain}",
                "city": city,
                "tier": "Not scanned",
                "hiring": False,
                "remote": False,
                "roles_found": [],
                "requirements": "",
                "emails": emails,
                "email_keywords": {"suggested_subject": f"Full-Stack Developer — Remote — {city}"},
                "industry": industry,
                "size": size,
                "linkedin": f"https://linkedin.com/company/{linkedin_slug}",
                "scanned": False,
            }
        )

    stats: dict[str, Any] = {"total": len(companies_data), "with_emails": len(companies_data)}

    if verify:
        try:
            from backend.automation.email_validator import validate_emails_for_domain

            sem = asyncio.Semaphore(5)
            verified_count = 0

            async def verify_company(c: dict[str, Any]) -> None:
                nonlocal verified_count
                domain = c["website"].replace("https://", "").replace("http://", "").split("/")[0]
                async with sem:
                    try:
                        validated = await asyncio.wait_for(
                            validate_emails_for_domain(domain, c.get("emails", [])),
                            timeout=20,
                        )
                        c["emails"] = validated
                        verified_count += 1
                    except TimeoutError:
                        pass

            await asyncio.gather(*[verify_company(c) for c in companies_data], return_exceptions=True)
            stats["verified"] = verified_count
        except ImportError:
            stats["verify_error"] = 1

    return StartupEmailsResponse(
        companies=companies_data,
        stats=stats,
    )


# -- Background email verification ---------------------------------------------

verify_tasks: dict[str, dict[str, Any]] = {}


@router.post("/startup-emails/verify", response_model=VerifyStatusResponse)
async def verify_startup_emails(
    body: VerifyStartRequest,
    _need_key: None = _need_key,
) -> VerifyStatusResponse:
    task_id = uuid.uuid4().hex[:12]
    task: dict[str, Any] = {
        "status": "running",
        "progress": 0,
        "total": len(body.companies),
        "companies": body.companies,
        "stats": {"total": len(body.companies), "with_emails": len(body.companies)},
    }
    verify_tasks[task_id] = task

    from backend.automation.email_validator import validate_emails_for_domain

    sem = asyncio.Semaphore(3)
    verified_count = 0

    async def verify_one(i: int, c: dict[str, Any]) -> None:
        nonlocal verified_count
        domain = c["website"].replace("https://", "").replace("http://", "").split("/")[0]
        async with sem:
            try:
                validated = await asyncio.wait_for(
                    validate_emails_for_domain(domain, c.get("emails", [])),
                    timeout=30,
                )
                c["emails"] = validated
                verified_count += 1
            except TimeoutError:
                pass
        task["progress"] = i + 1
        task["stats"]["verified"] = verified_count

    asyncio.create_task(_run_verification(task, verify_one))

    return VerifyStatusResponse(
        task_id=task_id,
        status="running",
        progress=0,
        total=task["total"],
        companies=task["companies"],
        stats=task["stats"],
    )


async def _run_verification(
    task: dict[str, Any],
    verify_one: Any,
) -> None:
    try:
        await asyncio.gather(
            *[verify_one(i, c) for i, c in enumerate(task["companies"])],
            return_exceptions=True,
        )
        task["status"] = "completed"
    except Exception:
        task["status"] = "error"
    finally:
        task["stats"]["verified"] = task["stats"].get("verified", 0)


@router.get("/startup-emails/verify/{task_id}", response_model=VerifyStatusResponse)
async def get_verify_status(task_id: str) -> VerifyStatusResponse:
    task = verify_tasks.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Verification task not found")
    return VerifyStatusResponse(
        task_id=task_id,
        status=task["status"],
        progress=task["progress"],
        total=task["total"],
        companies=task["companies"],
        stats=task["stats"],
    )

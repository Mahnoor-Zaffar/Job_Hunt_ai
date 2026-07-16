"""Resume upload + parsing API endpoint."""

from typing import Any

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import Field

from backend.ai.intelligence.resume import ResumeIntelligence
from backend.schemas.base import BaseSchema
from backend.utils.validation import validate_file

router = APIRouter(prefix="/resumes", tags=["resumes"])
_intelligence = ResumeIntelligence()


class ParsedResumeResponse(BaseSchema):
    full_name: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    summary: str = ""
    skills: list[str] = Field(default_factory=list)
    experience: list[dict[str, Any]] = Field(default_factory=list)
    education: list[dict[str, Any]] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    total_experience_years: int | None = None


@router.post("/parse", response_model=ParsedResumeResponse)
async def parse_resume(
    file: UploadFile = File(..., description="PDF, DOCX, or TXT resume file"),
) -> ParsedResumeResponse:
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    content = await file.read()
    try:
        validate_file(file.filename, content)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    text = await _extract_text(content, file.filename)

    parsed = _intelligence.parse(text)

    return ParsedResumeResponse(
        full_name=parsed.full_name,
        email=parsed.email,
        phone=parsed.phone,
        location=parsed.location,
        summary=parsed.summary,
        skills=parsed.skills,
        experience=[
            {
                "title": e.title,
                "company": e.company,
                "start_date": e.start_date,
                "end_date": e.end_date,
            }
            for e in parsed.experience
        ],
        education=[
            {"degree": e.degree, "field": e.field, "school": e.school, "year": e.year}
            for e in parsed.education
        ],
        certifications=parsed.certifications,
        projects=parsed.projects,
        languages=parsed.languages,
        total_experience_years=parsed.total_experience_years,
    )


async def _extract_text(content: bytes, filename: str) -> str:
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""

    if ext == "pdf":
        try:
            import fitz

            doc = fitz.open(stream=content, filetype="pdf")
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text.strip()
        except ImportError:
            return content.decode("utf-8", errors="ignore")
        except Exception:
            return content.decode("utf-8", errors="ignore")

    if ext in ("docx", "doc"):
        try:
            from io import BytesIO

            from docx import Document

            doc = Document(BytesIO(content))
            return "\n".join(p.text for p in doc.paragraphs)
        except ImportError:
            return content.decode("utf-8", errors="ignore")
        except Exception:
            return content.decode("utf-8", errors="ignore")

    return content.decode("utf-8", errors="ignore")

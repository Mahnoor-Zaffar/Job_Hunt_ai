"""Resume intelligence — section detection, timeline, skill extraction.

Parses raw resume text into structured sections without LLM calls.
Uses regex-based section detection and the existing technology
extractor for skills identification.
"""

import logging
import re
from dataclasses import dataclass, field

from backend.scrapers.technologies.extractor import TechnologyExtractor

logger = logging.getLogger("job_hunting.intelligence.resume")

SECTION_PATTERNS = {
    "summary": re.compile(
        r"(?i)^\s*(summary|profile|objective|about me|professional summary)\s*$",
        re.MULTILINE,
    ),
    "experience": re.compile(
        r"(?i)^\s*(experience|work experience|employment|work history|professional experience)\s*$",
        re.MULTILINE,
    ),
    "education": re.compile(
        r"(?i)^\s*(education|academic|academics|qualification|university)\s*$",
        re.MULTILINE,
    ),
    "skills": re.compile(
        r"(?i)^\s*(skills|technical skills|technologies|competencies|expertise)\s*$",
        re.MULTILINE,
    ),
    "certifications": re.compile(
        r"(?i)^\s*(certifications|certificates|licenses|accreditations)\s*$",
        re.MULTILINE,
    ),
    "projects": re.compile(
        r"(?i)^\s*(projects|personal projects|side projects|portfolio)\s*$",
        re.MULTILINE,
    ),
    "languages": re.compile(
        r"(?i)^\s*(languages|language proficiency)\s*$",
        re.MULTILINE,
    ),
}

JOB_ENTRY_PATTERN = re.compile(
    r"(?P<title>[A-Z][\w\s/&#+-]+?)\s+at\s+(?P<company>[A-Z][\w\s.&()-]+?)\s*"
    r"(?P<dates>\(?\d{4}\s*(?:-|to)\s*(?:\d{4}|Present|Current)\)?)",
    re.MULTILINE,
)

JOB_ENTRY_PATTERN_ALT = re.compile(
    r"^(?P<title>[A-Z][\w\s/&#+-]{5,60})$",
    re.MULTILINE,
)

EDUCATION_PATTERN = re.compile(
    r"(?P<degree>B\.?\s*Sc\.?|M\.?\s*Sc\.?|B\.?\s*A\.?|M\.?\s*A\.?|Ph\.?\s*D\.?|"
    r"Bachelor|Master|Doctorate|Bachelors|Masters|MBA|Associate|Diploma|BS|MS|BA|MA|PhD)"
    r"[,\s]+(?:of|in)?\s*(?P<field>[A-Z][\w\s&]{2,30})"
    r"\s+from\s+(?P<school>[A-Z][\w\s.&,-]{2,30})\b"
    r"(?:\s*\((?P<year>\d{4})\))?",
    re.MULTILINE | re.IGNORECASE,
)

EDUCATION_PATTERN_SIMPLE = re.compile(
    r"(?P<degree>B\.?\s*Sc\.?|M\.?\s*Sc\.?|B\.?\s*A\.?|M\.?\s*A\.?|Ph\.?\s*D\.?|"
    r"Bachelor|Master|Doctorate|Bachelors|Masters|MBA|Associate|Diploma|BS|MS|BA|MA|PhD)"
    r"[,\s]+(?P<field>[A-Z][\w\s&]+?)"
    r"[,\s]+(?P<school>[A-Z][\w\s.&,]+?)"
    r"[,\s]*(?P<year>\d{4})",
    re.MULTILINE | re.IGNORECASE,
)


@dataclass
class ResumeSection:
    name: str
    content: str
    start_line: int = 0


@dataclass
class JobEntry:
    title: str
    company: str = ""
    start_date: str = ""
    end_date: str = ""
    highlights: list[str] = field(default_factory=list)


@dataclass
class EducationEntry:
    degree: str
    field: str = ""
    school: str = ""
    year: str = ""


@dataclass
class ParsedResume:
    full_name: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    summary: str = ""
    skills: list[str] = field(default_factory=list)
    experience: list[JobEntry] = field(default_factory=list)
    education: list[EducationEntry] = field(default_factory=list)
    certifications: list[str] = field(default_factory=list)
    projects: list[str] = field(default_factory=list)
    languages: list[str] = field(default_factory=list)
    total_experience_years: int | None = None
    raw_sections: list[ResumeSection] = field(default_factory=list)


class ResumeIntelligence:
    def __init__(self, tech_extractor: TechnologyExtractor | None = None) -> None:
        self._tech = tech_extractor or TechnologyExtractor()

    def parse(self, text: str) -> ParsedResume:
        result = ParsedResume()

        result.full_name, result.email, result.phone = _extract_contact(text)
        result.location = _extract_location(text)

        sections = self._detect_sections(text)
        result.raw_sections = sections

        for section in sections:
            if section.name == "summary":
                result.summary = section.content.strip()
            elif section.name == "skills":
                result.skills = self._tech.extract(section.content)
            elif section.name == "experience":
                result.experience = self._extract_jobs(section.content)
            elif section.name == "education":
                result.education = self._extract_education(section.content)
            elif section.name == "certifications":
                result.certifications = self._extract_bullet_items(section.content)
            elif section.name == "projects":
                result.projects = self._extract_bullet_items(section.content)
            elif section.name == "languages":
                result.languages = self._extract_bullet_items(section.content)

        if not result.skills:
            result.skills = self._tech.extract(text)

        result.total_experience_years = self._estimate_experience(result.experience)

        return result

    def _detect_sections(self, text: str) -> list[ResumeSection]:
        lines = text.split("\n")
        sections: list[ResumeSection] = []
        current_name = "header"
        current_start = 0
        current_lines: list[str] = []

        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped:
                continue

            section_name = None
            for name, pattern in SECTION_PATTERNS.items():
                if pattern.match(stripped) and len(stripped) < 40:
                    section_name = name
                    break

            if section_name:
                if current_lines:
                    sections.append(
                        ResumeSection(
                            name=current_name,
                            content="\n".join(current_lines),
                            start_line=current_start,
                        )
                    )
                current_name = section_name
                current_start = i + 1
                current_lines = []
            else:
                current_lines.append(line)

        if current_lines:
            sections.append(
                ResumeSection(
                    name=current_name,
                    content="\n".join(current_lines),
                    start_line=current_start,
                )
            )

        return sections

    def _extract_jobs(self, text: str) -> list[JobEntry]:
        jobs: list[JobEntry] = []
        for match in JOB_ENTRY_PATTERN.finditer(text):
            title = match.group("title").strip() if match.group("title") else ""
            company = match.group("company").strip() if match.group("company") else ""
            dates = match.group("dates") if match.group("dates") else ""
            start_date, end_date = _parse_date_range(dates)
            jobs.append(JobEntry(title=title, company=company, start_date=start_date, end_date=end_date))
        return jobs

    def _extract_education(self, text: str) -> list[EducationEntry]:
        entries: list[EducationEntry] = []
        for pattern in (EDUCATION_PATTERN, EDUCATION_PATTERN_SIMPLE):
            for match in pattern.finditer(text):
                entry = EducationEntry(
                    degree=match.group("degree") or "",
                    field=match.group("field") or "",
                    school=match.group("school") or "",
                    year=match.group("year") or "",
                )
                if entry not in entries:
                    entries.append(entry)
        return entries

    def _extract_bullet_items(self, text: str) -> list[str]:
        items: list[str] = []
        for line in text.split("\n"):
            stripped = line.strip().lstrip("-•·*1234567890. ")
            if stripped and len(stripped) > 2:
                items.append(stripped)
        return items

    def _estimate_experience(self, jobs: list[JobEntry]) -> int | None:
        if not jobs:
            return None
        total = 0
        for job in jobs:
            if job.start_date and job.end_date:
                try:
                    start = int(job.start_date)
                    end = int(job.end_date.replace("Present", "2026").replace("Current", "2026"))
                    total += max(0, end - start)
                except ValueError:
                    continue
        if total > 0:
            return total
        return max(1, len(jobs) * 2)


def _extract_contact(text: str) -> tuple[str, str, str]:
    email_match = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", text)
    email = email_match.group(0) if email_match else ""

    phone_match = re.search(r"\+?\d[\d\s().-]{7,}\d", text)
    phone = phone_match.group(0).strip() if phone_match else ""

    lines = text.split("\n")
    name = ""
    for line in lines[:5]:
        stripped = line.strip()
        if (stripped and len(stripped.split()) >= 2 and not email_match) or not re.search(
            r"[\w.+-]+@", stripped
        ):
            words = [w for w in stripped.split() if w[0].isupper()]
            if len(words) >= 2:
                name = stripped
                break

    return name, email, phone


_SECTION_NAMES = {"summary", "experience", "education", "skills", "certifications", "projects", "languages"}


def _parse_date_range(dates: str) -> tuple[str, str]:
    import re

    nums = re.findall(r"\d{4}", dates)
    if len(nums) >= 2:
        return nums[0], nums[1]
    if len(nums) == 1:
        if "Present" in dates or "Current" in dates:
            return nums[0], "Present"
        return nums[0], ""
    return "", ""


def _extract_location(text: str) -> str:
    cities = [
        "Islamabad",
        "Rawalpindi",
        "Lahore",
        "Karachi",
        "London",
        "New York",
        "San Francisco",
        "Dubai",
        "Berlin",
        "Toronto",
    ]
    for city in cities:
        if city in text:
            idx = text.find(city)
            end = min(len(text), idx + len(city) + 30)
            return text[idx:end].split("\n")[0].strip()
    return ""

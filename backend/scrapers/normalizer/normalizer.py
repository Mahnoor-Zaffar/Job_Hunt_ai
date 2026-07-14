import logging

from backend.scrapers.models.models import NormalizedJob, RawJob, RemoteType
from backend.scrapers.technologies.extractor import TechnologyExtractor
from backend.utils.hashing import generate_fingerprint

logger = logging.getLogger("job_hunting.normalizer")

REMOTE_KEYWORDS = [
    "remote",
    "work from home",
    "wfh",
    "fully remote",
    "100% remote",
]

HYBRID_KEYWORDS = [
    "hybrid",
    "hybrid-remote",
    "hybrid remote",
    "partially remote",
    "flexible remote",
]

EMPLOYMENT_TYPE_MAP = {
    "full time": "full_time",
    "full-time": "full_time",
    "fulltime": "full_time",
    "part time": "part_time",
    "part-time": "part_time",
    "parttime": "part_time",
    "contract": "contract",
    "internship": "internship",
    "intern": "internship",
    "freelance": "freelance",
    "freelancer": "freelance",
    "temporary": "contract",
}

EXPERIENCE_MAP = {
    "intern": "intern",
    "entry level": "intern",
    "entry": "intern",
    "junior": "junior",
    "associate": "junior",
    "mid level": "mid",
    "mid": "mid",
    "mid-senior": "mid",
    "senior": "senior",
    "lead": "lead",
    "principal": "lead",
    "manager": "lead",
    "head": "lead",
    "executive": "executive",
    "director": "executive",
    "vp": "executive",
    "vice president": "executive",
}

COUNTRY_MAP = {
    "pk": "Pakistan",
    "pakistan": "Pakistan",
    "us": "United States",
    "usa": "United States",
    "uk": "United Kingdom",
    "gb": "United Kingdom",
    "ae": "United Arab Emirates",
    "de": "Germany",
    "germany": "Germany",
    "ca": "Canada",
    "canada": "Canada",
    "au": "Australia",
    "australia": "Australia",
    "sg": "Singapore",
    "singapore": "Singapore",
    "in": "India",
    "india": "India",
    "fr": "France",
    "france": "France",
}

KNOWN_CITIES_PK = {
    "islamabad",
    "rawalpindi",
    "lahore",
    "karachi",
    "faisalabad",
    "multan",
    "peshawar",
    "quetta",
    "sialkot",
    "gujranwala",
    "gujrat",
    "hyderabad",
    "sahiwal",
    "abbottabad",
}

SUPPORTED_LOCATIONS_PK: frozenset[str] = frozenset({"islamabad", "rawalpindi", "lahore"})


class Normalizer:
    """Applies shared normalisation across all job sources.

    Each normalisation step is a separate method so concrete scrapers
    can override individual pieces without duplicating the full flow.
    """

    def __init__(self, tech_extractor: TechnologyExtractor | None = None) -> None:
        self._tech_extractor = tech_extractor or TechnologyExtractor()

    def normalize(self, raw: RawJob) -> NormalizedJob:
        title = self._clean_title(raw.title)
        location, city, country, remote_type = self._parse_location(
            raw.location, raw.is_remote, raw.remote_type
        )
        salary_min, salary_max, currency = self._resolve_salary(
            raw.salary_min, raw.salary_max, raw.currency
        )
        employment_type = self._normalize_employment_type(raw.employment_type)
        experience_level = self._normalize_experience(raw.experience_level)
        skills = self._merge_skills(raw.skills, raw.description)

        normalized = NormalizedJob(
            title=title,
            company=raw.company.strip() if raw.company else "",
            company_url=raw.company_url,
            location=location,
            city=city or raw.city,
            country=country or raw.country,
            remote_type=remote_type,
            is_remote=(remote_type == "remote"),
            description=self._clean_text(raw.description),
            requirements=self._clean_text(raw.requirements),
            url=raw.url.strip(),
            apply_url=raw.apply_url.strip() if raw.apply_url else None,
            source=raw.source,
            source_id=raw.source_id.strip(),
            salary_min=salary_min,
            salary_max=salary_max,
            currency=currency,
            employment_type=employment_type,
            experience_level=experience_level,
            skills=skills,
            posted_at=raw.posted_at,
            expires_at=raw.expires_at,
            fingerprint="",
        )
        normalized.fingerprint = generate_fingerprint(
            normalized.title,
            normalized.company,
            normalized.location,
            normalized.url,
        )
        return normalized

    def is_supported_location(self, job: NormalizedJob) -> bool:
        """Return True when a job targets Islamabad, Rawalpindi, Lahore or is remote."""
        if job.remote_type in ("remote",):
            return True
        city = (job.city or "").strip().lower()
        return city in SUPPORTED_LOCATIONS_PK

    # ---- private helpers ------------------------------------------------

    def _clean_title(self, title: str) -> str:
        return " ".join(title.strip().split())

    def _clean_text(self, text: str | None) -> str | None:
        if text is None:
            return None
        cleaned = " ".join(text.replace("\r\n", "\n").split())
        return cleaned if cleaned else None

    def _parse_location(
        self,
        location: str | None,
        is_remote: bool,
        raw_remote_type: RemoteType,
    ) -> tuple[str, str | None, str | None, RemoteType]:
        if not location:
            default_type: RemoteType = "remote" if is_remote else raw_remote_type
            return (
                "Remote" if is_remote else "Unknown",
                None,
                None,
                default_type,
            )

        cleaned = location.strip()
        lower = cleaned.lower()

        remote_type = self._derive_remote_type(lower, is_remote, raw_remote_type)

        parts = [p.strip() for p in cleaned.split(",")]
        known_city: str | None = None
        known_country: str | None = None

        for part in parts:
            pl = part.lower().strip()
            if pl in COUNTRY_MAP:
                known_country = COUNTRY_MAP[pl]
            elif pl in KNOWN_CITIES_PK:
                known_city = part

        if known_city:
            location_display = f"{known_city}, {known_country}" if known_country else known_city
            return location_display, known_city, known_country, remote_type

        if known_country:
            return cleaned, None, known_country, remote_type

        return cleaned, parts[0] if len(parts) >= 1 else None, None, remote_type

    def _derive_remote_type(
        self, lower_location: str, is_remote: bool, raw_remote_type: RemoteType
    ) -> RemoteType:
        if raw_remote_type != "onsite":
            return raw_remote_type

        if is_remote:
            return "remote"

        if any(kw in lower_location for kw in HYBRID_KEYWORDS):
            return "hybrid"

        if any(kw in lower_location for kw in REMOTE_KEYWORDS):
            return "remote"

        return "onsite"

    def _resolve_salary(
        self,
        salary_min: float | None,
        salary_max: float | None,
        currency: str | None,
    ) -> tuple[float | None, float | None, str | None]:
        if not currency:
            return salary_min, salary_max, None
        upper = currency.upper()
        if upper in ("PKR", "RS", "RP"):
            return salary_min, salary_max, "PKR"
        if upper in ("USD", "$", "US$"):
            return salary_min, salary_max, "USD"
        if upper in ("EUR", "€"):
            return salary_min, salary_max, "EUR"
        if upper in ("GBP", "£"):
            return salary_min, salary_max, "GBP"
        if upper in ("AED", "DHS"):
            return salary_min, salary_max, "AED"
        return salary_min, salary_max, currency

    def _normalize_employment_type(self, raw: str | None) -> str | None:
        if raw is None:
            return None
        key = raw.strip().lower()
        return EMPLOYMENT_TYPE_MAP.get(key, key.replace(" ", "_"))

    def _normalize_experience(self, raw: str | None) -> str | None:
        if raw is None:
            return None
        key = raw.strip().lower()
        return EXPERIENCE_MAP.get(key, key)

    def _merge_skills(
        self, provided: list[str] | None, description: str | None
    ) -> list[str] | None:
        extracted = self._tech_extractor.extract(description) if description else []
        if provided:
            combined = {s.strip() for s in provided if s and s.strip()}
            combined.update(extracted)
        else:
            combined = set(extracted)

        return sorted(combined) if combined else None

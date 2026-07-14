import logging
from datetime import datetime
from typing import Any

from backend.scrapers.ats.adapter import BaseATSAdapter
from backend.scrapers.ats.companies import CompanyConfig
from backend.scrapers.models.models import RawJob

logger = logging.getLogger("job_hunting.ats.workable")


class WorkableAdapter(BaseATSAdapter):
    """Adapter for Workable ATS public job board.

    Workable hosts each company's careers page at::

        https://apply.workable.com/{company}

    The embedded data is typically available via the page HTML
    (JSON-LD or inline script) or a companion API.

    Fallback: scrape the HTML page and parse JSON-LD structured data.
    """

    platform = "workable"

    async def fetch(self, company: CompanyConfig) -> list[dict[str, Any]]:
        url = company.careers_url.rstrip("/")
        try:
            html = await self.http.get(url)
            return self._extract_json_ld(html, company)
        except Exception:
            logger.exception("Failed to fetch Workable jobs for %s", company.name)
            return []

    async def parse(
        self,
        raw: list[dict[str, Any]],
        company: CompanyConfig,
    ) -> list[RawJob]:
        result: list[RawJob] = []
        for item in raw:
            try:
                job = self._parse_item(item, company)
                if job:
                    result.append(job)
            except Exception:
                logger.exception("Failed to parse Workable job for %s", company.name)
        return result

    def _extract_json_ld(self, html: str, company: CompanyConfig) -> list[dict[str, Any]]:
        import json as json_mod
        import re
        from html import unescape

        pattern = re.compile(
            r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>',
            re.DOTALL,
        )
        matches = pattern.findall(html)
        for match in matches:
            try:
                data = json_mod.loads(unescape(match))
                if isinstance(data, list):
                    items = [
                        d for d in data if isinstance(d, dict) and d.get("@type") == "JobPosting"
                    ]
                    if items:
                        return items
                elif isinstance(data, dict) and data.get("@type") == "JobPosting":
                    return [data]
            except json_mod.JSONDecodeError:
                continue

        return self._fallback_parse(html)

    def _fallback_parse(self, html: str) -> list[dict[str, Any]]:
        import json as json_mod
        import re

        pattern = re.compile(r"window\.__INITIAL_STATE__\s*=\s*({.*?});", re.DOTALL)
        match = pattern.search(html)
        if match:
            try:
                data = json_mod.loads(match.group(1))
                jobs = data.get("jobs", []) or []
                return [j for j in jobs if isinstance(j, dict)]
            except json_mod.JSONDecodeError:
                pass
        return []

    def _parse_item(self, item: dict[str, Any], company: CompanyConfig) -> RawJob | None:
        title = (item.get("title") or "").strip()
        if not title:
            return None

        job_id = str(item.get("id") or item.get("identifier", {}).get("value", ""))
        location = item.get("jobLocation", {}) or {}
        if isinstance(location, dict):
            address = location.get("address", {}) or {}
            locality = address.get("addressLocality", "") or location.get("name", "")
            country_name = address.get("addressCountry", "")
            location_str = ", ".join(p for p in [locality, country_name] if p) or "Remote"
        else:
            location_str = str(location) if location else "Remote"

        apply_url = (item.get("url") or item.get("sameAs") or "").strip()
        posted_str = item.get("datePosted", "")
        posted_at = _parse_date(posted_str)

        description = (item.get("description") or "").strip()
        employment_type = item.get("employmentType")
        hiring_organization = item.get("hiringOrganization", {}) or {}
        org_name = (
            hiring_organization.get("name", company.name)
            if isinstance(hiring_organization, dict)
            else company.name
        )

        salary_info = item.get("baseSalary", {}) or {}
        salary_min = None
        salary_max = None
        salary_currency = None
        if isinstance(salary_info, dict):
            value_obj = salary_info.get("value", {})
            if isinstance(value_obj, dict):
                raw_min = value_obj.get("minValue")
                raw_max = value_obj.get("maxValue")
                salary_min = float(raw_min) if isinstance(raw_min, (int, float, str)) else None
                salary_max = float(raw_max) if isinstance(raw_max, (int, float, str)) else None
            salary_currency = salary_info.get("currency", None)

        return RawJob(
            title=title,
            company=org_name or company.name,
            company_url=company.careers_url,
            location=location_str,
            description=description,
            url=apply_url,
            apply_url=apply_url,
            source="workable",
            source_id=f"wb-{company.name}-{job_id}",
            salary_min=salary_min,
            salary_max=salary_max,
            currency=salary_currency,
            employment_type=employment_type,
            posted_at=posted_at,
            is_remote=_is_remote(location_str),
            remote_type="remote" if _is_remote(location_str) else "onsite",
        )


def _parse_date(value: str) -> datetime | None:
    if not value:
        return None
    for fmt in (
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%d",
        "%Y-%m-%dT%H:%M:%S",
    ):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def _is_remote(location: str) -> bool:
    lower = location.lower()
    return any(kw in lower for kw in ("remote", "anywhere", "worldwide"))

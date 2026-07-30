from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from backend.scrapers.ats.adapter import BaseATSAdapter
from backend.scrapers.ats.companies import CompanyConfig
from backend.scrapers.models.models import RawJob

logger = logging.getLogger("job_hunting.ats.workable")

_WIDGET_API = "https://apply.workable.com/api/v1/widget/accounts"


class WorkableAdapter(BaseATSAdapter):
    """Adapter for Workable ATS public job board.

    Uses the widget API at ``/api/v1/widget/accounts/{slug}`` which returns
    a JSON payload with a ``jobs`` array.  Falls back to JSON-LD / inline
    ``window.__INITIAL_STATE__`` extraction from the HTML page when the
    widget API is unavailable.
    """

    platform = "workable"

    async def fetch(self, company: CompanyConfig) -> list[dict[str, Any]]:
        slug = _extract_slug(company.careers_url)
        if not slug:
            logger.warning("Cannot determine Workable slug from URL: %s", company.careers_url)
            return []

        widget_url = f"{_WIDGET_API}/{slug}"
        try:
            data: dict[str, Any] = await self.http.get_json(widget_url)
            jobs: list[dict[str, Any]] = data.get("jobs", [])
            if jobs:
                return jobs
        except Exception:
            logger.debug("Widget API unavailable for %s, trying HTML fallback", company.name)

        return await self._html_fetch(company, slug)

    async def _html_fetch(self, company: CompanyConfig, slug: str) -> list[dict[str, Any]]:
        url = f"https://apply.workable.com/{slug}/"
        try:
            html = await self.http.get(url)
        except Exception:
            logger.exception("Failed to fetch Workable HTML for %s", company.name)
            return []
        return self._extract_json_ld(html)

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

    @staticmethod
    def _extract_json_ld(html: str) -> list[dict[str, Any]]:
        import json as json_mod
        import re
        from html import unescape

        pattern = re.compile(
            r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>',
            re.DOTALL,
        )
        for match in pattern.findall(html):
            try:
                data = json_mod.loads(unescape(match))
                if isinstance(data, list):
                    items = [d for d in data if isinstance(d, dict) and d.get("@type") == "JobPosting"]
                    if items:
                        return items
                elif isinstance(data, dict) and data.get("@type") == "JobPosting":
                    return [data]
            except json_mod.JSONDecodeError:
                continue
        return _fallback_initial_state(html)

    def _parse_item(self, item: dict[str, Any], company: CompanyConfig) -> RawJob | None:
        title = (item.get("title") or "").strip()
        if not title:
            return None

        job_id = str(item.get("id") or item.get("shortcode", ""))
        location_str = _extract_location(item)
        apply_url = (item.get("url") or item.get("application_url") or "").strip()
        department = item.get("department")

        posted_str = item.get("published", item.get("created_at", ""))
        posted_at = _parse_date(posted_str)

        description = (item.get("description") or item.get("full_description") or "").strip()
        employment_type = item.get("employment_type", item.get("type"))

        salary_min: float | None = None
        salary_max: float | None = None
        salary_currency: str | None = None
        salary_raw = item.get("salary_range") or {}
        if isinstance(salary_raw, dict):
            salary_min = _to_float(salary_raw.get("min"))
            salary_max = _to_float(salary_raw.get("max"))
            salary_currency = salary_raw.get("currency")

        return RawJob(
            title=title,
            company=company.name,
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
            experience_level=department,
            posted_at=posted_at,
            is_remote=_is_remote(location_str),
            remote_type="remote" if _is_remote(location_str) else "onsite",
        )


def _extract_slug(careers_url: str) -> str | None:
    url = careers_url.rstrip("/")
    if "apply.workable.com" in url:
        parts = url.strip("/").split("/")
        for part in parts:
            if "apply.workable.com" in part:
                idx = parts.index(part) + 1
                if idx < len(parts):
                    return parts[idx]
        return None
    return url.strip("/").split("/")[-1] or None


def _extract_location(item: dict[str, Any]) -> str:
    loc = item.get("location") or {}
    if isinstance(loc, dict):
        parts = []
        city = loc.get("city", "")
        region = loc.get("region", "")
        country = loc.get("country", "")
        if city:
            parts.append(city)
        if region and region != city:
            parts.append(region)
        if country:
            parts.append(country)
        return ", ".join(parts) if parts else "Remote"
    if isinstance(loc, str) and loc.strip():
        return loc.strip()
    if item.get("workplace") or item.get("remote"):
        return "Remote"
    return "Remote"


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


def _to_float(val: Any) -> float | None:
    if val is None:
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def _fallback_initial_state(html: str) -> list[dict[str, Any]]:
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


def _is_remote(location: str) -> bool:
    lower = location.lower()
    return any(kw in lower for kw in ("remote", "anywhere", "worldwide"))

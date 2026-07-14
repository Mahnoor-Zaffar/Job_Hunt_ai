import logging
from datetime import datetime
from typing import Any

from backend.scrapers.ats.adapter import BaseATSAdapter
from backend.scrapers.ats.companies import CompanyConfig
from backend.scrapers.models.models import RawJob

logger = logging.getLogger("job_hunting.ats.greenhouse")


class GreenhouseAdapter(BaseATSAdapter):
    """Adapter for Greenhouse ATS public job board API.

    Each company's jobs are available at::

        {careers_url}/jobs (HTML or JSON — try JSON first)

    JSON endpoint pattern: ``{careers_url}/jobs`` with
    ``Accept: application/json`` header.
    """

    platform = "greenhouse"

    async def fetch(self, company: CompanyConfig) -> list[dict[str, Any]]:
        base = company.careers_url.rstrip("/")
        json_url = f"{base}/jobs"

        try:
            data = await self.http.get_json(json_url)
            if isinstance(data, dict):
                jobs: list[dict[str, Any]] = data.get("jobs", [])
                return jobs
            if isinstance(data, list):
                return [j for j in data if isinstance(j, dict)]
        except Exception:
            logger.warning("JSON fallback failed for %s", company.name)
            return []

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
                logger.exception("Failed to parse Greenhouse job for %s", company.name)
        return result

    def _parse_item(self, item: dict[str, Any], company: CompanyConfig) -> RawJob | None:
        title = (item.get("title") or "").strip()
        if not title:
            return None

        job_id = str(item.get("id", ""))
        absolute_url = item.get("absolute_url", "")
        location_info = item.get("location", {}) or {}
        location_name = (
            location_info.get("name", "") if isinstance(location_info, dict) else str(location_info)
        )
        metadata: list[dict[str, Any]] = item.get("metadata", []) or []

        employment_type = _extract_metadata(metadata, "Employment Type")
        departments = " > ".join(
            d.get("name", "") for d in item.get("departments", []) or [] if isinstance(d, dict)
        )

        posted_str = item.get("updated_at", "")
        posted_at = _parse_gh_datetime(posted_str)

        return RawJob(
            title=title,
            company=company.name,
            company_url=company.careers_url,
            location=location_name or "Remote",
            description=_build_description(item),
            url=absolute_url,
            apply_url=absolute_url,
            source="greenhouse",
            source_id=f"gh-{company.name}-{job_id}",
            employment_type=employment_type,
            experience_level=_extract_metadata(metadata, "Experience Level") or departments or None,
            posted_at=posted_at,
            is_remote=_is_remote(location_name),
            remote_type="remote"
            if _is_remote(location_name)
            else "hybrid"
            if "hybrid" in location_name.lower()
            else "onsite",
        )


def _extract_metadata(metadata: list[dict[str, Any]], field: str) -> str | None:
    for entry in metadata:
        if isinstance(entry, dict) and entry.get("name") == field:
            values = entry.get("value", []) or []
            if isinstance(values, list) and values:
                first = values[0]
                if isinstance(first, dict):
                    return first.get("name") or first.get("value")
                return str(first)
    return None


def _build_description(item: dict[str, Any]) -> str:
    content = (item.get("content") or "").strip()
    description = (item.get("description") or "").strip()
    if content:
        return content
    if description:
        return description
    return ""


def _is_remote(location: str) -> bool:
    lower = location.lower()
    return any(kw in lower for kw in ("remote", "anywhere", "worldwide"))


def _parse_gh_datetime(value: str) -> datetime | None:
    if not value:
        return None
    for fmt in (
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S",
    ):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None

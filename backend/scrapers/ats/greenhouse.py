from __future__ import annotations

import json as _json
import logging
import re
from datetime import datetime
from typing import Any

import json5

from backend.scrapers.ats.adapter import BaseATSAdapter
from backend.scrapers.ats.companies import CompanyConfig
from backend.scrapers.models.models import RawJob

logger = logging.getLogger("job_hunting.ats.greenhouse")

_REMIX_RE = re.compile(r"window\.__remixContext\s*=\s*({.*?});", re.DOTALL)
_NEXT_DATA_RE = re.compile(
    r'<script[^>]*id="__NEXT_DATA__"[^>]*type="application/json"[^>]*>(.*?)</script>',
    re.DOTALL,
)


class GreenhouseAdapter(BaseATSAdapter):
    platform = "greenhouse"

    async def fetch(self, company: CompanyConfig) -> list[dict[str, Any]]:
        base = company.careers_url.rstrip("/")
        try:
            html = await self.http.get(base)
        except Exception:
            logger.debug("HTTP fetch failed for %s", company.name)
            return []

        jobs = _extract_remix_jobs(html, company.name)
        if jobs:
            return jobs

        jobs = _extract_next_jobs(html, company.name)
        if jobs:
            return jobs

        logger.debug("No recognized data format for %s", company.name)
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

        job_id = str(item.get("id", item.get("greenhouseId", "")))
        absolute_url = item.get("absolute_url", "")
        location_name = _resolve_location(item)

        metadata: list[dict[str, Any]] = item.get("metadata", []) or []
        employment_type = _extract_metadata(metadata, "Employment Type") or item.get("employmentType")
        departments = " > ".join(
            d.get("name", "") for d in item.get("departments", []) or [] if isinstance(d, dict)
        )
        experience = (
            _extract_metadata(metadata, "Experience Level")
            or departments
            or item.get("team")
            or None
        )

        posted_str = item.get("updated_at", item.get("updatedAt", ""))
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
            experience_level=experience,
            posted_at=posted_at,
            is_remote=_is_remote(location_name),
            remote_type="remote"
            if _is_remote(location_name)
            else "hybrid"
            if "hybrid" in location_name.lower()
            else "onsite",
        )


def _extract_remix_jobs(html: str, company_name: str) -> list[dict[str, Any]]:
    m = _REMIX_RE.search(html)
    if not m:
        return []
    try:
        data = json5.loads(m.group(1))
        ld_key = [k for k in data["state"]["loaderData"] if k != "root"]
        if not ld_key:
            return []
        ld = data["state"]["loaderData"][ld_key[0]]
        return list(ld.get("jobPosts", {}).get("data", []))
    except Exception:
        logger.debug("Remix parse failed for %s", company_name)
        return []


def _extract_next_jobs(html: str, company_name: str) -> list[dict[str, Any]]:
    m = _NEXT_DATA_RE.search(html)
    if not m:
        return []
    try:
        data = _json.loads(m.group(1))
    except (_json.JSONDecodeError, ValueError):
        logger.debug("Next.js JSON parse failed for %s", company_name)
        return []

    pp = data.get("props", {}).get("pageProps", {})
    job_index = pp.get("jobIndexData", {})
    if not job_index:
        return []

    jobs_list = job_index.get("jobs", job_index.get("jobPosts", job_index.get("listings", [])))
    if not jobs_list:
        return []

    filters = job_index.get("filters", {}) or {}
    location_map = _build_lookup(filters.get("locations", []))
    team_map = _build_lookup(filters.get("teams", []))
    tag_map = _build_lookup(filters.get("tags", []))
    emp_types = filters.get("employmentTypes", []) or []

    result: list[dict[str, Any]] = []
    for j in jobs_list:
        try:
            enriched = dict(j)
            enriched["id"] = str(j.get("id", j.get("greenhouseId", "")))
            enriched["absolute_url"] = f"https://job-boards.greenhouse.io/{company_name}/jobs/{j.get('slug', enriched['id'])}"

            loc_indices = j.get("locationIndices", []) or []
            locations = [location_map.get(i, "") for i in loc_indices if isinstance(i, int)]
            enriched["location"] = ", ".join(loc for loc in locations if loc) or "Remote"

            team_indices = j.get("teamIndices", []) or []
            teams = [team_map.get(i, "") for i in team_indices if isinstance(i, int)]
            enriched["team"] = " > ".join(t for t in teams if t) or None

            tag_indices = j.get("tagIndices", []) or []
            tags = [tag_map.get(i, "") for i in tag_indices if isinstance(i, int)]
            enriched["tags"] = [tg for tg in tags if tg]

            et_idx = j.get("employmentTypeIndex")
            if et_idx is not None and et_idx < len(emp_types):
                et_item = emp_types[et_idx]
                enriched["employmentType"] = et_item.get("text", et_item.get("name", "")) if isinstance(et_item, dict) else str(et_item)

            result.append(enriched)
        except Exception:
            logger.debug("Failed to enrich Next.js job for %s", company_name)

    return result


def _build_lookup(items: list[dict[str, Any]]) -> dict[int, str]:
    if not items:
        return {}
    lookup: dict[int, str] = {}
    for i, item in enumerate(items):
        if isinstance(item, dict):
            idx = item.get("id", i)
            text = item.get("text", item.get("name", str(idx)))
            if isinstance(idx, int):
                lookup[idx] = str(text)
    return lookup


def _resolve_location(item: dict[str, Any]) -> str:
    loc = item.get("location", "")
    if isinstance(loc, dict):
        return loc.get("name", "")
    if isinstance(loc, str) and loc.strip():
        return loc.strip()
    return "Remote"


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
        return _strip_html(content)[:5000]
    if description:
        return _strip_html(description)[:5000]
    return ""


def _strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


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

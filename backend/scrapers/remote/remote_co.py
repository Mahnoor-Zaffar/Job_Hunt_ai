import logging
import re
from datetime import datetime
from typing import Any

from backend.scrapers.base.scraper import BaseScraper
from backend.scrapers.models.models import RawJob
from backend.scrapers.registry.registry import register

logger = logging.getLogger("job_hunting.remote_co")

BASE_URL = "https://remote.co"


@register(
    "remote_co",
    display_name="Remote.co",
    locations=["Remote"],
    interval=30,
)
class RemoteCoScraper(BaseScraper):
    """Scraper for Remote.co — curated remote job listings."""

    source = "remote_co"
    _MAX_PAGES = 3

    async def fetch(self) -> list[str]:
        pages: list[str] = []
        urls = [f"{BASE_URL}/remote-jobs/"] + [
            f"{BASE_URL}/remote-jobs/page/{p}/" for p in range(2, self._MAX_PAGES + 1)
        ]
        for url in urls:
            try:
                html = await self.http.get(url)
                pages.append(html)
            except Exception:
                logger.exception("Failed to fetch %s", url)
        return pages

    async def parse(self, raw: Any) -> list[RawJob]:
        pages: list[str] = raw if isinstance(raw, list) else [str(raw)]
        jobs: list[RawJob] = []
        seen: set[str] = set()

        for html in pages:
            for item in self._extract_jobs(html):
                key = item.get("source_id", "")
                if key and key not in seen:
                    seen.add(key)
                    try:
                        jobs.append(self._to_raw(item))
                    except Exception:
                        logger.exception("Failed to parse job %s", key)

        return jobs

    def _extract_jobs(self, html: str) -> list[dict[str, str]]:
        results: list[dict[str, str]] = []
        blocks = re.split(r'<div\s+class="job[^"]*"[^>]*>', html, flags=re.IGNORECASE)
        for block in blocks[1:]:
            match = re.search(
                r'<a\s+href="(/?remote-jobs/[^"]+)"[^>]*>\s*([^<]+)\s*</a>',
                block, re.IGNORECASE | re.DOTALL,
            )
            title_match = re.search(r'<h2[^>]*>\s*<a[^>]*>\s*([^<]+)\s*</a>\s*</h2>', block, re.IGNORECASE | re.DOTALL)
            title = match.group(2).strip() if match else ""
            if not title:
                title = title_match.group(1).strip() if title_match else ""
            url_path = match.group(1) if match else ""
            apply_url = f"{BASE_URL}{url_path}" if url_path and not url_path.startswith("http") else url_path

            company = ""
            cm = re.search(r'<p\s+class="company">\s*([^<]+)\s*</p>', block, re.IGNORECASE)
            if cm:
                company = re.sub(r'<[^>]+>', '', cm.group(1)).strip()

            location = "Remote"
            lm = re.search(r'<p\s+class="location">\s*([^<]+)\s*</p>', block, re.IGNORECASE)
            if lm:
                location = lm.group(1).strip()

            description = ""
            dm = re.search(r'<div\s+class="desc">\s*([^<]+)\s*</div>', block, re.IGNORECASE | re.DOTALL)
            if dm:
                description = re.sub(r'<[^>]+>', '', dm.group(1)).strip()

            if title and company:
                job_id = re.sub(r'[^a-z0-9]+', '-', f"{title}-{company}".lower()).strip("-")
                results.append({
                    "title": title,
                    "company": company,
                    "location": location,
                    "apply_url": apply_url,
                    "description": description[:2000] if description else "",
                    "source_id": f"remoteco-{job_id}",
                })

        return results

    def _to_raw(self, item: dict[str, str]) -> RawJob:
        return RawJob(
            title=item["title"],
            company=item["company"],
            location=item.get("location", "Remote"),
            description=item.get("description", ""),
            url=item.get("apply_url", ""),
            apply_url=item.get("apply_url") or None,
            source=self.source,
            source_id=item["source_id"],
            posted_at=datetime.utcnow(),
            is_remote=True,
            remote_type="remote",
        )

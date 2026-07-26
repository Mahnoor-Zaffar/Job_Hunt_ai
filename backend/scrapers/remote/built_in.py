import logging
import re
from datetime import datetime
from typing import Any
from urllib.parse import urljoin

from backend.scrapers.base.scraper import BaseScraper
from backend.scrapers.models.models import RawJob
from backend.scrapers.registry.registry import register

logger = logging.getLogger("job_hunting.built_in")

BASE_URL = "https://builtin.com"


@register(
    "built_in",
    display_name="Built In",
    locations=["Remote"],
    interval=60,
)
class BuiltInScraper(BaseScraper):
    """Scraper for BuiltIn.com — tech-focused remote jobs."""

    source = "built_in"
    _MAX_PAGES = 2

    async def fetch(self) -> list[str]:
        pages: list[str] = []
        urls = [f"{BASE_URL}/jobs/remote"] + [
            f"{BASE_URL}/jobs/remote?page={p}" for p in range(2, self._MAX_PAGES + 1)
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
        blocks = re.split(r'<article[^>]*>', html, flags=re.IGNORECASE)
        if len(blocks) < 2:
            blocks = re.split(r'<div[^>]*class="[^"]*job-card[^"]*"[^>]*>', html, flags=re.IGNORECASE)

        for block in blocks[1:]:
            title = ""
            tm = re.search(
                r'<a[^>]*href="(/jobs/[^"]+)"[^>]*>\s*([^<]+)\s*</a>',
                block, re.IGNORECASE | re.DOTALL,
            )
            if tm:
                url_path = tm.group(1)
                title = re.sub(r'\s+', ' ', tm.group(2)).strip()

            if not title:
                tm2 = re.search(r'<h3[^>]*>\s*<a[^>]*>\s*([^<]+)\s*</a>\s*</h3>', block, re.IGNORECASE | re.DOTALL)
                if tm2:
                    title = re.sub(r'\s+', ' ', tm2.group(1)).strip()
                    url_match = re.search(r'href="([^"]+)"', tm2.group(0))
                    url_path = url_match.group(1) if url_match else ""

            company = ""
            cm = re.search(r'<span[^>]*class="[^"]*company[^"]*"[^>]*>\s*([^<]+)\s*</span>', block, re.IGNORECASE)
            if not cm:
                cm = re.search(r'<div[^>]*class="[^"]*company[^"]*"[^>]*>\s*([^<]+)\s*</div>', block, re.IGNORECASE)
            if cm:
                company = re.sub(r'\s+', ' ', cm.group(1)).strip()

            location = "Remote"
            lm = re.search(r'<span[^>]*class="[^"]*location[^"]*"[^>]*>\s*([^<]+)\s*</span>', block, re.IGNORECASE)
            if lm:
                loc_text = lm.group(1).strip()
                if "remote" in loc_text.lower():
                    location = "Remote"
                else:
                    location = loc_text

            description = ""
            dm = re.search(r'<p[^>]*class="[^"]*description[^"]*"[^>]*>\s*([^<]+)\s*</p>', block, re.IGNORECASE | re.DOTALL)
            if dm:
                description = re.sub(r'<[^>]+>', '', dm.group(1)).strip()

            if title and company:
                job_id = re.sub(r'[^a-z0-9]+', '-', f"{title}-{company}".lower()).strip("-")
                apply_url = urljoin(BASE_URL, url_path) if 'url_path' in dir() and url_path else ""
                results.append({
                    "title": title,
                    "company": company,
                    "location": location,
                    "apply_url": apply_url,
                    "description": description[:2000] if description else "",
                    "source_id": f"builtin-{job_id}",
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

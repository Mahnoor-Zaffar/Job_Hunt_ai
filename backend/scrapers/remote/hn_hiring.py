"""Hacker News 'Who is hiring?' scraper — monthly thread via Firebase API."""

import logging
import re
from datetime import UTC, datetime
from typing import Any

from backend.scrapers.base.scraper import BaseScraper
from backend.scrapers.models.models import RawJob
from backend.scrapers.registry.registry import register

logger = logging.getLogger("job_hunting.hn_hiring")

HN_API = "https://hacker-news.firebaseio.com/v0"


@register("hn_hiring", display_name="HN Who's Hiring", locations=["Remote"], interval=60)
class HNHiringScraper(BaseScraper):
    source = "hn_hiring"

    async def fetch(self) -> str:
        try:
            top_stories = await self.http.get_json(f"{HN_API}/topstories.json")
            who_is_hiring = None
            for story_id in top_stories[:30] if isinstance(top_stories, list) else []:
                item = await self.http.get_json(f"{HN_API}/item/{story_id}.json")
                if (
                    isinstance(item, dict)
                    and "who is hiring" in (item.get("title", "") or "").lower()
                ):
                    who_is_hiring = item.get("id")
                    break
            if who_is_hiring:
                return await self.http.get(f"https://news.ycombinator.com/item?id={who_is_hiring}")
        except Exception:
            logger.exception("HN fetch failed")
        return ""

    async def parse(self, raw: Any) -> list[RawJob]:
        html = str(raw)
        jobs: list[RawJob] = []
        comments = re.findall(r'<div class="comment">(.*?)</div>', html, re.DOTALL)
        for comment in comments:
            text = re.sub(r"<[^>]+>", " ", comment).strip()
            if len(text) < 30:
                continue

            lines = text.split("\n")
            first_line = lines[0].strip() if lines else ""
            location = "Remote"
            for kw in ["remote", "onsite", "hybrid", "on-site"]:
                if kw in first_line.lower():
                    location = "Remote" if kw == "remote" else kw.title()
                    break

            company = first_line.split("|")[0].split("-")[0].strip()[:100]
            title_parts = first_line.split("|")
            title = title_parts[1].strip() if len(title_parts) > 1 else first_line[:100]

            source_id = f"hn-{hash(comment) & 0xFFFFFFFF}"

            jobs.append(
                RawJob(
                    title=title[:200] or "Software Engineer",
                    company=company or "Y Combinator Startup",
                    location=location,
                    description=text[:3000],
                    url=f"https://news.ycombinator.com/item?id={source_id[3:]}",
                    source=self.source,
                    source_id=source_id,
                    is_remote="remote" in location.lower(),
                    remote_type="remote" if "remote" in location.lower() else "onsite",
                    posted_at=datetime.now(UTC),
                )
            )
        return jobs

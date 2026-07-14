"""Illustrative scraper that parses mock HTML.

This scraper demonstrates how to implement ``fetch`` and ``parse``
using the framework's parser utilities.  It does **not** hit a real
website — instead it returns a hardcoded HTML snippet that mimics a
typical job-listing page.
"""

import logging
from datetime import UTC, datetime
from typing import Any

from backend.scrapers.base.scraper import BaseScraper
from backend.scrapers.models.models import RawJob
from backend.scrapers.parser import parser as parse_utils
from backend.scrapers.registry.registry import register

logger = logging.getLogger("job_hunting.example")

MOCK_HTML = """
<div class="job-listing">
  <h2 class="title">Senior Python Engineer</h2>
  <div class="company">Acme Corp</div>
  <div class="location">Islamabad, Pakistan</div>
  <div class="description">
    We are looking for an experienced Python engineer to join our team.
  </div>
  <a class="apply-link" href="https://example.com/apply/123">Apply</a>
  <div class="meta">
    <span class="type">Full Time</span>
    <span class="level">Senior</span>
    <span class="salary">$80,000 - $100,000</span>
  </div>
</div>
"""


@register(
    "example",
    display_name="Example Mock Source",
    locations=["Pakistan"],
    interval=30,
)
class MockHTMLScraper(BaseScraper):
    """Demonstrates the scraper framework with a hardcoded HTML snippet.

    Useful for integration testing and as a reference implementation.
    """

    source = "example"

    async def fetch(self) -> str:
        return MOCK_HTML

    async def parse(self, raw: Any) -> list[RawJob]:
        tree = parse_utils.from_html(raw)

        title = parse_utils.text(tree, "h2.title")
        company = parse_utils.text(tree, ".company")
        location = parse_utils.text(tree, ".location")
        description = parse_utils.text(tree, ".description")
        url = parse_utils.attr(tree, "a.apply-link", "href")
        employment_type = parse_utils.text(tree, ".type")
        experience_level = parse_utils.text(tree, ".level")
        salary_text = parse_utils.text(tree, ".salary")

        salary_min = salary_max = currency = None
        if salary_text:
            parts = salary_text.replace(",", "").split(" - ")
            if parts and parts[0].lstrip("$€£").replace(".", "").isdigit():
                salary_min = float(parts[0].lstrip("$€£"))
                currency = "USD"
            if len(parts) > 1:
                salary_max = float(parts[1].lstrip("$€£"))

        raw_job = RawJob(
            title=title or "",
            company=company or "",
            location=location or "",
            description=description,
            url=url or "https://example.com",
            source=self.source,
            source_id="example-123",
            salary_min=salary_min,
            salary_max=salary_max,
            currency=currency,
            employment_type=employment_type,
            experience_level=experience_level,
            posted_at=datetime.now(UTC),
            is_remote=" remote" in (location or "").lower(),
        )
        return [raw_job]

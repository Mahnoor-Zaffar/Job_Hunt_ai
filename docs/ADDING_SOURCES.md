# Adding a New Job Source

This guide explains how to add a new job source to the scraper framework in under
one hour. You will:

1. Create a scraper class
2. Implement `fetch()` and `parse()`
3. Register it with the `@register` decorator
4. Write tests

## Quick Start

### Step 1: Create your scraper file

```python
# backend/scrapers/your_source/scraper.py

import logging
from typing import Any
from backend.scrapers.base.scraper import BaseScraper
from backend.scrapers.models.models import RawJob
from backend.scrapers.parser import parser as parse_utils
from backend.scrapers.registry.registry import register

logger = logging.getLogger("job_hunting.your_source")


@register(
    "your_source",                       # unique source key
    display_name="Your Source Name",      # human-readable name
    locations=["Remote"],                 # Pakistan, Remote, or both
    interval=30,                          # minutes between scrapes
)
class YourScraper(BaseScraper):
    source = "your_source"
    BASE_URL = "https://yoursource.com"

    async def fetch(self) -> Any:
        """Retrieve raw data from your source."""
        html = await self.http.get(f"{self.BASE_URL}/jobs")
        return html

    async def parse(self, raw: Any) -> list[RawJob]:
        """Convert raw HTML into RawJob objects."""
        tree = parse_utils.from_html(raw)
        # Your parsing logic here
        ...
```

### Step 2: Implement `fetch()`

**For static HTML sites** — use `self.http.get()`:

```python
async def fetch(self) -> str:
    return await self.http.get("https://example.com/jobs")
```

**For JSON APIs** — use `self.http.get_json()`:

```python
async def fetch(self) -> list[dict]:
    return await self.http.get_json("https://api.example.com/jobs")
```

**For JavaScript-rendered pages** — use `self.get_page()`:

```python
async def fetch(self) -> str:
    page = await self.get_page()
    await page.goto("https://example.com/jobs")
    await page.wait_for_selector(".job-listing")
    return await page.content()
```

**For multi-page scraping** — return a list of pages:

```python
async def fetch(self) -> list[str]:
    pages = []
    for page_num in range(1, 6):
        html = await self.http.get(f"{BASE_URL}/jobs?page={page_num}")
        pages.append(html)
    return pages
```

### Step 3: Implement `parse()`

Use the parser utilities to extract data from HTML:

```python
async def parse(self, raw: Any) -> list[RawJob]:
    tree = parse_utils.from_html(raw)
    jobs = []

    for card in tree.css(".job-card"):
        # Parse each card's inner HTML
        card_tree = parse_utils.from_html(card.html)

        # Extract fields with CSS selectors
        title = parse_utils.text(card_tree, ".job-title") or ""
        company = parse_utils.text(card_tree, ".company") or ""
        location = parse_utils.text(card_tree, ".location") or ""
        url = parse_utils.attr(card_tree, "a.apply", "href") or ""

        jobs.append(RawJob(
            title=title,
            company=company,
            location=location,
            url=url,
            source=self.source,
            source_id=f"my-{job_id}",
            is_remote="remote" in location.lower(),
        ))

    return jobs
```

For JSON API responses, iterate over the JSON directly:

```python
async def parse(self, raw: Any) -> list[RawJob]:
    for item in raw:
        yield RawJob(
            title=item["title"],
            company=item["company"]["name"],
            ...
        )
```

### Step 4: Add to package exports

Update `backend/scrapers/__init__.py` to export your scraper:

```python
from backend.scrapers.your_source import YourScraper
```

### Step 5: Write tests

Create `tests/test_scrapers/test_your_source.py`:

```python
from unittest.mock import AsyncMock, patch
import pytest
from backend.scrapers.your_source import YourScraper
from backend.scrapers.models.models import RawJob


class TestYourScraper:
    @pytest.mark.asyncio
    async def test_parse_extracts_fields(self) -> None:
        scraper = YourScraper()
        html = '<div class="job">...</div>'
        jobs = await scraper.parse(html)
        assert len(jobs) == 1
        assert isinstance(jobs[0], RawJob)
        assert jobs[0].title == "Expected Title"

    @pytest.mark.asyncio
    async def test_fetch_mocked(self) -> None:
        scraper = YourScraper()
        with patch.object(scraper.http, "get", AsyncMock(return_value="mock html")):
            result = await scraper.fetch()
            assert result == "mock html"
```

## Parser Utilities Reference

All from `backend.scrapers.parser.parser`:

| Function | Returns | Description |
|---|---|---|
| `from_html(html)` | `HTMLParser` | Parse HTML string (Selectolax) |
| `from_html_soup(html)` | `BeautifulSoup` | Parse HTML string (BS4 fallback) |
| `text(tree, selector)` | `str \| None` | Text of first matching element |
| `texts(tree, selector)` | `list[str]` | Text of all matching elements |
| `attr(tree, selector, name)` | `str \| None` | Attribute value of first match |
| `attrs(tree, selector, name)` | `list[str]` | Attribute values of all matches |

## RawJob Field Reference

All scraper-extracted fields available:

| Field | Type | Required | Description |
|---|---|---|---|
| `title` | `str` | Yes | Job title |
| `company` | `str` | Yes | Company name |
| `company_url` | `str \| None` | No | Company website |
| `location` | `str \| None` | No | Raw location string |
| `description` | `str \| None` | No | Full job description |
| `url` | `str` | Yes | Job listing URL |
| `apply_url` | `str \| None` | No | Direct application URL |
| `source` | `str` | Yes | Source key (auto-set by framework) |
| `source_id` | `str` | Yes | Unique ID within source |
| `salary_min` | `float \| None` | No | Minimum salary |
| `salary_max` | `float \| None` | No | Maximum salary |
| `currency` | `str \| None` | No | Salary currency (USD, PKR, EUR...) |
| `employment_type` | `str \| None` | No | Full time, part time, contract... |
| `experience_level` | `str \| None` | No | Senior, mid, junior, intern... |
| `skills` | `list[str] \| None` | No | Technologies/skills (enriched by normalizer) |
| `requirements` | `str \| None` | No | Extracted requirements |
| `posted_at` | `datetime \| None` | No | When job was posted |
| `expires_at` | `datetime \| None` | No | When job expires |
| `remote_type` | `Literal["remote","hybrid","onsite"]` | No | Default "onsite" |
| `is_remote` | `bool` | No | Default False |
| `city` | `str \| None` | No | City (auto-resolved by normalizer) |
| `country` | `str \| None` | No | Country (auto-resolved by normalizer) |

## What the Framework Handles for You

You do **not** need to implement:
- **Normalization** — Titles are cleaned, locations parsed, salaries normalized,
  employment types mapped, skills enriched from description.
- **Validation** — Required fields, URL format, salary consistency checked.
- **Deduplication** — SHA-256 fingerprint computed and checked via repository.
- **Persistence** — Orchestrator writes validated jobs to PostgreSQL.
- **Retry logic** — `HttpClient` retries network errors with configurable count.
- **Rate limiting** — Configurable delay between requests.
- **Error isolation** — One failing scraper never stops others.
- **Browser lifecycle** — Shared `BrowserManager` handles Playwright lifecycle.
- **Metrics & logging** — Structured logging per source with duration tracking.

## ATS Adapters

If you're adding an ATS platform (like a new ATS provider), see the ATS adapter
architecture in `SCRAPER_FRAMEWORK.md`. ATS adapters use a different pattern:

1. Create an adapter class inheriting `BaseATSAdapter` in `scrapers/ats/`
2. Implement `fetch(company)` and `parse(raw, company)`
3. Register it in `_ADAPTER_REGISTRY` in the ATS orchestrator
4. Add companies to `scrapers/config/companies.yaml`

## Register Decorator Parameters

```python
@register(
    source: str,                              # unique key (required)
    display_name: str = "",                   # human-readable label
    locations: list[str] | None = None,       # Pakistan, Remote
    interval: int = 30,                       # scrape interval in minutes
)
```

## Example: Complete API-Based Scraper

```python
# backend/scrapers/new_source/scraper.py
import logging
from datetime import datetime
from typing import Any

from backend.scrapers.base.scraper import BaseScraper
from backend.scrapers.models.models import RawJob
from backend.scrapers.registry.registry import register

logger = logging.getLogger("job_hunting.new_source")
API_URL = "https://api.example.com/v1/jobs"


@register("new_source", display_name="New Source", locations=["Remote"])
class NewSourceScraper(BaseScraper):
    source = "new_source"

    async def fetch(self) -> list[dict[str, Any]]:
        return await self.http.get_json(API_URL)

    async def parse(self, raw: Any) -> list[RawJob]:
        items: list[dict] = raw
        jobs = []
        for item in items:
            if not item.get("title") or not item.get("company"):
                continue
            jobs.append(RawJob(
                title=item["title"].strip(),
                company=item["company"].strip(),
                location=item.get("location", "Remote"),
                description=item.get("description"),
                url=item.get("url", ""),
                apply_url=item.get("apply_url"),
                source=self.source,
                source_id=f"ns-{item['id']}",
                salary_min=float(item["salary"]) if item.get("salary") else None,
                currency="USD",
                posted_at=_parse_date(item.get("posted_at")),
                is_remote=True,
                remote_type="remote",
            ))
        return jobs


def _parse_date(value: str) -> datetime | None:
    if not value:
        return None
    from datetime import datetime
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
```

## Checklist

After creating your scraper, verify:

- [ ] `@register` decorator with unique source key
- [ ] `fetch()` returns raw data (HTML, JSON, or list)
- [ ] `parse()` returns `list[RawJob]` with all extractable fields
- [ ] `source_id` is unique within your source (use pattern like `source-{id}`)
- [ ] No direct database writes
- [ ] No AI/notification/business logic
- [ ] Tests written with mocked HTTP/browser
- [ ] Exported in `scrapers/__init__.py`
- [ ] `ruff check .` passes
- [ ] `mypy backend/` passes
- [ ] `pytest tests/test_scrapers/` passes

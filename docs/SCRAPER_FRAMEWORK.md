# Scraper Framework

The Job Hunting scraper framework provides a reusable, strongly-typed foundation for
building job-source integrations. Every scraper inherits `BaseScraper`, receives
infrastructure via dependency injection, and follows a consistent pipeline.

## Architecture

```text
┌──────────────────────────────────────────────────────────────┐
│                   ScraperOrchestrator                         │
│  Parallel execution · Semaphore · Persistence · Metrics      │
└──────────────────────┬───────────────────────────────────────┘
                       │ dispatches
     ┌─────────────────┼──────────────────┐
     ▼                 ▼                  ▼
┌──────────┐  ┌──────────────┐  ┌─────────────────────────┐
│ Pakistan │  │   Remote     │  │         ATS             │
│ Rozee    │  │ RemoteOK     │  │ companies.yaml          │
│ Mustakbil│  │ WWRemotely   │  │ GreenhouseAdapter       │
│BrightSpyr│  │ Remotive     │  │ LeverAdapter            │
└──────────┘  └──────────────┘  │ AshbyAdapter             │
                                │ WorkableAdapter          │
                                │ ATSOrchestrator          │
                                └─────────────────────────┘

Shared Components:
  HttpClient  ·  BrowserManager  ·  Normalizer  ·  Validator
  Parser      ·  TechnologyExtractor  ·  ScraperRegistry
```

## Data Pipeline

Every job follows the same pipeline regardless of source:

```text
Website / API
       │
       ▼
  HTTP / Browser          (fetch — async)
       │
       ▼
  Parser                  (parse — async)
       │
       ▼
  RawJob                  (source-specific extracted data)
       │
       ▼
  Normalizer              (normalize — sync)
       │
       ▼
  Validator               (validate — sync)
       │
       ▼
  NormalizedJob           (canonical, ready for storage)
       │
       ▼
  Repository              (dedup via fingerprint + persist)
```

## Core Interfaces

### `BaseScraper`

The abstract base that all scrapers inherit. Subclasses only implement two methods:

```python
class MyScraper(BaseScraper):
    source = "my_source"

    async def fetch(self) -> Any:
        """Retrieve raw data (HTML, JSON, bytes)."""
        ...

    async def parse(self, raw: Any) -> list[RawJob]:
        """Convert raw data into RawJob list."""
        ...
```

Properties injected automatically:
- `self.http` — shared `HttpClient` with connection pooling, retry, rate limiting
- `self._browser_manager` — singleton `BrowserManager` for JS-rendered pages
- `self._normalizer` — `Normalizer` with location, salary, skills enrichment
- `self._validator` — `Validator` with required-field, URL, and salary checks
- `self._settings` — `ScraperSettings` from env vars (prefix `SCRAPER_`)

Helper methods available:
- `await self.get_page()` — returns a Playwright `Page` for JS rendering
- `self.normalize(raw_job)` — convert `RawJob` → `NormalizedJob`
- `self.validate(job)` — validate a `NormalizedJob`
- `self.cleanup()` — release resources (override in subclasses if needed)

### Registration

Register scrapers with the `@register` decorator:

```python
from backend.scrapers.registry.registry import register

@register(
    "source_key",
    display_name="Human-Readable Name",
    locations=["Pakistan"],
    interval=30,  # minutes between scrapes
)
class MyScraper(BaseScraper):
    ...
```

### `ScraperRegistry`

The global registry tracks all registered scraper classes:

```python
registry = ScraperRegistry()
registry.all()            # → dict[str, type[BaseScraper]]
registry.get("source")    # → type[BaseScraper] | None
registry.get_enabled()    # → list filtered by ENABLED_SCRAPERS / DISABLED_SCRAPERS
registry.list_sources()   # → list of metadata dicts
```

### `ScraperOrchestrator`

Runs scrapers in parallel with controlled concurrency:

```python
orchestrator = ScraperOrchestrator()
summary = await orchestrator.run_all()         # all enabled scrapers
result = await orchestrator.run_single("rozee")  # one specific scraper
```

Returns `ExecutionSummary` with per-scraper `ScraperResult` entries.

## Components

### HTTP Client (`scrapers/http/client.py`)

- Async `httpx` with connection pooling
- Configurable retries (max 3)
- Rate limit detection (HTTP 429 → raises `RateLimitError`)
- Convenience `get_json()` for API sources

### Browser Manager (`scrapers/browser/manager.py`)

- Shared Playwright singleton across all scrapers
- Lazy-starts Chromium on first `get_page()` call
- Injected into `BaseScraper` via `BrowserManager`
- Scrapers use `await self.get_page()` for JS-rendered content

### Parser (`scrapers/parser/parser.py`)

- Selectolax (fast C parser) with BeautifulSoup fallback
- `from_html(html)`, `from_html_soup(html)` — parse HTML strings
- `text(tree, selector)`, `texts(tree, selector)` — extract text content
- `attr(tree, selector, name)`, `attrs(tree, selector, name)` — extract attributes

### Normalizer (`scrapers/normalizer/normalizer.py`)

- Cleans titles, strips whitespace, normalizes text
- Maps employment types: `"Full Time"` → `"full_time"`
- Maps experience levels: `"senior"` → `"senior"`
- Parses location into city + country using known cities map
- Derives `remote_type` from location text (remote/hybrid/onsite)
- Generate SHA-256 fingerprint for deduplication
- Merges scraper-provided skills with technology extraction from description

### Validator (`scrapers/validator/validator.py`)

- Checks required fields (title, company, location, url, source, source_id, fingerprint)
- Validates URL format (must start with http/https)
- Warns on salary inconsistencies (min > max, salary without currency)
- Reports errors and warnings separately

### Technology Extractor (`scrapers/technologies/extractor.py`)

- Deterministic regex-based extraction from job descriptions
- Covers 80+ technologies across categories:
  - Languages: Python, JavaScript, TypeScript, Rust, Go, Java, C#, C++, Ruby, PHP, Swift, Kotlin
  - Frameworks: FastAPI, Django, Flask, React, Vue, Angular, Next.js, Ruby on Rails
  - Infrastructure: Docker, Kubernetes, AWS, Azure, GCP, Terraform, CI/CD
  - Databases: PostgreSQL, MySQL, MongoDB, Redis, Elasticsearch
  - ML/AI: PyTorch, TensorFlow, scikit-learn, LangChain, OpenAI
  - Tools: Git, Selenium, Playwright, Cypress, Pytest, Jest, Jira
- Case-insensitive matching
- Returns sorted list to ensure determinism

### Exception Hierarchy (`scrapers/exceptions/exceptions.py`)

```text
ScraperError
├── FetchError          — HTTP / network failures
├── ParseError          — HTML / JSON parse failures
├── BrowserError        — Playwright / browser failures
├── ScraperTimeoutError — request timeouts
├── RateLimitError      — HTTP 429 or similar
└── NormalizationError  — data normalization failures
```

## Configuration

### `ScraperSettings` (env vars with `SCRAPER_` prefix)

| Variable | Default | Description |
|---|---|---|
| `SCRAPER_INTERVAL_MINUTES` | 30 | Default scrape interval |
| `SCRAPER_MAX_CONCURRENT` | 5 | Max parallel scrapers |
| `SCRAPER_TIMEOUT_SECONDS` | 30 | HTTP request timeout |
| `SCRAPER_HEADLESS` | true | Run Playwright headless |
| `SCRAPER_MAX_RETRIES` | 3 | HTTP retry count |
| `SCRAPER_RATE_LIMIT_DELAY` | 0.5 | Delay between requests |
| `SCRAPER_ENABLED_SCRAPERS` | [] | Explicitly enabled sources |
| `SCRAPER_DISABLED_SCRAPERS` | [] | Explicitly disabled sources |
| `SCRAPER_PROXY_URL` | "" | Optional HTTP proxy |

### Company Configuration (`scrapers/config/companies.yaml`)

```yaml
companies:
  - name: Motive
    platform: greenhouse
    careers_url: https://boards.greenhouse.io/motive

  - name: Arbisoft
    platform: lever
    careers_url: https://api.lever.co/v0/postings/arbisoft

  - name: Systems Ltd
    platform: workable
    careers_url: https://apply.workable.com/systems
    skip: false
```

Adding a company to ATS scraping requires NO code changes — just a YAML entry.

### Per-Source Settings (future)

For scrapers that need custom configuration (API keys, custom base URLs), add
fields to `ScraperSettings` with the env var prefix pattern (e.g., `SCRAPER_ROZEE_API_KEY`).

## Canonical Models

### `RawJob`

Extracted but un-normalized job data from a source. Fields include:
`title`, `company`, `company_url`, `location`, `description`, `url`, `apply_url`,
`source`, `source_id`, `salary_min`, `salary_max`, `currency`, `employment_type`,
`experience_level`, `skills`, `requirements`, `posted_at`, `expires_at`,
`remote_type`, `is_remote`, `city`, `country`

### `NormalizedJob`

Canonical representation after normalization. Identical to `RawJob` but with
`location`, `remote_type`, and `fingerprint` fully resolved. Ready for persistence.

### `ValidationResult`

- `is_valid: bool`
- `errors: list[str]` — blocking issues (missing required fields)
- `warnings: list[str]` — non-blocking issues (salary inconsistencies)

### `ScraperResult` / `ExecutionSummary`

Execution metrics:
- `source`, `success`, `jobs_found`, `duration_seconds`, `error`
- Aggregated via `ExecutionSummary`: totals across all scrapers

## ATS Adapter Architecture

ATS platforms (Greenhouse, Lever, Ashby, Workable) use a different architecture:

```text
companies.yaml
       │
       ▼
  ATSOrchestrator  (BaseScraper subclass, registered as "ats")
       │
       ├── GreenhouseAdapter  ←  companies with platform=greenhouse
       ├── LeverAdapter       ←  companies with platform=lever
       ├── AshbyAdapter       ←  companies with platform=ashby
       └── WorkableAdapter    ←  companies with platform=workable
```

Each adapter implements `fetch(company)` and `parse(raw, company)` but does NOT
inherit `BaseScraper`. The `ATSOrchestrator` handles orchestration, error isolation,
data aggregation, and framework integration.

### Company configuration

Company entries live in `scrapers/config/companies.yaml`. Adding a company is a
config-only change — no new scraper code required.

## Design Principles

1. **Scrapers never contain business logic.** They only discover, fetch, parse,
   normalize, and validate.
2. **Scrapers never write directly to the database.** Persistence is delegated to
   the repository layer (called by the orchestrator).
3. **One failing scraper never stops the pipeline.** Errors are isolated per-source.
4. **Dependency injection throughout.** HttpClient, BrowserManager, Normalizer,
   Validator are injected, not hardcoded.
5. **Async end-to-end.** IO operations are async; normalization and validation are sync.
6. **Strongly typed.** Everything has type hints; mypy runs in strict mode.

## Pakistan Location Filtering

The platform targets Islamabad, Rawalpindi, and Lahore. Remote jobs are always included.

The `Normalizer.is_supported_location(job)` method returns `True` when:
- `job.remote_type == "remote"` OR
- `job.city` (lowercase) is in `{islamabad, rawalpindi, lahore}`

Karachi and other Pakistani cities are recognized (city extraction works) but are
flagged as unsupported by the filter.

## Remote Type Detection

`remote_type` is derived from multiple signals, in order:
1. **Raw remote_type** from the scraper (if set to non-"onsite")
2. **is_remote flag** from the scraper → "remote"
3. **Hybrid keywords** in location text ("hybrid", "hybrid-remote", "flexible remote") → "hybrid"
4. **Remote keywords** in location text ("remote", "WFH", "work from home") → "remote"
5. **Default** → "onsite"

## Technology Extraction

Technology names are extracted from job descriptions using pre-compiled regex patterns
in `scrapers/technologies/extractor.py`. The approach is deterministic (no AI) and covers
80+ common keywords. Results are returned as a sorted list.

Usage in a scraper does not require explicit code — the `Normalizer` automatically
merges scraper-provided skills with extracted technologies from the description.

## Location Normalization

The `Normalizer._parse_location` method:
1. Splits location string on commas
2. Matches each part against `COUNTRY_MAP` and `KNOWN_CITIES_PK`
3. Returns formatted location, city, country, and remote_type
4. Recognizes Pakistan cities: Islamabad, Rawalpindi, Lahore, Karachi, Faisalabad,
   Multan, Peshawar, Quetta, Sialkot, Gujranwala, Gujrat, Hyderabad, Sahiwal, Abbottabad
5. Maps country shortcuts: pk→Pakistan, us→United States, uk→United Kingdom, etc.

## Metrics & Logging

All scrapers use structured logging via Python's `logging` module with the
`job_hunting.*` namespace. Key events include:
- Fetch/parse start and completion
- Jobs discovered per source
- Validation failures (with field-level details)
- Duration tracking
- Retries and failures

Prometheus-compatible metrics are planned for future integration.

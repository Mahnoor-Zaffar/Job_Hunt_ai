# Service Layer

The service layer contains **all business logic** for the Job Hunting platform.
Services never access the database directly — they delegate persistence to
repositories.  API routes delegate business rules to services.

## Architecture

```text
API Route (FastAPI)
       │
       ▼
   Service            ←  Business logic lives here
       │
       ▼
   Repository         ←  Persistence logic lives here
       │
       ▼
   SQLAlchemy / DB
```

Every service:
- Inherits `BaseService` (logging, error helpers)
- Accepts repositories via constructor injection
- Returns typed domain models
- Is fully async
- Is independently testable with mocked repositories

## Services

### `JobService`

Manages job status transitions and duplicate detection.

| Method | Description |
|---|---|
| `mark_applied(job_id)` | Mark a job as applied |
| `mark_saved(job_id)` | Save a job for later |
| `mark_expired(job_id)` | Mark a job as expired |
| `find_duplicates(fingerprint)` | Find all jobs sharing a fingerprint |
| `expire_old_jobs()` | Batch-expire past-due jobs |
| `get_stats()` | Count active jobs |
| `ensure_company_exists(name)` | Create Company record if missing |

### `CompanyService`

Manages company records discovered during scraping.

| Method | Description |
|---|---|
| `get_or_create(name)` | Find or create company by name |
| `get_active_companies()` | List non-deactivated companies |
| `find_by_name(name)` | Look up a specific company |
| `deactivate(company_name)` | Soft-deactivate a company |
| `update_metadata(name, ...)` | Enrich company with website/industry/desc |

### `ResumeService`

Handles resume upload, parsing, and version management.

| Method | Description |
|---|---|
| `get_user_resumes(user_id)` | List all resumes for a user |
| `get_primary_resume(user_id)` | Get the default resume |
| `set_primary(resume_id)` | Promote a resume to primary |
| `create_resume(user_id, ...)` | Upload a new resume |
| `update_text(resume_id, text)` | Update the parsed text content |

### `SearchService`

Job search with filtering, designed for future pgvector semantic search.

| Method | Description |
|---|---|
| `search(**filters)` | Filter jobs by title, company, location, salary, skills, etc. |
| `search_by_keyword(keyword)` | Full-text style search across title + company |

The `embedding` parameter is reserved for pgvector integration — accepted but
unused today.

### `ApplicationService`

Lifecycle management for job applications.

| Method | Description |
|---|---|
| `apply(user_id, job_id)` | Create (or return existing) application |
| `submit(application_id)` | Submit an application with timestamp |
| `update_status(id, status)` | Transition to any valid status |
| `get_user_applications(user_id)` | List user's applications |
| `get_by_status(status)` | Filter applications by status |
| `get_interviews(user_id)` | Applications in interview stage |

Valid statuses: `draft`, `submitted`, `under_review`, `interview`, `offer`,
`rejected`, `withdrawn`.

### `NotificationService`

Creates and manages user-facing notifications.

| Method | Description |
|---|---|
| `create(user_id, type, title, msg)` | Create a notification |
| `get_unread(user_id)` | Get unread notifications |
| `get_all(user_id)` | All notifications, paginated |
| `mark_read(notification_id)` | Mark single notification as read |
| `mark_all_read(user_id)` | Mark all notifications read for a user |

### `AnalyticsService`

Computes aggregate statistics for dashboard displays.

| Method | Description |
|---|---|
| `get_dashboard_stats()` | Total and active job counts |
| `get_jobs_by_source()` | Job count grouped by source |
| `get_applications_by_status()` | Application count by status |
| `get_scrape_health(limit)` | Recent scraper execution details |
| `get_full_dashboard()` | All dashboard data in one call |

### `SettingsService`

User-scoped key-value store for preferences.

| Method | Description |
|---|---|
| `get(user_id, key, default)` | Read a setting value |
| `set(user_id, key, value)` | Write or update a setting |
| `get_all(user_id)` | All settings for a user as dict |
| `delete(user_id, key)` | Remove a setting |

## Exception Hierarchy

All service exceptions extend `ServiceError`:

```text
ServiceError
├── NotFoundError     — Entity not found (404 equivalent)
├── DuplicateError    — Unique constraint violation (409 equivalent)
└── ValidationError   — Business rule violation (422 equivalent)
```

Usage in services:
```python
self._raise_not_found("Job", job_id)      # → NotFoundError
self._raise_duplicate("User", "email", e) # → DuplicateError
self._raise_validation("Status invalid")  # → ValidationError
```

## Protocol Interfaces

`backend/services/interfaces.py` defines `Protocol` classes for each service.
Use these for dependency injection so consumers depend on the contract, not the
implementation:

```python
from backend.services.interfaces import JobServiceProtocol

async def do_thing(service: JobServiceProtocol) -> None:
    job = await service.mark_applied(some_id)
```

## Base Service

`BaseService` provides:
- `self._log` — preconfigured logger
- `self._raise_not_found(entity, id)` — raise NotFoundError
- `self._raise_duplicate(entity, field, value)` — raise DuplicateError
- `self._raise_validation(message)` — raise ValidationError
- `self._log_operation(op, duration_ms, **extra)` — structured logging

## Adding a New Service

1. Create a file in `backend/services/`
2. Inherit from `BaseService`
3. Accept repository dependencies in `__init__`
4. Define a `Protocol` in `interfaces.py`
5. Export from `backend/services/__init__.py`
6. Write tests with mocked repositories

Example:

```python
from backend.services.base import BaseService

class MyService(BaseService):
    def __init__(self, repo: MyRepo) -> None:
        super().__init__()
        self._repo = repo

    async def do_work(self) -> int:
        result = await self._repo.count()
        self._log_operation("do_work", count=result)
        return result
```

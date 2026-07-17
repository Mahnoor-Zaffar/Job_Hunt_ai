# Job Hunting AI

AI-powered Job Intelligence & Application Automation Platform.

Automatically discovers jobs from multiple sources, normalizes them, matches them to your profile using AI, and can auto-fill application forms — all with human review before submission.

---

## Architecture

```text
┌─────────────────────────────────────────────────────────┐
│                    Next.js Dashboard                     │
│     Jobs · Companies · Applications · Resume · Settings  │
└──────────────────────┬──────────────────────────────────┘
                       │ REST API
┌──────────────────────▼──────────────────────────────────┐
│                   FastAPI Backend                        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────┐ │
│  │ Scrapers │ │ AI Engine│ │Automation│ │  Services   │ │
│  │ 4 sources│ │ OpenRouter│ │ Playwright│ │ Jobs/Co/App│ │
│  └──────────┘ └──────────┘ └──────────┘ └────────────┘ │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│              PostgreSQL · Redis · Celery                │
└─────────────────────────────────────────────────────────┘
```

## Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.13, FastAPI, SQLAlchemy 2.x, Pydantic v2 |
| **Frontend** | Next.js 15, React 19, TypeScript, Tailwind CSS |
| **Database** | PostgreSQL 16, Redis 7 |
| **AI** | OpenRouter (Claude 3.5, GPT-4o, Gemini, DeepSeek), sentence-transformers |
| **Scraping** | httpx, Playwright, Selectolax |
| **Queue** | Celery + Redis |
| **Infra** | Docker Compose, uv, Ruff, mypy |

## Features

### Job Discovery
- 4 live scrapers: **RemoteOK**, **Indeed**, **Mustakbil**, **BrightSpyre**
- Auto-scheduled via Celery Beat every 30 minutes
- Company records auto-created from scraped jobs
- 322+ jobs from 4 sources (demo instance)

### AI Career Assistant
Powered by OpenRouter with Claude 3.5 Sonnet:
- **Job summaries** — AI-generated bullet summaries
- **Cover letters** — Tailored to job + company + your profile
- **Interview prep** — Technical, behavioral, company questions with answers
- **Resume optimization** — Rewrite bullets, suggest keywords
- **Skill gap analysis** — Missing skills + learning roadmap
- **21 versioned prompts** in a centralized registry

### Intelligent Matching
- **9-factor deterministic scoring**: skills (30%), experience (15%), technologies (15%), location (10%), employment (8%), salary (8%), seniority (7%), remote (5%), company (2%)
- Semantic similarity via embeddings (sentence-transformers)

### Resume Manager
- Upload PDF/DOCX/TXT → auto-parsed into structured data
- Extract: skills, experience, education, certifications, projects
- Multiple resumes, version tracking

### Dashboard
- Real-time job stats with animated bar charts
- Source breakdown, top technologies, location distribution
- Scraper status panel with live refresh
- Dark mode toggle

### Applications
- Track applications through lifecycle: draft → submitted → interview → offer → rejected
- Follow-up reminders, timeline view
- AI-assisted form completion

### Browser Automation Platform
- Workflow engine with reusable steps (navigate, fill, upload, submit)
- 4 ATS adapters: Greenhouse, Lever, Ashby, Workable
- Intelligent form field mapping (80+ aliases, 18 categories)
- Session recording + audit trail

## Quick Start

```bash
# 1. Clone
git clone https://github.com/Mahnoor-Zaffar/Job_Hunt_ai.git
cd Job_Hunt_ai

# 2. One-command startup
bash scripts/dev.sh

# 3. Open
open http://localhost:3000
```

Then click **"Run All Scrapers"** on the dashboard to pull fresh jobs.

## API Endpoints (50+)

| Group | Key Endpoints |
|---|---|
| Jobs | `GET /jobs` (18 filters), `GET /jobs/{id}`, `GET /jobs/{id}/similar` |
| Companies | `GET /companies`, watchlist CRUD |
| Applications | Full lifecycle: create, status, notes, timeline, reminders |
| Resumes | Upload, parse, versions, set primary |
| Scrapers | List, run, status |
| Career AI | Summary, cover letter, interview prep, skill gap, salary guidance |
| Analytics | Dashboard stats, source breakdown, trends, top tech |
| AI Ops | Metrics, model inventory, prompt registry, evaluation suite |

Full docs at `http://localhost:8000/docs`

## Quality

- **251 tests**, all passing
- **ruff** lint + format clean
- **mypy** strict mode on 188 source files
- **CI/CD** via GitHub Actions (lint, type-check, unit tests, integration tests)

## Project Structure

```
backend/
├── ai/              AI platform (providers, prompts, matching, career assistant)
├── api/v1/          REST API (50+ endpoints, 10 resource groups)
├── automation/      Browser automation (workflows, ATS adapters, form engine)
├── config/          Settings, constants
├── database/        Engine, session, base
├── events/          Event bus (publish/subscribe)
├── models/          13 SQLAlchemy models
├── notifications/   Telegram + Email notifiers
├── repositories/    10 repositories
├── scrapers/        4 job scrapers + framework (orchestrator, parser, normalizer)
├── services/        8 business services
├── storage/         File storage (Local + S3)
├── utils/           Hashing, validation, metrics, logging
└── workers/         Celery app + tasks

frontend/
├── app/             Next.js pages (dashboard, jobs, companies, resume, settings)
└── components/      UI components (charts, cards, AI panel, theme toggle)

docs/                Architecture, AI readiness, automation platform docs
tests/               251 tests across all layers
```

## Environment

Copy `.env.example` to `.env` and set:

```env
OPENROUTER_API_KEY=sk-or-v1-...     # Required for AI features
TELEGRAM_BOT_TOKEN=...               # Optional: Telegram notifications
```

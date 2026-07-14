# System Architecture

# Job Hunting

**Version:** 1.0
**Status:** Planning
**Last Updated:** July 12, 2026

---

# 1. Purpose

This document defines the overall architecture of the Job Hunting platform, including its services, data flow, communication patterns, and design principles.

The system follows a **modular, service-oriented monolith** architecture. Although initially deployed as a single application, every major module is designed to be independently scalable and eventually extractable into its own service if needed.

---

# 2. High-Level Architecture

```text
                                        User
                                          │
                                          ▼
                                 Next.js Dashboard
                                          │
                                          ▼
                                   FastAPI Backend
                                          │
        ┌─────────────────────────────────┼─────────────────────────────────┐
        │                                 │                                 │
        ▼                                 ▼                                 ▼
 Authentication                   Job Service                     Resume Service
        │                                 │                                 │
        └─────────────────────────────────┼─────────────────────────────────┘
                                          │
                                          ▼
                                 PostgreSQL Database
                                          │
                                          ▼
                                   Redis Cache / Queue
                                          │
                                          ▼
                                 Celery Worker Pool
                                          │
               ┌──────────────────────────┼──────────────────────────┐
               │                          │                          │
               ▼                          ▼                          ▼
      Scraper Framework           AI Processing              Notification Service
               │                          │                          │
               ▼                          ▼                          ▼
      Multiple Job Sources        OpenRouter / Local AI      Telegram / Email
```

---

# 3. Design Principles

The system is designed around the following principles:

* Modular architecture
* Single Responsibility Principle
* Dependency Injection
* Clean Architecture
* API-first development
* Configuration over hardcoding
* Async-first backend
* Strong typing
* Testability
* Scalability

---

# 4. System Components

The platform is divided into several independent domains.

```
Frontend

↓

Backend API

↓

Business Services

↓

Infrastructure Services

↓

External Services
```

---

# 5. Frontend Layer

Technology

* Next.js
* React
* TypeScript
* Tailwind CSS

Responsibilities

* Dashboard
* Authentication
* Search
* Resume management
* Job management
* Application tracking
* Analytics

The frontend never communicates directly with external services.

All communication happens through the FastAPI backend.

---

# 6. API Layer

Technology

* FastAPI

Responsibilities

* Authentication
* Authorization
* Validation
* Routing
* Business orchestration
* REST API
* OpenAPI documentation

The API should contain minimal business logic.

Business logic belongs inside services.

---

# 7. Business Layer

The business layer contains all application logic.

Modules

```
Job Service

Resume Service

Company Service

Notification Service

Search Service

Application Service

AI Service

Settings Service
```

Each service should remain independent.

---

# 8. Infrastructure Layer

Infrastructure contains reusable utilities.

Examples

```
Database

Redis

Logging

Scheduler

Browser Manager

Storage

Configuration

Repositories
```

Business logic must never depend on infrastructure implementations.

---

# 9. Data Layer

Primary Database

PostgreSQL

Caching

Redis

Future

pgvector

Storage

Local filesystem initially

Object storage later

---

# 10. Scraper Framework

The scraper framework is completely independent of the API.

```
Scheduler

↓

Scraper Manager

↓

Base Scraper

↓

Individual Scrapers

↓

Parser

↓

Normalizer

↓

Validator

↓

Deduplicator

↓

Repository

↓

Database
```

Each scraper only extracts data.

It never performs business logic.

---

# 11. Scraper Architecture

```
BaseScraper

├── Rozee

├── Mustakbil

├── BrightSpyre

├── RemoteOK

├── Greenhouse

├── Lever

├── Ashby

└── Workable
```

Every scraper implements the same interface.

```python
class BaseScraper:

    async def scrape()

    async def parse()

    async def normalize()
```

---

# 12. Browser Manager

Instead of launching multiple browsers:

```
Scraper

↓

Browser Manager

↓

Shared Browser

↓

Shared Context

↓

Shared Pages
```

Advantages

* Less memory
* Faster execution
* Better session management

---

# 13. Scheduler

The scheduler is responsible for triggering scraping jobs.

```
Every 30 minutes

↓

Scheduler

↓

Queue

↓

Worker

↓

Scraper

↓

Database
```

Future improvements

* Dynamic scheduling
* Priority queues
* Job retries

---

# 14. Data Processing Pipeline

Every discovered job passes through the same pipeline.

```
Raw HTML

↓

Parser

↓

Job Object

↓

Normalizer

↓

Validator

↓

Duplicate Detector

↓

Repository

↓

Database
```

No scraper writes directly into PostgreSQL.

---

# 15. Job Lifecycle

```
Discover Job

↓

Normalize

↓

Validate

↓

Deduplicate

↓

Save

↓

AI Match

↓

Notify

↓

Display
```

---

# 16. AI Pipeline

```
Resume

↓

Resume Parser

↓

Embedding

↓

Job Description

↓

Embedding

↓

Similarity

↓

Ranking

↓

OpenRouter

↓

Recommendations
```

OpenRouter is only used for reasoning tasks.

Embeddings should be computed locally whenever possible.

---

# 17. Auto Apply Pipeline

```
Job Selected

↓

Browser Automation

↓

Open Apply URL

↓

Extract Form

↓

Map Fields

↓

Resume Selection

↓

Upload Resume

↓

Generate Answers

↓

Preview

↓

Submit

↓

Track Application
```

The default behavior should require human confirmation before submission.

---

# 18. Notification Pipeline

```
New Job

↓

Job Saved

↓

Preference Match

↓

Notification Queue

↓

Telegram

↓

Email
```

Notifications are asynchronous.

---

# 19. Search Pipeline

```
Search Request

↓

Filters

↓

Repository

↓

PostgreSQL

↓

Results

↓

Pagination

↓

Response
```

Future versions will support semantic search using pgvector.

---

# 20. Repository Pattern

The application should never access SQLAlchemy models directly from services.

```
Service

↓

Repository

↓

SQLAlchemy

↓

Database
```

Benefits

* Easier testing
* Better abstraction
* Cleaner services

---

# 21. Dependency Injection

Every service receives dependencies through constructors or FastAPI dependency injection.

Example

```
JobService

↓

JobRepository

↓

Database Session
```

Avoid global objects.

---

# 22. Configuration

All configuration must come from environment variables.

Examples

```
Database URL

Redis URL

OpenRouter API Key

Telegram Token

Scheduler Interval

Playwright Settings
```

Nothing should be hardcoded.

---

# 23. Logging

Every service produces structured logs.

Example

```
Timestamp

Service

Operation

Duration

Result

Error
```

Future

* JSON logging
* Centralized log aggregation

---

# 24. Error Handling

Every module should fail independently.

Example

```
Rozee

✓ Success

RemoteOK

✗ Failed

Greenhouse

✓ Success
```

A single scraper failure must never stop the pipeline.

---

# 25. Security Architecture

Secrets

* Environment variables

Authentication

* JWT (future)

Authorization

* RBAC (future)

Passwords

* Argon2

Transport

* HTTPS in production

Uploads

* File validation
* MIME type checking

---

# 26. Scalability

Current Deployment

```
FastAPI

↓

PostgreSQL

↓

Redis

↓

Celery
```

Future

```
Load Balancer

↓

API Instances

↓

Worker Pool

↓

Redis Cluster

↓

PostgreSQL

↓

Vector Database
```

No architectural changes should be required to scale horizontally.

---

# 27. Folder Structure

```
job_hunting/

backend/
│
├── api/
├── core/
├── services/
├── repositories/
├── models/
├── schemas/
├── database/
├── workers/
├── scrapers/
├── ai/
├── notifications/
├── scheduler/
├── utils/
└── config/

frontend/

docs/

tests/

docker/

scripts/
```

---

# 28. External Services

Current

* OpenRouter
* Telegram Bot API

Future

* Email Provider
* Object Storage
* Analytics
* Monitoring

All external services should be accessed through dedicated adapter classes.

---

# 29. Future Evolution

The architecture intentionally supports migration from a modular monolith to microservices.

Potential service extraction:

* Scraper Service
* AI Service
* Notification Service
* Browser Automation Service
* Search Service

Since communication boundaries are already defined, these components can be extracted without major refactoring.

---

# 30. Architectural Principles

The architecture should always prioritize:

* Simplicity over unnecessary complexity.
* Clear separation of concerns.
* Loose coupling between modules.
* High cohesion within modules.
* Dependency inversion.
* Independent testability.
* Scalability without redesign.
* Deterministic workflows before AI-driven workflows.
* AI as an enhancement, not a core dependency.
* Human oversight for high-impact actions such as application submission.

These principles should guide every architectural decision throughout the project's lifecycle.

# PROJECT_CONTEXT.md

# Job Hunting — Project Context & Engineering Specification

## Purpose

You are assisting in the development of **Job Hunting**, an AI-powered Job Intelligence and Application Automation Platform.

This is **NOT** a simple job scraper.

It is a production-grade software platform that automates the entire job hunting lifecycle, including:

* Job discovery
* Data aggregation
* Data normalization
* Duplicate detection
* AI-powered job matching
* Resume management
* Resume optimization
* Cover letter generation
* Browser-based application automation
* Application tracking
* Career analytics

The project is initially built for a single user but must be architected to support a future SaaS platform without requiring significant redesign.

---

# Project Philosophy

The goal is to build software like a senior backend engineering team would.

Every implementation should prioritize:

* Maintainability
* Scalability
* Modularity
* Testability
* Performance
* Readability

Avoid shortcuts that make future maintenance difficult.

---

# Technology Stack

## Backend

Python 3.13+

FastAPI

SQLAlchemy 2.x

Alembic

Pydantic v2

---

## Database

PostgreSQL

Redis

pgvector (future)

---

## Scraping

Playwright

httpx

Selectolax

BeautifulSoup

---

## AI

OpenRouter

Sentence Transformers

Local embedding models

PyMuPDF

---

## Frontend

Next.js

React

TypeScript

TailwindCSS

shadcn/ui

---

## Background Processing

Celery

Celery Beat

Redis

---

## DevOps

Docker

Docker Compose

GitHub Actions

uv

Ruff

pytest

mypy

pre-commit

---

# High-Level Architecture

```text
User
        │
        ▼
Next.js Dashboard
        │
        ▼
FastAPI API
        │
 ┌──────┴───────────────────────┐
 │                              │
 ▼                              ▼
Business Services         Background Workers
 │                              │
 ▼                              ▼
Repositories         Scraper Framework
 │                              │
 ▼                              ▼
PostgreSQL              Multiple Job Sources
```

The architecture follows a **modular monolith**.

Every module should be independently testable.

Future microservice extraction should be possible.

---

# Core Modules

The system consists of the following modules.

## Authentication

Future feature.

JWT based.

---

## Job Discovery

Responsible for collecting jobs.

Supported sources include:

Pakistan

* Rozee
* Mustakbil
* BrightSpyre
* Company Career Pages

Remote

* RemoteOK
* Greenhouse
* Lever
* Ashby
* Workable

Responsibilities

* Scraping
* Parsing
* Normalization
* Validation

Never contains business logic.

---

## Scraper Framework

Every scraper must inherit a common BaseScraper.

Responsibilities

* Browser management
* HTTP requests
* Parsing
* Retry handling
* Rate limiting
* Logging

Every scraper returns a standardized Job object.

No scraper writes directly to the database.

---

## Job Processing Pipeline

Every job follows the same pipeline.

```text
Scraper

↓

Parser

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

---

## Search Engine

Supports

* Keywords
* Company
* Location
* Salary
* Experience
* Employment Type

Future

Semantic search using pgvector.

---

## Resume Manager

Responsible for

* Resume uploads
* Resume parsing
* Resume versions
* Resume metadata

Supports multiple resumes.

---

## AI Engine

Uses OpenRouter only when reasoning is required.

Local embedding models should be preferred.

Capabilities

* Resume parsing
* Job matching
* Cover letters
* Resume optimization
* Interview preparation
* Skill gap analysis

AI should enhance deterministic logic rather than replace it.

---

## Notification Service

Supports

Telegram

Email

Future

Discord

Slack

Must be asynchronous.

---

## Browser Automation

Responsible for

* Opening applications
* Detecting forms
* Filling forms
* Uploading resumes
* Uploading cover letters
* Answering questions
* Human review
* Submission

Each ATS platform should have its own implementation.

---

## Dashboard

Displays

* Jobs
* Applications
* Companies
* Analytics
* Search
* Resume Manager

---

# Engineering Principles

Always follow these principles.

## Clean Architecture

Separate

* API
* Services
* Repositories
* Infrastructure
* Domain Models

Business logic must never exist inside routes.

---

## SOLID

Every class should have a single responsibility.

---

## DRY

Avoid duplicate implementations.

Extract reusable logic.

---

## Composition over inheritance

Only inherit when appropriate.

Prefer reusable services.

---

## Strong Typing

Everything should use

Python type hints

Pydantic models

SQLAlchemy typing

Avoid Any whenever possible.

---

## Dependency Injection

Never create dependencies manually inside business logic.

Inject dependencies.

---

## Repository Pattern

Services should never directly use SQLAlchemy.

Correct flow

```text
Service

↓

Repository

↓

Database
```

---

## Configuration

Never hardcode

* API keys
* URLs
* Locations
* Keywords
* Retry limits

Everything should be configurable.

---

## Async First

Prefer asynchronous implementations whenever supported.

Avoid blocking operations.

---

## Logging

Every major operation should log

* Duration
* Status
* Errors
* Source
* Metadata

---

## Error Handling

One failing scraper must never stop the others.

Errors should be isolated.

---

## Testing

Every business service should be unit testable.

Avoid tightly coupling logic to infrastructure.

---

# Coding Standards

Use

* Ruff
* Black-compatible formatting
* mypy
* Docstrings for public APIs
* Meaningful variable names
* Small focused functions

Avoid

God classes.

Massive functions.

Nested logic.

Magic numbers.

Hardcoded values.

---

# Folder Structure

```text
job_hunting/

backend/

    api/

    core/

    config/

    database/

    models/

    repositories/

    services/

    workers/

    scheduler/

    scrapers/

        base/

        pakistan/

        remote/

        ats/

    ai/

    notifications/

    utils/

frontend/

docs/

docker/

scripts/

tests/
```

---

# Development Guidelines

When implementing any feature

Always

1. Understand the requirement.

2. Design before coding.

3. Keep modules isolated.

4. Write reusable code.

5. Follow existing architecture.

6. Avoid unnecessary dependencies.

7. Keep business logic independent.

8. Consider future scalability.

9. Document public interfaces.

10. Write maintainable code.

---

# AI Assistant Expectations

When assisting with implementation:

* Respect the existing architecture.
* Never bypass the repository layer.
* Never place business logic inside API routes.
* Prefer reusable services over duplicated code.
* Follow dependency injection patterns.
* Write production-quality code.
* Suggest improvements when architecture can be strengthened.
* Point out potential performance, security, or maintainability issues before implementing.
* Preserve consistency across the codebase.

When uncertain, prioritize long-term maintainability over the quickest implementation.

---

# End Goal

The finished product should resemble a production-ready career platform rather than a collection of scripts.

Every feature should fit naturally into the overall architecture.

The codebase should be clean enough that an experienced engineer could understand and extend it without significant refactoring.

The project should demonstrate advanced backend engineering, software architecture, automation, AI integration, and systems design suitable for a senior-level portfolio.

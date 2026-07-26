import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from backend.api.router import api_router
from backend.config.settings import get_settings
from backend.core.middleware import ErrorHandlingMiddleware, RequestLoggingMiddleware
from backend.core.rate_limit import RateLimitMiddleware
from backend.core.request_id import RequestIDMiddleware
from backend.core.security import SecurityHeadersMiddleware
from backend.database.engine import dispose_engine
from backend.database.session import get_session_factory
from backend.events import NEW_JOB_DISCOVERED, subscribe
from backend.services.digest import run_daily_digest
from backend.services.email_verification_service import EmailVerificationService
from backend.services.job_alert_service import JobAlertService
from backend.utils.logging import setup_logging
from backend.utils.metrics import get_metrics

_background_tasks: list[asyncio.Task] = []


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    setup_logging(settings.LOG_LEVEL)

    session_factory = get_session_factory()

    # Start email verification background loop
    email_verify_service = EmailVerificationService(session_factory)
    _background_tasks.append(
        asyncio.create_task(
            email_verify_service.run_loop(interval=1800),
            name="email-verify-loop",
        )
    )

    # Wire job alert service to NEW_JOB_DISCOVERED
    job_alert_service = JobAlertService(session_factory)
    subscribe(NEW_JOB_DISCOVERED, job_alert_service.handle_new_job)

    # Start daily digest background loop
    _background_tasks.append(
        asyncio.create_task(
            run_daily_digest(session_factory),
            name="daily-digest",
        )
    )

    yield

    # Cancel background tasks on shutdown
    for task in _background_tasks:
        task.cancel()
    await asyncio.gather(*_background_tasks, return_exceptions=True)
    _background_tasks.clear()

    await dispose_engine()


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.APP_NAME,
        version="0.1.0",
        description="AI-powered Job Intelligence & Application Automation Platform",
        lifespan=lifespan,
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
    )

    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )
    app.add_middleware(RateLimitMiddleware, max_requests=10000, window=60)
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(ErrorHandlingMiddleware)
    app.add_middleware(RequestLoggingMiddleware)

    app.include_router(api_router, prefix="/api")

    @app.get("/metrics", include_in_schema=False)
    async def metrics_endpoint() -> Response:
        return Response(content=get_metrics(), media_type="text/plain")

    return app


app = create_app()

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
from backend.utils.logging import setup_logging
from backend.utils.metrics import get_metrics


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    setup_logging(settings.LOG_LEVEL)
    yield
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
    app.add_middleware(RateLimitMiddleware, max_requests=120, window=60)
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(ErrorHandlingMiddleware)
    app.add_middleware(RequestLoggingMiddleware)

    app.include_router(api_router, prefix="/api")

    @app.get("/metrics", include_in_schema=False)
    async def metrics_endpoint() -> Response:
        return Response(content=get_metrics(), media_type="text/plain")

    return app


app = create_app()

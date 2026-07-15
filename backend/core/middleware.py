import logging
import time
from typing import Any

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse

from backend.core.exceptions import AppException
from backend.services.base import (
    DuplicateError,
    NotFoundError,
    ServiceError,
    ValidationError,
)

logger = logging.getLogger("job_hunting.middleware")

_SERVICE_ERROR_MAP: dict[type[ServiceError], int] = {
    NotFoundError: 404,
    DuplicateError: 409,
    ValidationError: 422,
}


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        try:
            return await call_next(request)
        except AppException as exc:
            return JSONResponse(
                status_code=exc.status_code,
                content={"detail": exc.message, "success": False},
            )
        except ServiceError as exc:
            status = _SERVICE_ERROR_MAP.get(type(exc), 500)
            content: dict[str, Any] = {
                "detail": str(exc),
                "success": False,
            }
            if isinstance(exc, NotFoundError):
                content["entity"] = exc.entity
                content["entity_id"] = exc.entity_id
            elif isinstance(exc, DuplicateError):
                content["entity"] = exc.entity
            return JSONResponse(status_code=status, content=content)
        except Exception:
            logger.exception("Unhandled error on %s %s", request.method, request.url.path)
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error", "success": False},
            )


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000

        logger.info(
            "%s %s -> %d (%.1fms)",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response

"""Rate limiting middleware — in-memory sliding window.

Protects the API from abuse by limiting requests per client IP
within a configurable window.  Uses an in-memory store (suitable for
single-process deployments); a Redis-backed store can replace it later.
"""

import time
from collections import defaultdict
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

_WINDOW_SECONDS = 60
_MAX_REQUESTS = 120
_store: dict[str, list[float]] = defaultdict(list)


def _clean_window(ip: str) -> None:
    now = time.time()
    cutoff = now - _WINDOW_SECONDS
    _store[ip] = [ts for ts in _store[ip] if ts > cutoff]


class RateLimitMiddleware(BaseHTTPMiddleware):
    """In-memory rate limiter — 120 req/min per IP by default."""

    def __init__(
        self, app: Any, *, max_requests: int = _MAX_REQUESTS, window: int = _WINDOW_SECONDS
    ) -> None:
        super().__init__(app)
        self._max = max_requests
        self._window = window

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        ip = request.client.host if request.client else "unknown"
        _clean_window(ip)
        if len(_store[ip]) >= self._max:
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Too many requests. Please try again later.",
                    "retry_after_seconds": self._window,
                },
            )
        _store[ip].append(time.time())
        return await call_next(request)

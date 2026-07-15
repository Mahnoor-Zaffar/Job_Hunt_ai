"""Request ID middleware — injects a unique ID into every request.

Adds a ``X-Request-ID`` header to every response (echoes the
client-supplied value or generates a UUID) and makes it available
via context variables for correlation across logs, metrics, and traces.
"""

import uuid
from contextvars import ContextVar

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

REQUEST_ID_CTX: ContextVar[str] = ContextVar("request_id", default="-")

HEADER_REQUEST_ID = "X-Request-ID"


def get_request_id() -> str:
    return REQUEST_ID_CTX.get()


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        req_id = request.headers.get(HEADER_REQUEST_ID) or str(uuid.uuid4())[:8]
        REQUEST_ID_CTX.set(req_id)
        response = await call_next(request)
        response.headers[HEADER_REQUEST_ID] = req_id
        return response

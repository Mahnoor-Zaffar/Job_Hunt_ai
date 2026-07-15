import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from backend.core.exceptions import AppException, NotFoundException
from backend.core.middleware import ErrorHandlingMiddleware, RequestLoggingMiddleware


@pytest.fixture
def app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(ErrorHandlingMiddleware)
    app.add_middleware(RequestLoggingMiddleware)

    @app.get("/ok")
    async def ok_endpoint() -> dict:
        return {"status": "ok"}

    @app.get("/app-exception")
    async def app_exception_endpoint() -> dict:
        raise AppException("test app error", status_code=400)

    @app.get("/not-found")
    async def not_found_endpoint() -> dict:
        raise NotFoundException(resource="Item", identifier="42")

    return app


@pytest.fixture
async def client(app: FastAPI) -> AsyncClient:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestErrorHandlingMiddleware:
    @pytest.mark.asyncio
    async def test_normal_response_passes_through(self, client: AsyncClient) -> None:
        resp = await client.get("/ok")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"

    @pytest.mark.asyncio
    async def test_app_exception_returns_correct_status(self, client: AsyncClient) -> None:
        resp = await client.get("/app-exception")
        assert resp.status_code == 400
        data = resp.json()
        assert data["detail"] == "test app error"
        assert data["success"] is False

    @pytest.mark.asyncio
    async def test_not_found_returns_404(self, client: AsyncClient) -> None:
        resp = await client.get("/not-found")
        assert resp.status_code == 404
        data = resp.json()
        assert "Item" in data["detail"]


class TestRequestLoggingMiddleware:
    @pytest.mark.asyncio
    async def test_request_logged_successfully(self, client: AsyncClient) -> None:
        resp = await client.get("/ok")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_error_request_still_logged(self, client: AsyncClient) -> None:
        resp = await client.get("/app-exception")
        assert resp.status_code == 400

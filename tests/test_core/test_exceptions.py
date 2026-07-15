from backend.core.exceptions import (
    AppException,
    ConflictException,
    ExternalServiceException,
    NotFoundException,
    ScraperException,
    ValidationException,
)


class TestAppException:
    def test_base_exception_fields(self) -> None:
        exc = AppException("generic error")
        assert exc.message == "generic error"
        assert exc.status_code == 500
        assert str(exc) == "generic error"

    def test_custom_status_code(self) -> None:
        exc = AppException("bad request", status_code=400)
        assert exc.status_code == 400

    def test_not_found_exception(self) -> None:
        exc = NotFoundException(resource="User", identifier="abc-123")
        assert exc.status_code == 404
        assert "User" in exc.message
        assert "abc-123" in exc.message

    def test_validation_exception(self) -> None:
        exc = ValidationException("Invalid email format")
        assert exc.status_code == 422
        assert "email" in exc.message

    def test_conflict_exception(self) -> None:
        exc = ConflictException("Email already exists")
        assert exc.status_code == 409

    def test_scraper_exception(self) -> None:
        exc = ScraperException(source="rozee", message="Connection refused")
        assert exc.status_code == 500
        assert "rozee" in exc.message
        assert exc.source == "rozee"

    def test_external_service_exception(self) -> None:
        exc = ExternalServiceException(service="OpenRouter", message="Rate limited")
        assert exc.status_code == 502
        assert "OpenRouter" in exc.message
        assert exc.service == "OpenRouter"

    def test_all_exceptions_are_app_exceptions(self) -> None:
        exc1 = NotFoundException(resource="Item", identifier="42")
        assert isinstance(exc1, AppException)

        exc2 = ValidationException("invalid")
        assert isinstance(exc2, AppException)

        exc3 = ConflictException("duplicate")
        assert isinstance(exc3, AppException)

        exc4 = ScraperException(source="x", message="err")
        assert isinstance(exc4, AppException)

        exc5 = ExternalServiceException(service="svc", message="err")
        assert isinstance(exc5, AppException)

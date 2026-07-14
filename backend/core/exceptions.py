class AppException(Exception):  # noqa: N818
    def __init__(self, message: str, status_code: int = 500) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class NotFoundException(AppException):
    def __init__(self, resource: str, identifier: str) -> None:
        super().__init__(
            message=f"{resource} with id '{identifier}' not found",
            status_code=404,
        )


class ValidationException(AppException):
    def __init__(self, message: str) -> None:
        super().__init__(message=message, status_code=422)


class ConflictException(AppException):
    def __init__(self, message: str) -> None:
        super().__init__(message=message, status_code=409)


class ScraperException(AppException):
    def __init__(self, source: str, message: str) -> None:
        super().__init__(
            message=f"Scraper [{source}]: {message}",
            status_code=500,
        )
        self.source = source


class ExternalServiceException(AppException):
    def __init__(self, service: str, message: str) -> None:
        super().__init__(
            message=f"External service [{service}]: {message}",
            status_code=502,
        )
        self.service = service

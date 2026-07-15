"""Base class for all business services.

Provides structured logging, domain exception helpers, and common
patterns shared across the entire service layer.
"""

import logging
import uuid
from typing import Any


class ServiceError(Exception):
    """Base exception for service-layer errors."""

    def __init__(self, message: str, *, entity: str = "", entity_id: str = "") -> None:
        self.entity = entity
        self.entity_id = entity_id
        super().__init__(message)


class NotFoundError(ServiceError):
    """Raised when a requested entity does not exist."""

    def __init__(self, entity: str, entity_id: str) -> None:
        super().__init__(
            f"{entity} with id '{entity_id}' not found",
            entity=entity,
            entity_id=entity_id,
        )


class DuplicateError(ServiceError):
    """Raised when creating an entity that already exists."""

    def __init__(self, entity: str, field: str, value: str) -> None:
        super().__init__(
            f"{entity} with {field} '{value}' already exists",
            entity=entity,
        )


class ValidationError(ServiceError):
    """Raised when business-rule validation fails."""

    pass


class BaseService:
    """Shared base for all business services.

    Subclasses receive a logger automatically and gain access to
    common error-raising helpers.
    """

    def __init__(self) -> None:
        module = self.__class__.__module__.rsplit(".", 1)[-1]
        self._log = logging.getLogger(f"job_hunting.services.{module}")

    def _raise_not_found(self, entity: str, entity_id: uuid.UUID | str) -> None:
        raise NotFoundError(entity=entity, entity_id=str(entity_id))

    def _raise_duplicate(self, entity: str, field: str, value: str) -> None:
        raise DuplicateError(entity=entity, field=field, value=value)

    def _raise_validation(self, message: str) -> None:
        raise ValidationError(message)

    def _log_operation(
        self, operation: str, duration_ms: float | None = None, **extra: Any
    ) -> None:
        parts = [f"op={operation}"]
        if duration_ms is not None:
            parts.append(f"duration={duration_ms:.1f}ms")
        for k, v in extra.items():
            parts.append(f"{k}={v}")
        self._log.info(" | ".join(parts))

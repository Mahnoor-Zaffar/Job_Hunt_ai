import uuid
from contextlib import suppress
from datetime import datetime

from sqlalchemy import func, inspect
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.base import Base


class BaseModel(Base):
    """Abstract declarative base shared by all domain models.

    Provides a UUID primary key and creation/update timestamps so every
    concrete model inherits a consistent, strongly-typed identity contract.

    Column-level defaults (``mapped_column(..., default=...)``) are
    applied at the Python constructor level so that model instances
    created without a session still carry expected default values.  This
    is critical for testing and serialisation outside of an ORM context.
    """

    __abstract__ = True

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
    )

    def __init__(self, **kwargs: object) -> None:
        mapper = inspect(type(self))
        if mapper is not None:
            for c in mapper.columns:
                if c.name not in kwargs and c.default is not None:
                    default_arg = getattr(c.default, "arg", None)
                    if default_arg is not None:
                        if c.default.is_scalar:
                            kwargs[c.name] = default_arg
                        elif c.default.is_callable:
                            with suppress(TypeError, ValueError):
                                kwargs[c.name] = default_arg()
                            if c.name not in kwargs:
                                with suppress(TypeError, ValueError):
                                    kwargs[c.name] = default_arg(None)
        super().__init__(**kwargs)

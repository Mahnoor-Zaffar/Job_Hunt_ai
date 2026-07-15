import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import BaseModel


class Settings(BaseModel):
    """Key-value settings store, scoped per-user.

    Allows persisting user preferences without adding columns to the
    User model.  Keys are namespaced by convention (e.g.,
    ``notifications.telegram``, ``search.default_location``).
    """

    __tablename__ = "settings"

    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), index=True)
    key: Mapped[str] = mapped_column(String(100), index=True)
    value: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(String(500))
    is_encrypted: Mapped[bool] = mapped_column(default=False)

import uuid

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import BaseModel


class CompanyWatchlist(BaseModel):
    __tablename__ = "company_watchlists"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    company_name: Mapped[str] = mapped_column(index=True)
    notes: Mapped[str | None] = mapped_column()
    notify_on_new_jobs: Mapped[bool] = mapped_column(default=True)
    is_active: Mapped[bool] = mapped_column(default=True)

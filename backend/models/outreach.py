import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import BaseModel


class Outreach(BaseModel):
    __tablename__ = "outreach"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    application_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("applications.id"), nullable=True)
    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("jobs.id"))
    recipient_email: Mapped[str] = mapped_column(String(255))
    recipient_name: Mapped[str | None] = mapped_column(String(255))
    subject: Mapped[str] = mapped_column(String(500))
    body: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    sent_at: Mapped[datetime | None] = mapped_column(DateTime)

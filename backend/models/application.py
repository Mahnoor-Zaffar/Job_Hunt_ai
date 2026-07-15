import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import BaseModel


class Application(BaseModel):
    __tablename__ = "applications"

    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), index=True)
    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("jobs.id"), index=True)
    resume_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("resumes.id"))
    status: Mapped[str] = mapped_column(String(30), default="draft", index=True)
    applied_at: Mapped[datetime | None] = mapped_column(DateTime)
    cover_letter: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    match_score: Mapped[float | None] = mapped_column()
    interview_date: Mapped[datetime | None] = mapped_column(DateTime)
    feedback: Mapped[str | None] = mapped_column(Text)
    is_submitted: Mapped[bool] = mapped_column(default=False)

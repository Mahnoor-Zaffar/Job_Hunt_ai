from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import BaseModel


class ScrapeLog(BaseModel):
    """Audit log recording every scraper execution.

    Each row represents a single run of a specific scraper source —
    whether successful or not.  Useful for monitoring, debugging,
    and tracking scraper health over time.
    """

    __tablename__ = "scrape_logs"

    source: Mapped[str] = mapped_column(String(50), index=True)
    status: Mapped[str] = mapped_column(String(20), default="running")
    jobs_discovered: Mapped[int] = mapped_column(Integer, default=0)
    jobs_new: Mapped[int] = mapped_column(Integer, default=0)
    jobs_duplicate: Mapped[int] = mapped_column(Integer, default=0)
    jobs_skipped: Mapped[int] = mapped_column(Integer, default=0)
    duration_seconds: Mapped[float] = mapped_column(Float, default=0.0)
    error_message: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(DateTime)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime)
    metadata_json: Mapped[str | None] = mapped_column(Text)

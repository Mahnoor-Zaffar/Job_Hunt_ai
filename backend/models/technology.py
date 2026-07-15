from sqlalchemy import Column, ForeignKey, String, Table
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import BaseModel

job_technology = Table(
    "job_technologies",
    BaseModel.metadata,
    Column("job_id", ForeignKey("jobs.id", ondelete="CASCADE"), primary_key=True),
    Column("technology_id", ForeignKey("technologies.id", ondelete="CASCADE"), primary_key=True),
)


class Technology(BaseModel):
    __tablename__ = "technologies"

    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    category: Mapped[str | None] = mapped_column(String(50))
    version: Mapped[str | None] = mapped_column(String(50))
    description: Mapped[str | None] = mapped_column(String(500))
    is_active: Mapped[bool] = mapped_column(default=True)

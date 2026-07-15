from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import BaseModel


class Company(BaseModel):
    """Separate entity for companies, distinct from denormalised job company strings.

    Created from unique company names discovered during scraping.  A
    background service can enrich companies with metadata later.
    """

    __tablename__ = "companies"

    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    website: Mapped[str | None] = mapped_column(String(500))
    logo_url: Mapped[str | None] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text)
    industry: Mapped[str | None] = mapped_column(String(100))
    size: Mapped[str | None] = mapped_column(String(50))
    headquarters: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(default=True)

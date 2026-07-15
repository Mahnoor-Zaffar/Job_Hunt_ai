from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import BaseModel


class Location(BaseModel):
    """Normalised location data extracted from job listings.

    Acts as a reference table so that every job can reference a
    canonical city / country pair without string duplication.
    """

    __tablename__ = "locations"

    city: Mapped[str] = mapped_column(String(100), index=True)
    country: Mapped[str] = mapped_column(String(100), index=True)
    region: Mapped[str | None] = mapped_column(String(100))
    country_code: Mapped[str | None] = mapped_column(String(5))
    latitude: Mapped[float | None] = mapped_column()
    longitude: Mapped[float | None] = mapped_column()
    is_supported: Mapped[bool] = mapped_column(Boolean, default=False)
    is_remote: Mapped[bool] = mapped_column(Boolean, default=False)

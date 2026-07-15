from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import BaseModel


class ATSPlatform(BaseModel):
    """Metadata about supported ATS platforms.

    Each platform has a name (greenhouse, lever, etc.), a base URL
    pattern, and references the adapter class that handles it.
    """

    __tablename__ = "ats_platforms"

    name: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(100))
    base_url_pattern: Mapped[str | None] = mapped_column(String(500))
    api_base_url: Mapped[str | None] = mapped_column(String(500))
    adapter_module: Mapped[str] = mapped_column(String(255))
    adapter_class: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    requires_api_key: Mapped[bool] = mapped_column(Boolean, default=False)
    supports_json_api: Mapped[bool] = mapped_column(Boolean, default=True)

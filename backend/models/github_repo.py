import uuid

from sqlalchemy import ARRAY, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import BaseModel


class GitHubRepo(BaseModel):
    __tablename__ = "github_repos"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    repo_name: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    language: Mapped[str | None] = mapped_column(String(100), nullable=True)
    topics: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    readme_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    stars: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    forks: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")

import uuid

from sqlalchemy import JSON, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import BaseModel


class Resume(BaseModel):
    __tablename__ = "resumes"

    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    file_path: Mapped[str] = mapped_column(String(500))
    file_type: Mapped[str] = mapped_column(String(20))
    parsed_text: Mapped[str | None] = mapped_column(Text)
    extracted_skills: Mapped[list[str] | None] = mapped_column(JSON)
    total_experience_years: Mapped[int | None] = mapped_column(Integer)
    is_primary: Mapped[bool] = mapped_column(default=False)

    versions: Mapped[list["ResumeVersion"]] = relationship(
        "ResumeVersion", back_populates="resume", cascade="all, delete-orphan"
    )


class ResumeVersion(BaseModel):
    __tablename__ = "resume_versions"

    resume_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("resumes.id"), index=True)
    version_number: Mapped[int] = mapped_column(Integer)
    file_path: Mapped[str] = mapped_column(String(500))
    change_summary: Mapped[str | None] = mapped_column(Text)

    resume: Mapped["Resume"] = relationship("Resume", back_populates="versions")

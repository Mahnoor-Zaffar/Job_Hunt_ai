import uuid

from sqlalchemy import ARRAY, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import BaseModel


class CareerProfile(BaseModel):
    __tablename__ = "career_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), unique=True, index=True)
    skills: Mapped[list[str] | None] = mapped_column(ARRAY(String), default=list)
    experience_level: Mapped[str] = mapped_column(String(20), default="mid")
    years_experience: Mapped[int] = mapped_column(default=0)
    target_roles: Mapped[list[str] | None] = mapped_column(ARRAY(String), default=list)
    preferred_locations: Mapped[list[str] | None] = mapped_column(ARRAY(String), default=list)
    remote_preference: Mapped[str] = mapped_column(String(20), default="no_preference")
    preferred_salary_min: Mapped[float | None] = mapped_column(Float)
    preferred_companies: Mapped[list[str] | None] = mapped_column(ARRAY(String), default=list)
    tech_stack: Mapped[list[str] | None] = mapped_column(ARRAY(String), default=list)
    learning_goals: Mapped[list[str] | None] = mapped_column(ARRAY(String), default=list)
    resume_text: Mapped[str | None] = mapped_column(Text)

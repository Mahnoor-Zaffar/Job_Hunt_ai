from pydantic import EmailStr

from backend.schemas.base import BaseSchema, TimestampSchema


class UserCreate(BaseSchema):
    email: EmailStr
    name: str
    password: str


class UserUpdate(BaseSchema):
    email: EmailStr | None = None
    name: str | None = None


class UserResponse(TimestampSchema):
    email: str
    name: str
    is_active: bool

"""Auth API — register, login, get current user."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.auth import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from backend.database.session import get_db
from backend.models.user import User
from backend.repositories.user import UserRepository
from backend.schemas.base import BaseSchema

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer(auto_error=False)


class RegisterRequest(BaseSchema):
    email: str
    name: str
    password: str


class LoginRequest(BaseSchema):
    email: str
    password: str


class TokenResponse(BaseSchema):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    name: str
    email: str


class UserResponse(BaseSchema):
    id: str
    email: str
    name: str
    is_active: bool


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user_id = decode_access_token(credentials.credentials)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user


@router.post("/register", response_model=TokenResponse)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    repo = UserRepository(db)
    existing = await repo.get_by_email(body.email)
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(
        email=body.email,
        name=body.name,
        hashed_password=hash_password(body.password),
        is_active=True,
    )
    created = await repo.create(user)
    await db.flush()
    await db.commit()

    token = create_access_token(created.id)
    return TokenResponse(
        access_token=token,
        user_id=str(created.id),
        name=created.name,
        email=created.email,
    )


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    repo = UserRepository(db)
    user = await repo.get_by_email(body.email)
    if user is None or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token(user.id)
    return TokenResponse(access_token=token, user_id=str(user.id), name=user.name, email=user.email)


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        name=current_user.name,
        is_active=current_user.is_active,
    )

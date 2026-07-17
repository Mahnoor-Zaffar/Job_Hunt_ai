"""Auth utilities — JWT tokens + password hashing."""

import uuid
from datetime import UTC, datetime, timedelta

import bcrypt
from jose import jwt

from backend.config.settings import get_settings

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(user_id: uuid.UUID) -> str:
    settings = get_settings()
    expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": str(user_id), "exp": expire}
    return str(
        jwt.encode(
            to_encode,
            settings.OPENROUTER_API_KEY or "dev-secret-key",
            algorithm=ALGORITHM,
        )
    )


def decode_access_token(token: str) -> uuid.UUID | None:
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.OPENROUTER_API_KEY or "dev-secret-key",
            algorithms=[ALGORITHM],
        )
        sub = payload.get("sub")
        if sub:
            return uuid.UUID(sub)
        return None
    except Exception:
        return None

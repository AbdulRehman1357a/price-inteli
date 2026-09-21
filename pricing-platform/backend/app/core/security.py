import uuid
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any

import bcrypt
from jose import JWTError, jwt

from app.core.config import get_settings

_BCRYPT_MAX_BYTES = 72  # bcrypt's own hard limit; longer inputs are truncated, not rejected


def _bcrypt_bytes(plain_password: str) -> bytes:
    return plain_password.encode("utf-8")[:_BCRYPT_MAX_BYTES]


def hash_password(plain_password: str) -> str:
    return bcrypt.hashpw(_bcrypt_bytes(plain_password), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(_bcrypt_bytes(plain_password), password_hash.encode("utf-8"))


class TokenType(StrEnum):
    ACCESS = "access"
    REFRESH = "refresh"


def _create_token(*, subject: uuid.UUID, token_type: TokenType, expires_delta: timedelta) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    payload = {
        "sub": str(subject),
        "type": token_type.value,
        "iat": now,
        "exp": now + expires_delta,
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(user_id: uuid.UUID) -> str:
    settings = get_settings()
    return _create_token(
        subject=user_id,
        token_type=TokenType.ACCESS,
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )


def create_refresh_token(user_id: uuid.UUID, *, remember_me: bool = False) -> str:
    settings = get_settings()
    days = (
        settings.remember_me_refresh_token_expire_days
        if remember_me
        else settings.refresh_token_expire_days
    )
    return _create_token(subject=user_id, token_type=TokenType.REFRESH, expires_delta=timedelta(days=days))


def decode_token(token: str) -> dict[str, Any] | None:
    settings = get_settings()
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError:
        return None

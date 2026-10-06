import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, Literal

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError
from jose import JWTError, jwt

from app.core.config import settings

ALGORITHM = "HS256"
password_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return password_hasher.verify(password_hash, password)
    except (VerifyMismatchError, InvalidHashError):
        return False


def create_token(
    user_id: uuid.UUID,
    role: str,
    token_type: Literal["access", "refresh"],
) -> str:
    now = datetime.now(UTC)
    if token_type == "access":
        expires_at = now + timedelta(minutes=settings.access_token_minutes)
        secret = settings.jwt_secret
    else:
        expires_at = now + timedelta(days=settings.refresh_token_days)
        secret = settings.jwt_refresh_secret

    payload: dict[str, Any] = {
        "sub": str(user_id),
        "role": role,
        "type": token_type,
        "iat": now,
        "exp": expires_at,
    }
    return jwt.encode(payload, secret, algorithm=ALGORITHM)


def decode_token(token: str, token_type: Literal["access", "refresh"]) -> dict[str, Any]:
    secret = settings.jwt_secret if token_type == "access" else settings.jwt_refresh_secret
    try:
        payload = jwt.decode(token, secret, algorithms=[ALGORITHM])
    except JWTError as error:
        raise ValueError("Invalid or expired token") from error
    if payload.get("type") != token_type or not payload.get("sub"):
        raise ValueError("Invalid token type")
    return payload

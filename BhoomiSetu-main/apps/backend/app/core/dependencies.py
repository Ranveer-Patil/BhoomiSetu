import uuid
from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_token
from app.models import User
from app.models.enums import UserRole

bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(credentials.credentials, "access")
        user_id = uuid.UUID(payload["sub"])
    except (ValueError, TypeError):
        raise credentials_error from None

    user = await db.get(User, user_id)
    if user is None:
        raise credentials_error
    return user


def require_roles(*allowed_roles: UserRole) -> Callable[..., User]:
    async def role_dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Your role cannot perform this action")
        return current_user

    return role_dependency

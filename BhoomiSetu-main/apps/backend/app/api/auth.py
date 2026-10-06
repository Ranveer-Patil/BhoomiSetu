import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_roles
from app.core.security import create_token, decode_token, hash_password, verify_password
from app.models import User
from app.models.enums import UserRole
from app.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.services.audit import write_audit_log

router = APIRouter(prefix="/auth", tags=["authentication"])


def build_token_response(user: User) -> TokenResponse:
    return TokenResponse(
        access_token=create_token(user.id, user.role.value, "access"),
        refresh_token=create_token(user.id, user.role.value, "refresh"),
        user=UserResponse.model_validate(user),
    )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    if payload.role != UserRole.LANDOWNER:
        raise HTTPException(403, "Staff accounts must be provisioned by an administrator")
    return await provision_user(payload, db)


@router.post("/users", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def create_staff_account(
    payload: RegisterRequest,
    db: AsyncSession = Depends(get_db),
    actor: User = Depends(require_roles(UserRole.SENIOR_ADMIN)),
) -> TokenResponse:
    return await provision_user(payload, db, actor)


async def provision_user(payload: RegisterRequest, db: AsyncSession, actor: User | None = None):
    user = User(
        name=payload.name.strip(),
        email=payload.email,
        role=payload.role,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    try:
        await db.flush()
        await write_audit_log(
            db, actor.id if actor else user.id, f"user.register:{user.id}:{user.role.value}"
        )
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=409,
            detail="An account with this email already exists",
        ) from None
    return build_token_response(user)


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    email = payload.email.strip().lower()
    user = await db.scalar(select(User).where(User.email == email))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    return build_token_response(user)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(payload: RefreshRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    try:
        token_payload = decode_token(payload.refresh_token, "refresh")
        user_id = uuid.UUID(token_payload["sub"])
    except (ValueError, TypeError):
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token") from None

    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="User no longer exists")
    return build_token_response(user)

import uuid

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import UserRole


class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=10, max_length=128)
    role: UserRole = UserRole.LANDOWNER

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if "@" not in normalized:
            raise ValueError("Enter a valid email address")
        return normalized


class LoginRequest(BaseModel):
    email: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    locale: str = "en"
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    email: str
    role: UserRole


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse

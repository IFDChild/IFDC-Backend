from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)
    remember_device: bool = True

    @field_validator("email")
    @classmethod
    def normalise_email(cls, value: str) -> str:
        return value.strip().lower()


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=10, max_length=128)

    @field_validator("new_password")
    @classmethod
    def strong_password(cls, value: str) -> str:
        checks = [
            any(c.islower() for c in value),
            any(c.isupper() for c in value),
            any(c.isdigit() for c in value),
            any(not c.isalnum() for c in value),
        ]
        if sum(checks) < 3:
            raise ValueError(
                "Password must mix at least three of: lowercase, uppercase, numbers, symbols"
            )
        return value


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: str | None = None
    role: str
    last_login_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class ProfileUpdate(BaseModel):
    """A user editing their own name."""

    full_name: str = Field(min_length=2, max_length=150)

    @field_validator("full_name")
    @classmethod
    def tidy(cls, value: str) -> str:
        return " ".join(value.split())


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=150)
    role: str = Field(default="Editor", min_length=2, max_length=100)
    password: str = Field(min_length=10, max_length=128)

    @field_validator("email")
    @classmethod
    def normalise_email(cls, value: str) -> str:
        return value.strip().lower()

    @field_validator("password")
    @classmethod
    def strong_password(cls, value: str) -> str:
        checks = [
            any(c.islower() for c in value),
            any(c.isupper() for c in value),
            any(c.isdigit() for c in value),
            any(not c.isalnum() for c in value),
        ]
        if sum(checks) < 3:
            raise ValueError(
                "Password must mix at least three of: lowercase, uppercase, numbers, symbols"
            )
        return value


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=150)
    role: str | None = Field(default=None, min_length=2, max_length=100)
    is_active: bool | None = None


class TeamMemberResponse(UserResponse):
    is_active: bool
    created_at: datetime

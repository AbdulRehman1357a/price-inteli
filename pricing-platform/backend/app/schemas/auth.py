from pydantic import BaseModel, EmailStr, Field, model_validator

from app.schemas.organization import OrganizationOut
from app.schemas.user import UserOut


class RegisterRequest(BaseModel):
    organization_name: str = Field(min_length=1, max_length=255)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    confirm_password: str = Field(min_length=8, max_length=128)
    country: str | None = Field(default=None, max_length=100)
    timezone: str = Field(default="UTC", max_length=100)
    currency: str = Field(default="USD", max_length=10)

    @model_validator(mode="after")
    def passwords_match(self) -> "RegisterRequest":
        if self.password != self.confirm_password:
            raise ValueError("password and confirm_password do not match")
        return self


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)
    remember_me: bool = False


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class MeResponse(BaseModel):
    user: UserOut
    organization: OrganizationOut
    roles: list[str]
    permissions: list[str]

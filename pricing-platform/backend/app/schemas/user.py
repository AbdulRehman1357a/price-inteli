import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import UserStatus
from app.schemas.common import PaginationParams
from app.schemas.role import RoleOut


class UserCreate(BaseModel):
    """Admin-created user, gated by PermissionCode.USERS_CREATE. No invite/email
    flow exists yet, so the admin sets an initial password directly and the
    user is active immediately — mirrors registration's own password handling.
    """

    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    phone: str | None = Field(default=None, max_length=50)
    role_ids: list[uuid.UUID] = Field(min_length=1)


class UserAdminUpdate(BaseModel):
    """Fields an admin may edit on another user in their organization,
    gated by PermissionCode.USERS_UPDATE. Distinct from UserUpdateSelf:
    also covers status (activate/deactivate) and role assignment. Email and
    password are deliberately excluded — same reasoning as self-service
    edits (login identifier / no verification flow), password changes go
    through a future reset flow, not this endpoint.
    """

    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    phone: str | None = Field(default=None, max_length=50)
    status: UserStatus | None = None
    role_ids: list[uuid.UUID] | None = Field(default=None, min_length=1)


class UserUpdateSelf(BaseModel):
    """Fields a user may edit on their own profile.

    Email is deliberately excluded: it's the login identifier and changing
    it needs a re-verification flow that doesn't exist yet. Status is
    system/admin-controlled, not self-editable.
    """

    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    phone: str | None = Field(default=None, max_length=50)


class UserOut(BaseModel):
    """Public user representation. Never includes password_hash."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    first_name: str
    last_name: str
    email: str
    phone: str | None
    status: UserStatus
    email_verified_at: datetime | None
    last_login_at: datetime | None
    created_at: datetime
    updated_at: datetime


class UserWithRolesOut(UserOut):
    """Used by the admin user-management endpoints (GET/POST/PUT /users...);
    UserOut alone still backs the self-service /auth/me response.
    """

    roles: list[RoleOut]


class UserListParams(PaginationParams):
    search: str | None = Field(default=None, description="Matches first name, last name, or email")

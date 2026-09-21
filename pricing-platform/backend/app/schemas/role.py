import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.permission import PermissionOut


class RoleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str | None
    is_system_role: bool


class RoleWithPermissionsOut(RoleOut):
    permissions: list[PermissionOut]


class RolePermissionsUpdate(BaseModel):
    """The full replacement permission set for a role, chosen from the
    global permission catalog (GET /permissions). Editing a still-global
    system role forks it into an organization-scoped copy first — see
    role_service.update_role_permissions.
    """

    permission_ids: list[uuid.UUID] = Field(min_length=1)

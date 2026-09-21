import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.rbac import PermissionCode
from app.core.responses import APIResponse
from app.db.session import get_db
from app.dependencies.auth import require_permission
from app.models.user import User
from app.schemas.permission import PermissionOut
from app.schemas.role import RolePermissionsUpdate, RoleWithPermissionsOut
from app.services import role_service

# Roles have no dedicated permission code of their own — viewing/editing them
# is only ever done alongside managing users (the user-edit screen's role
# picker, and the role/permission editor), so this reuses USERS_READ/
# USERS_UPDATE rather than adding new "roles.read"/"roles.update" permissions
# + a migration.
router = APIRouter(prefix="/roles", tags=["roles"])


def _to_out(role, permissions) -> RoleWithPermissionsOut:
    return RoleWithPermissionsOut(
        id=role.id,
        name=role.name,
        description=role.description,
        is_system_role=role.is_system_role,
        permissions=[PermissionOut.model_validate(p) for p in permissions],
    )


@router.get("", response_model=APIResponse[list[RoleWithPermissionsOut]])
def list_roles(
    current_user: User = Depends(require_permission(PermissionCode.USERS_READ)),
    db: Session = Depends(get_db),
) -> APIResponse[list[RoleWithPermissionsOut]]:
    roles = role_service.list_roles_with_permissions(db, organization_id=current_user.organization_id)
    return APIResponse(data=[_to_out(role, permissions) for role, permissions in roles])


@router.put("/{role_id}/permissions", response_model=APIResponse[RoleWithPermissionsOut])
def update_role_permissions(
    role_id: uuid.UUID,
    payload: RolePermissionsUpdate,
    current_user: User = Depends(require_permission(PermissionCode.USERS_UPDATE)),
    db: Session = Depends(get_db),
) -> APIResponse[RoleWithPermissionsOut]:
    """Editing a role that's still the shared global template forks it into
    an organization-scoped copy first — see role_service.update_role_permissions.
    """
    role, permissions = role_service.update_role_permissions(
        db,
        organization_id=current_user.organization_id,
        actor=current_user,
        role_id=role_id,
        permission_ids=payload.permission_ids,
    )
    return APIResponse(data=_to_out(role, permissions))

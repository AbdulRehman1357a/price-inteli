from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.rbac import PermissionCode
from app.core.responses import APIResponse
from app.db.session import get_db
from app.dependencies.auth import require_permission
from app.models.user import User
from app.schemas.permission import PermissionOut
from app.services import permission_service

# Same rationale as roles.py: permissions are only ever browsed as reference
# data while managing users/roles, so this reuses USERS_READ rather than
# adding a new "permissions.read" permission + migration.
router = APIRouter(prefix="/permissions", tags=["permissions"])


@router.get("", response_model=APIResponse[list[PermissionOut]])
def list_permissions(
    current_user: User = Depends(require_permission(PermissionCode.USERS_READ)),
    db: Session = Depends(get_db),
) -> APIResponse[list[PermissionOut]]:
    permissions = permission_service.list_permissions(db)
    return APIResponse(data=[PermissionOut.model_validate(p) for p in permissions])

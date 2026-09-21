import math
import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.rbac import PermissionCode
from app.core.responses import APIResponse
from app.db.session import get_db
from app.dependencies.auth import require_permission
from app.models.user import User
from app.schemas.common import PaginationMeta
from app.schemas.role import RoleOut
from app.schemas.user import UserAdminUpdate, UserCreate, UserListParams, UserOut, UserWithRolesOut
from app.services import user_service

router = APIRouter(prefix="/users", tags=["users"])


def _with_roles(db: Session, user: User) -> UserWithRolesOut:
    roles = user_service.roles_for_user(db, user.id)
    return UserWithRolesOut(
        **UserOut.model_validate(user).model_dump(), roles=[RoleOut.model_validate(r) for r in roles]
    )


@router.get("", response_model=APIResponse[list[UserWithRolesOut]])
def list_users(
    params: UserListParams = Depends(),
    current_user: User = Depends(require_permission(PermissionCode.USERS_READ)),
    db: Session = Depends(get_db),
) -> APIResponse[list[UserWithRolesOut]]:
    """List users in the caller's own organization. Tenant-scoped: never
    returns rows from another organization, regardless of who asks.
    """
    users, total = user_service.list_users(db, organization_id=current_user.organization_id, params=params)
    meta = PaginationMeta(
        page=params.page,
        page_size=params.page_size,
        total=total,
        total_pages=math.ceil(total / params.page_size) if total else 0,
    )
    return APIResponse(data=[_with_roles(db, u) for u in users], meta=meta.model_dump())


@router.post("", response_model=APIResponse[UserWithRolesOut], status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    current_user: User = Depends(require_permission(PermissionCode.USERS_CREATE)),
    db: Session = Depends(get_db),
) -> APIResponse[UserWithRolesOut]:
    user = user_service.create_user(db, organization_id=current_user.organization_id, payload=payload)
    return APIResponse(data=_with_roles(db, user))


@router.get("/{user_id}", response_model=APIResponse[UserWithRolesOut])
def get_user(
    user_id: uuid.UUID,
    current_user: User = Depends(require_permission(PermissionCode.USERS_READ)),
    db: Session = Depends(get_db),
) -> APIResponse[UserWithRolesOut]:
    user = user_service.get_user(db, organization_id=current_user.organization_id, user_id=user_id)
    return APIResponse(data=_with_roles(db, user))


@router.put("/{user_id}", response_model=APIResponse[UserWithRolesOut])
def update_user(
    user_id: uuid.UUID,
    payload: UserAdminUpdate,
    current_user: User = Depends(require_permission(PermissionCode.USERS_UPDATE)),
    db: Session = Depends(get_db),
) -> APIResponse[UserWithRolesOut]:
    user = user_service.update_user(
        db,
        organization_id=current_user.organization_id,
        actor_id=current_user.id,
        user_id=user_id,
        payload=payload,
    )
    return APIResponse(data=_with_roles(db, user))


@router.delete("/{user_id}", response_model=APIResponse[dict[str, bool]])
def delete_user(
    user_id: uuid.UUID,
    current_user: User = Depends(require_permission(PermissionCode.USERS_DELETE)),
    db: Session = Depends(get_db),
) -> APIResponse[dict[str, bool]]:
    user_service.delete_user(
        db, organization_id=current_user.organization_id, actor_id=current_user.id, user_id=user_id
    )
    return APIResponse(data={"deleted": True})

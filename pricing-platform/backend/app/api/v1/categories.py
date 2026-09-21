import math
import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.rbac import PermissionCode
from app.core.responses import APIResponse
from app.db.session import get_db
from app.dependencies.auth import require_permission
from app.models.user import User
from app.schemas.category import CategoryCreate, CategoryListParams, CategoryOut, CategoryUpdate
from app.schemas.common import PaginationMeta
from app.services import category_service

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=APIResponse[list[CategoryOut]])
def list_categories(
    params: CategoryListParams = Depends(),
    current_user: User = Depends(require_permission(PermissionCode.CATEGORIES_READ)),
    db: Session = Depends(get_db),
) -> APIResponse[list[CategoryOut]]:
    items, total = category_service.list_categories(
        db, organization_id=current_user.organization_id, params=params
    )
    meta = PaginationMeta(
        page=params.page,
        page_size=params.page_size,
        total=total,
        total_pages=math.ceil(total / params.page_size) if total else 0,
    )
    return APIResponse(data=[CategoryOut.model_validate(c) for c in items], meta=meta.model_dump())


@router.post("", response_model=APIResponse[CategoryOut], status_code=status.HTTP_201_CREATED)
def create_category(
    payload: CategoryCreate,
    current_user: User = Depends(require_permission(PermissionCode.CATEGORIES_CREATE)),
    db: Session = Depends(get_db),
) -> APIResponse[CategoryOut]:
    category = category_service.create_category(
        db, organization_id=current_user.organization_id, payload=payload
    )
    return APIResponse(data=CategoryOut.model_validate(category))


@router.get("/{category_id}", response_model=APIResponse[CategoryOut])
def get_category(
    category_id: uuid.UUID,
    current_user: User = Depends(require_permission(PermissionCode.CATEGORIES_READ)),
    db: Session = Depends(get_db),
) -> APIResponse[CategoryOut]:
    category = category_service.get_category(
        db, organization_id=current_user.organization_id, category_id=category_id
    )
    return APIResponse(data=CategoryOut.model_validate(category))


@router.put("/{category_id}", response_model=APIResponse[CategoryOut])
def update_category(
    category_id: uuid.UUID,
    payload: CategoryUpdate,
    current_user: User = Depends(require_permission(PermissionCode.CATEGORIES_UPDATE)),
    db: Session = Depends(get_db),
) -> APIResponse[CategoryOut]:
    category = category_service.update_category(
        db, organization_id=current_user.organization_id, category_id=category_id, payload=payload
    )
    return APIResponse(data=CategoryOut.model_validate(category))


@router.delete("/{category_id}", response_model=APIResponse[dict[str, bool]])
def delete_category(
    category_id: uuid.UUID,
    current_user: User = Depends(require_permission(PermissionCode.CATEGORIES_DELETE)),
    db: Session = Depends(get_db),
) -> APIResponse[dict[str, bool]]:
    category_service.delete_category(
        db, organization_id=current_user.organization_id, category_id=category_id
    )
    return APIResponse(data={"deleted": True})

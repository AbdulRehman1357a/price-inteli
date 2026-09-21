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
from app.schemas.store import StoreCreate, StoreListParams, StoreOut, StoreUpdate
from app.services import store_service

router = APIRouter(prefix="/stores", tags=["stores"])


@router.get("", response_model=APIResponse[list[StoreOut]])
def list_stores(
    params: StoreListParams = Depends(),
    current_user: User = Depends(require_permission(PermissionCode.STORES_READ)),
    db: Session = Depends(get_db),
) -> APIResponse[list[StoreOut]]:
    items, total = store_service.list_stores(
        db, organization_id=current_user.organization_id, params=params
    )
    meta = PaginationMeta(
        page=params.page,
        page_size=params.page_size,
        total=total,
        total_pages=math.ceil(total / params.page_size) if total else 0,
    )
    return APIResponse(data=[StoreOut.model_validate(s) for s in items], meta=meta.model_dump())


@router.post("", response_model=APIResponse[StoreOut], status_code=status.HTTP_201_CREATED)
def create_store(
    payload: StoreCreate,
    current_user: User = Depends(require_permission(PermissionCode.STORES_CREATE)),
    db: Session = Depends(get_db),
) -> APIResponse[StoreOut]:
    store = store_service.create_store(db, organization_id=current_user.organization_id, payload=payload)
    return APIResponse(data=StoreOut.model_validate(store))


@router.get("/{store_id}", response_model=APIResponse[StoreOut])
def get_store(
    store_id: uuid.UUID,
    current_user: User = Depends(require_permission(PermissionCode.STORES_READ)),
    db: Session = Depends(get_db),
) -> APIResponse[StoreOut]:
    store = store_service.get_store(db, organization_id=current_user.organization_id, store_id=store_id)
    return APIResponse(data=StoreOut.model_validate(store))


@router.put("/{store_id}", response_model=APIResponse[StoreOut])
def update_store(
    store_id: uuid.UUID,
    payload: StoreUpdate,
    current_user: User = Depends(require_permission(PermissionCode.STORES_UPDATE)),
    db: Session = Depends(get_db),
) -> APIResponse[StoreOut]:
    store = store_service.update_store(
        db, organization_id=current_user.organization_id, store_id=store_id, payload=payload
    )
    return APIResponse(data=StoreOut.model_validate(store))


@router.delete("/{store_id}", response_model=APIResponse[dict[str, bool]])
def delete_store(
    store_id: uuid.UUID,
    current_user: User = Depends(require_permission(PermissionCode.STORES_DELETE)),
    db: Session = Depends(get_db),
) -> APIResponse[dict[str, bool]]:
    store_service.delete_store(db, organization_id=current_user.organization_id, store_id=store_id)
    return APIResponse(data={"deleted": True})

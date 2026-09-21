import math
import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.rbac import PermissionCode
from app.core.responses import APIResponse
from app.db.session import get_db
from app.dependencies.auth import require_permission
from app.models.inventory import Inventory
from app.models.user import User
from app.schemas.common import PaginationMeta
from app.schemas.inventory import (
    BulkInventoryUpdateRequest,
    InventoryCreate,
    InventoryListParams,
    InventoryOut,
    InventorySummary,
    InventoryUpdate,
)
from app.services import inventory_service

router = APIRouter(prefix="/inventory", tags=["inventory"])


def _to_out(item: Inventory, details: dict[str, str]) -> InventoryOut:
    return InventoryOut(
        id=item.id,
        organization_id=item.organization_id,
        store_id=item.store_id,
        product_id=item.product_id,
        quantity_on_hand=item.quantity_on_hand,
        quantity_reserved=item.quantity_reserved,
        quantity_available=item.quantity_available,
        reorder_point=item.reorder_point,
        safety_stock=item.safety_stock,
        last_stock_update_at=item.last_stock_update_at,
        created_at=item.created_at,
        updated_at=item.updated_at,
        status=inventory_service.compute_status(item),
        product_name=details["product_name"],
        product_sku=details["product_sku"],
        store_name=details["store_name"],
        store_code=details["store_code"],
    )


def _to_out_list(db: Session, items: list[Inventory]) -> list[InventoryOut]:
    details_by_id = inventory_service.get_display_details(db, items)
    return [_to_out(item, details_by_id[item.id]) for item in items if item.id in details_by_id]


@router.get("", response_model=APIResponse[list[InventoryOut]])
def list_inventory(
    params: InventoryListParams = Depends(),
    current_user: User = Depends(require_permission(PermissionCode.INVENTORY_READ)),
    db: Session = Depends(get_db),
) -> APIResponse[list[InventoryOut]]:
    items, total = inventory_service.list_inventory(
        db, organization_id=current_user.organization_id, params=params
    )
    meta = PaginationMeta(
        page=params.page,
        page_size=params.page_size,
        total=total,
        total_pages=math.ceil(total / params.page_size) if total else 0,
    )
    return APIResponse(data=_to_out_list(db, items), meta=meta.model_dump())


@router.get("/summary", response_model=APIResponse[InventorySummary])
def get_inventory_summary(
    store_id: uuid.UUID | None = None,
    category_id: uuid.UUID | None = None,
    product_id: uuid.UUID | None = None,
    current_user: User = Depends(require_permission(PermissionCode.INVENTORY_READ)),
    db: Session = Depends(get_db),
) -> APIResponse[InventorySummary]:
    summary = inventory_service.get_summary(
        db,
        organization_id=current_user.organization_id,
        store_id=store_id,
        category_id=category_id,
        product_id=product_id,
    )
    return APIResponse(data=summary)


@router.post("", response_model=APIResponse[InventoryOut], status_code=status.HTTP_201_CREATED)
def create_inventory(
    payload: InventoryCreate,
    current_user: User = Depends(require_permission(PermissionCode.INVENTORY_CREATE)),
    db: Session = Depends(get_db),
) -> APIResponse[InventoryOut]:
    item = inventory_service.create_inventory(
        db, organization_id=current_user.organization_id, payload=payload
    )
    return APIResponse(data=_to_out_list(db, [item])[0])


@router.get("/{inventory_id}", response_model=APIResponse[InventoryOut])
def get_inventory(
    inventory_id: uuid.UUID,
    current_user: User = Depends(require_permission(PermissionCode.INVENTORY_READ)),
    db: Session = Depends(get_db),
) -> APIResponse[InventoryOut]:
    item = inventory_service.get_inventory(
        db, organization_id=current_user.organization_id, inventory_id=inventory_id
    )
    return APIResponse(data=_to_out_list(db, [item])[0])


@router.put("/{inventory_id}", response_model=APIResponse[InventoryOut])
def update_inventory(
    inventory_id: uuid.UUID,
    payload: InventoryUpdate,
    current_user: User = Depends(require_permission(PermissionCode.INVENTORY_UPDATE)),
    db: Session = Depends(get_db),
) -> APIResponse[InventoryOut]:
    item = inventory_service.update_inventory(
        db, organization_id=current_user.organization_id, inventory_id=inventory_id, payload=payload
    )
    return APIResponse(data=_to_out_list(db, [item])[0])


@router.post("/bulk-update", response_model=APIResponse[list[InventoryOut]])
def bulk_update_inventory(
    payload: BulkInventoryUpdateRequest,
    current_user: User = Depends(require_permission(PermissionCode.INVENTORY_ADJUST)),
    db: Session = Depends(get_db),
) -> APIResponse[list[InventoryOut]]:
    items = inventory_service.bulk_update(
        db, organization_id=current_user.organization_id, user_id=current_user.id, payload=payload
    )
    return APIResponse(data=_to_out_list(db, items))

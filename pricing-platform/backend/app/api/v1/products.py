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
from app.schemas.product import (
    ProductCreate,
    ProductListParams,
    ProductOut,
    ProductUpdate,
    ProductUrlFetchRequest,
    ProductUrlSuggestion,
)
from app.services import product_service, product_url_fetcher

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=APIResponse[list[ProductOut]])
def list_products(
    params: ProductListParams = Depends(),
    current_user: User = Depends(require_permission(PermissionCode.PRODUCTS_READ)),
    db: Session = Depends(get_db),
) -> APIResponse[list[ProductOut]]:
    items, total = product_service.list_products(
        db, organization_id=current_user.organization_id, params=params
    )
    meta = PaginationMeta(
        page=params.page,
        page_size=params.page_size,
        total=total,
        total_pages=math.ceil(total / params.page_size) if total else 0,
    )
    return APIResponse(data=[ProductOut.model_validate(p) for p in items], meta=meta.model_dump())


@router.post("", response_model=APIResponse[ProductOut], status_code=status.HTTP_201_CREATED)
def create_product(
    payload: ProductCreate,
    current_user: User = Depends(require_permission(PermissionCode.PRODUCTS_CREATE)),
    db: Session = Depends(get_db),
) -> APIResponse[ProductOut]:
    product = product_service.create_product(
        db, organization_id=current_user.organization_id, payload=payload
    )
    return APIResponse(data=ProductOut.model_validate(product))


@router.post("/fetch-from-url", response_model=APIResponse[ProductUrlSuggestion])
def fetch_product_from_url(
    payload: ProductUrlFetchRequest,
    current_user: User = Depends(require_permission(PermissionCode.PRODUCTS_CREATE)),
) -> APIResponse[ProductUrlSuggestion]:
    """Best-effort: gather product fields from a product page URL for the create form
    to pre-fill. Read-only helper — never writes to the database."""
    suggestion = product_url_fetcher.fetch_product_from_url(payload.url)
    return APIResponse(data=suggestion)


@router.get("/{product_id}", response_model=APIResponse[ProductOut])
def get_product(
    product_id: uuid.UUID,
    current_user: User = Depends(require_permission(PermissionCode.PRODUCTS_READ)),
    db: Session = Depends(get_db),
) -> APIResponse[ProductOut]:
    product = product_service.get_product(
        db, organization_id=current_user.organization_id, product_id=product_id
    )
    return APIResponse(data=ProductOut.model_validate(product))


@router.put("/{product_id}", response_model=APIResponse[ProductOut])
def update_product(
    product_id: uuid.UUID,
    payload: ProductUpdate,
    current_user: User = Depends(require_permission(PermissionCode.PRODUCTS_UPDATE)),
    db: Session = Depends(get_db),
) -> APIResponse[ProductOut]:
    product = product_service.update_product(
        db, organization_id=current_user.organization_id, product_id=product_id, payload=payload
    )
    return APIResponse(data=ProductOut.model_validate(product))


@router.delete("/{product_id}", response_model=APIResponse[dict[str, bool]])
def delete_product(
    product_id: uuid.UUID,
    current_user: User = Depends(require_permission(PermissionCode.PRODUCTS_DELETE)),
    db: Session = Depends(get_db),
) -> APIResponse[dict[str, bool]]:
    product_service.delete_product(
        db, organization_id=current_user.organization_id, product_id=product_id
    )
    return APIResponse(data={"deleted": True})

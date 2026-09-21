import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.rbac import PermissionCode
from app.core.responses import APIResponse
from app.db.session import get_db
from app.dependencies.auth import require_permission
from app.models.competitor_product import CompetitorProduct
from app.models.user import User
from app.repositories.competitor_price_repository import CompetitorPriceRepository
from app.repositories.product_repository import ProductRepository
from app.schemas.competitor import (
    CompetitorCreate,
    CompetitorDashboardRow,
    CompetitorOut,
    CompetitorPriceOut,
    CompetitorProductCreate,
    CompetitorProductDetail,
    CompetitorProductOut,
    CompetitorProductUpdate,
    CompetitorUpdate,
    ManualCompetitorPriceCreate,
)
from app.services import competitor_service

router = APIRouter(prefix="/competitors", tags=["competitors"])


def _to_detail(db: Session, cp: CompetitorProduct) -> CompetitorProductDetail:
    product = ProductRepository(db).get_by_id(cp.product_id)
    latest = CompetitorPriceRepository(db).get_latest_for_competitor_product(cp.id)
    return CompetitorProductDetail(
        **CompetitorProductOut.model_validate(cp).model_dump(),
        product_name=product.product_name if product else "Unknown",
        sku=product.sku if product else "",
        latest_price=latest.price if latest else None,
        latest_price_currency=latest.currency if latest else None,
        latest_price_captured_at=latest.captured_at if latest else None,
    )


@router.get("/dashboard", response_model=APIResponse[list[CompetitorDashboardRow]])
def get_dashboard(
    current_user: User = Depends(require_permission(PermissionCode.PRICING_READ)),
    db: Session = Depends(get_db),
) -> APIResponse[list[CompetitorDashboardRow]]:
    rows = competitor_service.get_dashboard(db, organization_id=current_user.organization_id)
    return APIResponse(data=rows)


@router.post("", response_model=APIResponse[CompetitorOut], status_code=status.HTTP_201_CREATED)
def create_competitor(
    payload: CompetitorCreate,
    current_user: User = Depends(require_permission(PermissionCode.PRICING_CREATE)),
    db: Session = Depends(get_db),
) -> APIResponse[CompetitorOut]:
    competitor = competitor_service.create_competitor(
        db, organization_id=current_user.organization_id, payload=payload
    )
    return APIResponse(data=CompetitorOut.model_validate(competitor))


@router.get("", response_model=APIResponse[list[CompetitorOut]])
def list_competitors(
    current_user: User = Depends(require_permission(PermissionCode.PRICING_READ)),
    db: Session = Depends(get_db),
) -> APIResponse[list[CompetitorOut]]:
    competitors = competitor_service.list_competitors(db, organization_id=current_user.organization_id)
    return APIResponse(data=[CompetitorOut.model_validate(c) for c in competitors])


@router.put("/products/{competitor_product_id}", response_model=APIResponse[CompetitorProductDetail])
def update_competitor_product(
    competitor_product_id: uuid.UUID,
    payload: CompetitorProductUpdate,
    current_user: User = Depends(require_permission(PermissionCode.PRICING_UPDATE)),
    db: Session = Depends(get_db),
) -> APIResponse[CompetitorProductDetail]:
    cp = competitor_service.update_competitor_product(
        db,
        organization_id=current_user.organization_id,
        competitor_product_id=competitor_product_id,
        payload=payload,
    )
    return APIResponse(data=_to_detail(db, cp))


@router.delete("/products/{competitor_product_id}", response_model=APIResponse[dict[str, bool]])
def delete_competitor_product(
    competitor_product_id: uuid.UUID,
    current_user: User = Depends(require_permission(PermissionCode.PRICING_UPDATE)),
    db: Session = Depends(get_db),
) -> APIResponse[dict[str, bool]]:
    competitor_service.delete_competitor_product(
        db, organization_id=current_user.organization_id, competitor_product_id=competitor_product_id
    )
    return APIResponse(data={"deleted": True})


@router.get("/products/{competitor_product_id}/prices", response_model=APIResponse[list[CompetitorPriceOut]])
def list_prices(
    competitor_product_id: uuid.UUID,
    current_user: User = Depends(require_permission(PermissionCode.PRICING_READ)),
    db: Session = Depends(get_db),
) -> APIResponse[list[CompetitorPriceOut]]:
    prices = competitor_service.list_prices(
        db, organization_id=current_user.organization_id, competitor_product_id=competitor_product_id
    )
    return APIResponse(data=[CompetitorPriceOut.model_validate(p) for p in prices])


@router.post(
    "/products/{competitor_product_id}/prices",
    response_model=APIResponse[CompetitorPriceOut],
    status_code=status.HTTP_201_CREATED,
)
def record_manual_price(
    competitor_product_id: uuid.UUID,
    payload: ManualCompetitorPriceCreate,
    current_user: User = Depends(require_permission(PermissionCode.PRICING_CREATE)),
    db: Session = Depends(get_db),
) -> APIResponse[CompetitorPriceOut]:
    price = competitor_service.record_manual_price(
        db,
        organization_id=current_user.organization_id,
        competitor_product_id=competitor_product_id,
        payload=payload,
    )
    return APIResponse(data=CompetitorPriceOut.model_validate(price))


@router.post(
    "/products/{competitor_product_id}/prices/sync",
    response_model=APIResponse[CompetitorPriceOut],
    status_code=status.HTTP_201_CREATED,
)
def sync_price(
    competitor_product_id: uuid.UUID,
    current_user: User = Depends(require_permission(PermissionCode.PRICING_CREATE)),
    db: Session = Depends(get_db),
) -> APIResponse[CompetitorPriceOut]:
    price = competitor_service.sync_price_from_api(
        db, organization_id=current_user.organization_id, competitor_product_id=competitor_product_id
    )
    return APIResponse(data=CompetitorPriceOut.model_validate(price))


@router.get("/{competitor_id}", response_model=APIResponse[CompetitorOut])
def get_competitor(
    competitor_id: uuid.UUID,
    current_user: User = Depends(require_permission(PermissionCode.PRICING_READ)),
    db: Session = Depends(get_db),
) -> APIResponse[CompetitorOut]:
    competitor = competitor_service.get_competitor(
        db, organization_id=current_user.organization_id, competitor_id=competitor_id
    )
    return APIResponse(data=CompetitorOut.model_validate(competitor))


@router.put("/{competitor_id}", response_model=APIResponse[CompetitorOut])
def update_competitor(
    competitor_id: uuid.UUID,
    payload: CompetitorUpdate,
    current_user: User = Depends(require_permission(PermissionCode.PRICING_UPDATE)),
    db: Session = Depends(get_db),
) -> APIResponse[CompetitorOut]:
    competitor = competitor_service.update_competitor(
        db, organization_id=current_user.organization_id, competitor_id=competitor_id, payload=payload
    )
    return APIResponse(data=CompetitorOut.model_validate(competitor))


@router.delete("/{competitor_id}", response_model=APIResponse[dict[str, bool]])
def delete_competitor(
    competitor_id: uuid.UUID,
    current_user: User = Depends(require_permission(PermissionCode.PRICING_UPDATE)),
    db: Session = Depends(get_db),
) -> APIResponse[dict[str, bool]]:
    competitor_service.delete_competitor(
        db, organization_id=current_user.organization_id, competitor_id=competitor_id
    )
    return APIResponse(data={"deleted": True})


@router.post(
    "/{competitor_id}/products",
    response_model=APIResponse[CompetitorProductDetail],
    status_code=status.HTTP_201_CREATED,
)
def add_competitor_product(
    competitor_id: uuid.UUID,
    payload: CompetitorProductCreate,
    current_user: User = Depends(require_permission(PermissionCode.PRICING_CREATE)),
    db: Session = Depends(get_db),
) -> APIResponse[CompetitorProductDetail]:
    cp = competitor_service.add_competitor_product(
        db, organization_id=current_user.organization_id, competitor_id=competitor_id, payload=payload
    )
    return APIResponse(data=_to_detail(db, cp))


@router.get("/{competitor_id}/products", response_model=APIResponse[list[CompetitorProductDetail]])
def list_competitor_products(
    competitor_id: uuid.UUID,
    current_user: User = Depends(require_permission(PermissionCode.PRICING_READ)),
    db: Session = Depends(get_db),
) -> APIResponse[list[CompetitorProductDetail]]:
    items = competitor_service.list_competitor_products(
        db, organization_id=current_user.organization_id, competitor_id=competitor_id
    )
    return APIResponse(data=[_to_detail(db, cp) for cp in items])

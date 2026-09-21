import math
import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.rbac import PermissionCode
from app.core.responses import APIResponse
from app.db.session import get_db
from app.dependencies.auth import require_permission
from app.models.ai_pricing_recommendation import AIPricingRecommendation
from app.models.user import User
from app.repositories.category_repository import CategoryRepository
from app.repositories.price_history_repository import PriceHistoryRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.store_repository import StoreRepository
from app.schemas.ai_pricing_recommendation import (
    AIPricingRecommendationDetail,
    AIPricingRecommendationListItem,
    AIPricingRecommendationListParams,
    AIPricingRecommendationOut,
    GenerateRecommendationRequest,
    ModifyRecommendationRequest,
)
from app.schemas.common import PaginationMeta
from app.schemas.price import PriceHistoryOut
from app.services import pricing_recommendation_service

router = APIRouter(prefix="/ai-recommendations", tags=["ai-pricing"])


def _list_item(db: Session, r: AIPricingRecommendation) -> AIPricingRecommendationListItem:
    product = ProductRepository(db).get_by_id(r.product_id)
    store = StoreRepository(db).get_by_id(r.store_id) if r.store_id else None
    difference = r.recommended_price - r.current_price
    difference_pct = (difference / r.current_price * Decimal("100")) if r.current_price else None
    difference_pct = difference_pct.quantize(Decimal("0.01")) if difference_pct is not None else None
    return AIPricingRecommendationListItem(
        **AIPricingRecommendationOut.model_validate(r).model_dump(),
        product_name=product.product_name if product else "Unknown",
        sku=product.sku if product else "",
        store_name=store.name if store else None,
        price_difference=difference,
        price_difference_percentage=difference_pct,
    )


def _detail(db: Session, r: AIPricingRecommendation) -> AIPricingRecommendationDetail:
    item = _list_item(db, r)
    product = ProductRepository(db).get_by_id(r.product_id)
    category = CategoryRepository(db).get_by_id(product.category_id) if product else None
    history = PriceHistoryRepository(db).list_recent_for_product(
        r.organization_id, product_id=r.product_id, limit=10
    )
    return AIPricingRecommendationDetail(
        **item.model_dump(),
        category_name=category.name if category else "Unknown",
        input_snapshot=r.input_snapshot,
        price_history=[PriceHistoryOut.model_validate(h) for h in history],
    )


@router.post(
    "/generate",
    response_model=APIResponse[AIPricingRecommendationDetail],
    status_code=status.HTTP_201_CREATED,
)
def generate_recommendation(
    payload: GenerateRecommendationRequest,
    current_user: User = Depends(require_permission(PermissionCode.AI_RECOMMENDATIONS_CREATE)),
    db: Session = Depends(get_db),
) -> APIResponse[AIPricingRecommendationDetail]:
    recommendation = pricing_recommendation_service.generate_recommendation(
        db,
        organization_id=current_user.organization_id,
        product_id=payload.product_id,
        store_id=payload.store_id,
        provider_name=payload.provider,
    )
    return APIResponse(data=_detail(db, recommendation))


@router.get("", response_model=APIResponse[list[AIPricingRecommendationListItem]])
def list_recommendations(
    params: AIPricingRecommendationListParams = Depends(),
    current_user: User = Depends(require_permission(PermissionCode.AI_RECOMMENDATIONS_READ)),
    db: Session = Depends(get_db),
) -> APIResponse[list[AIPricingRecommendationListItem]]:
    items, total = pricing_recommendation_service.list_recommendations(
        db, organization_id=current_user.organization_id, params=params
    )
    meta = PaginationMeta(
        page=params.page,
        page_size=params.page_size,
        total=total,
        total_pages=math.ceil(total / params.page_size) if total else 0,
    )
    return APIResponse(data=[_list_item(db, r) for r in items], meta=meta.model_dump())


@router.get("/summary", response_model=APIResponse[dict])
def get_summary(
    current_user: User = Depends(require_permission(PermissionCode.AI_RECOMMENDATIONS_READ)),
    db: Session = Depends(get_db),
) -> APIResponse[dict]:
    summary = pricing_recommendation_service.get_dashboard_summary(
        db, organization_id=current_user.organization_id
    )
    return APIResponse(data=summary)


@router.get("/{recommendation_id}", response_model=APIResponse[AIPricingRecommendationDetail])
def get_recommendation(
    recommendation_id: uuid.UUID,
    current_user: User = Depends(require_permission(PermissionCode.AI_RECOMMENDATIONS_READ)),
    db: Session = Depends(get_db),
) -> APIResponse[AIPricingRecommendationDetail]:
    recommendation = pricing_recommendation_service.get_recommendation(
        db, organization_id=current_user.organization_id, recommendation_id=recommendation_id
    )
    return APIResponse(data=_detail(db, recommendation))


@router.post("/{recommendation_id}/approve", response_model=APIResponse[AIPricingRecommendationDetail])
def approve_recommendation(
    recommendation_id: uuid.UUID,
    current_user: User = Depends(require_permission(PermissionCode.AI_RECOMMENDATIONS_REVIEW)),
    db: Session = Depends(get_db),
) -> APIResponse[AIPricingRecommendationDetail]:
    recommendation = pricing_recommendation_service.approve_recommendation(
        db,
        organization_id=current_user.organization_id,
        recommendation_id=recommendation_id,
        reviewer_id=current_user.id,
    )
    return APIResponse(data=_detail(db, recommendation))


@router.post("/{recommendation_id}/reject", response_model=APIResponse[AIPricingRecommendationDetail])
def reject_recommendation(
    recommendation_id: uuid.UUID,
    current_user: User = Depends(require_permission(PermissionCode.AI_RECOMMENDATIONS_REVIEW)),
    db: Session = Depends(get_db),
) -> APIResponse[AIPricingRecommendationDetail]:
    recommendation = pricing_recommendation_service.reject_recommendation(
        db,
        organization_id=current_user.organization_id,
        recommendation_id=recommendation_id,
        reviewer_id=current_user.id,
    )
    return APIResponse(data=_detail(db, recommendation))


@router.put("/{recommendation_id}/modify", response_model=APIResponse[AIPricingRecommendationDetail])
def modify_recommendation(
    recommendation_id: uuid.UUID,
    payload: ModifyRecommendationRequest,
    current_user: User = Depends(require_permission(PermissionCode.AI_RECOMMENDATIONS_REVIEW)),
    db: Session = Depends(get_db),
) -> APIResponse[AIPricingRecommendationDetail]:
    recommendation = pricing_recommendation_service.modify_recommendation(
        db,
        organization_id=current_user.organization_id,
        recommendation_id=recommendation_id,
        reviewer_id=current_user.id,
        new_price=payload.recommended_price,
    )
    return APIResponse(data=_detail(db, recommendation))


@router.post("/{recommendation_id}/apply", response_model=APIResponse[AIPricingRecommendationDetail])
def apply_recommendation(
    recommendation_id: uuid.UUID,
    current_user: User = Depends(require_permission(PermissionCode.AI_RECOMMENDATIONS_APPLY)),
    db: Session = Depends(get_db),
) -> APIResponse[AIPricingRecommendationDetail]:
    recommendation = pricing_recommendation_service.apply_recommendation(
        db,
        organization_id=current_user.organization_id,
        recommendation_id=recommendation_id,
        actor_id=current_user.id,
    )
    return APIResponse(data=_detail(db, recommendation))

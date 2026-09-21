import math
import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.rbac import PermissionCode
from app.core.responses import APIResponse
from app.db.session import get_db
from app.dependencies.auth import require_permission
from app.models.price import Price
from app.models.user import User
from app.schemas.common import PaginationMeta
from app.schemas.price import PriceCreate, PriceListParams, PriceOut, PriceUpdate
from app.schemas.pricing_rule import (
    PricingRuleCreate,
    PricingRuleListParams,
    PricingRuleOut,
    PricingRuleUpdate,
    RuleTestRequest,
    RuleTestResult,
)
from app.schemas.pricing_simulation import SimulationRequest, SimulationResponse
from app.services import price_service, pricing_rule_service, pricing_simulation_service

router = APIRouter(prefix="/pricing", tags=["pricing"])


def _to_price_out(price: Price) -> PriceOut:
    data = PriceOut.model_validate(price).model_dump()
    data["status"] = price_service.compute_display_status(price)
    return PriceOut(**data)


# --- Prices: list/create come first (no path-shape conflict with anything).
# --- Rules routes (all under the literal "/rules" segment) are declared
# --- before the parameterized "/{price_id}" routes below, so GET /pricing/rules
# --- is never swallowed by GET /pricing/{price_id}'s UUID-typed path param.


@router.get("", response_model=APIResponse[list[PriceOut]])
def list_prices(
    params: PriceListParams = Depends(),
    current_user: User = Depends(require_permission(PermissionCode.PRICING_READ)),
    db: Session = Depends(get_db),
) -> APIResponse[list[PriceOut]]:
    items, total = price_service.list_prices(db, organization_id=current_user.organization_id, params=params)
    meta = PaginationMeta(
        page=params.page,
        page_size=params.page_size,
        total=total,
        total_pages=math.ceil(total / params.page_size) if total else 0,
    )
    return APIResponse(data=[_to_price_out(p) for p in items], meta=meta.model_dump())


@router.post("", response_model=APIResponse[PriceOut], status_code=status.HTTP_201_CREATED)
def create_price(
    payload: PriceCreate,
    current_user: User = Depends(require_permission(PermissionCode.PRICING_CREATE)),
    db: Session = Depends(get_db),
) -> APIResponse[PriceOut]:
    price = price_service.create_price(
        db, organization_id=current_user.organization_id, user_id=current_user.id, payload=payload
    )
    return APIResponse(data=_to_price_out(price))


@router.post("/rules", response_model=APIResponse[PricingRuleOut], status_code=status.HTTP_201_CREATED)
def create_rule(
    payload: PricingRuleCreate,
    current_user: User = Depends(require_permission(PermissionCode.PRICING_CREATE)),
    db: Session = Depends(get_db),
) -> APIResponse[PricingRuleOut]:
    rule = pricing_rule_service.create_rule(db, organization_id=current_user.organization_id, payload=payload)
    return APIResponse(data=PricingRuleOut.model_validate(rule))


@router.get("/rules", response_model=APIResponse[list[PricingRuleOut]])
def list_rules(
    params: PricingRuleListParams = Depends(),
    current_user: User = Depends(require_permission(PermissionCode.PRICING_READ)),
    db: Session = Depends(get_db),
) -> APIResponse[list[PricingRuleOut]]:
    items, total = pricing_rule_service.list_rules(
        db, organization_id=current_user.organization_id, params=params
    )
    meta = PaginationMeta(
        page=params.page,
        page_size=params.page_size,
        total=total,
        total_pages=math.ceil(total / params.page_size) if total else 0,
    )
    return APIResponse(data=[PricingRuleOut.model_validate(r) for r in items], meta=meta.model_dump())


@router.get("/rules/{rule_id}", response_model=APIResponse[PricingRuleOut])
def get_rule(
    rule_id: uuid.UUID,
    current_user: User = Depends(require_permission(PermissionCode.PRICING_READ)),
    db: Session = Depends(get_db),
) -> APIResponse[PricingRuleOut]:
    rule = pricing_rule_service.get_rule(db, organization_id=current_user.organization_id, rule_id=rule_id)
    return APIResponse(data=PricingRuleOut.model_validate(rule))


@router.put("/rules/{rule_id}", response_model=APIResponse[PricingRuleOut])
def update_rule(
    rule_id: uuid.UUID,
    payload: PricingRuleUpdate,
    current_user: User = Depends(require_permission(PermissionCode.PRICING_UPDATE)),
    db: Session = Depends(get_db),
) -> APIResponse[PricingRuleOut]:
    rule = pricing_rule_service.update_rule(
        db, organization_id=current_user.organization_id, rule_id=rule_id, payload=payload
    )
    return APIResponse(data=PricingRuleOut.model_validate(rule))


@router.post("/rules/{rule_id}/test", response_model=APIResponse[RuleTestResult])
def test_rule(
    rule_id: uuid.UUID,
    payload: RuleTestRequest,
    current_user: User = Depends(require_permission(PermissionCode.PRICING_READ)),
    db: Session = Depends(get_db),
) -> APIResponse[RuleTestResult]:
    result = pricing_rule_service.test_rule(
        db, organization_id=current_user.organization_id, rule_id=rule_id, payload=payload
    )
    return APIResponse(data=result)


@router.post("/simulations", response_model=APIResponse[SimulationResponse])
def create_simulation(
    payload: SimulationRequest,
    current_user: User = Depends(require_permission(PermissionCode.PRICING_READ)),
    db: Session = Depends(get_db),
) -> APIResponse[SimulationResponse]:
    """Stateless what-if calculation — nothing is persisted, no price is
    ever changed. PRICING_READ is enough since this can't write anything.
    """
    result = pricing_simulation_service.simulate(
        db, organization_id=current_user.organization_id, payload=payload
    )
    return APIResponse(data=result)


@router.get("/{price_id}", response_model=APIResponse[PriceOut])
def get_price(
    price_id: uuid.UUID,
    current_user: User = Depends(require_permission(PermissionCode.PRICING_READ)),
    db: Session = Depends(get_db),
) -> APIResponse[PriceOut]:
    price = price_service.get_price(db, organization_id=current_user.organization_id, price_id=price_id)
    return APIResponse(data=_to_price_out(price))


@router.put("/{price_id}", response_model=APIResponse[PriceOut])
def update_price(
    price_id: uuid.UUID,
    payload: PriceUpdate,
    current_user: User = Depends(require_permission(PermissionCode.PRICING_UPDATE)),
    db: Session = Depends(get_db),
) -> APIResponse[PriceOut]:
    price = price_service.update_price(
        db,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        price_id=price_id,
        payload=payload,
    )
    return APIResponse(data=_to_price_out(price))

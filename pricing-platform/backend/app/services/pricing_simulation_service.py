import uuid
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.repositories.product_repository import ProductRepository
from app.repositories.store_repository import StoreRepository
from app.schemas.pricing_simulation import ScenarioResult, SimulationRequest, SimulationResponse
from app.services import pricing_engine, sales_velocity

_MONEY = Decimal("0.0001")
_HORIZON_DAYS = 30
# A retail price-elasticity-of-demand default used only when the caller
# doesn't supply expected_demand_change_percent themselves: -2.0 means "a 1%
# price increase is assumed to reduce unit demand by 2%" — a commonly-cited
# elastic-goods estimate, not derived from this organization's actual data.
# Using it lowers the simulation's confidence (see _compute_risk), and the
# caller can always override it with a real estimate.
_DEFAULT_ELASTICITY = Decimal("-2.0")


def _build_scenario(
    *, price: Decimal, units: Decimal, cost: Decimal | None, inventory: Decimal
) -> ScenarioResult:
    units = max(units, Decimal("0"))
    revenue = (price * units).quantize(_MONEY)

    gross_margin = None
    gross_margin_percent = None
    if cost is not None:
        gross_margin = ((price - cost) * units).quantize(_MONEY)
        if price > 0:
            gross_margin_percent = ((price - cost) / price * Decimal("100")).quantize(Decimal("0.01"))

    inventory_days = None
    units_per_day = units / Decimal(_HORIZON_DAYS)
    if units_per_day > 0:
        inventory_days = (inventory / units_per_day).quantize(Decimal("0.1"))

    return ScenarioResult(
        price=price.quantize(_MONEY),
        estimated_unit_sales=units.quantize(Decimal("0.01")),
        revenue=revenue,
        gross_margin=gross_margin,
        gross_margin_percent=gross_margin_percent,
        inventory_days=inventory_days,
    )


def _compute_risk(
    *, price_change_percent: Decimal, proposed: ScenarioResult, demand_defaulted: bool
) -> tuple[Decimal, str]:
    score = Decimal("0")

    if proposed.gross_margin_percent is not None:
        if proposed.gross_margin_percent < 0:
            score += 40
        elif proposed.gross_margin_percent < 10:
            score += 25
        elif proposed.gross_margin_percent < 20:
            score += 10

    if proposed.inventory_days is not None:
        if proposed.inventory_days < 7:
            score += 30
        elif proposed.inventory_days < 14:
            score += 15
        elif proposed.inventory_days > 180:
            score += 20
        elif proposed.inventory_days > 90:
            score += 10

    abs_change = abs(price_change_percent)
    if abs_change > 50:
        score += 20
    elif abs_change > 30:
        score += 12
    elif abs_change > 15:
        score += 5

    if demand_defaulted:
        score += 10

    score = min(score, Decimal("100"))
    level = "low" if score < 30 else "medium" if score < 60 else "high"
    return score, level


def _build_recommendation(
    *, revenue_change: Decimal, margin_change: Decimal | None, risk_level: str
) -> str:
    if margin_change is not None and margin_change > 0 and revenue_change > 0 and risk_level != "high":
        return f"Recommended — projected to increase both revenue and margin, with {risk_level} risk."
    if margin_change is not None and margin_change < 0 and risk_level == "high":
        return "Not recommended — projected margin decline combined with high risk."
    if revenue_change > 0 and (margin_change is None or margin_change <= 0):
        return "Caution — revenue may increase, but margin is projected to be flat or lower."
    if revenue_change <= 0 and margin_change is not None and margin_change > 0:
        return "Consider — margin improves despite lower projected revenue, a controlled trade-off."
    if revenue_change <= 0 and (margin_change is None or margin_change <= 0):
        return "Not recommended — projected declines in both revenue and margin."
    return f"Review manually — mixed signal with {risk_level} risk before applying this price."


def simulate(
    db: Session, *, organization_id: uuid.UUID, payload: SimulationRequest
) -> SimulationResponse:
    product = ProductRepository(db).get_by_id_for_organization(payload.product_id, organization_id)
    if product is None:
        raise NotFoundError("Product not found.", code="product_not_found")
    if payload.store_id is not None:
        store = StoreRepository(db).get_by_id_for_organization(payload.store_id, organization_id)
        if store is None:
            raise NotFoundError("Store not found.", code="store_not_found")

    velocity = sales_velocity.resolve(
        db,
        organization_id=organization_id,
        product_id=product.id,
        store_id=payload.store_id,
        lookback_days=_HORIZON_DAYS,
    )

    current_price = payload.current_price
    if current_price is None:
        current_price = pricing_engine.evaluate_for_product(
            db, organization_id=organization_id, product=product, store_id=payload.store_id
        ).current_price

    cost = payload.cost if payload.cost is not None else product.cost_price
    inventory_quantity = (
        payload.inventory_quantity if payload.inventory_quantity is not None else velocity.quantity_available
    )

    proposed_price = payload.proposed_price
    if current_price > 0:
        price_change_percent = (proposed_price - current_price) / current_price * Decimal("100")
    else:
        price_change_percent = Decimal("0")

    demand_defaulted = payload.expected_demand_change_percent is None
    if not demand_defaulted:
        demand_change_percent = payload.expected_demand_change_percent
    else:
        demand_change_percent = max(_DEFAULT_ELASTICITY * price_change_percent, Decimal("-100"))

    current_units = velocity.sales_velocity_per_day * Decimal(_HORIZON_DAYS)
    demand_multiplier = Decimal("1") + demand_change_percent / Decimal("100")
    proposed_units = max(Decimal("0"), current_units * demand_multiplier)

    current_scenario = _build_scenario(
        price=current_price, units=current_units, cost=cost, inventory=inventory_quantity
    )
    proposed_scenario = _build_scenario(
        price=proposed_price, units=proposed_units, cost=cost, inventory=inventory_quantity
    )

    revenue_change = (proposed_scenario.revenue - current_scenario.revenue).quantize(_MONEY)
    revenue_change_percent = None
    if current_scenario.revenue > 0:
        revenue_change_percent = (revenue_change / current_scenario.revenue * Decimal("100")).quantize(
            Decimal("0.01")
        )

    margin_change = None
    margin_change_percent_points = None
    if current_scenario.gross_margin is not None and proposed_scenario.gross_margin is not None:
        margin_change = (proposed_scenario.gross_margin - current_scenario.gross_margin).quantize(_MONEY)
    current_margin_pct = current_scenario.gross_margin_percent
    proposed_margin_pct = proposed_scenario.gross_margin_percent
    if current_margin_pct is not None and proposed_margin_pct is not None:
        margin_change_percent_points = proposed_margin_pct - current_margin_pct

    risk_score, risk_level = _compute_risk(
        price_change_percent=price_change_percent,
        proposed=proposed_scenario,
        demand_defaulted=demand_defaulted,
    )
    recommendation = _build_recommendation(
        revenue_change=revenue_change, margin_change=margin_change, risk_level=risk_level
    )

    return SimulationResponse(
        product_id=product.id,
        product_name=product.product_name,
        sku=product.sku,
        store_id=payload.store_id,
        horizon_days=_HORIZON_DAYS,
        current_scenario=current_scenario,
        proposed_scenario=proposed_scenario,
        revenue_change=revenue_change,
        revenue_change_percent=revenue_change_percent,
        margin_change=margin_change,
        margin_change_percent_points=margin_change_percent_points,
        risk_score=risk_score,
        risk_level=risk_level,
        recommendation=recommendation,
        assumptions={
            "price_change_percent": str(price_change_percent.quantize(Decimal("0.01"))),
            "demand_change_percent": str(demand_change_percent.quantize(Decimal("0.01"))),
            "demand_change_defaulted": demand_defaulted,
            "default_elasticity_used": str(_DEFAULT_ELASTICITY) if demand_defaulted else None,
            "cost_known": cost is not None,
            "baseline_sales_velocity_per_day": str(velocity.sales_velocity_per_day),
            "baseline_units_sold_lookback": str(velocity.units_sold_lookback),
        },
    )

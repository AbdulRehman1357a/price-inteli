import uuid
from decimal import Decimal

from pydantic import BaseModel, Field


class SimulationRequest(BaseModel):
    """Every field but proposed_price is optional and, if omitted, resolved
    deterministically from the product/store (current effective price,
    Product.cost_price, current inventory, and a price-elasticity default
    for demand change) — see pricing_simulation_service.simulate.
    """

    product_id: uuid.UUID
    store_id: uuid.UUID | None = None
    current_price: Decimal | None = Field(default=None, gt=0, max_digits=15, decimal_places=4)
    proposed_price: Decimal = Field(gt=0, max_digits=15, decimal_places=4)
    expected_demand_change_percent: Decimal | None = Field(default=None, max_digits=6, decimal_places=2)
    cost: Decimal | None = Field(default=None, ge=0, max_digits=15, decimal_places=4)
    inventory_quantity: Decimal | None = Field(default=None, ge=0, max_digits=15, decimal_places=4)


class ScenarioResult(BaseModel):
    price: Decimal
    estimated_unit_sales: Decimal
    revenue: Decimal
    gross_margin: Decimal | None
    gross_margin_percent: Decimal | None
    inventory_days: Decimal | None


class SimulationResponse(BaseModel):
    product_id: uuid.UUID
    product_name: str
    sku: str
    store_id: uuid.UUID | None
    horizon_days: int
    current_scenario: ScenarioResult
    proposed_scenario: ScenarioResult
    revenue_change: Decimal
    revenue_change_percent: Decimal | None
    margin_change: Decimal | None
    margin_change_percent_points: Decimal | None
    risk_score: Decimal
    risk_level: str
    recommendation: str
    assumptions: dict

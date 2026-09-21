import uuid
from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.mixins import utcnow
from app.repositories.inventory_adjustment_repository import InventoryAdjustmentRepository
from app.repositories.inventory_repository import InventoryRepository

DEFAULT_LOOKBACK_DAYS = 30


@dataclass
class InventoryVelocitySnapshot:
    quantity_on_hand: Decimal
    quantity_available: Decimal
    reorder_point: Decimal | None
    units_sold_lookback: Decimal
    lookback_days: int
    sales_velocity_per_day: Decimal


def resolve(
    db: Session,
    *,
    organization_id: uuid.UUID,
    product_id: uuid.UUID,
    store_id: uuid.UUID | None,
    lookback_days: int = DEFAULT_LOOKBACK_DAYS,
) -> InventoryVelocitySnapshot:
    """Inventory levels plus a deterministic sales-velocity proxy, shared by
    app.services.pricing_recommendation_service and pricing_simulation_service.

    This platform has no Orders/POS-transaction module, so there's no real
    sell-through count — a stock decrease (InventoryAdjustment,
    adjustment_type=decrease) over the lookback window is the closest
    available signal, same documented heuristic as Phase 11.
    """
    if store_id is not None:
        store_inventory = InventoryRepository(db).get_by_store_and_product(
            organization_id, store_id, product_id
        )
        inventory_rows = [store_inventory] if store_inventory is not None else []
    else:
        inventory_rows = InventoryRepository(db).list_for_product(organization_id, product_id=product_id)

    quantity_on_hand = sum((row.quantity_on_hand for row in inventory_rows), Decimal("0"))
    quantity_available = sum((row.quantity_available for row in inventory_rows), Decimal("0"))
    reorder_point = next((row.reorder_point for row in inventory_rows if row.reorder_point is not None), None)

    since = utcnow() - timedelta(days=lookback_days)
    adjustment_repo = InventoryAdjustmentRepository(db)
    decreases = [
        adj
        for row in inventory_rows
        for adj in adjustment_repo.list_decreases_since(organization_id, inventory_id=row.id, since=since)
    ]
    units_sold = sum((adj.adjustment_quantity for adj in decreases), Decimal("0"))
    sales_velocity_per_day = (units_sold / Decimal(lookback_days)).quantize(Decimal("0.0001"))

    return InventoryVelocitySnapshot(
        quantity_on_hand=quantity_on_hand,
        quantity_available=quantity_available,
        reorder_point=reorder_point,
        units_sold_lookback=units_sold,
        lookback_days=lookback_days,
        sales_velocity_per_day=sales_velocity_per_day,
    )

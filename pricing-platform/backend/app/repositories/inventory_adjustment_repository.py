import datetime as dt
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import func, select

from app.models.inventory import Inventory
from app.models.inventory_adjustment import AdjustmentType, InventoryAdjustment
from app.models.product import Product
from app.repositories.base import BaseRepository


class InventoryAdjustmentRepository(BaseRepository[InventoryAdjustment]):
    model = InventoryAdjustment

    def list_decreases_since(
        self, organization_id: uuid.UUID, *, inventory_id: uuid.UUID, since: datetime
    ) -> list[InventoryAdjustment]:
        """Stock decreases for one (store, product) since a cutoff — used as
        a deterministic sales-velocity proxy (see
        app/services/pricing_recommendation_service.py). This platform has
        no Orders/POS-transaction module yet, so a real sell-through count
        doesn't exist; a stock decrease is the closest available signal.
        """
        stmt = select(InventoryAdjustment).where(
            InventoryAdjustment.organization_id == organization_id,
            InventoryAdjustment.inventory_id == inventory_id,
            InventoryAdjustment.adjustment_type == AdjustmentType.DECREASE,
            InventoryAdjustment.created_at >= since,
        )
        return list(self.db.execute(stmt).scalars().all())

    def aggregate_decreases_by_day_store_product(
        self, organization_id: uuid.UUID, *, date_from: dt.date, date_to: dt.date
    ) -> list[tuple[dt.date, uuid.UUID, uuid.UUID, Decimal]]:
        """(day, store_id, product_id, quantity) for every stock decrease in
        range — the same "units sold" proxy as app.services.sales_velocity,
        bucketed for AnalyticsSnapshot's revenue/cogs pre-aggregation.
        analytics_service multiplies quantity by each product's current
        selling_price/cost_price (fetched separately) to get money amounts,
        since this table only ever stores quantities.
        """
        day_col = func.date(InventoryAdjustment.created_at)
        qty_sum = func.sum(InventoryAdjustment.adjustment_quantity)
        stmt = (
            select(day_col, Inventory.store_id, Inventory.product_id, qty_sum)
            .join(Inventory, Inventory.id == InventoryAdjustment.inventory_id)
            .where(
                InventoryAdjustment.organization_id == organization_id,
                InventoryAdjustment.adjustment_type == AdjustmentType.DECREASE,
                InventoryAdjustment.created_at >= date_from,
                InventoryAdjustment.created_at < date_to + dt.timedelta(days=1),
            )
            .group_by(day_col, Inventory.store_id, Inventory.product_id)
        )
        return [
            (_as_date(day), store_id, product_id, Decimal(qty or 0))
            for day, store_id, product_id, qty in self.db.execute(stmt).all()
        ]

    def totals_for_filters(
        self,
        organization_id: uuid.UUID,
        *,
        date_from: dt.date,
        date_to: dt.date,
        store_id: uuid.UUID | None,
        category_id: uuid.UUID | None,
        product_id: uuid.UUID | None,
    ) -> list[tuple[uuid.UUID, Decimal]]:
        """(product_id, quantity) totals over the whole range for a
        category/product filtered (live) dashboard request — grouped by
        product since revenue/cogs still needs each product's own
        price/cost (see analytics_service._live_revenue_and_cogs).
        """
        conditions = [
            InventoryAdjustment.organization_id == organization_id,
            InventoryAdjustment.adjustment_type == AdjustmentType.DECREASE,
            InventoryAdjustment.created_at >= date_from,
            InventoryAdjustment.created_at < date_to + dt.timedelta(days=1),
        ]
        if store_id is not None:
            conditions.append(Inventory.store_id == store_id)
        if product_id is not None:
            conditions.append(Inventory.product_id == product_id)
        if category_id is not None:
            conditions.append(
                Inventory.product_id.in_(select(Product.id).where(Product.category_id == category_id))
            )

        stmt = (
            select(Inventory.product_id, func.sum(InventoryAdjustment.adjustment_quantity))
            .join(Inventory, Inventory.id == InventoryAdjustment.inventory_id)
            .where(*conditions)
            .group_by(Inventory.product_id)
        )
        return [(pid, Decimal(qty or 0)) for pid, qty in self.db.execute(stmt).all()]


def _as_date(value) -> dt.date:
    return value if isinstance(value, dt.date) else dt.date.fromisoformat(str(value))

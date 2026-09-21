import uuid
from decimal import Decimal

from sqlalchemy import and_, func, select

from app.models.inventory import Inventory
from app.models.product import Product
from app.repositories.base import BaseRepository

# A row is "overstock" when on-hand exceeds this multiple of its reorder
# point. Not in the Phase 4 spec (no max_stock_level column exists) — a
# documented heuristic standing in for one, easy to swap for a real
# threshold field later.
OVERSTOCK_MULTIPLIER = Decimal("3")


def out_of_stock_condition():
    return Inventory.quantity_available <= 0


def low_stock_condition():
    return and_(
        Inventory.reorder_point.is_not(None),
        Inventory.quantity_available <= Inventory.reorder_point,
        ~out_of_stock_condition(),
    )


def overstock_condition():
    return and_(
        Inventory.reorder_point.is_not(None),
        Inventory.quantity_on_hand > Inventory.reorder_point * OVERSTOCK_MULTIPLIER,
        ~out_of_stock_condition(),
        ~low_stock_condition(),
    )


class InventoryRepository(BaseRepository[Inventory]):
    model = Inventory

    def get_by_id_for_organization(
        self, inventory_id: uuid.UUID, organization_id: uuid.UUID
    ) -> Inventory | None:
        stmt = select(Inventory).where(
            Inventory.id == inventory_id, Inventory.organization_id == organization_id
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_for_product(self, organization_id: uuid.UUID, *, product_id: uuid.UUID) -> list[Inventory]:
        stmt = select(Inventory).where(
            Inventory.organization_id == organization_id, Inventory.product_id == product_id
        )
        return list(self.db.execute(stmt).scalars().all())

    def get_by_store_and_product(
        self, organization_id: uuid.UUID, store_id: uuid.UUID, product_id: uuid.UUID
    ) -> Inventory | None:
        stmt = select(Inventory).where(
            Inventory.organization_id == organization_id,
            Inventory.store_id == store_id,
            Inventory.product_id == product_id,
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def _base_conditions(
        self,
        organization_id: uuid.UUID,
        *,
        store_id: uuid.UUID | None,
        category_id: uuid.UUID | None,
        product_id: uuid.UUID | None,
    ) -> list:
        conditions = [Inventory.organization_id == organization_id]
        if store_id is not None:
            conditions.append(Inventory.store_id == store_id)
        if product_id is not None:
            conditions.append(Inventory.product_id == product_id)
        if category_id is not None:
            conditions.append(
                Inventory.product_id.in_(select(Product.id).where(Product.category_id == category_id))
            )
        return conditions

    def search(
        self,
        organization_id: uuid.UUID,
        *,
        store_id: uuid.UUID | None = None,
        category_id: uuid.UUID | None = None,
        product_id: uuid.UUID | None = None,
        low_stock: bool | None = None,
        out_of_stock: bool | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Inventory], int]:
        conditions = self._base_conditions(
            organization_id, store_id=store_id, category_id=category_id, product_id=product_id
        )
        if low_stock:
            conditions.append(low_stock_condition())
        if out_of_stock:
            conditions.append(out_of_stock_condition())

        base_stmt = select(Inventory).where(*conditions)

        total = self.db.execute(select(func.count()).select_from(base_stmt.subquery())).scalar_one()

        items = list(
            self.db.execute(
                base_stmt.order_by(Inventory.last_stock_update_at.desc()).offset(offset).limit(limit)
            )
            .scalars()
            .all()
        )
        return items, total

    def summary_counts(
        self,
        organization_id: uuid.UUID,
        *,
        store_id: uuid.UUID | None = None,
        category_id: uuid.UUID | None = None,
        product_id: uuid.UUID | None = None,
    ) -> dict[str, int]:
        conditions = self._base_conditions(
            organization_id, store_id=store_id, category_id=category_id, product_id=product_id
        )

        def count_where(*extra) -> int:
            stmt = select(func.count()).select_from(Inventory).where(*conditions, *extra)
            return self.db.execute(stmt).scalar_one()

        return {
            "total_products": count_where(),
            "low_stock": count_where(low_stock_condition()),
            "out_of_stock": count_where(out_of_stock_condition()),
            "overstock": count_where(overstock_condition()),
        }

import uuid

from sqlalchemy import func, or_, select

from app.models.product import Product, ProductStatus
from app.repositories.base import BaseRepository

_SORTABLE_COLUMNS = {
    "product_name": Product.product_name,
    "sku": Product.sku,
    "selling_price": Product.selling_price,
    "created_at": Product.created_at,
}
_DEFAULT_SORT = Product.created_at.desc()


def _resolve_sort(sort: str | None):
    if not sort:
        return _DEFAULT_SORT
    descending = sort.startswith("-")
    key = sort[1:] if descending else sort
    column = _SORTABLE_COLUMNS.get(key)
    if column is None:
        return _DEFAULT_SORT
    return column.desc() if descending else column.asc()


class ProductRepository(BaseRepository[Product]):
    model = Product

    def get_by_id_for_organization(
        self, product_id: uuid.UUID, organization_id: uuid.UUID
    ) -> Product | None:
        stmt = self._not_deleted(
            select(Product).where(Product.id == product_id, Product.organization_id == organization_id)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_sku(self, organization_id: uuid.UUID, sku: str) -> Product | None:
        stmt = self._not_deleted(
            select(Product).where(Product.organization_id == organization_id, Product.sku == sku)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_prices_by_ids(
        self, organization_id: uuid.UUID, product_ids: list[uuid.UUID]
    ) -> dict[uuid.UUID, tuple]:
        """{product_id: (selling_price, cost_price)} for a batch of ids —
        used by analytics_service to value stock-decrease quantities into
        revenue/cost without an N+1 query per product.
        """
        if not product_ids:
            return {}
        stmt = self._not_deleted(
            select(Product.id, Product.selling_price, Product.cost_price).where(
                Product.organization_id == organization_id, Product.id.in_(product_ids)
            )
        )
        return {pid: (selling_price, cost_price) for pid, selling_price, cost_price in self.db.execute(stmt)}

    def search(
        self,
        organization_id: uuid.UUID,
        *,
        search: str | None = None,
        category_id: uuid.UUID | None = None,
        status: ProductStatus | None = None,
        sort: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Product], int]:
        conditions = [Product.organization_id == organization_id]
        if category_id is not None:
            conditions.append(Product.category_id == category_id)
        if status is not None:
            conditions.append(Product.status == status)
        if search:
            pattern = f"%{search.strip()}%"
            conditions.append(
                or_(
                    Product.sku.ilike(pattern),
                    Product.barcode.ilike(pattern),
                    Product.product_name.ilike(pattern),
                )
            )

        base_stmt = self._not_deleted(select(Product).where(*conditions))

        total = self.db.execute(
            select(func.count()).select_from(base_stmt.order_by(None).subquery())
        ).scalar_one()

        items = list(
            self.db.execute(base_stmt.order_by(_resolve_sort(sort)).offset(offset).limit(limit))
            .scalars()
            .all()
        )
        return items, total

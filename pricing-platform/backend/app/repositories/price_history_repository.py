import datetime as dt
import uuid
from decimal import Decimal

from sqlalchemy import func, select

from app.models.price_history import PriceHistory
from app.models.product import Product
from app.repositories.base import BaseRepository

# "A change" requires a prior price — a row with old_price IS NULL is the
# first-ever Price for that product/store, not a change in either count.
_HAS_PRIOR_PRICE = PriceHistory.old_price.is_not(None)
_SIGNED_DELTA = PriceHistory.new_price - PriceHistory.old_price


class PriceHistoryRepository(BaseRepository[PriceHistory]):
    model = PriceHistory

    def list_recent_for_product(
        self, organization_id: uuid.UUID, *, product_id: uuid.UUID, limit: int = 10
    ) -> list[PriceHistory]:
        stmt = (
            select(PriceHistory)
            .where(PriceHistory.organization_id == organization_id, PriceHistory.product_id == product_id)
            .order_by(PriceHistory.created_at.desc())
            .limit(limit)
        )
        return list(self.db.execute(stmt).scalars().all())

    def aggregate_by_day_and_store(
        self, organization_id: uuid.UUID, *, date_from: dt.date, date_to: dt.date
    ) -> list[tuple[dt.date, uuid.UUID | None, int, Decimal]]:
        """(day, store_id, count, signed_sum) for every day/store in range —
        the pre-aggregation source for AnalyticsSnapshot.price_changes_count
        / price_change_amount_sum. store_id is whatever this PriceHistory
        row itself carries (NULL = an org-wide price change), not filtered
        to one store — analytics_service buckets these per snapshot row.
        """
        day_col = func.date(PriceHistory.created_at)
        stmt = (
            select(day_col, PriceHistory.store_id, func.count(), func.sum(_SIGNED_DELTA))
            .where(
                PriceHistory.organization_id == organization_id,
                _HAS_PRIOR_PRICE,
                PriceHistory.created_at >= date_from,
                PriceHistory.created_at < date_to + dt.timedelta(days=1),
            )
            .group_by(day_col, PriceHistory.store_id)
        )
        return [
            (_as_date(day), store_id, count, Decimal(total or 0))
            for day, store_id, count, total in self.db.execute(stmt).all()
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
    ) -> tuple[int, Decimal]:
        """(count, signed_sum) over the whole range for a category/product
        filtered (live, non-pre-aggregated) dashboard request — see
        analytics_service.get_dashboard_metrics.
        """
        conditions = [
            PriceHistory.organization_id == organization_id,
            _HAS_PRIOR_PRICE,
            PriceHistory.created_at >= date_from,
            PriceHistory.created_at < date_to + dt.timedelta(days=1),
        ]
        if store_id is not None:
            conditions.append(PriceHistory.store_id == store_id)
        if product_id is not None:
            conditions.append(PriceHistory.product_id == product_id)
        if category_id is not None:
            conditions.append(
                PriceHistory.product_id.in_(select(Product.id).where(Product.category_id == category_id))
            )

        stmt = select(func.count(), func.sum(_SIGNED_DELTA)).where(*conditions)
        count, total = self.db.execute(stmt).one()
        return count, Decimal(total or 0)


def _as_date(value) -> dt.date:
    """SQLite's func.date() returns an ISO string; MySQL's DATE() returns a
    real date already — normalize both to a date object.
    """
    return value if isinstance(value, dt.date) else dt.date.fromisoformat(str(value))

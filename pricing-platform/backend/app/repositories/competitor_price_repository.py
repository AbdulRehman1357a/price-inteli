import uuid

from sqlalchemy import select

from app.models.competitor_price import CompetitorPrice
from app.repositories.base import BaseRepository


class CompetitorPriceRepository(BaseRepository[CompetitorPrice]):
    model = CompetitorPrice

    def list_for_competitor_product(
        self, competitor_product_id: uuid.UUID, *, limit: int = 20
    ) -> list[CompetitorPrice]:
        stmt = (
            select(CompetitorPrice)
            .where(CompetitorPrice.competitor_product_id == competitor_product_id)
            .order_by(CompetitorPrice.captured_at.desc())
            .limit(limit)
        )
        return list(self.db.execute(stmt).scalars().all())

    def get_latest_for_competitor_product(self, competitor_product_id: uuid.UUID) -> CompetitorPrice | None:
        stmt = (
            select(CompetitorPrice)
            .where(CompetitorPrice.competitor_product_id == competitor_product_id)
            .order_by(CompetitorPrice.captured_at.desc())
            .limit(1)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_latest_for_competitor_products(
        self, competitor_product_ids: list[uuid.UUID]
    ) -> dict[uuid.UUID, CompetitorPrice]:
        """One latest observation per competitor_product — used by the
        dashboard. Small per-tenant dataset, so this fetches every row for
        the given ids (newest first) and keeps the first one seen per id in
        Python, rather than a window-function query.
        """
        if not competitor_product_ids:
            return {}
        stmt = (
            select(CompetitorPrice)
            .where(CompetitorPrice.competitor_product_id.in_(competitor_product_ids))
            .order_by(CompetitorPrice.captured_at.desc())
        )
        latest: dict[uuid.UUID, CompetitorPrice] = {}
        for price in self.db.execute(stmt).scalars().all():
            latest.setdefault(price.competitor_product_id, price)
        return latest

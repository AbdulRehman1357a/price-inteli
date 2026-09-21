import uuid

from sqlalchemy import select

from app.models.competitor import Competitor
from app.models.competitor_product import CompetitorProduct
from app.repositories.base import BaseRepository


class CompetitorProductRepository(BaseRepository[CompetitorProduct]):
    model = CompetitorProduct

    def get_by_id_for_organization(
        self, competitor_product_id: uuid.UUID, organization_id: uuid.UUID
    ) -> CompetitorProduct | None:
        stmt = (
            select(CompetitorProduct)
            .join(Competitor, Competitor.id == CompetitorProduct.competitor_id)
            .where(
                CompetitorProduct.id == competitor_product_id,
                Competitor.organization_id == organization_id,
            )
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_for_competitor(self, competitor_id: uuid.UUID) -> list[CompetitorProduct]:
        stmt = select(CompetitorProduct).where(CompetitorProduct.competitor_id == competitor_id)
        return list(self.db.execute(stmt).scalars().all())

    def list_for_organization(self, organization_id: uuid.UUID) -> list[CompetitorProduct]:
        stmt = (
            select(CompetitorProduct)
            .join(Competitor, Competitor.id == CompetitorProduct.competitor_id)
            .where(Competitor.organization_id == organization_id)
        )
        return list(self.db.execute(stmt).scalars().all())

    def list_for_product(self, organization_id: uuid.UUID, product_id: uuid.UUID) -> list[CompetitorProduct]:
        stmt = (
            select(CompetitorProduct)
            .join(Competitor, Competitor.id == CompetitorProduct.competitor_id)
            .where(Competitor.organization_id == organization_id, CompetitorProduct.product_id == product_id)
        )
        return list(self.db.execute(stmt).scalars().all())

    def delete(self, competitor_product: CompetitorProduct) -> None:
        self.db.delete(competitor_product)
        self.db.flush()

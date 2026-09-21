import uuid

from sqlalchemy import select

from app.models.competitor import Competitor
from app.repositories.base import BaseRepository


class CompetitorRepository(BaseRepository[Competitor]):
    model = Competitor

    def get_by_id_for_organization(
        self, competitor_id: uuid.UUID, organization_id: uuid.UUID
    ) -> Competitor | None:
        stmt = select(Competitor).where(
            Competitor.id == competitor_id, Competitor.organization_id == organization_id
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_for_organization(self, organization_id: uuid.UUID) -> list[Competitor]:
        stmt = (
            select(Competitor)
            .where(Competitor.organization_id == organization_id)
            .order_by(Competitor.name)
        )
        return list(self.db.execute(stmt).scalars().all())

    def delete(self, competitor: Competitor) -> None:
        self.db.delete(competitor)
        self.db.flush()

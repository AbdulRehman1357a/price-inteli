import uuid

from sqlalchemy import select

from app.models.external_product import ExternalProduct
from app.repositories.base import BaseRepository


class ExternalProductRepository(BaseRepository[ExternalProduct]):
    model = ExternalProduct

    def get_by_external_id(self, integration_id: uuid.UUID, external_id: str) -> ExternalProduct | None:
        stmt = select(ExternalProduct).where(
            ExternalProduct.integration_id == integration_id, ExternalProduct.external_id == external_id
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_for_integration(self, integration_id: uuid.UUID) -> list[ExternalProduct]:
        stmt = select(ExternalProduct).where(ExternalProduct.integration_id == integration_id)
        return list(self.db.execute(stmt).scalars().all())

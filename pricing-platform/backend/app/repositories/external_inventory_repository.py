import uuid

from sqlalchemy import select

from app.models.external_inventory import ExternalInventory
from app.repositories.base import BaseRepository


class ExternalInventoryRepository(BaseRepository[ExternalInventory]):
    model = ExternalInventory

    def get_by_sku_store(
        self, integration_id: uuid.UUID, *, sku: str, store_code: str
    ) -> ExternalInventory | None:
        stmt = select(ExternalInventory).where(
            ExternalInventory.integration_id == integration_id,
            ExternalInventory.sku == sku,
            ExternalInventory.store_code == store_code,
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_for_integration(self, integration_id: uuid.UUID) -> list[ExternalInventory]:
        stmt = select(ExternalInventory).where(ExternalInventory.integration_id == integration_id)
        return list(self.db.execute(stmt).scalars().all())

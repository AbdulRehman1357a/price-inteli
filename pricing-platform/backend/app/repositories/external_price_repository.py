import uuid

from sqlalchemy import select

from app.models.external_price import ExternalPrice
from app.repositories.base import BaseRepository


class ExternalPriceRepository(BaseRepository[ExternalPrice]):
    model = ExternalPrice

    def get_by_sku_store(
        self, integration_id: uuid.UUID, *, sku: str, store_code: str | None
    ) -> ExternalPrice | None:
        if store_code is not None:
            store_condition = ExternalPrice.store_code == store_code
        else:
            store_condition = ExternalPrice.store_code.is_(None)
        stmt = select(ExternalPrice).where(
            ExternalPrice.integration_id == integration_id, ExternalPrice.sku == sku, store_condition
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_for_integration(self, integration_id: uuid.UUID) -> list[ExternalPrice]:
        stmt = select(ExternalPrice).where(ExternalPrice.integration_id == integration_id)
        return list(self.db.execute(stmt).scalars().all())

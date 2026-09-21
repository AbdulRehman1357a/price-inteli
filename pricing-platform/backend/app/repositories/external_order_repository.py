import uuid

from sqlalchemy import select

from app.models.external_order import ExternalOrder
from app.repositories.base import BaseRepository


class ExternalOrderRepository(BaseRepository[ExternalOrder]):
    model = ExternalOrder

    def get_by_external_order_id(
        self, integration_id: uuid.UUID, external_order_id: str
    ) -> ExternalOrder | None:
        stmt = select(ExternalOrder).where(
            ExternalOrder.integration_id == integration_id,
            ExternalOrder.external_order_id == external_order_id,
        )
        return self.db.execute(stmt).scalar_one_or_none()

import uuid

from sqlalchemy import func, select

from app.models.integration import Integration
from app.models.integration_webhook_event import IntegrationWebhookEvent
from app.repositories.base import BaseRepository


class IntegrationWebhookEventRepository(BaseRepository[IntegrationWebhookEvent]):
    model = IntegrationWebhookEvent

    def get_by_integration_and_event_id(
        self, integration_id: uuid.UUID, provider_event_id: str
    ) -> IntegrationWebhookEvent | None:
        stmt = select(IntegrationWebhookEvent).where(
            IntegrationWebhookEvent.integration_id == integration_id,
            IntegrationWebhookEvent.provider_event_id == provider_event_id,
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def search_for_integration(
        self, *, integration_id: uuid.UUID, organization_id: uuid.UUID, offset: int = 0, limit: int = 20
    ) -> tuple[list[IntegrationWebhookEvent], int]:
        base_stmt = (
            select(IntegrationWebhookEvent)
            .join(Integration, Integration.id == IntegrationWebhookEvent.integration_id)
            .where(
                IntegrationWebhookEvent.integration_id == integration_id,
                Integration.organization_id == organization_id,
            )
        )
        total = self.db.execute(select(func.count()).select_from(base_stmt.subquery())).scalar_one()
        items = list(
            self.db.execute(
                base_stmt.order_by(IntegrationWebhookEvent.received_at.desc()).offset(offset).limit(limit)
            )
            .scalars()
            .all()
        )
        return items, total

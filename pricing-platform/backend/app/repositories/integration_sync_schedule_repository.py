import uuid
from datetime import datetime

from sqlalchemy import select

from app.models.integration import Integration
from app.models.integration_mapping import CanonicalEntityType
from app.models.integration_sync_schedule import IntegrationSyncSchedule
from app.repositories.base import BaseRepository


class IntegrationSyncScheduleRepository(BaseRepository[IntegrationSyncSchedule]):
    model = IntegrationSyncSchedule

    def get_by_id_for_organization(
        self, schedule_id: uuid.UUID, organization_id: uuid.UUID
    ) -> IntegrationSyncSchedule | None:
        stmt = (
            select(IntegrationSyncSchedule)
            .join(Integration, Integration.id == IntegrationSyncSchedule.integration_id)
            .where(IntegrationSyncSchedule.id == schedule_id, Integration.organization_id == organization_id)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def get_for_entity_type(
        self, integration_id: uuid.UUID, entity_type: CanonicalEntityType
    ) -> IntegrationSyncSchedule | None:
        stmt = select(IntegrationSyncSchedule).where(
            IntegrationSyncSchedule.integration_id == integration_id,
            IntegrationSyncSchedule.entity_type == entity_type,
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_for_integration(self, integration_id: uuid.UUID) -> list[IntegrationSyncSchedule]:
        stmt = select(IntegrationSyncSchedule).where(IntegrationSyncSchedule.integration_id == integration_id)
        return list(self.db.execute(stmt).scalars().all())

    def list_due(self, *, now: datetime) -> list[IntegrationSyncSchedule]:
        """Cross-tenant by design — the Celery Beat task
        (app.services.integration_schedule_service.dispatch_due_schedules)
        runs globally, not per-organization-request.
        """
        stmt = select(IntegrationSyncSchedule).where(
            IntegrationSyncSchedule.is_enabled.is_(True),
            IntegrationSyncSchedule.next_run_at <= now,
        )
        return list(self.db.execute(stmt).scalars().all())

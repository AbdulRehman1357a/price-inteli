import uuid

from sqlalchemy import func, select

from app.models.integration import Integration
from app.models.integration_sync_job import IntegrationSyncJob, IntegrationSyncJobStatus
from app.repositories.base import BaseRepository


class IntegrationSyncJobRepository(BaseRepository[IntegrationSyncJob]):
    """No organization_id column on integration_sync_jobs (per the literal
    Phase 10 spec) — tenant-scoped queries join through integration_id to
    Integration.organization_id, same as Phase 8/9's device_sync_logs.
    """

    model = IntegrationSyncJob

    def get_by_id_for_organization(
        self, job_id: uuid.UUID, organization_id: uuid.UUID
    ) -> IntegrationSyncJob | None:
        stmt = (
            select(IntegrationSyncJob)
            .join(Integration, Integration.id == IntegrationSyncJob.integration_id)
            .where(IntegrationSyncJob.id == job_id, Integration.organization_id == organization_id)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def get_latest_for_integration(self, integration_id: uuid.UUID) -> IntegrationSyncJob | None:
        stmt = (
            select(IntegrationSyncJob)
            .where(IntegrationSyncJob.integration_id == integration_id)
            .order_by(IntegrationSyncJob.started_at.desc())
        )
        return self.db.execute(stmt).scalars().first()

    def search_for_integration(
        self,
        *,
        integration_id: uuid.UUID,
        organization_id: uuid.UUID,
        status: IntegrationSyncJobStatus | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[IntegrationSyncJob], int]:
        conditions = [
            IntegrationSyncJob.integration_id == integration_id,
            Integration.organization_id == organization_id,
        ]
        if status is not None:
            conditions.append(IntegrationSyncJob.status == status)

        base_stmt = (
            select(IntegrationSyncJob)
            .join(Integration, Integration.id == IntegrationSyncJob.integration_id)
            .where(*conditions)
        )
        total = self.db.execute(select(func.count()).select_from(base_stmt.subquery())).scalar_one()
        items = list(
            self.db.execute(
                base_stmt.order_by(IntegrationSyncJob.started_at.desc()).offset(offset).limit(limit)
            )
            .scalars()
            .all()
        )
        return items, total

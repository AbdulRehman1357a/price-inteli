import uuid

from sqlalchemy import func, select

from app.models.integration import Integration
from app.models.integration_reconciliation import IntegrationReconciliation, IntegrationReconciliationStatus
from app.repositories.base import BaseRepository


class IntegrationReconciliationRepository(BaseRepository[IntegrationReconciliation]):
    model = IntegrationReconciliation

    def get_by_id_for_organization(
        self, reconciliation_id: uuid.UUID, organization_id: uuid.UUID
    ) -> IntegrationReconciliation | None:
        stmt = (
            select(IntegrationReconciliation)
            .join(Integration, Integration.id == IntegrationReconciliation.integration_id)
            .where(
                IntegrationReconciliation.id == reconciliation_id,
                Integration.organization_id == organization_id,
            )
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def search_for_integration(
        self,
        *,
        integration_id: uuid.UUID,
        organization_id: uuid.UUID,
        status: IntegrationReconciliationStatus | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[IntegrationReconciliation], int]:
        conditions = [
            IntegrationReconciliation.integration_id == integration_id,
            Integration.organization_id == organization_id,
        ]
        if status is not None:
            conditions.append(IntegrationReconciliation.status == status)

        base_stmt = (
            select(IntegrationReconciliation)
            .join(Integration, Integration.id == IntegrationReconciliation.integration_id)
            .where(*conditions)
        )
        total = self.db.execute(select(func.count()).select_from(base_stmt.subquery())).scalar_one()
        items = list(
            self.db.execute(
                base_stmt.order_by(IntegrationReconciliation.detected_at.desc()).offset(offset).limit(limit)
            )
            .scalars()
            .all()
        )
        return items, total

    def count_open(self, integration_id: uuid.UUID) -> int:
        stmt = select(func.count()).where(
            IntegrationReconciliation.integration_id == integration_id,
            IntegrationReconciliation.status == IntegrationReconciliationStatus.OPEN,
        )
        return self.db.execute(stmt).scalar_one()

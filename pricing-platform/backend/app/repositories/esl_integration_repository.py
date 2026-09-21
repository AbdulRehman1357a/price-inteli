import uuid

from sqlalchemy import func, select

from app.models.esl_integration import ESLIntegration, ESLIntegrationStatus, ESLIntegrationType
from app.repositories.base import BaseRepository


class ESLIntegrationRepository(BaseRepository[ESLIntegration]):
    model = ESLIntegration

    def get_by_id_for_organization(
        self, integration_id: uuid.UUID, organization_id: uuid.UUID
    ) -> ESLIntegration | None:
        stmt = select(ESLIntegration).where(
            ESLIntegration.id == integration_id, ESLIntegration.organization_id == organization_id
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def search(
        self,
        organization_id: uuid.UUID,
        *,
        vendor_id: uuid.UUID | None = None,
        integration_type: ESLIntegrationType | None = None,
        status: ESLIntegrationStatus | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[ESLIntegration], int]:
        conditions = [ESLIntegration.organization_id == organization_id]
        if vendor_id is not None:
            conditions.append(ESLIntegration.vendor_id == vendor_id)
        if integration_type is not None:
            conditions.append(ESLIntegration.integration_type == integration_type)
        if status is not None:
            conditions.append(ESLIntegration.status == status)

        base_stmt = select(ESLIntegration).where(*conditions)
        total = self.db.execute(select(func.count()).select_from(base_stmt.subquery())).scalar_one()
        items = list(
            self.db.execute(
                base_stmt.order_by(ESLIntegration.created_at.desc()).offset(offset).limit(limit)
            )
            .scalars()
            .all()
        )
        return items, total

    def delete(self, integration: ESLIntegration) -> None:
        self.db.delete(integration)
        self.db.flush()

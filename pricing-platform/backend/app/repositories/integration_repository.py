import uuid

from sqlalchemy import func, select

from app.models.integration import Integration, IntegrationCategory, IntegrationProvider, IntegrationStatus
from app.repositories.base import BaseRepository


class IntegrationRepository(BaseRepository[Integration]):
    model = Integration

    def get_by_id_for_organization(
        self, integration_id: uuid.UUID, organization_id: uuid.UUID
    ) -> Integration | None:
        stmt = select(Integration).where(
            Integration.id == integration_id, Integration.organization_id == organization_id
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def search(
        self,
        organization_id: uuid.UUID,
        *,
        integration_category: IntegrationCategory | None = None,
        provider: IntegrationProvider | None = None,
        status: IntegrationStatus | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Integration], int]:
        conditions = [Integration.organization_id == organization_id]
        if integration_category is not None:
            conditions.append(Integration.integration_category == integration_category)
        if provider is not None:
            conditions.append(Integration.provider == provider)
        if status is not None:
            conditions.append(Integration.status == status)

        base_stmt = select(Integration).where(*conditions)
        total = self.db.execute(select(func.count()).select_from(base_stmt.subquery())).scalar_one()
        items = list(
            self.db.execute(
                base_stmt.order_by(Integration.created_at.desc()).offset(offset).limit(limit)
            )
            .scalars()
            .all()
        )
        return items, total

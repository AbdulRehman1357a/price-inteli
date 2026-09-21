import uuid

from sqlalchemy import func, select

from app.models.integration import Integration
from app.models.integration_error import IntegrationError
from app.repositories.base import BaseRepository


class IntegrationErrorRepository(BaseRepository[IntegrationError]):
    model = IntegrationError

    def get_by_id_for_organization(
        self, error_id: uuid.UUID, organization_id: uuid.UUID
    ) -> IntegrationError | None:
        stmt = (
            select(IntegrationError)
            .join(Integration, Integration.id == IntegrationError.integration_id)
            .where(IntegrationError.id == error_id, Integration.organization_id == organization_id)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def search_for_integration(
        self,
        *,
        integration_id: uuid.UUID,
        organization_id: uuid.UUID,
        is_resolved: bool | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[IntegrationError], int]:
        conditions = [
            IntegrationError.integration_id == integration_id,
            Integration.organization_id == organization_id,
        ]
        if is_resolved is not None:
            conditions.append(IntegrationError.is_resolved.is_(is_resolved))

        base_stmt = (
            select(IntegrationError)
            .join(Integration, Integration.id == IntegrationError.integration_id)
            .where(*conditions)
        )
        total = self.db.execute(select(func.count()).select_from(base_stmt.subquery())).scalar_one()
        items = list(
            self.db.execute(
                base_stmt.order_by(IntegrationError.created_at.desc()).offset(offset).limit(limit)
            )
            .scalars()
            .all()
        )
        return items, total

    def count_unresolved(self, integration_id: uuid.UUID) -> int:
        stmt = select(func.count()).where(
            IntegrationError.integration_id == integration_id, IntegrationError.is_resolved.is_(False)
        )
        return self.db.execute(stmt).scalar_one()

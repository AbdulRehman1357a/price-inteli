import uuid

from sqlalchemy import select

from app.models.integration import Integration
from app.models.integration_location import IntegrationLocation
from app.repositories.base import BaseRepository


class IntegrationLocationRepository(BaseRepository[IntegrationLocation]):
    """No organization_id column — tenant scoping joins through
    integration_id, same as IntegrationMapping/IntegrationSyncJob.
    """

    model = IntegrationLocation

    def get_by_id_for_organization(
        self, location_id: uuid.UUID, organization_id: uuid.UUID
    ) -> IntegrationLocation | None:
        stmt = (
            select(IntegrationLocation)
            .join(Integration, Integration.id == IntegrationLocation.integration_id)
            .where(IntegrationLocation.id == location_id, Integration.organization_id == organization_id)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_external_location_id(
        self, integration_id: uuid.UUID, external_location_id: str
    ) -> IntegrationLocation | None:
        stmt = select(IntegrationLocation).where(
            IntegrationLocation.integration_id == integration_id,
            IntegrationLocation.external_location_id == external_location_id,
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_for_integration(self, integration_id: uuid.UUID) -> list[IntegrationLocation]:
        stmt = (
            select(IntegrationLocation)
            .where(IntegrationLocation.integration_id == integration_id)
            .order_by(IntegrationLocation.external_location_name)
        )
        return list(self.db.execute(stmt).scalars().all())

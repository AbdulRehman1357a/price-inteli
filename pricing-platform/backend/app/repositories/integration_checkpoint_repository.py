import uuid

from sqlalchemy import select

from app.models.integration_checkpoint import IntegrationCheckpoint
from app.models.integration_mapping import CanonicalEntityType
from app.repositories.base import BaseRepository


class IntegrationCheckpointRepository(BaseRepository[IntegrationCheckpoint]):
    model = IntegrationCheckpoint

    def get_for_entity_type(
        self, integration_id: uuid.UUID, entity_type: CanonicalEntityType
    ) -> IntegrationCheckpoint | None:
        stmt = select(IntegrationCheckpoint).where(
            IntegrationCheckpoint.integration_id == integration_id,
            IntegrationCheckpoint.entity_type == entity_type,
        )
        return self.db.execute(stmt).scalar_one_or_none()

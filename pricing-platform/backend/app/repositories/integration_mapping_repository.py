import uuid

from sqlalchemy import select

from app.models.integration import Integration
from app.models.integration_mapping import CanonicalEntityType, IntegrationMapping
from app.repositories.base import BaseRepository


class IntegrationMappingRepository(BaseRepository[IntegrationMapping]):
    """No organization_id column on integration_mappings (per the literal
    Phase 10 spec) — tenant-scoped queries join through integration_id,
    same as IntegrationSyncJobRepository.
    """

    model = IntegrationMapping

    def get_by_id_for_organization(
        self, mapping_id: uuid.UUID, organization_id: uuid.UUID
    ) -> IntegrationMapping | None:
        stmt = (
            select(IntegrationMapping)
            .join(Integration, Integration.id == IntegrationMapping.integration_id)
            .where(IntegrationMapping.id == mapping_id, Integration.organization_id == organization_id)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_for_integration(
        self, *, integration_id: uuid.UUID, entity_type: CanonicalEntityType | None = None
    ) -> list[IntegrationMapping]:
        conditions = [IntegrationMapping.integration_id == integration_id]
        if entity_type is not None:
            conditions.append(IntegrationMapping.entity_type == entity_type)
        stmt = select(IntegrationMapping).where(*conditions).order_by(IntegrationMapping.created_at)
        return list(self.db.execute(stmt).scalars().all())

    def delete(self, mapping: IntegrationMapping) -> None:
        """Hard delete — mappings have no deleted_at column (not in the
        literal Phase 10 spec) and no soft-delete-worthy history concern.
        """
        self.db.delete(mapping)
        self.db.flush()

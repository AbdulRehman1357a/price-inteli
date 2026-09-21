import uuid

from sqlalchemy import select

from app.models.integration import Integration
from app.models.integration_authority import IntegrationAuthority
from app.models.integration_mapping import CanonicalEntityType
from app.repositories.base import BaseRepository


class IntegrationAuthorityRepository(BaseRepository[IntegrationAuthority]):
    """No organization_id column — tenant scoping joins through
    integration_id.
    """

    model = IntegrationAuthority

    def get_by_id_for_organization(
        self, authority_id: uuid.UUID, organization_id: uuid.UUID
    ) -> IntegrationAuthority | None:
        stmt = (
            select(IntegrationAuthority)
            .join(Integration, Integration.id == IntegrationAuthority.integration_id)
            .where(IntegrationAuthority.id == authority_id, Integration.organization_id == organization_id)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def get_effective(
        self, integration_id: uuid.UUID, *, entity_type: CanonicalEntityType, field_name: str
    ) -> IntegrationAuthority | None:
        """The field-specific row if configured, else the "*" wildcard row
        for this entity_type, else None (meaning: no configuration at all —
        app.services.integration_authority_service.may_apply treats that as
        today's default behavior).
        """
        specific = self.db.execute(
            select(IntegrationAuthority).where(
                IntegrationAuthority.integration_id == integration_id,
                IntegrationAuthority.entity_type == entity_type,
                IntegrationAuthority.field_name == field_name,
            )
        ).scalar_one_or_none()
        if specific is not None:
            return specific
        if field_name == "*":
            return None
        return self.db.execute(
            select(IntegrationAuthority).where(
                IntegrationAuthority.integration_id == integration_id,
                IntegrationAuthority.entity_type == entity_type,
                IntegrationAuthority.field_name == "*",
            )
        ).scalar_one_or_none()

    def list_for_integration(self, integration_id: uuid.UUID) -> list[IntegrationAuthority]:
        stmt = select(IntegrationAuthority).where(IntegrationAuthority.integration_id == integration_id)
        return list(self.db.execute(stmt).scalars().all())

    def delete(self, authority: IntegrationAuthority) -> None:
        self.db.delete(authority)
        self.db.flush()

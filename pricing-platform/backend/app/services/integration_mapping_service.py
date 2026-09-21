import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.integration_mapping import CanonicalEntityType, IntegrationMapping
from app.repositories.integration_mapping_repository import IntegrationMappingRepository
from app.schemas.integration_mapping import IntegrationMappingCreate
from app.services.integration_service import get_integration


def create_mapping(
    db: Session, *, organization_id: uuid.UUID, integration_id: uuid.UUID, payload: IntegrationMappingCreate
) -> IntegrationMapping:
    get_integration(db, organization_id=organization_id, integration_id=integration_id)  # tenant check

    mapping = IntegrationMapping(
        id=uuid.uuid4(),
        integration_id=integration_id,
        entity_type=payload.entity_type,
        source_field=payload.source_field,
        canonical_field=payload.canonical_field,
        transformation_rule=payload.transformation_rule,
        data_type=payload.data_type,
        required=payload.required,
        default_value=payload.default_value,
        validation_rule=payload.validation_rule,
    )
    return IntegrationMappingRepository(db).add(mapping)


def list_mappings(
    db: Session,
    *,
    organization_id: uuid.UUID,
    integration_id: uuid.UUID,
    entity_type: CanonicalEntityType | None = None,
) -> list[IntegrationMapping]:
    get_integration(db, organization_id=organization_id, integration_id=integration_id)  # tenant check
    return IntegrationMappingRepository(db).list_for_integration(
        integration_id=integration_id, entity_type=entity_type
    )


def delete_mapping(db: Session, *, organization_id: uuid.UUID, mapping_id: uuid.UUID) -> None:
    repo = IntegrationMappingRepository(db)
    mapping = repo.get_by_id_for_organization(mapping_id, organization_id)
    if mapping is None:
        raise NotFoundError("Integration mapping not found.", code="integration_mapping_not_found")
    repo.delete(mapping)

import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.integration_location import IntegrationLocation
from app.models.integration_mapping import CanonicalEntityType
from app.repositories.integration_location_repository import IntegrationLocationRepository
from app.schemas.integration_location import IntegrationLocationUpdate
from app.services import integration_service
from app.services.integration_mapping_engine import map_record
from app.services.integration_service import get_integration


def discover_locations(
    db: Session, *, organization_id: uuid.UUID, integration_id: uuid.UUID
) -> list[IntegrationLocation]:
    """The Setup Checklist's "discover locations" step — calls the
    adapter's fetch_records(entity_type="store") and upserts one
    IntegrationLocation per raw record. Uses whatever field-mapping rows
    are configured for entity_type=store (source_field -> canonical_field)
    to read a location id/name; falls back to raw common key names when no
    mapping exists yet, since discovery is meant to work before the
    mapping step is necessarily configured.
    """
    from app.repositories.integration_mapping_repository import IntegrationMappingRepository

    integration = get_integration(db, organization_id=organization_id, integration_id=integration_id)
    adapter = integration_service.adapter_for(integration)
    credentials = integration_service.decrypt(integration)
    raw_records = adapter.fetch_records(integration, credentials, entity_type="store")

    mappings = IntegrationMappingRepository(db).list_for_integration(
        integration_id=integration_id, entity_type=CanonicalEntityType.STORE
    )
    repo = IntegrationLocationRepository(db)
    discovered: list[IntegrationLocation] = []

    for raw_record in raw_records:
        mapped = map_record(raw_record, mappings) if mappings else {}
        external_id = str(
            mapped.get("external_id")
            or raw_record.get("id")
            or raw_record.get("store_code")
            or raw_record.get("location_id")
            or ""
        )
        if not external_id:
            continue
        name = str(
            mapped.get("name") or raw_record.get("name") or raw_record.get("store_code") or external_id
        )

        existing = repo.get_by_external_location_id(integration_id, external_id)
        if existing is not None:
            existing.external_location_name = name
            discovered.append(repo.add(existing))
            continue
        discovered.append(
            repo.add(
                IntegrationLocation(
                    id=uuid.uuid4(),
                    integration_id=integration_id,
                    external_location_id=external_id,
                    external_location_name=name,
                )
            )
        )
    return discovered


def list_locations(
    db: Session, *, organization_id: uuid.UUID, integration_id: uuid.UUID
) -> list[IntegrationLocation]:
    get_integration(db, organization_id=organization_id, integration_id=integration_id)  # tenant check
    return IntegrationLocationRepository(db).list_for_integration(integration_id)


def update_location(
    db: Session, *, organization_id: uuid.UUID, location_id: uuid.UUID, payload: IntegrationLocationUpdate
) -> IntegrationLocation:
    from app.models.mixins import utcnow

    repo = IntegrationLocationRepository(db)
    location = repo.get_by_id_for_organization(location_id, organization_id)
    if location is None:
        raise NotFoundError("Integration location not found.", code="integration_location_not_found")

    data = payload.model_dump(exclude_unset=True)
    if "store_id" in data:
        location.store_id = data["store_id"]
        location.linked_at = utcnow() if data["store_id"] else None
    if "is_active" in data:
        location.is_active = data["is_active"]
    return repo.add(location)

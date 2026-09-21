import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.integration_error import IntegrationError
from app.models.mixins import utcnow
from app.repositories.integration_error_repository import IntegrationErrorRepository
from app.services.integration_service import get_integration


def list_errors(
    db: Session,
    *,
    organization_id: uuid.UUID,
    integration_id: uuid.UUID,
    is_resolved: bool | None,
    offset: int,
    limit: int,
) -> tuple[list[IntegrationError], int]:
    get_integration(db, organization_id=organization_id, integration_id=integration_id)  # tenant check
    return IntegrationErrorRepository(db).search_for_integration(
        integration_id=integration_id,
        organization_id=organization_id,
        is_resolved=is_resolved,
        offset=offset,
        limit=limit,
    )


def resolve_error(
    db: Session, *, organization_id: uuid.UUID, error_id: uuid.UUID, resolved_by: uuid.UUID
) -> IntegrationError:
    repo = IntegrationErrorRepository(db)
    error = repo.get_by_id_for_organization(error_id, organization_id)
    if error is None:
        raise NotFoundError("Integration error not found.", code="integration_error_not_found")

    error.is_resolved = True
    error.resolved_at = utcnow()
    error.resolved_by = resolved_by
    return repo.add(error)

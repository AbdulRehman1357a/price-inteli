import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.organization import Organization
from app.repositories.organization_repository import OrganizationRepository
from app.schemas.organization import OrganizationUpdate


def update_organization(
    db: Session, *, organization_id: uuid.UUID, payload: OrganizationUpdate
) -> Organization:
    repo = OrganizationRepository(db)
    organization = repo.get_by_id(organization_id)
    if organization is None:
        raise NotFoundError("Organization not found.", code="organization_not_found")

    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(organization, field, value)

    return repo.add(organization)

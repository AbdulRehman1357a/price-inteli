import uuid

from fastapi import status
from sqlalchemy.orm import Session

from app.core.exceptions import AppError, NotFoundError
from app.models.integration_authority import AuthoritySource, IntegrationAuthority
from app.models.integration_mapping import CanonicalEntityType
from app.models.integration_reconciliation import IntegrationReconciliation, IntegrationReconciliationStatus
from app.repositories.integration_authority_repository import IntegrationAuthorityRepository
from app.repositories.integration_reconciliation_repository import IntegrationReconciliationRepository
from app.schemas.integration_authority import IntegrationAuthorityCreate
from app.services.integration_service import get_integration


class AuthorityBlockedError(AppError):
    """Raised when an inbound write is blocked because PIP is configured
    as the authority for that field and allow_override is False. A
    subclass of ApplyError-compatible AppError so it's caught the same way
    by integration_sync_service._run()'s per-record exception handling —
    see app.services.integration_apply_service, which imports and raises
    this alongside its existing ApplyError.
    """

    status_code = status.HTTP_409_CONFLICT
    code = "integration_authority_blocked"


def may_apply(
    db: Session,
    *,
    integration_id: uuid.UUID,
    entity_type: CanonicalEntityType,
    field_name: str,
) -> tuple[bool, IntegrationAuthority | None]:
    """Whether an inbound apply_* write to this field may proceed.

    No configured row at all -> (True, None): today's default behavior
    (external is authoritative) is preserved for every integration that
    hasn't touched authority configuration — this is what keeps the
    Phase 10 upgrade backward compatible with the original implementation.
    """
    authority = IntegrationAuthorityRepository(db).get_effective(
        integration_id, entity_type=entity_type, field_name=field_name
    )
    if authority is None or authority.authority != AuthoritySource.PIP:
        return True, authority
    if authority.allow_override:
        return True, authority
    return False, authority


def log_override(
    db: Session,
    *,
    integration_id: uuid.UUID,
    entity_type: CanonicalEntityType,
    external_id: str,
    field_name: str,
    pip_value: str | None,
    external_value: str | None,
) -> IntegrationReconciliation:
    """Called by integration_apply_service whenever may_apply() allowed a
    write specifically because allow_override=True — the write proceeded,
    but is still flagged for review rather than passing silently, per the
    IntegrationAuthority.allow_override docstring's "allow, but log"
    contract.
    """
    return IntegrationReconciliationRepository(db).add(
        IntegrationReconciliation(
            id=uuid.uuid4(),
            integration_id=integration_id,
            entity_type=entity_type,
            external_id=external_id,
            field_name=field_name,
            pip_value=pip_value,
            external_value=external_value,
            authority_at_detection=AuthoritySource.PIP,
            status=IntegrationReconciliationStatus.OPEN,
        )
    )


def create_authority(
    db: Session, *, organization_id: uuid.UUID, integration_id: uuid.UUID, payload: IntegrationAuthorityCreate
) -> IntegrationAuthority:
    get_integration(db, organization_id=organization_id, integration_id=integration_id)  # tenant check

    authority = IntegrationAuthority(
        id=uuid.uuid4(),
        integration_id=integration_id,
        entity_type=payload.entity_type,
        field_name=payload.field_name,
        authority=payload.authority,
        allow_override=payload.allow_override,
    )
    return IntegrationAuthorityRepository(db).add(authority)


def list_authorities(
    db: Session, *, organization_id: uuid.UUID, integration_id: uuid.UUID
) -> list[IntegrationAuthority]:
    get_integration(db, organization_id=organization_id, integration_id=integration_id)  # tenant check
    return IntegrationAuthorityRepository(db).list_for_integration(integration_id)


def delete_authority(db: Session, *, organization_id: uuid.UUID, authority_id: uuid.UUID) -> None:
    repo = IntegrationAuthorityRepository(db)
    authority = repo.get_by_id_for_organization(authority_id, organization_id)
    if authority is None:
        raise NotFoundError("Integration authority not found.", code="integration_authority_not_found")
    repo.delete(authority)

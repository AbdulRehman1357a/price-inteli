import uuid

from sqlalchemy.orm import Session

from app.core.crypto import decrypt_credentials, encrypt_credentials
from app.core.exceptions import NotFoundError
from app.integrations.base import IntegrationAdapter
from app.integrations.hub.registry import get_hub_adapter
from app.models.integration import Integration, IntegrationStatus
from app.models.mixins import utcnow
from app.repositories.integration_error_repository import IntegrationErrorRepository
from app.repositories.integration_reconciliation_repository import IntegrationReconciliationRepository
from app.repositories.integration_repository import IntegrationRepository
from app.repositories.integration_sync_job_repository import IntegrationSyncJobRepository
from app.schemas.integration import (
    IntegrationCreate,
    IntegrationListParams,
    IntegrationOut,
    IntegrationUpdate,
    TestConnectionResult,
)
from app.schemas.integration_health import IntegrationHealthOut

# The subset of a credentials dict that's safe to keep in plain text on the
# Integration row itself (Integration.base_url_display/auth_type) so the
# UI can show connection details without ever decrypting
# configuration_encrypted — neither key holds a secret.
_DISPLAYABLE_CREDENTIAL_KEYS = {"base_url": "base_url_display", "authentication_type": "auth_type"}

_CAPABILITY_FLAGS = (
    "supports_product_read",
    "supports_product_write",
    "supports_price_read",
    "supports_price_write",
    "supports_inventory_read",
    "supports_inventory_write",
    "supports_promotion_read",
    "supports_promotion_write",
    "supports_sales_read",
    "supports_webhooks",
    "supports_incremental_sync",
)


def _sync_displayable_credentials(integration: Integration, credentials: dict) -> None:
    for credential_key, column_name in _DISPLAYABLE_CREDENTIAL_KEYS.items():
        if credential_key in credentials:
            setattr(integration, column_name, credentials[credential_key] or None)


def create_integration(db: Session, *, organization_id: uuid.UUID, payload: IntegrationCreate) -> Integration:
    integration = Integration(
        id=uuid.uuid4(),
        organization_id=organization_id,
        name=payload.name,
        integration_category=payload.integration_category,
        provider=payload.provider,
        status=payload.status,
        configuration_encrypted=encrypt_credentials(payload.credentials) if payload.credentials else None,
    )
    _sync_displayable_credentials(integration, payload.credentials)
    return IntegrationRepository(db).add(integration)


def get_integration(db: Session, *, organization_id: uuid.UUID, integration_id: uuid.UUID) -> Integration:
    integration = IntegrationRepository(db).get_by_id_for_organization(integration_id, organization_id)
    if integration is None:
        raise NotFoundError("Integration not found.", code="integration_not_found")
    return integration


def list_integrations(
    db: Session, *, organization_id: uuid.UUID, params: IntegrationListParams
) -> tuple[list[Integration], int]:
    offset = (params.page - 1) * params.page_size
    return IntegrationRepository(db).search(
        organization_id,
        integration_category=params.integration_category,
        provider=params.provider,
        status=params.status,
        offset=offset,
        limit=params.page_size,
    )


def update_integration(
    db: Session, *, organization_id: uuid.UUID, integration_id: uuid.UUID, payload: IntegrationUpdate
) -> Integration:
    integration = get_integration(db, organization_id=organization_id, integration_id=integration_id)
    data = payload.model_dump(exclude_unset=True)

    if "name" in data:
        integration.name = data["name"]
    if "integration_category" in data:
        integration.integration_category = data["integration_category"]
    if "status" in data:
        integration.status = data["status"]
    if data.get("credentials") is not None:
        integration.configuration_encrypted = encrypt_credentials(data["credentials"])
        _sync_displayable_credentials(integration, data["credentials"])

    return IntegrationRepository(db).add(integration)


def decrypt(integration: Integration) -> dict:
    if not integration.configuration_encrypted:
        return {}
    return decrypt_credentials(integration.configuration_encrypted)


def adapter_for(integration: Integration) -> IntegrationAdapter:
    return get_hub_adapter(integration.provider)


def get_capabilities(integration: Integration) -> dict[str, bool]:
    """Reads the resolved adapter's capability flags (app/integrations/base.py)
    — a plain attribute lookup, not a live provider call — so IntegrationOut
    can expose them cheaply on every read.
    """
    adapter = adapter_for(integration)
    return {flag: bool(getattr(adapter, flag)) for flag in _CAPABILITY_FLAGS}


def to_out(integration: Integration) -> IntegrationOut:
    """IntegrationOut.model_validate(integration) alone can't populate
    capabilities/has_webhook_secret — neither is a real model column
    (capabilities is adapter-derived; has_webhook_secret deliberately
    reports presence only, never the secret itself) — so every route
    builds the response through this helper instead of calling
    model_validate directly.
    """
    out = IntegrationOut.model_validate(integration)
    out.capabilities = get_capabilities(integration)
    out.has_webhook_secret = bool(integration.webhook_secret_encrypted)
    return out


def test_connection(
    db: Session, *, organization_id: uuid.UUID, integration_id: uuid.UUID
) -> TestConnectionResult:
    integration = get_integration(db, organization_id=organization_id, integration_id=integration_id)
    adapter = adapter_for(integration)
    result = adapter.test_connection(integration, decrypt(integration))

    now = utcnow()
    success = bool(result.get("success"))
    integration.status = IntegrationStatus.ACTIVE if success else IntegrationStatus.ERROR
    if success:
        integration.last_successful_connection_at = now
        integration.last_connection_error = None
    else:
        integration.last_failed_connection_at = now
        integration.last_connection_error = result.get("message")
    IntegrationRepository(db).add(integration)

    return TestConnectionResult(success=success, message=result.get("message"))


def get_health(db: Session, *, organization_id: uuid.UUID, integration_id: uuid.UUID) -> IntegrationHealthOut:
    integration = get_integration(db, organization_id=organization_id, integration_id=integration_id)
    latest_job = IntegrationSyncJobRepository(db).get_latest_for_integration(integration_id)

    return IntegrationHealthOut(
        integration_id=integration.id,
        status=integration.status,
        last_successful_connection_at=integration.last_successful_connection_at,
        last_failed_connection_at=integration.last_failed_connection_at,
        last_sync_at=integration.last_sync_at,
        last_job_status=latest_job.status if latest_job else None,
        last_job_completed_at=latest_job.completed_at if latest_job else None,
        open_error_count=IntegrationErrorRepository(db).count_unresolved(integration_id),
        open_reconciliation_count=IntegrationReconciliationRepository(db).count_open(integration_id),
        webhook_configured=bool(integration.webhook_secret_encrypted),
    )

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.integration import (
    IntegrationCategory,
    IntegrationEnvironment,
    IntegrationProvider,
    IntegrationStatus,
)
from app.schemas.common import PaginationParams


class IntegrationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    integration_category: IntegrationCategory
    provider: IntegrationProvider
    status: IntegrationStatus = IntegrationStatus.PENDING
    # Write-only bundle of whatever the Integration Form's Authentication
    # Type/Base URL/Username/Password/API Key/Webhook URL fields collected —
    # encrypted immediately (app/core/crypto.py) and never echoed back. See
    # IntegrationOut, which has no field for this or for any credential.
    credentials: dict[str, Any] = Field(default_factory=dict)


class IntegrationUpdate(BaseModel):
    """provider is deliberately not updatable — same immutable-after-creation
    precedent as ESLIntegration.integration_type (Phase 9): it determines
    which adapter this integration resolves to.
    """

    name: str | None = Field(default=None, min_length=1, max_length=255)
    integration_category: IntegrationCategory | None = None
    status: IntegrationStatus | None = None
    credentials: dict[str, Any] | None = None


class IntegrationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    integration_category: IntegrationCategory
    provider: IntegrationProvider
    status: IntegrationStatus
    last_sync_at: datetime | None
    created_at: datetime
    updated_at: datetime
    # --- Phase 10 upgrade ---
    provider_version: str | None = None
    environment: IntegrationEnvironment
    base_url_display: str | None = None
    auth_type: str | None = None
    last_successful_connection_at: datetime | None = None
    last_failed_connection_at: datetime | None = None
    last_connection_error: str | None = None
    has_webhook_secret: bool = False
    # Not a model column — resolved by integration_service.get_capabilities()
    # from the adapter's class attributes (app/integrations/base.py) so the
    # frontend can disable/hide entity-type options the resolved adapter
    # doesn't support without duplicating the capability table client-side.
    capabilities: dict[str, bool] = Field(default_factory=dict)


class IntegrationListParams(PaginationParams):
    integration_category: IntegrationCategory | None = None
    provider: IntegrationProvider | None = None
    status: IntegrationStatus | None = None


class TestConnectionResult(BaseModel):
    success: bool
    message: str | None = None

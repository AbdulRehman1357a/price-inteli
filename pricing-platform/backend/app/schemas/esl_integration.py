import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.esl_integration import ESLIntegrationStatus, ESLIntegrationType
from app.schemas.common import PaginationParams


class ESLIntegrationCreate(BaseModel):
    vendor_id: uuid.UUID
    name: str = Field(min_length=1, max_length=255)
    integration_type: ESLIntegrationType
    # Required: an integration is set up for exactly one store, and its
    # devices inherit this store instead of asking for one again per-device
    # or per-import (see esl_integration_service.import_devices,
    # device_service.create_device).
    store_id: uuid.UUID
    base_url: str | None = Field(default=None, max_length=500)
    # Write-only: encrypted immediately on create (app/core/crypto.py) and
    # never echoed back — see ESLIntegrationOut, which has no field for
    # this at all. "Never expose credentials back to the frontend."
    credentials: dict[str, Any] = Field(default_factory=dict)


class ESLIntegrationUpdate(BaseModel):
    """vendor_id/integration_type are deliberately not updatable — same
    immutable-after-creation precedent as OutputChannel.output_type
    (Phase 7) and Device.vendor_id/device_model_id (Phase 8): they
    determine which adapter this integration resolves to.
    """

    name: str | None = Field(default=None, min_length=1, max_length=255)
    base_url: str | None = Field(default=None, max_length=500)
    store_id: uuid.UUID | None = None
    status: ESLIntegrationStatus | None = None
    credentials: dict[str, Any] | None = None


class ESLIntegrationOut(BaseModel):
    """Deliberately has no field for configuration_encrypted or decrypted
    credentials — see ESLIntegrationCreate.credentials.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    vendor_id: uuid.UUID
    name: str
    integration_type: ESLIntegrationType
    store_id: uuid.UUID | None
    base_url: str | None
    status: ESLIntegrationStatus
    last_sync_at: datetime | None
    created_at: datetime
    updated_at: datetime


class ESLIntegrationListParams(PaginationParams):
    vendor_id: uuid.UUID | None = None
    integration_type: ESLIntegrationType | None = None
    status: ESLIntegrationStatus | None = None


class AdapterActionResult(BaseModel):
    """The uniform {success, message, ...} shape every
    ESLIntegrationAdapter method returns, echoed back to the API caller
    as-is (never includes credentials — adapters never receive raw
    ciphertext, only the already-decrypted dict, which they don't return).
    """

    success: bool
    message: str | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


class DiscoveredDevice(BaseModel):
    # protected_namespaces=() — model_hint is a legitimate field name, not
    # a Pydantic model-namespace clash (same fix as DeviceModelOut.model_code).
    model_config = ConfigDict(protected_namespaces=())

    device_identifier: str
    device_name: str
    model_hint: str | None = None
    status: str | None = None


class DiscoverDevicesResult(BaseModel):
    success: bool
    message: str | None = None
    devices: list[DiscoveredDevice] = Field(default_factory=list)


class ImportDeviceItem(BaseModel):
    device_identifier: str = Field(min_length=1, max_length=255)
    device_name: str = Field(min_length=1, max_length=255)


class ImportDevicesRequest(BaseModel):
    # No store_id — imported devices inherit the integration's own store
    # (ESLIntegration.store_id), set once at integration creation.
    device_model_id: uuid.UUID
    devices: list[ImportDeviceItem] = Field(min_length=1)


class TestPriceUpdateRequest(BaseModel):
    device_id: uuid.UUID
    product_id: uuid.UUID | None = None

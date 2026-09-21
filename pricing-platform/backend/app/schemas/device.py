import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.device import DeviceStatus
from app.schemas.common import PaginationParams


class DeviceCreate(BaseModel):
    """store_id/vendor_id are required for the manual creation path
    (DeviceForm) — but when esl_integration_id is set instead, the device
    is being plugged into an existing vendor integration, and
    device_service.create_device derives store_id/vendor_id from that
    integration instead (server-derived, not client-sent), same precedent
    as import_devices. Exactly one of the two paths must be used.
    """

    store_id: uuid.UUID | None = None
    vendor_id: uuid.UUID | None = None
    esl_integration_id: uuid.UUID | None = None
    device_model_id: uuid.UUID
    device_identifier: str = Field(min_length=1, max_length=255)
    device_name: str = Field(min_length=1, max_length=255)
    status: DeviceStatus = DeviceStatus.ACTIVE

    @model_validator(mode="after")
    def _require_integration_or_store_and_vendor(self) -> "DeviceCreate":
        if self.esl_integration_id is not None:
            return self
        if self.store_id is None or self.vendor_id is None:
            raise ValueError("Provide either esl_integration_id, or both store_id and vendor_id.")
        return self


class DeviceUpdate(BaseModel):
    """vendor_id/device_model_id/device_identifier are deliberately not
    updatable — same immutable-after-creation precedent as OutputChannel's
    output_type in Phase 7 (they identify what physical hardware this row
    represents, not a configurable property of it).
    """

    device_name: str | None = Field(default=None, min_length=1, max_length=255)
    store_id: uuid.UUID | None = None
    status: DeviceStatus | None = None


class DeviceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    store_id: uuid.UUID
    vendor_id: uuid.UUID
    esl_integration_id: uuid.UUID | None
    device_model_id: uuid.UUID
    device_identifier: str
    device_name: str
    status: DeviceStatus
    battery_level: int | None
    signal_strength: int | None
    firmware_version: str | None
    last_seen_at: datetime | None
    last_sync_at: datetime | None
    created_at: datetime
    updated_at: datetime


class DeviceListParams(PaginationParams):
    store_id: uuid.UUID | None = None
    vendor_id: uuid.UUID | None = None
    esl_integration_id: uuid.UUID | None = None
    device_model_id: uuid.UUID | None = None
    status: DeviceStatus | None = None
    search: str | None = None


class DeviceHealthOut(BaseModel):
    battery_level: int | None
    signal_strength: int | None
    firmware_version: str | None
    last_seen_at: datetime | None
    connectivity: str
